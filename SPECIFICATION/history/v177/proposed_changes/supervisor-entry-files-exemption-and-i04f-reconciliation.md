---
topic: supervisor-entry-files-exemption-and-i04f-reconciliation
author: claude-opus-5
created_at: 2026-07-29T00:11:21Z
---

## Proposal: State the Result-return exemption set ONCE, exhaustively, and identically in both places

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The Result/IOResult return rule is stated TWICE with incompatible exemption sets — §"ROP composition" closes the set ("The rule exempts only such supervisors") while §"Typechecker rule set" opens it with "e.g." AND adds a member (`build_parser`). The two MUST be reconciled to one exhaustive set, resolved toward the CLOSED discipline: take §"Typechecker rule set"'s CONTENT and §"ROP composition"'s DISCIPLINE.

### Motivation

Filed as livespec-i04f and blocking `livespec-dev-tooling-8o8e`, the epic arming `check-public-api-result-typed`. An implementer cannot build to two contradictory clauses, and the enforcing check currently implements the §"Typechecker rule set" superset while §"ROP composition" says that superset is forbidden — so the check is either over- or under-enforcing depending on which sentence is read as authoritative. The `e.g.` is the sharper half of the defect: an open-ended list in a NORMATIVE exemption clause is the same ambiguity class this fleet has spent an entire epic removing from the role-key schema, where a value that meant "whatever the reader needs" silently disarmed six checks. An exemption list that a reader may extend by analogy is that defect in different clothes. Resolving toward the closed set is therefore not a tightening for its own sake; it is applying the discipline the project has already ratified elsewhere.

### Proposed Changes

Both statements of the rule MUST be reconciled so they express the SAME exemption set, and that set MUST be EXHAUSTIVE.

- §"ROP composition" (the architectural statement) and §"Typechecker rule set" (the tooling statement) MUST NOT state the exemption set differently. One of them SHOULD state the set in full and the other SHOULD cite it by section reference rather than restating it, so the two cannot drift apart again. Restating a normative set in two places is what produced this defect.
- The `e.g.` in §"Typechecker rule set" MUST be removed. An exemption list in a normative clause MUST be exhaustive; a reader MUST NOT extend it by analogy. Where the set genuinely needs a new member, that member MUST be added by amendment.
- `build_parser() -> ArgumentParser` in `commands/**.py` MUST be retained as a member of the reconciled set. It is genuinely a boundary factory, it is already implemented by the enforcing check, and dropping it would redden conforming code.
- The reconciled clause MUST retain the closing discipline of §"ROP composition" — that the rule exempts ONLY the enumerated supervisors — so the set reads as closed on its face.

The reconciled exemption set is: `main() -> int` in `commands/*.py` and in `doctor/run_static.py`; `build_parser() -> ArgumentParser` in `commands/**.py`; any function whose return annotation is `None`; and any function in a file the consumer DECLARES as a supervisor entry point (see the companion proposal in this change).

## Proposal: Admit a declared supervisor entry file to the exemption set, through the existing supervisor_entry_files role key

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The supervisor exemption is granted to a LOCATION (`commands/*.py`, `doctor/run_static.py`), which a flat-layout consumer has no way to satisfy. The exemption set MUST additionally admit a file the consumer has DECLARED in the `supervisor_entry_files` role key — the same category of function, admitted through a per-file declaration rather than a directory glob.

### Motivation

Measured in `livespec-dev-tooling`, which is the enforcement suite itself: 12 of its public functions are `main() -> int` process supervisors, and NONE is exempt, because the repo has a flat package layout and declares no commands tree. Its supervisors sit at `livespec_dev_tooling/*.py` and `livespec_dev_tooling/checks/*.py`. The enforcing check is implementing the spec FAITHFULLY — its own docstring records that the path scoping is "load-bearing, not decoration" — so the gap is in the rule's scoping, not in the check.

`supervisor_entry_files` already exists for exactly this concept, at exactly this granularity, and is already consumed by FOUR checks: `check-no-except-outside-io` (the `main()` direct-child broad-catch boundary), `check-no-write-direct`, `check-supervisor-discipline`, and `check-partition-completeness`. `check-public-api-result-typed` is the ONLY one of the five consumers of the supervisor concept that never asks the consumer. So today the Result-return check and the catch-position check DISAGREE about what a supervisor is, while reading the same repo.

