# Lexo trading decision system

Turns the Lexo NVIDIA research artifacts into a deterministic decision system that
shows its reasoning.

**Deployed:** https://vikram-assignment.onrender.com/

---

## The three questions

The brief asks that someone open the app and answer three questions unaided. Each
has its own page.

| Question | Page |
|---|---|
| What does the research actually conclude? | `/research` |
| What rules were derived, and where did each come from? | `/rules` |
| What would the system do, when, and why? | `/timeline/guide_holds` and `/timeline/capex_turns` |

Three more: `/determinism` re-runs both scenarios and shows the hashes side by side,
`/how-it-works` is the design walkthrough — how the system works, what it buys, and
the approaches weighed and rejected — and `/where-this-goes-next` covers where a
learned layer would go and what the source could not supply.

## Run it

Natively:

```bash
uv sync
uv run uvicorn app.web.main:app --reload
uv run pytest
```

Or in the container that actually ships:

```bash
docker compose up --build        # http://localhost:8000
```

Compose runs the same image and the same command Render runs, with `PORT`
injected the same way, so the `$PORT` path is exercised locally rather than only
in production. **Render does not read `docker-compose.yml`** — it builds the
`Dockerfile` directly. Compose exists so you can run what you ship, not so the
platform can consume it.

`/health` reports what actually loaded — tickers, rule count, factor count and
events per scenario — rather than merely that a socket is open. It is the
blueprint's `healthCheckPath`.

Fixtures are validated at boot, not lazily. A rule missing its source raises
during startup, the server exits non-zero, and the deploy fails. Verified: a
container started against a fixture with one `source` block removed exits with
code 3 rather than serving a broken app.

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

`render.yaml` is a Render blueprint using the Docker runtime. Connect the repo as a
Blueprint in the Render dashboard; the Dockerfile path, build context and health
check path are already set, and the Python version comes from the base image rather
than any platform setting.

Verified locally before committing: the image builds (138MB), runs as a non-root
user, binds `0.0.0.0` on an injected `PORT` of 10000, serves all nine routes,
reports healthy, stops gracefully in ~0.6s because `exec` in the entrypoint lets
`SIGTERM` reach uvicorn, and exits non-zero when fixtures are invalid.

## Where the rest of the thinking is

- `docs/decisions/notepad.md` — the full discussion log, turn by turn, including
  what was rejected and why
- `docs/specs/FEAT-20260924-1250-lexo-trading-decision-system.md` — the build spec
- `docs/adr/ADR-20260924-1250-tiered-decision-engine.md` — the architecture decision
- `PROJECT.md` — **start here.** The whole project in one document: the task, why it
  was built this way, how it works, when the work happened, and what came out
- `SUBMISSION.md` — the half-page note for reviewers: what to look at first, and why
- `TODO.md` — every item, including the defects found and closed along the way
- `HOW_IT_WORKS.md` — how the system works, why it is built this way, and the
  approaches considered and rejected (served at `/how-it-works`)
- `WHERE_THIS_GOES_NEXT.md` — where this goes next (served at `/where-this-goes-next`)
