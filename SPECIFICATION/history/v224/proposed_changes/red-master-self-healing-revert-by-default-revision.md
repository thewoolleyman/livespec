---
proposal: red-master-self-healing-revert-by-default.md
decision: modify
revised_at: 2026-10-15T11:43:14Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

MODIFY. Ratifies red-master self-healing for the fleet: a deterministic, LLM-free master-health reconciler reverts the culprit merge by default, and a mechanical fix-forward claim holds the revert only while the fix makes measured progress, under a hard cap at which only a proven revert lands; plus rebase-merge metadata invariance of every fleet CI check. Plan red-master-self-healing (livespec-dev-tooling epic livespec-dev-tooling-zcp5vb, child livespec-dev-tooling-4v2yrw). The four calls were decided under the maintainer's delegation to the gitops-fleet-capacity-monitoring driver after Fable review (recorded on livespec-dev-tooling-dfixhe; entered into the revising session's pane): (1) claimants = both the maintainer by forge login and the culprit PR's opener with a Claimed-By: line; (2) hard cap = 2 h default, committed per-repo override; (3) stall = measured p90 per step x 1.5 rounded up to 5 min, in committed config, re-measured after fleet rollout (livespec-dev-tooling plan/red-master-self-healing/research/002); (4) only a revert whose own CI is green merges at the cap. A two-reviewer Fable consensus panel blocked the first draft on the exemption clause and approved this text with zero blockers. Modifications vs the filed proposal: the revert-creation clause is aligned with the merged implementation (livespec-dev-tooling PR 2447): the reconciler describes the revert and the forge commits it via createCommitOnBranch under the fleet App token, and the clause no longer asserts that the forge signs it (GitHub revert commits were measured unsigned; App-commit signing is an open host-captured measurement on livespec-dev-tooling-7n2itg); the exemption's three conditions are stated and may not be weakened; a red-master episode is defined only by the all-green gate job; a revert that would overwrite later work is refused; a reconciler never reverts its own revert and reverts a culprit at most once per episode; the drill reverts product implementation code; the (maintainer call N) markers are removed. Recorded deviations: the proposal's three scenario H2s were consolidated into one H2 of seven scenarios (house style), plus one H2 for metadata invariance; the requested clauses[] gap-id links on the new coverage entries were not added (no gate reads them; behavior_scenario_link runs in warn mode). Consequential non-spec edit owed after this revise: livespec .ai/ci-gate-discipline.md must name the reconciler's describe-and-createCommitOnBranch revert under the App token and the progress-bounded fix-forward claim as the sanctioned remedies, never 'a revert PR via the web UI or API', while still forbidding every other lever.

## Modifications

Revert clause aligned with the merged createCommitOnBranch implementation and the exemption's three conditions; episode defined by the all-green gate job only; clobber refusal; no revert-of-revert and once per culprit; product-code drill; workflow-token vs App-token split; stall rule made concrete (p90 x 1.5, rounded up to 5 min); call markers removed; scenarios restyled to the house gherkin form.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md
- ../tests/heading-coverage.json
- ../tests/heading-coverage-debt.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-15T11:42:22Z
verdict: NO BLOCKERS
proposal_stem: red-master-self-healing-revert-by-default
content_digest: d242d91b5861787734eb4cf6d0eea46d3b602918a5c3c9989fba0db26b6b6111
