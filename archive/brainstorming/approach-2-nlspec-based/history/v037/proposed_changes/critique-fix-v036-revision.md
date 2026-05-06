# critique-fix v036 → v037 revision

## Origin

v036 D1 introduced a Red-mode-aware pre-commit aggregate
(`just check-pre-commit`) that classifies the staged tree
shape and skips `check-tests` + `check-coverage` when the
shape matches the v034 D3 Red commit shape. The classifier
was specified in PROPOSAL.md three places — §"Activation"
(lines 3494-3499), §"Coexistence with the pre-commit gate
(v036 D1)" prose (lines 3566-3567), and the literal `git`
command in the same sub-paragraph (line 3564) — all three
loci use "added" wording (and `--diff-filter=A` literally).

The cycles authored from v036-codification onward (drain
cycles 2-6 + the resolve_template gap-fix cycles A and B)
all happened to author brand-new test+impl file pairs, so
the classifier's `--diff-filter=A` (added files only)
shape worked for every cycle on record. Phase 6's
post-seed `version_directories_complete` v* filter Red→Green
cycle (open-issues 2026-05-03T02:39:00Z) is the first cycle
that EXTENDS pre-existing test and impl files in their
established mirror-pairing (one new test case in
`tests/livespec/doctor/static/test_version_directories_complete.py`;
one new behavior in
`.claude-plugin/scripts/livespec/doctor/static/version_directories_complete.py`).
The Red commit's `git diff --cached --name-only --diff-filter=A`
returns empty (file is M, not A); `LIVESPEC_PRECOMMIT_RED_MODE`
stays unset; full `just check` runs; `check-tests` fails on
the new failing test; pre-commit blocks the Red commit.

The design intent behind v036 D1 was always "Red commit =
new test (no impl)" where "new test" includes new test
cases in pre-existing test files (mirror-pairing routinely
calls for one test file per impl file, not one test file
per behavior). The `--diff-filter=A` narrowing in
PROPOSAL.md and the matching `justfile` recipe was a
codification slip — the cycles authored under v033 D5b +
v034 D7 happened to be all-new-pair shapes, so the
narrowing was latent through v036. The first attempt at
extending an existing pair surfaced the contradiction.

The remedy is a v037 revision covering two decisions:

- **D1** Broaden the Red-mode classifier from
  `--diff-filter=A` to `--diff-filter=AM` for both the
  tests bucket AND the impl bucket. The semantic stays the
  same ("Red commit = staged test change with no staged
  impl change") but now correctly admits the
  pre-existing-pair extension shape. Both buckets must
  broaden together: keeping impl on `A` while broadening
  tests to `AM` would let a Red commit modify an existing
  impl file undetected, which is a worse failure mode than
  the original narrowing.
- **D2** Plan-text + housekeeping. Plan §"Version basis"
  preamble gains a v037 decision-block; Phase 0 step-1
  byte-identity → `history/v037/`; Phase 0 step-2
  frozen-status → "Frozen at v037" (per precedent — this
  header literal is itself a no-op convention; the actual
  PROPOSAL.md frozen-status header has stayed "Frozen at
  v024" since v024 — see §"Implementation note" below);
  Execution-prompt block authoritative-version → v037;
  STATUS.md updates.

The v037 codification commit is spec-only (matching the
v035 / v033 D5a spec-then-implementation precedent). The
implementation (`justfile` `check-pre-commit` recipe edit
broadening both `--diff-filter` invocations) lands in a
separate follow-up commit before cycle (ii) of the Phase
6 gap-fix work resumes.

## Decisions captured in v037

### D1 — Broaden the v036 D1 classifier from `A` to `AM`

**Surface in PROPOSAL.md.** Three locations, all in
§"Testing approach":

- §"Activation" (lines 3492-3508) — current wording says
  "exactly one test file added under `tests/` AND zero
  implementation files added under
  `.claude-plugin/scripts/livespec/**`,
  `.claude-plugin/scripts/bin/**`, or
  `dev-tooling/checks/**`".
- §"v034 D2-D3 Red→Green replay contract" §"Red mode
  (initial commit)" §"Coexistence with the pre-commit gate
  (v036 D1)" (lines 3558-3572) — current wording says
  "added or modified" → just kidding, current wording says
  the literal `--diff-filter=A` and "one test file added
  under `tests/`, zero impl files added".

**Decision.** Broaden the classifier in all three loci to
recognize ADDED OR MODIFIED tests + ADDED OR MODIFIED
impl. The replacement term in prose: "added or modified".
The replacement git invocation:
`git diff --cached --name-only --diff-filter=AM`.

The semantic claim: "Red mode = staged change to test files
ONLY (added or modified), with no staged change to impl
files (added or modified)". This is the design intent
v036 D1's prose was always trying to capture; the
codification narrowed it to "added" by accident because
every cycle on the record at v036-codification time
happened to be a new-file-pair shape.

The broadening symmetry across both buckets is
load-bearing. If only the tests bucket broadens (test
changes count whether A or M; impl changes only count
when A), then a Red commit that modifies an existing impl
file would slip through the classifier as Red mode — the
test-bucket count would be ≥ 1 and the impl-bucket count
would be 0 (because the impl modification doesn't match
filter `A`). The full `just check` would skip; the
modified impl would land in a Red commit; the Green amend
contract would be undermined (the Green amend contract
requires impl to be staged at the amend; but if impl was
already staged at Red, the amend's "stage impl" step is
ambiguous). Both buckets must broaden.

**Rationale.** The v036 D1 conflict-resolution mechanism
(defer test-execution to commit-msg replay hook in Red
mode; run full check in all other modes) was correct.
The narrowing to `A` was a codification slip. The
straightforward broadening to `AM` preserves the
mechanism while admitting the natural extension shape.
No other v036 D1 invariants change.

The broadening was preferred over three alternatives:

- **Force every Red commit to use a brand-new test file**
  (split test files per behavior). Violates mirror-pairing
  (v033 D1: one test file per impl file). Rejected.
- **Allow `--no-verify` on Red commits with extension
  shape**. Bypasses lefthook entirely; same global-rule
  prohibition that v036 D1 already rejected. Rejected.
- **Different filter semantics (e.g., delete-only and
  rename-aware) in the classifier**. The `AM` shape covers
  the mirror-paired-extension case; deletion shapes are
  load-bearing only for refactor: / chore: subjects which
  are exempt from the replay hook anyway. Rejected as
  unnecessary complexity.

**PROPOSAL edits.** Three locations:

1. §"Testing approach — Activation" (lines 3492-3508):
   replace "exactly one test file added under `tests/` AND
   zero implementation files added under
   `.claude-plugin/scripts/livespec/**`,
   `.claude-plugin/scripts/bin/**`, or
   `dev-tooling/checks/**`" with "exactly one test file
   added or modified under `tests/` AND zero implementation
   files added or modified under
   `.claude-plugin/scripts/livespec/**`,
   `.claude-plugin/scripts/bin/**`, or
   `dev-tooling/checks/**`".

2. §"v034 D2-D3 Red→Green replay contract" §"Red mode
   (initial commit)" §"Coexistence with the pre-commit gate
   (v036 D1)" (line 3564): replace `git diff --cached
   --name-only --diff-filter=A` with `git diff --cached
   --name-only --diff-filter=AM`.

3. §"v034 D2-D3 Red→Green replay contract" §"Red mode
   (initial commit)" §"Coexistence with the pre-commit gate
   (v036 D1)" (lines 3566-3567): replace "one test file
   added under `tests/`, zero impl files added" with "one
   test file added or modified under `tests/`, zero impl
   files added or modified".

### D2 — Plan-text and housekeeping edits

**Surface in plan and PROPOSAL.**

1. PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md §"Version
   basis": preamble decision block gains a v037 entry
   (D1-D2 summary line).

2. PLAN §"Phase 0 step 1": byte-identity check reference
   bumps from `history/v036/` to `history/v037/` (and the
   nested narrative chain extends with the v037
   substance line).

3. PLAN §"Phase 0 step 2": frozen-status header reference
   bumps from "Frozen at v036" to "Frozen at v037" (per
   the established no-op convention — see §"Implementation
   note" below).

4. PLAN §"Execution prompt": authoritative-version line
   bumps from "Treat PROPOSAL.md v036 as authoritative" to
   v037.

5. STATUS.md: §"Phase 6 entry" gets a brief mention of v037
   D1; Last-commit field updates after the v037
   codification commit lands.

**No companion-doc edits required** — the
`python-skill-script-style-requirements.md`, `NOTICES.md`,
`.vendor.jsonc`, and `pyproject.toml` don't reference the
classifier's specific filter semantics.

**Implementation lands in a separate follow-up commit**
(per v035 / v033 D5a spec-then-implementation precedent).
The follow-up commit:

- Edits `justfile` `check-pre-commit` recipe (lines
  205-220): both `--diff-filter=A` invocations broaden to
  `--diff-filter=AM`; the surrounding prose comments
  update to match.
- Subject: `chore!: implement v037 D1 — broaden v036 D1
  classifier to AM`. No TDD trailers required (chore per
  v034 D2 exempt list).

Cycle (ii) of the Phase 6 gap-fix work (the
`version_directories_complete` v* filter Red→Green) lands
immediately after the implementation commit.

## Implementation note

The "Phase 0 step 2 frozen-status header bump" instruction
present in every revision file from v025 onward (and
re-stated here as v037 D2 item 3) refers to the LITERAL
text in the PLAN's Phase 0 step 2 description (which says
"`> **Status:** Frozen at vNNN`"), NOT to the actual
PROPOSAL.md `> **Status:** Frozen at v024.` line at
PROPOSAL.md:3. The PROPOSAL.md frozen-status header has
remained "Frozen at v024" across every snapshot
(`history/v024/PROPOSAL.md` through
`history/v036/PROPOSAL.md` all carry "Frozen at v024" at
line 3). Treating the header as marking "the version at
which the spec entered the frozen-evolution-via-
SPECIFICATION/ regime" (set once at v024; stable since)
is the established convention. v037 follows the same
convention — the PROPOSAL.md edit set above does NOT
include the header bump; only the PLAN's Phase 0 step 2
narrative reference is bumped.
