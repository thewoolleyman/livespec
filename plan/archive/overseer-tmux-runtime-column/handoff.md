# Archived — annotate the overseer table's tmux column with the runtime

**Status: CLOSED, merged and live-exercised (2026-07-18).** This thread is archived;
its follow-on work continues under `plan/overseer-productization/`.

## What shipped

The overseer daemon's live table now shows the harness/runtime in parentheses after
the tmux session name — `livespec (claude)`, `livespec1 (codex)` — so the operator can
tell at a glance whether a track is a Claude or a Codex session (maintainer-requested
2026-07-18). No-managed-pane rows (`unassigned` / `session-gone` / `live-outside-tmux`)
render a bare `—` with no annotation.

- **PR [#1345](https://github.com/thewoolleyman/livespec/pull/1345)** — the feature.
  `RowView` gained a `runtime` field, derived once in `evaluate` from `is_codex` and
  carried onto every row with a live managed pane; a shared `_tmux_cell(row)` helper
  single-sources the cell formatting for both the table (`render`) and the `NEEDS YOU`
  block (`_attention_lines`), so the two annotate identically and cannot drift. Column
  width is computed from the annotated string (alignment holds); the jump command still
  uses the bare session name.
- **PR [#1351](https://github.com/thewoolleyman/livespec/pull/1351)** — a master-red
  follow-up. A concurrent PR (`a24e3e13`) re-keyed the live `_codex` map by
  `(tmux, name)`; this thread's Codex test still used the old `{session: …}` key, so the
  two merged green independently but broke `pytest` on master. Re-keyed the fixture to
  match. **This break is the concrete motivating case** for the productization thread:
  the hermetic beside-tests are the sole gate on the overseer folder but are NOT wired
  into `just check`/CI, so a semantic merge-break reached master uncaught.

## Verification

- `uv run pytest .claude/skills/overseer/ -q` → 280 passed (both runtimes end-to-end
  through `evaluate → render`, the no-pane `—` cases, and column alignment).
  Sabotage-verified: dropping the derivation reddened the evaluate tests; dropping the
  `_tmux_cell` annotation reddened the formatting tests; both restored.
- Live read-only render against the real fleet (`supervisor.py list`) showed live panes
  as `livespecN (claude)` and no-pane rows as `—`, alignment intact. (No live Codex
  track was running to show `(codex)` live; the Codex path is exercised through the
  beside-test with the real Codex-shape fixtures.)

## Follow-on

The runtime-column work exposed the structural gap — the overseer's beside-tests are
outside every product gate. That, plus the question of shipping the overseer to
adopters, is now tracked under **`plan/overseer-productization/`** (Phase 1: bring the
overseer inside the product gates as a first-class local module; Phase 2: host-decouple
and ship it to adopters via the Driver split + fleet-manifest contract).
