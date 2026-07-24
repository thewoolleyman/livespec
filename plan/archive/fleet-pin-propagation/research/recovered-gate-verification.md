# Recovered 12-gate verification pass

**Captured:** 2026-07-19, in Fabro sandbox for work-item `livespec-e7lanq`.
**Scope:** verify the recovered table in
`research/recovered/gate-breakage-inventory.md` against the live local fleet
clones available to this run. This is a verification pass over the recovered
inventory, not a new full sweep.

## Inputs checked

Local committed state was checked in the target checkout and the seven sibling
fleet clones under `/workspace/siblings/`:

| Repo | Ref checked |
|---|---|
| `livespec` | current Fabro branch, files compared to the same committed tree |
| `livespec-dev-tooling` | `origin/master` at `307b3c3f9787506d706e3654c7c6c328827597fd` |
| `livespec-console-beads-fabro` | `origin/master` at `df2c8d80d845da362dec1857ab4f75a1ae4ad5e4` |
| `livespec-driver-claude` | `origin/master` at `f570c700ee2369a34d6345234aded214e7684e5a` |
| `livespec-runtime` | `origin/master` at `cf48e8578642277d717c5bd22bd3514796702e91` |
| `livespec-driver-codex` | local sibling clone, `master...origin/master` |
| `livespec-orchestrator-beads-fabro` | local sibling clone, `master...origin/master` |
| `livespec-orchestrator-git-jsonl` | local sibling clone, `master...origin/master` |

The two current snapshot values in the recovered report are stale but not
classification-changing: reusable workflow refs and Fabro sandbox image tags
now read `v0.50.3` in the checked clones, not `v0.49.2`.

## Row verification table

| # | Recovered gate | Status | Verification result |
|---|---|---|---|
| 1 | `check-aggregate-completeness` | **verified** | Exists in dev-tooling and consumer justfiles. `canonical_checks.py` discovers slugs from `livespec_dev_tooling/checks/*.py` by `pkgutil.iter_modules`, filters `_` modules, maps snake case to `check-kebab-case`, and returns sorted slugs. `aggregate_completeness.py` reads the consumer `justfile` `check:` `targets=(...)` array and fails missing or out-of-order canonical slugs. A new check module invalidates the consumer array. |
| 2 | `check-canonical-recipe-fidelity` | **verified** | Exists in dev-tooling and consumer justfiles. The check reads each canonical `check-<slug>:` recipe body and requires the literal shared-module invocation `python -m livespec_dev_tooling.checks.<module>`. A new check module invalidates consumers that lack the new recipe. The recipe body is a fixed derivation from the module name. |
| 3 | `check-ci-matrix-completeness` | **verified** | Exists in dev-tooling and consumer CI/justfiles. The check reads `.github/workflows/ci.yml`, compares CI-covered slugs to the justfile aggregate, and checks `ci-green.needs`. It still carries the `LIVESPEC_FAIL_IF_CI_MATRIX_GAPS_EXIST` severity lever described by the recovery. A new canonical slug invalidates the CI matrix unless reconciled. |
| 4 | `check-no-shadow-ledger-body-identical` | **verified** | Exists in dev-tooling and in both Driver repos' justfiles. The Driver role key `neutral_hook_body_path` points at the shipped hook body, and the check imports `CANONICAL_NO_SHADOW_LEDGER_BODY` from `install_no_shadow_ledger.py` for strict byte-identity. An upstream edit to that constant invalidates the Driver copies. |
| 5 | `check-primary-checkout-commit-refuse-hook-installed` / console `check-baseline` | **verified with correction** | The gate imports `CANONICAL_HOOK_BODY` and the worktree-pack constants from dev-tooling, then verifies installed `.git/hooks/*` plus the optional worktree pack. The recovered "no repo tracks any pack file" remains true in the checked clones: `dev-tooling/worktree-lib.sh`, `branch-protection.sh`, `worktree.just`, and `branch-protection.just` are not tracked or present as committed files. Several repos now install/import the pack as gitignored generated files, so the pack arm is dormant for committed-state pin propagation but can fire locally after `just install-worktree-pack`. |
| 6 | core `check-canonical-slugs-projection` | **verified** | Exists in core `justfile`. It reads `templates/orchestrator-plugin/canonical-slugs.yml`, compares set and order to `livespec_dev_tooling.canonical_checks.canonical_check_slugs()`, and writes the artifact through `just stamp-canonical-slugs`. A dev-tooling pin bump that changes canonical slugs invalidates this committed projection. |
| 7 | core `check-copier-template-smoke` canonical-slug arm | **verified** | The smoke check delegates canonical slug verification to `dev-tooling/checks/copier_template_smoke_canonical.py`. That helper imports `canonical_check_slugs()`, extracts stamped `check-*` targets from the generated justfile, and compares them. It still warns and skips this sub-assertion when `livespec_dev_tooling.canonical_checks` is unavailable, as the recovered inventory said. |
| 8 | console `check-completeness` | **verified** | Exists in the console `justfile`, `just check`, and CI matrix. `tests/fixtures/orchestrator-config-manifest.json` carries `captured_at_pin: v0.16.0`, matching `.livespec.jsonc` on master. `check_pin()` reads `.livespec.jsonc` and the fixture stamp and returns a mismatch on any inequality. `just refresh-config-manifest` pipes `livespec-orchestrator-drive --action config-manifest --json` into the Rust refresh mode, so the refresh needs the live orchestrator drive surface and credentials. |
| 9 | `check-doctor-static` | **verified** | Exists in the six recovered non-core consumers: both Driver repos, both orchestrator repos, runtime, and console. Each CI job checks out core at the consumer's `.livespec.jsonc compat.pinned` ref, exports `LIVESPEC_CORE_PLUGIN_ROOT`, and runs `just check-doctor-static`; each `ci-green` gates it. Core currently has 21 non-helper static doctor checks under `.claude-plugin/scripts/livespec/doctor/static/`. A stricter or new static check invalidates consumer spec/source and generally needs a human source/spec edit. |
| 10 | `github_workflow_uses_ref` reusable workflow contract | **verified with correction** | Reusable workflow `uses:` refs are now at `@v0.50.3` in the checked fleet clones. The dev-tooling `pin_rewrite.py` handler for `github_workflow_uses_ref` rewrites only the `uses: ...@ref` line; it does not reconcile caller `with:` blocks. The reusable workflows still define required `workflow_call.inputs` and required secrets, so a future required input or renamed input can redden callers. The required-input delta is computable, but the correct value for a new input can be judgment-bearing, so the recovered `(b)` classification stands. |
| 11 | `fabro_sandbox_docker_image` | **verified with correction** | Image pins are now at `python-v0.50.3` or `python-rust-v0.50.3` in the checked fleet clones. The dev-tooling `fabro_image_pin_rewrite.py` rewrites GitHub Actions `container.image` lines and Fabro `workflow.toml` `docker =` lines while preserving the layer prefix. Every checked CI job that uses the image starts inside that tag, so a missing or bad registry image fails the job before in-repo repair code can run. The row remains `(b)` because the live registry artifact must exist. |
| 12 | re-vendored `_vendor/livespec_runtime` trees | **verified; recovered unknown resolved** | The vendored tree exists in `livespec`, `livespec-orchestrator-beads-fabro`, and `livespec-orchestrator-git-jsonl`, and the three `.vendor.jsonc` manifests pin `livespec_runtime` at `v0.11.0`. The bump action runs `just vendor-update <lib>` for `vendor_jsonc` records. `_vendor` is excluded from ruff and pyright in the three repos checked. The recovered residual unknown is resolved: `tests_mirror_pairing.py` skips any path containing `_vendor`, and `partition_completeness.py` receives its universe from `filter_first_party_py()`, which excludes any tracked `.py` path with an `_vendor` segment. |

