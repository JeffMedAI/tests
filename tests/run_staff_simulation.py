"""Staff simulation — inspect + resolve 5 fresh CSV batch cases via Playwright."""
from playwright.sync_api import sync_playwright
import json, time, urllib.request as ur, urllib.parse

BASE  = "http://127.0.0.1:8765"
BATCH = "CSV-FRESH-20260619-1315"
SUFFIXES = ["001-PRESCRIPTION", "002-TESTRESULT", "003-SICKNOTE", "004-THIRDPARTY", "005-REDFLAG"]

observations = []

def post_form(path, body_dict, cookie_hdr):
    data = urllib.parse.urlencode(body_dict).encode()
    req = ur.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie_hdr},
        method="POST",
    )
    try:
        with ur.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode()[:300]
    except ur.HTTPError as e:
        return e.code, e.read().decode()[:300]


def get_case(call_id, cookie_hdr):
    req = ur.Request(f"{BASE}/api/cases/{call_id}", headers={"Cookie": cookie_hdr})
    with ur.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(base_url=BASE, ignore_https_errors=True)
    page = ctx.new_page()

    # ── Login ─────────────────────────────────────────────────────────────────
    page.goto(f"{BASE}/login")
    page.fill("#username", "test_user")
    page.fill('input[name="password"]', "test_pass")
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/login" not in u, timeout=10000)
    print(f"LOGIN OK: {page.url}")

    for suffix in SUFFIXES:
        call_id = f"{BATCH}-{suffix}"
        obs = {"call_id": call_id}

        # Fresh cookie header each iteration
        cookies = ctx.cookies()
        cookie_hdr = "; ".join(f'{c["name"]}={c["value"]}' for c in cookies)

        # ── Inspect incoming case ─────────────────────────────────────────────
        try:
            data = get_case(call_id, cookie_hdr)
            obs["incoming"] = {
                "status":              data.get("status"),
                "priority":            data.get("priority"),
                "verification_status": data.get("verification_status"),
                "safe_to_queue":       data.get("safe_to_queue"),
                "red_flags_present":   data.get("red_flags_present"),
                "request_type":        data.get("request_type"),
                "canonical_request_type": data.get("canonical_request_type"),
            }
        except Exception as e:
            obs["incoming_error"] = str(e)

        # ── Open dashboard page and check detail panel renders ────────────────
        page.goto(f"{BASE}/requests")
        page.wait_for_load_state("networkidle")

        # Try to click the case card
        try:
            page.locator(f'[data-call-id="{call_id}"]').first.click(timeout=3000)
            obs["card_open"] = "ok"
        except Exception:
            try:
                page.get_by_text(call_id).first.click(timeout=3000)
                obs["card_open"] = "text_click"
            except Exception:
                obs["card_open"] = "not_found"

        time.sleep(0.8)
        html = page.content()
        obs["panel_shows_outcome_field"] = "outcome_notes" in html.lower() or "outcome notes" in html.lower()
        obs["panel_shows_resolve_button"] = "mark_resolved" in html.lower() or "resolve" in html.lower()

        # ── Resolution by case type ───────────────────────────────────────────
        if "005-REDFLAG" in call_id:
            # Must reject resolve without notes
            s, b = post_form(f"/case/{call_id}/update", {
                "mark_resolved": "yes", "resolved_by": "test_user",
                "last_edited_by": "test_user", "outcome_notes": "",
            }, cookie_hdr)
            obs["redflag_no_notes_status"] = s
            obs["redflag_no_notes_correct"] = (s == 400)
            # Now resolve properly
            s2, _ = post_form(f"/case/{call_id}/update", {
                "mark_resolved": "yes", "resolved_by": "test_user",
                "last_edited_by": "test_user",
                "outcome_notes": "Emergency escalation confirmed. Patient called 999. GP informed. Practice record updated.",
            }, cookie_hdr)
            obs["redflag_resolved_status"] = s2

        elif "004-THIRDPARTY" in call_id:
            # Step 1: start_review
            s0, _ = post_form(f"/case/{call_id}/quick_action", {
                "action": "start_review", "edited_by": "test_user",
            }, cookie_hdr)
            obs["identity_start_review"] = s0
            # Step 2: try resolve without notes (must fail)
            s, b = post_form(f"/case/{call_id}/update", {
                "mark_resolved": "yes", "resolved_by": "test_user",
                "last_edited_by": "test_user", "outcome_notes": "",
            }, cookie_hdr)
            obs["identity_no_notes_status"] = s
            obs["identity_no_notes_correct"] = (s == 400)
            # Step 3: resolve with notes
            s2, _ = post_form(f"/case/{call_id}/update", {
                "mark_resolved": "yes", "resolved_by": "test_user",
                "last_edited_by": "test_user",
                "outcome_notes": "Daughter confirmed as authorised caller. Identity verified by callback. Medication review booked for next week.",
            }, cookie_hdr)
            obs["identity_resolved_status"] = s2

        elif "002-TESTRESULT" in call_id:
            s0, _ = post_form(f"/case/{call_id}/quick_action", {
                "action": "start_review", "edited_by": "test_user",
            }, cookie_hdr)
            obs["start_review"] = s0
            s, _ = post_form(f"/case/{call_id}/update", {
                "mark_resolved": "yes", "resolved_by": "test_user",
                "last_edited_by": "test_user",
                "outcome_notes": "HbA1c and cholesterol results reviewed. Both within normal range. Patient called back and informed.",
            }, cookie_hdr)
            obs["resolve_status"] = s

        elif "003-SICKNOTE" in call_id:
            s0, _ = post_form(f"/case/{call_id}/quick_action", {
                "action": "start_review", "edited_by": "test_user",
            }, cookie_hdr)
            obs["start_review"] = s0
            s, _ = post_form(f"/case/{call_id}/update", {
                "mark_resolved": "yes", "resolved_by": "test_user",
                "last_edited_by": "test_user",
                "outcome_notes": "Fit note issued for two weeks (anxiety and work-related stress). Sent to patient.",
            }, cookie_hdr)
            obs["resolve_status"] = s

        else:  # 001-PRESCRIPTION
            # Locked field probe first (before resolving)
            s_lock, b_lock = post_form(f"/case/{call_id}/update", {
                "priority": "999 Emergency",
                "verification_status": "no_match",
                "safe_to_queue": "false",
                "last_edited_by": "test_user",
                "outcome_notes": "Locked field test",
            }, cookie_hdr)
            obs["locked_probe_status"] = s_lock
            # Verify locked fields unchanged
            check = get_case(call_id, cookie_hdr)
            obs["locked_probe_priority_unchanged"] = (check.get("priority") != "999 Emergency")
            obs["locked_probe_verification_unchanged"] = (check.get("verification_status") != "no_match")
            # Now proper resolve
            s, _ = post_form(f"/case/{call_id}/update", {
                "mark_resolved": "yes", "resolved_by": "test_user",
                "last_edited_by": "test_user", "assigned_to": "test_user",
                "outcome_notes": "Repeat prescription for ramipril 10mg sent to Churchtown Pharmacy. Patient informed by text.",
            }, cookie_hdr)
            obs["resolve_status"] = s

        # ── Verify final resolved state ───────────────────────────────────────
        time.sleep(0.5)
        cookies = ctx.cookies()
        cookie_hdr = "; ".join(f'{c["name"]}={c["value"]}' for c in cookies)
        try:
            final = get_case(call_id, cookie_hdr)
            obs["final_status"] = final.get("status")
            obs["final_priority"] = final.get("priority")
            obs["final_verification"] = final.get("verification_status")
            obs["final_resolved_by"] = final.get("resolved_by")
        except Exception as e:
            obs["final_error"] = str(e)

        observations.append(obs)
        print(f"DONE: {suffix}")

    browser.close()

print("\n" + "="*60)
print(json.dumps(observations, indent=2))
