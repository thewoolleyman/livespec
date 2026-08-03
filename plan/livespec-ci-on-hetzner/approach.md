# Livespec CI on Hetzner — approach

## Objective

Move Livespec's merge-gating CI onto the dedicated Hetzner NixOS host as quickly as the accepted safety contract allows, while retaining a mechanically usable GitHub-hosted fallback. Completion is a live forge observation: a required same-repository CI job runs on the Hetzner host under a one-job registration, the registration and workspace do not survive the job, and the hosted fallback is exercised successfully.

## Authoritative inputs

- Livespec `SPECIFICATION/non-functional-requirements.md` §“Self-hosted CI runner host requirements”, ratified in v192 by merge `73cf2dbc1dc73d8d15bbe3353d5f97a2719cbfa7`.
- The two v192 scenarios: a conforming host carries a fleet gate without host-wide privilege, and an unavailable host does not deadlock the merge gate.
- Homelab's active `plan/05-hetzner-fleet-member/` and `plan/07-build-substrate/` threads. Their ledger state, not their plan prose, decides readiness.

## Ownership boundary

This thread owns the Livespec side:

- GitHub repository policy and fork-approval measurement;
- workflow routing and a hosted-capacity fallback;
- the repository-facing registration/supervision contract;
- liveness observation and the runner-binary freshness obligation;
- a live required-job exercise and evidence from the forge.

Homelab owns the host side. Thread 05 owns the physical server, installation admission, disk identity, credential transit, and operator closure. Thread 07 owns the NixOS build/CI substrate and host services. This thread supplies accepted properties and consumes their measured outputs; it does not contact, install, or mutate the Hetzner host and does not duplicate either homelab plan.

The archived `fabro-ci-image-factoring` / Phase-0 resident-pool design is historical input only. Its persistent shared-factory listeners conflict with v192's dedicated-host and one-job-registration requirements and must not be revived as the execution plan.

## Delivery shape

The fastest conforming shape is direct host execution under a dedicated unprivileged job identity. Container execution is optional and adds no delivery value unless a real workflow dependency requires it; if later used, it must be rootless, expose no daemon socket, and refuse privileged mode.

A separate supervising identity owns the credential that mints short-lived runner registrations. A job receives neither that credential nor fleet secrets. Each minted registration accepts at most one job, uses a fresh workspace, and deregisters after the job. The implementation must prove these properties from process, filesystem, and forge artifacts rather than infer them from a service's configured intent.

Only same-repository pull requests and protected-branch pushes may select the Hetzner label. Fork-originating, privileged, and stronger-secret jobs remain on hosted capacity. The GitHub fork-workflow approval setting must be observed at its strictest “all outside collaborators” tier before self-hosted gating is enabled.

Workflow routing must retain an operator-usable hosted fallback that does not require a specification revision. The concrete control should fail closed to `ubuntu-latest` when its self-hosted value is absent or disabled, be changeable without editing the accepted specification, and be covered by a mutation/control test so a missing runner cannot strand the sole required gate indefinitely.

The supervisor must expose a liveness signal that distinguishes “no registered runner is taking jobs” from an ordinary quiet queue. Because the NixOS runner package may disable agent self-update, the host realization must also refresh or prove the agent within GitHub's supported freshness window (30 days at the time of v192 planning, with critical updates potentially shortening it).

## Verification order

1. Re-read live ledger state in both repositories; do not treat archived plans or local branches as delivery.
2. Land the minimal Livespec workflow/policy/fallback changes once the host-side registration contract is concrete enough to name labels and identities without guessing.
3. Verify the host reports conforming liveness before routing a required gate to it.
4. Trigger exactly one necessary same-repository CI run and prove from the job metadata/log that a required job ran on the Hetzner runner.
5. Prove the one-job registration and workspace are gone after completion, and that the job could not read the minting credential or stronger fleet secrets.
6. Disable or withdraw self-hosted capacity through the retained fallback and prove the same required gate reports on GitHub-hosted capacity instead of queuing indefinitely.
7. Restore the intended self-hosted posture only after both paths are proven.

Hosted Actions quota is paid and scarce during this transition. Local controls must be exhausted before a push; each pushed change should carry all evidence its single run can provide. Do not rerun unchanged code.
