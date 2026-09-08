---
topic: delegated-gate-execution
author: opus-5
created_at: 2026-09-08T02:22:17Z
---

## Proposal: A delegated pre-push gate runs the same aggregate and refuses on an absent verdict

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Adds a Delegated gate execution clause to the Contracts section "Enforcement-suite invocation", permitting a repository's pre-push gate to execute on a remote executor while constraining that delegation: it MUST run the aggregate the local gate would have run for the same push and never a subset; the absence of a verdict MUST refuse the push; a target that degrades silently without a credential MUST fail rather than warn under delegation; and delegation MUST be per-repository opt-in and revocable to local execution without a specification revision. Adds two contributor-facing Gherkin scenarios to the Scenarios section covering the absent-verdict refusal and the credential-degradation failure.

### Motivation

The specification governs the pre-push gate as an invocation surface but assumes throughout that it executes on the pushing host. The livespec plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn) is building a delegation primitive whose client replaces the pre-push gate's fall-through with a verdict taken from a job on another host, so a verdict will shortly be able to arrive from somewhere the specification has never described. Two properties the fleet already relies on are silently at risk the moment that happens, and neither is written down.

The first is that the gate is not weakened by moving. The maintainer's direction for that plan was explicit that the gate moves WHERE it runs and not WHAT it runs, and that subsetting it was rejected, but that intent currently lives only in a plan research note and would not survive the note being archived.

The second is measured rather than hypothetical, and it fails toward a false green. The targets check-branch-protection-alignment and check-master-ci-green shell out to the forge CLI and exit zero with a structured warning when that CLI is unauthenticated. That is correct behavior at a developer's shell, where a person reads the warning. In a remote executor holding no forge credential it means the gate reports the tree green having skipped two checks the local gate runs authenticated, which is a subset masquerading as a pass and which no clause presently forbids. The same shape applies to any target that completes successfully while skipping the work it exists to do.

Stating these as properties now, before the client lands, keeps the delegation an execution-location change rather than an unreviewed weakening of the gate, and gives the implementation something to conform to rather than something to reconstruct.

### Proposed Changes

Two edits to `SPECIFICATION/non-functional-requirements.md`, both architecture rather than mechanism: the clause names no executor technology, no scheduler, and no transport, so any conforming realization satisfies it.

**Edit 1 — a new clause in the Contracts section `### Enforcement-suite invocation`.**

Insert the following paragraph immediately after the `**Invocation surfaces:**` bullet list, whose final entry reads verbatim:

`- **Manual (developer at the shell):** \`just <target>\` — same targets hooks and CI use.`

and immediately before the paragraph beginning `**Fleet CI execution posture.**`:

> **Delegated gate execution.** A repository's pre-push gate MAY execute on a remote executor rather than on the pushing host. Delegation changes WHERE the gate runs and MUST NOT change WHAT it runs: a delegated gate MUST execute the aggregate the local gate for that repository would have executed for the same push, selected through the same tracked inventory, and MUST NOT execute a subset of it. The ABSENCE of a verdict MUST refuse the push. A delegated gate that cannot be reached, cannot authenticate, is interrupted, or terminates without reporting an outcome has produced no verdict, and no reachable failure of the delegation path MUST be reported as a pass. A check target that DEGRADES SILENTLY when a credential it requires is absent — completing successfully while skipping the work it exists to perform — MUST fail rather than warn when it executes as part of a delegated gate, because the operator who would read the warning is not present to read it. Delegation MUST be opt-in per repository and MUST remain revocable to local execution without a specification revision, so that a remote executor is never a single point of failure for pushing.

Note for the reviewer on the first sentence's scope: it says the aggregate the LOCAL gate would have executed, deliberately, rather than the aggregate CI executes. A repository whose pre-push gate already omits a named world-gate member from the local aggregate keeps that omission under delegation; the clause forbids the delegated gate from omitting anything FURTHER, and does not silently re-litigate an existing local carve-out.

**Edit 2 — two scenarios in the `## Scenarios` section.**

Insert both immediately before the existing heading, which reads verbatim:

`### Scenario: An unavailable self-hosted host does not deadlock the merge gate`

Using that section's gherkin-blank-line convention (one step per paragraph, no fenced code blocks):

> ### Scenario: A delegated pre-push gate refuses the push when no verdict arrives
>
> Given a repository has opted in to executing its pre-push gate on a remote executor
>
> When the gate is dispatched and the executor becomes unreachable before reporting an outcome
>
> Then the push is refused
>
> And no marker recording the tree as having passed the gate is written
>
> And the refusal names the absent verdict rather than reporting a failing check

> ### Scenario: A delegated gate fails a credential-degraded target rather than warning
>
> Given a check target completes successfully with a warning when a credential it requires is absent
>
> And a repository has opted in to executing its pre-push gate on a remote executor
>
> When that target executes as part of the delegated gate without that credential
>
> Then the target fails
>
> And the delegated gate produces no passing verdict for that push

Both scenarios are `###` headings inside `non-functional-requirements.md`'s own `## Scenarios` section, matching the three CI-host scenarios already there, so no `tests/heading-coverage.json` entry is owed: that map covers `## ` headings, and the existing `### Scenario:` entries in this file carry none.

Placement rationale under the Boundary litmus: a delegated pre-push gate is livespec's own contributor infrastructure and is not inherited by a project merely governed by livespec, so it belongs in `non-functional-requirements.md` rather than `spec.md`, `contracts.md`, or `constraints.md` — and specifically in `### Enforcement-suite invocation`, which already declares the suite invocation-surface-agnostic and enumerates pre-push among its consumers.
