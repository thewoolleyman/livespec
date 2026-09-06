# CI churn relocated off `/` — done and verified

Performed 2026-08-28 on `poweredge-xubuntu`, maintainer-directed. This is the
"full optimization with existing drives" work, and it is complete.

**Note the honest framing: this delivers no throughput improvement.** `sda4`
and `sda5` are partitions of the same virtual disk on the same three drives
behind the same controller, so moving bytes between them changes no physical
property. It was done for blast radius and for what it makes possible later.

## What changed

| Path | Now backed by |
|---|---|
| `/var/lib/rancher/k3s/agent/containerd` | `/dev/sda5[/k3s-containerd]` (bind mount) |
| `/var/lib/rancher/k3s/storage` | `/dev/sda5[/k3s-storage]` (bind mount) |

Two fstab entries, both carrying
`x-systemd.requires-mounts-for=/var/cache/ci-runner` so systemd orders them
after the volume they live on:

```
/var/cache/ci-runner/k3s-containerd /var/lib/rancher/k3s/agent/containerd none bind,x-systemd.requires-mounts-for=/var/cache/ci-runner 0 0
/var/cache/ci-runner/k3s-storage    /var/lib/rancher/k3s/storage          none bind,x-systemd.requires-mounts-for=/var/cache/ci-runner 0 0
```

## Why, given it makes nothing faster

1. **Blast radius.** CI churn previously wrote to the root filesystem, so a
   runaway job filling `/` took down the OS and k3s, not just CI. A dedicated
   filesystem contains that.
2. **It converts the future fix into a mount change.** With containerd and the
   PVC root at known mount points, moving them to different media — a rebuilt
   array, an NVMe, a tmpfs tier — becomes a remount rather than a k3s
   reconfiguration. This is what makes Phase 7's layout cheap.

This was the outstanding half of `livespec-s43svm.2`, which was re-scoped in
2026-08 and delivered a warm `uv` cache on sda5 without moving containerd or the
local-path provisioner.

## Procedure actually used

1. Recorded the image list for later comparison: **174 images**.
2. `systemctl stop k3s`, then `k3s-killall.sh` — **45 mounts** remained after the
   stop and had to be cleared; `lsof +D` then showed 0 open files under
   containerd. Do not skip this: copying a live containerd store is meaningless.
3. `rsync -aHAX --numeric-ids` of the 12 G store to sda5. **`-H` and `-X` are
   load-bearing** — containerd's overlayfs snapshots are built on hardlinks and
   `trusted.overlay.*` xattrs, and a copy without them is silently broken.
4. Renamed the originals to `*.premove` rather than deleting them, so rollback
   was one `mv` away.
5. Added the fstab entries, `daemon-reload`, `mount -a`.
6. `systemctl start k3s`.

## Verification

| Check | Result |
|---|---|
| Entry count, source vs destination | **117,040 = 117,040** |
| `du -sh` source vs destination | **12 G = 12 G** — equal size proves hardlinks survived; a broken copy would balloon |
| Copy duration | 33 s |
| Mount source after bind | `/dev/sda5[/k3s-containerd]`, `/dev/sda5[/k3s-storage]` |
| k3s after restart | `active` |
| Images after restart | **174, list byte-identical to before** |

The equal `du` is the important one. It is the cheap test that distinguishes a
correct hardlink-preserving copy from one that silently exploded into
independent files.

## A correction to the plan's assumption

`plan-overview.md` and the characterization both describe the PVC root as
**13 GB**, sized from a measurement taken under load. **It is 36 K at idle.**
The local-path PVC directory is transient — a running CI job creates thousands
of files there and the whole tree is deleted when the job finishes.

So the `k3s-storage` bind mount governs **where future PVCs land**; it moved no
meaningful data. This matters beyond bookkeeping: that same volatility later
broke a backup pass (see `phase3-backup-and-restore-procedure.md`), because
rsync cannot meaningfully copy a directory being deleted underneath it.

## Rollback, and the cleanup that followed

The originals were kept as `containerd.premove` (12 G) and `storage.premove`
until the relocation was shown stable. They were **excluded from the backup**
once it was clear they merely duplicated what `var-cache-ci-runner/` already
held, and the stranded copies were purged from the USB with
`--delete-excluded`.

**They still exist on `/`.** Deleting them recovers 12 G on `sda4` and is safe
once the bind-mounted layout has run through real CI. That is the one piece of
this work left outstanding, and it is deliberately not automatic.
