"""
Resolve all E2E-20260601-135250 cases via the dashboard API,
simulating realistic staff actions for each case type.
Uses form POSTs to quick_action and update endpoints — same as the browser UI.
"""
import sys, json, urllib.request, urllib.error, http.cookiejar, urllib.parse

BASE = "http://localhost:5000"
BATCH = "20260601-135250"

CASES = [
    ("01-PRESCRIPTION",      "Prescription request processed. Checked patient record — repeat prescription authorised by GP. Sent to Boots Lord Street pharmacy via EMIS. Patient advised by callback that prescription will be ready within 2 working days."),
    ("02-SICKNOTE",          "Sick note request reviewed. Patient (James Whitfield) confirmed 10-day period of incapacity for work starting 01/06/2026. MED3 certificate issued by GP and posted to patient address on record. Patient notified by callback."),
    ("03-REFERRAL",          "Referral request reviewed. GP has reviewed clinical notes and agreed urgent referral to Cardiology is appropriate. Referral letter submitted via NHS e-Referral Service. Patient advised expected wait time 4-6 weeks and to call if symptoms worsen."),
    ("04-TEST-RESULT",       "Test result reviewed with GP. Cholesterol results within acceptable range — no immediate action required. GP has added a note to patient record. Patient called back and informed of results. Follow-up blood test booked for 3 months."),
    ("05-REDFLAG",           "Red-flag case reviewed immediately with duty GP. Concerning symptoms documented — GP has arranged same-day urgent appointment. Patient contacted and instructed to attend surgery at 15:30 today. If symptoms worsen before appointment, patient advised to call 999."),
    ("06-IDENTITY-MISMATCH", "Identity mismatch flagged by system. Staff manually cross-checked patient details against EMIS records. DOB and postcode confirmed via secondary verification call to patient. Record updated with verified details. Identity confirmed — safe to proceed."),
    ("07-ADMIN",             "Admin query handled. Patient requested change of registered address. New address verified and updated in EMIS. Patient sent confirmation letter. No clinical action required."),
    ("08-LOW-CONFIDENCE",    "Low-confidence extraction case reviewed by staff. Transcript checked manually. Request identified as medication query re: metformin dosage. GP asked — dose change not indicated at this time. Patient called back with GP advice."),
    ("09-MULTI-INTENT",      "Multi-intent call reviewed. Patient had both a prescription request and appointment query. Repeat prescription actioned (sent to pharmacy). Appointment booked for routine review with GP next Tuesday. Both requests confirmed with patient by callback."),
]

# Set up cookie jar for session
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def post(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=body,
          headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with opener.open(req, timeout=15) as r:
            return r.status, r.url
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)

# Login first
print("Logging in as saeed1...")
status, url = post("/login", {"username": "Saeed1", "password": "Saeed1Test",
                               "auth_method": "password", "next": "/"})
if "login" in url:
    print(f"  Login failed — HTTP {status} redirected to {url}")
    sys.exit(1)
print(f"  Logged in OK → {url}")

resolved = 0
for suffix, outcome in CASES:
    call_id = f"E2E-{BATCH}-{suffix}"
    case_url = f"/case/{call_id}"

    # Start review
    status, url = post(f"{case_url}/quick_action",
                       {"action": "start_review", "return_url": case_url,
                        "assigned_to": "Saeed 1", "edited_by": "Saeed 1"})
    print(f"  [{suffix}] start_review → HTTP {status}")

    # Resolve with outcome notes
    status, url = post(f"{case_url}/update",
                       {"action": "resolve",
                        "outcome_notes": outcome,
                        "resolved_by": "Saeed 1",
                        "edited_by": "Saeed 1",
                        "return_url": case_url,
                        "confirm_review": "on"})
    ok = "case_resolved" in url or status in (200, 302)
    print(f"  [{suffix}] resolve    → HTTP {status} {'OK' if ok else 'FAIL: ' + url}")
    if ok:
        resolved += 1

print(f"\nResolved {resolved}/{len(CASES)} cases.")
