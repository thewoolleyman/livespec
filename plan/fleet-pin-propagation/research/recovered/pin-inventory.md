The research is complete — I did finish it and posted the full report, but it went to my own output rather than to you. Relaying it now in full.

---

# BOTTOM LINE

1. **41 open pin-bump PRs across the fleet, and 100% of them are red.** Zero exceptions. Every fleet repo's `master` CI is green — the redness is exclusive to the auto-generated bump PRs.
2. **The backlog is NOT console-specific — `livespec-runtime` is the worst at 18 stacked PRs** (oldest 2026-07-13), vs. the console's 12. The console was simply the most visible.
3. **Two distinct failure classes bifurcate cleanly by `mergeStateStatus`:** 29 PRs are `DIRTY` (merge-conflicted, superseded garbage — master already pins a *newer* tag than the PR proposes), and 11 are `BLOCKED` (all `livespec-console-beads-fabro`, mergeable but failing a real required check).
4. **The console's `check-completeness` failure is the only genuine, reproducible defect** — a required co-update the fan-out is structurally incapable of performing (it needs a live orchestrator call plus cargo; the fan-out runtime has neither).
5. **6 pin formats are managed by the fan-out; at least 5 more are entirely UNMANAGED**, and **all 3 adopters (`openbrain`, `resume`, `homelab`) have no fan-out wiring at all** — their pins drift silently.

---

# Part 3 — Observed backlog (leading, per your priority order)

**41 open pin-bump PRs. 41 red. 0 green.** All authored by `app/livespec-pr-bot`, all with auto-merge enabled. Meanwhile **every fleet repo's `master` CI is green** (verified 2026-07-19, all 8 `success`).

| Repo | Open pin PRs | Oldest | State breakdown | Dominant failing check(s) on newest PR |
|---|---|---|---|---|
| `livespec` | 2 | #1261, 2026-07-15 | 2 DIRTY | `check-doctor-static`, `check-plan-thread-anchor-declared` |
| `livespec-dev-tooling` | 2 | #418, 2026-07-16 | 2 DIRTY | `check-comment-line-anchors`, `check-commit-pairs-source-and-test`, `check-no-fmt-directives`, `check-partition-completeness`, `check-primary-checkout-commit-refuse-hook-installed`, `check-red-green-replay` |
| `livespec-driver-claude` | 2 | #188, 2026-07-16 | 2 DIRTY | **19 checks fail** on #196 (mass failure incl. `check-no-inheritance`, `check-keyword-only-args`, `check-rop-pipeline-shape`) |
| `livespec-driver-codex` | 2 | #174, 2026-07-17 | 2 DIRTY | **19 checks fail** on #180 (identical cluster to driver-claude) |
| `livespec-orchestrator-beads-fabro` | 1 | #696, 2026-07-16 | 1 UNKNOWN | `check-source-trees-scoped-to-consumer` |
| `livespec-orchestrator-git-jsonl` | 2 | #299, 2026-07-16 | 2 DIRTY | 5-check cluster (same as dev-tooling) |
| **`livespec-runtime`** | **18** | **#206, 2026-07-13** | **18 DIRTY** | #250: 5-check cluster. Older 17: `check-aggregate-completeness` (10) / `check-ci-matrix-completeness` (7) |
| **`livespec-console-beads-fabro`** | **12** | #195, 2026-07-13 | **11 BLOCKED + 1 DIRTY** | **`check-completeness`** — uniformly, on all 11 |
| `openbrain` / `resume` / `homelab` | 0 | — | — | **not wired into the fan-out at all** |

*(Excluded as non-pin PRs: `livespec-dev-tooling#285`, `livespec-driver-claude#214`, `livespec-console-beads-fabro#292`/`#265`.)*

## The bifurcation — and why it matters

