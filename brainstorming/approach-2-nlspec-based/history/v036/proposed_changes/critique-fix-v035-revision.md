# critique-fix v035 → v036 revision

## Origin

The v034 step-3 activation commit
(`chore!: activate v034 replay hook + remove v033 hook`,
sha `495e5ce`) wired the replay hook into lefthook's
`commit-msg` stage and renumbered pre-commit's stages
(removed v033 `02-red-output-in-commit`; renumbered
`03-check` → `02-check`). Pre-commit's `02-check`
continued to invoke the full `just check` aggregate, which
includes `check-tests` (line 148: `uv run pytest`) and
`check-coverage` (line 150: `uv run pytest --cov`).

The v034 D2-D3 Red→Green replay contract requires the
**Red commit to stage a test file that fails** (per
PROPOSAL §"Red mode (initial commit)" lines 3522-3531:
"Hook computes the test file's SHA-256, runs the listed
test... expects non-zero exit code"). The replay hook
fires at `commit-msg` stage, AFTER pre-commit. But
pre-commit's `02-check` runs pytest on the staged tree; a
failing test causes pytest to exit non-zero, `check-tests`
fails, the `just check` aggregate fails, lefthook
pre-commit aborts the commit BEFORE the commit-msg stage
ever fires. The replay hook never gets a chance to
validate the Red moment or write trailers.

Cycles 173-183 didn't expose the contradiction because
they were authored under v033 discipline (test+impl staged
together → pre-commit gate sees Green → passes). The
v034 codification (`eaa3f7b`) and v035 codification
(`cf1c279`) didn't address the structural conflict. Drain
cycle 1 (`25a8033`) used `test:` subject so the replay
hook exempted it AND the staged tests passed (no Red
moment), so pre-commit's `check-tests` passed. The first
attempt to author a `feat:` Red commit (drain cycle 2,
`livespec/types.py`) is blocked.

PROPOSAL.md §"Activation" (lines 3492-3511) explicitly
specifies that the pre-commit gate includes "`just
check-coverage` at 100% line+branch **per-file** per v033
D2, plus the rest of `just check`, plus the v034 D3
Red→Green replay verification". The "rest of `just
check`" is what creates the conflict: it includes
`check-tests`. The Red mode contract and the pre-commit
gate as written cannot both hold — one of them has to
yield.

The remedy is a v036 revision covering two decisions:

- **D1** Resolve the conflict by introducing a Red-mode-aware
  pre-commit aggregate (`just check-pre-commit`) that
  detects Red-mode shape (exactly one test file added
  under `tests/` AND zero implementation files added under
  `livespec/**`, `bin/**`, or `dev-tooling/checks/**`) and
  conditionally skips `check-tests` + `check-coverage`,
  deferring their verification to the commit-msg replay
  hook. All other shapes (Green amend, `test:` commits,
  `chore:` commits, etc.) run the full `check` aggregate.
  Lefthook pre-commit's `02-check` invokes the new
  `just check-pre-commit` aggregate. Pre-push and CI keep
  invoking `just check` (full suite, no filter).
- **D2** Plan-text + housekeeping. Plan §"Version basis"
  preamble gains a v036 decision-block; Phase 0 step-1
  byte-identity → `history/v036/`; Phase 0 step-2
  frozen-status → "Frozen at v036"; Execution-prompt block
  authoritative-version → v036; plan §"v034 transition"
  step 3 + §"Per-cycle workflow" gain notes about the
  `check-pre-commit` aggregate; STATUS.md updates.

The v036 codification commit is spec-only (matching the
v035 pattern + v033 D5a spec-then-implementation
precedent). The implementation (`justfile` recipes +
`lefthook.yml` update) lands in a separate follow-up
commit before drain cycle 2 resumes.

## Decisions captured in v036

### D1 — Red-mode-aware pre-commit aggregate

**Surface in PROPOSAL.md.** Two locations:

- §"Testing approach — Activation" (lines 3492-3511) —
  current wording specifies pre-commit gate runs full
  `just check`; needs adjustment to describe the
  `check-pre-commit` aggregate.
- §"v034 D2-D3 Red→Green replay contract" §"Red mode
  (initial commit)" (lines 3522-3531) — needs a paragraph
  describing how the Red-staged failing test coexists with
  the pre-commit gate via `check-pre-commit`'s shape
  detection.

**Decision.** Introduce a new `just check-pre-commit`
aggregate that is identical to `just check` EXCEPT it
classifies the staged tree shape and conditionally
substitutes the test-execution checks:

- **Red-mode shape** (exactly one test file added under
  `tests/` AND zero implementation files added under
  `.claude-plugin/scripts/livespec/**`,
  `.claude-plugin/scripts/bin/**`, or
  `dev-tooling/checks/**` in the staged tree per
  `git diff --cached --name-only --diff-filter=A`): skip
  `check-tests` and `check-coverage`. Verification of the
  staged failing test is performed by the commit-msg
  replay hook (which already runs
  `pytest <staged-test-file>` per the v034 D3 contract);
  per-file 100% coverage of pre-existing impl files
  remains green (no impl staged, no coverage drift).
- **All other shapes** (Green amend; `test:`, `chore:`,
  `docs:`, `build:`, `ci:`, `style:`, `refactor:`,
  `perf:`, `revert:` commits; `feat:`/`fix:` commits with
  paired test+impl staged together; pure config-only
  commits): run the full `check` aggregate including
  `check-tests` and `check-coverage`.

The Red-mode classifier is shared with the commit-msg
replay hook's existing `_classify_staged` logic (cycle
178, sha `2d5f11b`); duplicating the rule in two places
is acceptable for the bootstrap-throwaway era. A future
post-Phase-6 propose-change can factor out a shared
`dev-tooling/checks/staged_shape.py` helper if the
duplication becomes load-bearing.

`lefthook.yml` pre-commit's `02-check` invokes
`just check-pre-commit` instead of `just check`. The
pre-push hook + the manual `just check` invocation + CI
matrix all keep using `just check` (the full,
unconditional aggregate).

The Green amend takes the all-other-shapes path: the test
file is in HEAD~0 (the Red commit), so it is no longer
"added" per `--diff-filter=A` semantics; the impl files
ARE added; the staged-tree shape doesn't match Red mode;
the full `check` aggregate runs; tests pass against the
new impl; per-file coverage validates 100% on the new
impl; the commit-msg replay hook runs Green-mode logic
and writes Green trailers. End-to-end verification is
preserved.

**Rationale.** The conflict is fundamental: two
mechanisms both claim authority over test execution at
commit time. Pre-commit's `just check` says "tests must
pass to commit". v034 D3's Red mode says "tests must fail
to commit (in Red mode only)". The cleanest resolution is
deferral: pre-commit's test-execution defers to the
commit-msg replay hook in Red mode (where the replay hook
is the load-bearing verifier anyway), and runs at full
strength in all other modes (where the replay hook is
exempt). The total verification is the SAME — one of the
two stages runs pytest on the staged test file in either
case, plus the Green amend always runs the full
`check-tests` against the post-amend tree.

The classifier-based approach was preferred over four
alternatives:

- **Drop the amend pattern** (revert to v033 D5b
  test+impl atomically; trailers in single commit). Big
  semantic walkback of v034 D2-D3; loses the
  reflog-verifiable temporal proof the amend provides.
  Rejected.
- **Move all test execution to pre-push only**.
  Eliminates the conflict but weakens the per-commit
  hard-gate that v033 D5a moved forward specifically to
  close the discipline gap. Rejected.
- **Allow `--no-verify` for Red commits**. Bypasses
  lefthook entirely; defeats the pre-commit gate's
  purpose; relies on developer discipline to use the
  bypass only at Red moments. Rejected per the
  global-rule prohibition on `--no-verify`.
- **Subject-line-aware pre-commit**. Inspect the commit
  subject at pre-commit and skip tests for
  `feat:`/`fix:`. Pre-commit doesn't have access to the
  commit message file (that's commit-msg stage). Could
  inspect a marker file or the prepare-commit-msg output,
  but adds plumbing. The shape-based classifier achieves
  the same outcome without subject-line dependence.
  Rejected as more complex than the chosen mechanism.

**PROPOSAL edits.** Two locations:

1. §"Testing approach — Activation" (lines 3492-3511):
   replace the parenthetical "(`just check-coverage` at
   100% line+branch **per-file** per v033 D2, plus the
   rest of `just check`, plus the v034 D3 Red→Green
   replay verification)" with a description of the
   `check-pre-commit` aggregate's Red-mode classifier:

   ```
   The hard-constraint pre-commit gate runs
   `just check-pre-commit` — a Red-mode-aware aggregate
   that detects the v034 D3 Red commit shape (exactly
   one test file added under `tests/` AND zero
   implementation files added under `livespec/**`,
   `bin/**`, or `dev-tooling/checks/**`) and skips
   `check-tests` + `check-coverage` in that case
   (deferring their verification to the commit-msg
   replay hook), running the full `just check` aggregate
   (including 100% line+branch per-file coverage per
   v033 D2 and all 24 canonical-target checks) in every
   other case (Green amend, `test:`/`chore:`/etc.,
   non-Red `feat:`/`fix:`). Pre-push and CI invoke
   `just check` directly (no Red-mode classifier; full
   suite always).
   ```

2. §"v034 D2-D3 Red→Green replay contract" §"Red mode
   (initial commit)" (lines 3522-3531): append a
   paragraph after the existing §"Per-file constraint
   (v035 D4)" sub-section:

   ```
   **Coexistence with the pre-commit gate (v036 D1).**
   The Red commit's failing test would otherwise be
   blocked by lefthook pre-commit's `check-tests` /
   `check-coverage` invocations. Per v036 D1, lefthook
   pre-commit invokes `just check-pre-commit` (not `just
   check`); that aggregate detects Red-mode shape via
   `git diff --cached --name-only --diff-filter=A` and
   skips `check-tests` + `check-coverage` when the
   shape matches (one test file added under `tests/`,
   zero impl files added). The commit-msg replay hook
   (this hook) runs pytest on the staged test file,
   verifying the Red moment. Net effect: each Red
   commit's test is run exactly once at commit time
   (by the replay hook), and pre-commit's other 22
   canonical-target checks run unconditionally.
   ```

### D2 — Plan-text and housekeeping edits

**Surface in plan and PROPOSAL.**

1. PROPOSAL.md §"Versioning" decisions block: append a
   v036 entry summarising D1 + D2.

2. PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md §"Version
   basis": preamble decision block bump (current text
   describes v034 + v035; append v036 D1-D2 summary line).

3. PLAN §"Phase 0 step 1": byte-identity check reference
   bumps from `history/v035/` to `history/v036/`.

4. PLAN §"Phase 0 step 2": frozen-status header bumps from
   "Frozen at v035" to "Frozen at v036".

5. PLAN §"Execution prompt": authoritative-version line
   bumps from "Treat PROPOSAL.md v035 as authoritative" to
   v036.

6. PLAN §"v034 transition — replay-hook activation +
   drain authorization (v034 D3 / D5 / D6)" step 3
   description of `lefthook.yml` updates: append note that
   pre-commit's `02-check` invokes `just check-pre-commit`
   per v036 D1 (the v034 step-3 activation commit
   `495e5ce` predated this and used `just check`; v036's
   implementation commit corrects it).

7. PLAN Phase 5 §"Aggregate-restoration drain" §"Per-cycle
   workflow": add a note to step 2 (the Red→Green amend
   description) clarifying that the Red commit's failing
   test passes through pre-commit because of v036 D1's
   `check-pre-commit` aggregate's Red-mode classifier;
   the commit-msg replay hook is the verifier.

8. STATUS.md: update §"Drain rhythm" with a brief mention
   of v036 D1; update Last-commit field after the v036
   codification commit lands.

**No companion-doc edits are required** — the
`python-skill-script-style-requirements.md`,
`NOTICES.md`, `.vendor.jsonc`, and `pyproject.toml` don't
carry any references to the pre-commit aggregate's
specific recipe name.

**Implementation lands in a separate follow-up commit**
(matching the v035 / v033 D5a precedent: codification
commit is spec-only). The follow-up commit:

- Edits `justfile`: adds `check-pre-commit` recipe (with
  the Red-mode classifier inline as a bash heredoc; or
  delegates to a small helper at
  `dev-tooling/check-pre-commit.sh` if the inline grows
  beyond ~20 lines).
- Edits `lefthook.yml`: pre-commit's `02-check` `run:`
  field changes from `just check` to `just check-pre-commit`.
- Subject: `chore!: implement v036 D1 check-pre-commit
  Red-mode classifier`. No TDD trailers required (chore
  per v034 D2 exempt list).

Drain cycle 2 (the first `feat:` Red→Green amend) follows
the implementation commit.
