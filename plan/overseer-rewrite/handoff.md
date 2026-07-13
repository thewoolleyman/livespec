# Handoff — overseer: simplify the invocation/config surface

**Status (2026-07-13):** CORRECTNESS DONE; INVOCATION SURFACE MUST BE
SIMPLIFIED. The deterministic overseer daemon is built, all 15 adversarial-review
findings are fixed and on `master` (release 0.9.4), and it is live-validated. But
the OPERATOR / INVOCATION surface was built over-configurable and mis-shaped; the
maintainer rejected it (2026-07-13). This handoff drives the simplification. It is
self-sufficient — a fresh session can execute from here alone. **Owning session:**
livespec core, "overseer-rewrite".

## Bottom line

The overseer is a deterministic tmux-supervising daemon (top pane,
`.claude/skills/overseer/supervisor.py`) + a thin interactive `/overseer` skill
(bottom pane), local-only in **livespec**. It watches each tracked session's
context %, injects a wrap-up at threshold, and — once the session certifies "done"
via an out-of-band `.overseer-ready` marker — atomically restarts it fresh, renamed
to the plan topic. It is a **PERMANENT human-supervised alternate to autonomous
mode**. The core logic is CORRECT (see the review history below). The remaining
work is to strip the invocation/config surface down to the intended
internal-skill shape.

## THE WORK — simplify per `design.md` §"Simplification requirements (2026-07-13)"

Read that section in `design.md` first — it is the authoritative spec. In short,
WITHOUT regressing any correctness fix (B1–B8, RB1–4, Codex #1/#3; Codex #2 kept):

1. **`/overseer` skill is the ONLY operator surface** — no manual
   `python3 supervisor.py` usage path.
2. **Daemon = self-invokable script via `uv`, not `python3`** — proper shebang
   (`uv run`), `chmod +x`, launched directly by the skill. (This is a LOCAL
   host-only skill, NOT a distributed plugin script, so the CLAUDE.md
   `python3 ${CLAUDE_PLUGIN_ROOT}` rule does NOT apply — uv + shebang is correct.
   Verify the shebang resolves the stdlib-only sibling imports.)
3. **Hard-code the store + stamp paths** (`~/.livespec-overseer.jsonl`,
   `~/.livespec-overseer-stamps.json`). Remove the `--store` / `--stamp` CLI
   flags. Keep the `Supervisor` dataclass fields injectable for the beside-tests
   ONLY.
4. **Remove `--repos` / `--repos-only`.** The watch-set is the whole fleet, read
   from `.livespec-fleet-manifest.jsonc` (members + adopters). No repo override,
   no "scratch repo." Keep `watch_repos` injectable for tests only.
5. **Subcommands take `--repo` / `--topic` KEYWORD flags** (not positional),
   first-class in the SKILL, which **prompts** when one is omitted and accepts
   natural-language drivers to add/manage tracks (add/remove/unassign/start).
6. **`daemon` takes no required args** — all optional with defaults; `overseer
   daemon` = watch the whole fleet with the hard-coded paths.
7. **Preserve the original operator model**: discovery-driven list from each fleet
   repo's `plan/`, JSONL = mapping-only, surface-only (never auto-spawn), thin
   bottom-pane skill that starts the daemon + drives textual commands + surfaces
   blocked/danger with a recommendation.

**Open question to resolve with the maintainer BEFORE finishing:** with no
`--repos` escape hatch, how does a developer live-exercise a change without
touching the maintainer's real fleet sessions? (beside-tests are the primary gate;
surface-only design keeps a real-fleet run safe; do NOT re-add `--repos`.) See the
design section's "Open question."

## Files to change (all under `.claude/skills/overseer/`, on `master`)

- `supervisor.py` — the CLI (`main`, `_supervisor_from_args`, the subparsers,
  `_cmd_start`/`_cmd_add`/`_cmd_remove`/`_cmd_daemon`) is where `--store`/`--stamp`/
  `--repos`/`--repos-only` + positional `repo`/`topic` live. Rework to §5/§6 shape.
  Add the `uv` shebang + make executable (§2).
- `registry.py` — `DEFAULT_STORE_PATH`/`DEFAULT_STAMP_PATH` are already the
  hardcoded defaults; `watch_set(manifest, extra_repos)` already reads the manifest
  — make the manifest the sole source (drop the extra_repos override from the CLI).
- `SKILL.md` — make repo/topic first-class skill args with prompting + textual
  drivers (§1/§5); ensure it launches the daemon via the uv shebang, never
  `python3` (§2). It is the operator surface.
- `test_supervisor.py` / `test_tmuxio.py` — update CLI tests for the new
  flag shape; keep the injectable dataclass fields for isolation.
- `AGENTS.md` — update any `python3 …` invocation references to the uv form; note
  the hardcoded-paths + fleet-only watch-set invariants.

