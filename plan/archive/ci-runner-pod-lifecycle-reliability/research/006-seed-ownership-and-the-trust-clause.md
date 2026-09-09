# 006 — The hardlink seed and "Trust by construction": what enforcement is possible on ext4 (2026-09-04)

Written by the plan session on the day Carrier F1 (`livespec-lvtu`,
livespec-dev-tooling PR #1711 = `e568c588`) landed and was applied to
`poweredge-xubuntu`. Every measurement below is from that host on
2026-09-04 between 15:27Z and 15:40Z unless it says otherwise. Repository
names are written in full; "the specification clause" means
livespec-dev-tooling `SPECIFICATION/non-functional-requirements.md`
§"Runner-pool build cache tiers", "Trust by construction": *a job MUST NOT
be able to write any shared cache*.

## Bottom line

1. The hardlink seed works and is fast. A real job's volume received the
   full 1,388 MB / 161,843-file generation within 3 s of the volume's
   creation, while the runner pod was still `SchedulingGated`; the disk
   saw 135 MB at that point and 282 MB by +6 s (metadata and journal; the
   copy it replaced wrote 2,153 MB). The job's `uv sync --all-groups`
   resolved 48 packages in 1 ms, installed 46 in 71 ms, downloaded
   nothing, and took 1.7 s; the whole `check-lint` job ran in 27 s.
2. The seed is NOT enforced read-only for the job, and on ext4 with
   hardlinks it cannot be, by the kernel's rules, without breaking uv.
   The workflow pod's work volume is idmapped so that its root is uid 0
   on the volume; the generation is root-owned; so every seeded inode is
   writable in place from every job. This is the state PR #1711 shipped
   with (its description deferred the closure to "a populator change for
   the sibling items"), and the specification clause is therefore
   unmet — visibly: `ci-runner/k3s/phase2/isolation/cache-negative-tests.sh`
   case 1 reports the violation on its six-hourly timer and stays red on
   purpose.
3. The closure that PR #1711's review added — own every generation as a
   uid no workflow pod maps (200000) — was applied live at 15:28Z and
   broke every job on the pool within a minute. It was reverted on the
   host at 15:34Z and in git by the follow-up PR named below. Section 3
   records why it cannot work with uv.
4. The remaining options are (a) reflinks: reformat the `ci-workvols`
   tier as XFS (or btrfs) and seed by `cp --reflink`, so the job owns every
   inode it sees and writes never reach the generation — the clean,
   mechanical closure, at the cost of a host filesystem change; (b) the
   unmapped-owner design plus per-volume copies of everything uv opens for
   writing and an accepted hard-failure class; (c) re-base the clause.
   **Recommendation: (a).** This is a host filesystem decision and is the
   maintainer's; nothing here proceeds on it unasked.

## 1. What happened, in order

| Time (UTC) | Event |
|---|---|
| 15:22 | PR #1711 rebased onto master `af6a923d` with the review additions (ownership by uid 200000, per-volume lock files, negative test case 1 re-based, gauges reader moved); `just check` passed; auto-merge armed by the factory bot. |
| 15:26 | Merged as `e568c588`. |
| 15:27 | Host: `rsync -aH` of `/var/cache/ci-runner/warm/` to `/var/lib/rancher/k3s/storage/.warm/` (2 generations, 1,913 MB, 325,070 files), `chown -R 200000:200000` on the generations (2.2 s); `install-converge-unit.sh`; `install-observability.sh` (gauges unit runs as capability-less root; first run exit 0). |
| 15:28:14–15:29:13 | `systemctl start converge-ci-stack.service`: provisioner ConfigMap configured, ten scale sets upgraded, hook ConfigMap configured, CronJob configured. Exit 0. |
| 15:29:22 | A runner pod created BEFORE the converge (old hook template, still carrying the warm-cache mount and the `cp -rp` copy) started a workflow pod. Its copy ran into a volume the new provisioner had already seeded with 200000-owned inodes; ~160k `Permission denied` lines; the hook's output exceeded the kubelet's 16 MiB gRPC limit (`ResourceExhausted`, `kuberuntime_container.go:327`); the kubelet failed the hook and the pod; livespec-dev-tooling master CI run 33889491753 `check-coverage` died with "pod failed to come online". |
| 15:30:27 | Controlled start (livespec-runtime run 33759185409 `check-lint`, attempt 5): seed complete by +3 s, 95 MB written. |
| 15:31:04 | That job FAILED: `error: Failed to initialize cache at /__w/_warm/uv — Caused by: failed to open file /__w/_warm/uv/CACHEDIR.TAG: Permission denied (os error 13)`. |
| 15:31:55 | The negative-tests workflow (run 33889947198), triggered on demand from inside a routed job: case 1 `shared inode refused as required, but /__w/_warm/uv is not writable for new entries either — uv cannot use this cache`; cases 2–4 pass. The instrument reported exactly the uselessness it was written to catch. |
| 15:34:31 | Mitigation on the host: `chown -R 0:0` on the generations (the hardlinks in live volumes see it at once); `kubectl set env cronjob/warm-cache-populate WARM_GENERATION_OWNER=0` (a live drift from git, closed by the follow-up PR). |
| 15:35:14–15:35:41 | Controlled start again (attempt 6): seed by +3 s (135 MB), job green, `uv sync` 1.7 s with no downloads. |
| 15:38 | Master CI run 33889491753 re-run: green (attempt 2). |

## 2. The seed, measured

Single-start watcher (research/005 §1) on the passing run, volume
`livespec-runtime-k3s-fnlzt-runner-z6zwg-work`:

| t after PVC dir appeared | files in volume | `ci-workvols` MB written | runner pod | workflow pod |
|---|---|---|---|---|
| +0 s | 36,059 | 0 | SchedulingGated | — |
| +3 s | 161,843 (seed complete) | 135 | SchedulingGated | — |
| +6 s | 161,843 | 282 | Running | — |
| +12 s | 164,331 | 440 | Running | — |
| +18 s | 170,978 | 883 | Running | Running |
| +24 s | 174,025 | 888 | Terminating | — |
| +30 s | volume removed | 909 | — | — |

So: the seed itself is ≤3 s and ~135–280 MB of metadata on the live
1.4 GB / 162k-file generation (research/005 predicted 2.3 s / 269 MB);
the job's own writes (checkout, the venv that `UV_LINK_MODE=copy` copies
instead of links, the lint) are the remaining ~630 MB. The under-1 s /
under-100 MB acceptance figure on `livespec-lvtu` is, as the PR said,
reachable only with F2's trimmed generation (`livespec-41w4`): the seed's
cost scales with the file count.

## 3. Why an unmapped owner cannot work with uv

The idea: files owned by a uid outside the pod's 65,536-id mapping appear
inside the pod as `nobody`, no capability of the pod's root applies to
them, and mode bits govern — 0644 is read-only. True, and insufficient,
because Linux does more than consult mode bits for an inode whose owner
the caller's user namespace does not map (`HAS_UNMAPPED_ID`):

- `inode_permission()` refuses ANY `MAY_WRITE` on such an inode — so a
  0666 file is not writable either, and an open for writing fails with
  `EACCES` regardless of mode. uv's cache init does exactly that on
  `CACHEDIR.TAG` (the observed failure).
- `may_delete()` refuses unlink and rename-over of such an inode with
  `EPERM` — so uv's temp-file-then-rename cannot replace a seeded entry
  (an index-metadata refresh in `simple-v18/` on re-resolution, a
  `revision` rewrite), and `git fetch` into a seeded bare repository in
  `git-v0/db/` cannot write `FETCH_HEAD`. Under the kill switch the
  hook's `rm -rf` of the seed would fail the same way.
- A directory with an unmapped owner refuses creates — and `cp -al`
  gives the seeded directories the generation's owner, so before the
  seed also re-owned every directory, uv could not add an entry anywhere
  (case 1's "not writable for new entries either").

Making it work would need: per-volume copies of every file uv opens for
writing at init (`CACHEDIR.TAG`, `.gitignore`, every `.lock`); per-volume
ownership of every seeded directory; not seeding `simple-v18/` and
`git-v0/` at all (so their refreshes create rather than replace); and
accepting that any other replace-or-remove uv ever needs fails the job
hard, with a permission error, until the next populate. That is a new
failure class on a lane whose charter is "fast and flake-free", and it
depends on uv's internal write patterns staying as they are.

Also learned, and fixed in the follow-up PR's docs: the populator's
container had every capability dropped, so it could not have performed
the `chown` without `CAP_CHOWN`, and could not have written into a
predecessor-owned tree without `CAP_DAC_OVERRIDE`; both were added and
then removed again.

## 4. Options

| | Mechanism | Enforced? | Per-start cost | Cost to adopt | Risk |
|---|---|---|---|---|---|
| (a) **Reflink seed on XFS** (recommended) | Reformat the `ci-workvols` LV as XFS (`mkfs.xfs -L ci-workvols`; the LABEL-based fstab from `livespec-el5y` makes this a mkfs, nothing else); the provisioner's setup script seeds with `cp -a --reflink=always` (needs a helper image with GNU cp — the current helper is busybox, whose `cp` has no `--reflink`); the populator is unchanged. | Yes, by the filesystem: every seeded inode is the job's own; writes copy-on-write and never reach the generation. | One inode create plus one extent-share per file: metadata-only like the hardlink seed, some seconds per 160k files, well under 1 s after F2's trim. | One maintenance window on the host (the tier holds only ephemeral volumes and `.warm`, which is regenerable); a helper-image pin; re-verify the idmapped-mount and fsGroup facts on XFS (both supported since 5.12 / 1.36). | `UV_LINK_MODE=copy` becomes unnecessary (a hardlinked venv file is the job's own inode) — a per-job saving. Every seed-time and job-time behaviour of uv is unchanged. |
| (b) Unmapped owner + carve-outs | Section 3's list. | Yes for the inodes that are shared; the carve-outs are per-volume. | Hardlink seed plus a `chown` pass over the directories. | Populator capabilities; a longer setup script; two buckets unseeded. | A job that must replace a seeded entry fails hard; the carve-out list tracks uv internals. |
| (c) Re-base the clause | Accept uv's write discipline plus `UV_LINK_MODE=copy` plus the 30-minute from-empty rebuild (F2) as the protection, and say so in the specification. | No. | Hardlink seed as today. | A spec-op (`livespec-1qpt` already re-bases the same clause's per-start-copy language). | A job CAN corrupt the fleet-wide cache for up to 30 minutes; the negative test loses its case 1. |

## 5. State left behind, and what the decision unblocks

- Live: hardlink seed from root-owned generations; `UV_LINK_MODE=copy`;
  per-volume lock files; negative test case 1 red by design; the gauges
  and triggers on the new root; the old root `/var/cache/ci-runner/warm`
  retired after the passing seeded job. Git equals live once the
  follow-up livespec-dev-tooling PR (`fix/warm-seed-ownership-revert`)
  merges and is host-applied.
- `livespec-lvtu` criteria: (1) master — met; (2) live seed under 1 s /
  100 MB — 3 s / 135–282 MB on the untrimmed generation, so F2-gated as
  the PR said; uv hits the cache as the job's uid — met; (3) one clean
  reboot — pending until git equals live; (4) evidence — journaled.
- The decision in section 4 gates the remaining trust work, not F1's
  speed: F2–F4 (`livespec-41w4`, `livespec-44qx`, `livespec-1qpt`) and F5
  (`livespec-wm7c`) proceed on the hardlink seed as it stands, and (a)
  would change only the provisioner's setup script and the tier's
  filesystem underneath them.
