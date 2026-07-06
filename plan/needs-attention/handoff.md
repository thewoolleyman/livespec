# needs-attention — track handoff (overseer run-prompt)

**Track:** `needs-attention` · **Repo:** `thewoolleyman/livespec` ·
**Ledger epic anchor:** `livespec-bj9x` (read status LIVE from the
ledger; never trust a status written here).

**Read-first chain (open these, in order, before acting):**

1. `research/design.md` — the settled design + the full cross-repo rollout.
2. `research/glossary.md` — every term used below.

## How to drive this track

This track is driven by the **local `overseer` skill**
(`.claude/skills/overseer/SKILL.md`) running it as a single plan-driven
track. Adequacy note (see "Gate map" below): the overseer + the
`ready-queue-drain` prototype drive the **autonomous factory portion**
(dispatching ready code work-items once they exist), but this track's
critical path is front-loaded with **by-design maintainer-owned gates**
(the initial `groom`, each spec ratification with its independent Fable
review, and the exit gate). The overseer **surfaces** those with a
recommendation; it does not resolve them, and it should not — auto-
resolving them would violate the declared maintainer-owned-gate
disciplines. So this track runs **semi-autonomously**: hands-off between
gates, maintainer at each gate.

### The prompt to run (paste into an overseer session)

```
Run the overseer skill (.claude/skills/overseer/SKILL.md). Register ONE
plan-driven track and drive it to completion, in isolation (no other
tracks this run):

  Track:  needs-attention
  Repo:   /data/projects/livespec   (epic anchor: livespec-bj9x)
  Thread: plan/needs-attention/  (read research/design.md + research/glossary.md first)

Read %Complete and every lane LIVE from the ledger (bd -C /data/projects/livespec
show livespec-bj9x, via the credential wrapper). Print the
Epic · Track · Status · %Complete table before any gate or status report.

Drive it in this order, surfacing each maintainer-owned gate WITH a
recommendation (one clickable pick at a time) and continuing autonomously
between gates:

1. DECOMPOSE FIRST. livespec-bj9x has no children yet. Surface
   `/livespec-orchestrator-beads-fabro:groom livespec-bj9x` as the first
   gate — the maintainer owns the cut. Feed the groomer research/design.md
   section "Rollout" as the slice source, foundational-first:
   livespec-runtime -> orchestrator plugins -> livespec core -> console -> adopters.

2. SPEC PIECES route through the spec lifecycle: /livespec:propose-change
   in the owning repo -> independent Fable review (mandatory, read-only,
   separately spawned) -> surface ratification (/livespec:revise) as a
   maintainer gate. The spec pieces are: the orchestrate->drive rename +
   the next scope-asymmetry note (orchestrator repos), and the Attention
   narrow/broad reconciliation + needs-attention rename (console repo).

3. CODE PIECES, once groomed to `ready` and their spec deps landed, are
   dispatched through the factory. Drive the ready queue with the
   ready-queue-drain prototype
   (.claude/skills/ready-queue-drain.md) against each owning repo:
   dispatch -> land -> AI-approve -> accept-on-behalf -> close, sequential,
   verifying each landing. Ask ONCE for accept-on-behalf authorization per
   batch; hold thereafter.

4. Enumerate backlog + pending-approval every survey (the not-yet-ready
   scan) so nothing strands; surface groom cuts and approvals.

5. EXIT GATE: when every child is `done`, surface closing the epic
   livespec-bj9x to the maintainer; do not close it autonomously.

Never hand-code inline; never --no-verify; verify every landing against
the live ledger + master-ancestor, not a session's self-summary.
```

## Gate map (what will surface, and why it is correct)

| Step | Overseer does | Maintainer gate |
|---|---|---|
| Decompose epic | surfaces `groom livespec-bj9x` | **groom cut** (maintainer owns the slice) |
| Spec pieces | drives propose-change + spawns Fable review; surfaces ratification | **spec ratification** (+ mandatory Fable review) |
| Code pieces | dispatches ready items through the factory (drain) | **accept-on-behalf** authorized once per batch |
| Not-yet-ready scan | enumerates backlog/pending-approval | groom / approve, per item |
| Close | surfaces the exit gate | **exit gate** (close the epic) |

## Standing constraints

- Status is derived from the ledger, never stored here (no shadow queue).
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never `--no-verify`.
- Ripe work is built factory-side under the janitor gate, never hand-coded.
- Observability/telemetry is deferred (`design.md` §"Deferred") — out of this rollout.
