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
   runner-externals copy (595 MB, 9,028 files, ~14 s) and the hook
   template's `postStart` warm-cache copy (1,923 MB, 159,802 files, ~14 s).
   That is 28 of a 38-second lint job's 56-second pod lifetime spent
   copying (GitHub's own "Initialize containers" step for that job spans
   09:57:20–09:57:46Z, 26 s), and it is the same for every job regardless
   of what the job does.
2. **The warm-cache copy has quietly grown 3.7×.** The tier was measured at
   379 MB when it shipped on 2026-08-23; the generation live at 09:30Z on
   2026-09-04 was 1,388 MB in 159,409 files, because each generation is
   hardlink-seeded from its predecessor and nothing prunes stale entries
   within a generation (generations themselves are kept to 2). The copy the
   workflow container pays is now 3.2× the externals copy it was meant to
   sit beside, and 5× the 379 MB it shipped at.
3. **Across the 08:25–09:17Z busy window, 184 jobs wrote 526 GB to
   `ci-workvols`** (50.9 M write operations). Per-minute writes track
   concurrent jobs with r = 0.90 at ~1.45 GB per job-minute. Most of those
   jobs lived under a minute (about 89 of the 184 pods ran ~30 s, 11 ran
   ~50 s, 44 ran ~60 s, 14 ran 70 s–3 min, 23 ran 3.5–7 min, one ran 10 s),
   so the start copies are between a third and seven eighths of every byte
   the tier wrote.
4. **The "six simultaneous starts saturate the array" premise does not
   hold on the 7-drive array.** In that window 18 jobs started in a single
   minute (31.9 GB written to the tier in that minute) and 24 ran
   concurrently at a 36.5 GB/min peak, while `sda` write await stayed at
   16–23 ms with the device busy 6–8 % of the time. The same instrument on
   2026-09-02 (old 3-drive array) showed 35–160 ms await at 90–98 % busy for
   a third of the bytes. The knee measured on 2026-09-02 was the old
   array's; on this array no knee is visible up to 24 concurrent jobs (a
   per-minute distinct count, so an upper bound on instantaneous
   concurrency). A start-rate limiter is therefore not justified by this
   window's data (max 18 starts per minute; no fan-out observed).
5. **Recommendation:** (a) rebuild the warm cache from empty now and bound
   its growth in the populator (cheapest, ~4–5× fewer start bytes); (b) turn
   the per-start warm-cache copy into a hardlink seed performed at volume
   creation by the local-path provisioner's setup hook, which runs inside
   the provisioner's busybox helper pod on the volume's parent mount — so
   the warm root must live inside `/var/lib/rancher/k3s/storage` itself
   (measured on the live tree: 2.3 s and 269 MB of metadata writes instead
   of 6.8 s and 2,153 MB), with `fsGroupChangePolicy: OnRootMismatch` on
   the scale sets and `UV_LINK_MODE=copy` in the hook template so no job
   can write a shared inode; (c) leave the externals copy alone until the
   hook's behaviour on a pre-seeded volume is verified against its source;
   (d) do not adopt the start-rate limiter — not justified by this window's
   data; (e) re-base the ratified "six starts" clause in
   livespec-dev-tooling's specification on the media-independent
   bytes-per-start principle. The decision belongs to the maintainer; the
   costs are in §6.

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
  CI run `33759185409`, re-run alone on the idle pool three times
  (attempts 2–4, `gh run rerun --job`), the last one sampled from the host
  by a watcher that read the work volume's size and file count with `du`
  and `find` (as root — the storage directory is `0700`), the tier's sector
  and write-operation counters from `/proc/diskstats`, and the pod phases
  from `kubectl`. The watcher's `+N s` labels are a loop counter × 3, not
  elapsed time: each iteration's reads took 3–7 s, so the samples are
  3–7 s apart, and every duration in this note is taken from the
  wall-clock stamp the watcher printed beside each row (§2 carries them).
  The sampled attempt (attempt 4) is §2; attempt 3's volume was read once
  at its +30 s row and agreed to the file.
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

