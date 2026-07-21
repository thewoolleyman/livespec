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
8. A standalone `just check-coverage` re-reported a 16-hour-old `.coverage` data
   file and read as a master regression that did not exist. **The recipe
   short-circuits when the data file is present; only the full gate is honest.**
9. A follow-by-name tail of the dispatch journal replayed 2811 lines of history
   as if live, reporting a green unattended close that predated the fix being
   tested. **Filter on the record timestamp; sanity-check PR numbers against the
   current range.**
10. `bd-ib-yqfw`'s own prescribed reproduction for clause 3 was root-masked, so
    the test it asked for would have passed vacuously in CI's root container.
    **A permission-based provocation is silently disarmed for root** — the same
    masking the item was filed to fix.
11. PR #847 was reported as "OPEN, auto-merge deliberately off, dual review
    running" when it had already merged unreviewed. `gh pr checks` was read as
    if it reported merge STATE; merge state was actually reported from the
    operator's own INTENT. **Not doing a thing is not evidence the thing did not
    happen** — query `gh pr view --json state,mergedAt,reviews`.
12. A concurrency probe was staged by copying the module off the FILESYSTEM of a
    primary checkout that was 2 commits behind, so it silently tested the
    PRE-fix code. Caught only because the copied source visibly lacked the fix.
    **Read committed state with `git show origin/master:<path>`** — the standing
    rule exists precisely for this, and a working tree deliberately left unpulled
    is exactly when it bites.

## Corrections the overseer made to its own directives

Recorded because they are load-bearing, and because a thread that logs only the
operator's corrections and not the supervisor's is not an honest record.

1. **"The thread does not exist, active or archived."** False — it existed and
   had been deleted. See the reclaim rationale above.
2. **"The retirement is essentially done."** Retracted on discovering
   `bd-gj-rb3`: a sibling's ratified spec still contracts the retired paradigm,
   so the retirement is not fleet-wide complete.

## RUNNING STATE — 2026-07-20 (cont. — clause 3 session)

### ✅ `bd-ib-yqfw` (P0) — CLOSED. All three clauses landed and bar 4 is proven.

**The maintainer escalated this in their own words: "Something is fucked up with
the factory. Make sure this gets fixed."** It ranked above every §B finding and
above all remaining Defect-B work. It is now closed `resolution:completed`, with
the full evidence appended to the ledger item so the record does not depend on
any session transcript.

