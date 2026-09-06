# 002 — Goal 0: every host this plan touches is rebuildable from bare metal, from git; the record map; the re-derived slice order (2026-09-06)

Written 2026-09-06 after the maintainer's direction of the same day, which
this note records verbatim in substance and which SUPERSEDES §5 "The slice
order, challenged" of research/001. Everything measured in research/001
stands; what changes is what the plan optimizes for first.

## The maintainer's direction (2026-09-06, settled)

1. **GitOps is the absolute, number-one priority of this plan.** Every host
   this plan touches — `gmktec-xubuntu`, `poweredge-xubuntu`, `hp-xubuntu` —
   MUST be 100 % reproducible: rebuildable from scratch, from git, if needed.
   **The only exception is the VPS**, because it pre-existed. Nothing is
   changed on a live host by hand; every host change is a committed
   installer or manifest first and is applied from that commit.
2. **Every change is spec-driven and lands in its owning repository**:
   livespec `SPECIFICATION/non-functional-requirements.md` for the fleet
   property, livespec-dev-tooling for the gitops realization and its own
   specification, and the per-host info repositories (`vps-info`,
   `poweredge-xubuntu-info`, `gmktec-xubuntu-info`, `hp-xubuntu-info`) for
   host facts. Proposed changes go through `/livespec:propose-change`, an
   independent review, and `/livespec:revise`.
