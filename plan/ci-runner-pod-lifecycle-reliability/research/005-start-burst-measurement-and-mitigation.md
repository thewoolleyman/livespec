# 005 — What one job start writes, and whether the start burst is still the knee (2026-09-04)

Carrier F of the 2026-09-04 scope amendment on plan epic `livespec-ifwnqj`;
work-item `livespec-381e`. Measured on `poweredge-xubuntu` on 2026-09-04
between 09:25Z and 10:05Z, after the clean reboot of 09:17:55Z, on the
rebuilt 7-drive RAID-5 array with the three CI tiers as LABEL-keyed LVs
(`ci-cache` = `dm-2`, `ci-containerd` = `dm-3`, `ci-workvols` = `dm-4`; the
`dm-N` numbers are for this boot only).

## Bottom line

1. **One job start writes 2.5 GB in 171,591 files onto the work-volume
   tier** before the workflow's own steps run: the ARC container hook's
   runner-externals copy (595 MB, 9,028 files, ~12 s) and the hook
   template's `postStart` warm-cache copy (1,923 MB, 159,802 files, ~9 s).
   That is 21 of a 38-second lint job's 56-second pod lifetime spent
   copying, and it is the same for every job regardless of what the job
   does.
2. **The warm-cache copy has quietly grown 3.7×.** The tier was measured at
   379 MB when it shipped on 2026-08-23; the generation live today is
   1,388 MB in 159,409 files, because each generation is hardlink-seeded
   from its predecessor and nothing prunes. The copy the workflow container
   pays is now five times the externals copy it was meant to sit beside.
3. **Across the 08:25–09:17Z busy window, 184 jobs wrote 526 GB to
   `ci-workvols`** (50.9 M write operations). Per-minute writes track
   concurrent jobs with r = 0.90 at ~1.45 GB per job-minute. Since most of
   those jobs lived one to six minutes, the start copies are between a third
   and three quarters of every byte the tier wrote.
4. **The "six simultaneous starts saturate the array" premise does not
   hold on the 7-drive array.** In that window 18 jobs started in a single
   minute (31.9 GB written to the tier in that minute) and 24 ran
   concurrently at a 36.5 GB/min peak, while `sda` write await stayed at
   16–23 ms with the device busy 6–8 % of the time. The same instrument on
   2026-09-02 (old 3-drive array) showed 35–160 ms await at 90–98 % busy for
   a third of the bytes. The knee measured on 2026-09-02 was the old
   array's; on this array no knee is visible up to 26 concurrent jobs. A
   start-rate limiter is therefore not justified by the data.
5. **Recommendation:** (a) rebuild the warm cache from empty now and bound
   its growth in the populator (cheapest, ~3.5× fewer start bytes); (b) turn
   the per-start warm-cache copy into a hardlink seed performed host-side
   by the local-path provisioner's setup hook on the `ci-workvols`
   filesystem (measured on the live tree: 2.3 s and 269 MB of metadata
   writes instead of 6.8 s and 2,153 MB); (c) leave the externals copy alone
   until the hook's behaviour on a pre-seeded volume is verified against
   its source; (d) reject the start-rate limiter; (e) re-base the ratified
   "six starts" clause in livespec-dev-tooling's specification on the
   media-independent bytes-per-start principle. The decision belongs to
   the maintainer; the costs are in §6.

## 1. Method and instruments

Two instruments for every window-level claim, one controlled job for every
per-start claim, and one local experiment per lever:

- **Honeycomb**, environment `livespec`, dataset `metrics`,
  `host.name = poweredge-xubuntu`: `system.disk.io` / `system.disk.operations`
  / `system.disk.operation_time` per `device` (the hostmetrics scraper at
  30 s) and `k8s.pod.name` in namespace `arc-runners` ending in `-workflow`
  (one row per running job every 5 s). Query result pages, retained by
  Honeycomb:
  - writes per device, 08:25–09:17Z, 60 s buckets —
    `https://ui.honeycomb.io/thewoolleyweb/environments/livespec/datasets/metrics/result/ywNQxPg5Yvg`
  - concurrent workflow pods per minute, same window —
    `https://ui.honeycomb.io/thewoolleyweb/environments/livespec/datasets/metrics/result/iSaWYpcQeR5`
  - per-pod sample counts (job lifetimes), same window —
    `https://ui.honeycomb.io/thewoolleyweb/environments/livespec/datasets/metrics/result/bu5N29pPaTG`
  - `sda` write operation time and operations, same window —
    `https://ui.honeycomb.io/thewoolleyweb/environments/livespec/datasets/metrics/result/MN49CprovQ`
