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

**Recommendation: do the free optimization first, and buy the drive as a COLD
SPARE rather than as a RAID 10 trigger.** tmpfs removes the hot path from
storage altogether, which is a bigger win for CI than 2.7× random write, costs
nothing, and needs no downtime. Separately, at **$226 all-in** (Dell-branded,
tray included — the Dell option turns out to be the *cheapest* sane one) a
fourth drive earns its keep immediately as insurance against a failure on 4-year-old
drives, without touching the array or committing to anything. If the array is
later rebuilt anyway — for a drive failure, or because the Phase 3–5 backup
infrastructure exists and makes it cheap — that is the moment to switch to
RAID 10, using the spare already on the shelf.

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

## Cost — priced 2026-08-28

**The headline result is that the Dell-branded option and the cheapest sane
option are the same purchase.**

| Option | Drive | Caddy | **All-in** | Stock |
|---|---|---|---|---|
| **Dell G13 `0X31G3`** (Intel D3-S4610, 960GB, 3 DWPD MU), refurb — **G176J tray included** | $226.00 | in box | **$226.00** | **60 units**, 3yr warranty, 100% health |
| Samsung PM853T `MZ7GE960HMHP` — **exact match to the existing drives**, bare | $139.00 | $19.99 | **$158.99** | **1 unit only** |
| Samsung PM863a `MZ7LM960HMJP`, bare | $174.00 | $19.99 | **$193.99** | 18 units |
| Micron 5300 MAX (5 DWPD), bare | $209.00 | $19.99 | $228.99 | 45 units |
| Dell-branded **new** | $1,545.95 | — | **$1,565.94** | 1 unit, ships the *wrong-generation* `DXD9H` tray |

At $226 with the correct tray bundled, **the Dell-branded premium is effectively
$32** over the nearest generic-with-stock (PM863a + caddy at $194) — not the
four-figure gap the new-channel prices imply. What that $32 buys, factually:

- A drive without Dell firmware is detected by the PERC as non-certified and
  raises an advisory in iDRAC/OMSA that, per Dell's community documentation,
  **cannot be dismissed** — it puts the storage subsystem in a permanent warning
  state rather than OK. That is a real cost, because it trains you to ignore the
  health indicator.
- Dell's predictive-failure reporting and the DUP/Lifecycle-Controller firmware
  update path only apply to Dell-firmware drives.
- Non-Dell drives generally do work; scattered reports exist of third-party SSDs
  being dropped offline, but that is anecdotal, not a documented incompatibility.

Genuine new Dell **G176J caddies remain $19.99** at ServerPartDeals (60 in
stock) — the earlier pricing note's figure is confirmed still current.

### Purchasing traps, checked

- **SAS masquerading as SATA is live at this exact price point.** The same
  search returns a Seagate Nytro 3350 960GB **SAS 12Gb/s at $219** — $10 above
  the SATA Micron, identical to the SATA PM883. Nothing in the price flags it,
  and **the G176J tray is itself marketed as "SAS/SATA"**, so the tray's
  description tells you nothing about the drive. Confirm the interface on the
  drive's own spec block.
- **Several "960GB SATA" Dell SKUs are 3.5"/hybrid-carrier parts** that will not
  fit an R630's 2.5" SFF bay — `345-BECI`, `089Y1`, `0089Y1`, `Y1KT5`,
  `400-ATED` — and they appear in the same searches at the same ~$226. Buy only
  2.5" parts.
- **Never substitute an "800GB" drive.** 800,166,076,416 B = 745 GiB, well below
  the 894 GiB floor. The correct 960GB capacity point is 960,197,124,096 B =
  **894.25 GiB**, clearing the existing drives by ~0.25 GiB.
- **Verify the LBA count on arrival**, before committing the drive to the array.
  The H730P's default coercion mode was not confirmed, so do not assume it gives
  tolerance for a marginally smaller drive.

### What the pricing does NOT cover

