# Handoff — github-request-budget-discipline

**Thread anchor (ledger epic):** `livespec-httc`, in THIS repository's tenant
(`livespec`). This handoff records no status of its own; read status from the
ledger.

**One-line state:** the Contract and Installer slots are DONE and on master; the
Mechanism and Verifier slots are un-dispatched and ready to drive. Nothing is
blocked and no cleanup is outstanding.

## Read-first chain

Read these, in order. Nothing else is required.

1. `plan/github-request-budget-discipline/research/01-design.md` — the design
   record: the incident, the verified GitHub limits, the propagation-surface
   analysis, the Conformance-Pattern reframing, and the two obligations recorded
   after review.
2. `SPECIFICATION/non-functional-requirements.md` §"Request-budget discipline" —
   the ratified contract this thread implements (added by revision `v195`).
3. `.ai/dispatcher-drain-operations.md` — REQUIRED before driving any factory
   dispatch. Read it even if you think you know the flow.

## Compose current status first

```bash
/usr/local/bin/with-livespec-env.sh -- bd show livespec-httc
```

The epic's notes carry the full slot-by-slot record. Cross-tenant items are cited
in prose because beads cannot resolve a foreign-tenant id (`bd-ib-dvmh`); read one
with `bd show <id>` from inside that repository's checkout, under the same
credential wrapper.

## What is DONE — do not redo

- **Contract slot.** Ratified as spec revision `v195` (livespec PR #2030,
  merged). `SPECIFICATION/non-functional-requirements.md` now registers
  **Request-budget-discipline** in the Conformance-Pattern concern registry and
  carries a `### Request-budget discipline` section filling all five slots.
- **Installer slot.** `livespec-driver-claude-6xj` — merged by factory dispatch
  (PR #423, `merge_sha 776827d6`), released as `v0.5.0`.
  `github_rate_limit_guard.py` ships in that plugin's own
  `.claude-plugin/hooks/hooks.json`. Live-exercised through the adopter
  `resume`'s resolved plugin path: poll loop denied, bulk-mutation loop denied,
  ordinary read allowed, fail-open on malformed input, and ZERO occurrences of
  the guard in that adopter's own committed settings. Both acceptance legs are
  discharged and journaled on the item.
- **Blocker cleared.** `livespec-runtime-s8q` (P0, master red) is CLOSED. It
  resolved upstream: the dev-tooling pin moved v1.18.9 → v1.19.9 and restored the
  `pure_trees` role-absence gate, so the eleven ROP violations are no longer
  surfaced and the cross-repo migration that item anticipated is NOT required.
  `livespec-runtime` master CI is green.
- **Side deliverable.** `.ai/verifying-against-the-right-source.md` gained
  instances 17 and 18 (livespec PR #2034), plus repair of a stale instance count
  in `AGENTS.md`.

## NEXT ACTION — dispatch the Mechanism slice

`livespec-runtime-lzq` (Slice A: budget measurement — rate-limit snapshot, 403
classification, UNMEASURABLE outcome) is at status `pending-approval` with a
clean tree and nothing in flight. The dispatcher promotes it from that status on
admission; this was observed twice.

Preflight, then dispatch:

```bash
cd /data/projects/livespec-runtime
git status --short          # MUST be clean; the engine pushes the checkout state
mise exec -- git pull --ff-only origin master
```

Then run the dispatch **backgrounded, with NO kill timer**:

```bash
/usr/local/bin/with-livespec-env.sh -- python3 \
  "$(ls -d /home/ubuntu/.claude/plugins/cache/livespec-orchestrator-beads-fabro/livespec-orchestrator-beads-fabro/*/scripts/bin/drive.py | head -1)" \
  --action impl:livespec-runtime-lzq --repo /data/projects/livespec-runtime --json
```

⚠️ **NEVER wrap a dispatch in `timeout`.** A dispatch runs 7–76 minutes. A timer
that fires mid-run kills the supervising process while the sandbox keeps going,
orphaning the container and leaving the ledger item stuck at `active`. That
happened twice in the prior session. Recovery is documented on
`livespec-runtime-lzq`'s notes; the short version is that NO valve fixes it
(`approve:` requires manual admission, `resolve-blocked:` requires `blocked`, and
the reclaim path only journals a WIP-cap record), so the item must be reset to
`pending-approval` by hand.

After it lands, dispatch **`livespec-runtime-g2s`** (Slice B: conditional reads,
mutation pacing, backoff, reserved floor). It depends on slice A and must not be
driven before it.

## Then — the Verifier slice

`livespec-dev-tooling-t2q4` is deliberately **NOT** routed to `ready`, and this is
load-bearing: its real dependency is on the slice-A client in a DIFFERENT tenant,
which beads cannot express as an edge. Nothing in the machinery will stop the
factory from dispatching it early — only this instruction will. Route it only
after slice A has merged, then dispatch it the same way.

## Routing rules that bind every remaining slice

- Implementation is **factory-side**. Use `drive --action impl:<id>` or let the
  Dispatcher drain. Do NOT use the in-session `implement` operation; none of
  these items is recorded as factory-ineligible.
- If a dispatch is refused with *"dispatcher plugin build is stale"*, run
  `just ensure-plugins` from `/data/projects/livespec` and re-dispatch from the
  NEW cache path. That is the Plugin-currency gate working, not a defect.
- Keep dispatchable descriptions near ~1500 chars. All four items were resized
  for this; a 7196-char item is recorded as losing a full factory hour mid-publish.
- Verify a dispatch outcome from THREE sources — the drive result block's
  `status`/`merge_sha`, the forge, and the ledger. A shell exit code is the last
  command's status, never the dispatch verdict.

## Completion bar

Per this repository's completion rule, "done" requires driving the SHIPPED
behaviour end-to-end in its real environment with live-exercise evidence
journaled on the item — not merely merged, CI-green, and accepted. The Installer
slice's adopter exercise is the worked example to follow.

## Closing the thread

When all four slots are filled, close `livespec-httc` and archive:

```bash
git mv plan/github-request-budget-discipline/ plan/archive/github-request-budget-discipline/
```

Do **NOT** archive before then: `plan/<topic>/` is active if and only if its epic
is open, and per the spec's own rule a concern is not adopted until all five slots
are filled. Request-budget-discipline is currently REGISTERED but not yet ADOPTED.

## Spec-change discipline, if any slice needs one

Every proposed change needs an independent READ-ONLY adversarial review by a
separately-spawned Fable-model agent before `/livespec:revise` accepts it. The
revise CLI enforces this mechanically: it requires a `ratification_review` mode
plus `ratification_evidence` carrying a sha256 `content_digest` over the proposal
bytes AND each resulting file's content. **Every edit after a review invalidates
that digest** — batch all fixes into one pass, then request a single
digest-bound verdict. Note `.livespec.jsonc` pins the reviewer model, and the CLI
requires `reviewer_identity` to equal `reviewer_model`.
