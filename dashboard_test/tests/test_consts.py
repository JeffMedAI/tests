"""
TDD tests for app/consts.py — extracted dashboard constants.

RED phase: this file imports from app.consts which does not yet exist.
All tests should fail with ImportError until the module is created.
"""

from app.consts import (
    AUTH_PUBLIC_PATHS,
    AUTH_PUBLIC_PREFIXES,
    DATE_RANGE_OPTIONS,
    DEFAULT_ACTION_NEEDED,
    DEFAULT_OUTCOME_NOTES,
    DEMO_CALL_PREFIXES,
    IDENTITY_REVIEW_STATUSES,
    IN_PROGRESS_STATUS_NAMES,
    LOCAL_SERVICE_URLS,
    LOCKED_DETAIL_FIELDS,
    LOCKED_FIELD_CATEGORIES,
    MODAL_ALERT_TYPE_KEYWORDS,
    N8NTEST_ARCHIVE_FOLDERS,
    NON_MODAL_ALERT_TYPE_KEYWORDS,
    OPEN_BATCH_STATUSES,
    REQUEST_TYPE_CANONICAL,
    REQUEST_TYPE_CHIPS,
    REQUEST_TYPE_LABELS,
    RESOLVED_STATUSES,
    SAFE_MATCH_STATUSES,
    SESSION_COOKIE,
    SORT_OPTIONS,
    STAFF_ROLES,
    STAFF_REVIEW_STATUS_NAMES,
    SUMMARY_REQUEST_TYPES,
    TERMINAL_CASE_STATUSES,
)


class TestN8ntestArchiveFolders:
    def test_is_list(self):
        assert isinstance(N8NTEST_ARCHIVE_FOLDERS, list)

    def test_contains_queue_incoming(self):
        assert "queue/incoming" in N8NTEST_ARCHIVE_FOLDERS

    def test_contains_queue_processed(self):
        assert "queue/processed" in N8NTEST_ARCHIVE_FOLDERS

    def test_contains_queue_failed(self):
        assert "queue/failed" in N8NTEST_ARCHIVE_FOLDERS

    def test_contains_queue_deadletter(self):
        assert "queue/deadletter" in N8NTEST_ARCHIVE_FOLDERS

    def test_contains_handoff_json(self):
        assert "outputs/handoff_json" in N8NTEST_ARCHIVE_FOLDERS

    def test_contains_logs_transcripts(self):
        assert "logs/transcripts" in N8NTEST_ARCHIVE_FOLDERS

    def test_all_entries_are_strings(self):
        assert all(isinstance(f, str) for f in N8NTEST_ARCHIVE_FOLDERS)


class TestLocalServiceUrls:
    def test_is_dict(self):
        assert isinstance(LOCAL_SERVICE_URLS, dict)

    def test_has_dashboard_key(self):
        assert "dashboard" in LOCAL_SERVICE_URLS

    def test_has_n8n_key(self):
        assert "n8n" in LOCAL_SERVICE_URLS

    def test_dashboard_url_correct(self):
        assert LOCAL_SERVICE_URLS["dashboard"] == "http://127.0.0.1:8765"

    def test_n8n_url_correct(self):
        assert LOCAL_SERVICE_URLS["n8n"] == "http://localhost:5678"

    def test_all_values_are_strings(self):
        assert all(isinstance(v, str) for v in LOCAL_SERVICE_URLS.values())


class TestSessionCookie:
    def test_is_string(self):
        assert isinstance(SESSION_COOKIE, str)

    def test_correct_value(self):
        assert SESSION_COOKIE == "jefflocal_session"


class TestAuthPublicPaths:
    def test_is_set(self):
        assert isinstance(AUTH_PUBLIC_PATHS, (set, frozenset))

    def test_contains_login(self):
        assert "/login" in AUTH_PUBLIC_PATHS

    def test_contains_logout(self):
        assert "/logout" in AUTH_PUBLIC_PATHS

    def test_contains_favicon(self):
        assert "/favicon.ico" in AUTH_PUBLIC_PATHS

    def test_contains_forgot(self):
        assert "/forgot" in AUTH_PUBLIC_PATHS

    def test_contains_reset(self):
        assert "/reset" in AUTH_PUBLIC_PATHS


class TestAuthPublicPrefixes:
    def test_is_tuple(self):
        assert isinstance(AUTH_PUBLIC_PREFIXES, tuple)

    def test_contains_static(self):
        assert "/static/" in AUTH_PUBLIC_PREFIXES

    def test_contains_api_health(self):
        assert "/api/health" in AUTH_PUBLIC_PREFIXES

    def test_contains_api_n8n(self):
        assert "/api/n8n/" in AUTH_PUBLIC_PREFIXES


class TestLockedDetailFields:
    def test_is_list(self):
        assert isinstance(LOCKED_DETAIL_FIELDS, list)

    def test_entries_are_tuples(self):
        assert all(isinstance(item, tuple) for item in LOCKED_DETAIL_FIELDS)

    def test_has_patient_name_entry(self):
        field_keys = [f for _, f in LOCKED_DETAIL_FIELDS]
        assert "patient_name" in field_keys

    def test_has_priority_entry(self):
        field_keys = [f for _, f in LOCKED_DETAIL_FIELDS]
        assert "priority" in field_keys


