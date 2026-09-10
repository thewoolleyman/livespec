# Upgrade PowerEdge memory — plan overview

Opened 2026-09-10 after the maintainer confirmed that the additional memory is in hand.

## Bottom line

Upgrade the memory in `poweredge-xubuntu` (Dell PowerEdge R630, service tag `JBS0JB2`) without making the self-hosted CI pool a merge dependency, without trusting a stale backup, and without leaving the host or its documentation in an ambiguous state. The work is complete only when the new DIMMs are physically installed, the firmware and operating system recognize the intended topology and capacity, memory tests and error logs are clean, real CI has returned to the PowerEdge runners, every authoritative repository records the resulting state, every touched primary clone is synchronized and clean, and this plan passes its child-disposition and independent completeness-review archive gates.

The archived `poweredge-raid-array-maintenance` plan (epic `livespec-g52yrb`) is the operational precedent. Its durable controls are reused here: save the exact CI routing state before changing it; redirect every adopted repository with the guarded label writer; verify an effective hosted-runner fallback; take and prove a current Toshiba backup; keep physical work attended and maintainer-gated; restore self-hosted routing only after host and workload verification; land documentation through worktree → PR → merge → cleanup; and archive only after an independent completeness review. Read first:

- `plan/archive/poweredge-raid-array-maintenance/research/plan-overview.md`
- `plan/archive/poweredge-raid-array-maintenance/research/phase3-backup-and-restore-procedure.md`
- `plan/archive/poweredge-raid-array-maintenance/research/run-backup.sh`
- `plan/archive/poweredge-raid-array-maintenance/research/restore-verification-plan.md`
- the 2026-09-06T09:44:56Z corrective handoff on epic `livespec-g52yrb`, which demonstrates why late soak evidence must supersede an early green reading before archive

## Known baseline and facts to re-measure

The host record at `poweredge-xubuntu-info/AGENTS.md` currently says:

- Dell PowerEdge R630, 2 × Xeon E5-2696 v3, 72 hardware threads;
- 188 GiB RAM across two NUMA nodes;
- Ubuntu/k3s host for the fleet's ARC runner pool;
- churn-slot capacity `C = 32`, selected because CPU—not memory—was the measured ceiling;
- a seven-drive RAID-5 system volume plus separate `ci-containerd` and `ci-workvols` NVMe tiers, with the k3s datastore on tmpfs;
- Toshiba `POWEREDGE-BACKUP` at `/mnt/usb-backup` when attached.

These are historical facts, not permission to assume the live state. Before shutdown, capture the present DIMM slot map, type, rank, speed and capacity with firmware and OS views; capture current NUMA topology, allocatable memory, ECC/EDAC/MCE state, iDRAC/Lifecycle logs and system-event log; identify the new modules by label/part number; and derive the exact Dell-supported population map. Do not mix RDIMMs and LRDIMMs, exceed CPU/channel/rank constraints, or infer a valid layout from total capacity alone. Record the intended post-upgrade total and slot map before poweroff.

The extra memory does not itself authorize a higher CI concurrency cap, larger Redis cache, larger gate quota, larger tmpfs, or changed kube/system reservations. Any such change needs its own measurement-backed decision and authoritative GitOps update; otherwise the existing values remain unchanged.

## Phase 1 — Establish the carrier map and pre-change evidence

Before any mutation:

1. Enumerate the complete current set of repositories using the PowerEdge runner labels from the committed ARC/Kueue manifests and live GitHub repository variables. Do not reuse a historical list from the archived plan.
2. Save each repository's exact `CI_RUNNER_LABELS` presence and value so the restoration is byte-for-byte intentional; distinguish an absent variable from an empty one.
3. Inspect every local authoritative carrier containing the host name, the current 188 GiB figure, DIMM/NUMA facts, memory-derived budgets, backup procedure, or CI routing procedure. At minimum inspect `poweredge-xubuntu-info`, `livespec-dev-tooling`, `livespec`, and any GitOps/inventory repository discovered by search (including `tailscale-admin` or `homelab` only where they actually own a changed fact).
4. Record live host health, memory/error baseline, running CI workload count, and the new DIMM identification and proposed slot map.

