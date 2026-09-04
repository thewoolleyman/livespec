# The PEX8747 card cannot run the SN8100 at PCIe Gen3 — diagnosis, the Gen2 interim, and two gotchas

Recorded 2026-09-04 from the live NVMe install on `poweredge-xubuntu` (epic
`livespec-g52yrb`). Read this before touching the NVMe tier, before installing
the StarTech replacement card, and before running `fio` against a `by-id` path.

## Plain-language bottom line

The new NVMe card and drive were seated correctly and the machine sees them,
but the electrical link between the card's PCIe switch and the drive is
unreliable at the speed they first agree on (PCIe Gen3, 8 GT/s). Data still
arrives, but with so many retries that the drive delivered about 1 MB/s and
commands timed out. Forcing that one link one step slower (Gen2, 5 GT/s)
makes it perfectly clean and still about fifteen times faster than the array
ever needed. The machine now runs with that slower setting applied at every
boot. It is an interim: the different, better card already on order replaces
this one.

## Resolution 2026-09-04 — the StarTech PEX8M2E2 passes with the same drive; the card was the fault

The retry on 2026-09-04 (~17:00Z) seated the originally specified StarTech
PEX8M2E2 (ASMedia ASM2824 switch, Gen3 x8 uplink) in Slot 1 with the SAME
SN8100 that had failed on the PEX8747 (serial `25384T801085`; the second
SN8100 had not arrived). The link survey below passed on the first boot,
which settles the open question above: the drive is fine, the PEX8747 was
the fault.

| Check | StarTech PEX8M2E2 + SN8100, first boot | Acceptance |
|---|---|---|
| Card upstream `04:00.0` `LnkSta` | 8 GT/s x8 | rated width |
| Drive `08:00.0` `LnkSta` | 8 GT/s x4 ("downgraded" from its Gen5 `LnkCap`, expected) | Gen3 x4 |
| Endpoint `CESta` after clear + I/O | all `-` | all `-` |
| QD1 4k random read | 20.7k IOPS, avg 40 µs | tens of µs |
| QD32 4k random read | 245k IOPS | — |
| 1 MiB sequential read, QD16 | 3.5 GB/s | full Gen3 x4 |
| `dmesg` | no `nvme … timeout` | none |
| Drive temperature idle | 33–39 °C composite, sensor 1 50–54 °C | < 70 °C |

The switch's upstream port showed a sticky `AdvNonFatalErr+` from boot
enumeration; cleared once, it stayed clear under I/O. Topology: root port
`00:03.2` → ASM2824 upstream `04:00.0` → downstream ports `05:00.0`,
`05:04.0`, `05:08.0`, `05:0c.0` → drive `08:00.0`.

**What was then done (one drive, both tenants, label identity).** The
drive's stale VG `nvmea` from the Gen2 interim was wiped (`vgchange -an`,
`vgremove`, `pvremove`, `wipefs -a`), never reused. A fresh VG `nvmea` on
the by-id path got LVs `ci-containerd` and `ci-workvols` (1.5 TiB each,
~640 GiB unallocated), ext4 under temporary labels (`tmp-containerd` /
`tmp-workvols` on the day; the shipped tool uses `new-<suffix>`), a live
bulk rsync (13 GB in 40 s, 2.2 GB in 19 s), then the quiet window at
17:06–17:08Z with CI already routed to GitHub-hosted: k3s stopped, final
delta, dry-run verification with zero non-directory differences and
matching inode counts (123,758 / 386,900), unmount, relabel array volumes
to `old-containerd` / `old-workvols` and the NVMe volumes to the role
labels, `lvchange --refresh`, `mount -a` with fstab untouched, k3s started
plus the three `After=k3s` oneshots; 74 images before and after, 18 pods
Running, 0 failed units. A proving reboot at 17:08Z came up unattended at
17:12Z with every tier path on `/dev/mapper/nvmea-ci--{containerd,workvols}`,
the datastore on tmpfs, 74 images, link clean, 0 failed units.

That one-off script is now the reproducible tool
`ci-runner/k3s/phase2/storage-layout/migrate-tier.sh` in
`livespec-dev-tooling` (`prepare` / `cutover`), and the traps below are
`.ai/ci-node-storage-tiers.md` there. When the second SN8100 arrives,
`ci-workvols` moves to its own VG (`nvmeb`) with the same two commands.

