---
topic: v178-tightening-half-exposure-was-not-zero
author: claude-opus-5
created_at: 2026-07-29T13:08:07Z
---

## Proposal: v178's "MEASURED EXPOSURE OF THE TIGHTENING HALF: ZERO" is FALSE and MUST be corrected

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

§"ROP composition" records, as a ratified measurement:

> **MEASURED EXPOSURE OF THE TIGHTENING HALF AT RATIFICATION: ZERO, and it is recorded so the
> clause is not over-sold.** Across all eight `livespec-dev-tooling` siblings, no top-level
> function was consumed-but-undeclared; the 11 imported-but-undeclared names were all
> SUBMODULES, every one from test code. The clause is a guard against future gaming, not a
> correction of present state, and it turned nothing red on the day it landed.

**That is false.** The tightening half was IMPLEMENTED on 2026-07-29
(`livespec-dev-tooling-721o`, PR #861 → `0788e93c`, released `v1.3.0`) and immediately
reached **three** top-level functions in `livespec-dev-tooling` alone — each imported by
another first-party module, each absent from any `__all__`, and therefore invisible to the
`__all__`-membership proxy the criterion replaced:

| function | consumed by |
|---|---|
| `livespec_dev_tooling/fleet/fleet_conformance.py:187 fetch_manifest` | `fleet/wire_fleet_member.py`, `fleet/fleet_conformance_admin.py` |
| `livespec_dev_tooling/fleet/fleet_conformance.py:152 holds_app_class_credential` | `fleet/fleet_conformance_admin.py` |
| `livespec_dev_tooling/cross_repo/pin_autodiscovery.py:126 discover` | `fleet/_rows_pin_currency.py` |

The paragraph MUST be replaced with the measured result, naming the count, naming
`fetch_manifest` as reaching the NETWORK, and stating that the clause is a correction of
present state rather than only a guard against future gaming.

### Motivation

**A ratified claim contradicted by measurement is the defect class this rule set exists to
remove, and this instance is in text this rule set ratified about itself.** §"ROP composition"
already carries the general form of the lesson — a criterion that "reads as enforced and is
not" — and the same section now carries a measurement that reads as measured and was not.

**The paragraph was not a mis-measurement; it was a measurement of the wrong thing.** Nobody
had implemented the tightening half when it was written, so what was actually measured was the
set of imported-but-undeclared names visible to a probe built around the OLD proxy. The
correction MUST NOT therefore be softened to "approximately zero", and MUST NOT be scoped to
"true at ratification time, superseded since". It was wrong when written, and the reason it was
wrong — an unimplemented clause cannot have its exposure measured — is the part a later reader
needs, because that reasoning generalizes to every future clause ratified ahead of its
mechanization.

**`fetch_manifest` makes the error consequential rather than cosmetic.** It performs a network
fetch of the fleet manifest. Under v179 member 1 it is disqualified from the no-expected-
failure-mode exemption by clause (c) — an I/O boundary call — so it is a CONVERSION candidate,
not an exemption candidate. The paragraph's reassurance that the clause "turned nothing red on
the day it landed" therefore understates the clause's reach in exactly the direction that
matters: the tightening half found a public, network-reaching, unrailed function that the
criterion it replaced could not see.

**And the reassurance is load-bearing for other repos' planning.** Every fan-out estimate for
the remaining governed repos was computed on the assumption that v178 only ever REMOVES
functions from scope. It also ADDS them. A sibling can come out HIGHER than its pre-v178
figure, and no sibling has been measured since the tightening half existed. A ratified
paragraph saying the tightening half touches nothing is the specific sentence that would let a
planner skip that re-measurement.

### Proposed Changes

The paragraph beginning **"MEASURED EXPOSURE OF THE TIGHTENING HALF AT RATIFICATION: ZERO"**
MUST be replaced. The replacement MUST state all of the following:

- **The measured exposure is NOT zero.** The tightening half, once implemented, reached THREE
  top-level functions in `livespec-dev-tooling` — `fetch_manifest`,
  `holds_app_class_credential` and `discover` — each consumed by another first-party module and
  named in no `__all__`.
- **The earlier figure was wrong when written, and MUST be recorded as wrong rather than as
  superseded.** The reason MUST be stated: the clause had not been implemented, so what was
  measured was what the OLD `__all__`-membership proxy could see, which is precisely the set
  the tightening half exists to look past. **A clause's exposure cannot be measured before the
  clause is mechanized**, and a measurement offered in its place is a prediction wearing a
  measurement's clothes.
- **`fetch_manifest` reaches the NETWORK**, and is therefore a CONVERSION candidate under v179
  member 1 clause (c), not an exemption candidate. The tightening half is a correction of
  PRESENT STATE, not only a guard against future gaming.
- **Fan-out counts for every other governed repo are now unknown in BOTH directions.** Prior
  estimates assumed v178 only removes; it also adds, so a repo may measure HIGHER than its
  pre-v178 figure. Any figure quoted without a post-v178 re-measurement MUST be treated as
  stale.

The corrected paragraph MUST NOT retain the sentence "The clause is a guard against future
gaming, not a correction of present state" in any form, and MUST NOT be reduced to a hedge such
as "exposure may be non-zero in some repos". The specific measured number, the named functions,
and the network-reaching detail are what make the correction checkable by the next reader.

The `__all__`-independent tightening clause ITSELF is NOT changed by this proposal. It was
right; only the paragraph estimating its blast radius was wrong, and the two MUST NOT be
conflated — a reader who takes this correction as evidence against the clause has taken it
exactly backwards, since the clause found a real unrailed public function on its first run.
