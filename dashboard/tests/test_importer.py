import json
import shutil
from pathlib import Path
import sys


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from app.db import connect, init_db
from app.importer import import_handoffs, map_handoff_to_case
from app.main import filter_clause
from app.models import format_display_timestamp, parse_call_timestamp_sort


_BASE_HANDOFF = {
    "call_timestamp": "2026-05-12T09:00:00Z",
    "request_type": "prescription",
    "normalized_input": {
        "patient_name": "Test Patient",
        "dob": "1970-01-01",
        "postcode": "PR9 7LT",
        "callback_number": "07111000000",
    },
    "verification_status": "matched",
    "verification_reason": "test",
    "priority": "routine",
    "safe_to_queue": True,
    "staff_review_required": False,
    "red_flags_present": False,
    "task_title": "Routine task",
    "task_body": "Test task body",
    "call_summary": "Routine request",
    "raw_transcript": "Patient called about routine matter.",
    "status": "New",
}


def _write_handoff(handoff_dir: Path, call_id: str, **overrides) -> dict:
    data = {**_BASE_HANDOFF, "call_id": call_id, **overrides}
    path = handoff_dir / f"{call_id}_handoff.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def _seed_handoff_dir(handoff_dir: Path) -> list:
    """Write 12 synthetic handoff JSON files to a temp directory."""
    handoff_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    cases.append(_write_handoff(handoff_dir, "TC-001-REPEAT-EXACT"))
    cases.append(_write_handoff(
        handoff_dir, "TC-006-URGENT-REDFLAG",
        priority="999 Emergency",
        safe_to_queue=False,
        staff_review_required=True,
        red_flags_present=True,
        call_summary="Chest pain and breathlessness",
        raw_transcript="Caller reports chest pain and breathlessness.",
    ))
    cases.append(_write_handoff(
        handoff_dir, "TC-008-THIRD-PARTY-POSSIBLE",
        verification_status="possible_match",
        safe_to_queue=False,
        staff_review_required=True,
    ))
    cases.append(_write_handoff(
        handoff_dir, "TC-009-INSUFFICIENT-ID",
        verification_status="insufficient_data",
        safe_to_queue=False,
        staff_review_required=True,
    ))
    cases.append(_write_handoff(
        handoff_dir, "TC-011-NO-MATCH",
        verification_status="no_match",
        safe_to_queue=False,
        staff_review_required=True,
    ))
    for i in [2, 3, 4, 5, 7, 10, 12]:
        cases.append(_write_handoff(handoff_dir, f"TC-{i:03d}-ROUTINE"))
    return cases


def test_importer_reads_and_upserts_without_duplicates(tmp_path):
    handoff_dir = tmp_path / "handoffs"
    _seed_handoff_dir(handoff_dir)
    db_path = tmp_path / "dashboard.sqlite"
    with connect(db_path) as conn:
        init_db(conn)
        first_count = import_handoffs(conn, handoff_dir)
        second_count = import_handoffs(conn, handoff_dir)
        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

    assert first_count >= 12
    # Second pass imports nothing: the first pass retired those files to
    # processed/. Before this was fixed the importer re-imported every file on
    # every 60s pass forever, which re-stamped imported_at and made the
    # dashboard beep at staff once a minute for two-day-old cases.
    assert second_count == 0
    assert case_count == 12


def test_reimport_does_not_restamp_imported_at(tmp_path):
    """imported_at means 'when this case FIRST landed', not 'when we last
    touched the file'. /api/cases/new-since and the analytics volume queries
    both read it as an arrival time, so re-stamping it makes old cases look
    brand new (the every-60s beep, and skewed hourly volume)."""
    handoff_dir = tmp_path / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    _write_handoff(handoff_dir, "TC-REIMPORT-STAMP")
    db_path = tmp_path / "dashboard.sqlite"

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, handoff_dir)
        first_seen = conn.execute(
            "SELECT imported_at FROM cases WHERE call_id = ?", ("TC-REIMPORT-STAMP",)
        ).fetchone()[0]

        # Put the file back and re-import, exactly as the 60s loop used to.
        shutil.move(
            str(handoff_dir / "processed" / "TC-REIMPORT-STAMP_handoff.json"),
            str(handoff_dir / "TC-REIMPORT-STAMP_handoff.json"),
        )
        import_handoffs(conn, handoff_dir)
        after_reimport = conn.execute(
            "SELECT imported_at FROM cases WHERE call_id = ?", ("TC-REIMPORT-STAMP",)
        ).fetchone()[0]

    assert after_reimport == first_seen


