# PowerEdge RAID array maintenance — plan overview

## Bottom line

The CI host `poweredge-xubuntu` (a Dell PowerEdge R630, service tag
`JBS0JB2`) runs all fleet CI on a single **RAID 5** virtual disk built
from three ~4-year-old SATA SSDs behind a **PERC H730P Mini** controller.
Measurement (`research/storage-io-characterization.md`, copied into this
plan verbatim) established that the disk subsystem — not CPU or RAM — is
the constrained resource, and left **one open question**: each drive
delivers only ~69 MB/s of writes, far below its rating, and it is not yet
known whether that is FTL exhaustion (the drives were never TRIMmed and
had a prior life), an intrinsic drive-generation/controller floor, or
controller destage limits.

This plan turns that open question into a decision and then acts on it:
characterize the array for real on a quiet fleet, decide the cheapest
optimization that actually restores write throughput, make a **fully
recoverable rsync backup** of the xubuntu CI system to an attached USB
volume with a **single-command restore** stored on the volume itself,
prove CI falls back to GitHub-hosted runners while the host is down, then
execute the optimization (up to and including a full array wipe or a
RAID-level change to RAID 10 with added disks) and restore to a clean
Ubuntu install partitioned for a Kubernetes CI + agentic-factory server.

**Time-critical note:** the idle write-throughput measurement (Phase 1)
must run while the array is quiet. The maintainer has halted the fleet,
so that window is **now** — Phase 1's non-destructive perf write is the
first thing to run, ahead of the read-only BIOS research (Phase 0), which
can happen at any time.

## Scope, safety, and authorization posture

- The host is **live shared production CI infrastructure**. Every
  destructive or host-mutating step (array wipe, RAID recreate, BIOS/PERC
  reconfiguration, OS reinstall) is **explicitly maintainer-gated** and
  sequenced behind a verified, tested backup and a proven CI fallback.
- Non-destructive, read-only measurement and research (Phases 0, 1, 5,
  and the backup-verification re-run in Phase 4) proceed without
  per-step gating once the fleet is confirmed halted.
- **The other array volumes may be discarded.** Per maintainer
  direction, `sda2`/`sda3` (the old GitLab-Kubernetes installs) carry
  nothing this fleet needs and are wiped. Only the xubuntu CI system
  (`sda4` = `/`) and, optionally, its warm caches (`sda5` =
  `/var/cache/ci-runner`) are backed up and restored.
- This plan is filesystem research + a ledger epic. It files ripe work
  as ledger children after a scope event; it does not implement inline.

## Reference facts (from the characterization, confirm live in Phase 1)

| | |
|---|---|
| Host | Dell PowerEdge R630, service tag `JBS0JB2`, iDRAC present (out-of-band mgmt) |
| Controller | PERC H730P Mini (LSI MegaRAID SAS-3 3108), 2 GB battery-backed cache, BBU Optimal |
| Virtual disk | VD0, **RAID 5**, 3 × SSD, 64 KB strip (128 KB full stripe), WriteBack, Optimal |
| Drives | 3 × Samsung `MZ7GE960HMHP-000V3` (IBM OEM), SATA 6 Gb/s, ~96% endurance left, 0 reallocations |
| Enclosure | 8 bays, **3 populated, 5 free** |
| Expansion | PCIe Gen3 **x16 slot empty**, one x16 in use |
| TRIM | Drives support it (`Available, deterministic, zeroed`); **the RAID volume does not expose it** — 0 discards ever issued |
| Partitions | `sda1` ESP · `sda2`/`sda3` old gitlab-k8s (wipeable) · **531 GB unpartitioned** · `sda4` `/` (500 GB) · `sda5` `/var/cache/ci-runner` (718 GB, idle) |
| Measured write path | All CI churn writes to `/` (sda4); sda5 receives zero traffic |
| Open question | Each drive ~69 MB/s writes — FTL exhaustion (TRIM would help) vs. drive/controller floor (it would not) |

## The phases

### Phase 0 — Research controller/BIOS-level RAID management options (read-only)

**Goal:** enumerate, against this exact controller and platform, every
supported way to manage the array, so Phase 2's decision and Phase 6's
execution rest on verified capability, not assumption.

