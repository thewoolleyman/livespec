# Post-landing review closure

Date: 2026-09-10

Plan epic: `livespec-livyxu`

Status: authoritative amendment to notes 001, 003, 004, and 005. It closes the
remaining issues found by the fresh review of landed commit `0da6059d`. Where
older notes conflict, this note wins.

## Disposition

Fresh Sol and Fable review seats both returned conditional go for discovery and
design work, no new P0, and no permission to activate G-1 or retain unique data.
The following contracts close their shared P1 findings before implementation
slicing proceeds beyond Phase 0/1.

## Exact G-1 principals and verbs

G-1 defines at least these six principals; none may be collapsed merely to
reduce manifests:

| Principal | May do | Must not do |
|---|---|---|
| constrained run requester | create/get/watch/cancel a schema-validated custom run request; read its projected status, redacted logs, and artifacts | create/patch/exec Pods or Jobs; choose service account, command, image, Secret, PVC, host path, node, or security context |
| image builder | protected GitHub Actions workflow builds and pushes only the declared GHCR package | deploy workloads or read runtime credentials |
| ephemeral-test workload | execute one rendered test Job with only its fixture identity and scratch | mount dogfood PVC, service-account token unless required, host path, runtime socket, or production credential |
| dogfood workload | run the reviewed StatefulSet and mount the one live workspace PVC | launch VMs, mount other claims, mutate cluster objects, or expose its PVC to tests |
| VM client | submit bounded VM requests and read their result | supply arbitrary QEMU arguments, paths, image, network, command, or live workspace |
| controller/reconciler | render reviewed templates from immutable digests and own lifecycle/cleanup | accept unvalidated fields or act outside the dedicated namespaces/allowlists |

All workload service accounts set `automountServiceAccountToken: false` unless
a named API call requires a token. The constrained run requester has no
`pods/exec`; debugging happens through redacted logs, ephemeral artifacts, or a
separately authorized break-glass path with a ledger receipt and expiry.

The exact namespace/resource/verb matrix is schema-validated and negative
tested. “Own test pods” is never an RBAC selector.

## G-1a and G-1b ownership

`poweredge-xubuntu-info` is the host/cluster owner. Before G-1a begins it must
file and record a concrete work-item ID in `config/external-seams.yml`, along
with the accountable repository maintainer and the paths that reconstruct the
cluster.

G-1a is a human/cluster-admin-owned, seven-day maximum feasibility spike in a
temporary isolated namespace. Its temporary credential, cluster objects,
host files, devices, ports, and processes are inventoried before use and
proved absent at teardown. Its signed decision record selects the
non-privileged runner only if every criterion in note 004 passes; otherwise it
selects the narrow host broker. An inconclusive result defaults to the broker
and blocks G-1b rather than granting broader pod privilege.

G-1b installs the selected production-shaped substrate through
`poweredge-xubuntu-info`, runs admission/escape/resource/network/reboot
negatives, and issues the constrained requester credential. Autonomous G0-G3
begins only after G-1b.

## Closed reboot-reconstruction DAG

The empty-k3s-store test starts from only host GitOps source and separately
recoverable bootstrap credentials. The ordered DAG includes:

1. host storage, mounts, firewall/network namespace, KVM device or broker;
2. namespace and CustomResourceDefinitions;
3. controller/operator identities and recoverable credentials;
4. controller deployments, admission/image-policy webhooks, certificates,
   Kueue, and readiness checks;
5. Restricted Pod Security labels, default-deny policies, quotas, LimitRanges,
   priority classes, ClusterQueue, and admission templates;
6. static PV/PVC recovery, ConfigMaps/Secrets, workload accounts/RBAC;
7. dogfood/canary workloads and external requester credential refresh.

Admission is fail-closed from bootstrap start: no workload request is accepted
until every policy/controller/certificate readiness probe passes. Recovery
tests interrupt reconstruction after each layer and prove there is no policy
gap or workload launch with partially restored controls.

## Network containment

Every cockpit pod begins with default-deny ingress and egress. Allowlisted
egress is destination- and port-specific through a logged proxy where practical.
Before exceptions, deny:

- production tailnet `100.64.0.0/10` and tailnet IPv6;
- LAN/RFC1918 and other node/host networks;
- cloud metadata/link-local endpoints, Kubernetes API unless explicitly needed,
  node services, and unrelated cluster namespaces/services;
