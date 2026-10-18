# 001 — Re-measurement of the brief, corrections, settled open questions, and the challenged slice order (2026-09-06)

Written by the session that opened this plan, 2026-09-06 09:20Z–09:30Z,
from live probes of `vps` (the VPS, hostname `vmi3006760`),
`poweredge-xubuntu`, and `gmktec-xubuntu`, and from the committed
`livespec-dev-tooling` `ci-runner/k3s/` tree and the livespec ledger.
Every number names the command or file it came from. The maintainer's
goals and decisions in research/000 are settled and are not re-argued
here; this note re-measures what the brief said to re-measure, corrects
the brief where the fleet moved after it was written, settles the open
questions that can be settled from source, and challenges the proposed
slice order with the measurements. Repository names are written in full.

## Bottom line

1. **The brief's capacity picture is stale by five hours.** The churn-slot
   cap on `poweredge-xubuntu` is **32, not 64**: the predecessor plan
   stepped it back at 06:10Z, withdrew 40 at 07:51Z on a heavy-mix backlog
   read (CPU saturates at 25–30 running jobs), and archived. `kubectl get
   node` reads `ci-runner.io/churn-slot: 32` now. Consequence: the
   poweredge is AT its CPU ceiling, so a second node is the fleet's only
   remaining upward lever for CI throughput — goal 5 ("extra CPU headroom")
   is not a late nicety, it is the pool's growth path.
