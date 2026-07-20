# autonomous-mode-retirement — CLOSED + ARCHIVED

> **CLOSED 2026-07-19, ARCHIVED 2026-07-20.** Nothing below is a live
> instruction. Epic `livespec-33opqs` is closed.
>
> **This thread never executed.** It was opened to carry the retirement of the
> 3220-line `plan/autonomous-mode/` thread on the premise that archiving needed
> two cross-repo spec-amendment cycles first. A cleaner approach removed that
> premise, its duties were executed directly instead, and the thread was closed
> the same day it opened.
>
> **It is archived rather than deleted, and that is the point of this banner.**
> It WAS deleted on 2026-07-19 — `git rm` rather than `git mv` — which also
> destroyed the §"Ledger dispositions" section below, added hours earlier from a
> fleet-wide audit. Restored 2026-07-20. The fleet convention is that a thread
> with a closed epic is ARCHIVED, and the standing discipline is *relocate,
> never drop*; deleting satisfied neither.
>
> **What actually happened to this thread's duties:**
>
> | Duty | Outcome |
> |---|---|
> | Design-record citation repair | Done — but NOT as planned. Rather than repointing after an archive move, the old handoff was first collapsed in place; the archive move and all three citation repoints then landed together on 2026-07-20 (`livespec#1513`, `orchestrator#829` v044, `console#333` v033). |
> | Archive the core thread | Done — `plan/archive/autonomous-mode/`, cited section preserved byte-for-byte. |
> | Archive the orchestrator's stale sibling | Done — `orchestrator#826`. |
> | Operating-directive migration | No action needed — directives 1–2 verified already covered by `.ai/agent-disciplines.md`; directive 3 + the TUI-dogfooding boundary went to the acceptance thread. |
> | Disposition sweep | PARTIALLY done — see the WARNING below. |
>
> ## ⚠ THE SWEEP IS NOT FINISHED — live findings below
>
> The §"Ledger dispositions" section below is the ONLY record of several
> findings. Four were executed (`-3rdmqu` closed, `livespec-1t17` closed,
> `livespec-0jxs` regroomed, two label/status contradictions fixed). **These
> were NOT, and are still owed:**
>
> - **`bd-gj-rb3` (livespec-orchestrator-git-jsonl) — MAINTAINER DECISION.**
>   That repo's OWN spec still contracts the autonomous-mode paradigm
>   beads-fabro RETIRED at v034 (`constraints.md:94-131`,
>   `contracts.md:28-32`), unimplemented. Either re-steer the git-jsonl spec to
>   the v034 policy-settings model — the item dies as-written — or keep the
>   divergence consciously. **Do not dispatch it as-is.**
> - **`livespec-console-beads-fabro-nxsfih`** — re-scope the anchor to its
>   residue (the missing zero-Beads guard) or file that standalone and close it;
>   its plan thread is archived while the anchor stays open.
> - **`livespec-console-beads-fabro-8aw`** — LIVE; refresh its stale "v017"
>   pointer at groom (spec is v032).
> - **`bd-ib-24j5uy`** — decide keep-open-as-`bd-ib-0s5`'s-parent vs close.
>
> Everything from here down is preserved AS WRITTEN and is stale by design.

---

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

### 6. Ledger dispositions — from a completed fleet-wide audit (2026-07-19)

A full sweep of all 8 reachable fleet tenants (83 programme-connected records,
28 open) produced the dispositions below. **The good news first: the
phantom-open pattern was real but is ALREADY RECONCILED** — the console W-set
(`-yvikqp` + W1–W7), `-rt4`, `-pke3y3`, `-mb64bv`, `-d6o`, the `-0ak` freeform
children, orchestrator `bd-ib-82a`, O0–O10, and every Stage-2 throwaway
(`bd-ib-dqt`/`-tcar`/`-7zks`/`-86k`) are all closed. **Do not re-close them.**

Adopter tenants (`openbrain`, `resume`, `homelab`) were unreachable — nothing
is listed for them, which is not proof they are clean.

| Item | Tenant | Disposition |
|---|---|---|
| `livespec-console-beads-fabro-3rdmqu` | console | **Close** — its grievance is moot. The unmet half of `-0tu` (relocate prose into `docs/`) shipped in B6 impl `7df1ea2`; the three sentences are at `docs/detailed-usage.md:116/:120/:160`. Human-tier, so the maintainer ratifies. |
| `livespec-0jxs` | core | **Regroom, do NOT close.** Its operability trio is delivered, but residual duties 3/7/9/10 from its 2026-06-15 comment are genuinely open (no dispatcher master-ci-green pick-preflight exists). |
| `bd-gj-rb3` | git-jsonl | **MAINTAINER DECISION.** It describes the paradigm beads-fabro RETIRED at v034 — but git-jsonl's OWN spec still contracts it (`constraints.md:94-131`, `contracts.md:28-32`), unimplemented. Either re-steer that spec to the v034 policy-settings model (the item dies as-written) or keep the divergence consciously. **Do not dispatch as-is.** |
| `livespec-1t17` | core | **Close or downgrade to a pointer** — duplicates console `-mvu22t` (fuller description, right tenant, same Rust red-green-replay work, filed same day). Keep the console one. |
| `livespec-console-beads-fabro-nxsfih` | console | Re-scope the anchor to its residue (the missing zero-Beads guard) or file that standalone and close — its plan thread is already archived while the anchor stays open. |
| `livespec-console-beads-fabro-8aw` | console | LIVE — the four non-valve commands are still contracted (`contracts.md:412-415`) and unimplemented. Refresh its stale "v017" pointer at groom (spec is v032). |
| `bd-ib-24j5uy` | orchestrator | Decide: keep open as `bd-ib-0s5`'s parent, or close (work shipped + released + live-exercised) with `-0s5` standing alone. |
| Label/status contradictions | various | `livespec-console-beads-fabro-mvu22t` and `livespec-runtime-f5zhs5` each carry a `ready` LABEL on `backlog` STATUS. One of the two is wrong in each case. |

**No dangling dependency edges were found anywhere in the programme set**, and
no wrong-tenant filings.

#### A correction to that audit, and a live question it left

The audit reported `bd-ib-98c.10` as wrongly parked in the orchestrator's
`acceptance` lane on the reasoning that its proof dispatch never ran. **That is
wrong, and acting on it caused churn worth recording so nobody repeats it.**

All four `98c.*` confirmation artifacts DO exist — at
`plan/archive/codex-factory-telemetry/` in the orchestrator repo, each opening
"Created by an autonomous factory run". They were missed by searching only the
LIVE path (`plan/codex-factory-telemetry/`); that thread was ARCHIVED after the
dispatches completed, which moved every artifact. `bd-ib-98c.15`'s own
description corroborates this — it reports observing 6 `run_turn` spans from
`.14`'s run. Those items are awaiting a LEGITIMATE acceptance of real work and
belong exactly where they are. **Lesson: when checking whether a plan-thread
artifact exists, search `plan/archive/` too — an archived thread moves every
path it owns.**

**The residual question is real, though:** the prerequisites those proofs
confirm (`bd-ib-98c.5`, `.12`, `.7`) are all still recorded `backlog` while
their proofs demonstrably ran and landed. Either those records are stale-open
(the phantom-open pattern again) or the proofs ran ahead of a formal close.
Worth reconciling in the orchestrator tenant; it is NOT a reason to move
anything out of the acceptance lane.

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