- public ingress and any host port.

DNS, GHCR/GitHub, pinned package sources, agent test APIs, the Honeycomb test
environment, and the separate test-tailnet control plane receive only the
minimum explicit exception. Negative probes run from pods and guests.

The host broker launches QEMU in a dedicated network namespace/cgroup with
host-owned nftables rules enforcing the same deny/allow set; Kubernetes
NetworkPolicy is not credited for broker isolation. User-mode networking must
not inherit unrestricted PowerEdge reachability. Cleanup removes namespaces,
rules, forwards, and processes and a reboot-tested scavenger rejects stale
state before accepting a new run.

## Arithmetically closed resource policy

Each namespace has its own ResourceQuota/LimitRange, and one Kueue
ClusterQueue plus host cgroup caps the aggregate across ephemeral tests,
dogfood, and broker-launched guests at the envelope in note 005. Guest vCPU,
guest RAM, QEMU overhead, overlays, and broker scratch all count. No code path
can launch work outside the charged cgroup/ClusterQueue.

Before G-1b, a signed SLO decision records at least seven days of baseline or
100 representative CI jobs, whichever is longer; the comparison window and
minimum sample count; workload-attribution tags; p95 queue-delay calculation;
and abort behavior. Cockpit work is suspended on any attributable CI failure
or more than 10% p95 regression. The decision may adjust the numeric threshold
only through a reviewed plan/config change.

## Image, guest-image, and package trust

`config/external-seams.yml` pins:

- GHCR repository and digest;
- Sigstore/cosign trust root, certificate issuer and subject/workflow identity;
- SLSA provenance predicate, protected builder workflow path/ref, and source
  repository;
- required SBOM format and attestation predicate;
- vulnerability scanner database timestamp, fail threshold (unwaived Critical
  or High findings fail), maximum waiver age, approver, and expiry;
- Ubuntu cloud-image signing/checksum authority and verified immutable digest;
- apt repository snapshots or a tested archival/mirror fallback so a future
  rebuild does not depend on a vanished moving package version.

Admission verifies image digest, signature identity, provenance, SBOM, and
vulnerability attestations—not merely that some signature exists. Waivers are
typed, expiring evidence and cannot waive an absent attestation.

## Enforceable storage exclusion and backup

Only the dogfood StatefulSet identity/template may mount the live workspace PVC
writable. Admission denies that claim to every other workload. The VM broker's
path allowlist cannot address the live mount: it accepts only separately
provisioned fixture disks or quiesced, read-only-source reflinks whose writable
clone has a distinct path and identifier. This is the hard fence; Kubernetes
Lease coordination is supplementary only.

Before G2 admits unique work, the backup must be off PowerEdge and outside both
NVMe failure domains. `state-paths.yml` records owner, quiesce/application
consistency method, client-side encryption and independently escrowed recovery
key, retention, 12-hour schedule/monitor, restore source, and four-hour RTO.
Tests cover missing, stale, corrupt, and unreachable backups and perform a
fresh-LV restore after empty-store reconstruction.

## Measured AWS-wrapper authority

The prior “source deleted/rehome it” claim was stale and is withdrawn. Before
implementation, remeasure the live source/install reconciliation. If current
host authority is confirmed, `homelab/provision/with-homelab-aws.sh` remains
canonical, its exact Git commit is the external-seam pin, and the five-minute
reconciler remains deployment authority. Never edit `/usr/local/bin` or create
a duplicate cockpit-owned canonical wrapper.

Preserve the intended dual substrate on the VPS: the AWS wrapper/Parameter
Store for migrated consumers and `with-homelab-env.sh` for its four named live
consumers. Any later consumer migration needs separate authorization and
revoke-last evidence.

## Dedicated non-production identities

G0/G1 use fakes exclusively. G2/G3 may use only identities inventoried in
`config/test-identities.yml`, each owned by the corresponding external seam:

- fixture GitHub repositories/package with no production repository access;
- isolated Honeycomb test environment/dataset and test notification recipient;
- dedicated 1Password test account/vault/service account containing only
  planted synthetic secrets;
- least-cost/scoped Claude, Codex, and Pi test identities with budget ceilings
  and revocation receipts;
- a contract-fake Tailscale state machine or separate non-production tailnet.

