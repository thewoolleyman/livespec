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

## Measurements the recommendation asked for (04:10–04:20Z, 29–33 runners)

**sccache hit rate: 1.0 %.** `redis-cli INFO stats` on `sccache-redis`:
137 `keyspace_hits` against 13,750 `keyspace_misses`, 381 keys, 227 MiB used
of the 16 GiB ceiling, 0 evictions, uptime 7,892 s — i.e. since the 01:59Z
proving reboot. Cause, both halves by design: redis is RAM-only ("one
populate refills it after a restart", sccache/README.md), and the populator's
guardrail skips the sccache build whenever the pool has more than 16 admitted
jobs (`warm-cache-populate` 04:00Z: "pool busy (30 admitted jobs > threshold
16); skipping the build this tick"). CI was restored at 02:07Z and has been
above the threshold since, so the cache stays cold exactly when it is
needed, and every Rust job recompiles its dependency graph. The README's
16 GiB derivation also assumes 32 churn slots at 4 GiB each; at `C = 64`
that arithmetic no longer closes (64 × 4 GiB exceeds allocatable), though the
host's 143 GiB free shows the envelope was conservative.

**CPU split by process family (six 10-second `ps` samples, 29 runners,
load 47):** Python and node ~12.4 cores, `pytest-xdist` workers ~5.6 cores,
runner processes ~5.5 cores, git/rsync/tar/rm ~6.6 cores, k3s ~1.2 cores,
Rust/C compile **~0.9 cores**. In this window the fleet's CPU was Python
test suites and checkout/teardown filesystem work, not compilation; the
`rustc`/`clippy` processes that topped `top` at 03:44Z were one console
fan-out. So the compile cache is the lever for the console repository's
bursts and NOT the lever for the steady state.

**The steady-state multiplier is pytest-xdist.** livespec's `justfile` sets
the self-hosted lane to 25 % of cores per job (`-n 18` on this host,
`LIVESPEC_TEST_PARALLELISM` overridable); two `-n 18` jobs were running in the
sample. Ten concurrent Python test jobs is 180 workers on 72 threads, each
worker paying its own collection and import cost — that fixed per-worker
cost is what oversubscription wastes, since the test work itself is
zero-sum. livespec-dev-tooling `livespec-dev-tooling-7us.7` ("Tune
pytest-xdist worker cap for coverage runs") already owns this; the data is
now on it.

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
- Measured (above): the compile cache is cold after every reboot for as long
  as the pool stays busy, and the steady-state CPU is Python test workers,
  not compilers. Two work-items carry the follow-through in
  livespec-dev-tooling: the post-boot populate / persistence question under
  the cache-tiers epic `livespec-dev-tooling-efqeip`, and the per-job xdist
  cap under `livespec-dev-tooling-7us.7`.

## Read-first chain

This note → livespec-dev-tooling `.ai/ci-node-capacity-reads.md` →
livespec-dev-tooling `ci-runner/k3s/phase2/kueue/DERIVATION.md` "The
permanent C is still an open question" (tiered-host C = 64 entry) and "The
derivation at C = 64 restored (2026-09-06)" → poweredge-xubuntu-info
AGENTS.md §"Kubernetes / k3s" (the same-day bullet) → research/005 (the
pod-capacity constraint) → child `livespec-e2vcqf`.