## Self-declared unknowns from recovery

| Unknown | Status | Result |
|---|---|---|
| `f5380aa8` auto-merge bypass mechanism | **unconfirmable from this sandbox** | The recovery already noted GitHub Actions history had aged out. This run did not contact GitHub or re-run the old PRs, and no committed repo state records whether the bypass was warm-cache resolution or branch-protection configuration. The question remains unconfirmed. |
| Adopter ledgers unreachable | **out of scope by rescope** | The work item explicitly resolves adopter scope as out of scope. No adopter gate was added or reconsidered here. |
| `_vendor` exclusion completeness for `partition_completeness` and `tests_mirror_pairing` | **resolved** | Both checks exclude `_vendor`, as recorded in row 12. |
| Work-item bodies listed from `bd list` without full `bd show` | **not needed for this acceptance artifact** | This pass verified the gate inventory against committed repo state. It did not mutate or reconcile Beads ledger items. |

## Missed-gate check

No additional reddenable gate was found in this verification pass.

The check was targeted to avoid re-running the original sweep: I compared the
fan-out's managed pin formats (`.livespec.jsonc`, `pyproject.toml`
`[tool.uv.sources]`, `.vendor.jsonc`, reusable workflow `uses:` refs, Fabro
sandbox image pins, and the external codex-acp Docker ARG) against the
check recipes that read those artifacts or their derived outputs. The matching
surfaces are the same twelve rows above:

- dev-tooling canonical-set consumers: rows 1-5;
- core projection/smoke consumers: rows 6-7;
- console captured-manifest consumer: row 8;
- core doctor-static consumers: row 9;
- reusable workflow contract consumer: row 10;
- Fabro image consumer: row 11;
- vendored runtime consumer: row 12.

Other `check-*` recipes encountered in the targeted pass enforce ordinary
source, test, style, coverage, branch-protection, or ledger invariants. They can
fail on stale branches or unrelated source changes, but the checked source did
not show an additional gate whose read artifact is invalidated by one of the
managed upstream pin rewrites.

