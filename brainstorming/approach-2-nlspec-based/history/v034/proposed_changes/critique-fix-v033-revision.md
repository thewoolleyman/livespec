# critique-fix v033 → v034 revision

## Origin

The v033 D5b second retroactive redo reached Phase-4-parity at
commit `ed20f9b` (25 of 25 deleted dev-tooling check scripts
re-authored under TDD; 277 tests passing; 100% per-file
line+branch coverage). Of the 26 canonical `just check`
aggregate targets, 23 are now bound to the aggregate; 4 remain
unbound because their backing content is missing:

1. `check-complexity` — 31 ruff PLR/C90 violations + `seed.py`
   at 392 LLOC (>200 limit per `file_lloc.py`).
2. `check-pbt-coverage-pure-modules` — 3 test modules
   (`tests/livespec/parse/test_jsonc.py`,
   `tests/livespec/validate/test_seed_input.py`,
   `tests/livespec/validate/test_revise_input.py`) lack any
   `@given(...)` decorator.
3. `check-schema-dataclass-pairing` — 5 schemas lack paired
   dataclass+validator triples.
4. `check-newtype-domain-primitives` — `livespec/types.py`
   does not exist; 4 fields (`Finding.check_id`,
   `Finding.spec_root`, `RevisionInput.author`,
   `SeedInput.template`) use raw `str`.

Plus three config-tier targets currently failing: `check-lint`,
`check-format`, and (plan-deferred to Phase 7) `check-types`.

Three concurrent issues triggered v034:

**Issue 1 — broken pushes to master.** The `just check`
aggregate is thinned to the currently-passing 23 targets per
the explicit transitional comment at `justfile:55-74`. The
local pre-commit hook gates on this thinned aggregate. CI
(`.github/workflows/ci.yml`) runs the full canonical-target
matrix (31 targets) with `fail-fast: false`. Result: every
cycle in the second-redo's drain phase fails in CI on
`check-complexity`, `check-pbt-coverage-pure-modules`, and the
config-tier targets, until each cycle's fix lands. Master
keeps receiving CI-broken commits because the local gate does
not run the same scope CI does.

**Issue 2 — TDD discipline is honor-system in commit content.**
v033 D4 promoted `## Red output` capture from informational to
hard-gate, but the `red_output_in_commit.py` check verifies
only that the commit message contains a `## Red output`
heading + fenced code block — not that the captured output
reflects an actual Red moment that preceded the implementation.
A sub-agent could fabricate the output and the check cannot
tell. The goal of v032/v033 — "implementation must emerge
from failing tests, not be transcribed from prior attempts" —
depends on this honor-system layer. Mechanically proving
temporal order requires either a stash-and-replay hook
(filesystem-state manipulation, fragile) or an
amend-pattern-with-checksum approach (commit-state
manipulation, robust because git already tracks it).