**Class A — 29 `DIRTY` PRs (71%): obsolete garbage.** Master has already moved *past* the tag these PRs propose. `livespec-runtime` master pins livespec at **v0.18.0**, while its 18 open PRs propose v0.10.1–v0.11.4 and dev-tooling v0.44.0–v0.46.3. `livespec` master pins dev-tooling at **v0.49.2** while #1341 proposes v0.49.0 and #1261 v0.47.0. These conflict with master (hence `DIRTY`), can never auto-merge, and their red checks are stale artifacts of a July-13/14 base — not live defects. Corroborating: the 17 older `livespec-runtime` PRs fail `check-aggregate-completeness` / `check-ci-matrix-completeness`, the *exact* invariants the fan-out's reconcilers were later built to satisfy (`d90494b`, 2026-07-13; `7dc0d9b`, 2026-07-14 — both landing *after* those PRs were opened). They were never re-run.

**Class B — 11 `BLOCKED` PRs (all `livespec-console-beads-fabro`): one real, reproducible defect.** These are *mergeable* (no conflict — the diff touches only `.livespec.jsonc`) but held by a genuinely failing required check.

### Root cause of the console failure

`livespec-console-beads-fabro#287` diffs exactly one line:

```diff
-      "pinned": "v0.16.0"
+      "pinned": "v0.18.0"
```

But `tests/fixtures/orchestrator-config-manifest.json` still reads `"captured_at_pin": "v0.16.0"`. `check_pin` (`livespec-console-beads-fabro:crates/console-completeness-check/src/lib.rs:379-387`) compares the two and fails on any mismatch. Master is green precisely because both sit at v0.16.0.

The prescribed remedy is `just refresh-config-manifest` (`livespec-console-beads-fabro:justfile:233-234`):

```
refresh-config-manifest DRIVE="livespec-orchestrator-drive":
    {{DRIVE}} --action config-manifest --json | cargo run --quiet --package console-completeness-check -- --refresh
```

**The fan-out cannot possibly run this.** It requires (a) the orchestrator plugin on `PATH`, (b) the credential wrapper and beads/Dolt tenant secret, and (c) a cargo toolchain — and per Part 2 the fan-out job has *none* of the three. This is a structural co-update gap, not a transient failure: **every future console pin bump will fail identically.**

### The accumulation mechanism, stated plainly

`livespec` cut 11 releases between v0.17.0 (2026-07-17) and v0.18.0 (2026-07-19). Each fired a `sibling-released` dispatch. Each dispatch opened a fresh, uniquely-named branch and PR. **No dedupe closes the prior one.** Auto-merge is enabled but never fires because the check is red. Result: monotonic growth, one PR per upstream release, indefinitely.

---

# Part 2 — The fan-out machinery

*(All citations against `livespec-dev-tooling` `origin/master` = `c58ab539`.)*

## 2.1 Pin-freshness (the cron path)

`livespec-dev-tooling:.github/workflows/reusable-pin-freshness.yml`, invoked by each consumer's shim on `schedule: cron '0 13 * * *'` + `workflow_dispatch` (`.github/workflows/pin-freshness.yml:22-32`).

- **Scan**: `livespec_dev_tooling.cross_repo.pin_autodiscovery --root .` (`:116`) — all six managed formats.
- **Staleness rule**: `gh release view` for the latest tag (`:170`), `gh release list --limit 100` for an *ordinal distance* (`:185`); stale iff `ordinal_distance >= staleness_threshold_releases`, default **1** (`:70-75`) — any mismatch at all. The one external pin (`@zed-industries/codex-acp`) uses `npm view` (`:157`) and string inequality (`:160-168`).
- **Action on stale**: opens a **PR — never a direct push**. The `open-bump-pr` job (`:204+`) delegates to the composite action at `:277`.
- **Dedupe against already-open bump PRs: ABSENT.** Grepping `reusable-pin-freshness.yml` and `bump-pin-rewrite/action.yml` for `pr list` / `existing` / `dedupe` found no guard. Branch names are deterministic (`<prefix>-<source_repo>-<tag>`, `action.yml:120-126`), so a *same-tag* re-run would collide on push — but a *new tag* always produces a brand-new branch and PR regardless of how many prior bump PRs sit open. **This is the direct mechanical cause of the stacking in Part 3.**

