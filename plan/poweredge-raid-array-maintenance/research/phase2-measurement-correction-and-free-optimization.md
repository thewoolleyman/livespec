# Phase 2 — a measurement correction, and the no-spend optimization plan

Measured 2026-08-28 on the idle array, after `fio` and `perccli` were installed.
Two things happened: a **methodology error in the earlier Phase 2 numbers was
found and corrected**, and the free tuning knobs were tested properly.

**This note corrects `phase2-optimization-analysis.md`. Read this before quoting
any random-write figure from that note.**

## Bottom line

1. **The earlier random-write figures were measured COLD and are pessimistic by
   roughly 7×.** Warming the working set first raises 4 KB random writes from
   ~1,400 IOPS to **~10,400 IOPS**. The array is substantially better than
   reported — though *which* number is representative depends on the workload's
   working-set size and whether it is writing freshly-allocated blocks.
2. **The controller cache-policy knobs are not a meaningful win.** Cache-bypass
   OFF gives a modest ~9% IOPS / −31% p99 improvement on 4 KB random writes and
   **nothing measurable on the CI-shaped workload** (the test result straddled
   both baselines — that is noise, not signal). Original setting restored.
3. **The real no-spend win is moving the hot path off the array entirely**, via
   tmpfs, plus relocating containerd and the PVC root off `/`. Neither costs
   money and neither needs downtime or a rebuild.

## The methodology error, and why it matters

The earlier Phase 2 sweep created its `fio` files and measured in the same pass.
That conflates two different things: writing to **freshly-allocated** blocks, and
steady-state overwrite of blocks the array has already seen.

Re-running the identical random-write test with two discarded warm-up passes
first:

| | 4 KB random write |
|---|---|
| Earlier, cold, 8 GB working set, qd8 | **1,444 IOPS**, p99 505 ms |
| Warm, 4 GB working set, qd16 | **~10,400 IOPS**, p99 ~32 ms |

Two variables changed at once — warm-vs-cold *and* an 8 GB versus 4 GB working
set against a 2 GB controller cache — so this does not cleanly attribute the
gap. What it does establish is that **the earlier note's headline claim, that
the array "collapses to ~1,000 IOPS with p99 latency up to 2.1 seconds", is only
true for a cold, cache-exceeding working set** — not as a general property of
the array.

**Which figure is representative of CI is genuinely unresolved.** CI builds
constantly create new files, so the cold-allocation path is real and the
pessimistic number is not a pure artifact. But CI also re-reads and rewrites
caches and layers, which is the warm path. Both are happening. The honest
statement is a range — **roughly 1,400–10,400 IOPS depending on working set and
allocation state** — not a single ceiling.

**The general lesson, recorded because it nearly shipped as a finding twice in
one session:** a storage benchmark that allocates its own files measures
allocation on the first pass. Warm up, then measure, and bracket the measurement
between two baselines so drift is visible.

## The cache-policy tests, and why they were nearly reported wrong

The first attempt appeared to show a large win — 4 KB random writes rising from
5,019 to 8,900 IOPS with cache-bypass "disabled". **That result was false.** The
`perccli /c0/v0 set cbmode=7` command had silently failed (it printed a
syntax-help stub rather than `Status = Success`, because `cbmode` must be set
together with `cbsize`), and a verification read confirmed the policy was
unchanged. The apparent 77% improvement was **entirely warm-up** between
successive runs.

The correct controller-level form is `perccli /c0 set cachebypass=on|off`. Re-run
properly — warmed, and bracketed between two baselines:

**4 KB random write, qd16, 4 jobs:**

| Configuration | IOPS | p99 |
|---|---|---|
| Baseline 1 (bypass ON) | 10,397 | 32.37 ms |
| **Test (bypass OFF)** | **11,626** | **21.36 ms** |
| Baseline 2 (bypass ON) | 10,969 | 29.49 ms |

Baseline spread is ~5.5%, and the test sits outside it on both metrics:
**≈ +9% IOPS, ≈ −31% p99.** Real, but modest.

**CI-shaped (64 KB writes, fsync every write, 4 jobs):**

