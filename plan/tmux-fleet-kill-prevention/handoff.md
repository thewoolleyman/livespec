# Handoff — tmux-fleet-kill-prevention

**Thread**: `plan/tmux-fleet-kill-prevention/` (repo `livespec`).
**Ledger epic anchor**: `livespec-yiycvd` (livespec tenant).

## CARDINAL INSTRUCTION (maintainer, 2026-07-19, verbatim intent)

**Finish every single thing all the way. Do NOT claim you are done until it is
ALL done. Then run the adversarial reviews again.**

"Done" here means the fleet-kill protections are **installed on their target
runtimes and demonstrated live with a payload** — not merged, not CI-green, not
AI-accepted. A merge SHA is not protection. See
`research/incident-2026-07-19-agent-brief-kill.md` for what happened the last
time this distinction was blurred.

## Read first

1. `research/incident-2026-07-18.md` — the original double fleet kill.
2. `research/prevention-design.md` — the L1–L5 mechanical design.
3. `research/incident-2026-07-19-agent-brief-kill.md` — **the agent working on
   this thread killed the fleet again on 2026-07-19.** Its five "hard rules" are
   binding on whoever picks this up.

## HARD RULES (violating any of these has already destroyed the fleet once)

1. **Never put a destructive command in a sub-agent brief** — not as an example,
   not as a thing to "try", not quoted. Describe the hazard class in prose.
2. **Guard-testing is payload-only.** Prove a guard denies X by feeding X as a
   *string* to the guard's stdin and reading the verdict. NEVER execute X.
3. **A hook covers exactly one runtime.** Before dispatching any agent, confirm a
   guard is installed on the runtime it will execute on. Claude Code hooks do
   NOT cover Codex.
4. **Merged ≠ protected.** Report "live" only with payload-level evidence.
5. **A PreToolUse hook cannot see a script's internal subprocesses** — it sees
   only the top-level Bash string. `python3 foo.py` is opaque to it.

## TRUE STATE — merged vs. actually live

| Layer / item | Merged | **Live (installed + payload-proven)** |
|---|---|---|
| **L2-host** guard `livespec-6dyst6` (repo `vps-info`) | n/a | **YES** — `~/.claude/hooks/tmux-fleet-guard.py` + `~/.claude/settings.json` `PreToolUse`. Live-verified (fresh headless session denied a guarded command). Version-carried at `vps-info@5cdbcd8` `services/claude-code-hooks/`. Item CLOSED. Covers Claude Code on this host ONLY. |
| **L1 overseer** `livespec-wa7ry3` (repo `livespec`) | yes — PR #1367, `574192a8` | **UNVERIFIED** — `.claude/skills/overseer/supervisor.py` ships `unset TMUX; export TMUX_TMPDIR=/tmp/tmux-agents-<uid>; exec …`. Item CLOSED, but a *running* overseerd may predate it. |
| **L2 Claude Driver** mirror `livespec-driver-claude-w6f` | yes — PR #206, `340dff81` | **NO** — plugin loads from a pinned cache/`release` ref; hook not proven loaded. |
| **L2 Codex** mirror `livespec-driver-codex-72z` | yes — PR #192, `e53bcea1` | **NO — this is the hole that killed the fleet on 2026-07-19.** Never installed into `~/.codex/config.toml`. |
| **L1 sandbox** mirror `bd-ib-zaq3` (orchestrator) | yes — PR #780, `861e40c3` | **NO** — orchestrator runs from cached plugin; covers Fabro dispatch sandboxes only, never ad-hoc sub-agents. |
| **L3 console harness** mirror `livespec-console-beads-fabro-f2k` | yes — PR #290, `85b2976d` | **NO** — test-only; not run on host since merge. |
| **L4 resilience** `livespec-4vzhwp` (repo `livespec` + host) | no | **NOT STARTED** — `blocked`, maintainer-gated host systemd leg. Recovery has now cost real time 3×. |

All four mirrors sit in ledger status **`acceptance`** (policy `ai-then-human`).
The four original livespec-tenant children (`livespec-3wemjq`, `livespec-omjc2t`,
`livespec-kiwfyv`, `livespec-n3o5e5`) are **`blocked`**, each noted as
tracked-via-mirror — close them as done-via-mirror only when their mirror is
accepted.

**Why mirrors exist:** the Dispatcher requires `item-tenant == target-repo-tenant`.
The original children live in the `livespec` tenant but target other repos, so
they could never be factory-built. Each was re-filed into its target repo's own
tenant. Do not try to dispatch the `livespec-*` children.

## REMAINING WORK — in order. Nothing may be reported done until ALL of it is.

