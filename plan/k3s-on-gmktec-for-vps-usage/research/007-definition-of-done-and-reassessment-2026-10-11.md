# 007 — Plan Definition of Done, and the reassessment after the GitOps plan landed (2026-10-11)

This note records the plan's Definition of Done, authored with the maintainer on 2026-10-11 because the plan epic predated the requirement, and the live reassessment taken when the gating plan `gitops-deployment-discipline` (epic `livespec-qurhq2`) was confirmed archived. Every host fact below was measured 2026-10-11 unless dated otherwise.

## The maintainer's statement of what done means

Fleet CI runs on both k3s nodes with gmktec carrying real load and surviving poweredge reboots unattended, and a git push from the VPS can be gated on the cluster instead of the pushing host, with every host and cluster piece provisioned from committed source.

## Definition of Done assertions derived from that statement

- During a fleet CI backlog, runner pods are scheduled onto both poweredge-xubuntu and gmktec-xubuntu, and jobs that run on gmktec-xubuntu finish with a passing result.
- After an unattended poweredge-xubuntu reboot, gmktec-xubuntu returns to Ready, untainted and advertising its churn-slot capacity, and the cluster's churn-slot quotas and gate credential Secret are restored, with no operator command run on any host.
- In a repository with the delegated gate enabled, a git push from the VPS runs that repository's full pre-push gate as a cluster Job, and the push completes on a green verdict without the gate running on the VPS.
- When the cluster returns no verdict, a delegated git push from the VPS is refused rather than completed.
- After an unattended poweredge-xubuntu reboot, the VPS refreshes its gates credential automatically on the first rejected use, and the next delegated push succeeds without an operator step.
- The drift report for each playbook that provisions the two k3s nodes and the VPS's gates credential reports zero changes.

## How each assertion is carried

The carrier relation is recorded only in the plan epic's carrier-map scope event (2026-10-11T00:38:04Z). In summary, for a reader of this note: assertions 1, 2 and 6 are discharged by the plan's own Proof of Done record; assertion 5 by `livespec-dev-tooling-74q6iw`; assertions 3 and 4 by `livespec-dev-tooling-pj7q4m`, which depends on `74q6iw`. Both children live in the livespec-dev-tooling ledger, because the factory dispatches an item into the repository whose ledger holds it, and a parent edge cannot cross ledgers.

## Live state at the reassessment

| Fact | Value |
|---|---|
| gmktec-xubuntu | Ready, no taints, churn-slot allocatable 12 |
| poweredge-xubuntu | Ready, no taints, churn-slot allocatable 32 |
| Cluster churn-slot quota total | 44 |
| gmktec rejoin watchdog | idle between ticks, script matches the committed copy |
| `livespec-dev-tooling-xa6o`, `-9btv` | closed 2026-10-10 |
| gates namespace | git-daemon Deployment running, gate-submitter credential and gate-forge-credential Secret present, gates queues empty |

R5 is converged: the GitOps plan applied `ansible/ci-pool.yml` from the VPS on 2026-10-10, including the repair of the 2026-09-29 node-password race that had kept gmktec out of the cluster for eleven days. This plan does not converge or recover gmktec again.

## The gates-kubeconfig follow-up, live-exercised

`just ansible-drift ansible/gates-kubeconfig.yml` reported three changes (the refresh script, its env-file, the credential); `just ansible-apply` converged them; a second drift run reported zero changes. The installed credential authenticates as `system:serviceaccount:gates:gate-submitter`.

The root-run refresh then failed with `install: No such file or directory`, exit 1. The ssh identity drop that follow-up #2 added works; the failure is the write. Ubuntu 25.10 and 26.04 replace GNU coreutils with uutils coreutils by default, and uutils' `install` refuses to read standard input onto a destination that already exists:

| Host | Ubuntu | `install` reports | absent destination | existing destination |
|---|---|---|---|---|
| vps | 25.10 | uutils coreutils 0.2.2 | exit 0 | exit 1 |
| poweredge-xubuntu | 26.04 | uutils coreutils 0.8.0 | exit 0 | exit 1 |
| gmktec-xubuntu | 26.04 | uutils coreutils 0.8.0 | not probed | not probed |

The same idiom is in three more committed scripts, two of which run on the k3s nodes. The fleet's exit-test suites fake `install`, which is why none of them caught it. Filed as `livespec-dev-tooling-74q6iw`.

## The delegated gate (R4.S7) as it stands

The 2026-09-09 status summary (research/006) said S7 did not exist. That is no longer true: S7 was regroomed into S7a, S7b and S7c (`livespec-dev-tooling-xxlnq5`, `-v5fzvc`, `-m3tmxy`, PRs #2133, #2142, #2153), and the gate ran green 77/77 on gmktec on 2026-09-10 (epic `livespec-dev-tooling-rwmo`). What remains is that nobody can use it from the VPS as shipped:

1. The client runs bare `kubectl` with the inherited environment, so it neither finds `/etc/ci-runner/gates.kubeconfig` nor goes through the refresh-on-rejection wrapper.
2. The credential is `root:root 0600`, and pushes run as the login user.
3. The `delegated_gate` switch is per-repository and blind to the host, so opting a repository in would make a Fabro sandbox push in that repository try to delegate and then fail closed.
4. No repository sets `delegated_gate`.

Filed as `livespec-dev-tooling-pj7q4m`, which also opts in livespec-dev-tooling.

## Deferrals

Recorded in the same scope event: R6 and R7, fleet-wide `delegated_gate` rollout, and the Ansible migration's leftover dead artifacts and manual preconditions are deferred to archive time. `hp-xubuntu` as a worker node belongs to plan `factory-worker-nodes-gitops` (epic `livespec-sqvj7p`), not this plan.
