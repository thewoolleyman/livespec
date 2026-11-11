# Staging the independent replay before the orchestrator canary upgrade

Written 2026-11-10 by the successor seat for plan `codex-plugin-hook-path-regression` (livespec epic `livespec-3rfjga`). It records why the replay of plan assertions 1 and 6 must start BEFORE the upgrade it judges, and gives the phase-1 brief verbatim, so any seat can launch it.

## Why the replay is split in two

The plan record captured at 2026-11-10T01:18:52Z (ledger comment `01a1c309`) was replayed by a different-identity Codex session (`01a1c30f`). That replay posted `not_reproduced` at 01:37:25Z (ledger comment `01a1c31a`). Assertions 2, 3, 4, 5, 7 and 8 reproduced. Assertions 1 and 6 did not, for two separate reasons:

1. No plugin changed version during the replay. The livespec-orchestrator-beads-fabro marketplace `release` branch stayed at 0.309.2, so the replayer's own upgrade step changed nothing.
2. The replayer could not recreate a Codex session that was already open before the livespec-driver-codex 0.12.2 → 0.12.3 upgrade, because that upgrade had already completed.

Reason 2 recurs whenever the replayer is started after the capture, because by then the upgrade is over. So the replay runs in two phases:

- **Phase 1, before the upgrade.** A different-identity replayer opens its OWN interactive Codex sessions on the dev host and on the MacBook Pro, under the tmux socket `hookcache-replay`, runs the baseline turns, records its session id, and exits. It does not change the plugin cache.
- **Phase 2, after the upgrade and after the capture is posted.** The same replayer is resumed with `codex exec resume <session-id>` under the same `env -u CLAUDE_CODE_SESSION_ID -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT` prefix. Resuming keeps its identity, as recorded in livespec-dev-tooling `.ai/independent-host-replay-identity.md`. It runs the upgrade itself (`just ensure-codex-plugins`, which is idempotent if the capturing session already ran it), reads its still-open sessions, starts fresh ones, replays every step of the new captured record and posts `verified` or `not_reproduced` through `dispatcher.py post-plan-record`.

Launch phase 1 as a harness background task, not with `setsid nohup … &`, so its completion is reported:

```bash
mkdir -p /tmp/claude-1000/livespec-3rfjga-replay
env -u CLAUDE_CODE_SESSION_ID -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT \
  codex exec --dangerously-bypass-approvals-and-sandbox \
  -C /tmp/claude-1000/livespec-3rfjga-replay "$(cat <phase-1 brief file>)"
```

## Open risk: only one plugin moves in the canary window

Reason 1 is cured only for the plugin that moves. In the canary window expected about 08:00Z on 2026-11-10, only livespec-orchestrator-beads-fabro changes version (0.309.2 to the first 0.311.x adoption). At 03:47Z no livespec-driver-codex release was pending: its master carried one `chore(deps)` commit past v0.12.3. livespec core declares no Codex hooks. The `01a1c31a` replayer wrote "Invoking upgrade for every plugin does not prove a version upgrade of every plugin". A replayer that reads assertions 1 and 6 as requiring every hook-declaring fleet plugin to change version in one event may refuse them again. The recommendation sent to legacy-coordinator-agent on 2026-11-10: brief the replayer with the assertions verbatim and no interpretation. If it refuses on that reading, treat it as a Definition-of-Done wording question for the maintainer, not as a retry target.

