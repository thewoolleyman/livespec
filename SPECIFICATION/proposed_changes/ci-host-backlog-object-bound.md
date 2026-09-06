---
topic: ci-host-backlog-object-bound
author: claude-fable-5-1
created_at: 2026-09-06T08:11:06Z
---

## Proposal: A host that gates job concurrency MUST bound the pending work it materializes as control-plane objects

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add one clause to §"Self-hosted CI runner host requirements", immediately after the schedulable-unit-capacity clause, stating a host-observable property: on a host that admits jobs through a scheduler, the number of admitted-but-not-running jobs the host materializes as control-plane objects MUST be bounded to a small multiple of the admission cap, and queued work beyond that bound MUST wait at the forge rather than on the host. The multiple and the mechanism are the provisioning repository's. No `## ` heading is added, changed, or removed, so no tests/heading-coverage.json co-edit arises.

### Motivation

The section already bounds the node's schedulable-unit capacity ABOVE the admission cap's expansion (the units-per-job relation) but says nothing about the other direction: how much work a backlog may create on the host BELOW the cap. On 2026-09-06 the fleet's CI host (livespec plan poweredge-raid-array-maintenance, epic livespec-g52yrb; capacity owner epic livespec-ifwnqj) showed why that matters. With the cap at 32 and each repository's scale-set ceiling set to its doubled matrix width (ten ceilings summing to 574), the first fleet-wide backlog on the two-NVMe host materialized as 122 gated runner objects and 119 pending scheduler workloads while 25–30 jobs ran; each pending object is several control-plane records rewritten on every reconcile through the datastore's single writer, and the datastore logged 11 slow writes over one second in ten minutes — more than the 64-slot burst two hours earlier, because the write volume tracks the depth of the backlog rather than the admitted count. The earlier flannel panic that took the API server down for sixteen seconds fired at the tail of the same kind of churn. A host provisioned to this section today could conform on every existing clause and still let a backlog saturate its control plane. Stating the bound as a property keeps the section's opening rule: the fleet realizes it by bounding each scale set's `maxRunners` to `max(2 x nominalQuota, 6)` (livespec-dev-tooling ci-runner/k3s/phase2/kueue/DERIVATION.md "Bounding maxRunners to the quota (2026-09-06)"), and the matching provisioning-repository clause is amended by livespec-dev-tooling's proposed change scale-set-ceiling-bounded-to-fair-share.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Self-hosted CI runner host requirements", insert the following new clause paragraph immediately AFTER the clause that begins:

> **A host that runs jobs as containers and caps job concurrency through a scheduler MUST size the node's schedulable-unit capacity above the full expansion of that cap.**

(and therefore immediately BEFORE the clause that begins "**Storage tiers on a host that runs jobs as containers.**"). The inserted paragraph, verbatim:

> **A host that caps job concurrency through a scheduler MUST bound the pending work it materializes as control-plane objects.** The preceding clause sizes the node above the cap's expansion; this one bounds the other side. When the forge holds more queued jobs than the host admits, the host MUST NOT materialize every queued job as a pending admission object — a runner registration, a workload record, or their events — because each pending object is control-plane state the host keeps reconciling for as long as it waits, and a backlog materialized in full loads the host's control plane in proportion to the backlog's depth rather than to the work it is doing. The number of admitted-but-not-running jobs represented as objects on the host MUST therefore be bounded to a small multiple of the admission cap, large enough that a repository can take up capacity its peers leave idle, and queued work beyond that bound MUST wait at the forge, where it costs the host nothing and runs no later, since only the cap's worth can run in either case. This is a PROPERTY — the pending-objects-bounded-by-the-cap relation — and the multiple, any per-repository floor, and the mechanism that enforces it are recorded by the repository that provisions the host's job runtime, never in this specification. Maintainer-directed 2026-09-06.

No `## ` heading is added, changed, or removed (the section is an H3 and the clause is a bold-led paragraph in its existing style), so no tests/heading-coverage.json co-edit arises.
