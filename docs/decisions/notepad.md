# Decision Notepad — Lexo Trading Assignment

Append-only discussion log. Turn-numbered. Never rewritten, never reordered.

**What this file is:** the *why*. Decisions, rejected options, open questions.
**What this file is NOT:** the task checklist. That lives in `TODO.md` (one flat
list, `[ ]` / `[o]` / `[x]`, per CLAUDE.md Module 7). The final handover to the
implementor session is a spec under `docs/specs/`.

**Status:** discussion phase. No implementation this session.

---

## Turn 1 — 2026-09-23 — Framing

### Inputs located

`/home/lap-68/Downloads/Shared-Public-20260923T050713Z-1-001/Shared-Public/`

- `Problem Statement.docx`
- `Reports/{AMZN,NVDA,CSCO}/` — each: memo + theme report + factor report

| Company | memo | theme | factor |
|---|---|---|---|
| AMZN | 67p | 16p | 58p |
| NVDA | 92p | 34p | 157p |
| CSCO | 89p | 34p | 89p |

### The brief, in one line

Turn the research artifacts into a **deterministic decision system that shows its
reasoning**, deployed at a URL.

A stranger opening the app must be able to answer three questions unaided:
1. What does the research actually conclude?
2. What rules were derived from it, and where did each one come from?
3. What would the system do, when, and why?

Hard requirements from the brief:
- Rules are **derived, not invented** — each traces to a specific claim in the source docs. Anything invented must be labelled as such in the UI.
- Decides **over time**, not once: hold / size / stop.
- At least **two divergent futures**; at least one must turn on something that is **not a price** (disclosure, guidance change, third-party event).
- **Determinism** — same inputs, same decisions, and *show that it holds*.
- **Explainability** — any point in time, in terms a non-engineer follows.
- **Tests on the decision logic specifically.**
- **Deployed, reachable at a URL.**

Declared out of scope by the brief: PDF parsing (hand-transcribe into fixtures),
live market data, broker/order integration, auth/multi-user, serious backtesting,
machine learning, native/mobile apps.

### Discrepancy noted

Brief says "one memo (~90p), one theme report, **two** factor reports." No company
in the folder has two factor reports. Read as: the set is a *choice of one company*,
not a combined corpus.

### Decisions this turn

- **D1 — Scope: NVDA only.** 92p memo is the closest match to the brief's
  "roughly 90 pages", and it carries the richest factor report (157p). One company
  done properly beats three done shallowly. AMZN and CSCO are not in scope.

### Open questions carried to Turn 2

- **Q1 — ML allowed?** The written brief lists machine learning as out of scope and
  demands provable determinism. User reports that on a call it was said to everyone
  that "any method of choice" is fine. User is generating a transcript of that call
  for review. **Blocking** — it materially changes the architecture.
- **Q2 — What does "efficiency of the report" mean as the grading bar?** Same
  source: pending the call transcript.

### Rejected / not chosen

- Building for all three companies — transcription cost is high and the brief
  explicitly says not to spend time there.

### Conflict surfaced (CLAUDE.md)

Module 7 mandates a single tracking file, `TODO.md`. User asked for a checklist
inside this notepad. Resolution proposed and accepted in principle: this notepad
carries discussion and decisions only; the working checklist stays in `TODO.md`.
Rationale — a checklist living in two files drifts, and the implementor session
then has no single source of truth.

### Next turn

Read the call transcript. Resolve Q1 and Q2. Only then start reading the NVDA
artifacts — the ML answer changes what we're even looking for in them.

---

## Turn 2 — 2026-09-23 — Call transcript reviewed; Q1 and Q2 resolved

Source: Slack auto-transcript of the kickoff call. ~8 participants — 4 client side
(Vikram, Jagadesh, + 2), 4 external developers being evaluated (incl. us, Tilman,
Abhishek, Raja). Multi-speaker ASR, so attribution is inferred from context and is
not perfectly reliable; the substantive quotes below are unambiguous.

### Who is in the room (and what each one wants)

- **Jagadesh** — technical lead, built the research platform over ~1 year and built
  the sample demo. Cares about: the rule engine, converting memo prose to rules,
  detecting when a rule has triggered, event propagation across tickers.
