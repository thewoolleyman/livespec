# Raise the fleet CI runner pool to 48 churn-slots — approved ahead of the data

> **RE-STEER 2026-08-30 — the live target is now 64, not 48, and the reclaim
> flip is REJECTED.** After this note was written the maintainer re-steered the
> target from 48 to **64** churn-slots ("go big or go home") and declared a
> standing directive: **DO NOT EVER KILL HEALTHY JOBS** — so
> `reclaimWithinCohort` stays `Never` on all nine ClusterQueues and the
> "strongly recommended companion" reclaim→Any flip proposed lower in this note
> is **NOT adopted**. This note's body below is preserved as the original
> reasoning (the 16→48 argument applies unchanged to 16→64, only more so on the
> idle-headroom side). The authoritative current state is: the epic
> `livespec-zec4mz` handoff timeline, `livespec-dev-tooling` PR #1656, and that
> repo's `ci-runner/k3s/phase2/kueue/DERIVATION.md` §"The derivation at C = 64
> (2026-08-30)". The C=64 Hamilton apportionment is livespec 10, driver-codex 9,
> driver-claude 9, orchestrator-git-jsonl/overseer/runtime/dev-tooling 8 each,
> console-beads-fabro 2, driver-pi 2 = exactly 64.

Maintainer-approved 2026-08-30. **This plan is deliberately bold: it is APPROVED
EVEN THOUGH we have no hard disk-throughput data yet, and EVEN THOUGH the RAID-10
disks tracked in `poweredge-raid-array-maintenance` (epic `livespec-g52yrb`) are
not installed.** The point of raising the cap now is to stop a live, fleet-wide CI
starvation immediately and — if 48 runners saturate the disk — to *produce the very
throughput data we currently lack*. Saturation is an acceptable, wanted outcome
here, not a failure: it converts "no data" into "data."

## The problem this fixes, measured on the cluster 2026-08-30

