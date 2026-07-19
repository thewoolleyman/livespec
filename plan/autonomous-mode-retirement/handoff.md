# autonomous-mode-retirement — handoff

**Ledger anchor:** epic `livespec-33opqs` (livespec CORE tenant).
**Opened:** 2026-07-19, splitting the retired `plan/autonomous-mode/` thread.

Status is READ from the ledger, never stored here.

Runs in **PARALLEL** with `plan/autonomous-mode-acceptance/`. The two share no
internals and neither blocks the other — a different session can take each.

**Composing status.** Operations named here are skills of the
`livespec-orchestrator-beads-fabro` plugin — invoke as
`/livespec-orchestrator-beads-fabro:<operation>`. Each repo is its own beads
tenant, resolved from the working directory, so read a non-core tenant by
running from that repo's clone (`/data/projects/<repo>`).

## Read-first chain

1. This file.
2. `plan/autonomous-mode/handoff.md` — the thread being retired. You do NOT
   need to read its 3220 lines; you need §"OPERATING DIRECTIVES", §"TUI
   dogfooding — scope boundary", and the section named
   `SESSION UPDATE — 2026-07-14 (cont. 12)` (the design record three sibling
   specs cite). Everything else is session narration that stays in git history.

## Why this thread exists

`plan/autonomous-mode/` reached 3220 lines — the largest in the fleet — and the
maintainer's verdict was that it had become coupled, non-cohesive, and off
track. It failed **structurally**, not merely by size, and the successor
threads must not repeat the three causes:

1. **Append-only reverse-chronological session logs**, with corrections of
   corrections (cont.14 corrects cont.13; cont.15 corrects cont.14; cont.22
   corrects the entire frame).
2. **Duplicate tracking of a sibling repo's programme** — it carried a copy of
   the console's B1–B8 state. That copy going stale caused the cont.22
   "lost pointer" crisis, where the thread no longer knew where the real
   remaining work lived.
3. **Status stored in prose instead of read from the ledger.**

## ⚠ THE HARD PART — archiving is not a file move

**THREE LIVE-SPEC citations in TWO sibling repos name
`livespec:plan/autonomous-mode/handoff.md` as the DESIGN RECORD:**

| Repo | Location |
|---|---|
| `livespec-orchestrator-beads-fabro` | `SPECIFICATION/contracts.md:1594` |
| `livespec-orchestrator-beads-fabro` | `SPECIFICATION/contracts.md:1649` |
| `livespec-console-beads-fabro` | `SPECIFICATION/spec.md:340` |

All three cite the `SESSION UPDATE — 2026-07-14 (cont. 12)` section — "THE
RE-LOCKED DESIGN": six independent orthogonal `dispatcher.*` policy settings,
each a global default overridable per work-item by a ledger label, EXCEPT
`wip_cap`, a per-repo concurrency ceiling for which a per-item value is
structurally meaningless.

In this fleet **the cited design record is the TIEBREAKER over shipped spec
text.** Move the path without amending the citations and every future
spec-conflict resolution silently loses its tiebreaker. Worse: citation
fidelity here is **review-enforced only** — no mechanical check will catch a
dangling design-record path.

**HARD SEQUENCING: the archive move MUST NOT land before the amendments.**
Land them as one epic so master never carries a dangling citation.

A supersession header is ALREADY IN PLACE at the top of the live thread, so the
thread reads as superseded today; only the physical move is deferred.

## The work

### 1. Repair the three design-record citations
Two spec amendments, each via the full cycle: `/livespec:propose-change` →
**independent Fable review (NO-BLOCKERS is a precondition)** → `/livespec:revise`.
Repoint the design-record path to `plan/archive/autonomous-mode/handoff.md`.
The archive move preserves section text verbatim, so the section-NAME
references stay valid — only the path changes.

### 2. Archive `livespec:plan/autonomous-mode/`
`git mv plan/autonomous-mode/ plan/archive/autonomous-mode/`, keeping the
supersession header. Only after step 1 lands.

### 3. Archive `livespec-orchestrator-beads-fabro:plan/autonomous-mode/`
Frozen 2026-07-10 **pre-execution**: it instructs readers to WAIT for a
fable-review gate that exited that same day, while its O1/O2 work shipped by
2026-07-13 and was then superseded wholesale at orchestrator spec **v034**
(Full autonomous mode RETIRED, replaced by the `dispatcher.*` settings, built
under epic `bd-ib-24j5uy`, all done). It is actively misleading and claims no
live territory.

