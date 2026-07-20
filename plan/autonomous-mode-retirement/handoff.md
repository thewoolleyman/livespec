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

## RUNNING STATE — session close 2026-07-20

### ⚠ TOP PRIORITY ON RESTART: `bd-ib-yqfw` (P0) — one clause of three still open

**The maintainer escalated this in their own words: "Something is fucked up with
the factory. Make sure this gets fixed."** It ranks ABOVE every §B finding and
above all remaining Defect-B work. Start here.

**Two of its three clauses are LANDED (PR #845, merged to master). The third is
NOT STARTED.**

| Clause | State |
|---|---|
| 1. `just check` RED for non-root runners | ✅ FIXED, merged |
| 2. `fcntl.flock` reclaim mutex has ZERO coverage | ✅ FIXED, merged |
| 3. **unguarded mutex I/O** | ❌ **NOT STARTED — this is the resume point** |

**Clause 3, precisely.** `_stale_janitor_lock_reclaimed`
(`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_janitor_lock.py`,
~line 68) still opens the mutex with a raw
`_reclaim_mutex_path(path=path).open("a+b")`, OUTSIDE the `attempt(...)` Result
track the rest of that module uses for filesystem access — compare
`_read_janitor_lock`, which wraps its read. An expected I/O failure there
(permissions, full disk, vanished parent dir) propagates as a raised exception
out of the reclaim path instead of routing through the failure track.

### The mechanism — do NOT re-derive it

`os.kill(1, 0)` raises `PermissionError` for an unprivileged uid. The only
live-pid test probed **pid 1**, so off-root the probe fell through the
not-a-`ProcessLookupError` path and the direct `return True` at
`_dispatcher_janitor_lock.py:133` **never executed**. CI's root container covered
it; no other runner could. Reproduced independently by both the operator and the
overseer.

Probing our OWN pid is the privilege-independent way to reach that branch, but a
short-circuit on `lock.pid == os.getpid()` stopped the probe being consulted at
all. That clause was **production-dead** — the probe is always True whenever the
comparison is — so it could never change an outcome, only suppress coverage.

### ⛔ TWO HARD CONSTRAINTS

**DO NOT DISPATCH THIS TO THE FACTORY.** The factory's post-merge janitor gate is
the thing that is broken, so dispatching the fix strands the fix — the same trap
in a tighter loop. Hand-build in-session. This is explicitly sanctioned by the
repo's own carve-out for "repo/dev-tooling PLUMBING unsafe to self-run through
the factory (the factory substrate itself, the commit-refuse hooks, the dispatch
machinery)"; `_dispatcher_janitor_lock.py` IS the factory substrate. This is the
one case where hand-building is correct rather than a shortcut.

**THE ACCEPTANCE BAR IS NOT CI GREEN.** It is `just check` **green run as a
non-root user (uid 1000)**, captured before and after in the PR body. CI is the
source that MASKED this and must never be used to close it. Clause 3's fix is
product `.py`, so it needs full Red-Green-Replay with a genuine assertion failure
at Red.

### What landed, with evidence

PR #845 (`livespec-orchestrator-beads-fabro`), merged. Verified on `origin/master`:
the short-circuit is gone (`if lock is None or _pid_is_alive(pid=lock.pid):`) and
`tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_janitor_lock_nonroot.py`
is present.

- **Acceptance, uid 1000, not CI.** BEFORE: `check-coverage` failed —
  "Required test coverage of 100.0% not reached. Total coverage: 99.99%", with
  `_dispatcher_janitor_lock.py` missing exactly line 133. AFTER: full `just check`
  → **"All 67 targets passed"**, green token written.
- **Clause 2 was proven discriminating, not assumed.** With the mutex temporarily
  deleted the new test fails with
  `assert ('/tmp/.../janitor.lock.reclaim', 2) in []`; previously the ENTIRE SUITE
  passed with it gone. **Clause 2 is the one that gets dropped once the gate goes
  green — it is not optional.**
- Red was a genuine assertion failure (`assert probed == [os.getpid()]` →
  `-[] +[4117257]`), not an import error. Both `TDD-Red-*` and `TDD-Green-*`
  trailer sets are on the single commit.

**Worktree `~/.worktrees/livespec-orchestrator-beads-fabro/fix-janitor-lock-nonroot`
(branch `fix-janitor-lock-nonroot`) is fully merged and carries nothing unpushed.
It is SAFE TO REAP.** This is stated explicitly so the restart does not treat it
as live state.

### 🔬 THE NATURAL EXPERIMENT ALREADY RAN — and it answers the scope question

The open question was whether fixing `bd-ib-yqfw` fixes the factory EVERYWHERE or
only in one repo. **Evidence now says the failure was orchestrator-specific.**

| Dispatch | Repo | Outcome |
|---|---|---|
| D1 `bd-ib-24j5uy.4` | orchestrator (Python) | stranded at `janitor-post-merge`, `check-coverage` exit 2 |
| D2 `bd-ib-24j5uy.5` | orchestrator (Python) | stranded identically |
| Defect A `-bgc` | **console (Rust)** | **`status: green`, `stage: done`, PR #341, item CLOSED** |

Three orchestrator dispatches stranded; the one console dispatch completed
cleanly through the same janitor. **Do not assume Defect A is still running — it
finished and is closed.**

### 🚩 A GREEN GATE IS NOT A WORKING FACTORY — this is the actual finish line

**Do not mistake #845 merging for the factory being fixed.** It has been proven
GREEN ON A GATE, as uid 1000. It has NOT been proven to close work.

**The proof is a real item dispatched and reaching `done` with NO human
hand-closing it.** That has not happened in the orchestrator repo. Today produced
**three correct merged fixes and three manual closes** — D1, D2, and the git-jsonl
retirement all needed a human to read the outcome and close the item by hand. A
gate that passes is a precondition for that, not evidence of it.

**FIRST ACTION after clause 3 (or alongside it): dispatch one real
orchestrator-repo item post-#845 and watch whether it reaches `done` unattended.**
If it strands again, #845 was necessary but not sufficient and the remaining cause
is still unidentified.

The console evidence above is ONE run and does not settle this. It shows the
console repo did not strand *that time*; it does not show the orchestrator repo
now succeeds. Those are different claims and only the second is the maintainer's
bar.

Also carry forward: `bd-ib-9yi` (cargo-not-found / no Rust toolchain in the
orchestrator image) was raised as a possible ALTERNATIVE cause of console
stranding. It did not manifest in the run above, but it was never ruled out as a
latent issue.

### 🔁 THE CLASS FIX IS UNRESOLVED — `bd-ib-sfa2` (P1)

PR #845 fixed the LINE. It did not fix the CLASS. CI still runs the check matrix
as ROOT (`container: ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-v0.51.0`,
`MISE_DATA_DIR: /root/...`, confirmed at `ci.yml:121-124` and `:218-221`), so CI
**structurally cannot exhibit a non-root divergence and this WILL recur on some
other line.**

**The overseer's proposal, carried as UNRESOLVED not decided:** run that matrix
where it CAN fail — both ways, treating root/non-root divergence as a failure in
itself, converting environment-dependence from invisible to detectable.

**The operator's assessment, filed on `bd-ib-sfa2`:** agree with run-both,
disagree that divergence-detection machinery is needed. The existing **100%
coverage gate already converts divergence into a failure** — a line reachable
only as root is unreachable in the non-root run, which then misses 100% and
fails, and symmetrically. Two independently-gated runs make divergence
unsurvivable with no comparison step and no new tooling. **This holds ONLY while
fail-under is 100%**; lower it and explicit divergence detection becomes
necessary. Real cost is the IMAGE (hardcoded root `MISE_DATA_DIR`), not the
second job.

### Other work closed this session

- **Epic `bd-ib-24j5uy` CLOSED** — 15/15 children, **no `--force`**. The ledger
  refused to close over an open child; the child was FIXED instead.
- **`bd-gj-rb3` CLOSED** — git-jsonl autonomous mode retired at spec v018
  (PR #358). Zero hits for `utonomous`/`decided_by`/`auto_resolvable` on that
  repo's master.
- **Defect A `-bgc` CLOSED** — journal read leg conformant; path, stage and schema
  now match the producer.

### Still open, lower priority than yqfw clause 3

| Item | Tenant | What |
|---|---|---|
| `livespec-console-beads-fabro-knh` (P2) | console | The Scenario-15 fixture is SELF-digested, never re-derived from the producer — so producer drift still passes silently. Half of the anti-masking guarantee is missing; copy the `just refresh-config-manifest` pattern and beat its "as of last capture" limitation. |
| `livespec-console-beads-fabro-co3` (P3) | console | Defect B stale prose. `console-application/src/lib.rs:4588` still reads "Full autonomous mode". |
| `bd-ib-hdd6` (P2) | orchestrator | INVESTIGATE whether a reviewer verdict lost to silence reads as a PASS. The parser proved HONEST and the verdict gates nothing in Python; the untested risk is in the Fabro graph. |
| `bd-ib-yf2m` (P2) | orchestrator | Pairing gate blocks docstring-only diffs; needs an AST-based exemption, NOT a diff heuristic. |
| `bd-ib-0s5` | orchestrator | Detached; design-human-gated cost-gate spec amendment. |
| §B findings | various | Seven remain VERIFY-THEN-FILE (§ Preserved findings above). Verification MUST request CLOSED records — the default listing hides them. |

**The ride-along prose** is still staged-but-uncommitted at
`~/.worktrees/livespec-orchestrator-beads-fabro/docs-retire-mode-prose` (three
comment-only corrections in `dispatcher.py`, `_dispatcher_cost_pricing.py`,
`commands/CLAUDE.md`). Blocked alone by the pairing gate; it must ride a PR that
carries real tests. **DO NOT DISCARD THAT WORKTREE.** Clause 3's fix is a natural
carrier.

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