def test_importer_retires_successful_files_to_processed(tmp_path):
    """Successful files must leave the inbox. Only failures moved before, so
    successes were re-read on every pass forever."""
    handoff_dir = tmp_path / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    _write_handoff(handoff_dir, "TC-RETIRE-ME")
    db_path = tmp_path / "dashboard.sqlite"

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, handoff_dir)

    assert not (handoff_dir / "TC-RETIRE-ME_handoff.json").exists()
    assert (handoff_dir / "processed" / "TC-RETIRE-ME_handoff.json").exists()


def test_importer_ignores_already_processed_subfolder(tmp_path):
    """glob() must not reach into processed/ — otherwise retiring files
    achieves nothing and the re-import loop returns."""
    handoff_dir = tmp_path / "handoffs"
    processed = handoff_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    _write_handoff(processed, "TC-ALREADY-DONE")
    db_path = tmp_path / "dashboard.sqlite"

    with connect(db_path) as conn:
        init_db(conn)
        count = import_handoffs(conn, handoff_dir)
        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

    assert count == 0
    assert case_count == 0


def test_repeated_retire_failure_never_accumulates_pii_copies(tmp_path, monkeypatch):
    """A retire that fails every pass must not mint a new copy each time.

    These files hold patient data. shutil.move falls back to copy2+unlink when
    os.rename fails; if the unlink then fails, a copy lands in processed/ AND
    the original stays in the inbox, so the next pass writes copy N+1 — ~1440
    PII copies/day at the 60s import interval. os.replace either moves or
    raises, leaving nothing behind.
    """
    import app.importer as importer_module

    handoff_dir = tmp_path / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    _write_handoff(handoff_dir, "TC-STUCK")
    db_path = tmp_path / "dashboard.sqlite"

    calls = {"n": 0}

    def _always_fails(src, dst):
        calls["n"] += 1
        raise PermissionError("simulated AV/backup lock on the file")

    monkeypatch.setattr(importer_module.os, "replace", _always_fails)
    importer_module._retire_failures.clear()

    with connect(db_path) as conn:
        init_db(conn)
        for _ in range(10):  # ten 60s passes
            import_handoffs(conn, handoff_dir)
        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

    processed = handoff_dir / "processed"
    copies = list(processed.glob("*")) if processed.exists() else []

    assert calls["n"] == 10, "retire should be attempted on each pass"
    assert copies == [], f"a failing retire must leave NOTHING behind, found: {copies}"
    assert (handoff_dir / "TC-STUCK_handoff.json").exists(), "source must survive a failed retire"
    assert case_count == 1, "a stuck file must never block intake"
    # Failure escalated, not swallowed forever.
    assert importer_module._retire_failures[str(handoff_dir / "TC-STUCK_handoff.json")] == 10


def test_retire_is_idempotent_when_identical_file_already_processed(tmp_path):
    """The retry path: an identical file is already retired. Drop the source
    rather than minting copy N+1."""
    handoff_dir = tmp_path / "handoffs"
    processed = handoff_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    _write_handoff(handoff_dir, "TC-IDEMPOTENT")
    shutil.copy2(
        handoff_dir / "TC-IDEMPOTENT_handoff.json",
        processed / "TC-IDEMPOTENT_handoff.json",
    )
    db_path = tmp_path / "dashboard.sqlite"

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, handoff_dir)

    assert not (handoff_dir / "TC-IDEMPOTENT_handoff.json").exists()
    assert len(list(processed.glob("TC-IDEMPOTENT*"))) == 1, "must not create a .2 copy of an identical file"


def test_retiring_survives_a_name_collision_in_processed(tmp_path):
    """Same call_id arriving twice with DIFFERENT content must keep both —
    the earlier copy is evidence, not garbage."""
    handoff_dir = tmp_path / "handoffs"
    processed = handoff_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    # Content must DIFFER, or this exercises the idempotent path instead.
    _write_handoff(processed, "TC-COLLIDE", call_summary="first version")
    _write_handoff(handoff_dir, "TC-COLLIDE", call_summary="re-processed version")
    db_path = tmp_path / "dashboard.sqlite"

    with connect(db_path) as conn:
        init_db(conn)
        count = import_handoffs(conn, handoff_dir)

    # Both kept: the earlier copy is evidence.
    assert len(list(processed.glob("TC-COLLIDE*"))) == 2
    assert (processed / "TC-COLLIDE_handoff.2.json").exists()
    assert count == 1
    assert not (handoff_dir / "TC-COLLIDE_handoff.json").exists()


def test_importer_supports_pattern_filtered_import(tmp_path):
    handoff_dir = tmp_path / "handoffs"
    _seed_handoff_dir(handoff_dir)
    db_path = tmp_path / "dashboard.sqlite"
    with connect(db_path) as conn:
        init_db(conn)
        count = import_handoffs(conn, handoff_dir, pattern="TC*_handoff.json")
        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

    assert count == 12
    assert case_count == 12


