# needs-attention — track handoff (overseer run-prompt)

**Track:** `needs-attention` · **Repo:** `thewoolleyman/livespec` ·
**Ledger epic anchor:** `livespec-bj9x` (read status LIVE from the
ledger; never trust a status written here).

**Read-first chain (open these, in order, before acting):**

1. The `livespec-bj9x` ledger comments, top-to-bottom — the newest is a
   self-contained RESUME RECIPE with full live state. Read via the
   credential wrapper: `source
   /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C
   /data/projects/livespec show livespec-bj9x`.
2. `research/design.md` — the settled design + the full cross-repo rollout.
3. `research/glossary.md` — every term used below.

## Current state (2026-07-06; verify live against the ledger, don't trust this)

- **Gate 1 decompose:** DONE — approved 14-slice cut (in the ledger's
  DECOMPOSITION comment).
- **SP1 spec** (`orchestrate→drive` rename + `next` scope-asymmetry):
  **RATIFIED** — `history/v031`, PR #345 in `livespec-orchestrator-beads-fabro`.
- **OR1** (`orchestrate→drive` CODE rename): FILED `bd-ib-sesq5u`
  (orchestrator tenant), lane READY.
- **RT1** (`livespec-runtime-bvtkzm`; attention_item schema + compose fn):
  READY. **RT2** (`livespec-runtime-xtri75`; hygiene-scan): dep-gated on RT1.
- **SP2 spec** (`Attention→needs-attention`, console): committed `6776a46`
  in worktree `needs-attention-sp2-attention-rename`; PARKED on the console
  currency defect (external fix).

## How to drive this track

Driven by the **local `overseer` skill** (`.claude/skills/overseer/SKILL.md`)
against this ONE track (in isolation, no other tracks this run). Read
%Complete and every lane LIVE from the ledger; print the
`Epic · Track · Status · %Complete` table before any gate or status.

Drive in this order, surfacing each maintainer-owned gate WITH a
recommendation (one clickable pick at a time) and continuing autonomously
between gates:

1. **Dispatch** RT1 (runtime tenant) + OR1 (orchestrator tenant) through the
   factory once it frees (host-wide sequential — confirm free first). Ask
   ONCE for accept-on-behalf per batch, then hold.
2. **SP2:** once the console currency fix lands, push → independent **CODEX**
   sub-agent review (Fable is out of free usage; Opus 4.8 fallback ok) →
   surface `/livespec:revise` ratification.
3. **Next-wave code** (per `research/design.md` "Rollout"), file + dispatch
   as deps land: BR1/BR2 (driver-claude/codex binding renames) + BR3
   (openbrain) + BR4 (resume, manual) + orchestrator repo-root README —
   AFTER OR1 lands & `drive` exists; OR2 (list-plan-threads + needs-attention
   binding) + OR3 (git-jsonl binding) + CO1 (reaper refactor) + CO2
   (needs-attention-internal/-fleet) after RT1/RT2 build; CN1 (console port)
   after SP2 + RT1 + OR2.
4. Enumerate backlog + pending-approval every survey so nothing strands.
5. **EXIT GATE:** when every piece is `done`, surface closing `livespec-bj9x`;
   do not close it autonomously.

## Gate map

| Step | Overseer does | Maintainer gate |
|---|---|---|
| Dispatch RT1/OR1 | dispatches ready items through the factory (drain) | **accept-on-behalf** authorized once per batch |
| SP2 spec | drives push + spawns independent CODEX review; surfaces ratification | **spec ratification** (+ mandatory independent review) |
| Next-wave code | files ripe slices; dispatches through the factory | groom / approve per item as needed |
| Close | surfaces the exit gate | **exit gate** (close the epic) |

## Standing constraints

- Status is derived from the ledger, never stored here (no shadow queue).
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never `--no-verify`.
- Ripe work is built factory-side under the janitor gate, never hand-coded.
- **NEVER hand-edit `~/.claude/plugins/installed_plugins.json`** (it is a
  per-project registry; a manual dedup corrupted it and was reverted from a
  backup). **NEVER lever the currency gate** (no `LIVESPEC_CORE_PLUGIN_ROOT`
  override, no `--no-verify`) per `.ai/ci-gate-discipline.md`; if a livespec
  CLI reports "stale", `/reload-plugins` and retry.
- Independent adversarial review is REQUIRED before every ratification — use a
  separately-spawned **CODEX** sub-agent (Fable is out of free usage; Opus 4.8
  is an acceptable fallback).
- Loose ends: reap the obsolete `needs-attention-sp1-revise` worktree; keep
  `needs-attention-sp2-attention-rename` (parked SP2 proposal).
- Observability/telemetry is deferred (`design.md` §"Deferred") — out of this rollout.
