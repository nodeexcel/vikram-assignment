# Lexo trading assignment — submission

**Live:** _<Render URL>_
**Repo:** https://github.com/nodeexcel/vikram-assignment

A deterministic decision system built from the NVIDIA memo, theme report and factor
report. Open the URL and you can answer the three questions in the brief without
asking me anything.

---

## If you have two minutes

Three things, in the order I'd look at them.

**1. The memo overrules its own rule, and the system can say so.**
`/rules` → Overrides. The platform's entry logic maps a Neutral spring to a starter
position. The memo declines it: *"opening length into that distribution would be
following a rule against the analysis the rule exists to serve."* An engine that only
expresses `rule fires → action` cannot represent that sentence. So an override is a
first-class logged event carrying what the rule would have done, what happened
instead, why, and who decided. Most rule engines can only express compliance.

**2. One disclosure, two positions, opposite directions.**
`/timeline/capex_turns`. Hyperscaler capex turning credit-funded is market-ring in
both memos — bearish for NVIDIA's demand, a tailwind for Amazon's funding. The same
event re-rates both, in opposite directions, and neither reading is mine; each is
quoted from its own memo.

**3. The most interesting pairing is one the engine refuses to act on.**
`/rules` → "Human-observed but not engine-propagated". Hyperscalers building their own
silicon is a *threat* to NVIDIA and a *moat* for Amazon — the sharpest asymmetry in
the two documents. Both memos place it on the Internal ring, and the system only
propagates sector and market ring factors. Linking them would mean deciding for
myself that two differently-named factors are one force, which the research never
says. So the page shows it, with both quotes, and states plainly that the engine
declines to act on it.

That third one is the submission in miniature. Showing where the reasoning stops is
worth more than a demo that quietly papers over it.

---

## The idea the build rests on

The memo is already a decision system. It is just written in English — an execution
plan with a stop, a re-entry trigger and an exit trigger; three dates that change the
rating, each with a metric, a threshold and a timeframe; four kill switches with watch
cadences.

So I transcribed a state machine rather than inventing one. Every rule cites a page
and a sentence, and the application **refuses to start** if any rule lacks a source.
The risk was never inventing a rule — it was *flattening* one, taking a sentence with
a confirmation requirement and an exception and encoding only the number. That
happened repeatedly and each instance is in the commit history.

---

## On machine learning

Deliberately not in the decision path, and the interface says so next to the numbers
it affects.

The scenario probabilities — 25 / 50 / 25 — are the only values here a model could
sensibly produce. They are currently constants from the memo, frozen at its
publication date. `/where-this-goes-next` names a concrete buildable estimator that
would re-weight them as disclosures land.

I kept it out of runtime for three reasons, in order. There is nothing to learn from:
this is one company resolving on two future catalysts, so the sample size for "what
happens when NVIDIA guides FY2028 below 45%" is zero. It would break the one
requirement that is checkable — you cannot *show* determinism holds with a model in
the loop, and `/determinism` re-runs both scenarios live and compares hashes. And the
call asked for the seed, not the plant.

AI did most of the reading. 280 pages of source, cross-checking claims, and catching
my own errors — including a headline example I had wrong for half a day. It is simply
not in the runtime.

---

## What I'd want you to know before you judge it

- **9 of 28 factors are transcribed**, and the app says so on screen, names what is
  missing, and marks a factor's ring `unknown` rather than guessing when the source
  does not state it. PDF parsing was out of scope, so this was hand work and I traded
  depth for correctness.
- **One rule is marked `partial`** because the memo itself admits it never sourced an
  options chain. The brief asks for anything unsourced to be flagged; the source
  handed me a real instance.
- **Accepting a Tier 2 proposal records the decision without re-running the engine.**
  Correct against the constraint that nothing moves a position without a logged human
  decision, and less than you might expect.
- Full assumptions are in the README.

---

## Where the thinking is, if you want it

- `PROJECT.md` — the whole project in one document: task, reasoning, architecture,
  timeline, findings, limits. If you only open one file, open that one

- `HOW_IT_WORKS.md` (also at `/how-it-works`) — how it works, what it buys, and the
  seven approaches I considered and rejected, including the one that would have caught
  one of my own bugs statically
- `WHERE_THIS_GOES_NEXT.md` (also at `/where-this-goes-next`) — where the learned layer
  attaches, what the source could not supply, what I would build next
- `docs/decisions/notepad.md` — the working log, turn by turn, including what I got
  wrong and when
- `TODO.md` — every item, including the defects I found in my own work and closed

Run it locally with `docker compose up --build`, or `uv sync && uv run uvicorn
app.web.main:app`. Tests: `uv run pytest`.