**Issue 3 — no path to v1.0.0 versioning.** PROPOSAL.md
§"Versioning" (line 1713) describes spec versioning under
`SPECIFICATION/history/vNNN/`. It does not describe
livespec-the-software's version cadence. The Phase 10 plan
goal is to land a `v1.0.0` git tag (per Plan §"Phase 10 —
Verify the v1 Definition of Done", line 3125), but commits
today use `phase-N: cycle N — ...` prefixes that carry no
version-derivation signal. Conventional Commits +
semantic-release is the canonical machine-parseable format;
adopting it at the v034-codification boundary lets the entire
post-v034 history drive automatic versioning + changelog
generation by the time v1 ships, rather than retro-fitting at
Phase 10.

The remedy is a coordinated v034 revision covering eight
decisions:

- **D1** Conventional Commits + semantic-release adoption.
- **D2** TDD-Red/Green trailer schema for structured proof.
- **D3** Replay-based enforcement contract (amend pattern +
  pre-commit hook semantics).
- **D4** `git notes` as operational cache (advisory layer;
  never load-bearing for invariant checks).
- **D5** Plan-text edits + `dev-tooling/checks/` enumeration
  housekeeping for D1-D4.
- **D6** Baseline mechanism
  (`phase-5-deferred-violations.toml`) carving out existing
  violations from the full-scope local aggregate; drains
  per-fix; deletes when empty.
- **D7** Drain step authorization: a new Phase 5 sub-section
  §"Aggregate-restoration drain" bracketing the cycles that
  fix the four unbound targets (and the two config-tier
  targets) under the new D1-D5 discipline.
- **D8** Branch protection on `master` + PR-based workflow.
  Codified in PROPOSAL §"CI workflow" with explicit
  deferred-activation: the `gh api` call to enable the rule
  runs as the final sub-step of Phase 5 (after the Phase-5
  exit gate passes), so Phase 6 onward operates under
  protected master.

Pre-v034-codification commits are grandfathered (no
retroactive reformatting). The codification commit itself is
the first commit under the new convention.

## Decisions captured in v034

### D1 — Adopt Conventional Commits + semantic-release

**Decision.** All commits from v034 codification onward use
the Conventional Commits 1.0 format: `<type>[optional
scope][!]: <description>` for the subject line; an optional
body separated by a blank line; optional footer trailers in
`Token: value` form (one per line, separated from the body by
a blank line). Recognized types: `feat`, `fix`, `refactor`,
`perf`, `test`, `chore`, `docs`, `build`, `ci`, `style`,
`revert`. Breaking changes are marked with `!` after the
type/scope and a `BREAKING CHANGE:` trailer. Semantic-release
(specific tool selection deferred to Phase 9) consumes the
commit history to derive version numbers (`feat:` → minor;
`fix:` → patch; `BREAKING CHANGE:` → major). The `v1.0.0`
tag at Phase 10 exit is the first auto-derived release;
pre-v1 commits drive future changelog generation but trigger
no automatic version bumps.

**Rationale.** Three drivers. First, the existing `phase-N:
cycle N — ...` prose carries no machine-parseable signal —
it cannot drive automatic versioning, changelog generation,
or breaking-change detection. Conventional Commits is the
canonical solution; tooling (commitlint, semantic-release,
conventional-changelog) is mature. Second, the type prefix
cleanly scopes TDD-replay enforcement (D3): only `feat:` and
`fix:` commits require Red/Green trailers; `refactor:`,
`chore:`, `docs:`, `build:`, `ci:`, `style:`, `test:`,
`perf:` skip TDD enforcement (no new behavior introduced).
The marker-scoping problem dissolves. Third, livespec's
Phase 10 goal of cutting a v1.0.0 tag is best served by
automatic version derivation rather than manual semver
bumps; getting the convention in place at v034 means the
entire post-v034 history is changelog-ready by the time v1
ships.

**Cutover boundary.** Hard cutover at the v034 codification
commit. That commit's own message is the first conventional
commit: `chore!: codify v034 — TDD-replay, conventional-
commits, drain authorization`. Pre-v034 commits are
grandfathered: commitlint configured to skip any commit
whose ancestor SHA precedes the v034 codification commit;
only post-cutover commits are linted.

**Source-doc impact.**

- PROPOSAL.md: NEW top-level section §"Commit conventions
  and versioning" between §"Versioning" (line 1713) and
  §"Pruning history" (line 1753) describing the format, type
  set, breaking-change marking, semantic-release derivation
  rules, and the grandfather boundary.

**Plan-text impact.**

- §"Version basis" preamble: add v034 D1 decision summary
  block.
- Phase 0 step 1 byte-identity check: bump reference to
  v034.
- Phase 0 step 2 frozen-status: bump to "Frozen at v034".
- Execution-prompt block: bump authoritative-version line to
  v034.
- New plan housekeeping bullet at Phase 5 §"Aggregate-
  restoration drain" entry: post-codification commits use
  Conventional Commits format; pre-codification commits
  grandfathered.

**Companion-doc impact.** None. The style doc governs Python
authoring, not commit format.

### D2 — TDD-Red/Green trailer schema

**Decision.** Replace the v033 `## Red output` honor-system
content rule with a structured trailer schema in the commit
message footer. Trailers (per RFC 822-style `Token: value`
parseable by `git interpret-trailers --parse`) are added to
`feat:` and `fix:` commits at the Green amend boundary.
Schema (one trailer per line; all fields required for
`feat:`/`fix:` commits):

```
TDD-Red-Test: <pytest-node-id>
TDD-Red-Failure-Reason: <one-line failure summary>
TDD-Red-Test-File-Checksum: sha256:<hex>
TDD-Red-Output-Checksum: sha256:<hex>
TDD-Red-Captured-At: <UTC ISO 8601>
TDD-Green-Verified-At: <UTC ISO 8601>
TDD-Green-Parent-Reflog: <pre-amend SHA>
```

The captured pytest failure output continues to live in the
commit body as a fenced `## Red output` block (preserved for
human readability via `git log`); `TDD-Red-Output-Checksum`
is the SHA-256 of that block, allowing the hook to detect
tamper without parsing pytest's volatile formatting (which
includes timestamps, paths, and version-specific layout).
`TDD-Red-Test-File-Checksum` is the SHA-256 of the test
file's content as it was at the Red moment; the Green amend
must not alter the test file (verified by recomputing the
checksum at amend time).

