# Cloud-Local Memory Cleanup - Inventory Classification

Snapshot captured from `/data/projects/livespec` on 2026-07-13 while driving
`livespec-xhxasg`.

No harness-local memory source file was deleted, moved, or edited during this
slice. This artifact classifies the current records and names the follow-up
owner that should migrate or dispose of each record through its own repo flow.

## Scope Baseline

Fleet members from `.livespec-fleet-manifest.jsonc`:

- `livespec`
- `livespec-dev-tooling`
- `livespec-driver-claude`
- `livespec-driver-codex`
- `livespec-orchestrator-beads-fabro`
- `livespec-orchestrator-git-jsonl`
- `livespec-runtime`
- `livespec-console-beads-fabro`

Registered adopters:

- `openbrain`
- `resume`

Ledger refresh:

| Repo | Work item | Live status | Role |
|---|---|---:|---|
| `livespec` | `livespec-xhxasg` | `ready` | This inventory slice |
| `livespec-dev-tooling` | `livespec-dev-tooling-2amr6x` | `pending-approval` | Migrate `livespec-dev-tooling` local memory |
| `livespec-driver-claude` | `livespec-driver-claude-vx6gmo` | `pending-approval` | Migrate `livespec-driver-claude` local memory |
| `livespec-orchestrator-beads-fabro` | `bd-ib-jz62h3` | `pending-approval` | Migrate `livespec-orchestrator-beads-fabro` local memory |
| `livespec-runtime` | `livespec-runtime-fsumlo` | `pending-approval` | Migrate `livespec-runtime` local memory |
| `openbrain` | `ob-j5oend` | `pending-approval` | Migrate `openbrain` adopter local memory |
| `livespec-driver-claude` | `livespec-driver-claude-vxy7io` | `pending-approval` | Verify Claude Driver auto-memory guard |
| `livespec-driver-codex` | `livespec-driver-codex-ctzk3x` | `pending-approval` | Verify Codex local-memory guard |
| `livespec-dev-tooling` | `livespec-dev-tooling-gcpm3y` | `pending-approval` | Implement consumer-side local-memory drift audit |
| `livespec` | `livespec-eclobt` | `pending-approval` | Quarantine/remove after durable destinations land |

All non-inventory slices still depend on `livespec-xhxasg`.

## Snapshot Commands

Claude:

```bash
find /home/ubuntu/.claude/projects -maxdepth 3 -type f -path '*/memory/*.md' -print | sort
```

Codex:

```bash
find /home/ubuntu/.codex/memories -maxdepth 3 -type f -print
sqlite3 /home/ubuntu/.codex/memories_1.sqlite '.tables'
sqlite3 /home/ubuntu/.codex/memories_1.sqlite 'select count(*) from jobs; select count(*) from stage1_outputs;'
```

## Snapshot Summary

Claude local memory currently has 95 markdown files:

| Slug | Files | Classification |
|---|---:|---|
| `-data-projects-livespec` | 0 | Fleet member, no Claude records |
| `-data-projects-livespec-dev-tooling` | 9 | Fleet member, migrate via `livespec-dev-tooling-2amr6x` |
| `-data-projects-livespec-driver-claude` | 2 | Fleet member, migrate via `livespec-driver-claude-vx6gmo` |
| `-data-projects-livespec-driver-codex` | 0 | Fleet member, no Claude records |
| `-data-projects-livespec-orchestrator-beads-fabro` | 2 | Fleet member, migrate via `bd-ib-jz62h3` |
| `-data-projects-livespec-orchestrator-git-jsonl` | 0 | Fleet member, no Claude records |
| `-data-projects-livespec-runtime` | 7 | Fleet member, migrate via `livespec-runtime-fsumlo` |
| `-data-projects-livespec-console-beads-fabro` | 0 | Fleet member, no Claude records |
| `-data-projects-openbrain` | 47 | Registered adopter, migrate via `ob-j5oend` |
| `-data-projects-resume` | 0 | Registered adopter, no Claude records |
| Other slugs | 28 | Adjacent or non-governed; retain unless a later owner-specific cleanup includes them |

Codex local memory:

- `/home/ubuntu/.codex/memories/` exists and contains no files.
- `/home/ubuntu/.codex/memories_1.sqlite` exists.
- SQLite tables present: `_sqlx_migrations`, `jobs`, `stage1_outputs`.
- `jobs` row count: 0.
- `stage1_outputs` row count: 0.

## Classification Rules Used

- `index`: a local `MEMORY.md` index of other files in the same memory store.
- `durable-guidance`: maintainer preference, repo convention, process rule, or
  tool-use discipline that belongs in `AGENTS.md` or a referenced `.ai/*.md`.
