# Lexo trading decision system — the whole project

One document: what was asked, why it was built this way, how it works, when the work
happened, and what came out. Everything else in the repo is detail this points at.

---

## At a glance

- **What** — a web application that turns Lexo's NVIDIA investment research into a
  deterministic decision system and shows its reasoning.
- **Who for** — an evaluation exercise set by Lexo, reviewed by their technical lead
  and a partner. Two different bars, both have to be met.
- **Live** — _<Render URL>_
- **Repo** — https://github.com/nodeexcel/vikram-assignment
- **Status** — 53 of 55 tracked items closed, 74 tests passing. Outstanding: the
  deploy itself, and self-hosting the web fonts.
- **Built** — 23–25 September 2026. One day of reading and design, one day of
  building, a half day of review and polish.

| | |
|---|---|
| Engine | 670 lines of pure Python, no web imports |
| Web | 1,267 lines, server-rendered, no client framework |
| Tests | 865 lines, 74 tests, decision logic only |
| Fixtures | 793 lines of hand-transcribed claims, each with a page and a quote |
| Documentation | 2,581 lines |

---

## 1. The task

### What was asked

Lexo runs a research platform that produces long, opinionated investment memos. The
exercise: take that output and build *a working application that turns those artifacts
into a deterministic decision system and shows its reasoning*.

The test stated in the brief is that someone can open the app and answer three
questions without asking the author anything:

1. What does the research actually conclude?
2. What rules did you derive from it, and where did each one come from?
3. What would the system do, when, and why?

Hard requirements, all of which this build meets:

- Rules are derived, not invented. Every rule traces to a specific claim. Anything
  added that does not must be flagged **in the interface**.
- The system decides over time, not once: whether to hold, how large, and when to stop.
- At least two divergent futures, at least one turning on something that is not a
  price — a disclosure, a guidance change, a third-party event.
- Determinism. The same inputs produce the same decisions, and *"show us that it
  holds"*.
- Explainability at any point in time, in terms a non-engineer can follow.
- Tests on the decision logic specifically.
- Deployed, reachable at a URL.

Explicitly out of scope: PDF parsing at runtime, live market data, broker integration,
authentication, statistically serious backtesting, machine learning, native apps.

### What the kickoff call added

The written brief is the floor. The call loosened several things and that changes what
a good answer looks like.

- **There is no rubric.** *"It's not a hard bound rule that I have. I'm more excited to
  see what you guys can come up with."*
- **The thinking is graded as heavily as the code.** *"If there's a lot of thinking
  that went into it, where what you're showing is just the seeds of that thinking…
  where it is going should be easily able to be seen by us."*
- **Machine learning is permitted but not expected.** Asked directly, the answer was
  *"you're not gonna flesh out the full machine learning algorithm, but it gives you
  kind of the potential."* The word used repeatedly was *seeds*.
- **Rules or heuristics, either is fine, and the choice is itself informative.**
  *"Think of it as heuristics on one end, hard rules on another… either direction you
  take is indicative of something."*
- **One hard constraint.** *"It should be hooked into and based on the research, not
  just a blank sheet of paper."*
- **Human in the loop is the stated philosophy.** Fully automated trading is *"a nice
  to have"*; human oversight is what the partner *"fundamentally believes"* adds value.
- **Cross-ticker propagation was asked for directly.** One event should be able to
  *"trigger buy or sell recommendation for multiple tickers in the portfolio."*

### The source material

Three PDFs for NVIDIA — a 92-page memo, a 34-page theme report, a 157-page factor
report — plus equivalents for Amazon and Cisco. About 280 pages were read for NVIDIA
and Amazon.

**Scope taken:** NVIDIA in depth, Amazon thin. Amazon exists solely to demonstrate that
one event can reach two positions. Cisco was not used.

---

## 2. Why — the problem behind the problem

The trading logic is not the hard part. The hard part is that research is **prose** and
a decision system needs **rules**, and every conversion between the two is a judgement.

Prose says *"roughly"*, *"near 70%"*, *"in the late-January window"*. A rule has to say
`>= 70`, `2027-01-26 to 2027-02-06`. A system that hides those judgements behind
confident output is worse than no system, because it looks authoritative while being
unfalsifiable.

So the real requirement is not "build a rule engine". It is: **make every judgement
visible and attributable, and make the machine refuse to act on one that is not.**

### The idea the build rests on

The memo is already a decision system. It is just written in English.

