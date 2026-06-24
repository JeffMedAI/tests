# AVAMED — MONETIZATION & AUTONOMOUS MARKETING PLAN
# JeffLocal: AI Patient Intake for UK GP Surgeries
# Document type: Strategy — Confidential Internal
# Owner: Strategy Agent
# Status: RESEARCH-BACKED DRAFT — requires Saeed review before external use
# Created: 2026-05-31
# Research date: 2026-05-31 (live NHS, competitor, and procurement data)

---

## CONSTRAINTS (read before acting on any section)

- All external content requires Saeed's explicit approval before publication. No exceptions.
- Churchtown case study is embargoed until written consent + pilot metrics confirmed.
- Pricing figures in this document are internal working assumptions — not to be quoted externally.
- This document is the working basis for investment decisions and sprint planning.
- Revenue projections are modelled estimates, not guarantees.

---

## TABLE OF CONTENTS

1. Market Opportunity (with real numbers)
2. Recommended Pricing Model
3. Revenue Projections (3 scenarios × 3 years)
4. NHS Procurement Roadmap
5. Autonomous Marketing Execution
6. 30/60/90 Day Monetization Sprint
7. Plugin / MCP / Skill Stack for Autonomous Marketing

---

## SECTION 1: MARKET OPPORTUNITY

### 1.1 The Market — Real Numbers (sourced May 2026)

**GP Practices in England:**
As of April 2026, there are **6,158 GP practices** in England, down from ~7,600 a decade ago due to mergers and closures. The consolidation trend continues: 1,465 practices have closed or merged since 2015. This consolidation is strategically relevant — it means fewer but larger practices, which shifts the buyer profile toward Practice Managers managing larger patient lists (and larger call volumes).

Source: NHS Digital, Patients Registered at a GP Practice, March 2026; RCGP, April 2026

**Primary Care Networks (PCNs):**
There are **1,250 PCNs** across England. Each PCN typically covers 30,000–50,000 patients across a natural community of GP practices (averaging ~5 practices per PCN). Over 99% of practices are PCN members. PCN-level contracts are the bridge between single-practice sales and ICB-level commissioning.

Source: NHS England Primary Care Networks guidance, 2025/26

**Call Volume (the problem JeffLocal solves):**
NHS Digital's cloud-based telephony data (October 2025) recorded **2.17 million inbound calls** to GP practices between 8:00am and 10:00am on Monday mornings alone — the peak window. Individual practice data shows practices receiving 150–300+ calls per day. One documented case showed 247 abandoned calls per day before intervention. At a 30–40% admin burden per call (patient verification, pathway routing, note-taking), a 200-call-per-day practice consumes 60–80 call-hours per week on intake admin alone.

Source: NHS Digital Cloud-Based Telephony Data, October 2025; swcomms.co.uk GP call data; NHS England telephony analysis 2024

**AI in GP Administration — Validated Demand:**
A November 2025 Digital Health report (OneAdvanced) modelled that AI agents automating paperwork in GP surgeries could free the equivalent of **150,000 appointments/week** and generate **£75 million/year** in NHS productivity savings if adopted nationally. This validates the market appetite for exactly what JeffLocal does — automated admin processing at the point of patient contact.

Source: digitalhealth.net, November 2025

**GP Workforce Pressure (the urgency behind the sale):**
- 39,086 FTE NHS GPs as of February 2026
- FTE GP Partners fell by 424 in 12 months to April 2026
- 411 million standard appointments booked in the 12 months to April 2026
- Average patients per FTE GP: 2,199 (rising)

Every metric shows a system doing more with less. JeffLocal sells into a buyer who has no slack left.

Source: BMA Pressures in General Practice Data Analysis; NHS England GP workforce statistics, 2026

---

### 1.2 Market Sizing

**TAM — Total Addressable Market (England, GP intake automation)**

JeffLocal's total addressable market is every GP practice in England that handles inbound patient phone calls — which is all of them.

```
TAM calculation (conservative price point — see Section 2):
6,158 practices × £349/month = £2,149,142/month = £25.8m/year
```

This is the static TAM at a single-practice pricing tier. It understates the real opportunity because:
- PCN bundle deals carry a volume discount but capture 5+ practices per sale
- ICB enterprise deals (Phase 3) can cover 300+ practices in a single contract
- Wales, Scotland, and NI represent ~600 additional practices (not modelled here)

**SAM — Serviceable Addressable Market (Phase 1–2 geography)**

Phase 1 focus: North West England (Cheshire & Merseyside, Greater Manchester, Lancashire)
Estimated ~650 GP practices in this region.

```
SAM: 650 practices × £349/month = £226,850/month = £2.72m/year
```

Phase 2 expansion: all England, PCN-level deals.

```
SAM Phase 2: 1,250 PCNs × ~5 practices × £249/practice/month = £1.56m/month = £18.7m/year
(PCN bundle pricing — see Section 2)
```

**SOM — Serviceable Obtainable Market (realistic targets)**

```
12-month SOM (Year 1, Phase 1): 20 practices at £349/month = £83,760/year ARR
24-month SOM (Year 2, Phase 2): 80 practices + 3 PCN deals = £515k ARR (base case)
36-month SOM (Year 3, Phase 3): 200 practices + 8 PCN + 1 ICB = £1.26m ARR (base case)
```

Full projection detail in Section 3.

---

### 1.3 Revenue Model Comparison

Four models are viable for JeffLocal. Assessment:

| Model | Pros | Cons | Verdict |
|---|---|---|---|
| **Flat monthly per practice** | Predictable, easy to budget, GP Partner can sign off without committee | Doesn't capture value from high-volume practices | ✅ PRIMARY |
| **Per-call/per-transaction** | Aligns cost with usage, low upfront risk for buyer | Unpredictable for buyer (NHS hates budget surprises), harder to model ARR | ❌ Not recommended |
| **Per-patient per year** | Industry standard (Anima uses 80p/patient) | Requires knowing patient list size; feels like a data charge to privacy-conscious buyers | ⚠️ Consider for ICB tier only |
| **PCN bundle** | One sale covers 5+ practices, stronger LTV | Longer sales cycle, needs PCN-level relationship | ✅ PHASE 2 |
| **ICB enterprise** | Massive deal size, national scale | Very long sales cycle (12–24 months), requires framework listing | ✅ PHASE 3 |

