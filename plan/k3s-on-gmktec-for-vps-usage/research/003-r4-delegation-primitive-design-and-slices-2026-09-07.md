# 003 — R4, the delegation primitive: the design corrected against the live tree, the recommended shape, and the slices (2026-09-07)

Written 2026-09-07 after R0 through R3 landed and the gmktec rehearsal
completed. This note takes research/000's proposed delegation primitive,
re-derives it against the tree and the hosts as they are TODAY, and proposes
the shape R4 should be built in. Research/000's goals and research/001's
measurements stand; what changes here is the mechanism, in seven places where
the world moved after the brief was written.

Nothing in this note is ratified. It is the draft the scope event records and
the maintainer may object to.

## What R4 is (settled, quoted, unchanged)

Research/002 §"The slice order, re-derived under goal 0", item 4:

> **The delegation primitive** — `tls-san` in `k3s-config/config.yaml` (and
> its header's "no externally reachable API server" premise amended); the
> `gates` ServiceAccount, RBAC, ClusterQueue, `WorkloadPriorityClass` and Job
> template as manifests the converge applies; the bare mirror on the RAID and
> the read-only in-cluster git daemon as converge artifacts; the
> `gate-remote` client in livespec-dev-tooling wired into `check-pre-push`'s
> fall-through only; node affinity preferring gmktec. The VPS-side steps
> (`kubectl`, the rendered kubeconfig) are the one permitted hand-installed
> surface, recorded in `vps-info`.

The purpose, from research/001 §5: this is the slice that relieves the VPS —
the problem that opened the plan — and it does so without touching poweredge's
CI capacity, because the gates land on the otherwise idle gmktec.

The constraint that outranks the mechanism, research/000 goal 1: *move WHERE
the gate runs, not WHAT it runs*. No subsetting, no weakening.

## What R0–R3 already discharged

Four things the brief listed as R4 work, or as R4 preconditions, are done:

1. **R0 is ratified**, livespec v221 and livespec-dev-tooling v058, so R4 may
   be filed as implementation. Research/002 §"slice order" item 1 gated every
   child on that ratification.
2. **The hostPath singletons are pinned.** `sccache-redis`, `crates-proxy`,
   `pypi-proxy` and the warm-cache CronJob all carry
   `nodeSelector: ci-runner.io/cache-tier-carrier: "true"` (PR #1903). The
   latent hazard research/001 §"Bottom line" item 5 named — a singleton
   restarting onto gmktec with an empty hostPath — is closed.
3. **gmktec is a pool node.** Built from bare metal by the one recipe, joined
   as an agent at `192.168.1.156`, `Ready`, tainted
   `node-role/ci=pending:NoSchedule`, admission capacity `C=0`, its three
   tiers live.
4. **The node-local runbook completes on an agent**, after the seven defects
   the rehearsal found and the four follow-ups that closed the chain.

## Seven corrections to research/000's design, measured 2026-09-07

### 1. Preemption is OFF by maintainer declaration; the gates queue cannot preempt

The brief says a `WorkloadPriorityClass` above the CI runners means *"a gate
is admitted immediately and preempts a queued runner rather than waiting
behind CI."*

Every ClusterQueue in the pool sets `preemption.reclaimWithinCohort: Never`,
`preemption.borrowWithinCohort.policy: Never` and
`preemption.withinClusterQueue: Never`, under a maintainer declaration
recorded in `kueue/DERIVATION.md` (2026-08-30): **never preempt a running job
to rebalance the cohort.** That declaration is not R4's to reverse.

The premise is recoverable without touching it, because the brief asked for
the wrong mechanism. A gate does not need to evict anything; it needs not to
QUEUE behind CI. That is what a dedicated quota gives. The recommendation
below gives `gates` its own resource on its own flavor, so it is admitted
against capacity no CI queue can consume, and preemption never arises.

`WorkloadPriorityClass` still earns its place: it orders gates among
themselves, so the interactive push in front of a human beats a batch gate.

### 2. There is no single sandbox image tag; it is per-repo and it moves

The brief names `ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-v1.49.0`
and research/001 §8 flagged it for verification. Measured: livespec's CI runs
`python-v1.56.2`, livespec-dev-tooling's runs `python-v1.58.2`. The tag lives
in each repository's own `.github/workflows/ci.yml` `container:` block and
moves with the fleet image pin.

So the gate Job template MUST take the image from the repository it is gating,
read at gate time from that repository's own workflow, not from a constant
baked into the template. A hardcoded tag would silently gate against a
different toolchain than CI uses — the same class of defect as gating a
subset.

### 3. `/var/lib/git` on poweredge belongs to the `git` package; do not reuse it

Research/001 §8 left its origin open, and §2 item 6 said not to assume it is
free. Settled: `dpkg -S /var/lib/git` reports `git: /var/lib/git`, from
`git 1:2.53.0-1ubuntu1`. It is a distribution-owned directory, which is why it
is empty and root-owned and dated before the pool existed.

The mirror therefore goes on a role-labelled tier, not there. The live tiers on
poweredge are `/var/cache/ci-runner` (`poweredge-ci--cache`),
`/var/cache/ci-runner/k3s-containerd` (`nvmea-ci--containerd`) and
`/var/cache/ci-runner/k3s-storage` (`nvmeb-ci--workvols`, xfs). The mirror is
durable, modest, and not a container store, so `ci-cache` is its tier.

### 4. Two paths in the brief do not exist

`ci-runner/k3s/k3s-config/` and the fair-share `ci-runner/k3s/kueue/` are both
under `phase2/`: `ci-runner/k3s/phase2/k3s-config/` and
`ci-runner/k3s/phase2/kueue/`. A separate `ci-runner/k3s/kueue/resources.yaml`
exists but is only the phase-1 proof set. Every R4 slice must name the
`phase2/` paths.

### 5. A gate Job must tolerate gmktec's taint; no note said so

R3 taints gmktec `node-role/ci=pending:NoSchedule` and R5 untaints it. R4 sits
between them and is supposed to prefer gmktec. Nothing in any note gives the
gate Job a toleration, so as designed it would land on poweredge — the node
whose relief is the point of the slice.

The gate Job template carries an explicit toleration for
`node-role/ci=pending:NoSchedule`. This is correct rather than a workaround:
the taint exists to keep CI RUNNER pods off gmktec until its capacity is
derived (R5), and a gate is deliberately the first workload allowed there.

### 6. Gate Jobs should quota on cpu and memory, not on churn-slot

The brief has gate Jobs carry real cpu/memory requests but does not say what
the `gates` ClusterQueue quotas. If it quotas `ci-runner.io/churn-slot`, gates
draw on the extended resource whose per-node capacity is the CI admission
budget, and the slice that was supposed to relieve the pool would consume it.

`gates` gets its own `ResourceFlavor` selecting gmktec by node label and
quotas `cpu` and `memory` on it. The pattern already exists in the tree:
`cluster-queue-phase1-proof.yaml` carries a `phase1-proof-flavor` quotaed on
cpu and memory rather than churn-slot. Gates then draw only on gmktec's real
CPU and RAM, poweredge's `C=32` is untouched, and the two-node churn-slot
re-derivation stays R5's problem.

### 7. Pod cache telemetry is currently dropped on the floor — a live regression

Measured on poweredge 2026-09-07: the hook pod template posts cache and
sandbox spans to `http://$(CI_RUNNER_NODE_HOST_IP):4319`, a `status.hostIP`
fieldRef, which resolves to `192.168.1.200`. The host collector binds only
`127.0.0.1:4319` and `10.42.0.1:4319`. A POST to each, taking curl's own exit
status: loopback 200, bridge 200, node address exit 7, connection refused.

PR #1903 — R3's own two-node-preconditions slice — replaced the hardcoded
bridge address with the per-node fieldRef, and the collector was never rebound.
The emitter fails soft, so every job stayed green and the loss is invisible:
no error, no alert, no rows.

This is R7's (monitoring rides along with each topology change) and it blocks
R4, whose Job template reuses that env. Filed as `livespec-dev-tooling-sdu2`,
P1, dispatched 2026-09-07.

The fix must NOT bind the collector to the node's LAN address. That receiver is
KEYLESS, and its config states the bridge-only bind IS its access control:
reachable from the pod CIDR and the host, from nothing on the LAN or Tailscale.
Recommended instead: derive the endpoint inside the pod from the pod's own
DEFAULT GATEWAY, which is by construction its node's cni0 bridge —
`10.42.0.1` on poweredge, `10.42.1.1` on a second node — so one cluster-wide
template is correct on every node with no fieldRef and no new listener.

## The recommended shape

Nine artifacts. Every cluster-side one is a converge artifact applied by
`phase2/reconstruct/converge-ci-stack.sh` from git, per goal 0.

### A. The API-server route

Add the tailnet name and IP to `tls-san` in
`ci-runner/k3s/phase2/k3s-config/config.yaml`, and amend the
"no externally reachable API server" premise its header asserts — a premise
also stated in `provision-k3s.sh`'s kubeconfig-mode step, so both move
together.

The route itself already works. From the VPS, `https://poweredge-xubuntu:6443`
and `https://100.78.140.72:6443` both answer `401 Unauthorized`: TLS and HTTP
complete end to end and only credentials are missing. The LAN address
`192.168.1.200` times out from the VPS, which is a Contabo host and not on the
home LAN, so the tailnet is the only path and MagicDNS resolves it.

What the amendment must say is narrow: the API server is reachable over the
TAILNET, to tailnet members only, and the admin kubeconfig's `0644` mode is no
longer justified by unreachability. Tightening that mode is a consequence to
weigh in the same slice.

### B. The `gates` namespace, ServiceAccount and RBAC

A `gates` namespace; a ServiceAccount in it; a Role granting exactly
`create`, `get`, `list`, `watch` on `jobs` and `pods`, and `get` on
`pods/log`. Nothing cluster-scoped, nothing on Secrets, no `delete` beyond
what the Job TTL controller does for itself.

The credential is rendered by the mechanism that already exists:
`phase2/reconstruct/render-sa-kubeconfig.sh`, which builds a kubeconfig from a
ServiceAccount token Secret and is re-run by the boot converge because the
datastore is tmpfs and every ServiceAccount is recreated on each boot. R4 adds
one argument to it: the `server:` URL, which today is hardcoded
`https://127.0.0.1:6443` and must be the tailnet name for a kubeconfig that
leaves the host.

That tmpfs fact drives the whole credential design: **the gates kubeconfig
expires at every poweredge reboot**, so the VPS needs a re-delivery path, not a
one-time copy. See F.

### C. Kueue: a dedicated flavor and quota, not preemption

- `gates-flavor`: a `ResourceFlavor` whose `nodeLabels` select gmktec.
- `gates-cq`: a `ClusterQueue` covering `cpu` and `memory` on that flavor,
  with `preemption` left at the pool's `Never` settings, and a nominal quota
  sized to leave the LLM service its share — research/001 §3 item 5 derives
  ~50 GiB available to pods on gmktec without evicting the model from the GPU
  carveout, and 32 threads against a ~5 cpu / 6 Gi gate request.
  **Proposed opening quota: 15 cpu and 24 Gi**, i.e. three concurrent gates,
  under half the box. To be confirmed by the slice, not ratified here.
- `gates-lq`: a `LocalQueue` in the `gates` namespace.
- `gate-priority`: a `WorkloadPriorityClass` ordering gates among themselves.

Whether `gates-cq` joins the `fleet-ci-runner-pool` cohort is a real choice.
Recommendation: **it does not.** Cohort membership exists so unused CI quota is
borrowable; a gates queue on a different flavor and different resources has
nothing to lend or borrow, and joining would entangle its fair-share weight
with the CI derivation for no gain.

### D. The gate Job template

Per-repo, rendered by the client, carrying:

- the image read from the gated repository's own `.github/workflows/ci.yml`;
- `command`: the repository's own `just check`;
- real `requests` for cpu and memory, because the scheduler bin-packs on what
  is requested and runner pods request nothing but a churn slot;
- an explicit `LIVESPEC_TEST_PARALLELISM`, because `nproc` in a container
  reports the node's 32 threads regardless of the cpu request, and the local
  lane derives `nproc / 4`;
- the cache env from `phase2/arc/hook-pod-template.yaml` — the sccache Redis
  read-only endpoint, the uv cache dir, the proxies — reused, not re-invented;
- `kueue.x-k8s.io/queue-name: gates-lq`;
- a toleration for `node-role/ci=pending:NoSchedule` and node affinity
  preferring gmktec;
- `ttlSecondsAfterFinished`, so completed gate Jobs are collected rather than
  accumulating as control-plane objects. This matters more than it looks: the
  pool is under a ratified clause to bound the pending work it materializes as
  control-plane objects, and a gate Job is a new object on that same bounded
  control plane.

### E. The source tree: mirror and daemon

Push `HEAD` to a bare mirror on poweredge at `refs/gates/<tree-hash>`, served
read-only in-cluster so a pod on any node can fetch it, keeping GitHub out of
the loop. The transport is Tailscale SSH, which already lands the VPS on
poweredge as `cwoolley`, so the receive path is a tailnet-ACL question owned by
`tailscale-admin`, not a firewall one.

Corrections this note adds: the mirror lives on the `ci-cache` tier, not
`/var/lib/git` (correction 3); and the ref namespace needs a pruning rule, since
one ref per gated tree accumulates forever. Recommended: the client deletes its
own ref after the verdict, and a converge-owned sweep prunes
`refs/gates/*` older than a day.

### F. The VPS side, the one hand-installed surface

`kubectl`, plus the rendered scoped kubeconfig. Recorded in `vps-info`, which
records host changes as a committed `services/<name>/` directory with an
idempotent `install.sh` plus an `AGENTS.md` section — so even the exception
gets a committed installer, and only the SECRET is delivered out of band.

Because the ServiceAccount is recreated at every poweredge boot (B), the
kubeconfig must be re-delivered, not copied once. The fleet already has the
idiom, from the otel-collector onboarding: render on one host and pipe over ssh
into `sudo install -m 0600 /dev/stdin <dest>`, so the value never touches a
terminal or a file on the way. Same shape here, driven from poweredge's
post-converge step toward the VPS, or pulled by the VPS on a `gate-remote`
`401`.

Recommended: **pull on 401.** A push from poweredge needs the runner host to
hold an ssh credential for the VPS and to know its address; a pull needs
nothing new, retries naturally, and fails closed if it cannot re-render.

### G. The `gate-remote` client

In livespec-dev-tooling, wired into `check-pre-push`'s fall-through ONLY —
the `just check` branch after the green-token probe misses. The token path is
untouched.

The verdict contract is fail-closed and already has a model: `gate-run.sh`'s
`exit_code` present is the one marker of a verdict, and anything else is
`DIED_WITHOUT_VERDICT`, never a pass. A `Failed` Job, a lost connection, an
unreachable API server, an unauthenticated kubeconfig: all refuse the push.

On a pass the client calls the EXISTING
`python -m livespec_dev_tooling.green_token write`. No new token format: the
token is keyed on `git rev-parse HEAD^{tree}`, which is the same value that
named the mirror ref, and the existing skip path in `check-pre-push` then
completes the push. One value identifies the pushed tree, the served ref, and
the written token.

Two constraints on the wiring. The `check-pre-push` recipe is **per-repo, not
shared** — dev-tooling's is `scripts/just/check-pre-push.sh`, livespec's is
inline in its justfile — so the client is a shared module invoked from each
repository's own recipe, and rollout is per-repo. And an opt-in switch is
needed: a repository, or a push, must be able to run the gate locally, or the
cluster becomes a single point of failure for every push in the fleet.

### H. Credentials inside the gate pod — R4's first research item

Research/001 §3 item 2 names this as the slice's first item, and it is the
load-bearing hazard, because it fails toward false green:
`check-branch-protection-alignment` and `check-master-ci-green` shell out to
`gh api` and exit 0 with a structured warning when `gh` is unauthenticated. A
gate pod without a token would report green having silently skipped two checks
the VPS runs authenticated — which breaks goal 1's "move WHERE, not WHAT" while
appearing to honor it.

So the slice must, before it is trusted: enumerate every target that reads a
credential (at least those two plus `check-fleet-conformance-admin`, and
`BEADS_DOLT_PASSWORD`, which self-gates when absent); project the least-
privilege, read-scoped ones as Secrets in the `gates` namespace; and add a
check that FAILS, rather than warns, when a target that needs a credential
runs without one inside a gate pod. Warning is the right behavior for a
developer laptop and the wrong behavior for the gate that authorizes a push.

### I. Monitoring, in the same change

R7 binds monitoring to whichever slice changes topology. R4 changes it twice:
new workloads on a second node, and a new API-server exposure. The ride-along
is the collector config in the otel-collector repository, plus whatever signal
says a gate was refused for want of a verdict rather than for a red tree —
those two must be distinguishable, or a broken delegation reads as a failing
repository. Blocked behind `livespec-dev-tooling-sdu2` (correction 7), because
there is no point adding signals to a pipeline whose pod-side spans do not
arrive.

Honeycomb triggers and boards remain kept as code nowhere; research/002 ruled
their home is the otel-collector repository, and R4 is where the first gate
trigger would land. Not resolved here.

## What R4 does not include

Unchanged from research/001 §7 and research/002: moving fabro's docker
sandboxes onto the Job primitive, the orchestrator janitor's host-local
`just check`, and reducing the number of Claude sessions on the VPS — all
enabled BY R4 and all out of this plan. `hp-xubuntu` as a gate host and
`macmini` as any gate host stay deferred. The two-node Kueue churn-slot
re-derivation and the untaint are R5's, and this note's correction 6 is what
keeps them separable.

## The slices

Sized for the factory, dependency-ordered. Every one is scripting or manifests
and touches no host by hand.

| Slice | Deliverable | Depends on |
|---|---|---|
| S1 | `tls-san` for the tailnet name and IP; the "no externally reachable API server" premise amended in both places that assert it; the admin-kubeconfig mode consequence weighed | — |
| S2 | `gates` namespace, ServiceAccount, Role, RoleBinding as converge artifacts; `render-sa-kubeconfig.sh` learns a `--server` argument | S1 |
| S3 | `gates-flavor`, `gates-cq`, `gates-lq`, `gate-priority` as converge artifacts, with the quota derivation recorded in `kueue/DERIVATION.md` | — |
| S4 | The bare mirror on the `ci-cache` tier and the read-only in-cluster git daemon as converge artifacts, plus the `refs/gates/*` pruning rule | — |
| S5 | The gate Job template: per-repo image resolution, real requests, explicit parallelism, hook-template cache env, queue label, toleration, gmktec affinity, TTL | S3 |
| S6 | The credential audit of H and the `gates`-namespace Secrets, with the fail-not-warn check | S2 |
| S7 | The `gate-remote` client wired into `check-pre-push`'s fall-through, fail-closed, writing the existing green token; the per-repo opt-in switch | S2, S4, S5, S6 |
| S8 | The VPS-side installer and the pull-on-401 kubeconfig re-delivery, recorded in `vps-info` | S2, S7 |

S1, S3 and S4 are independent and can drain concurrently. S7 is the only slice
that touches the pre-push seam, so it must not overlap the worktree-pack heal
that the archived `optimize-gates` plan owned in the same recipe.

The proving obligation, from the ratified section: a host is proven by
EXECUTING a job. R4 is proven when a real push on the VPS is gated by a Job on
gmktec, the green token is written from that verdict, and a deliberately red
tree refuses the push.

## Draft scope-event text

Recorded verbatim by the scope event that accompanies this note:

- R4 is built in the eight slices above, cluster-side pieces as converge
  artifacts, the client fail-closed, gates admitted against gmktec's own cpu
  and memory quota rather than the churn-slot pool.
- The brief's preemption premise is withdrawn: the pool's
  `preemption: Never` maintainer declaration stands, and a dedicated quota
  gives gates the non-queueing property preemption was asked for.
- `livespec-dev-tooling-xa6o` is absorbed here and re-cut server-side: the
  churn-slot reapply timer stays on the server and reads each node's capacity
  from that node's profile, so no agent credential is created at all. The
  2026-09-07 ruling's per-node kubeconfig shape is superseded by its own
  premise correction of the same day, which found the server's timer already
  patches every labelled node.
- The VPS remains the one host changed by an installer it does not carry in a
  fleet repo, and the exception is recorded in `vps-info`.

## What this note could not settle

- The `gates` quota numbers are a derivation from research/001's ratios, not a
  measurement. The slice confirms them by the same soak method
  `livespec-ifwnqj` used, and records them in `DERIVATION.md`.
- Whether the admin kubeconfig's `0644` mode should tighten once the API
  server is tailnet-reachable. Named in S1; a security question, not a
  mechanism one.
- What `check-fleet-conformance-admin` needs inside a pod. Still open from
  research/001 §8; S6 answers it by enumeration rather than by assumption.
- Where Honeycomb triggers live as code. Ruled to the otel-collector
  repository by research/002, filed nowhere.

## Read-first chain

This note → research/002 §"The slice order, re-derived under goal 0" item 4
(R4's settled scope) → research/000 §"Proposed delegation primitive" (the
original mechanism, corrected in seven places here) → research/001 §3 and §4
(the measurements and the slice-2 design deltas) → livespec-dev-tooling
`ci-runner/k3s/phase2/kueue/DERIVATION.md` §"Bounding maxRunners to the quota"
and the preemption declaration → `phase2/arc/hook-pod-template.yaml` (the
cache env the Job template reuses) → `phase2/reconstruct/render-sa-kubeconfig.sh`
(the credential pattern) → `livespec-dev-tooling-sdu2` (the telemetry
regression this note found) and `-xa6o` (absorbed here).