| Configuration | IOPS | p99 |
|---|---|---|
| Baseline 1 (bypass ON) | 3,725 | 1.96 ms |
| Test (bypass OFF) | 3,505 | 1.78 ms |
| Baseline 2 (bypass ON) | 3,766 | 1.63 ms |
| Test 2 (bypass OFF) | 4,043 | 1.53 ms |

**The two OFF results (3,505 and 4,043) straddle the two ON results (3,725 and
3,766). That is noise.** There is no CI-shaped effect.

**Disposition: leave cache-bypass ON (the default).** It was restored after
testing. A ~9% gain confined to a synthetic 4 KB random pattern does not justify
diverging from the default configuration on a machine nobody is tuning daily.
Recorded so the question is not re-opened.

Also confirmed while testing: **the drives' own write cache is already
enabled** (`smartctl -g wcache` → `Write cache is: Enabled`, via the VD's
`Disk Cache Policy = Disk's Default`). These Samsung enterprise SATA parts carry
power-loss-protection capacitors, so that is both safe and already optimal —
there is no free win waiting there either.

## The no-spend optimization plan

Ranked by benefit per unit of effort. None of these costs money, requires
downtime, or requires a destructive rebuild.

### 1. tmpfs for runner work volumes — the largest available win

**111 GiB of RAM is available at ~0.3% memory pressure.** I/O to a tmpfs never
reaches storage, so it is immune to every question above — parity penalty,
working-set size, cold allocation, and the array's ceiling all stop applying to
whatever moves there.

This is strictly better than anything a drive purchase can buy for the *hot*
path, because it removes the storage layer rather than making it faster.

Constraints to design around:
- tmpfs counts against pod memory limits and node allocatable, so runner pod
  limits must be raised in step.
- It is volatile across reboots — correct for disposable runner scratch, wrong
  for anything durable.
- It scales with concurrent runner count, so it needs an explicit cap. At 16
  concurrent runners a 5 GiB cap each is 80 GiB worst case, which fits 111 GiB
  but leaves little headroom; size the cap against the real per-job footprint
  rather than the worst case.

### 2. Relocate containerd and the PVC root off `/`

The characterization established that **all CI write traffic lands on `sda4`
(`/`)** — `/var/lib/rancher/k3s/agent/containerd` (11 GB) and
`/var/lib/rancher/k3s/storage` (13 GB, every runner's work volume) — while
`sda5` (`/var/cache/ci-runner`, 718 GB) sits idle.

**This does not improve throughput** — both are partitions of the same virtual
disk on the same three drives, as `phase1` and the characterization both state.
It is still worth doing, for two reasons that have nothing to do with speed:

- **Blast radius.** A runaway job that fills `/` currently takes down the OS and
  k3s, not just CI. A dedicated filesystem contains that.
- **It converts the future fix into a mount change.** Once containerd and the
  PVC path live at a known mount point, moving them to different media — a new
  VD, an NVMe, or a tmpfs — becomes a remount rather than a k3s reconfiguration.

This was the original intent of `livespec-s43svm.2`, which was re-scoped and
delivered a warm `uv` cache on sda5 without moving containerd or the local-path
provisioner. That half remains outstanding.

### 3. Cache-policy tuning — measured, and declined

See above. Leave at defaults.

### 4. Strip size — declined without a rebuild

Current 64 KB strip / 128 KB full stripe against a ~158 KB average host write.
Changing it requires destroy + recreate, which means the full backup and restore
sequence. Not worth that cost on its own, given the sequential path is not where
the loss is. Reconsider only if the array is being rebuilt for another reason.

## What is NOT available without spending

For completeness, so the no-spend plan is not mistaken for the whole option set:

- **RAID 10 is impossible with three drives** — it requires an even count ≥ 4.
- **The only re-geometries available on three drives** are RAID 5 (current),
  RAID 0 (no redundancy at all), or RAID 1 across two with the third spare
  (losing a third of capacity and gaining no write throughput). None is an
  improvement worth a destructive rebuild.
- **A second VD on the same three drives does not help** — it would share the
  same spindles and the same parity behavior.

The purchase options, and the analysis of buying a single drive, are in
`phase2-pricing-comparison.md` and
`phase2-single-drive-raid10-analysis.md`.
