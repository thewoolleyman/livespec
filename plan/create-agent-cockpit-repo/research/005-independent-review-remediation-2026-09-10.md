# Independent-review remediation and execution contract

Date: 2026-09-10

Plan epic: `livespec-livyxu`

Status: authoritative amendment to research notes 001, 003, and 004. Where
those notes conflict with this amendment, this note wins.

## Review disposition

The second independent Sol and Fable review passes agreed with the standalone
repository and container-plus-machine test strategy, but rejected the plan as
execution-ready. Their legitimate findings are adopted below. The amendments
turn implied prerequisites into gates, remove unsafe Kubernetes authority,
make parity mechanically traceable, and give migration/recovery quantitative
exit criteria.

QEMU/KVM remains the preferred guest VMM. The Kubernetes integration is no
longer assumed to be a direct QEMU Job: a time-boxed feasibility spike must
compare that design with a narrow host-side VM broker before implementation
selects the control plane.

## G-1: one-time enablement before autonomous work

G0-G3 cannot be autonomous until a cluster administrator establishes a bounded
substrate. Add gate **G-1** with the PowerEdge/k3s configuration repository as
owner and immutable receipts for:

- namespace labels enforcing the selected Pod Security level;
- four separate identities: read-only external driver, image builder,
  long-running dogfood workload, and VM-runner/broker client;
- admission policy that restricts each identity to reviewed workload templates,
  service accounts, images, volumes, resources, security contexts, and nodes;
- ResourceQuota, LimitRange, NetworkPolicy, PriorityClass/Kueue admission, and
  a one-VM concurrency limit;
- the labeled PowerEdge mount, retained static PV/PVC, mount-fail-closed check,
  backup owner, and restore receipt;
- the exact `/dev/kvm` exposure or broker API, including QEMU UID/GID,
  `kvm`-group access, cgroup limits, scratch storage, networking, port
  allocation, shutdown, timeout, and orphan cleanup;
- protected GHCR build/push identity and a digest-only deploy policy;
- namespace-scoped kubeconfigs/wrappers with rotation and revocation tests;
- fake test services and, if ever needed, a separate non-production tailnet.

The external driver must not have arbitrary Pod or Job creation. Namespace
RBAC is insufficient because a principal that can author arbitrary pods can
indirectly select service accounts, secrets, PVCs, images, and host-adjacent
features. The driver may submit a commit/run request to an admission-locked
controller or narrow broker and read only its own status, logs, and artifacts.
Negative tests must prove that it cannot select another service account, mount
another Secret/PVC/hostPath, change an image or command outside the reviewed
template, request privileged mode/capabilities, target another node/namespace,
or create an arbitrary pod.

G-1 is allowed to require one consolidated administrator ceremony. After its
receipts pass, agents can drive G0-G3 without incremental maintainer work.

## PowerEdge reboot reconstruction is a hard invariant

The live k3s datastore is reconstructed after host reboot rather than treated
as durable authority. Every harness object must therefore be part of the
PowerEdge boot-reconstruction DAG, in dependency order:

1. host LV/filesystem/mount and fail-closed directory guard;
2. node labels, namespace, Pod Security labels, policies, quotas, limits,
   priority/admission objects, and KVM device/broker substrate;
3. static PV, PVC binding/claimRef recovery, service accounts, RBAC, and
   admission-locked templates;
4. dogfood workload, Services, canaries, and monitoring;
5. refreshed external-driver credentials.

Acceptance must reboot PowerEdge from a deliberately empty/reconstructed k3s
datastore, then prove the whole DAG, PVC rebinding, workload readiness, KVM
lane, and external driver. A successful one-time `kubectl apply` is not proof.

## Resource and scheduling envelope

Capacity observations are snapshots, not entitlements. The initial envelope is:

- at most one KVM guest; 8 vCPU and 24 GiB guest RAM maximum;
- dogfood request 1 CPU/4 GiB and limit 8 CPU/24 GiB;
- all ephemeral integration work combined: request 2 CPU/4 GiB, limit 12
  CPU/24 GiB;
- namespace cap: 20 CPU, 56 GiB RAM, 350 GiB persistent storage, 100 GiB
  ephemeral/scratch storage, and bounded object counts;
- VM/job active deadline 90 minutes, one automatic retry, explicit cleanup;
- low-priority/Kueue admission behind production CI, with preemption or
  suspension rather than starving ARC runners;