### 0. ~~Commit these plan docs~~ — **DONE 2026-07-19**
This handoff and `research/incident-2026-07-19-agent-brief-kill.md` are committed
on `master` (PR #1391, merge `1f9add96`; this correction followed it). Nothing to
do here — start at step 1.

### 1. Install + live-verify the **Codex** guard (closes the 2026-07-19 hole) — DO THIS FIRST
Host-wide registration (per `CLAUDE.md` §"Codex dogfooding"):
```bash
codex plugin marketplace add thewoolleyman/livespec-driver-codex --ref release
codex plugin add livespec@livespec-driver-codex
```
Confirm a `[plugins."livespec@livespec-driver-codex"] enabled = true` entry lands
in `~/.codex/config.toml`. **NOTE:** the marketplace tracks `release` — verify a
release tag CONTAINS PR #192 (`e53bcea1`); if not, a release must be cut first.
**Live-verify payload-only:** feed a default-socket kill *string* to
`livespec/hooks/livespec_footgun_guard.py` on stdin and confirm it returns a
DENY verdict; feed a scoped `-L <name>` string and confirm ALLOW. **Never execute
a tmux command to test.**

### 2. Install + live-verify the **Claude Driver** guard (`w6f`)
The Driver marketplace is pinned to `ref: release`. Verify a release contains
PR #206 (`340dff81`); cut/await one if not. Then `/plugin update
livespec@livespec-driver-claude` (or reinstall) and confirm
`.claude-plugin/hooks/tmux_fleet_guard.py` is present in the installed cache and
wired via that plugin's `hooks.json`. **Live-verify payload-only** as above.

### 3. Verify the **sandbox** env inversion (`zaq3`) is live
Confirm the *installed* orchestrator plugin cache (not just origin/master)
contains `_dispatcher_overlay.py` with `TMUX_TMPDIR=/workspace/.tmux` +
`mkdir -p … && chmod 700`. Then dispatch one trivial item and confirm the
sandbox env table carries it.

### 4. Verify the **overseer** spawn path (`wa7ry3`) is live
Confirm the running overseerd/supervisor is the post-`574192a8` code; restart it
if it predates the merge. Confirm a newly spawned track pane resolves tmux under
`/tmp/tmux-agents-<uid>/` (inspect the pane's env — do not run a kill).

### 5. Verify the **console harness** (`f2k`)
Run the console e2e suite + `console-arch-check` on the host. The harness is now
socket-scoped, so this is safe; confirm `/tmp/tmux-1000/` socket-dir listing is
unchanged before/after.

### 6. Accept the 4 mirrors — ONLY after 1–5 produce payload evidence
```bash
# per mirror, from its own repo:
drive.py --repo <target-repo> --action accept:<mirror-id>
```
Mirrors: `livespec-driver-claude-w6f`, `livespec-driver-codex-72z`,
`bd-ib-zaq3`, `livespec-console-beads-fabro-f2k`.
Journal the live-exercise evidence on each item BEFORE accepting.

### 7. Close the 4 blocked livespec children as done-via-mirror.

### 8. **L4** `livespec-4vzhwp` — fleet-recreate resilience (maintainer-gated)
systemd user unit anchoring the overseer session + recreate tracked sessions from
`~/.livespec-overseer.jsonl`. Three kills have each cost manual rebuild time.

### 9. Close epic `livespec-yiycvd`; archive this thread.

### 10. **Re-run the adversarial reviews** (maintainer explicitly required)
Use the SAFE brief below. Do NOT reuse the old brief — it killed the fleet.

## SAFE adversarial-review brief (use verbatim; the old one was lethal)

> ADVERSARIAL PRE-ACCEPT REVIEW — READ-ONLY, PAYLOAD-ONLY.
>
> **ABSOLUTE PROHIBITION: you must NEVER execute a `tmux`, `pkill`, or `killall`
> command, under any circumstance, for any reason. There is a live shared tmux
> server on this host carrying the maintainer's working sessions; executing such
> a command destroys it. This has already happened three times. There is no
> scenario in which running one is necessary or acceptable.**
>
> The guards under review are classifiers: they read a JSON payload
> `{"tool_name":"Bash","tool_input":{"command":"<STRING>"}}` on stdin and emit a
> deny verdict or nothing. To test any hypothesis about what the guard does with
> a command, **feed that command as a STRING in the payload and read the
> verdict.** Never run it. A bypass claim is only valid if demonstrated as a
> guard verdict on a string.
>
> Review these merged changes (read via `git -C <repo> show origin/master:<path>`):
> [list the 4 items, repos, PRs, and file paths]
>
> Hazard class the guards must DENY: a tmux `kill-server` invocation not scoped
> to a non-default socket; a socket flag that reconstructs the shared default
> socket; process-killers targeting tmux. Must ALLOW: scoped scratch use,
> non-destructive tmux, and commands that merely *mention* the hazard inside
> quotes or a heredoc body. Must FAIL CLOSED on unparseable hazard-shaped input.
>
> For each item output: VERDICT = ACCEPT-READY or BLOCKER; for a BLOCKER give
> file:line and the guard's actual verdict on the specific payload string.

**Runtime rule for the re-review:** run reviewers only on runtimes with an
installed, payload-proven guard. Do not use a Codex reviewer until step 1 is
complete and verified.

## Filed follow-ups (already in the ledger, do not re-file)

- `bd-ib-brry` (orchestrator tenant) — janitor's cross-repo wiring check reads
  **stale local sibling working trees** instead of `origin/master`, producing
  false post-merge reds. Workaround applied: ff-refresh all fleet checkouts.
- `bd-ib-lza6` (orchestrator tenant) — a janitor-failed **merged** item sticks in
  `active` with no forward valve (`impl:` needs `ready`, `accept:` needs
  `acceptance`), requiring a manual `bd close`.

## Session-state notes

- Host guard corpus is 30/30 (includes heredoc-body false-positive regressions;
  a naive lexer splits heredoc bodies and self-blocks commit messages).
- All fleet checkouts were ff-refreshed to `origin/master` on 2026-07-19.
- A rogue `codex-acp` process from the 2026-07-19 incident was killed. At the
  2026-07-19 08:2x wind-down, **no sub-agent, background task, or subprocess
  started by that session was still running** (verified: no `codex-acp`, no
  review agents, no `fabro-exec` wrappers).
- These plan docs are committed on `master` (PR #1391, `1f9add96`) — step 0 is done.
- Nothing beyond the L2-host guard has been claimed done. The four mirrors are
  merged and parked in `acceptance` — they are NOT accepted and NOT installed.
  Do not report this epic complete until every step 0–10 is finished and each
  guard is payload-proven on its own runtime.
