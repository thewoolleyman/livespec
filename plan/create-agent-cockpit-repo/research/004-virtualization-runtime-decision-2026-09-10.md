# Virtualization runtime decision: QEMU/KVM first

Date: 2026-09-10

## Decision

Use direct QEMU with KVM acceleration for the PowerEdge full-machine test lane.
Do not adopt Firecracker, KubeVirt, Cloud Hypervisor, Kata Containers, Incus,
LXD, or libvirt as an initial dependency.

This is a workload-fit decision, not a claim that QEMU is universally the best
virtual-machine monitor. The cockpit harness needs one or a few trusted,
VPS-shaped Ubuntu machines with maximum boot and device compatibility. It does
not need very high microVM density or millisecond-scale cold starts.

The fast development tier remains an ordinary Ubuntu-plus-XFCE container. QEMU
exists only to prove behaviors that share-the-host-kernel containers cannot.

## Required shape

```text
Kubernetes Job on poweredge-xubuntu
  └── qemu-system-x86_64 with /dev/kvm
        ├── checksum-pinned Ubuntu cloud-image base
        ├── disposable qcow2 root overlay
        ├── ephemeral NoCloud/cloud-init seed
        └── retained or freshly cloned workspace/data disk
```

Run QEMU directly from the Job rather than adding a persistent libvirt daemon.
Use KVM acceleration, virtio disks/network, qcow2 backing overlays, a serial
console, and user-mode networking where it satisfies the test. Add only the
narrow device/capability access required by measured failures; do not begin
with a privileged cockpit pod.

The guest boots its own Linux kernel and systemd. It therefore exercises a real
machine hostname, enablement/reboot ordering, fstab/mount behavior,
`systemd-creds` host binding, Tailscale node behavior, VNC listener placement,
and root-disk replacement independently from the Kubernetes host kernel.

## Alternatives considered

| Alternative | Strength | Why it is not the initial choice |
|---|---|---|
| Direct QEMU/KVM | Broad hardware/boot compatibility; ordinary Ubuntu cloud images; cloud-init; qcow2 overlays; familiar diagnostics | Selected; its larger feature surface and slower startup are acceptable for a few trusted test guests |
| Firecracker | Small device model, fast startup, high density, strong microVM isolation posture | Requires more bespoke kernel/rootfs, networking, disk, API/jailer, and Kubernetes integration; density/startup are not current requirements |
| KubeVirt | Kubernetes-native VM API, lifecycle, Services, PVC integration, and mature multi-VM operations | Installs an additional cluster virtualization control plane and still uses QEMU/KVM underneath; excessive for one initial guest and absent from the cluster today |
| Cloud Hypervisor | Modern, smaller cloud-focused VMM with conventional virtio concepts | Less operational familiarity and ecosystem/tooling than QEMU without a measured benefit for this workload |
| Kata Containers | Transparent VM isolation for Kubernetes pods | Models an isolated pod rather than a machine-rebuild laboratory; awkward for cloud-init, machine identity, reboot, and attached-host recovery assertions |
| Incus/LXD VM | Friendly image, storage, networking, and VM lifecycle management | Adds another daemon/control plane nested beside Kubernetes and duplicates orchestration already owned by the harness |
| libvirt over QEMU | Stable declarative VM management and broad tooling | A persistent daemon, XML domain layer, sockets, and state add complexity that a commit-scoped single-guest Job does not need |

## Why Firecracker is not better here

Firecracker would be favored if measurements showed that the product needed to
start hundreds or thousands of short-lived, mutually isolated microVMs with
minimal memory overhead and a deliberately small virtual-device surface. None
of those is an initial cockpit acceptance requirement.

For this plan, Firecracker makes the important path harder:

- stock Ubuntu cloud-image compatibility is less direct than QEMU;
- kernel and root filesystem preparation become harness-owned work;
- networking/TAP and Kubernetes lifecycle integration require more glue;
- its deliberately minimal device model provides no benefit to the headless
  XFCE/Xvfb desktop test and can complicate general VPS resemblance;