- **sysstat** on the host (`sar -d -p -f /var/log/sysstat/sa04` and `sa02`,
  10-minute buckets, host-local PDT = UTC − 7), the second instrument for
  the same windows, as research/004 did.
- **The controlled single job**: `check-lint` of livespec-runtime's master
  CI run `33759185409`, re-run alone on the idle pool four times
  (`gh run rerun --job`), the last one sampled every 3 s from the host by a
  watcher that read the work volume's size and file count with `du` and
  `find` (as root — the storage directory is `0700`), the tier's sector and
  write-operation counters from `/proc/diskstats`, and the pod phases from
  `kubectl`. The first sampled attempt's numbers are in §2; the untimed
  attempt's volume was read once at +30 s and agreed to the file.
- **Local experiments** (this VPS, uv 0.9.26): a read-only uv cache, and a
  hardlink-seeded uv cache, each driven through `uv sync --frozen`.
- **Host experiment**: `cp -al` versus `cp -rp` of the live warm generation
  within the `ci-cache` filesystem, timed, with `dm-2` counters before and
  after and the copies deleted afterwards.

What this note does NOT measure: a release fan-out (13 jobs per repo
within seconds across nine repos) — none happened in the window; the
heaviest minute had 18 starts. The Carrier B retrospective query on the
first fan-out at C = 32 stays the event that would show a knee if this
array has one below 64.

## 2. One start, sampled (livespec-runtime `check-lint`, 09:57:11–09:58:07Z)

| t (s) | volume, apparent MB | volume, real MB | files | `dm-4` MB written since t0 | `dm-4` write ops | pods |
|---|---|---|---|---|---|---|
| 0 | 0 | 1 | 0 | 0 | 0 | runner `SchedulingGated` |
| 3 | 0 | 1 | 0 | 0 | 0 | runner `Running` |
| 6 | 0 | 1 | 0 | 0 | 10 | runner `Running` |
| 9 | 120 | 124 | 1,221 | 123 | 1,258 | externals copy running |
| 12 | 249 | 269 | 4,434 | 269 | 5,359 | |
| 15 | 433 | 457 | 7,671 | 460 | 10,106 | |
| 18 | 572 | 615 | 12,141 | 597 | 11,568 | workflow `ContainerCreating` |
| 21 | 928 | 1,132 | 72,409 | 618 | 16,784 | `postStart` warm copy running |
| 24 | 1,558 | 1,933 | 136,470 | 671 | 30,481 | |
| 27 | 2,070 | 2,516 | 168,544 | 732 | 45,983 | workflow `Running` |
| 30 | 2,073 | 2,524 | 171,620 | 876 | 82,685 | job steps |
| 33 | 2,076 | 2,525 | 171,591 | 879 | 83,484 | runner `Completed` |
| 36 | 1,425 | 1,520 | 92,310 | 954 | 92,176 | volume being deleted |
| 39 | gone | gone | 0 | 954 | 92,176 | |

Layout at +30 s: `externals` 566 MB apparent / 595 MB real / 9,028 files;
`_warm` 1,506 MB apparent / 1,923 MB real / 159,802 files; everything else
under 5 MB. The job itself (checkout plus `uv sync --frozen` plus ruff)
added under 5 MB and a few hundred files. Job timing per GitHub: started
09:57:18Z, done 09:57:56Z (38 s). The same job's first re-run of the day,
onto a cold pool, took 57 s; its original run on 2026-09-03 took 33 s.

Three readings from the table:

- **Two copies, back to back, ~21 s of the pod's 56 s.** Externals from
  +6 s to +18 s at ~50 MB/s and ~1,000 files/s (the hook copies file by
  file); the warm cache from +18 s to +27 s at ~170 MB/s and ~17,000
  files/s. The workflow container is held in `ContainerCreating` for the
  whole `postStart`; the job cannot start until the 1.9 GB has been copied.
