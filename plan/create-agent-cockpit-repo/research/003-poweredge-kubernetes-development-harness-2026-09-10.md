# PowerEdge Kubernetes development and autonomous test harness

Date: 2026-09-10

## Decision

Use the k3s cluster on `poweredge-xubuntu` as the primary autonomous
development, integration-test, and pre-production dogfood environment for
`agent-cockpit-info`.

The cluster harness has two complementary execution tiers:

1. a fast, long-running Ubuntu-plus-XFCE container with an NVMe-backed
   persistent workspace; and
2. an ephemeral KVM Ubuntu guest, launched on PowerEdge from Kubernetes, for
   the bare-host, systemd, reboot, hostname, Tailscale, credential-sealing, and
   VNC assertions that a container cannot faithfully prove.

A real fresh VPS remains the final promotion gate. The cluster replaces manual
development/retesting and catches nearly all defects before VPS spend or human
identity enrollment; it does not redefine container behavior as proof of host
behavior.

The planning/implementation loop is autonomous. Agents should not interrupt the
maintainer with incremental setup questions. They use the defaults recorded
here, iterate until all mechanically testable parity gates pass, and present one
consolidated final identity/acceptance ceremony only when the system is ready.

## Measured cluster facts

These facts were read from the live cluster and PowerEdge host on 2026-09-10:

- both `poweredge-xubuntu` and `gmktec-xubuntu` are Ready on k3s
  `v1.36.2+k3s1`, Ubuntu 26.04 LTS, amd64;
- PowerEdge exposes 72 allocatable CPUs and `396114240Ki` allocatable memory;
- live use was about 13 CPU cores and 13 GiB memory, leaving ample capacity;
- the PowerEdge host reports 377 GiB RAM total and about 365 GiB available;
- `nvmeb/ci-workvols` is a 1.5 TiB XFS filesystem with reflink support,
  mounted at `/var/cache/ci-runner/k3s-storage`, with about 1.5 TiB free;
- `nvmeb` also has about 2.19 TiB of unallocated VG extents;
- `nvmea/ci-containerd` gives containerd a separate 1.5 TiB NVMe filesystem;
- the default `local-path` StorageClass uses `WaitForFirstConsumer`, has
  `reclaimPolicy: Delete`, does not support expansion, and maps to
  `/var/lib/rancher/k3s/storage`, which is the NVMe work-volume bind mount;
- PowerEdge has VT-x and `/dev/kvm` available;
- KubeVirt is not installed;
- the current `gates` service account can create pods only in its existing
  namespace and cannot read nodes/storage classes or manage PVCs. It is not an
  acceptable cockpit-development credential.

This capacity makes the proposed workload small relative to the host. The
desktop and agents are not CPU-intensive at idle; Chrome, installs, builds, and
parallel agents create bursts, so limits should preserve headroom for CI rather
than pretending the workload always uses one core.

## Why not only a “standard Xubuntu container”

The target starts from bare Ubuntu and installs a selected XFCE desktop stack;
it does not require a separately branded Xubuntu host image. The reproducible
container base should therefore be a digest-pinned official Ubuntu 26.04 image
with the exact XFCE/Xvfb/x11vnc packages installed by the repository. This
tests what the playbook actually owns and avoids an unversioned third-party
“Xubuntu” image.

A container is valuable but cannot alone demonstrate:

- bootstrapping a bare machine and making systemd PID 1;
- host reboots and enablement ordering;
- kernel hostname and machine identity semantics;
- `systemd-creds` host-key binding and replacement-host resealing;
- an ordinary in-box Tailscale node with TUN and Tailscale SSH;
- host firewall/listener behavior;
- disk discovery, fstab, mount ordering, and reattachment;
- absence of accidental container-only privileges.

Running the whole cockpit as a privileged systemd pod would make tests pass for
the wrong reasons and give agent credentials an unnecessarily strong path to
the Kubernetes node. The KVM tier supplies a real kernel and init system while
keeping the ordinary cockpit workload out of a privileged host container.