class TestLockedFieldCategories:
    def test_is_list(self):
        assert isinstance(LOCKED_FIELD_CATEGORIES, list)

    def test_entries_are_dicts(self):
        assert all(isinstance(c, dict) for c in LOCKED_FIELD_CATEGORIES)

    def test_has_patient_identity_category(self):
        titles = [c["title"] for c in LOCKED_FIELD_CATEGORIES]
        assert "Patient Identity" in titles


class TestSortOptions:
    def test_is_list(self):
        assert isinstance(SORT_OPTIONS, list)

    def test_has_newest(self):
        values = [o["value"] for o in SORT_OPTIONS]
        assert "newest" in values

    def test_has_priority(self):
        values = [o["value"] for o in SORT_OPTIONS]
        assert "priority" in values


class TestResolvedStatuses:
    def test_is_tuple(self):
        assert isinstance(RESOLVED_STATUSES, tuple)

    def test_contains_resolved(self):
        assert "Resolved" in RESOLVED_STATUSES


class TestTerminalCaseStatuses:
    def test_is_tuple(self):
        assert isinstance(TERMINAL_CASE_STATUSES, tuple)

    def test_contains_resolved(self):
        assert "resolved" in TERMINAL_CASE_STATUSES

    def test_contains_archived(self):
        assert "archived" in TERMINAL_CASE_STATUSES


class TestStatusNameConstants:
    def test_staff_review_names_is_tuple(self):
        assert isinstance(STAFF_REVIEW_STATUS_NAMES, tuple)

    def test_in_progress_names_is_tuple(self):
        assert isinstance(IN_PROGRESS_STATUS_NAMES, tuple)

    def test_staff_review_contains_escalated(self):
        assert "escalated" in STAFF_REVIEW_STATUS_NAMES


class TestIdentityReviewStatuses:
    def test_is_set(self):
        assert isinstance(IDENTITY_REVIEW_STATUSES, (set, frozenset))

    def test_contains_no_match(self):
        assert "no_match" in IDENTITY_REVIEW_STATUSES

    def test_contains_unverified(self):
        assert "unverified" in IDENTITY_REVIEW_STATUSES


class TestSafeMatchStatuses:
    def test_is_set(self):
        assert isinstance(SAFE_MATCH_STATUSES, (set, frozenset))

    def test_contains_matched(self):
        assert "matched" in SAFE_MATCH_STATUSES


class TestMiscSetConstants:
    def test_open_batch_statuses_is_set(self):
        assert isinstance(OPEN_BATCH_STATUSES, (set, frozenset))

    def test_open_batch_contains_new(self):
        assert "New" in OPEN_BATCH_STATUSES

    def test_staff_roles_is_set(self):
        assert isinstance(STAFF_ROLES, (set, frozenset))

    def test_staff_roles_contains_admin(self):
        assert "admin" in STAFF_ROLES


class TestDemoCallPrefixes:
    def test_is_tuple(self):
        assert isinstance(DEMO_CALL_PREFIXES, tuple)

    def test_contains_tc(self):
        assert "TC-" in DEMO_CALL_PREFIXES

    def test_contains_demo(self):
        assert "DEMO" in DEMO_CALL_PREFIXES


class TestAlertTypeKeywords:
    def test_modal_is_tuple(self):
        assert isinstance(MODAL_ALERT_TYPE_KEYWORDS, tuple)

    def test_non_modal_is_tuple(self):
        assert isinstance(NON_MODAL_ALERT_TYPE_KEYWORDS, tuple)

    def test_modal_contains_red_flag(self):
        assert "red flag" in MODAL_ALERT_TYPE_KEYWORDS

    def test_non_modal_contains_summary(self):
        assert "summary" in NON_MODAL_ALERT_TYPE_KEYWORDS


class TestDefaultStrings:
    def test_outcome_notes_is_string(self):
        assert isinstance(DEFAULT_OUTCOME_NOTES, str)

    def test_action_needed_is_string(self):
        assert isinstance(DEFAULT_ACTION_NEEDED, str)

    def test_outcome_notes_not_empty(self):
        assert len(DEFAULT_OUTCOME_NOTES) > 0


class TestRequestTypeConstants:
    def test_labels_is_dict(self):
        assert isinstance(REQUEST_TYPE_LABELS, dict)

    def test_labels_has_prescription(self):
        assert "prescription" in REQUEST_TYPE_LABELS

    def test_canonical_is_dict(self):
        assert isinstance(REQUEST_TYPE_CANONICAL, dict)

    def test_canonical_maps_prescription_request(self):
        assert REQUEST_TYPE_CANONICAL["prescription_request"] == "prescription"

    def test_chips_is_list(self):
        assert isinstance(REQUEST_TYPE_CHIPS, list)

    def test_chips_entries_are_tuples(self):
        assert all(isinstance(c, tuple) for c in REQUEST_TYPE_CHIPS)


class TestDateRangeOptions:
    def test_is_list(self):
        assert isinstance(DATE_RANGE_OPTIONS, list)

    def test_has_today(self):
        values = [o["value"] for o in DATE_RANGE_OPTIONS]
        assert "today" in values


class TestSummaryRequestTypes:
    def test_is_list(self):
        assert isinstance(SUMMARY_REQUEST_TYPES, list)

    def test_entries_are_tuples(self):
        assert all(isinstance(t, tuple) for t in SUMMARY_REQUEST_TYPES)

    def test_has_prescription(self):
        keys = [k for k, _ in SUMMARY_REQUEST_TYPES]
        assert "prescription" in keys
