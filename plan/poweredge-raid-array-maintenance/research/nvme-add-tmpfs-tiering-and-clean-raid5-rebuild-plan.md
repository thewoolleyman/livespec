# Execution plan — add an NVMe tier, move the CI datastore to tmpfs, and rebuild the RAID-5 array clean

Maintainer-decided 2026-09-02, in session with the maintainer. This note is the
executable successor to the original "Phase 6" (which assumed a RAID-5 → RAID-10
migration). **That RAID-10 migration is dropped.** The array stays **RAID-5**;
what changes is where each *kind* of data lives, plus a one-time clean rebuild of
the array to reclaim stranded space.

Host: `poweredge-xubuntu` (Dell PowerEdge R630, PERC H730 / MegaRAID SAS-3 3108,
8× 2.5" SATA bays, one free PCIe 3.0 x16 slot — Slot 1). Epic: `livespec-g52yrb`.

## Plain-language bottom line

The machine's disk problem was never bandwidth — it was **fsync latency**: many
CI jobs writing to one shared RAID-5 SATA array drove it to a ~100 ms,
~1000-IOPS ceiling, which stalled the Kubernetes datastore and took CI admission
down (see `ci-runner-pod-lifecycle-reliability` note 003). The fix is to stop
sharing one disk for three different workloads, and give each the right medium:

1. **The tiny, hot, rebuildable Kubernetes datastore → RAM (tmpfs).** ~150 MB.
   `fsync` to RAM is essentially free, so the stall disappears entirely. On
   reboot the datastore is empty and the CI cluster is rebuilt from Git.
2. **The large, write-heavy, disposable data (container image layers + per-job
   runner work volumes) → a new NVMe drive** in the free PCIe slot — an order of
   magnitude faster than SATA, and off the array entirely.
3. **The read-mostly bulk (warm caches, base images) → the RAID-5 array**, which
   is exactly what a big redundant volume is good at once the write-hot tenants
   leave.

No data is put anywhere it can be lost that matters: the **host OS itself stays
on the durable RAID array** the whole time; only the ~150 MB CI-cluster
datastore is volatile, and it is reconstructed from Git.

## Definitions (so this reads without infra background)

- **RAID-5 / RAID-10**: ways of spreading data across disks. RAID-5 = one disk's
  worth of parity, survives one failure, maximizes usable space. RAID-10 =
  mirrored pairs, survives more failures but halves usable space. We are keeping
  **RAID-5** because the write-heavy work is leaving the array, so RAID-10's only
  advantage (write speed) no longer buys anything, and RAID-5 gives more room.
- **kine / the "datastore"**: k3s (the lightweight Kubernetes on this host) keeps
  *all* Kubernetes cluster state — every Deployment, ConfigMap, Secret, the ARC
  runners, Kueue's queues — in a single SQLite database via a shim called *kine*
  (`/var/lib/rancher/k3s/server/db/state.db` + its write-ahead log). This is the
  ~150 MB that moves to tmpfs.
- **tmpfs**: a filesystem that lives in RAM. Fast, and **empty after every
  reboot**.
- **GitOps / "converge"**: cluster configuration lives in Git; a *converge*
  step (`helm upgrade --install` + `kubectl apply`) re-applies it to the cluster.
  It only ever creates/updates objects — it never deletes and never touches host
  files — so a bug in it can at worst leave the CI cluster half-built, never harm
  the host.
- **`fsync`**: the system call that forces a write to durable storage before
  returning. On a slow shared disk it is what stalled; on RAM it is ~free.

## The decisions, locked

| # | Decision |
|---|---|
| 1 | **Array stays RAID-5.** No RAID-10 migration. |
| 2 | **Full destructive rebuild** of the array (not an online expansion) to get clean, full-size partitions and reclaim the stranded space. |
| 3 | **Add NVMe in Slot 1** (the only free slot; the SATA bays cannot host NVMe). *Amended 2026-09-02 at purchase:* **two 4 TB drives on one dual-M.2 switch card, JBOD (no RAID), one LVM VG per drive** — see "Purchase — RESOLVED" below. |
| 4 | **CI datastore (kine) → tmpfs**, rebuilt-on-boot from GitOps. Owned by the `ci-runner-pod-lifecycle-reliability` plan. |
| 5 | **No `mdadm` write-behind mirror.** With kine in tmpfs, the NVMe holds only rebuildable/disposable data, so a live SATA fallback would only re-impose write load on the array for no benefit. |
| 6 | **NVMe boot is temporary scaffolding.** During the array's downtime the OS runs from an NVMe clone; afterward the OS returns to the redundant RAID-5. NVMe's steady-state job is the container/work tier. |

## Blast radius — what a bug can and cannot do

This was the maintainer's explicit worry ("is the machine bricked if the rebuild
script has a bug?"). It is not, and the reasoning is worth stating in the plan:

- **The host OS is never on tmpfs.** Kernel, systemd, sshd, `/etc`, `/home`, the
  RAID array — all on durable disk, untouched by any of this. After a reboot the
  box is a fully working Linux host you can SSH into regardless of cluster state.
- **The converge only creates/updates** (`helm upgrade --install`, `kubectl
  apply`); it never deletes and never writes host files. Worst case from a
  converge bug is "CI cluster objects wrong or missing," fixed by re-running the
  corrected converge — the same one-minute operation already done live by hand.
- **The rebuild/converge cannot block boot** — it is a separate one-shot systemd
  unit; if it fails, boot still completes.
- **The one real caveat is the tmpfs mount itself.** A bad `/etc/fstab` line can
  make systemd wait on a mount at boot. Mitigation: mark the tmpfs mount
  **`nofail`** so a mount hiccup can never hold up boot, and test it once before
  relying on it. This is the only part of the design that can affect *booting*,
  and it has a one-line fix.

## Steady-state storage tiering

| Tier | Medium | Data | Owning plan |
|---|---|---|---|
| Datastore | **tmpfs (RAM)** | kine `state.db` + WAL (~150 MB) | `ci-runner-pod-lifecycle-reliability` |
| Hot bulk | **NVMe ×2 (JBOD, LVM VG per drive)** | containerd image layers (`…/agent/containerd`) on drive A; runner work volumes (`…/k3s/storage`) on drive B — dedicated IO per tenant | this plan |
| Cold bulk | **RAID-5 array** | warm caches (`/var/cache/ci-runner/warm`), base images, OS | this plan |

The device→path binding is already designed to make this a **mount change, not a
k3s reconfiguration** — `containerd-relocation-completed.md` put containerd and
the local-path storage behind fixed mount points via `/etc/fstab` bind mounts
specifically so "moving them to different media — a rebuilt array, an NVMe, a
tmpfs tier — becomes a remount." So retiering is re-pointing those bind mounts,
not editing GitOps.

## Phased execution

Phases 3–5 of the original plan (make the bootable backup, verify it, prove the
restore boots on the metal) were **already completed and proven 2026-08-28** —
the backup boots (`restore-verification-plan.md` step 5, booted from `sda3` via
iDRAC). This plan reuses that machinery verbatim.

### Phase A — Install the NVMe and clone the OS onto it (bootable)

1. **Maintenance window (power down, open chassis)** to seat the low-profile
   PCIe→M.2 adapter + NVMe in Slot 1. Unlike the hot-swap SATA drives, the PCIe
   card is not hot-pluggable, so this is the one required downtime. (The two new
   SATA trays can be inserted in the same window.)
2. **Clone the CI Xubuntu system onto the NVMe using the *exact* prior rsync
   procedure** (`phase3-backup-and-restore-procedure.md` + `restore.sh`). The
   procedure is: three per-filesystem passes with
   `rsync -aHAXS --numeric-ids --delete --info=progress2 --one-file-system`
   (the `-H` for hardlinks and `-X` for xattrs are load-bearing for the
   containerd overlay store), the documented exclude set (`/swap.img`,
   `lost+found`, the per-job `k3s-storage/` PVC scratch, `/var/log/pods/`,
   `*.premove`), and `restore.sh` to lay it down and **regenerate `/etc/fstab`
   from real UUIDs** (`blkid`) — stale UUIDs are "the single most common reason a
   restored system will not boot."
3. **Drop the old GitLab volumes.** `sda2` (PARTLABEL `old-gitlab-k8s`) and
   `sda3` (PARTLABEL `new-gitlab-k8s`) are the maintainer-confirmed disposable
   old-GitLab pair; the clone does not include them. Reclaims ~690 GB.
4. This is the first time the **real `grub-install` onto the restored disk** runs
   (the 2026-08-28 rehearsal used a direct-kernel GRUB entry with
   `SKIP_BOOTLOADER=1`; here `restore.sh` runs *without* it, with `ESP_DEV`
   pointing at an ESP on the NVMe).

### Phase B — Prove the machine boots from the NVMe and runs CI

Boot the host from the NVMe clone (reversible one-shot boot entry first, as in
the rehearsal, then commit). Confirm SSH, k3s, tailscaled, and a real CI job.
The box is now running entirely off the NVMe with the RAID array idle and
detachable.

### Phase C — Rebuild the RAID-5 array clean + health maintenance

With the OS running from the NVMe, the array holds nothing live:

1. Destroy and recreate the VD as **RAID-5 across the drives** with a **clean,
   full-size partition layout** (no stranded ~690 GB, no leftover GitLab
   partitions). 5-drive RAID-5 ≈ **3.5 TB usable**.
2. Run **`fstrim`/TRIM** and any controller-level SSD health maintenance during
   the downtime (the array is empty, so it is the free moment for it).
3. Recreate the filesystems and the mount points the GitOps expects
   (`/var/cache/ci-runner` and the containerd/storage bind-mount targets).

### Phase D — Return to steady state

1. Move the **OS back onto the redundant RAID-5** (rsync back, `restore.sh`
   fstab/grub regen), so the durable, redundant medium carries the OS — NVMe is
   not a permanent single-point-of-failure for booting.
2. Re-point the bind mounts so the **hot bulk (containerd + work volumes) lands
   on the NVMe** and the **cold bulk (warm cache, base images) on the array**.
3. Flip the **kine datastore to tmpfs** (`nofail`) once the tmpfs converge gate
   below is proven.

## Required companion work — configurable storage location

The GitOps in `livespec-dev-tooling` (`ci-runner/k3s/`) is **not** hardcoded to
`/dev/*` (there are zero device references in it). But it *does* assume the
`/var/cache/ci-runner` filesystem path exists (the warm-cache `hostPath`s in
`ci-runner/k3s/phase2/arc/hook-pod-template.yaml` and
`.../warm-cache/warm-cache-cronjob.yaml`) and it uses k3s **bundled defaults**
for the containerd data-root and the local-path storage dir (no `--data-dir`
override in `ci-runner/k3s/provision-k3s.sh`).

So the "make mounts configurable" requirement (maintainer directive) refines to:
**parameterize the storage *location*** — the containerd data-root, the
local-path storage dir, and the bind-mount targets — so the tier a given
workload lands on (array vs NVMe vs tmpfs) is a config choice, not a hardcoded
path. This is a `livespec-dev-tooling` work-item to be filed as a child of this
epic.

## Cross-plan dependency and acceptance gate

The tmpfs flip depends on the `ci-runner-pod-lifecycle-reliability` plan's
reconstruct-on-boot automation. As reported by that plan's session, the relevant
work-items are: **`olp4c5` + `qqzlek`** (the converge automation that rebuilds the
cluster from Git) and **`mx26zz`** (the datastore-to-tmpfs flip itself — a
separate, reversible step). These ids are owned by the sibling plan and should be
confirmed against the ledger before linking.

**Acceptance gate for Phase D step 3:** kine flips to tmpfs only once "**boot with
an empty datastore → full CI cluster back from Git**" is proven, including the
bootstrap that a wipe would otherwise take out — the GitOps controller itself,
secret sourcing, k3s auto-deploy manifests, and the node-local config that is
already reapplied by its own units (the `ci-runner.io/churn-slot` capacity via
`ci-runner/k3s/phase2/node-extended-resource/` and the `fs.inotify` budget via
`ci-runner/k3s/phase2/node-inotify-budget/`). Until that is proven, the datastore
can sit on durable disk (array or NVMe) with all the rebuild automation still in
place as a safety net — the value is independent of the tmpfs flip.

## Scope

**Requirement carriers (this plan / epic `livespec-g52yrb`):**
1. NVMe drive + low-profile PCIe→M.2 adapter procured and seated in Slot 1.
2. Bootable NVMe clone via the proven rsync/`restore.sh` procedure; boot proven.
3. Clean RAID-5 rebuild with full-size partitions + TRIM/health maintenance.
4. OS returned to the array; hot/cold bulk retiered onto NVMe/array via bind
   mounts.
5. Configurable storage-location work-item filed against `livespec-dev-tooling`.

**Explicit deferrals:**
- **tmpfs datastore flip (`mx26zz`)** and the **reconstruct-on-boot automation
  (`olp4c5`/`qqzlek`)** belong to `ci-runner-pod-lifecycle-reliability`, not this
  plan. This plan *depends on* the acceptance gate above but does not own that
  work.
- **RAM-backed *work volumes* (`livespec-trxcf7`)** remain rejected/deferred
  (2026-09-01): work volumes are too large for RAM and go on NVMe. Only the tiny
  datastore is a tmpfs candidate. Do not conflate the two.
- **RAID-10** is dropped, not deferred.

## Purchase — RESOLVED 2026-09-02: two-drive JBOD split, ordered

Superseding the single-2TB spec below (kept for the reasoning trail): the
maintainer ordered a **two-drive, no-RAID (JBOD) build** the same day —

- **2× WD_Black SN8100 4 TB** (`WDS400T1X0M`, M.2 2280, single-sided,
  6.5–7 W) — $659.99 each.
- **1× StarTech PEX8M2E2 dual-M.2 adapter** (ASMedia **ASM2824 PCIe switch** —
  needs NO BIOS bifurcation; x8 Gen3 uplink; low-profile bracket included) —
  $169.99.

Design: the card goes in Slot 1 (Gen3 **x8 electrical**, x16 connector —
matches the card's x8 uplink exactly); each drive gets a dedicated Gen3 x4
(~3.5 GB/s) behind the switch, 2×3.5 ≈ 7 GB/s under the ~7.9 GB/s uplink — no
oversubscription. **No RAID: one LVM VG per physical drive**, splitting the two
write-heavy tenants so they cannot contend — **containerd image layers on
drive A, runner work volumes on drive B** — 8 TB total. LVM gives online
grow/`pvmove`/`vgextend` so future volumes never require a rebuild. **Address
PVs by `/dev/disk/by-id` (or wwid), never `/dev/nvme0n1` ordering** — the
switch renumbers PCI buses and enumeration order can shift across boots.

An independent adversarial fit-verification (separately-spawned reviewer,
read-only against the live host + vendor docs, 2026-09-02) returned
**PASS-WITH-CAUTIONS — no blocker**. Install-day checklist from it:

1. **MANDATORY: swap the PEX8M2E2 to its included low-profile bracket** — it
   ships with the full-height bracket attached, and Slot 1 is **low-profile,
   half-length** (card 159 mm < 167.65 mm limit — fits).
2. Eyeball that **Riser 2** (which carries Slot 1) is physically present when
   the lid is open — every remote signal says yes (SMBIOS slot record, `Riser
   Config Err: ok`), but no discrete riser-2 presence sensor exists.
3. Both CPUs populated (Slot 1 hangs off CPU1 root port `00:03.2` — link-capable,
   currently down); UEFI, BIOS 2.18.1, kernel `7.0.0-30` carries the mainline
   ASM2824 retrain quirk; no driver needed — drives appear as two independent
   NVMe controllers.
4. Expect `LnkSta` **8 GT/s x8** on the card and **8 GT/s x4** per drive — that
   is correct, not a fault.
5. **Check `nvme smart-log` temps under the first sustained CI load** — the
   drives and card ship with no heatsinks; likely fine at Gen3 speeds in R630
   airflow, but this is now load-bearing because the host's iDRAC
   third-party-card cooling response was DISABLED on 2026-09-02 (idle fans
   ~7.5k → ~3.9k RPM; recorded with re-apply/revert commands in the
   `poweredge-xubuntu-info` repo, `FAN_COOLING.md`). If a drive runs
   persistently > ~70 °C, add low-profile M.2 heatsinks (must stay within the
   slot's LP envelope).
6. Correction to earlier research: the PSUs are **2× 495 W redundant** (not
   1176 W); headroom still ample (~230 W projected vs 495 W).

### Original sizing reasoning (superseded, kept for the trail)

Because kine moved to tmpfs and the mirror is dropped, the NVMe no longer needs
**power-loss protection** (the fsync-critical datastore left for RAM) and the
960 GB enterprise option is now *under*-sized. The NVMe now holds container
layers + work volumes, so the spec shifts to **capacity + sustained write +
endurance**: a 2 TB DRAM-backed consumer NVMe was the initial pick; the
maintainer then chose the two-drive 4 TB JBOD split above for per-workload IO
isolation and 8 TB headroom at 64-runner concurrency.

## Read-first chain

- The disk-latency root cause and the tmpfs rationale:
  `plan/ci-runner-pod-lifecycle-reliability/research/003-kine-stall-drops-kueue-webhook.md`
  and `.../004-what-sysstat-recorded-for-the-array.md`.
- The proven rsync backup + bootable restore procedure to replicate exactly:
  `phase3-backup-and-restore-procedure.md`, `restore.sh`,
  `restore-verification-plan.md`.
- Why retiering is a mount change, not a k3s reconfig:
  `containerd-relocation-completed.md`.
- The controller's supported reconstruction paths (why RAID-10 needs
  destroy+recreate; RAID-5 stays): `phase0-controller-management-and-tooling.md`.
- Hardware compatibility for the drives and the free PCIe slot:
  `drive-expansion-compatibility-proof.md`.
