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
   - **Session missing (e.g. after a crash) → recover it**, preferring
     `claude --resume <session-id>` — this reloads the FULL pre-crash context.
     **Nothing is lost in a crash: every Claude session persists on disk**
     (`~/.claude/projects/<slug>/<id>.jsonl`); the tmux *window* dies, the
     *session* does not. Cold-start from the committed handoff (`run <handoff>`)
     is the alternative when you don't have the session id or want a clean
     restart — fine for any track whose state is externalized. See §"Cold start".
3. Fold in any other `livespec*` session running a livespec track not in the
   registry — discover and oversee it too.

## Track registry

Five live tracks, each in a fixed numbered session. Each recovers either by
**resuming its Claude session** (`claude --resume <id>` — preserves full
pre-crash context) or by **cold-starting from a committed handoff**. **The
overseer itself runs in `livespec-overseer`.**

| Session | Track | Epic | Recovery source |
|---|---|---|---|
| **livespec1** | Fleet-wide doctor-static enforcement | `livespec-6jfq` | handoff `prompts/doctor-static-fleet-enforcement-prompt.md` |
| **livespec2** | Register livespec-console in the fleet manifest (+ zs22 closure) | `livespec-zs22.7.8` | ledger scope (`bd show livespec-zs22.7.8`) — no standing handoff |
| **livespec3** | Dev-tooling single-source convergence | `livespec-zs22.7.9` | handoff `prompts/dev-tooling-single-source-convergence-handoff.md` |
| **livespec4** | Architecture mermaid-diagram cleanup (propose-change) | *ad-hoc* | `claude --resume 85750c9d-727c-4f22-aec7-d0d2fe4e2636` — **no handoff; resume is its only anchor** |
| **livespec5** | Governed-repo lifecycle (zs22 Increment 6) | `livespec-zs22.8` | handoff `prompts/governed-repo-lifecycle-handoff.md` |

Notes:
- **livespec2 (`zs22.7.8`)** is a discrete deferred task: add a `console`
  REPO_CLASS to the dev-tooling fleet contract + register livespec-console in the
  manifest. The `zs22` epic closes once `zs22.7.8` (livespec2) and `zs22.7.9`
  (livespec3) both land — the zs22 planning-lane increments (M0–M6) are already
  done and that handoff was archived.
- **livespec4 (mermaid)** is **maintainer-gated**: a diagram is drafted and it is
  **waiting for the maintainer's review/sign-off** before it files the
  propose-change. Keep it alive; do not push it past the review. ⚠️ It has **no
  committed handoff** — its only recovery anchor is the session id above. It
  should file a handoff so recovery stops depending on a remembered session id.
- **livespec5 (`zs22.8`)**: plan seeded (design doc
  `research/governed-repo-lifecycle/lifecycle-system-design.md`, PR #648);
  maintainer-gated next action is to file `zs22.8.1` (M1) as a propose-change.
- Sibling-repo sessions (`livespec-console-beads-fabro*`, `livespec-dev-tooling`,
  `livespec-impl-plaintext`) are separate repos — not overseen here unless told.

## Cold start / disaster recovery (sessions gone after a crash)

When `tmux ls` shows the track sessions are **missing** (VPS crash/reboot),
recreate each. First confirm the durable state recovered: the ledger is back
(`source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec list`
works → Dolt up), `git status` is clean on `master`, the handoff prompts exist
on disk, and reap any crash-orphaned worktrees (`git worktree list` → remove the
merged ones).

Then bring each track in §"Track registry" back, by **either** path:

```bash
tmux new-session -d -s <livespecN> -c /data/projects/livespec   # create the window

# A) RESUME the actual pre-crash session (preferred — reloads full context):
tmux send-keys -t <livespecN> -l 'claude --resume <session-id> --dangerously-skip-permissions'; tmux send-keys -t <livespecN> Enter
# if it offers "Resume from summary / Resume full session" → choose FULL for a mid-design track.

# B) COLD-START from the handoff (handoff-driven tracks, or if you lack the id):
tmux send-keys -t <livespecN> -l 'claude --dangerously-skip-permissions'; tmux send-keys -t <livespecN> Enter
# poll the pane until ready ("bypass permissions" / a "❯" prompt), THEN:
tmux send-keys -t <livespecN> -l 'run <handoff-prompt>'; tmux send-keys -t <livespecN> Enter
```

**Finding a session id** when you don't have it: search the transcripts —
`grep -l '<distinctive content>' ~/.claude/projects/-data-projects-livespec/*.jsonl` —
then **verify** by reading its last assistant message + token count before
resuming (a name like `w0c-mermaid-diagram` can be a TODO *inside* an unrelated
session, not its title — confirm the content matches).

**The lesson the crash taught — enforce it:** the crash proved **nothing is
lost** — every Claude session is on disk and resumable. BUT resume depends on
*finding the right session* (a remembered name / distinctive content), which is a
fragile anchor. The deterministic anchor is a **committed handoff + ledger
entries**. `livespec4`'s mermaid track had no handoff — it was recoverable only
because its session was findable, which is luck, not discipline. **Every track
must externalize its state to a committed handoff early and often**, not only at
the ~50% context mark.

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
- The five live track sessions are `livespec1`–`livespec5` (see registry). Name
  any **new** track/session `livespec6`, `livespec7`, … `livespecN`. The overseer
  is `livespec-overseer`. Sibling-repo sessions keep their repo-named sessions.
