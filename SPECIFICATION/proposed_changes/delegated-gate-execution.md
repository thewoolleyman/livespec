---
topic: delegated-gate-execution
author: opus-5
created_at: 2026-09-08T02:22:17Z
---

## Proposal: A delegated pre-push gate verifies the pushed tree, runs the same set, and fails rather than relocating or passing without a verdict

### Target specification files

SPECIFICATION/non-functional-requirements.md

### Summary

Adds a Delegated gate execution clause to the Contracts section "Enforcement-suite invocation", permitting a repository's pre-push gate to execute on a remote executor and constraining that delegation as a property of the delegation — the verdict, the executor, and the pushing host's handling of both — rather than as a requirement that any check target change its internals. Four sub-rules, stated in full in Edit 2 below and deliberately NOT restated here: *The tree* binds the verdict to the exact tree pushed; *The set* requires the delegated gate to perform every verification the recipe would and to fail where it cannot; *The credential* defines what counts as available to the executor, caps it, and names the factory-side remedy; *The verdict* defines when a verdict exists, what an absent one obliges, and what authorizes a push. This summary is a POINTER rather than a paraphrase, deliberately: a paraphrase of the clause is duplicated state, and drift between it and the normative text was a recurring finding across earlier review rounds. Amends the one bullet in that section that labels the surface as local, and adds three contributor-facing Gherkin scenarios.

### Motivation

The specification governs the pre-push gate as an invocation surface but assumes throughout that it executes on the pushing host. The livespec plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn) is building a delegation primitive whose client replaces the pre-push gate's fall-through with a verdict taken from a job on another host, so a verdict will shortly be able to arrive from somewhere the specification has never described.

The properties that make such a verdict trustworthy currently live only in that plan's research notes, which is the precise failure mode this proposal exists to prevent: a research note is archived when its plan closes, and the guarantees it carried leave with it.

Three of those properties are load-bearing and none is written down.

The first is tree identity. Nothing today would stop a delegated gate from running a full, honest aggregate against a stale mirror or a branch tip and returning a green verdict that authorizes pushing entirely different content. The plan's design solves this outside the specification, by naming the served ref after the pushed tree's hash so that one value identifies the tree, the ref, and the marker. That is exactly the kind of guarantee that must be in the clause rather than in a note.

The second is that the gate is not weakened by moving. The maintainer's direction for that plan was explicit that the gate moves WHERE it runs and not WHAT it runs, and that subsetting it was rejected.

The third is measured rather than hypothetical, and it fails toward a false green. Several check targets report success while skipping the work they exist to do when they cannot reach a forge credential. The two most prominent exit zero with a structured warning; a third logs its degradation only at info, and is quieter still. The degradation is not always a credential being ABSENT: the documented path for the branch-protection check is a credential that is PRESENT and too narrowly scoped, which is precisely the configuration a least-privilege gate pod would have. So a delegated gate could report a tree green having silently skipped checks the local gate performs, and keying the rule on absence would not catch the case the plan is actually about to build.

The disposition this proposal takes on that third property is the one the design record always prescribed and the maintainer has now ruled on twice: such a check FAILS the delegated gate, and the remedy is factory-side — provision the executor with what the verification needs, or remove the verification from the recipe. It is never relocated to the pushing host. The reasoning, in the maintainer's own terms, is that the factory must be self-sufficient and not coupled to special credentials on a local host: local hosts are dumb drivers, required to hold no credentials at all.

Stating these as properties now, before the client lands, keeps the delegation an execution-location change rather than an unreviewed weakening of the gate, and gives the implementation something to conform to rather than something to reconstruct.

### Proposed Changes

Three edits to `SPECIFICATION/non-functional-requirements.md`. All are architecture rather than mechanism: no executor technology, scheduler, or transport is named, and every requirement is stated about the delegation — the verdict, the executor, and the pushing host's handling of both — and about the outcome a delegated gate reports, rather than about how any check is written. That distinction is drawn honestly rather than asserted: under the FAIL disposition, a check running under delegation that cannot perform its verification has to end in a failing gate outcome rather than a silent success, and where a check today exits zero with a warning, satisfying the clause will mean that check distinguishing "verified" from "could not verify" when it runs under delegation. The clause states the outcome; it names no exit code, no signalling format, and no check.

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

