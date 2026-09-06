# Brief: k3s-on-gmktec-for-vps-usage (successor to poweredge-raid-array-maintenance)

Written 2026-09-06 by a Claude session in `vps-info` after a live investigation of
why the VPS CPU was saturated. Every number below was measured on that date; the
command that produced it is named so it can be re-measured. Predecessor plan:
`poweredge-raid-array-maintenance` (epic `livespec-g52yrb`, archived at
`plan/archive/poweredge-raid-array-maintenance/`). This plan inherits its
ownership of the poweredge k3s host configuration and extends it to a second
node and to a generic "delegate work to the cluster" primitive.

## Maintainer's goals (verbatim intent, 2026-09-06)

1. Keep the pre-push gate. Removing it or subsetting it was rejected: "every
   git push should be green as early as possible; faster feedback loops are
   always better." Do not propose dropping or weakening the local full
   aggregate. Move WHERE it runs, not WHAT it runs.
2. Make the offload generic and container-based, so that small/simple machines
   can drive Claude sessions while compute happens elsewhere.
3. A central Kubernetes control plane on poweredge (it has the RAID) that
   schedules work onto other nodes, with the CI cache tiers available to that
   work "for free, like fabro containers do".
4. gmktec-xubuntu is the first additional node. It is booted and reachable.
5. Extra CPU headroom for poweredge when it is full on CI capacity is IN SCOPE
   (open gmktec to CI runners once the prerequisites below are met).
6. Update monitoring for whatever datastore/topology changes land.

## What was measured on the VPS (the problem)

- `vps`: 18 cores, load 62, 0.7% idle at the start of the investigation.
- 24 Claude Code sessions in tmux on the VPS, ~2.3 cores just for their Node
  event loops.
- The dominant load was pre-push git hooks (`lefthook pre-push` → `just
  check-pre-push` → `just check`) running the FULL check aggregate on the VPS
  host, seven Python runs and two Rust runs concurrently. One session
  (`console-control-plane-primitives`) pushed the branch
  `chore/plan-record-migration-run` to ~10 repos at once via
  `livespec-orchestrator-beads-fabro/dev-tooling/gate-run.sh`, so 5 full
  aggregates ran in parallel on one box.
- Core split at peak (ps sample): Python gate work ~10.5 cores, Rust gate
  work ~4.2 cores, Claude sessions ~2.3 cores.
- Per-target timing from the structured push log for livespec-dev-tooling
  (`"event": "target_completed", "wall_s"`): pre-push total 862 s, of which
  `check-per-file-coverage` (pytest -n 4 + branch coverage) was 817 s;
  check-no-except-outside-io 77 s; check-types 73 s;
  check-fleet-conformance-admin 68 s. Other Python repos: livespec 773 s,
  livespec-overseer 942 s, livespec-driver-claude 571 s.
- Console (Rust) pre-push: 768 s total; cargo test build 13 s (compile cache
  working), nextest 63 s, the remaining ~690 s is the llvm-cov instrumented
  rebuild.
- Conclusion: the VPS load is Python pytest-under-coverage, not Rust. The CI
  box's sccache tier helps only the Rust repo; for Python the win is moving
  the compute, not caching.
- Dead processes found and removed (18 orphaned `tail -F | ugrep` watcher
  pipelines and two stray tails from sessions that ended 2 to 3 weeks ago,
  all PPID 1). ~10% of one core. Not the cause.

## Fleet capacity measured the same day

| host | cores | idle | load | notes |
|---|---|---|---|---|
| vps | 18 | ~1% | 35–62 | all gates run here today |
| hp-xubuntu | 16 | 37% | 7.7 | has just/mise/cargo/docker; sccache-redis for fabro sandboxes already provisioned there by fabro-hosts |
| poweredge-xubuntu | 72 threads | 14% | 127–179 | 153 runner pods, ~135 running across 10 ARC scale sets; 155 GB RAM free |
| gmktec-xubuntu | 32 threads | ~100% | 0.0 | 62 GB (unified with iGPU), 371 GB NVMe free, same LAN as poweredge (192.168.1.156 ↔ 192.168.1.200), NO docker, NO k3s, runs `local-homelab-llama-server.service` (llama.cpp, ~45 GiB model in the UMA carveout when loaded); both wired eno1 and wifi are up — pin node-ip to eno1 |
| macmini | 14 (Apple silicon) | ~85% | 2 | macOS: Linux-only checks would not port; not a gate host |

## CI pool facts relevant to the design (livespec-dev-tooling `ci-runner/k3s/`)

