# Handoff — overseer rewrite (final validation before "done")

**Status (2026-07-13):** BUILT + MERGED + LIVE-EXERCISED. The deterministic
overseer daemon is shipped on `master` and its core mechanics are validated
against a real Claude TUI. **Two things remain before we call it done:** (1) a
**full one-shot live test** of the complete unattended cycle, and (2) **two more
independent adversarial reviews (Fable + Codex) of the SHIPPED CODE** (the prior
reviews were of the design). This file is the self-sufficient resume point — a
fresh session can execute the remaining work from here alone. **Owning session:**
livespec core, "overseer-skill".

## Bottom line

The overseer is a deterministic tmux-supervising daemon (top pane) + a thin
interactive `/overseer` skill (bottom pane), local-only at
`.claude/skills/overseer/` in **livespec**. It watches each tracked session's
context %, injects a wrap-up at threshold, and — once the session certifies
"done" via an out-of-band `.overseer-ready` marker file — atomically restarts it
with a fresh context, renamed to the plan topic. Full design + rationale:
**`design.md` beside this file** (read it, incl. its "## Adversarial review
(2026-07-12)" and "## Live-exercise corrections (2026-07-13)" sections).

## What is DONE (do NOT rebuild — it's on `master`)

Shipped modules under `.claude/skills/overseer/`: `registry.py` (mapping store +
discovery ⋈ mapping), `signals.py` (pane parsing + marker certification),
`tmuxio.py` (the sole tmux subprocess boundary), `supervisor.py` (daemon loop +
state machine + table + CLI), 4 test files (**83 beside-tests, all green**),
`SKILL.md`, `AGENTS.md`, `marker-protocol.md`, `.claude/CLAUDE.md` symlink.

Merged PRs (all in **livespec** unless noted): #1106 (seed), #1108 (design
hardening), #1109 (ruff exclusion), **livespec-dev-tooling** #344/#345 (`.claude/`
universe exemption → v0.41.0), #1118 (pin bump), #1119 (core), #1121 (daemon),
#1124 (docs), #1125 (live-fix: 3 pane-parsing bugs), #1128 (live-fix:
verify-submit loop). Primary clean on `master`; master CI green.

Live-exercised already (against an isolated scratch session, never a real one):
real Ctx% parse, idle/busy/gate detection, bracketed-paste submission (single +
multi-line), the settled-delta busy detection, and **restart+rename unattended**
(respawn → fresh Claude → verify-submit loop → the session reads its handoff and
follows the resume line; PID changes, old context gone, `─── <topic> ──` rename
shows). `list` was verified against the 8 real `livespec/plan/` topics; archive-GC
dropped a bogus mapping row.

## Read-first chain (before acting)

1. `plan/overseer-rewrite/design.md` — full design + the two corrections sections.
2. `.claude/skills/overseer/signals.py`, `supervisor.py`, `tmuxio.py`,
   `registry.py` — the shipped code the reviews will scrutinize.
3. `.claude/skills/overseer/marker-protocol.md` — the wrap-up + marker contract.
4. `.claude/skills/overseer/AGENTS.md` — the maintenance invariants + gotchas.

## Verified environment facts (trust these)

- `command tmux` = tmux 3.5a (bypass the zsh alias). `claude` at
  `/home/ubuntu/.local/bin/claude`. The global statusline
  (`~/.claude/statusline-command.sh`) emits `Ctx: N% left`.
- Run the beside-tests: `uv run pytest .claude/skills/overseer/ -q` (NOT
  collected by the product `tests/` suite; `python3 -m pytest` lacks pytest).
- Host-only `.claude/skills/overseer/**` is OUTSIDE the product gates (ruff via
  extend-exclude PR #1109; dev-tooling mechanical suite via v0.41.0 `.claude/`
  exemption). Commits use `fix(overseer):` / `feat(overseer):` — TDD ritual
  EXEMPT. `just check` green, but it does NOT run the beside-tests — run those
  separately.
- **SAFETY (unskippable):** there are ~19 REAL, maintainer-attached tmux sessions
  (`livespec1`–`5`, `livespec-autonomous-mode`, `console-autonomous-mode`, etc.).
  ALL live testing uses ISOLATED scratch sessions with UNIQUE names (e.g.
  `ovtest-*`) in a scratch repo under the scratchpad — NEVER point the daemon's
  act-mode at, `respawn-pane`, or `kill` any real session. The repo-qualified
  `<slug>:<topic>` colon naming can't collide with the hyphen/number real names,
  but stay explicit anyway. Kill every scratch session when done.

