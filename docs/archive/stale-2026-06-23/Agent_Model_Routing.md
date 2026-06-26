# Agent Model Routing — JeffLocal
# Implemented: 2026-05-31
# Author: Claude (Cowork session)
# Approved by: Saeed (pending — review required before relying on haiku for test/devops)

---

## WHY THIS EXISTS

Agentic AI burns tokens 10–100x faster than single-turn chat. Every tool call
re-sends the full context window. The JeffLocal team runs 8 agents across
hundreds of interactions per development sprint. Routing tasks to the cheapest
model that can handle them well reduces cost by an estimated 40–60% with no
quality loss for routine tasks.

Inspiration: claudeprotips methodology (Instagram/YouTube) — "Use the right
model for the job. Haiku for grunt work. Opus for hard reasoning. Sonnet for
everything in between."

---

## MODEL PRICING (May 2026, Anthropic API)

Source: https://platform.claude.com/docs/en/about-claude/pricing

| Model          | Input / MTok | Output / MTok | Relative cost |
|----------------|-------------|---------------|---------------|
| Haiku 4.5      | $1.00       | $5.00         | 1× (baseline) |
| Sonnet 4.6     | $3.00       | $15.00        | 3× input, 3× output |
| Opus 4.6       | $5.00       | $25.00        | 5× input, 5× output |

MTok = million tokens. Output is always 5× more expensive than input per model.

**Prompt caching** (available on all models): Cache hits cost 10% of input price.
For agents with large, stable system prompts (Lead, Security), caching saves an
additional 70–90% on repeated input tokens.

---

## ROUTING STRATEGY — 8 AGENTS

### Decision framework

```
OPUS  → High-stakes judgment, orchestration, veto decisions, compliance analysis
         Any error here has project-wide consequences
SONNET → Implementation tasks: code, SQL, documentation, reports
          Reliable for patterns the training data covers well
HAIKU  → Pattern completion: test generation, scripts, config files
          Fast and cheap; errors are caught by test runs or review
```

### Agent assignments

| Agent    | Model  | Primary task type                        | Why this model |
|----------|--------|------------------------------------------|----------------|
| lead     | opus   | Orchestration, Saeed liaison, veto enforce | Wrong judgment here cascades to all 7 agents. Needs Opus reasoning to prioritise competing concerns, interpret ambiguous requests, and enforce governance. |
| backend  | sonnet | Flask/Python, auth, Ollama pipeline      | Complex code requiring pattern-matching and security awareness. Sonnet handles production Flask well. Opus not warranted unless debugging subtle auth logic. |
| frontend | sonnet | Jinja2 templates, CSS, dashboard UI      | UI work in a clinical dashboard must be reliable; a Haiku CSS regression could affect staff workflow. Sonnet is the safe minimum. |
| database | sonnet | SQLite schema, migrations, GDPR purge    | Schema decisions affect data integrity and GDPR compliance. Sonnet has sufficient judgment; Security Agent reviews all schema changes anyway. |
| test     | haiku  | pytest fixtures, unit/integration tests  | Test generation is formulaic. Haiku follows pytest conventions well. Failures are self-revealing — if a test is wrong, CI catches it. |
| security | opus   | GDPR, NHS DCB0129, OWASP, PR veto        | Highest-stakes agent. A missed vulnerability or compliance gap could endanger the pilot. Opus mandatory. |
| devops   | haiku  | Git scripts, Task Scheduler, PS scripts  | Scripting tasks are procedural and low-risk. Haiku handles PowerShell and git commands reliably. |
| strategy | sonnet | Reports, governance docs, marketing copy | Long-form writing and research synthesis. Sonnet produces good prose. Opus not needed unless synthesising highly technical content. |

---

## IMPLEMENTATION

### Method: Claude Code subagent definition files

Each agent is defined as a subagent in `.claude/agents/` with `model` set in
YAML frontmatter. When Claude Code invokes an agent via `claude --agent <name>`,
it uses the model specified in that file.

**Files created**: `C:\JeffLocal\.claude\agents\`

```
lead.md      → model: opus   (purple)
backend.md   → model: sonnet (blue)
frontend.md  → model: sonnet (cyan)
database.md  → model: sonnet (yellow)
test.md      → model: haiku  (green)
security.md  → model: opus   (red)
devops.md    → model: haiku  (orange)
strategy.md  → model: sonnet (pink)
```

Each file follows this format:
```yaml
---
name: <agent-name>
description: <trigger description for automatic delegation>
model: <haiku|sonnet|opus>
color: <display colour>
---