> **Delegated gate execution.** A repository MAY delegate its pre-push gate to a remote executor. Delegation MUST be opt-in, and the gate MUST remain runnable on the pushing host by an explicit act whether or not delegation is opted in, so that an executor is never a single point of failure for pushing. Delegation changes WHERE the gate runs and MUST NOT change WHAT it verifies. The requirements below are properties of the delegation — the verdict, the executor, and the pushing host's handling of both — and of the OUTCOME a delegated gate reports. They prescribe no check's internals; where satisfying them requires a check running under delegation to distinguish having VERIFIED from having been UNABLE to verify, that follows from the outcome property rather than from any rule about how a check is written.
>
> *The tree.* A delegated gate MUST run against the exact tree being pushed, and the pushing host MUST verify that identity before honouring the verdict. A verdict for any other content is an absent verdict.
>
> *The set.* A delegated gate MUST perform every verification the repository's gate recipe would perform for that tree on the pushing host without delegation. A check that exits without failing but did not perform its verification — for any cause, credential causes included — has NOT performed it, and MUST fail the delegated gate rather than report success. Relocating an individual verification to the pushing host is NOT a conforming response to that failure, and a narrowing that applies only on the delegated path is not conforming however it is expressed and whether or not it is version-controlled; the conforming responses are to provision the executor so that the verification can be performed, or to remove the verification from the repository's gate recipe, which narrows the delegated and non-delegated paths alike.
>
> *The credential.* A credential is AVAILABLE to an executor when the executor holds it, carries it in its environment, has it mounted, or can obtain it from any service it can reach. No forge credential stronger than the verifications the executor performs require may be available to it, and no credential from which such a stronger forge credential can be obtained may be available to it. A forge credential a verification requires MUST be provisioned to the executor deliberately and scoped to the verifications it is provisioned for — which is what makes it one those verifications require, and so permitted — and MUST NOT reach the executor incidentally as a consequence of where it runs or what else that environment holds. Where a verification's credential is not provisioned, the conforming responses are those *The set* names; a repository MUST NOT require the pushing host to hold a credential in order for a delegated gate to be conforming.
>
> *The verdict.* A verdict EXISTS only when the delegated gate itself reported its own OUTCOME for this push. An executor that could not be reached or authenticated, a transport that reported its own success without carrying the gate's outcome, a process terminated by signal, and any result stored or cached from any other run are each an ABSENT verdict; the pushing host's own gate-skip marker is read to decide whether a gate runs at all and is never a verdict. A push is authorized only by a present passing verdict, or — where no verdict is present — by a run on the pushing host of the entire gate recipe without delegation. A present FAILING verdict refuses the push of that tree, and a non-delegated run MUST NOT override it; the repository's remedy is the one *The set* names, or the explicit withdrawal of delegation, after which the repository is no longer delegating and this clause no longer governs its pushes. An absent verdict MUST NOT be treated as a pass, MUST be reported as absent rather than as a failing check, and MUST refuse the push where no such non-delegated run has authorized it. A marker recording a tree as having passed the gate MUST NOT be written on anything less.

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
> When the transport reports success without carrying the gate's outcome
>
> And the entire gate recipe has not been run on the pushing host without delegation
>
> Then the push is refused
>
> And no marker recording the tree as having passed the gate is written
>
> And the refusal names the absent verdict rather than reporting a failing check

> ### Scenario: A check that cannot perform its verification fails the delegated gate
>
> Given a check target reports success without performing its verification when it lacks a sufficiently scoped credential
>
> And a repository has delegated its pre-push gate to a remote executor to which that credential is not available
>
> When the delegated gate runs for a push
>
> Then the delegated gate fails, because reporting success without verifying is not performing the verification
>
> And that verification is not relocated to the pushing host
>
> And the push is authorized only once the executor is provisioned with the credential that verification requires, or the verification is removed from the repository's gate recipe

