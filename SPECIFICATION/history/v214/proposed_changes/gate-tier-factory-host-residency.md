---
topic: gate-tier-factory-host-residency
author: claude-fable-5
created_at: 2026-08-23T10:45:00Z
---

## Proposal: Bound the privileged gate tier's residency on the shared factory host explicitly, instead of leaving it in conflict with an unconditional prohibition

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

§"Fleet CI execution posture" says the shared factory host MUST NOT carry a resident CI supervisor, UNCONDITIONALLY, and pre-refuses reinterpretation. `gate-runner-supervisor.service` — the deliberately-privileged, operator-triggered tier that mints one JIT runner per verified golden-master gate run for `livespec-orchestrator-beads-fabro` — is a resident CI supervisor, and it runs on that host. Measured 2026-08-23: `ActiveState=active`, under `ci-sup`, with its opt-in file `/run/livespec-local-ci-enabled` present since 2026-08-14. The Scope carve-out in §"Self-hosted CI runner host requirements" for that tier exempts it from three NAMED clauses of the following section and does not reach this prohibition. So the specification forbids a thing the fleet runs, has run for nine days, and provisions from the repository (`livespec-dev-tooling` `ci-runner/gate-runner/provision-gate-runner.sh`).

This amendment resolves the conflict by NAMING the gate tier as a bounded exception to the factory-host prohibition, on the prohibition's own stated grounds, with the compensating control and its expiry written down as obligations. It does NOT relax the prohibition for any pool, listener, liveness timer, or cache timer — the things the clause was written against — and it does not touch the "UNCONDITIONALLY" sentence's force for those.

### Motivation

Filed from `livespec-s43svm.43`. Two readings were open: (1) the clause means what it says and the tier relocates to a dedicated host; (2) carve the tier out explicitly. This proposal takes (2), and the reasoning is the clause's OWN reasoning:

The prohibition states why it exists: "co-residency with the Fabro, Dolt, and Dispatcher machinery — not self-hosted execution as such — is what made the earlier resident pool untenable." That is a contention argument about a POOL: 482 `runner@*` listeners, a replenisher loop, a cache-prune timer, all competing with the factory's own work on one host. The gate tier is none of those things. It is one supervisor process that polls for a queued gate run, mints ONE ephemeral JIT runner only when a trusted dispatch event arrives, waits for that one job, and repeats. Its containment boundary — per the Scope carve-out already ratified in §"Self-hosted CI runner host requirements" — is the trigger filter that decides whether compute is granted at all. Between runs it holds no runner, no container, no listener pool. During a run it starts ONE ephemeral `gate-runner@<name>.service` on the same host, as the operator identity, running a full orchestrator build and factory proof — a heavy job, but a single serial one, and one a fork cannot trigger. It runs on the factory host as an ELECTED TRADE-OFF, not a necessity: the gate is specified against the operator's own environment (secret wrapper, Codex credential, checkouts, pinned fabro), and a dedicated uncontained privileged host could carry all of that at the cost of duplicating it; `gate-runner@.service`'s own comment names that duplication as the cost being avoided. The proposal says so plainly rather than dressing the trade-off as an impossibility, because a clause that rests on a false necessity rots the first time someone reads it against the relocate option.

Relocating it (reading 1) would cost a second dedicated privileged host carrying a copy of the operator's environment, for one workflow in one repository — a workflow that, measured 2026-08-23, is `disabled_manually` and last ran 2026-07-14, so the supervisor has been resident nine days serving zero runs. That is a real cost for little gain in the property the clause protects, and reading 1 stays available: the new paragraph says it may be revised to require exactly that. But reading 2 done implicitly — by letting the conflict stand and the service keep running — is worse than either, because it leaves a ratified MUST NOT that the fleet violates by design, which trains every reader that UNCONDITIONAL does not mean unconditional.

So the exception is made EXPLICIT, and it is made NARROW: it names exactly one tier, binds it to the compensating control that already exists, and fixes the defect that control was found to have.

**The compensating control's defect, measured.** The gate supervisor is gated by a systemd drop-in, `hosted-only.conf`, carrying `ConditionPathExists=/run/livespec-local-ci-enabled`, described in its own comment as a "reboot-ephemeral operator opt-in". On 2026-08-22 that drop-in was found committed NOWHERE — it existed on one machine only, and re-provisioning from the repository would have installed the unit with `enable --now` and no gate. That half is fixed: `livespec-dev-tooling` PR #1615 (9c36ab7f) commits the drop-in and installs it from `provision-gate-runner.sh`. The other half is NOT fixed, and cannot be fixed by tooling alone: "reboot-ephemeral" is not a bound on a host with 44 days of uptime. The opt-in file was created 2026-08-14 03:10:51 and is still present, so the supervisor has been continuously active for nine days under an opt-in whose only expiry is a reboot nobody schedules. An opt-in without an expiry is an on switch. This proposal therefore obliges a wall-clock expiry WITH A CEILING (24 hours) and a no-silent-renewal rule, so the carve-out cannot become the resident posture by default. A bare "MUST have an expiry" would admit a one-year expiry, and a timer that re-touches the opt-in file would satisfy "has an expiry" forever; both holes are closed in the text.

