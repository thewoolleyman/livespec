# Second failure class, same disk: a kine/SQLite stall drops Kueue's pod-admission webhook — measured 2026-09-01

Follow-on to research/002. With the inotify cap lifted (14:34:53Z) and the
pool running 60+ jobs, a different class appeared at 14:57Z. It is not the
inotify cap; it is the disk reaching the control plane.

## 1. The chain, as measured

1. **The k3s datastore shares the CI-churn disk.** k3s runs kine over
   SQLite: `/var/lib/rancher/k3s/server/db/state.db` (63 MB) with an 87 MB
   WAL, on `sda4` (`/`) — the same virtual disk (same three SSDs, same
   controller) that carries containerd's snapshots and every runner's
   `local-path` work volume. At 14:38Z `sda` was at 99.9 % util, aqu-sz 111,
   w_await 117 ms under 66 running CI pods.
2. **The API server's writes stall.** k3s journal: `Slow SQL: INSERT INTO
   kine(...)` — 13 at 14:52:27–28Z, 22 at 14:58:00–09Z.
3. **Kueue loses its leader lease and exits by design.** Kueue log:
   `Failed to update lease … context deadline exceeded` (14:57:40Z) →
   `Failed to renew lease` → `Failed to release lease` → `Could not run
   manager: leader election lost` (14:57:45Z). kubelet then saw liveness
   `connection refused` on :8081 and restarted the container (restart 9 in
   the pod's 17-day life; the deployment has `replicas: 1`, liveness
   `timeoutSeconds: 1`, `periodSeconds: 20`, `failureThreshold: 3`).
4. **Every pod creation in the fleet fails for the restart window.** Kueue's
   mutating webhook `mpod.kb.io` has `failurePolicy: Fail` (correctly — see
   §3) and is served only by that one pod; the API server logged **27**
   `mpod.kb.io` failures between 14:57Z and 15:00Z.
5. **CI jobs die at pod creation with no retry.** The ARC Kubernetes hook
   fails the job at `Initialize containers`: `failed to create job pod:
   Internal error occurred: failed calling webhook "mpod.kb.io": failed to
   call webhook: Post "https://kueue-webhook-service.kueue-system.svc:443/mutate--v1-pod…"`
   then `Executing the custom container implementation failed` —
   livespec#2527 run 33520802867 job 99899323518 (`check-per-file-coverage`,
   14:54–14:58Z). This is the second CI-visible signature after research/002's.

No other controller lost leadership today (journal count 0); the webhook
answered HTTP 200 in 8 ms from the node at 15:00:16Z once Kueue was back.

## 2. What it is not

- Not CPU or memory on the Kueue pod: 9 m CPU / 71 MiB at 15:00Z, zero
  cgroup throttling, memory peak ~100 MB under a 512 MiB limit.
- Not the inotify cap (0 EMFILE since 14:34:53Z).
- Not a Kueue bug: exiting on lost leadership is the documented behaviour;
  the fault is running the webhook's only server inside the one process
  that is allowed to exit.

## 3. Consequences for the legs

- **New requirement (scope amendment 15:02Z, carrier `livespec-okxbkg`):**
  the admission webhook must stay up through a control-plane latency spike —
  Kueue at ≥ 2 replicas (only the leader reconciles; every replica serves
  the webhook) and leader-election tolerances sized above the longest
  measured kine stall; liveness timeout > 1 s.
- **Rejected, not deferred:** `failurePolicy: Ignore` on `mpod.kb.io`. A pod
  that bypasses the webhook bypasses `churn-slot` gating, which is the
  physical cap the fleet's admission formula rests on
  (`kueue/DERIVATION.md`).
- **Deferred to `livespec-g52yrb`:** moving the datastore off the churn
  disk (or to etcd). This plan's requirement is only that a stall not drop
  the webhook; how long the stalls are is the storage plan's number.
- **Detector leg (c) gains a signature:** `failed calling webhook
  "mpod.kb.io"` in job logs / API-server audit, and `Slow SQL` in the k3s
  journal.
