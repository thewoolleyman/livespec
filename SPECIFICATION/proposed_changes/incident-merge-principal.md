---
topic: incident-merge-principal
author: claude-opus-5-5 (livespec-dev-tooling bqnzcm plan seat)
created_at: 2026-11-15T22:47:27Z
---

## Proposal: A distinct incident-merge principal may merge a green expedited repair outside the merge queue

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Let a merge-queue repository provision an incident-merge principal, distinct from the inverse-only recovery principal, that merges one expedited repair outside the queue only when the incident's genesis, the trusted PR signal, the attempt's exact base and head binding and a fully green required-check set on that head all hold at merge time. It merges against the expected head, records every merge and refusal on the incident item, never merges an inverse or a non-incident change, and leaves master CI, recovery and the unexpedited follow-up unchanged. Add the principal to first-enablement proof and add two scenarios.

### Motivation

Maintainer ruling on livespec-dev-tooling-72b33c, 2026-11-15, verbatim: "Yes option A is acceptable. The merge train can be bypassed for an incident". In a repository whose default branch requires a merge queue, the expedited lane speeds the commit but not the merge, so a forward repair waits behind every queued pull request. The only principal this policy lets act outside ordinary merging is the recovery principal, which MUST merge only the validated complete inverse, so a forward merge needs a distinct, separately authorized principal. A queue or ruleset bypass also skips required status checks, so the ratified text must keep the new principal from merging past a red check. Fleet scope: every governed repository whose default branch requires a merge queue. The companion implementing-repository proposal is livespec-dev-tooling incident-merge-principal-queue-bypass.

### Proposed Changes

In `contracts.md` §"Expedited incident response policy", immediately after the sentence "An independently provisioned recovery principal MUST merge only the validated complete inverse of the recorded incident change against current master, preserving later unrelated edits, revalidating the expected head, and recording an owned overlap conflict rather than overwriting descendants.", add:

A governed repository whose default branch requires a merge queue MAY provision an incident-merge principal, distinct from the recovery principal, so that an expedited repair is not held behind the whole queue. The incident-merge principal MAY merge one expedited repair pull request outside the merge queue only when, read at merge time, the incident has a recorded genesis in its canonical authority chain, the pull request carries the trusted PR-specific incident signal, the incident's current attempt binds that pull request's exact base and head, and every required check of the default branch has concluded success on that exact head. A queue or ruleset bypass also skips required status checks, so this verification MUST be the incident-merge principal's own obligation; it MUST NOT merge past a required check that is failing, pending or absent. The incident's recorded genesis in its canonical authority chain MUST be the sole authority for a merge: the trusted PR-specific incident signal is necessary but never sufficient, and a flag, environment variable, label alone or commit subject line MUST NOT count as authority. It MUST refuse when the incident work item is closed or the bound attempt has been superseded. It MUST act only by merging the pull request: it MUST NOT push to the default branch, force-push, or move the default branch's ref by any other means, even where its bypass permission would allow it, so that it bypasses the merge QUEUE only. It MUST merge against the expected head, so a head that moved after verification refuses. It MUST record each merge (acting principal, merged head, resulting master head, time, and the queue entries that were ahead) and each refusal on the incident work item. It MUST NOT merge an incident inverse, which remains the recovery principal's only merge, and it MUST NOT merge any change that is not an expedited incident repair. It changes no other obligation of this policy: the normal master CI run, first-failure recovery and the unexpedited factory follow-up apply to a principal-merged repair exactly as to a queue-merged one. The recovery principal MUST NOT also serve as the incident-merge principal.

In the same section, extend the first-enablement sentence's proof list: where a repository provisions an incident-merge principal, its first enablement MUST also require recorded proof of that principal's authorization against every overlapping classic protection or ruleset.

Add to `scenarios.md`, beside "An incident master failure takes immediate scoped recovery":

## An incident-merge principal merges a green expedited repair outside the merge queue

```gherkin
Given a repository whose default branch requires a merge queue provisions an incident-merge principal distinct from its recovery principal
And an expedited repair pull request whose incident's current attempt binds its exact base and head
And every required check of the default branch concluded success on that head
When the incident-merge principal merges the pull request
Then the repair lands without waiting behind the merge queue
And the incident work item records the acting principal, merged head, resulting master head, time and the queue entries that were ahead
And the normal master CI run, first-failure recovery and the unexpedited factory follow-up still apply
```

## An incident-merge principal refuses a repair with a required check that is not green

```gherkin
Given an expedited repair pull request whose incident's current attempt binds its exact base and head
And one required check of the default branch has not concluded success on that head
When the incident-merge principal is asked to merge the pull request
Then it does not merge
And the incident work item records the refusal naming that check
```

Realization mechanism, namely which forge App holds the role, how a governed repository declares it and how its branch-protection check admits it, belongs to the implementing repository's specification (livespec-dev-tooling's companion proposal incident-merge-principal-queue-bypass), not to core. Any heading-coverage rows the two new scenario headings owe MUST be co-edited in the revise commit.
