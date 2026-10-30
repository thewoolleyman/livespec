---
topic: pool-clause-selector-neutral-dispatch
author: claude-fable-5
created_at: 2026-08-25T15:27:47Z
---

## Proposal: Selector-neutral dispatch wording in the POOL clause

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Reword the POOL clause's dispatch sentence in §"Self-hosted CI runner host requirements" so it describes forge dispatch mechanism-neutrally (a job's selector) instead of label-mechanically ("carrying every label the job names"), matching the v213 restatement of pool-member addressability as a property that label-based pools satisfy with labels and autoscaling runner sets satisfy by set-name selection.

### Motivation

v213 restated the adjacent addressability requirement as a PROPERTY precisely because autoscaling-runner-set pools register runners with NO labels at all — a job selects them by set name, and a label-based reading is unsatisfiable rather than inconvenient (the measurement is recorded in livespec-dev-tooling ci-runner/k3s/phase2/README.md "Registrations are ephemeral"). The POOL clause one paragraph above still explains co-membership through the label mechanism: "The forge dispatches a job to any idle runner carrying every label the job names" and "hosts serving the same label are co-members". On the fleet's live ARC pool that sentence describes nothing that exists, and the v213 review flagged exactly this residue as a follow-up. The clause's substance — additive capacity, no inter-host coordination — is mechanism-independent and is kept verbatim.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Self-hosted CI runner host requirements", clause "**Self-hosted capacity is a POOL, and it MAY span more than one host.**", replace the sentence:

> The forge dispatches a job to any idle runner carrying every label the job names, wherever that runner runs, so hosts serving the same label are co-members whose capacity is ADDITIVE — a further host never supersedes an existing one.

with:

> The forge dispatches a job to any idle runner matching the job's selector — for individually-registered runners, one carrying every label the job names; for autoscaling runner sets, one registered under the set name the job selects — wherever that runner runs, so hosts serving the same selector are co-members whose capacity is ADDITIVE — a further host never supersedes an existing one.

Every other sentence of the clause is unchanged, including "Each host runs its own supervisor and mints its own registrations; no coordination between hosts is required, and none MUST be introduced." and the clause's opening "MAY span more than one host". No `## ` heading is added, changed, or removed, so no tests/heading-coverage.json co-edit arises.
