# Handoff — retire-research-dirs

The single resumable entry point for fully retiring the root
`research/` directories across the livespec fleet and the openbrain
adopter — the maintainer-directed successor to the
`cleanup-research-and-prompt-cruft` epic, superseding its "living
references stay in research/" end-state. A fresh session executes the
next action from this file alone via the read-first chain — no chat
history required.

## For a fresh session — read first

- **What this is.** ~18 remaining `research/` files across 4 repos
  (livespec, livespec-orchestrator-beads-fabro, livespec-dev-tooling,
  openbrain) either ARCHIVE, RELOCATE to a living home, or drive a
  REVISE of the Planning-Lane language that still blesses `research/`.
  Full per-item map, reference-retarget lists, ordering constraints,
  and the end-state assertion:
  `plan/retire-research-dirs/research/01-residual-map.md` — read it
  before acting. (Deep evidence: the predecessor thread's archived
  tables under `plan/archive/cleanup-research-and-prompt-cruft/research/`.)
- **Epic anchor:** `livespec-gt7crt` (livespec tenant). Status is READ
  from the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-gt7crt
  ```
  openbrain is an independent tenant — its commands run under ITS
  wrapper: `source /data/projects/openbrain/scripts/with-openbrain-env.sh
  bd -C /data/projects/openbrain …` (never the livespec one).
- **⚑ Golden rules** (all inherited from the predecessor epic, still
  binding):
  - Every repo mutation: worktree → PR → merge → cleanup in ITS OWN
    repo (`~/.worktrees/<repo>/<branch>`), `mise exec -- git …`, never
    `--no-verify`, halt + report verbatim on hook failure; never touch
    another session's worktree/branch.
  - Spec files change ONLY via propose-change → revise; revise lands
    before (or atomically with) the move it de-references. Plugin
    prose (`.claude-plugin/prose/`) is edited directly.
  - The orchestrator `lessons.md` path change is product code: full
    Red-Green-Replay TDD (one commit, Red test alone → Green amend).
  - Moves are `git mv`; inbound-reference retargets land in the SAME
    PR; each repo's full gate green before merge. Work-item ledger
    statuses use lifecycle values (`backlog`/`ready`/…, NEVER `open`).
  - Factory dispatch needs: item `ready` + `admission:auto` label
    (maintainer approval) + `--fabro-bin /home/ubuntu/.local/bin/fabro`
    (the credential wrapper drops `~/.local/bin` from PATH).
  - Secrets probe-only; no reapers during active dispatch; overseer
    rotates before ~50% context (refresh THIS file, print the resume
    command verbatim as the recap's last line).
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan retire-research-dirs`

## The next action

**Finish Phase 0: take design gate 2** (gate 1 is DECIDED — see the
residual map: the whole `research/loop-reflection-gate/` directory
moves to top-level `loop-reflection-gate/` in
livespec-orchestrator-beads-fabro, executed via a dedicated PR that
also opens that repo's `plan/loop-reflection-gate/` thread on epic
`livespec-impl-beads-29f`):

2. New home for openbrain's live `ob1-fork-patches.md` registry
   (recommendation: `docs/ob1-fork-patches.md`) — one picker,
   recommendation first.

Record the verdict in the residual map's gate section ("DECIDED:
<home>") via this thread's worktree → PR flow. Then proceed to
Phase 1 for the three remaining repos (livespec, dev-tooling,
openbrain) — the orchestrator's share is done when the gate-1 PR is
merged.

## Phase plan

- **Phase 0 — design gates.** As above. No mutation elsewhere before
  both verdicts land.
- **Phase 1 — per-repo execution.** File one child work-item per repo
  in that repo's OWN tenant (lifecycle status `ready`, cite
  `livespec-gt7crt`), then execute the residual map per repo — via
  factory dispatch where the item is autonomously verifiable, or a
  briefed executor agent where the changeset spans a spec revise. Four
  repos are file-disjoint and run in parallel; each changeset carries
  the cross-repo comment retargets the map assigns to IT (livespec:
  its `ci.yml:81`; dev-tooling: `branch-protection.sh:15`; openbrain:
  its `AGENTS.md:304`).
- **Phase 2 — fleet re-scan + close.** Assert the end-state per the
  residual map §"End-state assertion"; verify children closed; close
  `livespec-gt7crt`; archive this thread
  (`git mv plan/retire-research-dirs/ plan/archive/retire-research-dirs/`).

## Session log

### Session 1 (2026-07-04) — thread opened

- Trigger: maintainer question "what about the follow-ups to merge the
  remaining stuff into the respective specs to fully retire the old
  locations?" → answer: none existed (confirmed-D1 kept them);
  maintainer chose "open thread, drive it" from the picker.
- Filed epic anchor `livespec-gt7crt` (livespec tenant, status
  `backlog` — the predecessor epic's `open`-status conformance lesson
  applied at filing time).
- Authored this scaffold (`research/01-residual-map.md` + `handoff.md`)
  from the predecessor's verified dispositions; landed via the
  Session-1 scaffold PR (if you read this on master, it landed and the
  scaffold worktree/branch are gone).
- Cold-open self-sufficiency gate: PASS on run 1 (two non-blocking
  nits folded in: lowercase `delete`/`edit` verbs added to the
  vocabulary; anchors-drift rule already covered the one drifted line
  number).
- Maintainer answered lessons.md deep-dive questions (purpose, format,
  consumers) and DECIDED gate 1: whole directory → top-level
  `loop-reflection-gate/`, markdown stays; an orchestrator-repo
  executor was dispatched for the TDD move + reference sweep + 29f
  ledger repoint + the new `plan/loop-reflection-gate/` thread + a new
  child work-item for the missing lessons brief-injection consumer.
  Gate 2 (ob1-fork-patches home) remains open.