**Rationale.** Trailers are a git-native convention with
mature tooling support. They survive rebase, cherry-pick,
and squash. They are distinct from prose body content, so
the hook can reliably parse them without ambiguity. The
checksum fields make tamper detection mechanical: a bad
actor cannot fabricate a Red moment by hand-writing a
plausible failure block, because the trailers anchor the
content cryptographically and the reflog (D3) anchors the
temporal order.

**Required-vs-skipped by commit type.**

| Type | Trailers required? |
|---|---|
| `feat`, `fix` | Yes (full schema mandatory) |
| `refactor`, `perf` | No (must NOT add new failing tests; existing tests stay green) |
| `chore`, `docs`, `build`, `ci`, `style` | No (config/meta) |
| `test` | No (rare; characterization-test corrections only; if a `test:` commit introduces a new behavior expectation, it should be `feat:` instead) |
| `revert` | No (mirrors the reverted commit's type) |

**Source-doc impact.**

- PROPOSAL.md §"Test-Driven Development discipline" §"The
  internal authoring cycle (Red → Green)" (line 3157):
  update step 2 ("Green") to describe the amend-and-add-
  trailers pattern; reference D3 for the hook contract.
- PROPOSAL.md §"Testing approach" §"Activation" (line
  3406): replace the existing `## Red output` honor-system
  reference with the trailer-based contract; cross-
  reference D3.

**Plan-text impact.**

- Phase 5 §"Per-commit Red-output discipline (v032 D4 /
  v033 D4)" (line 2151): rename to §"Per-commit Red→Green
  replay discipline (v034 D2-D3)"; rewrite body to describe
  the trailer schema + hook contract; reference the new
  `dev-tooling/checks/red_green_replay.py` (D5).

**Companion-doc impact.**

- `python-skill-script-style-requirements.md` §"Canonical
  target list": rename `check-red-output-in-commit` to
  `check-red-green-replay` and update its rule wording.

### D3 — Replay-based enforcement contract

**Decision.** A new pre-commit check, `dev-tooling/checks/
red_green_replay.py`, mechanically verifies the temporal
Red→Green order via the amend pattern. Workflow:

1. **Red commit (initial).** Author writes the failing test,
   stages it (test files only — no implementation), runs
   `git commit` with a `feat:` or `fix:` subject line. The
   pre-commit hook detects this is a Red commit (test files
   staged but no impl files; `feat:`/`fix:` type). It
   computes the test file's SHA-256, runs the listed test
   (extracted from the commit message body or a candidate
   `TDD-Red-Test:` trailer), expects non-zero exit code +
   the test's pytest node-id appearing in the failure
   summary (NOT verbatim output equality, which is fragile
   per pytest version). On success, it writes the trailers
   into the commit message via `git interpret-trailers
   --in-place --trailer ...` and lets the commit land. The
   working tree at this point has a Red commit on the
   current branch.