## 2.2 The bump-pin action — heredoc vs. ported module (your explicit question)

**The `livespec-dev-tooling-9j8.1` claim is TRUE and verified.** Grepping the entire `.github/actions/bump-pin-rewrite/action.yml` — and every other workflow/action YAML in the repo — for `python3 - <<`, `<<'PY'`, `<<-'PY'` returns **zero matches**. Every format arm of the `case "$fmt"` block dispatches to a real module:

| Pin format | `action.yml` line | Module |
|---|---|---|
| `livespec_jsonc_compat_pinned` | `:152` | `cross_repo.pin_rewrite` |
| `pyproject_toml_uv_sources` | `:156` | `cross_repo.pin_rewrite` |
| `vendor_jsonc` | `:160` | `cross_repo.pin_rewrite` |
| `github_workflow_uses_ref` | `:164` | `cross_repo.pin_rewrite` |
| `fabro_sandbox_docker_image` | `:177` | `cross_repo.fabro_image_pin_rewrite` |
| `codex_acp_docker_arg` | `:191` | `cross_repo.codex_acp_pin_rewrite` |
| `unrecognized` | `:193` | `::warning::` skip |
| *(default)* | `:195-197` | `::error::` + `exit 1` |

The modules are genuinely tested. `tests/livespec_dev_tooling/cross_repo/test_pin_rewrite.py` (181 lines) carries a self-guarding regression test — `test_legacy_regex_pin_cases_dispatch_shared_pin_rewrite_module` asserts `"python - <<PYEOF" not in text` against the live `action.yml`, so reintroducing a heredoc fails master. Companions: `test_fabro_image_pin_rewrite.py` (285 lines), `test_codex_acp_pin_rewrite.py` (101 lines).

Two further ported (non-pin-rewriting) reconcilers live in the same action: `justfile_canonical_reconcile` (`action.yml:318`) and `ci_yaml_canonical_reconcile` (`action.yml:352`).

## 2.3 Release dispatch (the event path)

`reusable-release-dispatch.yml`, on `on: release: types: [published]` (`.github/workflows/release-dispatch.yml:20-29`).

- **Consumer discovery**: an unauthenticated raw fetch of core's manifest from `raw.githubusercontent.com/$OWNER/livespec/master/.livespec-fleet-manifest.jsonc` (`:118`), filtered on `.fleet // .members`, excluding the publisher. The GitHub `livespec-sibling` topic is **demoted to a conformance safety net**, not a live source (`:17`).
- **Blocking preflight**: `just check-fleet-conformance` (`:171-175`) against `livespec-dev-tooling` at master, before any dispatch.
- **Dispatch**: one `repository_dispatch` per sibling, `event_type: sibling-released`, payload `{source_repo, tag, release_url}` → `/repos/$OWNER/$SIBLING/dispatches` (`:217`). Soft-fails on 404; `fail-fast: false`.
- **Receiver**: `reusable-bump-pin-from-dispatch.yml`. Re-runs autodiscovery scoped to the source repo (`:167`), no-ops if zero matching pins, else delegates to the same composite action (`:215`) with `branch_prefix: chore/bump` (vs. `chore/freshness-bump` on the cron path — both prefixes are visible in the Part 3 branch names). Carries a stale-SHA rerun guard (`:110-133`) absent from the cron path.

## 2.4 Identity, permissions, and runtime capability (your load-bearing question)

