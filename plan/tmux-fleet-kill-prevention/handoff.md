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

## STATUS 2026-07-19 — BOTH DRIVER GUARDS ARE NOW LIVE AND PROVEN TO FIRE

The packaging defect described under CORRECTED DIAGNOSIS is **fixed, released,
installed, and firing-verified on both runtimes.** This supersedes the "DEAD ON
ARRIVAL" rows in the TRUE STATE table below for the two Driver mirrors.

| | Codex (`livespec-driver-codex-72z`) | Claude Driver (`livespec-driver-claude-w6f`) |
|---|---|---|
| Fix merged | PR #196 → `7979da2` | PR #213 → `fced250` + `b1b339d` |
| Released | `v0.5.1`; `release` ref confirmed to contain the fix | `v0.4.1`; `release` ref confirmed |
| Installed | cache `0.5.1`, ships `hooks/_result.py`, **zero `_vendor`** | project scope `b79a386e52d7` → `2b4be46808b9` |
| Payload corpus vs INSTALLED artifact | **15/15** | **15/15** |
| Hook trust | 7 `[hooks.state]` entries intact (`hooks.json` unchanged, so the bump did not disarm it) | n/a |
| **FIRING PROBE** | **`hook: PreToolUse Blocked` — `BLOCKED by livespec_footgun_guard.py`, no commit created** | **Write BLOCKED in a fresh session, file not created; the old cached version dies on `ModuleNotFoundError` for contrast** |

**The fix**: a stdlib-only `_result.py` shim placed INSIDE each packaged subtree,
imported as a plain sibling, with every `sys.path`/`_REPO_ROOT` arithmetic block
deleted and repo-root `_vendor` removed. Both repos also gained an
**install-shaped test** that stages ONLY the packaged subtree and runs each hook
under a bare interpreter with `PYTHONPATH` cleared, asserting real deny/allow
verdicts — the Claude repo's version is 21 tests, 19 of which fail against the
unmodified hooks. That test is the durable guard against this defect class
recurring; the old suites passed under `uv`, where the dependency resolved.

All three guards (host, Claude Driver, Codex) now score 15/15 on the same corpus.
Nothing was ever executed to verify them: hazard commands were fed as inert
strings on stdin, and firing was proven with the guards' unrelated `--no-verify`
/ memory-write deny paths, which are harmless whether blocked or executed.

**Blast radius was fleet-wide and is fully closed**: 8 of 12 active distributed
hooks could not start, including `block_auto_memory.py`. Only the two Driver
plugins ship Python hooks — core, the orchestrator, and Honeycomb ship none or
shell-only — so no third plugin carries this defect.

### Also verified live in this pass

- **L1 overseer (`livespec-wa7ry3`) — CONFIRMED LIVE.** A running overseer-spawned
  track process carries `TMUX_TMPDIR=/tmp/tmux-agents-1000`, and that agent-scoped
  socket dir exists and is actively in use. Verified by reading `/proc/<pid>/environ`
  — no tmux command run. The running daemon postdates `574192a8`.
- **L1 sandbox (`bd-ib-zaq3`) — code present in the INSTALLED cache**
  (`_SANDBOX_TMUX_TMPDIR = "/workspace/.tmux"` with `mkdir -p … && chmod 700`).
  Still outstanding: confirming a real dispatch's sandbox env table carries it.
- **L3 console (`livespec-console-beads-fabro-f2k`) — CI green** (`check-e2e-tmux`
  passes on master incl. `85b2976d`), and `console-arch-check` passes locally.
  Static audit: tmux usage is confined to ONE file, every invocation double-scoped
  (`TMUX_TMPDIR` + `-L`), AST-enforced, and the shipped binary never invokes tmux.
  **The host e2e run was deliberately DEFERRED by the maintainer** (2026-07-19)
  because the fleet was carrying ~13 live agent sessions and CI already proves the
  suite; it is an explicit residual, not a completed step.

### Known process gap surfaced by this work (needs a work-item)

`red_green_replay._IMPL_PREFIXES` (livespec-dev-tooling) omits
`.claude-plugin/hooks/`. In a repo whose only source tree lives there, `impl_paths`
is always empty, so a `fix:`/`feat:` subject routes every commit-msg invocation to
Red mode and the Green amend can never complete (`test-passed-at-red`). The ritual
silently degrades to a Red commit plus a separately-verified paired commit.
Occurrences: `b73260ee` (earlier) and `fced250`/`b1b339d` (this work). Both are
gate-clean with no `--no-verify`, but the mechanical Green pairing is absent.

## CORRECTED DIAGNOSIS (2026-07-19, established by live probing)

An earlier version of this document said the Codex guard was "merged but never
installed". **That was wrong.** It was installed, enabled, trusted, and cached 37
minutes before the kill, with correct logic and correct wiring — and it still
protected nothing, because it **crashes on import and fails OPEN**. Anyone
picking this up should start from these facts, not from the old story:

1. **The guards fail open on an import error.** Shipped hooks import modules that
   do not exist in the install cache (`_vendor` on Codex, `returns` on the Claude
   Driver); both live at repo root, outside the packaged subtree. The hook exits
   1, the runtime logs a terse `PreToolUse Failed`, and the command proceeds.
   Measured: **8 of 12 active distributed hooks could not start**, including
   `block_auto_memory.py`. CI stayed green throughout because tests run under
   `uv`, where the dependency resolves, and never in the install shape.
