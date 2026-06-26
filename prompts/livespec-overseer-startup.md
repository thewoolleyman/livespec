# Overseer startup — drive the livespec multi-track fleet

Run this to (re)start the **overseer** in the `livespec-overseer` tmux session.
Your job is NOT to do track work yourself — it is to keep every active track
moving in parallel: dispatch, watch, unblock, hand off at context limits, and
report. Load and follow the local overseer skill at
`.claude/skills/overseer/SKILL.md` (invoke `/overseer`); everything below is the
concrete track registry + the resume contract for this fleet.

## Prime law (do not violate)

**Never block the overseer loop on a human answer while other sessions are
live.** A pending blocking prompt freezes every watcher and strands all tracks.
Decide-and-inform over ask-and-wait; make every other track self-sustaining
before you surface any unavoidable gate. (This rule exists because a single
blocking question once froze every session overnight.)

## FIRST ACTION — RESUME, don't restart

The tracks below are almost certainly **already running** in tmux sessions. Do
NOT clear or re-kick a session that is mid-track — you would destroy live work.

1. Enumerate every `livespec*` tmux session: `command tmux ls`.
2. For each, capture the pane + read its transcript tail, and **identify which
   track it is on** (by epic id / milestone markers — see registry below).
3. If a session is **already on its track → CONTINUE overseeing it in place**
   (watch for stall/idle, unblock, hand off at ~50%). Resume where it is.
4. Only **kick off** a track's handoff prompt in a session that is idle/fresh or
   does not exist yet.
5. Fold in **any other** `livespec*` session running a livespec track that isn't
   in the registry — discover it and oversee it too.

## Track registry

The five tracks have each been migrated to their own fixed numbered session
(`livespec1`–`livespec5`), one track per session — already running. **The
overseer itself runs in `livespec-overseer`.** Resume each track **in place**
(its session holds live context); never `/clear` or restart a session mid-track.

| Session | Track | Epic / item | Handoff prompt |
|---|---|---|---|
| **livespec1** | Fleet-wide doctor-static enforcement | `livespec-6jfq` | `prompts/doctor-static-fleet-enforcement-prompt.md` |
| **livespec2** | Planning Lane + Conformance Pattern (zs22) | `livespec-zs22` (remaining: `zs22.7.8` register console + epic closure) | `prompts/livespec-zs22-handoff-planning-lane.md` |
| **livespec3** | Dev-tooling single-source convergence | `livespec-zs22.7.9` | `prompts/dev-tooling-single-source-convergence-handoff.md` |
| **livespec4** | Architecture / mermaid-diagram cleanup (propose-change) | *ad-hoc design session — no standing epic/handoff yet* | *resume by reading the session* |
| **livespec5** | Governed-repo lifecycle (zs22 Increment 6) | `livespec-zs22.8` | `prompts/governed-repo-lifecycle-handoff.md` |

Notes:
- **livespec2 (zs22)** is winding down: `zs22.7` is 7/9 (M6 / `zs22.7.7` closed);
  it closes (with parent `zs22`) only when `zs22.7.8` (livespec2) and `zs22.7.9`
  (livespec3) land.
- **livespec4 (mermaid cleanup)** is an in-session propose-change design
  **awaiting the maintainer's review** of the diagrams before it files. Keep it
  alive; do NOT restart or `/clear` it. It is maintainer-gated — do not push it
  past the review.
- **livespec5 (governed-repo lifecycle, `livespec-zs22.8`)** has its plan seeded
  (design doc `research/governed-repo-lifecycle/lifecycle-system-design.md`,
  handoff `prompts/governed-repo-lifecycle-handoff.md`, PR #648). The session
  holds the just-completed plan; the maintainer-gated next action is to file
  `zs22.8.1` (M1) and begin it as a `/livespec:propose-change`. Start execution
  on the maintainer's go.
- Sibling-repo sessions (`livespec-console-beads-fabro*`, `livespec-dev-tooling`,
  `livespec-impl-plaintext`) are separate repos — NOT part of this fleet of five
  and not overseen here unless told.

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
- `livespec1`–`livespec5` are the current five tracks; name any **new**
  track/session `livespec6`, `livespec7`, … `livespecN`. The overseer is
  `livespec-overseer`. Sibling-repo sessions keep their repo-named sessions.
