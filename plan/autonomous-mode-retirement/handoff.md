# autonomous-mode-retirement — RECLAIMED AND LIVE

> **RECLAIMED 2026-07-20 from `plan/archive/`.** This thread is ACTIVE again and
> has been REPURPOSED. It no longer carries its original charter (executed and
> closed 2026-07-19 under epic `livespec-33opqs`); it now carries the **close-out
> verification of the v034 Full-autonomous-mode retirement** and everything that
> verification found.
>
> Reclaimed at the maintainer's direction. The working directives driving this
> thread come from **the overseer** (the `livespec-overseer` tmux session,
> relaying to this track's pane, tmux session `autonomous-mode-retirement`), and
> are recorded as such — including the overseer's own two retractions, below.

## Why this thread was reclaimed rather than a new one opened

The maintainer kicked this session at `plan/autonomous-mode-retirement/handoff.md`
— the ACTIVE path. At the time the path resolved to nothing, and the overseer's
orientation stated the thread "does not exist active or archived; you were
pointed at a handoff that was never written."

**That was false, and the overseer retracted it.** The thread existed all along.
It had been DELETED by a `git rm` on 2026-07-19 and was not yet restored when
that orientation was written; it was restored to the archive on 2026-07-20
(`46ade934` / `116a4147`). The deletion was the anomaly — not the thread — and
the maintainer's kick at the active path was deliberate.

That same `git rm` also destroyed the §"Ledger dispositions" findings added hours
earlier. That is why those dispositions no longer live only here.

## ✅ THE BLOCKER IS CLEARED — the retirement is now complete fleet-wide

**RESOLVED 2026-07-20.** The maintainer cleared this for completion ("drive the
git JSONL to completion"). It landed as `livespec-orchestrator-git-jsonl`
**PR #358**, ratified as that repo's spec **v018**. Its ledger item
`bd-gj-rb3` is CLOSED as dies-as-written.

### What the blocker was

`livespec-orchestrator-git-jsonl`'s RATIFIED spec still contracted the paradigm
retired at beads-fabro v034 — `contracts.md:28-32` mandating a dangerous
`--autonomous` flag whose skills "MUST resolve [their] per-item consent gate(s)
with an LLM decision instead of prompting the user"; `constraints.md:94-107`
requiring the arming acknowledgement; `spec.md:106` a live `## Autonomous mode`
section. All ratified, all UNIMPLEMENTED.

### The disposition — BOTH original options were rejected

`bd-gj-rb3` offered "re-steer to the v034 policy-settings model, or consciously
keep the divergence". **Both rested on a false premise.** The two "Full
autonomous modes" are DIFFERENT SURFACES SHARING A NAME:

| | beads-fabro (retired at v034) | git-jsonl |
|---|---|---|
| Surface | a **Dispatcher drain mode** (`--mode autonomous`) | a `--autonomous` flag on **four heavyweight skills** |
| Governs | admission, post-merge acceptance, review fix-caps, WIP ceiling — inside a Fabro factory | **per-item consent gates** |
| Replaced by | six `dispatcher.*` policy settings | — |

git-jsonl ships **no dispatcher, no factory, no PR flow, no review gate, no WIP
limit** (its eight skills are `capture-impl-gaps`, `capture-spec-drift`,
`capture-work-item`, `detect-impl-gaps`, `implement`, `list-work-items`,
`needs-attention`, `next`). So "re-steer to the v034 model" was a **CATEGORY
ERROR** — `auto_approve_ready` / `merge_on_review_cap` / `review_fix_cap` /
`wip_cap` have nothing there to attach to.

It was **RETIRED OUTRIGHT** instead: a ratified, unimplemented, explicitly
DANGEROUS feature reads as sanctioned design intent and invites a future
implementer to build precisely the paradigm the family just spent a release
retiring. Zero migration cost — verified zero non-vendor `*.py` matches, zero
skill-body matches, and all three removed headings carried `"test": "TODO"`.

**What transfers from v034 is its PRINCIPLE, not its settings**: granular,
independently-defaulted, per-item-overridable consent policy with a hard
needs-human floor. If autonomy is ever wanted in git-jsonl it should be designed
fresh against that principle and against that plugin's ACTUAL consent gates.

### Judgment calls made during the retirement

- **`decided_by` REMOVED** — its enum `human | autonomous` degenerates to a
  single value once the run mode is gone; zero producers for either value.
- **`auto_resolvable` REMOVED, neighbours PRESERVED and generalized** — the hint
  was defined purely as "whether a full-autonomous run could progress the item";
  the extra-fields permission and the ranking-purity rule survive, the latter now
  binding ANY advisory field rather than only that one.
- **`Unresolvable decision` / `Escalation` RE-ANCHORED, not deleted** —
  escalating instead of guessing is a general safety principle. The never-guess
  floor moved to §"Forbidden patterns" so it outlives the section that housed it.
- **Scenario 6 renumbered to 5** rather than leaving a hole in a six-item list;
  exactly three references, all amended.

### What the mandatory sweep caught

Removing `decided_by` left the schema preamble asserting **"twenty keys"** over
an enumeration of **nineteen**, plus a dangling mention. NOT in the original edit
map — the sweep found it. Repaired, count verified by enumeration
(14 + `rank` + 4 = 19). This is the argument for sweeping BEFORE declaring done.

Final verification against git-jsonl `origin/master`: **zero hits** for
`utonomous`, `decided_by`, `auto_resolvable`, and the stale `twenty` across all
four live spec files. `just check`: all 62 targets pass.

## What this thread now owns — the close-out sweep

Three independent read-only adversarial verifiers re-derived the retirement
against live state rather than trusting the ledger, the spec's claims, or
CI-green. This discharges the non-behavior-bearing acceptance form.

| Leg | Verdict |
|---|---|
| Orchestrator SPEC | Clean — 8/8; retirement survived v034 → v044 without drift |
| Orchestrator IMPL | **D1 (P1)** + D2 + a test gap |
| Console | **Defect A (P1)** + Defect B |
| Cross-repo (git-jsonl) | **BLOCKER above** |

### Items this thread created

| Item | Tenant | State |
|---|---|---|
| `bd-ib-24j5uy` | orchestrator | EPIC — **OPEN**; description corrected (it falsely claimed "the IMPLEMENTATION DOES NOT EXIST YET") |
| `bd-ib-24j5uy.4` | orchestrator | D1 — fix MERGED (PR #839, `952d874c`); janitor red post-merge; still `active` |
| `bd-ib-24j5uy.5` | orchestrator | D2 — review-cap parser hardcodes `_REVIEW_CAP_VISITS = 3` |
| `bd-ib-od2i` | orchestrator | The wrong-source lesson; closes when `livespec#1546` merges |
| `bd-ib-yf2m` | orchestrator | Pairing gate blocks docstring-only diffs; AST-based exemption required |
| `livespec-console-beads-fabro-bgc` | console | Defect A — Scenario-15 journal read leg dead live |
| `livespec-console-beads-fabro-co3` | console | Defect B — stale prose cluster |
| `bd-ib-0s5` | orchestrator | DETACHED from the epic; design-human-gated, stands alone |

### D1 — what landed and what did not

Fix is on master; master CI green on that SHA. Verified by re-running the
reproduction: `effective_admission_policy` now takes `cwd: Path` as a REQUIRED
keyword-only argument and the old reproduction can no longer execute
(`TypeError: missing 1 required keyword-only argument: 'cwd'`) — the silent
fallback is closed at the type level across all five `effective_*` resolvers.

NOT done: the post-merge janitor went red on `check-coverage` in a fresh checkout
(kept at `~/.worktrees/livespec-orchestrator-beads-fabro/janitor-bd-ib-24j5uy.4`),
so the item is stuck `active`. Master CI passing while the janitor fails on the
same SHA is itself worth diagnosing.

Owed: three stale-prose corrections (`dispatcher.py`,
`_dispatcher_cost_pricing.py`, `commands/CLAUDE.md`) staged-but-uncommitted at
`~/.worktrees/livespec-orchestrator-beads-fabro/docs-retire-mode-prose`. Blocked
alone by the pairing gate; to ride along as Red-Green-Replay ride-along docs.
**Do not discard that worktree.**

## Preserved findings — the point is that this file is no longer the only copy

A `git rm` already destroyed these once. **The correct response to a file that
can be deleted is not to guard the file more carefully — it is to stop the file
being the only copy.** The §"Ledger dispositions" entries below have each been
attached as a comment on their own ledger item, in that item's own tenant. The
items always existed; what existed nowhere else was the ANALYSIS. This thread is
the narrative now, not the sole record.

### A. Ledger dispositions — 2026-07-19 fleet audit (8 tenants, 83 records, 28 open)

| Item | Tenant | Disposition |
|---|---|---|
| `bd-gj-rb3` | git-jsonl | **MAINTAINER DECISION — the blocker above.** Do not dispatch as-is. |
| `livespec-console-beads-fabro-nxsfih` | console | Re-scope the anchor to its residue (the missing zero-Beads guard), or file that standalone and close — its plan thread is archived while the anchor stays open. |
| `livespec-console-beads-fabro-8aw` | console | LIVE — four non-valve commands still contracted (`contracts.md:412-415`), unimplemented. Refresh its stale "v017" pointer at groom (spec is v032). |
| `livespec-console-beads-fabro-mvu22t` | console | Carries a `ready` LABEL on `backlog` STATUS — one of the two is wrong. |
| `livespec-runtime-f5zhs5` | runtime | Same label/status contradiction. |
| `bd-ib-98c.5` / `.12` / `.7` | orchestrator | Recorded `backlog` while their proofs demonstrably ran and landed. Reconcile: stale-open, or proofs ran ahead of a formal close. NOT a reason to move anything out of the acceptance lane. |

Already executed — **do not re-do**: `-3rdmqu` closed, `livespec-1t17` closed,
`livespec-0jxs` regroomed. **Do not re-close** the already-closed phantom-open
set (console `-yvikqp` + W1–W7, `-rt4`, `-pke3y3`, `-mb64bv`, `-d6o`, the `-0ak`
freeform children, orchestrator `bd-ib-82a`, O0–O10, Stage-2 throwaways). Adopter
tenants (`openbrain`, `resume`, `homelab`) were UNREACHABLE — not proof they are
clean. No dangling dependency edges and no wrong-tenant filings were found.

### B. Disposition sweep — findings that would otherwise die (NONE YET FILED)

Carried forward verbatim in substance from the original thread. Each is
**VERIFY-THEN-FILE**: check the owning tenant first, since filing a duplicate is
its own cruft — and per this thread's own lesson, that check must include CLOSED
records, which the default listing hides.

| Finding | Likely home |
|---|---|
| **Review-gate integrity hole** — a reviewer verdict lost to silence reads as a PASS; absence of an explicit verdict artifact must be a hard FAIL. Raised cont.15, reinforced cont.16, explicitly never filed ("maintainer's call"). **Highest value in this table.** | orchestrator |
| Spec-proposal defect taxonomy — claims that expire at ratification; prefer positive assertions about sibling-owned surfaces; clause-lockstep-at-revise as a Fable criterion | standing Fable-review criteria (`.ai/` topic or CLAUDE.md) |
| `list_work_items.py` drops `merge_sha` / `pr_number` from `--json` | orchestrator |
| Live-ledger hygiene backfill (62 console violations); console has no merge-evidence check | console |
| cont.20 flags 1–5: auto-merge vs review-gated manual PRs; impl→spec gate gap (`detect-impl-gaps` not gating); move source-breadth; `move:active` bypasses `wip_cap`; config-manifest self-version | orchestrator / console |
| Heading-coverage tier keyword sets diverge (console Rust check vs dev-tooling Python check overlap only on `integration`) | dev-tooling or console |
| Console coverage-convention lesson — the 100%-line-coverage gate is incompatible with MULTI-LINE `assert!` carrying interpolated messages; use single-line bare asserts | console guidance |
| Orchestrator operational lessons — sequentially-coupled items need `depends_on`; research-item close-in-place pattern; `mint_app_token.py` mints a REAL token (security) | orchestrator guidance |

## The lesson this thread kept re-teaching

**A green-looking signal read off the wrong source is not evidence.** Recorded as
`.ai/verifying-against-the-right-source.md` (PR `livespec#1546`), with instances
spanning three repos and two independent operators. Encountered here:

1. A passing suite that never exercised the live call site hid D1.
2. A fixture encoding the RETIRED wire shape hid Defect A.
3. A default `gh pr list` (open-only) hid an already-merged PR → duplicate PR for
   finished work.
4. A stale local `remotes/origin/*` ref read as proof of a push that never
   happened.
5. A default ledger listing hiding CLOSED records defeated a dedup sweep.
6. A dispatch reported `exit 0` while its `status` was `failed` — the shell exit
   came from a trailing `tail`, not the dispatcher.
7. From this thread's own audit correction: an artifact search that missed
   `plan/archive/` concluded a dispatch never ran. **An archived thread moves
   every path it owns.**

## Corrections the overseer made to its own directives

Recorded because they are load-bearing, and because a thread that logs only the
operator's corrections and not the supervisor's is not an honest record.

1. **"The thread does not exist, active or archived."** False — it existed and
   had been deleted. See the reclaim rationale above.
2. **"The retirement is essentially done."** Retracted on discovering
   `bd-gj-rb3`: a sibling's ratified spec still contracts the retired paradigm,
   so the retirement is not fleet-wide complete.

## RUNNING STATE — as of 2026-07-20

**THE EPIC IS CLOSED.** `bd-ib-24j5uy` closed with ALL 15 CHILDREN CLOSED and
**no `--force`**. The retirement is complete and verified fleet-wide.

### How the epic actually closed

The ledger REFUSED to close it with an open child (`cannot close epic ...: 1 open
child issue(s); close children first or use --force`). `--force` is exactly the
bypass this fleet forbids, so **the child was fixed instead**. That is the honest
resolution: repair what the gate names, do not override the gate.

| Child | Outcome |
|---|---|
| D1 `bd-ib-24j5uy.4` | CLOSED — PR #839, merge `952d874c`, master CI green. `cwd` now REQUIRED on all five `effective_*` resolvers; the old reproduction can no longer execute (`TypeError`), so the silent-fallback footgun is closed at the type level. |
| D2 `bd-ib-24j5uy.5` | CLOSED — PR #842, merge `349fe79f`, master CI green. `_REVIEW_CAP_VISITS = 3` gone; the parser now receives `emission.plan.review_fix_visit_cap`, the same value the workflow is injected with. |

D2's fix was REVIEWED, not trusted: its `None` default looked like it would make
`visit_count >= cap_visit_count` vacuously true, but the fix also added a
`fix_rounds > 0` guard, and production always supplies the plan's cap.

### ⚠ THE MOST OPERATIONALLY IMPORTANT FINDING — `bd-ib-yqfw` (P0, OPEN)

**D1 and D2 both landed correct fixes with green master CI, and BOTH were
stranded in `active` by the identical janitor failure** — `check-coverage` exit 2
in a non-root fresh checkout. Same target, same exit code, same master-CI-green
divergence, different changes touching different modules.

Root cause is already filed: `bd-ib-yqfw` — *"`just check` is RED on master for
non-root runners (CI runs as root and masks it)"*. The janitor runs NON-ROOT in a
fresh checkout; CI runs as ROOT and masks it.

**Consequence: the dark factory cannot close items unattended.** The janitor is
its hard gate; while that gate fails for reasons unrelated to the change under
test, every dispatched item lands its PR and then needs a human to diagnose and
close it by hand. Both items above required exactly that. Impact evidence is
recorded on `bd-ib-yqfw`.

**Second-order risk, also recorded there:** now that janitor red is KNOWN to be
usually environmental, there is a standing temptation to wave any janitor red
through as "the non-root thing" — the failure mode where a genuine catch gets
dismissed. Both closures verified the fix independently against `origin/master`
first, but that discipline will not survive volume.

### In flight

**Defect A (`livespec-console-beads-fabro-bgc`, P1) — DISPATCHED.** The
Scenario-15 orchestrator-journal read leg is dead live on three wire mismatches.

It was previously mis-filed as needing a MAINTAINER DECISION on a wire-contract
rename. **That framing was wrong and is retracted.** The console's OWN ratified
spec already specifies the orchestrator's current vocabulary verbatim —
`scenarios.md:529-533` names all five live disposition values (`auto-approve`,
`ai-auto-accept`, `ai-fail-auto-rework`, `ship-on-cap`, `cap-exceeded-escalation`)
and requires attributing each "to the setting that governed it", which is the
`governing_settings` array. Both sides' specs already agree; only the console's
IMPLEMENTATION lags. **This is CONFORMANCE work, not a contract change, and there
is nothing to ratify.**

The generalizable check, worth keeping: **"is this actually a DECISION, or an
UNIMPLEMENTED CONTRACT?"** Read both sides' ratified specs before concluding a
cross-repo change needs agreement. Mis-filed as a decision, this P1 would have sat
in backlog behind a negotiation that does not exist.

Two binding conditions on that fix: (1) `scenario_10_autonomous_run.rs` is the
green test that MASKED this defect and its repair is part of the fix — and the
fixture must be PINNED OR DIGEST-STAMPED against the PRODUCER's real output, not
hand-written again (instance 2's counter-move, applied to the very defect
instance 2 was derived from); (2) keep the severity framing — fail-OPEN for
observability, escalations still reach the operator via the orchestrator's own
`needs-attention` surface. It is not a decision-correctness bug.

### Remaining

- **Defect B** `livespec-console-beads-fabro-co3` (P3) — stale prose cluster,
  deliberately EXCLUDING `scenario_10_autonomous_run.rs` (that belongs to
  Defect A's fix, so a prose cleanup cannot leave the masking fixture alive).
- **The ride-along prose** — still staged-but-uncommitted at
  `~/.worktrees/livespec-orchestrator-beads-fabro/docs-retire-mode-prose`,
  blocked alone by the pairing gate (`bd-ib-yf2m`). Do not discard.
- **The §B findings** — `bd-ib-hdd6` filed (the review-gate integrity question,
  as INVESTIGATE not defect: the parser proved honest, the verdict gates nothing
  in Python, and the real risk sits untested in the Fabro graph). The rest remain
  VERIFY-THEN-FILE — and that verification MUST request CLOSED records, which the
  default ledger listing hides.

## Deliberately NOT owned here

- **`bd-ib-0s5`** — detached deliberately. A design-human-gated spec amendment on
  cost-gate coverage, not retirement work. Closing it with the epic would bury a
  real open question about a fail-open cost gate; holding the epic open for it
  would misrepresent a finished retirement.
- **The console cockpit programme** — `livespec-console-beads-fabro:plan/cockpit-ux-docs-release/`.
  Reference it; never copy its state. Duplicating a sibling's programme is what
  broke the original `plan/autonomous-mode/` thread.

## Provenance

The original charter and its execution record are preserved in git history at
`46ade934` (`plan/archive/autonomous-mode-retirement/handoff.md`, 253 lines). Its
`NEXT ACTION` and status claims are stale by design and must not be read as live
instructions. The design record three sibling specs cite remains
`plan/archive/autonomous-mode/handoff.md`, section
`SESSION UPDATE — 2026-07-14 (cont. 12)` — do not move it without amending
`livespec-orchestrator-beads-fabro` `contracts.md:1594` / `:1649` and
`livespec-console-beads-fabro` `spec.md:340` in the same landing.