- QEMU overlays and package/build scratch on the dedicated NVMe work area, not
  kubelet's ordinary ephemeral root.

Tune only from measured telemetry and committed review. G-1 and G3 must capture
CPU, memory, disk latency/capacity, inode, and I/O-pressure baselines. During a
cockpit run, existing CI queue delay and success rate may not regress beyond a
ratified threshold; the initial proposed threshold is less than 10% p95 queue
delay regression and no induced CI failures.

## Image supply chain

The existing local registry path is a pull-through cache and is not a push
destination. Build with the existing protected ARC/GitHub Actions path and
publish to GHCR. Every image must have:

- a digest-pinned official Ubuntu base;
- locked apt repository/key and agent/tool dependency policy;
- an immutable GHCR digest used by every deploy manifest (`@sha256`, never a
  mutable commit tag as authority);
- SBOM, provenance, vulnerability results, and signature/attestation;
- admission verification of the expected repository, digest, and signer.

## QEMU control-plane feasibility spike

Time-box the spike to a small boot/cloud-init/reboot/destroy prototype and
compare:

1. a non-privileged Kubernetes workload using a measured KVM device mechanism;
2. a minimal root-owned host service that exposes a narrow allowlisted API for
   create/status/log/destroy of commit-scoped QEMU guests.

Select the direct Job only if it needs no privileged pod, arbitrary hostPath,
broad workload-authoring identity, runtime socket, uncontrolled TAP/network
capability, or lifecycle state that survives cleanup. Otherwise select the
host broker and keep its API incapable of arbitrary QEMU arguments, paths,
images, networks, or commands. Both options require an immutable read-only
base image, per-run overlay, bounded NVMe scratch, unprivileged QEMU UID,
serial-console capture, unique forward allocation, deadline, graceful
shutdown, kill fallback, and a reboot-tested orphan scavenger.

Firecracker remains deferred: its density/startup advantages do not offset
custom kernel/rootfs and networking work for a single commodity-Ubuntu parity
guest. KubeVirt remains the scale-up option if VM lifecycle becomes routine.

## Tailscale isolation and network evidence

No disposable container or VM may join the production tailnet as an ordinary
untagged member. The production tailnet currently has broad member-to-member
reachability, so a “test name” is not isolation.

- G0-G3 use a contract fake by default.
- If real protocol behavior cannot be faked, use a separately administered
  non-production tailnet with disposable credentials and no route to the
  production tailnet or LAN.
- Actual untagged production-tailnet enrollment, key-expiry disablement,
  Tailscale SSH, duplicate-name rejection, and provider public-interface scans
  are exclusive to G4/G5.
- Tests distinguish a healthy listener from `BackendState: Running`, current
  Tailscale IP, empty advertised tags, and `RunSSH: true`; a continuous watcher
  must fail closed and restart/rebind on logout or IP change.

User-mode QEMU networking can prove guest-local policy but cannot prove that a
VPS provider public address is closed. That assertion is recorded only from an
external G4/G5 probe. For x11vnc, the invariant is externally unreachable from
public and non-tailnet paths; a wildcard IPv6 socket is a failure only if the
chosen implementation contract forbids it or the firewall negative test fails.

## Durable-state manifest, fencing, backup, and recovery

Create `config/state-paths.yml`. Every retained path must declare exact path,
owner/mode, state class, sensitivity, persistence location, migration method,
backup owner, RPO/RTO, restore procedure, destruction rule, and whether it may
be shared with a guest. Whole-home persistence is forbidden.

Minimum durable classes include repository/worktree state, Atuin history,
selected agent handoffs/transcripts, and user-approved browser state. Auth,
machine identities, caches, tmux sockets, and running processes are explicitly
re-minted or ephemeral.

The PowerEdge static `Retain` PV is neither backup nor high availability. It
must be independently backed up before unique work is allowed, with an initial
RPO of 12 hours and RTO of 4 hours, plus a restore-to-fresh-LV rehearsal. The
mount unit and workload init check must fail closed if the labeled filesystem
is absent, preventing writes into the underlying mount directory. RWO is not
fencing on one node: policy and leases must prevent simultaneous writable
attachment by the StatefulSet and a VM/test pod.

The VM lane never mounts the live dogfood workspace writable. It uses a
quiesced XFS reflink/snapshot fixture or a separate test disk. Root-destruction
tests plant one sentinel on the data disk and one on root, then require the data
sentinel to survive and the root sentinel to disappear.