- `project-runbook`: concrete operational state or procedure for a repo; migrate
  only after checking current repo docs/spec/work-items for newer truth.
- `trackable-work-or-spec`: content that should become, or be reconciled with,
  a spec change or work item instead of copied as static guidance.
- `adjacent-non-governed`: not in the current fleet/adopter set; out of scope
  for this slice.
- `resolved-historical`: useful only as archive context if the owning repo still
  lacks a durable history record.

## Fleet And Adopter Records

### `livespec`

No Claude `memory/*.md` files were observed for
`/home/ubuntu/.claude/projects/-data-projects-livespec/`.

### `livespec-dev-tooling`

Migration owner: `livespec-dev-tooling-2amr6x`.

| File | SHA-256 prefix | Class | Disposition |
|---|---|---|---|
| `MEMORY.md` | `3f4559cdded6` | `index` | Rebuild or drop after child migration; do not migrate as guidance by itself |
| `feedback_heading_coverage_pairing.md` | `5eb7ae5a0162` | `durable-guidance` | Reconcile with current `AGENTS.md` / `.ai` heading-coverage guidance |
| `feedback_livespec_commit_prefixes.md` | `a7b8122ff00f` | `durable-guidance` | Reconcile with repo-specific commit-prefix/TDD guidance |
| `feedback_no_spammy_bot_notifications.md` | `901a3864b208` | `durable-guidance` | Migrate as maintainer signaling preference if not already present |
| `feedback_revise_payload_format.md` | `ae441196bc41` | `durable-guidance` | Reconcile with livespec revise/propose-change instructions |
| `project_l2_tenant_migration_runbook.md` | `1bc491956ac0` | `project-runbook` | Preserve as L2 migration runbook or mark obsolete after checking current plan/spec |
| `project_livespec_sibling_family_cross_repo_coordination.md` | `5cefe505b690` | `project-runbook` | Reconcile with current fleet coordination docs; likely historical after newer fleet-manifest work |
| `project_reference_discipline_in_flight.md` | `2bd4c8a8a40c` | `trackable-work-or-spec` | Check whether the referenced upstream proposal has landed; file/close work instead of copying stale state |
| `reference_livespec_1password_setup.md` | `bc9fff4a47ce` | `durable-guidance` | Migrate only as secret-handling guidance; contains locations, not secret values |

### `livespec-driver-claude`

Migration owner: `livespec-driver-claude-vx6gmo`.

| File | SHA-256 prefix | Class | Disposition |
|---|---|---|---|
| `MEMORY.md` | `ed22bea0d28e` | `index` | Rebuild or drop after child migration |
| `l2-migration-work-item-state-machine.md` | `70911d91656f` | `project-runbook` | Preserve or archive L2 tenant migration completion state after checking current repo docs/spec |

### `livespec-driver-codex`

No Claude `memory/*.md` files were observed for
`/home/ubuntu/.claude/projects/-data-projects-livespec-driver-codex/`.

Guard follow-up remains `livespec-driver-codex-ctzk3x` because Codex's
background memory store is a separate enforcement concern even though the
current host store is empty.

### `livespec-orchestrator-beads-fabro`

Migration owner: `bd-ib-jz62h3`.

| File | SHA-256 prefix | Class | Disposition |
|---|---|---|---|
| `MEMORY.md` | `e2e250f524d9` | `index` | Rebuild or drop after child migration |
| `wism-l1a-rollout-state.md` | `17f8b35c3786` | `project-runbook` | Preserve or archive work-item-state-machine rollout completion state after checking current plan/spec |

### `livespec-orchestrator-git-jsonl`

No Claude `memory/*.md` files were observed for
`/home/ubuntu/.claude/projects/-data-projects-livespec-orchestrator-git-jsonl/`.

### `livespec-runtime`

Migration owner: `livespec-runtime-fsumlo`.

| File | SHA-256 prefix | Class | Disposition |
|---|---|---|---|
| `MEMORY.md` | `bd3b221c7571` | `index` | Rebuild or drop after child migration |
| `feedback_be_more_autonomous.md` | `6dbb57a3bbd5` | `durable-guidance` | Reconcile with current maintainer-working guidance in `AGENTS.md` / `.ai` |
| `feedback_draft_dont_materialize_propose_change.md` | `b658e5fc147d` | `durable-guidance` | Migrate if still valid for maintainer-owned revise gates |
| `feedback_worktree_discipline.md` | `3344bf273e4f` | `durable-guidance` | Reconcile with current worktree -> PR -> merge -> cleanup discipline |
| `reference_bd_autobackup_denial_by_design.md` | `37764acdace6` | `durable-guidance` | Migrate as beads-runtime operational guidance if not already in fleet core |
| `reference_beads_tenant_access.md` | `348f5170c5ac` | `durable-guidance` | Reconcile with current beads runtime prerequisites and wrapper guidance |
| `reference_livespec_repo_is_bare.md` | `cf4641660283` | `resolved-historical` | Verify current `/data/projects/livespec` config; archive or drop if obsolete |

