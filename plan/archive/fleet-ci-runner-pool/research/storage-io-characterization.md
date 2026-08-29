# The CI host's storage subsystem — characterization, and what is NOT wrong with it

Read this before proposing any change to `ci-runner.io/churn-slot` capacity, to
the RAID configuration of `poweredge-xubuntu`, or to where k3s writes.

Written 2026-08-26 against live state. It started as one narrow question — why a
single `check-lint` job waited 3m24s for a runner — and ended in the storage
subsystem, because that is where the answer was. Four hypotheses were raised and
**eliminated by measurement** along the way; they are recorded here with their
disproofs, because each one is plausible enough to be re-derived by the next
reader, and re-deriving a dead hypothesis is the expensive way to learn it.

One question remains genuinely open, and the cheap test that settles it is in
`## The measurement plan`.

## Why the plan cares

`kueue/DERIVATION.md` in `livespec-dev-tooling` states that `C` — the node's
churn-slot capacity, currently 16 — is "a measured ceiling, not a free
parameter", that picking it "is a HOST CAPACITY decision, made by a maintainer",
and that the permanent value "is still an open question", bracketed between 16
(soak-proven safe) and 482 (a target, never run). Choosing it needs to be
grounded in what the host can actually take. This document is the storage half
of that grounding.

It also corrects a claim made in this plan's own earlier reporting: that the
host has "much excess RAM and CPU capacity" and the 16-slot cap therefore looks
arbitrary. The RAM and CPU headroom is real. It is also irrelevant, because
neither is the constrained resource.

## Physical inventory

Every value below was read from the live host on 2026-08-26.

### Host

| | |
|---|---|
| Model | Dell **PowerEdge R630** |
| Service tag | `JBS0JB2` |
| CPU | **2 ×** Intel Xeon **E5-2696 v3** @ 2.30 GHz — 18 cores / 36 threads each, **72 threads total** |
| Memory | **188 GiB** (~118 GiB available, memory PSI ≈ 0.3%) |
| PCIe Slot 1 | PCI Express 3 **x16 — Available (empty)** |
| PCIe Slot 2 | PCI Express 3 — In Use |
| OS / kernel | Ubuntu 26.04 LTS, `7.0.0-29-generic` |

### RAID controller

| | |
|---|---|
| Product | **PERC H730P Mini** (Broadcom/LSI MegaRAID SAS-3 3108 "Invader", rev 02) |
| Serial | `84P036E` |
| FW package | `25.5.9.0001` |
| FW version | `4.300.00-8368` |
| BIOS | `6.33.01.0_4.19.08.00_0x06120304` |
| Cache | **2048 MB** |
| Host interface | PCIe |
| Cache flush interval | 4 s |
| Rebuild / BGI rate | 30% each |

**Battery backup unit — healthy.** `Battery State: Optimal`, `isSOHGood: Yes`,
3912 mV, 34 °C, remaining capacity 312 mAh of 321 mAh full-charge. No learn
cycle requested or active, none periodic-required.

### Enclosure and bays

| | |
|---|---|
| Enclosure device ID | 32 |
| **Slots total** | **8** |
| **Slots populated** | **3** |
| **Free bays** | **5** |

### Virtual disk

| | |
|---|---|
| VD | 0 (Target Id 0) |
| **RAID level** | **RAID 5** (Primary-5, Secondary-0, Qualifier-3) |
| Size | 1.745 TB (`parted` reports the device as 1919 GB) |
| Parity size | 893.75 GB |
| **Strip size** | **64 KB** → a full stripe is **128 KB** of data |
| Sector size | 512 |
| State | **Optimal** |
| Default cache policy | WriteBack, ReadAhead, Direct, No Write Cache if Bad BBU |
| **Current cache policy** | **WriteBack**, ReadAhead, Direct, No Write Cache if Bad BBU |
| Access policy | Read/Write (current = default) |
| Disk cache policy | Disk's Default |
| Bad blocks | No |