2. **Green amend.** Author writes the implementation, stages
   it (impl files; the test file MUST NOT be re-staged or
   modified). Runs `git commit --amend`. The hook detects
   this is an amend by inspecting `HEAD~0`'s message — if it
   carries Red trailers, this is a Green amend. The hook
   recomputes the test file SHA-256 from the staged tree;
   compares against `TDD-Red-Test-File-Checksum`; rejects if
   different. Runs the listed test; expects exit zero. On
   success, adds the `TDD-Green-Verified-At:` and
   `TDD-Green-Parent-Reflog:` trailers (the latter is the
   pre-amend HEAD SHA, recorded so the Green commit
   structurally references the Red moment in reflog).

3. **Anti-cheat.** Bad actor attempts to skip the Red
   commit and produce a single commit with hand-faked
   trailers. The hook detects this via reflog inspection:
   if `TDD-Green-Parent-Reflog` references a SHA that
   either (a) does not appear in the local reflog, or (b)
   appears but does not carry a Red marker + matching
   checksum, the commit is rejected. Since reflog is local-
   only and not pushed, server-side verification falls back
   to mutation testing (`check-mutation`) as a vacuity check
   — but local enforcement is mechanically airtight for any
   commit authored on a development machine running the
   hook.

4. **Failure-mode quality.** "Test failed for the right
   reason" (assertion vs. ImportError/SyntaxError) is hard
   to mechanize fully. The hook applies a 90% heuristic:
   uses `pytest --collect-only` to detect collection-time
   errors (rejected as "test not at Red — fix collection
   first"); accepts any non-zero pytest exit code where the
   test's node-id appears in the short summary. Edge cases
   (test errors mid-body via `RuntimeError` rather than
   `AssertionError`) are accepted; mutation testing catches
   the residual "tests are vacuous" case.

**Rationale.** The amend pattern moves the proof-of-
temporal-order from filesystem state (where stash-and-replay
was fragile) into git state (which git already tracks). No
broken commits land on master: only the post-amend commit
with both Red and Green trailers is what gets pushed. The
checksum-bound test file content prevents the implementer
from tweaking the test to fit. The reflog-bound parent SHA
prevents fabrication. Pytest output volatility is sidestepped
by checksumming the captured output rather than comparing
verbatim.

**Source-doc impact.**

- PROPOSAL.md §"Testing approach" §"Activation" (line
  3406): replace the v033 D4 honor-system reference with
  the v034 D2-D3 replay contract; cross-reference the new
  `dev-tooling/checks/red_green_replay.py`.

**Plan-text impact.**

- Phase 5 §"Per-commit Red→Green replay discipline (v034
  D2-D3)" (renamed per D2): describe the hook's three
  workflow stages, the anti-cheat reflog check, and the
  90%-heuristic for failure-mode quality.

**Companion-doc impact.**

- `python-skill-script-style-requirements.md` §"Enforcement
  suite — Canonical target list": replace
  `check-red-output-in-commit` rule with
  `check-red-green-replay`; update rule wording.

### D4 — Git notes as operational cache

**Decision.** `refs/notes/commits` is the designated
operational-cache namespace for execution metadata that does
NOT belong in commit messages. Examples: cached pytest
output for fast replay, cached mutation-testing scores, CI
status snapshots. Notes are never load-bearing for invariant
checks — the source of truth for any TDD or coverage claim is
the commit message itself (trailers + body). The hook
decisions read trailers; if notes disappear, fork, or
diverge, no invariant breaks.

**Replication.** Notes do not push/fetch by default. The
v034 plan adds a one-time `git config --add remote.origin.fetch
"+refs/notes/*:refs/notes/*"` step to the `just bootstrap`
recipe so notes survive across machines. Pushing notes uses
`git push origin "refs/notes/*"` explicitly; the hook does
NOT auto-push notes (push remains manual or scheduled).

