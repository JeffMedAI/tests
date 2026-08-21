# SHIPPING — Avamed (JeffLocal)

> How this project goes live, how to check it really did, and what not to do.
> Written 2026-08-21. St Marks has a matching page at
> `C:\JeffLocal\SMCPHARMA\docs\SHIPPING.md` — **the two projects ship in completely
> different ways, so do not carry assumptions from one to the other.**

**One-line difference from St Marks:** pushing this repo deploys **nothing** — the
dashboard is already live from disk. Pushing St Marks **republishes their public website**.

---

## What this project is, and where the code actually runs

On-premises AI patient triage. The dashboard is **43 Python files** (FastAPI) plus a local
SQLite database (`dashboard\jefflocal.db`), running **on this machine** on **port 8765**,
kept alive by the watchdog.

**Production is `C:\JeffLocal\dashboard\`.** Not a copy of it, not a build of it — that
folder, running directly.

The public address `https://dashboard.app-avamed.uk` is a **Cloudflare tunnel** pointing at
`localhost:8765`. A tunnel is a pipe to software running here. Cloudflare carries the
traffic; it does not run the code and does not hold the data.

That distinction is the product. CLAUDE.md line 58: *"All AI runs locally (Ollama/Gemma).
**No patient data leaves the building.**"* It is what is sold to GP practices and it
underpins DSPT, DTAC, Cyber Essentials and the NHS SBS submission.

**Do not "modernise" this onto Cloudflare Workers.** Asked and answered 2026-08-21: a
Worker *is* the software, running on Cloudflare's machines, so patient data would leave the
building. It would also be a full Python→JavaScript rewrite and would cut the dashboard off
from the local pipeline it exists to serve (local SQLite, `outputs\handoff_json\`, Ollama on
11434, n8n on 5678). Same vendor as St Marks, opposite compliance answer.

## How a change goes live

**Immediately, on save.** There is no deploy step and no build. Edit a file under
`dashboard\` and it is live as soon as the service picks it up.

There is **no CI**: no `.github\`, no `wrangler.toml`. **`git push` publishes nothing here.**
Git is version control and offsite backup only.

This cuts both ways: nothing can be "accidentally deployed" by a push — but equally,
half-finished code in `dashboard\` is *already live* before git is ever involved.

## How to verify it is really live

- Check the service answers on **port 8765**, and the public address through the tunnel.
- `git log` tells you what is *recorded*, not what is *running*. They can differ — that is
  normal here and is the opposite of St Marks.

## What you cannot see from a Claude session

- **The GitHub API 404s** on this repo — it is private. Use `git ls-remote origin` to
  confirm a push actually landed.
- Cloudflare tunnel status is dashboard-only. If it is unreachable from a session, say so
  rather than guessing.

## The nightly automation

At **19:00** `scripts\daily\combined_brief.ps1` runs the close for **both** projects, then
sends Saeed one combined WhatsApp brief. At **07:00** it sends the morning brief.

For this project the close: writes a session log from the day's git activity, refreshes
`HANDOFF.md` (unless a real session rewrote it that day), updates `PROJECT_MEMORY.md`,
commits **everything**, pushes, and cuts a restore tag.

**The push guard** (added 2026-08-21). This project watches **`dashboard\`**. If it has
unfinished work at close time, the commit still happens — nothing is lost — but the **push
is held** and that evening's brief says so loudly at the top. Finish it or undo it, and the
next close sends it.

Holding the push protects nothing *live* here (the code is already live from disk); it is
applied for one consistent rule across both projects, and because the warning tells Saeed
production code is sitting unfinished.

To change or disable: `-ProtectPath "dashboard"` in `combined_brief.ps1` section 6. Empty
string turns the guard off entirely.

## Do not do this

- **Do not use `git ... 2>&1` while `$ErrorActionPreference = "Stop"`.** Ordinary git
  notices ("LF will be replaced by CRLF") become fatal errors and silently abandon the
  commit. Judge git on `$LASTEXITCODE`. This bug hid a 3-week backup outage.
- **Do not weaken `.gitignore`.** The close runs `git add -A`; `.gitignore` is the only
  thing keeping `.env`, `*.sqlite`, `*.db`, `logs\`, `queue\`, `outputs\` and `data\` — and
  therefore patient data — out of the repo.
- **Do not commit `SMCPHARMA\` into this repo.** It is a separate repository; `git add -A`
  will otherwise add it as a broken submodule pointer. It is in `.gitignore` for that reason.
- **Do not create a Cowork scheduled task pointed at this folder.** Cowork writes the task's
  own file inside the folder, marks that path protected, then refuses the folder — the task
  runs with no access and fails silently. Proven by experiment 2026-08-20. Use PowerShell +
  Task Scheduler.
- **Do not move or delete `Scheduled\`** while a Cowork task still exists — it reads that
  file live and breaks instantly. Delete the *task* in Cowork; the folder goes with it.