- Every PR push already runs the identical `just check` aggregate on the ARC
  runners on poweredge; `ci-green` is the sole required merge check. CI wall
  time 3–10 min when not queued; six runs were queued at the time.
- CI jobs run in `ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-v1.49.0`
  (same image fabro uses). A gate can run in that image on any node.
- Cache tiers and their reach from a second node:
  - sccache-redis: hostPort 6379 on the node + ClusterIP; ACL users; the ARC
    hook pod template documents `SCCACHE_REDIS_ENDPOINT`, a read-only user,
    `SCCACHE_REDIS_RW_MODE=READ_ONLY`. Free via cluster DNS on any node.
  - crates-proxy: hostPort 3080 + ClusterIP. Free via cluster DNS. README's
    own number: <1 s/job.
  - pypi-proxy: ClusterIP only (port 8081). Free via cluster DNS.
  - uv warm cache (hardlink/reflink seed): hostPath on poweredge, ~6.5 s/job
    on `uv sync`. NOT free on a second node: the populator must run per node
    (DaemonSet-shaped) before gmktec matches poweredge on this tier.
  - sandbox image layers: pulled once per node then cached by containerd.
- Runner pods request NO cpu/memory, only `ci-runner.io/churn-slot: 1`. The
  scheduler therefore bin-packs on churn-slot alone. The churn-slot capacity
  is derived PER NODE (`kueue/DERIVATION.md`; currently 64 on poweredge per
  research/007 of ci-runner-pod-lifecycle-reliability). A second node raises
  the fleet ceiling; it must get its own derivation (NVMe, memory shared with
  the LLM service).
- ARC scale sets: maxRunners 63–66 per repo; Kueue ClusterQueue quotas per
  repo. Re-derive for a two-node pool before opening gmktec to CI.
- `phase2/reconstruct/render-sa-kubeconfig.sh` already renders a scoped
  ServiceAccount kubeconfig from git on every boot — the pattern for a
  driver-host credential.
- `phase2/install-node.sh` is the ordered node-local installer runbook
  (k3s-config, apparmor, inotify/keyring budgets, container-hook, sccache
  binary, ...). The subset that is node-local must run on gmktec too.

## Datastore: kine/SQLite vs embedded etcd (settled questions)

- Today: k3s `v1.36.2+k3s1`, single server, kine over SQLite on a 2 GB tmpfs
  (`phase2/datastore-tmpfs/`), cluster reconstructed from git on every boot.
  SQLite footprint 591 MB incl. WAL; ~62k kine rows; ~11 writes/s on a quiet
  host.
- Even on tmpfs, k3s logged 66 `Slow SQL: INSERT INTO kine` lines in 24 h
  (min 1.03 s, median 1.29 s, max 2.88 s), ALL during the 22h–01h window when
  host load was 127–179. Research/007 measured load 96 with zero Slow SQL and
  k3s-server at ~120% of one core (1.7% of the box). So: CPU is the ceiling
  for throughput (etcd cannot change job times), and the residual stalls are
  either control-plane scheduling latency under 134+ runnable threads or
  kine's single-writer lock under a churn burst; undetermined from outside.
- etcd is NOT required to add gmktec. Agents (worker nodes) join a
  SQLite-backed single server with the node token. Embedded etcd is required
  only for multiple SERVER (control-plane) nodes. gmktec joins as an AGENT.
- Maintainer decisions 2026-09-06: datastore stays in RAM; RAM is plentiful;
  do whatever maintenance keeps etcd from growing unbounded; exactly-two
  control planes is not a concern (gmktec is an agent); "real Kubernetes"
  (kubeadm) is NOT wanted — k3s is conformant upstream Kubernetes and with
  `cluster-init: true` runs upstream etcd; monitoring MUST be updated.
- Embedded etcd recommendation: do it as its own independent slice, for
  control-plane stability under write churn (the failure that dropped the
  Kueue webhook), not for speed. Required maintenance on tmpfs: keep k3s's
  periodic compaction (verify interval from the running etcd args), disable
  the 12 h snapshot cron or point it at the RAID (`--etcd-snapshot-dir` /
  `--etcd-disable-snapshots`), set an explicit backend quota
  (`--etcd-arg quota-backend-bytes=...`), a periodic defrag timer (k3s only
  defrags at startup), raise the tmpfs `size=2G` ceiling if needed, and
  gauge `etcd_mvcc_db_total_size_in_bytes` vs `..._in_use_in_bytes`.
- etcd is strictly WORSE than SQLite on a slow/shared disk (fsync → leader
  loss). Hard rule: the datastore never returns to the churn disk.
