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
- **v007** — revise driven by
  `proposed_changes/proposal-critique-v06.md` and its revision.
  A **defect critique with grounded research**, surfacing
  integration gaps the v005→v006 language migration left in
  PROPOSAL.md and `python-skill-script-style-requirements.md`.
  18 items (G1-G18) labelled with the NLSpec failure-mode
  framework (ambiguity / malformation / incompleteness /
  incorrectness). Major structural changes:
  **Per-sub-command skill structure** — restructured from a
  single `livespec` skill with internal `commands/` to one skill
  per sub-command (`/livespec:seed`, `/livespec:doctor`, etc.).
  Driven by Claude Code plugin invocation rules (research via
  claude-code-guide agent confirmed plugin skills MUST be
  namespaced `/<plugin>:<skill>` with no nested subcommand
  syntax). Each skill carries its own scoped `description`,
  `allowed-tools`, and (where applicable)
  `disable-model-invocation` frontmatter. Shared scripts move
  to plugin root: `.claude-plugin/scripts/`.
  **Sub-command lifecycle orchestration as ROP chain** — new
  PROPOSAL.md section codifying that the Python wrapper's
  `livespec.commands.<cmd>.main()` composes pre-step doctor
  static + sub-command logic + post-step doctor static as one
  ROP chain. The post-step LLM-driven phase runs from skill
  prose AFTER the wrapper exits. `--skip-pre-check` is
  wrapper-parsed; `--skip-subjective-checks` is an LLM-layer flag
  that never reaches Python.
  **Shared `bin/_bootstrap.py`** — extracts sys.path setup +
  Python version check into one shared module (~15 LOC) called
  by every wrapper's `bootstrap()`. Each `bin/<cmd>.py` is now
  a deterministic 6-line shape; `check-wrapper-shape` updated
  to match. `__init__.py` no longer raises (resolves the
  malformation between version-check raise and
  `check-no-raise-outside-io`).
  **Static check registry** — `livespec/doctor/static/__init__.py`
  imports every check by name and re-exports `(SLUG, run)` tuples.
  Adding/removing a check is one explicit registry edit. The
  v005-era "check insert/delete is a non-event" invariant is
  dropped (preferred static enumeration over dynamic discovery
  for the strongest possible guardrails). Pyright strict can fully
  type-check the orchestrator.
  **Factory-shape validators** — `validate/<name>.py` modules
  expose `validate_<name>(payload, schema) -> Result[...]`
  taking the schema dict as a parameter. `io/` reads the schema;
  `validate/` stays strictly pure. Resolves the malformation
  between purity-by-directory and "validate/ uses fastjsonschema
  loaded from schemas/".
  **Restricted-YAML front-matter parser** — hand-rolled at
  `livespec/parse/front_matter.py` (deferred to first-batch
  propose-change). Front-matter values restricted to JSON-
  compatible scalars; no nesting, no anchors. Codified in
  PROPOSAL.md so the parser stays narrow forever.
  **Vendored libs: drop check-vendor-audit, pin versions** —
  vendoring discipline reduces to (1) pinned version recorded in
  `.vendor.toml`, (2) no edits to `_vendor/`, (3) re-vendoring
  only via `just vendor-update <lib>`. The audit script and its
  schema-spec ambiguity are removed entirely; code review and
  git diff visibility cover the threat model.
  **Typed facades for vendored libs under `livespec/io/`** —
  `fastjsonschema_facade.py`, `structlog_facade.py`, and
  (conditionally) `returns_facade.py` confine `Any` and
  `# type: ignore` to a small audited surface. Pyright config
  excludes `_vendor/**` from strict mode.
  **Doctor exit-code derivation codified** — supervisor maps
  `IOFailure(err)` → `err.exit_code`; `IOSuccess(report)` + any
  `status:fail` finding → exit 3; otherwise exit 0;
  `status:skipped` never causes a fail exit.
  **CLAUDE.md coverage canonicalized** to `scripts/` + `tests/`
  + `dev-tooling/` with `_vendor/` and its entire subtree
  explicitly excluded. Resolves five-way disagreement across docs.
  **`just bootstrap`** target added for first-time setup
  (`lefthook install` + any other one-time setup); `just check`
  documented as continue-on-failure with aggregated exit.
  **Structlog config exemption documented** for `__init__.py`'s
  one-time `configure(...)` and `bind_contextvars(run_id=...)`
  calls.
  **New `deferred-items.md` companion** in the brainstorming
  folder — canonical tracking list for items deferred to
  first-batch propose-changes after seed. Each entry has a
  stable id, target spec file(s), and how-to-resolve paragraph.
  Future revisions MUST keep it authoritative; removals require
  explicit explanation. Bootstrapped from v006's `Self-application`
  list plus three new entries (`ast-check-semantics`,
  `returns-pyright-plugin-disposition`, `front-matter-parser`).
  **Documented "no `bin/doctor.py`" asymmetry** — `livespec
  doctor` has no Python wrapper for the LLM-driven phase;
  invocation is `bin/doctor_static.py` + skill prose.
  **Propose-change/critique LLM-vs-wrapper split made explicit**
  — `bin/propose_change.py` only accepts `--findings-json`;
  the freeform `<intent>` path is LLM-driven (LLM invokes
  template prompt, validates output, passes JSON to wrapper).
  Full decision record is in
  `v007/proposed_changes/proposal-critique-v06-revision.md`.