**Rationale.** Some execution metadata is too verbose for
commit bodies (full pytest --verbose output, multi-megabyte
mutation reports) or too volatile (cache scores that change
per CI run). Putting it in commit messages bloats `git log`
and rebases; putting it in notes keeps `git log` clean while
still letting tools cache progress. The "advisory only"
constraint is the safety property: nothing in the discipline
fails open when notes are absent.

**Source-doc impact.**

- PROPOSAL.md NEW short sub-section §"Git notes as
  operational cache" under §"Developer tooling layout"
  (line 3785) describing the namespace, replication config,
  and "never load-bearing" invariant.

**Plan-text impact.**

- Phase 1: add a `git config` step to the `bootstrap`
  recipe authoring sub-step for the notes refspec.

**Companion-doc impact.** None.

### D5 — Plan-text and dev-tooling enumeration housekeeping

**Decision.** Three housekeeping changes flow from D1-D4:

1. New `dev-tooling/checks/red_green_replay.py` added to
   the canonical enforcement-script enumeration. Replaces
   `dev-tooling/checks/red_output_in_commit.py` (the v033
   D4 script). The replacement check incorporates the v033
   D4 contract (hard-gate `## Red output` block presence)
   plus the new D2-D3 trailer + replay verification.

2. `lefthook.yml` pre-commit ordering updated:
   `check-red-green-replay` (cheap header-parsing + amend-
   detection) runs before `check-commit-pairs-source-and-
   test` (also cheap) before `check` (expensive aggregate).

3. Phase 5 sub-section §"Per-commit Red-output discipline
   (v032 D4 / v033 D4)" renamed to §"Per-commit Red→Green
   replay discipline (v034 D2-D3)" with rewritten body.

**Rationale.** Housekeeping. No new architectural decisions;
just the literal plan-text and tooling-config edits that
D1-D4 require.

**Source-doc impact.**

- PROPOSAL.md `dev-tooling/checks/` directory listing
  (line 3496-3520): replace `red_output_in_commit.py` with
  `red_green_replay.py`.

**Plan-text impact.**

- Phase 4 enforcement-script enumeration: replace
  `red_output_in_commit.py` with `red_green_replay.py`.
- Phase 5 §"Per-commit Red→Green replay discipline":
  rewritten body per D2-D3.

**Companion-doc impact.**

- `python-skill-script-style-requirements.md` §"Canonical
  target list": rename target as in D3.

### D6 — Baseline mechanism for currently-failing checks

**Decision.** A new file at `<repo-root>/phase-5-deferred-
violations.toml` enumerates every currently-failing
violation that is grandfathered during the drain phase.
Schema:

```toml
[[violation]]
target = "check-complexity"
file = ".claude-plugin/scripts/livespec/commands/seed.py"
rule = "PLR2004"
location = "186:39"
note = "magic value 2; fix in seed.py refactor cycle"

[[violation]]
target = "check-newtype-domain-primitives"
file = ".claude-plugin/scripts/livespec/types.py"
rule = "module-missing"
location = ""
note = "create types.py with NewType definitions; replace 4 raw-str fields"
```

The local pre-commit hook runs the FULL canonical-target
list (not the v033-thinned aggregate). Each check loads the
baseline and skips violations whose `(target, file, rule,
location)` tuple matches an entry. NEW violations
(violations not in the baseline) fail the hook
unconditionally. Each drain cycle that fixes a violation
ALSO removes the matching baseline entry in the same commit.
When the baseline file is empty (zero `[[violation]]`
entries), it is deleted from the tree; the absence of the
file means full-scope-no-grandfather is in effect.

The thinned `just check` aggregate at `justfile:75-99` is
removed. The check recipe runs the full canonical target
list against the baseline; the existing transitional
comment (lines 55-74) is replaced with a reference to D6
+ the baseline file.

**Rationale.** Three improvements over the v033 thinned-
aggregate transition. First, structured artifact: a TOML
file is parseable and auditable; the justfile comment was
20 lines of prose. Second, mechanical NEW-vs-OLD distinction:
the local hook blocks any new violation regardless of which
target it triggers, while drain cycles unblock by both
fixing AND removing the baseline entry in the same commit.
Third, atomic transition: when the baseline file empties +
deletes, full enforcement is mechanically live from that
commit forward — no manual justfile widening, no "did I
forget to update the aggregate" risk.

