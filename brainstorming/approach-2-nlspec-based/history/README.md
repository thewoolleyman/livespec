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

## Pointer

The current working `PROPOSAL.md` lives at the parent directory
(`brainstorming/approach-2-nlspec-based/PROPOSAL.md`). It is
byte-identical to `history/v010/PROPOSAL.md` until the next revise.
