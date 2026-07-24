# DRAFT — livespec-dev-tooling contracts.md severity-policy amendment (Slice 3, livespec-dh9r)

**Status: the CODE HAS LANDED; this spec amendment is the remaining half.**
Slice 3 merged as `livespec-dev-tooling` PR #590 — the sealed escalation
commit `9b3ee48` plus the context-scoping commit `d689793`. This text now
feeds `/livespec:propose-change` in the `livespec-dev-tooling` tenant, then
the independent Fable review to NO-BLOCKERS, then `/livespec:revise`.

**⚠ This draft was written against the ORIGINAL global-error design and has
been revised for the maintainer's 2026-07-24 CONTEXT-SCOPED ruling.** If any
sentence below still reads as an unconditional "persisting gap is an error",
it is stale — the escalation is conditional on the evaluating context.

Proposed topic (file stem): `pin-currency-severity-policy`

## Intent

Document, as contract, the pin-currency obligation rows and their severity
policy — including the context-scoped persisting-gap escalation that is
`livespec-dh9r`'s payload — so the enforcing code
(`livespec_dev_tooling/fleet/_rows_pin_currency.py`,
`_rows_files.py::_freshness_outcome`) and the spec agree.

## Replacement target 1 (verbatim FIND, contracts.md line ~343)

FIND (the clause fragment):

    has its pin freshness monitored centrally — at *warning* severity — by the `dev-tooling-pin` row's staleness leg rather than auto-bumped.

REPLACE WITH:

    has its pin freshness monitored centrally by the `dev-tooling-pin` row's staleness leg rather than auto-bumped, at the severity the §"Pin-currency severity policy" section defines.

(Clause-lockstep note: re-derive the surrounding sentence at draft-final
time — this section was reworded at v030 and the vantage-model
ratifications are actively editing nearby text.)

## Addition (new `## ` section — heading-coverage co-edit REQUIRED)

New section `## Pin-currency severity policy` (placement: after the
fleet-membership obligation-row enumeration):

    ## Pin-currency severity policy

    Central pin-currency evaluation covers all four fleet pin formats:
    the `pyproject.toml` `[tool.uv.sources]` dev-tooling pin
    (`dev-tooling-pin` row), `.livespec.jsonc` `compat.pinned`
    (`compat-pin-currency`), GitHub Actions `uses:` refs
    (`uses-pin-currency`), and the Fabro sandbox image tag
    (`fabro-pin-currency`). Version comparison is
    prefix-agnostic (`pin_staleness.denotes_same_release`).

    Severity is a two-tier policy, and the upper tier is CONTEXT-SCOPED:

    - **Plain staleness is a WARNING.** A pin behind the latest release
      with no open bump PR for that release is normal operation — the
      minutes-long window between a release and its bump PR merging.
      Warning severity moves no exit code and never gates the release
      fan-out.
    - **A PERSISTING gap is an ERROR only where a per-member remedy
      exists.** A pin that is stale AND whose bump PR for the latest
      release is already open means the self-heal mechanism fired and
      could not land; the open PR is the durable, stateless record of
      that failure. That finding escalates to error ONLY when it is
      evaluated in a context that can act on it PER MEMBER — the release
      fan-out preflight, whose per-member verdicts the dispatch-matrix
      filter consumes to exclude exactly the offending member. In any
      other context — notably an ordinary per-PR CI run, which can only
      pass or fail as a whole — the same condition is reported at
      WARNING severity.
    - **The diagnostic does not change with the context.** Both
      severities emit the identical message, naming the member, the pin
      format, and the open bump PR number. Scoping lowers the severity;
      it never suppresses, abbreviates, or silences the finding.
    - **A can't-read never escalates.** An unreadable PR list, release
      list, or tree keeps the row at its lower severity or skips it (a
      can't-read is not a violation).

    The scoping is a property of the EVALUATING CONTEXT, not a
    configurable severity. There is no lever, environment variable, or
    per-member exemption that changes a persisting gap's severity within
    a given context.

    An error finding excludes the member from the release-dispatch
    matrix via the fan-out preflight's per-member filter (the
    §"reusable-release-dispatch.yml" contract) — it never halts
    dispatch to conformant members.

## Why the escalation is context-scoped (narration for the proposal)

State this rationale in the proposal body; it is the load-bearing reason the
upper tier is conditional rather than global, and a reviewer who does not
have it will read the scoping as a weakening.

`check-fleet-conformance` is evaluated in exactly two contexts, and only one
of them can act on a per-member finding:

1. **The release fan-out preflight** invokes it to produce per-member
   verdicts, which the `livespec-f73t` filter consumes. A member's error
   finding excludes that member loudly and propagation continues to every
   conformant sibling. The finding is *actionable per member here*.
2. **`livespec-dev-tooling`'s own per-PR CI** — measured 2026-07-24, the
   only member repo running the check in CI (zero occurrences in the other
   eight members' `ci.yml`). This context has no per-member granularity: it
   passes or fails as a whole.

Promoted globally, any one member's persisting gap therefore reds
`livespec-dev-tooling`'s entire PR surface — including the PRs that would
repair the gap — while the offending member is typically owned by a
different track. That is the enforcement-before-adoption deadlock
`.ai/ci-gate-discipline.md` forbids resolving with a lever or a severity
downgrade, so the resolution is to scope the severity by context instead.

**This is not hypothetical.** It fired on the change's first live run: PR
#590's own CI produced 10 persisting-gap errors and blocked the PR that
introduced them. Several were transient (cleared by ordinary merges), the
`livespec-driver-claude` / `livespec-driver-codex` pair was a genuine
carrier-propagation defect (`livespec-dev-tooling-lmv2`), and
`livespec-overseer`'s is owned by `plan/overseer-productization/` with no
near-term clearance.

## Verification evidence (cite in the proposal; do not re-derive from memory)

- The scoping is live and non-vacuous: PR #590's post-amendment CI run
  `30059932539` is SUCCESS **while still reporting** the `livespec-overseer`
  persisting gap — same wording, `"level": "warning"` — with `fleet
  conformance passed`, `members: 9`, `blind_rows: 0`. The green is
  attributable to the scoping, not to the gap disappearing.
- The per-member filter was observed working in a real fan-out BEFORE the
  escalation landed: v0.53.2 run `30028730379`, verdict artifact emitted and
  consumed, `excluded=0 kept=8`, 8/8 dispatched.

## Ordering constraint — DISCHARGED, restate as history

Landing this severity promotion before the per-member preflight filter was
deployed AND exercised would have recreated the v0.20.0 fleet-wide stall
(one member's persisting gap halting all propagation). The filter shipped in
`livespec-dev-tooling` PR #580 and was observed working in the real v0.53.2
fan-out run cited above before the escalation merged, so the ordering
`.ai/ci-gate-discipline.md` codifies was honored. Keep the constraint in the
narration as the reason for the sequence, not as an open precondition.

## Co-edits

- `tests/heading-coverage.json` — entry for the new `## Pin-currency
  severity policy` heading (TODO + reason pattern).
- Drift sweep at draft-final time: any other contracts/spec sentence
  asserting the staleness leg is "warning severity" or warning-only
  (line ~343 found so far; re-grep at filing time — the vantage-model
  stream is actively editing this file). **Also sweep for any sentence
  asserting the persisting gap is unconditionally an error**, which the
  context-scoped ruling now contradicts.
