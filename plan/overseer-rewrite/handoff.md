# Handoff — overseer: DONE (correctness + invocation surface); HOLD before archive

**Status (2026-07-13):** ALL BUILD/REVIEW/SIMPLIFICATION WORK IS DONE + ON
`master`. The deterministic overseer daemon is built, all 15 adversarial-review
findings are fixed (release 0.9.4), and the operator/invocation surface has now
been de-gold-plated to the intended internal-skill shape (**PR #1158**, merge
commit `dc18a44`) and live-exercised against the real fleet. The ONLY thing left
is the maintainer's OWN exploratory testing. **Owning session:** livespec core,
"overseer-rewrite". This handoff is self-sufficient.

## Bottom line

The overseer is a deterministic tmux-supervising daemon (top pane,
`.claude/skills/overseer/supervisor.py`) + a thin interactive `/overseer` skill
(bottom pane), local-only in **livespec**. It watches each tracked session's
context %, injects a wrap-up at threshold, and — once the session certifies "done"
via an out-of-band `.overseer-ready` marker — atomically restarts it fresh, renamed
to the plan topic. It is a **PERMANENT human-supervised alternate to autonomous
mode**. The core logic is CORRECT and the invocation surface is now MINIMAL. Full
design: `design.md` beside this file.

## Simplification landed (2026-07-13, PR #1158 — `refactor(overseer):`)

Per `design.md` §"Simplification requirements (2026-07-13)", the invocation/config
surface was stripped to the intended shape WITHOUT regressing any correctness fix
(the state machine was untouched):

1. **`/overseer` skill is the sole operator surface** — no manual `python3 …`
   path.
2. **Daemon is a DEDICATED self-invokable executable `overseerd`** (maintainer
   correction 2026-07-13 — a dedicated daemon executable must NOT carry a
   positional `daemon` subcommand; the file IS the daemon). `overseerd` (shebang
   `#!/usr/bin/env -S uv run --script --no-project` + `chmod +x`) sits beside
   `supervisor.py`, takes NO args/options/subcommands, and calls
   `supervisor.run_daemon()`. `supervisor.py` reverts to a **plain module** (no
   shebang, not executable) holding the logic + `run_daemon()` + the track CLI
   (`list`/`add`/`remove`/`unassign`/`start`, no `daemon` subcommand); the skill
   invokes it as `uv run --no-project python …/supervisor.py <cmd>`. `overseerd`
   pins its own dir onto `sys.path` so `import supervisor`/siblings resolve from
   any cwd, and the manifest is resolved relative to the module file — path
   discovery "just works" from any cwd. Stdlib-only stays load-bearing (a
   third-party import would break the `--no-project` launch).
3. **Hard-coded store + stamp paths** (`~/.livespec-overseer.jsonl`,
   `~/.livespec-overseer-stamps.json`). Removed `--store`/`--stamp`.
4. **Removed `--repos`/`--repos-only`/`--manifest`** — the watch-set is the whole
   fleet read from `.livespec-fleet-manifest.jsonc`, no per-run override. (The
   `Supervisor` dataclass keeps `store_path`/`stamp_path`/`watch_repos`/
   `manifest_path` injectable, but ONLY the beside-tests inject them — they
   redirect `registry.DEFAULT_STORE_PATH` for CLI isolation now that `--store` is
   gone.)
5. **Track subcommands take `--repo`/`--topic` KEYWORD flags** (required); the
   skill prompts for whichever the maintainer omits and accepts natural-language
   drivers (add/remove/unassign/start).
6. **`daemon` takes no required args.**
7. **Original operator model preserved** — discovery-driven list, JSONL =
   mapping-only, surface-only (never auto-spawn), thin bottom-pane skill.

**Open question — RESOLVED by the maintainer (2026-07-13):** with no `--repos`
escape hatch, a developer live-exercises against the **real fleet** (option
"Real-fleet exercise"); it is safe because the daemon is surface-only (nothing is
touched unless a real track crosses threshold AND certifies AND is idle), and the
fake-tmux beside-tests remain the primary gate. Do NOT re-introduce `--repos`.