**Investigate:**
- **In-OS management** — is `perccli`/`perccli2` (or `storcli`) present or
  installable? It manages the PERC H730P online: report VD/PD state, cache
  policy, create/delete VDs, start consistency checks, and — critically —
  whether it exposes **RAID Level Migration (RLM)** / Online Capacity
  Expansion for RAID 5 → RAID 10 without data loss, and whether it can
  create a VD from a **subset** of the disk-group capacity (the mechanism
  for controller-level over-provisioning).
- **Boot-time config** — the PERC BIOS config utility (Ctrl+R legacy) and
  the UEFI **HII** "Device Settings → RAID controller" menu: what VD
  operations each offers (create, delete, initialize, level, strip size,
  cache policy) and which require the host offline.
- **Out-of-band via iDRAC** — is iDRAC reachable and credentialed? `racadm`
  (`storage`/`raid` subcommands) and the iDRAC web UI can drive the same
  RAID operations without the OS, which is the safer path for a
  destroy-and-recreate and the basis for remote, human-light execution.
- **RAID 10 feasibility** — whether RLM RAID5→RAID10 is supported here at
  all (often it is not for this transition), or whether RAID 10 requires
  **destroy + recreate** (hence: backup first). Confirm minimum disk count
  (RAID 10 needs an even count ≥ 4) against the 5 free bays.
- **Over-provisioning mechanics** — since TRIM cannot reach the drives,
  confirm the only durable free-block headroom is *unallocated capacity at
  VD creation*: build the VD from ~70–80% of the disk group and leave the
  rest untouched so garbage collection retains permanent headroom.

**Output:** a `research/controller-management-options.md` note: the
verified toolset, what each can/can't do here, and which operations need
the host offline vs. iDRAC out-of-band.

### Phase 1 — Confirm existing state non-destructively; measure real throughput on the quiet array

**Goal:** re-verify the characterization against current live state and
run the **idle write-throughput discriminator** now that the fleet is
halted, then persist any corrections back into the research notes.

**Non-destructive confirmation:** re-read controller/VD/PD state, BBU
health, partition layout, PSI, queue settings, and per-drive SMART
lifetime counters; diff against the characterization and update it where
live state has moved.

**The discriminator (idle perf write to the empty cache volume):**
`sda5` (`/var/cache/ci-runner`) is on the same three SSDs behind the same
controller but receives zero traffic, so an idle write there isolates the
drives' raw capability with nothing competing. Method:
- `fio`, **O_DIRECT** (bypasses the OS page cache so we measure the
  device, not RAM), sequential 1 MB writes, size ≫ the 2 GB controller
  cache (e.g. 32 GiB) so sustained rate past the cache burst is visible,
  logging bandwidth every second to see the *shape* of the curve; run
  `iostat -xy 1` on `sda` alongside and sample per-drive SMART counters
  either side to confirm the drives are the limiting element and compute
  write amplification, exactly as the characterization did.
- Re-run immediately (same LBAs, now dirty, since no TRIM frees them) as a
  steady-state control: a fast-then-slow pair is the GC/exhaustion
  signature; uniformly slow-from-the-first-second is a device/controller
  floor.

**Decision this settles:**
- Idle sequential **~400 MB/s+** → drives have headroom now → the loaded
  ~69 MB/s is contention/workload shape → TRIM is hygiene, not the cause;
  a full wipe is likely unnecessary and Phase 2 favors media/contention
  fixes.
- Idle sequential **~70 MB/s with the host otherwise idle** → no fast path
  on these drives, and TRIM cannot be delivered through this volume anyway
  → Phase 2 favors a fresh **over-provisioned** array (wipe+recreate) or
  different media (RAID 10 with added disks, or NVMe).
- In between (**~150–300 MB/s**) → run a short concurrency sweep (fio,
  CI-shaped small-file + high-fsync load) to find the throughput knee
  before committing.

**Non-destructive.** Writes to and deletes the plan's own scratch file on
the empty volume; adds ~0.06 TB to drives with ~96% endurance remaining.

### Phase 2 — Re-evaluate the optimization decision

**Goal:** with Phase 0's capability map and Phase 1's real numbers, choose
the cheapest change that actually restores write throughput and health,
and recommend concrete disk types if new hardware is warranted.

**Options on the table (ranked in the characterization, re-ranked here
against Phase 1 data):**
1. **NVMe in the empty x16 slot** — hundreds of thousands of IOPS, GB/s,
   working TRIM, bypasses SATA + the RAID controller. Robust to the open
   question. Recommend a specific enterprise NVMe (endurance/DWPD, capacity
   sized to containerd + PVC working set).