---

## REMAINING TASK 1 — Full one-shot live test (the complete unattended cycle)

Goal: drive the WHOLE cycle end-to-end against a real Claude TUI, unattended:
**threshold-crossing → wrap-up injection → session writes `.overseer-ready` →
daemon restart + rename → restarted session resumes from the handoff.** Plus
archive-GC and reboot-recovery live.

### Setup (isolated)

```bash
SB=<scratchpad>/overseer-e2e         # a scratch dir, NOT a real repo
mkdir -p "$SB/repoA/plan/e2e-test"
# A scratch handoff that also tells the session HOW to respond to a wrap-up, so
# the cycle is fully automatic (the session writes the marker itself):
cat > "$SB/repoA/plan/e2e-test/handoff.md" <<'EOF'
# Handoff — e2e-test (overseer full-cycle scratch fixture)
## Next action
Reply with the single word: RESUMED. Then stop.
## If you receive an overseer wrap-up message
Update this file's timestamp line below, then write the ready marker EXACTLY as
marker-protocol.md says: `sha256sum <this-file> | cut -d' ' -f1 > <dir>/.overseer-ready`,
then stop. Do NOT do any other work.
<!-- last-updated: initial -->
EOF
# Launch a real claude in an isolated, wide, detached session:
command tmux new-session -d -s ovtest-e2e -x 200 -y 50 -c "$SB/repoA"
command tmux send-keys -t ovtest-e2e -l "claude"; command tmux send-keys -t ovtest-e2e Enter
# Wait for it to boot; if a first-run TRUST prompt appears (❯ 1. Yes), send Enter to accept.
# Craft a scratch mapping row with a HIGH threshold so a fresh (~99%-left) session
# triggers WITHOUT forcing real context burn (which is impractical):
python3 - <<'PY'
import json, os
repo=os.path.expanduser(os.environ["SB"])+"/repoA"
row={"topic":"e2e-test","repo":repo,"tmux":"ovtest-e2e",
     "handoff":repo+"/plan/e2e-test/handoff.md",
     "resume":"read "+repo+"/plan/e2e-test/handoff.md and follow it",
     "ctx_threshold":100}                      # 100 ⇒ any Ctx% triggers
open(os.path.expanduser("~")+"/.livespec-overseer-e2e.jsonl","w").write(json.dumps(row)+"\n")
PY
```

### Drive + observe

```bash
# One tick with act=True, scratch store/stamp, watching ONLY the scratch repo:
python3 .claude/skills/overseer/supervisor.py daemon --once \
  --repos-only --repos "$SB/repoA" \
  --store ~/.livespec-overseer-e2e.jsonl --stamp ~/.livespec-overseer-e2e-stamps.json \
  2> /tmp/e2e-daemon.log
```

Expected sequence across a few `--once` ticks (re-run the command between ticks,
or run `daemon` without `--once` briefly and watch `/tmp/e2e-daemon.log` +
`command tmux capture-pane -p -t ovtest-e2e`):

1. **Tick 1 — inject:** ctx (≤100) ≤ threshold + verified idle-input + settled →
   the daemon writes the injection stamp and bracketed-pastes the wrap-up. Verify
   the wrap-up text appears + submits in the pane; status `warned`.