**eBay is entirely unmeasured** — it blocked every fetch method available. The
private-seller used market is normally the cheapest tier and usually below
dealer pricing, so **the $139–226 figures above are DEALER prices and should be
read as an upper bound**. A hand-check on eBay would likely find a lower floor.

Also unverified: Dell.com's own price (403s every fetch), and one $1,350
"for 11th/12th/13th Gen" listing whose own compatibility table names no 13G
machine — a contradiction that was not resolved.

**Inventory itself is a finding.** Across ServerPartDeals' entire 960GB SATA
2.5" catalogue, **every in-stock unit is "Seller Refurbished"** — not one New or
Manufacturer-Recertified drive is transactable. That is the NAND shortage
showing up as availability, not merely as price, and it argues for buying while
stock exists rather than assuming the option stays open.

## The dominant cost is still not the drive

At $226 the part is cheap. **The expensive thing is the destroy-and-recreate
cycle RAID 10 requires** — backup (Phase 3), verify (Phase 4), prove the CI
fallback (Phase 5), rebuild (Phase 6), restore and verify (Phase 7). Those
phases must happen before any destructive work regardless, but they are hours of
effort and carry the risk inherent in restoring a system from backup.

## The purchase has value that does NOT require a rebuild

This reframes the decision, and it is the strongest argument for buying now:

**A fourth 960GB drive is immediately useful as a COLD SPARE for the existing
RAID 5, with no rebuild, no downtime, and no commitment to RAID 10 at all.**

The three drives are 4+ years old at 33,000–36,000 power-on hours. If one fails,
the array runs **degraded** — and a degraded RAID 5 has zero redundancy — until
a replacement ≥894 GiB physically arrives. Having a matching drive on the shelf
turns that window from *days of shipping while unprotected* into *minutes*.
Given that a RAID 5 rebuild is itself the risky operation (it reads every sector
of both survivors), shortening the degraded window is worth real money.

So the $226 buys three things at once:

1. **Insurance now** — a cold spare against a failure on aging drives, usable
   the day it arrives, requiring nothing.
2. **Optionality later** — the fourth drive RAID 10 needs, if and when a rebuild
   happens for any reason.
3. **Availability** — locking in a correct-generation Dell part with the right
   tray while 60 units exist, in a market where new inventory has vanished.

None of that requires deciding about RAID 10 today, and none of it requires
touching the running array.

## Recommendation

1. **Now, free:** tmpfs for runner work volumes, and relocate containerd + the
   PVC root off `/`. This addresses the hot path better than any single-drive
   purchase can, with no downtime and no risk.
2. **Now, free:** add host and `kubepods.slice` `io.pressure` gauges to the
   existing heartbeat, so the cold-versus-warm question is answered from real
   traffic instead of synthetic benchmarks.
3. **Buy the drive now — as a COLD SPARE, not as a RAID 10 trigger.** At $226
   all-in for the Dell G13 `0X31G3` with the G176J tray included, it is
   immediately useful the day it arrives: it shortens the degraded-array window
   after a failure from days-of-shipping to minutes, on drives that are 4+ years
   old. It commits to nothing, touches nothing, and needs no downtime. It also
   happens to be exactly the drive RAID 10 would need later. Availability is the
   time pressure, not performance: every in-stock 960GB SATA unit at the
   surveyed dealer is now refurbished, with no new inventory transactable.
4. **Later, on reliability grounds:** if and when the array is rebuilt — because
   a drive fails, or because the Phase 3–5 backup infrastructure exists and
   makes a rebuild cheap — build RAID 10 then, using the spare bought in step 3.
   The safer rebuild path is the durable argument; the 2.67× random write is a
   bonus.
5. **Do not** buy the drive *in order to* trigger a rebuild. The performance
   case does not justify the destructive cycle on its own, and step 2 may show
   the array was never the constraint at CI's actual demand. Buying it as a
   spare is a different decision with a different justification, and it does not
   obligate the rebuild.