**Validation (PR #1158):** `uv run pytest .claude/skills/overseer/ -q` → **108
green** (106 baseline + 2 new: `test_cli_surface_has_no_config_knobs`,
`test_daemon_takes_no_required_args`). Full `just check` (63 targets) green in
pre-commit + pre-push. Live-exercised: the merged shebang CLI rendered the real
**20-track** fleet table read-only (`supervisor.py list`, `act=False`, zero
mutation) from the primary checkout. `SKILL.md`/`AGENTS.md` updated for the shebang
launch, keyword flags + prompting, fixed paths + fleet-only watch-set, and the
real-fleet live-exercise model.

## What is DONE — the correctness core (do NOT regress; all on `master` @ 0.9.4)

Two adversarial CODE-review rounds found and fixed **15** findings:
- **8 blockers** (PR #1138): B1 tmux `--` naming + exact `session_exists`; B2
  title-tolerant idle; B3 pane-identity gate; B4 marker/round lifecycle; B5
  failure propagation; B6 store atomicity/locking/read-only-`list`/singleton +
  per-op buffer + active-wins GC; B7 fail-soft loop; B8 `start` guard.
- **7 fix-re-review findings** (PR #1142): RB1 (critical — grace-based marker void),
  RB2 round re-certify, RB3 pane-id targeting, RB4 `start` fail-closed, Codex #1
  identity TOCTOU re-check, Codex #3 `new_session`-failure guard. **Codex #2 kept**
  (documented tradeoff — voiding the marker on a failed resume-submit).
- **AGENTS.md rule** (PR #1144): ALWAYS run the beside-tests before pushing folder
  changes (they are the ONLY gate on this folder — CI does NOT run them); exercise
  timing behavior with a CONTINUOUS loop (now covered deterministically by the
  beside-tests).

## Read-first chain

1. `design.md` §"Simplification requirements (2026-07-13)" — the spec the PR #1158
   work implemented.
2. `design.md` §"Adversarial review (2026-07-12)" + §"Live-exercise corrections
   (2026-07-13)" — why the CORE mechanics are shaped as they are (do not regress).
3. `.claude/skills/overseer/supervisor.py`, `registry.py`, `signals.py`,
   `tmuxio.py` — the code (all correctness + simplification landed).
4. `.claude/skills/overseer/SKILL.md` — the operator surface (uv shebang + keyword
   flags + prompting).
5. `.claude/skills/overseer/AGENTS.md` — maintenance invariants + the B1–B8/RB fix
   rationale + the invocation-surface invariant.
6. `.claude/skills/overseer/marker-protocol.md` — the wrap-up + marker contract.

## Verified environment facts (trust these)

- `command tmux` = tmux 3.5a (bypass the zsh alias). `claude` at
  `/home/ubuntu/.local/bin/claude`. `env` is uutils coreutils (supports `-S`).
  `uv run --script --no-project` runs the daemon isolated (no project/dep sync)
  and resolves the stdlib-only sibling imports. Statusline emits `Ctx: N% left`
  LAST — a narrow pane / very long path truncates it → daemon reads unknown and
  degrades safely (fail-closed).
- **Beside-tests are the ONLY gate on this folder** — `uv run pytest
  .claude/skills/overseer/ -q`; `just check`/pre-push/CI do NOT run them
  (`testpaths = ["tests"]`; no justfile/CI reference to `skills/overseer/`). RUN
  THEM before every push per the AGENTS.md rule.
- **PRs AUTO-MERGE on CI-green** (`app/livespec-pr-bot`). CI green does NOT
  exercise this folder, so it only ever means the product/plugin is unbroken. Do
  the beside-tests + live exercise BEFORE pushing.
- **SAFETY:** the daemon is surface-only — it never touches a session unless a
  track crosses threshold AND certifies AND is idle. The maintainer runs ~20 real
  sessions/tracks.

## Guardrails

- Repo mutations: worktree → PR → rebase-merge; never commit on the primary;
  never `--no-verify` (`mise exec -- git …`). Only touch your own worktree.
- Run `uv run pytest .claude/skills/overseer/ -q` before every push (the only gate).

## Definition of DONE

Everything the code/review/simplification side requires is DONE: all 15 review
findings landed (0.9.4), and the invocation/config surface now matches `design.md`
§"Simplification requirements" (PR #1158) — `/overseer`-only operation, uv-shebang
self-invokable daemon, hard-coded store/stamp, fleet-only watch-set, `--repo`/
`--topic` keyword flags with prompting, argless `daemon` — with the 108
beside-tests green and a real-fleet read-only render confirming discovery + the
table.

**Archive is BLOCKED on the maintainer.** Do NOT move this thread to
`plan/archive/overseer-rewrite/` until the maintainer confirms they have
exploratory-tested the overseer themselves and gives the go-ahead. Until then the
thread stays active as the resume point.

## Resume command

`read plan/overseer-rewrite/handoff.md and follow it`
