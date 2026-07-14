---
name: project-l2-tenant-migration-runbook
description: "How the work-item-lifecycle L2 thin tenant migration was run for livespec-dev-tooling, and the reusable runbook for the other thin tracks."
metadata: 
  node_type: memory
  type: project
  originSessionId: ff07d325-bf2e-48af-b058-2b00f551112a
---

L2 of the fleet work-item-lifecycle redesign migrated the `livespec-dev-tooling`
beads tenant on 2026-06-29 (epic `livespec-dev-tooling-l2sm`, PR #228, merge
`0522804`). dev-tooling is a **thin migration-only** track (decision 46): tenant
data migrates, **no code/spec change**. The in-repo record is
`plan/work-item-state-machine/` (handoff + research/00).

**Reusable runbook (also for `livespec-driver-claude`, `livespec-driver-codex`,
and the core `livespec` sweep):**

1. **Tenant selection is by PROCESS CWD**, not `StoreConfig`. `bd`'s per-command
   argv carries no `--server*` flags (orchestrator `_beads_client._build_argv`);
   it reads `.beads/config.yaml` from cwd (≡ `bd -C <repo>`). Run every
   tenant-touching command with cwd = the target repo, prefixed with
   `source /data/projects/1password-env-wrapper/with-livespec-env.sh <cmd>`
   (injects `BEADS_DOLT_PASSWORD`; never echo it). A probe from the wrong cwd
   silently reads the wrong tenant.
2. **Register statuses:** `register_custom_statuses` → `bd config set status.custom
   "backlog,pending-approval,ready:active,active:wip,acceptance:wip"` (decision 36;
   idempotent). Verify with `bd config get status.custom`.
3. **Rank backfill = LIVE (non-`done`) heads only.** The enforced doctor invariant
   (orchestrator `dev-tooling/checks/work_item_state_invariants.py` `_rank_findings`)
   and the shipped `rebalance-ranks` `main` (`_rebalance_live`) both EXEMPT `done`
   items, so only live heads need a non-sentinel rank — even though decision 39's
   prose says "whole set." Compute keys with `commands.rebalance_ranks.legacy_seed`
   seeded `priority → captured_at → id`. **Write as a lossless metadata MERGE**
   (`bd update --metadata` replaces the object, so pass `{**existing, "rank": key}`)
   — `store.update_work_item_rank` rebuilds metadata from modeled fields and would
   drop legacy metadata-only `origin`/`gap_id` keys (2 dev-tooling items had them).
4. **No orchestrator-version pin** lives in dev-tooling/driver repo files (host-wide/
   enabled plugin; `.livespec.jsonc` carries only the core-compat pin + tenant
   connection block), so the "bump to v0.3.0 if needed" step is a no-op — drive
   `legacy_seed`/`register_custom_statuses` directly from the L1a-released
   orchestrator code at `/data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts`
   (+ `_vendor` on sys.path).
5. **Anchor epic** in the repo's own tenant, prose-link `livespec-35s3zo` (decision 41 —
   NEVER a typed cross-tenant `depends_on`); close `done` with `audit.merge_sha` after
   the thread PR rebase-merges.

The benign `auto-backup failed … command denied to user '<tenant>'@'%'` warning on
writes is a known non-issue (least-priv tenant user lacks backup-remote grant).

Related: [[project-livespec-sibling-family-cross-repo-coordination]],
[[reference-livespec-1password-setup]]
