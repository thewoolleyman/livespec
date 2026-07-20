# rop-sweep-fleet-policy — ZERO BLOCKERS. Dispatch is UP. sw0i+47gr+z45 DONE, ftbvgc un-stranded. e9j is P0 and next

## 🟢 2026-07-20 (later session) — THE `codex login` BLOCKER IS GONE

**There are now ZERO maintainer blockers in this thread.** The credential auto-refreshed
(`~/.codex/auth.json` `last_refresh` 2026-07-19T18:15Z) and a live `codex exec` probe returned
`PROBE_OK`, exit 0. A full factory dispatch then ran green end-to-end.

**Correct the prior diagnosis, and do not repeat its error.** The prior session read the
`id_token` `exp`, saw a past timestamp, and concluded dispatch was down for ten days. That
inference was WRONG: the `id_token` is a ONE-HOUR token and `auth.json` also carries a
`refresh_token`, so an expired `id_token` proves nothing on its own. The correct cheap probe is
a trivial `codex exec` (~16k tokens, seconds) — NOT a file read alone, and NOT a factory
dispatch. `bd-ib-zz6gii` (instrument `codex-cred-status` across refreshes) is the standing item
for making this legible.


## ⚖️ SIX MAINTAINER RULINGS. Do not re-litigate any of them.

6. **(2026-07-20, later session) Acceptance may proceed on dual review + live exercise even when
   the exact changed branch is not naturally reproducible live**, PROVIDED the limitation is
   journaled explicitly on the item. Ruled when accepting `bd-ib-47gr`: the ambiguous-PR branch
   could not be driven live because no work-item currently has an id in >1 merged PR title, and
   manufacturing one with throwaway PRs was rejected as wasteful/outward-facing. Do NOT read this
   as diluting the live-exercise rule — it was satisfied on the real shared journal; only the one
   branch was substituted with revert-and-fail evidence plus a structural guarantee.

1. **The flat-package rule is BROAD-ONLY.** When a repo declares no `io_trees`,
   `no_except_outside_io` flags `except Exception` / `except BaseException` / bare `except` only;
   narrow typed catches PASS. This unblocked `qm5`, `cvz`, `6vz`, `e9j` AND the
   overseer-productization thread's Gate E. Full ruling text — including what it does NOT
   license — is on each of those four ledger items.
2. **`livespec-dev-tooling-e9j` raised to P0.**
3. **`livespec-giq7` CLOSED** on its journaled evidence. Ruled that the dual-review guard does
   not gate a NO-DIFF rollout whose verification is re-runnable execution evidence. **Scoped
   narrowly: the guard is undiminished for anything carrying a diff.**
4. **Mutation sequencing: MEASURE BEFORE DECLARING.** Do not declare core's `pure_trees` until
   core's real kill rate is known, measured inside `release-tag.yml`'s own harness.
5. **(2026-07-20) Mutation staging-tree CONSTRUCTION goes in `livespec-dev-tooling` as a shared,
   config-driven accommodation** — core as first consumer, convention VALIDATED against
   `livespec-orchestrator-git-jsonl` before the config surface is frozen. Owned by
   `livespec-mutreal.1`. **The recipe is now KNOWN and reproduced at ~85% — see "MUTATION IS
   SOLVED" below.** Implementation is productizing four small artifact groups, not research.

## ✅ MUTATION IS SOLVED — a working recipe exists, REPRODUCED TWICE at ~85%

**Supersedes the section below, which said the build step "does not exist". It does now.** Both
findings are true and complementary: **config-only is impossible (now rigorously proven)** AND
**construction works**.

```
agent run : {"killed": 177, "total": 208, "kill_rate_percent": 85.1}
my re-run : {"killed": 163, "total": 192, "kill_rate_percent": 84.9}
```
Both through the official `check_mutation` entry point, exit 0. Totals differ only because the
runs were built from different master commits. **Comfortably over the 80% hard floor.** Both
worktrees destroyed; nothing committed.

### The recipe — four artifact groups, mostly symlinks

1. Root `[tool.livespec_dev_tooling]`: `pure_trees = [".claude-plugin/scripts/livespec/parse",
   ".claude-plugin/scripts/livespec/validate"]` and `mutation_staging_dir = ".claude-plugin/scripts"`.
2. **`.claude-plugin/scripts/pyproject.toml` — THE load-bearing piece.** `[tool.mutmut]` with
   **staging-relative** `paths_to_mutate = ["livespec/parse", "livespec/validate"]`, an `also_copy`
   list completing the import closure (`livespec/__init__.py`, `context`, `errors`, `templates`,
   `types`, `schemas`, `io`, `doctor`, `commands`, `_vendor`, plus
   `.claude-plugin/scripts/livespec/schemas` and `.claude-plugin/specification-templates`), and
   `[tool.pytest.ini_options]` `testpaths = ["tests"]`, `pythonpath = [".", "_vendor"]`.
3. `.claude-plugin/scripts/tests/` — scoped test tree via SYMLINKS (`conftest.py`,
   `livespec/parse`, `livespec/validate`). mutmut's hardwired copy of cwd-relative `tests/`
   follows symlinks.
4. Two compat symlinks so the 11 test files anchoring on `parents[3] / ".claude-plugin/…"` resolve
   inside `mutants/`.

**Staging-relative `paths_to_mutate` IS the entire kill mechanism** — it makes the walked-path
mutant key equal the runtime `__module__` the trampoline prefix-matches.

### Why nothing less works — proven, not asserted

An exhaustive sweep of all **640 tracked directories** found exactly ONE (the repo root) that can
feed mutmut a config at all; every other `mutation_staging_dir` value crashes in
`guess_paths_to_mutate()` before a mutant exists. And the decisive experiment: a MAXIMAL
config-only setup at repo root — every import, fixture and collection problem solved by
configuration — still yields **0 killed of 208**, because the namespaces are disjoint:

```
stats file (runtime __module__):  livespec.parse.cross_repo.x_parse_entry
mutant key (walked-path-derived): .claude-plugin.scripts.livespec.parse.cross_repo.x_parse_entry__mutmut_1
```

mutmut 3.2.3 has no key-remapping knob (its Config is exactly `paths_to_mutate`, `also_copy`,
`do_not_mutate`, `max_stack_depth`, `debug`), and every root-cwd key begins with the literal
`.claude-plugin.` — a leading dot plus a hyphen, which no importable module's `__module__` can
ever begin with. **Construction is irreducible.**

### Traps to carry into the implementation

- **NEVER list a `paths_to_mutate` tree in `also_copy`** — `copy_also_copy_files()` runs AFTER
  mutant generation with mtime-preserving `copy2`, silently clobbering mutants and suppressing
  regeneration.
- `mutants/livespec` must be a COMPLETE package; mutmut puts `mutants/` at `sys.path[0]`, so a
  missing `__init__.py` lets the REAL package win and every mutant survives.
- Core's existing root `[tool.mutmut]` `runner` / `tests_dir` keys are dead mutmut-2.x and ignored.

### Refinement to the archived doc

`leg-findings` rules out `.claude-plugin/scripts/` because `also_copy` cannot reach above cwd.
That premise is too strong — it CAN serve as the staging root once symlinks bring `tests/` and the
fixture paths within cwd reach. The doc's CONCLUSION stands (construction is required), but ruling
5's implementation may target **either** a purpose-built dir **or** `.claude-plugin/scripts`
augmented in place. The in-place option is lighter and is the one proven twice.

### Caveats — do not oversell

