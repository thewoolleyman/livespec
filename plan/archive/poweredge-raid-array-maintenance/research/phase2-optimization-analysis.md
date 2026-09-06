# Phase 2 — workload-shaped measurement, and what to actually do about it

Measured 2026-08-28 with `fio` (installed this session) against the quiet array,
on `/var/cache/ci-runner`. Extends Phase 1, which used only large sequential
`dd` writes, to the request shapes CI actually issues.

**This note supersedes the Phase 2 option ranking in `plan-overview.md`, and it
CORRECTS one conclusion in `phase1-idle-throughput-measurement.md`.**

## Bottom line

Phase 1 concluded the drives are healthy and RAID 5's parity tax is "real but
small — measured 1.45–1.50×". **That is true for large sequential writes and
badly wrong for the workload CI actually runs.** Under small random writes this
array collapses to **~1,000 IOPS with p99 latency up to 2.1 seconds**. The
sequential number was measuring the case RAID 5 is good at.

So the optimization case is much stronger than Phase 1 implied — but the reason
is **RAID 5's read-modify-write penalty on small writes**, not drive
degradation. Both of these are now established:

- The drives are **not worn and not exhausted** (Phase 1, unchanged).
- The **array geometry is genuinely costly** for CI's request shape (this note).

**Recommendation: do both tiers.** Add a low-profile enterprise NVMe with
power-loss protection for the hot path (containerd + k3s PVC scratch), and
rebuild the SATA array as RAID 10 for the durable tier. NVMe is the
transformative change — 40–200× on the axis that hurts — while RAID 10 removes
the parity penalty from everything that stays on spinning-bay storage and keeps
redundancy. Neither requires believing anything about FTL state.

## The measurements

`fio`, O_DIRECT, `libaio`, 30 s time-based per point, on the idle array.

### A. Sequential 1 MB — concurrency sweep

| Jobs (× iodepth 8) | Bandwidth | p99 latency |
|---|---|---|
| **1** | **277.6 MB/s** | 114.8 ms |
| 2 | 197.0 MB/s | 187.7 ms |
| 4 | 174.8 MB/s | 329.3 ms |
| 8 | 136.2 MB/s | 918.6 ms |
| 16 | 163.9 MB/s | 1283.5 ms |

**The knee is at the very first point.** Peak sequential bandwidth is ~278 MB/s
at a single stream with queue depth 8; every added stream makes it *worse* while
latency climbs an order of magnitude. This is the RAID 5 signature: independent
sequential streams interleave at the controller, stop arriving as full stripes,
and degrade into read-modify-write.

This also reconciles the two Phase 1 numbers, which looked contradictory:
`dd` single-stream got 144 MB/s at queue depth 1; `fio` single-job at queue
depth 8 gets 278 MB/s. Queue depth, not stream count, is what this array
rewards.

### B. Random 4 KB — the case that matters

| Queue depth (× 4 jobs) | IOPS | Bandwidth | p99 latency |
|---|---|---|---|
| 1 | 4,610 | 18.0 MB/s | **4.8 ms** |
| 8 | 1,444 | 5.6 MB/s | **505 ms** |
| 32 | 1,061 | 4.1 MB/s | **1,116 ms** |
| 64 | 972 | 3.8 MB/s | **2,106 ms** |

**Throughput goes DOWN as queue depth goes up, and p99 latency reaches 2.1
seconds.** This is the clearest result in the whole plan. At queue depth 1 the
battery-backed cache absorbs everything (4,610 IOPS, 4.8 ms). Past what the
cache can absorb, every small random write costs four physical I/Os — read the
old data, read the old parity, write the new data, write the new parity — and
the array falls to roughly a thousand IOPS with multi-second tail latency.

A build step that fsyncs many small files does not experience this as "slow
disk". It experiences it as multi-second stalls.

### C. CI-shaped — 64 KB writes, fsync on every write

