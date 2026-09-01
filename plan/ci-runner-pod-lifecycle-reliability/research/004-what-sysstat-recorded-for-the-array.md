# What the host's own record says about the array during the 2026-09-01 incident — sysstat, not `iostat` samples

Written after the maintainer challenged research/001–003's disk statements
("I don't believe you on disk throughput … is the actual underlying RAID array
overloaded?"). Those notes' disk claims rested on hand-taken `iostat` `%util` /
`aqu-sz` / `w_await` samples — and `fleet-ci-runner-pool`'s
`storage-io-characterization.md` carries a section titled "Why %util misleads
on this array" that the author had not read. This note replaces those samples
with the host's continuous record and the RAID plan's own framing. It draws no
conclusion the data does not support.

## 1. Sources actually consulted

- `sysstat` (`sar`, 10-minute buckets, `/var/log/sysstat/sa01`; local time is
  UTC−7) — the only continuous per-device history on the host.
- `/proc/pressure/io` (PSI) — the "io.pressure instrumentation" the host-info
  note refers to; there is no PSI history sampler, only the live counters.
- `perccli64 /c0` — controller and virtual-disk state.
- `poweredge-raid-array-maintenance` phase 1 / phase 2 / phase-2-correction
  notes — the array's measured ceilings and the framing to use.
- The OTEL collector (`/etc/otel-collector/config.yaml`) runs a `hostmetrics`
  receiver with `cpu, load, memory, paging, disk, filesystem` scrapers exported
  to Honeycomb (`HONEYCOMB_INGEST_KEY_LIVESPEC`): Honeycomb therefore holds
  `system.disk.*` and `system.cpu.load_average.*` for the window at higher
  resolution than `sar`. Not queried here (no key in this session).

## 2. Controller and array state (15:32Z)

`/c0/v0`: **RAID 5, `Optl`, `RWBD` (write-back, direct I/O), no rebuild,
reconstruction, consistency check or background initialization in progress**;
all three `MZ7GE960HMHP` SATA SSDs `Onln`. The array was healthy; nothing
below is a degraded-array effect.

## 3. `sar -d` for `sda` (the one virtual disk behind `/` and the cache volume)

| UTC (10-min avg) | tps | written | aqu-sz | await | %util |
|---|---|---|---|---|---|
| 14:00 | 894 | 95.6 MB/s | 98.8 | 110 ms | 94.5 |
| 14:10 | 968 | 93.7 MB/s | 99.2 | 102 ms | 93.9 |
| 14:20 | 792 | 93.6 MB/s | 95.7 | 121 ms | 94.5 |
| 14:30 | 1333 | 97.4 MB/s | 109.0 | 82 ms | 95.1 |
| 14:40 | 906 | 94.5 MB/s | 96.2 | 106 ms | 98.6 |
| 14:50 | 1211 | 92.1 MB/s | 107.7 | 89 ms | 95.0 |
| 15:00 | 1030 | 92.7 MB/s | 96.0 | 93 ms | 95.3 |
| 15:10 | 1073 | 93.1 MB/s | 108.3 | 101 ms | 94.8 |
| 15:20 | 1118 | 92.3 MB/s | 119.7 | 107 ms | 92.9 |
| 15:30 | 563 | 59.4 MB/s | 54.6 | 97 ms | 47.8 |

Average request size ≈ 90 KB. For ninety minutes the device served a nearly
constant **~1,000 write requests/s at ~95 MB/s with ~100 requests outstanding
and ~100 ms average completion time**, independent of how many jobs were
running (11 to 66 pods over the window). By Little's law the flat ~100-deep
queue at a flat ~1,000 req/s is a device serving at a fixed rate with demand
above it — the shape of a service ceiling, not of a bursty workload.

## 4. `sar -u` / `sar -q` (CPU wait and blocked tasks), same buckets

| UTC | %iowait (72 CPUs) | ldavg-1 | blocked (D) |
|---|---|---|---|
| 14:00 | 16.1 | 27.8 | 1 |
| 14:10 | 18.3 | 48.5 | 14 |
| 14:20 | 17.6 | 37.3 | 11 |
| 14:30 | 26.4 | 69.5 | 35 |
| 14:40 | **54.2** | 198.1 | 25 |
| 14:50 | 23.8 | 136.9 | 9 |
| 15:00 | 22.5 | 77.2 | 0 |
| 15:10 | 22.0 | 85.7 | 19 |
| 15:20 | 17.1 | 20.1 | 4 |
| 15:30 | 6.2 | 1.3 | 0 |

`%iowait` on a 72-CPU host counts idle CPUs with I/O outstanding; it is a
weak proxy for "the disk is the bottleneck" but a direct measure of "tasks
were waiting on I/O", and it was never below 16 % in the window. PSI at
15:31Z (idle pool): `io full avg300 = 12.97 %` — for 13 % of the preceding
five minutes every non-idle task was stalled on I/O; cumulative `full` stall
since boot (4.3 days) ≈ 33,044 s ≈ 8.9 % of wall time.

## 5. What the RAID plan's numbers make of this

- Idle sequential ceiling: ~144 MB/s one stream, ~238 MB/s four streams at
  ~3× the write latency (phase 1). Today's 95 MB/s is below that, so **this
  was not a sequential-throughput ceiling**.
- Random 4 KB writes: **~1,400 IOPS (p99 505 ms) cold-allocating, ~10,400
  IOPS warm** (phase-2 correction) — "which figure is representative of CI is
  genuinely unresolved". Today's ~1,000 req/s of ~90 KB writes with ~100 ms
  average latency sits at the cold-allocation end of that range. CI churn
  (fresh overlay snapshots, new PVC directories, SQLite WALs) is
  allocation-heavy, which is the cold path.
- The phase-1 note's own verdict — CI is "latency-bound under queue depth"
  rather than throughput-saturated — is what the table shows. The word
  "overloaded" in research/001–003 should be read as **"operating at its
  cold-random-write service rate with a ~100-deep queue and ~100 ms
  latency for ninety minutes"**, which is what broke latency-sensitive work
  (SQLite open/`database is locked` in the console e2e; kine lease PUTs
  exceeding their deadline) without breaking bulk throughput.

## 6. What this does NOT establish

- Whether the array could serve this workload faster with a different
  layout, cache policy, or media: phase 2 measured the free knobs and found
  them small. Not re-measured here.
- Whether RAM-backed work volumes would help: **rejected by the maintainer
  on 2026-09-01** ("we are not going to do that; it will just take up RAM
  headroom") — `livespec-trxcf7` stays deferred and is not to be promoted on
  the strength of this note.
- Whether new drives are warranted: the maintainer holds that decision on
  `livespec-g52yrb`; nothing here pre-empts it.
- What the CI *jobs* themselves cost in I/O: the console's cargo-phase
  telemetry from the k3s lane never reaches Honeycomb (emitter default
  `http://172.17.0.1:4318`, unreachable from pods; filed as
  `livespec-console-beads-fabro-2dnpq3`), so per-job build I/O is not
  measured on this pool.

## 7. Where better data lives

Honeycomb (`hostmetrics` `disk` scraper: `system.disk.operations`,
`system.disk.io_time`, `system.disk.weighted_io_time`,
`system.disk.pending_operations`) for the same window at the collector's
scrape interval — the maintainer can query it; `sar` buckets are 10 minutes.