The alternative — telling flat-layout consumers to declare a `commands_trees` — is the WRONG instrument: in `livespec-dev-tooling` the supervisors are spread across `checks/`, so any tree wide enough to cover them would exempt that entire tree. File-level is the narrow instrument and it already ships.

### Proposed Changes

The Result/IOResult return-annotation rule's exemption set MUST additionally admit: a public function in a file the consumer declares in the `supervisor_entry_files` role key of its `[tool.livespec_dev_tooling]` block.

**This MUST NOT be read as widening the exemption in KIND.** It admits the SAME category the existing clause admits — a supervisor at a deliberate side-effect boundary — through a different mechanism. It creates NO new class of exempt function. A file declared in `supervisor_entry_files` is already, by that declaration, asserted to be a process entry artifact, and four checks already act on that assertion.

**The shape is STRICTER than the location scoping it complements, and that is the argument for it.** A `commands/*.py` glob exempts every file in that directory, present and future, automatically and silently — a file added to `commands/` tomorrow inherits the exemption with nobody deciding anything. `supervisor_entry_files` names each file individually, and the fleet's own convention requires a written reason per entry. A consumer that has NOT spoken gets NOTHING. Declared-and-greppable is the discipline this project has repeatedly chosen over inferred-and-silent.

**The cost MUST be stated rather than left implicit.** This is a real expansion of WHO can claim the exemption: consumers with a flat package layout can now express a supervisor exemption they currently cannot express at all. That is the intent — a flat-layout repo has process entry points exactly as a layered one does — but it means the count of exempt functions fleet-wide will rise, and each new claim MUST carry its own declaration and reason rather than arriving by inheritance from a directory name.

**The declaration MUST NOT be self-certifying beyond its stated scope.** Declaring a file in `supervisor_entry_files` exempts its supervisor entry points from the return-annotation rule; it MUST NOT be read as exempting every function in that file from the railway. A helper in a declared supervisor file that is neither a `main()`-shaped entry point nor annotated `None` remains subject to the rule.

## Proposal: A single-leading-underscore name is not public API for the return-annotation rule

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The return-annotation rule binds "every public function", and §"Typechecker rule set" already defines a private helper as "single-leading-underscore prefix OR not in `__all__`". That definition MUST be made explicitly load-bearing for the return-annotation rule, so a `_`-prefixed name listed in `__all__` is NOT subject to it.

### Motivation

The definition already exists in the spec, one paragraph above the second statement of the rule, and it treats a leading underscore as SUFFICIENT to mark a helper private — independent of `__all__` membership. But the return-annotation clause says only "every public function", and the enforcing check resolved that to "every name in `__all__`", which is a different rule.

Measured consequence in `livespec-dev-tooling`: `checks/check_mutation.py` declares `__all__` containing SIX `_`-prefixed helpers and NOT `main`. There `__all__` is a test-visibility declaration, not a public-API one, and the check reported six private helpers as unrailed public API. That is a false positive, and the spec already contains the sentence that resolves it.

The tension SHOULD be acknowledged rather than papered over: `__all__` is Python's explicit export declaration, so on a strict reading a name in it is public by declaration. This proposal resolves the tension toward the underscore because the alternative reports a helper the author marked private as public API, and because the spec's own definition of "private helper" already says so.

### Proposed Changes

The return-annotation rule MUST state that a function whose name carries a single leading underscore is NOT public for the purposes of the rule, REGARDLESS of its presence in `__all__`.

- The rule MUST cite the existing private-helper definition in §"Typechecker rule set" rather than introducing a second, independent definition of "public". Two definitions of the same term is the defect the first proposal in this change exists to fix, and it MUST NOT be reintroduced here.
- The clause SHOULD record that `__all__` membership alone is NOT sufficient to make a name public for this rule, because consumers legitimately list private helpers in `__all__` to make them importable by their tests.

No scenario accompanies these three proposals, and the reason is stated so the absence does not read as an oversight: `scenarios.md` in this repo specifies the livespec TOOL's own user-observable operations (seed, propose-change, revise, doctor). The Python style and ROP rules in `non-functional-requirements.md` are contributor-facing constraints on livespec's own source per the §"Boundary" litmus, not user-observable behavior of the tool, and no clause in that section carries a scenario link today.
