# Handoff — overseer rewrite (deterministic multi-track supervisor)

**Status:** DESIGN RATIFIED 2026-07-12, **build not yet started**. **Owning
session:** livespec core, session "overseer-skill", 2026-07-12. A fresh session
can execute the next action from this file alone.

## Bottom line

Rewrite the local-only overseer skill (`.claude/skills/overseer/`, currently
markdown-only, two drifted files) into a **deterministic top-pane Python
supervisor daemon** that keeps multiple parallel livespec plan tracks moving
across tmux sessions. It watches each tracked session's **context %**; at a
threshold it injects a wrap-up; the tracked session updates its own `handoff.md`
and certifies readiness by printing a **sentinel line**; the daemon then
**restarts that session with a fresh context**, renamed to the plan topic, and
pastes the resume line. The track list is **auto-discovered** from each watched
repo's `plan/` dir; `~/.livespec-overseer.jsonl` persists only the durable
**topic↔tmux-session mapping**. Full detail: **`design.md` beside this file —
read it first.**

## Read-first chain (do this before acting)

1. **`plan/overseer-rewrite/design.md`** — the ratified design (architecture,
   sentinel protocol, registry schema, state machine, components, build phases).
2. **`.claude/skills/overseer/SKILL.md`** and
   **`.claude/skills/overseer/livespec-overseer-startup.md`** — the current
   skill being replaced (mine the KEEP items listed in `design.md`).
3. **`.ai/agent-disciplines.md`** — overseer / long-running-coordinator
   discipline + factory-dispatch discipline (still authoritative).
4. Verified facts to trust (2026-07-12): the enforced product surface is only
   `.claude-plugin/scripts` + `dev-tooling` (`pyright.include`, coverage,
   import-linter `root_packages=["livespec"]`); host-only Python under
   `.claude/` is outside those gates (precedent
   `.claude/hooks/livespec_footgun_guard.py`). The global statusline
   `~/.claude/statusline-command.sh` emits `Ctx: N% left` from
   `context_window.remaining_percentage`. `claude -n <topic>` sets the session
   display name + terminal title; `claude "prompt"` pre-fills but does NOT
   auto-submit.

## Ratified decisions (do not re-litigate)

1. Loop engine = **deterministic top-pane supervisor daemon** (not Claude-driven,
   not hybrid).
2. Judgment = **tracked-session sentinel** (LLM certifies; Python matches token).
3. List = **discovery-driven** from `<repo>/plan/*/` minus `plan/archive/**`.
4. `~/.livespec-overseer.jsonl` = **mapping store only** (topic↔tmux + pinned
   session id + custom resume + threshold override).
5. **Surface-only** — never auto-spawn a session; unassigned plans show
   `unassigned`, flagged startable.
6. **Cross-repo** — rows repo-scoped; never hardcode `/data/projects/livespec`.
7. Language = **plain stdlib-only Python**, host-only, under
   `.claude/skills/overseer/`, outside the product gates.

## Next action (concrete)

**Begin Phase 1: registry helpers + tests.**

1. Create/confirm a worktree from `master` (repo mutation protocol):
   `mise exec -- git -C /data/projects/livespec worktree add -b feat-overseer-supervisor "$HOME/.worktrees/livespec/feat-overseer-supervisor" master`
2. Author the `~/.livespec-overseer.jsonl` read/write/filter helpers and the
   **discovery ⋈ mapping** join (scan `<repo>/plan/*/`, exclude
   `plan/archive/**`, left-join the mapping), under `.claude/skills/overseer/`
   (stdlib-only Python). Add tests beside the code.
3. First, confirm no repo-wide `.py` gate objects to the daemon's location
   (run `just check` on a trivial stub, or inspect lefthook/dev-tooling for a
   whole-repo `.py` scan). If one does, prefer complying; bash is the fallback.
4. Land Phase 1 via `worktree → PR → rebase-merge`. Product `.py`? This host-
   only tooling is outside the enforced trees, so it is exempt from the TDD
   red-green-replay ritual — use a `chore(overseer):` / `feat(overseer):`
   subject as appropriate, **never `--no-verify`**, and let the hooks decide.

Then proceed through the build phases in `design.md` §"Build phases"
(2: pane-parsers; 3: `supervisor.py` + table; 4: rewrite `SKILL.md` + sentinel-
convention doc + maintenance `AGENTS.md` + retire the startup file; 5: live
exercise across ≥2 repos).

## Resume command

`/livespec-orchestrator-beads-fabro:plan overseer-rewrite`
(or: `read plan/overseer-rewrite/handoff.md and follow it`)

## Guardrails

- Repo mutations go `worktree → PR → rebase-merge`; never commit on the primary
  checkout; never `--no-verify` (`mise exec -- git …`). Only ever touch the
  worktree you create.
- Secrets are probe-only (`printenv NAME | wc -c`). Scratch under `tmp/overseer/`.
- Before any handoff/exit, stop every background sub-agent/subprocess this
  session spawned.

## Not yet done (state of the world at handoff)

Nothing built yet — this thread is seeded with the ratified design only. No
epic anchored in the ledger yet; anchor one when Phase 1 opens if you want
`%Complete` tracking (optional — the design's `%Complete` column is a nice-to-
have, not load-bearing).