### `livespec-console-beads-fabro`

No Claude `memory/*.md` files were observed for
`/home/ubuntu/.claude/projects/-data-projects-livespec-console-beads-fabro/`.

### `openbrain`

Migration owner: `ob-j5oend`.

| File | SHA-256 prefix | Class | Disposition |
|---|---|---|---|
| `MEMORY.md` | `b8a24bd6b202` | `index` | Rebuild or drop after child migration |
| `feedback_bd_close_force.md` | `f736e4c8c634` | `durable-guidance` | Migrate if still valid for conservative dependency closures |
| `feedback_bd_dolt_sync_outpaces_git.md` | `c7531d7f919d` | `project-runbook` | Preserve as beads/Dolt sync hazard if still current |
| `feedback_deploy_via_wrappers.md` | `c3a6f8a3ec65` | `durable-guidance` | Migrate to openbrain deploy/operator guidance |
| `feedback_deps_via_mise.md` | `9e0f91c2248e` | `durable-guidance` | Migrate to dependency/tooling guidance |
| `feedback_dont_chase_infra_during_critique.md` | `d4c26417906a` | `durable-guidance` | Migrate as task-focus guidance |
| `feedback_drive_external_uis_yourself.md` | `03e798f244b6` | `durable-guidance` | Migrate as external UI/OAuth workflow guidance |
| `feedback_embeddings_always_available.md` | `361b89402a52` | `durable-guidance` | Migrate if still a system invariant |
| `feedback_fast_forward_execution.md` | `f79ea7f97c75` | `durable-guidance` | Migrate as track authorization guidance |
| `feedback_fetch_before_declaring_absent.md` | `afa33ba4624f` | `durable-guidance` | Migrate as stale-checkout discipline |
| `feedback_file_colocation.md` | `d13dcf5c2c12` | `durable-guidance` | Migrate as file-placement convention |
| `feedback_finish_what_we_started.md` | `b5950f650085` | `durable-guidance` | Migrate if still desired prioritization guidance |
| `feedback_harness_not_library.md` | `e04d25fe45f6` | `durable-guidance` | Migrate as package/dependency interpretation guidance |
| `feedback_match_domain_vocabulary.md` | `fd09cdbb9b69` | `durable-guidance` | Migrate as spec vocabulary discipline |
| `feedback_no_manual_auth.md` | `e39a3c9f15c9` | `durable-guidance` | Migrate as auth/token preference |
| `feedback_one_time_cost_permanent_benefit.md` | `e7b02c078ffe` | `durable-guidance` | Migrate if still desired decision heuristic |
| `feedback_otlp_export_ok_not_proof.md` | `0a9d12287677` | `durable-guidance` | Migrate as observability verification guidance |
| `feedback_plan_before_implement.md` | `e72c8f38e3ef` | `durable-guidance` | Migrate as spec-first discipline |
| `feedback_query_workitems_via_skill.md` | `69ef1ed9a00a` | `durable-guidance` | Migrate as work-item access guidance |
| `feedback_recommend_dont_present.md` | `c426cd611f46` | `durable-guidance` | Migrate as maintainer-interaction guidance |
| `feedback_revise_resulting_files_fresh.md` | `69ab3383e92f` | `durable-guidance` | Migrate as revise payload freshness guidance |
| `feedback_secrets_guard_triple_equals.md` | `31363d955575` | `durable-guidance` | Migrate as committed-code secret-guard convention |
| `feedback_subagent_jsonl_pane.md` | `9e657bdbcecf` | `durable-guidance` | Migrate only if openbrain still uses that subagent tmux pattern |
| `feedback_supabase_reserved_env.md` | `01bc6ccb9fd1` | `durable-guidance` | Migrate as Supabase env-var convention |
| `feedback_third_party_docs_first.md` | `a9e68fb840c1` | `durable-guidance` | Migrate as third-party surprise handling guidance |
| `feedback_track_authorization.md` | `b2257f647bc9` | `durable-guidance` | Migrate as standing authorization rule if still accepted |
| `feedback_vercel_serverless_otel.md` | `12fd513d40ca` | `durable-guidance` | Migrate as Vercel OTel implementation guidance |
| `feedback_verify_external_contracts.md` | `265035c703be` | `durable-guidance` | Migrate as external-contract verification discipline |
| `feedback_verify_external_ui_before_instructing.md` | `3e3dfcb1175b` | `durable-guidance` | Migrate as external UI guidance |
| `feedback_why_before_mechanics.md` | `431a4c3eeac6` | `durable-guidance` | Migrate as communication style guidance |
| `feedback_worktree_node_modules.md` | `ca5156df27cc` | `durable-guidance` | Migrate as worktree hydration guidance if still current |
| `project_beads_retired.md` | `9f6e3aa49e09` | `resolved-historical` | Do not copy as active guidance without preserving its superseded notice |
| `project_deploy_prod_detached_head.md` | `380b7aaaf4d6` | `project-runbook` | Verify current deploy wrappers before migrating |
| `project_gmail_backfill_contract_drift.md` | `bf5879c7eff1` | `resolved-historical` | Archive only if the resolved drift record is still useful |
| `project_honeycomb_ingest_key_only.md` | `bd04fa5e7235` | `project-runbook` | Migrate if current Honeycomb account posture is unchanged |
| `project_impl_plaintext_skills_unregistered.md` | `89194253ac94` | `resolved-historical` | Archive only; do not copy as active install guidance without current verification |
| `project_livespec_simulated.md` | `4220ec5fb6ba` | `resolved-historical` | Archive only; superseded by current plugin install path |
| `project_no_cd_manual_deploy.md` | `256e4a4d60f5` | `project-runbook` | Verify current dashboard deploy policy before migrating |
| `project_ob1_permanent_fork.md` | `ee2f27ad28d9` | `project-runbook` | Migrate if OB1 fork policy remains current |
| `project_op_environments_beta_only.md` | `49f29b1812e3` | `project-runbook` | Reverify 1Password CLI version state before migrating because it may be time-sensitive |
| `project_prompts_handoff_convention.md` | `b435ca292f51` | `durable-guidance` | Migrate to prompt/handoff instructions if still active |
| `project_reconcile_read_only.md` | `6a8b0e93dcc5` | `project-runbook` | Migrate if Obsidian reconcile contract remains current |
| `project_secret_management.md` | `a3a540970f8b` | `durable-guidance` | Migrate as secret-management guidance; contains process, not secret values |
| `project_shared_primary_checkout_collisions.md` | `7aeb22a759d0` | `durable-guidance` | Reconcile with current openbrain worktree-only mutation protocol |
| `project_smoke_obsidian_stale_redherring.md` | `595edb2be8de` | `project-runbook` | Migrate if smoke/health behavior remains current |
| `project_upstream_crossrepo_gate.md` | `78bf04005e41` | `trackable-work-or-spec` | Check whether referenced upstream livespec blockers are now closed before migrating |
| `reference_livespec_doctor_dev_tooling_bug.md` | `d5cd9d39ce1a` | `resolved-historical` | Archive only; note says resolved in 2026-06-12 |

