# Handoff — github-request-budget-discipline

**Thread anchor (ledger epic):** `livespec-httc`, in THIS repository's tenant
(`livespec`). This handoff records no status of its own; read status from the
ledger.

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

## Next action

**File the Contract slot as a spec amendment.** This is the thread's blocking
planning action and it is spec-side, not implementation.

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
