# factory-safe-by-default — planning handoff

**STATUS: EPIC IMPLEMENTATION COMPLETE; ACCEPT-LEG EVIDENCE GATHERED
(2026-07-19).** The two-axis model (`admission_policy` = permission vs.
`factory_safety` = runnability) is fully realized in code across the fleet.
Slices A, B, and C are all merged; the janitor fix (`bd-gj-9sj`) and the
legacy-fallback retirement (`bd-ib-y2o1`) are done. All affected repos' master CI
is green. **There is NO ripe implementation work left in this thread — do NOT
dispatch or groom anything.** What remains: the maintainer's human accept legs
(live evidence now journaled), ONE open finding against C3, and Slice D
(coordinated under `z2ctra`).

**Thread summary:** invert livespec's factory doctrine to factory-safe by default —
assume any work-item runs in the factory, require a machine-readable
admission-enforced opt-out (`factory_safety`) for a small host-only residue, and
give that residue a home as a distinct needs-attention `host-only` kind. Reshaped
2026-07-17 into the two-axis model; built out 2026-07-18/19. See
`research/design.md` §"Reshape (2026-07-17)".

## Read-first chain (open these, in order, before acting)

1. **The ledger epic `livespec-nrdk`** (livespec core tenant) — read its comments
   LIVE; the last comment ("ACCEPT-LEG LIVE-EXERCISE EVIDENCE GATHERED") is
   authoritative:
   ```bash
   source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-nrdk
   ```
2. **`research/design.md`** §"Reshape (2026-07-17)" — the settled two-axis design.

## What landed (all merged; all parked in `acceptance` awaiting human accept)

| Piece | Repo | PR | Note |
|---|---|---|---|
| A — spec/v040 | livespec-orchestrator-beads-fabro | #733 | ratified (prior session) |
| B1 — field | livespec-runtime | (v0.10.0) | `factory_safety` on shared `WorkItem` |
| B2 — store+gate | livespec-orchestrator-beads-fabro | #755 | regex → field-backed `is_host_only_item` |
| B3 — store persist | livespec-orchestrator-git-jsonl | #308 | persists `factory_safety` (0.5.5) |
| bd-gj-9sj — janitor fix | livespec-orchestrator-git-jsonl | #312 | untracked branch-protection.sh; unblocks git-jsonl factory dispatch |
| bd-ib-y2o1 — fallback retire | livespec-orchestrator-beads-fabro | #763 | classifier now label-only (no prose regex) |
| C1 + C1b — kind | livespec-runtime | #253, #258 | `AttentionKind` gains `host-only` (v0.11.0); C1 first shipped `factory-safety`, corrected to `host-only` per maintainer |
| C2 — needs-attention | livespec-orchestrator-beads-fabro | #768 | surfaces not-factory-safe items + `factory_safety` refusals |
| C3 — needs-attention | livespec-orchestrator-git-jsonl | #326 | emits `kind="host-only"` w/ shell handoff (0.6.0) |

`AttentionKind = human-valve|impl|spec|plan|hygiene|internal|host-only`.

This handoff doc itself is tracked by successive `docs(plan):` commits on
`livespec` master; PR #1369 landed the prior revision.

## Accept-leg evidence (gathered 2026-07-19; journaled on each item)

Live-exercised against real state. **No accept was triggered** — every item stays
in `acceptance`. Full detail is on each item's comment thread.

- **B2 `bd-ib-qcnbbp` — GREEN.** Against a REAL beads-fabro row (scratch
  `bd-ib-d617`, label `factory-safety:needs-host-secrets`, deleted after): the
  store decoded `factory_safety` from the LABEL (label-only path, no prose
  regex); `is_host_only_item` → True; `host_only_refusal` → outcome
  `host-only-refused` / `failed` with the actionable host-route detail.
