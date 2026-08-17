# Migration decision: rootless-podman host → k3s + Actions Runner Controller + Kueue

Maintainer-directed 2026-08-15, in the fleet-ci-runner-pool-supervisor
session, after `.11`'s podman-SQLite root-cause fix (PR
https://github.com/thewoolleyman/livespec-dev-tooling/pull/1415, merged)
prompted the question "why are we using SQLite for high-concurrency
persistence at all, and is there a more stable long-term architecture."
This note is the write-once research record of that decision; the
ledger epic (`livespec-s43svm`) carries the handoff timeline and scope
event, per the `plan` operation's own division of labor.

## Why the current architecture exists (traced, not assumed)

Rootless podman was never chosen for persistence/concurrency reasons.
It was chosen for a **security** reason, recorded in
`plan/archive/fabro-ci-image-factoring/phase0-runner-containment-design.md`:
CI job code must never be able to become host root, or `ptrace`/`/proc`-
inspect the runner agent process and steal its live GitHub credentials
to impersonate the runner on later trusted jobs. That design explicitly
states it "constrains the *property* (rootless + user-namespaced), not
the tool" and names rootless dockerd or bubblewrap as acceptable
alternatives. SQLite arrived as an incidental consequence: podman
(upstream, Red Hat/containers project) switched its own internal
libpod metadata store from BoltDB to SQLite around podman 4.8/4.9, for
its own reasons, unrelated to this fleet.

