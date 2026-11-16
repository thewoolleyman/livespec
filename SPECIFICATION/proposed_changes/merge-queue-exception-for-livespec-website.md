---
topic: merge-queue-exception-for-livespec-website
author: claude-sonnet-5-5
created_at: 2026-11-16T19:47:18Z
---

## Proposal: merge-queue-exception-for-livespec-website

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Qualify the every-organization-owned-repository merge-queue requirement with one named exception, livespec-website, whose maintainer publishes edits directly from the GitHub web editor.

### Motivation

Maintainer ruling on stale-base-merge-options epic livespec-dev-tooling-xowhol, relayed 2026-11-16 by throughput-plans-coordinator: "Livespec website is not unable to commit directly from changes to main. This is a hard requirement of that repo, it's an exception to the rule, so I can publish edits directly from the github website." A required status check or merge queue blocks a direct web-editor commit to the default branch, so livespec-ai/livespec-website cannot sit behind one. Ordering: the earlier proposal merge-queue-on-every-organization-owned-repository (merged as livespec-ai/livespec#3272) is not yet revised, so the two proposals ratify in ONE revise pass, this one second. The earlier file's wording 'every organization-owned repository' (and its 'Every repository whose owner is a GitHub organization ... MUST require GitHub's merge queue' sentence and 'no opt-out' text) is the wording being qualified here; the earlier file's scenario also uses livespec-website as its example, which this proposal replaces with livespec-runtime. In-flight survey: the pending proposals merge-queue-exception-names-the-recovery-principal and incident-merge-principal edit the recovery-bypass exception of the same paragraph, not its first sentence (relationship: align). Open spec PRs livespec#3270, livespec#3206 and livespec#3189 are unrelated (align); remote branches spec/merge-queue-every-org-repo and spec/org-move-merge-queue carry earlier steps of the same line of work (align).

### Proposed Changes

1. In SPECIFICATION/non-functional-requirements.md, paragraph **Merge queue on organization-owned repositories**, as rewritten by the earlier proposal merge-queue-on-every-organization-owned-repository, append to its first sentence (after "The requirement changes only with a livespec specification revision.") this text: "The single exception is the repository livespec-website of the livespec-ai organization: it is exempt from this requirement because its maintainer publishes edits directly from the GitHub web editor and so it cannot sit behind a required status check or a merge queue. The exemption is named in this specification and is not configurable per repository; no other repository may be exempt, and no ruleset requiring a status check or a merge queue may be created on livespec-website." Where that first sentence says "no per-repository name list", read it as "no per-repository name list other than this one named exception", and where it says "no opt-out", read it as "no opt-out other than this one named exception"; edit those phrases accordingly in the revise.

2. In SPECIFICATION/non-functional-requirements.md, in the scenario "### Scenario: Every organization-owned fleet repository requires the merge queue" (added by the earlier proposal), change the example repository "such as livespec-website" to "such as livespec-runtime", and change "that is not livespec-dev-tooling or livespec-orchestrator-beads-fabro" to "that is not livespec-website". Leave the remaining steps unchanged.

3. In SPECIFICATION/non-functional-requirements.md, add this scenario immediately after the scenario named in item 2 (a `###` scenario, so tests/heading-coverage.json needs no new row):

### Scenario: livespec-website is the one organization-owned repository exempt from the merge queue

Given the repository livespec-ai/livespec-website has no active ruleset on its default branch carrying a merge_queue rule or a required status check

When its branch protection is audited against this specification

Then the repository is conforming

And any other repository of the livespec-ai organization without a merge_queue rule on its default branch is non-conforming

And a ruleset requiring a status check or a merge queue on livespec-website is itself non-conforming

And the exemption cannot be extended to another repository by configuration.

Cross-repo placement: the requirement text is livespec core's. The enforcement realization (the branch_protection_alignment check and its owner test in livespec-dev-tooling) is that repository's; its companion change should carry the single named exemption for livespec-website.
