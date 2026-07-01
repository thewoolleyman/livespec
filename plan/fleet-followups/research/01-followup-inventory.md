# Follow-up inventory — fleet-followups

The full catalog of post-lifecycle follow-ups + lingering cleanup, gathered from
the archived `work-item-state-machine` handoff (its "Post-L2 follow-ups" +
session-8b/8c/9 side-findings) and this session. Grouped by kind. **Status is
read from the ledger, never from this file.** Cross-tenant items are
prose-linked (the fleet pattern); file the UNFILED ones into their named tenant
as `origin:freeform`, 2-step to `backlog`, then groom + dispatch in that repo's
own session.

Epic anchor: **`livespec-jcc6`** (core tenant, `backlog`).

---

## A. Already filed — cite read-only; groom + dispatch in the owning repo's session

| id | tenant | what | next |
|---|---|---|---|
| `livespec-127o` | core | README rewrite (spec-driven): add a README-contract to `SPECIFICATION/` (purpose, audience = zero-knowledge newcomer, required structure, reference-not-duplicate), then author the README to conform. Supersedes the incrementally-grown README (PR #723). | groom |
| `livespec-m0xu` | core | rename `templates/impl-plugin/` → `templates/orchestrator-plugin/` (it scaffolds orchestrator plugins; the name misleads). Plain `open` item filed via raw `bd create`. | groom into the new lifecycle |
| `bd-ib-2wq` | beads-fabro | doctor invariant: fail `just check` / `/livespec:doctor` when any LIVE work-item's status is outside the 7-state set (the enforcement gap — today it's pyright-only, no runtime/audit check). | groom |
| `livespec-dev-tooling-9j8` (+13 children) | dev-tooling | shell-logic hardening epic: substantive logic must live in tested, type-checked, importable code (no logic in shell OR `python -c`/heredocs). Rule + mechanical gates, NOT a ban. 2 ports ready: `9j8.1` (bump-pin rewriters → tested module), `livespec-gnjb` (`export-ci-telemetry.sh` → tested Python + re-stamp template). Doc PR #229 merged. | groom the epic |

## B. Unfiled — tooling / dev-ex bugs (file → groom → dispatch)

1. **Worktree reaper** (`dev-tooling/reap_stale_worktrees.py`) — **CORE** tenant — two bugs: (a) fails on a *relative* `--repo` run from the justfile dir — must pass an absolute path (**CONFIRMED hit 2026-07-01**; `just reap-stale-worktrees livespec` throws, `--repo /data/projects/livespec` works); (b) skips rebase-merged branches whose remotes weren't deleted. Fix both + make the justfile pass an absolute `--repo`.
2. **CORE `propose_change.py` / `revise.py` cwd resolution** — **CORE** tenant — resolve a relative `--spec-target` against **cwd**, not `--project-root`; honor `--project-root` (or document the absolute-path requirement).
3. **CORE `doctor_static.py` missing `--spec-target`** — **CORE** tenant — the flag exists on sibling wrappers; add it for consistency.
4. **No end-to-end `migrate-tenant` CLI** — **beads-fabro** (or runtime) — `legacy_seed` / `register_custom_statuses` are library primitives; wrap into one command so a future tenant onboards in one step (all 9 L2 tracks hand-composed the migration).
5. **Codex TUI `check-codex-skill-picker` blocked by hooks-trust prompt** (CI self-skips) — **driver-codex** / dev-tooling — make it runnable locally or document the skip.

## C. Unfiled — doc / config drift (file → fix)

6. **Stale `capture-work-item` / `plan` prose for v0.3.0** — **CORE** (`.claude-plugin/prose/`) — documents the OLD schema (`status=open` + `priority`, no `rank`); refresh to the 7-state + `rank` model.
7. **driver-codex `.livespec.jsonc` / `CLAUDE.md` say beads connection "DEFERRED"** — **driver-codex** — the tenant is migrated + connected; correct the stale "DEFERRED" wording.
8. **git-jsonl §6 doc-reconcile** — **git-jsonl** — the policy-fields-dropped-on-write behavior is a slice-plan-vs-design §6 tension; reconcile in that repo's design doc.

## D. Unfiled — env / infra

9. **`hydrate` doesn't provision the worktree-pack** (`branch-protection.just` etc.) into fresh worktrees (self-healed via `just install-worktree-pack`) — **fleet / dev-tooling** — make hydrate provision it. Also: the **git-jsonl PRIMARY checkout lacks `branch-protection.just`**.
10. **Branch protection requires checks but 0 reviews** — **fleet / core** — relevant once external contributions arrive; decide the review policy.

## E. Client-side operator actions (NOT factory work-items — do directly)

11. **Orchestrator-plugin cache stale fleet-wide** — client-side `claude plugin update <plugin>@<marketplace> --scope project` (per repo) + restart. (This core session refreshed to `06e3e080ae19` at SessionStart; other scopes may lag.)
12. **openbrain pin bump** needs a client-side `/plugin install` + restart — cannot be done in-session.
13. **Open-item status reclassification** — per-item grooming; a bulk rewrite is available if wanted.

## F. Cross-links — existing threads (resume THERE, not here)

14. **Slice 4 + Slice 6** (`real-work-dispatch.sh` unattended substrate moving off its self-clone + an E2E acceptance proving enabled-plugin dispatch) — **beads-fabro / orchestrator repo** — captured in that repo's thread `plan/orchestrator-plugin-self-containment/handoff.md`; resume there.

---

### Filing note
Core-tenant items (B1, B2, B3, C6, and arguably D9/D10) can be filed from THIS
session (`cd /data/projects/livespec` + the env wrapper, `bd create --type task
--labels origin:freeform` then 2-step `bd update --status backlog`). Cross-tenant
items must be filed from their own repo's session (the `bd` cwd-tenant trap).