It states an execution plan — rating, conviction, position action, stop level,
re-entry trigger, exit trigger, horizon. It names three dates that change the rating,
each with a metric, a threshold and a timeframe. It carries four kill switches with
watch cadences.

**So this transcribes a state machine a human analyst already wrote.** That is why
"derived, not invented" is honest here rather than aspirational, and why provenance can
be a page and a sentence rather than a gesture.

It also names the real failure mode. The risk was never inventing a rule. It was
**flattening** one — taking a sentence carrying a condition, a confirmation requirement
and an exception, and encoding only the number. That happened repeatedly during the
build; section 7 lists the instances.

---

## 3. What was built

Eight pages. Each of the brief's three questions has one.

| Page | Answers |
|---|---|
| `/` | Orientation. The conclusion, the key facts, where to go. |
| `/research` | **Q1.** Verdict and stance kept apart, both scenario tables, the dated triggers, the kill switches. |
| `/rules` | **Q2.** Eight rules, each with its machine condition beside the memo sentence it came from. Overrides, shared claims, factor coverage. |
| `/timeline/guide_holds` | **Q3.** The bull path: the guide confirms, the position goes to full weight, then stops out. |
| `/timeline/capex_turns` | **Q3.** The bear path: third-party capex guidance triggers the exit, and Tier 2 proposals re-rate Amazon the opposite way. |
| `/determinism` | Both scenarios re-run live and hashed, side by side. |
| `/how-it-works` | The design walkthrough and the approaches rejected. |
| `/where-this-goes-next` | Where a learned layer attaches, what the source could not supply. |

Plus `/health`, which reports what actually loaded rather than that a socket is open.

---

## 4. How it works

### The pipeline

```
  PDFs (read by hand)
        |
        v
  fixtures/*.yaml ........... every claim carries doc + page + verbatim quote
        |                     validated at boot; the app refuses to start unsourced
        v
  app/engine/ ............... pure Python library, zero web imports
        |                     run(rules, events, overrides, factors) -> log
        v
  DecisionLog ............... append-only; canonical JSON; SHA-256 hashable
        |
        v
  app/web/ .................. server-rendered pages; reads the log, never decides
```

`app/engine` must never import from `app/web`. The engine is a library; the web layer
is a shell over it. That separation is not tidiness — it is what makes the determinism
proof cheap, because the thing being proved is a function with no I/O in it.

### Provenance, and failing loud

Every rule, factor and scenario leg carries a `source` of document, page and exact
quote, plus a `provenance_status`:

- `derived` — traces to a specific claim.
- `partial` — the source states the rule but declines to supply parameters, and must
  quote the source admitting it.
- `added` — invented here. Must carry a rationale and must **not** carry a source,
  because it does not have one.

Validation runs at boot, not per request. A rule without a source raises during
startup, the server exits non-zero and a deploy fails. Verified: a container started
against a fixture with one `source` block removed exits with code 3 rather than
serving a broken app.

### Three tiers, with the boundary visible

The call said either hard rules or heuristics would be accepted and that the choice was
itself informative. This takes both and makes the line between them part of the product.

- **Tier 1 — hard rules.** The execution plan. Deterministic, auto-applied, each
  decision citing a sentence. This tier alone satisfies the written brief.
- **Tier 2 — factor heuristics.** Shared sector and market factors. When one moves,
  every exposed position is re-rated. Tier 2 **proposes and never executes.** A human
  accepts or rejects; both the proposal and the response are logged with the actor.
- **Tier 3 — the learned layer.** Not built. Scenario probabilities are fixed priors
  from the memo. The interface says so next to the numbers and names what an estimator
  would replace.

**Override is a first-class logged event.** The memo overrules its own platform rule —
a Neutral spring maps to a starter position, and the memo declines it because *"opening
length into that distribution would be following a rule against the analysis the rule
exists to serve."* An engine that only expresses `rule fires → action` cannot represent
its own source. So the log records what the rule would have done, what happened
instead, why, and who decided — whether that actor is the memo or a person.

### How one event reaches two companies

The memo's Light Cone diagram places each factor on an internal, sector or market ring.
Sector and market factors are ticker-agnostic by construction, so **ring decides
propagation, not name.** A factor shift re-rates every exposed ticker if and only if
the factor sits on the sector or market ring.

The engine-driven pairing is hyperscaler capex turning credit-funded — market ring in
both memos, bearish for NVIDIA's demand and a tailwind for Amazon's funding. One event,
two positions, opposite directions, neither reading invented.

