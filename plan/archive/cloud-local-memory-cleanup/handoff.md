# Cloud-Local Memory Cleanup — Handoff

## STATUS: COMPLETE (2026-07-14). No work remains. Do NOT re-run any step.

The entire `livespec-xei45t` epic is finished and verified. Every slice is
closed in the ledger, all PRs are merged, the source memory files are deleted,
and the deletion is fully recoverable from committed archives. **The only open
item is a maintainer decision to formally close/archive this plan thread and
remove it from the overseer track list** — there is no engineering work left.

If you are a fresh session that was told to "read this handoff and follow it":
there is nothing to build. Confirm the state below still holds if you wish, then
surface to the maintainer that the epic is complete and awaits their close/
archive decision. Do NOT re-run migrations, guards, archiving, or `eclobt` — they
are done, and re-running `eclobt` would try to delete already-deleted files.

## Final outcome — every slice

| Owning repo | Work item | Status | Outcome |
|---|---|---|---|
| `livespec` | `livespec-xhxasg` | done | Inventory + classification |
| `livespec-dev-tooling` | `dgin5n` | done | Source-evidence guard (pre-session) |
| `livespec-dev-tooling` | `gcpm3y` | done | Consumer-side `local_memory_drift_audit`, CI-wired (pre-session) |
| `livespec-dev-tooling` | `2amr6x` | done | Memory → `.ai/*` (PR #380, merged) |
| `livespec-driver-claude` | `vx6gmo` | done | Memory → `.ai/beads-tenant.md` (PR #163, merged) |
| `livespec-runtime` | `fsumlo` | done | Memory → `AGENTS.md` (PR #216, merged) |
| `openbrain` | `ob-j5oend` | done | Memory → openbrain durable homes (PR #5, merged) |
| `livespec-orchestrator-beads-fabro` | `bd-ib-jz62h3` | done | Migrated pre-session |
| `livespec-driver-claude` | `vxy7io` | done | `block_auto_memory.py` guard VERIFIED (no change) |
| `livespec-driver-codex` | `ctzk3x` | done | Codex background-memory audit `Stop` hook added (PR #148, merged) |
| `livespec` | `livespec-eclobt` | **done** | Deleted 67 source memory files; ledger closed |

### Follow-ups that also landed this session

- **Hook-drift → spec (maintainer-directed):** `capture-spec-drift` in
  `livespec-driver-codex` found the new `codex_background_memory_audit` Stop hook
  (from PR #148) was undocumented. Filed a propose-change → independent Fable
  review (caught + fixed one ownership-routing blocker) → ratified as
  **`livespec-driver-codex` PR #151** (spec `contracts.md` §"Hook bundle" now
  says FOUR hooks; `history/v005`). The two family-standard hooks
  (`block_auto_memory`, `no_shadow_ledger`) were already documented — no other
  drift.
- **Archive-before-delete:** fleet 20 snapshots → `livespec`
  `plan/cloud-local-memory-cleanup/archived-source-memory/<slug>/` (**PR #1230**);
  openbrain 47 snapshots → `openbrain` `plan/local-memory-archive/` (**PR #6**).
  Byte-verified; 2 openbrain files minimally de-fanged (`<SECRET_NAME>`
  placeholders) to pass `secrets-guard`, noted inline.
- **`feedback_subagent_jsonl_pane.md`** — maintainer chose ARCHIVE-ONLY (not
  migrated into openbrain active guidance). Archived + deleted with the rest.
- **`livespec-eclobt`:** deleted all 67 host-local memory files (dev-tooling 9,
  driver-claude 2, runtime 7, orchestrator-beads-fabro 2, openbrain 47), each
  verified archive-preserved first. All 5 governed stores now empty. The 28
  adjacent/non-governed slugs (`beads`, `vps-info`, etc.) were out of scope and
  remain.

## Prevention (why this won't silently recur)

The Driver plugins (`livespec-driver-claude`, `livespec-driver-codex`) ship
`block_auto_memory.py`, a `PreToolUse` hook that blocks writing durable guidance
into `~/.claude`/`~/.codex` local memory and routes it to `AGENTS.md`/`.ai`. It
is auto-active in every repo that enables the Driver plugin — including openbrain
(adopters inherit it via plugin enablement; they do not implement it). The Codex
Driver also now ships a warn-only `Stop` background-memory audit hook.

## Durable facts worth keeping (for future fleet work)

- **Local-memory migrations must run HOST-LOCAL** (direct
  `codex exec --dangerously-bypass-approvals-and-sandbox -C <repo>`); a Fabro
  sandbox / the `codex:codex-rescue` forwarder fails closed (EROFS) because it
  cannot see `~/.claude/projects/...`.
- **The fleet auto-merges green PRs** (`livespec-pr-bot` + `auto-enable-merge.yml`);
  drafting a PR is the only reliable hold. **openbrain has NO auto-merge bot** —
  its PRs must be merged explicitly (or land via direct push).
- **`openbrain` is an INDEPENDENT beads tenant** — `bd` uses its own
  `/data/projects/1password-env-wrapper/with-openbrain-env.sh`, not the fleet
  `with-livespec-env.sh`.
- **Recoverability:** every deleted memory file is preserved verbatim (2 openbrain
  files with noted de-fangs) in the two archive locations above.

## Optional open item for the maintainer

Post-merge look at `livespec-driver-codex` PR #148 if desired (a new shipped
warn-only Stop hook that auto-merged before it could be held; warn-only +
100%-tested + now spec-documented via #151; revert available). Not blocking.

## Thread Anchor

Ledger epic: `livespec-xei45t` (this epic is done). Owning repo: `livespec`.
Plan thread path: `plan/cloud-local-memory-cleanup/`.