- **Vikram** — the partner / decision maker. Repeatedly *loosens* Jagadesh's
  constraints ("let's not make that a hard requirement", "I don't want to impede on
  your own creativity"). Cares about: thought process, philosophy fit, evidence of
  AI-native working, and "where it is going".

Both are in the room. A submission that serves only one of them loses.

### Q1 — RESOLVED: is ML allowed?

Asked directly on the call ("are you looking for a principled machine learning
approach or algorithm to weigh those paths"). Answer:

> "you're not gonna flesh out the full machine learning algorithm [in the time
> box], but it gives you kind of the potential... we're leaving it open-ended to
> show the seeds or the fruits of your capabilities"

**Resolution: ML is permitted and is the stated direction of travel, but is
explicitly NOT expected to be built.** The operative word used repeatedly is
*seeds*. This does not overturn the written brief's determinism requirement — it
sits above it.

### Q2 — RESOLVED: what is the grading bar?

> Jagadesh: "it's not a hard bound rule that I have. I'm more excited to see what
> you guys can come up with instead of me putting certain criteria."

> Vikram: "it's not going to be purely technical... if there's a lot of thinking
> that went into it, where what you're showing is just the seeds of that thinking,
> think of a creative way using AI to flesh out your thought process"

> Vikram: "where it is going should be easily able to be seen by us"

> Vikram: "part of this too is just showing us what you've learned from using AI"

**Resolution: there is no rubric. The bar is visible thinking + demonstrated
direction + evidence of AI-native execution.** Not a finished product. Deliverable
may be code, product, seeds of either, plus a written explanation of where it goes
next. The explanation is graded, not just tolerated.

### The single hard constraint stated on the call

> "the most fundamental constraint is that it should be hooked into and based on
> the research, not just a blank sheet of paper."

This matches the written brief's "rules are derived, not invented".

### Other substantive statements from the call

- **Multi-ticker fan-out is explicitly confirmed.** Asked whether factor-level
  triggers should be global state re-rating multiple positions: *"yes... not
  necessarily one ticker. It can trigger buy or sell recommendation for multiple
  tickers in the portfolio."* Vikram: *"any event that can affect Nvidia can
  potentially affect 100 other companies."*
- **Rules vs heuristics is deliberately open.** *"think of it as heuristics on one
  end, hard rules on another. I don't care how you treat it, but either direction
  you take is indicative of something."* Hard-rule camp → output must be more
  refined and specific. Heuristic camp → output more flexible. *"Our platform
  supports both."*
- **Human in the loop is Vikram's stated philosophy.** *"If we ultimately get to
  fully automated trading, that's kind of a nice to have. But I fundamentally
  believe human in the loop can be value added."* The differentiation they are
  trying to prove is *trading based on fundamental research*, vs. the "thousands of
  people building their own trading applications".
- **Broker integration explicitly de-prioritised.** *"I wouldn't focus more on
  connecting to any trading application... spend more time on the core application.
  How do we create the rule engine? How do we identify when a particular rule has
  been [triggered]."* Mock is acceptable if wanted.
- **Manual rule entry wanted, then softened.** Jagadesh: *"we need a way to set
  rules manually as well"* — Vikram immediately: *"let's not make that a hard
  requirement."*
- **Probability-weighted paths are the core intellectual ask.** *"project different
  possibilities, different paths, the implications on Nvidia stock price... track
  those paths simultaneously, and as the future starts becoming realised... our
  decisions on whether we sell, buy more, or just hold might get affected."* And:
  *"the stock price today needs to account for the weighted probability of those
  different paths based on the price you're willing to pay."* This is richer than
  the written brief's "simulate at least two divergent futures".
- **Equity only for now.** Factors/themes reports are broader than NVDA by design.
- **The bar to beat (Jagadesh's demo).** Rules extracted from the memo; two
  branches — thesis holds → existing holder gets X return; thesis breaks → incur
  loss. Described by its author as "very preliminary". This is the reference point,
  explicitly framed as "not a template".

### The non-price trigger, handed to us verbatim

The written brief requires at least one divergent future turning on something that
is not a price. Jagadesh narrated the exact one:

> "Hyperscaler capex deceleration. Roughly half of the data center revenue is four
> customers. Any [hyperscaler] guiding capex flat or down in the late January 2027
> window, or FY2028 guidance below 45 — that is the exit."

Dated, disclosure-driven, sourced to the memo, and spoken aloud by a reviewer.
**Decision: this is our primary non-price trigger.** Using it proves both sources
were read. (Exact figures to be verified against the memo text — ASR may have
mangled "45" / "450B".)

### Decisions this turn

- **D2 — Written brief is the floor, the call is the ceiling.** Meet every written
  requirement literally (determinism, provenance, two futures, tests, deployed
  URL), because those are the only checkable items and the brief says "show us that
  it holds". Spend the call's latitude on the layer above. Rationale: candidates who
  read only the brief ship a rigid toy; candidates who only heard the call ship a
  vague AI demo.
- **D3 — Deterministic core, ML marked not built.** Runtime decision path stays
  fully deterministic and replayable. The probabilistic/learned layer is shown as a
  labelled seam in the product ("this weight is a fixed prior from memo p.X; here is
  the estimator that would replace it"). This satisfies the written brief's
  determinism proof AND the call's "show the potential" simultaneously. The two
  requirements are not in conflict once separated by tier.
- **D4 — Serve both evaluators explicitly.** Jagadesh's bar: engine quality, event→
  rule matching, fan-out. Vikram's bar: thinking, philosophy fit, direction. The
  written explanation is a first-class deliverable, not a README afterthought.
- **D5 — Human in the loop, not autotrader.** Anything above the deterministic rule
  tier is *proposed* to a human and requires acceptance; proposal and decision both
  logged. Aligns with the decision maker's stated philosophy, and inverts what
  "trading application" pattern-matches to.
- **D6 — AMENDS D1.** Scope is no longer strictly NVDA-only. NVDA remains the deep
  position (full memo + theme + factor transcription). Add ONE secondary ticker as
  thin fixtures, solely to demonstrate factor fan-out. Candidate: **AMZN** — it is
  one of the four hyperscalers the NVDA thesis depends on, so a capex-cut event is
  bearish NVDA while being non-obviously (possibly favourably) directional for AMZN.
  That asymmetry is precisely the "different paths, different implications" Vikram
  spent five minutes on. Rationale for amending D1: fan-out was explicitly requested
  on the call and cannot be demonstrated with one ticker. **Pending user
  confirmation.**

### Candidate differentiators, ranked by (signal to evaluators / cost)

1. **Provenance as a first-class object** — rule ↔ source claim is bidirectional and
   clickable down to the sentence. Most checkable requirement in the brief, cheapest
   to nail, and most will settle for a footnote.
2. **The hyperscaler-capex non-price trigger** — handed to us verbatim on the call.
3. **Factor fan-out across tickers** — explicitly requested, almost certainly absent
   from other submissions.
4. **Human-in-the-loop framing** — matches the decision maker's stated philosophy;
   inverts the obvious interpretation.
5. **Determinism demonstrated, not claimed** — a replay control + a test that runs
   the same timeline twice and diffs the decision log. "Show us that it holds" is an
   instruction to build a demonstration.
6. **The ML seam, marked in the product** — answers on-screen the exact question
   Tilman asked on the call.

### Open questions carried to Turn 3

- **Q3 — The three Telegram links.** Call: *"there are 3 links in the Telegram
  channel. So those 3 are the basis for whatever you guys come up with."* We have
  the Drive folder and the problem statement. Jagadesh's sample app link was pasted
  in-thread. Do we have all three? Seeing his demo sets the bar to beat.
- **Q4 — Fan-out scope**: confirm D6.
- **Q5 — Timeline reality**: call said "end of day Friday". Call date unknown.
  User has said time is not the priority, but pre- vs post-deadline changes posture.
- **Q6 — Stack and deployment target.** "Deployed, reachable at a URL" is a hard
  written requirement.

### Next turn

Resolve Q3–Q6, then begin reading the NVDA memo with a specific extraction target:
verdict/classification, the two scenario tables, the factor set with weights, risks
with watch-signals, the execution plan (entry/exit/stop/horizon), and the dated
catalyst calendar. The brief enumerates these, so they are known to exist.

---

## Turn 3 — 2026-09-23 — Q3–Q6 resolved; NVDA + AMZN source read

### Q3 — RESOLVED: the three Telegram links

1. Problem statement, 2. Drive folder (3 companies' reports), 3. Zoom recording.
**There is no separate demo-app link among the three.** Jagadesh pasted his sample
app in-thread during the call; it is not part of the shared starting point and we
do not have it. Proceeding without sight of it. Minor upside: no risk of anchoring
on his two-branch shape.

### Q4 — RESOLVED: D6 confirmed. NVDA deep + AMZN thin.

### Q5 — RESOLVED: deadline is Friday 2026-09-25. Today is Wednesday 2026-09-23.

~2.5 days. User's earlier "time is not important" and this answer are in mild
tension; working read is **real Friday target, quality wins on conflict**. The call
explicitly blesses shipping seeds plus a written direction, so scope discipline is
sanctioned by the client, not a compromise.

### Q6 — RESOLVED: Python engine + thin web UI.

### Local environment (verified, not recalled)

Python 3.13.11 (pyenv) · `uv` present · Node 24.18.0 / npm 11.16.0 · git 2.43.0 ·
`pdftotext` + `pdfinfo` present · PyMuPDF 1.27.2.3 present · Docker present.
No flyctl / render / vercel CLI (not needed — git-push deploys).
Project dir currently holds only `CLAUDE.md` + empty `README.md`. **Not a git repo
yet.** No venv, no dependencies installed.

### Source extraction

`pdftotext -layout` into the session scratchpad. NVDA memo 5,821 lines / 353KB;
factor 9,608 / 606KB; theme 2,350 / 154KB; AMZN memo 3,883 / 233KB. Text quality is
good — tables survive with `-layout`. **This is for reading only.** The brief puts
PDF parsing out of scope; fixtures get hand-transcribed.

### NVDA memo — verified decision core (quotes verified against source text)

As-of 2026-09-08. Reference price **$230.36** (2026-09-04 close, re-confirmed
2026-09-08).

- **Verdict (3–5yr intrinsic):** Diamond in Air | Ocean | Luminous — N-of-1, 83/100,
  multibagger gate BORDERLINE. Trajectory Bull 25% · Base 50% · Bear 25%
  (bear = 15% competitive + 10% geopolitical).
- **Trading stance (6–12mo tactical):** Hold · Low conviction · no position
  initiated. PWR −13.1% modelled, −9.7% with the $195.00 stop applied.
- **Intrinsic scenarios:** Bear $78.83 (−65.8%) · Base $139.24 (−39.6%) · Bull
  $189.80 (−17.6%) · Prob-weighted $136.78 (−40.6%). Even the bull is below price.
- **12-month price targets:** Bull $236.54 (+2.7%) · Base $200.09 (−13.1%) · Bear
  $164.07 (−28.8%). Weighted −13.1%; −9.7% with the stop.
- **Root disagreement:** FY2028 revenue $474,927M (26.8% growth) vs consensus
  $681,500M vs management guided ~70%. "The bet is against company guidance, not
  market exuberance."

### The state machine, as written in the memo's Execution Plan + "Three Dates"

| Date | Trigger | Transition |
|---|---|---|
| 2026-11-17 (confirmed) | FY2028 commentary near 70% **with backlog detail** | → Buy, **full** weight (re-entry trigger) |
| 2026-11-17 | commentary below 45% | → bear row |
| 2026-11-17 | neither confirms nor breaks | → base row, drift to $200.09 |
| 2027-01-26 → 2027-02-06 (est.) | **any two of the four** large hyperscalers guiding capex flat or down YoY | → exit / short trigger |
| ~2027-02-24 (est.) | formal FY2028 guide **below 45% growth** | → Sell |
| continuous | $195.00 on **two consecutive weekly closes** | → stop. **Existing holders only.** |

Other Execution Plan fields: Spring state **Neutral**; platform rule for Neutral =
starter position — **deliberately overridden**; horizon 6–12 months tactical.

**Correction to the ASR transcript.** The call rendered the exit trigger as "any
[hyperscaler]... below 45". The memo says **"any two"** of four, and **45% is a
growth rate**, not $450B. Fixtures follow the memo, not the transcript.

### Three findings that shape the architecture

**F1 — The memo is already a deterministic state machine written in prose.** We are
not deriving rules by interpretation; we are transcribing dated triggers that the
research already states with metric, threshold and timeframe. This makes the
brief's "rules are derived, not invented" cheap to satisfy honestly, and makes
provenance exact rather than approximate.

**F2 — The memo documents an override of its own platform rule, with reasons.**
Spring state Neutral → platform entry logic says starter position → the memo
declines it: *"Opening length into that distribution would be following a rule
against the analysis the rule exists to serve. A Hold means hold."* An engine that
can only express `rule fires → action` **cannot represent this memo**. The engine
must model override as a first-class, logged, attributable event. This simultaneously
serves (a) fidelity to the source, (b) Vikram's stated human-in-the-loop philosophy,
and (c) the explainability requirement. High confidence other submissions miss it.

**F3 — The memo names a rule whose parameters are explicitly absent from the
source.** On hedging: IV rank 0–9 of 100 → hedge existing exposure through the
2026-11-17 print and the late-Feb 2027 window — but *"no strike, expiry or premium
is named anywhere here: no options chain was sourced for this workbook, so the
instruction is the window and the volatility condition and nothing finer."* The
written brief requires: *"If you add [a rule] that does not [trace to source], say
so in the interface."* This is a real, non-contrived instance, where the source
itself declares the gap. Better evidence of the provenance discipline than any
invented example.

Also to honour: the memo insists the −40.6% intrinsic gap and the −13.1% 12-month
return are *"different measures on different clocks and neither substitutes for the
other."* Any UI collapsing them to one number contradicts its own source. **Two
horizons must be represented separately.**

Other constraints the memo states about itself, worth surfacing rather than hiding:
- The −13.1% weighted return is *"biased downward and should be read as a floor,
  not a point estimate"* (12-month targets are observed price levels, so upside is
  truncated at the 52-week high by construction).
- The 10% geopolitical bear route *is not modelled as a cash-flow path*; the full
  25% bear weight sits on the competitive route's $78.83.
- No Steelman and no Market-Implied scenario exists upstream, *"which is why this
  table can state the disagreement but cannot adjudicate it."*

### Factor architecture — the fan-out mechanism is in the source data

NVDA carries **28 factors**: 10 positive · 13 negative · 5 other. Two orthogonal
classifications, both present:

- **Force type** — Winds (temporary, 1–4 quarters) · Waves (secular, multi-year) ·
  Mud (structural drag). Each factor also carries an **IMPACT score 0–1**.
- **Light Cone ring** — **Internal** (1–10, NVDA-specific) · **Sector** (11–17) ·
  **Market** (18–28).

**Sector and market factors are ticker-agnostic by construction.** That is exactly
the "global state variables that re-rate multiple positions" capability Jagadesh
confirmed on the call — and we read it off the ring assignment rather than
inventing a propagation model.

Selected NVDA weights (of 100 points): Guidance Bet 21 · Share Ceded to Custom
Silicon 20 · Rack-Scale Platform Lock-In 17 · Demand Is Credit-Funded 13 ·
Founder-Led / Unplanned Succession 8 · Operating Leverage Already Spent 5.
*"Three factors sit on the external circle and together carry 54 of the 100 weight
points."*

**Four Kill Switches** (separate from the weighted factor set, with watch cadence):
frontier training run on non-NVIDIA silicon (continuous, 2027–28) · networking
attach convergence for 2 consecutive quarters (quarterly, 2027) · Taiwan Strait
interruption (unhedgeable pre-2028 Arizona mass production) · cash conversion below
65% unadjusted / 78% adjusted for 2 consecutive quarters with accruals above 20%
(current 69.7% / ~83.6% / 18.3%). Note the recurring **two-consecutive-period
confirmation** pattern — same shape as the stop. Worth a shared primitive.

### F4 — The AMZN fan-out is real and carries OPPOSITE sign

Verified by reading both memos' factor lists:

| Real-world mechanism | NVDA | AMZN |
|---|---|---|
| Hyperscalers building own silicon | #5 Inference Share Loss to Custom Silicon — **Wave −** | #2 Custom Silicon Margin Moat — **Wave +** |
| AI infrastructure buildout | #11 AI Infrastructure Buildout Wave — Wave + (Sector) | #12 AI Infrastructure Demand Wave — Wave + (Sector) |
| Capex funded by credit | #16 Hyperscaler Capex Turns Debt-Funded — **Wave −** | #24 Open Credit Funding AI Cloud Customers — **Tailwind (Market)** |
| Capex level itself | demand driver (bullish while high) | #6 AI Capex Cash Drain — **Wave − (Internal)**; #28 Accelerated Depreciation Shielding Capex Cash Taxes — Tailwind |

AMZN context: *"US hyperscalers plan about $725B of 2026 capex (+77% YoY)"*; AMZN
2026 capex ~$220B = 1.36x TTM operating cash flow of $161.4B, FCF negative.

**Consequence:** a single "hyperscaler shifts spend to in-house silicon / cuts
capex" event is bearish NVDA and *ambiguous-to-bullish* AMZN (it relieves the AI
Capex Cash Drain while signalling cloud demand softening). Both readings are
sourced to the respective memos. Nothing invented.

**Decision — D7: this asymmetry is the headline demo.** It satisfies, in one screen:
Jagadesh's explicit multi-ticker fan-out ask; Vikram's "different paths, different
implications"; the brief's non-price divergent future; and "derived, not invented".

### The two divergent futures (both non-price driven)

The brief requires ≥2 divergent futures, ≥1 turning on something that is not a
price. Both of ours are disclosure-driven, and both are dated in the source:

- **Future A — "Guide Holds".** 2026-11-17: FY2028 commentary near 70% with backlog
  detail → re-entry trigger → Buy at full weight. Driver: a company disclosure.
- **Future B — "Capex Turns".** 2026-11-17 ambiguous → base drift to $200.09;
  2027-01-26→02-06: two of four hyperscalers guide capex flat/down → exit. Driver:
  *third-party* disclosures from companies that are not the issuer. Possible $195.00
  two-weekly-close stop en route.

Candidate third path — the geopolitical route. The memo carries it at 10% weight
and explicitly *declines to model it as a cash-flow path*. Including it as a
visibly-unmodelled path would be another honest-provenance win. **Stretch, not
committed.**

### Decisions this turn

- **D7 — NVDA/AMZN opposite-sign factor asymmetry is the headline demo.** (above)
- **D8 — Two-consecutive-period confirmation is a shared engine primitive**, not
  special-cased on the stop. It appears on the $195 stop and on two of four kill
  switches. Source-driven, not speculative generalisation.
- **D9 — Two horizons are modelled separately** (3–5yr intrinsic vs 6–12mo
  tactical) and never collapsed. The memo explicitly forbids conflating them.

### Open questions carried to Turn 4

- **Q7 — Architecture: hard-rule camp, heuristic camp, or tiered hybrid?** The call
  explicitly framed this as a choice that is "indicative of something". Options and
  recommendation to be presented for approval.
- **Q8 — How much of the 28-factor set gets transcribed?** Full 28 with weights, or
  the ~8 promoted / decision-relevant ones? Cost vs completeness.
- **Q9 — Deployment target** (Render / Fly / Hugging Face Spaces / other) — needs a
  public URL by Friday.

### Next turn

Present architecture options (Q7) for approval, then the fixture schema. No code
until the spec is approved.

---

## Turn 4 — 2026-09-24 — Q7–Q9 resolved; architecture fixed

### Time check — this changed materially

Today is **Thursday 2026-09-24**. Deadline is **Friday 2026-09-25**. One working
day, not the 2.5 assumed in Turn 3. Turns 1–3 consumed a day on discovery. Judged
worthwhile — F1/F2/F3/F4 (the override, the unsourced hedging rule, the opposite-sign
AMZN asymmetry) would have been expensive to discover mid-build — but scope is now
genuinely tight and both resolutions below are the cheaper option.

### Q9 — RESOLVED: deploy to Render free tier.

Git-push deploy, Python native, free, real public URL. Cold starts accepted — this
is a demo, not a service.

### Q7 — RESOLVED: tiered hybrid with the boundary made visible (option C).

Explained to and approved by the user in plain terms as "both, with a visible line
between them".

- **Tier 1 — hard rules.** The Execution Plan state machine. Deterministic,
  auto-applied, every decision citing a specific source sentence. Satisfies the
  written brief on its own.
- **Tier 2 — factor heuristics.** Sector/market factors as shared state. When one
  moves, affected positions are re-rated — but Tier 2 **never executes**. It emits a
  *proposal*; a human accepts or rejects; proposal and response are both logged.
  This is where the NVDA↓ / AMZN↑ fan-out lives.
- **Tier 3 — the ML seam, marked but not built.** Scenario weights are fixed priors
  (25/50/25, memo p.44). The UI states this and names what a learned estimator would
  replace.

Rejected, with reasons recorded:
- **Hard rules only** — ships safest but is Jagadesh's own demo plus provenance, and
  cannot demonstrate the fan-out he explicitly asked for on the call.
- **Heuristic scoring only** — breaks the brief's first requirement. A decision
  emerging from a weighted sum of 28 factors cannot be traced to one claim.
  Determinism survives; explainability does not.

### Q8 — RESOLVED: decision-driver subset, with the shortfall stated in the UI.

Transcribe the memo's own promoted/weighted factors (Guidance Bet 21, Share Ceded to
Custom Silicon 20, Rack-Scale Platform Lock-In 17, Demand Is Credit-Funded 13,
Founder-Led/Unplanned Succession 8, Operating Leverage Already Spent 5, + remaining
promoted) plus the 4 kill switches, plus the 3–4 AMZN counterparts needed for the
fan-out. The fixture schema is shaped for the full 28 from the start.

**The UI states "N of 28 factors transcribed" on screen, and says which are missing.**
This is not an apology — it mirrors what the memo does to itself when it admits no
options chain was sourced, and it is the same discipline the brief asks for when it
says to flag anything not traceable to source.

### Decisions this turn

- **D10 — Tiered hybrid architecture** (Q7 above). Tier 1 auto-applies; Tier 2
  proposes only and requires logged human acceptance; Tier 3 is a labelled seam.
- **D11 — Subset transcription with on-screen disclosure** (Q8 above). Schema
  supports all 28; UI reports actual coverage honestly.
- **D12 — Extracted PDF text lives in the repo, gitignored** — not in a session temp
  directory. The Turn 3 extraction was wiped by a session restart. One command to
  regenerate (`pdftotext -layout`), but the implementor should not lose it twice.

### Open questions carried to Turn 5

- **Q10 — Dependency versions.** CLAUDE.md Module 3 requires validating packages
  against current sources and the local Python (3.13.11) before recommending, not
  from memory. Pending.
- **Q11 — Does the UI need HTMX at all?** Plain server-rendered forms with full page
  reloads may cover every interaction (pick scenario, step timeline, accept/reject
  proposal) at zero dependency cost. To settle before the spec.

### Next turn

Validate dependency versions, then present the complete task inventory for approval.
Per CLAUDE.md Module 7 nothing goes into `TODO.md` until the inventory is approved,
and no implementation code is written until the spec is approved.

---

## Turn 5 — 2026-09-24 — Inventory approved; TODO, ADR and spec written

### Q10 — RESOLVED: dependency versions validated, not recalled

Resolved with `uv pip compile --python-version 3.13` against the local Python
3.13.11 on 2026-09-24:

```
fastapi==0.141.1  starlette==1.7.0  uvicorn==0.53.0
jinja2==3.1.6     pydantic==2.13.5  pytest==9.1.1
```

All declare `requires_python >= 3.10` or lower; the set co-resolves cleanly. Note
starlette is at 1.x — a major line, pulled in by FastAPI 0.141.1's own constraint.

### Q11 — RESOLVED: no HTMX, no client framework

Every interaction needed — choose scenario, step the timeline, accept or reject a
proposal — is a plain form post with a full page reload. A JS library buys nothing
here and costs a dependency. Upgrade path if a specific interaction later demands
partial updates: add HTMX from a CDN, one script tag, no build step.

### Task inventory — approved by the user, then logged

14 items written to `TODO.md`, all `[ ]`. Nothing was logged before approval, per
CLAUDE.md Module 7.

**ID format deviation, surfaced not silent.** Module 7 specifies
`<PREFIX>-YYYYMMDD-HHMM`. All 14 items were approved in the same minute, so the
format would produce 14 identical IDs. A two-digit sequence suffix was appended
(`FEAT-20260924-1250-01` …). The timestamp still serves as the date-added field.
Noted in `TODO.md` itself.

### Artifacts written this turn

- `TODO.md` — 14 items, flat, all Todo.
- `docs/adr/ADR-20260924-1250-tiered-decision-engine.md` — the tiered architecture
  and the constraint that no Tier 2/3 output may move a position without a recorded
  human decision. Written as an ADR rather than a spec section because it is the
  cross-cutting pattern the whole application rests on, and the implementor session
  needs it as a standing constraint.
- `docs/specs/FEAT-20260924-1250-lexo-trading-decision-system.md` — the
  implementation spec covering all 14 items: requirement traceability, verified
  source facts, repo layout, fixture schema with fail-fast validation, engine
  semantics, the determinism proof, the two futures, interface, tests, deployment,
  and the cut order under time pressure.
- `.gitignore` — excludes `CLAUDE.md` (per user instruction, kept untracked),
  `sources/text/`, and the usual Python artefacts.

### Standing caveats recorded for the implementor

- **Page numbers in the spec's source table are indicative.** They come from the
  memo's own `N · 92` footers as observed during Turn 3 text extraction. Every page
  and quote is to be re-verified at transcription time and the spec corrected if
  wrong.
- **Fixtures follow the memo, never the call transcript.** The ASR mangled the exit
  trigger — it is "any **two**" of four hyperscalers, and 45% is a **growth rate**,
  not $450B.
- **`app/engine` must not import from `app/web`.** The engine is a library; the web
  layer is a shell. This is what keeps the determinism proof cheap.
- Branch and merge operations are human-directed. Commit to `master`; do not create,
  switch or merge branches.

### State at end of this session

Discussion phase complete. No implementation code written, by design — this session
was for research and decisions; the build hands over to a fresh session.

Open items requiring a human before implementation starts:
- **Spec approval.** CLAUDE.md Module 7 requires explicit approval of the spec before
  any implementation code is written. Not yet given.
- **Render account** must exist and be connected to the repo for item -01.

---

## Turn 6 — 2026-09-24 — Spec approved; Render not yet connected

Spec approved as-is by the user. Implementation begins with item -01.

**Render account is not yet connected to this repo.** Item -01 scaffolds the app,
pins dependencies and prepares everything a Render deploy needs (start command,
`requirements.txt`), but the actual deploy step is blocked until the user connects a
Render account. This will be flagged again when that step is reached rather than
skipped or faked with a placeholder URL.

---

## Turn 6 — 2026-09-24 — Fan-out example was ring-illegal; spec corrected

Raised by the implementor session while transcribing NVDA fixtures
(FEAT-20260924-1250-04), by checking the spec's claims against the memo text rather
than re-reading the spec. Correct catch. Verified independently here before acting.

### What was wrong

Spec §3 named this as the headline engine-driven fan-out demo:

| | NVDA | AMZN |
|---|---|---|
| Hyperscalers building own silicon | #5 Inference Share Loss to Custom Silicon | #2 Custom Silicon Margin Moat |

Re-extracted both memos' Light Cone diagrams on 2026-09-24 and confirmed: **NVDA #5
is Internal ring and AMZN #2 is Internal ring.** Spec §6.5 propagates on sector and
market factors only. So the pairing could never have driven the engine — it was a
name match, not a mechanism the engine would catch.

**Root cause of the error:** during Turn 3 the factor tables and the Light Cone ring
diagram were read in separate passes, and the ring assignment was not carried back
into the cross-ticker table. The force-type reading (Wave −/Wave +) was correct; the
ring was simply never checked for that row. Lesson recorded in the spec: **ring, not
name, decides propagation.**

### What is actually ring-legal (verified)

| Mechanism | NVDA | AMZN | Ring | Signs |
|---|---|---|---|---|
| Capex turning credit-funded | #22 Hyperscaler Capex Financing Shift — Wave − | #24 Open Credit Funding AI Cloud Customers — Tailwind | Market ↔ Market | **opposite** |
| AI infrastructure buildout | #11 AI Infrastructure Buildout Wave — Wave + | #12 AI Infrastructure Demand Wave — Wave + | Sector ↔ Sector | same |

The memo states the duplication itself, in the audit note on NVDA #16: *"This force
is carried twice."* #16 sits on Sector, #22 on Market. AMZN's counterpart #24 is
Market, so #22 is the correct NVDA side of the pairing.

Also checked and recorded so it is not re-litigated: NVDA #13 Custom ASIC
Substitution *is* Sector ring, but AMZN's factor set carries no sector-ring
counterpart, so it has nothing to fan out to.

### Options considered

**Relax the ring rule to match on name or theme.** Rejected. It would make the engine
propagate because *we* decided two differently-named Internal factors are the same
force. The research never says so. That is an invented linkage, which is the one
thing the brief prohibits, and it would trade a sourced mechanism for a guessed one
to save a demo. It also touches an accepted ADR.

**Use the ring-legal pairings and drop custom silicon.** Rejected as incomplete — it
throws away the most striking finding in the two memos.

**Use the ring-legal pairings and keep custom silicon as a labelled non-propagating
observation.** Accepted. See D13.

### Decisions this turn

- **D13 — Engine fan-out uses the two ring-legal pairings; the custom-silicon
  asymmetry is shown but explicitly not propagated.** It is displayed with both
  source quotes and labelled as a human-observed linkage the engine declines to act
  on, with the reason in plain language. Rationale: a finding that traces to source
  perfectly but which our own rule will not act on is *better* evidence of the
  discipline than the original claim was — and it mirrors what the memo does when it
  admits it never sourced an options chain. Showing where the reasoning stops is more
  credible than dropping the inconvenient case.
- **D14 — Include a same-sign fan-out pairing as well** (AI infrastructure buildout,
  Sector ↔ Sector, both positive), so the interface does not imply fan-out is always
  contrarian. Costs nothing; the data is already being transcribed.
- **D15 — A factor is shared, ticker-agnostic state.** Identity, ring and force are
  recorded once; direction, impact, weight and provenance are per ticker, under an
  `exposures` map. Per-ticker `local_id` and `local_name` preserve each memo's own
  numbering and wording, because the two memos name the same force differently and
  the interface must show the source's words, not ours. Spec §6.5 now carries the
  explicit shape.

### Items logged

- `BUG-20260924-1322-15` — the spec defect. Closed in this turn; spec §3 corrected.
- `FEAT-20260924-1322-16` — surface custom silicon as sourced-but-non-propagating.
  Open; implement within FEAT-20260924-1250-12.
- `BUG-20260924-1322-17` — factor schema needs the ticker-agnostic shape. Open;
  blocks FEAT-20260924-1250-08.

### Note on the schema divergence

Spec §6.5 already said `direction` **per ticker**; the schema built in
FEAT-20260924-1250-03 stored a single ticker and direction. The spec was right and
the implementation drifted, so the spec has been made concrete with an explicit YAML
shape rather than a prose phrase that could be read two ways.

### Process note

The implementor stopped and logged before continuing, per CLAUDE.md Module 7, rather
than fixing in passing. That is the behaviour that caught this — the error would have
been invisible in a working demo, because a hand-wired fan-out would have looked
identical on screen to a ring-derived one.

### Turn 6 addendum — factor schema shape confirmed against a proposed alternative

Implementor proposed a cheaper fix: keep the single-ticker/single-direction `Factor`
from FEAT-20260924-1250-03 and add an optional `fan_out_key` string so the engine can
group the same mechanism across tickers.

**Rejected, on a concrete failure mode in this dataset rather than on principle.**
Under a join key, `ring` stays a per-row property. NVDA carries the capex force at two
rings deliberately — #16 Sector, #22 Market. Nothing would prevent #16 and #24 being
keyed together, silently producing a Sector↔Market pairing the engine would propagate.
Each row would be individually correct and the pairing incoherent, and unlike
BUG-20260924-1322-15 it would not be catchable by reading either memo. Under
`exposures`, ring belongs to the factor and cannot disagree with itself.

Secondary reasons: a mistyped join key fails silently — no error, no propagation, a
demo that quietly does not fan out — whereas a missing `exposures` entry is visible in
the fixture; and `exposures` matches the question the engine actually asks, one lookup
rather than scan-group-reconcile.

Neither design is more honest about provenance: the shared `id` is our assertion
exactly as `fan_out_key` would be. `exposures` only makes each assertion structurally
visible as a multi-exposure factor.

Cost accepted: one model, the loader, and the few factor rows transcribed so far.
FEAT-20260924-1250-04 is mid-flight and -05 has not started, so the rework lands
before FEAT-20260924-1250-08, where the wrong shape would have been expensive. The
join key would have been the right call for a single-ticker build; fan-out is the
headline demo here.

**D16 — validation rules added to spec §6.5.** Ring is single-valued per factor;
every exposure carries its own source; a sector/market factor with one exposure is
legal but counted and reported in the coverage line, so an intended-but-untranscribed
pairing is visible rather than silently inert; an internal factor with more than one
exposure is a startup error, because internal factors do not propagate and a
multi-ticker internal factor is a category mistake.
