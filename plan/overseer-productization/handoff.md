# Plan — overseer-productization

**Owning session:** livespec core, "overseer-productization". **Status:** OPEN,
EXECUTING Phase 1.
**Decision (maintainer 2026-07-18):** *Gate now, ship as Phase 2.* Bring the overseer
fully inside the product gates as a first-class LOCAL module (Phase 1), then design
host-decoupling + adopter shipping (Phase 2). Phase 1's value is independent of Phase 2.

## Progress

| Gate | State | Where |
|---|---|---|
| A — tests in `just check`/CI | **DONE, live-exercised** | livespec PR [#1387](https://github.com/thewoolleyman/livespec/pull/1387), merged 2026-07-19 |
| C — ruff lint + format | **DONE, live-exercised** | livespec PR [#1396](https://github.com/thewoolleyman/livespec/pull/1396), merged 2026-07-19 |
| D — pyright strict | **DONE, live-exercised** | livespec PR [#1408](https://github.com/thewoolleyman/livespec/pull/1408), merged 2026-07-19 |
| B — coverage | **CODE DONE + VERIFIED, COMMITTED, UNPUSHED — BLOCKED** | worktree `~/.worktrees/livespec/gate-b-overseer-coverage`, branch `gate-b-overseer-coverage`, commit `39047284` |
| E — ROP railway | BLOCKED on D2 scope question — see below | — |

# ⛔ START HERE — Gate B is finished but could not be pushed

> **This handoff was rescued from the primary checkout on 2026-07-19** (commit below).
> It had been left UNCOMMITTED on disk at `/data/projects/livespec` — 153 unversioned
> lines, one `git checkout` from oblivion — because the session that wrote it believed
> the push blocker "prevents committing anything". **That belief was wrong** (see
> "Corrections" below): only `push` is blocked. Doc-only commits were always available.
> **Keep this file committed from now on; update it in-session as findings land, not
> at session end.**

Read this whole section before doing anything else. Gate B's code is COMPLETE and
FULLY VERIFIED. It is committed on a branch in a worktree and was never pushed, because
a master-red gate blocks `git push` (pre-push runs `just check`). Nothing about Gate B
itself is wrong.

## Step 1 — is the blocker gone?

```bash
cd /data/projects/livespec && just check-doctor-static >/dev/null 2>&1; echo "exit=$?"
```

- **exit 0** → the blocker cleared. Go to Step 2.
- **exit 3** → still blocked. Go to "The blocker" below.

**As of 2026-07-19 ~12:15 the fix is IN FLIGHT — do not start your own.** A concurrent
session (`session_014mhgdKfN9ucqxtJXjfeshe`) independently reached the identical
diagnosis and pushed branch `revert-cross-repo-targets-console` (commit `6bdccd04`,
worktree `~/.worktrees/livespec/revert-cross-repo-targets-console`), reverting ONLY the
`.livespec.jsonc` `cross_repo_targets` hunk of `7107be6c` and deliberately keeping its
`.ai/` docs change. **No PR was open yet at the time of writing** — check
`gh pr list --repo thewoolleyman/livespec` before acting. That branch could be pushed
at all precisely because the revert repairs the very gate that blocks pushing.

Do NOT duplicate it, and do NOT touch that branch or worktree — it is another session's
(the cross-session force-push/clobber ban in `AGENTS.md` applies). Gate B lands the
moment it merges.

## Step 2 — land Gate B (only once Step 1 is exit 0)

```bash
cd ~/.worktrees/livespec/gate-b-overseer-coverage
mise exec -- git fetch origin master -q
mise exec -- git rebase origin/master          # master moves fast; expect this to be needed
just check-overseer                            # MUST report 100.00% and ~438 passed
mise exec -- git push -u origin gate-b-overseer-coverage
```

Then open the PR. The commit message on `39047284` is complete and accurate — reuse it
as the PR body. After merge: confirm the post-merge master CI run's `check-overseer`
job passed against combined master (that is Gate B's live-exercise evidence, required
before calling it done), then `git -C /data/projects/livespec pull --ff-only origin
master`, remove the worktree, delete the branch.

**Do NOT `--no-verify`.** The blocker is a real red gate; bypassing it is explicitly
forbidden by `.ai/ci-gate-discipline.md`.

**Do NOT `git checkout <file>` in that worktree** to undo anything — it reverts to HEAD,
not to your working state, and has already destroyed in-progress work twice on this
thread. Copy to the scratch dir and restore from there.

## The blocker — another session's commit, fully diagnosed (do not re-investigate)

`check-doctor-static` fails on livespec master with 53
`(sibling, missing-canonical-slug)` drift pairs, all
`livespec-console-beads-fabro→check-*`. This is NOT caused by Gate B — it reproduces on
an untouched `/data/projects/livespec` and does not reproduce at the commit before the
cause.

**Cause:** commit `7107be6c` ("docs(ai): scope No-Circular-Dependency to code, never
work-items"), authored by the `fleet-pin-propagation` session
(`Claude-Session: session_01XybfmAK5sG5RugLNWcwUxm`, live in the tmux session of the
same name; landed under `thewoolleyman` authorship via `livespec-pr-bot`). It added
`livespec-dev-tooling` and `livespec-console-beads-fabro` to `.livespec.jsonc`'s
`cross_repo_targets` so cross-tenant `sibling_work_item` refs resolve for the
fleet-pin-propagation epic (`livespec-n4ptl2`). That reasoning is sound.

**The accident:** `cross_repo_targets` is DUAL-PURPOSE. It is also the input to
`doctor-wiring-completeness-cross-repo`, which requires every listed sibling to wire all
53 canonical **Python** check slugs. `livespec-console-beads-fabro` is a **Rust** repo
whose `check:` aggregate correctly wires only Rust targets (`check-format`,
`check-clippy`, `check-test`, …). Registering it for a PLANNING purpose silently
enrolled it in a CODE-CONFORMANCE check it cannot satisfy.

**Why CI is green while every local push is blocked:** the check resolves each sibling
from `cross_repo_targets[<slug>].local_clone` (e.g. `/data/projects/<sibling>`), and CI
sets an env override pointing at a freshly-cloned siblings-root. So the check effectively
only ever fires locally. `filter_sibling_targets`
(`.claude-plugin/scripts/livespec/doctor/static/_wiring_completeness_cross_repo_helpers.py`)
drops only non-dict entries and the host repo — there is **no** language/class-based
exemption, even though the fleet manifest already carries `class: console` for that repo.

**Dead end already ruled out:** the `livespec-dev-tooling` v0.49.4 pin bump (`4a4b39cb`)
is NOT the cause. The timing makes it look guilty; bisecting cleared it. Re-confirmed
2026-07-19: master has since bumped to **v0.50.0** (`4dd7c836`) and the failure is
byte-identical — same 53 pairs, same repo. The pin is not implicated at any version.
(The Gate B worktree still sits at 0.49.3 and will need `uv sync` after rebasing.)

**Status of the fix — RESOLVED BY ANOTHER SESSION, remedy (a).** The four remedies once
put to the maintainer were: (a) revert only the `.livespec.jsonc` hunk of `7107be6c`,
keeping its `.ai/` docs change — the revert-and-reland remedy `.ai/ci-gate-discipline.md`
prescribes; (b) teach the check to exempt a sibling with no first-party Python;
(c) split `cross_repo_targets` into a planning list and a conformance list — the real
design fix; (d) hold. **(a) was chosen and executed** by
`session_014mhgdKfN9ucqxtJXjfeshe` on branch `revert-cross-repo-targets-console` — see
the START HERE box. This thread never owned that decision and did not drive it.

Note (a) is a *restoration*, not the design fix: it un-breaks the gate but drops the
cross-tenant `sibling_work_item` linkage that `7107be6c` existed to create — the
fleet-pin-propagation epic (`livespec-n4ptl2`) has a real filed child in that tenant,
`livespec-console-beads-fabro-tafkuw`. The revert commit says the re-land is tracked.
(c) remains the durable fix and is unowned.

### Corrections to this document's own earlier claims (verified 2026-07-19)

Two statements written above/below were checked against the live tree and are FALSE.
Both cost real time; do not re-inherit them.

1. **"the check ships from livespec-dev-tooling" — WRONG.** `filter_sibling_targets`
   lives in **livespec core**, at
   `.claude-plugin/scripts/livespec/doctor/static/_wiring_completeness_cross_repo_helpers.py:314`.
   Remedy (b) is therefore a SINGLE-REPO change in this repo, not the cross-repo lift
   the earlier text implied — materially cheaper than it was priced at.
2. **"the push blocker prevents committing anything" — WRONG.** `just
   check-pre-commit-doc-only` runs exactly seven targets
   (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`,
   `check-no-direct-tool-invocation`, `check-codex-no-repo-local-adapters`,
   `check-copier-template-smoke`, `check-tools`) and `check-doctor-static` is NOT among
   them. Only `push` runs full `just check`. **A doc-only commit was available the whole
   time** — which is why this handoff sat unversioned for no good reason.

Supporting facts measured this session, none previously recorded:

- `livespec-console-beads-fabro` carries **zero** first-party `.py` files and 28 `.rs`
  files. It cannot satisfy 53 Python check slugs even in principle.
- `.livespec-fleet-manifest.jsonc` already tags it `class: console` — the discriminator
  a remedy-(b) exemption would key on already exists.
- Removing ONLY the console entry takes `check-doctor-static` from exit 3 to **exit 0**;
  `livespec-dev-tooling` contributes zero drift pairs. (Verified by experiment, then
  reverted — the config was restored to HEAD.)
- The `fleet-pin-propagation` tmux session named below **no longer exists**; there is no
  tmux server running at all. Any instruction here to "check that session" is dead.

## What Gate B contains (already committed as `39047284`)

100.00% coverage — statements AND branches — on every module; 344 → 438 tests; full
`just check` green (all 71 targets); no behavior change. Sabotage-verified three ways.

- **Boundary extraction** (the D1 option the maintainer chose over a scoped threshold).
  The premise that host-glue is untestable proved mostly false. `overseer-start` was the
  real case: its `main()` constructed its own `TmuxIO`, so the whole bootstrap
  orchestration could only run against a live tmux window and therefore never ran. It now
  takes `io` / `build_supervisor` / `core_root` seams defaulting to the real
  implementations. `core_root` specifically keeps the daemon's marker-dir `mkdir` out of
  the real checkout when a test drives the split path. 49% → 100%.
- **`tmuxio.WindowLayoutDriver`** — a second Protocol for the six window-LAYOUT methods,
  the counterpart to Gate D's `PaneDriver` and the reason that one declares only twelve
  of `TmuxIO`'s methods.
- **Two `# pragma` annotations, the FIRST in first-party code** (all 33 pre-existing ones
  are vendored), each with its reasoning inline: `_clear_idle_nudge_state`'s
  `except OSError` (`no cover` — only reachable via a permission-denied parent, and CI
  runs as root where chmod denies nothing, so a test would pass locally and silently stop
  exercising it in CI); and `elif claude_status == "busy"` (`no branch` — provably always
  True there, but KEPT as an `elif` rather than demoted to `else` because the proof
  depends on the current contents of `_CLAUDE_BUSY_STATUSES`, which exists to be extended).
- **Beside-tests omitted from measurement**, mirroring `[tool.pyright].exclude`: coverage
  measures the code under test, not the test code.
- **Also closes a hole in Gates C AND D.** `ruff check .` and pyright's `include` both
  resolve files by EXTENSION, so `overseer-start` and `overseerd` — Python with a shebang,
  invoked by bare name — were never linted or type-checked at all. Explicitly they carried
  17 ruff findings (including 7 `print` calls Gate C claimed to have eliminated) and 5
  pyright errors. `[tool.ruff].extend-include` now matches the folder's `overseer*` naming
  convention; pyright names the two files individually; the launcher's output goes through
  the `streams` sink.

## Verified daemon findings — NOT fixed, no work-items filed yet

All three were independently verified in source, not taken on trust. None is a live
defect; each is recorded so it is not lost.

1. **`recover_missing_sessions` derives session names with an EMPTY collision set.**
   `_colliding` is only populated inside `build_rows` (supervisor.py), but `run()` calls
   recovery BEFORE the first `tick()`. A mapping row with no stored `tmux` would derive
   the bare topic instead of `<slug>-<topic>`.
2. **Codex reboot-recovery dispatch keys on topic alone.** `recover_missing_sessions`
   calls `codex_sessions.latest_session_for_thread_name(track.topic, …)` with no repo
   scoping, so two watched repos sharing a plan topic could resume the wrong rollout in
   the wrong repo.
   **SEVERITY CORRECTION for both:** the shipped daemon calls
   `supervisor.run(..., recover=False)` — deliberately and documented ("keeps the daemon a
   pure surface-only watcher"). So `recover_missing_sessions` is **unreachable in
   production today**. These are traps for whoever enables recovery, not active bugs. A
   sub-agent reported #2 as "reachable rather than exotic"; that framing is wrong.
3. **`rewrite_mapping` / `repoint_tmux` return a claim, not a fact.** Both return a count
   computed from the in-memory diff, but `_atomic_write` beneath them swallows `OSError`
   into a warning by design (the documented B7 fail-soft). So both can report "dropped N
   rows" when nothing persisted. Self-correcting (archive-GC re-drops next tick), but the
   return value is unreliable. Fixing means `_atomic_write` returning a success flag —
   a change to the fail-soft contract's shape, hence a decision, not a fix.

## Gate D — pyright strict (PR #1408, merged 2026-07-19)

**Live-exercise evidence.** Post-merge master CI run
[29679815083](https://github.com/thewoolleyman/livespec/actions/runs/29679815083):
`check-types`, `check-lint`, `check-format`, and `check-overseer` all passed against
combined master. Sabotage-verified — a function returning `int` from a `-> str`
signature turned `just check-types` red.

**Clean under strict mode with NO pragma and NO suppression anywhere.** 174 product-module
errors → 0, no behavior change (344 beside-tests pass; 304 pre-existing + 40 new).

**The scope decision, which was NOT in the plan and matters most.** The plan estimated
163 errors. The true first measurement was **3116** — because the beside-tests are
unannotated (`def test_x(tmp_path):`) and generate ~2942 `reportMissingParameterType` and
friends. The resolution is not a carve-out: **pyright checks SOURCE, not tests,
repo-wide** — the product `tests/` tree is out of scope simply by never appearing in
`[tool.pyright].include`. The overseer's tests live BESIDE their source, so applying the
identical rule takes an explicit `exclude` entry rather than an omission. Do not read
that exclude as an overseer exemption; it is the repo's existing rule, spelled out.

| step | errors |
|---|---|
| baseline (product modules only) | 174 |
| `PaneDriver` Protocol for the tmux seam | 57 |
| `_codex` / `out` given their real types | 24 |
| `jsonio` narrowing at the JSON boundary | 2 |
| final two narrowings | **0** |

What each step was, so Gate B/E does not re-derive it:

- **`tmux: object` was over half the total.** `tmuxio.PaneDriver` is a `Protocol`
  declaring the TWELVE methods `Supervisor` calls, not all nineteen `TmuxIO` exposes.
  `TmuxIO` and `FakeTmux` satisfy it structurally — what a Protocol is for, and where the
  no-inheritance rule points. The narrow surface states what a substitute must implement
  to BE substitutable, so a future test double is complete when it satisfies this.
- **`_codex` and `out` already had real types.** `_codex` is
  `dict[tuple[str, str], CodexSession]`; typing it retired a `# type: ignore[attr-defined]`
  that existed only to paper over `object`. `out` is `IO[str]` and is no longer Optional:
  nothing ever passed `None`, so `__post_init__` existed solely to re-default it. A
  `default_factory` resolves it at construction, keeping the late binding tests rely on.
- **New `jsonio.py`** (stdlib-only, 40 beside-tests) narrows parsed JSON at the boundary.
  `json.loads` returns `Any` and `isinstance(x, dict)` narrows only to
  `dict[Unknown, Unknown]`, so every `.get()` went unknown and the per-field isinstance
  guards the call sites ALREADY performed stopped meaning anything to the checker.
  `as_object` / `as_list` / `as_float` fix it once. Two deliberate details: `as_object` is
  separate from `parse_object` so the two registry readers that report malformed-file and
  non-object-file with DIFFERENT diagnostics keep them; `as_float` rejects `bool` because
  it is an `int` subclass and a bare numeric check would turn `true` into `1.0`.
  The rejected alternative was the file-level `# pyright: reportUnknown...=none` pragma
  the product tree uses in one helpers module — right there (a pure-helper module),
  wrong here (a few parsing lines inside modules full of unrelated logic).
- **One source change rather than a type change:** `eff_ctx` is guarded by
  `has_context_left`, but pyright cannot narrow through an intermediate boolean, so the
  `is not None` is spelled out at the branch. VERIFIED not a latent bug — the guard
  already made `None` unreachable.
- The remaining 24 were `reportUnusedCallResult`, discharged with `_ =`.

**Trap for whoever automates a bulk edit here.** A script that rewrote lines via
`re.match(r"^(\s*)(\S.*)$", line)` silently DROPPED each line's trailing newline, merging
it with the next and producing syntax errors across two modules. Recovery was only cheap
because the other edits to those files were few and re-appliable from a clean `git
checkout`. Preserve the line terminator explicitly (`^([ \t]*)(.*?)(\r?\n?)$`), and
prefer per-file verification after any scripted rewrite.

## Gate C — ruff (PR #1396, merged 2026-07-19)

**Live-exercise evidence.** Post-merge master CI run
[29677133101](https://github.com/thewoolleyman/livespec/actions/runs/29677133101):
`check-lint`, `check-format`, and `check-overseer` all ran and passed against
combined master. Sabotage-verified before the PR — adding a `print` to `tmuxio.py`
turned `just check-lint` red; removing it turned it green.

**Measured outcome.** 929 raw findings → zero, with NO behavior change (the 304
beside-tests passed unchanged throughout). The handoff's 2026-07-18 estimate held up:
the cost really was concentrated in a handful of places, not spread thin.

How they resolved, so Gate D does not re-litigate any of it:

- **35 ambiguous-unicode** → `[tool.ruff.lint].allowed-confusables = ["❯", "›"]`.
  These are domain vocabulary (the prompt glyphs Claude Code and Codex print), and a
  two-codepoint repo-wide whitelist is NARROWER than a per-file-ignore, which would
  disable RUF001/2/3 across whole files and hide a genuinely confusable character
  introduced later. The repo was at zero findings for those rules, so it masks nothing.
- **~790 test-file findings** → one per-file-ignore for `.claude/skills/overseer/test_*.py`
  inheriting the `tests/**.py` rationale, plus three beside-test-specific entries:
  SLF001 (testing private decision helpers directly IS the point of a beside-test),
  ARG001/2 (signature-matching test doubles must accept args they do not use), S108
  (the real `/tmp` tmux socket paths are the fixture).
- **12 `print`** → refactored away, NOT exempted. The repo has zero T201 escapes and
  `SPECIFICATION/constraints.md` names ruff `T20` as the mechanical enforcement of its
  stdout-reservation rule. New stdlib-only `.claude/skills/overseer/streams.py` mirrors
  the product's `livespec/io/streams.py` one-hop indirection, with 5 beside-tests. The
  daemon's table render already used an injectable stream and was untouched.
- **~25 genuine fixes** → pathlib over `os.path`, named constants for the `/proc` stat
  field indices and the `list-panes` row width, `contextlib.suppress`, a keyword-only
  bool arg, line wraps, and three inline `# noqa: <CODE> — <reason>` escapes for cases
  correct as written (PATH `git`, the uid-scoped `/tmp` tmux socket namespace, the
  daemon loop's outermost bug-catcher boundary).

**The `evaluate` decision (maintainer-chosen 2026-07-19): split observe from decide.**
A new `Supervisor._observe` gathers the 16 facts the guard cascade reads and returns a
frozen `_Observation`. That took `evaluate` from 106 statements / 38 branches /
complexity 34 to **83 / 33 / 31** — a real reduction, but NOT under the thresholds
(10 branches, 30 statements). The residual is the decision cascade itself, whose
ORDERING is the design: the cardinal rule is enforced by which guard comes first. So
C901/PLR0911/PLR0912/PLR0915 are suppressed on that ONE function via an inline noqa,
with the full reasoning in its docstring; every other function in the module is still
held to them. Full decomposition was considered and rejected — it would scatter the
precedence order across call sites where no reader can verify it in one pass.

**Two facts Gate D should know:**

1. **`check-doctor-static` ALREADY reaches `.claude/skills/overseer/`.** It rejected a
   heading-level spec citation (`§"…"`) in the new `streams.py` docstring — the folder
   was never as far outside the gates as its own docs claimed. Cite spec FILES, not
   headings, in overseer code.
2. **Never `git checkout <file>` to undo a sabotage probe.** It reverts to HEAD, not to
   your working state, and silently discarded a whole file's worth of Gate C edits mid-run.
   Copy to the scratch dir and restore from there.

**Gate A live-exercise evidence (not merely merged + CI-green).** The post-merge master
CI run [29673873687](https://github.com/thewoolleyman/livespec/actions/runs/29673873687)
carried a `check-overseer` job that ran and passed against combined master — so the gate
is real in the environment it exists to protect, not only in a PR sandbox. Sabotage was
verified locally before the PR: appending a failing beside-test turned
`just check-overseer` red with a non-zero recipe exit; restoring it turned it green.

**Gate A (2026-07-19, PR #1387).** Adds a livespec-private `check-overseer` justfile
target (`uv run pytest .claude/skills/overseer/ -q`, **no coverage**), makes it a literal
member of the `just check` aggregate, and adds the matching `check-python` CI matrix leg
(`py_changed`-gated). Sabotage-verified. Also rewrites the overseer `AGENTS.md` paragraph
that documented the now-reversed "deliberately outside the product gates" design (D3).

Wiring facts learned (do NOT re-derive): `check-overseer` is a **livespec-private**
slug — it is not a module under `livespec_dev_tooling/checks/`, so
`canonical_check_slugs()` never emits it and the canonical meta-checks are inert. Only
two things are mandatory: the justfile recipe, and aggregate membership **anywhere after
the last canonical slug** (`check-aggregate-completeness` only enforces alphabetical
order WITHIN the canonical block, plus "no extras interleaved before it"). The CI matrix
leg is required by intent, not by a gate (`check-ci-matrix-completeness` is
canonical-scoped; `check-tool-backed-check-completeness` uses a fixed 4-slug policy).
`branch-protection.json` needs NO change — `ci-green` is the sole live required context,
and a matrix leg absent from the required list is a warning, exit 0. No test asserts over
the live justfile target list or CI matrix; `tests/heading-coverage.json` has no
justfile-target dimension.

The target deliberately runs WITHOUT `--cov` so host-glue modules never enter the
`fail_under = 100` gate, and it sorts after `check-coverage`/`check-per-file-coverage` in
the aggregate — keep it there if it ever moves.

Two operational lessons from landing it, both worth carrying into Gates C/D:

- **A conflicting PR gets NO CI run at all.** GitHub only creates a `pull_request` run
  when it can compute the merge ref, so a branch that conflicts with master silently
  reports zero checks rather than a failure — it looks like CI never fired. Master moves
  fast here (three unrelated threads landed commits during this one PR), so rebase onto
  `origin/master` and re-push the moment `gh pr view --json mergeStateStatus` reports
  `DIRTY`/`CONFLICTING`.
- **`.claude/skills/overseer/AGENTS.md` is contended surface.** The `overseer-known-defects`
  thread edited the same paragraph concurrently. Its addition — the *combined-master-state*
  warning (two overseer branches merging git-clean can still leave the folder red) — was
  PRESERVED and rewritten, not dropped: master CI now catches that case post-merge, but
  auto-merge lands before the master run finishes, so the manual combined-state re-run is
  still the advice while another overseer branch is in flight.

## Why this thread exists

The `overseer-tmux-runtime-column` work (merged: PRs #1345, #1351 — now archived under
`plan/archive/`) exposed a structural gap and prompted a bigger question:

1. **The overseer is outside every product gate.** Its beside-tests
   (`.claude/skills/overseer/`) are the SOLE gate on the folder but are a *manual*
   pre-push step — not wired into `just check`/CI. This is deliberate today (AGENTS.md:
   "outside the product gates… the discipline lives here, in the developer's hands").
   The cost: a broken overseer merges green. It happened **twice today** — the runtime
   column landed with no gate exercising it, and a concurrent `_codex` re-key
   (`a24e3e13`) + this thread's Codex test merged green independently but broke `pytest`
   on master (fixed by #1351). That is the exact "merges green with nothing exercising
   its behavior" failure the AGENTS.md warns about.
2. **Should it be shipped like everything else — usable by adopters?** (maintainer:
   "isn't it all just code? … explore making it part of the plugin and usable from the
   drivers for any adopter that wants to use it, as long as there is a fleet manifest.")

## Grounded findings (measured 2026-07-18 — do NOT re-measure, verify if stale)

### The gate-cost is far lower than first claimed ("many carve-outs" was WRONG)

Ruff, against the project's real ruleset:
- **All overseer `.py`: 929 findings — but 76% (705) are `assert` in TEST files** (S101),
  plus 52 private-member-access + 41 magic-values, almost all in tests. The product
  `tests/` tree already silences exactly these via per-file-ignores → ONE config line.
- **Product modules only (`supervisor`/`signals`/`registry`/`tmuxio`/`claude_sessions`/
  `codex_sessions`): ~70 findings**, clustering into: **35 ambiguous-unicode** (the `—`,
  `❯`, `›`, box-drawing glyphs the overseer literally parses out of real TUIs — one
  legitimate allowance, not a smell), **12 `print`** (the daemon's stderr log + table
  render — a daemon's output IS print), and **~20 genuine trivial fixes** (3 long lines,
  3 magic values, 2 pathlib, 2 "function too complex" on `evaluate`).

Pyright STRICT (project config: `typeCheckingMode = "strict"` + 7 strict-plus
diagnostics + the `returns` plugin), product modules: **163 errors** — the real work
(the `tmux: object` injectable seam, the duck-typed `FakeTmux`, the dynamic session
maps). Bounded, but this is where Phase 1's effort actually is.

### Per-gate honest cost

| Gate | Cost | What it is |
|---|---|---|
| A — tests run in `just check`/CI | **free** | beside-tests are hermetic (FakeTmux, fake `/proc`) → run anywhere. Add a separate `check-overseer` slug (no coverage). **Closes the regression that bit us twice.** |
| C — ruff lint | small | one unicode-glyph allowance + `print`-in-daemon policy + ~20 trivial fixes |
| B — coverage 100% | medium | host-glue (subprocess/`/proc`/daemon-loop/`main`) isn't unit-testable → needs a thin I/O-boundary extraction + `# pragma: no cover`, or a scoped threshold |
| D — pyright strict | real (163) | the injectable/duck-typed seams |
| E — dev-tooling ROP railway + AST style | judgment call | fleet-wide `Result`/no-`raise`-outside-`io` (spec §"ROP railway is fleet+adopter-wide"). Maintainer leans "treat it like everything else" → include it. |

### Fleet-manifest is an official spec contract (answers Phase 2's key question)

Live `SPECIFICATION/non-functional-requirements.md`:
- §"Fleet membership contract" → **Fleet manifest**: `.livespec-fleet-manifest.jsonc`
  enumerates `fleet` members and MAY carry an `adopters` array.
- §"Adopters": each adopter names `repo`, a conformance `profile`, and a `posture`
  (`released`/`pinned`/`none`); "an adopter … MAY be a fleet itself."

Two caveats that shape Phase 2:
1. It's ONE central manifest **hosted in livespec core** listing adopters — NOT a
   per-adopter file each ships (though an adopter *family* can host its own).
2. It is specified as **non-functional, fleet-self-application infrastructure**, bound
   to "the livespec fleet, its adopters, and the reference orchestrators, **never a
   third-party `livespec` consumer or the `/livespec:*` plugin skills core ships**."

So if a shipped overseer read a fleet manifest, that either (a) makes the manifest a
**functional shipped contract** — a deliberate spec-boundary change — or (b) keeps it a
fleet-self-application tool adopters MAY run within the same manifest model. (b) fits
today's boundary; (a) is a real spec change. (Note: a live `register-homelab-adopter`
thread is exercising the adopter path right now.)

## Phase 1 — inside the gates (the committed near-term)

Goal: the overseer folder is a first-class module — `just check`/pre-push/CI run its
lint, types, tests, and a coverage policy — with NO special local-only exemption beyond
what the code's host-glue nature genuinely requires (and each such exemption is a
documented severity lever, not a silent skip, per the enforcement discipline).

Proposed sequence (each its own small PR; Gate A first for the immediate win):

1. ~~**Gate A — wire the hermetic beside-tests into `just check`.**~~ **DONE** (PR #1387).
2. ~~**Gate C — ruff.**~~ **DONE** (PR #1396). Landed as planned, with one deviation worth
   noting: the `print`-in-daemon *allowance* the plan offered as an option was NOT taken —
   the prints were refactored through a new `streams.py` sink instead, because the repo has
   zero T201 escapes and the spec names `T20` as the enforcement of a normative rule. See
   the Gate C section above.
3. ~~**Gate D — pyright strict.**~~ **DONE** (PR #1408). The plan's prediction was right
   about the shape — a `Protocol` for the tmux boundary and typed session maps WERE the
   bulk — and wrong about the count only because it did not anticipate the beside-tests.
   See the Gate D section above.
4. **Gate B + E — coverage + ROP railway.** The real design decision (below): how
   host-glue reaches 100% and whether it goes on the `Result` railway. B needs D1; E is
   blocked on D2's remaining scope question.

### OPEN DECISIONS (resolve one at a time)

- **D1 — coverage strategy for host-glue.** Options: (a) *boundary extraction* — isolate
  every real-world side effect (subprocess/tmux/`/proc`/`main`/daemon-loop) behind the
  existing `tmuxio`/`claude_sessions` seams so the pure logic hits 100% and only the thin
  I/O shell is `# pragma: no cover`d [Recommended — matches the product's io/ boundary
  discipline]; (b) a scoped per-file coverage threshold for the folder; (c) keep coverage
  out and enforce only lint+types+tests. Recommend (a).
- **D2 — ROP railway for host-glue (Gate E).** Maintainer leans "treat it like
  everything else" → put the overseer on the `Result`/`IOResult` railway with the fleet's
  `reportUnusedCallResult`/`BLE` guardrails, the single outermost supervisor bug-catcher
  boundary. Confirm scope: is the overseer "product logic" for the railway rule, or
  host-glue like the `.claude/hooks/` footgun-guard (which is NOT on the railway)? The
  spec's railway rule is fleet+adopter-wide for "first-party Python"; the overseer is
  `.claude/skills/` host tooling. RESOLVE before Gate B/E work.
- **D3 — does "inside the gates" change the LOCAL-ONLY status?** RESOLVED (no, by
  default): gate coverage (quality) is independent of distribution. The folder stays
  local-only in Phase 1. The AGENTS.md paragraph asserting "deliberately outside the
  product gates … the discipline lives in the developer's hands" was REWRITTEN in
  PR #1387 (it was the documented decision being reversed).

**Cross-thread input for D2 — read `plan/rop-sweep-fleet-policy/handoff.md` before
resolving it.** That thread's ratified fleet policy (livespec PR #1321, merged;
`non-functional-requirements.md` v165) mandates the FULL `Result`/`IOResult` railway for
every Python-carrying fleet repo — Drivers and dev-tooling included — with the sole
exemption being a repo with zero first-party Python.

⚠️ **Gate C invalidated one of that thread's stated facts — tell it.** The rop-sweep
audit recorded that the "noqa the fail-open/supervisor catchers" step was moot because
those catchers sit in ruff-EXCLUDED directories, and it listed
`.claude/skills/overseer/**` among them. **That is no longer true as of PR #1396**:
the overseer is inside ruff now, `BLE` reaches it, and its single blind catch — the
daemon loop's outermost bug-catcher — already carries an explicit
`# noqa: BLE001 — outermost supervisor boundary`. The other listed directories
(`.claude/hooks/**`, `.claude-plugin/hooks/**`, `livespec/hooks/**`) are unaffected.

So D2's remaining question is narrower than it was: not "will `BLE` ever reach the
overseer" (it does, and the one site is resolved), but whether the repo-level full-ROP
bar is intended to reach a `.claude/skills/` host-tooling folder at all, or only the
`livespec` package.

Both facts were RELAYED to the live `rop-sweep-fleet-policy` tmux session on 2026-07-19
(pane idle, bracketed-paste). Nothing here was edited on their behalf.

### ✅ D2 marker blocker — RESOLVED by the rop-sweep thread (2026-07-19)

The gap below was relayed to the `rop-sweep-fleet-policy` session, which **adopted a
fifth marker** in commit `98dfb144`, using the suggested wording verbatim:

> `— sole loop-iteration bug-catcher: log traceback, continue`

Its contract: a daemon supervising N independent units MAY carry ONE ADDITIONAL broad
catch as a direct child of its supervision-loop body; it MUST log the FULL traceback
(a silent `pass` is forbidden), MUST NOT exit, and its cardinality is one per
SUPERVISION LOOP rather than one per entry artifact — so an entry artifact running such
a loop may carry both its `main()` boundary handler and this one, and no more. The
proposal now cites the overseer as the worked example for the category.

The overseer's marker was updated to the conforming wording in PR #1408's second commit,
so the worked example no longer contradicts the text citing it. The proposal is still
UNRATIFIED, so nothing is binding yet.

Two follow-ups the proposal itself flags, neither owned by this thread:

1. `check-supervisor-discipline` scopes on `source_tree_prefixes`, which does NOT include
   `.claude/skills/`, so nothing mechanically enforces this over the overseer. The
   proposal explicitly tracks extending that scope separately.
2. The proposal ALSO resolves a spec-versus-implementation divergence it found on the
   way: the current text mandates an explicit `try/except Exception` bug-catcher in every
   supervisor, but shipped core supervisors carry none and CI is green.

**What remains open for D2** is only the original scope question, unchanged: whether the
repo-level full-ROP bar reaches a `.claude/skills/` host-tooling folder at all, or only
the `livespec` package. Gate E stays blocked on that.

### The original gap (kept for the record)

⚠️ **The overseer's daemon catch fit none of the FOUR original markers**

`SPECIFICATION/proposed_changes/rop-broad-except-boundary-rule.md` (filed by the
rop-sweep thread, commit `985a4322`, under Fable review at the time of writing) defines a
**closed set of four** standardized `# noqa: BLE001` markers and rules that any other
wording "marks a violation, not an escape":

1. `— sole supervisor bug-catcher: log traceback, exit 1`
2. `— sole fail-open hook boundary: silent pass-through, exit 0`
3. `— sole fail-closed guard boundary: deny per policy, exit 0`
4. `— foreign-code isolation: <surface> crash captured as <ErrorType>, reported`

The overseer's one broad catch (`supervisor.py`, inside `Supervisor.run`'s `while True`)
matches NONE of them. It logs the full traceback and **continues the loop** — it does not
exit 1, and it is not a direct child of `main()`:

```python
except Exception:  # noqa: BLE001 — outermost supervisor boundary
    self._log("tick error (continuing):\n" + traceback.format_exc())
```

That shape is the daemon's whole point: it supervises N independent tracks, and a bug
evaluating ONE track must not take the process down and strand the other N-1. "Log and
exit 1" is the wrong contract for it.

So the proposal, as written, has no category for a long-running supervisor's
**per-iteration resilience catch**. If it ratifies unchanged, the overseer becomes
non-conforming immediately, and the only conforming moves would be to mis-label it as
marker 1 (a lie — it does not exit 1) or to change the daemon's behavior (wrong).

Note the conflict would be **spec-text-only, not mechanical**: `check-supervisor-discipline`
scopes on `source_tree_prefixes`, which does not include `.claude/skills/`, so nothing
would actually flag it. That is precisely why it needs a human ruling rather than a gate.

**Do not resolve this here.** It is the rop-sweep thread's proposal and its reviewer's
pass; the gap was relayed to that session with two options to weigh (add a fifth marker
such as `— sole loop-iteration bug-catcher: log traceback, continue`, or rule that the
bar does not reach `.claude/skills/` at all). Gate B/E work stays blocked until that
lands, because the answer determines whether the overseer goes on the `Result` railway.

## Phase 2 — ship it (design exploration, not yet committed)

Goal: an adopter with a fleet manifest can run the overseer. Architecturally plausible
(stdlib-only, `python3`-invokable — fits the plugin model), but real coupling to resolve:

- **Host coupling.** Scans `/proc` (Linux-only), drives real tmux, reads
  `~/.claude/sessions/` (Claude registry) + Codex rollout fds. macOS/non-tmux adopters
  can't run it unchanged. Needs a portability boundary (or a declared "Linux+tmux only"
  requirement).
- **Driver split.** Per the architecture, the interactive `/overseer` *skill* would ship
  from the Driver repos (`livespec-driver-claude`/`-codex`), with the daemon + prose in
  CORE — the established prose-in-core / thin-binding-in-driver pattern used by every
  `/livespec:*` operation.
- **The fleet-manifest boundary decision (from findings above).** (a) promote the
  manifest to a functional shipped contract, or (b) keep it fleet-self-application and
  ship the overseer as a tool adopters-as-families MAY run. Recommend deciding this
  early — it gates the whole Phase 2 shape.

### OPEN DECISIONS (Phase 2 — deferred until Phase 1 lands)

- **D4 — portability target.** "Linux+tmux only, declared requirement" vs. abstract the
  host boundary for macOS/other. Recommend declared-requirement first (the fleet is
  Linux+tmux), abstract later if an adopter needs it.
- **D5 — manifest boundary** (functional shipped contract vs. fleet-self-application).
- **D6 — anchor a ledger epic?** Phase 2 is multi-repo (CORE + both Drivers) → an epic
  with per-repo work-items + cross-repo links is the right shape IF Phase 2 proceeds.
  Phase 1 is single-repo/local and can run as this plan thread without an epic.

## Discipline (this folder)

- **Worktree → PR → merge → cleanup for EVERY change** (learned the hard way this
  session: edits were first made in the primary checkout — the live daemon reads the
  primary, so in-place edits risk it importing half-finished code. Do edits in a
  worktree from the start).
- Beside-tests remain the correctness gate; run `uv run pytest .claude/skills/overseer/ -q`
  before every push. Once Gate A lands, `just check` runs them too.
- Overseer `.py` is exempt from Red-Green-Replay (not an `_IMPL_PREFIXES` path) — use
  `fix(overseer):` / `chore(overseer):` with test+impl in one commit; never `--no-verify`.
- Sabotage-verify any new guard (break it → watch its test go red → restore).
- **This handoff is an owned artifact, not a read-only inbox.** A session working this
  track updates it AS findings land and commits it — never accumulating them in
  conversation context to be written at session end (a session can die first; that is
  how 153 lines ended up unversioned on 2026-07-19). If a claim here is disproved,
  correct it in place and say so; a stale handoff actively misleads, and two of this
  document's own claims sent a later session down wrong paths before being caught.
  Doc-only commits are NOT gated by `check-doctor-static` — there is no blocker excuse
  for leaving it dirty.
