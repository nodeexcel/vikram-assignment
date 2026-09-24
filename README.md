# Lexo trading decision system

Turns the Lexo NVIDIA research artifacts into a deterministic decision system that
shows its reasoning.

**Deployed:** _<paste the Render URL here once the service is live>_

---

## The three questions

The brief asks that someone open the app and answer three questions unaided. Each
has its own page.

| Question | Page |
|---|---|
| What does the research actually conclude? | `/research` |
| What rules were derived, and where did each come from? | `/rules` |
| What would the system do, when, and why? | `/timeline/guide_holds` and `/timeline/capex_turns` |

Two more: `/determinism` re-runs both scenarios and shows the hashes side by side,
and `/where-this-goes-next` covers where a learned layer would go and what the
source could not supply.

## Run it

```bash
uv sync
uv run uvicorn app.web.main:app --reload
uv run pytest
```

## How it decides

Three tiers, with the automation boundary deliberately visible — see
`docs/adr/ADR-20260924-1250-tiered-decision-engine.md`.

- **Tier 1, hard rules.** Transcribed from the memo's Execution Plan. Deterministic,
  auto-applied, every decision citing a specific sentence with its page.
- **Tier 2, factor heuristics.** Sector- and market-ring factors are shared state; a
  shift re-rates every exposed ticker. Tier 2 **proposes and never executes** — a
  human accepts or rejects, and both the proposal and the response are logged.
- **Tier 3, the learned layer.** Not built. Scenario probabilities are fixed priors
  from the memo, labelled as such in the interface.

`app/engine` is a pure library with no web imports. That is what makes the
determinism proof cheap: `run(rules, events, overrides, factors)` is a pure function.

## Assumptions

Stated plainly, because the brief says anything not in the source documents is a
decision we are making.

1. **NVDA is the subject; AMZN is present only for cross-ticker fan-out.** AMZN
   carries two factor exposures and no rules of its own.
2. **Rules come from the memo, never from the call transcript.** The transcript's
   speech-to-text rendered the exit trigger as "any hyperscaler… below 45"; the memo
   says **any two** of four, and 45% is a **growth rate**, not $450B.
3. **Ring, not name, decides propagation.** A factor fans out only if the memo's own
   Light Cone diagram places it on the sector or market ring. Where a promoted factor
   has no Light Cone entry its ring is recorded as `unknown` and it is excluded from
   propagation rather than inferred. The custom-silicon asymmetry — a threat to NVDA,
   a moat for AMZN — is real and sourced but sits on the internal ring in both memos,
   so it is displayed on `/rules` and explicitly **not** propagated.
4. **Scenario event paths are simulated; the rules they exercise are derived.** The
   $195.00 level, the two-consecutive-weekly-close confirmation and the holders-only
   condition all come from the memo. The weekly closes in `guide_holds` are a
   hypothetical future shaped to exercise them.
5. **Only 9 of NVDA's 28 Light Cone factors are transcribed** — all 8 of the memo's
   weighted composition factors plus one used for the fan-out. The interface says so
   on `/rules` and names what is missing. The brief puts PDF parsing out of scope, so
   fixtures are hand-transcribed and depth was traded for correctness.
6. **Accepting a Tier 2 proposal records the decision; it does not re-run the
   engine.** The ADR requires that nothing move a position without a logged human
   decision. It does not require acceptance to act, and within the time box it does
   not.
7. **Proposal responses are held in memory**, not persisted. Single-user demo; the
   brief puts auth and multi-user out of scope.

## Deploying

`render.yaml` is a Render blueprint. Connect the repo as a Blueprint in the Render
dashboard; build and start commands and the Python version are already set. The
clean-install path (`pip install -r requirements.txt`, then the start command) has
been verified from a fresh virtualenv.

## Where the rest of the thinking is

- `docs/decisions/notepad.md` — the full discussion log, turn by turn, including
  what was rejected and why
- `docs/specs/FEAT-20260924-1250-lexo-trading-decision-system.md` — the build spec
- `docs/adr/ADR-20260924-1250-tiered-decision-engine.md` — the architecture decision
- `TODO.md` — every item, including the defects found and closed along the way
- `WHERE_THIS_GOES_NEXT.md` — where this goes next