### `resume`

No Claude `memory/*.md` files were observed for
`/home/ubuntu/.claude/projects/-data-projects-resume/`.

## Adjacent Or Non-Governed Claude Records

These slugs are not current fleet members or registered adopters. They should
not be removed by the fleet/adopter cleanup unless a later owner-specific
decision brings them into scope.

| Slug | Files | Disposition |
|---|---:|---|
| `-data-projects-beads` | 3 | Adjacent/non-governed; retain |
| `-data-projects-kilroy` | 3 | Adjacent/non-governed; retain |
| `-data-projects-livespec-impl-plaintext` | 8 | Historical retired livespec impl repo; retain unless explicitly covered by cleanup follow-up |
| `-data-projects-vps-info` | 10 | Adjacent/non-governed; retain |
| `-home-ubuntu-gt-personal-knowledge-base-polecats-quartz-personal-knowledge-base` | 1 | Adjacent/non-governed; retain |
| `-home-ubuntu-gt-personal-knowledge-base-refinery-rig` | 2 | Adjacent/non-governed; retain |
| `-home-ubuntu-tmp` | 1 | Adjacent/non-governed scratch; retain in this slice |

## Follow-Up Routing

Recommended order after this slice lands:

1. Run the five migration work items that have observed source files:
   `livespec-dev-tooling-2amr6x`, `livespec-driver-claude-vx6gmo`,
   `bd-ib-jz62h3`, `livespec-runtime-fsumlo`, and `ob-j5oend`.
2. Run the guard/audit work items:
   `livespec-driver-claude-vxy7io`, `livespec-driver-codex-ctzk3x`, and
   `livespec-dev-tooling-gcpm3y`.
3. Run `livespec-eclobt` only after durable destinations have landed or each
   source file has been explicitly classified as ephemeral.

Migration work should not blindly copy memory bodies. Each owner should compare
the memory record against current `AGENTS.md`, `.ai/*.md`, `SPECIFICATION/`,
plan files, and work-item state first. Several records are already resolved or
time-sensitive and should become archive notes or cleanup confirmations rather
than active instructions.
