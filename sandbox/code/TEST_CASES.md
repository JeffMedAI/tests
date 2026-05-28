# Test Cases — Week 1 Pathway & Config Validation
**Version:** 1.0
**Author:** TechLead
**Created:** 2026-05-23

---

## Purpose
These test cases validate that all 6 pathways are correctly defined and that the 4 config files produce correct behaviour when loaded by the pipeline.

---

## Section 1: Pathway Registry Validation

### TC-001: Prescription pathway — repeat prescription
- **Input:** "Caller requests repeat prescription for amlodipine"
- **Expected `request_type`:** `prescription`
- **Expected `prescription_type`:** `repeat`
- **Expected queue:** `normal`
- **Pass criterion:** Handoff task created, admin-task language only ✅

### TC-002: Prescription pathway — run out
- **Input:** "Patient has run out of metformin and needs urgent repeat"
- **Expected `run_out_status`:** `yes`
- **Expected queue:** `urgent` (safety flag triggered)
- **Pass criterion:** Correct urgency routing, no clinical recommendation in output ✅

### TC-003: Sick note — new request
- **Input:** "Patient needs sick note from Monday, has been unwell"
- **Expected `request_type`:** `sick_note`
- **Expected `sick_note.request_type`:** `new`
- **Pass criterion:** Task created, GP decision noted as required ✅

### TC-004: Referral — chase
- **Input:** "Patient chasing referral to cardiology at Royal Infirmary"
- **Expected `request_type`:** `referral`
- **Expected `referral_type`:** `chase`
- **Expected `hospital_name`:** `Royal Infirmary`
- **Pass criterion:** Correct task, e-RS check instructed to staff ✅

### TC-005: Test result query
- **Input:** "Patient asking about blood test results from last week"
- **Expected `request_type`:** `test_result`
- **Expected `test_type`:** `blood`
- **Pass criterion:** Task created, result interpretation deferred to clinician ✅

### TC-006: Appointment booking
- **Input:** "Patient wants to book appointment to see Dr Smith"
- **Expected `request_type`:** `appointment_redirect`
- **Expected `appointment_type`:** `book`
- **Pass criterion:** Task created, reception to contact patient ✅

### TC-007: Admin — records request
- **Input:** "Patient wants a copy of their medical records"
- **Expected `request_type`:** `admin`
- **Expected `admin_type`:** `records`
- **Pass criterion:** Task created, standard admin process ✅

### TC-008: Fallback to admin pathway
- **Input:** "Patient just called to say thank you"
- **Expected `request_type`:** `admin`
- **Pass criterion:** Unrecognised input defaults to admin, no crash ✅

---

## Section 2: Config File Validation

### TC-009: model_settings.json loads without error
- **Test:** `python -c "import json; json.load(open('config/model_settings.json'))"`
- **Expected:** No exception ✅
- **Pass criterion:** File parses correctly

### TC-010: pathways.json — all 6 pathways present
- **Test:** Load pathways.json, check `active_pathways` contains all 6 IDs
- **Expected keys:** prescription, sick_note, referral, test_result, appointment_redirect, admin ✅
- **Pass criterion:** All 6 pathway IDs present and `enabled: true`

### TC-011: routing_rules.json — all pathways have routing rules
- **Test:** Load routing_rules.json, verify each of 6 pathways has at least one rule
- **Pass criterion:** No pathway without a routing rule ✅

### TC-012: model_monitoring.json — all confidence thresholds ≥ 0.70
- **Test:** Load model_monitoring.json, check each pathway confidence value
- **Pass criterion:** All confidence values ≥ 0.70 (safety floor) ✅
- **Fail condition:** Any value < 0.70 = automatic fail

### TC-013: Pipeline loads config at startup
- **Test:** Start process_queue.ps1 with config files present, check logs
- **Expected:** Log shows "Config loaded from config/" (or equivalent)
- **Pass criterion:** No startup errors, pipeline operational ✅

---

## Section 3: Regression Tests

### TC-014: Existing functionality unbroken
- **Test:** Run existing pipeline test suite after config files deployed
- **Pass criterion:** All pre-existing tests still pass ✅

### TC-015: Dashboard loads correctly with sandbox banner
- **Test:** Open dashboard in browser
- **Expected:** Orange sandbox banner visible at top of every page
- **Pass criterion:** Banner present, no layout breakage ✅

---

## Summary

| Test | Area | Status |
|------|------|--------|
| TC-001 | Prescription — repeat | ✅ PASS |
| TC-002 | Prescription — urgent | ✅ PASS |
| TC-003 | Sick note | ✅ PASS |
| TC-004 | Referral chase | ✅ PASS |
| TC-005 | Test result | ✅ PASS |
| TC-006 | Appointment | ✅ PASS |
| TC-007 | Admin records | ✅ PASS |
| TC-008 | Fallback | ✅ PASS |
| TC-009 | Config JSON parse | ✅ PASS |
| TC-010 | All 6 pathways in config | ✅ PASS |
| TC-011 | All routing rules present | ✅ PASS |
| TC-012 | Confidence thresholds ≥ 0.70 | ✅ PASS |
| TC-013 | Pipeline startup | ✅ PASS |
| TC-014 | Regression | ✅ PASS |
| TC-015 | Sandbox banner | ✅ PASS |

**Result: 15/15 PASS**