- snapshot/cold-start improvements do not materially shorten Ansible package
  installation, agent setup, Chrome tests, or the deliberate reboot cycle;
- the guest is trusted configuration under test, so reduced VMM attack surface
  is useful but not worth dominating the first implementation.

Firecracker remains a valid later execution-runtime experiment for isolated
agent workers. It is not the reference environment used to certify that a
commodity VPS can be rebuilt.

## Why QEMU/KVM is the best first choice

- PowerEdge already exposes VT-x and `/dev/kvm`.
- CPU, RAM, container storage, and NVMe workspace capacity are abundant, so
  QEMU overhead is not a binding constraint.
- the test can boot a conventional checksum-pinned Ubuntu cloud image rather
  than building a custom kernel/rootfs distribution;
- cloud-init and SSH-based Ansible closely resemble common VPS provisioning;
- disposable qcow2 overlays make “destroy root, retain data, rebuild” cheap and
  explicit;
- serial console and QEMU diagnostics are straightforward to collect as
  Kubernetes Job artifacts;
- the implementation can remain a small, version-pinned launcher rather than a
  permanent virtualization service;
- successful QEMU tests transfer directly to the external-VPS acceptance lane,
  while the container lane separately tests future pod viability.

## When to reconsider

### Reconsider KubeVirt when

- more than a few concurrent or long-lived cockpit VMs are routinely needed;
- native Kubernetes VM objects, declarative power state, PVC attachment,
  Services, snapshots, or scheduling become recurring code in the custom
  runner;
- maintaining the direct QEMU launcher becomes more costly than operating the
  KubeVirt control plane;
- another cluster workload already justifies and operates KubeVirt.

KubeVirt is the preferred scale-up path because it preserves QEMU/KVM guest
compatibility while replacing bespoke lifecycle glue.

### Reconsider Firecracker when

- measured startup latency or per-guest memory prevents required concurrency;
- the architecture shifts from one interactive cockpit to many disposable
  isolated agent workers;
- custom kernel/rootfs production and networking integration already have a
  maintained owner;
- hostile multi-tenant workload isolation becomes a stronger concern than
  broad VPS compatibility.

### Reconsider Cloud Hypervisor when

- a smaller VMM becomes an explicit security/maintenance goal;
- required Ubuntu, cloud-init, networking, disk, snapshot, and observability
  paths have equivalent automated evidence;
- the team has operational ownership rather than adopting it solely for
  novelty.

### Reconsider libvirt when

- domain lifecycle persists beyond individual Kubernetes Jobs;
- the project needs a stable management API shared by several tools;
- direct command-line construction becomes an unsafe configuration surface.

## Acceptance implications

The implementation must not grade “QEMU process started” as success. The guest
lane passes only when the VM:

- boots from a known Ubuntu base with its own systemd and kernel;
- accepts the same `ubuntu` bootstrap and Ansible roles intended for a VPS;
- reaches a clean second convergence;
- reboots and restores every enabled cockpit service;
- proves Tailscale test identity, SSH, VNC/XFCE/Chrome/CDP, 1Password wrapper
  sealing semantics, Claude/Codex/Pi, MCPs, and Honeycomb evidence;
- destroys and recreates its root disk while retaining only the declared data
  disk;
- exports machine-readable results tied to the Git commit and test-run ID.

The container lane and QEMU lane are both required. A QEMU pass does not prove
that the cockpit can run cleanly as a pod, and a container pass does not prove
that a bare Ubuntu VPS can be reproduced.

## Version-selection note

This decision records architecture only. At implementation time, verify and pin
the current supported QEMU package/image, Ubuntu cloud-image digest or checksum,
machine type, virtio behavior, and any required Kubernetes device exposure
against primary upstream documentation. The web-data connector was unavailable
when this comparison was discussed, so no upstream release-number claim is
carried forward from that conversation.