| label | wall clock (Z) | volume, apparent MB | volume, real MB | files | `dm-4` MB written since t0 | `dm-4` write ops | pods |
|---|---|---|---|---|---|---|---|
| +0 s | 09:57:11 | 0 | 1 | 0 | 0 | 0 | runner `SchedulingGated` |
| +3 s | 09:57:14 | 0 | 1 | 0 | 0 | 0 | runner `Running` |
| +6 s | 09:57:18 | 0 | 1 | 0 | 0 | 10 | runner `Running` |
| +9 s | 09:57:22 | 120 | 124 | 1,221 | 123 | 1,258 | externals copy running |
| +12 s | 09:57:25 | 249 | 269 | 4,434 | 269 | 5,359 | |
| +15 s | 09:57:29 | 433 | 457 | 7,671 | 460 | 10,106 | |
| +18 s | 09:57:32 | 572 | 615 | 12,141 | 597 | 11,568 | workflow `ContainerCreating` |
| +21 s | 09:57:37 | 928 | 1,132 | 72,409 | 618 | 16,784 | `postStart` warm copy running |
| +24 s | 09:57:41 | 1,558 | 1,933 | 136,470 | 671 | 30,481 | |
| +27 s | 09:57:46 | 2,070 | 2,516 | 168,544 | 732 | 45,983 | workflow `Running` |
| +30 s | 09:57:52 | 2,073 | 2,524 | 171,620 | 876 | 82,685 | job steps |
| +33 s | 09:57:59 | 2,076 | 2,525 | 171,591 | 879 | 83,484 | runner `Completed` |
| +36 s | 09:58:04 | 1,425 | 1,520 | 92,310 | 954 | 92,176 | volume being deleted |
| +39 s | 09:58:07 | gone | gone | 0 | 954 | 92,176 | |

The `label` column is the watcher's loop counter (× 3 s), kept because the
raw output and the ledger comments cite rows by it; the `wall clock`
column is when each sample was actually read (3–7 s apart), and it is the
source of every duration and rate below.

Layout at +30 s: `externals` 566 MB apparent / 595 MB real / 9,028 files;
`_warm` 1,506 MB apparent / 1,923 MB real / 159,802 files; everything else
under 5 MB. The job itself (checkout plus `uv sync --frozen` plus ruff)
added under 5 MB and a few hundred files. Job timing per GitHub: started
09:57:18Z, done 09:57:56Z (38 s). The same job's first re-run of the day,
onto a cold pool, took 57 s; its original run on 2026-09-03 took 33 s.

Three readings from the table:

- **Two copies, back to back, ~28 s of the pod's 56 s.** Externals from
  09:57:18 to 09:57:32 (the `+6 s` to `+18 s` rows; ~14 s) at ~42 MB/s and
  ~650 files/s (the hook copies file by file); the warm cache from 09:57:32
  to 09:57:46 (`+18 s` to `+27 s`; ~14 s) at ~137 MB/s and ~11,000 files/s.
  GitHub's "Initialize containers" step for this job spans
  09:57:20–09:57:46Z (26 s). The workflow container is held in
  `ContainerCreating` for the whole `postStart`; the job cannot start until
  the 1.9 GB has been copied.
- **The disk saw 954 MB of the 2,525 MB.** The externals reached the
  device during their own copy (`dm-4` tracked them in real time: 123/124,
  269/269, 460/457, 597/615 MB on the `+9 s`…`+18 s` rows); of the warm
  copy, 1,571 MB (2,525 − 954) was still dirty page cache when the volume
  was deleted (09:58:04, the `+36 s` row), so it never reached the array. A
  job longer than the kernel's dirty-expiry window (30 s) pays the full
  2.5 GB. So the per-start DISK cost is 0.95–2.5 GB depending on job
  length; the per-start CPU, page-cache and inode cost is the full 2.5 GB
  and 171,591 creates every time.
- **92,176 write operations for one start**, 82,685 of them by +30 s: the
  inode and journal traffic of 171,591 creates dominates the operation
  count, not the bytes. That is what made the 2026-09-02 attribution see
  "~1,000 write req/s at ~95 MB/s" — small, metadata-heavy writes.

## 3. The busy window, 08:25–09:17Z: bytes track concurrency, not starts alone

