# factory-safe-by-default — planning handoff (CLOSED)

**Ledger anchor:** `livespec-nrdk` (livespec core tenant) — CLOSED 2026-07-19.

**STATUS: THREAD COMPLETE, ACCEPTED, AND ARCHIVED (2026-07-19).** Everything
this thread set out to build is built, merged, live-exercised, and accepted.
All nine work-items went `acceptance → done`. No work remains here. This
document is a historical record — do NOT resume, dispatch, or groom from it.

**What it did:** invert livespec's factory doctrine to factory-safe by default —
assume any work-item can run on the automated build machinery, require a
machine-readable, admission-enforced opt-out (`factory_safety`) for the small
residue that genuinely cannot, and give that residue somewhere to surface for a
human (a distinct needs-attention `host-only` kind). Reshaped 2026-07-17 into
the two-axis model (`admission_policy` = *may a human approve it* vs.
`factory_safety` = *can a sandbox run it at all*); built, exercised, and closed
out 2026-07-18/19. Design rationale: `research/design.md` §"Reshape
(2026-07-17)".

## What landed (all merged; all subsequently accepted → `done`)

| Piece | Repo | PR | Note |
|---|---|---|---|
| A — spec/v040 | livespec-orchestrator-beads-fabro | #733 | ratified |
| B1 — field | livespec-runtime | (v0.10.0) | `factory_safety` on shared `WorkItem` |
| B2 — store+gate | livespec-orchestrator-beads-fabro | #755 | regex → field-backed `is_host_only_item` |
| B3 — store persist | livespec-orchestrator-git-jsonl | #308 | persists `factory_safety` (0.5.5) |
| bd-gj-9sj — janitor fix | livespec-orchestrator-git-jsonl | #312 | untracked branch-protection.sh; unblocked git-jsonl factory dispatch |
| bd-ib-y2o1 — fallback retire | livespec-orchestrator-beads-fabro | #763 | classifier now label-only (no prose regex) |
| C1 + C1b — kind | livespec-runtime | #253, #258 | `AttentionKind` gains `host-only` (v0.11.0); C1 first shipped `factory-safety`, corrected to `host-only` per maintainer |
| C2 — needs-attention | livespec-orchestrator-beads-fabro | #768 | surfaces not-factory-safe items + `factory_safety` refusals |
| C3 — needs-attention | livespec-orchestrator-git-jsonl | #326 | emits `kind="host-only"` w/ shell handoff (0.6.0) |
| C3 follow-up — impl-lane parity | livespec-orchestrator-git-jsonl | #333 | `impl_next` excludes not-factory-safe items (see finding below) |

`AttentionKind = human-valve|impl|spec|plan|hygiene|internal|host-only`.

## Acceptance (2026-07-19) — all nine `acceptance → done`

Accepted via `drive --action accept:<id>` (stage `human-valve-accept`) after a
per-item evidence audit. `accept:` is NOT mechanically gated on evidence
(`_accept_item` only checks `status == "acceptance"`), so each item was audited
individually rather than flipped en masse.

- **Directly exercised:** B2 (`bd-ib-qcnbbp`) — real stored row decoded
  `factory_safety` from the LABEL, `is_host_only_item` → True, admission valve
  returned `host-only-refused`/`failed`. C2 (`bd-ib-ayga`) — same row surfaced
  as `kind='host-only'` with a `shell` handoff. C3 (`bd-gj-5u8`) — real CLI
  emitted the host-only item with no contradiction.
