# 007 — The first hour at C = 64 on the two-NVMe host: CPU is the ceiling, and what that decides (2026-09-06)

Written by the poweredge-raid-array-maintenance plan session (livespec epic
`livespec-g52yrb`) on the day the second NVMe landed and the churn-slot cap
returned from the 2026-09-02 interim 32 to 64 (livespec-dev-tooling PR #1751,
applied ~03:35Z). Filed HERE because this plan (epic `livespec-ifwnqj`) owns
the cap and the k3s host configuration; the storage plan only produced the
conditions. Every measurement is from `poweredge-xubuntu` between 03:36Z and
04:05Z unless it says otherwise. Repository names are written in full.

## Bottom line

1. **Storage is no longer the ceiling. CPU is.** At 33 concurrent runners
   `mpstat 5 6` read 84 % busy (60 % user, 24 % system), idle floor 6–8 %,
   1-minute load 96 with 134 runnable threads on 72; the maintainer observed
   a load peak near 120. Under the same bursts the `ci-workvols` NVMe ran
   38k writes/s at 1.2 ms `w_await` (66 % util), the containerd NVMe 10.6 ms
   at queue depth 18 (7 % util), the RAID array idle, iowait 0.05 %, zero
   `Slow SQL`, zero failed units of consequence.
2. **96 is out**, not deferred. There is no CPU for it, and `max-pods = 200`
   cannot hold `2 × 96` plus helper and system pods (research/005's
   pod-capacity constraint).
3. **The cap is throughput-derived, never utilization-derived** (maintainer
   ruling, 2026-09-06, on the question "should you really be aiming for
   100 %?"). More runners than cores is right while jobs have phases that
   wait — clone, fetch, container start — because a throttled job can still
   begin loading its cache and setting up its container. CPU-bound phases
   are zero-sum: past saturation each extra runner lengthens every job and
   pushes long ones toward their timeouts. The number that sets `C` is p95
   job duration against concurrency, with the control plane responsive; 64
   sits in the oversubscribed-but-flowing regime, and the soak decides
   whether it stays.
4. **`k3s-server` needs no CPU priority.** Its ~120 % of one core is 1.7 % of
   the box, spread over ~20 threads at 3–6 % each (API-server watch fan-out
   to 11 listeners, Kueue, the provisioner and the ARC controller; kubelet
   cgroup stats and pod churn; scheduler; kine; networking). `k3s.service`
   carries no `CPUWeight`, `Nice 0`, no quota — and needs none: at the cgroup
   root `/sys/fs/cgroup/kubepods` and `system.slice` are peers at
   `cpu.weight` 100, so under contention the host side may take half the
   machine. Load 96 produced no `Slow SQL` and no lease trouble.
   `CPUWeight`, `--kube-reserved` and `--system-reserved` are shares that
   decide contention only and never idle a core (a cpuset pin would; none is
   proposed), and runner pods request no CPU (only `ci-runner.io/churn-slot:
   1`), so reserved CPU would change no scheduling decision. Withdrawn as a
   recommendation; recorded so it is not re-proposed.
5. **`metrics-server` stays.** It is not an observability dependency — the
   host OTel collector's `metrics/k3s` pipeline reads `kubeletstats` and
   `k8s_cluster` directly (thewoolleyman/otel-collector PR #7 records it) and
   the cluster has zero HPAs — but its cost is a rounding error and removing
   a component for no gain on "safe as far as I can see" is the wrong trade.
   Maintainer-confirmed.
6. **The memory lever is cache hit rate.** ~143 GiB free, swap unused.
   Memory cannot create CPU cycles; it can stop compute from being repeated.
   The top consumers are `rustc`, `cc1`, `clippy`, so the question is
   `sccache`'s hit rate (the converge stands up `sccache-redis`) and the
   per-repo Rust target-dir and cargo-registry caching the
   livespec-dev-tooling ci-runner-cache-tiers plan owns. A RAM disk for work
   volumes buys nothing at 1–3 ms NVMe latency and zero iowait.

## What else the first hour showed

- **`pvc-pending` fired at the 51-runner burst** (`scan-runner-pod-lifecycle`,
  report-only, exit 1 = its report): 30-odd runner work PVCs pending 165–182 s.
  The local-path provisioner's helper pods compete for the same saturated
  CPU. Below the 600 s bind deadline of research/001; cleared on its own.
  Worth a duration series across the soak.
- **The runner-count signal exceeds `C`.** `EphemeralRunner` objects peaked
  at 96 while `C = 64`; Kueue gates admission, so the surplus is queued
  runners awaiting a slot, not oversubscription of the cap.
- **`sar` is blind to bursts here.** `sysstat-collect.timer` runs every ten
  minutes, so the 20:30–20:40 bucket averaged 43 % busy and closed at load
  48 while the live peak was ~120. Read `mpstat` live for "how busy".
- **Two instrument mistakes, both mine, both recorded in livespec-dev-tooling
  `.ai/ci-node-capacity-reads.md`:** an `iostat -dx` awk that printed `%wrqm`
  (`$11`) as `w_await` (`$12`) and fired a false 75 ms alarm on a 2 ms drive;
  and a first CPU answer ("CPU is the ceiling, 96 is out") given from the
  load average before sampling `mpstat`. The conclusion survived the
  correction; the evidence for it did not exist until the sample.

## What this decides for the plan

- Child `livespec-e2vcqf` (storage plan) has every storage criterion met and
  the 64 restore done; its last open item is the 64-runner soak READ, which
  is this plan's instrument. The soak's deliverable is p95 job duration and
  PVC-pending duration against concurrency, plus `mpstat` at peak.
- A livespec proposed change `ci-host-admission-cap-derivation` states the
  two durable properties as fleet contract: the admission cap is derived from
  job-duration growth and control-plane responsiveness rather than from
  utilization, and the control plane's share of CPU under job contention is
  a host property that MUST hold. It is filed, not ratified, by this note.
- Next measurement: `sccache` hit rate and the compile-versus-test CPU split
  on a real fan-out, to size the cache lever before anyone proposes a number
  above 64 again.

## Read-first chain

This note → livespec-dev-tooling `.ai/ci-node-capacity-reads.md` →
livespec-dev-tooling `ci-runner/k3s/phase2/kueue/DERIVATION.md` "The
permanent C is still an open question" (tiered-host C = 64 entry) and "The
derivation at C = 64 restored (2026-09-06)" → poweredge-xubuntu-info
AGENTS.md §"Kubernetes / k3s" (the same-day bullet) → research/005 (the
pod-capacity constraint) → child `livespec-e2vcqf`.
