# Verifying the restore — risk assessment, and the test that settles it

Written 2026-08-28, after Phases 3 and 4 completed. **Read this before running
`restore.sh` for real, and before scheduling the Phase 6 rebuild.**

## Bottom line

The **backup** is verified. The **restore** is not, and the gap between those
two is the whole risk.

`restore.sh` has **never been executed — not once, not even dry-run.** Every
green signal so far is about the backup. A backup that has never been restored
is a hypothesis.

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
