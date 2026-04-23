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

- **v009** — revise driven by
  `proposed_changes/proposal-critique-v08.md` and its revision.
  A **recreatability defect critique with discipline codification**,
  surfacing 14 items (I1-I14) plus one mid-interview meta-item (I0)
  labelled with the NLSpec failure-mode framework (ambiguity /
  malformation / incompleteness / incorrectness). User-driven
  reshapings this pass: I2 push (over-specification flagged) led to
  the new I0 meta-item; I10 push ("unrecoverable bugs shouldn't be
  handled via ROP track; only EXPECTED errors") led to full
  codification of a domain-vs-bugs error-handling discipline
  grounded in GitLab Remote Development's domain-message pattern.
  Major structural changes:
  **Architecture-vs-mechanism discipline codified** — new top-level
  section `Architecture-Level Constraints (Implementation
  Discipline)` added to `livespec-nlspec-spec.md` between §"Spec
  Economy" and §"Intentional vs. Accidental Ambiguity." The
  section names what's in scope for architecture-constrained
  specs (language deps, code-quality tooling, type-level
  public-API guarantees, structural boundaries enforced by
  checks, externally-visible invariants, inspected directory
  layouts) and what stays out (internal composition details,
  illustrative code as normative, non-public signatures,
  mechanism where an enforcement check already binds it). The
  discipline self-propagates: `livespec-nlspec-spec.md` is
  injected as reference context before every template-prompt
  invocation.
  **Error Handling Discipline codified** — new subsection under
  Architecture-Level Constraints distinguishing *domain errors*
  (expected: user input, environment, infra, timing; flow
  through Result/IOResult track) from *bugs* (unrecoverable
  programming errors; propagate as raised exceptions to the
  outermost supervisor bug-catcher). Inspired by GitLab Remote
  Development's "What types of errors should be handled as
  domain Messages?" pattern.
  **Python style doc consequences of the error discipline:**
  `DoctorInternalError` **retired** (a "bug" subclass on the
  domain hierarchy was a category confusion); `@safe` /
  `@impure_safe` rule tightened from blanket-catch to
  **targeted-catch** (MUST enumerate specific expected
  exception types); `check-no-raise-outside-io` narrows to
  restrict ONLY `LivespecError` subclasses (bug-class
  exceptions are permitted everywhere); new
  `check-no-except-outside-io` mirrors the narrowing for catch
  clauses; **every supervisor gains a top-level
  `try/except Exception` bug-catcher** (logs via structlog +
  returns 1); `assert` statements first-class for invariants;
  `LivespecError` hierarchy gains `ValidationError` and
  `GitUnavailableError`; the "returns None for side-effect
  boundary" supervisor exception rewritten to boundary-based
  exemption regardless of return type.
  **ROP composition illustrations backed off** — the style doc's
  illustrative `flow(ctx, run_static, bind(cmd_run),
  bind(run_static))` chain and `read_file / bind(parse_jsonc) /
  bind(validate_config)` mixed-monad example were mechanism-
  level over-specifications; stripped under I2 and I6 back-off
  dispositions. Replaced with behavioral prose + the general rule
  that composition uses `dry-python/returns` primitives
  (`flow`, `bind`, `bind_result`, `bind_ioresult`, `Fold.collect`,
  `.map`, `.lash`) and mixed-monad chains lift via
  `bind_result` / `IOResult.from_result` / equivalent.
  **Seed exempt from pre-step doctor static** — seed's purpose
  is to create the template-declared files; pre-step
  `template-files-present` would fail on a green-field repo
  before `seed_run` ran. Added to the pre-step exemption list
  alongside `help` and `doctor`.
  **Spec-root parameterization for custom templates** —
  `template.json` gains optional `spec_root: string` (default
  `"SPECIFICATION/"`); `DoctorContext.spec_root: Path` added;
  every doctor-static check's path references parameterized
  against `<spec-root>/` (covers `proposed-changes-and-history-
  dirs`, `version-directories-complete`, `version-contiguity`,
  `revision-to-proposed-change-pairing`,
  `proposed-change-topic-format`, `out-of-band-edits`,
  `anchor-reference-resolution`). Custom templates can now use
  `spec_root: "./"` or any subdirectory.
  **LLM→validator protocol simplified** — SKILL.md prose names
  `livespec.validate.<name>.validate` as the validation entry
  point was under-specified (LLM has no Python-function
  invocation mechanism). Simpler contract: wrapper validates
  the payload internally; on validation failure exits 3 with
  structured findings; LLM retries the template prompt with
  error context up to 3 times. No separate validator CLI
  wrappers.
  **Schema ↔ dataclass pairing** — "dataclasses generated from
  schemas" language replaced with hand-authored dataclasses at
  `schemas/dataclasses/<name>.py`. New
  `check-schema-dataclass-pairing` (AST) enforces drift-free
  pairing in both directions. No codegen toolchain.
  **Git-read allowlist extended** — `git config user.name /
  user.email` added as a second documented git reader (for
  `reviser_human` capture in `revise` and `seed` auto-capture).
  New `livespec.io.git.get_git_user() -> IOResult[str,
  GitUnavailableError]` function. Fallback to literal
  `"unknown"` when git is unavailable or config values unset.
  **Reserved `livespec-` author prefix** — identifiers with the
  prefix are reserved for automated skill-tool authorship
  (`livespec-seed`, `livespec-doctor`). Human and LLM authors
  use non-prefixed identifiers. Front-matter schemas
  pattern-validate the reservation.
  **Front-matter schemas split** —
  `proposed_change_front_matter.schema.json` (fields: `topic`,
  `author`, `created_at`) and
  `revision_front_matter.schema.json` (fields: `proposal`,
  `decision`, `revised_at`, `reviser_human`, `reviser_llm`)
  replace the single ambiguous `front_matter.schema.json`. Sum-
  type fidelity per the livespec-nlspec-spec.md principle.
  **LLM identifier precedence** — new environment variable
  `LIVESPEC_REVISER_LLM` with precedence: env var → LLM
  self-declaration in wrapper JSON payload → literal
  `"unknown-llm"` fallback. The critique and revise template
  prompts instruct the LLM to self-identify best-effort.
  **Dogfood symlink direction specified** — `.claude/skills/`
  is a relative symlink pointing at `../.claude-plugin/skills/`.
  `just bootstrap` creates it idempotently.
  **`bin/doctor_static.py` rejects `--skip-pre-check`** — the
  flag is about wrapper lifecycle chains, not the static phase
  itself. Passing it produces exit 2.
  **Housekeeping:** the upstream `nlspec-spec.md` (TG-Techie's
  prior art, preserved verbatim) relocated from
  `brainstorming/approach-2-nlspec-based/nlspec-spec.md` to
  `<repo-root>/prior-art/nlspec-spec.md`. Cross-references in
  `livespec-nlspec-spec.md`, `prior-art.md`, and
  `critique-interview-prompt.md` updated. The v003 disposition
  to "delete entirely in favor of permalink" is replaced with
  "preserve verbatim at repo-root `prior-art/` with permalink
  header for easy local diffing against the adapted version."
  Full decision record is in
  `v009/proposed_changes/proposal-critique-v08-revision.md`.

- **v010** — revise driven by
  `proposed_changes/proposal-critique-v09.md` and its revision.
  A **recreatability defect cleanup pass** surfacing 14 items
  (J1-J14) labelled with the NLSpec failure-mode framework
  (ambiguity / malformation / incompleteness / incorrectness).
  Three items moved from recommended to alternate option based on
  user input: J4 (new exit code `4` for schema validation; user
  correctly probed exit-code conventions and the alternate is
  cleaner than the structlog-kwarg discriminator); J9 (switch
  `.vendor.toml` → `.vendor.jsonc` reusing already-vendored
  `jsoncomment` rather than forcing a new `tomli` dep on the 3.10+
  floor); J10 (add inverse `--run-pre-check` flag for
  bidirectional CLI control over pre-step skip). One mid-interview
  enrichment on J3 added a new deferred-items entry
  `user-hosted-custom-templates` capturing v2+ template-discovery
  extension intent. Major structural changes:
  **DoctorInternalError + Fold.collect residuals cleaned** — v009
  I10 retired `DoctorInternalError` and I2/I6 backed off from
  naming `Fold.collect` as normative mechanism, but the
  implementer pass left residuals in PROPOSAL.md §"Static-phase
  structure" (lines 1284, 1303, DoD #6) and the style doc's
  per-check module contract. v010 J1 scrubs both: doctor static
  check signatures uniformly say `IOResult[Finding, E]` where `E`
  is any `LivespecError` subclass; orchestrator composition says
  "single ROP chain, specific primitive is implementer choice."
  **io/git.get_git_user() semantics unified** — PROPOSAL.md said
  "git-unavailable → `IOSuccess('unknown')`"; deferred-items +
  v009 revision said "git-binary absent → `IOFailure
  (GitUnavailableError)` exit 3." v010 J2 aligns PROPOSAL.md to
  the revision intent: missing binary = IOFailure (exit 3);
  missing config = IOSuccess("unknown") fallback.
  **Custom-template prompt-path resolution** — v009 SKILL.md body
  used literal `@`-references that work only for the built-in
  `livespec` template. v010 J3 introduces `bin/resolve_template.py`
  (+ `livespec/commands/resolve_template.py`): a two-step dispatch
  where SKILL.md prose invokes the wrapper via Bash, captures the
  resolved path from stdout, then uses Read to fetch
  `<path>/prompts/<name>.md`. Works uniformly for built-in and
  custom templates; seeds the extensibility surface for the new
  deferred-items entry `user-hosted-custom-templates`.
  **New exit code 4 for schema validation** — v010 J4 splits the
  retryable validation failure from non-retryable precondition
  failures. `ValidationError.exit_code = 4` (was 3); SKILL.md
  retry step renames to "Retry-on-exit-4." Clean exit-code
  discriminator; LLM can classify failures without parsing
  stderr structlog events.
  **build_parser exemption in check-public-api-result-typed** —
  v010 J5 adds the `build_parser` factory in `commands/**.py` to
  the exemption list (alongside `main`). Pure argparse
  constructor, no effects, framework return type.
  **Propose-change author precedence** — v010 J6 mirrors v009 I13
  for propose-change's `author` field: CLI `--author` → env var
  `LIVESPEC_REVISER_LLM` → LLM self-declared `author` field in
  `proposal_findings.schema.json` payload → `"unknown-llm"`
  fallback. Env var coverage widens to propose-change alongside
  revise and critique; schema extends with optional file-level
  `author` field.
  **HelpRequested class; `--help` exits 0** — v010 J7 adds
  `HelpRequested` as a non-`LivespecError` informational early-
  exit category. Supervisor pattern-matches it separately from
  `UsageError`; help text to stdout; exit 0. Avoids the v009
  conflation of help-requested with usage-error (both would have
  exited 2).
  **Coverage scope includes scripts/bin/** — v010 J8 extends the
  100% line+branch mandate from `scripts/livespec/**` +
  `dev-tooling/**` to also include `scripts/bin/**`. `_bootstrap.py`
  is fully covered; wrapper bodies pragma-excluded (trivial
  pass-throughs verified by the wrapper-shape meta-test).
  **`.vendor.toml` → `.vendor.jsonc`** — v010 J9 renames to avoid
  adding a new `tomli` vendored library (stdlib `tomllib` is
  3.11+-only, forbidden on the 3.10+ floor); the already-vendored
  `jsoncomment` parses `.vendor.jsonc`. Strips the stale "or
  per-lib VERSION files" parenthetical.
  **Inverse --run-pre-check flag** — v010 J10 adds bidirectional
  CLI control: `--skip-pre-check` → skip; `--run-pre-check` → run
  (overrides config); neither → use config default; both →
  argparse mutually-exclusive UsageError exit 2.
  `bin/doctor_static.py` rejects both flags (supersedes v009 I14's
  single-flag rejection — now rejects both).
  **Finding moved to schemas/dataclasses/finding.py** — v010 J11
  co-locates `Finding` with `DoctorFindings` in the
  `check-schema-dataclass-pairing`-walked tree. Constructor
  helpers (`pass_finding`, `fail_finding`) move with it.
  **Dogfood symlink committed to git** — v010 J12 codifies that
  `.claude/skills/ → ../.claude-plugin/skills/` is a tracked
  symbolic link (not gitignored). `just bootstrap` is defensive
  (re-creates if a developer deletes it); not required before
  Claude Code can load skills on a fresh clone.
  **template_format_version supported-set enumerated** — v010 J13
  adds "v1 livespec supports only `template_format_version: 1`"
  as an explicit invariant in PROPOSAL.md §"Custom templates are
  in v1 scope." Future versions extend the set.
  **prune-history repeat-no-op** — v010 J14 extends the
  idempotency rule: "Running `prune-history` on a project where
  the oldest surviving history entry is already a
  `PRUNED_HISTORY.json` marker (no full versions to prune) is a
  no-op. The existing marker is NOT re-written."
  **New deferred-items entry user-hosted-custom-templates** —
  explicit capture of v2+ template-discovery extension intent
  (remote URLs, registries, plugin-path hints, per-environment
  overrides). `bin/resolve_template.py`'s output contract is the
  stability shield for future extensions.
  **Scope-widened deferred-items entries:** `static-check-
  semantics` (J4, J5, J7, J10, J11, J14), `wrapper-input-schemas`
  (J6), `task-runner-and-ci-config` (J8, J9, J10),
  `skill-md-prose-authoring` (J3, J4, J7, J10). No entries
  removed. Full decision record is in
  `v010/proposed_changes/proposal-critique-v09-revision.md`.

- **v011** — revise driven by
  `proposed_changes/proposal-critique-v10.md` and its revision.
  A **recreatability defect cleanup + discipline-expansion pass**
  surfacing 11 items (K1–K11) labelled with the NLSpec failure-mode
  framework (ambiguity / malformation / incompleteness /
  incorrectness). Three items moved from recommended disposition
  to alternate option based on user input; two items expanded
  mid-interview from localized documentation fixes into broader
  project-level discipline decisions. Major structural changes:
  **Orphaned `commands/doctor.py` removed** — K1: layout tree no
  longer lists the unreferenced `commands/doctor.py`; doctor's
  Python entry lives uniformly at `livespec/doctor/run_static.py`
  (per the v007 "no `bin/doctor.py`" discipline).
  **`bin/resolve_template.py` wrapper contract codified** — K2:
  six invariants added to a new §"Template resolution contract"
  subsection: zero-positional-args + `--project-root` flag,
  one-line absolute-POSIX-path stdout contract, built-in vs user-
  provided path resolution, lifecycle exemption (no pre/post
  doctor static), exit-code set (0/2/3/127), v2+ extensibility
  shield preserving the stdout contract shape.
  **Wrapper coverage via per-wrapper tests** — K3: 100% coverage
  of `scripts/bin/**` achieved by dedicated `tests/bin/test_<cmd>.py`
  files that import each wrapper and catch `SystemExit` via
  `pytest.raises` + `monkeypatch` of `main`. No `# pragma: no
  cover` applied to wrapper bodies; no coverage-config `omit`.
  Wrapper-shape 6-line rule preserved unchanged;
  `check-wrapper-shape` + `test_wrappers.py` meta-test continue
  in parallel. Dissolves the v010 conflict between 6-line rule,
  coverage mandate, and 3-pragma-line cap.
  **Keyword-only arguments + keyword-only match patterns** —
  K4: new project-wide Python discipline. Every `def` in
  livespec scope (`scripts/livespec/**`, `scripts/bin/**`,
  `<repo-root>/dev-tooling/**`) MUST use `*` as its first
  parameter separator so all params are keyword-only. Every
  `@dataclass` MUST declare `kw_only=True` (Python 3.10+).
  `match` statements destructuring livespec-authored classes
  MUST use keyword sub-patterns (`case Foo(x=x)`); positional
  destructure permitted only for third-party library types
  (`dry-python/returns`'s `IOFailure`/`IOSuccess`/etc.). Exempts
  Python-mandated dunder signatures and `Exception.__init__`
  forwarding. Two new AST checks:
  `check-keyword-only-args` and `check-match-keyword-only`.
  Consequence: no livespec-authored class declares
  `__match_args__`; `HelpRequested` uses
  `def __init__(self, *, text: str)` and supervisor matches via
  `case IOFailure(HelpRequested(text=text))`.
  **Skill decoupled from `livespec-nlspec-spec.md`** — K5 part 1:
  every runtime-layer reference to the discipline doc removed from
  the skill. The skill no longer names, reads, or injects
  `livespec-nlspec-spec.md` at any layer. Built-in `livespec`
  template ships it at its template root; the template's own
  prompts (`seed.md`, `propose-change.md`, `critique.md`,
  `revise.md`, and the new `doctor-llm-subjective-checks.md`)
  Read it template-internally. Custom templates are not required
  to have the file. Changes: generic template-layout diagram
  loses the "OPTIONAL: discipline doc the skill injects" line;
  the "skill concatenates" paragraph deleted; the "skill injects"
  paragraph in the Built-in template section rewritten to
  template-internal; §"NLSpec conformance" section deleted in
  full; DoD item 8 rewritten to drop the "loads discipline doc"
  clause.
  **Three-category doctor extensibility** — K5 part 2: doctor's
  LLM-driven phase restructured into three categories (python-
  driven static, LLM-driven objective, LLM-driven subjective), all
  three extensible via new `template.json` fields:
  `doctor_static_check_modules: list[string]` (template-shipped
  Python modules loaded via `importlib.util.spec_from_file_location`;
  each exports `TEMPLATE_CHECKS: list[tuple[str, CheckRunFn]]`),
  `doctor_llm_objective_checks_prompt: string | null`, and
  `doctor_llm_subjective_checks_prompt: string | null` (paths
  relative to template root). Two new symmetric flag pairs
  replacing v010's single `--skip-subjective-checks`:
  `--skip-doctor-llm-objective-checks` /
  `--run-doctor-llm-objective-checks` and
  `--skip-doctor-llm-subjective-checks` /
  `--run-doctor-llm-subjective-checks`. Corresponding config keys:
  `post_step_skip_doctor_llm_objective_checks`,
  `post_step_skip_doctor_llm_subjective_checks`. All LLM-layer
  only (never passed to Python wrappers); CLI → config → default
  precedence (default `false`). Pre-step/post-step lifecycle
  applicability list adds `resolve_template` to the "no pre-step,
  no post-step" exemption alongside `help` and `doctor`.
  **`--run-*` narration symmetry accepted as intentional** —
  K6: the asymmetry between warn-on-silent-skip and neutral-on-
  CLI-override is documented as intentional; same rule extends
  to the K5 flag pairs. Explicit CLI flag use is self-evident;
  structlog records provide structured visibility for machine
  consumers.
  **Domain-term rename `reviser` → `author`** — K7:
  `LIVESPEC_REVISER_LLM` → `LIVESPEC_AUTHOR_LLM` (env var);
  `reviser_llm` → `author` (wrapper payload fields on critique
  and revise, matching propose-change's existing `author` field);
  `reviser_human` / `reviser_llm` → `author_human` / `author_llm`
  (revision-file front-matter fields). Uniform `--author <id>`
  CLI flag across all three LLM-driven wrappers (`propose-change`,
  `critique`, `revise`). Critique's v010 positional `<author>`
  replaced with `--author` flag; topic still derived as
  `<resolved-author>-critique`. Unified precedence across all
  three: CLI → env → payload → `"unknown-llm"` fallback.
  **Style-doc layout-tree duplication removed** — K8: both the
  package-layout tree and the tests tree in the Python style doc
  deleted; PROPOSAL.md is sole source of truth for directory
  layouts. Per-directory convention notes (rules, not layouts)
  retained in the style doc.
  **`livespec-` prefix demoted to convention-only** — K9: the
  v009 I9 "reserved prefix" is now a SHOULD-NOT convention with
  no mechanical enforcement. Schemas no longer pattern-validate
  `^livespec-`; wrappers no longer reject user-supplied
  `livespec-` values from CLI / env / payload. The prefix is
  retained in PROPOSAL.md prose as a convention for visual
  audit-trail disambiguation between skill-auto artifacts
  (`livespec-seed`, `livespec-doctor`) and user/LLM authorship;
  no code branches on it. Resolves the v010 cross-document
  contradiction between "schema pattern-validates" and "format
  layer rejects, not schema layer" by eliminating the enforcement
  machinery.
  **Doctor-static domain-failure-to-fail-Finding discipline** —
  K10: new opening paragraph in §"Static-phase checks" stating
  that doctor-static checks MUST map domain-meaningful failure
  modes to `IOSuccess(Finding(status="fail", ...))`, not
  `IOFailure(err)`. `IOFailure` reserved for boundary errors
  where the check cannot continue. Preserves the invariant that
  `bin/doctor_static.py` never emits exit 4 (which is reserved
  for schema-validation retries on LLM-provided JSON payloads,
  not doctor-static output).
  **Tests-tree example adds `schemas/dataclasses/`** — K11:
  `tests/livespec/schemas/dataclasses/test_finding.py` +
  `test_doctor_findings.py` + `...` added to PROPOSAL.md's
  test-tree example. Mirror rule already universal; example
  made consistent with the rule. Per K8 the style doc's tests
  tree is removed entirely, so PROPOSAL.md is the sole example
  location.
  **Deferred-items updates:** 6 existing entries scope-widened
  (`template-prompt-authoring`, `enforcement-check-scripts`,
  `static-check-semantics`, `front-matter-parser`,
  `wrapper-input-schemas`, `skill-md-prose-authoring`,
  `task-runner-and-ci-config`); 0 new entries added; 0 removed.
  Full decision record is in
  `v011/proposed_changes/proposal-critique-v10-revision.md`.
- **v012** — revise driven by
  `proposed_changes/proposal-critique-v11.md` and its revision.
  An **agent-guardrail-focused incompleteness pass** producing
  15 items (L1–L15) labelled with the NLSpec failure-mode
  framework. The pass was driven by the v005+ "strongest-
  possible guardrails for agent-authored Python" memory and
  informed by 2026 Python tooling research (pyright strict-plus
  options, ruff rule-set expansion, Hypothesis property-based
  testing, mutmut mutation testing, Import-Linter declarative
  architecture enforcement, basedpyright). Two items were
  revised mid-interview based on user pushback (L5: dropped
  the `@final` mandate as redundant with the AST check; L6:
  switched from a dedicated `check-no-abc` AST check to TID
  banned-imports reuse). One item split into two (L15a / L15b)
  after the user noted dev-tooling and bundle-vendoring were
  conflated. Major structural changes:
  **`reportUnusedCallResult` enabled in pyright** — L1: closes
  the largest single ROP-discipline hole (silently-discarded
  `Result` / `IOResult` values become type errors). One-line
  `[tool.pyright]` config addition.
  **Six pyright strict-plus diagnostics enabled** — L2:
  `reportImplicitOverride`, `reportUninitializedInstanceVariable`,
  `reportUnnecessaryTypeIgnoreComment`, `reportUnnecessaryCast`,
  `reportUnnecessaryIsInstance`, `reportImplicitStringConcatenation`.
  Open dependency follow-up: `typing_extensions` for `@override`
  on Python 3.10 (verify transitive vendoring via
  dry-python/returns OR add direct mise-pin OR bump floor).
  **16 ruff rule categories added** — L3 + L10 + L11:
  `TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC` (L3)
  plus `T20` (L10) plus `S` (L11). Total v012 selection: 27
  categories above v011's 11.
  **Strict-dataclass triple completed** — L4: K4's
  `frozen=True, kw_only=True` rule extended to require
  `slots=True` as well. The existing `check-keyword-only-args`
  AST walker extends to verify all three. Pure win for livespec
  (no `__weakref__` use; no multiple inheritance per L5).
  **`check-no-inheritance` AST check** — L5 (revised): forbids
  `class X(Y):` outside the allowlist `{Exception,
  BaseException, LivespecError, Protocol, NamedTuple,
  TypedDict}` or LivespecError subclasses. Codifies flat-
  composition direction. `LivespecError` itself remains an open
  base for new domain-error subclasses; leaf domain errors are
  closed-by-allowlist. `@final` decorator OPTIONAL throughout
  livespec; AST check is the source of truth (revised from
  originally-recommended "both" after user noted `@final`
  redundancy).
  **`abc.*` banned via TID** — L6 (revised): `abc.ABC`,
  `abc.ABCMeta`, `abc.abstractmethod` added to the v011 K4
  / v012 L11 TID banned-imports list. Reuses ruff TID
  infrastructure rather than a dedicated AST check.
  **`assert_never` exhaustiveness mandated** — L7: every
  `match` statement in `livespec/**` MUST terminate with
  `case _: assert_never(<subject>)`. Conservative scope (every
  match, regardless of subject type). Adding a new variant
  becomes a type error at every unhandled dispatch site.
  Open dependency follow-up: `typing_extensions` on Python
  3.10 (shared with L2).
  **NewType domain primitives** — L8: new `livespec/types.py`
  module declaring 8 NewType aliases (`CheckId`, `RunId`,
  `TopicSlug`, `SpecRoot`, `SchemaId`, `TemplateName`,
  `Author`, `VersionTag`). AST check
  `check-newtype-domain-primitives` verifies field annotations
  matching canonical field names use the corresponding
  NewType. Eliminates the cross-wiring class of bug.
  **Per-module `__all__` mandated** — L9: every module under
  `livespec/**` declares module-top `__all__: list[str]`.
  `check-public-api-result-typed` rescoped to use `__all__`
  for public-API detection rather than the underscore
  convention.
  **`check-no-write-direct` + ruff `T20`** — L10: bans
  `print` / `pprint` (T20) and `sys.stdout.write` /
  `sys.stderr.write` (custom AST check) outside three
  documented exemptions: `bin/_bootstrap.py` (pre-import
  stderr), supervisor `main()` in `commands/**.py`
  (HelpRequested stdout per K7), `doctor/run_static.py::main()`
  (findings JSON stdout). All other output via structlog.
  **Forbidden imports (security)** — L11: ruff `S` enabled;
  `pickle`, `marshal`, `shelve` added to TID banned-imports.
  **Hypothesis PBT mandated for pure modules** — L12:
  `hypothesis` (MPL-2.0) + `hypothesis-jsonschema` (MIT)
  mise-pinned (NOT vendored — test-only deps follow the v011
  test-dep packaging convention). Each test module under
  `tests/livespec/parse/**` and `tests/livespec/validate/**`
  MUST declare ≥1 `@given(...)`-decorated test. AST check
  `check-pbt-coverage-pure-modules`.
  **Mutation testing as release-gate** — L13: `mutmut` (MIT)
  mise-pinned. New `just check-mutation` target runs against
  `livespec/parse/` and `livespec/validate/` on a release-tag
  CI workflow only (NOT in `just check`; NOT per-commit).
  Threshold: ≥80% mutation kill rate (tunable on first real
  measurement).
  **Import-Linter at dev-tooling layer** — L15a: `import-
  linter` (BSD-2) mise-pinned. New `[tool.importlinter]`
  configuration in `pyproject.toml` declares three contracts
  replacing the planned hand-written `check-purity` +
  `check-import-graph` + import-surface portion of
  `check-no-raise-outside-io`. Single new
  `check-imports-architecture` target replaces those three
  in the canonical target list. Raise-site portion of
  `check-no-raise-outside-io` remains hand-written and
  narrower.
  **User-provided extensions get minimal requirements** —
  L15b + new governing principle: PROPOSAL.md's
  `doctor_static_check_modules` section explicitly states
  that extension modules carry NO architecture / library /
  pattern expectations beyond the calling-API contract.
  livespec's enforcement suite does NOT scope to extension
  code. Import-Linter is NOT vendored in the bundle (would
  set a precedent of vendoring libraries livespec OFFERS to
  extension authors rather than libraries livespec NEEDS).
  Style doc §"Scope" extended with the matching extension-
  exemption clause. Recorded as a new feedback memory
  (`feedback_user_extensions_minimal_requirements.md`).
  **basedpyright deferred** — L14: stay on pyright; new
  standalone `basedpyright-vs-pyright` deferred-items entry
  to revisit later.
  **Deferred-items updates:** 4 existing entries scope-widened
  (`enforcement-check-scripts`, `static-check-semantics`,
  `task-runner-and-ci-config`, plus the static-check-semantics
  semantic catalogue extended with v012 check semantics);
  1 new entry added (`basedpyright-vs-pyright`); 0 removed.
  **Careful-review pass (first)** caught and fixed 10
  inconsistencies before the history write: example dataclasses
  updated to the strict triple; example match statement updated
  with `assert_never` terminator; `check-no-write-direct`
  exemption list expanded to include supervisor stdout surfaces
  (HelpRequested + findings JSON); ruff category count corrected
  from 28 to 27; canonical role-name list corrected to use
  actual field names (`topic` not `topic_slug`;
  `author` / `author_human` / `author_llm` for Author);
  `livespec/types.py` added to package-layout tree and DoD;
  underscore-convention public-API references updated to point
  to `__all__`; deferred-items AST-check enumeration updated to
  drop replaced `check-purity` / `check-import-graph` and add
  v012 new checks; style doc Purity-and-IO-isolation enforcement
  reference updated from `check-purity` to
  `check-imports-architecture`; revision-file ruff-count
  arithmetic reconciled.
  **Careful-review pass (second)** caught 6 additional issues:
  DoD #10 + #12 not updated for v012 L12 / L13 / mise-pin
  additions / pyright strict-plus / ruff selection / TID
  banned-imports / Import-Linter contracts / release-tag CI
  workflow; PROPOSAL.md §Coverage section missing scripts/bin/**
  scope (v010 J8 / v011 K3 oversight); Self-application step 5
  not mentioning new `basedpyright-vs-pyright` deferred entry;
  L10's check-no-write-direct exemption #2 too narrow (only
  HelpRequested.text; should also cover `bin/resolve_template.py`
  resolved-path stdout per K2 and any future supervisor-owned
  stdout contracts); style doc §Code coverage line 948-949
  contradicting line 962-973 ('wrapper bodies pragma-excluded'
  vs 'NOT pragma-excluded' — v011 K3 oversight). All 6 fixed;
  PROPOSAL.md re-copied to history/v012/PROPOSAL.md
  (byte-identical verified).
  **Careful-review pass (third)** caught 6 more issues: deferred-
  items.md item-schema example version range stopped at v011 (now
  includes v012); wrapper-input-schemas + front-matter-parser
  entries didn't reflect v012 L4 strict-dataclass triple or L8
  NewType usage on their dataclasses (scope-widened both with
  explicit dataclass-by-dataclass NewType mappings); PROPOSAL.md
  dev-tooling/checks/ package-layout still listed `purity.py`
  and `import_graph.py` (which v012 L15a replaces with Import-
  Linter contracts) AND was missing all v011 K4 + v012
  L5/L7/L8/L9/L10/L12 added check scripts (replaced layout block
  with the v012-accurate inventory); claude-md-prose deferred-
  entry source line was stale at "v006 (carried forward to v008)"
  (now v006 carried-forward-through-every-version-since) and
  didn't list v012 per-directory CLAUDE.md notes for parse/ +
  validate/ (L12 PBT) / types.py (L8 location) / io/ (L10
  supervisor exemption scope); stale cross-reference at style
  doc line 1211 to non-existent §"HelpRequested disposition"
  subsection (fixed to point at the actual HelpRequested class
  definition in §Exit code contract + HelpRequested example in
  §Structural pattern matching). All 6 fixed; PROPOSAL.md
  re-copied to history/v012/PROPOSAL.md (byte-identical
  verified).
  **Careful-review pass (fourth)** focused on the v012 revision
  file's self-consistency vs the working deferred-items.md
  state. Caught 5 issues: revision-file 'Carried forward
  unchanged from v011' list still listed front-matter-parser /
  wrapper-input-schemas / claude-md-prose entries as carried
  forward — but pass 3 had widened them; moved to 'Scope-widened
  in v012' with full per-entry detail; revision-file 'Outstanding
  follow-ups' count said '4 existing entries' but actual count
  after pass 3 is 6 (original 3 + pass 3 widened 3); revision-
  file L10 summary-table row still said '(with `_bootstrap.py`
  exemption)' from pre-pass-2 wording, but L10 actually has 3
  documented exemptions; revision-file line 837 still said '17
  categories' instead of '16 categories above v011's 11 (27
  total)' — earlier replace_all hadn't caught this; L8 canonical
  NewType mapping cited field name `template_name` →
  `TemplateName` but the actual `.livespec.jsonc` schema field
  is `template` (LivespecConfig dataclass field is `template`
  per schema-dataclass-pairing) — fixed across style doc +
  deferred-items + revision file with disambiguation note about
  `template_root: Path` being a different field that uses raw
  `Path`. PROPOSAL.md NOT edited in this pass (no re-copy
  needed). **Cumulative across 4 review passes: 27
  inconsistencies caught and fixed (10 + 6 + 6 + 5).**
  Full decision record is in
  `v012/proposed_changes/proposal-critique-v11-revision.md`.

- **v013** — revise driven by
  `proposed_changes/proposal-critique-v12.md` and its revision.
  A **recreatability-and-integration-gap cleanup pass**
  surfacing 13 items (M1-M7 major/significant + C1-C6
  smaller cleanup) plus one new item M8 added mid-interview
  after user clarification. Each item labelled with the NLSpec
  failure-mode framework (ambiguity / malformation /
  incompleteness / incorrectness). Three items moved from
  recommended to alternate option based on user input: M4
  (retry count — 3 total attempts instead of 3 retries after
  initial); M5 (check-no-inheritance — tighten to direct-
  parent-only instead of accepting transitive-MRO); C5 (scope
  wording — full `.claude-plugin/scripts/...` form throughout
  instead of short form with shortcut note). Two items were
  reshaped mid-interview (M2 split into format-only + new M8
  for lifecycle; M8 options re-framed when user surfaced the
  shipped-vs-not-shipped architectural distinction). One item
  (M1) underwent a mid-lifecycle correction (interview picked
  Option A "mise-pin typing_extensions"; assistant caught
  during apply phase that mise-pinning can't make the symbols
  available at user runtime; re-interview chose A''' "vendor
  as ~15-line shim at `_vendor/typing_extensions/`" after
  user noted size disproportionality vs upstream). Major
  structural changes:
  **`typing_extensions` vendored as minimal shim** — M1: the
  largest recreatability blocker (L2's `reportImplicitOverride`
  + L7's `assert_never` require typing_extensions on the 3.10
  floor). Resolution: `_vendor/typing_extensions/__init__.py`
  exports `override` + `assert_never` keeping the
  `typing_extensions` module name for pyright recognition; the
  shim ships upstream PSF-2.0 LICENSE verbatim with attribution.
  License policy extended from `MIT, BSD-2, BSD-3, Apache-2.0`
  to include `PSF-2.0` narrowly. Future shim widening is a
  one-line edit.
  **Heading-coverage registry format extended** — M2 + M8:
  `tests/heading-coverage.json` extended from `{heading, test}`
  to `{spec_file, heading, test}` to disambiguate heading-text
  collisions across spec files; scenario-block headings
  excluded from meta-test scope; new optional `reason` field
  required when `test: "TODO"`. The meta-test tolerates
  `"TODO"` with non-empty reason at `just check` time; new
  release-gate `check-no-todo-registry` (paired with
  `check-mutation` on release-tag CI only) rejects any TODO
  entry regardless of reason. Livespec-repo-internal
  enforcement; NOT shipped in the `.claude-plugin/` bundle.
  **Mutation testing bootstrap discipline** — M3:
  `.mutmut-baseline.json` recorded at repo root; release-gate
  ratchet compares against `min(baseline - 5%, 80%)` until
  sustained 80%; `just check-mutation` emits structured JSON
  with surviving-mutant file+line+kind per v013 M3.
  **Retry count disambiguated** — M4: rename from "3 retries"
  to "up to 2 retries (3 attempts total)" across PROPOSAL.md +
  style doc + deferred-items.
  **`check-no-inheritance` tightened** — M5: AST check now
  direct-parent-only; `LivespecError` subclasses (`UsageError`,
  etc.) are NOT acceptable bases. Enforces v012 revision-file
  leaf-closed intent mechanically.
  **Three-way schema↔dataclass↔validator pairing** — M6:
  `check-schema-dataclass-pairing` widened to walk validators
  too; v1 validators enumerated in PROPOSAL.md layout tree.
  **Import-Linter minimum concrete example** — M7: style doc
  §"Import-Linter contracts (minimum configuration)" adds a
  25-line `[tool.importlinter]` TOML example with illustrative
  caveat anchoring the load-bearing architectural outcomes
  while preserving architecture-vs-mechanism discipline.
  **Typo + drift cleanups** — C1 (`python-skill-script-script-
  style-requirements.md` double-"script" typo at PROPOSAL.md
  line 392); C2 (style doc dev-dep list references PROPOSAL.md
  as single source); C3 (test-filename rule for leading-
  underscore source modules); C4 (`livespec/types.py` stdlib-
  shadow acknowledgement note); C5 (scope canonicalization on
  full-path `.claude-plugin/scripts/...` throughout style doc);
  C6 ("unconditionally" wording at PROPOSAL.md §"Environment
  variables" replaced with precedence-matching phrasing).
  **Deferred-items updates:** 6 existing entries scope-widened
  (`enforcement-check-scripts`, `static-check-semantics`,
  `task-runner-and-ci-config`, `skill-md-prose-authoring`,
  `wrapper-input-schemas`, `front-matter-parser`); the v012
  `typing_extensions` availability follow-up under
  `task-runner-and-ci-config` CLOSED per M1; 0 new entries;
  0 removed.
  **Careful-review passes.** 4 general careful-review passes
  plus 1 dedicated deferred-items-consistency pass. Pass 1
  caught 5 load-bearing fixes: revision-file M1 section still
  described mise-pinning `typing_extensions` (rewrote to
  A'''-vendored-shim); style doc §"Dataclass authorship"
  said "AST walker over both sides" for
  `check-schema-dataclass-pairing` (updated to three-way);
  deferred-items `check-assert-never-exhaustiveness`
  semantics subsection still referenced "typing_extensions
  3.10" (updated to uniform import source); DoD item 10
  missed M3 baseline + M8 check-no-todo-registry + M8 reason
  tolerance; dev-tooling layout tree missed
  `.mutmut-baseline.json`. Pass 2 caught 3 load-bearing
  fixes: added shim-libraries distinction to style doc
  §"Vendoring discipline" (shims are livespec-authored, not
  upstream-sourced; `.vendor.jsonc` carries `shim: true`);
  PROPOSAL.md §"Vendored pure-Python libraries" noted
  `just vendor-update` applies only to upstream-sourced
  libs; heading-coverage.json example extended with TODO-
  with-reason illustrative row. Pass 3 caught 4 load-
  bearing fixes: fixed 2 stale Source lines in deferred-
  items.md (`python-style-doc-into-constraints` and
  `returns-pyright-plugin-disposition` both said "carried
  forward to v008" instead of "carried forward through
  every version since" — same drift pattern v012's pass 3
  caught for `claude-md-prose`); fixed out-of-chronological-
  order widening list in `static-check-semantics` Source
  line (moved v013 to end); added M1 to
  `static-check-semantics` v013 widenings in revision file
  (the `check-assert-never-exhaustiveness` import-source
  tightening counts as M1's reach). Pass 4 landed no load-
  bearing fixes (pass 4 was intentionally the final pass
  per the "continue until pass lands no load-bearing
  fixes" rule). **Cumulative across 4 careful-review
  passes: 12 inconsistencies caught and fixed (5 + 3 + 4
  + 0).**
  **Dedicated deferred-items-consistency pass.** Walks
  every deferred-items entry and verifies source line +
  body fully reflects every decision across every prior
  version. Caught 4 load-bearing fixes: `no_todo_registry.py`
  missing from `dev-tooling/checks/` layout tree (added
  per M8 follow-through); `check-no-todo-registry` bullet
  missing from `enforcement-check-scripts` deferred entry
  body (added); `template_config.schema.json` +
  `template_config.py` missing from PROPOSAL.md's schemas/
  and schemas/dataclasses/ layout trees (pre-existing
  v011 K5 drift that v012 careful-review passes missed);
  `§"Type safety — @override and assert_never import
  source"` cross-reference pointed at a bolded inline
  paragraph rather than a proper `###` subsection heading
  (promoted the paragraph to a subsection at style doc
  line 745 so the cross-ref resolves).
  **Cumulative total findings across all 5 passes (4
  careful-review + 1 deferred-items-consistency): 16
  inconsistencies caught and fixed (5 + 3 + 4 + 0 + 4).**
  Full decision record is in
  `v013/proposed_changes/proposal-critique-v12-revision.md`.

## Pointer

The current working `PROPOSAL.md` lives at the parent directory
(`brainstorming/approach-2-nlspec-based/PROPOSAL.md`). It is
byte-identical to `history/v013/PROPOSAL.md` until the next revise.
