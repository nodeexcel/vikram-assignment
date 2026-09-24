# How this system works, and why it is built this way

A walkthrough of the design: what problem it solves, the shape of the solution,
what that buys, and the approaches we weighed and rejected.

---

## 1. The problem

We were given roughly 280 pages of investment research on NVIDIA — a memo, a theme
report and a factor report — and asked to turn them into a working decision system
that shows its reasoning.

The hard part is not the trading logic. It is that the research is **prose**, and a
decision system needs **rules**, and the distance between the two is where every
honest failure lives. Prose can say "roughly", "near 70%", "in the late-January
window". A rule has to say `>= 70`, `2027-01-26 to 2027-02-06`. Every one of those
conversions is a judgement, and a system that hides its judgements behind confident
output is worse than no system.

So the real requirement is not "make a rule engine". It is: **make every judgement
visible and attributable, and make the machine refuse to act on one that is not.**

---

## 2. The insight that shapes everything

The memo is already a decision system. It is just written in English.

It states an execution plan with a rating, a conviction, a position action, a
stop-loss level, a re-entry trigger, an exit trigger and a horizon. It names three
dates that change the rating, each with a metric, a threshold and a timeframe. It
carries four kill switches with watch cadences.

We are not deriving rules by interpretation. **We are transcribing a state machine
that a human analyst already wrote.** That single fact is why "rules are derived, not
invented" is honest here rather than aspirational, and it is why provenance can be
exact — a page and a sentence — rather than approximate.

It also sets the failure mode to guard against. The risk is not that we invent a
rule. It is that we **flatten** one: take a sentence with a condition, a confirmation
requirement and an exception, and encode only the number.

That is not hypothetical. It happened repeatedly during the build, and each time the
same shape: a constraint the memo states precisely, encoded as something the engine
could not evaluate.

- The stop is `$195.00 on two consecutive weekly closes`. Encoded first as a bare
  count of two periods, with no unit — so on a daily series it would have fired on
  two consecutive days, defeating the exact thing the memo says the confirmation
  exists for.
- The stop applies to existing holders only. Encoded first as the free-text string
  `"position != none"`, which no engine can act on.
- The 17 November partition is three-way with a residual: bull needs near 70%
  **and backlog detail**, bear is below 45%, base is everything else. Encoded first
  as two overlapping numeric ranges that both fired at 72%. Fixed by bounding the
  middle range — which then opened the opposite hole, where 72% **without** backlog
  detail matched nothing at all and the system silently made no decision on the one
  date the whole thesis resolves on.

Each was caught by reading the memo against the code, not by reading the code.

---

## 3. How it works

Four stages, one direction, no loops.

```
  PDFs (read by hand)
        |
        v
  fixtures/*.yaml ........... every claim carries doc + page + verbatim quote
        |                     validated at startup; refuses to load unsourced
        v
  app/engine/ ............... pure Python library, zero web imports
        |                     run(rules, events, overrides, factors) -> log
        v
  DecisionLog ............... append-only; canonical JSON; SHA-256 hashable
        |
        v
  app/web/ .................. server-rendered pages; reads the log, never decides
```

**Fixtures.** The memo's claims, hand-transcribed. The brief puts PDF parsing out of
scope, so nothing is machine-extracted at runtime. Each rule, factor and scenario leg
carries a `source` of document, page and exact quote, plus a `provenance_status` of
`derived`, `partial` or `added`. `partial` means the source states the rule but
declines to supply parameters and must quote the source admitting it. `added` means
we made it up and must carry a rationale — and must **not** carry a source, because
it does not have one.

**Validation is a startup error, not a warning.** A rule without a source does not
load. The application does not boot. There is no default that lets it run anyway,
because a system whose whole claim is traceability must not be able to start in a
state where that claim is false.

**The engine.** A pure function. It sorts events into a total order of
`(date, kind, ticker)`, walks them once, evaluates rules, and appends to an
immutable log. No wall-clock reads, no randomness, no reliance on dictionary or set
iteration order anywhere that affects output.

**The web layer decides nothing.** It re-runs the engine and renders the log. That
separation is not architectural neatness — it is what makes the determinism proof
cheap, because the thing being proved is a function with no I/O in it.

---

## 4. One decision, traced end to end

Take the stop firing in the "Guide Holds" scenario.

1. The memo says, on page 46: *"a stop at $195.00 on two consecutive weekly closes -
   -15.3% from the $230.36 reference price"*, and, separately, that this applies to a
   reader who already owns the stock.
2. That becomes a rule with `threshold: 195.00`, `comparator: lte`,
   `consecutive_periods: 2`, `period_unit: weekly`,
   `requires_existing_position: true`, and the quote above as its source.
3. The scenario opens a full-weight position on 17 November when FY2028 commentary
   confirms the guide with backlog detail.
4. On 15 January the price closes at $193.50 — below the level. The streak counter
   goes to one. **Nothing happens.**
