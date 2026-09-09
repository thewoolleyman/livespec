# 006 — Plan status: the original goals, what is done, and what is left (2026-09-09)

This document is the second half of the maintainer's directive recorded in
`plan/k3s-on-gmktec-for-vps-usage/research/004-ansible-migration-direction-2026-09-09.md`
§1 in this repository (livespec). That directive had two parts. The first part —
migrate host provisioning off the home-grown installer shell and onto Ansible —
is merged, and is listed under §"The Ansible migration" below. The second part
was stated as *"then when complete, I want you to stop and present me a summary
of everything in the original goals, what we've done, and what's left."* That
summary had produced no committed artifact; the plan's status existed only as
comments on the work-item ledger, which no reader outside that ledger can reach.
This file is that artifact.

## How to read this document, and what its notation means

Three sections follow — **THE ORIGINAL GOALS**, **WHAT IS DONE**, and **WHAT IS
LEFT** — and all three use the same spine, so a reader can pick any one label and
read straight across the three sections to learn what it required, what shipped,
and what remains.

That spine is the **requirement carriers**, written `R0` through `R7`. A
requirement carrier is a single named requirement of this plan, drafted in
`plan/k3s-on-gmktec-for-vps-usage/research/002-goal-zero-gitops-from-bare-metal-and-the-record-map-2026-09-06.md`
§"Draft requirement carriers" in this repository (livespec) and recorded on the
scope comment of epic `livespec-sab5gn` in the work-item ledger. There are eight
of them and they are not phases: several were worked concurrently, and two of
them (`R5` and `R6`) were never started at all.

One carrier, `R4`, is itself divided into eight **slices**, written `S1` through
`S8`. A slice is one factory-sized unit of implementation work with its own
work-item; the slices and their dependency order are the table in
`plan/k3s-on-gmktec-for-vps-usage/research/003-r4-delegation-primitive-design-and-slices-2026-09-07.md`
§"The slices" in this repository (livespec). Slice numbering is local to `R4`;
no other carrier has slices.

Two further terms recur below and are defined here rather than at each use. The
**converge** is the boot-time reconciler
`ci-runner/k3s/phase2/reconstruct/converge-ci-stack.sh` in the
livespec-dev-tooling repository, which rebuilds the k3s cluster's objects from
git on every boot; a thing is "a converge artifact" when the converge applies it,
which is what makes it reproducible from git rather than hand-applied. A **gate**
is one run of a repository's full `just check` aggregate performed to authorize a
`git push`, which today runs on whichever host issued the push.

Every pull request number below is written beside the repository that owns it,
because the fleet spans many repositories and a bare number is ambiguous. Every
file path is likewise written beside its owning repository.

The statuses below were read from the work-item ledger live on 2026-09-09 and
are accurate as of that date. Facts drawn from the in-repository research notes
rather than from that ledger reading are attributed to the note they come from,
and where a status is genuinely not known, this document says so instead of
guessing.

---

## THE ORIGINAL GOALS

The plan opened with the maintainer's six numbered goals, recorded verbatim in
substance in
`plan/k3s-on-gmktec-for-vps-usage/research/000-brief-from-vps-info-investigation-2026-09-06.md`
§"Maintainer's goals" in this repository (livespec). In short: keep the pre-push
gate exactly as strong as it is and move only *where* it runs rather than *what*
it runs; make that offload generic and container-based; run a central Kubernetes
control plane on `poweredge-xubuntu` that schedules work onto other nodes with
the continuous-integration cache tiers available to that work at no cost; make
`gmktec-xubuntu` the first additional node; open `gmktec-xubuntu` to
continuous-integration runners once its prerequisites are met, for extra headroom
when `poweredge-xubuntu` is at its ceiling; and update monitoring for whatever
datastore or topology changes land.

A seventh goal, numbered zero because it outranks the other six, was added by
maintainer direction on 2026-09-06 and is recorded in
`plan/k3s-on-gmktec-for-vps-usage/research/002-goal-zero-gitops-from-bare-metal-and-the-record-map-2026-09-06.md`
§"The maintainer's direction" in this repository (livespec): every host this plan
touches must be one hundred percent reproducible from git, rebuildable from bare
metal, with the VPS as the sole exception because it pre-existed. Nothing is
changed on a live host by hand.

The eight requirement carriers are what those seven goals were decomposed into.

