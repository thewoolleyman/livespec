# Runner-pod lifecycle stall: PVC provisioning vs the scheduler's bind deadline — measured 2026-09-01

Captured 2026-09-01 13:40–14:20 UTC on `poweredge-xubuntu` (single-node k3s
v1.36.2+k3s1, the fleet CI runner pool) while three console PRs (#915, #916,
#917) sat with every check `queued` for 17–60 minutes. Every number below was
read from the cluster or the forge at the stated time; nothing is inferred
from a capacity signal. This note is the seed for this plan's charter and its
first scoping event; it ratifies nothing.

## 1. What the stall looked like

- `gh run list`: three CI runs `queued`, 16 jobs each, zero jobs started
  (13:17Z, 13:30Z, ~13:57Z creation). #915's jobs began trickling at ~13:47Z;
  #916 and #917 still had zero started at 14:15Z.
- The repo rule's wedge scan (`kubectl logs <runner pod> --tail=40 | grep "was
  not found"`) over every `Running` non-`-workflow` runner pod: **0 hits**
  (7 pods at 13:44Z, 8 pods at 13:59Z). Not a wedged runner.
- Node headroom at 13:59Z: 72 CPU with **700m requested**, 188 GiB RAM with
  16 GiB used, `/` 9 % and `/var/lib/rancher/k3s/storage` (sda5) 11 % used.
  `ci-runner.io/churn-slot`: 64 allocatable, 8 allocated. The maintainer's
  disk-load monitor showed no I/O wait during the window. Not compute, memory,
  disk space, or churn-slot capacity.
- Kueue (console ClusterQueue `livespec-console-beads-fabro-cq`,
  `nominalQuota` 2): **16 admitted, 0 pending, borrowing 14** — Kueue had
  admitted everything the console asked for. Not quota.

## 2. The chain, as measured

1. **containerd sandbox lifecycle calls time out.** k3s journal, 20 minutes:
   20 × `KillPodSandbox … rpc error: code = DeadlineExceeded desc = stream
   terminated by RST_STREAM with error code: CANCEL` — on
   `livespec-driver-pi` runner pods AND on the storage provisioner's own
   `helper-pod-create-pvc-*` pods in `kube-system`.
2. **The local-path provisioner's per-PVC helper pod therefore sometimes
   exceeds its 120 s ceiling.** Provisioner log, 20 minutes: 47 `Creating
   volume`, 40 `ProvisioningSucceeded`, **6 `ProvisioningFailed: … create
   process timeout after 120 seconds`**, 38 `Deleting volume`, **76 `claim
   "<uid>" in work queue no longer exists`** (stale claims from pod churn),
   **25 `client-side throttling`** waits (~1.2 s each). Helper pods that did
   complete took 8–13 s; one took 2m10s. The deployment ran at k3s's bundled
   defaults: `--worker-threads 4`, `--kube-client-qps 5`,
   `--kube-client-burst 10`, config `/etc/config/config.json` →
   `/var/lib/rancher/k3s/storage`.
3. **PVC provisioning latency reached ~11 minutes.** Runner pod
   `livespec-console-beads-k3s-nm5xz-runner-7xqhm`: PVC
   `…-7xqhm-work` created ~13:50Z (`WaitForPodScheduled`, then
   `ExternalProvisioning` ×43 over 10 m); its PV appeared **14:01:50Z**.
4. **So the kube-scheduler's volume-bind deadline (k3s default 600 s)
   expires**: pod event `FailedScheduling: running PreBind plugin
   "VolumeBinding": binding volumes: context deadline exceeded`; k3s journal
   **94** such expiries in 20 minutes. The pod returns to the queue, waits
   again, and — because ARC keeps creating runner pods for the queued jobs
   and Kueue gates them — every cycle adds PVCs and stale claims to the
   provisioner's queue.
5. **The backlog grew for the whole window rather than draining:**

   | time (UTC) | PVCs Pending | PVCs Bound | pods Pending | pods SchedulingGated | pods Running |
   |---|---|---|---|---|---|
   | 13:59 | 38 | 9 | 9 | 32 | 10 |
   | 14:04 | 39 | 11 | 1 (+5 ContainerCreating) | 38 | 11 |
   | 14:15 | 51 | 15 | 33 | 18 | 14 |
   | 14:19 | 57 | 10 | 47 | 10 | 13 |

   Every scale set was affected (dev-tooling, driver-pi, overseer,
   orchestrator-git-jsonl PVCs all appear in the provisioner's queue), not
   only the console's.
6. Churn scale, `arc-runners` events over 20 minutes: 471 `Started`, 278
   `Created`, 209 `FailedScheduling`, 193 `CreatedWorkload`/`Admitted`, 156
   `Provisioning`.

## 3. Why this is a distinct finding from the 2026-08-30 disk attribution

`increase-ci-runners` (`livespec-zec4mz`, handoff 2026-08-30 13:45Z)
recorded that "containerd DeadlineExceeded lifecycle timeouts occur in
bursts … disk-CHRONIC, not cap-caused", and kept the cap at 64 with RAID-10
(`livespec-g52yrb`) as the durable fix. Today's window had the same
DeadlineExceeded signature **with the disk not saturated** (maintainer's
monitor; <12 % used on both filesystems). So the disk attribution is at
best incomplete: the serialization point that actually stalled CI is the
**PVC provisioning control path** — one provisioner, four workers, a
throttled API client, one helper pod per volume through a containerd that
is itself timing out sandbox operations under pod churn. The 2026-08-30
raise (C = 16 → 64, `livespec-dev-tooling@3b5a6a2f`) multiplied the number
of pods, hence PVCs, hence helper pods, that this path must serve.

`fleet-ci-runner-pool`'s `research/storage-io-characterization.md` already
listed "RAM-backed runner work volumes" as the option "robust to the open
question", and `livespec-trxcf7` (relocated out of that plan 2026-08-29)
holds the maintainer's better shape — a hybrid tmpfs/disk pool that prices
RAM as the resource that sets pool size. Both are about the *bytes*; this
incident shows the *control path* that allocates the volume is a limiter
on its own, and any design that keeps a dynamic per-pod PVC keeps it.

ARC's `containerMode: kubernetes` requires the `work` volume to be a PVC
shared between the runner pod and the per-job `-workflow` pod
(`values-livespec-console-beads-fabro.yaml`:
`kubernetesModeWorkVolumeClaim` → `local-path`, 5 Gi). An `emptyDir` cannot
be shared across pods, so "no PVC" means a static/pre-provisioned local PV
pool or a provisioner that does not need a helper pod per volume — a
design question for this plan, not a one-line change.

## 4. Interim mitigation applied (maintainer-authorized, 2026-09-01 14:19Z)

`kubectl -n kube-system patch deploy local-path-provisioner --type=json -p
'[{"op":"add","path":"/spec/template/spec/containers/0/args","value":["--worker-threads","32","--kube-client-qps","50","--kube-client-burst","100"]}]'`

Rolled out 14:19:20Z (pod `local-path-provisioner-57c446f55b-rkqz8`).
Chosen over "leave the cluster untouched" because fleet CI was stalled and
worsening; recorded as a **bet, not a fix** — if containerd is the true
serialization point, more concurrent helper pods can make its timeouts
worse. **It reverts on the next k3s restart**: k3s re-applies its bundled
`/var/lib/rancher/k3s/server/manifests/local-storage.yaml`, which carries no
args. The durable form (a k3s `--disable local-storage` plus a fleet-owned
copy, or a different provisioner) is leg (b) below.

Measured effect: see the handoff entry recorded after the drain watch; this
note is not updated for status (the ledger is).

## 5. Legs this plan proposes (the scoping event cuts them)

- **(a) Root-cause containerd's sandbox `DeadlineExceeded` under pod churn**
  with the disk *not* saturated — cgroup/AppArmor/user-namespace setup
  (`livespec-dev-tooling@dda8ee3a` runs workflow pods in a user namespace),
  containerd's own concurrency limits, or something else. Host observation
  on `poweredge-xubuntu`; factory-ineligible.
- **(b) Take the dynamic provisioner off the per-job critical path** — the
  `trxcf7` hybrid tmpfs/disk design plus a static or helper-pod-free
  allocation of the `work` volume; make whatever remains of the provisioner
  configuration fleet-owned rather than k3s-bundled so the interim patch is
  not lost on restart.
- **(c) Make this class alarm instead of looking like a queue**: a detector
  for `PVC Pending > N s`, bind-deadline expiries, and `ProvisioningFailed`
  in the same family as the wedged-runner scan (`livespec-s43svm.30`), and
  the "abnormal inter-job gap with spare capacity" seed on
  `livespec-s43svm.20`.
- **(d) Account for helper pods and `-workflow` pods in the churn model**:
  each job now costs three pod lifecycles (runner, helper, workflow) against
  a `churn-slot` budget that counts one.

## 6. Open questions

- Is the provisioner's 120 s helper timeout a symptom (containerd slow) or a
  cause (helper pods queueing behind runner pods for the same containerd)?
- Does the scheduler's 600 s bind deadline matter once provisioning is
  seconds again, or does it only shape the failure?
- What does the drain look like after the interim patch — throughput-bound
  on helper pods, or still bound on containerd?
