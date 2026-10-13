# 001 — gate lifted, maintainer rulings, confirmed Definition of Done, and the child set (2026-10-13)

Written by the first attended resume of this plan (session
`claude:factory-worker-nodes-gitops`, 2026-10-13). Research note 000 in this
directory is the write-once opening brief; it carries the maintainer's verbatim
statement of done and six session-derived assertions. This note records what
changed between its writing and this resume, every ruling the maintainer made in
this session, the Definition of Done as confirmed, and the children filed to carry
it. Status is read from the ledger; nothing here shadows it.

## How to read this note

Every work-item id below is written beside the repository whose ledger holds it,
because the fleet spans many repositories and a bare id is ambiguous. "Epic"
means this plan's anchor `livespec-sqvj7p` in the livespec ledger. "Host-captured"
and "factory-captured" are the proof modes of
`SPECIFICATION/contracts.md` §"Definition of Done and Proof of Done" in the
livespec repository: a factory-captured assertion is proven inside the factory
sandbox that implements the item, a host-captured one only on a live host after
the maintainer's apply.

## What changed since note 000 (all verified live on 2026-10-13)

| Claim in note 000 | State on 2026-10-13 | Evidence |
|---|---|---|
| Plan `gitops-deployment-discipline` (epic `livespec-qurhq2`, livespec) gates every host change | **Lifted.** The epic closed and the plan was archived on 2026-10-10 after a verified Proof of Done | livespec PR #2805; the Proof of Done comment of 2026-10-10T21:45Z on `livespec-qurhq2` |
| gmktec-xubuntu NotReady since 2026-09-28 (node-password mismatch) | **Ready.** Rejoined on its own after the poweredge reboot of 2026-10-12 23:12 UTC | `kubectl get nodes` on poweredge-xubuntu; the mechanism is the `agent_node_password` role in livespec-dev-tooling `ansible/ci-pool.yml` |
| R5 merged but never converged; xa6o and 9btv open | **Converged.** churn-slot 12, untainted, cohort quota 44, drift clean; both items closed | the same Proof of Done; `bd show` in the livespec-dev-tooling ledger |
| hp-xubuntu not a node | Unchanged: no k3s binary, no `/etc/rancher`, no kubeconfig | read-only ssh on 2026-10-13 |
| The poweredge datastore is a tmpfs | Unchanged, and plan `k3s-on-gmktec-for-vps-usage` (epic `livespec-sab5gn`, livespec) is replaying unattended reboots against that design | its Proof of Done comments of 2026-10-13 |

The Fabro-currency plan (livespec-orchestrator-beads-fabro, epic `bd-ib-6tcjfx`)
named this plan "unblocked" in its 2026-10-13T07:20Z handoff. The maintainer
confirmed the go-ahead in this session.

### hp-xubuntu as measured on 2026-10-13 (read-only)

| Fact | Value |
|---|---|
| CPUs, memory | 16, 30 GB; swap 8 GB file plus 160 GB `sandbox-swap` partition |
| Operating system | Ubuntu 26.04 LTS, kernel 7.0.0-31-generic |
| Disks | `sda1` 466 GB ext4 root (no label), `sda2` 1 GB EFI, `sda3` 1.4 TB ext4 `data` at `/data`; `sdc1` 160 GB swap `sandbox-swap`; `sdc2` 3.6 TB ext4 `sandbox-stores` at `/srv/sandbox-storage`; `sdb1` a backup disk |
| Storage tiers of the CI recipe (`ci-cache`, `ci-containerd`, `ci-workvols`) | none, and none wanted |
| Network | wired `enp11s0` 192.168.1.4/24; wireless `wlp10s0` 192.168.1.54/24 on the same subnet, so the node address must be pinned; tailnet 100.68.193.50 |
| Docker sandbox slice | `fabro-sandbox.slice`: MemoryHigh 22G, MemoryMax 24G, CPUQuota 1400%; ten live Fabro runs at measurement |
| Fabro servers | `fabro-server` (max_concurrent_runs 10, raised from 7 on 2026-10-13) and `fabro-server-candidate` both active |
| Ports 80, 443, 6443, 10250 | none listening; the cluster has ServiceLB and Traefik disabled, so joining claims none of them |

## The maintainer's rulings in this session

1. **hp-xubuntu joins factory-only.** It carries a taint CI pool pods do not
   tolerate (the `node_taints` role's one key `node-role/ci`, with a factory
   value) and advertises `ADMISSION_CAPACITY_C=0`, so no CI runner pod is ever
   scheduled on it and the cohort churn-slot quota stays 44. This agrees with the
   ruling the maintainer gave in the k3s plan session on 2026-10-12, recorded on
   this epic as a scope event, in the maintainer's words: "It shouldn't be
   running CI load, but it can definitely be a worker, so it can be used if
   absolutely necessary. In other words, all of the plumbing should be there,
   but it can be tainted or whatever, so it doesn't actively run CI unless we
   change that."