**R0 — the from-bare-metal-rebuildable property, ratified as specification.**
Propose and ratify, in the livespec repository's
`SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner host
requirements", the property that a host carrying fleet continuous integration
must be rebuildable from bare metal by a committed, rehearsed, idempotent
procedure owned by the repository that provisions its job runtime; that a
hand-run step in that procedure is a defect rather than an accepted gap; and that
a rebuild is proven by executing the procedure rather than by reading it. Propose
the matching clause in the livespec-dev-tooling repository's own specification,
naming that repository as the recipe's home. This carrier gated every other one:
nothing below was to be filed as implementation until it was ratified, because it
is what every child would be verified against.

**R1 — close the gitops gaps `poweredge-xubuntu` inherited.** The predecessor
plan left three recorded gaps, owned by epic `livespec-ifwnqj` in the work-item
ledger. `livespec-ifwnqj.3` required the first mile of a rebuild — the
seven-drive RAID-5 virtual disk, the GPT partition table and EFI system
partition, the LVM physical volume, the volume group and its logical volumes — to
be scripted rather than hand-run from a Recovery USB stick. `livespec-ifwnqj.4`
required `build-recovery-usb.sh`, which lives in this repository (livespec) at
`plan/archive/poweredge-raid-array-maintenance/research/build-recovery-usb.sh`,
to actually reproduce the Recovery USB stick that was proven in practice; the
committed builder predates two boot fixes and does not. `livespec-ifwnqj.5`
required the running host to match git, which it did not in two places.

**R2 — relocate the untracked hotfix on `hp-xubuntu` into a repository.**
`hp-xubuntu` carried `/usr/local/sbin/disk-guard.sh` together with a
`docker-prune.timer` and a `disk-guard.timer`, documented in the hp-xubuntu-info
repository's `README.md` §Caveats as existing nowhere in git. Under goal zero
that had to move into the fabro-hosts repository, which already owns that host's
services, or be retired by a committed change.

**R3 — join `gmktec-xubuntu` to the cluster, built by the one recipe.** Build
`gmktec-xubuntu` from bare metal using the same recipe `R0` requires, driven by a
per-host profile that is data rather than a second recipe; lay down its
role-labelled storage tiers on the unpartitioned NVMe space; join it as a k3s
*agent* — a worker node, not a second control plane — with its node IP pinned to
the wired interface; run the node-local subset of the runbook
`ci-runner/k3s/phase2/install-node.sh` in the livespec-dev-tooling repository;
apply a `NoSchedule` taint so nothing schedules there until its capacity is
derived; and correct and extend the gmktec-xubuntu-info repository's host record,
which was wrong about the machine's memory.

**R4 — build the delegation primitive.** This is the carrier that answers the
problem which opened the plan: the VPS was saturated by pre-push gates. `R4`
moves a gate off the pushing host and onto a Kubernetes Job in the cluster,
without weakening what the gate runs. Its eight slices are:

- **S1** — add the tailnet name and address to `tls-san` in the
  livespec-dev-tooling repository's `ci-runner/k3s/phase2/k3s-config/config.yaml`
  so the API server presents a certificate valid over the tailnet, and amend the
  "no externally reachable API server" premise both places assert it.
- **S2** — a `gates` namespace, a ServiceAccount in it, and a Role granting
  exactly `create`, `get`, `list` and `watch` on Jobs and pods plus `get` on pod
  logs — nothing cluster-scoped, nothing on Secrets — all as converge artifacts,
  with the existing credential renderer
  `ci-runner/k3s/phase2/reconstruct/render-sa-kubeconfig.sh` in the
  livespec-dev-tooling repository learning a `--server` argument so the rendered
  credential names the tailnet address rather than loopback.
- **S3** — a dedicated Kueue `ResourceFlavor`, `ClusterQueue`, `LocalQueue` and
  `WorkloadPriorityClass` for gates, quotaed on real CPU and memory on
  `gmktec-xubuntu` rather than on the continuous-integration churn-slot resource,
  so admitting a gate cannot consume the pool's own admission budget.
- **S4** — a bare git mirror on `poweredge-xubuntu`'s cache tier plus a read-only
  in-cluster git daemon serving it, as converge artifacts, so a pod on any node
  can fetch the exact tree being gated without involving GitHub, together with a
  pruning rule for the accumulating `refs/gates/*` namespace.
- **S5** — the gate Job template: the container image resolved per repository
  from that repository's own workflow rather than baked in, real CPU and memory
  requests, an explicit test-parallelism value, the cache environment reused from
  the existing runner hook pod template, the queue label, a toleration for
  `gmktec-xubuntu`'s taint, node affinity preferring `gmktec-xubuntu`, and a
  time-to-live so finished Jobs are collected rather than accumulating as
  control-plane objects.
- **S6** — an audit of every check target that reads a credential, because two
  of them shell out to `gh api` and exit zero with a warning when unauthenticated;
  a gate pod without a token would report green having silently skipped them.
  The slice projects the least-privilege credentials as Secrets in the `gates`
  namespace and adds a check that *fails* rather than warns inside a gate pod.
- **S7** — the `gate-remote` client in the livespec-dev-tooling repository, wired
  into `check-pre-push`'s fall-through branch only, leaving the existing
  green-token fast path untouched; fail-closed, so a failed Job, a lost
  connection, an unreachable API server or an unauthenticated credential all
  refuse the push rather than passing it; and on a genuine pass, writing the
  existing green token keyed on the pushed tree hash.
- **S8** — the VPS-side surface: `kubectl` plus the rendered scoped credential,
  which is the one hand-installed surface the plan permits, recorded in the
  vps-info repository.

**R5 — untaint `gmktec-xubuntu` for continuous integration.** Seed the per-node
package warm cache on the new node, derive `gmktec-xubuntu`'s own churn-slot
admission capacity by the same method the predecessor plan used for
`poweredge-xubuntu`, add a `gmktec-xubuntu-k3s` runner scale set for the
per-member addressing and the proving job the ratified clauses require,
re-derive the Kueue quotas for a two-node pool, and then remove the taint. This
is the carrier that delivers goal 5, the extra headroom.

**R6 — move the datastore to embedded etcd.** Replace the kine-over-SQLite
datastore on the 2 GB tmpfs with k3s's embedded etcd, for control-plane stability
under write churn rather than for speed, together with the maintenance set that
etcd on a tmpfs requires — compaction interval verified, the snapshot cron
disabled or pointed at durable storage, an explicit backend quota, a periodic
defragmentation timer — and the monitoring rewrite that follows, because
seventeen files across two repositories key on the SQLite-era `Slow SQL` journal
signature that etcd does not emit.

**R7 — monitoring rides along with each topology change.** This carrier is a
discipline rather than a deliverable: whichever slice changes topology updates
the monitoring in the same change, rather than deferring it. It applies to `R3`
through `R6` and was deliberately not given a standalone slice.

---

## WHAT IS DONE

**R0 — done, ratified and landed in both repositories.** In the livespec
repository, **pull request 2624** merged 2026-09-06, carrying `history/v221` and
the clause *"A host carrying fleet CI MUST be rebuildable from bare metal by a
committed procedure"* into `SPECIFICATION/non-functional-requirements.md`
§"Self-hosted CI runner host requirements". In the livespec-dev-tooling
repository, **pull request 1864** merged 2026-09-06, carrying `history/v058` and
a new specification section, "Runner-pool node rebuild recipe", which names that
repository as the recipe's home. With both ratified, the gate on filing the
remaining carriers as implementation was released.

**R1 — two of three closed.** `livespec-ifwnqj.3` is closed: the first mile is
scripted. `livespec-ifwnqj.5` is closed: the running host matches git. The third,
`livespec-ifwnqj.4`, is not done and is carried in WHAT IS LEFT below. The ledger
reading of 2026-09-09 records these as closed work-items and does not record
pull request numbers for them, so none are cited here rather than inventing any.

**R2 — done.** `livespec-cy2syw` is closed; the untracked disk-guard hotfix on
`hp-xubuntu` is relocated into the fabro-hosts repository. As with `R1`, the
ledger reading records the closure without a pull request number, so none is
cited.

**R3 — done.** `livespec-sab5gn.2` is closed. `gmktec-xubuntu` was built from
bare metal by the one recipe, joined the cluster as an agent at `192.168.1.156`,
reached `Ready`, was tainted `node-role/ci=pending:NoSchedule` with an admission
capacity of zero, and brought up its three storage tiers; the gmktec-xubuntu-info
repository's host record now records the node's cluster role. Two supporting
facts come from
`plan/k3s-on-gmktec-for-vps-usage/research/003-r4-delegation-primitive-design-and-slices-2026-09-07.md`
in this repository (livespec) rather than from the ledger reading: the
livespec-dev-tooling repository's **pull request 1903** pinned the four hostPath
singletons to `poweredge-xubuntu` by node selector, closing the hazard that one
of them could restart onto `gmktec-xubuntu` against an empty directory; and that
repository's **pull request 1828** corrected the node runbook's from-scratch
capacity argument.

**R4 — the ratified clause and six of eight slices are closed; a seventh is
discharged in substance.** The carrier's own specification clause,
`livespec-sab5gn.3`, is closed. Seven of the eight slices are tracked in the
livespec-dev-tooling repository's work-item ledger and the eighth in this
repository's (livespec):

- **S1**, `livespec-dev-tooling-vlku` — closed. The tailnet subject alternative
  name is in the API server's certificate.
- **S2**, `livespec-dev-tooling-y8em` — closed. The `gates` namespace, its
  ServiceAccount and its role-based access control are converge artifacts.
- **S3**, `livespec-dev-tooling-ewyx` — closed. The gates `ClusterQueue` and
  priority class exist and are converged.
- **S4**, `livespec-dev-tooling-2hno` — closed 2026-09-09 against the
  livespec-dev-tooling repository's **pull request 2094**, which committed the
  bare mirror and the read-only in-cluster git daemon. The code is merged; it has
  not been converged onto the host, which is the blocking fact recorded in WHAT
  IS LEFT below.
- **S5**, `livespec-dev-tooling-sk8f` — closed. The gate Job template and its
  renderer exist.
- **S6**, `livespec-dev-tooling-ul61` — closed, and behaviourally proven: a
  target that needs a credential now fails rather than warning when it runs
  unauthenticated inside a gate pod.
- **S8**, `livespec-sab5gn.1` in this repository (livespec) — at status
  `acceptance`, discharged in substance by the Ansible role `gates_kubeconfig`
  applied to the VPS. Its original form, an approximately hundred-line shell
  installer, merged in the vps-info repository as **pull request 64** and was
  never run; the Ansible role that replaced it landed in the livespec-dev-tooling
  repository's **pull request 2077** and was applied to the VPS and verified
  against the live API server, per
  `plan/k3s-on-gmktec-for-vps-usage/research/005-ansible-migration-estate-inventory-2026-09-09.md`
  §7 in this repository (livespec).

The remaining slice, **S7**, is not done and is the subject of WHAT IS LEFT.

Beyond the slices, one end-to-end exercise on 2026-09-08 is worth recording as
progress: a real gate Job, rendered from master, was admitted by Kueue on the
gates queue and scheduled onto `gmktec-xubuntu`. The delegation plane therefore
works from the client's submission through admission and scheduling; it failed
closed at exactly one unbuilt component, which is `S4`'s daemon.

**R5 — nothing is done.** No work-item was ever filed for this carrier.

**R6 — nothing is done.** No work-item was ever filed for this carrier.

**R7 — nothing is done as a standalone carrier, and none was intended.** No
work-item was ever filed for it, because it is a discipline folded into `R3`
through `R6` rather than a separate slice. There is therefore no merged pull
request attributable to `R7` on its own; what monitoring work happened rode
along inside the `R3` and `R4` changes that touched topology. One
monitoring defect found while designing `R4` was filed separately in the
livespec-dev-tooling repository as `livespec-dev-tooling-sdu2` — pod-side cache
telemetry posting to an address the host collector does not bind, so the spans
are silently dropped while every job stays green. The ledger reading of
2026-09-09 did not cover that item, so this document does not state whether it
is closed.

### The Ansible migration

The Ansible migration is not one of the eight carriers. It is
`livespec-sab5gn.4`, a cross-cutting correction the maintainer directed on
2026-09-09 after judging the fleet's home-grown installer and converge shell to
be a reinvention of configuration management, at a measured cost of roughly three
to five times per change. It is recorded here because it is the largest single
piece of work the plan completed, and because this document is the second half of
that same work-item.

It merged in five pull requests across three repositories:

- **Phase 0, sizing the estate** — this repository (livespec), **pull request
  2702**, which inventoried and classified 349 committed artifacts across the
  three provisioning trees and decided both where the Ansible tree lives and how
  the tool resolves.
- **Phases 1, 2 and 3, the skeleton and the roles** — the livespec-dev-tooling
  repository, **pull requests 2077, 2084 and 2098**. Phase 1 established the
  tree at `ansible/` in that repository with a legacy-only inventory, wired
  `ansible-lint` into that repository's `just check`, and proved itself on one
  real change, the `gates_kubeconfig` role above. Phases 2 and 3 converted the
  host-record repositories' services and then the harder continuous-integration
  host glue.
- **Phase 4, retiring the replaced shell** — the fabro-hosts repository, **pull
  request 17**.

---

## WHAT IS LEFT

**The track is halted.** The maintainer halted this plan on 2026-09-09 and is
opening a separate plan, `mechanically-enforce-factory-usage`. Everything listed
below is therefore *open work that is not being driven*, not *work in flight*.
This document deliberately says nothing further about that separate plan.

**R0 — nothing is left.** The property is ratified in both repositories and
needs no further work under this plan.

**R1 — one item is left.** `livespec-ifwnqj.4` is open in the backlog at priority
P3: `build-recovery-usb.sh`, in this repository (livespec) at
`plan/archive/poweredge-raid-array-maintenance/research/build-recovery-usb.sh`,
predates the two boot fixes and therefore no longer reproduces the Recovery USB
stick that was actually proven. Under `R0`'s ratified property, a committed
artifact that does not reproduce the proven one is a defect rather than an
accepted gap, so this remains genuinely open rather than merely tidy-up.

**R2 — nothing is left.** The hotfix is relocated and the work-item is closed.

**R3 — nothing is left within the carrier's own scope.** `gmktec-xubuntu` is a
joined, `Ready`, tainted agent, which is exactly what `R3` required. The taint
that keeps continuous-integration runner pods off it is `R3`'s deliberate output,
not an unfinished piece of it; removing it is `R5`'s work.

**R4 — one slice is left, and one merged slice has never been converged.** These
are two separate problems and both must be resolved before a delegated gate can
run.

The first is **the blocking fact**, verified live on 2026-09-09: `S4`'s converge
has **never run** on `poweredge-xubuntu`, so the read-only in-cluster git daemon
is not up, even though its code merged in the livespec-dev-tooling repository's
pull request 2094 and the work-item is closed. The surrounding state is healthy —
both cluster nodes are `Ready`, and the VPS credential answers `kubectl auth
can-i create jobs -n gates` with `yes` over the tailnet — but the `gates`
namespace is **empty**. This is the exact component at which the 2026-09-08
end-to-end exercise failed closed, with a real gate Job admitted by Kueue and
scheduled onto `gmktec-xubuntu`. Closing a work-item against merged code while
that code has never been converged onto the host is the same failure mode this
plan already hit once and recorded, and it is what the Ansible migration's
`--check --diff` drift report exists to surface.

The second is **`S7`**, `livespec-dev-tooling-2u2c`, open at status
`pending-approval` and the only remaining slice of `R4`. Its code does not
exist: no file in the livespec-dev-tooling repository matches `gate-remote`, and
`check-pre-push` in that repository has no delegation fall-through. `S7` is
what actually connects a developer's `git push` to the cluster, so until it is
written, every gate still runs on the pushing host and the problem that opened
the plan is unrelieved.

Two smaller items ride on `S7` and should be settled when it is written. The
first is recorded in
`plan/k3s-on-gmktec-for-vps-usage/research/005-ansible-migration-estate-inventory-2026-09-09.md`
§8 in this repository (livespec): the gates credential is installed root-owned at
mode `0600`, faithfully reproducing the shell installer it replaced, but the
`gate-remote` client is intended to run as the maintainer's ordinary account,
which cannot read that file. The resolution — run the client under `sudo` through
a wrapper, or give the file a group and mode `0640` — belongs to `S7`'s design.
The second, from
`plan/k3s-on-gmktec-for-vps-usage/research/003-r4-delegation-primitive-design-and-slices-2026-09-07.md`
§G in the same repository, is that `check-pre-push` is per-repository rather
than shared, so `S7` must be a shared module invoked from each repository's own
recipe and rolled out per repository, and it must carry an opt-in switch so a
repository or a single push can run its gate locally — otherwise the cluster
becomes a single point of failure for every push in the fleet.

Finally, `S8`, `livespec-sab5gn.1` in this repository (livespec), sits at status
`acceptance` rather than closed. It is discharged in substance by the applied
Ansible role, so what is left on it is the acceptance step itself.

**R5 — everything is left, and nothing was ever filed.** No work-item exists for
this carrier at all, which means the fleet's only remaining upward lever for
continuous-integration throughput has no tracking record. What it requires is
unchanged from THE ORIGINAL GOALS above: the per-node package warm seed on
`gmktec-xubuntu`, that node's own churn-slot capacity derivation, a
`gmktec-xubuntu-k3s` scale set with the per-member addressing and proving job the
ratified clauses require, the two-node Kueue quota re-derivation, and then the
untaint. Filing it is itself part of what is left.

**R6 — everything is left, and nothing was ever filed.** No work-item exists for
the embedded-etcd move, its tmpfs maintenance set, or the monitoring rewrite that
follows it. This carrier was deliberately ordered last, and
`plan/k3s-on-gmktec-for-vps-usage/research/001-re-measurement-corrections-and-challenged-slice-order-2026-09-06.md`
§5 in this repository (livespec) attached a measurement rule to that ordering:
any `Slow SQL` line observed in the next fleet-wide backlog at the current
admission capacity moves `R6` ahead of `R5`. Nobody is currently watching for
that signal, so the rule is recorded but unarmed.

**R7 — everything that remains of it is carried by `R5` and `R6`.** No work-item
exists and none was intended, since the carrier is a discipline rather than a
deliverable. Because it binds monitoring to whichever change alters topology, and
because both remaining topology-changing carriers (`R5`'s untaint and `R6`'s
datastore replacement) are unstarted and unfiled, `R7`'s remaining obligation is
unstarted with them. Two named monitoring questions are still unresolved and
would land under it: the pod-side telemetry defect filed in the
livespec-dev-tooling repository as `livespec-dev-tooling-sdu2`, whose status this
document does not claim; and where the Honeycomb triggers and boards live as
code, which
`plan/k3s-on-gmktec-for-vps-usage/research/002-goal-zero-gitops-from-bare-metal-and-the-record-map-2026-09-06.md`
in this repository (livespec) ruled belongs to the otel-collector repository but
which has been filed nowhere.

### Left over from the Ansible migration

Two items recorded during the migration are open and are not attributable to any
carrier. Both come from
`plan/k3s-on-gmktec-for-vps-usage/research/005-ansible-migration-estate-inventory-2026-09-09.md`
§2 in this repository (livespec), and this document does not claim whether the
merged phases resolved them.

The first is twelve artifacts across the provisioning trees classified as already
dead — four of them a superseded by-hand phase that the converge inlines rather
than invokes — which were to be deleted with their pre-deletion commit hashes
cited.

The second is nineteen manual steps that survive any migration: eleven in the
vps-info repository and eight in the fabro-hosts repository, covering things such
as building a binary, minting a server token file, loading a private key into a
vault, and adding a mapping in another repository. Ansible does not absorb these.
They were to be recorded as inventory-level preconditions with a preflight
assertion in each role, or the first apply against a rebuilt host fails partway
through rather than at the start.

### Deferrals that remain deferred

For completeness, the explicit deferrals recorded in
`plan/k3s-on-gmktec-for-vps-usage/research/002-goal-zero-gitops-from-bare-metal-and-the-record-map-2026-09-06.md`
§"Explicit deferrals" in this repository (livespec) are unchanged and are not
part of what is left above: turning the llama.cpp install on `gmktec-xubuntu`
into a scripted installer, which research/002 assigns to the repository owning
the local large-language-model service rather than to any repository this plan
touches; moving the Fabro factory's Docker sandboxes onto the same Job
primitive; the orchestrator janitor's host-local `just check`; reducing the
number of agent sessions on the VPS; the discriminating measurement between
scheduling latency and datastore lock serialization; and `hp-xubuntu` or the Mac
mini as gate hosts.

---

## Read-first chain

A reader picking this plan up should read, in order: this document; then
`plan/k3s-on-gmktec-for-vps-usage/research/004-ansible-migration-direction-2026-09-09.md`
in this repository (livespec) for the directive that produced both halves of
`livespec-sab5gn.4`; then
`plan/k3s-on-gmktec-for-vps-usage/research/003-r4-delegation-primitive-design-and-slices-2026-09-07.md`
in the same repository for the design of the one carrier with open
implementation; then
`plan/k3s-on-gmktec-for-vps-usage/research/002-goal-zero-gitops-from-bare-metal-and-the-record-map-2026-09-06.md`
for goal zero and the record map naming which repository owns which layer; and
finally
`plan/k3s-on-gmktec-for-vps-usage/research/000-brief-from-vps-info-investigation-2026-09-06.md`
for the original measured problem on the VPS.