## Phase-1 brief, verbatim

    You are the INDEPENDENT REPLAYER for the plan Proof of Done of livespec plan epic `livespec-3rfjga` (repository /data/projects/livespec, plan `codex-plugin-hook-path-regression`). This is PHASE 1 of 2: open your own pre-upgrade Codex sessions BEFORE an upgrade happens. Then stop. You will be resumed (same session, same identity) for phase 2 after the upgrade.
    
    Why there are two phases: two of the assertions are about a Codex session that was ALREADY OPEN before a marketplace upgrade. A replay cannot recreate such a session after the upgrade has completed; the previous replay (2026-11-10T01:37Z) failed for exactly that reason. So you must open those sessions yourself, now, while the cache still holds the pre-upgrade versions.
    
    The two assertions your phase-1 sessions serve, verbatim from the epic's Definition of Done:
    
    1. On the dev host, after a marketplace upgrade of every fleet Codex plugin, a Codex session started after that upgrade completes a turn that runs every declared hook with no 'Hook failed' error, any hook that a session already open before that upgrade cannot run is reported in that session as a visible 'Hook failed' error rather than skipped silently, and every hook command that open session captured at startup resolves to an existing entrypoint in a validated current payload.
    6. On the MacBook Pro, after a normal marketplace upgrade of every fleet Codex plugin, a Codex session started after that upgrade completes a turn that runs every declared hook with no 'Hook failed' error, and any hook that a session already open before that upgrade cannot run is reported in that session as a visible 'Hook failed' error rather than skipped silently.
    
    You judge these yourself in phase 2. Nobody will tell you what the capturing session observed, and you must not look for it.
    
    ## Phase-1 steps
    
    Take every UTC time with a fresh `date -u` at the moment of the step. Write ALL of your own outputs (scripts, captures, notes) under `REPLAY_DIR=/tmp/claude-1000/livespec-3rfjga-replay` (create it), never inside any git checkout.
    
    On the dev host (this machine):
    
    1. Record the installed versions: `readlink` the `latest` symlink and list the version directories under `~/.codex/plugins/cache/livespec-orchestrator-beads-fabro/livespec-orchestrator-beads-fabro/`, `~/.codex/plugins/cache/livespec-driver-codex/livespec/` and `~/.codex/plugins/cache/livespec/livespec/` (if present). Also record the inode of each current version directory.
    2. Create a scratch git repository OUTSIDE every checkout: `$REPLAY_DIR/dev-scratch` (`git init`, then a normal `git commit --allow-empty -m init` from your own shell before Codex starts).
    3. Start an interactive Codex TUI in that directory inside a tmux server on the socket name `hookcache-replay` ONLY (`tmux -L hookcache-replay new-session -d -s dev -x 220 -y 50 -c "$REPLAY_DIR/dev-scratch" codex`). If Codex offers a CLI update, press Esc to skip it; never update the CLI. If it asks for folder access to the scratch directory, grant that.
    4. Baseline turn in that TUI: ask it to run `echo baseline-replay`, then ask it to run exactly `git commit --allow-empty --no-verify -m guard-probe-replay-pre`. Read the screen with `tmux -L hookcache-replay capture-pane -p -S -200 -t dev` and save it to `$REPLAY_DIR/dev-baseline.txt`. Record whether the commit was BLOCKED by a PreToolUse hook and how many 'Hook failed' lines appear.
    5. LEAVE THAT TUI RUNNING. Do not exit it, do not kill the tmux server.
    
    On the MacBook Pro, over `ssh cwoolley@chads-macbook-pro` (codex is at `/opt/homebrew/bin`):
    
    6. Repeat steps 1-5 there, with the scratch repository at `~/livespec-3rfjga-replay/pro-scratch` on the Pro, the tmux socket name `hookcache-replay` on the Pro, session name `pro`, and the capture saved back to `$REPLAY_DIR/pro-baseline.txt` on the dev host.
    
    Finally:
    
    7. Write `$REPLAY_DIR/phase1-summary.md` with: every UTC time, the versions and inodes from steps 1 and 6, both baseline results, and YOUR OWN Codex session id (it is printed in the header of your own `codex exec` output; also state the value of `CODEX_SESSION_ID` if set). Then end your turn with that same summary.
    
    ## Hard rules
    
    - Do NOT run `just ensure-codex-plugins`, `codex plugin ...` upgrade/install commands, or anything else that changes the plugin cache. The upgrade must happen AFTER your sessions are open; you will run it yourself in phase 2.
    - Do NOT stop, start or modify `codex-hook-trust.timer`, the hook-cache observer, launchd agents, or `~/.codex/config.toml`. Never grant or edit hook trust by hand.
    - Do NOT touch the tmux server `hookcache-accept` or any session it holds (that belongs to the capturing session), and never use the default tmux socket. Never run `tmux kill-server` without `-L hookcache-replay`.
    - Do NOT post anything to the ledger or GitHub in phase 1.
    - Do NOT mask, bind-mount over, or redirect any checkout's `tmp/` directory.
    - Do not read the epic's comments or any "Plan Proof of Done" record in phase 1.
    - If any step fails, stop, write what failed into the summary, and end your turn. Never use `--no-verify` for any commit of your own.
