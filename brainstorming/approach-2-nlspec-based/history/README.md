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

- **v014** — revise driven by
  `proposed_changes/proposal-critique-v13.md` and its
  revision. A **recreatability-and-integration-gap cleanup
  pass** surfacing 11 items (N1-N8 major/significant +
  C1-C3 smaller cleanup) plus one new item N9 added
  mid-interview after N1's resolution surfaced the need for
  an end-to-end integration test. Each item labelled with
  the NLSpec failure-mode framework (ambiguity /
  malformation / incompleteness / incorrectness). Two items
  moved from recommended to alternate option based on user
  input: N6 (monotonic counter from `-2` instead of
  always-appended UTC-timestamp) and N9-D1 (live-LLM always
  for real tier + deterministic API-compatible pass-through
  mock; no stub/replay blending). Two items were reshaped
  mid-interview: N1 (originally narrow resolve_template
  contradiction; reshaped to bring `minimal` template into
  v1 scope + seed SKILL.md pre-seed dialogue) and N7
  (original three recovery options refined during apply
  phase to reuse existing `--skip-pre-check` flag pair).
  One new item (N9) was added mid-interview. Major
  structural changes:
  **`minimal` template added as second built-in** — N1:
  single-file `SPECIFICATION.md` at repo root
  (`spec_root: "./"`); four required prompts + starter
  `SPECIFICATION.md`; `.claude-plugin/
  specification-templates/minimal/` layout codified in
  PROPOSAL.md. Seed's SKILL.md prose prompts the user for
  template choice in dialogue when `.livespec.jsonc` is
  absent (pre-seed); writes config with chosen template at
  end of seed flow. `resolve_template.py` keeps its strict
  exit-3-on-missing contract for non-seed sub-commands.
  **End-to-end harness-level integration test** — N9:
  `minimal` template is the canonical E2E fixture shape.
  Two `just` targets share the same pytest suite with env
  var `LIVESPEC_E2E_HARNESS=mock|real` selecting the
  executable. `just e2e-test-claude-code-mock` (in
  `just check`; per-commit): livespec-authored API-
  compatible pass-through mock at `<repo-root>/tests/e2e/
  fake_claude.py` reads `minimal`'s prompts with
  hardcoded delimiter comments and invokes wrappers
  deterministically. `just e2e-test-claude-code-real`
  (NOT in `just check`): real `claude-agent-sdk` against
  live Anthropic API via `ANTHROPIC_API_KEY`. CI triggers
  for real tier: `merge_group` (pre-merge via GitHub merge
  queue), `push` to `master` (every master commit),
  `workflow_dispatch` (manual any-branch invocation).
  Mock scope: replaces ONLY the Claude Agent SDK / LLM
  layer (wrappers always run for real). Coverage: happy
  path (seed → propose-change → critique → revise →
  doctor → prune-history) plus three error paths (retry-
  on-exit-4; doctor fail-then-fix; prune-history no-op).
  **`finding.schema.json` + `validate/finding.py`
  REQUIRED** — N2: the v010 J11 implementer-choice between
  standalone-schema and embedded-in-doctor_findings is
  CLOSED; standalone required. Three-way
  `check-schema-dataclass-pairing` symmetry holds strictly
  without a by-name exemption.
  **Doctor-static orchestrator bootstrap lenience** — N3:
  `DoctorContext` gains `config_load_status` and
  `template_load_status` Literal fields; orchestrator
  builds context with best-effort defaults on malformed /
  absent `.livespec.jsonc` or `template.json`;
  `livespec-jsonc-valid` and `template-exists` emit fail
  Findings (preserving K10 fail-Finding discipline)
  rather than aborting without findings.
  **`template-exists` widening** — N4: the check now also
  verifies the four REQUIRED prompt files exist under
  `prompts/` AND any `template.json`-declared
  `doctor_llm_*_checks_prompt` paths AND all
  `doctor_static_check_modules` paths exist.
  **Author identifier → filename slug transformation** —
  N5: wrapper transforms resolved `author` value via GFM
  slug algorithm (lowercase; non-[a-z0-9] → hyphen;
  trim/collapse/truncate-64; empty fallback to
  `"unknown-llm"`) for use as filename component; original
  un-slugged value preserved in YAML front-matter for
  audit. Applies uniformly across propose-change,
  critique, revise.
  **Topic collision disambiguation codified** — N6:
  monotonic integer suffix starting at `-2`; no
  zero-padding; only on conflict (not always-appended);
  scope: propose-change and critique filenames only
  (out-of-band-edit-* uses separate UTC-timestamp
  convention).
  **Seed post-step-failure recovery path** — N7: documents
  existing `--skip-pre-check` reuse as the recovery
  mechanism (propose-change --skip-pre-check + revise
  --skip-pre-check); no new flags; seed idempotency stays
  strict.
  **prune-history wording fix** — N8: line 1543 updated
  from "Accepts no arguments in v1" to explicit listing of
  the mutually-exclusive `--skip-pre-check` /
  `--run-pre-check` flag pair per §"Pre-step skip control".
  **Template-extension module load failure routing** — C3:
  syntax error / import error / missing `TEMPLATE_CHECKS`
  export all route through `IOFailure(PreconditionError)`
  → exit 3 at livespec's I/O boundary; preserves domain-
  error/bug split; bug-class exit 1 reserved for livespec's
  own code.
  **Smaller cleanups:** C1 (sweep-replace residual short-
  form `scripts/_vendor/` → `.claude-plugin/scripts/_vendor/`
  at PROPOSAL.md lines 880, 2051, 2501); C2 (one-sentence
  parentheticals on seed / propose-change / revise
  sub-command headings explicitly noting LLM-vs-wrapper
  split).
  **Deferred-items updates:** 5 existing entries
  scope-widened (`template-prompt-authoring`,
  `static-check-semantics`, `task-runner-and-ci-config`,
  `skill-md-prose-authoring`, `wrapper-input-schemas`);
  `enforcement-check-scripts` was initially included but
  reclassified to carried-forward-unchanged during the
  dedicated deferred-items-consistency pass (N2 and N4
  affect sibling entries, not enforcement-check-scripts's
  scope). 2 new entries added:
  `end-to-end-integration-test` (v014 N9) and
  `local-bundled-model-e2e` (v014 N9-D1; v2+ future
  scope to eliminate the `ANTHROPIC_API_KEY` CI
  dependency). 0 entries removed.
  **Careful-review pass (first)** caught 3 load-bearing
  fixes: stale v010 J11 implementer-choice language inside
  the pre-existing static-check-semantics deferred entry
  (updated to note v014 N2 closure); missing SPECIFICATION
  directory structure section for minimal template
  (added); DoctorContext cross-ref in DoD needed to
  mention new N3 fields.
  **Careful-review pass (second)** caught 3 load-bearing
  fixes: missing `tests/e2e/` subtree in PROPOSAL.md's test
  tree example (added) plus stale `test_purity.py`
  reference (replaced by Import-Linter per v012 L15a);
  CLAUDE.md-coverage exclusion rule needed to widen
  `fixtures/` subtree-exclusion to cover `tests/e2e/
  fixtures/` per N9 (updated in both style doc and
  PROPOSAL.md DoD).
  **Careful-review pass (third)** caught 1 load-bearing
  fix: revision file "Outstanding follow-ups" said
  "touched 7 existing entries" but only 6 were listed;
  corrected to 6.
  **Careful-review pass (fourth)** caught 2 load-bearing
  fixes (overlapping with the dedicated deferred-items-
  consistency pass): `enforcement-check-scripts` source
  line incorrectly claimed v014 N2/N4 widening but those
  items affect sibling entries (`wrapper-input-schemas`
  and `static-check-semantics`); revision file's
  deferred-items inventory moved `enforcement-check-
  scripts` from Scope-widened to Carried-forward-unchanged
  category with explanatory note; Outstanding follow-ups
  count updated from 6 to 5.
  **Careful-review pass (fifth)** caught 2 load-bearing
  fixes: duplicate `front-matter-parser` entry in the
  revision file's deferred-items inventory removed;
  revision file's C3 row cross-ref updated from §"Template-
  extension doctor-static check loading" to the more
  specific §"Template-extension doctor-static check
  loading — failure routing" (v014 addition following the
  v011 K5 subsection).
  **Careful-review pass (sixth)** landed no load-bearing
  fixes (pass 6 was intentionally the final pass per the
  "continue until pass lands no load-bearing fixes" rule).
  **Dedicated deferred-items-consistency pass** walked
  every deferred-items entry and verified source line +
  body fully reflects every decision across every prior
  version. Findings overlapped with pass 4 (the
  enforcement-check-scripts source-line correction);
  walked confirmation identified 0 additional drift
  beyond those already caught.
  **Cumulative total findings across all 6 careful-review
  passes + 1 deferred-items-consistency pass: 11
  inconsistencies caught and fixed (3 + 3 + 1 + 2 + 2 +
  0 + 0; deferred-items-consistency findings merged into
  pass 4's count).**
  Full decision record is in
  `v014/proposed_changes/proposal-critique-v13-revision.md`.

- **v015** — revise driven by
  `proposed_changes/proposal-critique-v14.md` and its
  revision. A **recreatability-and-cross-doc-consistency
  cleanup pass** surfacing 4 items (O1-O4), all of which
  were framed as repairs to stale wording or underspecified
  ownership boundaries introduced by earlier settled
  decisions rather than as architectural reversals. Two
  items preserved the v009 I7 / v014 N1 template direction
  by removing stale generic hardcodings (O1, O2). One item
  widened mid-interview from a `critique`-local naming
  ambiguity into a general wrapper-boundary contract for
  direct `propose-change` callers (O3). One item was
  reshaped during interview from "how many retries?" into
  "who owns the retry mechanism and what is actually
  testable?" (O4). Major structural changes:
  **Generic lifecycle paths parameterized by `<spec-root>`**
  — O1: generic operational prose no longer hardcodes
  `SPECIFICATION/...`; template-specific `livespec`
  examples remain literal only in the sections that are
  actually about that template. Applied to sub-command
  semantics plus the generic versioning, pruning, revision-
  file, doctor-output, and other operational sections.
  **Seed/history snapshot wording made template-aware** —
  O2: seed snapshots the active template's versioned
  surface; per-version README copies exist only for
  templates whose versioned surface defines one. The built-
  in `minimal` template therefore continues to have no
  `history/vNNN/README.md`.
  **Central topic canonicalization at `propose-change`**
  — O3: inbound `<topic>` is now explicitly treated as a
  user-facing topic hint. `bin/propose_change.py`
  canonicalizes it centrally (lowercase; runs of
  non-`[a-z0-9]` collapse to `-`; trim; truncate to 64;
  empty-after-canonicalization is `UsageError` exit 2) and
  uses the canonicalized value for filename,
  front-matter `topic`, and collision disambiguation.
  `critique` now passes raw `<resolved-author>-critique`
  topic hints into that shared rule instead of owning a
  separate slugification path.
  **Retry semantics de-over-specified; deterministic
  retry-path E2E coverage narrowed to mock-only** — O4:
  fixed retry counts were removed from the working docs.
  Exit `4` remains the malformed-payload signal distinct
  from exit `3`, and SKILL/prompt orchestration SHOULD use
  wrapper return codes to decide whether to retry with
  error context. The common E2E pytest suite now
  explicitly allows harness-specific pytest markers /
  `skipif`s; deterministic retry-on-exit-4 coverage runs
  only in mock mode (first malformed, second well-formed)
  and is skipped in real mode.
  **Deferred-items updates:** 4 existing entries
  scope-widened (`template-prompt-authoring`,
  `static-check-semantics`, `skill-md-prose-authoring`,
  `end-to-end-integration-test`); 0 new entries added;
  0 removed.
  **Careful-review pass (first)** caught 1 load-bearing
  fix cluster: additional O1 path drift remained in generic
  lifecycle prose outside the sub-command sections.
  **Careful-review pass (second)** caught 5 more
  load-bearing fixes: stale generic path references
  remained in `Versioning`, `Pruning history`, `Revision
  file format`, the doctor output example, and the
  self-application seed path.
  **Careful-review pass (third)** landed no load-bearing
  fixes (final pass per the "continue until a pass lands no
  load-bearing fixes" rule).
  **Dedicated deferred-items-consistency pass** walked the
  updated deferred entries and found 0 additional drift.
  **Cumulative total findings across all 3 careful-review
  passes + 1 deferred-items-consistency pass: 6
  inconsistencies caught and fixed (1 + 5 + 0 + 0).**
  Full decision record is in
  `v015/proposed_changes/proposal-critique-v14-revision.md`.

- **v016** — revise driven by
  `proposed_changes/proposal-critique-v15.md` and its revision.
  A **recreatability-and-cross-doc-consistency cleanup pass**
  surfacing 5 items (P1-P5), all of which were framed as
  repairs to stale or underspecified wording from earlier
  settled decisions rather than architectural reversals. Four
  items were accepted as proposed; one item (P4) was reshaped
  during interview from "what exact `topic` value does
  `out-of-band-edits` backfill assign?" into a MUST-level
  single-canonicalization architecture requirement after the
  user correctly pushed that the original framing had drifted
  into implementation mechanism. Major structural changes:
  **`anchor-reference-resolution` walk set codified** — P1:
  under the built-in `minimal` template's `spec_root: "./"`,
  the check was walking the entire repo root (top-level
  `README.md`, `CONTRIBUTING.md`, source trees, `.github/`,
  etc.) as an incidental side effect of v014 N1 plus v009 I7.
  The check's walk is now scoped to the template-declared spec
  file set, the spec-root `README.md` when the template
  declares one, `<spec-root>/proposed_changes/**`,
  `<spec-root>/history/**/proposed_changes/**`, and per-version
  snapshots of each template-declared spec file. The same
  walk-set semantic applies uniformly to any future
  doctor-static check that walks `<spec-root>/` recursively.
  **Seed's `.livespec.jsonc` write made wrapper-owned** — P2:
  `bin/seed.py` writes `.livespec.jsonc` as part of its
  deterministic file-shaping work, BEFORE post-step
  doctor-static runs. `seed_input.schema.json` gains a required
  top-level `template: string` field carrying the user-chosen
  value from the pre-seed SKILL.md-prose dialogue. Post-step
  now inspects a fully-bootstrapped project tree including the
  `.livespec.jsonc` it just wrote.
  **Reserve-suffix canonicalization mechanism added** — P3:
  `bin/propose_change.py` gains `--reserve-suffix <text>` (also
  exposed as a Python internal API parameter). When supplied,
  canonicalization truncates the non-suffix portion to `64 −
  len(canonicalized-suffix)` and re-appends the suffix
  verbatim. `critique` uses this to guarantee its `-critique`
  suffix survives truncation on long author slugs without
  fragmenting v015 O3's single-rule canonicalization boundary.
  **MUST-level single-canonicalization invariant for the
  `topic` field** — P4: the `topic` YAML front-matter field
  MUST be derived via the same canonicalization rule across
  all creation paths (user-invoked `propose-change`,
  `critique`'s internal delegation, skill-auto paths like
  `seed` auto-capture and `out-of-band-edits` backfill).
  Implementations MUST route all `topic` derivations through a
  single shared canonicalization. No mechanism detail
  prescribed (architecture, not mechanism).
  **Shebang-wrapper contract 6-line → 6-statement** — P5:
  the `"6-line shape"` phrasing was self-contradictory with
  the canonical 7-line example (blank line between imports
  and `raise SystemExit`). Rewrote as "6 statements (no other
  statements, no other lines beyond the optional single blank
  line...)". `check-wrapper-shape`'s AST-lite walker operates
  on the AST module body so the optional blank is accepted
  automatically; codified in `static-check-semantics`.
  **Deferred-items updates:** 5 existing entries
  scope-widened (`static-check-semantics` for P1/P3/P5 +
  critique-path update, `wrapper-input-schemas` for P2,
  `skill-md-prose-authoring` for P2/P3,
  `template-prompt-authoring` for P2's schema-field addition
  propagating to every template's seed prompt,
  `enforcement-check-scripts` for P5's algorithm change);
  0 new entries added; 0 removed.
  **Careful-review pass (first)** caught 9 load-bearing fixes:
  5 stale `6-line` phrasings in the style doc (lines 227,
  388, 1149, 1173, 1176); 2 stale `6-line` phrasings in
  PROPOSAL.md (lines 317, 2497 as-written pre-pass); a
  pre-existing typo at PROPOSAL.md line 1960
  (`python-skill-script-script-style-requirements.md`); a
  previously-missed v015 O2 ripple where
  `version-directories-complete` still required a
  per-version `README.md` unconditionally contradicting
  `minimal`'s no-per-version-README rule.
  **Careful-review pass (second)** caught 2 load-bearing
  fixes: the preceding paragraph of §"Proposed-change file
  format" only named propose-change/critique as `topic`
  sources (broadened for P4 consistency); and a
  self-violation of the P4 disposition caught during that
  broadening — the first draft prescribed an exact
  `topic: out-of-band-edit-<UTC-seconds>` value, which P4's
  reshape explicitly said is implementation choice.
  **Careful-review pass (third)** landed 0 load-bearing fixes
  (final pass per the "continue until a pass lands no
  load-bearing fixes" rule).
  **Dedicated deferred-items-consistency pass** landed 5
  load-bearing findings distinct from the careful-review
  passes: 3 Source-line drift fixes
  (`skill-md-prose-authoring`, `template-prompt-authoring`,
  `enforcement-check-scripts` all lacked v016 widening
  notations despite body text widened elsewhere);
  1 sub-section content update (the v014 N1 SKILL.md-prose
  sub-section still said seed's SKILL.md writes
  `.livespec.jsonc`, stale after P2's wrapper-ownership move);
  1 cross-reference validity fix (two `see PROPOSAL.md §"seed
  — ..."` references pointed at bolded-bullet labels not
  `##`/`###` headings; rewrote as `§"seed" bullet "..."`
  form). Layout-tree drift check: no new files introduced by
  v016; no tree edits required. Example-vs-rule alignment
  check: verified reserve-suffix arithmetic in the worked
  examples (26+9=35; 73→55+9=64; pre-attached suffix strips
  and re-appends cleanly).
  **Cumulative total findings across all 3 careful-review
  passes + 1 deferred-items-consistency pass: 16
  inconsistencies caught and fixed (9 + 2 + 0 + 5).**
  Full decision record is in
  `v016/proposed_changes/proposal-critique-v15-revision.md`.

- **v017** — revise driven by
  `proposed_changes/proposal-critique-v16.md` and its revision.
  A **recreatability-and-cross-doc-consistency cleanup pass**
  surfacing 10 items (Q1-Q10 originally; Q5-original retracted
  mid-interview as a false alarm, renumbering to 9 items
  Q1-Q9). All items accepted at option A. Major structural
  changes:
  **Reserve-suffix canonicalization delegated to deferred-
  items.md** — Q1: PROPOSAL.md §"propose-change → Reserve-
  suffix canonicalization" trimmed to invariants-only (≤64
  chars; suffix preserved intact regardless of pre-attachment
  or truncation-clip; empty → UsageError). The full algorithm
  (pre-strip + truncate-and-hyphen-trim + re-append) lives
  solely in `deferred-items.md`'s `static-check-semantics`
  entry. PROPOSAL.md's prior sketch was strictly smaller than
  the algorithm and would have caused doubled suffixes for
  pre-attached inputs; the sole-source-of-truth move
  eliminates drift risk by construction.
  **Pre-seed template resolution via `--template` flag** —
  Q2: `bin/resolve_template.py` gains an optional
  `--template <value>` flag (alongside the existing
  `--project-root <path>`) that, when supplied, bypasses
  `.livespec.jsonc` lookup and resolves the value directly
  (built-in names → `<bundle-root>/specification-templates/
  <name>/`; other values → relative to `--project-root`).
  `seed/SKILL.md` pre-seed dialogue uses
  `bin/resolve_template.py --project-root . --template
  <chosen>` to resolve the chosen template's `prompts/seed.md`
  before the wrapper has written `.livespec.jsonc`. The v011
  K2 v2+-extensibility shield is extended to cover both the
  stdout contract AND the flag shape (`--project-root`,
  `--template`); v2+ extensions MUST extend the flag set,
  not replace it. Closes the previously-undocumented pre-seed
  template-resolution gap that v014 N1 left open.
  **Import-Linter raise-discipline contract retracted** —
  Q3: v012 L15a's third Import-Linter contract (forbidden
  imports of `livespec.errors` outside `io/**` and
  `errors.py`) is dropped from the illustrative TOML and
  from the authoritative English rules. Rationale:
  Import-Linter cannot distinguish import-for-raising from
  import-for-annotating; blanket-forbidding the imports
  blocks legitimate type-annotation and match-pattern uses
  in `commands/`, `doctor/`, and `validate/` modules. The
  hand-written `check-no-raise-outside-io` covers the
  raise-discipline fully (raise-site enforcement only).
  v012 L15a's claim that Import-Linter "replaces the
  import-surface portion of check-no-raise-outside-io" is
  retracted. The style doc's minimum configuration now has
  two contracts (purity + layered architecture).
  **Seed post-step recovery narration contract expanded** —
  Q4: PROPOSAL.md §"seed → Post-step doctor-static failure
  recovery" adds an explicit narration contract for
  propose-change's expected exit-3 during recovery (its
  post-step trips the same findings that tripped seed's
  post-step; the proposed-change file IS on disk per the
  partial-state-commit pattern). Adds the explicit
  git-commit step between propose-change and revise (so
  `doctor-out-of-band-edits` doesn't trip its pre-backfill
  guard on the next invocation). propose-change's SKILL.md
  prose narrates the exit-3 path distinctly when
  seed-recovery-in-progress is detectable (heuristic: no
  vNNN beyond v001 AND pre-check was skipped).
  **Seed wrapper present-but-invalid `.livespec.jsonc`
  handling** — Q5: PROPOSAL.md §"seed" codifies a third
  branch alongside the v016 P2 absent + present-valid
  branches. Present-but-invalid (JSONC parse failure or
  schema-invalid) → exit 3 with `PreconditionError`
  citing the parse error or schema-violation path.
  Preserves the existing non-doctor fail-fast rule
  (§"Doctor → Bootstrap lenience") and never silently
  overwrites a user's manual edit.
  **Payload-vs-config template mismatch exit code** — Q6:
  the v016 P2 mismatch clause updated from exit 2
  (UsageError) to exit 3 (PreconditionError). The payload
  is a wire-format input (validated against
  `seed_input.schema.json`), not a CLI-argument surface; a
  mismatch between two validated inputs is the
  "incompatible state" category covered by exit 3.
  **Revision-pairing walks filename stems** — Q7:
  PROPOSAL.md §"revise", §"Proposed-change file format",
  and §"doctor → Static-phase checks →
  `revision-to-proposed-change-pairing`" clarify that
  collision-suffix lives in the filename stem
  (`foo-2.md`, `foo-3.md`), distinct from the front-matter
  `topic` field (which carries ONLY the canonical topic
  without the `-N` suffix). Revision-pairing walks
  filename stems — every `<stem>-revision.md` pairs with
  `<stem>.md` — not front-matter `topic` values. Closes
  v014 N6 + v016 P4 interaction ambiguity.
  **Grammar fix at PROPOSAL.md line 853** — Q8: "The
  every doctor-static check's path references parameterize"
  → "Every doctor-static check's path references are
  parameterized". Trivial cleanup.
  **Uniform `--project-root` contract across every
  wrapper** — Q9: PROPOSAL.md §"Sub-command dispatch and
  invocation chain" codifies that every wrapper operating
  on project state (`bin/seed.py`, `bin/propose_change.py`,
  `bin/critique.py`, `bin/revise.py`,
  `bin/prune_history.py`, `bin/doctor_static.py`,
  `bin/resolve_template.py`) accepts
  `--project-root <path>` with default `Path.cwd()`.
  Upward-walk logic to find `.livespec.jsonc` lives in
  `livespec.io.fs` as a shared helper reused by every
  wrapper and by `livespec.doctor.run_static`.
  **Q5-original retracted** — a proposal claiming that
  `tests/e2e/fake_claude.py` needed style-rule exemptions
  (`check-no-inheritance`, strict-dataclass triple, etc.)
  to be SDK-compatible was retracted mid-interview on
  user pushback. The mock is hand-rolled test
  infrastructure that handles input/output streams and
  invokes subprocesses; it complies with every livespec
  Python rule by construction. A feedback memory was
  saved so future sessions don't surface this class of
  false alarm again. The critique file and revision file
  record the retraction; 9 items (Q1-Q9) are the
  finalized set.
  **Deferred-items updates:** 5 existing entries
  scope-widened (`static-check-semantics` for Q1/Q3/Q7/Q9;
  `skill-md-prose-authoring` for Q2/Q4;
  `task-runner-and-ci-config` for Q3;
  `enforcement-check-scripts` for Q3;
  `template-prompt-authoring` for Q2). Two additional
  note-only Source-line widenings from the dedicated
  deferred-items-consistency pass: `user-hosted-custom-
  templates` (Q2 flag-surface freeze) and `claude-md-prose`
  (Q9 `livespec/io/CLAUDE.md` helper mention). 0 new
  entries; 0 removed.
  **Careful-review pass (first)** caught 4 load-bearing
  fixes: revision-file "touched N entries" off-by-one
  (Q5 affects seed wrapper, not schemas); PROPOSAL.md
  §"critique" still duplicated the reserve-suffix
  algorithm despite Q1's invariants-only trim;
  `deferred-items.md` item-schema version range stopped
  at v014 (drift pattern v012 pass 3 caught for other
  entries); revision-file inventory removed the spurious
  `wrapper-input-schemas` entry.
  **Careful-review pass (second)** caught 3 load-bearing
  fixes: PROPOSAL.md §"Per-sub-command SKILL.md body
  structure" step 4 didn't mention Q2's pre-seed
  `--template` flag path; `deferred-items.md`'s
  `static-check-semantics` AST-checks list described
  `check-no-raise-outside-io` with the stale
  v012 L15a import-surface-delegation wording;
  `deferred-items.md`'s `task-runner-and-ci-config` body
  paragraph on Import-Linter mise-pin still described
  three contracts.
  **Careful-review pass (third)** caught 3 interlocking
  fixes for `task-runner-and-ci-config`: Source line
  needed v017 Q3 widening notation (its body had been
  edited in pass 2); revision-file "Carried forward
  unchanged from v016" list included it but pass 2 had
  widened its body; revision-file "touched 4 existing
  entries" claim was now incorrect (5 entries).
  **Careful-review pass (fourth)** caught 3 load-bearing
  fixes: `deferred-items.md`'s `task-runner-and-ci-config`
  v013 M7 subsection still said "three contracts";
  PROPOSAL.md's `dev-tooling/checks/` layout tree
  annotation still claimed Import-Linter "replaced" the
  import-surface portion of `no_raise_outside_io`;
  PROPOSAL.md DoD item 12 said "Import-Linter contracts
  per L15a + v013 M7 minimum-configuration example"
  without the v017 Q3 narrowing; PROPOSAL.md's
  `pyproject.toml` layout entry also updated.
  **Careful-review pass (fifth)** landed 0 load-bearing
  fixes (final pass per the "continue until pass lands no
  load-bearing fixes" rule).
  **Dedicated deferred-items-consistency pass** landed 3
  load-bearing findings distinct from the careful-review
  passes: `template-prompt-authoring`'s v017 Q2 Source-
  line note was "note-only" but the minimal template's
  `prompts/seed.md` delimiter comments must now cover a
  new `bin/resolve_template.py --template` pre-seed
  invocation — rewrote to mark Q2 as a substantive
  widening; `user-hosted-custom-templates` body didn't
  mention the CLI flag surface in the v2+ shield —
  added an explicit paragraph noting that `--project-root`
  + `--template` flag shape is v1-frozen; `claude-md-prose`
  had no mention of the v017 Q9 shared upward-walk helper
  — added a Source-line note covering the
  `livespec/io/CLAUDE.md` obligation.
  Layout-tree drift check: no new files introduced by
  v017. Cross-reference validity: all new Q# cross-
  references resolve to existing headings. Example-vs-
  rule alignment: reserve-suffix worked examples pass the
  arithmetic; PROPOSAL.md §"critique" informal description
  consistent with the full algorithm in deferred-items.
  **Cumulative total findings across all 5 careful-review
  passes + 1 deferred-items-consistency pass: 16
  inconsistencies caught and fixed (4 + 3 + 3 + 3 + 0 + 3).**
  Full decision record is in
  `v017/proposed_changes/proposal-critique-v16-revision.md`.

- **v018** — revise driven by
  `proposed_changes/proposal-critique-v17.md` and its revision.
  A **recreatability-and-integration-gap cleanup pass**
  surfacing 6 items (Q1-Q6) labelled with the NLSpec failure-
  mode framework. Q1 was captured in a prior session (the
  major gap — built-in templates lack sufficient specifications
  for agentic regeneration); Q2-Q6 were surfaced during a
  bootstrap-plan review and user-driven triage in the
  continuation session. All six items accepted at Option A.
  Major structural changes:
  **Template sub-specifications** — Q1: extends
  `SPECIFICATION/` to admit nested sub-specification trees
  under `SPECIFICATION/templates/<name>/` per built-in
  template. Each sub-spec is structurally identical to a
  main-spec tree (own `spec.md`, `contracts.md`,
  `constraints.md`, `scenarios.md`, `proposed_changes/`,
  `history/`) but scoped to the template's internal
  contracts, starter-content policies, and prompt interview
  flows. Template content (`template.json`, `prompts/*.md`,
  `specification-template/`) is agent-generated from each
  sub-spec via `propose-change --spec-target
  SPECIFICATION/templates/<name>` → `revise --spec-target ...`
  cycles, not hand-authored. Doctor-static iterates over
  every spec tree (main + each sub-spec) per-tree, with
  applicability dispatch (`gherkin-blank-line-format`
  conditional per template; `template-exists` /
  `template-files-present` main-tree only; all other checks
  per-tree uniformly). `seed_input.schema.json` widens with
  `sub_specs: list[SubSpecPayload]`; paired
  `SubSpecPayload` schema + dataclass + validator authored.
  `tests/heading-coverage.json` entries carry a `spec_root`
  field. Closes `template-prompt-authoring` deferred entry;
  opens new `sub-spec-structural-formalization` entry. Does
  NOT re-open the v1 "Multi-specification per project"
  non-goal (that non-goal concerns independent specs
  co-existing; this is hierarchical sub-specs of a single
  primary spec — a narrower, strictly smaller model).
  **Bootstrap exception articulated** — Q2: PROPOSAL.md
  §"Self-application" gains an explicit bootstrap-exception
  clause naming first seed as the boundary. Bootstrap
  ordering (steps 1-4, up through first seed) lands
  imperatively; the governed propose-change → revise loop
  becomes MANDATORY from step 5 onward. Hand-editing any
  file under any spec tree or under
  `.claude-plugin/specification-templates/<name>/` after
  first seed is a bug in execution. Applies ONCE per
  livespec repo at initial bootstrap; does NOT apply to v2+
  releases.
  **Initial-vendoring exception** — Q3: PROPOSAL.md
  §"Vendoring discipline" (and style doc mirror) gain a
  one-time 7-step manual procedure for the first population
  of every upstream-sourced vendored lib (`returns`,
  `returns_pyright_plugin`, `fastjsonschema`, `structlog`,
  `jsoncomment`). Applies ONCE per livespec repo at Phase 2
  of the bootstrap plan; post-bootstrap all upstream-
  sourced-lib mutations flow through `just vendor-update`.
  Shim libraries (currently only `typing_extensions`)
  continue following their separate "widened manually via
  code review" rule. Resolves the circularity where
  `just vendor-update` depends on `jsoncomment` which depends
  on itself being vendored.
  **Typechecker + returns-plugin decisions CLOSED at spec
  level** — Q4: PROPOSAL.md adds the `dry-python/returns`
  pyright plugin as the sixth vendored lib at
  `.claude-plugin/scripts/_vendor/returns_pyright_plugin/`
  (BSD-2; LICENSE preserved). `pyproject.toml`'s
  `[tool.pyright]` section declares `pluginPaths =
  ["_vendor/returns_pyright_plugin"]` so strict-mode
  `Result` / `IOResult` inference works without routine
  `# type: ignore`. Typechecker decision: pyright
  (microsoft/pyright), NOT basedpyright — v012 L1+L2 manual
  strict-plus config already enables every diagnostic that
  matters; community-fork maintainer-pool risk outweighs
  basedpyright's defaults-simplification benefit. Closes
  both `returns-pyright-plugin-disposition` and
  `basedpyright-vs-pyright` deferred items.
  **Prompt-QA tier at `tests/prompts/`** — Q5: new
  verification tier under `<repo-root>/tests/prompts/
  <template>/` mirroring each built-in template's REQUIRED
  prompts (seed, propose-change, revise, critique). A
  deterministic prompt-QA harness (scope-distinct from
  `tests/e2e/fake_claude.py`) replays prompt-response pairs
  and asserts on structured output at the input-schema
  boundary PLUS declared semantic properties per prompt.
  Every built-in template ships ≥ 1 prompt-QA test per
  REQUIRED prompt (8 minimum test cases). `just
  check-prompts` runs the suite per-commit as part of
  `just check`. Opens new `prompt-qa-harness` deferred
  entry joint-resolved with
  `sub-spec-structural-formalization` (which supersedes
  the closed `template-prompt-authoring` for prompt
  authoring) and `end-to-end-integration-test`.
  **Companion-doc migration classes formalized** — Q6:
  PROPOSAL.md §"Self-application" gains a "Companion
  documents and migration classes" subsection with three
  classes (MIGRATED-to-SPEC-file / SUPERSEDED-by-section /
  ARCHIVE-ONLY) and a per-doc assignment table covering
  every companion document in `brainstorming/
  approach-2-nlspec-based/` (including `PROPOSAL.md`,
  `goals-and-non-goals.md`, `python-skill-script-style-
  requirements.md`, `subdomains-and-unsolved-routing.md`,
  `prior-art.md`, the four 2026-04-19 lifecycle docs,
  `livespec-nlspec-spec.md`, `deferred-items.md`,
  `critique-interview-prompt.md`,
  `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`) with
  target Phase annotations (Phase 6 / Phase 8 /
  already-shipped / bootstrap-only). Rewrites
  `companion-docs-mapping` deferred entry body to a
  pointer.
  **Deferred-items updates:** 9 existing entries
  scope-widened (`static-check-semantics` per Q1 + Q5;
  `skill-md-prose-authoring` per Q1;
  `enforcement-check-scripts` per Q4 + Q5;
  `task-runner-and-ci-config` per Q3 + Q4 + Q5;
  `wrapper-input-schemas` per Q1; `companion-docs-mapping`
  per Q6 — body rewritten to pointer;
  `end-to-end-integration-test` per Q5;
  `user-hosted-custom-templates` per Q1; `claude-md-prose`
  per Q5). 2 new entries added
  (`sub-spec-structural-formalization`,
  `prompt-qa-harness`). 3 entries CLOSED
  (`template-prompt-authoring`,
  `returns-pyright-plugin-disposition`,
  `basedpyright-vs-pyright`) — closure pointers in their
  bodies reference PROPOSAL.md's closure decisions.
  3 entries carried forward unchanged
  (`python-style-doc-into-constraints`,
  `front-matter-parser`, `local-bundled-model-e2e`).
  **Careful-review pass (first)** caught 6 load-bearing
  fixes (plus 2 deferred-items.md follow-on fixes): stale
  `template-prompt-authoring` references at 4 PROPOSAL.md
  locations (schema-authoring cross-ref; minimal-template
  delimiter joint-resolution; prompt-QA tier joint-
  resolution; E2E section delimiter joint-resolution);
  DoD item 14 needed sub-spec extension; `## Multi-
  specification per project` subsection + non-goal needed
  clarification that Q1's hierarchical-sub-specs is a
  narrower carve-out, not a re-opening of the non-goal;
  deferred-items.md `skill-md-prose-authoring` entry line
  1290 had stale `template-prompt-authoring` cross-ref;
  `end-to-end-integration-test` entry lines 1627-1628 had
  stale joint-resolution language.
  **Careful-review pass (second)** caught 1 load-bearing
  fix: seed wrapper step 5 (sub-spec tree history/v001
  creation) had slightly inconsistent phrasing about
  "same multi-file convention as main livespec template";
  rewrote to say each sub-spec follows its OWN template's
  convention for per-version README presence.
  **Careful-review pass (third)** caught 2 load-bearing
  fixes (revision-file drift): "Carried forward unchanged
  from v017" list omitted `python-style-doc-into-constraints`
  (added); "Scope-widened in v018" list included
  `template-prompt-authoring` which is CLOSED, not widened
  (removed from scope-widened; it remains only in
  "Removed / closed in v018"). The "Outstanding
  follow-ups" count of 9 widened entries was already
  correct.
  **Careful-review pass (fourth)** landed 0 load-bearing
  fixes (final pass per the "continue until pass lands
  no load-bearing fixes" rule).
  **Dedicated deferred-items-consistency pass** caught 1
  load-bearing finding distinct from the careful-review
  passes: PROPOSAL.md `tests/` tree diagram (around the
  Testing-approach section) was missing the `tests/prompts/`
  subtree that v018 Q5 introduces. Added — with
  per-template subdirectories (`livespec/`, `minimal/`),
  each with `test_{seed,propose_change,revise,critique}.py`,
  plus a `CLAUDE.md` at `tests/prompts/` per the v018 Q5
  + claude-md-prose (v018 note-only widening) discipline.
  Source-line drift check: all 9 scope-widened entries
  carry v018 widening notations; 3 closed entries carry
  "CLOSED in v018" notations + closure pointers; 2 new
  entries carry proper "v018 (Qn; new)" Source lines; 3
  carried-forward-unchanged entries have no v018 touch.
  Cross-reference validity: all new Q# cross-references
  (`§"SPECIFICATION directory structure — Template
  sub-specifications"`, `§"Companion documents and
  migration classes"`, `§"Sub-command dispatch and
  invocation chain — Spec-target selection contract"`,
  `§"Prompt-QA tier (per-prompt verification)"`,
  `§"Vendoring discipline"`) resolve to existing
  headings. Example-vs-rule alignment: heading-coverage
  JSON example includes `spec_root` matching the new
  rule; `seed_input.schema.json` example shows `sub_specs`
  field; sub-spec ASCII tree layout correctly distinguishes
  `livespec`-sub-spec's optional README from `minimal`-
  sub-spec's no-README convention.
  **Cumulative total findings across all 4 careful-review
  passes + 1 deferred-items-consistency pass: 10
  inconsistencies caught and fixed (6 + 1 + 2 + 0 + 1).**
  Plan-file ripple:
  `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` was
  already Q1-Option-A aligned from a prior session;
  updated in this cycle for Q2 (bootstrap exception
  cross-referenced in §"Cutover principle"), Q3
  (initial-vendoring procedure referenced in Phase 2), Q4
  (Phase 1 pyproject.toml pluginPaths + typechecker
  decision rationale cross-reference), Q5 (Phase 5 adds
  `tests/prompts/` skeleton + `just check-prompts`), Q6
  (Phase 8's companion-docs-mapping item points at
  PROPOSAL.md migration-classes table). Phase 8's
  canonical list widened to 17 entries (15 + 2 new).
  Full decision record is in
  `v018/proposed_changes/proposal-critique-v17-revision.md`.
- **v019** — fast-track single-issue revise driven by
  `proposed_changes/proposal-critique-v18.md` and its revision.
  Resolves a self-contained logical contradiction in v018
  §"Self-application": steps 2/4 + the Q2 bootstrap-exception
  clause encoded a chicken-and-egg in which step 4 was required
  to implement `propose-change` / `revise` using `propose-change`
  / `revise`, but the imperative-landing window had already closed
  at the end of step 3. v019 Q1 widens step 2 to include
  minimum-viable `propose-change`, `critique`, `revise`
  implementations alongside the seed surface (placing them
  BEFORE the seed, inside the imperative window); step 4 is
  re-narrated as pure widening + remaining-sub-command
  implementation via dogfooded propose-change/revise cycles. The
  Q2 bootstrap-exception clause's "imperative window ends at
  first seed" boundary is unmoved; one acknowledgment sentence is
  appended. No deferred-items entries open or close. No companion
  docs touched. Plan-file ripple:
  `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` re-freezes at
  v019, Phase 3 widens to mirror v019's step 2 scope, Phase 7
  re-narrates as pure dogfood. Full decision record is in
  `v019/proposed_changes/proposal-critique-v18-revision.md`.
- **v020** — four-issue critique-revise driven by
  `proposed_changes/proposal-critique-v19.md` and its revision.
  Closes two shipped-contract defects in the v018 Q1 template-
  sub-specification mechanism plus two plan-level quality
  fixes:
  - **Q1** (PROPOSAL.md, critical) — the `minimal` template's
    sub-spec was described as multi-file (spec.md / contracts.md
    / constraints.md / scenarios.md) under a framing that
    claimed sub-specs are "structurally identical to a main
    spec tree per the template's own conventions" — a claim
    that held for the `livespec` sub-spec but contradicted the
    `minimal` template's own single-file convention. v020 Q1
    reframes sub-specs as livespec-internal artifacts that use
    the multi-file livespec layout uniformly, decoupled from
    the end-user-facing convention of the template the sub-spec
    describes. The `minimal` sub-spec gains a sub-spec-root
    `README.md` and a per-version `README.md` snapshot it did
    not have in v019; both v1 sub-specs become structurally
    identical.
  - **Q2** (PROPOSAL.md, critical) — the `livespec` template's
    seed prompt unconditionally emitted `sub_specs[]` for both
    built-in templates whenever the active main-spec template
    was `livespec`, even though end-user projects that pick
    the `livespec` template don't ship templates of their own
    and have no use for those trees. v020 Q2 makes sub-spec
    emission opt-in via a new pre-seed dialogue question
    ("Does this project ship its own livespec templates?
    default: no"); on "yes", the prompt enumerates user-named
    templates and emits one `sub_specs[]` entry per name; on
    "no" (the default), it emits `sub_specs: []`. The shipped
    seed prompt's behavior becomes uniform across templates;
    livespec-the-project's own bootstrap answers "yes" naming
    the two built-ins.
  - **Q3** (PLAN, medium) — Phase 3's exit-criterion smoke
    test exercised `--spec-target SPECIFICATION` (main tree)
    only, so sub-spec routing escaped the Phase 3 gate and
    only manifested at Phase 7's dogfooded cycles. v020 Q3
    extends the smoke with a second propose-change/revise
    cycle targeting `--spec-target SPECIFICATION/templates/
    livespec`, catching sub-spec routing bugs at the Phase 3
    boundary where recovery is imperative-landing.
  - **Q4** (PLAN, medium) — v019's Phase 3 widened only
    `prompts/seed.md` to "bootstrap-minimum"; the other three
    `livespec`-template prompts stayed at Phase-2 minimum-
    viable level, but Phase 7 then used them to author the
    full final prompt content (its heaviest semantic work,
    including recursively authoring the very prompts being
    used). v020 Q4 widens all four `livespec`-template prompts
    at Phase 3, mirroring the existing seed.md widening
    pattern.
  All four Q1-Q4 accepted at Option A. No deferred-items
  entries open or close. No companion docs touched. Plan-file
  ripple: `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  re-freezes at v020 — Version basis paragraph extended,
  Phase 0 freeze-target updated, Phase 2 (livespec template's
  minimum-viable `prompts/seed.md` includes the new dialogue
  question scaffold), Phase 3 (Q3 + Q4 amendments), Phase 6
  (Q1 minimal sub-spec uniformity + Q2 explicit "yes" answer
  in seed intent block + sub-spec-emission verification at
  Phase 7's revise step), execution prompt re-pointed at
  v020. Full decision record is in
  `v020/proposed_changes/proposal-critique-v19-revision.md`.

## Pointer

The current working `PROPOSAL.md` lives at the parent directory
(`brainstorming/approach-2-nlspec-based/PROPOSAL.md`). It is
byte-identical to `history/v020/PROPOSAL.md` until the next revise.
