# Verifying the restore — risk assessment, and the test that settles it

Written 2026-08-28, after Phases 3 and 4 completed. **Read this before running
`restore.sh` for real, and before scheduling the Phase 6 rebuild.**

> **UPDATE 2026-08-28 (later the same day): the rehearsal in "The test that
> settles it" was executed. `restore.sh` was fixed and then run end-to-end
> against `sda3`, steps 1–4 all passing. See "## Rehearsal result" at the
> bottom. The section below records the pre-rehearsal risk position; it is kept
> intact for the record, but "runs to completion" is no longer a hypothesis —
> it was measured. The one thing still un-measured is step 5, an actual boot.**

## Bottom line

The **backup** is verified. The **restore** is not, and the gap between those
two is the whole risk.

`restore.sh` has **never been executed — not once, not even dry-run.** Every
green signal so far is about the backup. A backup that has never been restored
is a hypothesis. *(Pre-rehearsal statement — superseded by the rehearsal
result below.)*

## Calibrated confidence, as of 2026-08-28

| Claim | Confidence | Basis |
|---|---|---|
| The data on the USB is complete and correct | **~95%** | exit 0 on all three passes; a full re-run completed in **96 s for 18 G**, which is only possible if rsync was confirming existing files rather than copying. Flags preserve hardlinks, ACLs, xattrs, numeric ownership |
| `restore.sh` runs to completion without intervention | **~50%** | ~80 lines of never-executed bash |
| The restored system boots unaided | **~60%** | grub-install-in-chroot and ESP detection are both untested |
| Failure is recoverable with manual work | **~97%** | the data is demonstrably present; worst case is fixing fstab/GRUB from rescue media |
| Catastrophic unrecoverable loss | **~2%** | dominated by "pointed at the wrong target", which the script's refusals guard against |

**The most relevant calibration input is this session's own error rate on bash.**
Three real defects shipped and were caught by the maintainer, not by testing:
`pipefail` silently truncating the backup after one of three passes; rc=23
misclassified as tolerable, which accepted an incomplete backup as success; and
`--delete` failing to purge excluded paths, stranding 13 G. **All three looked
correct on reading.** `restore.sh` is longer, more conditional, and has had zero
execution. Assuming it is correct because it reads correctly would repeat
exactly the mistake that produced those three.

## Known gaps in `restore.sh`, in priority order

**1. It drops the `/var/cache/ci-runner` volume and both bind mounts.**
`restore.sh` regenerates `/etc/fstab` from the target's real UUIDs — necessary,
because stale UUIDs are the most common reason a restored system will not
boot — but it writes **only root and the ESP**. The cache volume and the two
containerd/PVC bind mounts are silently absent. The script prints a warning and
relies on a human reading it.

**This should be fixed before the test restore**, so the test exercises the
version that would actually be used. Fixing it means reconstructing all
filesystems from `meta/fstab.txt` and `meta/blkid.txt` rather than just root.

**2. ESP detection is a first-match guess.**
`lsblk -lno PATH,PARTTYPENAME | awk '/EFI System/{print $1; exit}'` takes the
first EFI System Partition it finds. With a USB drive attached, or more than one
disk present, that may not be the right one. Untested.

**3. `grub-install` failure is warned about, then execution continues.**
That is arguably correct for a script a human is watching, and arguably wrong
for one run under pressure. The test restore will show which.

**4. The captured backup is a slightly blurry snapshot.**
It was taken while CI was live — a job started mid-run. Volatile paths are now
excluded so they cannot fail the backup, but `/` was not quiesced. **For the
real pre-rebuild backup, halt the fleet first and re-run**, so the captured
state is coherent rather than mid-job.

## The test that settles it — and it is free

The host has spare partitions that the maintainer has already confirmed are
disposable: **`sda2` (32 G)** and **`sda3` (125 G)**, both holding an old
GitLab-Kubernetes install, plus **531 G unpartitioned**. So a full end-to-end
restore can be rehearsed **at zero risk to the running system**.

1. **Fix gap 1 first** — make `restore.sh` reconstruct every filesystem from
   `meta/fstab.txt`, not just root and ESP. Otherwise the rehearsal validates a
   script nobody would use.
