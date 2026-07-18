# Handoff — annotate the overseer table's tmux column with the runtime

**Owning session:** livespec core, "overseer-tmux-runtime-column". **Status:** OPEN, ready
to start.

**Requirement (maintainer 2026-07-18).** In the overseer daemon's live table, the `tmux`
column must show the HARNESS/runtime in parentheses AFTER the tmux session name — e.g.
`livespec (claude)`, `livespec1 (codex)`. Today the column shows only the bare tmux name,
so the operator cannot tell at a glance whether a track is a Claude or a Codex session.

## Scope

- The **`tmux` column of the daemon's rendered table** (`supervisor.py` `render`). That is
  the specific surface the requirement names ("the tmux daemon column").
- Only rows with a LIVE MANAGED pane carry a runtime: `working` / `idle` /
  `idle-with-context-left` / `warned` / `danger` / `winding-down` / `restarting` /
  `settling` / `blocked:human` render `<tmux> (claude)` or `<tmux> (codex)`.
- Rows with NO managed pane already report `tmux=None` (rendered `—`): `unassigned`,
  `session-gone`, `live-outside-tmux`. They get NO `(...)` annotation (there is no tmux
  session and, for the first two, no runtime).
- The `NEEDS YOU` block is OUT of scope unless the implementer sees clear value — the
  requirement is specifically the table column. Decide and note it either way.

## Where the code + the discipline live

`.claude/skills/overseer/supervisor.py`:
- `evaluate(track, act=...)` already computes `is_codex = self._is_codex_track(...)` per
  row, so the runtime is KNOWN at evaluate time — carry it onto the row rather than
  re-deriving it in `render`.
- `RowView` is the per-row projection (`topic` / `repo` / `tmux` / `ctx` / `status` /
  `note`). It is the natural place for a new `runtime` field.
- `render` builds the table; see the "Row color is a TTY-only, whole-LINE affordance"
  bullet in `AGENTS.md` for the two column invariants you MUST preserve (below).

The folder is stdlib-only, host-only, and OUTSIDE every product gate (ruff / pyright /
coverage / import-linter all exclude it; `just check` never collects it). **The
beside-tests are the SOLE gate** — always run before pushing:

```bash
uv run pytest .claude/skills/overseer/ -q
```

**Sabotage-verify any new guard** (break it, watch its test go red, restore). Follow the
worktree → PR → merge → cleanup protocol; overseer `.py` is exempt from the
Red-Green-Replay ritual (it is not an `_IMPL_PREFIXES` path), so use a `fix(overseer):`
subject with test + impl in one commit, and never `--no-verify`. Read `AGENTS.md` first.

## Implementation direction (architecture, not mechanism)

- **Derive the runtime once, in `evaluate`.** Set a row `runtime` to `"codex"` when
  `is_codex`, else `"claude"`, for any row that has a live managed pane (i.e. the branches
  that set `tmux=session`); leave it `None` for the no-managed-pane rows (`unassigned` /
  `session-gone` / `live-outside-tmux`, which already carry `tmux=None`).
- **Format in `render`.** Build the tmux cell as `f"{tmux} ({runtime})"` when BOTH `tmux`
  and `runtime` are present, else the bare `tmux` name, else `—` (tmux is None).
- **Preserve the two column invariants** (they are load-bearing — see `AGENTS.md`):
  1. Column widths are computed on the PLAIN-TEXT `len` of each cell, so compute the width
     from the ALREADY-ANNOTATED string (`livespec (claude)`), not the bare name, or the
     column will be too narrow and misalign.
  2. TTY color wraps the whole already-padded LINE, never a cell, so alignment is preserved
     as long as (1) holds. Color is emitted only to a TTY, so a piped
     `supervisor.py list` and the beside-tests' `StringIO` stay plain text and every
     `row.split()` assertion must still hold.

## Acceptance (beside-tests are the sole gate)

- A `working` / `idle` **Claude** row renders its tmux cell as `<tmux> (claude)`; a
  **Codex** row (adopted in `_codex`, `bun` pane) as `<tmux> (codex)`.
- `unassigned` and `session-gone` rows render `—` with no `(...)`.
- Column alignment holds: the header (`Status Topic tmux Ctx% Repo`) and separator still
  line up, and existing `row.split()` assertions still parse (the runtime token adds ONE
  extra whitespace-split field in the tmux cell — update any test that indexes the tmux
  column by split position, OR keep the annotation paren-joined so `split()` sees
  `livespec` and `(claude)` as two tokens and assert accordingly; pick one and pin it).
- Add a focused test for each runtime, and sabotage-verify (drop the runtime → the cell
  loses `(claude)`/`(codex)` → the test goes red).

## Live-exercise (the acceptance leg — "done" means rolled out and exercised)

1. Read-only render against the real fleet:
   `uv run --no-project python .claude/skills/overseer/supervisor.py list` — confirm the
   tmux column shows `(claude)` / `(codex)` per row, alignment intact.
2. Respawn the live daemon so its table picks up the change: `respawn-pane -k` on the
   `overseer-daemon` pane (session `livespec-overseer`, pane `%77`) with
   `.claude/skills/overseer/overseerd 2>> tmp/overseer/daemon.log` (cwd
   `/data/projects/livespec`; the stderr redirect is REQUIRED). See the overseer-rewrite
   handoff's "Standing operational notes".

## Related

Sibling overseer-daemon backlog: `plan/overseer-known-defects/handoff.md` (defects #4–#6).
Same folder, same discipline — this is a small, independent rendering enhancement.
