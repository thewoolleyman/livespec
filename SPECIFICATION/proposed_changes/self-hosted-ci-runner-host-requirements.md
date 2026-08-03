---
topic: self-hosted-ci-runner-host-requirements
author: claude-opus-5
created_at: 2026-08-03T07:52:38Z
---

## Proposal: Self-hosted CI runner host requirements, stated as host-observable properties

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a new `### Self-hosted CI runner host requirements` subsection under `## Contracts` in `non-functional-requirements.md`, immediately after `### Enforcement-suite invocation`, defining what a host MUST provide before any livespec-governed repository's CI may execute on it. Every requirement is stated as a host-observable PROPERTY rather than as a package, unit, or distribution mechanism, so a provisioning repository (the fleet's own hosts are provisioned from `homelab`) owns the realization and a non-FHS distribution such as NixOS can satisfy the same contract by its own native means. The containment floor is deliberately REDUCED relative to a public-fork threat model, and this section makes that reduction conditional on a stated fork-exclusion precondition rather than leaving it as unrecorded rationale.

### Motivation

Two forces converge. First, GitHub Actions billed quota is now a real cost, and the fleet wants to move gating CI onto homelab capacity — starting with the Hetzner NixOS member specified by `homelab`'s thread 05, with thread 07 separately planning a self-hosted builder on the same host. Second, `non-functional-requirements.md` §"Enforcement-suite invocation" already anticipates exactly this: its **GitHub-hosted-only fleet posture** paragraph states that "Reactivating fleet self-hosted CI requires a later spec revision and separately provisioned capacity." Nothing in the specification currently says WHAT that capacity must provide, so a provisioning engineer has no contract to build against.

The naive assumption — that a runner host needs only Docker plus the runner agent — is wrong in both directions, which is why the requirement set is worth stating explicitly rather than leaving to discovery.

It is too small in one direction. The agent is a .NET application that dynamically links a Kerberos library, zlib, LTTng-UST, OpenSSL 3, and ICU (the authoritative list is the runner's own `bin/installdependencies.sh`). Jobs additionally need `git`, `tar`, `gzip`, `curl`, and a JavaScript runtime for JavaScript actions, plus this fleet's pinned contributor toolchain. And on a non-FHS distribution the published runner archive does not execute at all: NixOS is absent from GitHub's supported-distribution list, its filesystem layout does not satisfy the archive's interpreter and library paths, and the working path is a distribution-native build of the agent. An engineer who unpacks the archive on NixOS and reads the resulting failure as a host defect rather than a packaging mismatch loses time to a diagnosis the specification can prevent in one sentence.

It is too large in the other direction. Docker is not required at all unless workflows use container actions or service containers — and on this fleet's hosts, membership in a container-daemon group is root-equivalent, so granting it as a convenience would hand any job full host control. The requirement is therefore stated as a prohibition on that group membership plus an OPTIONAL rootless path, not as a Docker dependency.

The reduced containment floor is a maintainer decision (2026-08-03) with an explicit rationale: the fleet does not accept fork pull requests, so the fork-code-execution vector the full Phase 0 containment design was built against is not live, and getting runners serving the maintainer alone is the overriding goal. That decision is sound only while its premise holds, which is why the fork-exclusion precondition is written as a binding condition rather than as a footnote — a premise that lives only in rationale expires silently the first time someone approves a fork pull request, and the specification would then be asserting a containment floor that no longer matches the threat model.

Placement follows the §"Boundary" litmus: a project merely governed by livespec does not inherit livespec's CI host provisioning, so this is contributor-facing infrastructure and belongs in `non-functional-requirements.md` §"Contracts" — the analogue of `contracts.md`'s role for the user-facing surface — rather than in `contracts.md` or `constraints.md`, which govern the user-facing product surface (wrapper CLIs, exit codes, templates, plugin distribution). Cross-repo placement follows the same split: the requirements a host must MEET are a fleet-level fact owned by core, while the NixOS modules, packages, and units that MEET them are realization owned by `homelab`.

Scope notes for the reviser, not text to ratify. (a) This proposal adds `###` headings only, under the existing `## Contracts` and `## Scenarios` H2 headings; `tests/heading-coverage.json` tracks `## ` headings exclusively and already carries all five of this file's H2 entries, so NO heading-coverage co-edit is owed. (b) The full Phase 0 containment design (rootless user-namespaced execution, host-loopback denial, agent/job PID-namespace separation, the eleven isolation exit tests) is deliberately NOT ratified here; it remains recorded in `livespec`'s `plan/archive/fabro-ci-image-factoring/phase0-runner-containment-design.md` and implemented in `livespec-dev-tooling/ci-runner/`, and the fork-exclusion precondition names the condition under which it must be re-established. (c) The drift surface for the companion posture amendment is exactly two sites in this file (the posture paragraph and one scenario Given); both are handled in the companion findings of this same proposal.

### Proposed Changes

In `non-functional-requirements.md`, under `## Contracts`, insert a new subsection `### Self-hosted CI runner host requirements` immediately AFTER the existing `### Enforcement-suite invocation` subsection and BEFORE `### CI telemetry export`, with the following content.

---

### Self-hosted CI runner host requirements

This section defines what a host MUST provide before any livespec-governed repository's CI may execute on it. Every requirement is stated as a host-observable PROPERTY, never as a package name, service unit, or distribution mechanism: realization is owned by whichever repository provisions the host (the fleet's own hosts are provisioned from `homelab`), and a host whose distribution differs from the fleet's development hosts MUST be free to satisfy each property by its own native means.

