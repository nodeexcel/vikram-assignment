# TODO

Single tracking file. One flat checklist. Status changes in place by replacing the
marker only — items are never moved or reordered.

`[ ]` Todo · `[o]` In-Progress · `[x]` Done

> **Note on IDs.** CLAUDE.md Module 7 specifies `<PREFIX>-YYYYMMDD-HHMM`. All items
> below were approved and logged in the same minute, so a two-digit sequence suffix
> is appended to keep IDs unique. The timestamp still doubles as the date-added
> field. Flagged rather than silently changed.

Spec for every item below: `docs/specs/FEAT-20260924-1250-lexo-trading-decision-system.md`
Architecture decision: `docs/adr/ADR-20260924-1250-tiered-decision-engine.md`
Discussion history and rationale: `docs/decisions/notepad.md`

- [ ] FEAT-20260924-1250-01 — Scaffold the project (uv, FastAPI, pytest) and deploy an empty page to Render before any engine code, so the public URL exists from the start and Friday's deploy is a redeploy rather than a first attempt
- [ ] ISS-20260924-1250-02 — Extract the NVDA and AMZN PDF text into `sources/text/` via a committed script, gitignored output, so the transcription reference survives session restarts (it was lost once already)
- [ ] FEAT-20260924-1250-03 — Define the fixture schema in Pydantic with fail-fast validation: every claim carries doc, page and verbatim quote, and the app refuses to start if any rule or factor lacks a source
- [ ] FEAT-20260924-1250-04 — Transcribe the NVDA fixtures by hand: verdict and stance, execution plan, the three dates, both scenario tables, the decision-driving weighted factors, and the four kill switches — each with page and quote
- [ ] FEAT-20260924-1250-05 — Transcribe the thin AMZN fixtures: the three-to-four factors that mirror NVDA's, enough to drive the cross-ticker fan-out demo (depends on FEAT-20260924-1250-03)
- [ ] FEAT-20260924-1250-06 — Build the Tier 1 deterministic rule engine: walks a dated event timeline, fires rules, appends to an immutable decision log, and implements the two-consecutive-period confirmation primitive shared by the $195 stop and two kill switches
- [ ] FEAT-20260924-1250-07 — Model rule override as a first-class logged event, so the engine can represent the memo's own deliberate override of the Neutral-spring starter-position rule with its stated reason (depends on FEAT-20260924-1250-06)
- [ ] FEAT-20260924-1250-08 — Build the Tier 2 factor layer: sector and market factors as shared state that re-rate every affected ticker, emitting proposals only — never auto-executing — with human accept/reject recorded in the decision log (depends on FEAT-20260924-1250-06)
- [ ] FEAT-20260924-1250-09 — Author the two divergent futures as event timelines: "Guide Holds" (2026-11-17 FY2028 commentary near 70% with backlog detail) and "Capex Turns" (two of four hyperscalers guiding capex flat or down, 2027-01-26 to 2027-02-06) — both driven by disclosures, not prices
- [ ] FEAT-20260924-1250-10 — Prove determinism: canonicalise and hash the decision log, run each scenario twice, assert the hashes match; surface the proof both as a test and as a visible check in the app, because the brief asks us to show that it holds
- [ ] FEAT-20260924-1250-11 — Write pytest coverage against the decision logic specifically: trigger boundaries, the two-close confirmation, position-conditional rules, override behaviour and fan-out sign
- [ ] FEAT-20260924-1250-12 — Build the read-only views: what the research concludes, every rule with its source quote and a bidirectional link to the claim, and the honest on-screen factor-coverage disclosure ("N of 28 transcribed", naming what is missing)
- [ ] FEAT-20260924-1250-13 — Build the timeline view: step through dated events, see what the system did and why in plain language at each point, and accept or reject Tier 2 proposals
- [ ] FEAT-20260924-1250-14 — Write the "where this goes next" document: where a learned model would replace the fixed scenario priors, what the source could not supply, and what would be built next — graded as heavily as the code per the kickoff call