2. `mkfs.ext4` on **`sda3`** (125 G — comfortably larger than the 18 G rootfs),
   mount it at a scratch path.
3. Run `restore.sh /mnt/testrestore`. Record whether it completes, and what it
   exits with.
4. **Inspect the result**: does `/etc/fstab` list every filesystem? Is there a
   kernel at `/boot/vmlinuz-*`? Did GRUB install? Do ownership and permissions
   on a sample of files match the live system?
5. **Optionally, and this is the only test that truly settles it — add a GRUB
   entry and boot it.** Everything short of booting is inference.

Completing steps 1–4 should move "runs to completion" and "boots unaided" from
~50–60% to **~90%**. Completing step 5 makes it a measurement rather than an
estimate.

## Why this is not optional

Phase 6 destroys `/dev/sda`, which carries `/boot/efi`, `/`, and
`/var/cache/ci-runner`. After that point the USB volume is the only copy of this
system that exists. Discovering a restore bug then means discovering it with no
fallback.

The rehearsal costs one `mkfs` on a partition already agreed to be disposable.
Treat it as a Phase 4 completion requirement rather than a nice-to-have.

## Rehearsal result — 2026-08-28

The rehearsal was executed. Steps 1–4 all passed; step 5 (an actual boot) was
deliberately not attempted this session. The fixed script is committed beside
this note as `research/restore.sh` (it had lived only on the USB volume, which
Phase 6 wipes).

### Gap 1 fixed, and a fresh bug caught before it could ship

`restore.sh` was rewritten so fstab regeneration **preserves every captured
filesystem**, not just root and the ESP: it rewrites only the root (and, when an
ESP is supplied, the ESP) line to the new disk's real UUID, carries swap, the
`/var/cache/ci-runner` volume, and both containerd/PVC bind mounts through
verbatim, and marks `nofail` — with a printed remap list — any `UUID=` volume
whose captured UUID no longer resolves, so a missing device cannot wedge the
boot.

That new logic was proven **offline first**, against the real captured fstab,
under two scenarios (UUIDs that still resolve → rehearsal; UUIDs gone → real
rebuild). The offline test caught a genuine defect that *read as correct*: the
"already has `nofail`?" check inspected the wrong field (the fs **type**, not
the options column), so `/mnt/usb-backup`'s existing `nofail` was appended a
second time (`defaults,nofail,noatime,nofail`). Fixed to read options as field
4 of the line. This is the fourth "looked correct on reading" defect of this
plan's scripting work, and the first caught by a test rather than by the
maintainer — vindicating the verification plan's core warning.

### Gap 2 hardened — the live ESP is now structurally protected

The old ESP detection grabbed the first EFI System Partition globally. On this
host that is the **live `sda1` ESP**, so the original bootloader step would have
written to the running boot chain and EFI NVRAM during a rehearsal. The rewrite:
the bootloader step runs only against an ESP named explicitly (`ESP_DEV=`),
refuses an `ESP_DEV` that is the currently-mounted `/boot/efi`, and is skipped
wholesale under `SKIP_BOOTLOADER=1` (the safe rehearsal default, which prints
the exact manual bootloader commands for the real restore instead).

### What the rehearsal measured (mkfs.ext4 sda3 → mount → `SKIP_BOOTLOADER=1 restore.sh`)

- **Ran to completion**, reached `=== restore complete ===`, zero rsync errors
  in the full log.
- **fstab correct**: root remapped to sda3's real UUID
  (`7a41175e-…`); ESP left un-remapped and commented (no ESP supplied); swap,
  the cache volume, both bind mounts, and the USB entry all preserved; no remap
  warnings (the cache/USB UUIDs still resolve on the live host — the
  resolve-path branch). Original kept at `/etc/fstab.restored-original`.
- **Boot artifacts present**: `vmlinuz-7.0.0-29/-30` and both initrds under
  `/boot`.
- **Ownership/permission fidelity exact**: `etc/shadow` 640, `root` 700, and —
  the security-load-bearing check — setuid preserved on `passwd`/`chsh`
  (`-rwsr-xr-x`), symlinks preserved (`usr/bin/sudo`).
