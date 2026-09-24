# Spec — Lexo trading decision system

- **Covers:** all items in `TODO.md` (FEAT/ISS-20260924-1250-01 … -14)
- **ADR:** `docs/adr/ADR-20260924-1250-tiered-decision-engine.md`
- **Discussion history:** `docs/decisions/notepad.md` Turns 1–4
- **Branch:** `master` (base: `master`) — commit directly to the checked-out branch.
  Do not create, switch or merge branches; that is human-directed per CLAUDE.md Module 7.
- **Deadline:** Friday 2026-09-25.

---

## 1. What is being built

A web application that turns the Lexo NVIDIA research artifacts into a deterministic
decision system and shows its reasoning. A stranger opens the URL and answers three
questions unaided:

1. What does the research actually conclude?
2. What rules were derived from it, and where did each one come from?
3. What would the system do, when, and why?

**Ticker scope:** NVDA in depth; AMZN thin, solely to demonstrate cross-ticker
factor propagation.

---

## 2. Requirement traceability

Written-brief requirements and where each is satisfied. Nothing here is optional.

| Requirement | Satisfied by |
|---|---|
| Rules derived, not invented; each traces to a claim | Fixture schema §5 — no rule loads without doc/page/quote. UI §9 shows the quote. |
| Anything not traceable is flagged in the interface | §5.3 `provenance_status`; the hedging rule is a real instance. |
| Decides over time: hold, size, stop | Tier 1 engine §6 over a dated event timeline. |
| ≥2 divergent futures, ≥1 non-price | §8 — both futures are disclosure-driven. |
| Determinism, demonstrated | §7 — canonical hash of the decision log, as a test and as a visible check. |
| Explainability at any point in time | §9 timeline view, plain-language reason per decision. |
| Tests on the decision logic specifically | §10. |
| Deployed at a URL | §11 — Render, stood up first, not last. |

---

## 3. Verified source facts

Read from `NVDA-memo.pdf` via `pdftotext -layout` during Turn 3. **Page numbers below
are from the memo's own `N · 92` footers and are indicative; the implementor
re-verifies every page and quote at transcription time and corrects this table if it
is wrong.** Fixtures follow the memo, never the call transcript.

As-of 2026-09-08. Reference price **$230.36** (2026-09-04 close, re-confirmed
2026-09-08).

**Stance.** Hold · Low conviction · no position initiated. Horizon 6–12 months
tactical. Spring state Neutral; the platform rule for Neutral is a starter position,
**deliberately overridden**.

**Two horizons, which the memo forbids conflating** — *"different measures on
different clocks and neither substitutes for the other"*:

- 3–5yr intrinsic: probability-weighted $136.78 vs price → **−40.6%**
- 6–12mo tactical: probability-weighted 12-month return **−13.1%**, or **−9.7%** with
  the $195.00 stop applied

**Intrinsic scenarios (memo ~p.44):** Bear 25% $78.83 (−65.8%) · Base 50% $139.24
(−39.6%) · Bull 25% $189.80 (−17.6%) · Weighted $136.78 (−40.6%). The bear 25% is
itself 15% competitive + 10% geopolitical.

**12-month price targets (memo ~p.45):** Bull $236.54 (+2.7%) · Base $200.09 (−13.1%)
· Bear $164.07 (−28.8%).

**Execution plan (memo ~p.46) and the three dates (memo ~p.47):**

| When | Trigger | Transition |
|---|---|---|
| 2026-11-17 (company-confirmed) | FY2028 commentary near 70% **with backlog detail** | → Buy at **full** weight (re-entry trigger) |
| 2026-11-17 | commentary below 45% | → bear row |
| 2026-11-17 | neither confirms nor breaks | → base row, drift toward $200.09 |
| 2027-01-26 → 2027-02-06 (est.) | **any two of the four** large hyperscalers guiding capex flat or down YoY | → exit / short trigger |
| ~2027-02-24 (est.) | formal FY2028 guide **below 45% growth** | → Sell |
| continuous | $195.00 on **two consecutive weekly closes** | → stop. **Existing holders only.** |

