\# JeffLocal



JeffLocal is a local GP reception workflow system for processing voice-agent transcripts, extracting structured request details, applying deterministic patient matching and safety rules, and creating staff handoff output.



\## Purpose



JeffLocal is designed to support reception/admin staff by turning messy voice-agent call transcripts into clear, safe, staff-facing tasks.



The system should help staff quickly understand:



\- Who the request is for

\- What the caller wants

\- Whether the patient was matched

\- Whether identity/staff review is required

\- What needs to happen next



\## Core Safety Rule



> Ollama may extract and draft. Deterministic JeffLocal code must verify, match, validate, post-process, and finalize. LLM output must never override verified EMIS/NHS/patient lookup data.



\## AI Build and Review Prompts



This repo includes structured prompts for working with Codex, Claude Code, and Cursor:



\- \[Codex Build Prompt](docs/prompts/codex\_build\_prompt.md)

\- \[Claude/Cursor Review Prompt](docs/prompts/claude\_cursor\_review\_prompt.md)

\- \[LLM vs Rules Responsibility](docs/architecture/llm\_vs\_rules\_responsibility.md)

\- \[End-to-End Test Requirements](docs/testing/end\_to\_end\_test\_requirements.md)



\## Intended Workflow



1\. Receive raw call transcript.

2\. Use local Ollama model to extract draft structured details.

3\. Apply deterministic patient matching.

4\. Apply verification, safety, and review rules.

5\. Post-process final staff-facing fields using verified EMIS/NHS identifiers where available.

6\. Build staff handoff JSON.

7\. Move items through the queue.

8\. Push staff handoff output to Google Sheets or mock push in test mode.

9\. Run monitoring/evaluation checks.



\## Key Principle



The LLM helps understand messy language.



The rules layer protects patient identity, safety, matching, queueing, and final staff handoff quality.