- **Completeness**: 18 G ≡ 18 G; 222 793 restored files vs 222 791 in the
  source — a **+2** fully accounted for by `/lost+found` (from mkfs) and the new
  `/etc/fstab.restored-original`.
- **Live host untouched**: after unmount, `/`=sda4 and `/boot/efi`=sda1
  unchanged. The rehearsed rootfs remains on the disposable `sda3` (label
  `rehearsal-restore`) should a boot test be wanted before Phase 6 reclaims it.

### Revised confidence

"Runs to completion" moves from ~50% to **measured — it did**. "Boots unaided"
moves from ~60% to **~90%**: everything a boot depends on (a correct fstab, a
kernel/initrd, faithful ownership) is verified, but the GRUB install path was
deliberately not exercised (gap 2), so booting is still an inference. Step 5 —
add a GRUB entry for `sda3` and boot it — is the only thing that makes it a
measurement, and it is optional and separately gated because it touches the boot
menu of the live host.

## Step 5 executed — the restore was BOOTED — 2026-08-28

Step 5 is done. The rehearsed `sda3` restore was booted on the metal, with the
iDRAC virtual console as the recovery net, and it came up as a working system.
"Boots unaided" is now **measured, not inferred**.

**Method — a reversible one-shot boot (default stayed `sda4` throughout):**
temporarily un-hid the GRUB menu (`TIMEOUT 0→10`, style `menu`), added a custom
direct-kernel entry (`--id restore-rehearsal-sda3`) that loads `sda3`'s
`vmlinuz-7.0.0-30` with `root=UUID=<sda3>`, `update-grub`, then `grub-reboot`
that id — which sets `next_entry` for the NEXT boot only. os-prober was disabled
for the run so its flaky `sda3` chainload entry (it chainloads a bootloader the
rehearsal deliberately never installed) could not be chosen by mistake. After
the test, `/etc/default/grub` and `/etc/grub.d/40_custom` were restored
byte-for-byte from backups and `update-grub` re-run — the host was left exactly
as found.

**Result:**
- **Reboot #1 booted `sda3`.** `findmnt / → /dev/sda3`, kernel `7.0.0-30`. The
  restored system reached multi-user with **`ssh`, `k3s`, and `tailscaled` all
  active** — a fully functional clone (same hostname/machine-id, expected).
- **One failed unit, and it is the informative one: `swap.img.swap`.** `/swap.img`
  was **absent** on the restore — the backup *correctly* excludes swap contents,
  but the preserved fstab still names the swap file, so the swap unit failed and
  `systemctl is-system-running` read `degraded`. Harmless at runtime (the system
  runs without swap), but a real defect of the restore procedure that **only a
  boot could surface** — a file-inspection pass never would.
- **Reboot #2 returned cleanly to `sda4`.** The one-shot was consumed (verified
  `next_entry=` empty in `sda4`'s grubenv *before* rebooting), so a plain reboot
  booted the default. The real system came back `running`, k3s node `Ready`,
  zero failed units, swap intact (8 GiB) — confirming the swap gap is
  restore-specific, not a host problem.

**Fix applied.** `restore.sh` now recreates any swap FILE named in the restored
fstab that is missing after the rsync — sized from `meta/swap-size-bytes.txt`
(the backup now records the real size, 8 GiB) with an 8 GiB fallback, `chmod
600` + `mkswap`, leaving swap PARTITIONS (`/dev/…`/`UUID=`) alone. The swap
detection was unit-tested against mixed fstab lines. This closes the last defect
the boot surfaced; `restore.sh` on the USB and at `research/restore.sh` carry it.

**Remaining inference:** the bare-metal `grub-install` path (gap 2) is still not
exercised — this boot used a direct-kernel GRUB entry from the live disk's
bootloader, not a bootloader installed onto the restored disk. That path runs
for real in Phase 6/7, where the ESP is rebuilt and `restore.sh` is invoked
without `SKIP_BOOTLOADER`. Everything the OS itself needs to boot is now proven.