2. **Full wipe + recreate the existing array, over-provisioned** — resets
   FTL state (writing every LBA once during a secure-style prep, then
   creating a VD from only ~70–80% of raw). Costs the array's data (hence
   backup first) but needs no new hardware.
3. **Switch to RAID 10** — buy and install matched SSDs into the free bays
   (RAID 10 needs an even count ≥ 4; 5 bays free). Roughly N/2 × single-
   drive write, no parity penalty, single-drive fault tolerance. Recommend
   disk type: enterprise SATA/SAS SSD matched to the enclosure, sized and
   over-provisioned at creation. Explicitly authorized by the maintainer
   as a candidate even with hardware purchase.
4. **RAM-backed runner work volumes (tmpfs)** — 118 GiB free, ~0.3% memory
   pressure; robust to the open question because I/O never reaches storage.
   Needs an explicit cap and scales with churn-slot capacity `C`.
5. **Strip-size tuning** — minor, RAID-5-only.

**Output:** a recommendation with plain trade-offs and, if hardware is
recommended, exact part-class guidance — routed to the maintainer as the
one genuine product/spend decision.

### Phase 3 — Fully recoverable backup to the attached USB volume

**Goal:** an `rsync`-based, bit-faithful, **single-command-restorable**
backup of the xubuntu CI system to the attached USB drive, restorable onto
a clean xubuntu install.

**What to back up:** `sda4` (`/`, the CI system — the load-bearing data)
and, optionally, `sda5` (`/var/cache/ci-runner`, warm caches — regenerable
but cheap to keep). **Not** `sda2`/`sda3` (wipeable). The ESP/bootloader
is re-established by the clean install in Phase 7, so the backup captures
`/etc/fstab`, machine-specific config, k3s state, and data — not the boot
chain.

**rsync flags — the maintainer specified `rsync -vlaP`; recommendation to
discuss:** `-a` already implies `-l`, so `-vlaP` works but for a faithful
rootfs backup prefer **`rsync -aHAXS --numeric-ids --info=progress2`**:
adds `-H` (preserve hardlinks), `-A` (ACLs), `-X` (extended attributes,
which some tooling and security contexts depend on), `-S` (sparse-file
handling), and `--numeric-ids` (don't remap uid/gid through name lookups —
essential when restoring onto a fresh install whose name↔id mapping may
differ). `-P` = `--partial --progress` is retained. This is the standard
"back up a running Linux rootfs" incantation and is strictly safer than
`-vlaP` for bare-metal restore; adopt it unless the maintainer prefers the
literal flag set.

**Required excludes** (pseudo-filesystems and volatile/mount paths, or the
backup loops or captures garbage): `/proc`, `/sys`, `/dev`, `/run`,
`/tmp`, `/mnt`, `/media`, `/lost+found`, the USB mountpoint itself, and
swap. Use `--one-file-system` per source root so a stray mount isn't
swept in.

**Single-command recovery, stored on the volume:** a `restore.sh` at the
USB root that (1) takes the target root mountpoint as its one argument,
(2) rsyncs the captured tree back with the same faithful flags, (3)
regenerates `/etc/fstab` for the new disk/UUIDs, and (4) reinstalls and
updates the bootloader (`grub-install` + `update-grub` in a chroot) so the
restored system boots. The script is self-documenting and refuses to run
against a target it can't identify.

**Alternative considered:** block-level imaging (Clonezilla/`dd`/`partclone`)
is faster to restore identically but is inflexible to a changed disk
geometry (which is exactly what Phase 6 may produce) and captures the
old array's layout. **File-level rsync is the right tool here** precisely
because the restore target geometry will differ; noted for the record.

### Phase 4 — Verify the backup (prove it, don't trust it)

**Goal:** demonstrate the backup is complete and the restore path works,
before anything destructive.
- **Re-run the backup `rsync`.** A second pass must transfer effectively
  nothing (only files changed since the first pass) — an **effective
  no-op**. A large second transfer means the first was incomplete or
  excludes are wrong.
- **Dry-run the restore** (`restore.sh` against a scratch target, or
  `rsync -n`) and confirm it, too, is a near-no-op against a
  representative target.
- Record byte/file counts and the no-op evidence in the research note.
- Per fleet policy, "done" for this backup is the restore path **actually
  exercised**, not merely written.

