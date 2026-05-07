# Contracts — `livespec`

This file enumerates the wire-level interfaces between `livespec`'s skill prompts, Python wrappers, and templates. Per `livespec`'s repo-native principle, contracts MUST be language-neutral (JSON or CLI argument shapes), so any tool authored against the contracts works regardless of which language internalizes them.

## Wrapper CLI surface

Every Python wrapper under `.claude-plugin/scripts/bin/<sub-command>.py` MUST accept `--project-root <path>`, defaulting to `Path.cwd()`. Each sub-command adds its own flags above that baseline.

| Sub-command | Required flags | Optional flags |
|---|---|---|
| `seed` | `--seed-json <path>` | `--project-root <path>` |
| `propose-change` | `--findings-json <path>`, `<topic>` (positional) | `--author <id>`, `--reserve-suffix <text>`, `--spec-target <path>`, `--project-root <path>` |
| `critique` | `--findings-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |
| `revise` | `--revise-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |
| `prune-history` | (none) | `--skip-pre-check`, `--run-pre-check`, `--project-root <path>` |
| `doctor` (static) | (none) | `--project-root <path>` |
| `resolve-template` | `--template <value>` (Phase-3-min required; Phase-7 widens to optional) | `--project-root <path>` |

The `--spec-target <path>` flag MUST select a spec tree (the main spec or a sub-spec) explicitly. When omitted, the wrapper SHOULD default to `<project-root>/SPECIFICATION/` (the main spec).

## Lifecycle exit-code table

Every wrapper MUST emit one of the following exit codes:

| Code | Meaning |
|---|---|
| `0` | success — operation completed and any documented stdout was emitted |
| `1` | internal bug — uncaught exception; structured traceback on stderr |
| `2` | `UsageError` — bad CLI invocation (unknown flag, missing required arg, wrong arg count) |
| `3` | `PreconditionError` — project-state precondition not met (missing config, malformed file, idempotency conflict) |
| `4` | `ValidationError` — schema or wire-format validation failure on inbound payload (retryable per the calling SKILL.md's retry-on-exit-4 contract) |
| `127` | too-old Python or missing tool — `_bootstrap.py` early exit |

Domain errors flow as `Failure(<LivespecError>)` payloads on the railway; the supervisor `main()` pattern-matches and lifts the exit code from the error's `exit_code` ClassVar. Bugs propagate as raised exceptions to the supervisor's bug-catcher and result in exit 1.

## Skill ↔ template JSON contracts

The seed flow exchanges a JSON payload conforming to `seed_input.schema.json`. The schema is co-authoritative with its paired dataclass at `livespec/schemas/dataclasses/seed_input.py` per the schema-dataclass-pairing convention (v013 M6). Drift is caught by `dev-tooling/checks/schema_dataclass_pairing.py`.

The propose-change flow ingests `proposal_findings.schema.json`-conforming JSON via `--findings-json <path>`. The critique flow emits `proposal_findings.schema.json`-conforming JSON for downstream propose-change consumption. The doctor flow emits `doctor_findings.schema.json`-conforming JSON to stdout for the supervisor's exit-code derivation.

The revise flow ingests `revise_input.schema.json`-conforming JSON describing per-proposal accept/reject decisions and the resulting spec edits. Future widening MAY add additional payload schemas; each new schema MUST land with its paired dataclass in the same revision.

**Path-relativity documentation requirement.** Every wire-contract schema field that names a spec file path MUST document its path-relativity convention in the field `description`: either *project-root-relative* (e.g., `"SPECIFICATION/contracts.md"`) OR *spec-target-relative* (e.g., `"contracts.md"`). The two conventions MUST NOT be mixed within a single schema. Specifically: `proposal_findings.schema.json` `target_spec_files[]` items are project-root-relative; `revise_input.schema.json` `decisions[].resulting_files[].path` is spec-target-relative. Schema description text is the v1 enforcement surface; the description MUST appear directly on the field (not only in the surrounding human-prose contracts) so it is visible to any LLM or tool inspecting the loaded schema. A future revise cycle MAY add a doctor static check that grep-asserts every schema field whose JSON-pointer path matches `/path/i` or `/file/i` carries one of the two convention strings in its description.

## Sub-spec structural mechanism

Sub-spec emission is opt-in per v020 Q2: the seed prompt's pre-seed dialogue asks "Does this project ship its own livespec templates that should be governed by sub-spec trees?" On "yes", the prompt emits one `sub_specs[]` entry per template named in the dialogue, each carrying a per-template `files[]` array with its own spec-file paths under `<spec_root>/templates/<template_name>/`.

The seed wrapper materializes the main spec tree AND each sub-spec tree atomically per v018 Q1: a single `bin/seed.py --seed-json <payload>` invocation writes, for every spec tree, (a) every template-declared spec file, (b) the skill-owned `proposed_changes/README.md` and `history/README.md` directory-description files, (c) the `history/v001/` snapshot of every template-declared spec file, and (d) the `history/v001/proposed_changes/` subdirectory marker preserved in git via `.gitkeep` when the directory would otherwise be empty. The auto-captured `history/v001/proposed_changes/seed.md` + `seed-revision.md` are emitted for the main spec only; sub-specs do NOT receive auto-captured seed proposals per v018 Q1 — the main-spec `seed.md` documents the multi-tree creation as a whole, and each sub-spec's `history/v001/proposed_changes/` is consequently empty (the `.gitkeep` is the marker).

The `propose-change`, `revise`, and `critique` sub-commands accept `--spec-target <path>` to scope their operation to one specific spec tree. `--spec-target <project-root>/SPECIFICATION/templates/livespec/` targets the `livespec` template's sub-spec; `--spec-target <project-root>/SPECIFICATION/` targets the main spec; etc. The `doctor` sub-command takes only `--project-root`; its multi-tree enumeration is internal (see §"Per-sub-spec doctor parameterization").

## Per-sub-spec doctor parameterization

The doctor static phase runs once per spec tree. The wrapper's main loop enumerates the main spec plus every `<spec_root>/templates/<name>/` sub-spec, runs the static checks against each, and emits per-tree findings on stdout. The wrapper's overall exit code is the worst per-tree code: any `fail` finding lifts the wrapper to exit non-zero.

The static-check registry per v022 D7 is a narrowed enumeration in `livespec/doctor/static/__init__.py`. Each registered check exports `run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]`; the `ctx.spec_root` attribute carries the per-tree root. Per-check applicability dispatch (some checks apply only to main specs, some only to sub-specs) is finalized via the `DoctorContext`'s template-config inspection per v021 Q1.

## Resolved-template stdout contract

`bin/resolve_template.py` MUST emit on success exactly one line: the resolved template directory as an absolute POSIX path, followed by `\n`. Paths containing spaces are emitted literally; callers MUST NOT pipe through shells that re-split on whitespace. The contract is frozen in v1; future template-discovery extensions MUST extend, not replace, the stdout shape and CLI flag set.

## Help-requested escape

Every wrapper MUST treat `-h` / `--help` as a `HelpRequested` signal, emit the argparse-rendered help text on stdout, and exit 0 (NOT exit 2). Per `commands/CLAUDE.md`, `HelpRequested.text` is one of two `commands/`-layer stdout-write exemptions (the other being `resolve_template`'s resolved-path emission).

## Plugin distribution

`livespec` is distributed as a Claude Code plugin via a marketplace catalog at the repo-root path `.claude-plugin/marketplace.json`. The marketplace lists the single plugin declared by `.claude-plugin/plugin.json`.

End-user install path:

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec@livespec
```

The marketplace name (`livespec`) and the plugin name (`livespec`) are independent fields that share the same value by deliberate choice; both names are stable v1 contracts. Renaming either requires a propose-change cycle.

After install, the plugin exposes seven slash commands, namespaced under the plugin name: `/livespec:seed`, `/livespec:propose-change`, `/livespec:critique`, `/livespec:revise`, `/livespec:doctor`, `/livespec:prune-history`, `/livespec:help`. Renaming any command requires a propose-change cycle.

The `marketplace.json` `description` field is a manual duplicate of `plugin.json`'s `description`; `plugin.json` is the source of truth. v1 does NOT enforce equality mechanically; future revise cycles MAY add a doctor static check to detect drift if it becomes operationally relevant.

Plugin uninstall and update flows are Claude Code platform behaviors and are not part of this contract.

### Daily dogfooding path

For maintainer development of the plugin source in this repo, launch Claude Code with `--plugin-dir .` to load the plugin directly from the local source. Live edits to `.claude-plugin/skills/<name>/SKILL.md` and `.claude-plugin/scripts/...` are picked up via `/reload-plugins` without re-installing. The marketplace install path (`/plugin install livespec@livespec`) is for verifying the published install flow; it copies the plugin into `~/.claude/plugins/cache/` and does NOT live-reload.

## Pre-commit step ordering

Lefthook pre-commit runs three commands in order: `00-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `01-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `02-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest. Commit-msg stage runs `just check-red-green-replay {1}` (the v034 D3 replay hook). Pre-push runs `just check` (the full aggregate).

When the staged tree contains ZERO `.py` files, `just check-pre-commit` runs a CONSERVATIVE doc-only subset (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full aggregate, since the Python-related gates have no work to do on doc-only commits. The classification trigger is the strict "zero `.py` staged" predicate; any `.py` file in the staged tree (even a single test file in Red mode) routes through the full aggregate. Pre-push and CI MUST apply the same zero-`.py` subsetting predicate as pre-commit. (a) Pre-push delegates to a new `just check-pre-push` recipe (mirroring `check-pre-commit`) that computes the changeset via `git diff --name-only @{upstream}..HEAD` (falling back to `git diff --name-only origin/master..HEAD` when no upstream is configured); when zero `.py` paths appear in the diff, the recipe delegates to `check-pre-commit-doc-only`; otherwise it delegates to `just check`. (b) CI in `.github/workflows/ci.yml` MUST add a `setup` job that runs `git diff --name-only origin/${{ github.base_ref }}...HEAD` for `pull_request` events (and outputs `py_changed=true` for `push` and `merge_group` events unconditionally, since master/merge-queue must always run the full safety net), exposes `outputs.py_changed`, and the Python-code matrix entries gate on `if: needs.setup.outputs.py_changed == 'true'`. The repo-metadata matrix entries (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) MUST run unconditionally in CI to preserve the metadata safety net. (c) The lefthook `pre-push` stanza in `lefthook.yml` MUST be updated from `run: just check` to `run: just check-pre-push`. (d) The categorization of every `just check` target into either `python-code-checks` or `repo-metadata-checks` MUST be kept synchronized between justfile, lefthook, and CI without drift. The repo-metadata subset is exactly the current `check-pre-commit-doc-only` body: `check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`. Every other target in `just check` is a python-code check.

The zero-`.py` subsetting is sound because the Python-code checks are deterministic functions of the Python source tree; with no `.py` delta in the changeset, every Python-code check would pass-or-fail identically against the merge-base, and any pre-existing failure is a master-branch-state concern (covered by `check-master-ci-green`), not a per-PR concern. Master-branch CI runs (`push` to `master`, `merge_group`) MUST still run the full aggregate as the merge-queue safety net.

## Prompt-QA harness contract

The prompt-QA harness lives at `tests/prompts/_harness.py` as a dedicated test-infrastructure module, NOT a stripped-down `tests/e2e/fake_claude.py` variant. The two harnesses are scope-distinct: the prompt-QA harness performs no LLM round-trip and no wrapper invocation; the e2e harness drives wrappers end-to-end via the Claude Agent SDK surface. The leading underscore on `_harness.py` marks it as test-internal; it is not imported outside `tests/prompts/`.

### Fixture format

Each prompt-QA test case ships under `tests/prompts/<template>/<prompt>/<case>.json` as a JSON document conforming to the fixture-format schema at `tests/prompts/_fixture.schema.json` (validated at load time via `fastjsonschema`). The fixture's required fields are:

- `prompt_name` (string): the REQUIRED-prompt name, one of `"seed"`, `"propose-change"`, `"revise"`, `"critique"`.
- `schema_id` (string): the named wire-contract schema the `replayed_response` MUST validate against — one of `"seed_input.schema.json"`, `"proposal_findings.schema.json"`, `"revise_input.schema.json"`.
- `input_context` (object): the variables the skill prose would pass to the prompt at invocation time. Shape is template-specific.
- `replayed_response` (object): the canonical LLM-output JSON the harness asserts against. Authored alongside the fixture by hand or via a per-prompt regeneration cycle.
- `expected_schema_valid` (boolean): whether `replayed_response` is expected to validate against `schema_id`. The default-true case asserts schema conformance; the false case is reserved for negative-test fixtures (malformed-payload regression coverage).
- `expected_semantic_properties` (array of strings): each entry names a per-template assertion function the harness MUST invoke against `replayed_response`.

### Per-template assertion registry

Each built-in template ships `tests/prompts/<template>/_assertions.py` exporting a module-level `ASSERTIONS: dict[str, Callable[..., None]]` populated via explicit imports per the static-enumeration discipline. Dynamic discovery via `glob+importlib` is forbidden — the dict's contents MUST be visible to pyright strict so registry completeness is type-checkable. Each assertion function MUST accept keyword-only arguments `*, replayed_response: object, input_context: object` and raise `AssertionError` on any property violation. The harness invokes each name listed in `expected_semantic_properties` by lookup against the per-template `ASSERTIONS` dict; an unknown name MUST fail the test with a clear "unknown property name" diagnostic that names the missing assertion.

### Harness behavior

The harness exposes a single primary entry point with keyword-only arguments. Its behavior, in order:

1. Load the fixture file and validate it against `_fixture.schema.json`. Validation failure → `AssertionError`.
2. When `expected_schema_valid` is true, validate `replayed_response` against the JSON Schema named by `schema_id`. Validation failure → `AssertionError`.
3. When `expected_schema_valid` is false, assert that schema validation FAILS (negative-test coverage). Validation pass on a negative-test fixture → `AssertionError`.
4. For each name in `expected_semantic_properties`, look up the function in the per-template `ASSERTIONS` dict and invoke it with `replayed_response` and `input_context` keyword arguments. Any raised `AssertionError` propagates.

The harness does NOT execute the prompt against any LLM; it asserts that the canonical `replayed_response` continues to satisfy the contract. Per-prompt regeneration cycles in Phase 7 items (c) and (d) update fixtures alongside their prompts — if a regenerated prompt no longer satisfies the per-template catalogue's properties, the prompt-QA test fails and the regeneration is rejected.

### Python-rule compliance

The harness module, the fixture-format schema, the per-template assertion modules, and the per-prompt test modules MUST satisfy every livespec Python rule that applies to test infrastructure: each `.py` file declares `__all__`; functions take keyword-only arguments per the universal `*` separator; function and method signatures carry full return-type annotations; dataclasses are `frozen=True, slots=True, kw_only=True`; private helpers carry the leading `_` prefix. Coverage measurement does NOT include `tests/prompts/` — the source list for `[tool.coverage.run]` is anchored at `livespec/`, `bin/`, `dev-tooling/`, so the unit-tier per-file 100% coverage gate does not extend to test infrastructure.

## E2E harness contract

The E2E integration test harness lives at `tests/e2e/fake_claude.py` as a
deterministic mock of the Claude Agent SDK's query-interface surface. It is
NOT the prompt-QA harness (`tests/prompts/_harness.py`); the two harnesses
are scope-distinct: the prompt-QA harness replays prompt-response pairs for
schema + semantic assertions; the E2E harness drives real wrappers end-to-end.

### Harness mode selection

The env var `LIVESPEC_E2E_HARNESS=mock|real` selects the harness tier:

- `mock` — uses `tests/e2e/fake_claude.py`. Invoked by
  `just e2e-test-claude-code-mock` (included in `just check`). Deterministic,
  instant, no LLM API cost. All mock-only scenarios run in this tier.
- `real` — uses the real `claude-agent-sdk` Python library. Invoked by
  `just e2e-test-claude-code-real` (NOT in `just check`). Requires
  `ANTHROPIC_API_KEY` env var. Mock-only scenarios MUST carry explicit pytest
  markers or `skipif` annotations and MUST be skipped in real mode.

### Mock-tier harness interface

`tests/e2e/fake_claude.py` exports one function per livespec sub-command. Each
function:

1. Generates a deterministic JSON payload conforming to the sub-command's
   wire-contract schema (per `SPECIFICATION/contracts.md` §"Skill ↔ template
   JSON contracts").
2. Writes the payload to a temporary file.
3. Invokes the corresponding `bin/<cmd>.py` wrapper as a subprocess via
   `sys.executable`.
4. Returns the `subprocess.CompletedProcess[str]` result.

All functions accept keyword-only arguments and carry full return-type
annotations. The mock DOES NOT stub any wrapper Python code; wrappers always
run for real. The mock replaces ONLY the payload-generation step that a real
LLM would perform.

### Seed-payload path convention

The mock's `seed` function generates a seed payload with the spec file at
`SPECIFICATION/spec.md` (path parts: `["SPECIFICATION", "spec.md"]`). This
two-part path satisfies the seed wrapper's `_MIN_PARTS_MAIN_SPEC = 2`
constraint so that `history/v001/` and `proposed_changes/` are materialized
under `SPECIFICATION/`. The doctor static phase and `prune-history` both
resolve the main spec root as `<project_root>/SPECIFICATION/` by default,
matching this convention.

### Test structure

The E2E test suite lives under `tests/e2e/test_*.py`. Shared tests run in
both mock and real tiers; mock-only scenarios carry explicit pytest markers.

**Happy path** (`test_happy_path.py`): seed → propose-change → critique →
revise → doctor → prune-history against a `tmp_path`-scoped git repo.
Each wrapper step is followed by `git add && git commit` so the
`out-of-band-edits` doctor check sees HEAD-committed spec state. Asserts on
filesystem state after each step (files exist, exit codes 0).

**Error paths**:
- `test_retry_on_exit_4.py` — first propose-change payload is schema-invalid
  (exit 4); second is well-formed (exit 0). Mock-only; real tier skips via
  `pytest.mark.mock_only`.
- `test_doctor_fail_then_fix.py` — pre-seeded `SPECIFICATION/spec.md` containing a normative keyword
  in non-standard capitalization trips `bcp14-keyword-wellformedness`; propose-change +
  revise with `--skip-pre-check` fixes it; second doctor invocation exits 0.
  Runs in both tiers.
- `test_prune_history_noop.py` — project with only `v001` history; prune-history
  emits a `prune-history-no-op` skipped Finding and exits 0. Runs in both tiers.

### Python-rule compliance

`tests/e2e/fake_claude.py` and `tests/e2e/test_*.py` MUST satisfy every
livespec Python rule that applies to test infrastructure: each `.py` file
declares `__all__`; functions take keyword-only arguments per the universal
`*` separator; function and method signatures carry full return-type
annotations; private helpers carry the leading `_` prefix. Coverage
measurement does NOT include `tests/e2e/` — the source list for
`[tool.coverage.run]` is anchored at `livespec/`, `bin/`, `dev-tooling/`, so
the unit-tier per-file 100% coverage gate does not extend to E2E test
infrastructure.