5. On 22 January it closes at $198.20. The streak breaks and resets. This is the
   memo's stated reason for requiring two closes: *"so a single volatile week around
   an earnings print does not trigger the exit."*
6. On 29 January it closes at $192.10 — streak one. On 5 February, $188.40 — streak
   two. The stop fires. Position goes from full weight to none.
7. The log records the date, the rule, the action, the position after, and the quote.
   The timeline page shows all of it in plain language.

Every step of that is checkable against a sentence in a PDF. That is the whole
design goal.

---

## 5. Three tiers, with the boundary made visible

The client said explicitly that they would accept either hard rules or heuristics,
and that whichever direction we took would itself be informative. We took both, and
made the line between them part of the product.

- **Tier 1 — hard rules.** The execution plan. Deterministic, applied automatically,
  each decision citing a sentence. This tier alone satisfies every written
  requirement.
- **Tier 2 — factor heuristics.** Shared sector and market factors. When one moves,
  every exposed position is re-rated. Tier 2 **proposes and never executes.** A human
  accepts or rejects; the proposal and the response are both logged with the actor,
  and the position is shown as unchanged on the proposal itself.
- **Tier 3 — the learned layer.** Not built. The scenario probabilities are fixed
  priors transcribed from the memo. The interface says so and names what a learned
  estimator would replace.

Why draw the line rather than pick a side: a decision that emerges from a weighted
sum of 28 factors cannot be traced to one claim. Determinism would survive that;
explainability would not, and explainability is the first requirement. But refusing
heuristics entirely gives up the cross-ticker reasoning that makes the research
valuable. Tiering keeps both and makes it obvious which one produced any given row.

**Override is a first-class, logged event.** The memo overrides its own platform
rule: the Neutral spring state maps to a starter position, and the memo declines it
because *"opening length into that distribution would be following a rule against the
analysis the rule exists to serve."* An engine that can only express
`rule fires -> action` cannot represent its own source document. So the log records
what the rule would have done, what happened instead, why, and who decided — whether
that actor is the memo or a human.

---

## 6. How one event reaches two companies

The memo's Light Cone diagram places each factor on one of three rings: internal to
the company, sector-wide, or market-wide. **Sector and market factors are
ticker-agnostic by construction.**

So the propagation rule is read off the source, not modelled by us: a factor shift
re-rates every ticker exposed to that factor, if and only if the factor sits on the
sector or market ring. Internal factors never propagate.