**Source-doc impact.**

- PROPOSAL.md §"Developer tooling layout" (line 3785):
  add NEW sub-section §"Baseline-grandfathered violations"
  describing the schema, hook-integration semantics, and
  lifecycle (created at v034 codification with current
  violations; drains per fix; deleted when empty).

**Plan-text impact.**

- Phase 5 NEW sub-section §"Aggregate-restoration drain"
  (D7): references the baseline file as the drain target.
- Phase 1: add `phase-5-deferred-violations.toml` to the
  initial-file-creation sub-step (or note it's authored at
  the v034 codification commit).
- Replace the thinned-aggregate note in `justfile:55-74`
  with a one-line reference to D6 + the baseline file.

**Companion-doc impact.**

- `python-skill-script-style-requirements.md` §"Enforcement
  suite — Invocation surfaces": add reference to the
  baseline file's role.

### D7 — Drain step authorization

**Decision.** Phase 5 gains a NEW sub-section §"Aggregate-
restoration drain" placed AFTER §"Per-commit Red→Green
replay discipline (v034 D2-D3)" and BEFORE §"Quality-
comparison report — v033 D5c scope expansion" (the v033 D5c
report is renamed v034 D5c with the same scope).

The drain step bracket: entry condition is the first cycle
after the v034 codification commit + replay-hook authoring
sub-cycles complete. Exit condition is `phase-5-deferred-
violations.toml` is empty AND deleted. Each drain cycle:

- Targets one or more violations from the baseline.
- Authors fixes under the new D1-D5 discipline (Conventional
  Commits + TDD-Red/Green trailers + replay verification).
- Removes the resolved baseline entries in the same commit.
- The Conventional Commit type is `feat:` (when fixing a
  violation introduces NEW code paths under test, e.g.,
  creating `livespec/types.py`) or `fix:` (when fixing a
  violation only adjusts existing code, e.g., refactoring
  `seed.py` to drop below 200 LLOC).

The drain subsumes what was previously called "Batch 7" in
STATUS.md prose. There is no "rest of the redo" beyond the
drain — once the baseline empties, the only remaining work
is the v034 D5c quality-comparison report and the Phase 5
exit gates.

**Estimated cycles:** ~11-15 cycles total (~1-2 for PBT
decorators; ~2-3 for `types.py` + NewType migration; ~5 for
schema/dataclass triples; ~3-5 for `seed.py` refactor +
remaining ruff PLR/C90 fixes; ~2-3 for config-tier cleanup
of `check-lint`/`check-format`).

**Rationale.** Without an explicit drain bracket, the gap-
filling work would proceed under ambient discipline — risk
of forgetting which violations were grandfathered, which
were fixed, and when full-scope went live. The bracket
gives the executor a clean entry/exit boundary AND makes
"how much is left" mechanically visible (count of
`[[violation]]` entries in the baseline file).

**Source-doc impact.** None directly. The drain is a Plan
construct; PROPOSAL describes the steady-state, not the
transition.

**Plan-text impact.**

- Phase 5 NEW sub-section §"Aggregate-restoration drain"
  with the entry/exit conditions, per-cycle workflow, and
  estimated-cycle range.
- Phase 5 §"Quality-comparison report — v033 D5c scope
  expansion" renamed §"Quality-comparison report — v034
  D5c scope" with one-line addition: report runs against
  the post-drain tree.

**Companion-doc impact.** None.

### D8 — Branch protection on master + PR-based workflow

**Decision.** A GitHub branch protection rule on `master`
requires (a) all CI matrix jobs pass before merge, (b)
linear history (no merge commits — PRs land via squash or
rebase), (c) no direct pushes to master (all changes via
PR). Solo-dev workflow: agent opens PR with auto-merge
enabled (`gh pr create --fill && gh pr merge --auto
--squash`); GitHub merges automatically when CI is green.
User retains manual override (manual `gh pr merge` or
`gh pr review` if desired).

