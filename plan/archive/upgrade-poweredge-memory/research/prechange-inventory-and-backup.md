# PowerEdge memory upgrade — pre-change inventory and backup gate

Recorded 2026-09-10 for plan epic `livespec-iy6hbf`. This is the committed
pre-shutdown evidence. Execution state and handoffs remain ledger-held.

## CI isolation

All ten adopted repositories were redirected to GitHub-hosted runners before
this preflight. The PowerEdge pool then read zero ARC workflow pods, zero
EphemeralRunner resources, zero unfinished Kueue Workloads, and zero current,
pending, or running runners across all ten repository scale sets. The exact
temporary values and each repository's restore value are held in the plan
epic's 2026-09-10 fleet-cutover handoff. CI must remain hosted until the memory,
boot, k3s/ARC/Kueue, and real self-hosted workload proofs pass.

## Delivered memory and target map

The maintainer has twelve SK Hynix `HMA42GR7MFR4N-TF` modules. The supplier
page (Amazon ASIN `B00Q6QOLJ8`) identifies each as 16 GB DDR4-2133 ECC
registered, dual-rank x4 (`2Rx4`), 1.2 V. Its 240-pin field is wrong for DDR4;
visually confirm all twelve physical labels before seating them.

Live `dmidecode` before shutdown reports twelve 16 GB Samsung
`M393A2G40EB1-CPB` DDR4-2133 ECC registered, dual-rank, x4, 1.2 V modules in
A1-A6 and B1-B6. A7-A12 and B7-B12 are empty. The new kit matches the current
capacity, generation, ECC/RDIMM class, nominal speed, rank, organization, and
voltage. The supported target is therefore all empty sockets: A7-A12 and
B7-B12, preserving identical populations on both processors and producing
384 GB raw capacity.

The final state is three DIMMs per channel. Dell's R630 documentation permits
three single/dual-rank RDIMMs per channel and specifies 1866 MT/s at 3 DPC, so
a negotiated downclock from 2133 to 1866 MT/s is expected. The permanent host
record and post-boot acceptance checklist are in
`poweredge-xubuntu-info/MEMORY.md`.

## Toshiba backup gate — passed

Read live at 2026-09-10 05:24-05:26 UTC:

- Toshiba `MQ04UBF100`, serial `11PHT0S6T`, ext4 label
  `POWEREDGE-BACKUP`, UUID `9045b3fe-6754-4135-9c9a-e405a3fd9935`, mounted
  read-write at `/mnt/usb-backup`.
- `usb-backup.service` completed successfully at 2026-09-10 04:15:24 UTC,
  69 minutes before the inspection. Its rootfs, EFI, and k3s datastore passes
  each returned success; systemd recorded status 0.
- The backup implementation treats rsync 23 and every status other than 0/24
  as fatal, refuses an unmounted destination, refuses concurrent rsync, uses
  `-aHAXS --numeric-ids --delete --one-file-system`, and creates the k3s copy
  with SQLite's online `.backup` operation.
- `/mnt/usb-backup/k3s-datastore/state.db` was 345,198,592 bytes and its
  `PRAGMA integrity_check` returned `ok`.
- Required rootfs, EFI, metadata, and datastore sentinels exist. Every metadata
  and EFI regular file completed a SHA-256 read probe, followed by a successful
  `sync`.
- The volume reports 916 GB usable, 41 GB used, and 876 GB available.

This satisfies the current off-array backup gate. No shutdown or chassis work
had begun when this evidence was captured.

## Post-boot documentation obligations

After the modules are installed, record the actual capacity, per-slot
manufacturer/part/rank/speed, NUMA split, diagnostics and memory-test result in
`poweredge-xubuntu-info/MEMORY.md`. Re-evaluate every RAM-derived limit in
`livespec-dev-tooling` from measurements rather than automatically increasing
it: the current churn-slot cap is CPU-derived, while sccache, tmpfs datastore,
and pod limits contain explicit memory arithmetic. Only then restore the exact
repository routing values from the ledger handoff.