**On the registry obligations this change carries.** No `tests/heading-coverage.json` entry is owed: that map's heading direction covers `## ` headings, all three scenarios are `###` headings inside this file's existing `## Scenarios` section, and none of that section's sixteen current `### Scenario:` headings carries an entry. Stated precisely, because an adjacent obligation in the same registry file should not go unmentioned: the new normative sentences DO add behavior clauses to a file that the `behavior_scenario_link` check treats as a clause source, and that check wants each clause linked to a `scenarios.md` H2 section, which a contributor-facing `###` scenario structurally cannot be. Those clauses therefore join that check's existing warn-mode backlog, which already holds several hundred unlinked clauses for this file (306 measured 2026-09-08, against 505 across the four clause-source files). They do not create the backlog and do not change the lever's severity, but the honest statement is that they join it rather than that nothing is owed.

**Two properties earlier drafts carried and this one drops.** Both are named because a proposal that discloses one dropped property while silently dropping another is worse than one that discloses neither.

*Withdrawal invalidating markers.* An earlier draft required that withdrawing delegation invalidate every marker delegation produced. It is gone, and is NOT reconstructible from the surviving four sub-rules: the clause never requires a marker to record HOW it was produced, so "every marker delegation produced" names a set no implementation can identify without marker provenance that nothing requires. It remains implementable by over-approximation (invalidate all markers on withdrawal), so the honest statement is that it was dropped as unenforceable-as-written rather than as impossible. None of the clause's sub-rules depends on it, and the obligation was defence-in-depth against an executor already violating the clause; it is named here because the maintainer last saw a summary that carried it.

*The prohibition on automatic fallback.* An earlier draft ended *The verdict* with "falling back to the pushing host is an explicit act, never automatic". That is gone, and its removal is NOT a restatement of the opening paragraph: the opening paragraph guarantees the gate remains RUNNABLE locally by an explicit act, a capability, while the removed sentence PROHIBITED the client from falling back on its own, a restriction. A capability guarantee does not imply that prohibition. So the consequence is stated plainly rather than left implicit: under this text a client MAY fall back automatically when the executor yields no verdict, PROVIDED the fallback runs the entire gate recipe without delegation. What it may not do — and what *The set* now forbids outright — is fall back with a REMAINDER, running locally only the checks the executor could not perform. A whole-recipe fallback is simply the non-delegated path the clause already preserves, and verifies nothing less; a remainder is the split this proposal exists to rule out.

**The consequence of FAIL, stated plainly rather than left to be discovered.** Under this text a delegated gate that cannot perform one of its verifications produces a FAILING verdict, and *The verdict* forbids a later non-delegated run from overriding it. So a contributor whose factory is missing a credential cannot push that tree by running the recipe locally instead. That is the ruling's intent — a hard gate is what makes the factory self-sufficient — and it is not a deadlock, because two remedies remain and both are named in the clause: fix the factory (provision the credential, or remove the verification from the recipe), or explicitly withdraw delegation, after which the repository is not delegating and the clause governs nothing. Withdrawal is deliberately an explicit act rather than an automatic fallback: an automatic one would turn every factory outage into a silent return to the weaker local gate, which is the outcome the whole clause exists to prevent.

**Two decisions this proposal carries, and where each came from.** Neither is the author's invention; both are recorded so that ratification is informed rather than implicit.

*The FAIL disposition, and the factory-side remedy (maintainer ruling, 2026-09-08).* An earlier draft of this proposal departed from the design record: where the record prescribed a check that FAILS when it cannot perform its verification inside the executor, the draft instead required that verification to be performed on the pushing host — a hybrid push, most of the gate delegated and a named remainder local. That departure was invented by this proposal in response to a review blocker, not by the design record, and the maintainer has ruled it out: the factory must be self-sufficient rather than coupled to special credentials on a local host, and a missing credential is fixed factory-side by injecting it or by removing what needs it. This text restores the record's disposition. It is substantially SIMPLER than the draft it replaces: the hybrid push, the named-remainder-is-local shape, the per-check authorization split in *The verdict*, and the parity subtlety about a narrowing being "made good on the pushing host" are all deleted, because each existed only to support the departure. The removal costs nothing measurable: `livespec`'s `justfile` contains no `check-fleet-conformance-admin` at all, and `livespec-dev-tooling`'s pre-push recipe skips exactly that one member (`hook_gate_skips` at `scripts/just/check.sh:48`), so no recipe that would be delegated today contains an admin-scoped check. The two checks the design record actually names — `check-branch-protection-alignment` and `check-master-ci-green` — need a read-scoped token, which *The credential* permits outright.

