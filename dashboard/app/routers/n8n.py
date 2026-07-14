"""
n8n workflow integration routes — extracted from main.py.

Covers: /api/n8n/sync, /api/n8n/red-flags, /api/n8n/overdue,
        /api/n8n/daily-summary, /api/n8n/test-intake-batch
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from ..consts import N8NTEST_ARCHIVE_FOLDERS
from ..db import connect, row_to_dict
from ..helpers import ensure_ready
from ..importer import import_handoffs
from ..models import utc_now_iso

_log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/n8n/sync")
def api_sync(rawmock_only: bool = False) -> dict[str, Any]:
    ensure_ready()
    pattern = "TC-*_handoff.json" if rawmock_only else "*_handoff.json"
    with connect() as conn:
        imported = import_handoffs(conn, pattern=pattern)
    return {
        "ok": True,
        "imported": imported,
        "pattern": pattern,
        "timestamp": utc_now_iso(),
    }


@router.get("/api/n8n/red-flags")
def api_red_flags() -> dict[str, Any]:
    ensure_ready()
    from ..main import active_red_flag_clause, api_case
    red_flag_sql, red_flag_params = active_red_flag_clause()
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT call_id, patient_name, request_type, priority, red_flags_present,
                   safe_to_queue, status, call_summary
            FROM cases
            WHERE {red_flag_sql}
            ORDER BY COALESCE(call_timestamp_sort, 0) DESC, call_id ASC
            """,
            red_flag_params,
        ).fetchall()
    cases = [api_case(row) for row in rows]
    return {
        "ok": True,
        "count": len(cases),
        "cases": cases,
    }