Encryption and unattended reboot behavior must be measured before choosing a
design. Record key custody, recovery key escrow, console/rescue dependency,
automatic unlock boundary, and replacement-host procedure. A host-bound seal
alone is not a portable disk-recovery mechanism.

## Requirement and measured-surface ledgers

Create schema-validated `config/requirements-traceability.yml` and
`config/measured-current-surface.yml` before implementation children are
declared complete.

Every clause from the verbatim seed note gets a stable requirement ID. Each
traceability row records requirement text/source, implementation owner,
disposition (`implement`, `preserve`, `exclude`, or `defer`), rationale,
work-item ID, applicable capability gates, acceptance command, and immutable
evidence URI/hash. There may be no unclassified seed clause.

The measured-surface ledger inventories every current service, unit/timer,
package/tool/version, tmux and shell behavior, agent config key, plugin, hook,
MCP, wrapper, repository/destination/origin, desktop process, listener, state
path, credential consumer, and observability path. Each row carries source
repo/path, current owner, new owner/disposition, reason, test, and deprecation
commit. “Anything else” is closed by a fresh measured inventory, not prose.

Re-snapshot the workspace at migration freeze. Counts in prior notes are
historical observations, not constants. Required repos are only those whose
origins are reachable and whose requirement row says `required: true`;
GitLab-blocked repos remain explicit pending/optional rows and cannot both be
required and accepted while unreachable.

## Repository fidelity and cutover transaction

For every migrating Git directory record and restore:

- dirty, staged, untracked, and ignored-but-required files;
- local branches, unpushed commits, tags, reflogs where required, and stashes;
- linked worktrees and absolute `.git` pointer files;
- submodules, Git LFS objects, alternates, shallow/sparse state;
- all remotes, normalized fetch URLs, push URLs, and upstream tracking.

Plain clone parity is insufficient. Use bundles/archives only with encryption,
hashes, restore tests, and an explicit expiry. At cutover establish a
single-writer epoch: inventory and hash source, stop creation of new VPS cockpit
work, transfer, hash destination, compare, record exceptions, then open the new
cockpit. Concurrent writable use of both copies is prohibited.

## Credential recovery is additive

The exposed 1Password service-account credential is rotated as a staged
consumer migration, never “revoke first”:

1. enumerate every consumer and positive/negative health probe;
2. mint a replacement credential without revoking the old one;
3. explicitly probe required `op` beta capabilities and pin the wrapper to an
   exact reviewed commit until it publishes a release;
4. seal separately on every host using explicit `systemd-creds
   --with-key=host`; never copy `/var/lib/systemd/credential.secret` or a sealed
   blob;
5. test every migrated consumer, rollback path, restart, and reboot;
6. revoke the old credential only after all receipts pass.

Do not remove or rewrite the current VPS `with-homelab-env.sh`. It remains
load-bearing for `vps-restic-backup`, `cloudflare-mcp`, `honeycomb-mcp`, and
`honeycomb-trigger-recipients-check`. Those bespoke/server consumers stay on
the VPS until their own independently authorized migrations complete.

## Complete agent-activity observability

“All agent activity” requires a canonical cockpit launcher as the supported
choke point. Tmux bindings, shell entrypoints, factory/NTM/Fabro clients, and
automation must invoke Claude, Codex, and Pi through it. Direct binary execution
is either blocked/warned by policy or counted as an observable bypass.

Define the denominator as launcher invocations plus discovered direct-agent
processes. Required coverage includes interactive sessions, non-interactive
`exec`, factory/NTM/Fabro-launched work, MCP/tool subprocesses where observable,
failures before provider initialization, restarts, and exporter outage. A gate
passes only when every synthetic invocation has one correlated lifecycle event
and no unexplained discovered invocation lacks one. Native provider spans may
enrich but do not replace the wrapper lifecycle event.

The privacy contract covers traces, local logs, JUnit/JSON, screenshots,
cloud-init, serial consoles, and hyperlinks—not just Honeycomb event bodies.
Default content capture is off. Declare allowlisted metadata, redaction,
cardinality budgets, retention, access, deletion, and artifact expiry. Plant
unique fake secrets in prompts, environment, tool arguments/results, repo
URLs, cloud-init, desktop fields, and failure messages; require their absence
from every exported/local artifact while positive canaries remain visible.
At least one alert test must verify delivered notification, not only trigger
configuration.

## External seam and ownership contract

