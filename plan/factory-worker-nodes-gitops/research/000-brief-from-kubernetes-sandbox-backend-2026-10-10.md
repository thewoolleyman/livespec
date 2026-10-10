## The maintainer's statement of what done means

I think we should have separate plans, whether they are existing ones or new ones, to get GMKTEC, and HP fully up with proper GitOps discipline as worker nodes. I can go ahead and wrap up those plans, and not muddy this plan with Kubernetes dependencies and infrastructure that will probably not be implemented properly because of the lack of focus.

## Definition of Done assertions derived from that statement

- `kubectl get nodes` on poweredge-xubuntu reports gmktec-xubuntu and hp-xubuntu as Ready, and both return to Ready after a poweredge-xubuntu reboot with no hand step on any host.
- hp-xubuntu is a member of the `ci_pool` inventory group with `cluster_role: agent`, and `just ansible-drift ansible/ci-pool.yml` reports no drift for poweredge-xubuntu, gmktec-xubuntu or hp-xubuntu after `just ansible-apply ansible/ci-pool.yml`.
- gmktec-xubuntu is untainted with churn-slot capacity 12 and the cohort quota is 44 as the R5 derivation in livespec-dev-tooling kueue/DERIVATION.md records, and livespec-dev-tooling-xa6o and livespec-dev-tooling-9btv are closed.
- A `factory` namespace with a ServiceAccount, ResourceQuota and NetworkPolicy exists as converge artifacts and is present again after a poweredge-xubuntu reboot.
- hp-xubuntu, as the Fabro server host, holds a kubeconfig scoped to the `factory` namespace that refreshes itself after a poweredge-xubuntu reboot, and `kubectl auth can-i create pods -n factory` answers yes from that host.
- The Docker sandbox slice on hp-xubuntu runs factory dispatches to completion while hp-xubuntu is a k3s agent, within the coexistence budget this plan records.

# 000 — brief from the kubernetes-sandbox-backend plan (2026-10-10)

## Why this plan exists

The livespec-orchestrator-beads-fabro plan `kubernetes-sandbox-backend` (epic
`bd-ib-nmuyjc`) moves the dark factory's sandboxes from Docker on hp-xubuntu to
pods on a maintainer-owned Kubernetes cluster through a sandbox-driver protocol
v2 plugin. On 2026-10-10 the maintainer ruled that cluster and node provisioning
is OUT of that plan and belongs to separate plans in this repository, so that
the backend plan stays focused on the plugin, the Fabro and Petri extension, the
dispatcher wiring and the cutover. This plan is the node-provisioning half. The
backend plan names a Ready cluster with a non-hp worker as its hard external
dependency, and this plan is the owner of that dependency.

Full measurements and the ruling: livespec-orchestrator-beads-fabro
`plan/kubernetes-sandbox-backend/research/002-existing-cluster-measurements-and-scope-ruling-2026-10-10.md`
(merged in that repository's PR #2737).

## What exists today (measured live 2026-10-10, 01:30 to 01:35 UTC)

| Node | Role | Hardware | State |
|---|---|---|---|
| poweredge-xubuntu | k3s server, v1.36.2+k3s1 | 72 CPUs, 377 GB | Ready; datastore on a 2 GB tmpfs rebuilt from git at every boot; runs the whole CI pool |
| gmktec-xubuntu | k3s agent, label `k3s-role=arc-runner-host` | 32 threads, 62 GB | NotReady since 2026-09-28 19:47 PDT, taint `node.kubernetes.io/unreachable:NoExecute` |
| hp-xubuntu | not a node; Fabro server host | 16 CPUs, 30 GB | no k3s; runs the Docker sandbox slice; in Ansible inventory group `sandbox_hosts`, not `ci_pool` |

gmktec's failure: poweredge booted 2026-09-28 19:45:18; the node object was
created 19:46:11; gmktec's `/etc/rancher/node/password` was rewritten 19:46:14;
the kubelet stopped posting 19:47:05. The `k3s-agent` unit has been
`activating` since, logging `Node password rejected ... contents of
'/etc/rancher/node/password' may not match server node-passwd entry` every ten
seconds. The server's `gmktec-xubuntu.node-password.k3s` secret in
`kube-system` dates from that rebuild. The `agent_rejoin` watchdog role in
livespec-dev-tooling restarts a wedged agent; a restart cannot clear a password
mismatch, so the R5 mechanism does not cover this failure mode. The repair is
the standard one (delete the stale secret, restart the agent) and must land as a
converge artifact or an Ansible task, never by hand.

## Relation to the existing plans

- `gitops-deployment-discipline` (epic `livespec-qurhq2`) is the gate: by the
  maintainer's 2026-09-12 direction nobody converges or touches a host until it
  is fully landed. Its work sits in five executor worktrees since that day. This
  plan does not start host work before that plan lands or the maintainer lifts
  the gate explicitly.
- `k3s-on-gmktec-for-vps-usage` (epic `livespec-sab5gn`): all children closed,
  but R5 (two-node CI: gmktec untaint, churn-slot 12, quota 44) is merged code
  never converged, and its latest handoff believes both nodes are Ready. This
  plan takes over the R5 converge and gmktec's repair; the CI-only remainders
  (gate-remote S7 `livespec-dev-tooling-2u2c`, embedded etcd R6, monitoring R7)
  stay with that plan or its successors.
- Nothing anywhere planned hp as a worker. That is new scope here.

## Draft requirement carriers

1. gmktec Ready again, by a mechanism that survives the next poweredge reboot.
2. R5 converged through `just ansible-drift` / `just ansible-apply
   ansible/ci-pool.yml`, never by hand; xa6o and 9btv closed.
3. hp joins `ci_pool` as an agent with its own capacity profile, while the
   Docker slice keeps running under a recorded coexistence budget (review
   finding 4 of the backend plan: at 8 GB requests a 30 GB host schedules three
   such pods, not fifteen; Traefik and ServiceLB defaults take ports 80 and 443;
   reservations and eviction thresholds set deliberately).
4. A `factory` namespace, ServiceAccount, ResourceQuota and NetworkPolicy as
   converge artifacts, plus the kubeconfig re-delivery to the Fabro server host
   on the pull-on-401 idiom the gates kubeconfig already uses.
5. Pod-to-tailnet reach from every worker to the beads Dolt tenant and the
   telemetry receiver verified, and registry access for the sandbox image.

## Open question to settle early

The control plane's datastore is a tmpfs, so a poweredge reboot drops every pod
and lease on the cluster at once. CI jobs tolerate that; factory runs lasting
hours do not. Either persistent datastore (R6, embedded etcd) becomes a
prerequisite here, or the backend plan's plugin must survive a control-plane
rebuild by design. Decide which plan owns it before the backend plan's design
child is written.

## Definition of Done status

The statement above is the maintainer's words verbatim. The six assertions are
SESSION-DERIVED by the kubernetes-sandbox-backend session and await the
maintainer's confirmation or amendment at this plan's first attended resume.