**Activation boundary.** Deferred to the FINAL sub-step of
Phase 5, AFTER the Phase 5 exit gate passes. Concrete
sequencing:

1. v034 codification commit (this revision lands).
2. Replay-hook authoring sub-cycles (under existing v033
   discipline; the new hook isn't gating yet).
3. Replay-hook activation commit (lefthook.yml updated;
   D1-D5 fully in force from this point).
4. Drain step (D7): cycles fix violations under new
   discipline; baseline drains to empty.
5. v034 D5c quality-comparison report authored.
6. Phase 5 exit gates: 5a drift-review → 5b exit-criterion
   check → 5c advance-to-Phase-6 confirmation.
7. **D8 activation sub-step (NEW):** invoke `gh api -X PUT
   repos/:owner/:repo/branches/master/protection ...` to
   enable the rule; verify direct push is rejected by
   making a trivial test push that fails as expected;
   verify PR + auto-merge path works on a trivial test PR.
8. Phase 6 begins under protected master.

**Rationale.** D6 (baseline mechanism) closes the broken-
pushes problem locally for any commit authored on a
development machine running the hook. D8 closes the residual
risk of environment divergence (local Python/tool versions
≠ CI's) AND prevents bypass via `--no-verify`. Activating
at end-of-Phase-5 means D6 has had the entire drain to
prove out (any local-passes-CI-fails divergence surfaces
during the drain, where it's cheap to fix); Phase 6 onward
operates under full protection without the bootstrap-mode
risk of a misconfigured hook bricking commits.

**CI cost.** Roughly 2x current CI usage (PR push + master
merge push each trigger CI). At ~1.5 min per matrix run,
~3 min per cycle wall-clock added; for 15 drain cycles +
ongoing post-Phase-5 cycles, this is ~45 min of CI per
phase — well under the GitHub Free tier 2000-min/month
budget for private repos, and unlimited for public.

**Source-doc impact.**

- PROPOSAL.md NEW sub-section §"CI workflow" under
  §"Developer tooling layout" (line 3785): describes the
  branch protection rule, the auto-merge convention, and
  the deferred-activation boundary at end-of-Phase-5.

**Plan-text impact.**

- Phase 5: NEW final sub-step at end of phase (after 5c
  advance gate) authorizing the `gh api` invocation +
  verification.
- Phase 6 onward: replace any direct-push references with
  PR + auto-merge wording.

**Companion-doc impact.** None.

## Activation sequencing summary

For convenience, the order of operations after this v034
revision lands:

| Step | Description | Discipline in force |
|---|---|---|
| 1 | v034 codification commit | Last `phase-N: ...` style commit; first conventional commit `chore!: codify v034` |
| 2 | Replay-hook authoring sub-cycles | v033 discipline (existing `## Red output` honor system) |
| 3 | Replay-hook activation commit | v034 D1-D5 in force; D6 baseline file authored with current violations |
| 4 | Drain step (D7) | Full v034 discipline (TDD-replay + Conventional Commits + baseline grandfather) |
| 5 | v034 D5c quality-comparison report | Full v034 discipline |
| 6 | Phase 5 exit gates (5a/5b/5c) | Full v034 discipline |
| 7 | D8 branch protection activation | Final Phase 5 sub-step |
| 8 | Phase 6 onward | Full v034 + D8 protected master |

## Open items deferred to later revisions

- **Specific semantic-release tool selection** (semantic-
  release/semantic-release vs. cocogitto vs. release-please):
  deferred to Phase 9 alongside the e2e test work. The v034
  decision commits to the convention; tool selection is
  configuration-tier and not load-bearing for the discipline.
- **Commitlint configuration file shape**: deferred to the
  D5 implementation cycles. The v034 decision commits to
  the rule set; the .commitlintrc file is authored when the
  hook integration lands.
- **Semantic-release workflow trigger** (push-to-master vs.
  manual tag vs. scheduled): deferred to Phase 10 alongside
  the v1.0.0 tagging decision.