- **Identity**: a GitHub App installation token from `secrets.APP_ID` + `secrets.APP_PRIVATE_KEY` via `actions/create-github-app-token@v1` (`reusable-pin-freshness.yml:90,216,305`; `reusable-release-dispatch.yml:159,189`; `reusable-bump-pin-from-dispatch.yml:98`). Permissions: `contents: write`, `pull-requests: write`, `metadata: read` (`reusable-release-dispatch.yml:9,52-55`). **Empirically confirmed**: every open pin PR is authored by `app/livespec-pr-bot`. The App token is used deliberately *instead of* `GITHUB_TOKEN` so bump commits retrigger required checks (`reusable-bump-pin-from-dispatch.yml:49`).
- **All PRs get auto-merge enabled.** Confirmed live on `livespec-console-beads-fabro#287`, `livespec-runtime#250`/`#206`, `livespec-driver-claude#196` — all `autoMergeRequest != null`. **A red PR therefore sits open indefinitely rather than failing loudly.**
- **Runner**: `ubuntu-latest` uniformly.
- **What the job HAS**:
  - Full checkout of the consumer with `fetch-depth: 0` (`reusable-bump-pin-from-dispatch.yml:104`), plus a second checkout of `livespec-dev-tooling` **at master** into `.livespec-dev-tooling/` (`:148`).
  - `jdx/mise-action@v2` (`:155`) → `uv 0.9.26`, `just 1.36.0`, `lefthook 1.13.6`; then `uv sync --all-groups` (`:158`).
  - It **does** invoke consumer `just` recipes when present: `just vendor-update <lib>` (`action.yml:223`), `just stamp-canonical-slugs` (`:380`), plus `uv lock --refresh-package` relocking and the two canonical reconcilers.
- **What the job LACKS — the constraint that decides everything**:
  - **No Rust/cargo toolchain.** No `dtolnay/rust-toolchain` or equivalent anywhere in the three reusable workflows or the composite action.
  - **No orchestrator plugin, no beads/Dolt credentials, no credential wrapper** — so no live orchestrator call is possible.
  - **It deliberately never runs the consumer's `just check`** (`action.yml:26-32`); the consumer's own PR CI is the sole gate.
  - ⚠️ **Documentation discrepancy**: `bump-pin-from-dispatch.yml`, `reusable-bump-pin-from-dispatch.yml:38`, and `reusable-pin-freshness.yml:52,60` all claim the workflow "runs `just check` to verify the consumer's checks still pass." No such step exists. The only real `just check*` invocation is `just check-fleet-conformance` at `reusable-release-dispatch.yml:175`, against `livespec-dev-tooling` itself. The prose is stale.

## 2.5 `canonical_check_slugs()` and the two different "completeness" checks

- **`canonical_check_slugs()`** — `livespec_dev_tooling/canonical_checks.py:159-167`. **Filesystem-derived, not hardcoded**: `_discover_slugs()` (`:135-156`) walks `livespec_dev_tooling/checks/` via `pkgutil.iter_modules` (`:150`), skips `_`-prefixed helpers and `__init__` (`:153`), maps `snake_case` → `check-kebab-case` (`:155`), returns sorted (`:156`) — "no second source of truth" (`:34-38`). Two hand-curated *subsets* (`_BASELINE_CHECK_SLUGS`, `_WORLD_GATE_CHECK_SLUGS`) are runtime-asserted to be strict subsets.
- **`aggregate_completeness`** — `livespec_dev_tooling/checks/aggregate_completeness.py`. Verifies a consumer's `justfile` `check:` recipe `targets=(…)` array contains every canonical slug (`_emit_missing`, `:297`) in the same alphabetical order, extras allowed only after the canonical block (`_emit_out_of_order`, `:307`; `_compare_canonical_subset`, `:254`). Four failure modes: `justfile_not_found` (`:353`), `check_recipe_not_found` (`:363`), `targets_array_not_found` (`:372`), plus the two comparison findings. `_EXIT_VIOLATIONS = 4` (`:88`).
- **`livespec-console-beads-fabro`'s `check-completeness` is a COMPLETELY SEPARATE Rust check — not a port, not the same invariant.** `crates/console-completeness-check/` (684-line `src/lib.rs`), wired at `livespec-console-beads-fabro:justfile:223-224`. It verifies that every API-configurable key in the orchestrator's `config-manifest` reaches three console surfaces (Settings row, inline help, README doc). **It additionally gates on `check_pin`** (`lib.rs:379-387`) — the mechanism behind the 11 blocked PRs. The two checks share only the English word "completeness."

