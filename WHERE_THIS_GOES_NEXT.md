# Where this goes next

This build is a tiered decision system: a deterministic Tier 1 (the memo's own
Execution Plan, transcribed as dated rules), a Tier 2 that proposes cross-ticker
re-ratings but never executes them, and a Tier 3 that is deliberately not built —
marked instead, as a labelled seam in the product. This document is that seam
spelled out: where a learned model would go, what the two source memos could not
give us even when we read them closely, and what we'd build next with more time.

It's written for both people in the room. Jagadesh's bar is the engine — does the
rule-to-trigger matching actually work, is the fan-out real. Vikram's bar is the
thinking — where this is going, and whether we understand the difference between
a rule and a belief. This tries to answer both.

---

## 1. Where a learned model would replace the fixed scenario priors

Right now, every probability in this build is a constant transcribed from the
memo: Bull 25% / Base 50% / Bear 25% on both the 3–5yr intrinsic table and the
12-month tactical table, unchanged for the life of the run. `Tier3` is a label in
the code, not a component — no model is trained, fit, or served anywhere in this
repo. That's a deliberate scope decision (ADR, Tier 3), not an oversight, and the
UI says so next to the numbers it shows.

**What the learned layer would actually do.** Not replace the Tier 1 rules —
those stay hard-coded, sourced, deterministic, and auditable; that's the part of
the brief that isn't negotiable ("derived, not invented", "show us that it
holds"). What it would replace is the *prior weight* on the three scenario
buckets: instead of a static 25/50/25 fixed at the memo's publication date, a
model would re-estimate `P(bull) / P(base) / P(bear)` every time a relevant
disclosure lands — the 2026-11-17 print, each hyperscaler's capex guide, the
formal FY2028 number — using the same event stream this build's timelines
already produce as evidence.

**A concrete, buildable version of it.** A calibrated classifier over a small,
explainable feature set: the company's own historical guide-vs-actual delta,
sector-wide guide-beat rate over the trailing several quarters, analyst estimate
dispersion going into the print, and whether backlog detail specifically was
disclosed (the memo treats that as the one detail that turns a number into a
confirmation). Output is a probability triple, recalibrated after each event —
architecturally closer to a Bayesian update than a black box, which matters,
because "the model said so" is not an acceptable substitute for a cited claim in
a system whose whole premise is that decisions trace to sources. Whatever
estimator gets built here would need to expose *why* it moved a probability the
same way `provenance_status` and `gap_note` expose why a rule is `partial` — an
opaque probability update would violate the same discipline the rest of the
system is built around, just one layer up.

**Why the seam is here and not somewhere else.** Tier 2 already proposes without
executing; a learned Tier 3 slots into the same shape — it re-weights the
*inputs* to a decision (the scenario priors that feed the expected-value framing
in view 1), it does not *make* a decision. Nothing about adding it would touch
Tier 1's rule engine, the determinism proof, or the human-in-the-loop constraint
on Tier 2. That's the intellectual case for the tiering, and it's also why this
was buildable in the scope this had: the seam existing and being labelled is the
deliverable at this stage, not the model behind it.

## 2. What the source could not supply

Found while transcribing, not assumed going in — each of these is a specific,
verified gap, not a general disclaimer.

- **The hedging rule has no instrument.** The memo justifies hedging existing
  exposure through IV rank 0–9, then states outright that "no strike, expiry or
  premium is named anywhere here: no options chain was sourced for this
  workbook." This is the one `provenance_status: partial` case in the build, and
  it's real, not manufactured — the source admits the gap itself.
- **Force type and impact are missing for most of the weighted factor set.**
  The Light Cone diagram gives every one of NVDA's 28 factors a force type
  (Wind/Wave/Mud) and an impact score. The memo's *separate* promoted/weighted
  write-up (the 8 factors that sum to the 100-point composition) gives weight and
  a "zone" instead — not force, not impact. Five of NVDA's eight weighted factors
  carry no force or impact in this build's fixtures because the source simply
  doesn't state it there, and guessing it from a same-named diagram entry turned
  out to be actively wrong (see BUG-18 below) — so it's left unset rather than
  invented.
