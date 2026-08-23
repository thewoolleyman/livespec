---
topic: gate-tier-factory-host-residency
author: claude-fable-5
created_at: 2026-08-23T10:45:00Z
---

## Proposal: Bound the privileged gate tier's residency on the shared factory host explicitly, instead of leaving it in conflict with an unconditional prohibition

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

§"Fleet CI execution posture" says the shared factory host MUST NOT carry a resident CI supervisor, UNCONDITIONALLY, and pre-refuses reinterpretation. `gate-runner-supervisor.service` — the deliberately-privileged, operator-triggered tier that mints one JIT runner per verified golden-master gate run for `livespec-orchestrator-beads-fabro` — is a resident CI supervisor, and it runs on that host. Measured 2026-08-23: `ActiveState=active`, under `ci-sup`, with its opt-in file `/run/livespec-local-ci-enabled` present since 2026-08-14. The §"Scope" carve-out for that tier exempts it from three NAMED clauses of the following section and does not reach this prohibition. So the specification forbids a thing the fleet runs, has run for nine days, and provisions from the repository (`livespec-dev-tooling` `ci-runner/gate-runner/provision-gate-runner.sh`).

This amendment resolves the conflict by NAMING the gate tier as a bounded exception to the factory-host prohibition, on the prohibition's own stated grounds, with the compensating control and its expiry written down as obligations. It does NOT relax the prohibition for any pool, listener, liveness timer, or cache timer — the things the clause was written against — and it does not touch the "UNCONDITIONALLY" sentence's force for those.

### Motivation

Filed from `livespec-s43svm.43`. Two readings were open: (1) the clause means what it says and the tier relocates to a dedicated host; (2) carve the tier out explicitly. This proposal takes (2), and the reasoning is the clause's OWN reasoning:

The prohibition states why it exists: "co-residency with the Fabro, Dolt, and Dispatcher machinery — not self-hosted execution as such — is what made the earlier resident pool untenable." That is a contention argument about a POOL: 482 `runner@*` listeners, a replenisher loop, a cache-prune timer, all competing with the factory's own work on one host. The gate tier is none of those things. It is one supervisor process that polls for a queued gate run, mints ONE ephemeral JIT runner only when a trusted dispatch event arrives, waits for that one job, and repeats. Its containment boundary — per the §"Scope" carve-out already ratified — is the trigger filter that decides whether compute is granted at all. Between runs it holds no runner, no container, no listener pool. During a run it starts ONE ephemeral `gate-runner@<name>.service` on the same host, as the operator identity, because the gate's work needs the host-resident Codex subscription credential that a stock hosted runner cannot hold — which is the whole reason this tier exists.

Relocating it (reading 1) would cost a second dedicated host for one workflow in one repository, to satisfy a clause whose stated rationale does not describe the thing being relocated. That is a real cost for no gain in the property the clause protects. But reading 2 done implicitly — by letting the conflict stand and the service keep running — is worse than either, because it leaves a ratified MUST NOT that the fleet violates by design, which trains every reader that UNCONDITIONAL does not mean unconditional.

So the exception is made EXPLICIT, and it is made NARROW: it names exactly one tier, binds it to the compensating control that already exists, and fixes the defect that control was found to have.

**The compensating control's defect, measured.** The gate supervisor is gated by a systemd drop-in, `hosted-only.conf`, carrying `ConditionPathExists=/run/livespec-local-ci-enabled`, described in its own comment as a "reboot-ephemeral operator opt-in". On 2026-08-22 that drop-in was found committed NOWHERE — it existed on one machine only, and re-provisioning from the repository would have installed the unit with `enable --now` and no gate. That half is fixed: `livespec-dev-tooling` PR #1615 (9c36ab7f) commits the drop-in and installs it from `provision-gate-runner.sh`. The other half is NOT fixed, and cannot be fixed by tooling alone: "reboot-ephemeral" is not a bound on a host with 44 days of uptime. The opt-in file was created 2026-08-14 03:10:51 and is still present, so the supervisor has been continuously active for nine days under an opt-in whose only expiry is a reboot nobody schedules. An opt-in without an expiry is an on switch. This proposal therefore obliges a wall-clock expiry, so the carve-out cannot become the resident posture by default.

