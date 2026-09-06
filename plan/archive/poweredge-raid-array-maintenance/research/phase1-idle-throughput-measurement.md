# Phase 1 — idle write-throughput measurement, and what it settles

Measured 2026-08-28T00:04Z–00:17Z on `poweredge-xubuntu` against a genuinely
quiet array, executing the Phase 1 discriminator specified in
`plan-overview.md`. This note records what was run, what came back, and which
of the three candidate explanations in `storage-io-characterization.md`
§"The open question" survive.

**Read this before choosing a Phase 2 option or costing any hardware.**

## Bottom line

**The ~69 MB/s-per-drive figure is not a symptom of CI contention, and it is
not FTL exhaustion. It is close to this array's real single-stream ceiling,
and the array is healthy.** An idle, single-stream, sequential, O_DIRECT write
to the *empty, never-CI-written* cache volume reached ~144 MB/s host / ~72 MB/s
per drive — statistically the same figure the characterization measured under
full concurrent CI load (141 MB/s host / 69 MB/s per drive).

But concurrency does buy real throughput: **four parallel streams reached
~238 MB/s host / ~120 MB/s per drive**, a 1.65× gain over one stream, at the
cost of 3× write latency. So the array was never "saturated at 141 MB/s" — CI's
observed rate is close to what a *single* stream gets, and the device has more
to give under queue depth.

This kills the FTL-exhaustion hypothesis (which predicted the *opposite* result
on this exact test) and reframes the problem: the constraint is a modest,
healthy per-device ceiling plus RAID 5's parity tax, not degradation needing
TRIM.

## Method

Executed over `ssh poweredge-xubuntu` (user `cwoolley`, passwordless sudo).

**Quiet-array precondition, verified before writing** — `iostat` showed `sda`
at 0.00 writes/s across samples; PSI `io` `avg10`/`avg60` = **0.00**; `vmstat`
showed 0 blocked processes; `kubectl get pods -A` showed only idle ARC listener
pods, zero running CI jobs. The `ci-warm-cache` cronjob fires ~every 30 min and
had run 3 min earlier, so the tests ran inside a clear window.

**Target** — `/var/cache/ci-runner` (`sda5`): same three SSDs, same controller,
same flash translation state as `/`, but ~1.2 GB used of 658 GB and receiving
zero CI traffic. This is what makes it a clean probe of device capability.

**Instrument** — `dd ... oflag=direct conv=fsync` (O_DIRECT bypasses the page
cache so the measurement is of the device, not RAM; `conv=fsync` forces the
final flush), sized **32 GiB** — far past the controller's 2 GB battery-backed
cache, so the sustained rate past the cache burst is what the average reflects.
Per-second `iostat -dxy 1` ran concurrently for the throughput *curve*, and
per-drive SMART attribute 241 (`Total_LBAs_Written`, read via
`smartctl -d megaraid,N`) was sampled either side of each run to compute
write amplification from the drives' own counters. Scratch files were deleted
after each run.

`fio` is **not installed** on this host and was deliberately not installed;
`dd`+`iostat`+`smartctl` answer the Phase 1 question with zero package changes.
A `fio` sweep remains the right tool for the Phase 2 knee-finding sweep if one
is still wanted — see "What this does not settle".

## Results

### Test A — one stream, 32 GiB, O_DIRECT sequential

| | |
|---|---|
| `dd` reported | 34.36 GB in **191.2 s** = **180 MB/s** (includes the opening cache burst) |
| Steady-state host rate (last `iostat` samples) | **~144 MB/s** |
| Opening burst (first 1 s sample) | **~1,535 MB/s** — the 2 GB write-back cache absorbing |
| Drives wrote (SMART Δ, summed) | 16.60 + 16.60 + 16.60 = **49.8 GB** |
| **Write amplification** | **1.45×** (RAID 5 3-drive full-stripe floor is 1.50×) |
| **Per-drive steady throughput** | **~72 MB/s** |
| `w_await` steady | ~4.0–4.3 ms |
| `aqu-sz` | ~3.0 |
| `%util` | ~88–91% |

The curve shape matters: a ~1.5 GB/s first second, decaying over ~5 s, then
flat at ~144 MB/s for the remaining ~185 s. That is exactly the signature of a
healthy write-back cache absorbing a burst and then destaging at device speed.
There is no downward drift over the run — no sign of garbage collection
progressively choking.

### Test B — four parallel streams, 8 GiB each (32 GiB total)

| | |
|---|---|
| Per-stream `dd` | 8.59 GB in **144.0 s** = **60 MB/s** each (all four within 0.2 s of each other) |
| **Aggregate host rate** | **~238 MB/s** (4 × 60; `iostat` mid-run samples ~212–325 MB/s, consistent) |
| Drives wrote (SMART Δ, summed) | 17.24 × 3 = **51.7 GB** |
| **Write amplification** | **1.50×** (exactly the theoretical floor) |
| **Per-drive throughput** | **~120 MB/s** |
| `w_await` | ~11–17 ms (**3–4× Test A**) |
| `aqu-sz` | ~17.5–18.1 (**6× Test A**) |
| `%util` | ~85–90% |

Note the `wall=400s` line in the raw capture is a **script artifact** — the
`wait` also waited on the 400-sample background `iostat` logger, not just the
writers. The true write duration is the 144.0 s the four `dd` processes each
reported. Any aggregate computed from 400 s (≈82 MB/s) is wrong; the correct
aggregate is ~238 MB/s.

### The comparison that answers the question

| Condition | Host write | Per drive | Queue depth | `w_await` | WA |
|---|---|---|---|---|---|
| Real CI load (characterization, 2026-08-26) | 141 MB/s | ~69 MB/s | — | — | 1.47× |
| **Idle, 1 stream, empty volume** | **~144 MB/s** | **~72 MB/s** | ~3 | ~4 ms | 1.45× |
| **Idle, 4 streams, empty volume** | **~238 MB/s** | **~120 MB/s** | ~18 | ~13 ms | 1.50× |

