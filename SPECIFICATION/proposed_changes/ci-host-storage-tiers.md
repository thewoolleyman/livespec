---
topic: ci-host-storage-tiers
author: claude-fable-5-1
created_at: 2026-09-04T17:32:26Z
---

## Proposal: Storage tiers on a self-hosted CI host that runs jobs as containers

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add one clause to §"Self-hosted CI runner host requirements" stating, as host-observable properties, what a containerized-job host owes for its storage: the operating system and every non-reconstructible artifact on redundant durable media; job churn (image store, work volumes) and any boot-rebuilt cluster datastore off the OS volume and allowed on non-redundant or volatile media; every tier identified by ROLE medium-neutrally so a media move never edits the git-held mount configuration; that configuration reproducible from the provisioning repository; the job runtime refusing to start while a tier is absent; media moves by verified copy plus identity transfer in a job-free window; and PCIe-attached media accepted only after the link trains clean under I/O. Physical placement stays a host-record fact, never spec content.

### Motivation

The 2026-09-04 storage work on the fleet's CI host (livespec plan poweredge-raid-array-maintenance, epic livespec-g52yrb; sibling plan ci-runner-pod-lifecycle-reliability, epic livespec-ifwnqj) established every one of these properties in the fleet's realization — LABEL-keyed tiers installed from git by livespec-dev-tooling's storage-layout installer, a k3s drop-in that refuses to start on a missing tier, the datastore on tmpfs rebuilt from git on boot, and the containerd store and runner work volumes moved onto an NVMe by copy + relabel with /etc/fstab byte-identical before and after — yet §"Self-hosted CI runner host requirements" says nothing about storage at all. Each property was paid for: a job runtime that starts with a tier missing runs the whole pool's churn on the root filesystem silently until it fills (the 2026-08-28 relocation's motivating failure); a UUID-keyed mount configuration drifted out of git on every media change until labels replaced it (livespec-el5y); a stale tier copy on a drive that came back from a failed attempt would have silently shipped old image layers had it been reused; and an NVMe card whose PCIe link was marginal at Gen3 halted the host's firmware at boot (Dell UEFI0066), which no OS-side setting could rescue — the acceptance test that would have caught it is a link survey run before any tier is placed on the medium. Without the clause a second host provisioned to this section could satisfy every existing requirement while placing the pool's churn on its OS volume, keying mounts by UUID, or accepting a marginal link, and nothing in the specification would name that as non-conforming. The clause is stated as properties (what a host must exhibit), consistent with the section's own opening rule that realization is owned by whichever repository provisions the host; the physical placement of each tier — which drive, which slot — is a host fact and is deliberately kept out of the specification (it lives in the host's own record, poweredge-xubuntu-info AGENTS.md §Storage, and in the provisioning repository's README).

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Self-hosted CI runner host requirements", insert the following new clause paragraph immediately BEFORE the clause that begins:

> **Availability MUST NOT become a merge dependency.**

(and therefore immediately AFTER the clause that begins "**A host that runs jobs as containers and caps job concurrency through a scheduler MUST size the node's schedulable-unit capacity above the full expansion of that cap.**"). The inserted paragraph, verbatim:

> **Storage tiers on a host that runs jobs as containers.** The host's operating system, and every fleet artifact on the host that is not reconstructible without operator action, MUST reside on redundant durable media. The state that jobs churn — the container image store and each job's work volume — and any cluster datastore the host rebuilds from version control on boot MUST reside off the operating system's volume, so that job churn can neither exhaust nor stall it, and MAY reside on non-redundant or volatile media because every byte of it is reconstructible. Each such tier MUST be identified by ROLE in a medium-neutral way — a filesystem label or an equivalent identity that is the same on any medium — so that moving a tier between media never changes the mount configuration; that configuration, the identity-to-mountpoint binding, and the refusal in the next sentence MUST be reproducible from the repository that provisions the host and idempotently re-appliable, and a tier's physical placement is a host fact recorded in the host's own record, never in this specification. The job runtime MUST refuse to start while any tier it writes to is absent, rather than silently run on the root filesystem. A tier MUST move between media only by copying its contents to the new medium and transferring the role identity in a window in which no job is running, with the copy verified before the identity moves; the old volume MUST NOT retain the role identity afterwards, and a copy of a tier on a medium that left the host MUST NOT be reused once jobs have run. Storage media attached over a PCIe link MUST be accepted only after that link has trained at its rated width and speed with no correctable errors under sustained I/O, measured before any tier is placed on the medium — a link that trains marginally can halt the host's firmware at boot, which no operating-system setting can rescue. Maintainer-declared 2026-09-04.

No other sentence of the section changes. No `## ` heading is added, changed, or removed (the section is an H3 and the clause is a bold-led paragraph in its existing style), so no tests/heading-coverage.json co-edit arises.
