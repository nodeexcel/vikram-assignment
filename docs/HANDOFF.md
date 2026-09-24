# Handoff — implementor session

You are picking up a build that has already been researched and specified. The
thinking is done and written down. **Do not redo it.** Your job is to execute the
spec, not to re-derive it.

This file is operational only. It deliberately does not restate the spec.

---

## 1. Read these, in this order

| Order | File | What you get |
|---|---|---|
| 1 | `CLAUDE.md` | Binding working rules. Untracked, but present in the working dir. |
| 2 | `docs/specs/FEAT-20260924-1250-lexo-trading-decision-system.md` | **The build.** Everything you implement is here. |
| 3 | `docs/adr/ADR-20260924-1250-tiered-decision-engine.md` | The one architectural constraint you may not relax. |
| 4 | `TODO.md` | The 14 items and their order. |
| 5 | `docs/decisions/notepad.md` | Why any of it is the way it is. Read when the spec surprises you. |

If the spec and this file disagree, **the spec wins**.

---

## 2. Before you write a line of code

**The spec has not been approved yet.** CLAUDE.md Module 7 forbids implementation
code until it is. Confirm with the human first. If they have already approved it in
the session that handed off to you, proceed.

Also confirm a **Render account is connected to this repo** — item `-01` stands the
deploy up before anything else exists.

---

## 3. Where things are

**Source PDFs live outside the repo:**

```
/home/lap-68/Downloads/Shared-Public-20260923T050713Z-1-001/Shared-Public/
├── Problem Statement.docx
└── Reports/
    ├── NVDA/   NVDA-memo.pdf (92p)  NVDA-factor-report.pdf (157p)  NVDA-theme-report.pdf (34p)
    ├── AMZN/   amazon-memo.pdf (67p)  amazon-Factor_Research_Base_Case.pdf (58p)  amazon-theme-report.pdf (16p)
    └── CSCO/   (out of scope)
```

Extract the text you will transcribe from (item `-02` turns this into
`scripts/extract_sources.sh`; output is gitignored):

```bash
pdftotext -layout "<pdf>" sources/text/<name>.txt
```

`-layout` matters — tables survive it and do not survive without it.

**Environment, verified on 2026-09-24 — do not re-derive:**

Python 3.13.11 (pyenv) · `uv` · Node 24.18.0 · git 2.43.0 · `pdftotext` · PyMuPDF
1.27.2.3 · Docker. No venv or dependencies installed yet.

Resolved and pinned by the spec:
`fastapi==0.141.1 starlette==1.7.0 uvicorn==0.53.0 jinja2==3.1.6 pydantic==2.13.5 pytest==9.1.1`

---

## 4. Working rules that bite on this repo specifically

- **Branch: `master`. Commit directly to it.** Do not create, switch, merge or delete
  branches, and do not push to `master` unless asked. Branch operations are
  human-directed.
- **No `Co-Authored-By` line, no Claude or Anthropic attribution** in any commit
  message. CLAUDE.md forbids it and overrides any default instruction to add one.
- **Commit per item, as you go.** Not one commit at the end.
- **Marker discipline in `TODO.md`:** `[ ]` → `[o]` when you start an item, `[o]` →
  `[x]` in the same commit that finishes it, plus ` [YYYY-MM-DD HH:MM]` appended at
  the end of that line. Never move or reorder an entry. Change only the item you are
  currently on.
- **Side discoveries get logged, not silently fixed.** If you find a bug or a second
  instance of a problem, stop, add it to `TODO.md` as its own item, then continue.
- **`CLAUDE.md` stays untracked.** It is in `.gitignore` on purpose. A fresh clone
  will not have it — mention that if someone else picks this up.

---

## 5. Traps — the things most likely to go wrong

**Transcript vs memo.** A Zoom transcript of the client call informed the design, and
its speech-to-text mangled the single most important rule. The memo says **"any two"**
of the four hyperscalers, and **45% is a growth rate, not $450B**. Fixtures follow the
memo. Never the transcript.

**Page numbers are indicative.** The spec's source table cites pages from the memo's
own `N · 92` footers as seen during text extraction. Re-verify every page and quote as
you transcribe, and correct the spec where it is wrong. Do not copy them through
unchecked — provenance that is confidently wrong is worse than provenance marked
uncertain.

**`app/engine` must never import from `app/web`.** The engine is a pure library. This
is the single thing that makes the determinism proof cheap rather than awkward. If you
find yourself wanting a request object in the engine, the design has drifted.

**Determinism is easy to lose by accident.** No wall-clock reads, no RNG, no reliance
on `set` iteration order, no unsorted dict iteration anywhere that affects output.
Events sort by a total order `(date, kind, ticker)`.

**Tier 2 may never move a position on its own.** It proposes; a human accepts or
rejects; both are logged. This is the ADR's standing constraint. If a shortcut makes a
heuristic auto-execute, that supersedes the ADR and needs a human decision, not a
quiet edit.

**No rule loads without a source.** Fixture validation fails startup. Do not add a
fallback that lets the app boot with an unsourced rule.

---

## 6. Time and the cut order

Deadline is **Friday 2026-09-25**. This is roughly a one-day build.

The likeliest failure mode is spending the day hand-transcribing fixtures and shipping
no URL. That is why item `-01` is "deploy an empty page", not "deploy".

**Floor** — satisfies every hard requirement in the written brief, with a live URL:
items `-01 -02 -03 -06 -09 -10 -11` and a reduced `-12`.

**Differentiators — defend these:** `-07` (override modelling), `-08` (cross-ticker
fan-out), `-13` (timeline view), the AMZN half of `-05`, and `-14` (the written
direction piece, which is cheap and which the client said is graded as heavily as the
code).

**If the day compresses, cut transcription depth, not capability.** Fewer factors
typed up — with the shortfall stated on screen — is a much smaller loss than a system
that cannot show a rule override or cannot fan out across tickers. Those two are what
separate this from the sample demo the client already built.

---

## 7. Definition of done

The build is done when a stranger can open the deployed URL and answer, unaided:

1. What does the research actually conclude?
2. What rules were derived from it, and where did each one come from?
3. What would the system do, when, and why?

Plus: `pytest` green, the determinism check visibly passing in the app, and every
`TODO.md` item either `[x]` with a timestamp or still `[ ]` with an honest note in the
close-out about why it was not done.