**Four kill switches (memo ~p.38),** separate from the weighted factor set, each with
a watch cadence: frontier training run on non-NVIDIA silicon (continuous, 2027–28) ·
networking attach convergence within ~10 points for two consecutive quarters
(quarterly, 2027) · Taiwan Strait interruption (unhedgeable before TSMC Arizona mass
production, 2028) · cash conversion below 65% unadjusted or 78% adjusted for two
consecutive quarters with accruals above 20% (current 69.7% / ~83.6% / 18.3%).

**Factor set.** 28 factors — 10 positive, 13 negative, 5 other. Two orthogonal
classifications, both in the source:

- **Force type:** Wind (temporary, 1–4 quarters) · Wave (secular, multi-year) · Mud
  (structural). Each carries an IMPACT score 0–1.
- **Light Cone ring:** Internal (1–10) · Sector (11–17) · Market (18–28).

Selected weights of 100: Guidance Bet 21 · Share Ceded to Custom Silicon 20 ·
Rack-Scale Platform Lock-In 17 · Demand Is Credit-Funded 13 · Founder-Led/Unplanned
Succession 8 · Operating Leverage Already Spent 5. *"Three factors sit on the external
circle and together carry 54 of the 100 weight points."*

**Cross-ticker factor pairings.** Ring assignments re-verified against both memos'
Light Cone diagrams on 2026-09-24. **Ring, not name, decides whether a pairing can
propagate** — §6.5 fans out on sector and market factors only.

*Corrected 2026-09-24. An earlier revision of this table named the custom-silicon
pairing as the headline engine-driven demo. That was wrong: both sides sit on the
Internal ring and cannot propagate under our own rule. See BUG-20260924-1322-15.*

**Engine-driven fan-out — ring-legal, use these:**

| Mechanism | NVDA | AMZN | Ring | Signs |
|---|---|---|---|---|
| Hyperscaler capex turning credit-funded | #22 Hyperscaler Capex Financing Shift — **Wave −** | #24 Open Credit Funding AI Cloud Customers — **Tailwind** | Market ↔ Market | **opposite** |
| AI infrastructure buildout | #11 AI Infrastructure Buildout Wave — Wave + | #12 AI Infrastructure Demand Wave — Wave + | Sector ↔ Sector | same |

The capex-financing pairing is the headline: one event, two positions, **opposite
directions**, both sourced. The AI-buildout pairing is included deliberately as a
same-sign case, so the interface does not imply that fan-out is always contrarian.

NVDA carries the capex-financing force at two rings on purpose, and the memo says so
in its own audit note on #16: *"This force is carried twice."* #16 Hyperscaler Capex
Turns Debt-Funded sits on Sector, #22 Hyperscaler Capex Financing Shift on Market.
Use #22 for the AMZN pairing, since AMZN's counterpart #24 is Market ring.

**Sourced but NOT engine-propagated — must be shown, and shown as such:**

| Mechanism | NVDA | AMZN | Ring |
|---|---|---|---|
| Hyperscalers building their own silicon | #5 Inference Share Loss to Custom Silicon — **Wave −** | #2 Custom Silicon Margin Moat — **Wave +** | Internal ↔ Internal |

This is the most striking asymmetry in the two memos — the same real-world mechanism
is a threat to one holding and a moat to the other, each stated in its own source. It
is also **Internal ring on both sides, so the engine does not and must not propagate
it.** Linking the two would mean deciding for ourselves that these are the same force;
the research never says so, and inventing that linkage is precisely what the brief
prohibits.

Show it anyway, labelled as a human-observed linkage the engine deliberately declines
to act on, with both quotes. A system that shows where its own reasoning stops is more
credible than one that quietly drops the inconvenient case — the same move the memo
makes when it admits it never sourced an options chain. Tracked as
FEAT-20260924-1322-16.

Also noted, not paired: NVDA #13 Custom ASIC Substitution *is* Sector ring, but AMZN's
factor set carries no sector-ring counterpart for it, so it has nothing to fan out to.
Recorded so this is not re-litigated.

---

## 4. Design rationale

