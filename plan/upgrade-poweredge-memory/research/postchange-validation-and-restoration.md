# PowerEdge memory upgrade — post-change validation and restoration

Recorded 2026-09-10 for plan epic `livespec-iy6hbf`.

## Installed result

The PowerEdge R630 now has all 24 DIMM sockets populated. The existing twelve
16 GiB Samsung `M393A2G40EB1-CPB` RDIMMs remain in A1-A6/B1-B6 and the twelve
new 16 GiB Hynix `HMA42GR7MFR4N-TF` RDIMMs occupy A7-A12/B7-B12. DMI and
`lshw` report every module as dual-rank registered/buffered ECC at 1.2 V.
The configured speed is 1866 MT/s, as expected with three DIMMs per channel.

Raw capacity is 384 GiB. Linux exposes 405,620,961,280 bytes (377 GiB), split
symmetrically between NUMA node 0 at 193,313 MB and node 1 at 193,517 MB, with
36 logical CPUs assigned to each node. The iDRAC Lifecycle Controller recorded
all twelve new modules at 2026-09-10 08:12:56-57 UTC with informational
severity and no disabled-DIMM or training failure. IPMI SEL contains only the
expected chassis-intrusion events from opening the server.

## Load and ECC evidence

A temporary, unpacked `memtester` 4.7.1 binary allocated and locked 300 GiB
(322,122,547,200 bytes) and exercised it for approximately two hours. Stuck
Address, Random Value, Compare XOR, Compare SUB, Compare MUL, Compare DIV,
Compare OR, Compare AND, and Sequential Increment completed `ok`; Solid Bits
reached iteration 5. The maintainer judged the remaining exhaustive patterns
disproportionate to the maintenance window and directed the run to stop.

On the closing pass the maintainer explicitly accepted this boundary, stating
that the remaining exhaustive run was overkill and that the memory should be
treated as good. This is the maintainer-approved amendment to the plan's
original full-address-test gate: no claim is made that a Dell extended
diagnostic or every `memtester` pattern ran.

This was an intentionally partial pass, not a claim that every `memtester`
pattern completed. It nonetheless exercised almost 80% of installed usable
memory for an extended period. All four EDAC controller CE/UE totals and every
per-DIMM counter stayed zero before, during, and after the run. The kernel
journal since test start contains no MCE, ECC, hardware-error, or memory-error
record. The process stopped cleanly, memory returned to 388,876,536 KiB
available, and the temporary package tree was removed without installing a
package. Final temperatures were 26 C inlet, 46 C exhaust, and 54/56 C at the
CPUs.

## Host and CI-platform acceptance

The post-boot host reached `systemd` running state with zero failed units.
Root, EFI, the RAID cache volume, both NVMe CI tiers and their bind mounts, the
tmpfs k3s datastore, and the Toshiba `POWEREDGE-BACKUP` volume were mounted
read-write from their expected sources. The reconstruct-on-boot chain
completed successfully. The k3s node was Ready with churn-slot capacity and
allocatable both 32; all eleven ARC listeners were Running; every Kueue queue
was Active; and the lifecycle scan reported all fault classes clean.