**Recommendation:** Launch with flat monthly per-practice. Introduce PCN bundle at Phase 2. Develop ICB enterprise pricing for Phase 3 framework applications.

---

## SECTION 2: RECOMMENDED PRICING MODEL

### 2.1 Competitor Pricing Context (researched May 2026)

Before setting price, the competitive landscape:

**Accurx** (broad comms platform — messaging, triage, video, batch):
- G-Cloud 14 published pricing: Bronze ~£5,300/year (~£442/month) for 10k patients; Gold ~£10,700/year (~£892/month) for 10k patients
- Individual modules: Patient triage alone ~£5,100/year (~£425/month) for 10k patients
- Market position: dominant, used by thousands of practices, funded in many areas by ICBs
- Differentiation from JeffLocal: digital/text-based, not phone-focused; cloud data model

**Anima** (AI-first online triage + document processing):
- Pricing: ~80p per patient per year → £8,000/year (~£667/month) for 10k-patient practice
- Deployed: 200+ practices, 2 million patients
- Differentiation: online form submission, not voice/phone; AI triage scoring

**eConsult** (online consultation):
- Similar tier to Anima; NHS-funded in many ICBs post the 2025 mandatory online consultation requirement
- Funded nationally in many areas — practices often receive it "free" from ICB budget

**Hero Health** (care navigation):
- 45p per patient per year → £4,500/year (~£375/month) for 10k patients
- Cheaper positioning, newer entrant

**Klinik** (AI phone + online triage):
- Pricing not public; case study shows a PCN saved £300,000 over the deployment period
- Most similar to JeffLocal (includes phone triage component)
- Positioned at PCN/enterprise level

**Key insight from competitor data:**
The market has established a pricing band of **£375–£900/month per 10k-patient practice** for digital triage/communication tools. JeffLocal's on-premise architecture, phone-specific focus, and GDPR-clean data model justify positioning within (or slightly below) this band.

The "no data leaves the building" differentiator is a genuine premium — practices that have rejected cloud tools on GDPR grounds are an underserved segment. JeffLocal should not undercut on price; it should match the market and win on trust.

---

### 2.2 Recommended Price Points

**Tier 1 — Practice Starter (single practice, flat monthly)**

```
£299/month (£3,588/year)
```

Rationale:
- Below Accurx Bronze (£442/month) — accessible for practices not in ICB-funded areas
- Above Hero Health (£375/month for 10k patients on per-patient model) — not the cheapest
- Simple: one number, one invoice, no usage metering
- Below the informal GP Partner sign-off threshold (~£500/month) — Practice Manager can often approve without a partners' meeting
- Annual equivalent: £3,588/year — well below the typical partner sign-off threshold that triggers formal review (estimated £5,000–£10,000/year based on NHS procurement norms for minor revenue contracts)

**Tier 2 — Practice Standard (includes priority support + multi-site access)**

```
£449/month (£5,388/year)
```

Rationale:
- Comparable to Accurx Silver / Anima pricing band
- Includes dedicated onboarding, quarterly review call, and priority response to technical issues
- Appropriate for larger practices (10,000+ patients) where the ROI is proportionally higher
- £449/month likely requires a brief GP Partner nod but not a formal committee review

**Tier 3 — PCN Bundle (per-network pricing)**

```
£249/practice/month (billing to PCN, not individual practices)
= £1,245/month for a 5-practice PCN
= £2,490/month for a 10-practice PCN
```

Rationale:
- 17% discount vs. Starter tier — reward for volume commitment
- Billing at PCN level simplifies administration (one invoice, one relationship)
- At 5 practices: £14,940/year — manageable for PCN shared budgets
- PCN budget context: PCNs receive ~£1.50 per registered patient from NHS England for additional roles and services; a 30,000-patient PCN has ~£45,000 in flexible services budget — JeffLocal at £1,245/month (£14,940/year) is ~33% of that, which requires a clear ROI case

**Tier 4 — ICB Enterprise (negotiated, framework-listed)**

```
£200/practice/month at volume (estimated; framework-dependent)
= £200,000/month for 1,000 practices across an ICB
```

Not for current pricing — model for Phase 3 framework applications only.

**Pilot/Trial Pricing (low-friction entry — critical for NHS market)**

```
Free for 30 days, then £249/month (month-to-month, cancel anytime)
```

Rationale:
- No NHS buyer signs a 12-month contract for a new vendor without a trial
- 30-day free trial removes the biggest barrier ("prove it before we pay")
- £249/month post-trial is below Practice Starter — reward for early commitment
- Month-to-month initially, option to switch to annual (with 15% discount) after 3 months
- This is the entry point for outreach sequences — "try it free for 30 days" is a call to action that GP Practice Managers can agree to without GP Partner sign-off

---

### 2.3 What Triggers GP Partner Review vs. Practice Manager Sign-Off

Based on NHS procurement norms and GP practice governance:

| Spend Level | Decision Maker | Typical Threshold | Implication for JeffLocal |
|---|---|---|---|
| Under £100/month | Practice Manager alone | No approval needed | Pilot phase: aim to get under this threshold or make it "free trial" |
| £100–£500/month | Practice Manager with informal Partner awareness | Partners notified, not voted | Starter tier (£299/month) sits in this band — Practice Manager can proceed |
| £500–£1,500/month | GP Partners informal vote or majority agreement | Raised at partners' meeting | Standard tier (£449/month) is borderline — position as Practice Manager decision |
| £1,500–£5,000/month | Formal partners' meeting + vote | Requires meeting agenda item | PCN tier: PCN Manager takes this to PCN board |
| Over £5,000/month or long-term contract | Formal procurement, potentially ICB review | Written proposal required | Enterprise tier: full sales cycle |

**Sales process implication:** The first sale is always Practice Manager → pilot → Practice Manager approves Starter tier → Referral to GP Partners for Standard or PCN upgrade. Design all outreach to close a trial, not a contract.