**What is NOT claimed.** No claim that the gate tier's privilege model is wrong; that is governed by `livespec-orchestrator-beads-fabro`'s own specification per the existing carve-out. No claim that the factory host may carry any other CI process — the prohibition stands in full for pools, listeners, liveness timers, and cache timers. No claim about the `Execution-identity` / `Credential-separation` / `Event-routing` exemptions, which are unchanged.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, §"Fleet CI execution posture":

**1. Replace the whole paragraph beginning "**Fleet CI execution posture.**"** — that is, the entire single-line paragraph whose text is:

"**Fleet CI execution posture.** Every fleet repository's merge-gating CI MUST execute on GitHub-hosted runners, EXCEPT where it executes on a self-hosted host satisfying §"Self-hosted CI runner host requirements" in full. Routing a repository's gating jobs to a conforming host MUST NOT require a further specification revision. The shared factory host MUST NOT carry a resident CI supervisor, listener pool, runner-liveness timer, or runner-cache timer; that constraint holds UNCONDITIONALLY and independently of the execution posture in the preceding sentence, because co-residency with the Fabro, Dolt, and Dispatcher machinery — not self-hosted execution as such — is what made the earlier resident pool untenable, and a later change to the execution posture MUST NOT be read as relaxing it. Self-hosted CI capacity MUST therefore be separately provisioned on a host dedicated to carrying it. This rule does not disable the shared factory host's Fabro, Dolt, Dispatcher, or other factory machinery. A repository whose gating jobs name a self-hosted label while no conforming host is registered to serve them MUST route those jobs to hosted capacity rather than allow them to accumulate in a queue. This decision supersedes the local-hot-runner rollout recorded by `livespec-3lev` and its Phase 0/2/3 children."

**with these two paragraphs:**

"**Fleet CI execution posture.** Every fleet repository's merge-gating CI MUST execute on GitHub-hosted runners, EXCEPT where it executes on a self-hosted host satisfying §"Self-hosted CI runner host requirements" in full. Routing a repository's gating jobs to a conforming host MUST NOT require a further specification revision. The shared factory host MUST NOT carry a resident CI listener pool, runner-liveness timer, runner-cache timer, or any CI supervisor other than the single deliberately-privileged operator-triggered gate supervisor named in the next paragraph; that constraint holds UNCONDITIONALLY and independently of the execution posture in the preceding sentence, because co-residency with the Fabro, Dolt, and Dispatcher machinery — not self-hosted execution as such — is what made the earlier resident pool untenable, and a later change to the execution posture MUST NOT be read as relaxing it. All other self-hosted CI capacity MUST therefore be separately provisioned on a host dedicated to carrying it. This rule does not disable the shared factory host's Fabro, Dolt, Dispatcher, or other factory machinery. A repository whose gating jobs name a self-hosted label while no conforming host is registered to serve them MUST route those jobs to hosted capacity rather than allow them to accumulate in a queue. This decision supersedes the local-hot-runner rollout recorded by `livespec-3lev` and its Phase 0/2/3 children.

The one permitted resident is the deliberately-privileged, operator-triggered gate supervisor (the tier that §"Self-hosted CI runner host requirements" already names in its Scope clause), together with the single ephemeral gate runner it starts on the shared factory host for the duration of one verified run. It is permitted on the prohibition's own grounds: between runs nothing but the supervisor's poll loop is resident — no listener pool, no registration, no runner — and during a run it is one serial, operator-triggered, trigger-filtered job, torn down after that job, so it does not present the idle-listener co-residency load the prohibition exists to prevent. It runs on the shared factory host rather than a dedicated one as an ELECTED TRADE-OFF, not a necessity: its work is specified against the operator's own environment (secret wrapper, Codex credential, checkouts, pinned fabro), which the fleet chooses not to duplicate onto a second privileged host; a dedicated uncontained privileged host could carry it, at that duplication cost, and this paragraph may be revised to require exactly that. Its residency is bounded, not free. It MUST be gated behind an explicit operator opt-in that the provisioning path installs from the repository, so that re-provisioning the host converges to the GATED state and never to an auto-starting supervisor. That opt-in MUST carry a wall-clock expiry enforced on the host of no more than 24 hours from the opt-in's creation, and an opt-in MUST NOT be extended, renewed, or re-created by anything other than a fresh explicit operator act — because an opt-in that lapses only on reboot is not bounded on a long-uptime host, as the nine-day opt-in measured on 2026-08-23 showed, and an opt-in a timer could re-touch would never lapse at all. A gate supervisor found active with no opt-in present, or with an opt-in past its expiry, is a violation of this paragraph, not a configuration detail."

The replacement is the WHOLE paragraph, not one sentence, so that the paragraph's remaining sentences are carried explicitly and the one that would otherwise contradict the carve-out — "Self-hosted CI capacity MUST therefore be separately provisioned on a host dedicated to carrying it" — becomes "All OTHER self-hosted CI capacity MUST therefore …". Every other sentence of the original paragraph is preserved verbatim and in order.

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
