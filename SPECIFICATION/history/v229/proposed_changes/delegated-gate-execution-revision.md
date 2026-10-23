---
proposal: delegated-gate-execution.md
decision: modify
revised_at: 2026-10-23T21:32:03Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted with modifications. The proposal ratifies delegated pre-push gate execution: opt-in delegation that changes WHERE the gate runs and not WHAT it verifies, with sub-rules *The host*, *The tree*, *The set*, *The authority*, *The credential* and *The verdict*. It conforms livespec to the delegation client that livespec-dev-tooling ratified in its spec v082 and shipped in v1.126.0, which this repository pins. Without it, livespec's spec says pre-push runs `just check` locally, which is false for a delegating repository.

DESIGN-RECORD DEPARTURE, ACKNOWLEDGED. This resolution departs from the maintainer's 2026-09-08 delegated-gate ruling, which is recorded in this proposal's 'Two decisions this proposal carries' section and in the design record of plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn, research/003). That ruling said no verification relocates to the pushing host and that pushing hosts hold no credentials. The departure covers exactly two classes: (1) a check that reads an authorization held outside the tree runs on the pushing host and joins the delegated verdict (*The authority*); and (2) a host that holds no executor credential runs the gate recipe locally and reports that it did (*The host*). The maintainer accepted both explicitly on 2026-10-23 through the plan owner's picker (answer: 'Accept both'; recorded on ledger epic livespec-dev-tooling-mvalxq). The 2026-09-08 FAIL disposition and its factory-side remedy still govern every other verification.

WHY MODIFY. The proposal's 2026-10-23 amendment qualified Edit 4 for *The host* and *The authority*. It left Edits 5 and 6, and *The set*'s 'in full', unqualified. Verbatim ratification would therefore have left contracts.md section 'Pre-commit step ordering' contradicting the new clause. The first independent ratification review found this and returned BLOCKERS. The modifications are internal-consistency repairs inside the two accepted classes. They add no new obligation.

## Modifications

M1 (contracts.md, Edit 5): the executor runs the aggregate only for a push from a delegating host, save the members that read an authorization held outside the tree, which the pushing host runs.
M2 (contracts.md, Edit 6): the same qualification.
M3 (contracts.md, Edit 4): adds that from a host that is not a delegating host, the recipe runs `just check` as above.
M4 (non-functional-requirements.md, *The set*): 'the executor MUST run the gate under that configuration in full' gains 'save the checks *The authority* places on the pushing host'.
M5 (non-functional-requirements.md, scenario 'A host that holds no executor credential gates locally in a delegating repository'): drops the last And-step, which described a different host (a delegating host whose executor returns no verdict). Scenario 'A delegated pre-push gate refuses the push when no verdict arrives' already covers that case.

## Resulting Changes

- contracts.md
- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-23T21:31:33Z
verdict: NO BLOCKERS
proposal_stem: delegated-gate-execution
content_digest: c2a6feef99dcc96c441f05cf39c4bbae2b8a082e445ee59252cd029e7622ed03
