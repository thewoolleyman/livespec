---
topic: public-api-consumed-across-a-boundary
author: claude-opus-5-rop-railway-enforcement
created_at: 2026-07-29T04:30:44Z
spec_commitments:
  impl_followups:
    - id_hint: public-api-consumed-criterion-check
      description: |
        Implement the consumed-across-a-boundary criterion in `check-public-api-result-typed` (repo-local half): the check's universe becomes the repo's DECLARED public surface rather than raw `__all__` membership, and a name consumed across a boundary is in scope whether or not it appears in `__all__`. Red-Green-Replay, one slice per PR.
    - id_hint: public-api-fleet-consumption-conformance-row
      description: |
        Implement the CENTRAL half as a central-vantage conformance row that re-measures the fleet-wide import graph across all governed members and FAILS when a member's declared public surface omits a name another member actually consumes. Only this half can see a sibling's import; a repo-local check structurally cannot. This is the mechanism that would have caught `parse_manifest` BEFORE its conversion broke `livespec-orchestrator-beads-fabro`'s master.
---

## Proposal: Public API for the Result-return rule means CONSUMED ACROSS A BOUNDARY, measured fleet-wide

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The Result-return rule in §"ROP composition" scopes itself to "every public function", and `check-public-api-result-typed` implements public as "named in `__all__`". That premise is false at scale: measured in `livespec-dev-tooling`, 40 of 46 offenders were exported in `__all__` but consumed by no other module anywhere in the fleet. This proposal states the criterion the rule has always meant — a function is public API when it is CONSUMED ACROSS A BOUNDARY — defines consumption fleet-wide in four enumerated forms, and makes the criterion `__all__`-INDEPENDENT in the tightening direction so that removing a name from `__all__` is not an escape. It generalizes the existing `_`-prefix paragraph from a spelling to a substance.

### Motivation

Ratified spec v177 settled WHICH supervisors are exempt but left WHAT COUNTS AS PUBLIC unstated, so the check inherited `__all__` membership as a proxy. Two independent measurements show the proxy is wrong in both directions, and the second one cost a red sibling master. (1) In `livespec-dev-tooling`, 40 of 46 offenders are `__all__`-exported and consumed by nothing — the rule over-reaches, manufacturing `Result` types whose failure track would be uninhabited. (2) `parse_manifest` was converted to `Result` on the strength of a REPO-LOCAL reading that found no importer; `livespec-orchestrator-beads-fabro`'s `codex_yolo_gate.py` hook imports it, and the auto-merge bump fan-out delivered the change within minutes. Its master went RED (filed as `livespec-dev-tooling-dx8l`). A criterion that is right about 40 functions and wrong about the ones that cross repo boundaries is worse than none, because it is confidently wrong exactly where the blast radius is largest. Hence: fleet-wide scope is a REQUIREMENT of the criterion, not a refinement of it.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"ROP composition", REPLACE the paragraph beginning "**A function whose name carries a single leading underscore is NOT public for the purposes of this rule**" with the following. That paragraph is the NARROW SPELLING of this same defect (`__all__` membership is not sufficient to make a name public) and is preserved as clause (0) below rather than deleted — deleting it alongside its generalization is the obvious tidy and would discard the ratified `_`-prefix rule that `check-public-api-result-typed` already enforces.

---

**WHAT COUNTS AS PUBLIC FOR THIS RULE.** `__all__` membership alone does NOT make a name public. A top-level function is PUBLIC API for the purposes of the Result-return rule when, and only when, it is CONSUMED ACROSS A BOUNDARY. Consumption is measured FLEET-WIDE — across every governed repo, not only the declaring one — and has exactly these forms:

0. **A single leading underscore disqualifies outright.** A `_`-prefixed name is NOT public regardless of its presence in `__all__` or of any consumption below, per the private-helper definition in §"Typechecker rule set", which this rule adopts rather than restates. Consumers legitimately list private helpers in `__all__` to make them importable by their tests.
1. **Product import** — imported by NON-TEST first-party code, in the declaring repo across a module boundary, or in ANY governed sibling.
2. **Cross-repo test import** — imported by the TEST code of a DIFFERENT governed repo. A module whose product IS a distributed test harness has sibling test suites as its real consumers, and a change to its shape breaks their green gates exactly as a product import would.
3. **Process entry point** — reached as a process rather than by import: `python -m`, a console script, or a binary baked from the module.
4. **Declared distributed surface** — invoked by name from a live non-Python artifact the fleet ships: a hook body, a `justfile` recipe, a CI workflow step, or a plugin manifest.

A name consumed by NONE of these forms is not public API; it is a TEST-VISIBILITY EXPORT, and the rule does not reach it.

**A name imported only by the DECLARING repo's own tests is NOT public API, and that is correct rather than a blind spot.** Its test suite is not a consumer whose contract the railway exists to protect; it is the module's own scaffolding. Clause 2 draws the line precisely where it belongs — at the REPO boundary, not at the `tests/` boundary — so that a distributed harness does not escape through a rule aimed at scaffolding. Do not "fix" clause 1 by dropping its non-test qualifier; that would re-classify every test-visibility export as public and restore the over-reach this criterion removes.