The `livespec-s43svm.10/.11/.12/.13` incident chain (2026-08-14/15) —
dockershim exec failures, multi-minute Initialize/Stop-containers
hangs, `database is locked` exit-125 crashes escalating to a 14-job
blast radius on `livespec` master, a recurring PyPI/uv-fetch timeout —
is the accumulated cost signature of driving podman as a bare CLI-per-
invocation tool: every dockershim invocation is a separate process
independently opening and locking the shared libpod SQLite state file.
`.11`'s WAL-mode migration (merged) is a correct, low-risk partial
mitigation, NOT a complete fix — podman's own upstream issue tracker
documents this same class of contention as a known, unresolved problem
for exactly this multi-process-CLI usage pattern:
[containers/podman#20563](https://github.com/containers/podman/issues/20563),
[#18356](https://github.com/containers/podman/issues/18356),
[#17859](https://github.com/containers/podman/issues/17859). The
community-validated complete fix for that class of problem is to route
all podman operations through one long-lived `podman system service`
daemon/connection-pool instead of N independent CLI processes — the
same daemon-centralization model Docker's `dockerd` already uses.

Git history of `ci-runner/dockershim*`/`ci-runner/provision*` in
`livespec-dev-tooling` also shows a long, continuing tail of bespoke
one-off fixes required just to keep a "docker CLI shim wrapping
rootless podman" combination working at all: installing
`podman-docker` ("without which every containerized job dies"),
silencing a podman-docker stdout banner that corrupted the container
hook protocol, translating a bare `docker logout`, repairing a scrubbed
environment container hooks hand podman, creating missing bind
sources "as dockerd would," a kernel per-UID keyring quota ceiling, and
now the SQLite contention chain. This is the load-bearing evidence for
"stop shaving this yak" — it is this epic's own recorded history, not
a hypothetical.

## Does GitHub recommend the current approach?

No. GitHub's own officially-recommended path for scaling self-hosted
runners is **Actions Runner Controller (ARC)** on Kubernetes — pods
scheduled by containerd via the kubelet, no bespoke CLI-per-invocation
container runtime. `ACTIONS_RUNNER_CONTAINER_HOOKS` (the extensibility
point this fleet's `dockershim` implements) exists precisely so
operators can substitute Docker; ARC's own hook is the reference
implementation GitHub ships, and it is containerd-backed, not podman.

## Does moving to Kubernetes make the epic's own load-balancing goal
## easier or harder?

Easier, and the fit is close to 1:1, not a stretch. `.5`'s own spec
(`livespec-dev-tooling/SPECIFICATION/non-functional-requirements.md`
§"Adaptive JIT runner admission budget") requires: `min(queued jobs,
doubled repository logical ceiling, fair share of remaining host-wide
capacity)` with fair borrowing of unused per-repository capacity. That
is, clause for clause, the shape of
[Kueue](https://kueue.sigs.k8s.io/)'s Cohort model: each repo becomes a
`ClusterQueue` with its own nominal quota (the "logical ceiling"),
grouped into a `Cohort` that borrows unused quota from each other, with
Fair Sharing ordering admission by historical resource consumption.
What `.5` is hand-building (dedup event-driven demand queue, durable
single-writer admission state, retry/jitter, fair-share math) is
substantially what Kueue's admission controller already does as a
matured, community-maintained reconciliation loop. ARC's own
`AutoscalingRunnerSet` gives native per-repo `minRunners`/`maxRunners`
scaling off actual queued-job count.

The one honest caveat: `.11`/`.12` found the fleet's real host-wide
bottleneck is **iowait from concurrent container churn**, not CPU or
memory — Kubernetes' default scheduler bin-packs on CPU/memory
requests, so it will not automatically protect against that specific
resource dimension out of the box. It would need to be modeled
deliberately as a Kubernetes
[extended resource](https://kubernetes.io/docs/tasks/administer-cluster/extended-resource-node/)
so the scheduler treats "concurrent container-churn capacity" as a
real, schedulable quantity. This is a real modeling task — but the
current bash supervisor has no mechanism for this at all beyond a
hardcoded "482" guess, so Kubernetes is at worst at parity here and
gives a supported primitive to do better.

## Does this contract need to change in SPECIFICATION?

No, and this matters for scoping the migration. Two sections govern
this area today:

- `livespec/SPECIFICATION/non-functional-requirements.md`
  §"Self-hosted CI runner host requirements" (line 371) — written
  entirely as host-observable PROPERTIES ("a rootless engine," "the
  in-container root identity MUST map to a non-root host identity"),
  never naming podman, bwrap, or any specific tool. An ARC-based host
  with default Kubernetes pod namespace isolation and a non-root
  `securityContext` already satisfies this contract as written.
- `livespec-dev-tooling/SPECIFICATION/non-functional-requirements.md`
  §"Adaptive JIT runner admission budget" (line 94) plus the five JIT
  scenarios in `scenarios.md` starting at line 273 — the fair-share
  formula and the "482, never imply 964" invariant. These describe the
  desired BEHAVIOR of the admission system, not its implementation
  mechanism; Kueue/ARC satisfying that same formula does not require a
  spec rewrite, only a possible confirmation pass once implemented.

The epic/plan/ledger breakdown itself (this thread, `livespec-s43svm`)
correctly stays out of SPECIFICATION per this repo's own convention —
it is tracking, not a durable contract.

## Why k3s, not a "full" kubeadm-provisioned Kubernetes

k3s is CNCF-conformant — same core binaries, packaged as one process —
so ARC and Kueue run on it unmodified; there is no capability gap for
this fleet's needs. "Full" Kubernetes' extra machinery (multi-master HA
control plane, cloud-provider LoadBalancer/dynamic-storage
integrations) is not load-bearing for a bare-metal homelab host with no
cloud provider and a purely-outbound network posture (already required
by the existing host-requirements contract above). k3s does not
foreclose HA later: it supports embedded etcd across 3+ server nodes if
the fleet's stated "multi-host... poweredge-xubuntu first" trajectory
ever needs it. One honest, deliberately-noted parallel: k3s's own
control-plane defaults to single-node SQLite too — but accessed by one
long-lived server process, not hundreds of independent CLI invocations
hammering the file concurrently, which is the actual root cause
diagnosed in `.11`; not the same failure mode, and swappable to
embedded etcd/external DB if ever needed.

A secondary, load-bearing finding: k3s ships its own bundled
`containerd`. Choosing k3s does not just fix the podman contention
problem, it **retires the entire custom dockershim / rootless-podman /
wedge-guard / WAL-migration layer as a category** — ARC schedules job
containers as ordinary Pods directly onto k3s's own containerd. `.11`
and `.12`'s merged fixes are still worth having (they hold the current
host stable during the migration window), but should not receive
further investment once this direction is confirmed.

## Migration strategy — maintainer-directed 2026-08-15

**Side-by-side, not in-place.** Stand up k3s + ARC + Kueue on
poweredge-xubuntu ALONGSIDE the existing podman/dockershim runner pool
(different host-unique label per the existing "every runner MUST carry
both a shared pool label and a host-unique label" contract clause).
Cut traffic over incrementally per repository or per label, never a
single flag flip for the whole fleet. Soak the new path under real
load for a deliberate observation window before treating it as proven.
Only after that verification explicitly confirms EVERY problem in the
`.10`/`.11`/`.12`/`.13` incident chain is gone under the new path —
not merely believed fixed — remove the podman/dockershim stack and
every bespoke script entirely, leaving no trace (provisioning scripts,
systemd units, wedge-guard, WAL-migration script, containers.conf,
sanitize-hook.js, the bash ci-runner-supervisor.sh admission loop that
`.5` has been extending).

Phases (to become ledger children of this epic, dependency-layered,
after the scope event below):

1. **Stand up k3s + ARC + Kueue alongside the existing pool.** New
   host-unique label, zero traffic routed to it yet. Prove it can run
   one real, non-gating job end-to-end.
2. **Model the fleet's admission/fair-share formula in ARC
   AutoscalingRunnerSets + Kueue ClusterQueues/Cohort**, matching
   `.5`'s spec section exactly (the spec does not need to change; the
   implementation does). Model the iowait/container-churn bottleneck as
   an explicit Kubernetes extended resource rather than assuming
   CPU/memory bin-packing alone protects the host.
3. **Incremental per-repo cutover**, starting with a low-risk
   non-gating lane, then one gating repo, observing before the next.
4. **Soak-under-load verification** — a deliberate, bounded observation
   window across a real concurrent-job burst, explicitly checked
   against every symptom in the `.10`/`.11`/`.12`/`.13` chain (no
   dockershim hangs, no `database is locked`, no PyPI-timeout
   correlation with the old path, correct fair-share admission,
   correct 482-equivalent host-wide cap enforcement) before declaring
   the new path proven.
5. **Full cutover** of every remaining repo/label.
6. **Delete the podman/dockershim stack entirely** — provisioning
   scripts, systemd units, `wedge-guard.sh`, `podman-wal-migrate.sh`,
   `containers.conf`, `sanitize-hook.js`, the bash
   `ci-runner-supervisor.sh` admission loop, and every reference to
   them in docs/READMEs — verified by a completeness check (e.g. `grep
   -ri "podman\|dockershim" ci-runner/` returning nothing live) before
   this epic can archive.

**What is explicitly deferred, not silently dropped** (to be restated
formally in the ledger scope event): the existing `.1`-`.9` children's
specific podman-era remediation content (e.g. `.6`'s JIT-slot-preflight
`jq`/tmp-dir bugs, `.8`/`.9`'s fleet-complete-scope bugs) is superseded
by this migration wherever it is bash-supervisor-specific, and should
be closed as superseded rather than implemented, UNLESS its underlying
requirement is genuinely orchestrator-agnostic (e.g. a `.9`-style
"never report recovery success with a repo still starved" invariant
applies equally to a Kueue-based admission controller and should be
carried forward as an acceptance criterion on the new work, not
dropped). Each closed-as-superseded child gets an explicit disposition
comment naming what carries forward vs. what is dropped and why, per
this operation's archive-gate discipline.

## Real-traffic cutover log (livespec-s43svm.16)

Per-repo real-production-traffic cutovers (phase 3 above), each driven purely
through the repo variable `CI_RUNNER_LABELS` — never a workflow-file edit, since
`livespec` itself structurally forbids `.github/workflows/` changes on any
branch via `check-no-workflow-edits` (unlike sibling repos, which record the
cutover as an in-file comment note). Full evidence for each entry lives on the
livespec-s43svm.16 / .22 ledger comments; this section is the durable
cross-repo index.

- **livespec-console-beads-fabro** (non-gating lane), 2026-08-17: real
  production traffic cut to ARC scale set `livespec-console-beads-k3s`.
  First attempt (`livespec-console-beads-fabro-local-ci-k3s`, 41 chars)
  surfaced livespec-s43svm.22 — an ARC workflow-pod naming collision under
  real concurrency (runner-container-hooks truncates the per-job pod name at
  a hard 63-char limit). Fixed by renaming to the 26-char form
  (livespec-dev-tooling PR #1479); the concurrency proof — 14 gating jobs
  dispatched simultaneously by
  https://github.com/thewoolleyman/livespec-console-beads-fabro/pull/663,
  zero collisions — closed .22.
- **livespec** (gating-repo leg), 2026-08-17: real production traffic cut to
  ARC scale set `livespec-local-ci-k3s` (already live since the phase-2
  stand-up, proven at proof-of-life scale by PR #2355). This is the REQUIRED
  `pull_request`/`push` matrix, not a `workflow_dispatch` proof — the fleet's
  `check-self-hosted-routing` guard explicitly allows `pull_request` against a
  gating self-hosted label and forbids only `workflow_dispatch` and five other
  fork-reachable/privileged triggers; an earlier attempt to prove this scale
  set via a `workflow_dispatch`-only smoke workflow was correctly BLOCKED by
  that guard and abandoned without weakening it (PR #2352, closed unmerged).
  This entry's own PR is that real-traffic proof.
- **livespec-runtime**, 2026-08-17: stood up ARC scale set
  `livespec-runtime-k3s` on poweredge-xubuntu, zero traffic (helm release,
  chart 0.14.2, ClusterQueue/LocalQueue `livespec-runtime-cq`/`-lq` in the
  `fleet-ci-runner-pool` cohort, `maxRunners`/`nominalQuota` 64 — this repo's
  own live-measured slot count, confirmed via `systemctl cat
  ci-runner-supervisor`). Real production traffic then cut via
  `CI_RUNNER_LABELS`. Like `livespec`, this repo's own
  `check-no-workflow-edits` forbids an in-file cutover note, so the note lives
  in this repo's own `AGENTS.md` ("CI runner routing") instead, pointing back
  here as the canonical cross-repo record.
- **livespec-overseer**, 2026-08-17: stood up ARC scale set
  `livespec-overseer-k3s` on poweredge-xubuntu, zero traffic (helm release,
  chart 0.14.2, ClusterQueue/LocalQueue `livespec-overseer-cq`/`-lq` in the
  `fleet-ci-runner-pool` cohort, `maxRunners`/`nominalQuota` 65 — this repo's
  own live-measured slot count, confirmed via `systemctl cat
  ci-runner-supervisor`). Real production traffic then cut via
  `CI_RUNNER_LABELS`. Shares `check-no-workflow-edits`, so the note lives in
  this repo's own `AGENTS.md` ("CI runner routing") instead.
- **livespec-driver-claude**, 2026-08-17: stood up ARC scale set
  `livespec-driver-claude-k3s` on poweredge-xubuntu, zero traffic (helm
  release, chart 0.14.2, ClusterQueue/LocalQueue
  `livespec-driver-claude-cq`/`-lq` in the `fleet-ci-runner-pool` cohort,
  `maxRunners`/`nominalQuota` 66 — this repo's own live-measured slot count,
  confirmed via `systemctl cat ci-runner-supervisor`). Real production
  traffic then cut via `CI_RUNNER_LABELS`. Shares `check-no-workflow-edits`,
  so the note lives in this repo's own `AGENTS.md` ("CI runner routing")
  instead.
- **livespec-driver-codex**, 2026-08-17: stood up ARC scale set
  `livespec-driver-codex-k3s` on poweredge-xubuntu, zero traffic (helm
  release, chart 0.14.2, ClusterQueue/LocalQueue
  `livespec-driver-codex-cq`/`-lq` in the `fleet-ci-runner-pool` cohort,
  `maxRunners`/`nominalQuota` 67 — this repo's own live-measured slot count,
  confirmed via `systemctl cat ci-runner-supervisor`). Real production
  traffic then cut via `CI_RUNNER_LABELS`. Shares `check-no-workflow-edits`,
  so the note lives in this repo's own `AGENTS.md` ("CI runner routing")
  instead. Ran `just install-worktree-pack` proactively in the fresh
  worktree before the first push, per the gotcha found on the
  `livespec-driver-claude` leg.