### Physical drives

All three identical model, all `Online, Spun Up`, all `Media Type: Solid State
Device`, all `PD Type: SATA`, all `Secured: Unsecured` (**not** self-encrypting).

| | Slot 0 | Slot 1 | Slot 2 |
|---|---|---|---|
| Model | `MZ7GE960HMHP-000V3` | same | same |
| OEM part | `00FN363` / `00FN366` (**IBM**) | same | same |
| Serial | `90Y7O07V` | `90Y7I12A` | `90Y7I1K5` |
| Drive firmware | `CA35` | `CA35` | `CA35` |
| Raw size | 894.252 GB | 894.252 GB | 894.252 GB |
| Interface | SATA 3.1, 6.0 Gb/s (negotiated 6.0) | same | same |
| **Power-on hours** | **33,413 (3.81 yr)** | **35,562 (4.06 yr)** | **35,951 (4.10 yr)** |
| Total LBAs written | 101,442,285,399 → **51.9 TB** | 128,628,477,467 → **65.9 TB** | 144,340,854,404 → **73.9 TB** |
| Total LBAs read | 179,789,803,719 → **92.0 TB** | 413,022,741,319 → **211.5 TB** | 838,608,091,127 → **429.4 TB** |
| Reallocated sectors | **0** | **0** | **0** |
| Media / Other / Predictive errors | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| UDMA CRC errors | 0 | — | 0 |
| Temperature | 29 °C | 30 °C | 28 °C |
| Endurance attrs (173 / 231), normalized | — | — | 96 / 96 (≈96% remaining) |
| Reserved space (attr 170), normalized | — | — | 100 (full) |
| Power cycles | — | — | 69 |
| **TRIM support** | `Available, deterministic, zeroed` | same | same |

Note the read:write asymmetry in lifetime counters — 92/212/429 TB read against
52/66/74 TB written, while the *host* issues essentially zero reads to this array
under load (`r/s` measured 0.00 in every sample). Most of that read history
therefore predates this array rather than reflecting current RAID 5 behavior; the
write-amplification measurement below establishes that parity reads are not
happening now.

These are Samsung `MZ7GE`-family enterprise SATA SSDs — a 2013–2014 generation
part, carrying IBM OEM part numbers, i.e. they had a **prior life before this
array**. The 22 TB spread in lifetime writes between slot 0 and slot 2 can only
have accumulated before they were assembled into this RAID 5 set, where writes
land on all three roughly equally.

The drives are **not worn**: zero reallocations, full reserve space, ~96%
endurance remaining, cool. Whatever is limiting them, it is not wear-out.

### Partition layout of the virtual disk

```
 #      Start     End       Size    FS     Name / mount
 1      0.00GB    1.13GB    1.13GB  fat32  boot, esp
 2      1.13GB   35.5GB    34.4GB   ext4   old-gitlab-k8s
 3     35.5GB    170GB    134GB     ext4   new-gitlab-k8s
        170GB    701GB    531GB            *** Free Space (unpartitioned) ***
 4     701GB    1201GB    500GB     ext4   homelab-xubuntu   -> /        (sda4)
 5    1201GB    1919GB    718GB     ext4   /var/cache/ci-runner          (sda5)
```

`sda2` and `sda3` (168 GB combined) are named for a GitLab Kubernetes install
that is not part of this fleet. **531 GB is unpartitioned.** Together with
sda5's unused space, well over a terabyte of the array is idle.

## What was measured

### The disk is the constrained resource; CPU and RAM are not

Kernel **Pressure Stall Information** (`/proc/pressure/*`), which reports the
fraction of wall-clock time during which work could not proceed for want of a
resource. `some` = at least one task stalled; `full` = every runnable task
stalled, i.e. the machine accomplished nothing.