*The credential ceiling as a least-privilege default rather than an absolute bar (maintainer ruling, 2026-09-08).* An earlier draft barred any forge credential stronger than a least-privilege read-scoped token from being "obtainable by it from any service it can reach". That is an absolute bar, and it forbade the maintainer's own remedy: a credential deliberately projected into the executor's namespace IS obtainable from a service the executor reaches, so under that text "inject the cred" was unavailable and only relocation remained — which inverted the coupling the ruling is about, making the local host hold what the factory was forbidden to have. *The credential* keeps the containment property and rescopes it: the same availability enumeration now defines what counts as available, the ceiling binds to what the executor's verifications REQUIRE rather than to a fixed token class, and a stronger credential is permitted exactly when it is provisioned deliberately and scoped to the verifications that need it. The rejected alternative was to drop the ceiling entirely in favour of "the factory holds whatever it needs, least-privilege where practical"; it was rejected because an operator would then be free to provision an admin token because that makes everything green, with no sentence objecting. So over-provisioning and incidental acquisition remain forbidden, and deliberate least-privilege provisioning is the named remedy.

**On the parity line.** *The set* constrains the NARROWING rather than defining a reference set. A narrowing that lives in the recipe itself — such as the `hook_gate=1` omission `livespec-dev-tooling`'s pre-push recipe already carries — remains legal, because it narrows the delegated and non-delegated paths identically and delegation changes nothing about it. A narrowing that applies only on the delegated path does NOT become legal by being committed: a version-controlled executor manifest exporting a skip list narrows what the delegated gate performs and is forbidden however it is expressed. The rejected alternative was to forbid every narrowing, which would have outlawed the existing in-recipe carve-out. Two earlier drafts drew this line elsewhere and both failed under review — first at AUDITABILITY, where a committed executor-side skip list satisfied the line while defeating the clause's purpose; then at a REFERENCE SET defined by a local counterfactual run, which this repository's own recipe cannot satisfy, since `just check-pre-push` first consults a green-token marker stored in `.git/`, outside any tree, so the set it selects differs between hosts for one tree. Attaching parity to the narrowing needs no function-of-the-tree reference set. It does still refer to what the recipe would perform on the pushing host without delegation, so the counterfactual is narrowed rather than removed; what makes that tractable where the earlier draft was not is that the gate-skip marker decides whether a gate runs AT ALL rather than which verifications the recipe selects, so it does not vary the set. On that footing: an in-recipe narrowing conforms, a narrowing expressed only for the delegated path is forbidden whether or not it is committed, and a whole-gate skip keyed on a marker outside the tree is, on the executor, a cached result *The verdict* treats as an absent verdict, while on the pushing host it is what *The verdict* calls the pushing host's own gate-skip marker, which that sub-rule says "is read to decide whether a gate runs at all and is never a verdict" — in neither case a narrowing this rule adjudicates.

**On the aggregate's reference point.** *The set* binds to the repository's own gate recipe — the one its pre-push hook invokes — not to what CI runs. This is deliberate: `livespec-dev-tooling`'s pre-push recipe (`scripts/just/check-pre-push.sh`, whose tracked last line is `just hook_gate=1 check`) already omits a single admin-scoped member, `check-fleet-conformance-admin`, that its CI matrix also omits, and binding to CI's set would have silently outlawed that existing carve-out, while binding to a literal full aggregate would make that repository's delegated gate run a superset it cannot satisfy and refuse every delegated push.

**Placement rationale** under the Boundary litmus: a delegated pre-push gate is livespec's own contributor infrastructure and is not inherited by a project merely governed by livespec, so it belongs in `non-functional-requirements.md` rather than `spec.md`, `contracts.md`, or `constraints.md` — and specifically in `### Enforcement-suite invocation`, which already declares the suite invocation-surface-agnostic and enumerates pre-push among its consumers.
