---
topic: ci-host-container-concurrency-budgets
author: claude-opus-4-8
created_at: 2026-09-01T15:39:13Z
---

## Proposal: Container-concurrency kernel-watch and node-capacity budgets for self-hosted CI hosts

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add two host-observable property clauses to §"Self-hosted CI runner host requirements", both scoped to a host that runs jobs as containers under a scheduler (the OPTIONAL containerized path the section already carves out): (1) the kernel's per-user watch budget MUST cover the pool's peak container concurrency × the per-container watch instances the runtime opens, with headroom; (2) the node's schedulable-unit capacity MUST cover the full expansion of the scheduler's concurrency cap — units-per-job × the cap, plus infrastructure and system units — with headroom. Both are stated as properties, not as kernel-tunable names or numeric defaults; the concrete measurement that motivates them is cited here in the rationale. No `## ` heading is added, changed, or removed, so no `tests/heading-coverage.json` co-edit arises.

### Motivation

On 2026-09-01 fleet CI stalled — runs queued with nothing starting for over an hour — and the root cause was a per-user KERNEL RESOURCE budget left at its distribution default, not compute, disk, memory, or admission quota (measured on the fleet's single-node k3s pool `poweredge-xubuntu`; the full chain is in livespec `plan/ci-runner-pod-lifecycle-reliability/research/001-provisioner-bind-deadline-stall-2026-09-01.md` and `research/002-inotify-instance-cap-root-cause.md`, and the scope event on epic `livespec-ifwnqj`).

Two distinct default ceilings were crossed, and the section names neither as a property today:

1. **Per-user inotify-instance budget.** `fs.inotify.max_user_instances` was the kernel default 128; uid 0 held 127/128 with ~110 `containerd-shim` processes (each holding 2 instances for the cgroup v2 `memory.events` OOM watch) plus the kubelet/cadvisor cgroup-tree watcher. At the cap, containerd logged `failed to create inotify fd: too many open files`, shim/ttrpc streams broke, and container create/kill calls timed out (`DeadlineExceeded`), so PVCs never bound and CI queued. The instance ceiling is a function of concurrent containers, which the 2026-08-30 churn-slot raise (C = 16 → 64) roughly quadrupled; raising the ceiling to 8192 (persisted in `/etc/sysctl.d/`) cleared it immediately. The pre-existing `max_user_watches` had been raised long ago; the INSTANCE ceiling never was, precisely because nothing in the contract said it had to scale with pool concurrency.

2. **Node pod-slot capacity vs. the admission cap.** Each admitted job occupies TWO pods on this pool (an ARC runner pod and a separate per-job `-workflow` pod), plus a transient `local-path` provisioner helper pod per volume. At C = 64 that is at least 128 job pods against the default kubelet `max-pods` of 110 — the pool can never run the concurrency it is configured for, and at ~50 concurrent jobs the helper pods that provision the NEXT job's volume cannot even schedule (`Too many pods`). The admission layer keeps granting churn-slots while the node rejects the surplus. The derivation of the churn-slot cap against node capacity is in `livespec-dev-tooling` `ci-runner/k3s/phase2/kueue/DERIVATION.md`.

Both are host-observable relations that any conforming containerized pool must satisfy, and both were invisible failure modes: a default that is silently too small for the pool's configured concurrency, discovered only when the pool stalled. The section already states every requirement as a property realized by the provisioning repository's own native means; these two extend that discipline to the kernel-resource and node-capacity budgets that a high-churn containerized pool depends on. They are scoped to the containerized path because §"Containerized job execution is OPTIONAL" makes running jobs directly on the host the simplest conforming shape, and a direct-execution host opens no per-container watchers and schedules no pods, so neither property binds it.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Self-hosted CI runner host requirements", immediately after the clause beginning "**Containerized job execution is OPTIONAL.**" (the clause that ends "...A host that offers only a root-equivalent container daemon MUST run jobs directly rather than in containers."), insert the following two new clauses:

> **A host that runs jobs as containers MUST provision the kernel's per-user watch budgets to cover the pool's peak container concurrency.** The clause above makes containerized execution optional; a host that takes it on runs a container runtime that opens several per-container kernel watch instances — a runtime that watches each container's cgroup for out-of-memory and lifecycle events, and the node agent's own cgroup-tree watcher. Those instances are charged against a per-user budget, and the pool's containers run under a single service identity, so that budget MUST cover the pool's maximum concurrent containers multiplied by the watch instances the runtime opens per container, with headroom. A budget left at a distribution default does not conform merely by being the default: when it is exhausted the runtime can no longer create watches and its container lifecycle calls begin to fail, which stalls the whole pool while jobs queue and nothing starts. This is a PROPERTY — the budget-covers-peak-concurrency relation — realized by whatever per-user kernel-resource setting the host provides, and a pool that raises its concurrency cap MUST re-check it against the new peak.
>
> **A host that caps job concurrency through a scheduler MUST size the node's schedulable-unit capacity above the full expansion of that cap.** Where a host admits jobs through an orchestrator that gates concurrency at a fixed number of slots, the number of schedulable units the node must hold is not that slot count: one admitted job can expand into several units — a runner unit and a separate per-job workload unit — and the node also carries transient infrastructure units, such as per-job volume provisioning, plus the system's own units. The node's schedulable-unit ceiling MUST therefore cover the units-per-job multiplied by the admission cap, plus peak infrastructure units, plus system units, with headroom. A node whose ceiling is below that expansion cannot run the concurrency it was configured for: the admission layer keeps granting slots while the node rejects the surplus units, so a job is admitted and then cannot place its own pods. This is a PROPERTY — the ceiling-covers-expansion relation — and the concrete node ceiling and admission cap are the host's and the pool's to set consistently.

Every other clause of the section is unchanged. No `## ` heading is added, changed, or removed (both additions are `**bold.**`-lead clauses inside the existing `### Self-hosted CI runner host requirements` section), so no `tests/heading-coverage.json` co-edit arises.