---

# Part 1 — Every pin format

**Managed** = handled by `pin_autodiscovery` and rewritten by `bump-pin-rewrite` (the six formats at `action.yml:139-199`).

| # | Format / file pattern | Which repos | Example current value | Managed? |
|---|---|---|---|---|
| 1 | `.livespec.jsonc` → `compat.pinned` | All 8 fleet + all 3 adopters | `livespec:.livespec.jsonc:25` `"pinned": "v0.17.5"`; `livespec-console-beads-fabro:.livespec.jsonc:33` `"v0.16.0"` | **YES** (`action.yml:152`) |
| 2 | `pyproject.toml` → `[tool.uv.sources]` git tag | 7 of 8 (not the producer `livespec-dev-tooling`) | `livespec:pyproject.toml:73-74` — dev-tooling `tag = "v0.49.2"`, runtime `tag = "v0.11.0"` | **YES** (`:156`) |
| 3 | `.vendor.jsonc` → `upstream_ref` | `livespec`, `livespec-dev-tooling`, `livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl` | `livespec:.vendor.jsonc` — `livespec_runtime`, `"upstream_ref": "v0.11.0"` | **YES** (`:160`) |
| 4 | `.github/workflows/*.yml` → `uses: thewoolleyman/…@ref` | All 8 fleet | `livespec:.github/workflows/pin-freshness.yml` → `@v0.49.2` | **YES** (`:164`) |
| 5 | `.fabro/**/workflow.toml` → `docker = "…:python[-rust]-vX.Y.Z"` | `livespec-orchestrator-beads-fabro`, `livespec-console-beads-fabro`, `openbrain` | `livespec-console-beads-fabro:.fabro/workflows/implement-work-item/workflow.toml:103-115` | **YES** (`:177`) |
| 6 | `ARG CODEX_ACP_VERSION=…` (external npm) | `livespec-dev-tooling` | resolved via `npm view` (`reusable-pin-freshness.yml:157`) | **YES** (`:191`) |
| 7 | `.mise.toml` `[tools]` | All 8 fleet + `openbrain` | `livespec:.mise.toml:20-22` — `uv 0.9.26`, `just 1.36.0`, `lefthook 1.13.6` | **NO — UNMANAGED** |
| 8 | `.python-version` | All 8 fleet | `3.10.16` (uniform) | **NO — UNMANAGED** |
| 9 | `uv.lock` | 8 repos | transitive from #2 | **INDIRECT** — relocked inside the action, never independently bumped |
| 10 | `Cargo.toml` / `Cargo.lock` (8 crates + `fuzz/`) | `livespec-console-beads-fabro` only | `crates/console-*/Cargo.toml` | **NO — UNMANAGED**; no Rust toolchain in the fan-out at all |
| 11 | `.claude/settings.json` → marketplace `ref` | All 8 fleet + all 3 adopters | `livespec-runtime:.claude/settings.json:58,65,72` — `"ref": "release"` | **NO — UNMANAGED** (deliberately a moving ref) |
| 12 | `tests/fixtures/orchestrator-config-manifest.json` → `captured_at_pin` | `livespec-console-beads-fabro` only | `"captured_at_pin": "v0.16.0"` | **NO — UNMANAGED. This is the co-update gap.** |
| 13 | `.copier-answers.yml` `_commit` | template consumers | — | **Explicitly EXCLUDED by design** (`pin_autodiscovery.py:25`) |

### Current pin state

