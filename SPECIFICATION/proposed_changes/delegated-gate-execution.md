---
topic: delegated-gate-execution
author: opus-5
created_at: 2026-09-08T02:22:17Z
---

## Proposal: A delegated pre-push gate verifies the pushed tree, runs the same set, and refuses without a verdict

### Target specification files

SPECIFICATION/non-functional-requirements.md

### Summary

Adds a Delegated gate execution clause to the Contracts section "Enforcement-suite invocation", permitting a repository's pre-push gate to execute on a remote executor and constraining that delegation as a property of the delegation — the verdict, the executor, and the pushing host's handling of both — rather than as a requirement that any check target change its internals. Three sub-rules, stated in full in Edit 2 below and deliberately NOT restated here: *The tree* binds the verdict to the exact tree pushed; *The set* requires that the executor's run and the pushing host's run together perform every verification a local run would, and caps the executor's credential; *The verdict* defines when a verdict exists, what an absent one obliges, and when a push is authorized. This summary is a POINTER rather than a paraphrase, deliberately: a paraphrase of the clause is duplicated state, and drift between it and the normative text was a recurring review finding. Amends the one bullet in that section that labels the surface as local, and adds three contributor-facing Gherkin scenarios.

### Motivation

The specification governs the pre-push gate as an invocation surface but assumes throughout that it executes on the pushing host. The livespec plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn) is building a delegation primitive whose client replaces the pre-push gate's fall-through with a verdict taken from a job on another host, so a verdict will shortly be able to arrive from somewhere the specification has never described.

The properties that make such a verdict trustworthy currently live only in that plan's research notes, which is the precise failure mode this proposal exists to prevent: a research note is archived when its plan closes, and the guarantees it carried leave with it.

Three of those properties are load-bearing and none is written down.

The first is tree identity. Nothing today would stop a delegated gate from running a full, honest aggregate against a stale mirror or a branch tip and returning a green verdict that authorizes pushing entirely different content. The plan's design solves this outside the specification, by naming the served ref after the pushed tree's hash so that one value identifies the tree, the ref, and the marker. That is exactly the kind of guarantee that must be in the clause rather than in a note.

The second is that the gate is not weakened by moving. The maintainer's direction for that plan was explicit that the gate moves WHERE it runs and not WHAT it runs, and that subsetting it was rejected.

The third is measured rather than hypothetical, and it fails toward a false green. Several check targets report success while skipping the work they exist to do when they cannot reach a forge credential. The two most prominent exit zero with a structured warning; a third logs only at info, and is quieter still. The degradation is not always a credential being ABSENT: the documented path for the branch-protection check is a credential that is PRESENT and too narrowly scoped, which is precisely the configuration a least-privilege gate pod would have. So a delegated gate could report a tree green having silently skipped checks the local gate performs, and keying the rule on absence would not catch the case the plan is actually about to build.

Stating these as properties now, before the client lands, keeps the delegation an execution-location change rather than an unreviewed weakening of the gate, and gives the implementation something to conform to rather than something to reconstruct.

### Proposed Changes

Three edits to `SPECIFICATION/non-functional-requirements.md`. All are architecture rather than mechanism: no executor technology, scheduler, or transport is named, and every requirement is stated about the delegation — the verdict, the executor, and the pushing host's handling of both — rather than as a requirement that any check target change its internals.

**Edit 1 — amend the one bullet that states the pushing-host assumption.**

In the `**Invocation surfaces:**` list of `### Enforcement-suite invocation`, replace this line verbatim:

```text
- **Pre-commit and pre-push (local):** `lefthook.yml` runs `just check`.
```

with:

```text
- **Pre-commit and pre-push (hook):** `lefthook.yml` runs the repository's gate recipe, which runs `just check` on the pushing host unless that repository has delegated its pre-push gate per **Delegated gate execution** below.
```