- **Covered transitively:** B1 (B2's probe decoded into `item.factory_safety`);
  B3 (the C3 probe round-tripped the field through the real `append_work_item`
  write path); C1/C1b (both surfaces emitted `kind='host-only'` under the
  corrected name); `bd-gj-9sj` (a fresh worktree ran the fixed `just check`
  path — `branch-protection: OK — All 62 targets passed`).
- **`bd-ib-y2o1` had NO evidence and was exercised separately before accepting.**
  B2's labelled-item refusal proves nothing about whether the prose regex is
  gone; the item's actual claim is the NEGATIVE case. A scratch item naming
  `host-only` and `host_only` in BOTH title and description, with no label,
  decoded `factory_safety=None`, was not refused, and was not surfaced. Both
  scratch items used for evidence were deleted and verified gone.

## Finding found and FIXED — git-jsonl impl-lane contradiction

The live exercise caught a defect C3 had shipped: git-jsonl needs-attention
emitted, in ONE output, BOTH `kind='host-only'` ("host-route this; do not
dispatch") AND `kind='impl'` ("this is your next item to drive") for the SAME
not-factory-safe work-item. `attention_impl.impl_next` passed `rank_candidates`
UNFILTERED where the beads-fabro sibling filters `factory_safety is None` at the
analogous call site; git-jsonl runs NO dispatcher and has NO admission gate, so
nothing backstopped it.

FIXED — `livespec-orchestrator-git-jsonl` PR #333 (master `d4c4999`, CI green),
a one-line parity change authored Red→Green; no shim, no gate weakened, no test
skipped. Live before/after:

```
BEFORE  host-only=['gj-host']  impl=['gj-host']  CONTRADICTORY=['gj-host']
AFTER   host-only=['gj-host']  impl=['gj-safe']  CONTRADICTORY=NONE
```

Deliberately NOT changed: neither repo's `next.py` `rank_candidates` filters on
`factory_safety`, so leaving it alone IS the consistent choice; and git-jsonl
having no admission gate is correct-by-design (no dispatcher), not a gap.

## Related work that outlived this thread (NOT tracked here)

The fourth original goal — **widening what the automated build sandbox can
handle**, so fewer tasks need the "cannot be automated" exemption — was never
part of this thread's slices and is NOT complete. Earlier revisions of this
handoff said it was "coordinated under `z2ctra`"; **that was wrong** and is
corrected here. `bd-ib-z2ctra` is about adopter dispatch (per-tenant Fabro
server recipe + a dispatcher preflight that the targeted server's GitHub App can
reach the target repo) — related to dispatch capability, but not the toolchain
work. The remaining capability work is three separate BACKLOG items in the
`livespec-orchestrator-beads-fabro` tenant, none blocking anything this thread
delivered:

- **`bd-ib-9yi`** — the build sandbox image has no Rust, so the post-merge
  janitor fails with cargo-not-found for Rust target repos.
- **`bd-ib-2nq`** — the build system's GitHub App token expires after 60
  minutes, so any run longer than an hour dies at the push stage (part 1 merged
  as PR #429; parts 2–3 outstanding).
- **`bd-ib-z2ctra`** — adopter repos need their own Fabro server recipe plus a
  preflight credential-reachability check.

These matter because this thread's whole thesis was "assume everything is
factory-safe; keep the exception list tiny" — those three are what stops the
exception list from creeping back up.

## Findings recorded — do not re-litigate

- **Self-reference:** B2's first dispatch was refused by the very regex it
  removes; C1's first by the legacy fallback that replaced it. Both worked
  around by wording; the fallback is now retired (`bd-ib-y2o1`), so naming
  `host-only` in a work-item is safe again.
- **Value-name:** C1 shipped the kind as `factory-safety`; maintainer chose
  `host-only`; corrected via C1b.
- **Fan-out race:** dispatching a slice that bumps a runtime pin can race the
  release fan-out's own bump PR (C3/#324 conflicted, re-dispatched clean as
  #326). If master already bumped, re-dispatch on top of the stable master.
- **Live exercise beats CI (three times):** the C3 impl/host-only contradiction
  survived merge, CI, and AI acceptance, and surfaced only on the first real
  exercise of the shipped surface. The generalizable lesson: a test asserting a
  new lane APPEARS does not assert the item is ABSENT from the lanes it now
  contradicts — assert both sides whenever a change splits items across
  mutually-exclusive lanes.
- **Trust the ledger, not the handoff:** the `z2ctra` misattribution above rode
  forward through several handoff revisions unchallenged because each rewrite
  copied it instead of reading the item. Status and cross-references come from
  the ledger.
