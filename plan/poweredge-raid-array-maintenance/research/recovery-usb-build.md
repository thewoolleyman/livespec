# The Ubuntu Desktop Recovery USB — how it was built, fixed, and proven

Built 2026-09-03, boot-proven on TWO machines by 2026-09-04. This is the
rescue environment the single-window array rebuild boots from. Recorded so
the stick is recreatable and its two boot traps are never re-hit blind.

## What it is

A PNY 128 GB USB 3.2 stick (serial `071C556D2BABC126`) carrying a REAL
installed Ubuntu 26.04 "resolute" (debootstrap, not a live image): GNOME
desktop (`ubuntu-desktop-minimal`), sshd with `PermitRootLogin yes` +
`PasswordAuthentication yes`, users `root` and `ubuntu` (password
`password` — deliberately weak lab-only rescue media), NOPASSWD sudoers,
NetworkManager DHCP on all NICs, `unattended-upgrades` disabled, and the
full storage toolchain: `lvm2 mdadm gdisk parted dosfstools smartmontools
nvme-cli ipmitool rsync debootstrap` plus a copy of `perccli64` at
`/opt/MegaRAID/perccli/`. Google Chrome is installed (menu entry ships in
the deb) and the OFFICIAL tailscale web UI is enabled
(`tailscale set --webclient=true`, port 5252) with a "Tailscale UI"
launcher in the applications menu.

Tailnet identity: **`ubuntu-recovery-usb`** (100.117.231.34), enrolled
2026-09-04 as an ordinary untagged member under the maintainer's account —
recorded in the `tailscale-admin` repo's machines inventory (PR #38). The
identity travels with the stick: whatever machine boots it appears on the
tailnet under that name, which is exactly what makes the rebuild window
remotely drivable with no tunnel.

## Build and test scripts (committed beside this note)

- `run-backup.sh` — the Toshiba USB backup driver. Its ONLY other copy
  lives on the backup volume itself (`/mnt/usb-backup/run-backup.sh`);
  committed here 2026-09-04 to close that single-copy risk.
- `build-recovery-usb.sh` — builds the stick end-to-end on a running host
  (partition → debootstrap → chroot package install → grub → perccli).
  NOTE: a fresh build must ALSO apply the two boot fixes below — the
  script as committed predates them.
- `test-recovery-usb.sh` — boots the PHYSICAL stick in QEMU+OVMF on the
  host, then sshes in (root/password via hostfwd :2222) and verifies
  hostname, NOPASSWD sudo, every tool, perccli, and the README. This test
  caught both boot traps before any human walked to a machine.

## The two boot traps (both hit, both fixed, both will recur on a rebuild)

1. **Ubuntu's signed GRUB cannot read modern ext4.** resolute's
   `mkfs.ext4` defaults include `orphan_file`/`orphan_present`/
   `metadata_csum_seed`; the signed `grubx64.efi` fails on them, leaving a
   bare `grub>` prompt. Fix: GRUB must never touch the ext4 — the kernel
   and initrd are COPIED to the FAT32 ESP (`/vmlinuz`, `/initrd.img`) and
   loaded from there; only the kernel mounts the ext4 root. Consequence:
   after any kernel upgrade ON THE STICK, re-copy the new
   `vmlinuz`/`initrd.img` from `/boot` to the ESP or the stick boots the
   old kernel (recorded in the stick's `/root/README-RECOVERY.md`).
2. **`grub-install --removable` with the signed packages installs the
   CD-variant GRUB whose baked-in config path is `/boot/grub/grub.cfg` ON
   THE ESP** (tell-tale: `/.disk/info` probe errors on the serial
   console). It ignores `EFI/ubuntu/grub.cfg` and `EFI/BOOT/grub.cfg`.
   Fix: the menu config lives at **`ESP:/boot/grub/grub.cfg`**:

   ```
   set timeout=3
   search.fs_uuid <ESP-UUID> root
   menuentry "Ubuntu Desktop Recovery USB" {
     linux /vmlinuz root=UUID=<ext4-root-UUID> rw
     initrd /initrd.img
   }
   ```

## Boot proofs

- **QEMU/OVMF on poweredge-xubuntu** (2026-09-03): PASS in ~40 s —
  firmware → shim → GRUB → kernel → sshd, root login, all tools verified.
- **gmktec (physical)** (2026-09-04): booted to desktop, sshd reachable
  over a Mac reverse tunnel, then enrolled in tailscale.
- **poweredge-xubuntu (physical)** (2026-09-04): booted via firmware entry
  `Boot0004 "Ubuntu Recovery USB"` (created with
  `efibootmgr -C -d <PNY-by-id> -p 1 -L "Ubuntu Recovery USB"
  -l "\EFI\BOOT\BOOTX64.EFI"`; default BootOrder untouched — select it
  per-boot with `efibootmgr --bootnext 0004` or F11), came up in ~190 s at
  LAN `192.168.1.200` (the reservation is MAC-bound, so the stick inherits
  each host's reserved IP) and on the tailnet; hardware verified
  `PowerEdge R630`.

## Operational notes

- Device addressing during any surgery: ONLY
  `/dev/disk/by-id/usb-PNY_USB_3.2.1_FD_071C556D2BABC126-0:0…` — `sdb` vs
  `sdc` ordering swaps between boots (the Toshiba backup disk is also USB:
  `usb-TOSHIBA_External_USB_3.0_…`).
- The stick's GNOME first-boot wizard created the `ubuntu` user and reset
  the hostname on its first interactive boot; the hostname was re-set to
  `ubuntu-recovery-usb` when tailscale was enrolled.