| Resource | `some avg300` | `full avg300` |
|---|---|---|
| **io** | **22.25%** | **21.70%** |
| cpu | 0.01% | **0.00%** |
| memory | 0.30% | 0.29% |

Per-cgroup, `kubepods.slice` (all CI pods): `full avg300` = **17.71%**. So about
four fifths of the host's total I/O stall is generated by CI itself.

Meanwhile `vmstat` during load shows CPU **74–85% idle** with **7–13 processes
blocked** in uninterruptible I/O wait.

**PSI is the right instrument here and `%util` is not** — see
`## Why %util misleads on this array`.

### All write traffic is on `/`; the cache volume is idle

Per-partition, 10-second interval under live CI load:

| Partition | Mount | Writes | `%util` |
|---|---|---|---|
| **sda4** | `/` | **2,630/s, 149 MB/s** | **99.96%** |
| sda5 | `/var/cache/ci-runner` | **0.00** | **0.00%** |

What is on `/`, measured:

| Path | Role | Size |
|---|---|---|
| `/var/lib/rancher/k3s/agent/containerd` | container image + snapshot store | **11 GB** |
| `/var/lib/rancher/k3s/storage` | local-path PVCs = every runner's work volume | **13 GB** |
| `/var/lib/rancher/k3s/server` | k3s server state | 318 MB |

k3s runs with the **default** `--data-dir` (`/var/lib/rancher/k3s`), and the
`local-path-config` ConfigMap still reads
`"paths":["/var/lib/rancher/k3s/storage"]`. Nothing was ever repointed at sda5.

### RAID 5 parity is costing near the theoretical minimum

Measured by sampling the **drives' own SMART lifetime counters** either side of a
90-second window of live CI load, and comparing against host-level writes to the
array over the same window. No synthetic load; no benchmark.

| | measured |
|---|---|
| Host wrote to the array | **12.68 GB** (141 MB/s) |
| Drives wrote, all three summed | **18.59 GB** |
| → **write amplification** | **1.47×** |
| Drives read, all three summed | **0.35 GB** |
| → drive reads per host write | **0.03×** |
| → **per-drive write throughput** | **~69 MB/s** |

A full-stripe write on 3-drive RAID 5 writes 2 data chunks plus 1 parity chunk
for 2 chunks of host data — a theoretical **1.5×**. The measured 1.47× is
essentially that floor, and the near-total absence of drive-level reads proves
**read-modify-write is not happening**: the 2 GB battery-backed write cache is
coalescing into full stripes exactly as designed.

The residual fact is that each drive is delivering only **~69 MB/s** — roughly
1,077 write IOPS at the ~64 KB chunk size the controller issues — against a part
whose sequential write rating is several times that. That gap is the open
question.

### TRIM has never reached these drives

| Check | Result |
|---|---|
| `/sys/block/sda/queue/discard_max_bytes` | **0** |
| `/sys/block/sda/queue/discard_max_hw_bytes` | **0** |
| Discards ever issued (`/proc/diskstats`) | **0** |
| `fstrim.timer` | **enabled**, active since 2026-08-12, firing weekly |
| `fstrim -v --dry-run /` | **"0 B trimmed"** |
| Drive-reported TRIM support | **`Available, deterministic, zeroed`** |

**The drives support TRIM; the RAID volume does not expose it.** In four years
and 52–74 TB of writes per drive, not one discard command has been issued.

Note the operational trap in the middle of that table: `fstrim.timer` is
enabled, reports healthy, runs weekly, and does **absolutely nothing**. A reader
checking "are we maintaining the SSDs?" gets a green answer that is false.

### The kernel issues no cache flushes, and that is correct

| Check | Result |
|---|---|
| SCSI `WCE` (write cache enable) on the VD | **0**, and marked **not changeable** |
| Flush commands issued, lifetime | **0** across **942,832,540** writes |
| `/sys/block/sda/queue/write_cache` | `write through` |

