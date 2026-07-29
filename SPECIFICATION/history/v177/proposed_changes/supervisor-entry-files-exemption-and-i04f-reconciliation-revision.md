---
proposal: supervisor-entry-files-exemption-and-i04f-reconciliation.md
decision: accept
revised_at: 2026-07-29T00:13:21Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

ACCEPTED, all three proposals, under the maintainer ruling of 2026-07-29 delegating the accept/reject decision at revise, extended to this repo by the supervising thread after verifying that the rule being amended is this epic's own subject matter and that the grant was not repo-scoped.

PROPOSAL 1 -- i04f reconciled, toward the CLOSED set. The rule was stated twice with incompatible exemption sets: 'ROP composition' closed it ('The rule exempts only such supervisors'), 'Typechecker rule set' opened it with 'e.g.' AND added build_parser. Resolved by taking the second's CONTENT (build_parser is genuinely a boundary factory, is already implemented by the enforcing check, and dropping it would redden conforming code) with the first's DISCIPLINE (exhaustive, 'exempts only'). The 'e.g.' is the sharper half: an open-ended list in a NORMATIVE exemption clause is the same ambiguity class this fleet spent an epic removing from the role-key schema, where a value meaning 'whatever the reader needs' silently disarmed six checks. The set is now stated ONCE, in 'ROP composition', and 'Typechecker rule set' cites it by reference rather than restating it -- because restating a normative set in two places is what produced the defect, and two copies would drift again.

PROPOSAL 2 -- supervisor_entry_files admitted as member 4. Measured in livespec-dev-tooling, the enforcement suite itself: 12 public functions are main() -> int process supervisors and NONE is exempt, because the repo is flat-layout and declares no commands tree. The enforcing check is implementing the spec FAITHFULLY -- its own docstring records the path scoping as 'load-bearing, not decoration' -- so the gap was in the rule's scoping, not the check. supervisor_entry_files already exists at exactly this granularity and is already consumed by FOUR checks; public_api_result_typed was the ONLY one of five consumers of the supervisor concept that never asked the consumer, so the Result-return check and the catch-position check disagreed about what a supervisor is while reading the same repo.

Three things are stated in the ratified text rather than left implicit, because each is easy to lose in a later edit: member 4 admits the SAME category through a different mechanism and creates NO new class of exempt function; a per-file declaration is STRICTER than a directory glob, which exempts every present and future file with nobody deciding anything; and the COST is real -- flat-layout consumers gain an exemption they cannot express today, so the fleet-wide count of exempt functions will rise, and each claim must carry its own written reason. Member 4 is also explicitly BOUNDED: it exempts supervisor entry points in a declared file, not every function in it.

PROPOSAL 3 -- the underscore rule. This is the smallest change and the best supported: 'Typechecker rule set' ALREADY defines a private helper as 'single-leading-underscore prefix OR not in __all__', one paragraph above the second statement of the rule. Making that load-bearing for the return rule resolves a measured false positive -- check_mutation.py declares __all__ with SIX _-prefixed helpers and not main, so __all__ there is a test-visibility declaration. The rule CITES the existing definition rather than introducing a second one, since two definitions of one term is precisely what proposal 1 exists to fix.

NO SCENARIO ACCOMPANIES THIS, and the reason is recorded so the absence does not read as an oversight: scenarios.md in this repo specifies the livespec TOOL's own user-observable operations (seed, propose-change, revise, doctor). These are contributor-facing constraints on livespec's own source per the Boundary litmus, and no clause in non-functional-requirements.md carries a scenario link today.

TWO PENDING PROPOSALS BY OTHER AUTHORS ARE DELIBERATELY LEFT PENDING -- github-app-request-budget (claude-opus-5, 2026-07-28) and owned-heading-coverage-todos (claude-fable-5, 2026-07-04). The revise validation is one-directional: it rejects a decision naming a nonexistent topic, and does NOT require every pending file to be decided. Judging another session's in-flight spec content is not this thread's to do, and this repo's own AGENTS.md forbids the cross-session equivalent for branches.

## Resulting Changes

- non-functional-requirements.md