Three findings from the source drive the design. Full reasoning in notepad Turn 3.

**The memo is already a decision system written in prose.** Triggers carry a metric,
a threshold and a timeframe. We transcribe a state machine; we do not interpret one
into existence. This makes "derived, not invented" honest rather than aspirational.

**The memo overrides its own platform rule and states why** — *"A Hold means hold...
opening length into that distribution would be following a rule against the analysis
the rule exists to serve."* An engine that can only express `rule fires → action`
cannot represent its own source. Override is therefore a first-class logged event
(§6.4), which also implements the human-in-the-loop philosophy from the call.

**The memo names a rule whose parameters it could not source.** On hedging: IV rank
0–9 of 100 justifies hedging existing exposure through the 2026-11-17 print and the
late-February 2027 window — but *"no strike, expiry or premium is named anywhere here:
no options chain was sourced for this workbook."* The brief requires flagging
anything not traceable to source. This is a genuine instance where the source itself
declares the gap, and it is better evidence of the discipline than an invented
example. Carry it as `provenance_status: partial` with the memo's own admission shown.

---

## 5. Data model

### 5.1 Repo layout

```
app/
  engine/           # pure Python. NO web imports. importable and testable alone.
    models.py       # Pydantic fixture models
    loader.py       # load + validate fixtures, fail loud
    rules.py        # Tier 1 evaluation
    factors.py      # Tier 2 propagation -> proposals
    timeline.py     # event ordering and the run loop
    log.py          # append-only decision log + canonical hash
  web/
    main.py         # FastAPI app
    templates/      # Jinja2
    static/
fixtures/
  nvda/             # research.yaml, rules.yaml, factors.yaml, catalysts.yaml, scenarios.yaml
  amzn/             # factors.yaml, research.yaml (thin)
  timelines/        # guide_holds.yaml, capex_turns.yaml
sources/
  text/             # gitignored, regenerated by the script below
scripts/
  extract_sources.sh
tests/
docs/
```

`app/engine` must not import from `app/web`. The engine is a library; the web layer
is a shell over it. This is what keeps the determinism proof clean and cheap.

### 5.2 Every claim carries provenance

```yaml
source:
  doc: NVDA-memo            # NVDA-memo | NVDA-theme | NVDA-factor | AMZN-memo
  page: 46
  quote: "$195.00 on two consecutive weekly closes = -15.3% from $230.36"
```

### 5.3 Provenance status

Every rule and factor carries one of:

- `derived` — traces to a specific claim; quote present.
- `partial` — the source states the rule but declines to supply parameters. Must
  carry `gap_note` quoting the source's own admission. The hedging rule is the one
  known instance.
- `added` — not in the source. Must carry `rationale`. **The UI renders these
  distinctly and says plainly that they were added by us.** Prefer zero of these;
  if a build shortcut needs one, it is visible, not buried.

### 5.4 Fail-fast validation (CLAUDE.md Module 4)

Fixture loading validates at startup. A rule or factor missing `source`, or carrying
`provenance_status: added` without `rationale`, or `partial` without `gap_note`, is a
**startup error**. The app does not boot with an unsourced rule. No default that
"works" with bad config.

---

## 6. Engine semantics

### 6.1 Events

An event is `{date, kind, ticker|null, payload, source}`. Kinds: `disclosure`,
`guidance`, `third_party_guidance`, `price_close`, `factor_shift`. Events come from
scenario timeline fixtures. No live data, no network at runtime.

### 6.2 The run loop

Sort events by `(date, kind, ticker)` — a total order, no ties, so iteration order can
never vary. For each event: evaluate Tier 1 rules, then Tier 2 factors. Append every
outcome to the decision log. Pure function: `run(fixtures, timeline) -> DecisionLog`.
No wall-clock reads, no RNG, no dict-ordering dependence, no `set` iteration in any
path that affects output.

### 6.3 Tier 1 rules

Declarative predicates over event payload and engine state. Each rule declares
`applies_when` (notably `position != none` for the stop — the memo is explicit that
the stop is for existing holders only) and carries its source.