- **C2 `bd-ib-ayga` — GREEN.** The same real row surfaced as
  `kind='host-only'`, `urgency='high'`, with a `shell` host-route handoff.
  beads-fabro's `impl_next` correctly EXCLUDES not-factory-safe items.
- **C3 `bd-gj-5u8` — surfacing GREEN, but see the open finding below.**

Method note: B2 was exercised through the exact functions the admission valve
calls, not the full `dispatcher loop`, because the loop's post-verdict legs
(self-update, OTel egress, reflection) are host-mutating and must not fire
interactively merely to demonstrate a refusal. A refused item never reaches
`dispatch_one`, so no sandbox or token path is involved either way.

## Open finding — argues against accepting C3 as-is

The shipped git-jsonl needs-attention emits, in ONE output, BOTH
`kind='host-only'` ("host-route this; do not dispatch to Fabro") AND
`kind='impl'` ("this is your next item to drive") for the SAME not-factory-safe
work-item — self-contradictory operator guidance. Root cause:
`attention_impl.impl_next` passes `rank_candidates` UNFILTERED, where the
beads-fabro sibling filters `[item for item in items if item.factory_safety is
None]` at the analogous call site. `livespec-orchestrator-git-jsonl` runs NO
dispatcher and has NO admission gate, so nothing backstops that recommendation.
C3's tests assert only that the host-only item appears, never its absence from
the impl lane.

**Maintainer decision needed (deliberately NOT filed unilaterally):** neither
repo's `next.py` `rank_candidates` filters on `factory_safety` — the filter lives
only at beads-fabro's `impl_next` call site. So the fix is either a
git-jsonl-only `impl_next` parity patch, or a broader both-repos `next`-ranking
exclusion. Scope it, then file the work-item.

## Next actions (in order) — NONE are dispatch/groom work

1. **Decide the C3 finding's scope** (above) and file the resulting work-item.
2. **Human accept legs — MAINTAINER-OWNED, do NOT auto-accept.** B1/B2/B3,
   `bd-gj-9sj`, `bd-ib-y2o1`, C1(/C1b) and C2 now carry live evidence and are
   ready for the maintainer's accept. C3 should wait on the finding above.
3. **Slice D** — capability-widening (per-toolchain workflows + the Fabro
   GitHub-App-token 60-min-TTL candidate) stays under `z2ctra`. No action here.
4. **Optional cleanup:** the blessed reaper DECLINES the stale git-jsonl janitor
   worktrees — `janitor-bd-gj-5i1` and `-cn4` sit under the repo-local
   `worktrees/` dir (outside the reaper's `~/.worktrees` scan) and `-7adugd` is a
   protected detached-HEAD janitor worktree. Do NOT hand-delete them. The C3
   branch `feat/bd-gj-5u8` is already gone locally.

## Findings recorded (on the epic + items) — do not re-litigate

- **Self-reference:** B2's first dispatch was refused by the very regex it removes;
  C1's first by the legacy fallback that replaced it. Both worked around by wording;
  the fallback is now retired (`bd-ib-y2o1`) so naming `host-only` in a work-item is
  safe again.
- **Value-name:** C1 shipped the kind as `factory-safety`; maintainer chose
  `host-only`; corrected via C1b.
- **Fan-out race:** dispatching a slice that bumps a runtime pin can race the release
  fan-out's own bump PR (C3/#324 conflicted, re-dispatched clean as #326). If master
  already bumped, re-dispatch on top of the stable master.
- **Live exercise beats CI (third time):** the C3 impl/host-only contradiction
  survived merge, CI, and AI acceptance, and surfaced only on the first real
  exercise of the shipped surface.

## Standing constraints

- Status derived from the ledger, never trusted from this file.
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never `--no-verify`;
  doc-only plan edits use `docs(plan): ...`.
- Build ripe work factory-side (`drive --action impl:<id>` / Dispatcher) under the
  janitor gate — never hand-code inline. (N/A now — nothing ripe remains.)
