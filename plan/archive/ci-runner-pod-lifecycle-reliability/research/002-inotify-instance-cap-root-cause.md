# Root cause: `fs.inotify.max_user_instances=128` exhausted by uid 0 at ~100 containers — measured and fixed 2026-09-01

Follow-on to research/001. That note stopped at "containerd sandbox lifecycle
calls time out and nobody knows why with the disk idle". This note answers it.

## 1. The measurement chain (poweredge-xubuntu, 14:25–14:35 UTC)

1. **What the load-average tasks were NOT waiting on.** `ps -eo state,wchan`
   at load 68.7: only 12 tasks in D state — kernel writeback workers
   (`flush-8:0`, `inode_switch_wbs`) and one `runc:[2:INIT]`. No I/O queue,
   consistent with the maintainer's disk monitor. The load was churn, not
   blocked I/O.
2. **containerd's own log** (`/var/lib/rancher/k3s/agent/containerd/containerd.log`,
   last 10 min at 14:25Z), error classes by count:
   - 122 `failed to delete task: context deadline exceeded`
   - **55 `failed to watch oom events … failed to create inotify fd: too many
     open files`**
   - 146 `ttrpc: received message on inactive stream` (streams 29/31/33/35)
   - 29 `StopContainer … DeadlineExceeded: failed to get task for container`
   - 27 `StopPodSandbox … DeadlineExceeded`
   `EMFILE` from `inotify_init` is not an open-files limit on the process
   (containerd `RLIMIT_NOFILE` 1048576, 814 fds open): it is the per-UID
   **inotify instance** cap.
3. **The cap and its occupancy.** `fs.inotify.max_user_instances = 128`
   (kernel default; `max_user_watches` had been raised to 1048576,
   instances never were; nothing under `/etc/sysctl.d` mentioned inotify).
   Instances held by uid 0: **122 at 14:25:40Z, 127 at 14:26:38Z** with 101
   → 110 `containerd-shim` processes; a healthy shim holds 2 (cgroup v2
   `memory.events` OOM watch), `k3s-server` (kubelet + cadvisor cgroup-tree
   watcher) 21, system daemons the rest. So the cap is reached at roughly
   50 healthy shims' worth of containers, and every job costs a runner pod, a
   `-workflow` pod, and a transient provisioner helper pod.
4. **The cap tracks the incident exactly.** `EMFILE` lines per 10-minute
   bucket: 14:00 → 6, 14:10 → 5, **14:20 → 100** (the window in which the
   provisioner was widened to 32 workers and ~30 extra helper pods appeared).
   k3s journal, `DeadlineExceeded` per window: 20/20 min (13:40–14:00),
   112/5 min (14:17–14:22), **4282/3 min with 842 `KillPodSandbox` (14:32–14:35,
   141 shims, load 181)**.
5. **Where a helper pod's time went** (`helper-pod-create-pvc-e1fec0a0…`):
   created 14:23:42 → scheduled 14:23:46 → sandbox ready **14:24:12 (26 s)**
   → container started 14:24:24 (12 s) → finished 14:24:24. Under the worst
   window the same lifecycle exceeded the provisioner's 120 s ceiling
   (`create process timeout after 120 seconds`, 34 in 5 min).
6. **kubelet symptoms of the same cap** (k3s journal): cadvisor
   `manager.go:1184 Failed to process watch event {… kubepods-besteffort-pod…}`
   and `watcher.go:95 Error while processing event (… IN_CREATE|IN_ISDIR)`,
   `kubelet_pods.go:2193 failed to read memory cgroup config for the pod`.
   cadvisor watches the cgroup tree with inotify; when it cannot, kubelet's
   view of container state degrades and pod lifecycle slows further.
7. **The forge-side signature** of the same failure: PR #916's
   `check-e2e-tmux` job (runner `…-runner-45pkr`, 14:23–14:31Z) failed with
   the ARC Kubernetes hook's `Executing the custom container implementation
   failed. Please contact your self hosted runner administrator.` — the
   `-workflow` pod could not be created. That line is what a CI consumer sees
   when this host condition is active, and is the detector seed for leg (c).

## 2. Why this was misattributed before

`livespec-zec4mz` (2026-08-30 13:45Z) recorded the `DeadlineExceeded` bursts as
"disk-CHRONIC" because they coincided with disk saturation under the
synthetic burst. Today's window reproduced the bursts with the disk idle and
the inotify cap saturated; the cap is a function of concurrent containers,
which the 08-30 raise (C = 16 → 64) roughly quadrupled. The disk finding is
not wrong — the array does saturate at single-digit job concurrency — but it
is not what stalled CI today, and it should not be read as the cause of the
containerd timeouts without this variable controlled.

## 3. The fix applied (maintainer-authorized, 14:34:53Z)

```
sysctl -w fs.inotify.max_user_instances=8192
/etc/sysctl.d/99-ci-runner-inotify.conf   # persisted, with the why
```

First 30 s after: `EMFILE` on inotify 0, `failed to delete task` 0, `inactive
stream` 0 (new calls); uid 0 at 120 instances under an 8192 cap. Whether
containerd's already-broken tasks recover without a restart is the watch
recorded on the epic's timeline, not here.

Left in place from research/001: local-path-provisioner at
`--worker-threads 8 --kube-client-qps 50 --kube-client-burst 100` (the 32
setting was reverted at 14:23Z after it multiplied helper-pod concurrency
into the cap). Its disposition — keep, tune, or replace the provisioner
path — is leg (b).

## 4. What this changes in the legs

- **(a) is answered** for the sandbox-timeout half: the inotify instance cap.
  What remains of (a) is the confirmation over a full organic day and the
  re-characterization of the 08-30 "disk-chronic" bursts with the cap lifted.
- **New leg (e): make the host requirement durable and ratified.** The
  fleet's self-hosted host contract
  (`livespec` `non-functional-requirements.md` §"Self-hosted CI runner host
  requirements") states host-observable properties; this one is "the
  kernel's per-user inotify instance budget MUST cover the pool's maximum
  concurrent containers × the per-container watchers (shim + cadvisor) with
  headroom" — a propose-change in core. Realization: a node-local sysctl
  installed by the same mechanism as
  `livespec-dev-tooling/ci-runner/k3s/phase2/node-extended-resource/`
  (install unit + reapply timer), and the fact recorded in
  `poweredge-xubuntu-info`. Any new pool member inherits it.
- **(d) gets a number:** per job, three pod lifecycles and at least four
  inotify instances (two shims × 2), against a `churn-slot` budget that counts
  one.