**Shared primitive: `consecutive_periods(n)`.** The `$195.00 on two consecutive weekly
closes` stop and two of the four kill switches all use two-consecutive-period
confirmation. Implement once, from the source pattern. The memo states the reason:
*"The two-close confirmation exists so a single volatile week around an earnings print
does not trigger the exit."*

### 6.4 Override

An override is a logged record: `{rule_id, would_have_done, actual, reason, source,
actor}`. Two kinds exist:

- **Source override** — the memo's own. Neutral spring → platform rule says starter
  position → memo declines, with its stated reason. Present from the first run,
  sourced to the memo, `actor: memo`.
- **Human override** — a user rejecting a Tier 2 proposal. `actor: user`.

Both render in the timeline as "this rule fired, here is what it would have done,
here is why it did not."

### 6.5 Tier 2 factors

**A factor is shared, ticker-agnostic state. It does not belong to a ticker.** Each
factor carries its ring, force type and identity once; direction, impact, weight and
provenance are recorded **per ticker**, because the same force is bearish for one
holding and bullish for another. A schema with a single `ticker` and a single
`direction` field cannot express the fan-out and will need reworking — this is what
BUG-20260924-1322-17 records.

```yaml
id: hyperscaler_capex_financing_shift
ring: market                  # internal | sector | market
force: wave                   # wind | wave | mud
label: "Hyperscaler capex turning credit-funded"
exposures:
  NVDA:
    local_id: 22
    local_name: "Hyperscaler Capex Financing Shift"
    direction: negative
    impact: 0.80
    weight: 13                # omit where the memo assigns none
    source: {doc: NVDA-memo, page: 6, quote: "..."}
  AMZN:
    local_id: 24
    local_name: "Open Credit Funding AI Cloud Customers"
    direction: positive
    impact: ...
    source: {doc: AMZN-memo, page: ..., quote: "..."}
```

`local_id` and `local_name` exist because the two memos number and name the same
force differently. The shared `id` is ours; every per-ticker name and number stays
verbatim from its own source, and the interface shows the source's wording, not ours.

**Ring decides propagation, not name.** A `factor_shift` event on a factor whose ring
is `sector` or `market` re-rates every ticker in that factor's `exposures` — read off
the ring assignment rather than modelled by us. A factor on the `internal` ring never
propagates, **even when an equivalent force appears under a different name in another
ticker's internal set.** Matching those would be our judgement, not the research's.
See §3 for the one known case and how it is surfaced instead.

Output is a **proposal**: `{factor, affected_tickers, direction_per_ticker, reasoning,
source_per_ticker}`.

**A proposal never mutates a position.** It waits for accept or reject. Both outcomes
append to the decision log with the actor recorded. This constraint comes from the
ADR and may not be relaxed.

### 6.6 Tier 3

Not implemented. Scenario priors (25/50/25) are fixture values with their source
cited. The UI states they are fixed priors and names what a learned estimator would
replace. No model, no training, no inference.

---

## 7. Determinism

Canonicalise the decision log — sorted keys, fixed float formatting, no timestamps of
execution, only in-world dates — serialise, SHA-256.

- **Test:** for each scenario, run twice in one process and once in a subprocess with
  `PYTHONHASHSEED` varied; assert all three hashes are equal.
- **In the app:** a visible control that re-runs the active scenario and displays both
  hashes side by side with a match indicator. The brief says *"show us that it
  holds"* — so it is shown, not asserted.

Record the expected hash per scenario in the test suite, so an accidental change to
decision logic fails loudly rather than silently producing a different-but-stable
answer.

---

## 8. The two divergent futures

Both turn on disclosures, not prices. The brief requires at least one; we have two.

**Future A — "Guide Holds".** 2026-11-17: FY2028 commentary holds near 70% with
backlog detail. Re-entry trigger fires → Buy at full weight. Driver: an **issuer
disclosure**.