Before the physical window, the hosted-capacity proof was
[livespec run 34441603667](https://github.com/thewoolleyman/livespec/actions/runs/34441603667).
Every executed job reported `labels=["ubuntu-latest"]`, a GitHub-hosted runner
name, and success, including `ci-green`.

The manual-only, non-gating `k3s-arc-proof-job` then completed successfully as
[livespec-dev-tooling run 34469453160](https://github.com/thewoolleyman/livespec-dev-tooling/actions/runs/34469453160).
GitHub assigned job `102845676189` to ephemeral runner
`poweredge-xubuntu-k3s-nd2xp-runner-jlhj8`, addressed by the host-unique
`poweredge-xubuntu-k3s` scale set. Its log proved kernel
`7.0.0-31-generic`, non-root UID 1000, and a Kubernetes service-account
projection. It completed in five seconds and its runner pod was removed.

The authoritative host record landed in `poweredge-xubuntu-info` PR #19 as
commit `b30b237`. A final stale-fact sweep found one historical storage note
whose 188 GiB figure was not clearly scoped to its pre-upgrade date;
`poweredge-xubuntu-info` PR #20 corrected it and merged as `44fd34d`. The HP
backup addition is separately documented in
`hp-xubuntu-info` PR #3 (`631a8e8`): the guarded USB backup and verification
completed before that host was shut down for relocation.

After the memory test, the fleet was diverted to hosted capacity once more and
the PowerEdge was rebooted at 2026-09-10 11:27 UTC. Its boot ID changed from
`5c40f60f-3852-4f0b-952c-0eb4713e5e1e` to
`32125a6e-895e-4653-85ca-332f2d55422d`. The system returned unattended at
11:31 UTC. After the five-minute post-start observation window, the lifecycle
scan completed cleanly: systemd was `running` with zero failed units, the node
was Ready, all eleven ARC listeners were Running, all twelve ClusterQueues
were present with zero unfinished Workloads, and the expected RAID, EFI, NVMe,
tmpfs-datastore, and Toshiba mounts were present. Linux exposed 396,114,240 KiB
total, split 197,952,744/198,161,496 KiB between NUMA nodes 0/1. EDAC CE and UE
totals were still zero and the new-boot journal contained no hardware,
corrected, uncorrected, MCE, or memory error. Four PCI DOE mailbox-init messages
were the only priority-error kernel entries and are unrelated to memory.

## Toshiba backup evidence

The pre-change `usb-backup.service` run started at 2026-09-10 03:59:27 UTC and
finished successfully at 04:15:24 UTC. Its journal records `rc=0` for the
rootfs and EFI rsync passes and for the online SQLite datastore snapshot,
followed by `BACKUP COMPLETE — all passes succeeded`; systemd records
`Result=success` and `ExecMainStatus=0`. The evidence remains on the
`POWEREDGE-BACKUP` ext4 filesystem mounted from `/dev/sdb1` at
`/mnt/usb-backup`, including `rootfs/`, `boot-efi/`, `k3s-datastore/`, `meta/`,
`restore.sh`, and historical logs.

The resulting image contains 181,218 regular rootfs files occupying
39,807,546,765 bytes, ten EFI files occupying 9,391,234 bytes, and one
345,198,592-byte k3s datastore snapshot. SQLite `PRAGMA quick_check` returned
`ok`. A read-only second rsync comparison exited 0 for both rootfs and EFI. EFI
was an exact no-op. The live root had 609 creates, 666 deletes and 574 regular
file transfers (4,202,682,023 bytes), explained as ordinary live-system drift
after the pre-change image rather than a failed backup pass.

The restore path is not merely theoretical: the same Toshiba layout and
`restore.sh` path restored the host during the 2026-09-04 RAID-array rebuild,
including regenerated fstab and a real `grub-install`. The current image was
not destructively restore-tested during this memory-only window. Its
unrehearsed delta is the newer root/EFI/datastore content and metadata; the
block, LVM, filesystem, and boot topology did not change during the memory
upgrade.

## Fleet routing restoration

After the host-unique proof passed, the sanctioned
`livespec-dev-tooling/ci-runner/set-ci-runner-labels.sh` writer restored the
ten exact pre-maintenance values. Every repository first read the strict
fork-PR approval policy `all_external_contributors`, then independently read
back its variable:

| Repository | Restored `CI_RUNNER_LABELS` |
|---|---|
| `livespec` | `["livespec-local-ci-k3s"]` |
| `livespec-console-beads-fabro` | `["livespec-console-beads-k3s"]` |
| `livespec-dev-tooling` | `["livespec-dev-tooling-k3s"]` |
| `livespec-driver-claude` | `["livespec-driver-claude-k3s"]` |
| `livespec-driver-codex` | `["livespec-driver-codex-k3s"]` |
| `livespec-driver-pi` | `["livespec-driver-pi-k3s"]` |
| `livespec-orchestrator-beads-fabro` | `["livespec-orchestrator-k3s"]` |
| `livespec-orchestrator-git-jsonl` | `["livespec-orchestrator-git-k3s"]` |
| `livespec-overseer` | `["livespec-overseer-k3s"]` |
| `livespec-runtime` | `["livespec-runtime-k3s"]` |

A separate ten-repository API read returned those exact values. Immediately
after restoration, the PowerEdge node remained Ready at 32/32 churn slots,
all eleven listeners were Running, all queues were Active with zero pending
or admitted Workloads, no runner pod was left behind, no systemd unit was
failed, and EDAC remained zero.

The same guarded restoration was repeated after the final reboot. Each of the
ten repositories again passed the strict-tier check and independently read
back its exact self-hosted value, so none remains routed to GitHub-hosted
capacity.

The existing host-unique proof workflow and routing writer required no
operational change. The final stale-fact sweep did find dated capacity prose in
`livespec-dev-tooling` that still read like current state: two sccache passages
said 188 GiB and that churn capacity remained 64, and the phase-1 README did
not explicitly distinguish its 188 GiB baseline from current inventory. PR
#2217 corrected those carriers to the current 377 GiB, restored C=32 state and
unchanged 16 GiB Redis ceiling; all required checks passed and it merged as
`55d514c0`. Both affected primary clones were refreshed and their temporary
worktrees removed.