## Harness architecture

```text
agent branch / commit
        |
        v
OCI build + static tests ----------------------------+
(Ubuntu 26.04 + exact XFCE/cockpit packages)          |
        |                                              |
        +--> ephemeral container integration Jobs     |
        |    - schema/lint/unit tests                  |
        |    - Ansible role application               |
        |    - tmux/zsh/Atuin/CLI/config checks        |
        |    - Xvfb/XFCE/Chrome/1Password launch       |
        |                                              |
        +--> agent-cockpit-dev-0 StatefulSet           |
        |    - long-running tmux/agent dogfood         |
        |    - retained NVMe workspace PVC             |
        |    - containerization compatibility          |
        |                                              |
        +--> KVM runner Pod on poweredge-xubuntu ------+
             - digest-pinned Ubuntu cloud image
             - disposable guest root disk
             - retained NVMe workspace/data disk
             - cloud-init -> Ansible -> reboot
             - real systemd/Tailscale/VNC/hostname tests
                          |
                          v
                  fresh external VPS gate
```

The same committed roles and acceptance scripts run in all tiers. Tests may
declare a capability as not applicable in a container, but they may not quietly
turn a missing host assertion into green; the corresponding KVM/VPS evidence
must exist.

## Kubernetes resources

Create a dedicated `agent-cockpit-dev` namespace. Do not reuse `gates` or
`arc-runners`.

The repository owns namespaced desired state under a `deploy/kubernetes/`
Kustomize tree:

- service account `agent-cockpit-driver`;
- Role/RoleBinding for Jobs, Pods, logs/exec, StatefulSets, Deployments,
  Services, ConfigMaps, Events, and leases needed by this harness;
- no node, PV, StorageClass, cluster-role, host-secret, or unrelated-namespace
  authority;
- one long-running `agent-cockpit-dev-0` StatefulSet;
- ephemeral integration Jobs keyed by Git commit;
- a KVM-runner workload pinned to `poweredge-xubuntu`;
- network policies and Services required for SSH/VNC test probes;
- resource quotas so a runaway agent cannot starve CI;
- commit-SHA image references, never moving `latest` tags.

Cluster-scoped/host glue has a different owner and is applied ahead of the
namespaced harness:

- a label dedicated to cockpit test placement on `poweredge-xubuntu`;
- the host mount and static local PV;
- `/dev/kvm` exposure to the KVM runner through the narrowest viable device
  mechanism;
- the pre-created retained PVC or binding contract;
- a refreshable, namespace-scoped kubeconfig for cockpit-driving agents.

This glue belongs with PowerEdge/k3s host configuration, not in the bare-VPS
roles. `agent-cockpit-info` declares the interface it requires and verifies it.
The cluster owner implements that interface without making production cockpit
hosts depend on `livespec-dev-tooling`.

## NVMe persistence

Do not use an ordinary default `local-path` PVC for the durable cockpit
workspace. Its current reclaim policy is Delete, it cannot expand, and a claim
could bind on the other node without explicit placement.

Provision a dedicated, capacity-bounded local volume on `nvmeb`:

1. allocate an initial 250 GiB LV from the roughly 2.19 TiB free extents in
   `nvmeb`;
2. create a labeled filesystem and mount it at a cockpit-specific path such as
   `/var/lib/agent-cockpit-volumes/dev-0`;
3. represent it as a static Kubernetes Local PersistentVolume with
   `persistentVolumeReclaimPolicy: Retain` and node affinity to
   `poweredge-xubuntu`;
4. bind it to a named RWO claim in `agent-cockpit-dev`;
5. mount the filesystem as `/home/ubuntu/workspace`, a real directory;
6. keep guest root disks and throwaway test state outside the retained work
   subvolume, so destroy/rebuild tests can prove the boundary;
7. add capacity, inode, mount, ownership, and backup health to
   `cockpit-doctor`.