**Fork-exclusion precondition.** The containment floor below is REDUCED relative to a public-fork threat model, and that reduction is CONDITIONAL. Self-hosted capacity MAY carry a repository's merge gate ONLY while no workflow originating from a fork of that repository can execute on it. That exclusion MUST be enforced by the repository's fork-pull-request workflow-approval setting rather than by author vigilance. A repository that begins accepting fork pull requests MUST either return its gating jobs to hosted capacity or first re-establish a containment floor adequate to running untrusted code — approving a fork pull request while self-hosted CI is active executes fork-controlled code on the host. Maintainer-declared 2026-08-03.

**Platform.** A conforming host MUST be x86_64 Linux with systemd and cgroups v2. The fleet's pinned toolchain and container images are x86_64; a host of another architecture is out of contract for fleet CI until the fleet publishes images for that architecture.

**Runner agent runtime.** The host MUST be able to execute the GitHub Actions runner agent under its own operating system. The agent is a .NET application and MUST find, at run time, a Kerberos library, zlib, LTTng-UST, OpenSSL 3, and ICU. A host whose filesystem layout the published runner archive does not target — any non-FHS distribution — MUST supply a distribution-native build of the agent instead of unpacking that archive; such a host MUST NOT be diagnosed as defective when the archive fails to launch, because the failure is a packaging mismatch rather than a host fault.

**Workflow runtime.** `git`, `tar`, `gzip`, `curl`, and a JavaScript runtime for JavaScript actions MUST be resolvable by the runner identity. The pinned contributor toolchain of §"Toolchain pins" MUST likewise be resolvable at its pinned versions: a self-hosted host is NOT exempt from those pins, and a check MUST NOT be satisfied by a differently-versioned host tool.

**Network.** The host MUST be able to open outbound HTTPS connections on port 443 to the runner control plane, the action-download endpoint, the artifact/cache/log-receiver endpoint, the agent-self-update endpoint, and — where jobs pull images — the container-registry endpoint. The host MUST NOT require inbound reachability from the forge; the agent establishes every connection outbound. This clause deliberately states endpoint CLASSES rather than a hostname list, because the forge's published hostnames change without notice and a copied list would rot into a false constraint.

**Execution identity.** The agent MUST run under a dedicated unprivileged service identity that holds no administrative escalation and is NOT a member of any group conferring root-equivalent control of a container daemon. Such membership is equivalent to host root and MUST NOT be granted as a convenience, including to make containerized jobs work.

**Ephemeral registration.** Each runner registration MUST serve at most one job and MUST deregister afterwards, and a job MUST NOT be able to observe a previous job's workspace. This bounds both state bleed between jobs and the value of a captured registration.

**Credential separation.** The credential that mints runner registrations MUST be readable only by the supervising identity and MUST NOT be readable from a job. No fleet secret beyond a least-privilege, read-scoped forge token for the run MUST be injected into a self-hosted job's environment; a check that genuinely requires a stronger credential MUST remain on hosted capacity.

**Event routing.** Self-hosted capacity MUST be reachable only from same-repository pull-request events and from pushes to a protected branch. Trigger classes a non-collaborator can reach, and privileged trigger classes that check out or interpret externally-supplied content, MUST remain on hosted capacity.