2. **The classifiers are CORRECT.** Both guards score 15/15 on a hazard/benign
   corpus once importable, and Codex sends the Claude-shaped payload
   (`tool_name: "Bash"`, `tool_input.command`), so the matchers are right too.
   The defect is packaging alone — do not redesign the classification logic.
3. **Codex re-extracts its plugin cache on every run.** Patching a cached file is
   silently reverted; a fix reaches Codex only by shipping in a release.
4. **Codex silently skips UNTRUSTED hooks.** A changed `hooks.json` invalidates
   its `trusted_hash`, after which every hook from that plugin is skipped with no
   warning. Any version bump can disarm the guard invisibly — check
   `[hooks.state]` after every update.

~~**Only the host guard is real protection today.** **Codex is entirely unguarded** —
do not run a Codex agent until the fixed release lands and a firing probe passes.~~
**SUPERSEDED — see STATUS above.** That was true when this diagnosis was written.
Both Driver guards have since been fixed, released, installed, and firing-verified,
and the host guard (`~/.claude/hooks/tmux-fleet-guard.py`, 15/15) remains wired as
an independent Claude-runtime backstop. Codex is no longer unguarded.

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
| **L2 Claude Driver** mirror `livespec-driver-claude-w6f` | yes — PR #206, `340dff81` | **NO — installed but DEAD ON ARRIVAL.** Present in the cache and wired, but crashes on `ModuleNotFoundError: returns` before classifying; fails OPEN. 0/15 on the payload corpus. |
| **L2 Codex** mirror `livespec-driver-codex-72z` | yes — PR #192, `e53bcea1` | **NO — installed, enabled, trusted, and DEAD ON ARRIVAL.** This is the hole that killed the fleet on 2026-07-19. It was NOT "never installed" (the earlier claim here was wrong): it was cached 37 min before the kill and crashes on `ModuleNotFoundError: _vendor`, failing OPEN. 0/15 on the payload corpus. |
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

### 1. Ship + live-verify the **Codex** guard (closes the 2026-07-19 hole) — DO THIS FIRST

**The installation step is already done and is NOT the problem.** The plugin is
registered, enabled, and trusted in `~/.codex/config.toml`, and the guard is in
the cache with correct logic and correct wiring. It nevertheless protects nothing,
because it crashes on import (`_vendor` is not inside the packaged `./livespec`
subtree) and therefore fails OPEN. Do not spend time on `codex plugin add`.

What is actually required:

1. **Fix the packaging** so every shipped hook runs under bare `python3` with no
   venv and no third-party packages — the maintainer's decision is a stdlib-only
   sibling `_result.py` shim plus an install-shaped test that stages ONLY the
   packaged subtree and asserts real verdicts. (In flight; see §"Corrected
   diagnosis" below.)
2. **Cut a release.** The marketplace tracks `ref: release`, and — critically —
   **Codex re-extracts its plugin cache on every run**, so patching the cache as a
   stopgap does NOT work; it is silently reverted. A fix reaches Codex only via a
   release.
3. **Re-establish hook trust.** Codex SILENTLY skips untrusted hooks, and a
   changed `hooks.json` invalidates its `trusted_hash`. After the update, confirm
   `[hooks.state]` carries entries for the plugin — otherwise the guard is absent
   with no warning whatsoever.
4. **Verify in two stages, both required.** (a) Payload corpus against the
   INSTALLED artifact — 15/15. (b) A **firing probe** proving the hook actually
   blocks: use the guard's unrelated `--no-verify` deny rule inside a throwaway
   git repository, which is harmless whether it is blocked or executed. **Never
   execute a tmux command to test.** Stage (a) alone is what created the last
   false-confidence report — a perfect classifier that never runs.

### 2. Ship + live-verify the **Claude Driver** guard (`w6f`)

Identical defect, identical remedy: installed and wired, but dies on
`ModuleNotFoundError: returns` and fails OPEN. Fix packaging, release, update the
plugin, then verify with BOTH the payload corpus and a firing probe.

Note the asymmetry while this is open: Claude Code on this host is still covered
by the **host guard** (`~/.claude/hooks/tmux-fleet-guard.py`, payload-verified
15/15), which is independent of the plugin. **Codex has no such fallback and is
therefore completely unguarded until step 1 lands.** Do not run any Codex agent
until it does.

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
  merged and parked in `acceptance` — they are NOT accepted, and the two Driver
  guards are installed but non-functional. Do not report this epic complete until
  every step 0–10 is finished and each guard is proven to FIRE on its own runtime
  (payload corpus alone is insufficient — see CORRECTED DIAGNOSIS).
- **Verification recipe that works, for reuse.** Payload-probe a guard by feeding
  `{"tool_name":"Bash","tool_input":{"command":"<STRING>"}}` to its stdin and
  reading the verdict; nothing is ever executed. Then prove FIRING with a payload
  the guard denies for an unrelated, inert reason — `git commit --no-verify` in a
  throwaway git repository — which is harmless whether blocked or executed. To
  inspect Codex hook behavior without touching host config, point `CODEX_HOME` at
  a scratch directory (copy `auth.json` in, delete the whole directory after) and
  use `codex exec --dangerously-bypass-hook-trust` with a diagnostic recorder
  plugin. That is how the payload shape above was established.