This edit is the point of the proposal's own motivation: that bullet is the single place in this section that labels the surface as local, and leaving it would ratify a contradiction two lines above the new text. It is NOT the only place the specification describes pre-push as running on the pushing host: `contracts.md` §"Pre-commit step ordering" also describes the non-delegating realization (notably "local pre-push is defense-in-depth that runs the same full aggregate" and "Pre-push delegates to `just check`"). Those sentences are deliberately left unamended and are NOT in this proposal's target files, because this clause is permissive — a repository MAY delegate — so they remain accurate for every repository that has not opted in. Extending the edit map to `contracts.md` would widen the ratified surface without strengthening any guarantee.

**Edit 2 — the new clause.**

Insert immediately after that amended bullet list, and immediately before the paragraph beginning `**Fleet CI execution posture.**`:

> **Delegated gate execution.** A repository MAY delegate its pre-push gate to a remote executor. Delegation MUST be opt-in, and the gate MUST remain runnable on the pushing host by an explicit act whether or not delegation is opted in, so that an executor is never a single point of failure for pushing. Delegation changes WHERE the gate runs and MUST NOT change WHAT it verifies. The requirements below are properties of the delegation — the verdict, the executor, and the pushing host's handling of both — and MUST NOT be read as requiring any check target to change its internals.
>
> *The tree.* A delegated gate MUST run against the exact tree being pushed, and the pushing host MUST verify that identity before honouring the verdict. A verdict for any other content is an absent verdict.
>
> *The set.* Taking the executor's run and the pushing host's run together, every verification the repository's gate recipe would perform for that tree on the pushing host without delegation MUST actually be performed; a check that exits without failing but did not perform its verification — for any cause, credential causes included — has not performed it, and where that verification is one the recipe would perform on the pushing host without delegation it MUST be performed there; a narrowing that applies only on the delegated path and is not made good on the pushing host is not conforming, however it is expressed and whether or not it is version-controlled. A forge credential beyond a least-privilege, read-scoped token for that gate run MUST NOT be available to a remote executor performing a delegated gate — held by it, present in its environment, mounted into it, or obtainable by it from any service it can reach — and a credential from which such a forge credential can be obtained MUST NOT be available to it on those same terms.
>
> *The verdict.* A verdict EXISTS only when the delegated gate itself reported its own OUTCOME for this push. An executor that could not be reached or authenticated, a transport that reported its own success without carrying the gate's outcome, a process terminated by signal, and any stored or cached result are each an ABSENT verdict; the pushing host's own gate-skip marker is read to decide whether a gate runs at all and is never a verdict. The push is authorized only when every check the recipe would perform has passed — those covered by a present delegated verdict, and those performed on the pushing host — and a marker recording a tree as having passed the gate MUST NOT be written on anything less. An absent verdict MUST NOT be treated as a pass and MUST be reported as absent rather than as a failing check; where no fallback performs the uncovered checks on the pushing host, an absent verdict MUST refuse the push.

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
> Then that verdict does not authorize the push
>
> And the verdict is treated as absent rather than as a pass
>
> And no marker recording the pushed tree as having passed the gate is written on the strength of it

> ### Scenario: A delegated pre-push gate refuses the push when no verdict arrives
>
> Given a repository has delegated its pre-push gate to a remote executor
>
> When the transport reports success without carrying the gate's completion status
>
> And no fallback performs the uncovered checks on the pushing host
>
> Then the push is refused
>
> And no marker recording the tree as having passed the gate is written
>
> And the refusal names the absent verdict rather than reporting a failing check

> ### Scenario: A check that reported success without verifying is performed on the pushing host
>
> Given a check target reports success without performing its verification when it lacks a sufficiently scoped credential
>
> And a repository has delegated its pre-push gate to a remote executor holding only a least-privilege read-scoped token
>
> When the delegated gate runs for a push
>
> Then that check is performed on the pushing host, because reporting success without verifying is not performing it
>
> And no wider forge credential is made available to the executor, whatever purpose it would be provisioned for
>
> And the push is authorized only when every check the recipe would perform has passed, that one included