- **The theme report's "zone" and the memo's Light Cone "ring" are not the same
  axis, and nothing in the source says so.** Zone (intrinsic/ecosystem/external)
  is a controllability split over the 8 weighted factors. Ring
  (internal/sector/market) is a propagation-scope split over all 28, and it's
  the one that decides whether a factor can fan out to another ticker. They
  disagree for real factors — `Share Ceded to Custom Silicon` is zone-external
  but Light Cone-internal — and an earlier pass in this build's own history
  conflated them, which would have made the engine propagate a linkage the
  research never actually licenses. Caught and fixed (BUG-20260924-1421-18);
  five of NVDA's nine transcribed factors carry `ring: unknown` rather than a
  guessed value, because no confident Light Cone match exists for them in the
  source.
- **The custom-silicon asymmetry is sourced on both sides but not linkable.**
  NVDA's "Inference Share Loss to Custom Silicon" and AMZN's "Custom Silicon
  Margin Moat" describe the same real-world mechanism with opposite
  consequences — and both sit on the Internal ring in their own memo. The
  research states each side; it never states they're the same propagatable
  force. This build shows both quotes side by side and says plainly that the
  engine declines to act on the link, rather than inventing the connection to
  make a better demo.
- **19 of NVDA's 28 Light Cone factors were never transcribed at all.** The
  eight weighted/promoted factors plus one more (used for the AI-infrastructure
  fan-out pairing) are in the fixtures with real citations. The rest — mostly
  sector- and market-wide risk factors outside the weighted composition, e.g.
  export-control regimes, memory pricing, Taiwan Strait concentration — are
  named in the source and in this document, but not given full paragraph/quote
  treatment. The app states the count on screen rather than pretending coverage
  is complete.
- **AMZN is deliberately thin.** Two factor exposures exist so the fan-out demo
  is real, not staged with fabricated data. AMZN never holds a position, has no
  Execution Plan of its own transcribed, and never runs its own Tier 1 walk in
  this build — the assignment's own framing treats it as a secondary ticker to
  prove propagation, not a second full analysis.
- **Kill switches are watched, not simulated.** Their thresholds are compound
  prose ("below 65% unadjusted or 78% adjusted... with accruals above 20%"), not
  a single metric/comparator/threshold the way a Tier 1 trigger is. They're
  correctly sourced and displayed as risk-watch disclosures; none of them can
  fire automatically against a timeline event in this build.
- **The geopolitical bear route is explicitly not modelled as a cash-flow path
  — by the source itself, not by this build.** It carries 10% of the bear leg's
  weight with no separate scenario table entry. The memo says why: no
  Steelman and no Market-Implied case exists upstream to price it against.

## 3. What would be built next

Roughly in the order it would actually get picked up:

1. **Structure the kill-switch thresholds the same way rule triggers were
   structured.** This build already went through one full pass of turning free
   prose into machine-evaluable fields for `Rule.trigger` (upper bounds, period
   units, backlog-detail flags — all found and fixed during this session). The
   same treatment for `KillSwitch.threshold` is the same kind of work, not a new
   kind, and it's what closes the "shared primitive" claim for real instead of
   for two of the intended four triggers.
2. **Re-verify the Light Cone ring assignments against the source diagram
   directly**, not `pdftotext -layout`'s linearization of it — the diagram is a
   spatial layout, and text extraction visibly scrambled some of its
   number-to-label pairings during this build. A confident pass here would
   likely resolve some of the five `unknown`-ring factors without guessing.
3. **Give AMZN a real Tier 1 walk of its own** — its own transcribed Execution
   Plan, its own position, its own rules — rather than the two thin exposures
   that exist purely to demonstrate fan-out. CSCO, which the shared source
   folder also included and this build scoped out entirely (decided in the
   discussion log, Turn 1), would be the next ticker after that.
4. **Build the Tier 3 seam for real**, starting from the Bayesian-update version
   sketched in §1 — cheap, explainable, and closest in spirit to what this
   engine already does elsewhere (log why a number changed, don't just report
   that it did).
5. **Persist decision-log and proposal-response state server-side.** It's
   in-memory today and resets on redeploy, which is fine for a demo and wrong
   for anything a person would actually rely on. SQLite is enough; this doesn't
   need a database server.
6. **Build a backtest harness against real dates as they pass.** 2026-11-17 is
   roughly eight weeks out from this build. Once it happens, replaying this
   engine's own Tier 1 rules against what actually got disclosed is the real
   test of whether "rules derived from research" hold up outside a fixture —
   more valuable than anything else on this list, and the only one that can't
   be done yet.

Auth and multi-user support are explicitly out of scope per the written brief
and aren't on this list for that reason, not because they're unimportant to a
real deployment.