def test_filters_return_expected_cases(tmp_path):
    handoff_dir = tmp_path / "handoffs"
    _seed_handoff_dir(handoff_dir)
    db_path = tmp_path / "dashboard.sqlite"
    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, handoff_dir)

        where, params = filter_clause("urgent_red_flags")
        urgent_ids = {
            row["call_id"]
            for row in conn.execute(f"SELECT call_id FROM cases WHERE {where}", params).fetchall()
        }

        where, params = filter_clause("identity_issues")
        identity_ids = {
            row["call_id"]
            for row in conn.execute(f"SELECT call_id FROM cases WHERE {where}", params).fetchall()
        }

    assert "TC-006-URGENT-REDFLAG" in urgent_ids
    assert "TC-008-THIRD-PARTY-POSSIBLE" in identity_ids
    assert "TC-009-INSUFFICIENT-ID" in identity_ids
    assert "TC-011-NO-MATCH" in identity_ids


def test_reimport_updates_locked_fields_and_preserves_staff_fields(tmp_path):
    handoff_dir = tmp_path / "handoffs"
    handoff_dir.mkdir()
    data = _write_handoff(handoff_dir, "TC-012-MULTI-INTENT", request_type="admin")
    target = handoff_dir / "TC-012-MULTI-INTENT_handoff.json"

    db_path = tmp_path / "dashboard.sqlite"
    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, handoff_dir)
        conn.execute(
            """
            UPDATE cases
            SET assigned_to = ?, outcome_notes = ?, staff_action = ?,
                last_edited_at = ?, last_edited_by = ?, action_needed = ?
            WHERE call_id = ?
            """,
            (
                "Test Staff",
                "Keep this note",
                "Keep this action",
                "2026-05-11T13:00:00+00:00",
                "tester",
                "Staff edited action needed",
                "TC-012-MULTI-INTENT",
            ),
        )
        conn.commit()

    data["priority"] = "review_required"
    data["safe_to_queue"] = False
    data["staff_review_required"] = True
    data["red_flags_present"] = False
    data["verification_status"] = "matched"
    data["request_type"] = "admin"
    target.write_text(json.dumps(data), encoding="utf-8")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, handoff_dir)
        row = conn.execute(
            """
            SELECT priority, safe_to_queue, staff_review_required, red_flags_present,
                   verification_status, request_type, assigned_to, outcome_notes,
                   staff_action, action_needed, source_file_mtime
            FROM cases WHERE call_id = ?
            """,
            ("TC-012-MULTI-INTENT",),
        ).fetchone()

    assert row["priority"] == "review_required"
    assert row["safe_to_queue"] == 0
    assert row["staff_review_required"] == 1
    assert row["red_flags_present"] == 0
    assert row["verification_status"] == "matched"
    assert row["request_type"] == "admin"
    assert row["assigned_to"] == "Test Staff"
    assert row["outcome_notes"] == "Keep this note"
    assert row["staff_action"] == "Keep this action"
    assert row["action_needed"] == "Staff edited action needed"
    assert row["source_file_mtime"]


def test_locked_fields_match_source_json(tmp_path):
    handoff_dir = tmp_path / "handoffs"
    cases_data = _seed_handoff_dir(handoff_dir)
    db_path = tmp_path / "dashboard.sqlite"
    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, handoff_dir)
        rows = {
            row["call_id"]: row
            for row in conn.execute(
                """
                SELECT call_id, request_type, priority, safe_to_queue,
                       staff_review_required, red_flags_present, verification_status
                FROM cases
                """
            ).fetchall()
        }

    assert len(rows) == 12
    for data in cases_data:
        row = rows[data["call_id"]]
        assert row["request_type"] == data["request_type"]
        assert row["priority"] == data["priority"]
        assert bool(row["safe_to_queue"]) == bool(data["safe_to_queue"])
        assert bool(row["staff_review_required"]) == bool(data["staff_review_required"])
        assert bool(row["red_flags_present"]) == bool(data["red_flags_present"])
        assert row["verification_status"] == data["verification_status"]
        assert row["priority"] not in {"low", "medium", "high"}


def test_timestamp_sort_parses_supported_formats():
    values = [
        "2026-05-11T12:50:00Z",
        "2026-05-11T12:50:00",
        "2026-05-08T12:22:04.583719Z",
        "2026-05-11 12:50",
    ]

    parsed = [parse_call_timestamp_sort(value) for value in values]

    assert all(value > 0 for value in parsed)
    assert parsed[0] == parsed[1]
    assert parsed[0] == parsed[3]
    assert parsed[2] < parsed[0]


def test_timestamp_display_formatter():
    assert format_display_timestamp("2026-05-11T12:50:00Z") == "11-05-2026 T 12.50"
    assert format_display_timestamp("2026-05-08T12:22:04.583719Z") == "08-05-2026 T 12.22"