**What is NOT claimed.** No claim that the gate tier's privilege model is wrong; that is governed by `livespec-orchestrator-beads-fabro`'s own specification per the existing carve-out. No claim that the factory host may carry any other CI process — the prohibition stands in full for pools, listeners, liveness timers, and cache timers. No claim about the `Execution-identity` / `Credential-separation` / `Event-routing` exemptions, which are unchanged.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, §"Fleet CI execution posture":

**1. Replace the sentence:**

"The shared factory host MUST NOT carry a resident CI supervisor, listener pool, runner-liveness timer, or runner-cache timer; that constraint holds UNCONDITIONALLY and independently of the execution posture in the preceding sentence, because co-residency with the Fabro, Dolt, and Dispatcher machinery — not self-hosted execution as such — is what made the earlier resident pool untenable, and a later change to the execution posture MUST NOT be read as relaxing it."

**with:**

"The shared factory host MUST NOT carry a resident CI listener pool, runner-liveness timer, runner-cache timer, or any CI supervisor other than the single deliberately-privileged operator-triggered gate supervisor named in the next paragraph; that constraint holds UNCONDITIONALLY and independently of the execution posture in the preceding sentence, because co-residency with the Fabro, Dolt, and Dispatcher machinery — not self-hosted execution as such — is what made the earlier resident pool untenable, and a later change to the execution posture MUST NOT be read as relaxing it.

The one permitted resident is the deliberately-privileged, operator-triggered gate supervisor (the tier §"Self-hosted CI runner host requirements" §"Scope" already names), together with the single ephemeral gate runner it starts on the same host for the duration of one verified run. It is permitted on the prohibition's own grounds: it holds no listener pool and no runner between runs, minting one ephemeral registration only when a trusted dispatch event arrives and tearing it down after that one job, so it does not present the co-residency load the prohibition exists to prevent; and it runs on this host rather than a dedicated one because its work needs a host-resident operator credential that no hosted or contained runner can carry, which is the property that defines the tier. Its residency is bounded, not free. It MUST be gated behind an explicit operator opt-in that the provisioning path installs from the repository, so that re-provisioning the host converges to the GATED state and never to an auto-starting supervisor; and that opt-in MUST carry a wall-clock expiry enforced on the host, because an opt-in that lapses only on reboot is not bounded on a long-uptime host — measured on 2026-08-23, one had stood open for nine days. A gate supervisor found active with no opt-in present, or with an opt-in past its expiry, is a violation of this paragraph, not a configuration detail."

**2. Amend the two scenarios in the same section that assert the absence.** Each currently reads as though NO CI process of any kind may be resident, and after change 1 that is no longer what the clause says during a gate run.

In "### Scenario: A fleet pull request uses hosted CI without occupying the factory host", replace the step:

"And no CI listener or worker process is resident on the shared factory host"

with:

"And no CI listener pool, runner-liveness timer, or runner-cache timer is resident on the shared factory host, and no CI worker process is resident there other than a single ephemeral gate runner during one verified operator-triggered run"

In "### Scenario: A conforming self-hosted host carries a fleet gate without host-wide privilege", replace the step:

"And the shared factory host carries no CI listener or worker process"

with:

"And the shared factory host carries no CI listener pool, runner-liveness timer, runner-cache timer, or CI worker process other than a single ephemeral gate runner during one verified operator-triggered run"

These are `And` steps inside existing `### Scenario` H3 headings; no `## ` heading is added, removed, or renamed, so `tests/heading-coverage.json` needs no co-edit. Reviewers should confirm the scenario heading names above against the live file rather than trusting this text — they are quoted from origin/master 13257aee, lines 1354 and 1366.