The *most striking* asymmetry is deliberately **not** propagated. Hyperscalers building
their own silicon is a threat to NVIDIA and a moat for Amazon, and both memos place it
on the internal ring. Linking them would mean deciding for ourselves that two
differently-named factors are one force. The research never says that, so the app
displays it with both quotes and states that the engine declines to act on it.

### Determinism

The brief does not ask for determinism. It asks us to *show that it holds*, which is
larger. The decision log is serialised to canonical JSON — sorted keys, fixed
separators, in-world dates only, no execution timestamps — and hashed with SHA-256.

- Two runs in one process must match.
- A run in a **subprocess with `PYTHONHASHSEED` varied** must match. This is the real
  proof; code review can miss a hidden dependence on dict or set iteration order, a
  differently-seeded process cannot.
- Both must match a hash recorded in the test suite, so a change in decision logic
  fails loudly rather than producing a different but self-consistent answer.

And the app has a page that re-runs both scenarios live, so a reviewer does not have to
trust a test file they will never open.

### The two futures

Both turn on disclosures, not prices. The brief requires one; there are two.

- **Guide Holds.** 2026-11-17: FY2028 commentary holds near 70% with backlog detail →
  buy at full weight. Then the position exists, so the $195.00 stop becomes live. One
  weekly close lands at $193.50 and does *not* stop out, because the next week recovers
  and breaks the streak — the memo's own reason for requiring two closes. Two
  consecutive closes later, it exits.
- **Capex Turns.** Commentary neither confirms nor breaks → base row. Then in the
  late-January window, two of four hyperscalers guide capex flat or down → exit. Driven
  by *other companies'* disclosures. This is also where the Amazon fan-out fires.

---

## 5. Key decisions, and why

- **The written brief is the floor, the call is the ceiling.** Meet every written
  requirement literally, because those are the only checkable items; spend the call's
  latitude above that. Candidates who read only the brief ship a rigid toy; candidates
  who only heard the call ship a vague AI demo.
- **Deterministic core, ML marked not built.** Satisfies the determinism proof and the
  call's "show the potential" at the same time, by separating them into tiers.
- **Human in the loop, not an autotrader.** Matches the decision-maker's stated
  philosophy and inverts what "trading application" pattern-matches to.
- **Ring, not name, decides propagation.** Prevents the engine acting on a linkage we
  invented rather than one the research states.
- **Subset transcription with the shortfall on screen.** Nine of 28 factors, stated as
  such, with unknown rings marked rather than guessed.
- **Python engine plus a thin server-rendered UI, no client framework.** Every
  interaction is a form post. A JS library buys nothing here.

---

## 6. What was considered and rejected

- **Hard rules only.** Smallest build, trivially deterministic. Rejected as the sole
  approach: it reproduces the client's own sample demo with better citations and cannot
  show the cross-ticker propagation they asked about.
- **A weighted conviction score.** Flexible and uses the factor weights as designed.
  Rejected because when the answer is "sell" and the question is "why", the honest reply
  becomes "twenty-eight numbers summed to forty-one". That breaks the first requirement.
- **An LLM in the decision path.** Tempting — no transcription, handles the
  unanticipated, reads nuance rules flatten. Rejected because determinism becomes
  unprovable and you lose the ability to point at the sentence. AI was used heavily at
  *build* time and kept out of the runtime entirely.
- **ML on historical outcomes.** Rejected on scope and, more fundamentally, on data:
  the sample size for "what happens when NVIDIA guides FY2028 below 45%" is zero.
- **A probabilistic graphical model over the scenario tree.** The most intellectually
  honest alternative and the natural next step, but the priors would still be the
  memo's hand-set 25/50/25, so it adds opacity without information.
- **An off-the-shelf rules or CEP engine.** Mature temporal operators, but provenance is
  not a first-class concept in any of them, and provenance is the point.
- **A formal state machine library.** Worth naming honestly: **this would have caught
  one of the real bugs statically** — the 17 November partition had a hole that
  exhaustiveness checking would have flagged immediately.
- **A spreadsheet.** Genuinely right for one position and six rules. Loses the audit
  trail, the determinism proof, and any fan-out.

---

## 7. When — how the work actually went

**23 September — reading and design.** No code. The source documents and the call
transcript were read first, decisions logged turn by turn in
`docs/decisions/notepad.md`, then a task inventory was approved and written to
`TODO.md`, followed by an ADR and a build spec. This day is why the build day went
quickly, and it is where the findings that shaped the architecture came from.

