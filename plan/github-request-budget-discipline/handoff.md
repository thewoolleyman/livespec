# Handoff — github-request-budget-discipline

**Ledger anchor:** epic `livespec-httc`

This handoff records no status of its own; read status from the ledger in THIS
repository's tenant (`livespec`).

## Read-first chain

Read these, in order, before acting. Nothing else is required.

1. `plan/github-request-budget-discipline/research/01-design.md` — the full design
   record: the incident, the verified GitHub limits, the propagation-surface
   analysis, and the Conformance-Pattern reframing. **This is the only document
   you need to understand the thread.**
2. `SPECIFICATION/non-functional-requirements.md` §"Conformance Pattern" — the
   five-slot anatomy the next action fills.
3. `.ai/no-circular-dependency.md` — governs where any cross-repo check may live.

## Compose current status first

Run the read-only status surface before deciding anything; do not trust any
status written into a planning artifact:

```bash
/usr/local/bin/with-livespec-env.sh -- bd show livespec-httc
```

The epic's notes carry the filed slice ids and the scope corrections. The three
implementation slices live in OTHER tenants and are cited in prose because beads
cannot resolve a foreign-tenant id (`bd-ib-dvmh`):

- `livespec-runtime-lzq` — `livespec-runtime` tenant — the Mechanism slot.
- `livespec-driver-claude-6xj` — `livespec-driver-claude` tenant — the Installer slot.
- `livespec-dev-tooling-t2q4` — `livespec-dev-tooling` tenant — the Verifier slot.

To read one, run `bd show <id>` from inside that repository's checkout under the
same credential wrapper.

## Progress as of 2026-08-05

Read status from the ledger, not from this list; these are landed facts, not
open state.

- **Contract slot — DONE.** Ratified as `v195` (livespec PR #2030). The registry
  now carries **Request-budget-discipline**, and `### Request-budget discipline`
  fills all five slots. Two separately-spawned read-only Fable reviewers each
  returned NO BLOCKERS bound to the exact ratified bytes; five blockers were
  found and fixed first.
- **Installer slot — DONE and live-exercised.** `livespec-driver-claude-6xj`
  merged via factory dispatch (PR #423, `merge_sha 776827d6`), released as
  `v0.5.0`. The guard denies a poll loop and a bulk-mutation loop, allows an
  ordinary read, and fails open on malformed input. Exercised through the
  adopter `resume`'s own resolved plugin path with zero per-repo wiring —
  proving the reach property the per-repo settings channel lacks.
- **Mechanism slot — BLOCKED.** `livespec-runtime-lzq` (slice A) and
  `livespec-runtime-g2s` (slice B) are blocked behind `livespec-runtime-s8q`, a
  P0: that repo's master is red from a DIFFERENT epic's enforcement-before-
  adoption, and unblocking it requires a cross-repo breaking ROP migration
  belonging to `livespec-y2lkf4`. Maintainer decided 2026-08-04 not to pull that
  into this thread.
- **Verifier slot — BLOCKED** on the Mechanism. `livespec-dev-tooling-t2q4` is
  deliberately NOT routed to `ready`: its real dependency is cross-tenant, which
  beads cannot express as an edge, so routing it would let the factory dispatch
  it before the client it checks for exists.

## Next action

**Unblock `livespec-runtime` by resolving `livespec-runtime-s8q`**, or accept
that this thread stays open until `livespec-y2lkf4` does it. Nothing else in
this thread can proceed: both remaining slots sit behind that P0.

The thread MUST NOT be archived yet — `plan/<topic>/` is active if and only if
its epic is open, and `livespec-httc` has two unfilled slots.

## Superseded next action (kept for context)

**File the Contract slot as a spec amendment.** COMPLETED — ratified as v195.

Per `SPECIFICATION/non-functional-requirements.md` §"Conformance Pattern", "a
concern is not adopted until all five slots are filled", and this concern's
Contract slot is empty — no document states the normative invariant. Four slots
have filed work; the one that makes them add up to an adopted concern does not
exist yet. Until it does, the three slices are unanchored machinery.

Drive it with:

```
/livespec:propose-change
```

The amendment targets `SPECIFICATION/non-functional-requirements.md` and should
state, as a `baseline` Conformance-Pattern concern binding the livespec fleet and
its adopters:

- Every GitHub API call originating from governed automation routes through one
  canonical client (the Mechanism), never an ad-hoc direct call.
- Polling paths use conditional requests; a `304` costs no primary budget.
- Mutations are paced to respect the secondary limit (5 points each against 900
  points/minute) and are never issued concurrently.
- A rate-limited `403` is UNMEASURABLE and MUST NOT collapse to an empty success.
- The five slots are named explicitly, following the worked example in
  §"Conformance Pattern" and the precedent of ledger item `livespec-gcp2`.

Two drafting constraints, both derived in the design record:

- The Verifier slot must place any cross-repo check in the existing
  fleet-conformance sweep (which already iterates fleet members plus opt-in
  adopters and carries `posture`-based exemptions), NOT in a new check inside
  `livespec-dev-tooling` reading downstream — that would be a circular dependency
  per `.ai/no-circular-dependency.md`.
- Reuse the Conformance Pattern spine; do not introduce a parallel mechanism. The
  spec forbids forking it.

Before driving `/livespec:revise` to accept the resulting proposal, an independent
READ-ONLY adversarial review by a separately-spawned Fable-model agent is
REQUIRED, per the repository's standing ratification rule. A NO-BLOCKERS verdict is
a precondition; it is never self-waived.

If the H2 heading set of any spec file changes, co-edit
`tests/heading-coverage.json` in the same `resulting_files[]` payload.

## After the Contract lands — implementation routing

The three slices are implemented **factory-side**, never inline in a planning
session. Dispatch each through the factory route:

```
/livespec-orchestrator-beads-fabro:drive --action impl:<work-item-id>
```

or leave them for the Dispatcher to drain from `ready`. Do NOT use the in-session
Red→Green `implement` operation for these — none is recorded as
factory-ineligible.

Ordering constraint, from ledger item `livespec-j49m` (this tenant): its
disposition is **MEASURE BEFORE MITIGATING**. `livespec-runtime-lzq` must land its
measurement and per-caller attribution half FIRST; the mitigation behaviours ride
on the same chokepoint afterwards. `livespec-dev-tooling-t2q4` cannot land before
`livespec-runtime-lzq`, because its check has no sanctioned path to point callers
at until the client exists.

## Completion bar

Per this repository's completion rule, "done" requires driving the SHIPPED
behaviour end-to-end in its real environment, with live-exercise evidence
journaled on the item — not merely merged, CI-green, and accepted. For
`livespec-driver-claude-6xj` specifically that means exercising the guard in a
real ADOPTER repository (`homelab`, `openbrain`, or `resume`) after a plugin
release, because adopter reach is the entire premise of that slice and the
same-repo happy path cannot demonstrate it.