**Containerized job execution is OPTIONAL.** Running jobs directly on the host under the execution identity above is conforming, and is the simplest conforming shape. A host that DOES run jobs in containers MUST use a rootless engine: the in-container root identity MUST map to a non-root host identity, no host container-daemon socket MUST be exposed into a job, and privileged mode MUST be refused. A host that offers only a root-equivalent container daemon MUST run jobs directly rather than in containers.

**Availability MUST NOT become a merge dependency.** Because §"CI as a merge gate (branch protection)" makes a single all-green gate the sole required check, an unreachable self-hosted host would otherwise block every merge in that repository indefinitely. A repository routing gating jobs to self-hosted capacity MUST therefore retain a route returning those jobs to hosted capacity that requires no specification revision to take, and the fleet MUST be able to observe that a registered host has stopped taking jobs rather than inferring it from jobs accumulating in a queue.

## Proposal: Replace the GitHub-hosted-only fleet posture with a conditional fleet CI execution posture

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Replace the **GitHub-hosted-only fleet posture** paragraph in `non-functional-requirements.md` §"Enforcement-suite invocation" with a **Fleet CI execution posture** paragraph that permits execution on a host satisfying §"Self-hosted CI runner host requirements" while retaining unconditionally the one constraint that actually caused the earlier reversal — no resident CI capacity on the shared factory host. The new paragraph declares itself to BE the reactivation revision the superseded paragraph required, so routing a repository's gate to a conforming host needs no further specification cycle. The one scenario Given that references the retired posture by name is amended in the same change so no unamended statement is left dangling.

### Motivation

The superseded paragraph names its own exit condition: "Reactivating fleet self-hosted CI requires a later spec revision and separately provisioned capacity, rather than an implicit repository-variable deletion or service restart." Leaving that clause in place while separately publishing host requirements would produce a specification that describes capacity nobody is permitted to use — and would force a second revision cycle at exactly the moment the first homelab host comes up, against a maintainer goal of getting runners serving as soon and as simply as possible. Satisfying the clause on its own terms means this revision IS the reactivation revision, and saying so in the text removes the ambiguity about whether a further cycle is owed.

What must NOT be relaxed is the constraint that produced the original reversal. The ratified record for that decision (`SPECIFICATION/history/v189/proposed_changes/github-hosted-ci-posture.md`) states the cause precisely: the shared factory host became overloaded, carrying 48 idle listeners across eight repositories even while ordinary CI already ran on hosted capacity. That failure was caused by CO-RESIDENCY with the Fabro, Dolt, and Dispatcher machinery, not by self-hosted execution as such. So the correct amendment separates the two rules that the original paragraph fused: self-hosted execution becomes conditionally permitted, while "no resident CI capacity on the shared factory host" is retained unconditionally and restated as independent of the posture, so a later posture change cannot silently take it with it. Requiring that self-hosted capacity be separately provisioned on a host dedicated to it is the positive form of the same rule, and it is exactly what the homelab fleet members are.

The superseded paragraph also carried a queue-safety rule — "Self-hosted-only auxiliary workflows remain administratively disabled instead of accumulating queued jobs" — whose motivation survives the posture change and whose form does not. Under the new posture the hazard is not an auxiliary workflow left enabled, but a repository whose gating jobs name a self-hosted label with no conforming host registered for them. The replacement states that hazard directly.

Drift sweep: `self-hosted`, `hosted-only`, and `livespec-3lev` were swept across the live spec tree. Exactly two sites reference the posture — the paragraph replaced here and the Given step of §"Scenario: A fleet pull request uses hosted CI without occupying the factory host", which reads "a fleet repository whose hosted-only posture is active". That phrase names a posture this change retires, so it is amended here rather than left to rot; the scenario's remaining steps continue to assert the factory-host constraint, which is retained, so the scenario stays true and keeps earning its place.

### Proposed Changes

**(a) Replace the posture paragraph.** In `non-functional-requirements.md` §"Enforcement-suite invocation", the paragraph beginning

```
**GitHub-hosted-only fleet posture.** While this posture is active, every fleet repository's merge-gating CI executes on GitHub-hosted runners
```

and ending

```
for the duration of this posture.
```

MUST be replaced in full by:

---

**Fleet CI execution posture.** Every fleet repository's merge-gating CI MUST execute on GitHub-hosted runners, EXCEPT where it executes on a self-hosted host satisfying §"Self-hosted CI runner host requirements" in full. This section IS the reactivation revision the superseded GitHub-hosted-only posture required, so routing a repository's gating jobs to a conforming host MUST NOT require any further specification revision.