Output: a dated preflight research note and a ledger scope event naming the requirement carriers and concrete deferrals before child work is admitted.

## Phase 2 — Redirect and drain CI to GitHub-hosted runners

Use `livespec-dev-tooling/ci-runner/set-ci-runner-labels.sh`, not ad-hoc `gh variable` calls, to clear routing for the full live adopted-repository set. Keep the saved original state for the later inverse operation.

Go/no-go evidence before shutdown:

- a representative matrix workflow runs on GitHub-hosted `ubuntu-latest` and reaches green;
- no new jobs are being admitted to the PowerEdge pool;
- every running self-hosted runner workflow has completed or been deliberately cancelled by the maintainer;
- ARC/Kueue reports zero running workload that the shutdown would kill;
- the exact hosted-runner run IDs and final drain observation are recorded.

Do not power off while the fleet is partially routed or while jobs remain on the host.

## Phase 3 — Make and verify a current Toshiba backup

Mount and identify the Toshiba volume by filesystem label `POWEREDGE-BACKUP` at `/mnt/usb-backup`; confirm the mount is the external filesystem rather than the underlying directory, confirm free space, filesystem health and `nofail`, and preserve backup logs on the volume.

The archived `run-backup.sh` is precedent, not an automatically valid current script. It predates the present LVM + two-NVMe layout. Re-derive the backup source set from current `findmnt`, `lsblk`, LVM and rebuildability facts. In particular, `--one-file-system` on `/var/cache/ci-runner` will not cross the nested `ci-containerd` and `ci-workvols` mounts. Decide and document which data on the RAID, `ci-cache`, `ci-containerd`, `ci-workvols`, tmpfs datastore and EFI system partition is non-reconstructible and therefore must be captured, versus deliberately reconstructible churn/cache data. Update the volume's backup/restore scripts if the present layout or restore contract requires it; never silently claim that the 2026-09-04 pre-rebuild image is a current backup.

Verification gate:

- every required pass exits 0 or only an explicitly justified rsync 24; rsync 23 is failure;
- a second pass is an effective no-op apart from explained live churn;
- metadata includes the live block/LVM/filesystem topology, fstab, package and enabled-unit state needed for recovery;
- the restore path is checked against the current layout, with the last full rehearsal evidence named and any un-rehearsed delta called out;
- byte/file counts, timestamps, log paths and resulting confidence are recorded.

No shutdown until this gate is green.

## Phase 4 — Land pre-change documentation and fix the attended runbook

Before poweroff, merge the facts that would otherwise disappear with the old configuration:

- `poweredge-xubuntu-info`: before-state DIMM slot map, new module identity, supported target population map, safety steps, expected total, test plan and rollback/reseat conditions;
- `livespec-dev-tooling`: CI diversion/drain/restore procedure or memory-derived GitOps inputs only if the existing authoritative procedure is missing or changed;
- `livespec`: this plan and any genuine cross-host requirement gap routed through the spec lifecycle, not host-specific operating data copied into the specification;
- other repositories discovered in Phase 1: update only facts they authoritatively own.

Every tracked change follows that repository's worktree → PR → required checks → rebase-merge → cleanup discipline. Do not leave the host-dependent instructions only in the plan timeline.

## Phase 5 — Shut down; maintainer installs memory; reboot

This is attended, factory-ineligible physical work.

Preconditions, restated immediately before the command: hosted CI proof green; PowerEdge runners drained; current Toshiba backup green; intended DIMM map recorded; pre-change docs merged; rollback/reseat conditions recorded; console/iDRAC or physical access available.

The agent performs a clean OS shutdown only after those gates are re-read. The maintainer then disconnects power as required by the Dell service procedure, observes ESD precautions, opens the chassis, installs the modules in the recorded population order, checks seating and air shrouds, closes the lid, reconnects power and boots. Do not improvise slot placement during the window. If firmware reports a memory configuration, training, ECC or population error, stop; photograph/transcribe the exact message, preserve the old modules and revert or reseat according to the pre-recorded condition.

The plan must carry a typed human next action across the offline interval so a resumed session cannot mistake loss of SSH for success.

## Phase 6 — Prove the memory and host