**Follow the model already set** by the console's archived sibling,
`livespec-console-beads-fabro:plan/archive/console-autonomous-mode/handoff.md`:
a `CLOSED + ARCHIVED` banner at the top, a §"Closing record" saying what
happened to each step and where surviving work went, and the original preserved
below AS WRITTEN and marked stale-by-design.

### 4. Migrate the standing OPERATING DIRECTIVES out of plan-space
Per `SPECIFICATION/contracts.md` §"Fleet agent-instruction core", durable
guidance belongs in `AGENTS.md` / `.ai/<topic>.md` — never a plan thread.

- **Directives 1–2** (hand off at 50% context; delegate heavy work to
  sub-agents/the factory) appear ALREADY covered by `.ai/agent-disciplines.md`
  (§session-end standing-handoff, §factory-dispatch-over-inline). **VERIFY
  before dropping** — if the coverage is partial, fold in the remainder rather
  than losing it.
- **Directive 3** (dogfood the console TUI as the operator surface) and the
  **TUI-dogfooding scope boundary** are programme-scoped, not durable fleet
  policy. They have been carried into
  `plan/autonomous-mode-acceptance/handoff.md`. Nothing to migrate; confirm and
  drop.

Apply the standing test: *"would this rule still make sense after the workflow
it scaffolds stabilizes?"* If not, it is not `.ai/` material.

### 5. Disposition sweep — findings that would otherwise die
Each is **VERIFY-THEN-FILE**: several may already be filed, and filing a
duplicate is its own cruft. Check the owning tenant's ledger first.

| Finding | Likely home |
|---|---|
| **Review-gate integrity hole** — a reviewer verdict lost to silence reads as a PASS; absence of an explicit verdict artifact must be a hard FAIL. Raised cont.15, reinforced cont.16, explicitly never filed ("maintainer's call"). **Highest value in this table.** | orchestrator (review-gate machinery lives there) |
| Spec-proposal defect taxonomy — claims that expire at ratification; prefer positive assertions about sibling-owned surfaces; clause-lockstep-at-revise as a Fable criterion | standing Fable-review criteria (CLAUDE.md bullet or an `.ai/` topic) |
| `list_work_items.py` drops `merge_sha` / `pr_number` from `--json` | orchestrator |
| Live-ledger hygiene backfill (62 console violations); console has no merge-evidence check | console |
| cont.20 flags 1–5: auto-merge vs review-gated manual PRs; impl→spec gate gap (`detect-impl-gaps` not gating); move source-breadth; `move:active` bypasses `wip_cap`; config-manifest self-version | orchestrator / console |
| Heading-coverage tier keyword sets diverge (console Rust check vs dev-tooling Python check overlap only on `integration`) | dev-tooling or console |
| Console coverage-convention lesson — the 100%-line-coverage gate is incompatible with MULTI-LINE `assert!` carrying interpolated messages; use single-line bare asserts | console repo guidance |
| Orchestrator operational lessons — sequentially-coupled items need `depends_on`; research-item close-in-place pattern; `mint_app_token.py` mints a REAL token (security) | orchestrator guidance |

## NEXT ACTION

**Groom `livespec-33opqs`**, then work step 1 (citation repair) first — it is
the only step with a hard ordering constraint, and it gates steps 2 and 3.

Steps 4 and 5 are independent of 1–3 and may run in any order or in parallel.

## Deliberately NOT owned here

- **The acceptance run** — `plan/autonomous-mode-acceptance/`.
- **The console cockpit programme** — `livespec-console-beads-fabro:plan/cockpit-ux-docs-release/`
  owns B6/B7/B8 and the E2E backfill. Do not re-home any of it.
- **Plan-handoff durability machinery** — `plan/plan-thread-integrity/` owns the
  session-end dirty-handoff check and the `plan/` uncommitted-edit widening.
  This thread archives specific threads; it does not build archival mechanism.

## Implementation route

Ledger-backed work is built **factory-side**: the `drive` operation
(`impl:<work-item-id>`) or a Dispatcher drain once `ready`. Do NOT hand-code in
a planning session and do NOT use the in-session `implement` operation. The
spec amendments in step 1 keep their designed human gate (independent Fable
review + the maintainer's accept).