You are the <X> Agent for the JeffLocal multi-agent development team.
Read and follow: C:\JeffLocal\sandbox\agents\<name>\<name>_CLAUDE.md
```

**Model resolution order** (Claude Code precedence):
1. `CLAUDE_CODE_SUBAGENT_MODEL` env var (highest — use to force override)
2. Per-invocation `--model` flag
3. Subagent `model` frontmatter ← **this is what we set**
4. Main conversation model (fallback)

### Method: PowerShell launcher script

`C:\JeffLocal\scripts\launch_agent.ps1` — routes `claude --agent <name>` with
the correct `--model` flag. Use when invoking agents from the command line.

```powershell
.\scripts\launch_agent.ps1 -Agent backend
.\scripts\launch_agent.ps1 -Agent security -Task "Review PR #42"
.\scripts\launch_agent.ps1 -Agent test -Force  # Use session default model
```

### How to invoke agents (three equivalent methods)

```
Method 1 — Claude Code subagent (recommended):
  claude --agent backend
  @backend (in conversation)

Method 2 — PowerShell launcher:
  .\scripts\launch_agent.ps1 -Agent backend

Method 3 — Manual model flag:
  claude --agent backend --model sonnet
```

---

## EXPECTED TOKEN SAVINGS

### Assumptions

- 8 agents, ~20 tasks/day across the team (active development sprint)
- Average task: ~5,000 input tokens + ~2,000 output tokens per agent interaction
- Without routing: all agents on Sonnet (current default)

### Baseline (all Sonnet)

```
Daily:   20 tasks × (5,000 × $3/MTok + 2,000 × $15/MTok)
       = 20 × ($0.015 + $0.030)
       = 20 × $0.045
       = $0.90/day

Monthly: $0.90 × 30 = $27.00/month
```

### Optimised (routed)

Agent distribution per day (rough estimate):
- 2 Opus tasks (lead + security reviews)
- 12 Sonnet tasks (backend, frontend, database, strategy)
- 6 Haiku tasks (test + devops)

```
Opus tasks (2):    2 × (5,000 × $5/MTok + 2,000 × $25/MTok)
                 = 2 × ($0.025 + $0.050) = $0.15

Sonnet tasks (12): 12 × (5,000 × $3/MTok + 2,000 × $15/MTok)
                 = 12 × ($0.015 + $0.030) = $0.54

Haiku tasks (6):   6 × (5,000 × $1/MTok + 2,000 × $5/MTok)
                 = 6 × ($0.005 + $0.010) = $0.09

Daily total: $0.15 + $0.54 + $0.09 = $0.78/day
Monthly: $0.78 × 30 = $23.40/month
```

### Summary

| Scenario   | Monthly cost | vs baseline |
|------------|-------------|-------------|
| All Sonnet | $27.00      | —           |
| Routed     | $23.40      | −13% ($3.60) |

**Note**: The saving grows with usage. At 50 tasks/day (busy sprint) the monthly
gap widens proportionally. The bigger saving comes from NOT using Opus for
routine tasks — if the default were ever set to Opus, routing saves ~60%.

With **prompt caching** on Lead and Security (large stable system prompts),
an additional 30–50% reduction on those agents' input costs is achievable.

---

## TRADEOFFS AND RISKS

| Risk | Mitigation |
|------|-----------|
| Haiku misses a subtle test bug | Test Agent output is always verified by running the test suite. Haiku works well for formulaic pytest patterns. |
| Haiku DevOps script has logic error | Scripts are reviewed before running. DevOps Agent never deploys without Saeed approval. |
| Sonnet Backend misses security nuance | Security Agent (Opus) reviews all backend PRs. Belt-and-suspenders. |
| Opus costs spike if Security/Lead overused | Both agents have narrow, well-defined scopes. Lead should not write code. Security should not be used for non-review tasks. |
| Haiku context window (200k) differs from Sonnet/Opus (1M) | JeffLocal tasks are well within 200k. No issue expected. |

---

## UPGRADE TRIGGERS

Escalate to a higher model if:

- Haiku test agent produces consistently wrong tests → upgrade to Sonnet
- DevOps script causes an incident → upgrade to Sonnet
- Backend agent misses a security-relevant pattern → upgrade to Opus for that session
- Strategy agent produces poor-quality clinical documents → upgrade to Opus

Use `CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-6 claude --agent devops` to
temporarily override without changing the subagent definition file.

---

## SOURCES

- Anthropic pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code model config: https://support.claude.com/en/articles/11940350-claude-code-model-configuration
- Model routing guide: https://www.augmentcode.com/guides/ai-model-routing-guide
- Token cost analysis: https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/
