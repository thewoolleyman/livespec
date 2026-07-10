# Fable fresh-review brief — autonomous-mode plans (review-loop round N)

**Who runs this:** a FRESH Fable-model session with NO prior involvement in
authoring or revising these plans. A session that revised the plans MUST NOT
review them (no self-certification — maintainer-declared 2026-07-10).

**The loop this brief serves.** The fable-review phase does NOT exit until
BOTH hold: (1) a fresh-session review of the current plans finds NOTHING
BLOCKING, and (2) the MAINTAINER certifies. Any blocking finding routes to a
fable-revise pass (fixes landed in the plan texts via worktree → PR → merge),
after which ANOTHER fresh session runs this brief again. Implementation
(console C1 / orchestrator O1) MUST NOT start before the gate is met. The
loop state lives in `plan/autonomous-mode/handoff.md` (repo
`thewoolleyman/livespec`).

## What to review (all three, current `origin/master`)

| Plan | Repo | Path |
|---|---|---|
| Overall | `thewoolleyman/livespec` | `plan/autonomous-mode/{handoff,design}.md` |
| Console operator surface | `thewoolleyman/livespec-console-beads-fabro` | `plan/autonomous-mode/{handoff,design}.md` |
| Orchestrator engine | `thewoolleyman/livespec-orchestrator-beads-fabro` | `plan/autonomous-mode/{handoff,design}.md` |

Prior rounds (read AFTER forming your own view, to check nothing was lost):
`research/step0-fable-verdict.md` (round 1, against the pre-revision plans)
and `research/fable-revising-session-self-assessment.md` (the revising
session's own claims — treat every claim in both as a hypothesis to verify,
never as truth).

## How to review

READ-ONLY: no edits, no commits, no ledger writes. Verify — do not trust —
the plans' factual claims against the real spec trees (`git show
origin/master:<path>`), the crate/script sources, the Beads ledgers (`bd
show <id> --json` via the repo's credential wrapper, run from inside each
repo), and master CI (`gh run list --workflow CI`). Cover at minimum:

- **Factual currency** — every state claim (spec versions, pending
  proposals, implementation absences, ledger item statuses, "verified
  drift-free" claims) is true TODAY.
- **Internal soundness** — each step has an owner, a gate, and a checkable
  "done"; step order self-consistent.
- **Cross-plan dependency correctness** — the graphs agree across the three
  documents; the I1 contract-first handshake and the C1
  persistence-seam-after-I1 sequencing hold; no circular or missing edge.
- **The pinned seam resolutions** — persistence model (single persistent
  permission key), division of resolution (engine owns gate resolution;
  Scenario-10 re-scope), vocabulary fixes — are the pins coherent, complete,
  and consistent with BOTH repos' live specs?
- **Goal reachability** — executing every step in order produces the MVP
  (TUI toggle → unattended factory → audited auto-resolutions →
  truly-unresolvable surfaces in-TUI) and passes I2 under its full gate.
- **Scope discipline and mechanics** — TUI-only; disciplines named
  (worktree → PR → merge, `mise exec -- git`, never `--no-verify`,
  Red-Green-Replay, heading-coverage co-edits, per-ratification Fable
  review).

## Verdict (your only output)

```
## Round N fresh review: NOTHING-BLOCKING | BLOCKERS FOUND
### Per-plan: <one line each>
### Blockers (if any): what, where, why it blocks, recommended fix
### Non-blocking observations
### Currency findings
```

Deliver the verdict in-session; the driver/maintainer records it as
`research/fable-review-round-N.md` on this thread and updates the handoff's
loop state. NOTHING-BLOCKING → present to the maintainer for certification.
BLOCKERS FOUND → a revise pass lands the fixes, then a NEW fresh session
runs this brief.