The exact initial size remains an inventory value. 250 GiB comfortably covers
the measured current workspace while remaining a small fraction of available
NVMe. Expansion is a host/LV/filesystem operation with an explicit runbook, not
a false claim that the current StorageClass expands volumes.

The development volume is not its own backup. Before it contains unique work,
assign an independent backup/snapshot owner and exercise restore. Reclaiming the
Kubernetes objects must leave the retained LV/filesystem intact.

## Fast container tier

Build a project-owned test image from a digest-pinned official Ubuntu 26.04
base. Install the exact selected packages and create user `ubuntu`; do not use a
third-party desktop image or clone the live VPS filesystem.

Use the container tier for every commit:

- schemas, linting, idempotence primitives, and generated-file drift;
- package repository/key setup and pinned binary checks;
- shell, zsh, Atuin Ctrl-R, tmux config parsing, and terminal capability tests;
- structural Claude/Codex/Pi, plugin, hook, and MCP reconciliation tests;
- non-secret repository-reconciliation fixtures, including dirty worktrees,
  duplicate origins, provider failures, and a no-origin directory;
- Xvfb/XFCE startup, shared D-Bus, Chrome/CDP, and 1Password Desktop
  install/launch smoke tests;
- OpenTelemetry emission into a disposable collector and assertions over the
  resulting events;
- listener and network-policy negatives that are meaningful inside a pod.

The fast tier uses fake/disposable credentials and test repositories. It never
mounts the retained real workspace, host Tailscale state, host credential
store, Docker/containerd socket, or a whole user home.

## Long-running container dogfood

`agent-cockpit-dev-0` is a one-replica StatefulSet pinned to PowerEdge. It
mounts the retained workspace and exercises the eventual container shape:

- `ubuntu` owns `/home/ubuntu/workspace`;
- tmux and agent processes run as `ubuntu`;
- only declared config and credential projections are mounted;
- updates use a controlled drain/handoff, image rollout, and resume sequence;
- a Pod replacement is expected to lose processes/tmux sockets while retaining
  work product and durable handoffs;
- readiness requires tmux/config/agent/collector/desktop probes, not merely a
  running PID;
- resource requests begin around 1 CPU/4 GiB and limits around 8 CPU/32 GiB,
  then are tuned from observed use;
- no host Docker socket, containerd socket, host home, or broad hostPath is
  mounted.

This tier is where autonomous agents do real non-production work and find
container-boundary defects. It is not allowed to carry production credentials
or become the only proof for host-specific requirements.

## Full-host KVM tier

Because PowerEdge exposes `/dev/kvm` and VT-x, a Kubernetes runner can launch a
real Ubuntu guest without installing KubeVirt initially. Use QEMU/KVM with
user-mode networking where practical and pass only the KVM device plus the
specific guest disks. Do not make the agent cockpit pod itself privileged.
The comparative decision and reconsideration triggers are recorded in
`004-virtualization-runtime-decision-2026-09-10.md`: direct QEMU is the initial
runtime, KubeVirt is the preferred scale-up path, and Firecracker is reserved
for a future high-density/disposable-worker requirement rather than VPS parity.

Each acceptance run:

1. creates a disposable root overlay from a digest/checksum-pinned Ubuntu 26.04
   cloud image;
2. attaches a fresh test workspace disk, or a snapshot/clone of a fixture disk;
3. injects only ephemeral cloud-init SSH material;
4. boots the VM and applies the committed bare-host bootstrap as `ubuntu`;
5. completes automated test-identity setup using disposable/scoped credentials;
6. runs Ansible twice and requires a clean second pass;
7. reboots the guest and proves enabled-service recovery;
8. exercises hostname, systemd, systemd-creds host binding, Tailscale test-node
   behavior, Tailscale SSH, VNC/XFCE/Chrome/CDP/1Password launch, all three
   agents, MCPs, repository reconciliation, and Honeycomb events;
