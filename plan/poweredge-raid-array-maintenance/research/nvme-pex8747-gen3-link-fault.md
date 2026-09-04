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

## Migration sequence that worked (reuse on the StarTech attempt)

With CI off and the survey clean: `systemctl stop k3s` then
`/usr/local/bin/k3s-killall.sh` (this k3s version leaves the
`/var/lib/rancher/k3s/*` bind mounts alone); `pvcreate` by `by-id`,
`vgcreate`, `lvcreate`, `mkfs.ext4 -L`; temp-mount the new LVs and
`rsync -aHAXS --numeric-ids --delete` from `/var/cache/ci-runner/k3s-containerd/`
and `…/k3s-storage/`; verify with a `-n -i` second pass (zero non-directory
lines) and a file count; unmount binds, stand-ins, temp mounts; swap the two
stand-in UUID lines in fstab for the NVMe UUIDs with
`defaults,noatime,nofail,x-systemd.device-timeout=90s,x-systemd.requires-mounts-for=/var/cache/ci-runner`,
and give each bind `nofail,x-systemd.requires-mounts-for=<its NVMe mount>`;
`systemctl daemon-reload && mount -a`; `systemctl start k3s`; confirm
`k3s crictl images -q | wc -l` unchanged and pods Running. The 12.7 GB
containerd copy took ~35 s (array-read-bound at ~360 MB/s).

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