| Jobs | IOPS | Bandwidth | p99 latency |
|---|---|---|---|
| 1 | 1,111 | 69.4 MB/s | 0.23 ms |
| **4** | **1,610** | **100.6 MB/s** | 5.4 ms |
| 16 | 1,520 | 95.0 MB/s | 16.3 ms |

**The array's practical CI ceiling is ~1,600 IOPS / ~100 MB/s**, reached at 4
concurrent writers and flat thereafter. Latency stays low because the BBU cache
absorbs the fsyncs — this is the configuration working as designed, and it is
why CI feels acceptable rather than catastrophic despite result B.

Compare the characterization's real-CI figure of ~2,630 writes/s at ~56 KB
average. That exceeds this ceiling because real CI writes go through the page
cache and get coalesced, whereas these are O_DIRECT. Both numbers are correct;
they measure different things.

## Correction to the Phase 1 note

`phase1-idle-throughput-measurement.md` §"Consequence for Phase 2" says:

> **RAID 5's parity tax is real but small** — measured 1.45–1.50×, at the
> theoretical floor, with no read-modify-write. Re-geometry alone recovers at
> most that factor; it is not where the big win is.

**Scope that claim to large sequential writes.** It was measured with 1 MB
sequential `dd`, where full-stripe writes make the parity cost exactly the 1.5×
floor and read-modify-write genuinely does not occur. Result B above shows that
for small random writes the same array pays roughly **4× write amplification**
and loses an order of magnitude of throughput. "Re-geometry is not where the big
win is" is therefore wrong for CI's actual workload; on small writes, re-geometry
is worth roughly 2–3×.

Everything else in the Phase 1 note stands, including the elimination of the
FTL-exhaustion hypothesis — that conclusion rested on the cache-burst shape, the
non-decaying steady state, and the concurrency response, none of which this note
disturbs.

## Options, re-ranked against this data

### 1. Enterprise NVMe for the hot path — the transformative change

A single modern enterprise NVMe delivers **200,000–1,000,000 random write IOPS**
and 1–7 GB/s, against this array's measured ~1,000–1,600. That is **two to three
orders of magnitude on the exact axis that is failing**, and it eliminates the
multi-second tail latency rather than reducing it.

It also bypasses the PERC entirely, which means **TRIM works natively** — the
hygiene problem the characterization documented (four years, zero discards ever
issued) simply does not exist on this tier.

Target it at `containerd`'s image/snapshot store and the k3s local-path PVC
root — the 11 GB + 13 GB the characterization measured, and the only paths that
receive CI write traffic.

**Purchasing constraints, both easy to get wrong (see the Phase 0 note):**
- **Low-profile / half-height card.** The chassis is 1U. The "Length: Long"
  field on Slot 1 refers to length, not height.
- **Power-loss protection (PLP) is a priced trade-off, not a precondition** —
  an earlier revision wrongly called it mandatory. See "Mixing SATA
  and NVMe" below — this is the single most important requirement.

### 2. RAID 10 for the durable tier — meaningful, and bounded

Rebuilding as RAID 10 removes the parity penalty: a random write costs **2**
physical I/Os instead of 4. Combined with more spindles, the projection is:

| Configuration | Random-write I/O cost | Rough projection vs today |
|---|---|---|
| Today: RAID 5, 3 drives | 4 I/O per write | baseline (~1,600 IOPS CI-shaped) |
| RAID 10, 4 drives | 2 I/O per write | ~2.5–3× |
| RAID 10, 8 drives | 2 I/O per write | ~5× |

These are **projections from the I/O-cost model, not measurements** — the BBU
cache complicates the arithmetic, and the honest range is wide. They are good
enough to rank options and not good enough to promise a number.

The bound worth stating plainly: **these are 2013-generation SATA SSDs**
delivering ~72 MB/s single-stream each. Even eight of them in RAID 10 lands
somewhere around 300–500 MB/s sequential and perhaps 8,000–15,000 random IOPS.
That is a real improvement and it is still one to two orders of magnitude short
of a single NVMe.