9. destroys the root disk, recreates it, reattaches only the declared workspace
   disk, re-mints identities, and proves recovery;
10. publishes logs, JUnit/JSON evidence, screenshots where useful, and
    Honeycomb trace links keyed by commit and run ID.

A reserved test tailnet identity must not collide with production
`agent-cockpit-{n}` names. Use a clearly test-scoped allocation managed by the
same naming allocator, and never copy its state into a VPS. Tests that cannot
use a disposable real external credential run against a contract fake on every
commit and a scoped real test credential in the protected acceptance lane.

KubeVirt may be reconsidered if maintaining the small QEMU runner becomes more
complex than operating KubeVirt. It is not a prerequisite for the first
harness, because it is absent today and adding a cluster virtualization control
plane is a materially larger operational change.

## Autonomous driver access

The current `gates` kubeconfig is deliberately insufficient and must remain so.
Create a separate short-lived/refreshed kubeconfig wrapper for the
`agent-cockpit-driver` service account. Distribute it to authorized cockpit
agents using the existing refresh-over-Tailscale-SSH pattern, but scope its
RBAC to the `agent-cockpit-dev` namespace and named workload operations.

Agents may autonomously:

- build/push commit-addressed test images through the existing cluster-local
  registry path;
- create and delete their integration Jobs;
- read status/events/logs and exec into their own test pods;
- roll the dogfood StatefulSet to a reviewed commit;
- launch, observe, and tear down KVM acceptance runs;
- collect artifacts and retry after code/config fixes.

They may not autonomously:

- allocate/delete host LVs or PVs after initial reconciliation;
- read arbitrary cluster Secrets or other namespaces;
- mutate nodes, StorageClasses, cluster roles, or CI runner workloads;
- mount host credentials, runtime sockets, or unrelated host paths;
- weaken listener, sandbox, network, or content-capture policy to make a test
  pass.

## Test/promotion ladder

| Gate | Environment | Required evidence |
|---|---|---|
| G0 | repository CI | schema/lint/unit/security/pin checks |
| G1 | ephemeral Ubuntu+XFCE Jobs | roles/configs/idempotence fixtures, desktop and telemetry smoke |
| G2 | long-running StatefulSet | real autonomous agent work, persistent workspace, drain/restart recovery |
| G3 | disposable KVM guest | bare bootstrap, systemd, reboot, reseal, network, VNC and destroy/rebuild parity |
| G4 | fresh external VPS | provider networking and final production-shaped acceptance |
| G5 | second instance | no hidden host literals; actual cattle/fleet proof |

Promotion is monotonic: a higher gate does not excuse a lower failure. The
implementation is “completely working” for maintainer review only when G0–G3
are green, all initially requested features have requirement-to-evidence
mapping, and the only remaining steps are the consolidated real-account/VPS
ceremony and observations that cannot safely be delegated.

## Default decisions for autonomous progress

To honor the instruction not to ask the maintainer piecemeal questions, use
these defaults until contradictory evidence requires escalation:

- Ubuntu 26.04 LTS amd64 for container and KVM test lanes;
- standalone `agent-cockpit-info` with pinned external seams;
- selected ACFS behavior re-expressed directly, no wholesale ACFS install;
- one credential/identity per cockpit or test instance;
- AWS CLI always installed; AWS workload identity implemented as a separately
  gated optional profile and tested with a scoped test identity;
- operational Honeycomb telemetry enabled, content capture disabled;
- 250 GiB retained NVMe development volume, adjustable through inventory;
- no production credential or copied machine identity in cluster tests;
- one consolidated maintainer ceremony only after autonomous G0–G3 parity.

Escalate early only for a genuine safety/authority blocker, such as needing to
weaken cluster isolation, expose a public listener, use/rotate an unapproved
credential, delete retained data, or expand beyond the authorized repositories
and cluster test scope. Ordinary implementation choices and test failures stay
with the autonomous agent loop.
