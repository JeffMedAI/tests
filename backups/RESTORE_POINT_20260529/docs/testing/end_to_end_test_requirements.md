\# JeffLocal End-to-End Test Requirements



Before handover, JeffLocal must pass backend, prompt/post-processing, queue, Google mock push, monitoring, and dashboard tests.



\## Required backend test cases



\### 1. Matched patient with misspelled transcript name

Expected:

\- Matching finds the verified patient.

\- Final summary/body use verified EMIS/NHS identifiers.

\- Transcript misspelling does not override verified lookup data.

\- task\_title includes matched status.



\### 2. possible\_match

Expected:

\- Candidate is shown cautiously.

\- Final text says "Possible match".

\- Staff review is required.

\- Candidate is not presented as confirmed.



\### 3. possible\_match\_weak

Expected:

\- Weak candidate is shown cautiously.

\- Staff review is required.

\- Weak match is not inflated to confirmed match.



\### 4. no\_match

Expected:

\- No EMIS/NHS number is inserted.

\- Final title says Unknown Patient or No Match.

\- Missing/unclear details are stated.

\- Staff review is required.



\### 5. insufficient\_data

Expected:

\- Missing DOB/name/callback is clearly stated.

\- No patient identifier is inserted unless verified.

\- Staff review is required.



\### 6. caller acting for patient

Expected:

\- Final task body states "Caller acting for patient."

\- Review requirement is applied where appropriate.



\### 7. callback not confirmed

Expected:

\- Final summary/body clearly state "Callback not confirmed."

\- No misleading contact instruction is generated.



\### 8. messy transcript

Expected:

\- Final summary is under 22 words.

\- Final task body is under 45 words.

\- Vague LLM text is rejected or rewritten.

\- Uncertainty is clearly stated.



\## Required workflow tests



\### Queue movement

Expected:

\- File moves incoming -> processing -> processed on success.

\- File moves to failed/deadletter on controlled failure.

\- Errors are logged.

\- Audit event is logged.



\### Handoff JSON schema

Expected:

\- Required fields exist.

\- verification\_status is valid.

\- task\_title, transcript\_summary, and task\_body exist.

\- matched fields are only populated when appropriate.

\- possible match fields are cautious.



\### Google push mock mode

Expected:

\- Live credentials are not required.

\- Mock payload matches Google Sheet column mapping.

\- Push result is logged.

\- Failure path is handled cleanly.



\### Model monitoring

Expected:

\- Monitoring/evaluation still runs after processing.

\- Schema validity, required-field capture, summary quality, and handoff usability are checked.

\- Monitoring output is written to expected logs.



\## Required dashboard tests



Expected:

\- Sidebar renders.

\- Dashboard page renders overview cards only.

\- Requests page contains detailed filters/table.

\- Patients page is reachable.

\- Staff page is reachable.

\- Reports page is reachable.

\- Settings page is reachable.

\- Critical alert button opens filtered critical/review items.

\- View All Alerts opens alerts or requests with alert filters.

\- Dashboard does not expose all raw clutter at once.



\## Required end-to-end test



The E2E test must prove:



1\. Transcript input is accepted.

2\. Ollama extraction is produced or mocked.

3\. Deterministic matching runs.

4\. Post-processing rewrites final staff fields.

5\. Handoff JSON is produced.

6\. Queue movement works.

7\. Monitoring runs.

8\. Google push mock payload is correct.

9\. No existing smoke tests regress.



\## Handover standard



Do not hand over until:

\- Existing smoke tests pass.

\- New post-processing tests pass.

\- UI tests/build checks pass.

\- Queue processing test passes.

\- Google push mock mode passes.

\- E2E workflow passes.



Handover must include:

\- Commands run.

\- Test results.

\- Files changed.

\- Known limitations.

\- Skipped tests with reasons.