---

## SECTION 3: REVENUE PROJECTIONS

### Assumptions (transparent — show your working)

```
Model inputs:
- Average revenue per practice (ARPP): £349/month (blended Starter/Pilot mix)
- Churn assumption: 5%/month initially (NHS buyers are sticky once implemented; 5% is conservative)
- Sales cycle: 6–10 weeks from first email to trial start; 8–12 weeks trial to paid
- Phase 1 (Year 1): North West England geography, founder-led sales, no sales team
- Phase 2 (Year 2): National geography, PCN-level deals begin, 1 part-time BD hire or agent-led
- Phase 3 (Year 3): ICB framework deals, agency/channel partnerships

PCN bundle: £249/practice, average PCN = 5 practices = £1,245/month per PCN
ICB pilot deal: 50 practices at £200/practice = £10,000/month assumed (one deal)
```

---

### Scenario A — Conservative

**Assumption:** Slow NHS adoption, extended pilot phases, 1 in 3 pilots converts to paid.

```
YEAR 1 (Phase 1: single geography, Churchtown pilot complete, outreach begins Q3 2026)
- Q3 2026: Churchtown transitions to paid + 2 new pilots = 3 practices, 1 paying
- Q4 2026: 2 more paid, 3 more in pilot = 3 paying
- End of Year 1: 6 paying practices at £299/month average
- MRR at 12 months: £1,794/month
- ARR at 12 months: £21,528

YEAR 2 (Phase 2: national outreach, PCN conversations begin)
- Q1 2027: 12 paying practices
- Q2 2027: 20 paying practices + 1 PCN deal (5 practices at £249)
- Q3 2027: 30 paying + 2 PCN deals
- Q4 2027: 40 paying + 2 PCN deals
- End of Year 2: 40 single practices + 2 PCN deals (10 practices)
- MRR at 24 months: (40 × £299) + (2 × £1,245) = £11,960 + £2,490 = £14,450/month
- ARR at 24 months: £173,400

YEAR 3 (Phase 3: ICB pursuit, framework listing in progress)
- End of Year 3: 80 single practices + 5 PCN deals (25 practices) + no ICB deal yet
- MRR at 36 months: (80 × £299) + (5 × £1,245) = £23,920 + £6,225 = £30,145/month
- ARR at 36 months: £361,740
```

---

### Scenario B — Base Case

**Assumption:** Normal NHS sales cycle, 1 in 2 pilots converts, PCN deals from Year 2, one ICB pilot in Year 3.

```
YEAR 1
- 20 paying practices by end of Year 1 (mix of £299 and £449)
- Blended ARPP: £349/month
- MRR at 12 months: £6,980/month
- ARR at 12 months: £83,760

YEAR 2
- 80 paying single practices + 3 PCN deals (15 practices at PCN rate)
- MRR at 24 months: (80 × £349) + (3 × £1,245) = £27,920 + £3,735 = £31,655/month
- ARR at 24 months: £379,860
- Note: at 80 practices this likely triggers a need for one CS/onboarding hire

YEAR 3
- 200 single practices + 8 PCN deals (40 practices) + 1 ICB pilot (50 practices at £200)
- MRR at 36 months: (200 × £349) + (8 × £1,245) + (50 × £200) = £69,800 + £9,960 + £10,000
  = £89,760/month
- ARR at 36 months: £1,077,120 (crossing £1m ARR)
```

---

### Scenario C — Optimistic

**Assumption:** Churchtown case study gets press coverage (Pulse Today), PCN Clinical Director endorses, 2 ICB pilots by Year 3.

```
YEAR 1
- 35 paying practices by end of Year 1 (word of mouth from Churchtown PCN)
- Blended ARPP: £399/month (more Standard tier uptake)
- MRR at 12 months: £13,965/month
- ARR at 12 months: £167,580

YEAR 2
- 150 paying single practices + 5 PCN deals (25 practices at PCN rate)
- MRR at 24 months: (150 × £399) + (5 × £1,245) = £59,850 + £6,225 = £66,075/month
- ARR at 24 months: £792,900

YEAR 3
- 400 practices + 12 PCN deals (60 practices) + 2 ICB pilots (100 practices at £200)
- MRR at 36 months: (400 × £399) + (12 × £1,245) + (100 × £200) = £159,600 + £14,940 + £20,000
  = £194,540/month
- ARR at 36 months: £2,334,480
```

---

### Summary Table

| Scenario | Year 1 ARR | Year 2 ARR | Year 3 ARR | Year 3 MRR |
|---|---|---|---|---|
| Conservative | £21,528 | £173,400 | £361,740 | £30,145 |
| **Base Case** | **£83,760** | **£379,860** | **£1,077,120** | **£89,760** |
| Optimistic | £167,580 | £792,900 | £2,334,480 | £194,540 |

**The base case crosses £1m ARR at approximately 36 months from Phase 1 completion.** This is achievable without external funding if Saeed is the sole sales resource in Year 1 and hires one BD/CS person in Year 2 from early revenue.

---

## SECTION 4: NHS PROCUREMENT ROADMAP

### 4.1 Compliance Prerequisites (do these first — everything gates on them)

Before any framework application or ICB pitch, JeffLocal needs these:

**1. Data Security and Protection Toolkit (DSPT)**
- What it is: Annual self-assessment against NHS data security standards. Mandatory for all organisations handling NHS patient data.
- Status: Must complete before any NHS commercial relationship.
- Process: Register at dsptoolkit.nhs.uk, complete self-assessment (~60 questions), submit by March each year.
- Cost: Free. Time: 4–8 weeks of internal effort.
- Agent role: Research all questions in advance, draft answers for Saeed review, identify any gaps (e.g., named Data Protection Officer, information asset register).

**2. DTAC (Digital Technology Assessment Criteria)**
- What it is: NHS England's baseline assurance standard for digital health technologies. Updated April 2026 (25% fewer questions, de-duplicated with DSPT).
- Five criteria: clinical safety, data protection, technical security, interoperability, usability & accessibility.
- Status: Required for NHS Buying Catalogue listing and recommended by all ICBs for procurement.
- Process: Complete DTAC self-assessment form (updated version, post 6 April 2026), submit alongside any NHS procurement application.
- JeffLocal advantage: On-premise architecture satisfies the hardest data protection questions immediately. No cloud transfer = no data residency concern.
- Agent role: Download current DTAC form, map each question to JeffLocal's architecture, draft responses, flag gaps.