## What was observed

| Condition | QD1 4k random read | 4k random write, QD32 x4 jobs | 1 MiB sequential write | PCIe error bits on the drive |
|---|---|---|---|---|
| Gen3 x4, card socket 1 (`05:09.0`) | avg 1.1 s (min 33 µs) | ~100 IOPS | ~1 MB/s | `RxErr+ BadTLP+ BadDLLP+ Timeout+`, re-set within seconds of clearing |
| Gen3 x4, card socket 4 (`05:11.0`) | driver probe FAILED (`CSTS=0x5`, admin timeout) | n/a | n/a | `RxErr+ BadDLLP+` |
| Gen2 x4, socket 1 | 39k IOPS @ 18 µs | 409k IOPS @ 308 µs | 1.7 GB/s sustained 20 s | all clear |
| Gen2 x4, socket 4 | 22k IOPS @ 33 µs | 407k IOPS @ 309 µs | 1.6 GB/s | all clear |

Kernel side at Gen3: `nvme nvme0: I/O tag … timeout, aborting req_op:WRITE`
bursts, then `Abort status: 0x0`; the socket-4 boot spent ~8 minutes in
`I/O tag 24 (0018) QID 0 timeout, disable controller` before giving up.
Retraining the link at Gen3 twice reproduced the fault both times. Disabling
autonomous power-state transitions and forcing power state 0 changed nothing.
No DMAR/IOMMU faults. `RxErr` is set on the ENDPOINT (the drive's receiver),
so the marginal direction is switch-transmit → drive-receive.

Why the kernel's own counters said zero: the root port (`00:03.2`) reports
`RootSta: CERcvd-` — correctable-error messages from behind the PLX switch
never reach it, so `/sys/bus/pci/devices/*/aer_dev_correctable` stays at zero
and `dmesg` carries no AER lines. Read the sticky status bits directly:

```bash
lspci -vvs <endpoint> | grep -E 'LnkSta:|CESta'
# clear them, run I/O, re-read: if they come back, the link is live-faulty
setpci -s <endpoint> ECAP_AER+0x10.l=0xFFFFFFFF
setpci -s <endpoint> CAP_EXP+0x0a.w=0x000F
```

Whether the DRIVE is also a factor is undetermined: the second SN8100 has not
been tried. The PEX8747 is 2012-era Gen3 silicon and the SN8100 is a Gen5
drive; Gen3 equalization between them is the most likely culprit, and it fails
on two of the card's four sockets, so the card is the common factor.

## The Gen2 cap (runtime recipe)

Target link speed is set on the switch's DOWNSTREAM port, not on the drive.
Link Control 2 is at PCIe-capability offset `0x30`; the retrain bit is bit 5 of
Link Control at offset `0x10`.

```bash
P=05:11.0                                   # the downstream port above the drive (re-derive from lspci -tv)
v=$(setpci -s $P CAP_EXP+0x30.w)
setpci -s $P CAP_EXP+0x30.w=$(printf %04x $(( (0x$v & 0xFFF0) | 2 )))   # 2 = 5 GT/s, 3 = 8 GT/s
lc=$(setpci -s $P CAP_EXP+0x10.w)
setpci -s $P CAP_EXP+0x10.w=$(printf %04x $(( 0x$lc | 0x20 )))          # retrain
sleep 2; lspci -vvs <endpoint> | grep -E 'LnkSta:|CESta'                 # expect 5GT/s x4, all '-'
```

If the driver already gave up (probe failed), rebind after capping:
`echo 0000:09:00.0 > /sys/bus/pci/drivers/nvme/bind`.

## The Gen2 cap at boot — tried, and why it CANNOT work

A boot-time cap was installed and then removed the same night: kernel cmdline
`modprobe.blacklist=nvme rd.driver.blacklist=nvme` (so the driver never binds
at Gen3 during early boot) plus a `sysinit.target` oneshot before
`local-fs-pre.target` that capped every PEX8747 downstream port to Gen2,
retrained, ran `modprobe nvme`, waited for the disk, and activated the VG.
It never got to run: the verification reboot halted in POST with Dell
`UEFI0066` ("A PCIe link training failure observed in Bus:5 Dev:17 Func:0 and
the link is disabled. System has halted"), and after moving the drive to
socket 1 and the card to the other PCIe slot, the same halt on Bus:4 Dev:9.
The firmware enumerates through the switch and trains the downstream links
itself, so a link that is marginal at Gen3 fails BEFORE any OS-side register
write. This is the general lesson: an OS-side link-speed cap can rescue a
running system, never a boot. The only fixes are at the hardware level (a
different card, a different drive, or a card whose own configuration EEPROM
pins the downstream speed).

The switch heatsink was extremely hot at the last power-off, consistent with
the fault getting worse boot over boot. The card is being returned.

What stayed on the host after the revert: the k3s drop-in
`k3s.service.d/10-requires-storage-mounts.conf` (`RequiresMountsFor` on the
two bind targets — k3s refuses to start on the root filesystem if a tier
mount is missing; harmless and wanted with the array stand-ins). Backups
`/etc/fstab.pre-nvme-2026-09-04` and `/etc/default/grub.pre-nvme-2026-09-04`
were the revert sources.

## Media-neutral tier identity (maintainer-directed 2026-09-04)

The tiers are addressed by ROLE, not by medium, so moving a tier between the
array and an NVMe never edits `/etc/fstab`: only the data copy and a
performance comparison need the hardware. Identity is the ext4 **LABEL**,
byte-identical on any medium (an ext4 label holds 16 bytes, which is why the
names are this short — `standin-containe` had already been truncated):

| Role | LV name (in whichever VG hosts it) | ext4 label | Today's home |
|---|---|---|---|
| warm cache | `ci-cache` | `ci-cache` | VG `poweredge` (array) |
| containerd image store | `ci-containerd` | `ci-containerd` | VG `poweredge` (array) |
| runner work volumes | `ci-workvols` | `ci-workvols` | VG `poweredge` (array) |

Applied on the array 2026-09-04 (live, mounted, pool quiet):
`lvrename poweredge standin-containerd ci-containerd`,
`lvrename poweredge standin-workvols ci-workvols`,
`tune2fs -L ci-containerd /dev/poweredge/ci-containerd`,
`tune2fs -L ci-workvols /dev/poweredge/ci-workvols`. Filesystem UUIDs are
unchanged, so the UUID-addressed fstab kept working; the
`ci-runner-pod-lifecycle-reliability` session (epic `livespec-ifwnqj`) owns
the follow-through: rewrite the tier fstab lines to `LABEL=`, put the lines
and the k3s `RequiresMountsFor` drop-in in git (the livespec-dev-tooling
storage-layout installer), and take the proving reboot.

### Gotcha 3 — `udevadm trigger` on mounted LVM devices unmounts them and stops k3s

The relabel step above was first followed by `udevadm trigger
--subsystem-match=block` to refresh `/dev/disk/by-label/`. In the same
second systemd began stopping k3s, then unmounted all four tier mounts, and
containerd's shims were orphaned (every ARC listener pod went `Unknown`).
Mechanism: the synthetic change event runs LVM's udev rules without the
device-mapper activation cookie, which marks the dm device not-ready
(`SYSTEMD_READY=0`); the fstab mount units are bound to their device unit,
so systemd issues stop jobs for the mounts, and the k3s drop-in's
`RequiresMountsFor` orders k3s's stop ahead of them. Recovery was `mount -a`,
`systemctl start k3s`, re-running the After=k3s oneshots, and force-deleting
the `Unknown` pods so their controllers recreated them. Counter-moves: after
`tune2fs -L` on a mounted LV do NOT trigger udev; the by-label symlink is
refreshed by `lvchange --refresh poweredge/<lv>` (a proper dm event) or
simply appears at the next boot, and `blkid` already shows the new label
immediately. Never run a blanket `udevadm trigger` on a host whose
filesystems sit on device-mapper.

## Migration sequence (amended for label identity; reuse on the StarTech attempt)

With CI off and the survey clean: `systemctl stop k3s` then
`/usr/local/bin/k3s-killall.sh` (this k3s version leaves the
`/var/lib/rancher/k3s/*` bind mounts alone); `pvcreate` by `by-id`,
`vgcreate` one VG per drive; `lvcreate` with the SAME role LV names
(`ci-containerd` on drive A's VG, `ci-workvols` on drive B's VG);
`mkfs.ext4 -L <role>-new` with a TEMPORARY label so two filesystems never
carry the same label at once; temp-mount the new LVs and
`rsync -aHAXS --numeric-ids --delete` from `/var/cache/ci-runner/k3s-containerd/`
and `…/k3s-storage/`; verify with a `-n -i` second pass (zero non-directory
lines) and a file count; unmount binds, the array tier mounts, and the temp
mounts; in the quiet window relabel old→new
(`tune2fs -L <role>-old /dev/poweredge/<role>` then
`tune2fs -L <role> /dev/<nvme-vg>/<role>`), `udevadm trigger
--subsystem-match=block`; `systemctl daemon-reload && mount -a` — fstab is
NOT edited, the `LABEL=` lines simply resolve to the new medium; `systemctl
start k3s`; confirm `k3s crictl images -q | wc -l` unchanged and pods Running.
The emptied array LVs stay in place (relabelled `<role>-old`) as spare
capacity. The 12.7 GB containerd copy took ~35 s (array-read-bound at
~360 MB/s). The fstab shape stays: `nofail,x-systemd.device-timeout=90s` on
the tier mounts, each bind `nofail` and requiring its tier mount, the k3s
drop-in refusing to start without them.

## Link survey (run after ANY card or socket change)

```bash
lspci -tv | sed -n '/03.2-\[/,/05.0/p'                         # where the drive landed
for ep in $(lspci -Dn -d ::0108 | awk '{print $1}'); do lspci -vvs $ep | grep -E 'Physical Slot|LnkSta:|CESta'; done
dmesg -T | grep -iE 'nvme.*(timeout|abort|probe)'
D=/dev/disk/by-id/nvme-WD_BLACK_SN8100_4000GB_25384T801085
test -b "$D" || echo "STOP: by-id path is not a block device"   # see gotcha 1
fio --name=r --filename=$D --rw=randread --bs=4k --iodepth=1 --ioengine=libaio --direct=1 \
    --runtime=5 --time_based | grep -E 'read: IOPS|clat.*avg'   # healthy: tens of µs; faulty: seconds
```

## Gotcha 1 — `fio` against a missing `by-id` path fills `/dev` (RAM) with a 200 GB file

When the driver probe had failed, the `by-id` symlink did not exist, and `fio
--filename=/dev/disk/by-id/… --size=200G` CREATED a regular file at that path
on `devtmpfs`. It grew to 88 GB (the whole `/dev` filesystem, RAM-backed) before
`ENOSPC`, took host memory from 3 GB used to 92 GB, and blocked udev from
creating the real symlink after the rebind. Worse, the next `fio` read that
FILE and reported 435k IOPS at 609 ns — a number that looked like a wildly
healthy drive and was actually RAM. Counter-move: `test -b "$D"` before every
raw-device run, never pass `--size` to a device test, and if `/dev` is ever
full (`df -h /dev`), look for a regular file under `/dev/disk/by-id/`.

## Gotcha 2 — fans at full speed with the lid off is the intrusion switch, not a thermal event

After the socket swap the fans sat at ~7.3k RPM with normal temperatures and
the third-party-card cooling response still disabled. The iDRAC SEL showed
`Physical Security #0x73 | General Chassis intrusion () | Asserted` with no
matching `Deasserted`, and `ipmitool sdr | grep -i intrusion` read `0x01`.
Dell runs the fans at full while the chassis is open; every earlier lid event
cleared within five seconds of closing. Seat the lid; do not touch the fan
settings (`poweredge-xubuntu-info` `FAN_COOLING.md`).

## Drive temperature note

Idle/light-load drive temperature read 39–41 °C in card socket 1 and 49–53 °C
in card socket 4, at the same ambient. Socket 4 is the interim seat; watch
`nvme smart-log /dev/nvme0 | grep temperature` under the first sustained CI
load (threshold for action stays ~70 °C per the install checklist).