## Read-first chain

1. `design.md` §"Simplification requirements (2026-07-13)" — the spec for THIS work.
2. `design.md` §"Adversarial review (2026-07-12)" + §"Live-exercise corrections
   (2026-07-13)" — why the CORE mechanics are shaped as they are (do not regress).
3. `.claude/skills/overseer/supervisor.py`, `registry.py`, `signals.py`,
   `tmuxio.py` — the code (all correctness fixes already landed).
4. `.claude/skills/overseer/SKILL.md` — the operator surface to reshape.
5. `.claude/skills/overseer/AGENTS.md` — maintenance invariants + the B1–B8/RB
   fix rationale.
6. `.claude/skills/overseer/marker-protocol.md` — the wrap-up + marker contract.

## What is DONE — the correctness core (do NOT regress; all on `master` @ 0.9.4)

Two adversarial CODE-review rounds found and fixed **15** findings:
- **8 blockers** (PR #1138): B1 tmux `--` naming + exact `session_exists`; B2
  title-tolerant idle; B3 pane-identity gate; B4 marker/round lifecycle; B5
  failure propagation; B6 store atomicity/locking/read-only-`list`/singleton +
  per-op buffer + active-wins GC; B7 fail-soft loop; B8 `start` guard.
- **7 fix-re-review findings** (PR #1142): RB1 (critical — grace-based marker void,
  a regression the B4 fix itself introduced), RB2 round re-certify, RB3 pane-id
  targeting, RB4 `start` fail-closed, Codex #1 identity TOCTOU re-check, Codex #3
  `new_session`-failure guard. **Codex #2 kept** (voiding the marker on a failed
  resume-submit — documented tradeoff; keeping it would respawn-kill the fresh
  session in a loop).
- **AGENTS.md rule** (PR #1144): ALWAYS run the beside-tests before pushing folder
  changes (they are the ONLY gate on this folder — CI does NOT run them); exercise
  timing behavior with a CONTINUOUS loop.
- **Validated:** 106 beside-tests green; a continuous 5s loop ran 3 full
  inject→certify→restart cycles with zero spurious voids (RB1 proof); a
  deterministic restart against the merged master artifact; the blocked-marker
  path. All prior scratch state cleaned; real sessions untouched.

## Verified environment facts (trust these)

- `command tmux` = tmux 3.5a (bypass the zsh alias). `claude` at
  `/home/ubuntu/.local/bin/claude`. Statusline emits `Ctx: N% left` LAST (after
  cwd) — a narrow pane / very long path truncates it → daemon reads unknown and
  degrades safely (fail-closed); a fresh 0-turn session has no `Ctx:` until its
  first turn.
- **Beside-tests are the ONLY gate on this folder** — `uv run pytest
  .claude/skills/overseer/ -q`; `just check`/pre-push/CI do NOT run them
  (`testpaths = ["tests"]`; no justfile/CI reference to `skills/overseer/`). RUN
  THEM before every push per the AGENTS.md rule.
- Folder is OUTSIDE the product gates (ruff extend-exclude, pyright.include omit,
  coverage testpaths, import-linter root). Commits use `fix(overseer):` /
  `feat(overseer):` / `docs(overseer):` — TDD ritual EXEMPT (no product `.py`).
- **PRs AUTO-MERGE on CI-green** (`app/livespec-pr-bot`). CI green does NOT
  exercise this folder, so it only ever means the product/plugin is unbroken. Do
  the beside-tests + live exercise BEFORE pushing, because a green PR merges before
  any out-of-band review can gate it.
- **SAFETY:** the daemon is surface-only — it never touches a session unless a
  track crosses threshold AND certifies AND is idle. Still, exercise carefully;
  the maintainer runs ~20 real sessions.

## Guardrails

- Repo mutations: worktree → PR → rebase-merge; never commit on the primary;
  never `--no-verify` (`mise exec -- git …`). Only touch your own worktree.
- Run `uv run pytest .claude/skills/overseer/ -q` before every push (the only gate).
- Live-exercise timing behavior with a CONTINUOUS daemon loop, not hand-spaced
  `--once` ticks (the RB1 lesson).

## Definition of DONE

The invocation/config surface matches `design.md` §"Simplification requirements":
`/overseer`-only operation, uv-shebang self-invokable daemon (no `python3`),
hard-coded store/stamp, fleet-only watch-set (no `--repos`), `--repo`/`--topic`
keyword flags with skill prompting + textual drivers, `daemon` needing no args —
all with the 106 beside-tests still green and a live exercise confirming a real
fleet track still gets injected → certified → restarted. THEN, and only then,
still **HOLD**: do NOT archive/close this plan thread until the maintainer has
done their OWN exploratory testing and gives the go-ahead.

## Resume command

`read plan/overseer-rewrite/handoff.md and follow it`