- **The disk saw 954 MB of the 2,525 MB.** The externals were written back
  (they sat on the volume for more than 30 s); most of the warm copy was
  still dirty page cache when the volume was deleted at +36 s, so it never
  reached the array. A job longer than the kernel's dirty-expiry window
  (30 s) pays the full 2.5 GB. So the per-start DISK cost is 0.95–2.5 GB
  depending on job length; the per-start CPU, page-cache and inode cost is
  the full 2.5 GB and 171,591 creates every time.
- **92,176 write operations for one start**, 82,685 of them by +30 s: the
  inode and journal traffic of 171,591 creates dominates the operation
  count, not the bytes. That is what made the 2026-09-02 attribution see
  "~1,000 write req/s at ~95 MB/s" — small, metadata-heavy writes.

## 3. The busy window, 08:25–09:17Z: bytes track concurrency, not starts alone

184 distinct workflow pods (jobs) in 52 minutes: livespec-dev-tooling's
master CI after PR #1697 and PR #1698's own CI, livespec-overseer's master
CI, livespec's, all at C = 32. Peak 24–26 concurrent. Writes on the
work-volume tier, per device, from Honeycomb (sysstat agrees within 15 %):

| device | GB written | write ops |
|---|---|---|
| `sda` (the array) | 536.6 | 7.69 M |
| `dm-4` `ci-workvols` | 525.7 | 50.87 M |
| `dm-3` `ci-containerd` | 7.9 | 1.59 M |
| `dm-0` root | 2.4 | 0.22 M |
| `dm-2` `ci-cache` | 0.6 | 0.16 M |

The LVM/RAID stack merges ~6.6 tier-level operations into one array-level
request (10 KB average at `dm-4`, 60–75 KB at `sda`).

Per-minute regression of `dm-4` MB on the number of concurrent workflow
pods and on the net-new pods in that minute (44 minutes with at least one
job):

| model | fit | R² |
|---|---|---|
| pods only | 1,547 MB/min per concurrent pod | 0.78 |
| pods + net-new pods | 1,232 per pod + 775 per new pod | 0.82 |
| new pods only | 2,685 per new pod | 0.38 |

Concurrency explains most of the variance; a separate start term adds
little, because most jobs in this window lived one to two minutes, so
"a running job" and "a job that just started" are nearly the same
population. With 184 starts at 0.95–2.5 GB each, the start copies are
175–460 GB of the 526 GB — a third to three quarters of the tier's writes.
The steady minutes with no new pods (08:53Z, 08:56Z: nine jobs, 5.1–5.3
GB/min) show what job bodies alone write on this fleet: about 0.6 GB per
job-minute, mostly `uv sync` materialising virtualenvs and pytest.

## 4. The array is not at its knee at C = 32

`sda` write behaviour in the same window, sysstat 10-minute buckets (PDT
labels; the busy buckets are 08:30–09:20Z):

| bucket (PDT) | wkB/s | areq-sz KB | aqu-sz | await ms | %util |
|---|---|---|---|---|---|
| 01:30 | 58,274 | 46 | 5.8 | 4.3 | 3.5 |
| 01:40 | 171,758 | 73 | 46.0 | 19.5 | 6.5 |
| 01:50 | 194,974 | 76 | 60.5 | 23.5 | 7.3 |
| 02:00 | 223,415 | 62 | 60.0 | 16.5 | 8.4 |
| 02:10 | 202,967 | 70 | 60.8 | 20.9 | 7.2 |

Honeycomb's window average agrees: 142,935 s of write operation time over
7.69 M operations = 18.6 ms per write.

The same table for the 2026-09-02 15:00–18:40Z fan-out on the old
3-drive array (`sa02`, buckets 08:10–11:40 PDT): 85–120 MB/s written,
aqu-sz 47–125, await 35–160 ms, %util 64–98 %. That is the window whose
"~6 simultaneous starts saturate `sda`" reading became Carrier F's
premise and, via the cache-tiers plan, a ratified clause in
livespec-dev-tooling's specification.

