# Phase 3/4 — the backup, and how to run and watch it

Built 2026-08-28 on `poweredge-xubuntu`. This is the operational record: the
exact commands, where they live, what the flags are for, and the mistakes made
building it that are worth not repeating.

**The array is the boot volume**, so this backup is a hard prerequisite for the
Phase 6 rebuild, not a precaution.

## The commands

Everything lives on the USB volume itself, so it travels with the data.

```bash
# run the backup (three rsync passes, logs with rsync's own percentage)
sudo /mnt/usb-backup/run-backup.sh 2>&1 | tee /mnt/usb-backup/rsync.log

# or detached, surviving an ssh drop:
sudo nohup sh -c "/mnt/usb-backup/run-backup.sh 2>&1 | tee /mnt/usb-backup/rsync.log" &

# watch it
tail -f /mnt/usb-backup/rsync.log
tail -f /mnt/usb-backup/rsync.log | tr '\r' '\n'   # one line per update

# restore onto a freshly-installed system
sudo /mnt/usb-backup/restore.sh /target
```

`rsync --info=progress2` prints the running percentage. Its `\r` makes
`tail -f` overwrite in place, which is what you want on a terminal; pipe
through `tr` if you would rather have a scrolling log.

## The USB volume

| | |
|---|---|
| Device | `/dev/sdb1`, Toshiba MQ04UBF100, 1 TB, 5400 rpm USB 3.0 |
| Filesystem | **ext4**, label `POWEREDGE-BACKUP`, mounted at `/mnt/usb-backup` |
| fstab | `UUID=… /mnt/usb-backup ext4 defaults,nofail,noatime 0 2` |
| Capacity | 916 G usable against a ~42 G source |

**`nofail` is load-bearing**: without it, booting with the drive unplugged
hangs the machine — a genuinely bad failure mode for a backup target.

**The drive had to be reformatted.** It arrived carrying an Apple Partition Map
whose main partition held no recognizable filesystem, yet had real data in it
(non-zero at 1 GB, 10 GB and 100 GB offsets). That was surfaced to the
maintainer, who confirmed the contents were disposable; only then was it wiped
to GPT + ext4. **ext4 is not a preference here** — HFS+, exFAT and NTFS cannot
carry Linux ownership, permissions, symlinks, hardlinks or xattrs, so a backup
onto any of them looks complete and cannot restore a bootable system.

## What gets copied, and the flags

Three passes, one per filesystem, because `--one-file-system` deliberately
refuses to cross mount boundaries:

| Pass | Source | Destination |
|---|---|---|
| 1 | `/` (sda4) | `rootfs/` |
| 2 | `/boot/efi` (sda1, vfat) | `boot-efi/` |
| 3 | `/var/cache/ci-runner` (sda5) | `var-cache-ci-runner/` |

```
-aHAXS --numeric-ids --delete --info=progress2 --one-file-system
```

- **`-a`** archive: recurse, symlinks, perms, times, group, owner, devices.
- **`-H`** hard links. The relocated containerd overlay store is full of them;
  without this the copy balloons and the snapshot layout breaks.
- **`-A`** ACLs. **`-X`** extended attributes — overlayfs and security contexts
  live there. **`-S`** sparse files.
- **`--numeric-ids`** do NOT remap uid/gid through name lookups. Essential when
  restoring onto a fresh install whose `/etc/passwd` ordering may differ;
  without it ownership silently shifts.
- **`--one-file-system`** so a stray mount — or the USB drive itself — is never
  swept in.

`-a` already implies `-l`, so the `-vlaP` form is both redundant and missing
`H`/`A`/`X`/`--numeric-ids`. For a rootfs backup those four are the difference
between a copy and a restorable system.

**Excluded:** `/swap.img` (8 G of swap file, not data) and `/lost+found`.

Alongside the data, `meta/` captures what a restore needs and the bytes do not
carry: `sfdisk -d /dev/sda`, `blkid`, `fstab`, `dpkg --get-selections`, enabled
systemd units, `uname`, os-release, `ip addr`, and the k3s version.

## Size accounting — check this, do not eyeball it

```
du -sx /            37.2 GiB
/swap.img            8.0 G   deliberately excluded
                    -------
expected on USB     ~29.2 G   ✓ matches the 29 G present
```

An unexplained shortfall in a backup is exactly the wrong thing to wave
through. It reconciles exactly.

One wasteful inclusion, deliberate for now: `/` still holds
`containerd.premove` (12 G), the rollback copy from the containerd relocation,
and it gets backed up. **Once the relocation is confirmed stable, deleting the
`.premove` directories shrinks both `/` and the backup by 12 G.**

## Mistakes made building this

Recorded because each cost real time and would recur.

**1. `set -euo pipefail` silently truncated the backup.** rsync exits **24**
when a file vanishes mid-transfer — routine on a live system (here a
`ci-warm-cache` pod log rotating away), and benign. Under `pipefail` that code
propagated and killed the script after the rootfs pass. The ESP and cache
passes **never ran, and nothing said so**: the log simply ended. `run-backup.sh`
therefore does **not** use `set -e`, and prints each pass's `rc` instead. Codes
**23** (partial) and **24** (vanished) are expected; anything else is real.

**2. An ssh-launched job survives the client being interrupted.** Ctrl-C on the
local side killed the tool call, not the remote process. Relaunching created
**two concurrent `rsync --delete` runs against the same destination**, which can
corrupt it. Always check `pgrep -x rsync` before starting a pass.

**3. `pgrep -f "backup.sh"` matches the ssh command that greps for it.** The
search string appears in the invoking command's own argv, so the check reports a
process that is only itself. Use `pgrep -x rsync`, or a pattern that cannot
match the caller.

**4. A size-derived "percent complete" is useless on a verification pass.**
Because the data is already at rest, it pins near 100% and never moves, which
correctly reads as broken. **Use rsync's own `--info=progress2`** rather than
deriving progress from `df`. The honest signal on a re-run is `xfr#N`: a *low*
count means rsync is confirming files already match, which is what a good
backup looks like the second time.

## Phase 4 — verifying

**Re-run `run-backup.sh`. The second run must transfer almost nothing.** That
effective no-op is the acceptance test: a large second transfer means the first
pass was incomplete or an exclude is wrong. Check `Number of regular files
transferred` per pass, and that all three passes report `rc=0`, `23` or `24`.

Then dry-run the restore path — `rsync -n` from `rootfs/` against a scratch
target — and confirm it is also near-silent.

## restore.sh — the interface and its refusals

```bash
sudo /mnt/usb-backup/restore.sh /target
```

One command, one argument: the mounted root of the new install.

**It does not partition anything.** Create and mount the target filesystems
first; the script only fills them. That separation is deliberate — an
auto-partitioning restore script is one typo from destroying the wrong disk.

It **refuses** when the target is not a directory, is not a mountpoint, is `/`
itself, or contains `/proc/1` (a live system), and requires typing `RESTORE` to
proceed. Those checks are not ceremony: a restore is run under pressure, and the
failure mode is unrecoverable.

After copying it **regenerates `/etc/fstab` from the new disk's real UUIDs** —
the old UUIDs will not exist after a rebuild, and a stale fstab is the single
most common reason a restored system will not boot — keeping the original at
`/etc/fstab.restored-original`. Then it reinstalls GRUB in a chroot and prints
what to check before rebooting.

The CI cache is **not** restored automatically; it is a reconstructible image
store, and the command to restore it is printed at the end.
