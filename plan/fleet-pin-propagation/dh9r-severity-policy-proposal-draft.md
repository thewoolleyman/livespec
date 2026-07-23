# DRAFT — livespec-dev-tooling contracts.md severity-policy amendment (Slice 3, livespec-dh9r)

**Status: DRAFT ONLY, per supervisor ruling 2026-07-23 ("prep now, land
later"). NOT filed into `SPECIFICATION/proposed_changes/`; no
`propose-change` run. When Slice 3 is cleared to land, this text feeds
`/livespec:propose-change` in the `livespec-dev-tooling` tenant, then the
independent Fable review, then `/livespec:revise` — the code will already
be on a branch, so the ratification and the merge sequence per
`.ai/ci-gate-discipline.md` (spec + code land together; the error
promotion must never precede the deployed filter).**

Proposed topic (file stem): `pin-currency-severity-policy`

## Intent

Document, as contract, the pin-currency obligation rows and their
severity policy — including the persisting-gap escalation that is
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

    Severity is a two-tier policy:

    - **Plain staleness is a WARNING.** A pin behind the latest release
      with no open bump PR for that release is normal operation — the
      minutes-long window between a release and its bump PR merging.
      Warning severity moves no exit code and never gates the release
      fan-out.
    - **A PERSISTING gap is an ERROR.** A pin that is stale AND whose
      bump PR for the latest release is already open means the
      self-heal mechanism fired and could not land; the open PR is the
      durable, stateless record of that failure. The error finding
      names the member, the pin format, and the open bump PR number.
    - **A can't-read never escalates.** An unreadable PR list, release
      list, or tree keeps the row at its lower severity or skips it (a
      can't-read is not a violation).

    An error finding excludes the member from the release-dispatch
    matrix via the fan-out preflight's per-member filter (the
    §"reusable-release-dispatch.yml" contract) — it never halts
    dispatch to conformant members.

## Ordering constraint to restate in the proposal narration

Landing this severity promotion before the per-member preflight filter
is deployed AND exercised recreates the v0.20.0 fleet-wide stall (one
member's persisting gap would halt all propagation). The filter shipped
in livespec-dev-tooling PR #580 and must be observed working in a real
fan-out run before the accept; `.ai/ci-gate-discipline.md` codifies the
ordering.

## Co-edits

- `tests/heading-coverage.json` — entry for the new `## Pin-currency
  severity policy` heading (TODO + reason pattern).
- Drift sweep at draft-final time: any other contracts/spec sentence
  asserting the staleness leg is "warning severity" or warning-only
  (line ~343 found so far; re-grep at filing time — the vantage-model
  stream is actively editing this file).