**3. Cyber Essentials Certification**
- What it is: UK government-backed cybersecurity scheme. Now mandatory for G-Cloud 15 and recommended for NHS SBS framework.
- Cost: £300–£500 for basic Cyber Essentials; £1,500–£3,000 for Cyber Essentials Plus.
- Timeline: 4–6 weeks from application to certificate.
- Agent role: Research certifying bodies, draft application preparation checklist, identify any JeffLocal systems that need remediation.

**4. ICO Registration**
- What it is: Registration with the Information Commissioner's Office as a data controller.
- Cost: £52/year (Tier 1 for small organisations).
- Status: Check whether Avamed is already registered.
- Agent role: Verify registration status, draft registration if needed.

---

### 4.2 G-Cloud 15

**Status:** G-Cloud 15 application window **closed January 30, 2026**. Awards expected September 2026. JeffLocal missed this iteration.

**Next step:** G-Cloud 16 is expected to open in late 2026 or early 2027. Preparation for G-Cloud 16 should begin in Q3 2026.

**What's required for G-Cloud listing:**
- Cyber Essentials (mandatory)
- DSPT completion
- Service definition document (what you sell, what it does, pricing)
- Carbon reduction plan (mandatory from G-Cloud 14 onward)
- Modern slavery statement
- Financial viability evidence

**JeffLocal G-Cloud fit:** JeffLocal is an on-premise system — unusual for G-Cloud (cloud-focused). However, the dashboard reporting layer and potential future managed-service offering could qualify under the "Software" lot. The strategy should be to list the dashboard/reporting component as a SaaS-adjacent product while describing the on-premise AI engine separately.

**Action items:**
- Q3 2026: Begin Cyber Essentials application
- Q4 2026: Complete DSPT and DTAC
- Q1 2027: Prepare G-Cloud 16 service definition
- Q2 2027: Submit G-Cloud 16 application (anticipated window)

---

### 4.3 NHS SBS Healthcare AI Solutions Framework

**Status:** This is the most immediately actionable framework for JeffLocal.

- **Launched:** 11 May 2026
- **Submission deadline: 23 June 2026** — THIS IS ACTIVE NOW
- **Value:** £900 million, valid May 2027 – May 2035
- **Lots relevant to JeffLocal:**
  - Lot 6: Operational efficiency (GP admin automation fits here)
  - Lot 4: Predictive analytics (secondary fit)
  - Lot 8: Integrated combined solutions (if winning 2+ lots)

**Requirements for submission:**
- Ariba Network account (free to register: supplier.ariba.com)
- Evidence of AI/technology capability
- DSPT completion (or in progress with a clear timeline)
- Cyber Essentials (or evidence of process started)
- SMEs explicitly welcomed

**Critical timeline:**
- Deadline: 23 June 2026 — 23 days from this document's date
- This is achievable if Saeed acts immediately on Ariba registration and DSPT
- Contract awards: March 2027
- Framework active: May 2027

**Recommendation: PURSUE THIS FRAMEWORK NOW.** Even if JeffLocal cannot satisfy all criteria by 23 June, submitting a strong response with evidence of DSPT-in-progress and a clear compliance roadmap is better than missing the 8-year framework window entirely. The NHS SBS explicitly welcomes SMEs.

**Agent role:** Register on Ariba Network today. Download the tender document from find-tender.service.gov.uk (Notice 043057-2026). Map JeffLocal's capabilities to each lot description. Draft the narrative sections of the submission for Saeed review. Flag which sections require Saeed's direct input (financial viability, director declarations).

---

### 4.4 Cheshire & Merseyside ICB — Direct Pilot Commissioning

**Why this ICB:** Churchtown Medical Centre is in Southport — within the Cheshire & Merseyside ICB geography. This ICB has:
- A £29.6 million transformation fund for 2026–27 (announced March 2026)
- An active Primary Care Digital Sub-Strategy (2024–2027) explicitly prioritising AI to "radically transform" operations
- A commitment to digital tools that "support clinical workflows and improve operational productivity"
- A stated ambition to establish a "digital centre of excellence" for innovation

This is a primed buyer. JeffLocal directly addresses their stated priorities.

**Key contacts to identify and approach:**
- Chief Digital Information Officer (CDIO), NHS Cheshire & Merseyside
- Primary Care Digital Lead / Director of Primary Care
- Innovation/Transformation Team

**How to approach:**
1. Secure Churchtown consent and basic pilot metrics first (essential — you cannot approach an ICB without evidence)
2. Draft a 2-page Commissioner Briefing: what JeffLocal does, Churchtown pilot results, cost per practice, compliance status
3. Saeed emails the CDIO or Digital Lead directly (founder-to-commissioner, not vendor pitch)
4. Propose a funded PCN-level pilot: 5–10 practices, 3-month evaluation, ICB pays at PCN bundle rate
5. If accepted: ICB issues a direct award under their transformation fund (under £50k threshold)

**Agent role:** Research names and contact details for C&M ICB digital leadership team (LinkedIn, ICB website, NHS Digital directory). Draft the Commissioner Briefing document. Draft the initial email for Saeed to send.

---

### 4.5 GP IT Futures Framework

**Status:** The GP IT Futures framework (the main NHS route for GP clinical software) is primarily focused on clinical systems (EMIS, SystmOne) and their ecosystem. It is not the right route for JeffLocal at this stage — it requires deeper NHS accreditation than Avamed currently holds. Monitor for Phase 3 when EMIS/SystmOne integration is planned.

---

### 4.6 NHS Buying Catalogue / DSIC

**Status:** The NHS Buying Catalogue (via Digital Services for Integrated Care) is the primary route for ICBs procuring GP software. Getting listed:
- Requires DTAC completion + DSPT
- Application through NHS Digital supplier portal
- Relevant when ICB commissioners are looking to procure — gives them a "safe" way to buy JeffLocal

