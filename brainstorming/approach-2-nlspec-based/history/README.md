# history

Versioned snapshots of the (pre-seed) `PROPOSAL.md` plus every proposed
change and revision that produced each version. This directory is
backfilled by hand to mirror what `livespec`'s own `history/`
mechanism would have produced if it had existed at the time these
revisions were made.

## Filename convention

Two filename conventions appear here, reflecting a rule change in
v003. The v003 revision dropped the `vNNN-` prefix from files inside
`history/vNNN/` to preserve relative markdown links under the parallel
`proposed_changes/` subdirectory structure. Historic v001 and v002
entries keep their original naming (immutable history).

**v001 and v002 (legacy naming, retained unchanged):**

- `vNNN/vNNN-PROPOSAL.md` — frozen copy of the working proposal.
- `vNNN/vNNN-proposed-change-<topic>.md` — a proposed change
  processed by the revise that cut this version.
- `vNNN/vNNN-proposed-change-<topic>-acknowledgement.md` — the
  paired decision record. (The term `acknowledgement` was renamed
  to `revision` in v003.)

**v003 and later (current naming):**

- `vNNN/PROPOSAL.md` — frozen copy of the working proposal.
- `vNNN/proposed_changes/<topic>.md` — a proposed change processed
  by the revise that cut this version.
- `vNNN/proposed_changes/<topic>-revision.md` — the paired
  revision decision record.
- Additional reference artifacts (pre-interview drafts, notes) MAY
  appear in `vNNN/proposed_changes/` with descriptive suffixes.

## Versions

- **v001** — initial proposal (commit `abba068`), seeded by hand
  before `livespec` existed. No proposed-change files; the `seed`
  step itself is not represented as a proposal under the model.
- **v002** — revise driven by `v002-proposed-change-proposal-
  critique-v01.md` and its acknowledgement, plus several follow-on
  in-conversation corrections that were absorbed into v002 rather
  than filed as separate proposals (gherkin-format change, holdout
  removal, doctor-warning removal, progressive-disclosure removal,
  filename rename `livespec-nlspec-guidelines.md` →
  `livespec-nlspec-spec.md`, etc.).
- **v003** — revise driven by
  `proposed_changes/proposal-critique-v02.md` and its revision.
  Restructures the proposal around: plugin packaging (not skill
  alone), Option 3 template architecture with custom templates in
  v1 scope, multi-proposal file format, rename
  `acknowledgement` → `revision`, rename `<freeform text>` →
  `<intent>` / `<revision-steering-intent>`, drop of `partition`
  term in favor of `specification file`, drop of `vNNN-` prefix
  inside history directories in favor of a parallel subdir layout,
  new `prune-history` sub-command with `PRUNED_HISTORY.json`
  marker, `jq` hard dependency, static-phase JSON output contract,
  objective/subjective split of doctor's LLM-driven phase with
  skip config and CLI flag, auto-backfill on check #9 drift
  detection, drop of `openspec` reservation, drop of
  `custom_critique_prompt` and `specification_dir` from
  `.livespec.jsonc`, and more. Full decision record is in
  `v003/proposed_changes/proposal-critique-v02-revision.md`.
- **v004** — revise driven by
  `proposed_changes/proposal-critique-v03.md` and its revision.
  Mid-interview, the user rewrote
  `bash-skill-script-style-requirements.md` to add module
  structure, purity/I/O isolation, complexity thresholds,
  testability, coverage, and architectural checks; four
  additional critique items (G22-G26) were appended to cover
  gaps between the rewritten style doc and PROPOSAL.md.
  Major structural changes: `schemas/` added to skill layout;
  `livespec-nlspec-spec.md` canonicalized at template root
  only; executables renamed (`dispatch`, `doctor-static` with
  no `.sh`); `scripts/bash-boilerplate.sh` added; `scripts/ci/`
  renamed to `scripts/checks/` in both PROPOSAL.md and the
  bash style doc; `prompts/propose-change.md` promoted to
  REQUIRED; `critique` uses internal delegation to
  `propose-change`; check #9 compares committed state
  (`git show HEAD:`) rather than working tree; doctor
  static-phase exit codes aligned to bash style doc (0/1/3);
  `plugin.json` delegated to Claude Code's current format;
  check #13 collapsed into #2 (now 12 static checks);
  `prune-history` preserves original-earliest across repeat
  prunes; `propose-change` drops content-shape sniffing in
  favor of `--findings-json` flag; `revise` orders files by
  `created_at` with whole-revise delegation scope;
  `<revision-steering-intent>` now forbids content injection;
  Testing section consolidated to name `bats-assert`,
  `bats-support`, `kcov` with coverage thresholds, and the
  `tests/` skeleton tree. Full decision record is in
  `v004/proposed_changes/proposal-critique-v03-revision.md`.
