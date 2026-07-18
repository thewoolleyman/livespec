# Handoff — tmux-fleet-kill-prevention

**Thread**: `plan/tmux-fleet-kill-prevention/` (repo `livespec`).
**Ledger epic anchor**: `livespec-yiycvd`.
**Status**: composed read-only from the ledger — run
`/livespec-orchestrator-beads-fabro:list-work-items --json` (or `next`)
and read the items below by id; this file stores no status.

## Read first

1. `plan/tmux-fleet-kill-prevention/research/incident-2026-07-18.md` —
   the verified incident record (what happened, evidence, prior art).
2. `plan/tmux-fleet-kill-prevention/research/prevention-design.md` —
   the multi-level mechanical design (L1–L5) and sequencing rationale.

## The work (cited read-only; status lives in the ledger)

- `livespec-yiycvd` — epic anchor.
- `livespec-6dyst6` — L2-host: maintainer's user-scope guard hook
  (repo `vps-info` / host `~/.claude/settings.json`). Maintainer-gated.
- `livespec-n3o5e5` — L3: console E2E harness private-socket scoping +
  enforcement check (repo `livespec-console-beads-fabro`).
- `livespec-wa7ry3` — L1: overseer spawn `TMUX_TMPDIR` inversion
  (repo `livespec`).
- `livespec-kiwfyv` — L1: dispatched-sandbox `TMUX_TMPDIR` inversion
  (repo `livespec-orchestrator-beads-fabro`).
- `livespec-3wemjq` — L2-durable: Driver-bundled guard hook
  (repo `livespec-driver-claude`).
- `livespec-omjc2t` — L2-durable: Codex-runtime guard equivalent
  (repo `livespec-driver-codex`).
- `livespec-4vzhwp` — L4: overseer-session systemd user unit +
  recreate-from-mapping (repo `livespec` + maintainer host leg).

## Next action

1. **Maintainer, first and highest-value (minutes of work, covers the
   whole host today)**: execute `livespec-6dyst6` — install the
   user-scope PreToolUse guard hook per its description, then verify
   with the probe commands and journal the evidence on the item.
2. **Admission valve**: approve (or amend) the five `pending-approval`
   items — `livespec-n3o5e5`, `livespec-wa7ry3`, `livespec-kiwfyv`,
   `livespec-3wemjq`, `livespec-omjc2t` — via
   `/livespec-orchestrator-beads-fabro:drive --action approve:<id>`.
3. **Implementation path (factory)**: approved items are built
   factory-side — the Dispatcher drains `ready` items, or an operator
   runs `/livespec-orchestrator-beads-fabro:drive --action impl:<id>`
   per item. Do NOT hand-code these inline in a planning session. The
   two maintainer-gated items (`livespec-6dyst6`, `livespec-4vzhwp`'s
   host leg) are the factory-ineligible exceptions recorded on the
   items themselves.
4. **Until L1+L2 land**: do not resume Claude conversation
   `5a8260e9-7cb0-434c-8ef4-85277e06a1c9` (the autonomous-mode track
   session whose subagents caused both kills — it would resume
   mid-width-probe), and leave the investigation instrumentation
   running (`tmux-death-canary` systemd user unit, `tmux-sigtrace`
   root unit; files under `tmp/tmux-death-investigation/`). Stand both
   down when L1+L2 are live: `systemctl --user stop tmux-death-canary`
   and `sudo systemctl stop tmux-sigtrace`.

## Close condition

Epic `livespec-yiycvd` closes when all children are closed with
live-exercise evidence journaled (per the fleet "done = rolled out and
exercised live" rule); then archive this thread
(`git mv plan/tmux-fleet-kill-prevention/ plan/archive/tmux-fleet-kill-prevention/`).