Before restoring CI routing:

1. Confirm firmware/iDRAC inventory matches the intended per-slot map, total, type and speed, with no disabled channel or degraded module.
2. Confirm Linux reports the expected total, NUMA distribution and usable/allocatable memory; explain the normal firmware-reserved difference rather than comparing only headline totals.
3. Compare Lifecycle/system-event logs, EDAC/MCE/RAS records and kernel journal against the pre-change baseline; any new correctable-error trend or any uncorrectable error blocks acceptance.
4. Run the agreed Dell preboot extended memory diagnostic or equivalent full-address test, plus an OS-side stress/memory test sized to leave the control plane safe. Record tool versions, coverage, duration, result and thermals. A short boot and `free -h` are not sufficient evidence.
5. Reboot at least once after testing and prove unattended boot, Tailscale/SSH, storage mounts, tmpfs datastore rebuild, k3s, ARC listeners, Kueue, monitoring and backup-mount `nofail` behavior.

If any test fails, keep CI on hosted runners, preserve error evidence, and return to the physical reseat/rollback decision instead of routing load back.

## Phase 7 — Restore CI routing and prove real workload

Restore every saved `CI_RUNNER_LABELS` state with the guarded writer, including deletion versus empty/value semantics. Verify the complete live set, not only a representative repository.

Then run a real representative matrix on the self-hosted labels and record run IDs, runner names, green conclusion, host health and error-log delta under load. Confirm no routing variable was missed and no repository is stranded on hosted or unavailable labels. Re-read memory errors after load. The pre-upgrade churn-slot cap and all other memory-derived budgets remain unchanged unless separately changed through their owning, reviewed GitOps path.

## Phase 8 — Final documentation, synchronization and archive

Land the observed result—not merely the intended result—through the authoritative repositories:

- `poweredge-xubuntu-info`: installed module part numbers, final slot map, reported total/speed/NUMA topology, firmware and OS evidence, diagnostics, any warnings/rollback, and dated verification commands;
- `livespec-dev-tooling`: only actual GitOps, CI-routing or memory-budget changes plus their derivation and proof;
- `livespec`: plan research, ledger evidence, and any ratified cross-host contract change genuinely required;
- every other carrier from Phase 1: update or explicitly record why no change is needed.

For every touched repository: merge through a PR, wait for checks, refresh the primary clone to its remote default branch, remove the worktree and local feature branch, and verify the primary is clean and not behind. Search once more for stale 188 GiB/DIMM/topology claims and resolve every authoritative hit. Confirm the live host, GitOps and documentation agree.

Finally dispose every plan child, record a closing handoff naming any transferred follow-up exactly, sweep for live references to `plan/upgrade-poweredge-memory/`, commission a fresh independent completeness reviewer, durably record its full requirement-carrier attestation, and archive through `archive_thread(...)`. A green first reading, a closed epic, or a directory move alone is not completion.

## Ordering and ownership

```text
preflight + carrier map
        ↓
redirect CI → hosted proof → drain to zero
        ↓
current backup + verification
        ↓
pre-change documentation merged
        ↓
clean shutdown → MAINTAINER installs DIMMs → boot
        ↓
firmware/OS inventory + diagnostics + reboot proof
        ↓
restore CI routing → real self-hosted workflow proof
        ↓
final docs + all touched primaries synchronized
        ↓
child disposition + independent completeness review + archive
```

The maintainer owns physical installation and any spend/compatibility choice not already settled by the parts in hand. The plan session owns evidence capture, CI diversion/restoration, backup verification, repository routing, tests that can safely run from the host, documentation/PR completion, local synchronization and archive gates. Routine repository implementation is filed as scoped ledger children and dispatched; host mutation and the offline physical interval remain attended and factory-ineligible.

## Explicit deferrals at creation

No implementation child is admitted by this initial note. The formal ledger scope event will name the final carriers after live discovery. Changes to CI concurrency, cache sizing, gate quotas, tmpfs sizing, kube/system reservations, BIOS performance policy, storage layout, or unrelated rebuildability gaps are deferred unless the memory installation proves one is required; otherwise each stays in its existing owner and may become a named follow-up rather than scope creep here.
