---
topic: delegated-gate-execution
author: opus-5
created_at: 2026-09-08T02:22:17Z
---

## Proposal: A delegated pre-push gate verifies the pushed tree, runs the same set, and refuses without a verdict

### Target specification files

SPECIFICATION/non-functional-requirements.md

### Summary

Adds a Delegated gate execution clause to the Contracts section "Enforcement-suite invocation", permitting a repository's pre-push gate to execute on a remote executor and constraining that delegation as a property of the VERDICT the executor returns rather than of any individual check target. The verdict must be produced against the exact tree being pushed; the delegated gate must run the same set of checks the local gate would have run, neither fewer nor more; a verdict exists only when the delegated gate reported its own completion status for that push, and every other condition is an absent verdict that refuses the push and is distinguishable from a failure; a check that reports success without performing its verification must not contribute to a passing verdict, and one the executor cannot be equipped to perform runs locally instead rather than by widening a credential's scope; a marker recording a tree as passed must not be written from a non-conforming verdict and must record what produced it; and a push must always be able to run its gate locally. Amends the one existing bullet that states the pushing-host assumption, and adds three contributor-facing Gherkin scenarios.

### Motivation

The specification governs the pre-push gate as an invocation surface but assumes throughout that it executes on the pushing host. The livespec plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn) is building a delegation primitive whose client replaces the pre-push gate's fall-through with a verdict taken from a job on another host, so a verdict will shortly be able to arrive from somewhere the specification has never described.

The properties that make such a verdict trustworthy currently live only in that plan's research notes, which is the precise failure mode this proposal exists to prevent: a research note is archived when its plan closes, and the guarantees it carried leave with it.

Three of those properties are load-bearing and none is written down.

The first is tree identity. Nothing today would stop a delegated gate from running a full, honest aggregate against a stale mirror or a branch tip and returning a green verdict that authorizes pushing entirely different content. The plan's design solves this outside the specification, by naming the served ref after the pushed tree's hash so that one value identifies the tree, the ref, and the marker. That is exactly the kind of guarantee that must be in the clause rather than in a note.

The second is that the gate is not weakened by moving. The maintainer's direction for that plan was explicit that the gate moves WHERE it runs and not WHAT it runs, and that subsetting it was rejected.

The third is measured rather than hypothetical, and it fails toward a false green. Several check targets report success while skipping the work they exist to do when they cannot reach a forge credential. The two most prominent exit zero with a structured warning; a third logs only at info, and is quieter still. The degradation is not always a credential being ABSENT: the documented path for the branch-protection check is a credential that is PRESENT and too narrowly scoped, which is precisely the configuration a least-privilege gate pod would have. So a delegated gate could report a tree green having silently skipped checks the local gate performs, and keying the rule on absence would not catch the case the plan is actually about to build.

Stating these as properties now, before the client lands, keeps the delegation an execution-location change rather than an unreviewed weakening of the gate, and gives the implementation something to conform to rather than something to reconstruct.

### Proposed Changes

Three edits to `SPECIFICATION/non-functional-requirements.md`. All are architecture rather than mechanism: no executor technology, scheduler, or transport is named, and every requirement is stated about the delegated VERDICT rather than about the internals of any check target.

**Edit 1 — amend the one bullet that states the pushing-host assumption.**

In the `**Invocation surfaces:**` list of `### Enforcement-suite invocation`, replace this line verbatim:

```text
- **Pre-commit and pre-push (local):** `lefthook.yml` runs `just check`.
```

with:

```text
- **Pre-commit and pre-push (hook):** `lefthook.yml` runs the repository's gate recipe, which runs `just check` on the pushing host unless that repository has delegated its pre-push gate per **Delegated gate execution** below.
```

This edit is the point of the proposal's own motivation: that bullet is the single place the specification states the assumption the new clause removes, and leaving it would ratify a contradiction two lines above the new text.

**Edit 2 — the new clause.**

Insert immediately after that amended bullet list, and immediately before the paragraph beginning `**Fleet CI execution posture.**`:

> **Delegated gate execution.** A repository's pre-push gate MAY execute on a remote executor rather than on the pushing host. Delegation changes WHERE the gate runs and MUST NOT change WHAT it verifies. Every requirement below is a property of the VERDICT the executor returns, not of any individual check target's internals.
>
> *The tree.* A delegated verdict MUST be produced against the exact source tree being pushed. A verdict produced against any other content — a stale mirror, a branch tip, a previously fetched revision — MUST NOT authorize that push and MUST be treated as an absent verdict under the refusal rule below.
>
> *The set.* A delegated gate MUST execute the same set of checks the repository's local gate would have executed for that push: neither fewer, so that delegation cannot weaken the gate, nor more, so that delegation cannot refuse a push over a check the local gate never ran. A repository whose local gate omits a member keeps that omission under delegation.
>
> *The verdict.* A verdict EXISTS only when the delegated gate itself reported its own completion status for that push. Every other condition is an ABSENT verdict — including an executor that could not be reached or authenticated, a transport that reported its own success without carrying the gate's completion status, a process terminated by signal, and any result read from a store rather than produced for this push. An absent verdict MUST refuse the push, and MUST be distinguishable from a verdict of failure, so that a broken delegation is never reported as a failing repository.
>
> *Degraded checks.* A check that reports success without performing the verification it exists to perform MUST NOT contribute to a passing delegated verdict, for any credential reason — absent, rejected, or too narrowly scoped to complete the check. A check the delegated executor cannot be equipped to perform MUST instead be executed on the pushing host. This clause MUST NOT be satisfied by widening a credential's scope on a remote executor, and a remote executor sharing a host with capacity bound by §"Self-hosted CI runner host requirements" remains bound by that section's Credential-separation clause.
>
> *The marker.* A marker recording a tree as having passed the gate MUST NOT be written from a verdict that does not satisfy this clause in full, and MUST record what produced it, so that withdrawing delegation invalidates the markers delegation produced.
>
> *Withdrawal.* Delegation MUST be opt-in, and a push MUST be able to run its gate on the pushing host regardless of that opt-in, so that a remote executor is never a single point of failure for pushing.

**Edit 3 — three scenarios in the `## Scenarios` section.**

Insert all three immediately before the existing heading, which reads verbatim:

```text
### Scenario: An unavailable self-hosted host does not deadlock the merge gate
```

Using that section's gherkin-blank-line convention (one step per paragraph, no fenced code blocks):

> ### Scenario: A delegated gate verdict does not authorize a tree it was not produced against
>
> Given a repository has delegated its pre-push gate to a remote executor
>
> When the executor returns a passing verdict produced against content other than the tree being pushed
>
> Then the push is refused
>
> And the verdict is treated as absent rather than as a pass
>
> And no marker recording the pushed tree as having passed the gate is written

> ### Scenario: A delegated pre-push gate refuses the push when no verdict arrives
>
> Given a repository has delegated its pre-push gate to a remote executor
>
> When the transport reports success without carrying the gate's completion status
>
> Then the push is refused
>
> And no marker recording the tree as having passed the gate is written
>
> And the refusal names the absent verdict rather than reporting a failing check

> ### Scenario: A delegated gate does not pass on a check that skipped its own verification
>
> Given a check target reports success without performing its verification when its credential is too narrowly scoped
>
> And a repository has delegated its pre-push gate to a remote executor holding only a least-privilege credential
>
> When that target runs as part of the delegated gate
>
> Then the delegated verdict does not pass
>
> And the target is executed on the pushing host instead, rather than the executor's credential being widened

**On the registry obligations this change carries.** No `tests/heading-coverage.json` entry is owed: that map's heading direction covers `## ` headings, all three scenarios are `###` headings inside this file's existing `## Scenarios` section, and none of that section's sixteen current `### Scenario:` headings carries an entry. Stated precisely, because an adjacent obligation in the same registry file should not go unmentioned: the new normative sentences DO add behavior clauses to a file that the `behavior_scenario_link` check treats as a clause source, and that check wants each clause linked to a `scenarios.md` H2 section, which a contributor-facing `###` scenario structurally cannot be. Those clauses therefore join that check's existing warn-mode backlog, which already holds several hundred unlinked clauses for this file (306 measured 2026-09-08, against 505 across the four clause-source files). They do not create the backlog and do not change the lever's severity, but the honest statement is that they join it rather than that nothing is owed.

**Placement rationale** under the Boundary litmus: a delegated pre-push gate is livespec's own contributor infrastructure and is not inherited by a project merely governed by livespec, so it belongs in `non-functional-requirements.md` rather than `spec.md`, `contracts.md`, or `constraints.md` — and specifically in `### Enforcement-suite invocation`, which already declares the suite invocation-surface-agnostic and enumerates pre-push among its consumers.

**On the aggregate's reference point.** *The set* binds to what the LOCAL gate would have run, not to what CI runs. This is deliberate: one fleet repository's pre-push recipe already omits a single admin-scoped member that its CI matrix also omits, and binding to CI's set would have silently outlawed that existing carve-out, while binding to a literal full aggregate would make that repository's delegated gate run a superset it cannot satisfy and refuse every delegated push.