2. **The Slow SQL driver was bounded after the brief was written.** The
   07:51Z read attributed the datastore stalls to backlog object churn, not
   to the admitted count; the fix (ARC `maxRunners` bounded to
   `max(2 × quota, 6)`) is live on the cluster (ten scale sets summing to
   76) and was ratified as a fleet property in livespec v220 this morning
   (`SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner
   host requirements", the "MUST bound the pending work it materializes as
   control-plane objects" clause). The k3s journal shows **zero `Slow SQL`
   from 02:09Z to 09:22Z** (70 in the preceding 24 h, 58 of them in the
   00Z–01Z fleet-backlog window). That period was lighter than a fleet
   fan-out, so it is not proof — but it moves the embedded-etcd slice from
   "first, for stability" to "after the next fleet-wide backlog is read
   with the bound in place". Section 5 makes the case.
3. **Two things the brief calls work are already done.** The VPS reaches
   the poweredge API server on port 6443 over the tailnet today (a TCP
   connect from the VPS to `100.78.140.72:6443` opens). What is missing is
   smaller than "route to the API server": the serving certificate's SANs
   do not include the tailnet IP or name (measured with `openssl s_client`
   from the VPS: `poweredge-xubuntu`, `192.168.1.200`, the cluster names
   and loopbacks only), so `tls-san` is confirmed necessary, and `kubectl`
   is not installed on the VPS.
4. **gmktec's memory budget is better than the brief assumed, and its disk
   budget is four times larger.** The llama.cpp model lives in the iGPU's
   firmware carveout (64 GiB VRAM, 49.7 GB in use), not in OS RAM; the
   service cgroup's 48.5 GB is mmap'd page cache (`anon` 95 MB) and is
   reclaimable. The OS sees 62 GiB with 59 GiB available. The NVMe has
   **1441 GiB of unpartitioned free space** beside the 466 GiB root
   partition (`parted print free`) — enough for dedicated, role-labeled
   storage tiers exactly as the ratified storage-tiers clause requires,
   without touching `/`.
5. **One latent hazard for the two-node cluster that the brief does not
   list:** `sccache-redis` and `crates-proxy` are hostPath singletons with
   **no `nodeSelector`** (read from the live Deployments), and the
   local-path provisioner selects only `kubernetes.io/os: linux`. A
   tainted gmktec is safe; the moment gmktec is untainted for CI, a
   restart of either singleton can land it on gmktec with an empty
   hostPath. Pinning them to poweredge is a precondition of the untaint
   slice, and belongs in the join slice while the taint still protects.
6. **Recommended slice order** (section 5): join gmktec tainted → the
   delegation primitive with gates preferring gmktec → untaint gmktec for
   CI → embedded etcd. The brief's order was etcd first. Every maintainer
   decision about etcd stands; only its position in the sequence is
   challenged, and section 5 names the measurement that would move it back
   up.

## 1. What was re-measured, host by host

### `vps` (09:21Z; `nproc`, `uptime`, `ps`, `tmux list-sessions`)

| item | brief (earlier 2026-09-06) | now |
|---|---|---|
| cores | 18 | 18 |
| 1-min load | 35–62 | 29 (5-min 25, 15-min 21) |
| Claude sessions in tmux | 24 | 23 tmux sessions; 25 `claude`/`node` processes at 1.8 cores |
| gates running | 7 Python + 2 Rust concurrently | one pytest-under-coverage gate at ~1 core, one rustc build from a fabro worktree |
| `kubectl` | not stated | absent |
| tailnet IP | not stated | `100.89.189.118` |
| poweredge API server reachable | "one-time: route to the API server" | **already reachable**: TCP connect to `100.78.140.72:6443` opens |
| API server cert SANs (seen from the VPS) | not stated | `kubernetes`, `kubernetes.default[.svc[.cluster.local]]`, `localhost`, `poweredge-xubuntu`, `10.43.0.1`, `127.0.0.1`, `192.168.1.200`, `::1` — **no tailnet IP or name** |

The load is lower than at the brief's measurement because fewer gates are
running now, not because anything changed; the shape (pytest under
coverage as the dominant consumer) is the same.

### `poweredge-xubuntu` (09:20Z; `kubectl`, `journalctl -u k3s`, `findmnt`, `ss`, `systemctl cat k3s`)

| item | brief | now |
|---|---|---|
| threads / load | 72 / 127–179 | 72 / 56 (12 admitted jobs, 42 pods Running) |
| k3s | `v1.36.2+k3s1`, single server, kine on SQLite on a 2 GB tmpfs | same; tmpfs `size=2097152k mode=700` on `/var/lib/rancher/k3s/server/db`; db 591 MB |
| `ci-runner.io/churn-slot` capacity | "currently 64" | **32** (stepped back 06:10Z; 40 withdrawn 07:51Z; see `livespec-e2vcqf` comments of 07:02Z and 07:51Z) |
| ARC `maxRunners` | 63–66 per repo | **bounded**: console 6, dev-tooling 8, driver-claude 8, driver-codex 8, driver-pi 6, livespec 10, orchestrator-git-jsonl 8, orchestrator-beads-fabro 6, overseer 8, runtime 8, `poweredge-xubuntu-k3s` 1 (sum 77) |
| `Slow SQL` last 24 h | 66 in 24 h, all 22h–01h | 70; by UTC hour: 22Z 7, 23Z 1, 00Z 44, 01Z 14, 02Z 4; **none 02:09Z–09:22Z** |
| Kueue | not stated | `kueue:v0.19.1`, `kueue-controller-manager` at 2 replicas; `WorkloadPriorityClass` CRD present, zero objects; eleven ClusterQueues, no cohort objects |
| singleton services | "hostPort 6379 / 3080 on the node" | `sccache-redis` and `crates-proxy` Deployments carry **no `nodeSelector`**; `pypi-proxy` is a Deployment in `ci-warm-cache`; local-path-provisioner `nodeSelector` is only `kubernetes.io/os: linux` |
| listeners | not stated | `6443` on all interfaces, `10250`, `8472/udp` (flannel vxlan); `ufw` inactive |
| git | "bare mirror on poweredge over SSH" | git 2.53.0; `/usr/lib/git-core/git-daemon` present; `/var/lib/git` exists, empty, root-owned (created 2026-03-02; purpose unknown — check before reuse) |
| ssh | not stated | inbound ssh from the VPS is **Tailscale SSH** (the session's process tree shows `tailscaled be-child ssh`); a LAN connect to gmktec's port 22 is refused, so sshd is not the transport between these hosts |
| tailnet | not stated | `100.78.140.72`, `poweredge-xubuntu.perch-rudd.ts.net` |
| k3s unit | not stated | `ExecStart=/usr/local/bin/k3s server --disable traefik --disable servicelb --node-label …`; the durable config is `/etc/rancher/k3s/config.yaml` (`kubelet-arg max-pods=200`, `disable: local-storage`, `write-kubeconfig-mode 0644`), whose header states "a single-tenant node with no externally reachable API server" — a premise the delegation primitive changes and must amend |

### `gmktec-xubuntu` (09:22Z; `lscpu`, `free`, `/proc/meminfo`, `parted`, `lsblk`, `ip`, `ss`, `sysctl`, cgroup files, `/sys/class/drm`)

| item | brief | now |
|---|---|---|
| CPU | 32 threads | AMD Ryzen AI MAX+ 395 (Strix Halo), 16 cores / 32 threads; load 0.04; uptime 1 h 10 min |
| OS | not stated | Ubuntu 26.04 LTS, kernel 7.0.0-30-generic, cgroup v2, AppArmor loaded (222 profiles), `ufw` inactive |
| RAM | "62 GB (unified with iGPU)" | OS-visible `MemTotal` 65.46 GB (62 GiB), `MemAvailable` 62.16 GB (59 GiB); GPU carveout `mem_info_vram_total` 64 GiB + GTT 31 GiB — the machine is 128 GB unified with 64 GiB reserved to the iGPU by firmware |
| LLM service | "~45 GiB model in the UMA carveout when loaded" | `local-homelab-llama-server.service` active (`User=homelab`, `ExecStart=/home/homelab/bin/run-llama-server.sh`, `Restart=always`); listens ONLY on the tailnet IP `100.79.195.82:8080`; 0 established clients at measurement; `mem_info_vram_used` 49.77 GB; cgroup `memory.current` 48.68 GB of which `file` 48.47 GB, `anon` 95 MB, `memory.max`/`memory.high` unset |
| NVMe | "371 GB NVMe free" | Lexar NM790 2 TB; `nvme0n1p1` ext4 466 GiB (371 GiB free) as `/`; `nvme0n1p2` 1 GiB ESP; **1441 GiB unpartitioned** |
| network | "eno1 and wifi both up; pin node-ip to eno1" | `eno1` `192.168.1.156/24`, `wlp195s0` `192.168.1.66/24`, `tailscale0` `100.79.195.82`; LAN rtt to poweredge 0.26–0.79 ms; both wired and wifi are on the same /24, so the `--node-ip 192.168.1.156` pin is confirmed necessary |
| container runtime | "NO docker, NO k3s" | confirmed: no `docker`, `k3s`, `kubectl`, or `containerd` on `PATH` |
| kernel budgets | not stated | `fs.inotify.max_user_instances` 128 (distribution default — the ratified watch-budget clause requires raising it), `fs.inotify.max_user_watches` 516864, `kernel.keys.maxkeys` 200 |
| swap | not stated | 8 GB `/swap.img`, 0 used |
| access | "booted and reachable" | ssh as `cwoolley` (uid 1000) via Tailscale SSH; passwordless `sudo`; no sshd listener |
| clock | not stated | UTC correct; host timezone `America/Los_Angeles` (local 02:22 = 09:22Z) |

Not re-measured: `hp-xubuntu` and `macmini` (outside this plan's scope).

## 2. Corrections to the brief

1. **Cap = 32, and the pool is at its CPU ceiling.** The brief's "currently
   64 on poweredge per research/007" was true at 03:35Z and false from
   06:10Z. The 07:51Z read on child `livespec-e2vcqf` is the load-bearing
   one: at a heavy-mix fleet backlog the CPU saturates at 25–30 running
   jobs, so 32 is AT the ceiling and 40 is withdrawn. The next rung of the
   recorded rollback ladder is 24. Everything in the brief that treats
   poweredge headroom as "later" should be read the other way round: the
   only way the pool's throughput grows is a second node.
2. **The pending-object bound is live and ratified.** `maxRunners` per
   scale set is `max(2 × nominalQuota, 6)` on the cluster now, recorded in
   livespec-dev-tooling `ci-runner/k3s/phase2/kueue/DERIVATION.md`
   "Bounding maxRunners to the quota (2026-09-06)" and ratified as livespec
   v220. The brief's sentence "ARC scale sets: maxRunners 63–66 per repo"
   is the pre-bound state.
3. **The model is not in OS RAM.** The brief budgets gmktec's memory as
   "shared with the LLM service". The weights live in the 64 GiB GPU
   carveout (49.77 GB used); the OS-side 48.5 GB is reclaimable file cache
   of the mmap'd weights file. A pod budget of ~50 GiB on gmktec does not
   evict the model from the GPU; under memory pressure the kernel drops the
   page cache and the next model load re-reads ~48 GB from NVMe. The
   coexistence question is therefore CPU and NVMe bandwidth, not RAM.
4. **The tailnet route already exists.** The delegation primitive's
   "one-time on a driver host" step reduces to: add the tailnet name and IP
   to `tls-san`, render the scoped kubeconfig, install `kubectl`.
5. **gmktec has 1.44 TiB of unallocated NVMe, not 371 GB free.** The tiers
   the ratified storage-tiers clause requires (container image store, work
   volumes, off the OS volume, identified by role label) can be dedicated
   partitions on that space; `/` stays untouched. The clause's "job runtime
   MUST refuse to start on an absent storage tier" `RequiresMountsFor`
   drop-in already exists for poweredge (`storage-layout/`) and is the
   pattern to reuse.
6. **`/var/lib/git` already exists on poweredge.** Empty, root-owned, dated
   2026-03-02 — older than the k3s pool. Do not assume it is free to reuse
   until its origin is checked (a distribution package or an earlier
   experiment).

## 3. The open questions the brief left, settled from source where they can be

1. **sccache redis from a non-pod source — SETTLED from source.**
   `ci-runner/k3s/phase2/sccache/sccache-redis.yaml` runs
   `redis-server --bind 0.0.0.0 --protected-mode no --aclfile
   /etc/redis/users.acl`, and `converge-sccache-redis.sh` writes
   `user default on nopass ~* &* -@all +@read +@connection +info` plus one
   named writer user with a password. The default user IS the read-only
   user; hostPort 6379 is exposed on the node, and the manifest header says
   off-node consumers (the fabro factory host) already use it. A read-only
   gate on any host that can reach the node's port 6379 needs no new ACL
   entry and never touches the populator's writer credential. Inside the
   cluster the question is moot (the hook template's
   `SCCACHE_REDIS_ENDPOINT` is the ClusterIP DNS name).
2. **Credentials inside a gate pod — PARTLY settled; remaining piece named.**
   From the livespec `justfile`: `check-branch-protection-alignment` and
   `check-master-ci-green` shell out to `gh api` and exit 0 with a
   structured warning when `gh` is unauthenticated, so a gate pod without a
   token would silently take the weak path — whereas the VPS pre-push today
   runs them authenticated. `BEADS_DOLT_PASSWORD` self-gates when absent
   (brief). The ratified credential-separation clause permits exactly "a
   least-privilege, read-scoped forge token for the run" in a self-hosted
   job, which is what a `gates`-namespace Secret would project. Not yet
   read: what `check-fleet-conformance-admin` (68 s on the VPS) needs.
   Carry into the delegation slice as its first research item.
3. **`check-e2e-tmux` (console) — SETTLED by precedent, to be re-verified in
   the slice.** The console's `just check` aggregate (which includes
   `check-e2e-tmux`) already runs on the ARC runner pods in the same sandbox
   image on this cluster and passes as the console's required `ci-green`;
   so tmux and a private socket already work in that image under a pod.
   The gate Job reuses the hook pod template's environment, so nothing new
   is needed beyond confirming the socket path is per-pod.
4. **Scheduling latency vs kine lock — DEFERRED, and the reason changed.**
   The 07:51Z read already answered the practical question (the stalls
   track backlog object churn) and the bound removed the driver. The
   discriminating measurement (kine request-duration histogram next to
   `compact` journal lines during a fleet push) is now a for-the-record
   item; the etcd slice's own before/after read supersedes it.
5. **gmktec memory budget with the model resident — SETTLED (section 1).**
   ~50 GiB for pods without evicting the model from the GPU. The slot
   derivation for gmktec is CPU-bound: the predecessor measured ~2.3 % of
   72 threads busy per running job (≈1.65 threads per job) on poweredge;
   at the same ratio gmktec's 32 threads carry ~14 jobs at 75 % busy. A
   first churn-slot capacity of 12 for gmktec, with gates carrying real
   CPU requests (~5 cpu / 6 Gi per the brief), leaves the LLM service its
   share. This is an initial derivation for the slice to confirm with the
   same soak method, not a settled number.

## 4. Slice-2 design deltas the measurements add

- **Per-node cache-telemetry endpoint.** The hook pod template posts cache
  spans to `CI_CACHE_OTLP_ENDPOINT=http://10.42.0.1:4319` — poweredge's
  `cni0` bridge, where the host OTel collector listens keylessly. On gmktec
  the bridge is `10.42.1.1` and nothing listens behind it, so every job on
  gmktec would lose its cache telemetry (or fail its emitter, if the
  emitter is strict). Fix in the join slice: a per-node value (`status.hostIP`
  with a host-network collector listener on each node) or a ClusterIP
  Service in front of the poweredge collector.
- **`LIVESPEC_TEST_PARALLELISM` in a pod.** The local lane derives
  `nproc / 4`; `nproc` in a container reports the node's threads (32 on
  gmktec → 8 workers) regardless of any CPU limit. The gate Job template
  must set the env explicitly (4 workers under a 5-cpu request), or the
  gate oversubscribes its own request exactly the way research/007's
  180-workers-on-72-threads observation describes.