**Future B — "Capex Turns".** 2026-11-17: commentary neither confirms nor breaks →
base row, drift toward $200.09. Price path may cross $195.00; the two-consecutive-
weekly-close confirmation governs whether the stop fires, and it only applies to an
existing holder. Then 2027-01-26 → 2027-02-06: two of the four large hyperscalers
guide capex flat or down → exit trigger. Driver: **third-party disclosures from
companies that are not the issuer** — the strongest possible reading of "not a price".

Future B is also where the AMZN fan-out fires: the same hyperscaler-silicon shift is
Wave − for NVDA and Wave + for AMZN, so one event produces two proposals with
opposite sign.

**Stretch, not committed:** a third path for the geopolitical route. The memo carries
it at 10% weight and explicitly declines to model it as a cash-flow path. Showing a
visibly unmodelled path would be a further provenance win. Build only if items 1–14
are done.

---

## 9. Interface

Server-rendered Jinja2 over FastAPI. Plain form posts, full page reloads. **No HTMX,
no client framework** — every interaction (choose scenario, step the timeline, accept
or reject a proposal) is a form post, and a JS library buys nothing here.

Three views, mapped to the brief's three questions.

**1 — What the research concludes.** Verdict, stance, both horizons shown *separately*
with the memo's own warning that they are different clocks. Both scenario tables. The
three dates. Everything cited.

**2 — Rules and their sources.** Every rule with its verbatim quote, doc and page.
Bidirectional: from a rule to its claim, and from a claim to the rules it produced.
Provenance status rendered distinctly for `partial` and `added`. On this page: the
honest factor-coverage line — **"N of 28 factors transcribed"**, naming which are
missing and why.

**3 — Timeline.** Pick a scenario, step through dated events. At each point: what the
system did, why, which rule, which quote, and what it would have done otherwise.
Overrides shown explicitly. Tier 2 proposals shown with accept/reject. The determinism
check lives here.

Plain language throughout — the brief says a non-engineer must follow it. No rule IDs
as primary labels, no jargon in the reason text.

---

## 10. Tests

`pytest`. Decision logic only; no UI tests.

- Trigger boundaries: 69.9% vs 70% commentary; 44.9% vs 45% guide; one, two and three
  hyperscalers guiding down (the rule is *two* of four).
- `consecutive_periods`: one close below $195 does not fire; two consecutive do; two
  non-consecutive do not.
- Position-conditional: the stop does not fire with no position held.
- Override: the Neutral-spring rule fires and is overridden; the log records both.
- Fan-out sign: one hyperscaler-silicon event yields NVDA negative and AMZN positive.
- Tier 2 never mutates a position without a recorded human decision.
- Determinism hashes (§7).
- Fixture validation: an unsourced rule fails startup.

---

## 11. Deployment

Render free tier, Python environment, `uvicorn app.web.main:app --host 0.0.0.0 --port
$PORT`. Dependencies pinned in `requirements.txt` generated by `uv pip compile`.

Validated against local Python 3.13.11 with `uv` on 2026-09-24 — resolved, not
recalled:

```
fastapi==0.141.1  starlette==1.7.0  uvicorn==0.53.0
jinja2==3.1.6     pydantic==2.13.5  pytest==9.1.1
```

**Stand the deploy up first, before engine code** (TODO item -01). Cold starts on the
free tier are accepted; this is a demo, not a service.

---

## 12. Out of scope

Per the brief: PDF parsing at runtime (hand-transcribed fixtures only), live market
data, broker or order integration, authentication and multi-user, statistically
serious backtesting, trained models, native or mobile apps.

---

## 13. Risk and cut order

One working day. The likeliest failure is spending it on transcription and shipping no
URL.

**Cut depth of transcription before cutting capability.** Fewer factors, honestly
disclosed on screen, is a far smaller loss than a system that cannot show an override
(item -07) or cannot fan out across tickers (item -08) — those are what distinguish
this from the client's own sample demo.

Must-have floor, satisfying every written requirement with a live URL: items -01, -02,
-03, -06, -09, -10, -11, and a reduced -12.

Differentiators to defend: -07, -08, -13, the AMZN half of -05, and -14. Item -14 is
cheap and disproportionately valuable — the call stated that the thinking and the
stated direction are graded as heavily as the code.
