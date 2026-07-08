# fleet-check-coverage — Phase-0 inventory of `livespec-dev-tooling` structural checks

Read-only research artifact — the durable Phase-0 classification for the
`plan/fleet-check-coverage/` thread. Its findings resolved open questions OQ1
(generated marker), OQ4 (classification), and OQ5 (first-party predicate) on
2026-07-08; see `design.md` for the resolutions. Package under study:
`/data/projects/livespec-dev-tooling/livespec_dev_tooling/`.

## 0. Where the checks live + how they resolve files

- Check modules: `livespec_dev_tooling/checks/*.py` (one module per check,
  `main() -> int`). Two extra check trees exist:
  `livespec_dev_tooling/driver_checks/plugin_structure.py` and
  `livespec_dev_tooling/workflow_checks/no_stale_revise_branches.py`.
- **Shared config loader:** `livespec_dev_tooling/config.py` — `load_config(*, repo_root)`
  reads the consumer's `[tool.livespec_dev_tooling]` block in `pyproject.toml`
  into a typed `Config` (role keys: `source_trees`, `io_trees`, `commands_trees`,
  `supervisor_entry_files`, `dataclasses_tree`, `pure_trees`, `covered_trees`,
  `source_tree_prefixes`, `tests_tree_prefix`, `target_dirs`, `mirror_pairings`).
  When the block is **absent** it returns `_livespec_core_config()` — the
  hardcoded historical livespec-core layout (this is why core stays green: the
  fallback IS core's real layout).
- **A shared walker ALREADY EXISTS:** `config.iter_py_files(*, root: Path)`
  (config.py:169). It `rglob("*.py")` under a **passed-in root**, skipping any
  path with a `_vendor` or `__pycache__` segment. It is exported in `__all__`.
  **BUT** it derives the universe from a filesystem `root` handed to it by the
  caller (which the caller gets from `load_config`), NOT from `git ls-files`.
  So the choke point exists in *shape* but its universe is still the
  config-driven / hardcoded tree — that is exactly the fail-open surface. The
  fix is to add a git-index-derived universe source (e.g. a new
  `iter_first_party_py_files(*, repo_root)` that shells `git ls-files '*.py'`
  minus exemptions) and route the applies-to-all checks + the partition guard
  through it; `iter_py_files(root=...)` can stay for role-scoped per-tree walks.

Two checks that walk `.py` do NOT use `iter_py_files` and do NOT call
`load_config` — they hardcode their trees with a raw `rglob`/`glob`:
`file_lloc` (the trigger), `main_guard`, `rop_pipeline_shape`,
`supervisor_discipline`, `wrapper_shape`, `tests_mirror_pairing`,
`pbt_coverage_pure_modules`, `no_direct_tool_invocation`.

## 1. The trigger, confirmed

`checks/file_lloc.py:50` hardcodes:
```
_COVERED_TREES = (
    Path(".claude-plugin")/"scripts"/"livespec",
    Path(".claude-plugin")/"scripts"/"bin",
    Path("dev-tooling"),
)
```
`main()` loops `for tree_rel in _COVERED_TREES: root = cwd/tree_rel; if not
root.is_dir(): continue`. In `livespec-orchestrator-beads-fabro` the product
package is `.claude-plugin/scripts/livespec_orchestrator_beads_fabro/` (not
`.../livespec/`), so all three trees miss, the loop walks zero files, and the
check exits 0 while `dispatcher.py` sails past the 250-LLOC hard ceiling. It
never calls `load_config`, so even the config escape hatch is unused.

`checks/no_lloc_soft_warnings.py` (the soft-band 201-250 sibling) DOES call
`load_config` and walks `config.covered_trees` via `iter_py_files` — but it
**no-ops when `covered_trees` is empty** (returns 0 with an info log,
no_lloc_soft_warnings.py:115). So it fails open the same way in a repo whose
`covered_trees` doesn't resolve. Both LLOC checks fail open.

## 2. Full check classification

Legend for "resolves-universe-how":
- **hardcoded** — literal tuple + raw `rglob`/`glob`, no `load_config`.
- **config:`<key>`** — `load_config` + the named `Config` role key.
- **git/spec/yaml/json/fs/ci** — inspects non-`.py` artifacts or external state.

The task asked for a strict binary (applies-to-all / role-scoped). That binary
only fits checks that walk a **first-party `.py` universe**. The remaining
checks inspect YAML / git / spec headings / JSON / CI state and have no `.py`
universe to derive — forcing them into the binary would be misleading, so they
are grouped as **n/a (not a `.py`-universe walk)** with what they inspect noted.

### 2a. applies-to-all — should DERIVE universe from `git ls-files '*.py'` minus exemptions

| check | resolves-universe-how | rationale |
|---|---|---|
| `file_lloc` | hardcoded `_COVERED_TREES` | per-file LLOC ceiling is universal to all first-party `.py`; THE trigger |
| `no_lloc_soft_warnings` | config:`covered_trees` | soft-band LLOC; same universe as file_lloc; carries the severity lever |
| `all_declared` | config:`source_trees` | every module must declare `__all__` — universal |
| `assert_never_exhaustiveness` | config:`source_trees` | every `match` ends `case _: assert_never(...)` — universal |
| `global_writes` | config:`source_trees` | bans `global`/`nonlocal` — universal |
| `keyword_only_args` | config:`source_trees` | `*`-separator on every `def` — universal |
| `match_keyword_only` | config:`source_trees` | keyword-pattern destructuring — universal |
| `no_inheritance` | config:`source_trees` | direct-parent allowlist for `class X(Y)` — universal |
| `private_calls` | config:`source_trees` | no cross-module `_`-prefixed calls — universal |
| `comment_line_anchors` | config:`target_dirs` | bans line-number anchors in comments/docstrings — universal (incl. tests) |
| `main_guard` | hardcoded rglob `livespec/**` | bans `if __name__=="__main__"` in product — universal (currently hardcoded) |
| `rop_pipeline_shape` | hardcoded rglob | structural rule over all `.py` (only bites `@rop_pipeline` classes) |
| `no_write_direct` | config:`covered_trees` (universe) + `commands_trees`/`supervisor_entry_files` (exemptions) | HYBRID: universe is applies-to-all; the write-permitted surfaces are role-scoped exemptions → derive universe, keep exemptions as semantic config |

### 2b. role-scoped — KEEP semantic partition config; ADD a partition-completeness guard

| check | resolves-universe-how | rationale |
|---|---|---|
| `no_except_outside_io` | config:`io_trees`+`commands_trees`+`source_trees`+`supervisor_entry_files` | `try/except` confined to `io/` + supervisors — needs io partition |
| `no_raise_outside_io` | config:`io_trees`+`source_trees` | domain-error raises confined to `io/**`+`errors.py` — needs io partition |
| `public_api_result_typed` | config:`pure_trees` | pure-layer public APIs return Result — needs pure partition |
| `newtype_domain_primitives` | config:`dataclasses_tree` | canonical field names use NewType — one specific subtree |
| `supervisor_discipline` | hardcoded rglob | `sys.exit`/`SystemExit` confined to `bin/*.py` — needs bin partition |
| `wrapper_shape` | hardcoded glob `bin/*.py` | 5-statement shebang-wrapper shape — bin-only |
| `tests_mirror_pairing` | hardcoded rglob | every covered `.py` has a paired test — needs source↔test map |
| `check_coverage_incremental` | config:`mirror_pairings`+`source_tree_prefixes` | path-scoped per-file 100% gate — needs source↔test map |
| `commit_pairs_source_and_test` | config:`source_tree_prefixes`+`tests_tree_prefix` | git-diff: source commit must touch tests — needs source vs test prefixes |
| `tests_no_subprocess_spawn` | config:`tests_tree_prefix` | walks the TEST tree, not product — test-tree partition |
| `pbt_coverage_pure_modules` | hardcoded glob | `@given` in every pure-layer test module — needs pure-test partition |

### 2c. n/a — not a first-party `.py`-universe walk (inspects other artifacts / external state)

| check | inspects |
|---|---|
| `agents_ai_references_resolve` | `AGENTS.md` `.ai/<topic>.md` references (markdown) |
| `aggregate_completeness` | consumer justfile check-slug wiring |
| `branch_protection_alignment` | GitHub branch protection + `ci.yml` |
| `check_mutation` | runs mutmut (RUN/SKIP lever) |
| `check_tools` | pinned tool versions installed |
| `claude_md_coverage` | `CLAUDE.md` presence per in-scope dir (uses `target_dirs` to enumerate dirs, not `.py` shape) |
| `fleet_marketplace_relative_sources` | plugin catalog `marketplace.json` sources |
| `heading_coverage` | spec-tree NLSpec headings vs `heading-coverage.json` |
| `master_ci_green` | latest master CI run status |
| `no_direct_destructive_cli` | agent-facing shell/prose trees for unwrapped destructive CLIs |
| `no_direct_tool_invocation` | `lefthook.yml` + CI YAML only call `just <target>` |
| `no_todo_registry` | `tests/heading-coverage.json` rejects `test: "TODO"` |
| `per_file_coverage` | `coverage.xml` (100% line+branch) |
| `plugin_resolution` | cross-harness plugin-resolution verifier |
| `primary_checkout_commit_refuse_hook_installed` | `.git/hooks/*` presence |
| `red_green_replay` | commit-message TDD trailers + commit range |
| `skill_invocation_paths` | `SKILL.md` fenced-invocation form |
| `tool_backed_check_completeness` | tool-backed checks wired on both surfaces |
| `vendor_manifest` | `.vendor.jsonc` placeholder/shim discipline |
| `driver_checks/plugin_structure` | Driver plugin bundle structure |
| `workflow_checks/no_stale_revise_branches` | stale spec revise branches (git) |

## 3. OQ1 — the "generated code" marker (grounded)

Swept all 8 repos' tracked `.py` for `@generated`, `DO NOT EDIT`,
`autogenerated`, `auto-generated`, `code generated by`, `Generated by`,
`GENERATED FILE`. Also swept for `generated/`-style tracked directories.

Findings:
- **Zero true generated `.py` files exist anywhere in the fleet.** No repo
  commits generator output as `.py`.
- **No `generated/` / `_generated/` / `gen/` tracked directory** exists in any
  of the 8 repos.
- **The single marker hit is a FALSE FRIEND, not generated code:**
  `livespec-runtime/livespec_runtime/work_items/_fractional_indexing.py:5`
  carries `# VERBATIM PORT — DO NOT EDIT (decision 38, G-1)`. This is a
  hand-maintained verbatim port of an upstream algorithm that must not be
  locally edited — it is first-party code that SHOULD still get shape checks,
  and it is NOT codegen output.
- **mutmut output (`mutants/`) is GITIGNORED** in `livespec-dev-tooling`
  (`git check-ignore mutants/` → ignored; `git ls-files 'mutants/*.py'` → 0).
  So deriving the universe from `git ls-files` (not a filesystem `rglob` from
  repo root) automatically excludes the only real generated tree — a point in
  favor of git-index derivation over `rglob`.

Implication for the marker choice: a **bare `# DO NOT EDIT` header sentinel is
already ambiguous** — it collides with the port-fidelity use in
`_fractional_indexing.py`, which must NOT be exempted from shape checks. A
**specific `# @generated` first-line sentinel** has zero current hits, so it
would be unambiguous and collision-free. Since there is presently NO generated
`.py` at all, either mechanism starts empty; the choice is about future-proofing
the convention, and the evidence favors a distinctive sentinel (`# @generated`)
over a bare "DO NOT EDIT" or over an explicit glob list (a glob list has nothing
to enumerate today and would be an empty stanza in every repo).

## 4. OQ5 — first-party `.py` predicate + per-repo counts

Per-repo tracked `.py` counts (via each repo's own `git ls-files`):

| repo | total .py | minus `_vendor/` | minus `_vendor/`+tests | character |
|---|---:|---:|---:|---|
| livespec | 412 | 238 | 116 | genuine product (`.claude-plugin/scripts/` 102, `dev-tooling` 11, `templates` 2, `.claude` 1) |
| livespec-dev-tooling | 207 | 181 | 88 | genuine product (flat `livespec_dev_tooling/` 87, `.claude` 1) |
| livespec-orchestrator-beads-fabro | 211 | 183 | 77 | **the trigger** — product under `.claude-plugin/scripts/` (66) + `dev-tooling` 6 + `orchestrator-image` 2 + `acceptance` 2 + `.claude` 2 |
| livespec-console-beads-fabro | **0** | 0 | 0 | **genuinely codeless** (no Python at all) — must PASS on empty universe |
| livespec-orchestrator-git-jsonl | 102 | 76 | 40 | genuine product (`.claude-plugin/scripts/` 37, `.claude` 2, `acceptance` 1) |
| livespec-runtime | 52 | 52 | 27 | genuine product (flat `livespec_runtime/` 26, `.claude` 1); no `_vendor/` |
| livespec-driver-claude | 9 | 9 | **2** | near-codeless: only 2 first-party non-test `.py`, BOTH hooks |
| livespec-driver-codex | 11 | 11 | **3** | near-codeless: only 3 first-party non-test `.py`, ALL hooks |

Exact non-test first-party `.py` in the small/thin repos:
- `livespec-driver-claude`: `.claude-plugin/hooks/no_shadow_ledger.py`,
  `.claude/hooks/livespec_footgun_guard.py`
- `livespec-driver-codex`: `livespec/hooks/block_auto_memory.py`,
  `livespec/hooks/livespec_footgun_guard.py`, `livespec/hooks/no_shadow_ledger.py`
- `livespec-console-beads-fabro`: (none — zero `.py`)

**Critical correction to the design hypothesis.** The brief assumed the drivers
might be "genuinely codeless pure-prose Drivers" that must PASS on empty. In
reality **both drivers carry first-party hook `.py`** (2 and 3 files) that
deserve shape coverage — they are NOT empty-universe repos. **The ONLY truly
zero-`.py` repo is `livespec-console-beads-fabro`.** So the empty-walk guard's
"legitimately zero → PASS" branch is exercised by the CONSOLE, not by the
drivers. For the drivers the guard should be ACTIVE (non-empty universe) and
their hooks should be claimed/covered — which also raises a wiring question:
whether the thin driver repos even wire the applies-to-all shape checks today.

**`.claude/hooks/*.py` scaffolding is near-universal:** `livespec_footgun_guard.py`
is tracked in 6 of 8 repos under `.claude/hooks/`; the two beads orchestrators
also carry `.claude/hooks/beads_access_guard.py`. These are first-party Python
and would be pulled into the derived universe — the predicate must decide
whether harness hooks are covered (recommended: yes — they run real logic).

**Edge cases found (real, not hypothetical):**
- `templates/orchestrator-plugin/.claude/hooks/{beads_access_guard,github_auth_guard}.py`
  in core — literal `.py` that are **copier template payload** (shipped into
  adopters). Core does NOT walk `templates/` today, so they are currently
  uncovered; a fail-closed git-derived universe would surface them as
  unclaimed first-party `.py`, forcing an explicit keep-or-exclude decision.
- No `conftest.py` / `setup.py` / `noxfile.py` exists OUTSIDE a `tests/` tree in
  any repo — so the "root-level test-infra `.py`" edge case is empty in practice
  (a `tests/`-prefix filter suffices today).
- `_fractional_indexing.py` (see OQ1) — first-party, carries a "DO NOT EDIT"
  port marker; must NOT be swept up by a generated-marker exemption.

**Recommended predicate for "first-party `.py`":**
> A path returned by `git ls-files '*.py'` (run in the repo root) that (a) has
> NO `_vendor` path segment, (b) is not under a configured test tree
> (`tests_tree_prefix`, default `tests/`, plus any `conftest.py`), and (c) does
> not carry the chosen generated-code marker.

The empty-walk guard then FAILS CLOSED iff this set is non-empty but a given
applies-to-all check walked zero of it (or, for role-scoped checks, iff some
member of this set is claimed by NO role tree and is not a named visible
exclusion). It PASSES on a genuinely empty set (the console). Deriving from the
git index (not `rglob`) is what makes it robust: it auto-excludes untracked
scratch like `mutants/` and the `.venv/`, and it is package-name-agnostic (it
finds `livespec_orchestrator_beads_fabro/` without any config).

Secondary candidate (if a lighter touch is wanted): "tracked `*.py` minus
`_vendor/` minus `tests/`" with NO marker clause — simpler, but then
`_fractional_indexing.py` and template payloads are still in-universe (fine) and
there is no exemption path for future codegen. The marker clause is cheap
insurance; recommend keeping it even though it matches nothing today.

## 5. Fan-out / wiring picture (Task 5)

- **Discovery is dynamic.** `livespec_dev_tooling/canonical_checks.py` walks the
  `checks/` package via `pkgutil.iter_modules`, filters `_`-prefixed helpers and
  `__init__`, and maps `snake_case` → `check-kebab-case`. Adding a new
  `checks/<name>.py` automatically extends the canonical slug set — no hardcoded
  registry to update. (`baseline_check_slugs()` is a separate hand-curated
  SUBSET for baseline conformance.)
- **Per-check recipe.** Each check is a standalone module with `main()`, wired in
  every consumer justfile as:
  ```
  check-<slug>:
      uv run python -m livespec_dev_tooling.checks.<slug>
  ```
  (`check-file-lloc` → `...checks.file_lloc`, etc.) The `check:` aggregate lists
  every `check-<slug>` and dispatches them in parallel via
  `livespec_dev_tooling.parallel_check_dispatcher`.
- **Completeness is enforced cross-repo.** `checks/aggregate_completeness.py`
  compares each consumer justfile's wired set (+ alphabetical order) against
  `canonical_check_slugs()`; `livespec/templates/impl-plugin/justfile.jinja`
  stamps the aggregate at copier-copy time; doctor carries a cross-repo
  invariant. So **"wire the new checks" touches:** (1) add `checks/<name>.py`
  here (auto-discovered), (2) add the `check-<slug>:` recipe + its line in the
  `check:` list to EVERY consumer justfile (dev-tooling + each fleet repo) or
  aggregate_completeness fails, (3) the copier `justfile.jinja` for new adopters.
- **Severity lever (warn-vs-fail).** The existing warn/fail mechanism to extend
  lives in `checks/no_lloc_soft_warnings.py`:
  `_FAIL_ENV_VAR = "LIVESPEC_FAIL_IF_LLOC_SOFT_WARNINGS_EXIST"` (line 54);
  `fail = bool(os.environ.get(_FAIL_ENV_VAR))` → offenders log at `error` + exit
  1 when set (CI sets it `true` for the release context), else log at `warning`
  + exit 0. The scan ALWAYS runs (no skip carve-out) — this replaced an older
  `LIVESPEC_RELEASE_GATE` skip. `file_lloc.py` itself has NO env lever: it is the
  per-commit two-tier check (soft warn 201-250, unconditional hard fail >250).
  Extend the `bool(os.environ.get(...))` warn-vs-fail pattern for any new
  applies-to-all check that needs a two-tier severity.
