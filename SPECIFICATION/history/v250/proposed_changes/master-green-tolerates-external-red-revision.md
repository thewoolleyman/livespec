---
proposal: master-green-tolerates-external-red.md
decision: modify
revised_at: 2026-11-16T01:01:00Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-fable-5-1
---

## Decision and Rationale

Modified and accepted by the delegated decider, the master-green-external-outage plan seat (epic livespec-dev-tooling-2ex7k7), on the maintainer's design direction recorded in the SUPERSEDES plan-scope-event on livespec-dev-tooling-6tgd2z (2026-11-15 23:22Z) and graded PASS by both legacy-coordinator-agent and throughput-plans-coordinator at head 8031763a before merge. The rule gives every fleet repository's master-green gate one evidence-keyed exception: a DEFECT red blocks as today, an EXTERNAL red (forge rate limit or quota recognised from its own rate-limit evidence whatever the status code, forge 5xx or outage, network unreachable, third-party dependency down) warns and admits every commit and push while the failing verdicts stay red on master and each pull request's own checks still bind; a job is external only when every failed step ended on a recorded external failure and it found no defect; evidence is read only from master's own gating push run of its HEAD commit; the tolerance ends at green or after a deterministic 24 h clock with one idempotent needs-attention alert per episode; no lever and no LLM in the gate. Placement: a contributor-facing CI-gate rule, so non-functional-requirements.md beside 'CI as a merge gate'; behaviour carried by six Gherkin scenarios in scenarios.md. Co-edits: six spec-first TODO rows in tests/heading-coverage.json naming the integration tier and the owning item livespec-xzxsqb, and the regenerated tests/heading-coverage-debt.json. Realization (the shared helper, the master-health check run, how the gate reads it, the alert's de-duplication) belongs to livespec-dev-tooling's companion proposal of the same topic (livespec-dev-tooling#4828), not to core. Explicit NON-CHANGE: the master-health reconciler's classification and the merge-queue paragraphs are untouched. Stale-branch precondition (Step 3.5) skipped via --skip-stale-branch-check at the decider's ruling. Warning, recorded verbatim: four other local spec/* branches are ahead of origin/master and each is a live, unrelated in-flight proposal or revise by another seat, neither merged nor abandoned: spec/ccs-wave1-revise (ahead 4), spec/doctor-surfaces-open-spec-pull-requests (ahead 1, livespec#3250), spec/fleet-manifest-adopter-owner (ahead 2), spec/propose-incident-merge-principal (ahead 2, livespec#3258). This pass disposes of none of them; --only-topic narrows it to master-green-tolerates-external-red.

## Modifications

Modified at the delegated decider's ruling after the pre-merge doctor LLM pass (2026-11-16T00:56:41Z) walked the accepted bytes through master_ci_green.py and the realizing livespec-dev-tooling proposal, four medium and three low findings, all folded in: (1) who alerts: the needs-attention alert is raised by the repository's CI step that publishes the verdicts, never by the gate, which stays read-only, and that step also runs on the existing schedule so a quiet master still alerts; (2) the 24 h sequence is defined: broken only by a completed run whose all-green gate job reads success; a cancelled, skipped or in-progress run neither extends nor breaks it; completion is the gate job's own completion time; (3) evidence scope: the VERDICT comes from master's own gating push run of its HEAD commit (latest completed run where one HEAD has several), and the episode may be computed from earlier master push runs' published verdicts, the one permitted read beyond HEAD; (4) a gate that cannot read the HEAD run behaves exactly as it does without this rule, including its recorded environmental skips, and blocks wherever it would block today, so the rule hardens no fail-soft case; (5) rate-limit evidence is recognised on a 403 or 429 response, not on any status; (6) no check that reads green on a red master may be added to the required-check set; (7) two scenarios added: the gate reads only master's own push run, never a scratch-branch run; the external clock does not restart on a new head; the one-day scenario now has CI's publishing step raise the alert once. Six scenario headings carry heading-coverage rows owned by livespec-xzxsqb.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md
- ../tests/heading-coverage.json
- ../tests/heading-coverage-debt.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-16T01:00:10Z
verdict: NO BLOCKERS
proposal_stem: master-green-tolerates-external-red
content_digest: 1793efa339c5ba82a6425da5fa9e9441aecca4c9ea811788a83c7beb5add4b69