184 distinct workflow pods (jobs) in 52 minutes, all at C = 32: 14
livespec-dev-tooling CI runs (7 master pushes — the storage-layout,
cache-tiers-align, storage-layout-verify, iDRAC and cache-tiers spec-accept
merges among them — and 5 PR runs, #1697 and #1698 among those), 4
livespec-overseer runs and 2 livespec runs. Peak 24 concurrent (a
per-minute distinct count, so an upper bound on instantaneous
concurrency). Writes on the work-volume tier, per device, from Honeycomb
(sysstat agrees within 15 %):

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
little, for two reasons. Most jobs in this window lived under a minute, so
"a running job" and "a job that just started" are nearly the same
population. And the instrument lags: a start's writes land while the
workflow pod is still `ContainerCreating`, before it appears in the pod
metric at all (08:40Z: 10.2 GB on `dm-4` with zero workflow pods in the
metric; 08:39Z: zero pods, 0.17 GB), so the "new pods" term trails the
writes it should explain by up to a minute — part of its weakness is the
instrument's, not only the short lifetimes'. With 184 starts at 0.95–2.5
GB each, the start copies are 175–460 GB of the 526 GB — a third to seven
eighths of the tier's writes. The 0.95 GB lower bound is specific to the
idle pool §2 sampled: under 24 concurrent starts the dirty pages pass
`dirty_background_ratio` (10 % of 188 GB) and more of each warm copy is
flushed before its volume is deleted, so the real per-start disk cost in
this window sits nearer the upper bound. The steady minutes with no new
pods (08:53Z, 08:56Z: nine jobs, 5.1–5.3 GB/min) show what job bodies
alone write on this fleet: about 0.6 GB per job-minute, mostly `uv sync`
materialising virtualenvs and pytest.

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
3-drive array (`sa02`, buckets 08:10–11:40 PDT), busy buckets only (the
16 of 22 at %util ≥ 64): 84–119 MB/s written, aqu-sz 69–125, await
35–160 ms, %util 64–98 %. The six quieter buckets in that window (08:10
and 09:10–09:50 PDT) read 20–104 MB/s at 10–50 % util, aqu-sz 11–47,
await 21–62 ms, and are omitted from those ranges. That is the window whose
"~6 simultaneous starts saturate `sda`" reading became Carrier F's
premise and, via the cache-tiers plan, a ratified clause in
livespec-dev-tooling's specification.

So: the rebuilt array absorbs twice the write rate at a fifth of the
latency and stays idle over 90 % of the time even in the peak minute. The
start-burst knee measured on 2026-09-02 was the old array's; on the
rebuilt array it is not observed in this window (max 18 starts per minute;
no fan-out). What survives is the media-independent point: 2.5 GB and 171k
creates per start is waste on any medium, and it is the largest single
write source on the pool. The cap re-derivation (Carrier B,
`kueue/DERIVATION.md`) is the maintainer's; this note's input to it is
that nothing in the 2026-09-04 data shows the array limiting at 24
concurrent jobs.

## 5. Why the warm copy is 1.9 GB, not 379 MB

`ci-runner/k3s/phase2/warm-cache/README.md` measured the tier at 379 MB
("the union of all nine routed repositories' locked trees") on 2026-08-23
and documents the growth mechanism under "Growth": each generation is
hardlink-seeded from its predecessor, so the cache "accumulates every
locked version ever synced", and the remedy is manual — delete
`uv-generations/` and the `uv` link, run one populate. As of 2026-09-04
it had not been run. The populator keeps only two generations
(`KEEP_GENERATIONS=2`); nothing prunes stale entries within a generation.
The generation live at 09:30Z on 2026-09-04
(`uv -> uv-generations/20260904T093001Z`; superseded at 10:00Z by
`20260904T100000Z`, 1,390 MB, 159,775 files) was 1,388 MB apparent,
159,409 files, of which `archive-v0` (unpacked wheels of every version
ever locked) is 1,159 MB. Every release-please bump of a fleet library
adds a version and never removes one, so the per-start copy grows with
the fleet's release cadence.

The `postStart` in `ci-runner/k3s/phase2/arc/hook-pod-template.yaml`
copies the whole generation with `cp -rp --no-preserve=ownership` into
`/__w/_warm/uv` and points `UV_CACHE_DIR` at it. The README's cost table
(0.8 s copy, `uv sync` 7.9 s → 0.5 s) was true at 379 MB; at 1.9 GB the
copy is 14 s on an idle pool and 44 MB/s under a six-start burst on the
old array (the 2026-09-02 evidence), so it costs twice the 7 s it saves
even on an idle pool.

## 6. Levers, with measured costs

| # | lever | per-start bytes to the tier | per-start files / ops | start latency | what it needs | verdict |
|---|---|---|---|---|---|---|
| L1 | **Rebuild the warm cache from empty and bound its growth** — run the README's reset now; change the populator to start a generation empty every Nth run or whenever the generation exceeds the current union by 2× | 1,923 MB → ~379–500 MB (the routed set is still the README's nine repos; the F2 design memo on `livespec-41w4` measured their locks' from-empty union at 379 MB in 8,070 files on 2026-09-04) | 159,802 → ~8,000 | 14 s → ~2.5 s | one host operation; a populator change in livespec-dev-tooling `warm-cache/` | **do first** — no design risk |
| L2 | **Hardlink seed instead of copy, at volume creation.** Seed `_warm/uv` with `cp -al` from the local-path provisioner's `setup` script; the hook's `postStart` becomes a guard (skip when `dst` exists). That script does NOT run on the host: it runs inside the provisioner's busybox helper pod (rancher/local-path-provisioner v0.0.36, `provisioner.go`), which mounts the volume's PARENT directory — `filepath.Split(o.Path)`'s `parentDir`, the `data` HostPath volume — at the same absolute path, with `VOL_DIR` = `parentDir/<pvc-dir>`. So the warm root must live INSIDE `/var/lib/rancher/k3s/storage` (as `.warm`): the same mount the helper sees, not merely the same filesystem (`ci-workvols` is mounted at two paths, and a link between them is `EXDEV` even host-side). With `WaitForFirstConsumer` the seed runs during PVC provisioning, after the runner pod is scheduled, so the workflow container's `ContainerCreating` hold disappears and the runner pod's volume wait absorbs the ~2 s. Two more things the seed needs: (i) kubelet's `fsGroup` ownership walk (`volume_linux.go` `changeFilePermission`: `Lchown` + `Chmod` on every entry under the default policy `Always`) would mutate every seeded shared inode on each start, so the scale sets must set `fsGroupChangePolicy: OnRootMismatch` and the setup script must pre-set the volume root's group and setgid bit; (ii) uv's default link mode hardlinks cache files into the job's `.venv`, so a job writing a site-packages file in place would write the shared generation, which the ratified clause forbids ("A job MUST NOT be able to write any shared cache") — so the hook template sets `UV_LINK_MODE=copy` (private venv copies; the cost is the venv's own bytes per job, to be measured in acceptance) | measured on the live 1,388 MB tree, same filesystem: **269 MB** of metadata in 68,986 ops vs **2,153 MB** in 237,006 ops for `cp -rp`; with L1 first, ~15 MB (pro rata by file count) | inode links only | 2.3 s vs 6.8 s (+1.6 s sync); with L1, under 1 s | livespec-dev-tooling: `local-path-provisioner/` setup script + the warm root inside the storage directory + `fsGroupChangePolicy` on the scale sets + `UV_LINK_MODE=copy` and the guard in the hook template; the populator writes generations there. Verified locally that `uv sync --frozen` from a hardlink-seeded cache leaves every shared inode intact: uv's own cache writes do not rewrite shared inodes (every original file's checksum unchanged, no link count dropped to 1) — what uv does do is hardlink cache files INTO the venv, hence `UV_LINK_MODE=copy` | **implementation child** after L1 — filed as `livespec-lvtu`, which does all of the above |
| L2′ | Read-only bind of the warm lower as `UV_CACHE_DIR` (no copy at all) | 0 | 0 | 0 | — | **not viable**: uv 0.9.26 refuses to initialise on a read-only cache (`Failed to initialize cache … Permission denied` on `sdists-v9/.git`), verified locally; and a link across two mounts of one filesystem fails with `EXDEV` (kernel semantics — `do_linkat` refuses when the two paths are on different vfsmounts, bind mounts included; stated from the source, not exercised here), which is why L2's warm root must sit inside the very mount the seeding process sees |
| L3 | **Externals** (595 MB, 9,028 files, ~14 s per start): pre-seed the volume from a host copy of the pinned image's `/home/runner/externals` in the same setup script, so the hook's copy finds its files present | 595 MB → 0 only if the hook skips existing files; the hook (`actions/runner-container-hooks`, `packages/k8s`, invoked from `/home/runner/k8s/index.js`) is upstream code that, as of 2026-09-04, the repo does not carry; whether its copy is unconditional is **unverified** | | | reading the hook's source at the pinned runner image `2.336.0`; if unconditional, a custom runner image or an upstream change is the only route | **verify first** — a research task, not a child yet |
| L4 | **Start-rate limiter** (Kueue admission check or a converge-side gate) | 0 | 0 | adds queueing | new control surface; as of 2026-09-04 no existing knob limits start RATE (every knob bounds concurrency: churn-slot capacity, `nominalQuota`, `maxRunners`, provisioner `--worker-threads 8`, `max-pods`) | **not justified by this window's data** — §4: 18 starts in one minute at 20 ms await on this array, and no fan-out in the window; revisit when the Carrier B fan-out read is in |
| L5 | tmpfs work volumes / per-pod PVC replacement | | | | | already rejected (maintainer 2026-09-01, `livespec-trxcf7`) — not reopened |