Create `config/external-seams.yml` for `1password-env-wrapper`,
`otel-collector`, `tailscale-admin`, PowerEdge/k3s reconstruction, GHCR/ARC,
and every agent driver. Each row names owning repository/team, exact pin/API,
compatibility range, update policy, deployment order, health evidence,
rollback commit, and deprecation dependency. Cross-repository changes land in
dependency order and rollback in reverse order; no copied canonical file may
remain after migration.

## Stronger functional acceptance

In addition to structural checks:

- Ansible idempotence compares actual package versions, files/hashes, units,
  listeners, settings, and probes; `changed_when: false` cannot manufacture a
  pass.
- Tmux parity uses a behavioral diff: prefix/key tables, copy/search, mouse,
  terminal features, status, new-window/pane working directories, session
  attach/detach/destroy, and restart behavior.
- Ctrl-R is exercised in Bash as requested and in zsh if zsh is retained, with
  a defined fallback when Atuin is unavailable.
- The per-agent matrix proves install/version, login state, settings merge,
  required plugin/hook/MCP calls, canonical launcher, telemetry, failure, and
  restart for Claude, Codex, and Pi.
- Remote VNC acceptance drives keyboard and pointer, captures a screenshot,
  renders Chrome, proves loopback-only CDP, tests Chrome crash/respawn and a
  single intended profile, opens/unlocks 1Password Desktop through the shared
  D-Bus session, and verifies its bounded two-hour/cgroup behavior.
- Resolve the existing desktop-documentation discrepancy from executable
  evidence before copying anything: the measured current launcher uses XFCE,
  while any stale Openbox prose is corrected or explicitly rejected. The
  requirements ledger names the selected window manager and source receipt.
- Chrome keeps its sandbox. Any container-only incompatibility is a failed
  capability or documented KVM-only check, never justification for
  `--no-sandbox`.
- Capability-specific filesystem hardening such as immutable attributes is
  required only in KVM/VPS lanes and must remain visibly not-applicable—not
  silently green—in restricted containers.
- Tailscale naming uses an allocator/registry and rejects duplicate instance
  numbers/names before enrollment.

The failure-injection matrix includes namespace deletion, node reboot, PVC/PV
object loss and claimRef recovery, missing/mis-mounted/full data disk, corrupt
or unavailable backup, exporter outage, Tailscale logout/IP change, Chrome and
desktop-process crashes, QEMU timeout/orphan, provider API failure, and absent
required repository origin. Each case declares fail-closed behavior, alert,
cleanup, recovery command, and immutable receipt.

## Promotion, dogfood, and deprecation thresholds

The revised gate ladder is G-1 (substrate), G0 (CI), G1 (ephemeral container),
G2 (long-running dogfood), G3 (KVM guest), G4 (first external VPS), and G5
(second instance).

Before G4, the cluster must accumulate at least 7 consecutive days, 30 real
non-production agent tasks, at least 5 tasks per agent, 3 dogfood Pod
replacements, 2 fresh VM root rebuilds, one PowerEdge reboot with empty-store
reconstruction, one restored NVMe backup, and no unresolved P0/P1 defect.

Before old-VPS cockpit deprecation, `agent-cockpit-0` must accumulate at least
14 consecutive days, 50 real tasks, at least 10 per agent, 2 guest/host reboots,
one compute-instance replacement retaining only declared data, a successful
external public-interface scan, a delivered telemetry alert, and zero new
cockpit sessions on the VPS during a 14-day rollback window. `agent-cockpit-1`
must independently pass fresh bootstrap/reboot/remote acceptance. Rollback
commits and the state recovery drill must remain valid throughout.

G4 cannot begin without a written provider contract: provider/image, immutable
image identifier, attached-disk API and stable identity, encryption/unlock and
recovery, firewall and IPv4/IPv6 defaults, serial/console/rescue access,
snapshots/backups, cloud-init retention/redaction, destroy semantics, and an
external scanner. The first destructive rebuild follows that contract.

Only after all thresholds pass may deprecation remove duplicated cockpit
material. It must preserve the four live `with-homelab-env.sh` consumers and
every excluded VPS service. Removal is a reviewed multi-repository transaction,
with zero-process/session evidence and reversible commits.

## Evidence integrity

Every gate publishes a signed or checksummed manifest containing source commit,
image digest, dependency pins, environment/capability, timestamps, test
results, artifact hashes/expiry, and Honeycomb trace/query references. Evidence
is append-only for the acceptance window. A mutable dashboard, tag, or “service
active” observation is supplementary and cannot be the sole receipt.