2. **The backend plugin owns surviving a control-plane reboot.** A persistent
   datastore (embedded etcd, the k3s plan's R6 remainder) is NOT a prerequisite
   here. The plugin's logical sandbox identity and lost-sandbox policy must
   survive or cleanly re-dispatch after a rebuild. Recorded as an explicit
   deferral to plan `kubernetes-sandbox-backend` (livespec-orchestrator-beads-fabro,
   epic `bd-ib-nmuyjc`).
3. **poweredge-xubuntu runs factory pods too.** Factory eligibility is a per-node
   label read from each node's committed phase0 profile; poweredge, gmktec and hp
   all carry it. poweredge stays untainted, because nothing in the CI stack
   carries a toleration. The `factory` namespace ResourceQuota is the only bound
   on what factory runs take from the CI pool; the churn-slot derivation is not
   re-done.
4. **The Definition of Done is eight assertions.** The six session-derived
   assertions of note 000 were amended: assertion 3 (gmktec untainted, churn-slot
   12, quota 44, xa6o and 9btv closed) was already proven elsewhere and is
   replaced by hp's factory-only contract including its survival of a poweredge
   reboot; Role and RoleBinding were added to assertion 4; network reach became
   assertion 7, carrying the brief's fifth requirement that had no assertion; and
   assertion 8 restores the open-and-re-close proof the maintainer had confirmed
   on 2026-10-12. The epic description carries the eight; they are not repeated
   here so there is one source.

## The children, in the livespec-dev-tooling ledger

Filed on 2026-10-13 under the one-slice/one-ledger rule (a child whose work lives
in livespec-dev-tooling is filed once, there, and never mirrored here). Each
description names this epic. The carrier map is the scope event of
2026-10-13 on the epic; this table is a reader's convenience, not the record.

| Child (livespec-dev-tooling ledger) | Delivers | Intake verdict at filing |
|---|---|---|
| `livespec-dev-tooling-7we6po` | hp as a factory-only agent: phase0 profile `hp-xubuntu.env`, `ci_pool` entry (hp stays in `sandbox_hosts`), role gating for an agent with no CI tiers, kubelet reservations and the recorded coexistence budget, a declarative factory-label reconcile on all three nodes, rehearsal recorded | ready |
| `livespec-dev-tooling-f5e6vl` | the `factory` namespace as converge artifacts under `ci-runner/k3s/phase2/factory/`: Namespace, ServiceAccount, Role, RoleBinding, token Secret, ResourceQuota, NetworkPolicy, applied by `converge-ci-stack.sh` at every boot | ready |
| `livespec-dev-tooling-sqobqv` | the factory kubeconfig on hp: rendered on poweredge over the tailnet at every converge, delivered by a `fabro-hosts.yml` role with pull-on-401 refresh | pending-approval, behind `f5e6vl` |
| `livespec-dev-tooling-sszvvw` | `verify-factory-reach.sh`: a Job-based check that a factory pod on hp and on gmktec reaches the Dolt tenant and the telemetry receiver and pulls the sandbox image | pending-approval, behind `7we6po` and `f5e6vl` |

Every child carries factory-captured assertions the sandbox can prove and a
`### Host-captured` section for what only the live hosts show. No child touches
a host: every apply is the maintainer's step from the control node `vps`,
`just ansible-drift` read first, then `just ansible-apply`, per the GitOps
deployment discipline.

## The coexistence budget as currently known

This is the input the hp child must turn into committed values and a derivation
beside them. hp has 30 GB. The Docker slice takes up to 24 GB (and `sccache-redis`
runs inside it). Both Fabro servers run outside the slice. The k3s agent, kubelet
and containerd need a reservation of their own, and the kubelet needs eviction
thresholds so it never races the slice for the last gigabyte. Honest arithmetic
leaves hp about 3 GiB and under one CPU allocatable to pods while the slice is at
its current size. So hp's cluster membership is PLUMBING until the backend plan's
cutover steps the slice budget down; the child records that rather than inflating
hp's capacity. The slice's own expiry is written in the `docker_sandbox_slice`
role's `HOST_VARS.md` in livespec-dev-tooling: it retires when the Kubernetes
sandbox backend enforces per-run limits.

## Deferrals

Recorded on the epic's scope event of 2026-10-13, each with what, why and where:
the persistent datastore (backend plugin owns reboot survival); retiring the
Docker slice (the backend plan's cutover assertion); the plugin's node selector,
toleration and per-run limits (backend design child); the k3s plan's R6 and R7
remainders, the gate-remote item `livespec-dev-tooling-2u2c`, and the dead
tailscale serve mapping for hp's parked homelab Fabro instance; and the Codex and
pi fleet-host-guard ports (`livespec-driver-codex-ygbpka`, `livespec-driver-pi-m7idkt`).

## Coordination with the k3s plan

`k3s-on-gmktec-for-vps-usage` is driving approved reboot drills of
poweredge-xubuntu through `ansible/reboot-ci-server.yml`. The hp apply and the
converge run for the factory namespace must not be scheduled inside one of its
drills; read that epic's latest handoff before the first apply.