This is the correct configuration for a controller with a battery-backed cache,
not a defect — see the eliminated hypotheses below.

### Other queue state

`scheduler` = `[mq-deadline]`, `nr_requests` = 256, `max_sectors_kb` = 256,
`read_ahead_kb` = 512, `rotational` = **1** (the controller misreports this;
the drives are SSDs).

## Why `%util` misleads on this array

`%util` is the fraction of time at least one request was in flight. An array
that serves several requests concurrently keeps its queue non-empty under
almost any load, so `%util` saturates near 100% long before the array does. It
cannot distinguish "busy" from "full".

It is also violently window-dependent on a bursty workload. All of these are the
same device on the same afternoon:

| Window | `%util` |
|---|---|
| Since boot (13 days) | **15.05%** |
| One 3-second window, mid-burst | **39.9%** |
| One 5-second window, mid-burst | **97.10%** |
| 40 samples × 1.5 s under 15 runner pods | min 9.3, **p50 93.9**, p90 99.5, max 99.8 |

24 of those 40 samples exceeded 90%; 36 of 40 exceeded 50%; writes averaged
152.6 MB/s and peaked at 430.9 MB/s. **Quote the distribution, never a single
sample.** An earlier version of this analysis asserted "98.77% — the disk is
saturated" from one 2-second reading; that was a real number and an unsound
generalization.

**A related trap, worth stating because it cost a round of confusion:** `btop`
on this host is configured with `io_mode = false`, which makes the percentage in
its disk box **filesystem space used, not I/O**. It also computes space as
`(total − available) / total`, counting ext4's reserved blocks, so it reads
**14.9%** for `/` where `df` reports 10.3%. A "16% disk" in btop and a "97% util"
in iostat were never in conflict; they were never measuring the same thing.

## Hypotheses raised and eliminated

Recorded so they are not re-derived. Each was plausible; each is dead.

1. **"The drives are rotational."** `lsblk` reports `ROTA=1` and the device
   identifies as a `PERC H730P Mini`. **Wrong** — the RAID controller
   misreports rotational status. `smartctl -d megaraid,N` reports
   `Rotation Rate: Solid State Device` on all three.

2. **"The array is in write-through because the BBU is dead or learning."**
   `/sys/block/sda/queue/write_cache` reads `write through`. **Wrong on both
   counts.** The controller reports `Current Cache Policy: WriteBack`, and the
   BBU is `Optimal` / `isSOHGood: Yes` with no learn cycle. The sysfs string
   describes the **kernel's flush policy**: the VD advertises `WCE 0`,
   *not changeable*, which is exactly what a battery-backed controller should
   do — it tells the OS there is no *volatile* cache, so no flushes are needed.
   Confirmed by 0 flush commands across 942 million writes.

3. **"RAID 5 read-modify-write is the bottleneck."** The classic small-write
   parity penalty, 4 I/Os per logical write. **Wrong** — measured write
   amplification is **1.47×** against a 1.5× theoretical floor, and drive-level
   reads run at **0.03×** per host write. There is essentially no RMW. The
   write-back cache is doing its job.

4. **"A rebuild is running."** `megasasctl` prints `rbld:30%`, which reads like
   rebuild progress. **Wrong** — it is the controller's **Rebuild Rate
   setting**. The VD is `Optimal`, all three drives are `Online, Spun Up`, and
   `-PDRbld -ShowProg` reports "not in rebuild process" for each. Patrol Read is
   `Stopped` (Manual mode), and no consistency check is running.

## The open question

**Why does each drive deliver only ~69 MB/s of writes?**

The candidates, none yet eliminated:

- **FTL exhaustion from never receiving TRIM.** These drives had a prior life
  (IBM OEM parts; 22 TB of lifetime-write divergence that predates this array)
  and have never been trimmed. If a previous owner filled the LBA range, every
  flash block is "live" to the drive regardless of how the array is partitioned
  today, garbage collection has no free-block headroom, and internal write
  amplification eats the throughput. **Arguing against:** roughly 1.25 TB of
  this array's LBA space (531 GB unpartitioned plus ~717 GB unused in sda5) has
  never been written by *this* system, which — if the drives arrived clean —
  would leave a large free pool. Which of those is true is not currently known.
- **Drive generation and request shape.** A 2013-generation SATA SSD's rating is
  a *sequential* number. The controller issues ~64 KB chunk writes scattered
  across the stripe geometry; steady-state performance for that pattern on this
  part may simply be far below the headline figure.
- **Controller destage limits.** Sustained throughput past the 2 GB cache is
  governed by how fast the controller can retire stripes, which is not the same
  as what the drives can absorb.

**Do not choose a capacity `C`, or buy hardware, on the basis of a guess between
these three.** The first test below separates them for the cost of one command.

## The measurement plan

Tracked as **`livespec-s43svm.45`** on this plan's epic.

**Test 1 — the cheap discriminator. Run this first.**
During an idle window (no CI in flight), write a large file to
`/var/cache/ci-runner` — which is on the same array but currently receives zero
traffic — and measure sustained throughput with no competing load.

- Sustains **~400 MB/s or better** → the drives are healthy, and the ceiling is
  workload shape / drive generation / controller destage. The TRIM finding stays
  a long-term hygiene issue rather than the present cause.
- Crawls near **~70 MB/s with the host otherwise idle** → the drives are
  exhausted, over-provisioning is the fix, and no amount of RAID re-geometry
  will help until that is addressed.

One command, non-destructive, decides between the two live explanations before
anyone touches hardware.

**Test 2 — characterize the array (idle window only).**
`fio` against `/var/cache/ci-runner`, workload shaped like CI's real pattern
(many small files, high fsync rate, mixed write sizes), sweeping concurrency
upward. Plot achieved throughput **and** p99 completion latency against offered
concurrency; the **knee** is the array's ceiling. A single-point reading can
never show a knee — only the sweep can. This disturbs live jobs.

**Test 3 — decide `C`, which is a different question from Test 2.**
The number that matters is not device capability but **how many slots stop
helping**. Raise `C` stepwise, soak at each step against real traffic, and
measure PSI `io.full`, p50/p99 job queue-wait and wall-clock, and total
time-to-green for a full matrix. The ceiling is where added slots stop reducing
time-to-green while stall and latency climb. That definition is immune to
arguments about which device metric is correct.

Two operational constraints on Test 3, from `kueue/DERIVATION.md`: quotas must be
raised **before** capacity (Kueue borrowing is capped by the cohort's summed
nominal quota, not by node capacity — raise capacity first and the change is a
no-op), and every step needs a revert condition fixed in advance.

**Instrument first, cheaply.** `ci-runner-heartbeat.sh` already POSTs OTLP gauges
every five minutes to the local collector and on to the `livespec` Honeycomb
environment, and already emits `livespec.ci_runners.active` (slot occupancy).
Adding host and `kubepods.slice` `io.pressure full` as gauges is a few lines, and
turns the capacity question into a dataset drawn from real traffic — with no
synthetic load, no disruption, and a permanent capacity signal left behind.

## What would actually help

Ranked by gain per unit of disruption, given five free bays and an empty x16
slot. **None of these is a partition change** — see the next section.

1. **NVMe in the free PCIe x16 slot.** The bottleneck is as much IOPS as
   bandwidth: ~2,630 writes/s at ~56 KB average. A single enterprise NVMe device
   delivers hundreds of thousands of IOPS and multiple GB/s, bypasses the SATA
   links and the RAID controller entirely, and has working TRIM. Scratch does not
   need to be bootable.