- **v005** — revise driven by
  `proposed_changes/proposal-critique-v04.md` and its revision.
  Critique focused specifically on
  `bash-skill-script-style-requirements.md` (the style doc) and
  its consequences for PROPOSAL.md — pragmatism,
  implementability, maintainability, and internal consistency.
  Major structural changes:
  **Runtime vs dev-time split** — `scripts/checks/` removed
  from the skill bundle; dev-time enforcement moves to
  `<repo-root>/dev-tooling/enforcement/` with `Makefile`,
  `.mise.toml`, `.pre-commit-config.yaml` at the repo root.
  `bash-boilerplate.sh` symlinked from `dev-tooling/`.
  **Single bash 3.2 standard** — the 4.4 floor is dropped;
  single uniform standard targets bash 3.2.57+ (macOS default
  `/bin/bash`). Bash 4.x features (namerefs, associative arrays,
  `mapfile`, `${var,,}`) forbidden; `"${arr[@]-}"` mandated for
  possibly-empty arrays under `nounset`. Boilerplate asserts
  bash version at load; exits 127 if too old.
  **Mise for tool pinning** — committed `.mise.toml` pins every
  external tool (bash=3.2.57, shellcheck, shfmt, shellharden,
  shellmetrics, kcov, bats-core, bats-assert, bats-support, jq,
  tree-sitter-bash). Scattered "MUST be pinned in CI" language
  collapses to the mise mandate.
  **Doctor-static decomposed** — `scripts/doctor-static`
  (monolithic) replaced by `scripts/doctor/run-static`
  (orchestrator) plus per-check executables at
  `scripts/doctor/static/<slug>`. Slug-only `check_id` format
  (`doctor-out-of-band-edits`, etc.) replaces positional numbers.
  Insert/delete of checks is a non-event.
  **Enforcement suite reframing** — invocation-surface-agnostic;
  every check is a Makefile target; pre-commit, pre-push, CI, and
  manual invocation are consumers. §"Enforcement via git hooks
  and CI" renamed §"Enforcement suite". Linux-only stated once.
  **Style-doc rule relaxations** — `main "$@"` final-line rule
  dropped in favor of sourceable guard (B1); CCN raised to ≤ 10,
  args to ≤ 6 (B4); `noclobber` dropped from mandatory strict
  mode (B5); `BASH_XTRACE`/`BASH_VERBOSE` renamed to
  `LIVESPEC_XTRACE`/`LIVESPEC_VERBOSE` (B6); `realpath` replaced
  with pure-bash `cd && pwd` (B7); pure-library env-var reads
  allow-listed (B8); `kcov` pure-library threshold ≥ 95% (B2);
  tree-sitter-bash named as parser for AST-level checks (B3);
  structured library header format mandated (B16); variadic
  mechanical definition (B15); stdin-routing checks permitted
  (B17). Full decision record is in
  `v005/proposed_changes/proposal-critique-v04-revision.md`.
- **v006** — revise driven by
  `proposed_changes/proposal-critique-v05.md` and its revision.
  A **language migration** pass (not a defect critique): bash
  replaced by Python 3.10+ as the implementation language for
  every skill-bundled script and every dev-tooling enforcement
  script. Motivating thesis: the v005 bash style doc grew to
  ~24 pages of rules compensating for features bash lacks
  (namespaces, import systems, data structures, a type system,
  AST access, test/coverage tooling); Python supplies those
  natively, shrinking the style doc and the enforcement
  toolchain. Major structural changes:
  **ROP-all-the-way-down** — vendored `dry-python/returns` for
  Result / IOResult / `@safe` / `@impure_safe` / `flow` / `bind`
  / `Fold.collect`. Every public function returns `Result` (pure)
  or `IOResult` (effectful). `sys.exit` only in shebang-wrapper
  supervisors; raises only at the `io/` boundary.
  **Type safety via pyright strict** (gating); ruff with strict
  rule selection (E F I B UP SIM C90 N RUF + PL + PTH) replaces
  shellcheck + shfmt + shellharden + shellmetrics; pytest +
  pytest-cov + pytest-icdiff replaces bats-core + bats-assert +
  bats-support + kcov.
  **Coverage raised to 100% line + branch everywhere** (pure/
  impure tier split retired with kcov; `# pragma: no cover —
  <reason>` the sole escape hatch, capped per file).
  **Complexity thresholds tightened** to Python density (CCN ≤ 10,
  func ≤ 30 LLOC, file ≤ 200 LLOC, nesting ≤ 4, no args limit,
  no waivers).
  **Vendored pure-Python libs** under `scripts/_vendor/`:
  `dry-python/returns` (BSD-2), `fastjsonschema` (MIT),
  `structlog` (BSD-2/MIT dual). `check-vendor-audit` target
  enforces drift detection against pinned upstream versions.
  **Per-command shebang wrappers** at `scripts/bin/*.py` (no
  top-level dispatcher, no bash stub, no per-check executables);
  single `bin/doctor_static.py` runs the whole static phase via
  one ROP chain composing per-check modules via `Fold.collect`.
  **Structural purity** enforced by directory (`parse/` and
  `validate/` pure, AST-checked; `io/` impure, `@impure_safe`).
  **Structured JSON logging** via `structlog` (JSON-only to
  stderr, `run_id` per invocation, kwargs-only style).
  **just task runner + lefthook hooks + GitHub Actions CI** with
  the invariant that `justfile` is the single source of truth
  for all dev-tooling invocations (`check-no-direct-tool-invocation`
  target enforces).
  **Per-directory `CLAUDE.md` coverage** across `scripts/`,
  `tests/`, and `dev-tooling/` (enforced by
  `check-claude-md-coverage`).
  **Retired artifacts:** `bash-skill-script-style-requirements.md`
  archived under `history/v006/retired-documents/` with README;
  `bash-boilerplate.sh` and its symlink deleted; `scripts/dispatch`
  (bash) removed; every bash-era enforcement tool (`shellcheck`,
  `shfmt`, `shellharden`, `shellmetrics`, `kcov`, `bats-*`,
  `tree-sitter-bash`, `jq` at runtime) retired. Full decision
  record is in
  `v006/proposed_changes/proposal-critique-v05-revision.md`.

## Pointer

The current working `PROPOSAL.md` lives at the parent directory
(`brainstorming/approach-2-nlspec-based/PROPOSAL.md`). It is
byte-identical to `history/v006/PROPOSAL.md` until the next revise.