def test_gp_demo_payload_processing_stores_informative_task_and_summary():
    case = map_handoff_to_case(
        {
            "call_id": "GPDEMO-20260513-120000-001-PRESCRIPTION",
            "timestamp_utc": "2026-05-13T12:00:00Z",
            "request_type": "prescription",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": False,
            "red_flags_present": False,
            "patient": {"callback_number": "07111000000"},
            "transcript": "Caller requests a repeat blood pressure prescription and confirms callback. No urgent symptoms reported.",
        }
    )

    assert case["task_body"]
    assert case["call_summary"]
    assert "prescription" in case["task_body"].lower()
    assert "blood pressure" in case["task_body"].lower()
    assert "07111000000" in case["task_body"]
    assert "matched" in case["task_body"]
    assert "Safe to queue" in case["task_body"]
    assert "Caller asked for" in case["call_summary"]
    assert case["staff_task_title"] == case["task_title"]
    assert case["staff_task_body"] == case["task_body"]
    assert case["ai_summary"] == case["call_summary"]
    assert case["patient_record_note"]
    assert "DOB" not in case["patient_record_note"]


def test_gp_demo_red_flag_task_includes_urgent_footer():
    case = map_handoff_to_case(
        {
            "call_id": "GPDEMO-20260513-120000-005-REDFLAG",
            "timestamp_utc": "2026-05-13T12:00:00Z",
            "request_type": "appointment_redirect",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient": {"callback_number": "07111000000"},
            "transcript": "Caller reports chest pain, breathlessness and sweating. Agent advises 999 immediately.",
        }
    )

    assert "Red flags present" in case["task_body"]
    assert "Not safe to queue" in case["task_body"]
    assert "999/A&E" in case["task_body"]
    assert "chest pain" in case["call_summary"].lower()
    assert "Urgent/red-flag case: follow local urgent escalation protocol" in case["patient_record_note"]


def test_identity_issue_summary_mentions_review_required():
    case = map_handoff_to_case(
        {
            "call_id": "GPDEMO-20260513-120000-004-IDENTITY",
            "timestamp_utc": "2026-05-13T12:00:00Z",
            "request_type": "admin",
            "verification_status": "possible_match",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "transcript": "Caller is a family member and gives partial demographics. Staff must complete identity checks.",
        }
    )

    assert "possible_match" in case["call_summary"]
    assert "Staff review required" in case["call_summary"]
    assert "Identity review" in case["task_title"] or "Admin request" in case["task_title"]


def test_patient_record_note_identifier_order_and_name_fallback():
    emis_case = map_handoff_to_case(
        {
            "call_id": "GPDEMO-EMIS",
            "timestamp_utc": "2026-05-13T12:00:00Z",
            "request_type": "prescription",
            "matched_emis_number": "E123",
            "matched_nhs_number": "9990001111",
            "patient_name": "Demo Name",
            "callback_number": "07111000000",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "transcript": "Caller requested repeat medication.",
        }
    )
    nhs_case = map_handoff_to_case(
        {
            "call_id": "GPDEMO-NHS",
            "timestamp_utc": "2026-05-13T12:00:00Z",
            "request_type": "prescription",
            "matched_nhs_number": "9990001111",
            "patient_name": "Demo Name",
            "callback_number": "07111000000",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "transcript": "Caller requested repeat medication.",
        }
    )
    name_case = map_handoff_to_case(
        {
            "call_id": "GPDEMO-NAME",
            "timestamp_utc": "2026-05-13T12:00:00Z",
            "request_type": "prescription",
            "patient_name": "Demo Name",
            "callback_number": "07111000000",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "transcript": "Caller requested repeat medication.",
        }
    )

    assert "EMIS: E123" in emis_case["patient_record_note"]
    assert "Patient: Demo Name" not in emis_case["patient_record_note"]
    assert "NHS: 9990001111" in nhs_case["patient_record_note"]
    assert "Patient: Demo Name" not in nhs_case["patient_record_note"]
    assert "Patient: Demo Name" in name_case["patient_record_note"]
    assert "07111000000" in name_case["patient_record_note"]


def test_missing_processing_output_uses_safe_fallback_for_dashboard_warning():
    case = map_handoff_to_case(
        {
            "call_id": "GPDEMO-20260513-120000-999-MISSING",
            "timestamp_utc": "2026-05-13T12:00:00Z",
            "request_type": "admin",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
        }
    )

    assert case["staff_review_required"] == 1
    assert case["task_title"] == "Processing output unavailable - staff review required"
    assert case["task_body"].startswith("AI-generated task output was unavailable")
    assert case["call_summary"] == "AI summary unavailable - staff review required."
    assert case["patient_record_note"]