This matters more than it looks. The most striking finding in the two memos is that
hyperscalers building their own chips is a **threat to NVIDIA** ("Inference Share
Loss to Custom Silicon") and a **moat for Amazon** ("Custom Silicon Margin Moat") —
the same real-world mechanism, opposite signs, each stated in its own source. It is
the perfect demo, and **the engine refuses to propagate it**, because both memos place
it on the internal ring.

Linking them would mean deciding for ourselves that those two differently-named
factors are one force. The research never says that. So the app displays the
asymmetry with both quotes and labels it a human observation the engine declines to
act on. Showing where the reasoning stops is more credible than quietly dropping the
inconvenient case.

The engine-driven fan-out uses a pairing that **is** ring-legal: hyperscaler capex
turning credit-funded, which is market-ring in both memos and carries opposite signs
— bearish for NVIDIA's demand, a tailwind for Amazon's funding.

---

## 7. Determinism, and proving it

The brief does not ask for determinism. It asks us to **show that it holds**, which
is a different and larger request.

The decision log is serialised to canonical JSON — sorted keys, fixed separators, no
execution timestamps, only in-world dates — and hashed with SHA-256. Three checks:

- Run the same scenario twice in one process; the hashes must match.
- Run it again in a **subprocess with `PYTHONHASHSEED` varied**; the hash must still
  match. This is the real proof. Code review can miss a hidden dependence on
  dictionary or set iteration order; a differently-seeded process cannot.
- Compare against a hash recorded in the test suite, so an accidental change to
  decision logic fails loudly rather than producing a different but internally
  consistent answer.

And the app has a page that re-runs both scenarios live and shows the hashes side by
side. A reviewer does not have to trust a test file they will never open.

---

## 8. What this buys

- **Every output is falsifiable.** Any decision can be checked against a page and a
  sentence. A reader who disagrees can argue with the analyst, not with the software.
- **The system cannot lie by omission.** Unsourced rules will not load. Incomplete
  provenance is labelled. Factor coverage is stated as a fraction with the gaps
  named. The one rule whose parameters the memo could not supply is shown as partial,
  quoting the memo admitting it.
- **Disagreement is representable.** Rules can fire and be overruled, with the reason
  and the actor recorded. Most rule engines can only express compliance.
- **Determinism is demonstrated, not asserted.** Same inputs, same hash, across
  processes.
- **Reasoning crosses tickers without being invented.** Propagation follows the
  source's own taxonomy.
- **The engine is a library.** No web imports, so it is testable alone and could be
  driven by a scheduler, a notebook or a broker adapter without touching it.

---

## 9. Approaches we considered and did not take

**Hard rules only.** The smallest build, trivially deterministic, satisfies the
written brief on its own. Rejected as the sole approach because it reproduces the
client's own sample demo with better citations, and cannot express the cross-ticker
propagation they asked about directly.

**A weighted conviction score.** Compose the 28 factors and their impact weights into
a single number; thresholds map the number to an action. Attractive: flexible,
handles situations the memo never anticipated, uses the factor weights as designed.
Rejected because when the answer is "sell" and the question is "why", the honest reply
becomes "twenty-eight numbers summed to forty-one". That breaks the first requirement.
The weights still exist in the fixtures and inform Tier 2 proposals — they just do not
silently produce Tier 1 decisions.

**An LLM in the decision path.** Feed the memo and the current events to a model and
ask what to do. Genuinely tempting: no transcription, handles events nobody
anticipated, and reads nuance that rules flatten. Rejected because it fails the
central requirement outright. Even at temperature zero with a fixed seed, identical
inputs are not contractually guaranteed to produce identical decisions across model
versions, and you cannot show a reviewer that it holds. You would also lose the thing
that makes this credible: the ability to point at the sentence. We used AI heavily at
**build** time — reading 280 pages, cross-checking claims, catching our own errors —
and kept it out of the runtime entirely.

**Machine learning on historical outcomes.** Learn the signal weights from past price
reactions. Rejected on two grounds. The brief puts serious backtesting and ML out of
scope. More fundamentally, this is a single-name thesis resolving on two future
catalysts: the sample size for "what happens when NVIDIA guides FY2028 below 45%" is
zero. A model fitted here would be fitting noise and dressing a guess as rigour.

**A probabilistic graphical model over the scenario tree.** Treat bull, base and bear
as a belief distribution and update posteriors as catalysts resolve. This is the most
intellectually honest of the alternatives, and it matches how the client described
the problem — weighing the probability of different futures. We did not build it
because the priors would still be the memo's hand-set 25/50/25, so the machinery
would add opacity without adding information, and a non-engineer cannot follow a
posterior update the way they can follow "this sentence says sell". It is the natural
next step, and it is where a learned layer would attach.

**An off-the-shelf rules engine or CEP system.** Drools, json-rules-engine, Flink
CEP. Mature temporal operators, and "two consecutive closes" is a built-in pattern
rather than something we wrote. Rejected because provenance is not a first-class
concept in any of them. We would spend the saved effort bolting citations onto a
foreign object model, and the citation is the point. The one primitive we actually
needed took about twenty lines.

**A formal state machine library.** Declare the states and transitions explicitly and
get exhaustiveness checking. Worth naming honestly: **this would have caught one of
our real bugs statically.** The 17 November partition had a hole where commentary at
or above 70% without backlog detail matched no branch, and a tool that checks
transition coverage would have flagged it immediately. We found it by probing the
engine instead. If this grew past a handful of tickers, that is the first thing we
would add.

**A spreadsheet.** What an analyst would actually build, in an afternoon, and own
without asking an engineer. Genuinely the right answer for a single position with six
rules. It loses the audit trail, the determinism proof, and any ability to fan one
event out across a portfolio — which is exactly what the platform is for.

---

## 10. What this approach costs

Stated plainly, because an explanation that only lists advantages is marketing.

- **Transcription is manual and does not scale.** Nine of NVIDIA's 28 factors are
  transcribed. Covering a portfolio means either a great deal of human effort or the
  automated extraction the brief put out of scope.
- **Rules only fire on events we anticipated.** A genuinely novel disclosure — one
  that matters but matches no trigger — produces silence. A scoring or LLM approach
  would at least react. Our mitigation is that silence is visible: the timeline shows
  the event and shows that nothing fired.
- **The memo's ambiguity does not disappear, it relocates.** "Near 70%" became
  `>= 70`. That is a judgement. It is visible next to its quote, so a reader can
  disagree — but it is still ours.
- **Accepting a Tier 2 proposal records the decision without re-running the engine.**
  Correct per the architectural constraint, and less than a reviewer might expect.
- **Two horizons must be held apart by the reader.** The memo insists the -40.6%
  intrinsic gap and the -13.1% twelve-month return are different clocks. We show them
  separately and warn against conflating them, but we cannot stop someone averaging
  them in their head.

---

## 11. What would change the design

- **More tickers** — formal state machine with exhaustiveness checking, and automated
  extraction with human review, because manual transcription becomes the bottleneck.
- **Real market data** — the price-close path becomes a feed, the stop becomes a live
  monitor, and the determinism proof needs pinned input snapshots rather than fixture
  files.
- **A learned layer** — scenario priors move from fixed values to estimates, and the
  interface has to distinguish a probability the analyst asserted from one a model
  inferred. That distinction is the whole reason Tier 3 is labelled rather than
  quietly absent.
- **Multiple analysts** — overrides need identity and review, and the log needs to
  become durable storage rather than an in-memory rerun.
