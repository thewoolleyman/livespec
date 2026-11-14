---
proposal: master-health-reconciler-reruns-cancelled-master-runs.md
decision: accept
revised_at: 2026-11-14T04:04:13Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as filed under delegated revise authority, in the livespec revise slot legacy-coordinator-agent granted (relayed by throughput-plans-coordinator) to the red-master-self-healing plan (livespec-dev-tooling epic zcp5vb), which carries this proposal for its child livespec-dev-tooling-tig7vu (option A of the maintainer's 2026-11-09 superseded-master-runs ruling). The track grader graded livespec#3190 FAIL at 02e49223684, then PASS-WITH-FIXES at fdcac3841c6b after four fixes: the re-run is bounded to once per commit per episode, a re-run without a verdict raises needs-attention, the re-run runs in a concurrency group of its own, and a scenario covers a re-run that is itself cancelled. CI was green at 88833300 before the merge. Both changes are applied word for word from the proposal: clause (b) of the 'Red master heals itself: revert by default.' paragraph in non-functional-requirements.md, and two scenarios appended inside the existing gherkin block under '## A red master heals by revert by default, or through a progressing fix-forward', after 'A revert that would clobber later work is refused'. Each quoted target matched the live file exactly once. No '## ' heading is added, so tests/heading-coverage.json needs no co-edit. The independent sonnet review compared the staged bytes with the proposal, recomputed the content digest, and reported no blockers. Its nits are not acted on: (1) the first scenario names only the earliest unverdicted commit, which is consistent with one step per reconcile; (2) clause (b) is a long sentence, a matter of style. Follow-on work: livespec-dev-tooling-tig7vu realises the clause; its Definition of Done dispatches a NEW gating run in its own group, because a plain GitHub re-run keeps the original master-push group. The other pending proposals are left in place by this single-topic pass.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-14T04:03:45Z
verdict: NO BLOCKERS
proposal_stem: master-health-reconciler-reruns-cancelled-master-runs
content_digest: c506d700f41f64b91cc374d43cbdda8b916ddb020e1df99e178e207b7876f1bf