### Phase 5 — Verify CI falls back to GitHub-hosted runners while the host is down

**Goal:** prove the ratified property "Availability MUST NOT become a merge
dependency" holds, so taking the host offline in Phase 6 does not block the
fleet.
- Clearing/emptying a repo's `CI_RUNNER_LABELS` routes its CI back to
  GitHub-hosted runners with no specification change (the documented
  fallback, verified once in `post-cutover-conformance-audit.md`).
- Exercise it live: on a representative repo, clear the labels, open a
  trivial PR, and confirm the CI matrix runs to green on `ubuntu-latest`
  hosted capacity with the self-hosted host quiesced. Record run IDs.
- This is the go/no-go gate for Phase 6.

### Phase 5.5 — Create the missing `poweredge-xubuntu-info` private repo

**Goal:** this host is the only member of the per-host documentation family
with no `*-info` repo. Create `thewoolleyman/poweredge-xubuntu-info` as a
**PRIVATE** repo mirroring the content and purpose of the existing
`vps-info`, `hp-xubuntu-info`, and `gmktec-xubuntu-info` — capturing the
hardware, firmware, RAID/disk layout, iDRAC, and access facts this plan has
been discovering, so they survive the rebuild rather than living only in
plan research.

**Why it sits here, immediately before the destructive work.** Everything
Phases 0–2 measured describes a machine that Phase 6 is about to change.
Recording the *pre-change* state is only possible now, and the restore in
Phase 7 needs exactly these facts. A `*-info` repo written after the rebuild
would silently lose the array's original geometry and the audit trail.

**The family's conventions** (audited 2026-08-28 across all three siblings):

- **`AGENTS.md` is the entry point, not a README.** Both `*-xubuntu-info`
  repos have no README at all; only the much larger `vps-info` has one, and
  it is a short pointer deferring to `AGENTS.md`. Add `CLAUDE.md` as a
  **symlink** to `AGENTS.md` (the pattern `vps-info` and `openclaw-info`
  use), never as a second file.
- **No front matter anywhere.** Metadata is bolded `**Key**: value` lines or
  a markdown Field|Value table.
- **Hand-authored prose; nothing script-generated.** Facts are typed after
  running a command, and the command is quoted alongside so a reader can
  re-derive it.