Interactions: L1 and L2 compound (the seed cost scales with file count).
L2 also removes the `ContainerCreating` hold on the workflow container
entirely: with `WaitForFirstConsumer` the PVC is provisioned after the
runner pod is scheduled, so the ~2 s seed runs inside the runner pod's
volume wait rather than inside the workflow container's `postStart`.
Neither changes what a long job writes in its body (~0.6 GB per
job-minute on this fleet); that is the job's own work and out of scope
here.

## 7. Recommendation and routing

1. **L1 now**, as a host operation plus a small livespec-dev-tooling change
   to `warm-cache/warm-cache-populate.sh` (empty-seed every Nth generation,
   or when the generation's size exceeds a bound); also record the current
   union size in the README's cost table.
2. **L2 as the implementation child** of this epic in livespec-dev-tooling
   (`local-path-provisioner/` setup script seeding with `cp -al` inside
   the busybox helper pod; the warm root relocated INSIDE
   `/var/lib/rancher/k3s/storage` as `.warm`, the same mount the helper
   sees; `fsGroupChangePolicy: OnRootMismatch` on the scale sets plus a
   pre-set group and setgid bit on the volume root; `UV_LINK_MODE=copy`
   and the guard in the hook template), host-routed and attended like
   every phase2 change, with the single-start watcher of §1 as its
   acceptance instrument: target under 100 MB and under 1 s of seeding per
   start, and measure the per-job venv copy cost that `UV_LINK_MODE=copy`
   adds. Filed as `livespec-lvtu`.
3. **L3 as a verification research task** (read the hook source at the
   pinned tag; decide pre-seed vs custom image vs leave), not yet a child.
4. **L4 not adopted** — not justified by this window's data (max 18
   starts per minute; no fan-out observed); the Carrier B fan-out read is
   the trigger to reconsider.
