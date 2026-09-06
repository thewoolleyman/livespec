---
topic: ci-host-admission-cap-derivation
author: claude-fable-5-1 (poweredge-raid-array-maintenance plan session)
created_at: 2026-09-06T04:05:00Z
---

## Proposal: A self-hosted CI host's job-admission cap is derived from job-duration growth and control-plane responsiveness, never from utilization

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add one clause to §"Self-hosted CI runner host requirements" stating two host-observable properties about the job-admission cap on a host that runs jobs as containers: the cap MUST be set from measured job throughput — the concurrency at which job-duration percentiles still grow roughly in proportion to concurrency while the host's control plane stays responsive — and MUST NOT be set from, or capped by, a CPU-utilization target, because more admitted jobs than cores is the correct regime whenever jobs have phases that wait rather than compute; and the host's control plane MUST retain enough CPU under full job contention to keep admitting, scheduling and tearing down jobs, stated as a property (no job-induced loss of control-plane responsiveness), not as a mechanism. The concrete cap value and the means of protection stay host facts in the provisioning repository's records.

### Motivation

The fleet's CI host reached a new ceiling on 2026-09-06 (livespec plan poweredge-raid-array-maintenance, epic livespec-g52yrb; capacity owner plan ci-runner-pod-lifecycle-reliability, epic livespec-ifwnqj, research/007). With both write-hot storage tiers on dedicated NVMe drives, the churn-slot cap returned from an interim 32 to 64 and the first hour showed CPU, not storage, as the binding resource: 84 % busy at 33 concurrent runners, load 96 with 134 runnable threads on 72, while every storage tier ran at 1–11 ms and the array sat idle. The maintainer ruled, in session, that the cap is a throughput decision — a job throttled for CPU can still begin cloning, fetching and setting up its container, so admitting more jobs than cores raises queue throughput — and that the number to watch is job-duration growth and control-plane health, not a utilization figure. The same session established that the host's control plane was already protected by the cgroup layout (the pod slice and the system slice are peers at the root) and that a proposed CPU-priority change would have been mechanism without a property behind it. Neither the principle nor the property is stated anywhere in the specification today: §"Self-hosted CI runner host requirements" bounds schedulable-unit capacity above the admission cap's expansion and requires storage tiers off the OS volume, but says nothing about how the admission cap itself is chosen or about the control plane's survival under job contention. A second host provisioned to this section could set its cap to "stay under 80 % CPU" or let job cgroups starve its control plane and satisfy every existing requirement. The clause is stated as properties, consistent with the section's opening rule; the provisioning repository's derivation record (livespec-dev-tooling `ci-runner/k3s/phase2/kueue/DERIVATION.md`) carries the arithmetic and the live number.

### Proposed Changes

**Change 1 — the new clause.** In SPECIFICATION/non-functional-requirements.md §"Self-hosted CI runner host requirements", insert the following new clause paragraph immediately BEFORE the clause that begins:

> **Availability MUST NOT become a merge dependency.**

(and therefore immediately AFTER the clause that begins "**Storage tiers on a host that runs jobs as containers.**"). The inserted paragraph, verbatim:

> **The job-admission cap on a host that runs jobs as containers is a throughput decision.** The host's job-admission cap — the number of jobs the host admits concurrently — MUST be set from measured job throughput: the concurrency at which job-duration percentiles still grow roughly in proportion to concurrency while the host's control plane remains responsive. It MUST NOT be set from, or bounded by, a CPU-utilization target: a job that is throttled for CPU can still perform the phases that wait rather than compute — cloning, fetching dependencies, starting its container — so admitting more jobs than the host has cores is the expected regime, and the cap is lowered only when job durations grow faster than concurrency or the control plane loses responsiveness. Under full job contention the host's control plane MUST retain enough CPU to keep admitting, scheduling and tearing down jobs without loss of responsiveness; how that share is guaranteed is the provisioning repository's choice, and it MUST NOT hold host cores idle to achieve it. The cap's current value, its derivation from measurement, and the protection mechanism are host facts recorded by the repository that provisions the host's job runtime, never in this specification. Maintainer-directed 2026-09-06.

No `## ` heading is added, changed, or removed (the section is an H3 and the clause is a bold-led paragraph in its existing style), so no tests/heading-coverage.json co-edit arises.