Symptom seen from a worker session (`test-adequacy-gates`, `livespec-console-beads-fabro`,
PR #891): checks "queued, nothing starting" for ~18 minutes, reported as a
"saturated pool." The host was NOT saturated. Measured directly on
`poweredge-xubuntu` (`KUBECONFIG=/etc/rancher/k3s/k3s.yaml`):

- **Node headroom is enormous and idle.** `kubectl top nodes`: CPU **5%** (3790m of
  72 cores), memory **3%** (7168Mi of ~197Gi). 43 of 110 pod slots used. The
  physical machine was ~95% idle the entire time.
- **The real cap is a hand-set synthetic resource, not the hardware.** The node
  advertises `ci-runner.io/churn-slot: 16` (capacity == allocatable == 16). Every
  runner pod requests exactly `ci-runner.io/churn-slot: 1`. So **16 concurrent
  runners is the hard ceiling for the entire fleet of ~9 repos combined**, wholly
  divorced from the 72-core/197-GiB box it runs on.
- **Kueue rations those 16 slots across one shared cohort** (`fleet-ci-runner-pool`),
  with tiny per-repo guarantees: `nominalQuota` of console=1, driver-pi=1,
  livespec=3, and 2 for the rest (cohort nominal sum 17, already over the physical
  16). Borrowing is unbounded, so a single busy repo takes the whole pool — I watched
  `livespec-driver-claude-cq` (nominal 2) sit at **16 admitted**, the entire node.
- **Reclaim is disabled, so a starved peer cannot claw its share back.** Every
  ClusterQueue carries `preemption: {borrowWithinCohort: Never, reclaimWithinCohort:
  Never, withinClusterQueue: Never}`. When console then queued 16 jobs, Kueue would
  not reclaim driver-claude's borrowed slots; console got its floor of 1 and waited
  for the hog's jobs to drain — the exact 18-minute stall, then a burst to 7-way
  parallelism draining in 16 minutes once the slots freed.

**Root cause (not a symptom): the fleet CI concurrency ceiling is a synthetic
`churn-slot` cap of 16 set far below the machine's real capacity, shared with a
no-reclaim policy that lets one repo monopolize it.** "Saturated pool" was a
misreading of quota-gating as resource-saturation.

## Why 48, and why now, before the disk work

The `churn-slot` gate exists to protect the SINGLE k3s node from ephemeral-pod
*churn* pressure — overwhelmingly a **disk-IO** property (image layers, containerd
snapshotter writes, ephemeral volumes), not CPU or memory. That is also the finding
of `poweredge-raid-array-maintenance`: its own research records that `sda4`/`sda5`
are partitions of the *same* virtual disk behind the *same* controller, so the
2026-08-28 containerd relocation moved bytes but delivered **no throughput
improvement**; the durable fix is new RAID-10 SATA SSDs, not yet installed.

So the honest situation is: CPU and memory have 20x headroom, disk IO is the real
and un-upgraded bottleneck, and we do not yet have a measured churn ceiling for this
disk. Rather than wait for the RAID-10 install to unblock CI fleet-wide, we
**overcommit deliberately**:

- **Target: total pool = 48 churn-slots** (3x the current 16). 48 runner pods is
  trivial for 72 cores / 197 GiB and well under the 110-pod kubelet ceiling, so the
  ONLY resource 48 can plausibly saturate is the disk — which is precisely the
  measurement we want.
- If 48 does saturate the disk, that is the throughput data `poweredge-raid-array-maintenance`
  needs, gathered under real CI load. If it does not, the fleet starvation is simply
  gone. Either result is a win over the status quo of an arbitrary 16.

## The change (execution — routes to `livespec-dev-tooling` `ci-runner/k3s` + host apply)

Two edits to the runner-pool config in `livespec-dev-tooling` (`ci-runner/k3s`),
then applied on `poweredge-xubuntu`:

1. **Advertise 48 slots on the node.** Raise the `ci-runner.io/churn-slot`
   capacity/allocatable on `poweredge-xubuntu` from 16 to **48** (however it is set
   today — static kubelet `--node-labels`/`status` patch or the device-plugin that
   backs it; the executor confirms the mechanism on-host).
2. **Raise the Kueue cohort nominals to sum to ~48, floors off 1.** A sane default
   split (executor may tune): console 3, driver-pi 3, livespec 9, and 5 each for
   dev-tooling, driver-claude, driver-codex, orchestrator-git-jsonl, overseer,
   runtime (= 48). Keep the cohort nominal sum ≤ node capacity so nominal alone never
   overcommits the physical slots.

**Strongly recommended companion (secondary to the approved 48 raise):** flip
`reclaimWithinCohort: Never → Any` on the ClusterQueues so the enlarged pool is
shared *fairly* — a starved repo reclaims its share in seconds instead of waiting
for a monopolizing peer to drain. This is the cheapest guard against the exact
starvation above and should land in the same change unless there is a reason not to.
The approved headline remains the capacity raise to 48; the reclaim flip is a
recommendation for the executor to weigh, not a precondition.

## Instrument the overcommit — this is how we buy the data

Because we are courting disk saturation on purpose, execution MUST watch the disk
while the raised pool runs and feed what it sees back to
`poweredge-raid-array-maintenance` (`livespec-g52yrb`):

- Sample `iostat -x 5` on `poweredge-xubuntu` under real CI load — `%util`, `await`,
  `aqu-sz` on the CI-runner-backing device — and record the numbers on the raid
  plan's epic as the throughput evidence it is missing.
- Watch CI job wall-times and failure rate for disk-pressure symptoms (slow image
  pulls, containerd timeouts, ETIMEDOUT). A rise in *those* — not CPU/mem — is the
  signal that 48 exceeded this disk's churn ceiling.

## Rollback

If 48 degrades CI reliability (not just latency), step the node `churn-slot`
capacity down — try 32, then 24 — and **record the number at which symptoms
appeared**: that number is the pre-RAID-10 churn ceiling for this disk and is itself
a deliverable for `poweredge-raid-array-maintenance`. Do not silently revert to 16;
capture the breaking point.

## Scope and deferrals

- **Requirement carriers:** (1) node advertises 48 `churn-slot`s; (2) Kueue cohort
  nominals raised to ~48 with floors ≥ 2; (3) disk-IO instrumentation sampled under
  load and recorded on `livespec-g52yrb`. All three are repository/host-config work
  that routes to a `livespec-dev-tooling` `ci-runner/k3s` carrier plus a host apply
  on `poweredge-xubuntu`.
- **Deferred — the durable throughput fix.** RAID-10 SSD installation and any
  disk-array rebuild stay in `poweredge-raid-array-maintenance` (`livespec-g52yrb`).
  This plan does NOT wait on it and does NOT own it. Reconsideration point: once the
  RAID-10 disks land and the array is characterized, revisit whether 48 is
  conservative and the pool can go higher.
- **Deferred — the reclaim/fair-sharing redesign** beyond the single
  `reclaimWithinCohort: Any` flip (per-CQ `borrowingLimit`s, Kueue fair sharing,
  preemption tuning) is out of scope here; it belongs to the archived
  `fleet-ci-runner-pool` lineage if it is taken up. This plan touches only the total
  capacity and, optionally, the one reclaim flag.

## Read-first chain

- Cluster evidence and the churn-slot/Kueue mechanics: this note.
- The disk bottleneck and why relocation bought nothing: `plan/poweredge-raid-array-maintenance/research/`
  (epic `livespec-g52yrb`).
- Where `churn-slot` and the ARC/Kueue cohort came from:
  `plan/archive/fleet-ci-runner-pool/research/k3s-arc-kueue-migration.md`.