2. **Session certifies:** the real session (following its handoff) writes
   `$SB/repoA/plan/e2e-test/.overseer-ready` containing `sha256sum handoff`.
   (If the real session does NOT reliably self-certify, simulate it
   deterministically: `sha256sum "$SB/repoA/plan/e2e-test/handoff.md" | cut -d' ' -f1 > "$SB/repoA/plan/e2e-test/.overseer-ready"` — this is a legitimate stand-in for the session's certification; note in the report that you used it.)
3. **Tick 2 — restart:** marker valid (mtime > stamp, hash matches) + idle +
   settled → `respawn-pane -k 'claude -n e2e-test'` → verify-submit loop pastes
   the resume line → the marker is deleted. Verify: pane PID changed, `─── e2e-test ──`
   rename in the box header, and the restarted session reads the handoff and
   replies `RESUMED` (fresh context — the pre-restart scrollback is gone).

**PASS = the full inject→marker→restart→resume cycle completes unattended.**

### Archive-GC live

```bash
mkdir -p "$SB/repoA/plan/archive"; git -C "$SB/repoA" 2>/dev/null; mv "$SB/repoA/plan/e2e-test" "$SB/repoA/plan/archive/e2e-test"
python3 .claude/skills/overseer/supervisor.py list \
  --repos-only --repos "$SB/repoA" --store ~/.livespec-overseer-e2e.jsonl
# PASS = the e2e-test mapping row is dropped (archive-GC), row gone from the table.
```

### Reboot-recovery live

```bash
command tmux kill-session -t ovtest-e2e      # simulate a lost session
# Re-add a mapping row (as in Setup) if archive-GC removed it, then:
python3 .claude/skills/overseer/supervisor.py daemon --once --recover \
  --repos-only --repos "$SB/repoA" --store ~/.livespec-overseer-e2e.jsonl --stamp ~/.livespec-overseer-e2e-stamps.json
# PASS = a fresh ovtest-e2e session is recreated running claude -n e2e-test with the resume line pasted.
```

### Cleanup (MANDATORY)

`command tmux kill-session -t ovtest-e2e` (+ any other `ovtest-*`); `rm -f
~/.livespec-overseer-e2e*.jsonl ~/.livespec-overseer-e2e*.json`. Confirm no
`ovtest-*` sessions remain and real sessions are untouched.

If any step fails: root-cause it against the real pane capture, fix `signals.py`
/ `supervisor.py` (host-only, `fix(overseer):`, worktree→PR→merge), re-run.
Record the exact pass/fail + evidence in this handoff.

---

## REMAINING TASK 2 — Two more adversarial reviews (Fable + Codex) of the CODE

The two prior adversarial reviews (2026-07-12) reviewed the DESIGN. Before "done",
run TWO fresh independent READ-ONLY reviews — one **Fable**-model agent, one
**Codex** agent — of the SHIPPED CODE. Dispatch both in parallel (background);
each returns `VERDICT: NO-BLOCKERS` or a concise blocker list (defect + concrete
failure scenario + fix). Ignore nitpicks.

Point each at: `signals.py`, `supervisor.py`, `tmuxio.py`, `registry.py`, their
test files, `design.md` (incl. both corrections sections), and `marker-protocol.md`.
Pressure-test AT LEAST:

- **Restart safety.** `respawn-pane -k` kills a live Claude mid-anything — is the
  interlock (fresh hash-matching `.overseer-ready` + not-busy + settled) airtight
  against every ordering? Can a STALE or attacker-writable marker ever trigger a
  wrong restart? Can the daemon restart a session that is actually mid-work?
- **The settled-delta.** Two captures `_SETTLE_DELAY` apart — can a slow/paused
  stream read "settled" and cause an inject/restart mid-work? Is the residual
  window acceptable, and is restart still safe there (marker-gated)?
- **The verify-submit loop.** Can it false-succeed (box reads empty when the paste
  never landed)? Can it spuriously submit an empty message or clobber existing
  input? Bounded correctly (`_SUBMIT_MAX_ENTERS`)?
- **`is_busy` gaps.** The live TUI shows no persistent spinner while streaming
  (settled-delta covers it) — are there other busy forms (`· Proofing…`,
  `✢ …`) that could slip through BOTH `is_busy` AND the settled-delta?
- **`parse_ctx_remaining` / `is_idle_input`.** The bounded last-N-rows scan and
  the `❯`-between-rules detection — any real pane layout (narrow pane, wrapped
  statusline, plugin footer) that breaks them into a harmful (not fail-closed)
  reading?
- **Cross-repo / auto-link, archive-GC, fail-soft.** Any path that mutates the
  wrong repo's session, drops a live row, or crashes the loop on one bad input.
- **Concurrency.** Two overseer daemons, or a human typing in a tracked pane
  while the daemon acts.

A NO-BLOCKERS verdict from BOTH = done. Any serious blocker → fix (worktree→PR→
merge) + re-review the fix. Record verdicts + dispositions here.

## Resume command

`/livespec-orchestrator-beads-fabro:plan overseer-rewrite`
(or: `read plan/overseer-rewrite/handoff.md and follow it`)

## Guardrails

- Repo mutations: worktree → PR → rebase-merge; never commit on the primary;
  never `--no-verify` (`mise exec -- git …`). Only touch your own worktree.
- Live testing: isolated scratch sessions only; never touch real sessions; kill
  all scratch state when done.
- Before any handoff/exit: stop every background sub-agent/subprocess you spawned;
  leave the primary clean on `master`.

## Definition of DONE

Both remaining tasks pass: the full one-shot cycle completes unattended (+ archive-GC
+ reboot-recovery verified live), AND both fresh adversarial reviews return
NO-BLOCKERS (or their blockers are fixed + re-reviewed). Then archive this plan
thread (`plan/archive/overseer-rewrite/`) per the plan-thread close convention.