3. **"From scratch" means bare metal to CI node, scripted end to end**
   (maintainer's choice among three definitions offered 2026-09-06): the
   first mile — disk, RAID, LVM layout, base OS install — is scripted too,
   not a recorded-and-rehearsed hand procedure and not an image restore.
   This closes `livespec-ifwnqj.3` and `.4` as this plan's work and applies
   to gmktec from its first step.
4. The plan starts by reviewing everything the predecessor
   (`poweredge-raid-array-maintenance`, epic `livespec-g52yrb`) did and
   recorded, and verifying it is in gitops; and it folds in what the other
   session's gitops-rebuildability audit left unresolved.

Goals 1–6 of research/000 stand unchanged beneath goal 0. The etcd
decisions of research/000 stand.

## Where the gitops record lives today (verified 2026-09-06 from the clones)

| Layer | Repository | Files |
|---|---|---|
| Host property contract | livespec | `SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner host requirements" (v220). Reproducibility is stated ONLY for the storage tiers ("reproducible from the repository that provisions the host's job runtime and idempotently re-appliable"); no clause states that the whole node is rebuildable from git. |
| CI pool, node-local half | livespec-dev-tooling | `ci-runner/k3s/provision-k3s.sh` (pinned k3s install); `ci-runner/k3s/phase2/install-node.sh` (the ordered runbook; argument 32 since PR #1828); `phase2/k3s-config/`, `storage-layout/` (five LABEL fstab lines, `migrate-tier.sh`, the k3s `RequiresMountsFor` drop-in), `node-inotify-budget/`, `node-keyring-budget/`, `apparmor/`, `node-extended-resource/`, `container-hook/`, `sccache/install-sccache-binary.sh`, `cache-telemetry/`, `host-thermal/`, `host-tools/`, `datastore-tmpfs/`, `storage-sweep/`, `../secret-reinjection/` |
| CI pool, cluster half | livespec-dev-tooling | `phase2/reconstruct/converge-ci-stack.sh` + `.service` (rebuilds the cluster from git on every boot), `render-sa-kubeconfig.sh`; `arc/values-*.yaml`, `arc/hook-pod-template.yaml`; `kueue/` + `DERIVATION.md`; `local-path-provisioner/`; `sccache/`; `crates-proxy/`; `warm-cache/` (incl. pypi-proxy); `runner-pod-lifecycle/`, `wedged-runner/`, `arc-log-archive/`; `../observability/install-observability.sh` |
| CI pool provisioning-repo contract | livespec-dev-tooling | `SPECIFICATION/non-functional-requirements.md` §"Adaptive JIT runner admission budget", §"Runner-pool build cache tiers", §"Runner-pool cache telemetry"; `contracts.md` §"Self-hosting"; v057 `scale-set-ceiling-bounded-to-fair-share`; `.ai/ci-node-storage-tiers.md`, `.ai/ci-node-capacity-reads.md` |
| Privileged gate runner (separate trust tier) | livespec-dev-tooling | `ci-runner/gate-runner/` |
| poweredge host record | poweredge-xubuntu-info | `AGENTS.md` (§Platform, §Storage with the LVM/label table, §Management / iDRAC, §Network / Tailscale identity, §Remote access, §PCIe expansion, §Kubernetes / k3s, §CI routing), `STORAGE_EXPANSION.md`, `FAN_COOLING.md`, `TAILSCALE_SSH.md` |
| poweredge rebuild artifacts | livespec | `plan/archive/poweredge-raid-array-maintenance/research/`: `restore.sh`, `run-backup.sh`, `build-recovery-usb.sh`, `test-recovery-usb.sh`, `recovery-usb-build.md`, `restore-verification-plan.md`, `phase3-backup-and-restore-procedure.md`, `nvme-add-tmpfs-tiering-and-clean-raid5-rebuild-plan.md`, `nvme-pex8747-gen3-link-fault.md`, `containerd-relocation-completed.md` |
| gmktec host record | gmktec-xubuntu-info | `AGENTS.md`, `llm-server.md` (verbatim llama.cpp build, model download, launcher, systemd unit, key handling) |
| hp host record | hp-xubuntu-info | `AGENTS.md`, `README.md` (service table pointing at the fleet repos), `TAILSCALE_SSH.md` |
| hp and VPS fabro-side services | fabro-hosts | `services/fabro-server/`, `services/sccache-redis/` (hp), `services/container-reclaim/`, each with `hosts/<host>.env` |
| Host monitoring | otel-collector | `config.ci-runner-host.yaml`, `systemd/*.ci-runner-host.service`, `scripts/install-ci-runner-host.sh`, `k8s/otel-collector-rbac.yaml`; `config.hp-factory.yaml` + `scripts/install-hp-factory-host.sh` for hp. Honeycomb triggers and boards are NOT in any repository found — an open item below. |
| Tailnet ACLs | tailscale-admin | openspec-driven; edited by PR there only |
| VPS (the exception) | vps-info | `AGENTS.md`, `services/*/install.sh`; five files dirty from another session at the time of this note |
| Livespec adopter with its own host-record contract | homelab | `SPECIFICATION/contracts.md` §"Machine inventory record", `hosts/example-host.md`; its fleet is EMPTY and it governs the Hetzner/AWS substrate, not these hosts. Named here so nobody assumes it already records them. |

## What the predecessor did, and whether it is in gitops

From a prepared disk onward, everything is in git and was proven by
unattended reboots on 2026-09-04 and 2026-09-06: the labeled storage tiers,
the k3s config file, the tmpfs datastore, the boot converge, every
node-local installer, the host collector. The other session's independent
gitops-rebuildability audit (2026-09-06) found four things; two are closed
(btop-loop moved into `host-tools/`; the runbook's from-scratch capacity
argument corrected to 32, livespec-dev-tooling PR #1828 merged 11:00Z) and
three remain open under epic `livespec-ifwnqj`:

- `livespec-ifwnqj.3` — the first mile is hand-run: the seven-drive RAID-5
  virtual disk, GPT/ESP and LVM PV, VG `poweredge` and its LVs were created
  from the Recovery USB on 2026-09-04 with no script; only the end state is
  recorded, and `restore.sh` refuses to partition by design.
- `livespec-ifwnqj.4` — `build-recovery-usb.sh` predates the two boot fixes,
  so the artifact in git does not reproduce the proven stick.
- `livespec-ifwnqj.5` — the host is behind git in two places (the
  runner-pod-lifecycle scan copies three commits old; the hooks directory
  from `install-node.sh` step 7c absent).

Two further gaps this session found, not filed anywhere yet:

- **The gmktec host record is wrong about memory.** `gmktec-xubuntu-info`
  `AGENTS.md` says 64 GiB. `sudo dmidecode -t memory` on 2026-09-06 lists
  128 GB of LPDDR5-8532 (Micron) installed; firmware carves 64 GiB out for
  the iGPU (`mem_info_vram_total`), leaving `MemTotal` 62 GiB to the OS.
  `llm-server.md`'s "62 GiB usable RAM budget" is the OS-visible figure and
  is consistent. The record must be corrected in that repository before any
  capacity derivation cites it.
- **hp carries an untracked hotfix**: `/usr/local/sbin/disk-guard.sh` with
  `docker-prune.timer` + `disk-guard.timer`, documented in
  `hp-xubuntu-info/README.md` §Caveats as existing nowhere in git. hp is
  named in scope by the maintainer, so under goal 0 that must move into
  `fabro-hosts` (with the low-water/journal-cleanup replacement decided) or
  be retired by a committed change.

And one observation about poweredge's OS layer, which the maintainer's
definition now settles: the OS is reproduced today by restoring an rsync
image with `restore.sh` from the Recovery USB, not by installing from a
recipe. Under definition 3 the base OS install is scripted too; `restore.sh`
and the backup remain the DISASTER-RECOVERY path (data), not the
REBUILD path (configuration).

## The slice order, re-derived under goal 0

Research/001 §5 ordered slices by value to the VPS and to CI throughput.
Under goal 0 the order is by what makes the next step reproducible. The
recommendation, for the maintainer's objection:

1. **Spec first.** Propose, in livespec `non-functional-requirements.md`
   §"Self-hosted CI runner host requirements", the property that a host
   carrying fleet CI MUST be rebuildable from bare metal by a committed,
   rehearsed, idempotent procedure owned by the repository that provisions
   its job runtime; that a hand-run step in that procedure is a defect, not
   an accepted gap; that the host's own record carries hardware facts and
   the first-mile parameters (controller, drives, partition roles) but never
   the procedure; and that a rebuild is proven by executing the procedure,
   not by reading it. Propose the matching provisioning-repository clause in
   livespec-dev-tooling's specification (the recipe's home, its rehearsal
   obligation, and that a per-host profile is data the one recipe consumes).
   Independent review, then `/livespec:revise`. Nothing below is filed as
   implementation until this is ratified, because it is what every child
   will be verified against.
2. **Close poweredge's gitops gaps** — the first mile scripted
   (`livespec-ifwnqj.3`), the Recovery USB builder made to reproduce the
   proven stick (`.4`), host-behind-git converged (`.5`), and the hp hotfix
   relocated or retired. These are the plan's inherited debt; a second node
   built by the same recipe is the rehearsal that proves it.
3. **gmktec, from bare metal, by the recipe** — a `gmktec-xubuntu` host
   profile (data) in livespec-dev-tooling consumed by the same recipe: base
   OS install, role-labeled tiers on the 1441 GiB of unpartitioned NVMe with
   the `RequiresMountsFor` drop-in, the k3s AGENT install pinned to
   `--node-ip 192.168.1.156` with the node token, the node-local subset of
   `install-node.sh`, a `NoSchedule` taint; plus the two two-node
   preconditions research/001 found (node pins for `sccache-redis`,
   `crates-proxy`, `pypi-proxy`, the warm-cache CronJob; a per-node
   cache-telemetry endpoint) landed in the converge tree; the
   gmktec-xubuntu-info record corrected (128 GB) and extended with the k3s
   facts; the LLM service's coexistence stated in that record. The
   pre-existing llama.cpp install is already a verbatim recipe in
   `llm-server.md`; under goal 0 it becomes a scripted, idempotent
   installer in the owning repository (that is the `local-llm` fleet's
   repository, not this plan's — an explicit deferral below).
4. **The delegation primitive** — `tls-san` in `k3s-config/config.yaml`
   (and its header's "no externally reachable API server" premise amended);
   the `gates` ServiceAccount, RBAC, ClusterQueue, `WorkloadPriorityClass`
   and Job template as manifests the converge applies; the bare mirror on
   the RAID and the read-only in-cluster git daemon as converge artifacts;
   the `gate-remote` client in livespec-dev-tooling wired into
   `check-pre-push`'s fall-through only; node affinity preferring gmktec.
   The VPS-side steps (`kubectl`, the rendered kubeconfig) are the one
   permitted hand-installed surface, recorded in `vps-info`.
5. **Untaint gmktec for CI** — the per-node uv warm seed, gmktec's own
   churn-slot derivation by `livespec-ifwnqj`'s method, a
   `gmktec-xubuntu-k3s` scale set for the per-member addressing and the
   proving job the ratified clauses require, the two-node Kueue quota
   re-derivation, the untaint.
6. **Embedded etcd on the tmpfs** with the maintenance set and the
   monitoring rewrite of research/000 — last, per research/001 §5's
   measurement rule (any `Slow SQL` in the next fleet-wide backlog at
   C = 32 moves it ahead of 5).

Monitoring (goal 6) is folded into every slice that changes topology:
otel-collector's `config.ci-runner-host.yaml` for the node and datastore
signals; where the alerting lives (Honeycomb triggers) is the open item
below.

## Draft requirement carriers (for the scoping event; not yet filed)

- R0 — the from-scratch-rebuildable property and its provisioning-repository
  clause, proposed and ratified (slice 1).
- R1 — poweredge's first mile scripted and rehearsed (`livespec-ifwnqj.3`);
  the Recovery USB builder reproduces the proven stick (`.4`); host matches
  git (`.5`). Owned today by epic `livespec-ifwnqj`; to be re-parented or
  cross-linked here — recorded in the handoff for the maintainer.
- R2 — hp's untracked hotfix relocated into `fabro-hosts` or retired.
- R3 — gmktec joined as a tainted agent by the recipe, with its tiers,
  node-local installs, singleton pins, per-node telemetry endpoint, and a
  corrected host record.
- R4 — the delegation primitive, every cluster-side piece a converge
  artifact, the client in livespec-dev-tooling, fail-closed.
- R5 — gmktec untainted for CI with its own derived cap, per-member
  addressing, and the proving job.
- R6 — embedded etcd with the maintenance set and monitoring migration.
- R7 — monitoring updated in the same change as each topology change.

## Explicit deferrals (to be recorded in the scoping event)

- The llama.cpp install on gmktec becoming a scripted installer: owned by
  the `local-llm` fleet's repository; this plan records its coexistence
  facts and touches nothing of it.
- Moving fabro's docker sandboxes onto the Job primitive; the orchestrator
  janitor's host-local `just check`; reducing the number of Claude sessions
  on the VPS (research/000 "later"; none needed for goals 0–6).
- The kine-vs-scheduling discriminating measurement (research/001 §3).
- `hp-xubuntu` as a gate host; `macmini` as any gate or CI host.
- Honeycomb triggers/boards as code: not in any repository today; whether
  they become one is a monitoring-ownership question for the otel-collector
  repository, raised in the handoff, not decided here.

## What this note could not settle

- The owning home for the bare-metal recipe: `livespec-dev-tooling`
  `ci-runner/k3s/phase2/storage-layout/` (beside `migrate-tier.sh`) versus a
  new `ci-runner/k3s/phase0-bare-metal/`. Recommendation: a new
  `phase0-bare-metal/` tree, because the recipe runs before k3s exists and
  before `install-node.sh`'s precondition (an admin kubeconfig) holds.
- Whether `livespec-ifwnqj.3/.4/.5` are re-parented under this plan's epic
  or left under `livespec-ifwnqj` and cross-linked (the maintainer's call;
  the other session wrote them "where the successor plan will find them").

## Read-first chain

This note → research/000 (goals 1–6, etcd decisions) → research/001
§"Bottom line" and §1–§4 (the measurements; §5 superseded here) →
`livespec-ifwnqj.3`, `.4`, `.5` (the inherited gaps) →
`poweredge-xubuntu-info/AGENTS.md` §Storage (the end state the first mile
must produce) → livespec-dev-tooling `ci-runner/k3s/phase2/install-node.sh`
(where the recipe hands off).
