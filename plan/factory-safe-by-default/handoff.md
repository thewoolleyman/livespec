# factory-safe-by-default — planning handoff

**Thread summary:** invert livespec's factory doctrine to **factory-safe by
default** — assume any work-item runs in the factory, require a machine-readable
admission-enforced opt-out for a small enumerable host-only residue, widen
factory capability so that residue stays tiny, and give the residue a home as a
distinct needs-attention host-only-action kind.

The single resumable entry point for this thread: a fresh session can execute
the next action from this file alone via the read-first chain — no chat history
required.

## Read-first chain (open these, in order, before acting)

1. **The ledger epic `livespec-nrdk`** (livespec core tenant) — read status and
   any comments **LIVE from the ledger**, never trust a status written in this
   file:
   ```bash
   source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-nrdk
   ```
2. **`research/design.md`** — the settled, maintainer-endorsed design: the
   two-classes-not-one analysis of the 2026-07-07 dispatch wave, the thesis, the
   irreducible residue, the four moves, cost/implications, the relationship to
   existing work (z2ctra, needs-attention epic livespec-bj9x, bd-gj-9sj), and the
   open questions / candidate slices.

## Current state

Thread opened 2026-07-07; design captured in `research/design.md`; epic
`livespec-nrdk` anchored (status is **derived from the ledger** — read it live via
the read-first chain, do not trust any value copied here). **No slices filed
yet** — the next step is to develop the open questions into ready, dependency-
layered slices.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan factory-safe-by-default
```

## Next actions

Mirror the design's **Open questions / candidate slices** (see
`research/design.md` §"Open questions / candidate slices"); develop each into a
ready slice under this epic:

1. **Label schema** — decide work-item label vs. a first-class schema field for
   the `not-factory-safe: <reason>` opt-out; finalize the reason enum
   ({needs-host-secrets, mutates-host-machinery, needs-privileged-host}; plus the
   already-not-factory requires-human-judgment case).
2. **Admission gate** — the dispatcher pre-check location + refusal message;
   settle the interaction with explicit `--item` targeting (does an explicit
   target override, or still refuse?).
3. **Host-only needs-attention kind** — schema + renderer + how the
   overseer/console consume it; dovetail with the needs-attention track (epic
   `livespec-bj9x`).
4. **Capability roadmap** — enumerate every fleet toolchain; author per-repo
   target-local workflows (console = Rust exemplar, openbrain = pnpm exemplar);
   land bd-gj-9sj (git-jsonl janitor worktree-pack hydration).
5. **Spec home** — the orchestrator (beads-fabro) contract for the classification
   + admission gate; git-jsonl parity.

**Golden rule:** FILE ripe work + GROOM it; never hand-code factory-safe
implementation inline in the planning session. Spec-side contract changes go
through the normal `/livespec:*` lifecycle (propose-change → independent review →
revise); ledger slices are dispatched through the factory under the janitor gate.

## Standing constraints

- Status is derived from the ledger, never stored here (no shadow queue).
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never
  `--no-verify`; doc-only plan edits use a `docs(plan): ...` subject.
- Ripe work is built factory-side under the janitor gate, never hand-coded.