Latest releases as of 2026-07-19: `livespec` **v0.18.0**, `livespec-dev-tooling` **v0.49.2**, `livespec-runtime` **v0.11.0**.

| Repo | `compat.pinned` (→ core) | `uv.sources` dev-tooling | Workflow `uses:` ref |
|---|---|---|---|
| `livespec` | v0.17.5 (self-pin, 1 behind) | v0.49.2 ✅ | v0.49.2 ✅ |
| `livespec-dev-tooling` | v0.18.0 ✅ | — (producer) | **v0.46.5 — 3 minors stale** |
| `livespec-driver-claude` | v0.18.0 ✅ | v0.49.2 ✅ | v0.49.2 ✅ |
| `livespec-driver-codex` | v0.18.0 ✅ | v0.49.2 ✅ | v0.49.2 ✅ |
| `livespec-orchestrator-beads-fabro` | v0.18.0 ✅ | v0.49.2 ✅ | v0.49.2 ✅ |
| `livespec-orchestrator-git-jsonl` | v0.18.0 ✅ | v0.49.2 ✅ | v0.49.2 ✅ |
| `livespec-runtime` | v0.18.0 ✅ | v0.49.2 ✅ | v0.49.2 ✅ |
| `livespec-console-beads-fabro` | **v0.16.0 — 2 minors stale** | v0.49.2 ✅ | v0.49.2 (only `bump-pin-from-dispatch.yml` shipped) |
| `openbrain` (adopter) | tag present, **no fan-out wiring** | — | — |
| `resume` (adopter) | **v0.7.1 — 11 minors stale** | — | — |
| `homelab` (adopter) | v0.17.1, posture `released` | — | — |

**Two structural gaps:**
- `livespec-dev-tooling` pins its *own* reusable workflows at `@v0.46.5` while every consumer is at `@v0.49.2` — the fan-out producer is the most stale consumer of itself.
- **No adopter is wired into the fan-out.** `openbrain` ships only `deploy-dashboard.yml` + `tripwire.yml`; `resume` ships `auto-enable-merge.yml` + `check.yml`; `homelab` ships no workflows. None carries `bump-pin-from-dispatch.yml`, `pin-freshness.yml`, or `release-dispatch.yml`. `resume` at v0.7.1 vs. current v0.18.0 is the visible consequence.

---

## Explicitly unverified

- **I could not retrieve the console `check-completeness` job log** (`gh run view --job 88152722570 --log` returned empty — likely expired). The root cause is inferred from three independent artifacts that agree conclusively: the PR diff, the fixture's `captured_at_pin` value, and the Rust `check_pin` source. It is not log-confirmed.
- `livespec-orchestrator-beads-fabro#696` reports `mergeStateStatus: UNKNOWN` — GitHub had not finished computing mergeability at query time.
- I did not run any test suite or execute the Python modules; "tested" claims rest on reading the test files.
- I did not audit `reusable-check-matrix.yml` or `fleet-conformance.yml` — out of scope.

## Key file paths for follow-up

- `/data/projects/livespec-dev-tooling/.github/actions/bump-pin-rewrite/action.yml` — the composite action; where a co-update hook would go
- `/data/projects/livespec-dev-tooling/.github/workflows/reusable-pin-freshness.yml` — where dedupe/supersede logic is missing
- `/data/projects/livespec-dev-tooling/livespec_dev_tooling/cross_repo/pin_autodiscovery.py` — the managed-format registry
- `/data/projects/livespec-console-beads-fabro/crates/console-completeness-check/src/lib.rs` — `check_pin` at lines 379-387
- `/data/projects/livespec-console-beads-fabro/justfile` lines 223-234 — the check and its un-runnable remedy
- `/data/projects/livespec/.livespec-fleet-manifest.jsonc` — the authoritative consumer list the dispatch fetches live

No files were written and nothing was mutated — the pass was strictly read-only as briefed.