**Recommended for Phase 2 (Q4 2026)** after DTAC and DSPT are complete.

---

## SECTION 5: AUTONOMOUS MARKETING EXECUTION

*This section defines what the Strategy Agent executes without Saeed's intervention, what requires approval, which tools enable each capability, and the specific workflow.*

---

### Philosophy (inspired by the Claude Code marketing skills ecosystem)

The jens.heitmann Instagram reel referenced in the brief ("You might not need a marketing hire. You need the right skills installed.") reflects a real and documented methodology in the Claude Code ecosystem. While Jens Heitmann's specific content is Instagram-native and not fully searchable, the methodology is thoroughly documented by Charles Dove (@charlieautomates), Corey Haines (coreyhaines31/marketingskills), and the broader Claude skills community.

**The core approach, as documented:**
1. Install the `coreyhaines31/marketingskills` pack (34 skills: copywriting, CRO, SEO, ad strategy, positioning, email sequences, and more) via `npx skills add coreyhaines31/marketingskills`
2. Combine with Claude's built-in `/frontend-design` skill for landing page generation
3. Generate a brand kit PDF (via fpdf2) that documents Avamed's colours, fonts, tone, and ICP
4. Lock the brand kit into CLAUDE.md so every session starts on-brand: `Always reference .claude/brand-kit.pdf before generating marketing copy`
5. Use a 5-skill pipeline for content automation: research → copywriting → repurposing → scheduling

**Avamed's adaptation:** The Strategy Agent should implement this methodology now, building the Avamed brand kit and marketing skill stack as described below. This makes every future content generation task on-brand, consistent, and agent-executable without Saeed re-explaining context.

---

### Capability 1: Landing Page Generation

**Agent can do autonomously:**
- Draft complete landing page copy (hero, problem, solution, social proof, pricing, CTA) using the `conversion-copywriter` skill and `landing-page-copywriter` skill from the marketing skills pack
- Generate HTML/React prototype using `/frontend-design` skill
- Apply Avamed brand kit (colours, tone, messaging) from .claude/brand-kit.pdf
- Draft 3 headline variants for A/B testing
- Write meta description and page title for SEO

**Requires Saeed sign-off:**
- Final copy approval before any public deployment
- Design approval (colours, imagery)
- Decision on website platform (currently no live website — this is a Phase 2 deliverable)

**Tool enabling it:**
- `npx skills add coreyhaines31/marketingskills` (install once in project)
- Claude's built-in `Write` tool for file creation
- `mcp__workspace__bash` for running fpdf2 brand kit generation

**Specific workflow:**
```
Agent prompt: "Using the marketing landing-page-copywriter skill and our brand kit 
at .claude/brand-kit.pdf, generate a complete landing page for app-avamed.uk 
targeting GP Practice Managers. Core message: AI phone intake that keeps data 
on-premise. Include: hero, 3 pain points, solution, how it works (3 steps), 
pilot reference, pricing teaser, CTA ('Book a 10-minute demo'). 
Output: HTML file to C:\JeffLocal\docs\marketing\landing-page-v1.html"
```

---

### Capability 2: LinkedIn Content Queue

**Agent can do autonomously:**
- Draft 4 weeks of LinkedIn posts (2 per week = 8 posts) based on the content calendar
- Research NHS statistics and recent primary care news to ground each post in current data
- Write in Saeed's voice (documented in brand kit as: direct, honest, non-corporate, founder-perspective)
- Format for LinkedIn: hook, body, hashtags, CTA
- Save to `docs/marketing/linkedin_queue/week-XX.md` for Saeed's review

**Requires Saeed sign-off:**
- All posts before publication — no exceptions (compliance constraint)
- Any post that references Churchtown, specific metrics, or clinical outcomes

**Tool enabling it:**
- `WebSearch` for current NHS data to ground posts
- `Write` for drafting and queueing posts
- Future: `sergebulaev/linkedin-skills` pack (LinkedIn-specific Claude Code skills)

**Specific workflow:**
```
Every Monday 07:00 (via scheduled task or session start):
Agent drafts 2 LinkedIn posts for that week, saves to 
docs/marketing/linkedin_queue/YYYY-MM-DD.md, flags in morning report:
"2 LinkedIn posts drafted and queued — review and publish when ready."
```

---

### Capability 3: Cold Email Sequences

**Agent can do autonomously:**
- Query NHS ODS API to build GP surgery lead list by geography (Python script via Bash tool)
- Enrich with practice name, email, patient list size, PCN affiliation
- Draft personalised email variants for each persona (Practice Manager, GP Partner, PCN Lead)
- Build sequences in Instantly.ai or Lemlist (when connected via API/MCP)
- Log all outreach in CRM (when HubSpot MCP is connected)

**Requires Saeed sign-off:**
- Final email copy before any send
- Confirmation that Churchtown pilot is ready to be referenced
- Approval of each outreach wave before it launches

**Tool enabling it:**
- `mcp__workspace__bash` for NHS ODS API query script
- `WebSearch` for practice research
- `coreyhaines31/marketingskills` email sequence skills
- Future: HubSpot MCP for CRM logging

**Specific workflow:**
```
Agent runs: python scripts/marketing/nhs_ods_pull.py --geography "Cheshire" --output docs/marketing/leads/cheshire_gp_list.csv
Agent personalises Email 1 for each practice using practice name + patient list size
Agent saves 3-email sequence per practice to docs/marketing/outreach/wave1/
Agent produces review summary: "Wave 1 ready: 45 practices, 3 email templates. 
Awaiting your approval before sending."
```

---

### Capability 4: Case Study Production

**Agent can do autonomously:**
- Maintain the case study template (already started in Sales & Marketing Pipeline doc)
- Auto-populate aggregate metrics from dashboard data (calls handled, time saved, pathways matched) when access is granted
- Format as professional PDF using the `pdf` skill
- Generate multiple variants: long-form (for download), 1-pager (for email), LinkedIn post version

**Requires Saeed sign-off:**
- All versions before any use — Churchtown consent gates this entirely
- Any specific data point from Churchtown must be approved by Churchtown practice