@router.get("/api/n8n/overdue")
def api_overdue(threshold_hours: float = 24) -> dict[str, Any]:
    ensure_ready()
    from ..main import active_case_clause, api_case
    cutoff = datetime.now(timezone.utc).timestamp() - (threshold_hours * 3600)
    active_sql, active_params = active_case_clause()
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT call_id, patient_name, request_type, priority, red_flags_present,
                   safe_to_queue, status, call_summary
            FROM cases
            WHERE ({active_sql})
              AND COALESCE(call_timestamp_sort, 0) > 0
              AND call_timestamp_sort <= ?
            ORDER BY COALESCE(call_timestamp_sort, 0) DESC, call_id ASC
            """,
            (*active_params, cutoff),
        ).fetchall()
    cases = [api_case(row) for row in rows]
    return {
        "ok": True,
        "threshold_hours": threshold_hours,
        "count": len(cases),
        "cases": cases,
    }


@router.get("/api/n8n/daily-summary")
def api_daily_summary() -> dict[str, Any]:
    ensure_ready()
    from ..main import (
        SUMMARY_REQUEST_TYPES,
        active_case_clause,
        active_identity_check_clause,
        active_red_flag_clause,
        resolved_case_clause,
    )
    with connect() as conn:
        active_sql, active_params = active_case_clause()
        resolved_sql, resolved_params = resolved_case_clause()
        red_flag_sql, red_flag_params = active_red_flag_clause()
        identity_sql, identity_params = active_identity_check_clause()
        total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        unresolved = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE {active_sql}",
            active_params,
        ).fetchone()[0]
        resolved = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE {resolved_sql}",
            resolved_params,
        ).fetchone()[0]
        red_flags = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE {red_flag_sql}",
            red_flag_params,
        ).fetchone()[0]
        identity_issues = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE {identity_sql}",
            identity_params,
        ).fetchone()[0]
        avg_turnaround = conn.execute(
            "SELECT AVG(turnaround_minutes) FROM cases WHERE turnaround_minutes IS NOT NULL"
        ).fetchone()[0]
        request_type_rows = conn.execute(
            """
            SELECT COALESCE(request_type, 'unknown') AS request_type, COUNT(*) AS count
            FROM cases
            GROUP BY COALESCE(request_type, 'unknown')
            """
        ).fetchall()
    request_type_counts = {value: 0 for value, _label in SUMMARY_REQUEST_TYPES}
    for row in request_type_rows:
        request_type_counts[row["request_type"] or "unknown"] = row["count"]
    return {
        "ok": True,
        "timestamp": utc_now_iso(),
        "total": total,
        "unresolved": unresolved,
        "resolved": resolved,
        "red_flags": red_flags,
        "identity_issues": identity_issues,
        "avg_turnaround_minutes": 0 if avg_turnaround is None else int(avg_turnaround),
        "request_type_counts": request_type_counts,
    }


# ── Test-intake helpers (SANDBOX / TEST ONLY) ─────────────────────────────────


def _is_encrypted_envelope(call: dict[str, Any]) -> bool:
    required_fields = {
        "protocol", "alg", "key_id", "sender_id", "message_id",
        "timestamp_utc", "nonce", "encrypted_key", "iv", "ciphertext",
        "tag", "signature_alg", "signature",
    }
    return required_fields.issubset(call.keys())


def _call_id_from_test_call(call: dict[str, Any]) -> str:
    if _is_encrypted_envelope(call):
        return str(call.get("message_id", "")).strip()
    return str(call.get("call_id", "")).strip()


def _encrypt_local_test_call(call: dict[str, Any]) -> dict[str, Any]:
    from ..main import ROOT_DIR
    fixtures_dir = ROOT_DIR / "tests" / "fixtures"
    if str(fixtures_dir) not in sys.path:
        sys.path.insert(0, str(fixtures_dir))
    from live_lookup_test_payloads import encrypt_envelope  # type: ignore
    return encrypt_envelope(call)


def _archive_n8ntest_artifacts() -> dict[str, Any]:
    from ..main import ROOT_DIR
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_root = ROOT_DIR / "backup" / f"n8ntest_regeneration_{timestamp}"
    summary = []
    total_archived = 0
    for relative_folder in N8NTEST_ARCHIVE_FOLDERS:
        source_folder = ROOT_DIR / relative_folder
        archived_count = 0
        if source_folder.exists():
            for path in sorted(source_folder.glob("*")):
                if not path.is_file():
                    continue
                target_folder = archive_root / relative_folder
                target_folder.mkdir(parents=True, exist_ok=True)
                path.replace(target_folder / path.name)
                archived_count += 1
                total_archived += 1
        summary.append({"folder": relative_folder.replace("/", "\\"), "archived_count": archived_count})
    return {
        "archive_root": str(archive_root) if total_archived else "",
        "total_archived": total_archived,
        "folders": summary,
    }


def _write_n8ntest_envelopes(calls: list[dict[str, Any]]) -> list[str]:
    from ..main import ROOT_DIR
    output_dir = ROOT_DIR / "queue" / "encrypted_raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for call in calls:
        call_id = _call_id_from_test_call(call)
        envelope = call if _is_encrypted_envelope(call) else _encrypt_local_test_call(call)
        path = output_dir / f"{call_id}.json"
        path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        written.append(str(path))
    return written


def _run_encrypted_cycle_disable_google_push() -> dict[str, Any]:
    from ..main import BASE_DIR, ROOT_DIR
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ROOT_DIR / "app" / "run_encrypted_intake_cycle.ps1"),
        "-DisableGooglePush",
    ]
    venv_scripts = BASE_DIR / ".venv" / "Scripts"
    env = os.environ.copy()
    if venv_scripts.exists():
        env["PATH"] = str(venv_scripts) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
        env=env,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def _count_n8ntest_files(relative_folder: str, pattern: str = "*N8NTEST*") -> int:
    from ..main import ROOT_DIR
    folder = ROOT_DIR / relative_folder
    if not folder.exists():
        return 0
    return len([path for path in folder.glob(pattern) if path.is_file()])


def _count_batch_files(relative_folder: str, call_ids: list[str], suffix: str = "") -> int:
    from ..main import ROOT_DIR
    folder = ROOT_DIR / relative_folder
    if not folder.exists():
        return 0
    count = 0
    for call_id in call_ids:
        candidates = [folder / f"{call_id}{suffix}", folder / f"{call_id}.json"] if suffix else [folder / f"{call_id}.json"]
        if any(path.exists() and path.is_file() for path in candidates):
            count += 1
    return count


def _n8ntest_dashboard_cases(call_ids: list[str] | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        if call_ids:
            placeholders = ", ".join(["?"] * len(call_ids))
            rows = conn.execute(
                f"""
                SELECT call_id, patient_name, request_type, priority, red_flags_present,
                       safe_to_queue, staff_review_required, verification_status, status,
                       call_summary
                FROM cases
                WHERE call_id IN ({placeholders})
                ORDER BY call_id ASC
                """,
                tuple(call_ids),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT call_id, patient_name, request_type, priority, red_flags_present,
                       safe_to_queue, staff_review_required, verification_status, status,
                       call_summary
                FROM cases
                ORDER BY call_id ASC
                """
            ).fetchall()
    cases = []
    for row in rows:
        case = row_to_dict(row) or {}
        case["red_flags_present"] = bool(case.get("red_flags_present"))
        case["safe_to_queue"] = bool(case.get("safe_to_queue"))
        case["staff_review_required"] = bool(case.get("staff_review_required"))
        cases.append(case)
    return cases


