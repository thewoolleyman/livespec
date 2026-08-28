# Buying one drive for RAID 10, versus optimizing the three we have

The specific question asked 2026-08-28: what does it cost and what does it buy
to purchase **a single appropriate drive** (enterprise, Dell-official, fitting,
≥960GB usable) to complete a **4-drive RAID 10**, compared with keeping the
three existing drives and doing the best available without spending?

## Bottom line

**The performance case for RAID 10 is narrower than it first looks, and the
reliability case is stronger.**

A 4-drive RAID 10 gives **the same sequential write throughput and the same
usable capacity** as the current 3-drive RAID 5. What it actually buys is
**~2.7× random write**, ~1.3× read, and — the argument that carries more weight
on 4-year-old drives — a **dramatically safer rebuild**.

But it costs a **full destroy-and-recreate cycle** (Phases 3–7: backup, verify,
CI fallback, rebuild, restore), because RAID 5 → RAID 10 cannot migrate in
place. That is hours of downtime and real risk, for a drive that costs on the
order of a couple of hundred dollars.

**Recommendation: do the free optimization first, and treat the drive purchase
as a separate, later decision made on reliability grounds rather than
performance grounds.** tmpfs removes the hot path from storage altogether, which
is a bigger win for CI than 2.7× random write, costs nothing, and needs no
downtime. If the array is later rebuilt anyway — for a drive failure, or because
the backup infrastructure from Phases 3–5 exists and makes it cheap — that is
the moment to add the fourth drive and switch to RAID 10.

## The arithmetic

Let **D** = one drive's throughput. Both configurations use 894 GiB drives.

| | RAID 5, 3 drives (current) | RAID 10, 4 drives | Change |
|---|---|---|---|
| **Usable capacity** | 2 × 894 GiB = **1,788 GiB** | 2 × 894 GiB = **1,788 GiB** | **none** |
| Random write I/O cost | 4 physical I/O per write | 2 physical I/O per write | — |
| **Random write throughput** | 3D / 4 = **0.75 D** | 4D / 2 = **2.0 D** | **2.67×** |
| **Sequential write** | 3D × 2/3 = **2.0 D** | 4D × 2/4 = **2.0 D** | **1.00× — none** |
| **Read** | 3 D | 4 D | 1.33× |
| Survives 1 drive failure | yes | yes | — |
| Survives 2 drive failures | no | only if in different mirrors (2 of 3 cases) | better |
| **Rebuild reads** | **every sector of both survivors** | **only the mirror partner** | much safer |

Two results here are worth stating plainly because they are counter-intuitive:

- **Capacity is identical.** Three drives in RAID 5 and four in RAID 10 both
  yield two drives' worth of usable space. The fourth drive buys no capacity.
- **Sequential write does not improve at all.** RAID 5 writes 2 data chunks per
  3 physical writes; RAID 10 writes 2 per 4 but across 4 spindles. They land on
  the same 2 D. The measured ~278 MB/s sequential peak would not move.

So the entire performance case rests on **random write**, which is exactly the
axis where the measurement is now known to be uncertain — see below.

## The complication: the random-write baseline is uncertain

`phase2-measurement-correction-and-free-optimization.md` records that the
earlier random-write figures were measured cold and are pessimistic by roughly
7×: the same test warmed gives ~10,400 IOPS rather than ~1,400.

This matters directly here. **2.67× applied to a number that is itself uncertain
within a factor of seven is not a solid basis for a purchase.** The honest
position:

- If CI's real behavior is closer to the **cold/large working set** case
  (~1,400 IOPS), the array is genuinely constrained and 2.67× is meaningful.
- If it is closer to the **warm** case (~10,400 IOPS), the array is already
  comfortable at CI's measured demand of ~2,630 writes/s, and 2.67× buys
  headroom nobody is currently using.

**Resolving this costs nothing and needs no purchase**: instrument the real
workload rather than benchmarking a synthetic one. The characterization already
notes that `ci-runner-heartbeat.sh` POSTs OTLP gauges every five minutes, and
that adding host and `kubepods.slice` `io.pressure` as gauges is a few lines.
Doing that first turns this question into a dataset drawn from real traffic —
and leaves a permanent capacity signal behind.

