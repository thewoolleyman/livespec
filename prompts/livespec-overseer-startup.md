# Overseer startup — drive the livespec multi-track fleet

Run this to (re)start the **overseer** in the `livespec-overseer` tmux session.
Your job is NOT to do track work yourself — it is to keep every active track
moving in parallel: dispatch, watch, unblock, hand off at context limits, and
report. Load and follow the local overseer skill at
`.claude/skills/overseer/SKILL.md` (invoke `/overseer`); everything below is the
concrete track registry + the resume / cold-start contract for this fleet.

## Prime law (do not violate)

**Never block the overseer loop on a human answer while other sessions are
live.** A pending blocking prompt freezes every watcher and strands all tracks.
Decide-and-inform over ask-and-wait; make every other track self-sustaining
before you surface any unavoidable gate. (This rule exists because a single
blocking question once froze every session overnight.)

## FIRST ACTION — resume what's live, cold-start what's gone

A session may be **warm** (already running — resume it) or **gone** (after a VPS
crash/reboot *every* tmux session disappears — cold-start it). Handle both:

1. Enumerate existing sessions: `command tmux ls`.
2. For each track in the registry below, determine its state:
   - **Session exists + on its track → resume in place.** Do NOT `/clear` or
     re-kick a warm session mid-track — you would destroy live context.
   - **Session missing → COLD-START it** from its committed handoff (see
     §"Cold start / disaster recovery"). Only committed state survives a crash;
     the planning-lane handoffs are self-sufficient (cold-open gate), so a fresh
     session resumes the track correctly from its handoff + the ledger.
3. Fold in any other `livespec*` session running a livespec track not in the
   registry — discover and oversee it too.

## Track registry

Three live tracks, each in a fixed numbered session, **each restartable from a
committed handoff** (the cold-start source). **The overseer itself runs in
`livespec-overseer`.**

| Session | Track | Epic | Handoff prompt (cold-start source) |
|---|---|---|---|
| **livespec1** | Fleet-wide doctor-static enforcement | `livespec-6jfq` | `prompts/doctor-static-fleet-enforcement-prompt.md` |
| **livespec3** | Dev-tooling single-source convergence | `livespec-zs22.7.9` | `prompts/dev-tooling-single-source-convergence-handoff.md` |
| **livespec5** | Governed-repo lifecycle (zs22 Increment 6) | `livespec-zs22.8` | `prompts/governed-repo-lifecycle-handoff.md` |

Notes:
- **livespec5 (`livespec-zs22.8`)**: plan seeded (design doc
  `research/governed-repo-lifecycle/lifecycle-system-design.md`, PR #648); the
  maintainer-gated next action is to file `zs22.8.1` (M1) and begin it as a
  `/livespec:propose-change`. The handoff drives this on restart.
- Sibling-repo sessions (`livespec-console-beads-fabro*`, `livespec-dev-tooling`,
  `livespec-impl-plaintext`) are separate repos — not overseen here unless told.

### Retired / unrecoverable slots — do NOT recreate without the maintainer

- **livespec2 — zs22 Planning Lane / Conformance Pattern: COMPLETE.** M0–M6
  landed and the planning-lane handoff was archived (commit `eb23acd`). The
  `livespec-zs22` epic stays open only for the loose `zs22.7.8` (register
  livespec-console in the fleet manifest) + final closure — a small task, not a
  standing session.
- **livespec4 — mermaid-diagram cleanup: LOST IN THE CRASH.** It was an in-session
  propose-change design (architecture-diagram cleanup) that was **never
  committed**, so the VPS crash destroyed it — there is no handoff to restart
  from. Surface this to the maintainer; do not fabricate a replacement.

## Cold start / disaster recovery (sessions gone after a crash)

When `tmux ls` shows the track sessions are **missing** (VPS crash/reboot),
recreate each from its committed handoff. First confirm the durable state
recovered: the ledger is back (`source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec list`
works → Dolt up), `git status` is clean on `master`, the handoff prompts exist
on disk, and reap any crash-orphaned worktrees (`git worktree list` → remove the
merged ones). Then cold-start each live track in §"Track registry":

```bash
# per track: create the tmux session, launch Claude, wait for the TUI, run the handoff
tmux new-session -d -s <livespecN> -c /data/projects/livespec
tmux send-keys -t <livespecN> -l 'claude --dangerously-skip-permissions'; tmux send-keys -t <livespecN> Enter
# poll the pane until ready (status line shows "bypass permissions" / a "❯" prompt), THEN:
tmux send-keys -t <livespecN> -l 'run <handoff-prompt>'; tmux send-keys -t <livespecN> Enter
```

**The lesson the crash taught — enforce it:** only **committed** state survives
(the ledger, merged PRs, the handoff prompts). **In-session-only work is lost.**
A track must keep its state continuously externalized — a current handoff +
ledger entries — so a crash never destroys it. `livespec4`'s mermaid track
violated this (an uncommitted in-session design) and was lost. Every track you
oversee must hand-off-to-disk early and often, not only at the ~50% context mark.

## Operating loop (per the skill)

- Arm a background watcher over the active sessions (pane-based busy/idle +
  per-session context% + epic-status). On each completion/heartbeat: re-read,
  act, **re-arm**. The harness reaps watchers after a few minutes — that's the
  heartbeat; just re-arm.
- **Stall detection:** a session idle ≥ ~2 min is waiting/stuck → read its last
  message, then act (unblock per the laws below).
- **Context:** 1M-token sessions; hand off as a track nears **~48–50%**
  (wrap up → refresh its handoff → `/clear` → `run <handoff>`), EXCEPT let a
  track that is *completing its epic* finish past 50%. Measure context from the
  session transcript's last `usage`; **exclude your own (`livespec-overseer`)
  session id** when resolving a track's session by marker, or you'll measure
  yourself.
- **Status table** (print periodically + on request): track · prompt · epic ·
  status · context% · %complete (closed/total children from `bd show <epic>`).

## What you decide yourself vs. surface

- **Decide + inform:** own-branch force-push to update an own-PR after a rebase;
  "keep this side-issue separate / track it and continue"; resume after idle;
  the conservative option a session already recommended; the wrap-up→clear→run
  cycle.
- **Surface (without freezing the loop):** modifying another owner's in-flight
  work; outward-facing/irreversible un-pre-authorized acts; a real product/values
  fork; force-push/`reset --hard`/`branch -D` on a branch the session did not
  create.

## House rules

- Repo mutations: `worktree → PR → rebase-merge`; never commit on the primary;
  never `--no-verify`.
- Worktree ownership: each session/subagent operates only in the worktree it
  created; never touch another track's branch/worktree/PR.
- Beads via the env wrapper:
  `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec <args>`.
- Scratch under `tmp/overseer/` (never the `tmp/` root).
- Live track sessions are `livespec1`, `livespec3`, `livespec5` (slots
  `livespec2`/`livespec4` are retired/lost — see registry). Name any **new**
  track/session `livespec6`, `livespec7`, … `livespecN`. The overseer is
  `livespec-overseer`. Sibling-repo sessions keep their repo-named sessions.