**On the registry obligations this change carries.** No `tests/heading-coverage.json` entry is owed: that map's heading direction covers `## ` headings, all three scenarios are `###` headings inside this file's existing `## Scenarios` section, and none of that section's sixteen current `### Scenario:` headings carries an entry. Stated precisely, because an adjacent obligation in the same registry file should not go unmentioned: the new normative sentences DO add behavior clauses to a file that the `behavior_scenario_link` check treats as a clause source, and that check wants each clause linked to a `scenarios.md` H2 section, which a contributor-facing `###` scenario structurally cannot be. Those clauses therefore join that check's existing warn-mode backlog, which already holds several hundred unlinked clauses for this file (306 measured 2026-09-08, against 505 across the four clause-source files). They do not create the backlog and do not change the lever's severity, but the honest statement is that they join it rather than that nothing is owed.

**Two properties earlier drafts carried and this one drops.** Both are named because a proposal that discloses one dropped property while silently dropping another is worse than one that discloses neither.

*Withdrawal invalidating markers.* An earlier draft required that withdrawing delegation invalidate every marker delegation produced. It is gone, and is NOT reconstructible from the surviving three sub-rules: the clause never requires a marker to record HOW it was produced, so "every marker delegation produced" names a set no implementation can identify without marker provenance that nothing requires. It remains implementable by over-approximation (invalidate all markers on withdrawal), so the honest statement is that it was dropped as unenforceable-as-written rather than as impossible. None of the clause's three sub-rules depends on it, and the obligation was defence-in-depth against an executor already violating the clause; it is named here because the maintainer last saw a summary that carried it.

*The prohibition on automatic fallback.* An earlier draft ended *The verdict* with "falling back to the pushing host is an explicit act, never automatic". That is gone, and its removal was previously justified as restating the opening paragraph — which it does NOT: the opening paragraph guarantees the gate remains RUNNABLE locally by an explicit act, a capability, while the removed clause PROHIBITED the client from falling back on its own, a restriction. A capability guarantee does not imply that prohibition. So the consequence is stated plainly rather than left implicit: under this text a client MAY fall back to the pushing host automatically when the executor yields no verdict. That is accepted, because the fallback performs locally every check the delegated verdict does not cover, so nothing is verified less. An earlier draft of this paragraph asserted that permission while the normative text still authorized a push only on the conjunction of a delegated verdict AND the local checks — which no fallback can satisfy, there being no verdict — so the disclosure described something the clause forbade, and two of the three scenarios below contradicted it. *The verdict* now states authorization per CHECK rather than per verdict, and refuses the push only where no fallback performs the uncovered checks, so the permission and the scenarios agree.

**Placement rationale** under the Boundary litmus: a delegated pre-push gate is livespec's own contributor infrastructure and is not inherited by a project merely governed by livespec, so it belongs in `non-functional-requirements.md` rather than `spec.md`, `contracts.md`, or `constraints.md` — and specifically in `### Enforcement-suite invocation`, which already declares the suite invocation-surface-agnostic and enumerates pre-push among its consumers.

**Three decisions the maintainer is being asked to ratify, not merely to confirm.** All three are choices this proposal makes; none is a restatement of the design record, and each was surfaced by review rather than by the author.

*A hybrid push.* The record's own disposition (research/003 §H, slice S6) was a check that FAILS rather than warns when a credential-needing target runs without one inside the executor — refusal. *The set* departs from that, in its words: a check that "exits without failing but did not perform its verification — for any cause, credential causes included — has not performed it, and where that verification is one the recipe would perform on the pushing host without delegation it MUST be performed there". So most of the gate is delegated and a named remainder is local, and a delegated push is not refused for a check the executor can never hold the credential for under the ceiling below. The record never described that shape.