| Clause | State |
|---|---|
| 1. `just check` RED for non-root runners | ✅ FIXED, merged (PR #845) |
| 2. `fcntl.flock` reclaim mutex has ZERO coverage | ✅ FIXED, merged (PR #845) |
| 3. unguarded mutex I/O | ✅ **MERGED** — PR #847, merge SHA `0cf21c53` |

**Clause 3, as shipped.** `_stale_janitor_lock_reclaimed`
(`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_janitor_lock.py`)
now routes BOTH the mutex `open` AND the `fcntl.flock` one line below it through
`attempt(...)`, failing **closed** — a claimant that cannot take the reclaim
mutex has not established exclusion, so it reports contention rather than
reclaiming. The item named only the `open`; the `flock` carried the identical
unguarded exposure and was fixed in the same pass rather than left as a
known-adjacent defect.

PR: `livespec-orchestrator-beads-fabro`
[#847](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/847),
merged `2026-07-20T21:27:28Z` as `0cf21c53`, on `origin/master`, master CI green,
release 0.45.17 cut on top. Both feature worktrees (`fix-janitor-mutex-io` and
`docs-retire-mode-prose`) are fully merged and SAFE TO REAP.

### 🛑 THE PREVIOUS REVISION OF THIS FILE SAID "OPEN, not yet merged". IT WAS WRONG.

It also said "**Auto-merge deliberately OFF** per the item's hard constraint".
Both false, and the reason is a fleet-wide defect, not an operator slip.

`bd-ib-yqfw` carried the hard constraint "Do NOT enable auto-merge — this needs
dual review". The operator complied literally and **the PR merged anyway,
unreviewed, 136 seconds after creation** (`reviews: []`). Auto-merge was enabled
by `app/livespec-pr-bot` at 21:26:12Z, not by any human or agent action.

**`.github/workflows/auto-enable-merge.yml:68-75` enables `--auto --rebase` on
every non-draft PR whose author is in the allowlist `["thewoolleyman"]` — the
identity EVERY agent pushes under.** So "do not enable auto-merge" is
**unenforceable by inaction**: not doing it accomplishes nothing, because the
repo does it for you. The only levers the workflow actually honors are the
**`do-not-merge` label** (`:70`) or opening the PR as a **draft** (`:69`). The
item named a lever that does not exist, so its constraint read as satisfiable
while being inert.

Same defect class as D1's inert `auto_approve_ready`, one layer up: **a control
that reads as governing but is structurally inert.** And nothing surfaces the
override — `reviews: []` plus a clean green merge is indistinguishable from
review-passed, which is `bd-ib-hdd6`'s "silence reads as a PASS" hole.

Fleet-wide: the workflow is copier-generated from livespec core's
`templates/impl-plugin/.github/workflows/auto-enable-merge.yml.jinja`, so EVERY
`livespec-impl-*` repo behaves identically and every future "needs dual review"
item has the same hole. **Filed as `livespec-4rq4` (P1, livespec core — where
the template lives).** Disposition is deliberately NOT self-resolved: it is a
fleet policy call between wiring the label into the dispatch path, re-wording
items to name the real lever, or narrowing the allowlist (which risks
re-stalling the release train `livespec-c1k9` fixed).

**How the operator got it wrong, so the next session does not:** they read
`gh pr checks` (which showed checks passing) and reported merge state from
their own INTENT rather than querying it. `gh pr view <n> --json state,mergedAt,reviews`
is the right source. This is instance 11 of this thread's standing lesson,
committed while writing up that very lesson.

### ⚠ CORRECTION TO `bd-ib-yqfw`'s OWN PRESCRIBED REPRODUCTION — it is root-masked

The item's FIX 3 prescribes reproducing with a non-writable (`0o555`) parent
dir. **Building that test would have reproduced clause 1's exact bug class
inside the fix for clause 3.** Root bypasses the permission check and opens the
mutex happily, so such a test passes vacuously in CI's root container and
discriminates only off-root. Measured both ways rather than assumed:

| Provocation | uid 1000 | uid 0 |
|---|---|---|
| `0o555` parent dir | `PermissionError` | **OPEN SUCCEEDS (masked)** |
| directory at the mutex path | `IsADirectoryError` | `IsADirectoryError` |

The shipped tests make the mutex path a DIRECTORY, which fails identically for
both. Generalizable rule, same family as the item's own pid-1 coverage-probe
lesson: **when provoking an I/O failure in a test, choose a provocation that is
privilege-independent — permission-based provocations are silently disarmed for
root.** Recorded as a comment on `bd-ib-yqfw` so it does not live only here.

### The acceptance evidence, and the probe that must NOT be used

uid 1000 (`ubuntu`) throughout. BEFORE: pristine worktree at master `944d13d9`
→ `All 67 targets passed`. AFTER: three independent full-gate runs on the branch
(Green-amend pre-commit, pre-push, standalone) → `All 67 targets passed`, green
token written, coverage 100% with no pragma, carve-out, or per-file exemption.

**Never probe with the isolated `just check-coverage` recipe.** `justfile:621-628`
short-circuits on an existing `.coverage` data file and re-reports it WITHOUT
running the suite, so a standalone invocation emits a verdict decoupled from the
tree — the overseer hit exactly this and nearly reported a master regression that
does not exist, off a data file 16 hours old. Only the full gate is honest
(`check-per-file-coverage` regenerates the data immediately before). Filed as
`bd-ib-d6v1`.

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

### ✅ A GREEN GATE IS NOT A WORKING FACTORY — and the factory is now PROVEN to close work

The bar was never "the gate is green"; it was **a real item dispatched and
reaching `done` with NO human hand-closing it**. Before 2026-07-20 that had never
happened in the orchestrator repo: the day produced three correct merged fixes
and three MANUAL closes (D1, D2, the git-jsonl retirement). **That bar is now
met** — see the proof-dispatch section below.

**⚠ SCOPE RESTRAINT — the correct claim is "fixed, and demonstrated in two
ecosystems", NOT "working everywhere".** Overseer directive 2026-07-20, recorded
here so this thread's record never overstates it. Unattended closes are proven in
**exactly two repos**: `livespec-orchestrator-beads-fabro` (Python, `bd-ib-lmi5`)
and `livespec-console-beads-fabro` (Rust, `-bgc`). **The other six fleet repos
have NO post-fix unattended-close evidence.** A single green run per ecosystem is
one observation, and the reflection record says so (`green_streak: 1`).

Also carry forward: `bd-ib-9yi` (cargo-not-found / no Rust toolchain in the
orchestrator image). The overseer's sharper read, which holds: that ticket
describes the post-merge janitor running in the ORCHESTRATOR CONTAINER, which is
Python-only. The console janitor that succeeded ran HOST-SIDE, in a worktree
under the per-user worktree root, where cargo exists. So `bd-ib-9yi` was **not
refuted by that run — it was simply not exercised**, and stays latent for the
containerized path. Do not close it on the strength of `-bgc`.

### ✅ THE PROOF DISPATCH — `bd-ib-lmi5` — CLOSED UNATTENDED

Launched 2026-07-20 21:30:50Z, alongside clause 3 rather than after it.

| Field | Value |
|---|---|
| Item | `bd-ib-lmi5` (P1 bug) — `set-config` strips ALL comments + reorders keys in `.livespec.jsonc` |
| Dispatch id | `9c54b6372eba41849b789225552b77fc` |
| Repo | `livespec-orchestrator-beads-fabro` (the Python repo — the one that stranded) |
| Log | `nohup` log in the session scratchpad; dispatcher pid 1493605 |

**Why this item.** It self-declares "Autonomy: FACTORY (mechanically verifiable —
a round-trip test is the whole acceptance)"; it is product `.py`, so it exercises
the full Red-Green-Replay ritual through the factory; and it is the config writer
behind the console Settings surface — **not** janitor or dispatch machinery, so it
respects the hard constraint that the substrate never goes through the factory.

**It cannot pick up a substrate item.** `drive --action impl:<id>` emits
`dispatcher.py loop --budget 1 --parallel 1 --item <id>`. "loop" is the
subcommand name, not an unbounded drain. Four independent layers, verified in
code: (1) `_dispatcher_loop_selection.py:76-78` treats `--item` as a hard
WHITELIST filter on the ranked ready set; (2) `[: args.budget]` with budget 1;
(3) `run_loop_command` is a SINGLE PASS — no `while` loop, so there is no next
iteration; (4) the ready queue is empty anyway. Journal confirms
`loop-pick → picked: ["bd-ib-lmi5"], budget: 1`.

**Sizing caveat — it did NOT materialize.** The factory warned at 21:30:52Z that
the 4688-char, 3-part description exceeded one unattended turn. The item
converged anyway (`converged: true`, `bounced_to_regroom: false`,
`fix_loop_count: 21`, 2405s wall clock). **The warning is conservative, not
predictive** — do not pre-emptively split an item on the strength of it alone.

### ✅ OUTCOME — bar 4 is MET

    22:10:59Z  janitor-post-merge   exit_code 0   <- the EXACT stage that stranded
                                                     all three pre-fix dispatches
    22:11:00Z  ledger-complete
    22:11:00Z  acceptance-ai-pass   verdict PASS, criteria matched vs merged diff
    22:11:05Z  ledger-accept
    22:11:05Z  auto-disposition     ai-auto-accept (governing: acceptance_mode)
    22:11:05Z  outcome              stage done, status green, PR 850, sha 108d390
    22:11:06Z  reflection           green_streak 1

Cross-checked against **three independent sources**, never the dispatcher's own
summary: the live-window journal, GitHub (`#850 MERGED 22:08:15Z`, `108d390` on
`origin/master`), and the ledger (`bd-ib-lmi5` CLOSED, assignee `fabro`).

**Attribution was ESTABLISHED, not assumed.** The overseer captured a ledger
baseline at 22:00:25Z showing `lmi5` ACTIVE and re-read at 22:11:20Z showing
CLOSED; between those reads the operator was idle holding for checks and the
overseer performed only reads. No human closed it. *Bracketing a state change
with two timestamped reads while all actors are provably read-only is how you
attribute an unattended close — a green outcome record alone does not.*

Benign detail for anyone reconstructing the chain: `janitor-checkout-preclean
exit_code 128` is git's "not a working tree" on a pre-clean of a non-existent
path — non-fatal; the next `janitor-checkout-add` succeeded.

### ⚠ `reviewCount: 0` IS NOT EVIDENCE OF NO REVIEW — do not repeat this error

The operator read `gh pr view 850 --json reviews` returning `reviewCount: 0` and
reported that the factory's output "lands unreviewed". **False, and corrected by
the overseer.** A zero GitHub review count means no GitHub-native review OBJECT
was created; the workflow's in-workflow review node does not create one. The
journal shows it fired and approved:

    review-gate-telemetry : review_verdict "approve", review_fix_rounds 0,
                            review_hit_cap false, pr_shipped_on_cap false
    acceptance-ai-pass    : verdict PASS, diff.observed true (16038 bytes,
                            "merged diff read")

**Two independent gates fired**, neither bypassed by auto-merge. This was a null
in one system read as an absence in another — the same silence-reads-as-PASS
inversion as `bd-ib-hdd6`, pointed the other way.

**Two cases must never be collapsed** — the distinction is the whole substance of
`livespec-4rq4`:

| | PR #847 | PR #850 |
|---|---|---|
| Origin | HAND-BUILT substrate, never dispatched | FACTORY dispatch |
| In-workflow review node | none existed | fired, verdict `approve` |
| Reviewed before merge? | **NO — no review of any kind** | yes |
| Verdict | the genuine defect (`livespec-4rq4`) | the DESIGNED path, not a hole |

To establish whether a dispatched PR was reviewed, read the journal's
`review-gate-telemetry` — not GitHub's review objects. For a hand-built PR no
such record exists, and THAT absence is real.

### ⚠ READING THE DISPATCH JOURNAL — filter on `at`, or you will read history as live

`tmp/fabro-dispatch-journal.jsonl` gets re-opened/rewritten, so a follow-by-name
tail re-reads it from the beginning and **replays the entire 2811-line history**.
The overseer armed such a watcher and it immediately emitted ~28 events reporting
janitor exit 0, acceptance pass, and outcome green for items `3hgprw`/`r3vsnd` —
all historical. The file had grown by FOUR lines. Taking it at face value would
have reported an unattended green close from days ago as proof the factory is
fixed, on a record PREDATING the fix.

**Two counter-moves, use both:** filter every journal read on the `at` field
against an explicit cutoff, and sanity-check PR numbers against the current range
(the giveaway was PRs 227/238 when this repo is issuing 845+). Confirmed
independently here: 2811 lines total, exactly 4 at/after the 21:30:00Z cutoff.
This is the same class as the stale-`.coverage` trap above — a green-looking
signal read off the wrong source.

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
necessary.

#### ✅ THAT ASSESSMENT IS NO LONGER AN ARGUMENT — it was MEASURED

Spike run 2026-07-20/21; full evidence on `bd-ib-sfa2`. At the TRUE pre-fix
baseline `bf2d859`, same container, same image, same tests, **only the uid
differing**:

    ROOT     (uid 0)     78 stmts   0 miss   22 branch   0 partial   100%
    NON-ROOT (uid 1000)  78 stmts   1 miss   22 branch   1 partial    98%   missing: 133

Line 133 is `return True` in `_pid_is_alive` — the exact line `bd-ib-yqfw` named.
Root green, non-root red. **`1303 passed` in BOTH runs** — no test failed either
way, so the divergence is invisible to the suite and surfaces ONLY through
coverage. The "no divergence-detection machinery needed" claim is now empirical.

#### The image is NOT the real cost — that was wrong

The line above ("Real cost is the IMAGE") was superseded. A non-root matrix needs
**no image change at all**. The only blocker is that `/root` is mode **0700**
while the whole toolchain lives beneath it (`mise` itself is at
`/root/.local/bin/mise`; there is NO copy anywhere else on the filesystem). Env
overrides alone CANNOT fix that — they change where mise WRITES, not where it IS.
A root-privileged `chmod 0755 /root` at job start, then `setpriv` to uid 1000
reusing the BAKED toolchain read-only, works: full `check-coverage` on master ran
**1950 passed, 0 missed, 100%** as uid 1000 in ~49s, with no toolchain install
(the baked mise dir's mtime stays at image-build time).

**Limitation, which must travel WITH the capability, never separately:** this is
a PARTIAL replica — "uid 1000 with access to root's toolchain", not "uid 1000 as
the janitor sees the world". Any divergence depending on `/root` genuinely being
0700 stays invisible to it. The faithful alternative relocates the toolchain to a
world-readable path in `livespec-dev-tooling`'s `docker/fabro-sandbox/base`
layer, costing a fleet-wide rebuild + republish + pin bump. **Bounded tradeoff,
maintainer's call, NOT decided here.**

Three traps recorded on the item for anyone re-deriving this: `HOME` must not be
under `/tmp` (it puts the janitor venue inside the `/tmp/*` coverage omit glob and
trips `livespec-impl-beads-1l6`'s regression guard); the two jobs must not share
`UV_CACHE_DIR` (root-owned cache files break the non-root run, intermittently);
and **`ff97ad8~1` is NOT the pre-fix baseline** — it resolves to `abdc50c`, which
already carries the coverage fix, so measuring there shows no divergence and
reads as "the route is decorative". Start from `bf2d859`.

Still owed: the demonstration above is SCOPED to the janitor-lock module (a local
full-gate run carries container-only noise from integration tests needing
docker/network). A full-matrix demonstration in real CI, plus criteria 3 and 4,
remain. `ci.yml` is UNTOUCHED.

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

**The ride-along prose is CARRIED AND MERGED — the debt is discharged.** The
three comment-only corrections (`dispatcher.py`, `_dispatcher_cost_pricing.py`,
`commands/CLAUDE.md`) rode PR #847 alongside clause 3's real tests, which is
exactly the carrier the previous session anticipated, and landed in `0cf21c53`.
The worktree `~/.worktrees/livespec-orchestrator-beads-fabro/docs-retire-mode-prose`
now holds nothing unique and is **safe to reap**.

One residual, P2 and cosmetic: `commands/CLAUDE.md` still says an unattended
queue drain "refuses to keep picking on unobservable cost" UNQUALIFIED, while
the `_dispatcher_cost_pricing.py` edit in that same PR correctly scopes refusal
to `LIVESPEC_COST_MODE=enforce` (the default `report` never refuses). Prose
half-corrected; self-resolvable in any later pass.

### Clause 3 was NOT an ownership-correctness fix — do not describe it as one

Verified in-session by a six-process probe against merged `origin/master`, and
against `0cf21c53~1` for discrimination (the second reviewer went idle three
times across two requests and never delivered, so this angle was verified
directly rather than recorded as reviewed):

| Code | mutex healthy | mutex BROKEN (dir at `<lock>.reclaim`) |
|---|---|---|
| merged `0cf21c53` | 1 winner, no exception | **0 winners, no exception**, stale lock intact |
| pre-fix `0cf21c53~1` | 1 winner, no exception | 0 winners, **`IsADirectoryError` UNCAUGHT** |

**The winner counts are identical before and after.** Double ownership was
already impossible pre-fix — because CRASHING also prevents it. The only
discriminator is the uncaught-exception field. So what clause 3 bought is: an
expected environment error that **killed the whole dispatcher process mid-drain**
now yields **one clean per-item `janitor-checkout-locked` outcome**. That is a
fail-open-invariant repair (the `0jxs` class), NOT a race repair. Saying "fixed
a lock race" would overclaim and misdirect anyone later auditing the ownership
protocol. The mutex remains load-bearing for the original `bd-ib-w4h4` race;
nothing here weakens it.

Also confirmed: fail-closed refuses to **CLAIM**, not merely to reclaim (the
safe direction), and the `for _ in range(2)` loop cannot reach a second
iteration on the mutex-failure path — `claim_janitor_lock:47-48` returns the
contention detail immediately. No permanent wedge: the mutex is opened only on
the contention path, so removing the stale lock file recovers via `O_EXCL`
without touching the mutex at all.

**Follow-up filed as `bd-ib-lzau` (P2):** PR #847's claim that the mutex
`open`/`flock` were "the only filesystem access in the module not wrapped in
`attempt(...)`" was OVERSTATED. `claim_janitor_lock:38` (`mkdir`, on every claim
path) and `_write_janitor_lock:62-64` (`os.fdopen` + writes, on the SUCCESS
path, where an ENOSPC can leave a partial-payload lock that reads as "no pid
recorded") are both still raw — same crash class.

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