- **Timestamps are per-claim and inline** ("Recorded 2026-08-28", "OS at
  time of recording"), not a single "last audited" header — and are paired
  with an instruction to re-measure before acting.
- **Secrets by reference only** — name the Environment, the variable, the
  value *format*, and the loader path; never a value.
- **Negative assertions are first-class** — write down what the host does
  NOT have as loudly as what it does.
- **Cross-repo links are explicit**, with the boundary stated: host-specific
  facts live here; anything running on more than one host belongs in a fleet
  repo. Default branch `main` (the newer siblings' choice).

**Content to carry, from this plan and a live audit:**

1. `## Platform` — PowerEdge R630, service tag `JBS0JB2`, BIOS 2.18.1
   (2023-08-14), UEFI, 1U; 2 × Xeon E5-2696 v3 (72 threads), 188 GiB RAM;
   Ubuntu 26.04 LTS, kernel `7.0.0-29-generic`.
2. `## Storage` — PERC H730P Mini (FW `25.5.9.0001`), BBU Optimal, the RAID 5
   VD and its three Samsung `MZ7GE960HMHP-000V3` drives, the partition
   layout, and the measured performance envelope. **Include the negative
   assertion that TRIM never reaches these drives and that `fstrim.timer`
   reports healthy while doing nothing** — exactly the operational trap the
   characterization documented.
3. `## Management / iDRAC` — iDRAC 2.85, shared-LOM on `eno1`, the address,
   and the Phase 0 finding that it is currently unreachable. Dell boot keys
   (F2 System Setup, F11 Boot Manager, F10 Lifecycle Controller).
4. `## Network / Tailscale identity` — `poweredge-xubuntu`, `100.78.140.72`,
   `eno1` at `192.168.1.200`; ACL policy owned by `tailscale-admin`, edited
   there by PR, never here.
5. `## Remote access` — the `ssh poweredge-xubuntu` stanza's account caveat
   (`cwoolley`, not `ubuntu`), mirroring `hp-xubuntu-info/TAILSCALE_SSH.md`
   including its `## Verification` section.
6. `## PCIe expansion` — Slot 1 x16 free, Slot 2 holding a Radeon Cedar
   display adapter, and the **low-profile-only** constraint that the 1U
   chassis imposes.
7. `## Related repos` — `tailscale-admin` (tailnet ACLs and inventory) and
   `livespec-dev-tooling` (the k3s/ARC CI-runner provisioning that already
   targets this host). **Cross-link that provisioning; do not copy it here** —
   `vps-info`'s README records, at cost, that a service running on several
   hosts must not live in a per-host repo.
8. The Kubernetes/k3s setup and install notes from the `fleet-ci-runner-pool`
   plan's research (`design.md`, `k3s-arc-kueue-migration.md`,
   `cache-tier-2-design.md`, `post-cutover-conformance-audit.md`) —
   summarized to host-specific facts, with the fleet-wide machinery
   cross-linked rather than duplicated.

9. **The future expansion/optimization options** — carried over from this
   plan's `phase2-pricing-comparison.md` and
   `phase2-single-drive-raid10-analysis.md`. Maintainer-requested
   2026-08-28: these are to live in the host repo as well as here, so the
   next person asking "what can this box take?" finds the answer beside the
   hardware facts rather than inside a plan they would have to know existed.
   Carry the **decision content** — the RAID 5 vs RAID 10 arithmetic, the
   1U low-profile constraint, Slot 1's confirmed x4x4x4x4 bifurcation, the
   bay/caddy requirements, the SAS-vs-SATA trap — and **date the price
   figures explicitly as a 2026-08-28 snapshot taken during a NAND
   shortage**, since those go stale within weeks while the constraints do
   not.

**Boundary:** creating a repo under the maintainer's GitHub account is an
outward-facing action, so the repo creation itself is maintainer-gated even
though the content authoring is not.

### Phase 6 — Execute the chosen optimization

**Goal:** carry out the Phase 2 decision — over-provisioned recreate,
RAID-level change to RAID 10 with added disks, NVMe install, or a
combination — with a clear split of human-required physical actions and
agent-drivable steps.
- **Preconditions (all must hold):** Phase 4 backup verified, Phase 5
  fallback proven, maintainer go on the specific plan, and a **revert
  condition fixed in advance**.
- **Human-required actions** (enumerated per chosen path): seating drives
  in free bays; inserting the NVMe card in the x16 slot; booting the PERC
  HII/BIOS utility or driving iDRAC; confirming the destroy/recreate.
- **Agentic work while the array is unavailable** — scaffold a **reverse
  SSH tunnel from an Ubuntu rescue/live USB**: boot the host from a live
  USB, bring up networking, and open an outbound reverse tunnel
  (`ssh -R`) to a reachable endpoint so the array rebuild and reconfig can
  be driven agentically even with the primary OS offline. This needs, and
  the note will specify: the rescue image, a persisted authorized key, the
  outbound endpoint + port, and a keepalive. Out-of-band iDRAC is the
  preferred alternative where available and may make the tunnel
  unnecessary.
- Rebuild/initialize the new array, over-provisioned at creation.

### Phase 7 — Restore to a clean Ubuntu install and verify the host is fully back

**Goal:** a fresh, correctly partitioned Ubuntu install, the CI system
restored onto it, and the host verified fully available.
- **Recommended partitioning for a Kubernetes CI + agentic-factory host**
  (draft, finalized against the Phase 2 decision):
  - Small ESP (~1 GiB) + root on the resilient array (RAID 10 or the
    over-provisioned recreate).
  - **A dedicated fast scratch device/mount** (NVMe, or an over-provisioned
    scratch VD, or tmpfs) for `containerd` image/snapshot store and the
    k3s local-path PVC root — so CI churn never lands on `/` again (the
    blast-radius and mount-point findings from the characterization).
  - k3s pointed at the fast mount via `--data-dir`/local-path config, made
    a mount change rather than a k3s reconfiguration.
- **Restore:** run the volume's `restore.sh` against the new root; fix
  fstab/UUIDs; reinstall the bootloader; reboot.
- **Verify fully up:** host boots unattended, k3s healthy, ARC scale sets
  register, a real matrix-shaped PR dispatches to the self-hosted runners
  and goes green, and CI throughput/PSI are re-measured to confirm the
  optimization delivered. Re-point each repo's `CI_RUNNER_LABELS` back to
  self-hosted only after that proof.

## Sequencing

```
Phase 1 (idle perf write — NOW, fleet halted)  ─┐
Phase 0 (BIOS/controller research — anytime)    ─┼─► Phase 2 (decision)
                                                 │
Phase 3 (backup) ─► Phase 4 (verify backup) ─────┤
Phase 5 (CI fallback proof) ─────────────────────┘
                                                 ▼
                              Phase 6 (execute, maintainer-gated)
                                                 ▼
                              Phase 7 (restore + verify up)
```

Phases 0–1 and 3–5 are independent and can proceed in parallel; Phase 2
consumes 0+1; Phase 6 consumes 2+4+5 plus an explicit go; Phase 7 closes
it out. Destructive work never precedes a verified backup and a proven
fallback.

## Status as of 2026-08-28

| Phase | State | Where the detail lives |
|---|---|---|
| 0 — controller/BIOS management | **DONE** | `phase0-controller-management-and-tooling.md` |
| 1 — idle throughput measurement | **DONE** | `phase1-idle-throughput-measurement.md`, corrected by `phase2-measurement-correction-and-free-optimization.md` |
| 2 — optimization decision | **DONE, drives ordered** | `phase2-*.md`, `drive-expansion-compatibility-proof.md` |
| — CI churn relocated off `/` | **DONE** | `containerd-relocation-completed.md` |
| — `io.pressure` instrumentation | **DONE, live** | `livespec-dev-tooling#1650`, installed on the host |
| 3 — backup to USB | **DONE** | `phase3-backup-and-restore-procedure.md` |
| 4 — verify the backup | **DONE** — backup verified; restore rehearsed end-to-end on `sda3` (steps 1–4 pass; boot test optional/deferred) | `restore-verification-plan.md` → "Rehearsal result", `research/restore.sh` |
| 5 — prove CI falls back to GitHub-hosted | **NOT STARTED** | this document, Phase 5 |
| 5.5 — `poweredge-xubuntu-info` repo | **NOT STARTED** | this document, Phase 5.5 |
| 6 — execute the rebuild | blocked on 4-restore, 5, and the drives arriving | this document, Phase 6 |
| 7 — restore and verify up | blocked on 6 | this document, Phase 7 |

**Two corrections to this document's own assumptions, established by doing the
work:**

- Phase 2's option ranking is superseded. A full wipe to reset FTL state is
  **not** justified — Phase 1 eliminated the exhaustion hypothesis. Four
  drives were ordered instead, and RAID 10 requires destroy+recreate because
  MegaRAID cannot migrate a single-span VD into a spanned one.
- Phase 3 assumed the PVC root held **13 GB**. It holds **36 K at idle** — the
  figure came from a measurement taken under load, and the directory is
  transient per-job. That volatility later broke a backup pass.

**~~The critical open item is that `restore.sh` has never been run.~~ RESOLVED
2026-08-28.** Phase 4 was half complete; the restore rehearsal has now been run
end-to-end against the disposable `sda3`. `restore.sh` was first fixed (gap 1:
it dropped `/var/cache/ci-runner` and the bind mounts; gap 2: it would have
touched the live `sda1` ESP) and the fstab logic proven offline — which caught a
fresh double-`nofail` bug that read as correct. The rehearsal ran to completion
with a correct fstab, kernels present, exact ownership/setuid fidelity, and the
live host untouched. See `restore-verification-plan.md` → "Rehearsal result".
The only thing still un-measured is an actual boot (step 5), deliberately
deferred. The remaining pre-Phase-6 gates are now **Phase 5** (prove CI falls
back to GitHub-hosted runners) and **Phase 5.5** (the `poweredge-xubuntu-info`
repo), plus a fleet-halted re-run of the backup for a coherent pre-rebuild
snapshot.

## Open questions to resolve within the plan

- The Phase 1 discriminator's verdict (drive headroom vs. floor) — decides
  whether a wipe is even necessary.
- Phase 0: is RLM RAID5→RAID10 supported on this controller, or is
  destroy+recreate mandatory?
- Phase 2: new hardware (NVMe and/or RAID-10 SSDs) yes/no, and exact
  part-class — the one genuine spend decision, routed to the maintainer.
- Phase 6: iDRAC out-of-band availability (which, if present, is safer
  than a rescue-USB reverse tunnel).