The Tailscale fake models login, Running/NeedsLogin, IP changes, empty tags,
SSH preference, expiry, logout, duplicate name, and health transitions; a
conformance suite compares supported state transitions with an isolated real
test node. If a dedicated real identity cannot be provisioned, its real login
or unlock criterion moves visibly to G4/G5 and cannot be reported green at G3.
No production credential is copied into the cluster.

## Complete execution accounting

The launcher writes a durable start record with a generated correlation ID
before exec and a completion record afterward. A root-owned Linux Audit
`execve` rule (or an equivalently durable kernel execution-accounting mechanism
ratified in the capability matrix) records every execution of the resolved
Claude/Codex/Pi binaries, including short-lived direct calls. Container lanes
use runtime/audit events with the same semantics.

Reconciliation joins launcher records to execution records by host/container,
UID, executable digest, PID/start time, and bounded time window. Every execution
must have exactly one launcher lifecycle or be an explicit bypass failure;
warning-only bypass is not acceptance. Audit loss, queue overflow, clock drift,
or exporter loss fails the coverage gate. Audit configuration itself is
reboot-tested and tamper-evident.

## Evidence store and deletion semantics

Add the evidence store as an explicit external seam before G-1b. It names the
service/repository owner, authenticated signer, WORM/versioning mechanism,
encryption, ACL administrator/readers, per-class retention, legal/operational
hold, replication/failure domain, and recovery test. Acceptance manifests must
be signed; an unauthenticated checksum alone is insufficient.

Append-only applies to the signed manifest and audit trail, not to leaked secret
payloads. Emergency purge quarantines and deletes the contaminated payload from
all replicas/caches, rotates the secret, and appends a signed tombstone carrying
only safe metadata and the deletion/rotation receipts. Normal expiry similarly
retains a signed non-sensitive tombstone when required while deleting the
artifact body.

## Reproducible quantitative gates

`schemas/dogfood-event.schema.json` and committed queries define the counters.
An eligible real task is a unique launcher correlation ID that performs a
non-canary repository operation, reaches a terminal success/failure state, has
complete execution/telemetry/evidence accounting, and is not a retry of the
same logical task. Both successes and failures count toward exposure volume but
the report shows them separately; unresolved attributable failures block
promotion.

A day is UTC `00:00:00` through `23:59:59`. “Consecutive” resets on an
unexplained telemetry/evidence gap over 15 minutes, failed required canary,
unrecovered P0/P1, or breach of CI/resource/security SLO. Planned maintenance is
recorded and extends rather than silently satisfies the window. One canonical
versioned query/report computes task uniqueness, per-agent counts, days,
replacements/reboots/restores, telemetry gaps, and reset causes from signed
events. Gate receipts include the query commit/hash and input window.

## Atomic Tailscale name allocation

`tailscale-admin` owns the production `agent-cockpit-{n}` registry. The unique
key is the integer instance number and derived hostname. Allocation is a
branch-protected Git transaction/PR whose CI rejects duplicates and whose merge
commit is the reservation receipt before enrollment. Each row records intended
host/provider, allocator, state, creation/expiry, enrolled node ID receipt, and
release tombstone. Stale un-enrolled reservations expire only through a
reviewed transition; enrolled names never auto-expire. Release requires node
removal proof and retains the tombstone so a replacement cannot be confused
with the old identity. Rollback restores the prior registry commit but never a
retired node key.

## Remaining measured desktop details

The measured-current-surface ledger explicitly captures Chrome's `set +e`
respawn loop, the prohibition on shell-launching the live profile, both desktop
overrides, and the single wrapper/main-process invariant. Tests include a dry
run or CDP-only path against an active profile without starting a second Chrome
process. These fixtures supplement, not replace, real G3/G4 input/render/crash
tests.

## Extended G4 provider contract

The provider seam also names IaC/API owner, scoped credential rotation, quota
and cost ceiling, availability-zone and disk-colocation rules, snapshot
consistency, rate-limit/retry behavior, and resource leak/cost detection. No
destructive dogfood begins until provider console/rescue, disk attachment,
snapshot/restore, and external scanning have positive receipts.

## Implementation admission

Phase 0/1 may now create repository scaffolding, schemas, inventories,
measurement probes, test fakes, and the G-1a design work item. Applying G-1b,
rotating credentials, admitting unique state, provisioning a VPS, migrating
work, or deprecating the VPS remains prohibited until the corresponding
schema/config rows and prerequisite receipts exist and pass.
