---
proposal: hand-built-class-obligation-inventory.md
decision: modify
revised_at: 2026-08-23T23:43:53Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as modified. The proposal names, in the Fleet membership contract, the committed-file obligations that today reach a member only as a side effect of copier-template generation, so a class with no template (hand-built by copying a donor sibling) is checked against a maintained inventory rather than one sibling's omissions; it adds no asserted conformance row, so no member goes red and the New-obligation discipline rule is extended with the documented-but-unarmed case. Both edit anchors exist verbatim exactly once on master; no H2 heading changes, so no tests/heading-coverage.json co-edit. Independent read-only Fable-model review (auto-spawn) on the exact final bytes: NO BLOCKERS; design-record fidelity confirmed against plan/archive/bootstrap-pi-driver/research/initial-research.md and livespec-dev-tooling TEMPLATE_BORN_CLASSES (impl-plugin only); reviewer noted the ratified MUST binds every non-template-born class, not only driver-plugin, and a soft pre-existing tension with contracts.md's 'optional overflow' wording, both non-blocking. Delegated decision under spec_governance.revise_decision_mode=delegated; no design-record contradiction, no drift-origin floor. Work-item livespec-icfycf carries the implementation follow-through.

## Modifications

Dropped the clause ', and two retrofits are already known to be outstanding at the time of writing — `livespec-driver-codex` carries no `.ai/` tree, and `livespec-driver-pi` has no `CI_RUNNER_LABELS` repo variable set' from the second appended paragraph, so it ends at 'Arming a row before its retrofit lands is what that rule forbids.' Reason: it is a claim that expires at ratification and an unanchored negative claim about sibling repos (spec-proposal-review classes 1 and 2), it is tracking rather than contract, and the reviewer found the CI_RUNNER_LABELS half already false (variable set 2026-08-20). Retrofit facts stay in the ledger. All other text applied verbatim; the two appended paragraphs are placed as separate bold-led paragraphs directly after the Obligations per repo class paragraph, matching document style.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-23T23:42:37Z
verdict: NO BLOCKERS
proposal_stem: hand-built-class-obligation-inventory
content_digest: 42e937626aba3d2565140339a041f4f658fbcca501d686c2ed3f9059588314fe