**Tool enabling it:**
- `pdf` skill (already installed)
- `docx` skill for Word version
- `mcp__workspace__bash` for data pull from dashboard SQLite

**Trigger:** This capability activates when Saeed confirms Churchtown consent is received. Agent then runs the full production pipeline in one session.

---

### Capability 5: NHS Tender Response Templates

**Agent can do autonomously:**
- Draft NHS SBS framework submission narrative sections (Lot 6: Operational Efficiency)
- Map JeffLocal features to framework evaluation criteria
- Draft G-Cloud service definition document
- Prepare DTAC self-assessment draft
- Write DSPT narrative responses for relevant questions
- Compile compliance evidence dossier

**Requires Saeed sign-off:**
- All financial declarations (company accounts, turnover)
- Director declarations and legal statements
- Final submission (agent prepares, Saeed submits)

**Tool enabling it:**
- `docx` and `pdf` skills for formatted submissions
- `WebSearch` for current framework requirements
- `mcp__workspace__bash` for generating structured documents

**IMMEDIATE ACTION:** Agent should begin drafting the NHS SBS framework response NOW given the 23 June 2026 deadline. This is a 23-day window.

---

### Capability 6: Brand Kit

**The Avamed brand kit should be generated and locked into CLAUDE.md immediately.** This is a one-time setup that makes all future marketing generation on-brand.

**Brand Kit Contents (Avamed/JeffLocal):**

```
AVAMED BRAND KIT — CLAUDE.md Reference Document

Company: Avamed | Product: JeffLocal
Domain: app-avamed.uk | Dashboard: dashboard.app-avamed.uk

COLOURS (proposed — Saeed to confirm):
- Primary: Deep NHS Blue (#003087) — builds NHS trust associations
- Secondary: Clean White (#FFFFFF)
- Accent: Warm Teal (#009B8D) — modern healthcare, less clinical than NHS blue
- Alert/CTA: Amber (#F5A623) — for buttons and CTAs
- Text: Near-black (#1A1A1A)

TYPOGRAPHY (proposed):
- Headings: Inter Bold or NHS-adjacent sans-serif
- Body: Inter Regular
- Code/data: JetBrains Mono

TONE OF VOICE:
- Direct. No buzzwords.
- Founder voice — honest about what we do and don't do
- "No patient data leaves the building" is the core safety message — lead with it
- Avoid: "revolutionary", "AI-powered" (overused), "transform" (overused in NHS)
- Use: "handles", "processes", "verified", "structured", "on your own hardware"
- Target reading age: Year 10 — Practice Managers are not technical

KEY MESSAGES (in order):
1. Patients call. Jeff handles intake. Staff get a verified task. Nobody types anything.
2. Everything runs on your own machine. No cloud. No data transfer. GDPR-clean by design.
3. Live at Churchtown Medical Centre, Southport. (when approved)
4. Book a 10-minute demo. No obligation.

ICP (Ideal Customer Profile):
- Practice Manager, NHS GP surgery, England
- Practice size: 5,000–15,000 registered patients
- Pain: reception team overwhelmed with call volume
- Fear: GDPR, patient complaints, anything that creates more admin
- Win: peer reference + free trial + on-premise data model

LOGO PATH: .claude/avamed-logo.png (add when created)
```

**Agent action:** Generate this brand kit as a PDF using fpdf2. Save to `.claude/brand-kit.pdf`. Add reference to CLAUDE.md. All subsequent marketing content generation references this file automatically.

---

### Capability 7: Press Release Template

**Agent can do autonomously:**
- Draft press release template (structure, boilerplate, spokesperson quote placeholders)
- Research named editors at Pulse Today, GPOnline, Digital Health
- Draft personalised pitch emails for each outlet
- Monitor media coverage of competitors and flag to Saeed

**Requires Saeed sign-off:**
- Final press release before any distribution
- Decision on exclusivity (one outlet gets it first)

**Specific workflow:**
Press release is drafted and saved to `docs/marketing/press/press-release-v1.md`. Triggered for send when Churchtown case study is approved.

---

### Capability 8: Demo Script

**A 15-minute JeffLocal demo for a GP Practice Manager should follow this structure:**

```
AVAMED JEFFLOCAL DEMO SCRIPT — 15 MINUTES

MINUTES 0–2: SET THE SCENE
- "Let me show you what happens when a patient calls your surgery right now."
- Describe the current state: phone rings, receptionist picks up, asks for name, 
  date of birth, reason for call, types notes, works out pathway, creates task.
- "That takes 3–5 minutes per call, 150 times a day."

MINUTES 2–5: THE JEFF EXPERIENCE (live or recorded demo)
- Trigger a simulated patient call to the demo dashboard
- Show Jeff's voice intake: greeting, patient reason capture, safety screening
- Show patient verification against practice register (matched)
- Show the structured task appearing on the reception dashboard in real-time
- "Jeff did all of that in under 90 seconds. Nothing was typed. No patient data 
  left this machine."

MINUTES 5–8: THE DASHBOARD
- Show the task queue: verified patient, reason code, pathway, priority flag
- Show the audit trail: what Jeff captured, when, what was verified
- Show the safety rules: what Jeff escalates immediately (chest pain, suicidal 
  ideation flags → immediate alert)
- "Staff still make all the decisions. Jeff just removes the intake burden."

MINUTES 8–10: DATA SAFETY DEEP DIVE
(This is what Practice Managers will push hardest on)
- "Show me where the data goes."
- Point to the machine: "It's here. Nowhere else."
- Show the architecture diagram (one slide): Jeff → n8n (local) → Ollama (local) 
  → dashboard (local) → reception staff
- "No cloud API. No data transfer. No AWS, no Azure, no Google. 
  Your patients' data never leaves the room."

MINUTES 10–12: RESULTS / PILOT
- Reference Churchtown pilot (when approved): "We're live at one surgery in 
  Southport. They were handling X calls/day. Jeff now handles the intake layer 
  on Y% of them."
- Show time saved calculation: "If your practice handles 150 calls/day and Jeff 
  handles 70% of intake, that's X hours of reception time per week returned."

MINUTES 12–14: PRICING AND NEXT STEPS
- "We offer a 30-day free trial. Nothing to sign, nothing to pay."
- "After that, it's £299/month. One invoice, no per-call charges."
- "You can cancel any time in the first three months."

MINUTE 14–15: QUESTIONS
- Expected: "What about EMIS integration?" → "CSV-based matching now; EMIS 
  integration is on our roadmap."
- Expected: "What if Jeff gets it wrong?" → "Every Jeff output is verified by 
  deterministic rules before it reaches staff. Staff see the task and confirm. 
  Jeff can't override a human."
- Expected: "What about CQC?" → "Jeff is an admin intake tool. Clinical decisions 
  are made by staff. CQC's position on AI admin tools is documented — happy to 
  share."
```

