---
proposal: driver-fleet-route-guard.md
decision: accept
revised_at: 2026-11-13T04:18:00Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-fable-5-2
---

## Decision and Rationale

Accepted as filed under delegated revise authority, in the revise slot the fleet coordinator assigned to the homelab-k8s-worker-nodes plan, which authored this proposal (livespec#3191). The coordinator graded the proposal text PASS before it merged. All five changes are applied word for word from the proposal: four clause changes in contracts.md under "Driver-shipped hooks" (the opening paragraph's bundle sentence, the runtime-specific hooks enumeration in the cross-Driver single-sourcing paragraph, the pi footgun guard's one-extension sentence, and three inserted paragraphs stating the Claude fleet route guard and its required Codex and pi ports) and one new scenarios.md section, "## A wrong SSH route to a tailnet machine is refused with the documented one", placed after "## A hand change to a fleet host is refused outside the committed apply". Every quoted replace target matched the live file exactly once. The tests/heading-coverage.json co-edit adds one TODO row for the new heading, owned by livespec-lhmjbd, which owes the integration-tier test; tests/heading-coverage-debt.json is regenerated in the same commit. The independent sonnet review compared the staged bytes with the proposal, recomputed the content digest, and reported no blockers. Its nits are not acted on: (1) the debt register is a generated file and is staged in the revise commit rather than carried in resulting_files; (2) the configured ratification reviewer model for this repository is sonnet. Follow-on work: livespec-driver-claude-bmacrp (the Claude guard), livespec-driver-codex-74dnlu (the Codex port), livespec-driver-pi-rjf7l5 (the pi port) and livespec-lhmjbd (the scenario test). The other pending proposals are left in place by this single-topic pass.

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-13T04:17:02Z
verdict: NO BLOCKERS
proposal_stem: driver-fleet-route-guard
content_digest: 2975b7be0eb663fd1d4fa37f5b60718134db1f4d0bbc752291444ede030fe327
