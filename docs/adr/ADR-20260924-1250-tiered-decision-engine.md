# ADR — Tiered decision engine with a visible automation boundary

- **ID:** ADR-20260924-1250
- **Date:** 2026-09-24
- **Status:** Accepted
- **Context source:** `docs/decisions/notepad.md` Turns 1–4

## Context

The assignment asks for a deterministic decision system derived from investment
research, which explains its reasoning. Two source documents govern it and they do
not fully agree.

The **written brief** requires: rules derived not invented, each traceable to a
specific claim; decisions over time; at least two divergent futures with at least
one turning on a non-price event; determinism, demonstrated; explainability for a
non-engineer; tests on the decision logic; a deployed URL. It lists machine learning
as out of scope.

The **kickoff call** loosens this. Asked directly whether a machine-learning approach
was wanted, the answer was that the time box means "you're not gonna flesh out the
full machine learning algorithm, but it gives you kind of the potential". On rules,
the framing was explicit: *"think of it as heuristics on one end, hard rules on
another... I don't care how you treat it, but either direction you take is indicative
of something"*, and *"our platform supports both"*. The single stated hard constraint
was that the system *"should be hooked into and based on the research, not just a
blank sheet of paper"*. The decision maker also stated that fully automated trading
is *"a nice to have"* while *"human in the loop"* is what he fundamentally believes
adds value.

Three options were considered.

**Hard rules only.** A deterministic state machine transcribed from the memo's
Execution Plan. Satisfies every written requirement and is the smallest build.
Rejected as the sole approach: it reproduces the client's own sample demo with better
provenance, and cannot express the cross-ticker propagation that was explicitly
requested on the call.

**Heuristic scoring only.** Compose the memo's 28 weighted factors into a conviction
score; thresholds map score to action. Rejected: when a decision emerges from a
weighted sum of 28 inputs, it can no longer be traced to one claim. Determinism
survives; explainability, the brief's first requirement, does not.

**Tiered hybrid.** Accepted. See below.

## Decision

Three tiers, with the automation boundary made visible in the product.

**Tier 1 — hard rules. Deterministic, auto-applied.**
The memo's Execution Plan and "Three Dates" transcribed as dated triggers. Every
decision cites a specific source sentence. This tier alone satisfies the written
brief.

**Tier 2 — factor heuristics. Proposes, never executes.**
Sector and market factors are shared state. When one moves, every position whose
factor set includes it is re-rated. Tier 2 emits a *proposal* carrying its reasoning;
a human accepts or rejects; both the proposal and the human's response are appended
to the decision log. No Tier 2 output ever reaches a position without a recorded
human decision.

**Tier 3 — the learned layer. Marked, not built.**
Scenario probabilities are fixed priors transcribed from the memo (Bull 25 / Base 50
/ Bear 25). The interface states that they are fixed priors, cites where they came
from, and names what a learned estimator would replace. No model is trained or
served.

**Rule override is a first-class, logged, attributable event** across all tiers. The
memo overrides its own platform rule — Neutral spring maps to a starter position, and
the memo declines it because *"opening length into that distribution would be
following a rule against the analysis the rule exists to serve"*. An engine that can
only express `rule fires → action` cannot represent its own source document.

## Consequences

**Positive.**
- The Tier 1/Tier 2 boundary is the human-in-the-loop philosophy made structural
  rather than decorative, matching what the decision maker said he values.
- Answers *"our platform supports both"* by supporting both and showing where the
  line falls — which the call framed as itself indicative.
- Determinism is provable because it is a property of Tier 1 and of Tier 2's
  recorded inputs, not of a model.
- Tier 3 answers the machine-learning question on screen without spending build time
  on it, which is what the call actually asked for.

**Negative / accepted costs.**
- More surface than hard-rules-only, against a one-day build. Mitigated: Tier 2 is
  the factor layer the fan-out demo needs regardless, and Tier 3 is an interface plus
  interface copy, not an implementation.
- A reader could mistake Tier 3's labelling for a claim that a model exists. Mitigated
  by explicit wording: fixed priors, source cited, not learned.

**Constraint this places on all later work.**
No Tier 2 or Tier 3 output may mutate a position without a recorded human decision.
Any future change that lets a heuristic auto-execute supersedes this ADR and must
replace it rather than quietly widen it.