---

## SECTION 6: 30/60/90 DAY MONETIZATION SPRINT

### Context
- Day 0 = the date Saeed confirms Phase 1 technical blockers are resolved and commercial activity can begin
- Given current PROJECT_MEMORY.md status, Day 0 is likely mid-June 2026 (after n8n→DB pipeline gap is fixed and Saeed's governance gates are addressed)
- **Exception:** NHS SBS framework deadline is 23 June 2026 — this must start NOW, regardless of Phase 1 status

---

### IMMEDIATE (Before Day 0) — Agent Does Now

| # | Action | Owner | Deliverable | Gate |
|---|---|---|---|---|
| I.1 | Register on Ariba Network (supplier.ariba.com) | **SAEED NOW** | Ariba account active | None — 23 June deadline |
| I.2 | Download NHS SBS tender docs (find-tender.service.gov.uk Notice 043057-2026) | Strategy Agent | Tender pack in docs/procurement/ | None |
| I.3 | Map JeffLocal to SBS Lot 6 (Operational Efficiency) criteria | Strategy Agent | Mapping document | None |
| I.4 | Draft SBS narrative sections for Saeed review | Strategy Agent | Draft submission in docs/procurement/sbs/ | Saeed to review + finalise |
| I.5 | Generate Avamed brand kit PDF and lock into CLAUDE.md | Strategy Agent | .claude/brand-kit.pdf | Saeed confirms brand colours |
| I.6 | Install marketing skills pack (coreyhaines31/marketingskills) | Strategy Agent | Skills loaded in session | None |

---

### DAYS 1–30: Foundation Sprint

**Agent-Executable (no Saeed needed)**

| # | Action | Deliverable |
|---|---|---|
| 1.1 | NHS ODS API script: pull all GP surgeries in Cheshire & Merseyside + Greater Manchester | CSV: 650 practices with name, email, list size, PCN |
| 1.2 | Identify Churchtown's PCN from NHS.uk + PCN Clinical Director name | Research note |
| 1.3 | Research C&M ICB digital leadership team — names, emails, LinkedIn | ICB contacts note |
| 1.4 | Draft 3-email outreach sequence (Practice Manager persona) | 3 email templates |
| 1.5 | Draft 4 LinkedIn posts (2 weeks of content) | Post queue: docs/marketing/linkedin/ |
| 1.6 | Draft landing page copy (hero through CTA) using marketing skills | landing-page-v1.html |
| 1.7 | Draft press release template (structure + placeholder quotes) | press-release-template.md |
| 1.8 | Draft Commissioner Briefing (2-page ICB pitch document) | commissioner-brief-v1.docx |
| 1.9 | Draft DTAC self-assessment (framework completed, gaps flagged) | dtac-draft.md |
| 1.10 | Draft demo script (per Section 5.8) and 10-slide deck | demo-script.md + demo-deck.pptx |

**Saeed Action Required**

| # | Action | Why Saeed |
|---|---|---|
| S.1 | Confirm brand colours/fonts for brand kit | Aesthetic/brand decision |
| S.2 | Approve email outreach sequence before any send | External content approval protocol |
| S.3 | Set up HubSpot free CRM account | Requires Saeed login/account |
| S.4 | Set up Calendly with demo booking link | Requires Saeed calendar access |
| S.5 | Send reference request to Churchtown Practice Manager | Relationship — must come from Saeed personally |
| S.6 | Submit NHS SBS tender (after agent drafts, Saeed finalises and submits) | Director declaration + legal sign-off |

**Technical Prerequisite**

- Phase 1 E2E pipeline (n8n→DB) must be working before any demo can be offered
- Churchtown pilot must be stable before referencing in any outreach

---

### DAYS 31–60: First Outreach Wave

**Agent-Executable**

| # | Action | Deliverable |
|---|---|---|
| 2.1 | Send Wave 1 email sequence to 20 practices (post-approval) | 20 sequences live |
| 2.2 | Draft Week 3–4 LinkedIn posts | 4 posts queued |
| 2.3 | Research Pulse Today and Digital Health editor names/coverage | Media contact list |
| 2.4 | CRM update: log Wave 1 engagement signals | Pipeline stage updates |
| 2.5 | Draft Wave 2 email sequence (50 practices) | Templates ready for Saeed approval |
| 2.6 | Research RCGP 2026 innovation showcase application | Research note + application if relevant |
| 2.7 | Draft LMC newsletter notice for Cheshire & Merseyside LMC | 150-word notice for Saeed |
| 2.8 | Draft DSPT self-assessment framework | DSPT-draft.md |

**Saeed Action Required**

| # | Action |
|---|---|
| S.7 | Publish LinkedIn posts 1–4 (drafted by agent) |
| S.8 | Reply personally to any Stage 3 engaged leads (agent flags immediately) |
| S.9 | Approach Cheshire & Merseyside ICB Digital Lead (agent drafts email) |
| S.10 | Approve Wave 2 email sequence before send |

---

### DAYS 61–90: Pipeline Acceleration

**Agent-Executable**

| # | Action | Deliverable |
|---|---|---|
| 3.1 | Wave 2 email sequences (50 practices) — send + track | 50 sequences live |
| 3.2 | Draft 4 more LinkedIn posts (Weeks 5–6) | Posts queued |
| 3.3 | Case study template ready (skeleton, no data yet) | case-study-template.docx |
| 3.4 | Compile 90-day pipeline report: contacts, stages, engagement, warm leads | Report in docs/reports/ |
| 3.5 | Research PCN Plus Live event (April 2027) — costs, format, application | Research note |
| 3.6 | Draft PCN one-pager for Churchtown PCN Clinical Director | pcn-onepager-v1.docx |
| 3.7 | Wave 3 (100 practices) — prep list and sequence | Ready for Saeed approval |

**Saeed Action Required**

| # | Action |
|---|---|
| S.11 | Conduct demo calls with any Stage 4 leads (agent prepares briefing for each) |
| S.12 | Submit Churchtown reference request (if not done in Day 1–30) |
| S.13 | Attend at least one NHS event as delegate (HETT September 2026 recommended) |
| S.14 | Review 90-day pipeline report and confirm Phase 2 scope |

---

## SECTION 7: PLUGIN / MCP / SKILL STACK FOR AUTONOMOUS MARKETING

### The Full Stack (prioritised)

---

**PRIORITY 1 — Install today (free, immediate impact)**

**1. coreyhaines31/marketingskills**
- What: 34 marketing skills for Claude Code — copywriting, CRO, SEO, ad strategy, email sequences, positioning, growth engineering
- Cost: Free (open-source, GitHub)
- Install: `npx skills add coreyhaines31/marketingskills`
- Enables: All copy generation, landing pages, email sequences, case study writing
- Marketing function: Replaces a copywriter and content strategist for internal drafts

**2. Avamed Brand Kit (generate now with fpdf2)**
- What: PDF document codifying Avamed colours, fonts, tone of voice, ICP, key messages
- Cost: Free (fpdf2 is Python library)
- Install: `pip install fpdf2 --break-system-packages`, run brand kit generation script
- Enables: All agent-generated marketing content stays on-brand without re-briefing
- Marketing function: Brand consistency across all touchpoints — no "AI slop" generic outputs

**3. Claude Built-in `/frontend-design` Skill**
- What: Forces design-first thinking before code; eliminates generic layouts
- Cost: Free (built into Claude Code)
- Enables: Landing page HTML generation with distinctive visual direction
- Marketing function: Landing page prototyping in one session

---

**PRIORITY 2 — Connect in Phase 2 (moderate cost, high leverage)**

**4. HubSpot MCP**
- What: Read/write CRM contacts, deals, pipeline stages, email tracking
- Cost: HubSpot free tier (unlimited contacts); MCP server is open-source
- Install: Search MCP registry for "HubSpot"; configure with HubSpot API key
- Enables: Agent updates CRM after every interaction; generates pipeline reports; flags warm leads in morning report
- Marketing function: Full CRM automation without Saeed logging in

**5. Calendly (API integration)**
- What: Booking link for demo scheduling; webhook when new booking made
- Cost: Free for single event type
- Enables: Agent monitors bookings, triggers pre-demo briefing send, updates CRM
- Marketing function: Converts interest → demo booking without human scheduling overhead

**6. Instantly.ai or Lemlist**
- What: Cold email sequence sending and tracking at scale
- Cost: Instantly.ai from ~£30/month; Lemlist from ~£39/month
- Enables: Agent queues approved sequences, system sends at scale, tracks opens/clicks/replies
- Marketing function: Outreach at 100+ practices without manual sending

---

**PRIORITY 3 — Phase 3 / advanced (for scale)**

**7. sergebulaev/linkedin-skills**
- What: LinkedIn-specific Claude Code skills — post writing, comment generation, feed analysis
- Cost: Free (GitHub)
- Install: `npx skills add sergebulaev/linkedin-skills`
- Enables: LinkedIn posts written in authentic founder voice; comment monitoring for warm signals
- Marketing function: LinkedIn organic growth without Saeed writing from scratch

**8. Gmail MCP (Google Workspace)**
- What: Read Saeed's inbox for prospect replies; flag warm responses in morning report
- Cost: Free (Google Workspace MCP, official)
- Enables: Agent monitors for prospect replies overnight; surfaces warm leads in daily briefing
- Marketing function: No warm lead goes cold because Saeed missed an email
- Note: Requires careful scope limitation — access to marketing threads only, not full inbox

**9. cognyai/claude-code-marketing-skills**
- What: SEO audits, ad analysis, ad optimisation — live Search Console and LinkedIn data
- Cost: $9/month for live data integrations
- Enables: SEO-optimised landing page content; ad performance analysis when running paid campaigns
- Marketing function: Phase 3 when budget exists for paid acquisition

---

### Top 3 Highest-Immediate-Impact Tools

1. **coreyhaines31/marketingskills** — install in the next session. Immediately enables landing page copy, email sequences, case study writing, and positioning work. Zero cost. 10-minute setup.

2. **Avamed Brand Kit (fpdf2)** — generate in the next session. Locks in brand context permanently. Every subsequent marketing asset is consistent without re-briefing. Zero cost.

3. **HubSpot MCP (Phase 2)** — the moment outreach begins, CRM becomes essential. Without it, Saeed is manually logging contacts. With it, the agent manages the full pipeline. Free tier + MCP = full pipeline automation.

---

## DOCUMENT METADATA

```
Document:       Avamed_Monetization_Plan.md
Status:         Research-backed draft — internal use only
Created:        2026-05-31
Research basis: Live NHS, competitor, and procurement data (sourced May 2026)
Sources:        NHS Digital, RCGP, BMA, Digital Health, iatrox.com, herohealthsoftware.net,
                find-tender.service.gov.uk, Cheshire & Merseyside ICB, NHS SBS,
                digitalhealth.net, MindStudio, MCP Market, charlieautomates.com
Review trigger: Before any external communication; before NHS SBS submission;
                when Churchtown case study is approved; when first paid customer signs
Next update:    End of Week 1 of monetization sprint (after NHS SBS submission)
Owner:          Strategy Agent
```

---

*This document supersedes informal pricing and procurement notes in Avamed_Sales_Marketing_Pipeline.md. Both documents should be cross-referenced — this document provides the financial model and procurement roadmap; the Sales & Marketing Pipeline provides the operational channel detail and outreach templates.*