So: the rebuilt array absorbs twice the write rate at a fifth of the
latency and stays idle over 90 % of the time even in the peak minute. The
start-burst knee was a property of the medium that no longer exists.
What survives is the media-independent point: 2.5 GB and 171k creates per
start is waste on any medium, and it is the largest single write source
on the pool. The cap re-derivation (Carrier B, `kueue/DERIVATION.md`) is
the maintainer's; this note's input to it is that nothing in the 2026-09-04
data shows the array limiting at 26 concurrent jobs.

## 5. Why the warm copy is 1.9 GB, not 379 MB

`ci-runner/k3s/phase2/warm-cache/README.md` measured the tier at 379 MB
("the union of all nine routed repositories' locked trees") on 2026-08-23
and documents the growth mechanism under "Growth": each generation is
hardlink-seeded from its predecessor, so the cache "accumulates every
locked version ever synced", and the remedy is manual — delete
`uv-generations/` and the `uv` link, run one populate. Nobody has run it.
Live on 2026-09-04: `uv -> uv-generations/20260904T093001Z`, 1,388 MB
apparent, 159,409 files, of which `archive-v0` (unpacked wheels of every
version ever locked) is 1,159 MB. Every release-please bump of a fleet
library adds a version and never removes one, so the per-start copy grows
with the fleet's release cadence.

The `postStart` in `ci-runner/k3s/phase2/arc/hook-pod-template.yaml`
copies the whole generation with `cp -rp --no-preserve=ownership` into
`/__w/_warm/uv` and points `UV_CACHE_DIR` at it. The README's cost table
(0.8 s copy, `uv sync` 7.9 s → 0.5 s) was true at 379 MB; at 1.9 GB the
copy is 9 s on an idle pool and 44 MB/s under a six-start burst on the old
array (the 2026-09-02 evidence), so it has been costing more than the 7 s
it saves whenever the pool is busy.

## 6. Levers, with measured costs

| # | lever | per-start bytes to the tier | per-start files / ops | start latency | what it needs | verdict |
|---|---|---|---|---|---|---|
| L1 | **Rebuild the warm cache from empty and bound its growth** — run the README's reset now; change the populator to start a generation empty every Nth run or whenever the generation exceeds the current union by 2× | 1,923 MB → ~500 MB (the 2026-08-23 union was 379 MB; the fleet has added repos since) | 159,802 → ~45,000 | 9 s → ~2.5 s | one host operation; a populator change in livespec-dev-tooling `warm-cache/` | **do first** — no design risk |
| L2 | **Hardlink seed instead of copy, host-side.** Move the warm root onto the `ci-workvols` filesystem (the LV that holds every PVC) and seed `_warm/uv` with `cp -al` from the local-path provisioner's `setup` script, which runs as root on the host path when the volume is created; the hook's `postStart` becomes a guard (skip when `dst` exists) | measured on the live 1,388 MB tree, same filesystem: **269 MB** of metadata in 68,986 ops vs **2,153 MB** in 237,006 ops for `cp -rp`; with L1 first, ~80 MB | inode links only | 2.3 s vs 6.8 s (+1.6 s sync); with L1, under 1 s | livespec-dev-tooling: `local-path-provisioner/` setup script + the warm root's location + the hook guard; the populator writes generations there. Verified locally that `uv sync --frozen` from a hardlink-seeded cache leaves every shared inode intact (uv creates new files, never rewrites cache entries in place) | **implementation child** after L1 |
| L2′ | Read-only bind of the warm lower as `UV_CACHE_DIR` (no copy at all) | 0 | 0 | 0 | — | **not viable**: uv 0.9.26 refuses to initialise on a read-only cache (`Failed to initialize cache … Permission denied` on `sdists-v9/.git`), verified locally; and a link across two bind mounts fails with `EXDEV`, which is why L2 must run host-side, not in the container |
| L3 | **Externals** (595 MB, 9,028 files, ~12 s per start): pre-seed the volume from a host copy of the pinned image's `/home/runner/externals` in the same setup script, so the hook's copy finds its files present | 595 MB → 0 only if the hook skips existing files; the hook (`actions/runner-container-hooks`, `packages/k8s`, invoked from `/home/runner/k8s/index.js`) is upstream code the repo does not carry; whether its copy is unconditional is **unverified** | | | reading the hook's source at the pinned runner image `2.336.0`; if unconditional, a custom runner image or an upstream change is the only route | **verify first** — a research task, not a child yet |
| L4 | **Start-rate limiter** (Kueue admission check or a converge-side gate) | 0 | 0 | adds queueing | new control surface, no existing knob (every knob today bounds concurrency: churn-slot capacity, `nominalQuota`, `maxRunners`, provisioner `--worker-threads 8`, `max-pods`) | **reject for now** — §4: 18 starts in one minute at 20 ms await on this array; revisit only if the Carrier B fan-out read shows a knee |
| L5 | tmpfs work volumes / per-pod PVC replacement | | | | | already rejected (maintainer 2026-09-01, `livespec-trxcf7`) — not reopened |