5. **Specification follow-up in livespec-dev-tooling** (spec-op,
   maintainer-gated): `SPECIFICATION/non-functional-requirements.md`
   §"Runner-pool build cache tiers" ratified "about six simultaneous job
   starts saturate the array" as the reason a host-served realisation MUST
   be preferred. The number is the old array's; the rule is right for a
   media-independent reason (bytes and creates per start are pure
   overhead, §2). A propose-change should re-base the clause on the
   measured per-start cost rather than on a knee not observed on the
   rebuilt array, so it does not rot when the NVMe lands either.
6. **Input to Carrier B / the cap**: §4 — no array limit visible at 24
   concurrent jobs on 2026-09-04; the fan-out read decides.

Acceptance for `livespec-381e`: criterion 1 is this note; criterion 2 is
the maintainer's decision on 1–5, recorded on `livespec-ifwnqj`, with the
children filed after it; criterion 3 is an independent adversarial review
of this note's factual claims against the live host and the Honeycomb
pages above (commissioned by the plan session before this note merges).

## 8. Raw evidence kept

- The `live-exercise-evidence` (14:33Z) and `review-evidence` (14:35Z)
  comments of 2026-09-04 on `livespec-381e` carry the headline numbers —
  the per-start totals, the window totals, the host `cp -al` / `cp -rp`
  timings (2.3 s / 269 MB / 69k ops vs 6.8 s / 2,153 MB / 237k ops), the
  two local uv findings — and the four Honeycomb query ids of §1; the
  second records the corrections this revision applies. The watcher's raw
  rows are the table in §2 (the watcher's session file is not a durable
  source).
- `sar -d -p -f /var/log/sysstat/sa04 -s 01:25:00 -e 02:17:00` and
  `sa02 -s 08:00:00 -e 11:40:00` reproduce §4 on the host.
- The 2026-09-02 evidence entry on `livespec-ifwnqj` (18:43:49Z) carries
  the old-array `pidstat` attribution this note supersedes in its
  numbers, not in its mechanism.

## 9. Decision (2026-09-04, after this note)

The maintainer's decision supersedes §7's phrasing and is recorded on
`livespec-ifwnqj` as the scope amendment of 2026-09-04T10:14:48Z (Carriers
F1–F5): remove the per-start copy entirely (a hardlink seed at volume
creation — realised, per §6 L2, inside the provisioner's helper pod on
the volume's parent mount rather than host-side), build every cache
generation from empty so nothing
unreferenced can be in it, emit metrics on every build and trim, add
checks that fail on unreferenced entries and alarm on over-budget size or
seed cost, re-base the specification clause on a bounded and checked
per-start cost, and verify the upstream externals copy before deciding
its route. The start-rate limiter is rejected.

Review: independent adversarial review 2026-09-04 (BLOCKERS: 7, NITs: 10),
all applied in this follow-up revision; the note's conclusions were
confirmed by re-derivation.