2. **Populate free bays with a dedicated scratch VD.** Four drives in RAID 10
   gives roughly `N/2` × single-drive write with no parity and single-drive fault
   tolerance; RAID 0 gives roughly `N` × with none. RAID 0 is defensible for CI
   scratch specifically because the data is disposable — a failure costs a
   reprovision, not data. **Over-provision at creation**: build the VD from only
   ~70–80% of raw capacity and leave the rest unallocated, so that — with TRIM
   still unavailable — garbage collection retains permanent headroom. Without
   that step, new drives degrade into the same state; buying speed without
   fixing free-block headroom buys a few months.
3. **RAM-backed runner work volumes.** 118 GiB available with ~0.3% memory
   pressure. This is the option **robust to the open question**: it does not
   matter whether the ceiling is FTL, drives, or controller, because the I/O
   never reaches storage. Constraints: tmpfs counts against pod memory limits and
   node allocatable, and 16 concurrent runners × 5 Gi is 80 GiB worst case, so it
   needs an explicit cap and limit adjustments, and it scales with `C`.
4. **Strip size**, only if RAID 5 is kept. Current strip 64 KB → 128 KB full
   stripe, against a measured average host write request of 158 KB. A tuning
   knob, not an architecture change, and the parity measurement above says there
   is little left to win here.

**Secure-erasing a drive in place is not a viable path on this host.** The drives
are `Secured: Unsecured`, i.e. not self-encrypting, so MegaRAID's
`InstantSecureErase` is unavailable; ATA SECURITY commands are not exposed
through `megaraid_sas`; `blkdiscard` is refused because the volume advertises no
discard support; and the one erase MegaRAID does offer for non-SED drives is a
**pattern overwrite**, which writes every LBA and therefore makes every block
live — the exact opposite of restoring a free pool. Even setting the mechanics
aside, doing it live would mean running a degraded RAID 5 on an already-saturated
array, with zero redundancy for hours across 4-year-old drives, followed by a
full rebuild competing with CI.

If the existing array must be rebuilt, **drain first**. Emptying or deleting each
repository's `CI_RUNNER_LABELS` routes all CI back to hosted runners with no
specification change — the ratified "Availability MUST NOT become a merge
dependency" property, verified holding in
`post-cutover-conformance-audit.md`. That is what the fallback route exists for.

## What will NOT help, and why

**Growing `/` into `/var/cache/ci-runner`, or relocating k3s's data onto sda5,
will not improve throughput, latency, or IOPS.** `sda4` and `sda5` are partitions
of the *same* virtual disk, on the *same* three SSDs, behind the *same*
controller, sharing the *same* flash translation state. Moving a byte from one to
the other changes no physical property. SSDs have no geometry-based locality, so
there is no short-stroking effect to capture either. And because TRIM never
reaches the drives, filesystem-level free space is invisible to them regardless
of how it is divided.

**The relocation is still worth doing, for two non-performance reasons**, and the
design record already called for it. `design.md` §"Cache tiers, and the volume
that holds them" budgets the volume as "…**20 GB of container image store**, **50
GB of runner work directories**…" — precisely the 11 GB and 13 GB now sitting on
`/`. The reasons to move them anyway:

1. **Blast radius.** CI churn currently writes to the root filesystem. A runaway
   job that fills `/` takes down the whole host — OS and k3s included — not just
   CI. A dedicated filesystem contains that.
2. **It makes the real fix a mount change.** Once containerd and the PVC path
   live at a known mount point, moving them to different physical media (a new VD
   on the free bays, NVMe, or tmpfs) becomes a remount rather than a k3s
   reconfiguration.

The relocation was never performed for the k3s lane: `livespec-s43svm.2` was
originally titled "Relocate warm-overlay CI cache tier onto the dedicated
/var/cache/ci-runner volume" and was parked for the migration; when it was
re-scoped in 2026-08 it delivered a warm `uv` cache **on sda5** but did not move
containerd or the local-path provisioner. That half of its original intent is
still outstanding, and `.2` was closed without saying so.