**RAID 10 needs an even drive count ≥ 4.** Five bays are free, three are
populated. So 4 drives (one purchase, one bay left spare) or 8 drives (five
purchases, chassis full) are the sensible configurations.

**Drive-type recommendation if buying:** enterprise/datacenter SATA SSDs with
power-loss protection and ≥ 1 DWPD endurance, matched capacity, ideally matched
model. Mixing a modern SATA SSD with the existing 2013-generation parts in one
RAID 10 set works, but the array runs at the **slowest** member's speed, so
pairing new drives with the old ones discards most of what the new ones offer.
If the budget allows only a partial refresh, prefer **four new drives as a
separate RAID 10 VD** over eight mixed drives in one.

**Destroy + recreate is REQUIRED — this is now confirmed, not assumed.**
`perccli64` (installed 2026-08-28) reports `Reconstruction = Yes` on this
controller, but RAID 10 is a *spanned* array and MegaRAID's reconstruction
matrix moves VDs between single-span levels only (RAID 5 → RAID 0 or RAID 6,
and nothing else). Spans are built at VD-creation time. See
`phase0-controller-management-and-tooling.md` §"On RAID 5 → RAID 10
specifically" for the full matrix and the evidence.

**Consequence: if RAID 10 is chosen, Phases 3–5 (backup, verify the backup,
prove the CI fallback) become mandatory prerequisites rather than
precautions** — the array's data does not survive the change.

### 3. tmpfs for runner work volumes — free, and available now

111 GiB of RAM is available at ~0.3% memory pressure. I/O to a tmpfs never
reaches storage at all, so it is immune to every question in this document. It
costs nothing and needs no hardware.

Constraints: tmpfs counts against pod memory limits and node allocatable, it is
volatile across reboots, and it scales with concurrent runner count — so it needs
an explicit cap. Worth doing regardless of what else is chosen, and it is the one
option available before any purchase.

### 4. Strip-size tuning — do not bother

Current 64 KB strip / 128 KB full stripe against a measured ~158 KB average host
write. Result A shows the sequential path is not where the loss is, and result B
shows the random path's problem is parity itself, which no strip size fixes.

### 5. Full wipe purely to reset FTL state — REMAINS UNJUSTIFIED

Phase 1 eliminated the premise. Nothing in this note revives it. If the array is
rebuilt for RAID 10, over-provision at creation (build the VD from ~70–80% of raw
capacity) as cheap insurance given TRIM can never reach these drives through the
PERC — but that is a rider on a rebuild done for another reason, not a reason.

## Mixing SATA and NVMe — the implications

Asked directly, and the answer has one structural fact and several operational
consequences.

### The structural fact: they cannot share an array

The PERC H730P manages SAS/SATA devices only. An NVMe drive is a PCIe endpoint
and is **invisible to the PERC**. There is no such thing as a hardware RAID set
spanning both. They are necessarily **separate storage tiers**, not a mixed
array — and that is a feature, because it means adding NVMe cannot destabilize
the existing array.

Linux software RAID (`mdadm`, LVM, btrfs, ZFS) *can* span both, but striping or
mirroring a 200,000-IOPS device with a 1,000-IOPS array drags the pair to the
slow device. **Do not do this.** The one legitimate mixed-tier construction is
**caching** rather than RAID — `lvmcache`, `bcache`, or `dm-writecache` placing
NVMe in front of the SATA array. That is a real option if a single unified
namespace is wanted, at the cost of a more complex failure story. For this host,
plain separate mounts are simpler and better: CI's hot paths are already
identifiable directories.

### Power-loss protection — the one that can lose data

This is the most important consequence and the easiest to get wrong.

The SATA array's write cache is protected by the PERC's **battery-backed unit**
(verified Optimal, `isSOHGood: Yes`). That is what makes it safe for the
controller to advertise `WCE 0` and for the kernel to issue zero flushes across
942 million writes — the characterization documented this and correctly
identified it as right, not broken.