**24 September — the build.** 35 commits. Scaffold and deploy config, fixture schema,
transcription, the Tier 1 engine, override modelling, the Tier 2 factor layer, both
timelines, the determinism proof, the test suite, the read-only views, the timeline
view, the write-up, and containerisation.

**25 September — review and polish.** Interface redesign, the defects that surfaced
from it, and the reviewer note.

### What was found along the way

Fifty-five tracked items: 19 features, 18 bugs, 17 issues, 1 wishlist. **Most of the bugs
were found in our own work, by checking claims against the source rather than reading
the code.** The pattern is worth stating because it is the same failure repeating:

- The headline cross-ticker example in the spec paired two **internal-ring** factors, so
  it could never have driven the engine. It was a name match, not a mechanism.
- The stop's "two consecutive periods" carried no unit, so on a daily series it would
  have fired on two consecutive days — defeating exactly what the memo says the
  confirmation is for.
- The 17 November rules overlapped and fired two contradictory actions at 72%. Fixing
  that by bounding the range then opened the opposite hole, where commentary at or above
  70% *without* backlog detail matched nothing and the system silently made no decision
  on the one date the whole thesis resolves on.
- The fail-fast guarantee was documented but never wired in: no startup hook existed, so
  the app would have booted, passed a health check, and 500ed on every real page.
- The rule-logic display added during the redesign understated grouped rules, making the
  base row read as firing in a case the re-entry rule takes.

Five of these are the same shape: **a constraint the memo states precisely, encoded as
something the engine could not evaluate.** The transcription was faithful to the words
and lossy on the logic. That is easy to do when the source is this well written,
because the prose reads like a spec and copying it feels like encoding it.

---

## 8. Honest limits

- **Transcription is manual and does not scale.** Nine of 28 factors. A portfolio means
  either a lot of human effort or the automated extraction the brief put out of scope.
- **Rules only fire on anticipated events.** A genuinely novel disclosure produces
  silence. Mitigated only in that the silence is visible — the timeline shows the event
  and shows nothing fired.
- **The memo's ambiguity relocates, it does not vanish.** *"Near 70%"* became `>= 70`.
  That is a judgement. It sits next to its quote so a reader can disagree, but it is
  still ours.
- **Accepting a Tier 2 proposal records the decision without re-running the engine.**
  Correct against the constraint; less than a reviewer might expect.
- **Proposal responses are in memory**, not persisted. Single-user demo.
- **Web fonts load from Google at render time.** Offline, every page falls back to
  system fonts and the typographic identity disappears — quietly, because `display=swap`
  hides it.

---

## 9. What's next

Immediately: deploy, and self-host the fonts.

Beyond that, in the order the design would want them:

- **A learned Tier 3** — scenario priors re-estimated as disclosures land, with the
  estimator required to expose *why* it moved a probability, the same way
  `provenance_status` exposes why a rule is partial.
- **A formal state machine** with exhaustiveness checking, which would catch the class
  of bug that got through twice here.
- **More tickers**, which makes automated extraction with human review unavoidable.
- **Real market data**, which turns the price path into a feed and requires pinned input
  snapshots for the determinism proof.
- **Multiple analysts**, which gives overrides an identity and turns the log into
  durable storage.

---

## 10. Running it

```bash
docker compose up --build          # http://localhost:8000 — the image Render builds
```

```bash
uv sync                            # or natively
uv run uvicorn app.web.main:app --reload
uv run pytest
```

Render reads `render.yaml`, which uses the Docker runtime and sets the health check
path. It does **not** read `docker-compose.yml`; compose exists so you can run locally
exactly what the platform runs.

Verified before committing: the image builds at 138MB, runs as a non-root user, binds
`0.0.0.0` on an injected `PORT`, serves every route, stops gracefully in ~0.6s, and
exits non-zero on invalid fixtures.

---

## 11. Where everything lives

| File | What |
|---|---|
| `PROJECT.md` | This document. Start here. |
| `SUBMISSION.md` | The half-page note for reviewers with limited time. |
| `README.md` | Running it, and the full list of assumptions. |
| `HOW_IT_WORKS.md` | The design walkthrough and the rejected approaches, at length. |
| `WHERE_THIS_GOES_NEXT.md` | The learned layer, the gaps, the next build. |
| `TODO.md` | All 51 items, including every defect found and closed. |
| `docs/decisions/notepad.md` | The working log, turn by turn, including what was wrong and when. |
| `docs/adr/` | The tiered-engine architecture decision. |
| `docs/specs/` | The build spec. |