## What this settles

Against `storage-io-characterization.md` §"The open question", which listed
three candidates:

1. **FTL exhaustion from never receiving TRIM — ELIMINATED.** This test was
   designed as its discriminator, and it produced the disconfirming outcome.
   Exhaustion predicts that a write to *any* LBA is slow because every flash
   block is live; it predicts no difference between the CI-hammered `/` and the
   pristine `sda5`, and it predicts degradation *within* a sustained run as the
   free pool drains. What was observed instead: a clean 1.5 GB/s cache burst, a
   flat non-decaying steady state, write amplification at the RAID-5 floor
   (1.45–1.50×) with essentially no read-modify-write, latency that stays low
   and *scales normally* with queue depth, and — decisively — **throughput that
   rises 1.65× when concurrency rises**. A drive whose garbage collection has no
   headroom cannot hand back 65% more throughput on demand. Combined with the
   drives' own health (0 reallocated sectors, ~96% endurance remaining, full
   reserve space), the flash is not the constraint.
   **Consequence: TRIM, secure-erase, and over-provisioning are hygiene, not the
   fix. A full array wipe purely to reset FTL state is NOT justified.**
2. **Drive generation / request shape — SURVIVES, and is the leading
   explanation.** ~72 MB/s single-stream and ~120 MB/s at depth per drive is a
   plausible steady-state O_DIRECT figure for a 2013-generation enterprise SATA
   SSD whose headline number is a sequential-burst rating. Nothing observed
   contradicts it.
3. **Controller destage limits — SURVIVES, partially.** The array scaled from
   144 to 238 MB/s with concurrency but did not scale linearly (4× the streams
   bought 1.65× the throughput), while `%util` sat ~90% in both cases and
   latency rose 3×. Something — the drives, the controller's destage path, or
   RAID 5 parity computation — imposes a soft ceiling somewhere above 238 MB/s.
   Distinguishing which is not necessary for the Phase 2 decision.

One further correction to the earlier picture: **the array is not "saturated"
under CI load in the way `%util` suggested.** CI achieves roughly what one
sequential stream achieves. The device had ~65% more to give at higher queue
depth the whole time. `%util` near 100% in both the 144 MB/s and 238 MB/s cases
is one more demonstration of the point already made in the characterization's
§"Why `%util` misleads on this array".

## What this does not settle

- **The CI-shaped workload's ceiling.** Both tests are large sequential writes.
  Real CI is many small files with a high fsync rate — a different request
  shape whose ceiling could be lower, and whose knee (throughput and p99
  latency vs. offered concurrency) is what Phase 2/Test 2 in the
  characterization's measurement plan was for. If a Phase 2 option is chosen on
  IOPS rather than bandwidth grounds, run that sweep first (it needs `fio`).
- **Where exactly the >238 MB/s ceiling sits, and whose it is** (drives vs.
  controller destage vs. parity). Not needed to choose between the Phase 2
  options, all of which either add devices or move the I/O elsewhere.
- **Whether RAID 5 → RAID 10 is achievable in place.** That is Phase 0
  (controller capability), unaffected by these numbers.

## Incidental findings

- **`fio`, `perccli`, `perccli2`, `storcli`, `megacli`, and `racadm` are all
  ABSENT** from this host; only `smartctl` and `iostat` are installed. Phase 0's
  controller-capability research therefore needs a tooling decision first:
  install the Dell/Broadcom management CLI, or drive the controller
  out-of-band via iDRAC, or at boot through the PERC HII menu. This is a real
  blocker for Phase 0 as written and should be resolved there.
- **`/var/cache/ci-runner` is not writable by the `cwoolley` login** — the first
  `dd` failed `Permission denied` and the test required `sudo`. Worth knowing
  for the Phase 3 backup and Phase 7 restore scripting.
- **A `ci-warm-cache` CronJob writes to `sda5` about every 30 minutes**
  (`warm-cache-populate-*`). It is the only writer to that volume. Any future
  idle-window measurement must be scheduled around it, and the Phase 6
  destructive window must account for it.
- Wear added by these tests: ~101 GB written across three drives with ~96%
  endurance remaining — negligible, and all scratch files were removed.

## Consequence for Phase 2

The decision reframes. The question is no longer "are the drives degraded, and
does restoring them recover throughput?" — they are not degraded, and there is
nothing to restore. It is now the plainer engineering question: **this array's
practical write ceiling is roughly 144 MB/s at CI's effective concurrency and
somewhere above 238 MB/s at depth; is that enough for the intended CI and
agentic-factory load, and if not, what is the cheapest way past it?**

That shifts the ranking materially:

- **A full wipe / secure-erase / rebuild purely to reset FTL state is now
  unjustified** — it was option 2's entire premise, and the premise is false.
- **Adding devices or moving the I/O is what remains**, and each option is now
  a pure capability argument rather than a repair: NVMe in the empty x16 slot
  (bypasses SATA, the controller, and parity entirely; by far the largest gain),
  RAID 10 across the free bays (removes the parity tax and adds spindles),
  or tmpfs work volumes (I/O never reaches storage; 118 GiB free RAM).
- **RAID 5's parity tax is real but small** — measured 1.45–1.50×, at the
  theoretical floor, with no read-modify-write. Re-geometry alone recovers at
  most that factor; it is not where the big win is.
- **Over-provisioning at VD creation remains worth doing** if any array is
  rebuilt for another reason, as cheap insurance given TRIM can never reach
  these drives — but it is no longer a reason to rebuild by itself.