- **Green token from a remote verdict.** `livespec_dev_tooling.green_token`
  keys the token on `git rev-parse HEAD^{tree}` and writes it to the
  per-worktree git dir; `check-pre-push` skips the aggregate when the token
  matches HEAD's tree and the worktree is clean. A remote gate that reports
  a verdict for tree-hash T while local HEAD's tree is T can therefore call
  `green_token write` and the existing skip path completes the push — no
  new token format. The fail-closed contract to mirror is `gate-run.sh`'s:
  `exit_code` present is the ONE marker of a verdict; anything else is
  `DIED_WITHOUT_VERDICT`, never a pass.
- **Kueue already has what the gates queue needs.** v0.19.1 at 2 replicas
  (the research/003 hardening landed), the `WorkloadPriorityClass` CRD
  installed with zero objects. A `gates` ClusterQueue with its own quota and
  a priority class above the runner workloads is additive to the live
  converge, not a Kueue change.
- **The transport for the git mirror is Tailscale SSH**, not sshd: the
  VPS's `ssh poweredge-xubuntu` already lands as `cwoolley` through
  `tailscaled`. The mirror's receive path is therefore a tailnet-ACL
  question, not a firewall one.
- **The `tls-san` change is a k3s config-file edit plus a restart at zero
  jobs**, and a `config.yaml` header amendment (its "no externally
  reachable API server" premise). It does not need the etcd window and
  should not wait for it.

## 5. The slice order, challenged

The brief proposed: (1) embedded etcd, (2) join gmktec tainted, (3) the
delegation primitive, (4) untaint gmktec for CI. Measured against today's
state, the recommended order is:

1. **Join gmktec as a tainted agent** — the node-local subset of
   `install-node.sh` (k3s config for an AGENT, inotify and keyring budgets,
   AppArmor profile, the sccache binary and cache-telemetry emitter, the
   container hook), role-labeled storage tiers on the 1.44 TiB free space
   with the `RequiresMountsFor` drop-in, `--node-ip 192.168.1.156`, the
   node token from poweredge, a `NoSchedule` taint; PLUS the two
   two-node preconditions the brief omits: pin `sccache-redis`,
   `crates-proxy`, `pypi-proxy`, and the warm-cache CronJob to poweredge by
   `nodeSelector`, and give the cache-telemetry endpoint a per-node value.
   Zero risk to the running pool (a tainted agent changes no scheduling
   decision), no quiet window needed, and it unblocks both 2 and 3.
2. **The delegation primitive** — `tls-san` + scoped `gates`
   ServiceAccount kubeconfig rendered on boot + `kubectl` on the VPS; the
   bare mirror on the RAID with a read-only in-cluster git daemon; the
   `gates` ClusterQueue and `WorkloadPriorityClass`; the per-repo Job
   template carrying the hook template's cache env, real requests, and an
   explicit `LIVESPEC_TEST_PARALLELISM`; the `gate-remote` client in
   livespec-dev-tooling wired into `check-pre-push`'s fall-through only;
   node affinity preferring gmktec. This is the slice that relieves the VPS
   — the problem that opened the plan — and it does so without touching
   poweredge's CI capacity at all, because the gates land on the otherwise
   idle gmktec. It is the highest-value slice and the brief had it third.
3. **Untaint gmktec for CI** — the per-node uv warm seed (a
   DaemonSet-shaped populator), gmktec's own churn-slot derivation
   (initially 12, section 3), a `gmktec-xubuntu-k3s` scale set with
   `maxRunners: 1` for the per-member addressing and the proving job the
   ratified clauses require ("every pool member MUST be separately
   addressable"; "a host is proven by EXECUTING a job"), the two-node
   Kueue quota re-derivation, then the untaint. With poweredge at its
   ceiling this is the pool's growth path.
4. **Embedded etcd on the tmpfs** with the maintenance set from research/000
   (compaction verified from the running args, snapshots disabled or
   pointed at the RAID — the default snapshot dir is INSIDE
   `server/db/`, i.e. inside the 2 GiB tmpfs — `quota-backend-bytes`, a
   defrag timer, the tmpfs ceiling) and the monitoring rewrite (the 17
   `Slow SQL` consumers; `--etcd-expose-metrics`; the leader, slow-apply,
   db-size, and compaction gauges into the k3s pipeline; Honeycomb triggers
   with recipients). Last, not first, because the stall driver it was
   justified against was bounded today and has been silent for seven hours,
   and because it is the only slice that needs a control-plane restart in a
   quiet window plus a monitoring migration. **The measurement that moves
   it back up:** any `Slow SQL` during the next fleet-wide backlog at C = 32
   with the bound live. If that read is non-zero, etcd goes before slice 3.

Every etcd decision in research/000 stands (datastore stays in RAM; the
maintenance set; monitoring MUST be updated; no kubeadm; gmktec is an
agent, never a server). Only the position changes.

## 6. Ownership boundaries with the live sibling plans

- **ci-runner-pod-lifecycle-reliability (epic `livespec-ifwnqj`)** owns the
  admission cap `C` and its derivation method (research/007 there:
  "this plan owns the cap and the k3s host configuration; the storage plan
  only produced the conditions"). This plan inherits the predecessor's
  ownership of the poweredge k3s HOST configuration (datastore placement
  and backend, storage tiers, the converge/reconstruct tree's node-local
  half) and extends it to node topology (which nodes, join, taints,
  per-node tiers) and to the delegation primitive. Proposed boundary:
  `livespec-ifwnqj` keeps the admission formula and poweredge's `C`; this
  plan derives gmktec's `C` in slice 3 by that plan's method and records
  it in `DERIVATION.md`; the two-node quota re-derivation is filed as a
  child here with a cross-reference there. Recorded as this session's
  disposition, open to the maintainer's objection.
- **optimize-gates (epic `livespec-xms725`)** works the same pre-push seam
  (`lefthook.yml` pre-push: `install-worktree-pack`, then
  `check-pre-push`). This plan's slice 2 replaces only the `just check`
  fall-through inside `check-pre-push`; the worktree-pack heal stays that
  plan's. Both land in the livespec-dev-tooling justfile template, so the
  two children must not overlap on the same lines.
- **livespec-ci-on-hetzner (epic `livespec-h22nve`, active)** is a separate,
  dedicated-host pool member under the same ratified section. No conflict:
  "Self-hosted capacity is a POOL, and it MAY span more than one host …
  capacity is ADDITIVE". Its per-member addressing and proving-job
  obligations apply to gmktec identically (slice 3).

## 7. Explicit deferrals (to be recorded in the scoping event)

- Moving fabro's docker sandboxes onto the Job primitive; the orchestrator
  janitor's host-local `just check`; reducing the number of Claude sessions
  on the VPS — all named "later / out of this plan" in research/000; kept
  out because none is needed for goals 1–6, and the Job primitive must
  exist first.
- The kine-vs-scheduling discriminating measurement (section 3, item 4).
- `hp-xubuntu` as a gate host (its sccache read path is settled in
  section 3; nothing else is needed for it and nothing routes gates there).
- `macmini` as any kind of gate or CI host (macOS; Linux-only checks).

## 8. What this note could not settle

- The origin of `/var/lib/git` on poweredge.
- What `check-fleet-conformance-admin` needs inside a pod.
- Whether the sandbox image the gate Job would use is the exact tag CI runs
  today (`python-v1.49.0` per the brief; verify from the live ARC values at
  slice 2).
- The k3s flags for the etcd flip on this k3s version (`cluster-init`,
  `--etcd-disable-snapshots` / `--etcd-snapshot-dir`, `--etcd-arg
  quota-backend-bytes=`, `--etcd-expose-metrics`) — to be verified against
  the k3s documentation for `v1.36` in slice 4's runbook, not assumed.

## Read-first chain

research/000 (the brief; goals and decisions) → this note §"Bottom line" →
child `livespec-e2vcqf` comments of 2026-09-06 07:02Z and 07:51Z (the C = 32
reads) → livespec-dev-tooling `ci-runner/k3s/phase2/kueue/DERIVATION.md`
"The step back to C = 32 on the tiered host (2026-09-06)" and "Bounding
maxRunners to the quota (2026-09-06)" → livespec
`SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner host
requirements" (v220) → livespec-dev-tooling
`ci-runner/k3s/phase2/install-node.sh` (the node-local order) and
`phase2/arc/hook-pod-template.yaml` (the cache env a gate Job reuses).