- Monitoring changes: 17 files in `livespec-dev-tooling/ci-runner` and
  `livespec/plan/ci-runner-pod-lifecycle-reliability` key on the `Slow SQL`
  journal signature; etcd equivalents are `apply request took too long`,
  `etcdserver: request timed out`, leader changed/lost, NOSPACE /
  `mvcc: database space exceeded`. Enable `--etcd-expose-metrics`; scrape
  `etcd_server_has_leader`, `etcd_server_leader_changes_seen_total`,
  `etcd_server_slow_apply_total`, the db-size gauges, compaction counters
  into the otel-collector k3s pipeline; add Honeycomb triggers (has_leader=0,
  db size vs quota, slow-apply during a fleet push) with recipients attached.

## Proposed delegation primitive (what "the VPS delegates to the cluster" means)

One-time on a driver host (vps or any small box): route to the API server
(k3s 6443 over the tailnet; add the tailnet name to `tls-san`), a scoped
kubeconfig (ServiceAccount in a `gates` namespace: create/get/watch/log on
Jobs and pods only; rendered by `render-sa-kubeconfig.sh` on every boot),
`kubectl`.

Per push (the pre-push hook's existing seam: `check-pre-push` calls
`green_token check`, falls through to `just check`; replace only the
fall-through):
1. Push HEAD to a bare mirror on poweredge over SSH at `refs/gates/<tree-hash>`;
   a read-only in-cluster git daemon serves the mirror from the RAID so a pod on
   ANY node can fetch it (keeps GitHub out of the loop).
2. `kubectl create` a Job from a per-repo template: sandbox image, `just
   check`, REAL cpu/memory requests (Python gate ~5 cpu / 6 Gi; console gate
   more for llvm-cov), the cache env from the hook pod template,
   `kueue.x-k8s.io/queue-name: gates`.
3. `kubectl wait` + `kubectl logs -f` back into the agent's terminal.
4. Complete → write the local green token for that tree-hash → push proceeds.
   Anything else (Failed, lost connection) is NOT a verdict → push refused
   (same fail-closed contract as `gate-run.sh`'s DIED_WITHOUT_VERDICT).

Kueue: a `gates` ClusterQueue with its own quota and a WorkloadPriorityClass
above the CI runners, so a gate is admitted immediately and preempts a queued
runner rather than waiting behind CI. Optional node affinity to prefer gmktec
for gates in the first weeks. Balancing across nodes comes from the scheduler
once Jobs carry real requests.

## Proposed slice order (from the investigation; the plan should challenge it)

1. Embedded etcd on poweredge (`cluster-init: true`) + the maintenance/
   monitoring set above. Independent of everything else; flip in a quiet
   window; verify via API-server request-duration metrics through the next
   fleet push.
2. Join gmktec as an agent over the LAN, tainted so nothing schedules there
   yet; run the node-local subset of `install-node.sh`; pin node-ip to eno1;
   decide the LLM service's memory footprint / coexistence.
3. Git mirror + gate ClusterQueue/priority + Job templates + `gate-remote`
   client in livespec-dev-tooling wired into `check-pre-push`. First gates run
   on gmktec.
4. Per-node uv warm seed; churn-slot derivation for gmktec; ARC/Kueue quota
   re-derivation for two nodes; untaint gmktec for CI. This is the slice that
   gives poweredge CPU headroom when full on CI.

Later / out of this plan unless the plan decides otherwise: moving fabro's
docker sandboxes onto the same Job primitive; the orchestrator janitor's
host-local `just check` runs; reducing the number of Claude sessions on the
VPS.

## Open questions the plan must settle

- Does poweredge's sccache redis `--bind`/`protected-mode` accept a non-pod
  source, and can a read-only ACL user be minted without touching the
  populator's writer credentials? (Only matters if a non-cluster host, e.g.
  hp, ever runs gates; inside the cluster it is moot.)
- Which check targets need credentials inside a gate pod (at least a GitHub
  token for fleet-conformance checks; `BEADS_DOLT_PASSWORD` self-gates when
  absent) and how they are projected as Secrets in the `gates` namespace.
- `check-e2e-tmux` (console) spawns a tmux server: needs its own socket in
  the pod.
- Whether the stalls are scheduling latency or kine lock serialization (the
  discriminating measurement: kine request-duration histogram next to
  `compact` journal lines during a fleet push). Only matters for the record;
  the etcd slice is justified either way by stability.
- gmktec memory budget with the LLM model resident (UMA carveout) — slot count
  for gates and for CI derives from it.