- **v008** — revise driven by
  `proposed_changes/proposal-critique-v07.md` and its revision.
  A **defect critique with grounded recreatability review**,
  surfacing 16 integration gaps (H1-H16) labelled with the NLSpec
  failure-mode framework (ambiguity / malformation /
  incompleteness / incorrectness). Two mid-interview corrections
  materially reshaped items: H5's arg-count gate (user pushback
  inverted the v006 P9 "no positional-arg limit" decision into
  mechanical `PLR0913 + PLR0917` enforcement at 6), and H11's
  out-of-band-edits cycle (user's "how is that non-destructive?"
  question surfaced the need for an explicit pre-backfill guard).
  Major structural changes:
  **Bootstrap sys.path fix** — `bin/_bootstrap.py` now inserts
  BOTH `scripts/` and `scripts/_vendor/` into `sys.path`; v007's
  single-path bootstrap would have left every vendored-lib
  import unresolvable.
  **JSONC parser vendored** — `jsoncomment` (MIT) added as the
  fourth vendored library. `scripts/livespec/parse/jsonc.py` is a
  thin pure wrapper. PROPOSAL.md's `.livespec.jsonc` section
  codifies the JSONC dialect (JSON + `//` and `/* ... */`
  comments; no JSON5 extras).
  **CLI argument-parsing seam** — argparse lives in
  `livespec/io/cli.py`, wrapped with `@impure_safe` and
  `exit_on_error=False`; `livespec/commands/<cmd>.py` exposes a
  pure `build_parser()` factory. `IOFailure(UsageError)` → exit
  `2` via the railway. `check-supervisor-discipline` scope
  narrowed: `livespec/**` in scope; `bin/*.py` sole exempt
  subtree.
  **Per-sub-command SKILL.md body structure** — PROPOSAL.md
  codifies the canonical body shape (opening, when-to-invoke,
  inputs, ordered steps, post-wrapper, failure handling); actual
  per-sub-command content deferred via new
  `skill-md-prose-authoring` entry in `deferred-items.md`.
  **Mechanical refactor-to-dataclass enforcement at 7+ args** —
  `max-args = 6` AND `max-positional-args = 6` (ruff `PLR0913` +
  `PLR0917`), reversing v006 P9. Functions needing more
  parameters MUST refactor to accept a dataclass.
  **Explicit seed / revise wrapper input contracts** —
  `bin/seed.py --seed-json` with `seed_input.schema.json`;
  `bin/revise.py --revise-json` with `revise_input.schema.json`.
  The v007 "or equivalent entry path" hedging is removed.
  **Context dataclass field sets codified** — Style doc lists
  minimum fields for `DoctorContext`, `SeedContext`,
  `ProposeChangeContext`, `CritiqueContext`, `ReviseContext`,
  `PruneHistoryContext`.
  **`doctor` allowed-tools honesty** — `Bash + Read + Write`
  (the static phase writes under the `out-of-band-edits`
  auto-backfill path). "Read-only validation" phrasing dropped.
  **Factory-validator cache relocation** — The
  `fastjsonschema.compile` cache moves to
  `livespec/io/fastjsonschema_facade.py` (impure boundary).
  `validate/` stays strictly pure. Cache added to the
  documented `check-global-writes` exemption list alongside
  `structlog.configure` and
  `structlog.contextvars.bind_contextvars`.
  **Findings-schema split** — `doctor_findings.schema.json`
  (doctor static-phase output: `check_id/status/message/path/line`)
  vs `proposal_findings.schema.json` (renamed from
  `critique_findings.schema.json`; propose-change/critique
  template output with `name/target_spec_files/summary/
  motivation/proposed_changes`). One-to-one field-copy mapping
  from proposal findings to `## Proposal` sections.
  **Out-of-band-edits pre-backfill guard** — HEAD-to-HEAD
  comparison plus a guard: if uncommitted
  `SPECIFICATION/history/v(N+1)/` or stale
  `out-of-band-edit-*.md` is on disk, the check emits "commit
  existing backfill and re-run" without repeating the backfill.
  Non-destructive via explicit detection.
  **Skill-owned directory-README paragraphs frozen verbatim** in
  PROPOSAL.md for `SPECIFICATION/proposed_changes/README.md` and
  `SPECIFICATION/history/README.md`.
  **Static-check-semantics deferred item** — Renamed from v007
  `ast-check-semantics`; widened to cover markdown-parsing checks
  (bcp14 typo list, GFM anchor-slug algorithm edge cases),
  doctor-cycle semantics (pre-backfill guard details), and
  argparse `SystemExit` disposition under supervisor-discipline.
  **Anchor-reference-resolution GFM algorithm** codified in
  PROPOSAL.md: lowercase; spaces → hyphens; punctuation stripped
  except `-` and `_`; collapse multi-hyphens; fenced-block
  headings excluded; no `{#custom-id}` in v1.
  **`tests/fixtures/` carve-out** from `check-claude-md-coverage`
  alongside the existing `_vendor/` carve-out.
  **Canonical seed auto-capture content** frozen in PROPOSAL.md:
  Target-spec-files = written paths; Summary = canonical one-liner;
  Motivation = verbatim intent; Proposed Changes = verbatim intent.
  **Two new deferred-items entries:**
  `skill-md-prose-authoring` (v008 H4) and `wrapper-input-schemas`
  (v008 H6 + H10 — includes the `proposal_findings` rename and
  the new `doctor_findings`, `seed_input`, `revise_input`
  schemas). `ast-check-semantics` renamed to
  `static-check-semantics` with widened scope. Full decision
  record is in
  `v008/proposed_changes/proposal-critique-v07-revision.md`.

## Pointer

The current working `PROPOSAL.md` lives at the parent directory
(`brainstorming/approach-2-nlspec-based/PROPOSAL.md`). It is
byte-identical to `history/v008/PROPOSAL.md` until the next revise.
