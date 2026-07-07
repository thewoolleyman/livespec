# orchestrator-surface-parity — planning handoff

**Thread summary:** make the livespec orchestrator plugins **full peers** —
one identical skill SET across every orchestrator, each skill packaged for
BOTH the Claude and Codex runtimes, every description leading with its owning
plugin name, mechanically enforced. `livespec-orchestrator-git-jsonl` becomes a
full peer of `livespec-orchestrator-beads-fabro` (it gains drive/groom/plan/
list-plan-threads and a full `.codex-plugin`). CAPTURED for LATER work — do NOT
tackle inside the needs-attention track.

The single resumable entry point for this thread: a fresh session can execute
the next action from this file alone via the read-first chain — no chat history
required.

## Read-first chain (open these, in order, before acting)

1. **The ledger epic `livespec-xfqd`** (livespec core tenant) — read status and
   any comments **LIVE from the ledger**, never trust a status written in this
   file:
   ```bash
   source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-xfqd
   ```
2. **`research/design.md`** — the settled, maintainer-endorsed design: the
   two-parity-gaps analysis (runtime parity vs. cross-orchestrator parity), the
   2026-07-07 FULL-PEER decision, the canonical 12-skill set and git-jsonl's
   4-skill deficit, the precedent (the Driver's already-enforced same-eight-
   operations contract vs. the un-enforced orchestrator surface), the 6-slice
   plan (P1–P6), the open questions, and the relationship to
   `factory-safe-by-default` (livespec-nrdk) and `needs-attention`
   (livespec-bj9x).

## Current state

Thread opened 2026-07-07; design captured in `research/design.md`; epic
`livespec-xfqd` anchored (status is **derived from the ledger** — read it live
via the read-first chain, do not trust any value copied here). Decision is
settled: **FULL PEER**. **No slices filed yet** — the next step is to develop
the 6-slice plan into ready, dependency-layered slices, starting with P1.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan orchestrator-surface-parity
```

## Next actions

Develop the design's **Slice plan (6)** (see `research/design.md` §"Slice plan
(6)") into ready slices under this epic. **Start with P1** — the core spec
change that establishes the contract everything else depends on:

1. **P1 — core spec [propose-change → revise].** Define the canonical
   orchestrator skill set, cross-runtime identity (Claude ≡ Codex within an
   orchestrator), cross-orchestrator identity (every orchestrator ships the
   same set), and the description-leads-with-plugin convention — as an
   architecture-level, mechanically-checkable contract in core. Settle the
   open question first: exactly-identical-12 vs. a required floor + allowed
   backend-specific extras (the decision leaned exactly-identical; confirm).
   Requires **independent adversarial (Fable) review** + maintainer-gated
   ratification before `/livespec:revise` accepts it.

Then the dependent slices in order: **P4** (git-jsonl spec supersede OR3 v017)
→ **P2** (core dev-tooling enforcement check, dep P1) → **P3** (git-jsonl gains
4 skills + full `.codex-plugin`, dep P1 + P4) → **P5** (both orchestrators:
lead descriptions with plugin + single-source Claude/Codex descriptions) →
**P6** (beads-fabro: reconcile its own `.claude`/`.codex` needs-attention
description drift).

**Golden rule:** FILE ripe work + GROOM it; never hand-code implementation
inline in the planning session. Spec-side contract changes (P1, P4) go through
the normal `/livespec:*` lifecycle (propose-change → independent review →
revise); ledger slices are dispatched through the factory under the janitor
gate.

## Standing constraints

- Status is derived from the ledger, never stored here (no shadow queue).
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never
  `--no-verify`; doc-only plan edits use a `docs(plan): ...` subject.
- Ripe work is built factory-side under the janitor gate, never hand-coded.
- P5's description fix is what resolves the Codex-picker confusion the
  maintainer hit on 2026-07-07; it is deliberately deferred OUT of the
  needs-attention track (livespec-bj9x) into this thread.