**THE CRITERION IS `__all__`-INDEPENDENT IN THE TIGHTENING DIRECTION.** A function consumed by form 1, 2 or 4 is PUBLIC API whether or not it appears in `__all__`. Removing a name from `__all__` is therefore NOT an escape from the rule, and narrowing an `__all__` is legitimate only for names that no form of consumption reaches. This is stated as a requirement because the criterion's relaxing half is otherwise trivially gameable: under the `__all__` proxy, deleting one line silences the check completely.

**MEASURED EXPOSURE OF THE TIGHTENING HALF TODAY: ZERO, and it is recorded so the clause is not over-sold.** Across all eight siblings, no top-level function is consumed-but-undeclared; the 11 imported-but-undeclared names are all SUBMODULES, every one from test code. The clause is a guard against future gaming, not a correction of present state. It will not turn anything red on the day it lands.

**ENFORCEMENT IS SPLIT ACROSS TWO VANTAGES AND NEITHER HALF SUFFICES ALONE.** The REPO-LOCAL half — `check-public-api-result-typed` — enforces Result-typing over the declaring repo's own surface; it is hermetic and runs in a pre-commit gate. The CENTRAL half is a central-vantage conformance row that re-measures the fleet-wide consumption graph across all governed members and FAILS when a member's declared public surface omits a name another member actually consumes. **A repo-local check structurally CANNOT see a sibling's import**, so a criterion that claims fleet-wide scope while being enforced only locally would assert a guarantee nothing computes — the manufactured-confidence failure this rule set exists to remove. The central half is the mechanism that would have caught `parse_manifest` before its conversion landed.

**KNOWN BLIND SPOT, stated here rather than discovered later: the oracle is STATIC.** A name reached DYNAMICALLY — `getattr(module, name)`, `importlib`, dispatch by string key — is invisible to it, and one such case is already recorded (a test reaching a function as `module.<name>` after an `importlib` load). A consumer that reaches a symbol dynamically ACROSS a repo boundary MUST declare it; an undeclared dynamic reach is outside what any measurement here can see, and the criterion claims nothing about it.

**AND A CONSUMPTION MEASUREMENT FINDS THE IMPORT, NOT THE GUARD — the failure mode that paid for this criterion.** When `parse_manifest` moved to `Result`, the consuming hook's `if manifest is None` guard did not FAIL. Against a `Result` that test is permanently False, so the guard SILENTLY STOPPED BEING A GUARD, and control flowed on into `manifest.owner`, raising an uncaught `AttributeError`. The consequence direction was the bad one: an access-gating marker went STALE rather than failing closed, and fail-stale on an access gate is strictly worse than fail-closed. **A `None`-check does not survive a `Result` migration by breaking loudly; it survives by no longer checking anything.** Every consumer-side `None`-guard, falsy test, or `or`-default over a converted symbol has this shape latent in it. Therefore, before converting any public symbol: locate its consumers by the criterion above, then READ each consumption site's guard — finding the import is not finding the guard — and land the consumer's wiring FIRST, in the consuming repo, through its own green gates, per the consumer-wiring-before-the-change-that-assumes-it discipline. Wiring that tolerates BOTH shapes satisfies that discipline for every pin version simultaneously, so the dependency may then move in either direction without re-breaking.

---

**DOES THIS WEAKEN THE RULE OR MAKE AN EXISTING REALITY EXPRESSIBLE? BOTH, and the honest answer is recorded rather than the flattering half.**

- For the names it removes, it EXPRESSES an existing reality: those functions were never public API; `__all__` said they were. This is the same premise on which the `_`-prefix clause was already ratified.
- But it MATERIALLY SHRINKS ENFORCEMENT SCOPE, and that is a real reduction rather than a reclassification. Measured in `livespec-dev-tooling`: of 43 current offenders, the criterion removes 25 — leaving 8 public by product import, 1 public as a distributed test harness, and 9 `main()` supervisors that need a `supervisor_entry_files` declaration each. Anyone reading this as cost-free has read it wrong.
- The `__all__`-independent clause STRENGTHENS the rule, and the split enforcement strengthens it again by adding a vantage that can see across repos.
- NET: the rule's scope moves from "what a module DECLARES about itself" to "what the fleet ACTUALLY CONSUMES." The `dx8l` evidence is that the old criterion was wrong precisely where the blast radius was largest, and the new one is anchored to the thing the rule exists to protect.

**WHY NOT SIMPLY CONVERT EVERYTHING INSTEAD.** A `Result` on a total function has an UNINHABITED failure track. Wrapping such a function satisfies the letter of "every public function" and defeats its purpose: it manufactures ceremony at every call site, forces callers to unwrap a `Failure` that cannot occur, and sells the result as railway coverage. The rule exists to move REAL failure modes onto the railway, so its scope must be the functions that have consumers AND failures — not every name a module happens to export.