def _verify_hmac_signature(payload_bytes: bytes, signature_header: str, secret: bytes) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


async def _verify_webhook_hmac(request: Request) -> None:
    secret = os.environ.get("JEFF_WEBHOOK_SECRET", "").encode()
    if not secret:
        _log.warning(
            "HMAC verification SKIPPED — JEFF_WEBHOOK_SECRET not set. "
            "Set this env var before accepting live traffic."
        )
        return
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()
    if not _verify_hmac_signature(body, sig_header, secret):
        _log.warning(
            "Webhook HMAC verification FAILED — path=%s method=%s sig_header_present=%s",
            request.url.path,
            request.method,
            bool(sig_header),
        )
        raise HTTPException(status_code=401, detail="Invalid or missing webhook signature")


@router.post("/api/n8n/test-intake-batch")
async def api_n8n_test_intake_batch(
    request: Request,
    payload: dict[str, Any] = Body(...),
    _hmac: None = Depends(_verify_webhook_hmac),
) -> dict[str, Any]:
    """SANDBOX / TEST ONLY — bypasses n8n entirely.
    All real calls must route through n8n webhook: POST /webhook/ava-live-intake (port 5678).
    Guarded by test_mode=true. HMAC-protected via JEFF_WEBHOOK_SECRET when set.
    It will be removed before production deployment.
    """
    ensure_ready()
    if payload.get("test_mode") is not True:
        raise HTTPException(status_code=400, detail="test_mode must be true")
    if payload.get("disable_google_push") is not True:
        raise HTTPException(status_code=400, detail="disable_google_push must be true")

    batch_id = str(payload.get("batch_id", "")).strip()

    calls = payload.get("calls")
    if not isinstance(calls, list):
        raise HTTPException(status_code=400, detail="calls must be an array")
    if not 1 <= len(calls) <= 5:
        raise HTTPException(status_code=400, detail="calls must contain 1 to 5 items")
    if not all(isinstance(call, dict) for call in calls):
        raise HTTPException(status_code=400, detail="each call must be an object")

    call_ids = [_call_id_from_test_call(call) for call in calls]
    if len(set(call_ids)) != len(call_ids):
        raise HTTPException(status_code=400, detail="duplicate call_id values in batch")

    archive = _archive_n8ntest_artifacts() if payload.get("refresh_artifacts", True) is True else {"total_archived": 0, "folders": []}
    written = _write_n8ntest_envelopes(calls)
    cycle = _run_encrypted_cycle_disable_google_push()
    if cycle["returncode"] != 0:
        raise HTTPException(status_code=500, detail={"message": "encrypted intake cycle failed", "cycle": cycle})

    with connect() as conn:
        dashboard_imported = import_handoffs(conn, pattern="*_handoff.json")

    total_processed = _count_n8ntest_files("queue/processed", "*")
    total_handoffs = _count_n8ntest_files("outputs/handoff_json", "*_handoff.json")
    batch_processed = _count_batch_files("queue/processed", call_ids)
    batch_handoffs = _count_batch_files("outputs/handoff_json", call_ids, "_handoff.json")
    batch_failed = _count_batch_files("queue/failed", call_ids)
    batch_deadletter = _count_batch_files("queue/deadletter", call_ids)
    try:
        cases = _n8ntest_dashboard_cases(call_ids)
    except TypeError:
        cases = _n8ntest_dashboard_cases()
    return {
        "ok": True,
        "batch_id": batch_id,
        "received": len(calls),
        "written": len(written),
        "batch_processed": batch_processed,
        "batch_handoffs": batch_handoffs,
        "batch_failed": batch_failed,
        "batch_deadletter": batch_deadletter,
        "total_n8ntest_handoffs": total_handoffs,
        "dashboard_imported_batch": len(cases),
        "processed": batch_processed if batch_processed else total_processed,
        "handoffs": batch_handoffs if batch_handoffs else total_handoffs,
        "failed": batch_failed,
        "deadletter": batch_deadletter,
        "google_push": "disabled_for_test",
        "dashboard_imported": dashboard_imported,
        "dashboard_imported_total": dashboard_imported,
        "archive": archive,
        "cases": cases,
    }