## The reliability case, which is the stronger one

The three drives are **4+ years old** — 33,451 / 35,562 / 35,951 power-on hours.
They are healthy today (zero reallocated sectors, ~96% endurance remaining, full
reserve space), so nothing is imminent. But the failure mode matters:

- **A RAID 5 rebuild reads every sector of both surviving drives** and
  recomputes parity. On aging drives that is a hours-long full-surface stress
  read, during which a second failure — or a single unrecoverable read error —
  destroys the array.
- **A RAID 10 rebuild copies one mirror member.** It reads one drive, finishes
  faster, and a read error costs one block rather than the whole array.

Scale honestly: across ~1.8 TB of rebuild reads at enterprise-SSD URE rates
(~1 in 10¹⁶–10¹⁷ bits), the probability of hitting a URE during a RAID 5 rebuild
is roughly **0.1–1%**. That is low — the "RAID 5 is dead" argument is much
stronger for large spinning disks than for healthy SSDs — but it is not zero,
and it compounds with the chance of a second drive failing during the window.

**If the drive is bought, buy it for this**, not for the 2.67×.

## A third option worth naming: a separate single-drive volume

A fourth drive does **not** have to go into a RAID 10. It could instead be added
as its **own single-drive virtual disk** for CI scratch. This has one large
practical advantage: **no destroy-and-recreate.** The existing VD is untouched,
so there is no backup gate, no restore, and no downtime beyond hot-plugging the
drive and creating the VD online with `perccli`.

But it is **not clearly faster**, and the reason is easy to miss:

| | 3-drive RAID 5 (shared) | single dedicated drive |
|---|---|---|
| Sequential write | 2.0 D | **1.0 D — worse** |
| Random write | 0.75 D, shared with OS | 1.0 D, dedicated |
| Redundancy | survives 1 failure | **none** |

A single drive is **worse sequentially than the three-drive array** and only
modestly better on random writes. Its real benefit is **isolation** — CI I/O
stops contending with OS and k3s I/O, and a runaway job cannot fill `/`. That is
worth something, but tmpfs delivers the same isolation for free and with far
better performance.

**So: worth knowing, not worth recommending over tmpfs.** It becomes interesting
only if the scratch working set is too large for RAM.

## Cost

Drive pricing is in `phase2-pricing-comparison.md`; a focused pricing pass for a
single ~960GB Dell-official enterprise SATA SSD was commissioned and its result
should be recorded here when it lands. Expect the order of **one used enterprise
960GB SATA SSD plus one genuine Dell G176J caddy (~$19.99)**, with a premium for
Dell-branded over generic.

The Dell-branded premium buys one concrete thing: non-Dell drives work fine on
the H730P but are flagged "non-certified" in OMSA/iDRAC, which leaves **iDRAC
health permanently amber** and can reduce predictive-failure alerting. On a
rebuildable lab host that is largely cosmetic — but a permanently-amber health
indicator is a real cost, because it trains you to ignore the indicator.

**The dominant cost is not the drive.** It is the destroy-and-recreate cycle
RAID 10 requires: backup (Phase 3), verify the backup (Phase 4), prove the CI
fallback (Phase 5), rebuild (Phase 6), restore and verify (Phase 7). Those
phases have to happen anyway before any destructive work, but they are hours of
effort and carry the risk inherent in restoring a system from backup.

## Recommendation

1. **Now, free:** tmpfs for runner work volumes, and relocate containerd + the
   PVC root off `/`. This addresses the hot path better than any single-drive
   purchase can, with no downtime and no risk.
2. **Now, free:** add host and `kubepods.slice` `io.pressure` gauges to the
   existing heartbeat, so the cold-versus-warm question is answered from real
   traffic instead of synthetic benchmarks.
3. **Later, on reliability grounds:** if and when the array is rebuilt — because
   a drive fails, or because the Phase 3–5 backup infrastructure exists and
   makes a rebuild cheap — add the fourth drive and build RAID 10 then. The
   safer rebuild path is the durable argument; the 2.67× random write is a
   bonus.
4. **Do not** buy the drive *in order to* trigger a rebuild. The performance
   case does not justify the destructive cycle on its own, and step 2 may show
   the array was never the constraint at CI's actual demand.