**An NVMe drive gets no such protection from the host.** It must provide its own,
onboard, in the form of power-loss-protection capacitors. Enterprise/datacenter
NVMe has PLP; **consumer NVMe (e.g. Samsung 9xx Pro, WD Black) does not.** On a
consumer part, a power loss can lose writes the drive has already acknowledged as
durable — and this host runs k3s, whose etcd state assumes fsync means fsync.

**This is a priced trade-off for the maintainer, NOT a precondition.** An
earlier revision of this note called enterprise NVMe with power-loss protection
a "hard requirement". **That was an assumption, and it was wrong** — it imported
a production risk posture onto a machine the maintainer has since confirmed is
**not production**: a rebuildable CI host with backups.

The technical fact stands and is worth stating precisely: on power loss, a
consumer NVMe can lose writes it has already acknowledged as durable, and k3s's
etcd state assumes fsync means fsync. What changes is the **consequence**. On
this host that is a reprovision from backup — annoying, bounded, and exactly what
Phases 3–4 exist to make cheap — rather than lost production data.

So the honest framing is a cost comparison, not a rule: consumer NVMe is
materially cheaper and delivers essentially the same performance; the premium
buys protection against a failure mode whose cost here is a restore. Note also
that **used enterprise NVMe** often undercuts new consumer parts while retaining
power-loss protection, which can make the trade-off moot. Surface all three as
priced options and let the maintainer choose.

### Boot

The host is **UEFI** (confirmed), so booting from NVMe is *architecturally*
possible. But 13th-generation PowerEdge firmware support for booting from an
add-in NVMe card is inconsistent, and this is not a question worth taking risk
on. **Keep boot and the OS on the PERC array; use NVMe purely as a data/scratch
mount.** That sidesteps the question entirely and costs nothing, since the whole
point is to move CI churn off `/`, not to move the OS.

### Physical and thermal

- **Slot 1 (x16) is free**, and a low-profile NVMe AIC fits.
- **Slot 2 holds only a Radeon Cedar display adapter.** If a mirrored NVMe pair
  is wanted, that card is the obvious thing to remove — it provides console video
  on a host managed over the network. This frees a second slot at zero cost.
- **Fan behavior is a known 13th-gen PowerEdge trap.** iDRAC ramps chassis fans
  based on recognised thermal sensors; a third-party PCIe card it does not
  recognise commonly produces either a loud unconditional fan ramp or no ramp at
  all. Plan to check fan behavior and NVMe temperature after installation rather
  than assuming, and note that 1U airflow over an AIC is limited.

### TRIM, monitoring, and redundancy asymmetries

- **TRIM works on NVMe** and never will through the PERC. The `fstrim.timer`
  trap the characterization documented — enabled, weekly, reporting healthy,
  trimming exactly zero bytes — will start doing real work for the NVMe mount
  while remaining a no-op for the array. Both facts will be true simultaneously
  on the same host, which is worth writing down before it confuses someone.
- **Monitoring differs.** The array needs `smartctl -d megaraid,N`; NVMe needs
  `nvme smart-log` (`nvme-cli` now installed). Any health check must cover both.
- **A single NVMe has no redundancy.** For disposable CI scratch that is
  defensible — a failure costs a reprovision, not data. For anything durable,
  mirror two NVMe devices with `mdadm` RAID 1. Note the array keeps its own
  redundancy independently, so the OS survives an NVMe failure either way; what
  a single NVMe risks is an interrupted CI run, not the host.

## Recommended target architecture

1. **NVMe (low-profile)** in Slot 1 → `containerd` image store
   + k3s local-path PVC root. Mount-point based, so it is a remount rather than
   a k3s reconfiguration later.
2. **SATA array rebuilt as RAID 10**, over-provisioned at creation → OS, k3s
   server state, durable data. Redundant, and free of the parity penalty for
   whatever small writes remain.
3. **tmpfs** for the most disposable runner scratch, capped explicitly — do this
   first, since it needs no purchase and no downtime.

This ordering also degrades gracefully: item 3 is free and immediate, item 1 is
one part and one slot, and item 2 is the only one requiring the full
backup/fallback/destructive sequence in Phases 3–7.