The shared factory host MUST NOT carry a resident CI supervisor, listener pool, runner-liveness timer, or runner-cache timer. That constraint is retained UNCONDITIONALLY and holds independently of the execution posture above: co-residency with the Fabro, Dolt, and Dispatcher machinery is what made the earlier resident pool untenable — 48 idle listeners across eight repositories while ordinary CI already ran hosted — and a later change to the execution posture MUST NOT be read as relaxing it. Self-hosted CI capacity MUST therefore be separately provisioned on a host dedicated to carrying it. This rule does not disable the shared factory host's Fabro, Dolt, Dispatcher, or other factory machinery.

A repository whose gating jobs name a self-hosted label while no conforming host is registered to serve them MUST route those jobs to hosted capacity rather than allow them to accumulate in a queue.

This decision supersedes the local-hot-runner rollout recorded by `livespec-3lev` and its Phase 0/2/3 children.

---

**(b) Amend the dangling scenario Given.** In §"Scenario: A fleet pull request uses hosted CI without occupying the factory host" under `## Scenarios`, the Given step

```
Given a pull request targets a fleet repository whose hosted-only posture is active
```

MUST be replaced by

```
Given a pull request targets a fleet repository whose gating jobs route to hosted capacity
```

so that no step names a posture this change retires. Every other step of that scenario MUST be left unchanged: they assert the factory-host constraint, which is retained unconditionally.

## Proposal: Scenarios covering conforming self-hosted execution and the merge-gate availability rule

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add two contributor-facing Gherkin scenarios under `## Scenarios` in `non-functional-requirements.md`: one proving that a conforming self-hosted host carries a fleet gate without host-wide privilege, ephemeral-registration reuse, or fleet-secret exposure; and one proving that an unavailable self-hosted host does not deadlock the merge gate. Both are placed adjacent to the existing hosted-capacity scenario so the three read as one set.

### Motivation

The authoring discipline for this specification requires that load-bearing behavior be stated as a BCP14 clause AND have a Given/When/Then scenario, with prose only augmenting the pair. The companion findings introduce two behaviors that meet that bar and would otherwise be carried by prose alone.

The first is the conforming-execution invariant. Its clauses — unprivileged identity with no root-equivalent container-daemon access, one job per registration, no fleet secret in the job environment beyond a read-scoped run token — are exactly the properties a provisioning engineer needs to be able to check on a finished host, and a scenario states them as an observable outcome rather than a provisioning checklist.

The second is the availability rule, which is the one clause in the new section whose violation is silent. Because §"CI as a merge gate (branch protection)" makes a single all-green gate the sole required check, a self-hosted host that stops taking jobs does not fail anything — it simply never reports, and every merge in that repository waits forever on a check that will not arrive. That is precisely the shape the superseded posture was guarding against with its "instead of accumulating queued jobs" clause. A scenario makes the required behavior — observing that the host stopped, and returning the jobs to hosted capacity without a specification revision — testable rather than aspirational.

Both scenarios follow the gherkin-blank-line convention stated at the head of `## Scenarios`: one step per paragraph, no fenced code blocks. Neither adds a `## ` heading, so no `tests/heading-coverage.json` co-edit is owed.

### Proposed Changes

In `non-functional-requirements.md` under `## Scenarios`, the following two scenarios MUST be added immediately after the existing §"Scenario: A fleet pull request uses hosted CI without occupying the factory host" and before §"Scenario: GitHub App budget exhaustion remains diagnosable after refill". Each step MUST be its own paragraph per the gherkin-blank-line convention stated at the head of that section, and neither scenario MUST be written with fenced code blocks.

---

### Scenario: A conforming self-hosted host carries a fleet gate without host-wide privilege

Given a self-hosted host satisfies the self-hosted CI runner host requirements

And no workflow originating from a fork of the repository can execute on that host

When a fleet repository routes its merge-gating jobs to that host

Then each job runs under a dedicated unprivileged identity holding no root-equivalent container-daemon access

And each runner registration serves one job and then deregisters

And no fleet secret beyond a least-privilege read-scoped run token is present in the job environment

And the shared factory host carries no CI listener or worker process

### Scenario: An unavailable self-hosted host does not deadlock the merge gate

Given a fleet repository routes its merge-gating jobs to a self-hosted host

When that host stops taking jobs

Then the fleet observes that the host stopped taking jobs rather than inferring it from an accumulating queue

And the repository returns those gating jobs to hosted capacity without a specification revision

And the repository's single all-green gate can report again