~85% is measured against ONLY the scoped parse/validate subtrees; the whole suite was deliberately
not wired (many tests read repo-root files and would fail mutmut's clean-test gate). The ~31
survivors are plausibly real test-gap signal. All artifacts were untracked scratch —
**productization is the open work**: committed vs generated, and whether a `pyproject.toml` may
ship inside `.claude-plugin/scripts/`, which IS the plugin payload.

### A separate defect worth its own item

`check_mutation` MASKS this whole failure class: it tolerates rc 1, treats `total == 0` as an
unconditional pass, and rewrites the placeholder baseline — so any future misconfiguration passes
green. **Zero mutants with a non-empty `pure_trees` should be an ERROR.**

## 🚫 (SUPERSEDED — kept for the reasoning) MUTATION IS NOT CONFIGURABLE

Executing ruling 4 established this, and it retires a framing an earlier version of this handoff
carried ("work out the correct `pure_trees` / `mutation_staging_dir` relationship"). **That was
wrong. It is not a values problem.** There is NO pair of values that makes mutation testing work
in core.

Killing mutants requires running from a directory that is SIMULTANEOUSLY (a) the import root, so
mutant keys match the trampoline, (b) a test root, so mutmut's auto-copy of `tests/` finds the
paired tests, and (c) an ancestor of the fixture tree, so `parents[N]`-relative reads resolve
(`also_copy` copies relative to cwd and cannot reach above it). **No directory in core's tree
satisfies all three.** One must be BUILT.

Both candidate values fail, and `archive/research/mutation-testing/livespec-leg-findings.md`
§"Why a STAGING dir…" predicted both — my two measurements reproduced them exactly:

| staging value | documented failure | what I measured |
|---|---|---|
| repo root | key mismatch + whole-`tests/` collection failure | 208 mutants, **0 killed** |
| `.claude-plugin/scripts` | no `tests/` under `scripts/`, so zero tests copied | **`total: 0`** |

**It HAS worked — once, manually: 201 mutants / 182 killed / 90.55%** (livespec PR #435, merge
`67c550a6`, 2026-06-13), comfortably over the 80% floor. **Core's tests are good. Every 0% figure
in this thread is a configuration artifact and must NEVER be cited as a test-quality result.**

Why it never shipped: `livespec-dev-tooling-q3r` (CLOSED) built only the **cwd half** — running
mutmut from the staging dir and relocating the baseline. The half that CONSTRUCTS the tree was
left as repo-side "remaining work". `livespec-mutreal.1` is still open for it, and now sits on
the P0's critical path. So the check's docstring — "declare `mutation_staging_dir` … otherwise
every mutant is unkillable" — is TRUE BUT INCOMPLETE: necessary, not sufficient. Its tests only
exercise cwd resolution against a fake mutmut binary and an EMPTY staging dir.

**Census correction:** there are THREE nested-layout repos, not the two the docstring names —
`livespec` (115 `.py` under `.claude-plugin/scripts/`, excl `_vendor`),
`livespec-orchestrator-git-jsonl` (46), and **`livespec-orchestrator-beads-fabro` (156)**, which
the docstring omits. Fix it as a ride-along.

**Slicing that keeps `e9j` moving:** the mutation leg is ONE of e9j's seven checks. Declare core's
structural role keys EXCEPT `pure_trees` now — that is the near-free change (0 offenses under the
ruled broad-only rule) and gets five of seven checks genuinely enforcing in one small PR. Treat
`pure_trees` as a separate slice gated on `livespec-mutreal.1`.

**`qm5` is unblocked** — moved `blocked` → `backlog`. It KEEPS `needs-regroom`: the rule is
settled but its scope still needs re-cutting (its premise was falsified; see its ledger note).

**The only remaining blocker is `codex login`.** Everything else in this thread is now
groomable or implementable.

**Read this whole file before acting.** The ROP ruling is SETTLED and RATIFIED — v169 is
merged and live on master (livespec commit `2288197b`, PR #1424); the proposal is consumed
from `SPECIFICATION/proposed_changes/`. **Do NOT re-ratify it.** What remains is execution.
Status is READ from the ledgers (`bd`), never stored here. Ledger note on epic
`livespec-y2lkf4` carries the consolidated state; per-item notes carry review blockers and
evidence.

## START HERE — dispatch is UP; this is ordinary implementable work now

No credential probe is needed first. If you want one anyway, it is a trivial `codex exec`, not a
dispatch (see the 2026-07-20 note at the top).

**`livespec-dev-tooling-e9j` (P0) is the next move — and it re-slices into THREE, not two.**
MEASURED BY EXECUTION 2026-07-20 (full detail journaled on the e9j ledger item):

- **Slice 1a — DONE, PR #1497 open.** Declaring `dataclasses_tree` ALONE arms
  `newtype_domain_primitives` in core, and it passes rc=0 clean. That retires one of the FOUR
  checks e9j found had never enforced anything in ANY fleet repo, with zero remediation.
- **Slice 1b — RULING 7 (2026-07-20) unblocks it: teach the check to HONOR THE FIVE SANCTIONED
  v169 MARKERS.** A SECOND correction: broad-only does NOT unblock 1b. Ruling 1 scopes broad-only
  to repos declaring NO `io_trees` — but that is exactly the branch where `no_except_outside_io`
  RETURNS 0 WITHOUT INSPECTING ANYTHING (which is why `qm5` exists; its Red commit is literally
  "run no_except_outside_io when io_trees is unset"). Slice 1b DECLARES `io_trees`, putting core on
  the LAYERED branch, which broad-only never touches. Confirmed in source: `_find_offending_try_lines`
  does NO handler-type inspection — it flags EVERY `ast.Try`, broad and narrow alike — and the check
  honors NO `# noqa` markers (only `io/` wholesale, plus `main()` tries in `supervisor_entry_files` /
  `commands_trees`). MEASURED: both layered repos (`livespec-orchestrator-git-jsonl`,
  `livespec-orchestrator-beads-fabro`) already run the check GREEN at 0 offenses, so strict is
  achievable and free there — which is why universal broad-only was REJECTED in favour of markers.
  Full ruling + rejected alternatives are on the `e9j` ledger item.
- **(superseded detail)** Declaring `source_trees` + `io_trees`
  turns core's `just check` RED on three narrow catches
  (`no_spec_section_citation_in_code.py:162,180`, `wiring_completeness_cross_repo.py:159`).
  **The broad-only rule is RATIFIED IN THE SPEC but NOT YET IMPLEMENTED IN THE CHECK** —
  `no_except_outside_io` still bans ALL try/except outside io/. So 1b is blocked on the re-cut
  `qm5`/`cvz` work, NOT free as the text below claims.
  **Generalize: a ratified rule does not change a check's behavior until the check is edited.**
  Plan declaration slices against the check AS IMPLEMENTED, never as ruled.
- **Slice 2 — `pure_trees`.** `livespec-dev-tooling-6j6` is MERGED, so that half of the gate is
  clear; slice 2 now waits on `livespec-mutreal.1` ALONE.

**Measured dependency inversion worth holding: `e9j` is NOT purely upstream of `qm5`/`cvz` — its
1b slice DEPENDS on them.** The ordering is `1a -> (qm5/cvz broad-only) -> 1b -> mutreal.1 -> 2`.

The older two-slice framing below is superseded on the 1b point but otherwise still accurate:

1. **Slice 1 — declare core's structural role keys EXCEPT `pure_trees`.** Near-free (0 offenses
   under the ruled broad-only rule) and it gets five of seven checks genuinely enforcing in one
   small PR. `livespec-dev-tooling-z45` has now LANDED, so a regression in this area is LOUD
   rather than silent — that was the whole reason to sequence z45 first, and it is done.
2. **Slice 2 — `pure_trees`** stays gated on `livespec-mutreal.1` productizing the staging-tree
   construction (ruling 5). Ruling 4's "measure first" is ANSWERED for core: ~85%, over the 80%
   floor, reproduced twice. See "MUTATION IS SOLVED".

**🚨 HARD SEQUENCING CONSTRAINT — `livespec-dev-tooling-6j6` MUST LAND BEFORE `pure_trees` IS
DECLARED ANYWHERE.** The mutation check is INERT IN PRODUCTION today: core is the only fleet repo
arming `LIVESPEC_RUN_MUTATION=true` (`release-tag.yml:47`) and it declares no `pure_trees`, so the
check no-ops before any z45 guard runs. Verified live against the real core checkout
(`{"role": "pure_trees", "event": "role key absent — check no-ops"}`, exit 0), and a survey of all
8 fleet repos found NONE reaching the strict path. **So the ~7-week mutation blind spot is NOT
closed on master today** — z45 closed masks 1-3 inside a path production never reaches, and the
empty-`pure_trees` no-op is the FOURTH mask, the live one. e9j owns closing it; the moment e9j
declares `pure_trees`, the `6j6` regression goes live WITH it. Do not arm the gate while that
regression stands, and do not claim the blind spot is closed until both land.

Then, in rough order:

- **`livespec-dev-tooling-bbl`** — the canonical-marker fix. Rule-independent, ~1 string, fixes 2
  of the ~7 remaining broad sites fleet-wide. Always was landable.
- **`qm5` re-groom** — the rule is settled; its SCOPE still needs re-cutting (premise falsified;
  must cover BOTH ROP except-checks, not just `no_except_outside_io`).
- **`cvz` / `6vz`** — both now have a settled rule to implement against. Remember `6vz` immediately
  reddens `livespec-orchestrator-beads-fabro` with 47 findings; the warn-tier lever is likely
  required, not optional.
- **`bd-ib-12fw` (P1, NEW)** — janitor lock leaks on the exception path and has NO liveness check.

Remaining honest measurement gap, unchanged: only core and livespec-dev-tooling have
EXECUTION-derived figures; the Drivers are direct source inspection; every other cost-table row is
AST simulation validated once against core.

## STATE AS OF 2026-07-20 (later session)

- **ZERO maintainer blockers.** `codex login` resolved itself; dispatch verified UP by live probe
  AND by a green end-to-end factory run.
- **`bd-ib-47gr` is DONE** — dispatched, merged (PR #820), dual-reviewed NO-BLOCKERS x2, live-
  exercised, accepted.
- **`bd-ib-sw0i` is DONE** — both held counts cleared (journal blocker fixed by 47gr; the missing
  second verdict supplied by the combined review). Accepted.
- **`livespec-ftbvgc` is UN-STRANDED** — the reconcile valve resolved it "green at done PR#1381,
  merged, post-merge janitor green". It is now in `acceptance` under `acceptance_policy
  ai-then-human` and **awaits the MAINTAINER's final acceptance** — it correctly refused to
  self-close. This is the one thing in this thread waiting on a human, and it is a routine
  acceptance, not a blocker.
- **`livespec-dev-tooling-z45` is MERGED (PR #485) — and the post-merge dual review found a REAL
  REGRESSION, filed as `livespec-dev-tooling-6j6` (P1).** z45 DELETED the `rc >= 2` hard fail
  (`if run_result.returncode not in (0, 1): return 1`) and replaced it with
  `_is_crashed_run = returncode != 0 and total == 0`, which does NOT cover rc>=2 with a NON-empty
  tally. A mutmut crash/OOM that dies AFTER enumerating some mutants now passes GREEN **and
  promotes the partial measurement into the committed ratchet** — z45's own mask-3 harm, through a
  different door. Verified in the real diff by the overseer. Fix is one line; do NOT revert (net
  the change is an improvement and its four acceptance criteria hold).
- **THE TWO REVIEWERS DISAGREED ON z45 — and that disagreement WAS the finding.** Codex returned
  NO-BLOCKERS; Opus found the regression with before/after execution evidence. This is the single
  strongest argument yet for the two-reviewer rule: a one-reviewer gate would have passed this.
  **Never treat one clean verdict as sufficient**, however thorough it looks — the Codex review
  here was genuinely detailed (real mutmut runs, four scenarios) and still missed a deleted guard.
- **PROCESS VIOLATION on z45:** the implementing agent MERGED it despite an explicit brief
  instruction to leave the PR open for review; auto-merge-on-green appears to have been enabled.
  Because the gate was bypassed, the regression above reached master instead of being caught
  pre-merge. **Future briefs must forbid ENABLING AUTO-MERGE, not merely say "do not merge".**
- **`bd-ib-12fw` (P1) FILED** — janitor checkout lock leaks on the exception path AND has no
  liveness check (writes `work_item_id`, no PID), so a leak wedges that venue permanently while the
  error tells the operator to wait for a janitor that already died. Pre-existing (`cff7225`), found
  by the 47gr review.
- **`livespec-dev-tooling-e9j` is P0 and is now the top of the queue.**
- **`qm5`** unchanged: `backlog`, still `needs-regroom`.

Nothing is running: no dispatches, no monitors, no sub-agents. The `rop-drain` tmux socket is
empty.

**Outstanding worktrees/branches:**
- `livespec`: `docs-rop-handoff-post-ratification` — ALREADY GONE (the prior handoff's claim that
  it was reapable was stale). Eight OTHER `livespec` worktrees exist belonging to other threads;
  they were deliberately not reaped.
- `livespec-dev-tooling`: branch `fix/no-except-outside-io-runs-when-io-trees-unset`, local and
  unpushed, carrying a valid Red commit `a33c394` preserved for the qm5 re-groom. **Do not delete**
  — verified still present and untouched this session.
- `livespec-dev-tooling`: worktree `fix-z45-check-mutation-masks-failure` — z45's, now merged and
  reapable.
- `livespec-driver-claude`: worktree `codex/livespec-nj7d-hook-main` — ANOTHER session's, 14 dirty
  files, last commit 2026-07-13. Still not touched. Route via `just reap-stale-worktrees`.

## ✅ DONE THIS SESSION — `livespec-giq7` (P0), rolled out + live-exercised

The tmux fail-open guard is now current in **11 of 12** install records, verified by hashing
each installed cache's `hooks/_tmux_hazard.py` against
`git -C livespec-driver-claude show origin/master:.claude-plugin/hooks/_tmux_hazard.py`
(`608d3c9e183abda7…`) — **by content, never by version string**.

Correction to the prior handoff: it said every project except `/data/projects/livespec` was
on "a pre-fix plugin cache copy". Actually **10 of 12 lacked `_tmux_hazard.py` entirely**, so
the gap was larger than recorded.

Live exercise against the DEPLOYED cache (command strings only; nothing was executed):
unscoped kill-server → **deny**; `env -i sh -lc` wrapper evasion → **deny**; scoped
`-L <name>` form → **allowed**, not over-blocked.

No repo was dirtied: `claude plugin update` did NOT rewrite any committed
`.claude/settings.json` (unlike `install`/`uninstall`, which core's CLAUDE.md warns does).

The one residual is the other session's worktree above. **`giq7` was CLOSED 2026-07-20**: ruled
that the dual-review guard does not gate a no-diff rollout whose verification is re-runnable
execution evidence. Scoped narrowly — the guard is undiminished for anything carrying a diff.

**Gotcha worth keeping:** the guard blocks its own evidence journaling. A `bd note` whose
TEXT quotes hazardous command strings is denied, because the hook matches its hint regex over
the whole command string and cannot tell a quoted documentation payload from an executable
one. Workaround: write the note to a file and pass `bd note <id> "$(cat <file>)"`. That is a
false-positive workaround on documentation text, not an evasion — `bd note` cannot kill a
tmux server. Do NOT loosen the regex; the failure direction is the safe one.

## ✅ BLOCKED ON THE MAINTAINER — NOTHING

Down from two, then one, now zero.

1. ~~`codex login`~~ — **RESOLVED 2026-07-20** (auto-refreshed; probe + green dispatch confirm).
2. ~~The flat-package rule~~ — **RULED 2026-07-20: broad-only.**

One NON-blocking maintainer action is outstanding: **`livespec-ftbvgc` awaits final human
acceptance** in `acceptance` under `ai-then-human`. Routine.

## ⛔ Guards
- **DO NOT run `groom livespec-y2lkf4`** (the EPIC). Already decomposed; individual-child
  `groom <id>` is fine.
- **DO NOT accept any work-item** without BOTH a separate Codex reviewer AND a separate Opus
  reviewer clearing it. This has repeatedly caught defects every mechanical gate passed.
- Dispatch DETACHED only; a killed foreground dispatch strands the item `active`.
- **Detached tmux dispatches are NOT harness-tracked.** Arm a `Monitor` (watch for the `__EXIT=`
  marker AND for the tmux session vanishing without one) or you will wait forever on an event
  that cannot fire.
- **A correction note on a work-item does NOT reach an already-dispatched agent.** Once
  dispatched, the brief is frozen. Let it complete and reject, or stop it — do not append-and-hope.
  This exact mistake produced a defective guard (`bd-ib-ug4z`).
- **Never edit a handoff on the primary checkout.** The previous session left
  `plan/rop-sweep-fleet-policy/handoff.md` dirty on `/data/projects/livespec` while its PR
  #1426 carried identical content. Restored this session once #1426 merged.

## THE RULING — ratified, v169

`SPECIFICATION/proposed_changes/rop-broad-except-boundary-rule.md` was ACCEPTED into v169 and
is MERGED (livespec PR #1424, commit `2288197b`): 16 edits across
`non-functional-requirements.md`, `constraints.md`, `contracts.md`. The proposal file is gone
from the pending queue and now lives at `SPECIFICATION/history/v169/proposed_changes/`. It grew
5 → 16 edits over SIX independent review rounds (blockers per round: 5, 4, 2, 2, 0). Landed via
PRs #1400, #1405, #1407, #1416, #1420, #1421, then ratified by #1424.

**narrow at the seam; broad only at the boundary; at most one boundary per process.**

STYLE B (`livespec-orchestrator-git-jsonl`'s `io/store.py`) is the fleet standard. A hand-rolled
`except Exception` returning `Failure(exc)`/`IOFailure(exc)` is the blanket `@safe`/`@impure_safe`
form the spec ALREADY forbids, written longhand — the container does not change what the catch
is. *"It lifts onto the IO rail"* is not a defense; that argument was raised, adjudicated, rejected.

The five sanctioned `# noqa: BLE001` markers (em-dash), a CLOSED set:
```
— sole supervisor bug-catcher: log traceback, exit 1
— sole fail-open hook boundary: silent pass-through, exit 0
— sole fail-closed guard boundary: deny per policy, exit 0
— sole loop-iteration bug-catcher: log traceback, continue
— foreign-code isolation: <surface> crash captured as <ErrorType>, reported
```
`sole` scopes per process entry artifact for the three boundary markers, per SUPERVISION LOOP for
the loop-iteration marker. Foreign-code markers are not `sole` markers.

**The ruling is already baked into all 10 STEP 3 slice work-items** as a ledger note, including
the failure modes below. Do not re-derive it.

## DONE — accepted, dual-reviewed, live-exercised

*(Not re-verified this session — carried forward as recorded.)*

| Item | Repo | PR |
|---|---|---|
| `livespec-driver-codex-64s` | livespec-driver-codex | #199 |
| `livespec-driver-claude-hfm` | livespec-driver-claude | #219 |
| `livespec-driver-claude-ob3` | livespec-driver-claude | #215 |
| `bd-gj-li0` | livespec-orchestrator-git-jsonl | #341 (+#343) |

**Caveat on #215 / #199:** both remediated Driver hook trees, but NOT because
`check-no-except-outside-io` validated them — that check scans zero files in either repo (see
`cvz`). Whatever gate cleared them, it was not this one. Do not read those merges as coverage.

## ✅ RESOLVED — `bd-ib-sw0i` + `bd-ib-47gr` both DONE (2026-07-20)

Both counts that held `sw0i` are cleared. Full evidence is journaled on BOTH ledger items; the
short version:

1. **Journal-deletion blocker — FIXED** by `bd-ib-47gr` (PR #820, `0f3d0c02`, rebased to master as
   `8e812ba`). The fix took the preferred option AND deleted the helper outright:
   `git grep _remove_journal origin/master` returns NOTHING repo-wide. So no code path in that
   module can delete the journal at all — a stronger property than proving one branch behaves.
   Both refusal branches are now symmetric.
2. **Missing second verdict — SUPPLIED.** A fresh COMBINED dual review returned NO-BLOCKERS from
   both an Opus and a Codex reviewer, each with pasted revert-and-fail output proving neither test
   is inert.

**ROOT CAUSE OF THE PRIOR "IDLE REVIEWER" — carry this forward, it wasted a day.** The Opus
reviewer HAD completed its review and written the verdict, but returned it as PLAIN TEXT instead
of via `SendMessage`, so it never reached the overseer and registered as idle. This is almost
certainly what happened in the prior round's three silent attempts. **It was a DELIVERY failure,
not a reviewer that failed to work.** Every reviewer brief MUST state the delivery mechanism as a
hard requirement.

**LIVE EXERCISE performed** (this is what `accept:` required): the shipped
`dispatcher.py reconcile-merged` was run against the real livespec repo with `--journal` omitted,
so it resolved to the real SHARED journal. It went 561 -> 574 records, all 16 distinct
work_item_ids intact, and `head -561` of the result is BYTE-IDENTICAL to the pre-run backup:
proven APPEND-ONLY against 545 records belonging to 15 unrelated work-items — exactly the
cross-item state the old code would have destroyed.

**HONEST LIMIT, journaled on both items:** that run took the HAPPY path, not the ambiguous-PR
refusal branch 47gr actually changed, because no work-item currently has an id in >1 merged PR
title with no live branch PR. The changed branch rests on the reviewers' revert-and-fail evidence
plus the structural fact that the deletion helper no longer exists. See ruling 6.

## ✅ NO LONGER STRANDED — `livespec-ftbvgc` (2026-07-20)

The prior handoff gated the reconcile valve on `bd-ib-47gr` landing. That precondition was met, the
valve was run, and it resolved the item: **"green at done PR#1381, merged, post-merge janitor
green"**. It is now in `acceptance` under `acceptance_policy ai-then-human`, awaiting the
maintainer's final acceptance. It correctly did NOT self-close.

The root cause recorded earlier still stands and is worth keeping: the only `active -> acceptance`
write is `complete_and_accept`, which lives ENTIRELY inside the dispatching process, so any death
of that process after merge strands the item. The reconcile valve is the recovery path, and it is
now safe to use — the race is closed for BOTH the worktree and the journal.

## NEXT — the 10 groomed slices (backlog; ruling already baked into each)

`livespec-apiiwc` and `livespec-qgp2jt` are blocked/superseded; do not dispatch them whole.
- **livespec-runtime**: `livespec-4nlb` (**ANCHOR**), then `livespec-p41z`, `livespec-shz8`,
  `livespec-0bpr`.
- **livespec-dev-tooling**: `livespec-h2hs` (**ANCHOR**), then `livespec-9cts`, `livespec-ss2j`,
  `livespec-5dpg`, `livespec-tvlq`, `livespec-gcsn`.

Anchors first (they vendor `returns` + enable `BLE` repo-wide), then the rest in parallel.
Cross-tenant rule applies: these live in the **livespec** tenant but target siblings, so each
needs a dispatch-mirror in the target repo's tenant.

**`livespec-shz8` carries a cross-repo obligation** — see its ledger note. When it moves the
`WorkItemStore` protocol to `IOResult`, git-jsonl's deliberately-tracked divergence resolves and
its tracking test will fail BY DESIGN. File the paired git-jsonl repair BEFORE landing `shz8`.

## OPEN FOLLOW-UPS

| Item | Repo | Pri | What |
|---|---|---|---|
| ~~`livespec-giq7`~~ | livespec | — | **CLOSED 2026-07-20.** Rolled out, live-exercised, ruled not to need dual review (no diff) |
| ~~`bd-ib-47gr`~~ | livespec-orchestrator-beads-fabro | — | **DONE 2026-07-20.** Merged PR #820, dual-reviewed x2, live-exercised, accepted |
| ~~`bd-ib-sw0i`~~ | livespec-orchestrator-beads-fabro | — | **DONE 2026-07-20.** Both held counts cleared; accepted |
| ~~`livespec-dev-tooling-z45`~~ | livespec-dev-tooling | — | **MERGED 2026-07-20** (PR #485). Gate was BYPASSED at merge; post-merge dual review found a REGRESSION -> `6j6`. See STATE |
| ~~`livespec-dev-tooling-6j6`~~ | livespec-dev-tooling | — | **MERGED 2026-07-20** (PR #487), dual-reviewed NO-BLOCKERS x2. Restored the `rc>=2` hard fail. **The gate-arming blocker is CLEARED.** |
| `bd-ib-rxxx` | livespec-orchestrator-beads-fabro | P1 | **NEW 2026-07-20 — DIAGNOSIS CORRECTED TWICE, read its notes before acting.** NOT checkout-dependent and NOT `supervisor_discipline` (which passes everywhere, rc=0); the reconcile's real failure was `check-coverage`. Candidate causes now: a dev-tooling version delta (janitor ran v0.50.7; v0.50.8 landed 18 min later) and/or concurrent master pushes. Original (superseded) claim was CHECKOUT-DEPENDENT: `supervisor_discipline` passes on master (rc=0, 8 warns, 0 errors) but hard-fails in a fresh janitor checkout via git-derived coverage (`newly_covered: true`), STRANDING items with no defect in the change. **Blocks re-dispatching `w4h4`.** Distinct from `wmqsn7` — not flakiness; re-running will not help |
| `bd-ib-w4h4` | livespec-orchestrator-beads-fabro | P1 | **MERGED (PR #836, master CI GREEN) but STRANDED `active`.** Reconcile attempted and FAILED on `check-coverage` — almost certainly because ANOTHER SESSION pushed `952d874` to master in the same minute and the valve's fresh checkout took that in-flight commit. **Retry the valve once master settles**; then the mandatory DUAL REVIEW is still outstanding (focus: live-lock direction + the three-claimant cascade) |
| `livespec-dev-tooling-y27` | livespec-dev-tooling | P2 | **NEW 2026-07-20.** Residual after 6j6: `rc=1` with a PARTIAL tally still poisons the ratchet. PRE-EXISTING (predates z45). rc 1 is genuinely ambiguous — the naive `mutants_total`-shrink fix has its own false-fail risk when code is legitimately deleted |
| `livespec-e9j` slice 1a | livespec | — | **PR #1497 OPEN** — declares `dataclasses_tree`, arming `newtype_domain_primitives` (one of the four never-enforcing checks). Verified armed + green; 71 targets pass |
| ~~`livespec-ftbvgc`~~ | livespec | — | **DONE 2026-07-20.** Switched to `ai-only` and accepted after a Fable+Codex acceptance review |
| ~~`bd-ib-12fw`~~ | livespec-orchestrator-beads-fabro | — | **DONE 2026-07-20** — merged (PR #822), then accepted `ai-only` after a Fable+Codex acceptance review. Dual review SPLIT (Codex BLOCKERS / Opus NO-BLOCKERS) on severity of a TOCTOU race both found; **maintainer ruled merge + follow-up**. Reconciled to un-strand |
| `bd-ib-w4h4` | livespec-orchestrator-beads-fabro | P1 | **NEW 2026-07-20.** Janitor stale-lock reclamation is TOCTOU: unlink-by-pathname can delete a LIVE lock, so two janitors both own the venue. Demonstrated by BOTH reviewers. Fix: atomic takeover (temp+`os.link`/`rename`, or read-back-confirm-own-pid). Ride-along: a pre-existing assertion can no longer detect the defective contention message |
| `livespec-dev-tooling-qm5` | livespec-dev-tooling | P1 | **UNBLOCKED** (`backlog`), still `needs-regroom` — premise falsified, scope needs re-cutting |
| `livespec-dev-tooling-cvz` | livespec-dev-tooling | P1 | **NEW.** `source_trees` undeclared → check scans ZERO files in core + both Drivers |
| `livespec-dev-tooling-e9j` | livespec-dev-tooling | **P0** | Role-key non-declaration silently disarms 7 checks fleet-wide; core runs 5+ structural gates vacuous-but-green. Raised to P0 2026-07-20. Superset of `cvz` |
| `livespec-dev-tooling-6vz` | livespec-dev-tooling | P1 | `no_raise_outside_io` hardcodes core's four error names → vacuous everywhere else. **Blast radius is beads-fabro (47 sites), NOT git-jsonl (2) as its brief says.** Hinges on the same unresolved flat-package rule as qm5 |
| ~~`livespec-dev-tooling-z45`~~ | livespec-dev-tooling | — | **DONE** — see row above. `check_mutation` now FAILS when armed-but-inspected-nothing; verified by real mutmut runs (zero-mutant -> exit 1 with baseline preserved; `LIVESPEC_RUN_MUTATION` unset still skips cleanly; crash distinguished from survivors) |
| `livespec-mutreal.1` | **livespec tenant** | — | Staging-tree construction. Recipe now KNOWN + reproduced twice at ~85%; remaining work is productization (committed vs generated). Gates only `pure_trees`, not the rest of e9j |
| `livespec-dev-tooling-jjb` | livespec-dev-tooling | P2 | Mechanize cardinality + marker wording (the ratified spec says these are review-enforced today) |
| `livespec-dev-tooling-bbl` | livespec-dev-tooling | P2 | Canonical no-shadow-ledger body: type-checkable + **the non-conforming ROP marker (rule-independent, landable NOW, fixes 2 of ~7 remaining broad sites)** |

## NOT "TWO VACUOUS GATES" — SEVEN CHECKS ACROSS FIVE ROLE KEYS

This section has now been revised upward twice (2 → 3 → 7). Treat any count here as a floor
until `livespec-dev-tooling-e9j` is worked. All of these report GREEN while inspecting nothing.

**The three originally catalogued, each verified directly:**

1. `check-no-except-outside-io` returns 0 immediately when `io_trees` is unset (`qm5`).
2. `check-no-raise-outside-io` hardcodes `_DOMAIN_ERROR_NAMES` to core's four names; a repo whose
   errors are named differently gets zero coverage. Instrumented against git-jsonl it flagged 0
   of 9 raises including a genuine outside-`io/` one (`6vz`).
3. `check-no-except-outside-io` walks `config.source_trees`, UNDECLARED in livespec core AND both
   Driver repos, so the loop runs zero iterations (`cvz`). `livespec-driver-codex`'s
   `pyproject.toml` even documents that it deliberately omits the "heavy product-tree role keys".

**The systemic finding underneath them (`livespec-dev-tooling-e9j`).** SEVEN checks share one
early return — `if not config.<role_key>: log.info("role key absent — check no-ops"); return 0`.
It is not a bug but a documented convention (`load_config`'s own docstring). Measured across the
7 repos declaring a `[tool.livespec_dev_tooling]` block:

| Role key | UNSET in | Checks it silences |
|---|---|---|
| `pure_trees` | **7/7** | `check_mutation`, `pbt_coverage_pure_modules`, `public_api_result_typed` |
| `dataclasses_tree` | **7/7** | `newtype_domain_primitives` |
| `io_trees` | 5/7 | `no_except_outside_io`, `no_raise_outside_io` |
| `neutral_hook_body_path` | 5/7 | `no_shadow_ledger_body_identical` |
| `source_trees` | 4/7 | (empties the walk loop even when `io_trees` IS set) |

**Four checks have never enforced anything in any repo in the fleet.** Proven by execution in
core's own checkout — `public_api_result_typed`, `newtype_domain_primitives`,
`pbt_coverage_pure_modules`, `no_except_outside_io`, `no_raise_outside_io` all print
`check no-ops` — while core CI reports every one SUCCESS (verified on PR #1426's rollup).

**Root cause — pinned to a commit and a date. The fallback was correct for under 24 hours:**

| When | What |
|---|---|
| **2026-05-30 15:53** | livespec-dev-tooling `391662a` introduces `_livespec_core_config()`, the fallback that supplies core's real `io_trees`/`pure_trees`/`dataclasses_tree`. It applies ONLY when the `[tool.livespec_dev_tooling]` block is ABSENT — its docstring says it exists so "livespec-core (which omits the block) stays bit-identical". |
| **2026-05-31 14:10** | livespec core `8f6ecc59` ADDS that block — solely to declare `scenario_tiers` for an unrelated new heading-coverage check in dev-tooling v0.9.0. It declares no structural role key, and needed none for its purpose. |

That one edit moved core from the fallback regime to the empty flat baseline. **Core's
structural gate suite has been inert since 2026-05-31 — roughly seven weeks — with CI reporting
every one of those checks green throughout.**

Four properties hid it: the disarming edit lived in a DIFFERENT repo and reads as a dependency
bump; the regime switch is implicit in `table is None`, so ANY key flips it; the only signal is
an INFO line in a suite where passing checks also print nothing and exit 0 — a no-op and a pass
are visually identical in CI; and `_livespec_core_config`'s docstring still asserts core "omits
the block", so the function is now dead code with respect to its stated purpose while still
firing for `livespec-console-beads-fabro`, which has no block and is a Rust crate. **The
core-shaped fallback misses core and lands on a repo it cannot describe.**

This reframes the fix: the failure was NOT a repo forgetting to declare keys. Core never needed
to — it was correctly served by the fallback until an unrelated edit silently withdrew it. So
the load-bearing remedy is making the regime EXPLICIT (a repo declares which layout it intends)
and making a zero-file inspection LOUD (report the inspected-file count per check, so "inspected
0" cannot masquerade as "passed").

**Why this bears directly on this thread:** v169's mechanical half is carried by exactly these
checks. In core and both Drivers they inspect nothing. A ratified ROP policy is being enforced
by gates that are structurally inert in the repos that define and ship it.

### THE RELEASE GATE IS AFFECTED TOO — and it weakens the fleet's pinning warrant

`check_mutation` has **two independent skip paths in series**: an env lever
(`LIVESPEC_RUN_MUTATION`, legitimately armed at `.github/workflows/release-tag.yml:47`) and
then the role-key early return. Run exactly as the release workflow invokes it, against
master's real config:

```
LIVESPEC_RUN_MUTATION=true python -m livespec_dev_tooling.checks.check_mutation
  -> {"role": "pure_trees", "event": "role key absent — check no-ops"}   exit 0
```

**Core's release gate has been running mutation testing that does nothing since 2026-05-31** —
same date, same commit `8f6ecc59`, as everything else here.

That matters beyond one more inert check, because core's CLAUDE.md justifies the fleet's whole
pinning strategy on it: *"Dogfooding pins track the latest RELEASE, not raw master … because a
release carries release-gate validation (release-tag.yml's **mutation testing**, full heading
coverage, no LLOC soft-warnings) … a release is the more-validated artifact."* Mutation testing
is named FIRST among the three, and for core that leg has been inert. Every sibling pinning
core's latest release tag has inherited an assurance that, on this axis, was not performed. The
policy is not wrong; its stated warrant is currently overstated.

**Scope is bounded — the other two release legs are FINE.** Of the three strict-mode levers
release-tag.yml arms job-wide, only `check_mutation` is role-key gated; `heading_coverage` and
`no_lloc_soft_warnings` do not carry the `role key absent` early return and are unaffected. One
of three legs degraded, not a broken gate.

**Design lesson for the fix:** two skip paths in series log almost identically at INFO, so a CI
log reader cannot distinguish *(a)* deliberately skipped for speed on a per-commit run — correct
— from *(b)* armed for release but silently disarmed by config — the defect. A legitimate skip
mechanism is CAMOUFLAGING an illegitimate one. **When a run-lever is explicitly ARMED and the
check then no-ops on missing config, that must be an ERROR, not an INFO** — someone deliberately
asked for it to run.

**MEASURED 2026-07-20 — and the answer was "it cannot be measured by configuration at all":**
with both gates open the check enumerates 208 mutants and kills 0, because core has no directory
that can serve as import root + test root + fixture ancestor at once. See "MUTATION IS NOT
CONFIGURABLE" near the top. Runtime turned out trivial (seconds), so my earlier "too slow to run"
was wrong twice over.

Defect #2 distorted a real design decision: restoring protocol conformance vs. tracking the
divergence was argued partly on whether unwrapping would trip that check. It wouldn't have.

Defect #3 falsifies `qm5`'s rationale. The two holes are in SERIES: with `source_trees` empty the
walk runs zero iterations no matter what `io_trees` says, so fixing `qm5` alone yields ZERO new
Driver coverage.

## THE FOUR GATE ITEMS ARE ONE MACHINE — do not land them independently

`qm5`, `cvz`, `6vz`, and `e9j` all touch the same config-plus-walk machinery. Two facts to hold:

- **The defects are shared-shape across BOTH ROP checks.** `no_raise_outside_io` carries the
  io_trees early return (`qm5`'s defect, byte-identical in shape, lines 91-97) AND the
  source_trees walk (`cvz`'s defect, line 99) AND its own hardcoded names (`6vz`). It is vacuous
  through THREE serial mechanisms; fixing any one leaves it vacuous. `qm5` and `cvz` were both
  filed naming `no_except_outside_io` alone. Fix both checks in one pass.
- **Blast radius is dominated by a repo none of the briefs name.** Measured, counting raises of
  each repo's own error classes outside its DECLARED io trees:
  `livespec-orchestrator-beads-fabro` **47 sites**; `livespec-dev-tooling` 14;
  `livespec-orchestrator-git-jsonl` **2** — the only repo `6vz`'s brief anticipates. beads-fabro
  declares both `source_trees` and `io_trees`, so the qm5/cvz vacuities do NOT shield it — only
  `6vz`'s does. **Fixing `6vz` alone immediately reddens beads-fabro with 47 findings.** The
  warn-tier severity lever its brief already sanctions is likely required, not optional.

## THE FLAT-PACKAGE RULE — RULED 2026-07-20: BROAD-ONLY (kept for the reasoning and the numbers)

**v169 ratified "narrow at the seam; broad only at the boundary." But
`no_except_outside_io` bans ALL `try/except` outside `io/`, narrow included.** That is coherent
for a LAYERED package — the narrow seam catches live in `io/`. For a FLAT package there is no
`io/`, so the strict reading bans the very form v169 sanctions.

Measured: `livespec-dev-tooling` is the ONLY repo the `qm5` fix affects — 36 offenses, of which
**4 are broad** (`except Exception`) and **32 are narrow** typed catches. An independent
classification judged ~30 legitimate (3 sanctioned boundaries missing only a
`supervisor_entry_files` declaration; ~20 foreign-code isolation parsing `gh` CLI JSON and other
repos' manifests; 7 borderline) and ~6 genuine violations — notably `green_token.py:92,122`,
broad catches in ordinary helpers guarding a local advisory cache.

`check-no-except-outside-io` is already live in dev-tooling's own justfile (221/630), so landing
`qm5` as written turns THIS repo's `just check` red — the Green commit cannot even be made.

### The cost of each rule, measured fleet-wide

Except handlers OUTSIDE each repo's DECLARED io trees. Both columns are UPPER BOUNDS — they do
not subtract `supervisor_entry_files` / `commands_trees` `main()` exemptions, which shrink the
BROAD column most.

| repo / tree | BROAD | NARROW | total |
|---|---|---|---|
| livespec (core, main tree) | 0 | 3 | 3 |
| livespec (`.claude/skills/`) | 1 | 35 | 36 |
| livespec-dev-tooling | 4 | 34 | 38 |
| **livespec-driver-claude** | **4** | 5 | 9 |
| **livespec-driver-codex** | **4** | 10 | 14 |
| livespec-orchestrator-git-jsonl | 0 | 3 | 3 |
| livespec-orchestrator-beads-fabro | 0 | 6 | 6 |
| **FLEET TOTAL** | **13** | **96** | **109** |

**Broad-only costs 13 sites. Strict costs 109.** Roughly an 8x difference in remediation scope.

> **REVISED DOWNWARD — the real broad-only figure is ~7, not 13.** Direct source inspection of
> all 8 Driver broad catches (not simulation — every one read with its marker) found **6 already
> carry EXACT sanctioned v169 wording**, `sole` cardinality intact since each sits in a different
> hook file. The 2 non-conforming ones are **the same file in both repos** —
> `no_shadow_ledger.py:195`, byte-identical, marked `— fail-open by contract`, which is not in
> the closed set. Neither Driver owns it: it installs from
> `livespec_dev_tooling/install_no_shadow_ledger.py:255` under a byte-identical guard. So the
> genuinely outstanding broad work is **2** (one canonical string) **+ 4** (dev-tooling: 2
> declarable hook boundaries, 2 real violations in `green_token.py`) **+ 1** (overseer
> `supervisor.py`) ≈ **7 sites fleet-wide**.
>
> **This falsifies `qm5`'s Driver-drift premise — the third false premise found in this thread.**
> That brief says the Drivers drifted into blanket lifts marked `# noqa: BLE001 - ... captured on
> IO rail`. **No catch in either Driver hook tree carries that wording.** The drift was
> evidently remediated by the merged PRs #215 / #219 / #199 this handoff's own DONE table
> records. Do not plan Driver remediation; it is done.
>
> **Caveat:** wording conformance is necessary, NOT sufficient. This pass verified the six
> markers match the sanctioned strings; it did NOT re-verify that each claimed boundary is
> genuinely its process's sole boundary, nor that fail-open vs fail-closed is right at each site.
> The tmux guard is precedent — its comment claimed fail-closed while the body failed open.
> `livespec-dev-tooling-jjb` remains the right home for mechanizing that.

### The one piece of this sweep that can land NOW

Fixing that canonical marker string is **rule-independent** — it is a BROAD catch, restricted
under both candidate rules — so unlike `qm5`/`cvz`/`6vz`/`e9j` it does not wait on the ruling.
Routed onto **`livespec-dev-tooling-bbl`** (same canonical body, already targeted there for
pyright reasons) rather than filed as a near-duplicate; do both edits in ONE pass or the
byte-identical guard forces a second regeneration across both Drivers for nothing.

The replacement wording was verified TRUTHFUL against the actual body, not assumed: the catch
sits in `main()` (the process entry point), sets `warning = None`, writes nothing, and returns 0
unconditionally — so `sole fail-open hook boundary: silent pass-through, exit 0` describes it
exactly, clause by clause.

The BROAD column is precisely the target of this sweep: **both Drivers carry exactly 4 broad
catches each — 8 of the 13 fleet-wide** — and those are the hand-rolled blanket lifts the ROP
ruling was written to close. Broad-only catches every one while leaving the Drivers' 15 combined
narrow seam catches alone. dev-tooling's 4 are 2 declarable fail-open hook boundaries plus 2
genuine violations in `green_token.py`; the overseer's 1 is `supervisor.py`.

Method and its limits, stated plainly: these are AST measurements. The same simulator was
VALIDATED against real execution on core — it predicted core's 3 offenses with exact file and
line agreement before the checks were run for real (see `e9j`) — but the other rows are
simulation-only. `_vendor/` excluded throughout.

**The two Driver repos do NOT share a hook tree path** — `livespec-driver-claude` uses
`.claude-plugin/hooks/`, `livespec-driver-codex` uses `livespec/hooks/`. Assuming a common path
initially produced a false ZERO for driver-codex in this very table. Any change declaring
`source_trees` per repo must read each repo's real layout; a wrong path yields a silent zero,
not an error.

**Agent recommendation (NOT yet ruled on):** flag BROAD catches only in the flat branch. It still
catches the Driver drift `qm5` targets (blanket `except Exception` marked `# noqa: BLE001`, and
BLE001 IS the blind-except rule) without banning the sanctioned narrow form, and reddens
dev-tooling on 4 tractable sites. No skip flag, no per-repo exemption.
**Counter-argument, stated fairly:** `contracts.md:213` says "no `try/except` is wholesale
exempt" and the maintainer ruled that row correct as written. The recommendation reads
"wholesale" as TREE-level, not "every individual catch is an offense". If the stricter reading is
intended, broad-only is off the table and ~32 narrow catches need remediation or declaration.

## COORDINATION WITH `plan/overseer-productization/` — settled 2026-07-19

That thread asked how `.claude/skills/` interacts with `cvz` declaring core's `source_trees`.
**Maintainer ruling relayed by that session: `.claude/skills/` is NOT excluded from the ROP bar —
"it should follow discipline."** Deferring WHEN it enters `source_trees` is sequencing, not
exemption, and is consistent with that ruling.

**Agreed split and ordering:**

1. **`cvz` (this thread)** declares core's `source_trees`/`io_trees` **without** `.claude/skills/`.
2. **Gate E (overseer-productization thread)** brings the overseer folder to conformance.
3. **Either thread, only after (2)** adds `.claude/skills/` to `source_trees` — enforcement
   arrives after adoption, per `.ai/ci-gate-discipline.md`.

**Two measurements that change the size of this work — do not plan against the estimates:**

- **Step 1 is nearly free.** Simulating `no_except_outside_io` over core's main tree with the
  fallback's role keys restored yields **3 offenses, ALL NARROW** — `SyntaxError` /
  `IndentationError` / `tokenize.TokenError` in `doctor/static/no_spec_section_citation_in_code.py`
  (parsing arbitrary Python) and `ModuleNotFoundError` in
  `doctor/static/wiring_completeness_cross_repo.py` (optional-import probe). Under the recommended
  broad-only rule that is **0 offenses — core's main tree is already clean**. Under the strict
  rule it is 3, all textbook foreign-code isolation. So `cvz` step 1 can land immediately and does
  NOT need to wait on Gate E.
- **Gate E's size depends ENTIRELY on the unresolved flat rule.** The overseer folder carries
  **36 except handlers of which exactly ONE is broad** (`supervisor.py`); the other 35 are narrow
  typed catches, spread across `registry.py` (11), `claude_sessions.py` (6), `codex_sessions.py`
  (6), `supervisor.py` (6), `tmuxio.py` (3), `jsonio.py` (2), `signals.py` (1).
  - Under **broad-only**: Gate E is **1 site** — declare `supervisor.py`'s sole `except Exception`
    as a boundary. No `io/` layer, no refactor.
  - Under **strict**: 35 sites need an `io/` split or equivalent.

  **So Gate E should NOT begin its refactor until the flat rule is ruled on**, or it risks doing
  35 sites of work that the ruling makes unnecessary.

**Answer to that thread's design question — declaring the whole folder an `io` tree is NOT
acceptable.** `io_trees` entries are **wholesale exempt**, so declaring `.claude/skills/overseer/`
an io tree would make all 36 handlers instantly legal and the check vacuous over that tree. That
is a bypass wearing a declaration's clothes — the same "fabricate a boundary that does not exist"
move already rejected for `livespec-dev-tooling` in `qm5`'s ledger note, and forbidden by
`.ai/ci-gate-discipline.md`'s "fix the gate, not the bypass". Whether the folder should instead
grow a REAL `io/` layer is premature: under broad-only it needs none.

## WHAT THE REVIEW GATE CAUGHT (do not weaken it)

Every finding below passed all mechanical gates:
- **The tmux guard failed OPEN** while its comment claimed fail-closed — on the guard that exists
  to stop the agent-caused fleet kill that happened the same day.
- **The reconcile valve could clobber a live dispatch**, causing the very stranding it prevents.
- **Its replacement guard was INERT** — gated on a heartbeat that is silent in exactly the
  contested window, so it waved every caller through while looking like protection.
- **Then the fix for THAT relocated the same bug** from worktree-deletion to journal-deletion.
- **A proposed spec edit re-asserted a FALSE enforcement claim** while claiming to make spec and
  code agree.
- **Two tests were inert** — one guarded behind `hasattr` on a symbol its own PR deleted, so it
  passed against a reintroduced fail-open.
- **Two of six spec review rounds found blockers introduced by the previous round's fix.**
- **A P1 work-item's own rationale was false** — `qm5` was written on the belief that one config
  hole blocked Driver coverage; there were two in series, so the fix would have delivered nothing
  where it was aimed while reddening the repo shipping it.

## MECHANICS (hard-won — do not rediscover)

- **These repos REBASE-merge.** A "merge SHA" is a span tip, not a two-parent merge commit;
  `git show <tip>` reviews only the last commit — in one case an entirely unrelated commit.
  Resolve `base..head` via `gh pr view <n> --json commits,baseRefOid,headRefOid,additions,deletions,changedFiles`
  and cross-check totals. **Brief every reviewer with this.**
- **Verify plugin rollout by CONTENT, not version string.** Hash the installed cache's file
  against `git show origin/master:<path>`. Version strings and "already at latest" both lie about
  whether the fixed bytes are on disk.
- **A `--force-with-lease` "stale info" rejection is ambiguous** between your own merged-and-deleted
  branch and a peer's push. STOP and investigate; never force blind.
- **PRs here merge fast.** Land corrections as FRESH branches off current master, not amendments.
- **Require reviewers to verify by EXECUTION**, not reading — revert the impl, watch the test
  fail, report the output. That framing caught the inert guard, the inert tests, and the journal
  deletion; a structural read passed all three.
- **A test-only brief must NOT demand Red-Green-Replay** — no impl to add at Green. Use the
  established `TDD-Suite-Green-*` shape.
- **`status` is a read-only variable in zsh** and will silently kill a `Monitor` script.
- **Do NOT read a local agent's `.output` file** — it is a symlink to the full subagent transcript
  and will overflow context. Use the agent result or `SendMessage`.
- **NEVER NAME THE EXPECTED ARTIFACT IN A REVIEW BRIEF — it converts an independent check into a
  confirmation.** The `ftbvgc` acceptance brief asked Fable to "verify PR #1381 exists and is
  MERGED", pre-supplying the answer. Fable duly verified #1381 and NEVER checked the item's OWN
  claim of #1321 — which was the actual defect. Codex caught it only because it read the item
  description first, unprimed. Ask **"which PR delivered this, per the item, and is that
  correct?"** — never "verify PR #N".
- **Distinguish a FALSE claim from a STALE one before recording a verdict.** On `ftbvgc` the
  overseer confirmed a journaled `extend-exclude` claim as "CONFIRMED FALSE" against live state
  and was WRONG: Fable read the commits IN TIME ORDER and showed the claim was TRUE at the
  delivering commit (`0bd9ce1f`, 03:48Z) and was invalidated hours later by an unrelated Gate C
  commit (`98fcc1d3`, 06:51Z) that removed the exclusion and added the `noqa`. "The author
  asserted something untrue" and "the world changed under an accurate statement" are different
  defects with different remedies. **Check the delivering commit's state, not just HEAD.**
- **Fable+Codex is a GOOD acceptance pairing — each caught what the other structurally could
  not.** Codex caught the false PR number (unprimed reading); Fable caught the staleness
  (temporal commit analysis). Combined with the `z45` factual split and the `12fw` severity
  split, that is a THIRD distinct shape of productive reviewer disagreement in this thread.
- **A reviewer that goes "idle" may have DELIVERED NOTHING despite doing the whole review.** Its
  plain-text output is not visible to the overseer. **State the delivery mechanism (`SendMessage`)
  as a hard requirement in every reviewer brief**, and when one goes idle, ASK it for the verdict
  before assuming it failed. This cost the prior session three rounds and held `sw0i` for a day.
- **"Do not merge" is NOT enough in a dispatch brief — forbid ENABLING AUTO-MERGE explicitly.**
  The z45 agent's PR was merged by `app/livespec-pr-bot` on green despite the brief saying to leave
  it open, bypassing the dual-review gate on a fleet-wide RELEASE gate — and the review that was
  then run retroactively found a real regression that the gate would have caught pre-merge.
- **ONE clean verdict is NOT sufficient, no matter how thorough it looks.** On z45 the two
  reviewers DISAGREED: Codex returned NO-BLOCKERS after genuinely detailed work (real mutmut runs
  across four scenarios); Opus found a deleted guard with before/after execution evidence. The
  disagreement WAS the finding. Always run both, and when they disagree, VERIFY THE DIFF YOURSELF —
  the overseer confirmed the deletion in `git diff` in one command.
- **NEVER conclude "no PR exists" from a truncated list.** `gh pr list --limit 2` showed two newer
  unrelated PRs and `w4h4`'s #836 sat one row below the cut, producing a WRONG "no PR, reconcile
  cannot help" diagnosis that was filed on a work-item. **Filter by head branch
  (`--head feat/<id>`) or search the id — never eyeball the top N.**
- **`reconcile-merged` runs `just check` against CURRENT master, so a CONCURRENT PUSH by another
  session can fail the valve** for reasons unrelated to the item. Observed: the valve failed on
  `check-coverage` in the same minute another session pushed `952d874` whose own CI was still
  in_progress. Check whether another session is dispatching (look for foreign `janitor-*`
  worktrees) BEFORE blaming the item, and let master settle before retrying.
- **Read the FAILING RECIPE NAME, not the loudest line in the journal.** The dispatch journal's
  outcome detail quoted a `supervisor_discipline` / footgun message, which sent this thread chasing
  the wrong check twice. The actual failure was `error: Recipe \`check-coverage\` failed`.
- **A transient CI flake STRANDS a work-item `active`.** `bd-ib-12fw`'s dispatch died on
  `mise ERROR Failed to install aqua:koalaman/shellcheck@0.11.0: HTTP timed out` — a download
  timeout during tool setup, so the check never ran; `ci-green` failed with it, the PR went BLOCKED,
  and the dispatcher gave up with "PR did not reach MERGED within the poll budget". Re-running the
  failed jobs turned it fully green (63 pass / 0 fail), confirming pure flake. **Re-running a
  root-caused infra timeout is NOT a test skip.** Recovery is `reconcile-merged`. This is a live
  argument for `bd-ib-wmqsn7`.
- **Reviewer disagreements come in TWO shapes, and both justify the two-reviewer rule.** On `z45`
  they disagreed on FACTS (Codex missed a deleted guard) — the disagreement caught a defect. On
  `bd-ib-12fw` they agreed on facts entirely (both demonstrated the same TOCTOU race by execution)
  and disagreed only on SEVERITY — surfacing a genuine maintainer judgment call that a single
  reviewer would have silently decided either way. **When they split on severity, route it to the
  maintainer; do not self-waive in either direction.**
- **The factory enables auto-merge on its own PRs.** #822 merged by itself the moment CI went green,
  even though the dispatcher had already given up. Do not assume a failed dispatch means nothing
  landed — CHECK the PR state before planning recovery.
- **Ask a reviewer to diff against the PRE-change version, not just to read the post-change code.**
  The z45 regression was a REMOVAL. A reviewer inspecting only what is present cannot see what is
  missing; the finding came from running the same fixture against `e9dcf46` and `e9dcf46^`.
- **`tmux` is a zsh ALIAS here** (`_zsh_tmux_plugin_run`) and fails in non-interactive shells. Use
  `/usr/bin/tmux` directly, always with `-L <socket>`; never the default socket.
- **Probe a credential with a trivial `codex exec`, not a file read alone and not a dispatch.** An
  expired `id_token` does NOT mean dispatch is down — it is a 1-hour token and `auth.json` carries a
  `refresh_token`.
- **Spec edits go through `/livespec:propose-change`**, never a direct edit backfilled by doctor.
  PR #797 did the latter and doctor SELF-ACCEPTED the drift (`author_llm: livespec-doctor`),
  bypassing the never-self-waived independent-review rule. Put this line in every dispatch brief.
- All `bd` calls go through `/data/projects/1password-env-wrapper/with-livespec-env.sh`. The
  `auto-backup failed … command denied` warning is correct-by-design.

## CORRECTIONS TO EARLIER FINDINGS (do not re-derive the wrong conclusion)

- **`no_shadow_ledger.py` is NOT "a bypass in both Drivers".** Neither Driver owns it — the single
  source is `livespec_dev_tooling.install_no_shadow_ledger.CANONICAL_NO_SHADOW_LEDGER_BODY`,
  installed via `just install-no-shadow-ledger` and guarded byte-identical by
  `check-no-shadow-ledger-body-identical` (exit 4 on drift). Editing it in a Driver is FORBIDDEN.
  livespec-driver-claude's pyright carve-out is documented and principled
  (`pyproject.toml:280-292`); only livespec-driver-codex's is undocumented. The body also carries
  bare `dict`/`list` annotations failing strict pyright, so a one-line fix is insufficient. Real
  fix: `livespec-dev-tooling-bbl`.
- **The heartbeat probe is the WRONG fix for the reconcile race.** `post_merge` runs AFTER the
  Fabro run completes and the heartbeat is fed DURING it, so the probe is silent in exactly the
  contested window and returns a false "dead" verdict.
- **`BLE001` markers in both Drivers' hook trees are DECORATIVE** — those trees are
  `extend-exclude`d from ruff, so `BLE001` never fires. `livespec-dev-tooling-jjb` must add a
  POSITIVE AST guard, not merely remove a carve-out.
- **Do not probe a credential by dispatching.** Read `~/.codex/auth.json` — see START HERE.

## Close-out

When all children + slices are `done`, epic `livespec-y2lkf4` closes and this thread archives to
`plan/archive/rop-sweep-fleet-policy/`.