*An unconditional credential ceiling.* *The set* says: "A forge credential beyond a least-privilege, read-scoped token for that gate run MUST NOT be available to a remote executor performing a delegated gate — held by it, present in its environment, mounted into it, or obtainable by it from any service it can reach — and a credential from which such a forge credential can be obtained MUST NOT be available to it on those same terms." That is scoped by credential class and availability, not by the purpose the credential was provisioned for, so a token declared for pod provisioning rather than for a check is equally forbidden. Earlier drafts only forbade WIDENING a credential's scope, and a reviewer showed that a dedicated executor provisioned with an admin-scoped token from the start violated no sentence — which is precisely what an operator would build, because it makes everything green. Closing that needs an unconditional ceiling, and an unconditional ceiling binds executors the fleet has not built yet. The consequence is deliberate and worth seeing plainly: a check that genuinely requires a stronger credential can never be delegated, only performed on the pushing host. The rejected alternative was to let a sufficiently privileged executor perform everything, which trades a containment property for convenience. This ceiling also removes the need to cross-reference §"Self-hosted CI runner host requirements" at all, which an earlier draft did and which imported a sentence sending such checks to hosted capacity — a destination a pre-push gate does not have.

*A parity line, not a no-narrowing line.* The rule constrains the NARROWING rather than defining a reference set. *The set* requires that, "[t]aking the executor's run and the pushing host's run together, every verification the repository's gate recipe would perform for that tree on the pushing host without delegation MUST actually be performed", and that "a narrowing that applies only on the delegated path and is not made good on the pushing host is not conforming". So a narrowing that lives in the recipe itself — such as the `hook_gate=1` omission `livespec-dev-tooling`'s pre-push recipe already carries — remains legal, because it narrows both paths identically and delegation changes nothing. A narrowing that applies only on the delegated path does NOT become legal by being committed: a version-controlled executor manifest exporting a skip list narrows what the delegated gate performs as a whole — a member it omits that the pushing host does not then perform — and is forbidden however it is expressed; a manifest that merely routes a member to the pushing host narrows nothing. The rejected alternative was to forbid every narrowing, which would have outlawed the existing in-recipe carve-out. Two earlier drafts of this bullet drew the line elsewhere and both failed under review — first at AUDITABILITY, where a committed executor-side skip list satisfied the line while defeating the clause's purpose; then at a REFERENCE SET defined by a local counterfactual run, which a reviewer showed this repository's own recipe cannot satisfy, since `just check-pre-push` first consults a green-token marker stored in `.git/`, outside any tree, so the set it selects differs between hosts for one tree. Attaching parity to the narrowing needs no function-of-the-tree reference set. It does still refer to what the recipe would perform on the pushing host without delegation, so the counterfactual is narrowed rather than removed; what makes that tractable where the earlier draft was not is that the gate-skip marker decides whether a gate runs AT ALL rather than which verifications the recipe selects, so it does not vary the set. On that footing: an in-recipe narrowing conforms, a narrowing expressed only for the delegated path is forbidden whether or not it is committed, and a whole-gate skip keyed on a marker outside the tree is, on the executor, a cached result *The verdict* treats as an absent verdict, while on the pushing host it is what *The verdict* calls the pushing host's own gate-skip marker, which that sub-rule says "is read to decide whether a gate runs at all and is never a verdict" — in neither case a narrowing this rule adjudicates.

**On the aggregate's reference point.** *The set* binds to the repository's own gate recipe — the one its pre-push hook invokes — not to what CI runs. This is deliberate: `livespec-dev-tooling`'s pre-push recipe (`scripts/just/check-pre-push.sh`, whose tracked last line is `just hook_gate=1 check`) already omits a single admin-scoped member, `check-fleet-conformance-admin`, that its CI matrix also omits, and binding to CI's set would have silently outlawed that existing carve-out, while binding to a literal full aggregate would make that repository's delegated gate run a superset it cannot satisfy and refuse every delegated push.