Interactions: L1 and L2 compound (the seed cost scales with file count).
L2 also removes the `ContainerCreating` hold on the workflow container
entirely, since the seed happens before the pod is scheduled. Neither
changes what a long job writes in its body (~0.6 GB per job-minute on this
fleet); that is the job's own work and out of scope here.

## 7. Recommendation and routing

1. **L1 now**, as a host operation plus a small livespec-dev-tooling change
   to `warm-cache/warm-cache-populate.sh` (empty-seed every Nth generation,
   or when the generation's size exceeds a bound); also record the current
   union size in the README's cost table.
2. **L2 as the implementation child** of this epic in livespec-dev-tooling
   (`local-path-provisioner/` setup script, warm root relocation onto
   `ci-workvols`, hook guard), host-routed and attended like every phase2
   change, with the single-start watcher of §1 as its acceptance
   instrument: target under 100 MB and under 1 s of seeding per start.
3. **L3 as a verification research task** (read the hook source at the
   pinned tag; decide pre-seed vs custom image vs leave), not yet a child.
4. **L4 rejected** on the 2026-09-04 evidence; the Carrier B fan-out read
   is the trigger to reconsider.
5. **Specification follow-up in livespec-dev-tooling** (spec-op,
   maintainer-gated): `SPECIFICATION/non-functional-requirements.md`
   §"Runner-pool build cache tiers" ratified "about six simultaneous job
   starts saturate the array" as the reason a host-served realisation MUST
   be preferred. The number is the old array's; the rule is right for a
   media-independent reason (bytes and creates per start are pure
   overhead, §2). A propose-change should re-base the clause on the
   measured per-start cost rather than on a knee that no longer exists, so
   it does not rot when the NVMe lands either.
6. **Input to Carrier B / the cap**: §4 — no array limit visible at 26
   concurrent jobs on 2026-09-04; the fan-out read decides.

Acceptance for `livespec-381e`: criterion 1 is this note; criterion 2 is
the maintainer's decision on 1–5, recorded on `livespec-ifwnqj`, with the
children filed after it; criterion 3 is an independent adversarial review
of this note's factual claims against the live host and the Honeycomb
pages above (commissioned by the plan session before this note merges).

## 8. Raw evidence kept

- Watcher output for the sampled start (§2), the local uv experiments and
  the host `cp -al` / `cp -rp` timings are quoted in full on
  `livespec-381e` (live-exercise-evidence comment, 2026-09-04).
- `sar -d -p -f /var/log/sysstat/sa04 -s 01:25:00 -e 02:17:00` and
  `sa02 -s 08:00:00 -e 11:40:00` reproduce §4 on the host.
- The 2026-09-02 evidence entry on `livespec-ifwnqj` (18:43:49Z) carries
  the old-array `pidstat` attribution this note supersedes in its
  numbers, not in its mechanism.

## 9. Decision (2026-09-04, after this note)

The maintainer's decision supersedes §7's phrasing and is recorded on
`livespec-ifwnqj` as the scope amendment of 2026-09-04T10:14:48Z (Carriers
F1–F5): remove the per-start copy entirely (host-side hardlink seed at
volume creation), build every cache generation from empty so nothing
unreferenced can be in it, emit metrics on every build and trim, add
checks that fail on unreferenced entries and alarm on over-budget size or
seed cost, re-base the specification clause on a bounded and checked
per-start cost, and verify the upstream externals copy before deciding
its route. The start-rate limiter is rejected.
