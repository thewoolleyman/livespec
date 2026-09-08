---
topic: delegated-gate-execution
author: opus-5
created_at: 2026-09-08T02:22:17Z
---

## Proposal: A delegated pre-push gate verifies the pushed tree, runs the same set, and fails rather than relocating or passing without a verdict

### Target specification files

SPECIFICATION/non-functional-requirements.md
SPECIFICATION/contracts.md

### Summary

Adds a Delegated gate execution clause to the Contracts section "Enforcement-suite invocation", permitting a repository's pre-push gate to execute on a remote executor and constraining that delegation as a property of the delegation — the verdict, the executor, and the pushing host's handling of both — and of the outcome a delegated gate reports. Four sub-rules, stated in full in Edit 2 below and deliberately NOT restated here: *The tree* binds the verdict to the exact tree pushed; *The set* requires the delegated gate to perform every verification the recipe would and to fail where it cannot; *The credential* defines what counts as available to the executor, caps it, and names the factory-side remedy; *The verdict* defines when a verdict exists, what an absent one obliges, and what authorizes a push. This summary is a POINTER rather than a paraphrase, deliberately: a paraphrase of the clause is duplicated state, and drift between it and the normative text was a recurring finding across earlier review rounds. Amends the one bullet in that section that labels the surface as local, adds three contributor-facing Gherkin scenarios, and qualifies the three sentences in `contracts.md` §"Pre-commit step ordering" that state unconditionally that pre-push runs `just check` locally.

### Motivation

The specification governs the pre-push gate as an invocation surface but assumes throughout that it executes on the pushing host. The livespec plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn) is building a delegation primitive whose client replaces the pre-push gate's fall-through with a verdict taken from a job on another host, so a verdict will shortly be able to arrive from somewhere the specification has never described.

The properties that make such a verdict trustworthy currently live only in that plan's research notes, which is the precise failure mode this proposal exists to prevent: a research note is archived when its plan closes, and the guarantees it carried leave with it.

Three of those properties are load-bearing and none is written down.

The first is tree identity. Nothing today would stop a delegated gate from running a full, honest aggregate against a stale mirror or a branch tip and returning a green verdict that authorizes pushing entirely different content. The plan's design solves this outside the specification, by naming the served ref after the pushed tree's hash so that one value identifies the tree, the ref, and the marker. That is exactly the kind of guarantee that must be in the clause rather than in a note.

The second is that the gate is not weakened by moving. The maintainer's direction for that plan was explicit that the gate moves WHERE it runs and not WHAT it runs, and that subsetting it was rejected.

The third is measured rather than hypothetical, and it fails toward a false green. Several check targets report success while skipping the work they exist to do when they cannot reach a forge credential. The two most prominent exit zero with a structured warning when they cannot reach a credential; others are gated behind run levers and log their skip only at info, quieter still. The degradation is not always a credential being ABSENT: the documented path for the branch-protection check is a credential that is PRESENT and too narrowly scoped, which is precisely the configuration a least-privilege gate pod would have. So a delegated gate could report a tree green having silently skipped checks the local gate performs, and keying the rule on absence would not catch the case the plan is actually about to build. Not every check with this shape ends up binding a delegated gate — the rule below is keyed to what the local gate actually performs, and several of these are levered off on both paths — but the shape is what the rule has to be written against.

The disposition this proposal takes on that third property is the one the design record always prescribed and the maintainer has now ruled on: such a check FAILS the delegated gate, and the remedy is factory-side — provision the executor with what the verification needs, or remove the verification from the recipe. It is never relocated to the pushing host. The reasoning, in the maintainer's own terms, is that the factory must be self-sufficient and not coupled to special credentials on a local host: local hosts are dumb drivers, required to hold no credentials at all.

Stating these as properties now, before the client lands, keeps the delegation an execution-location change rather than an unreviewed weakening of the gate, and gives the implementation something to conform to rather than something to reconstruct.

### Proposed Changes

Three edits to `SPECIFICATION/non-functional-requirements.md`, and three qualifying amendments to `SPECIFICATION/contracts.md`. All are architecture rather than mechanism: no executor technology, scheduler, or transport is named, and every requirement is stated about the delegation — the verdict, the executor, and the pushing host's handling of both — and about the outcome a delegated gate reports, rather than about how any check is written. That distinction is drawn honestly rather than asserted: under the FAIL disposition, a check running under delegation that cannot perform its verification has to end in a failing gate outcome rather than a silent success, and where a check today exits zero with a warning, satisfying the clause will mean that check distinguishing "verified" from "could not verify" when it runs under delegation. The clause states the outcome; it names no exit code, no signalling format, and no check.

**Edit 1 — amend the one bullet that states the pushing-host assumption.**

In the `**Invocation surfaces:**` list of `### Enforcement-suite invocation`, replace this line verbatim:

```text
- **Pre-commit and pre-push (local):** `lefthook.yml` runs `just check`.
```

with:

```text
- **Pre-commit and pre-push (hook):** `lefthook.yml` runs the repository's gate recipe, which runs `just check` on the pushing host unless that repository has delegated its pre-push gate per **Delegated gate execution** below.
```

This edit is the point of the proposal's own motivation: that bullet is the single place in this section that labels the surface as local, and leaving it would ratify a contradiction two lines above the new text. It is NOT the only place the specification describes pre-push as running on the pushing host — `contracts.md` §"Pre-commit step ordering" carries three such sentences, and Edits 4 to 6 below amend them.

An earlier draft left those three unamended, arguing that because this clause is permissive — a repository MAY delegate — they "remain accurate for every repository that has not opted in", and that extending the edit map would widen the ratified surface without strengthening a guarantee. **That argument confuses edit scope with truth.** The three sentences are unconditional statements about every governed repository (their own paragraph carries "A repository governed by this contract MUST NOT…"), and a MAY in another file does not make an unconditional sentence true for the repositories that exercise the MAY. For a delegating repository, `just check-pre-push` runs the delegation client rather than `just check`, and the run is not local. Since `livespec` itself is the repository the plan will delegate first, the contradiction would be live on ratification day, not hypothetical.

**Edit 2 — the new clause.**

Insert immediately after that amended bullet list, and immediately before the paragraph beginning `**Fleet CI execution posture.**`:

> **Delegated gate execution.** A repository MAY delegate its pre-push gate to a remote executor. Delegation MUST be opt-in, and the gate MUST remain runnable on the pushing host by an explicit act whether or not delegation is opted in, so that an executor is never a single point of failure for pushing. Delegation changes WHERE the gate runs and MUST NOT change WHAT it verifies. The requirements below are properties of the delegation — the verdict, the executor, and the pushing host's handling of both — and of the OUTCOME a delegated gate reports. They prescribe no check's internals; where satisfying them requires a check running under delegation to distinguish having VERIFIED from having been UNABLE to verify, that follows from the outcome property rather than from any rule about how a check is written.
>
> *The tree.* A delegated gate MUST run against the exact tree being pushed, and the pushing host MUST verify that identity before honouring the verdict. A verdict for any other content is an absent verdict.
>
> *The set.* A delegated gate MUST perform every verification the repository's gate recipe, as version-controlled, selects for its pre-push run of that tree. Within that set, a check that exits without failing but did not perform its verification — for any cause, credential causes included — has NOT performed it, and MUST fail the delegated gate rather than report success. A check the recipe selects but does not arm — one that, under the repository's version-controlled recipe and hook configuration alone, performs no verification on any host — is outside that set and is not made a delegated-gate failure by this rule. The set is a function of the repository's tree and committed configuration, and MUST NOT vary with what any particular host happens to hold. Relocating an individual verification to the pushing host is NOT a conforming response to that failure, and a narrowing that applies only on the delegated path is not conforming however it is expressed and whether or not it is version-controlled; the conforming responses are to provision the executor so that the verification can be performed, or to remove the verification from the repository's gate recipe, which narrows the delegated and non-delegated paths alike.
>
> *The credential.* A credential is AVAILABLE to an executor when the executor holds it, carries it in its environment, has it mounted, or can obtain it from any service it can reach. No credential stronger than the verifications the executor performs require may be available to it, and no credential from which such a stronger one can be obtained may be available to it. A credential a verification requires MUST be provisioned to the executor deliberately, designated for the verifications it is provisioned for and no stronger than those verifications need, and MUST NOT reach the executor incidentally as a consequence of where it runs or what else that environment holds. This binds every credential class a verification may need — a forge token, a datastore password, any other — and not forge credentials alone. Where a verification's credential is not provisioned, the conforming responses are those *The set* names; a repository MUST NOT require the pushing host to hold a credential in order for a delegated gate to be conforming.
>
> *The verdict.* A verdict EXISTS only when the delegated gate itself reported its own OUTCOME for this push. An executor that could not be reached or authenticated, a transport that reported its own success without carrying the gate's outcome, a process terminated by signal, and any result stored or cached from any other run are each an ABSENT verdict; the pushing host's own gate-skip marker is read to decide whether a gate runs at all and is never a verdict. A push is authorized only by a present passing verdict, or — where no verdict is present — by a run on the pushing host of the entire gate recipe without delegation, invoked as an explicit act rather than reached by automatic fallback. A present FAILING verdict refuses that push, and a non-delegated run MUST NOT override it; the repository's remedies are those *The set* names, or the withdrawal of delegation, after which the repository is no longer delegating and this clause no longer governs its pushes. Withdrawal of delegation is a change to the repository's version-controlled configuration, never a per-push or per-host act. An absent verdict MUST NOT be treated as a pass, MUST be reported as absent rather than as a failing check, and MUST refuse the push where no such non-delegated run has authorized it. A marker recording a tree as having passed the gate MUST NOT be written on anything less.

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
> And the push is authorized only once the executor is provisioned with the credential that verification requires, or the verification is removed from the repository's gate recipe, or delegation is withdrawn in the repository's version-controlled configuration

**Edits 4, 5 and 6 — qualify the three unconditional pre-push sentences in `contracts.md` §"Pre-commit step ordering".**

Each replaces a verbatim substring, each occurring exactly once in `SPECIFICATION/contracts.md`. None touches a `## ` heading, so no `tests/heading-coverage.json` co-edit is owed for this file either.

**Edit 4.** Replace:

```text
`01-check-pre-push` (delegates to `just check-pre-push`, which runs `just check` — the full aggregate — behind the memoizing short-circuit described below)
```

with:

```text
`01-check-pre-push` (delegates to `just check-pre-push`, which runs `just check` — the full aggregate — behind the memoizing short-circuit described below, unless the repository has delegated its pre-push gate per `non-functional-requirements.md` §"Enforcement-suite invocation", in which case that recipe, behind the same short-circuit, obtains the same aggregate's verdict from the executor against the pushed tree)
```

**Edit 5.** Replace:

```text
and local pre-push is defense-in-depth that runs the same full aggregate
```

with:

```text
and pre-push is defense-in-depth that runs the same full aggregate — on the pushing host, or, where the repository has delegated its pre-push gate, on the executor against the pushed tree
```

**Edit 6.** Replace:

```text
Pre-push delegates to `just check` (a pre-push short-circuit on a working tree byte-identical to one that already passed the full aggregate is memoization of the identical check set, not subsetting).
```

with:

```text
Pre-push delegates to `just check` (a pre-push short-circuit on a working tree byte-identical to one that already passed the full aggregate is memoization of the identical check set, not subsetting); where the repository has delegated its pre-push gate, the same aggregate runs on the executor instead, which changes WHERE it runs and not WHAT it verifies.
```

These three are the minimum that makes the section true for a delegating repository. They add no obligation: each states the delegated realization the new clause already governs, so the guarantee lives in `non-functional-requirements.md` and `contracts.md` merely stops asserting its negation.

**On the registry obligations this change carries.** No `tests/heading-coverage.json` entry is owed by either target file: that map's heading direction covers `## ` headings; all three scenarios are `###` headings inside `non-functional-requirements.md`'s existing `## Scenarios` section, and none of that section's sixteen current `### Scenario:` headings carries an entry; and Edits 4 to 6 amend prose inside an existing `contracts.md` `## ` section without adding, removing or renaming a heading. Stated precisely, because an adjacent obligation in the same registry file should not go unmentioned: the new normative sentences DO add behavior clauses to a file that the `behavior_scenario_link` check treats as a clause source, and that check wants each clause linked to a `scenarios.md` H2 section, which a contributor-facing `###` scenario structurally cannot be. Those clauses therefore join that check's existing warn-mode backlog, which already holds several hundred unlinked clauses for this file (306 measured 2026-09-08, against 505 across the four clause-source files). They do not create the backlog and do not change the lever's severity, but the honest statement is that they join it rather than that nothing is owed.

**Two properties whose disposition changed across drafts: one dropped here, one restored here.** Both are named because a proposal that discloses one such change while making another silently is worse than one that discloses neither.

*Withdrawal invalidating markers.* An earlier draft required that withdrawing delegation invalidate every marker delegation produced. It is gone, and is NOT reconstructible from the surviving four sub-rules: the clause never requires a marker to record HOW it was produced, so "every marker delegation produced" names a set no implementation can identify without marker provenance that nothing requires. It remains implementable by over-approximation (invalidate all markers on withdrawal), so the honest statement is that it was dropped as unenforceable-as-written rather than as impossible. None of the clause's sub-rules depends on it, and the obligation was defence-in-depth against an executor already violating the clause; it is named here because the maintainer last saw a summary that carried it.

*The prohibition on automatic fallback — dropped by an earlier draft, and RESTORED here.* An earlier draft ended *The verdict* with "falling back to the pushing host is an explicit act, never automatic", then removed it on the reasoning that the opening paragraph already said so. It did not: the opening paragraph guarantees the gate remains RUNNABLE locally by an explicit act, a capability, while the removed sentence PROHIBITED the client from falling back on its own, a restriction, and a capability guarantee does not imply that prohibition. The draft therefore permitted automatic fallback, and disclosed the permission — which is the shape this rework very nearly shipped, because the permission survived from the old text while the new *consequence of FAIL* paragraph argued the opposite. Under the FAIL disposition the two cannot both stand, and the ARGUMENT settles which goes: a factory outage IS the absent-verdict case, and the pushing host is a credential-less dumb driver whose whole-recipe run warn-passes exactly the checks the executor would have failed on. An automatic fallback would therefore turn every outage into a silent return to the weaker gate. *The verdict* now requires the non-delegated run to be an explicit act. This is not a new restriction on the operator: research/003 §G wants a local escape so the cluster is not a single point of failure, and an explicit local run supplies it. What is forbidden is the client reaching that weaker gate on its own, unasked. Separately, and still true: a fallback with a REMAINDER — running locally only the checks the executor could not perform — is forbidden outright by *The set*, whether explicit or not. That is the split this proposal exists to rule out; the explicitness rule above governs the whole-recipe run that remains legitimate.

One objection to that reasoning deserves answering rather than leaving for a reader to find. The paragraph below concedes a LARGER silent bypass than the one this rule forbids: the gate-skip marker means the ordinary local-then-push sequence never reaches the executor at all. So forbidding automatic fallback can look like straining at a gnat while a bigger hole stands open. The answer is that the two are not alternatives. The marker bypass is a pre-existing defect of the marker, owned and filed where the marker is implemented, and it is not in this clause's power to repair; automatic fallback would be a NEW silent downgrade that this clause would itself be authorizing. Declining to add the second is not made pointless by the first still being open, and the rule costs nothing that `research/003` §G's local escape needs, since an explicit run supplies it.

**The consequence of FAIL, stated plainly — including the limit of what it delivers.** Under this text a delegated gate that cannot perform one of its verifications produces a FAILING verdict; *The verdict* forbids a non-delegated run from overriding it within that attempt, and constrains withdrawal of delegation to a change in the repository's version-controlled configuration rather than a per-push or per-host act. Within an attempt that reached the delegated gate, the gate is therefore hard: the remedies are to provision the executor, to remove the verification from the recipe, or to withdraw delegation deliberately and visibly.

**What this clause does NOT deliver, said here rather than left to be discovered.** It does not make every push consult the executor, and an earlier draft of this paragraph wrongly claimed it did ("a contributor whose factory is missing a credential cannot push that tree by running the recipe locally instead"). Both repositories write the pre-push gate-skip marker at the tail of the PLAIN aggregate — `livespec`'s `justfile:329` and `livespec-dev-tooling`'s `scripts/just/check.sh:73` — and `check-pre-push` skips the gate when that marker matches the tree. So the ordinary sequence of running the aggregate locally and then pushing skips the gate, and under delegation the executor is never consulted. `research/003` §G designed it that way, leaving the token path untouched, so this is design-faithful rather than a loophole in the clause.

That marker's own soundness is a separate matter and deliberately not settled here. Memoizing a gate result is valid only where the gate is a pure function of the tree, and several members of both aggregates read state outside it — CI status, branch protection, the ledger, sibling clones — so a marker can assert a result that has since stopped being true, with or without any delegation. That is a pre-existing defect of the marker rather than a property of delegation, it is filed and owned where the marker is implemented, and this clause neither depends on it nor repairs it. What this clause does say about markers is only what it can enforce: the pushing host's gate-skip marker "is read to decide whether a gate runs at all and is never a verdict", and a marker recording a tree as having passed MUST NOT be written on anything less than the authorization *The verdict* defines.

**Two decisions this proposal carries, and where each came from.** Neither is the author's invention; both are recorded so that ratification is informed rather than implicit.

*The FAIL disposition, and the factory-side remedy (maintainer ruling, 2026-09-08).* An earlier draft of this proposal departed from the design record: where the record prescribed a check that FAILS when it cannot perform its verification inside the executor, the draft instead required that verification to be performed on the pushing host — a hybrid push, most of the gate delegated and a named remainder local. That departure was invented by this proposal in response to a review blocker, not by the design record, and the maintainer has ruled it out: the factory must be self-sufficient rather than coupled to special credentials on a local host, and a missing credential is fixed factory-side by injecting it or by removing what needs it. This text restores the record's disposition. It is substantially SIMPLER than the draft it replaces: the hybrid push, the named-remainder-is-local shape, the per-check authorization split in *The verdict*, and the parity subtlety about a narrowing being "made good on the pushing host" are all deleted, because each existed only to support the departure. **The removal has a real, measured cost, and an earlier draft of this paragraph understated it as "nothing measurable".** That claim rested on a query that asked the wrong question — it searched for `check-fleet-conformance-admin` by NAME and, finding it absent from `livespec`'s `justfile` and skipped by `livespec-dev-tooling`'s pre-push (`hook_gate_skips` at `scripts/just/check.sh:48`), concluded no delegated recipe holds an admin-scoped check. Those two facts are true and are restated here because they still matter: the fleet's admin-scoped WORLD-GATE is indeed absent from every recipe that would be delegated. But "admin-scoped check" is not the same set as "the check named admin", and the honest measurement is this:

- **`check-branch-protection-alignment` requires an admin-scoped token to perform its verification, and it is in BOTH delegated recipes** — `livespec`'s `justfile:204` and `livespec-dev-tooling`'s `justfile:210`, and it is not among `hook_gate_skips`'s members. Its own contract says so (`livespec_dev_tooling/checks/branch_protection_alignment.py:58-72`): the default Actions `GITHUB_TOKEN` "lacks the admin scope needed to READ branch protection", so the check hits its graceful-skip path and "does NOT enforce there"; it is wired into `just check` / pre-push precisely "where a maintainer's admin-scoped `gh` token CAN read protection".
- **`check-master-ci-green` likewise reports success without verifying when it has no credential**, and is likewise in both recipes. `master_ci_green.py:206` returns a "skip" with a warning and exit 0 when `_gh_has_stored_credential()` is false. That *The credential* permits a read-scoped token outright is not the same as the executor HAVING one: unprovisioned, this check exits without verifying and *The set* fails the delegated gate on it.

Both are selected by the committed recipe on every push, so both are in the set on every host — including a credential-less one. Both perform today on a maintainer's pushing host (`gh` there carries `admin:org` and `repo`) and neither would in an unprovisioned executor, which is the asymmetry *The set* exists to catch; but the obligation does not depend on that asymmetry persisting, which is the point of anchoring the set to committed configuration rather than to the host.

**One further member is conditional rather than certain, and is named so the "two" above is not read as more precise than it is.** `check-no-workflow-edits` is selected and unarmed by any lever, and its script exits 0 with "no base to compare against" when the clone it runs in resolves neither `origin/master` nor `origin/main`. That is a skip-pass *The set*'s second sentence catches, so it would fail a delegated gate in an executor whose clone lacks the base ref. `research/003` §E's bare mirror is expected to provide it, in which case the check performs normally and the count stays at two. It is listed because "two" is conditional on that expectation holding, and a disclosure that hid the condition would repeat this proposal's own history.

**Equally important is what is NOT in the set, because an earlier draft got this backwards.** That draft disclosed four `BEADS_DOLT_PASSWORD`-armed members (`check-plan-epic-parity`, `check-plan-record-conformance`, `check-work-item-interpolation-delimiters`, `check-work-item-status-vocabulary`) as further first-push failures. They are not, under *The set* as written: no hook or recipe on either repository ARMS their run levers, so the committed configuration selects them without ever causing them to verify anything, on any host — and *The set*'s reference is what that committed configuration selects. The same holds for `check-check-mutation`, `check-local-memory-drift-audit`, and `livespec-dev-tooling`'s `check-fleet-conformance`, whose `LIVESPEC_RUN_FLEET_CONFORMANCE` lever is set only in workflow files and never in a hook or recipe. The unscoped reading that would have caught the ledger checks would equally have required a delegated gate to run mutation testing on every push — which `non-functional-requirements.md` deliberately classifies as a release-gate target excluded from `just check`'s per-commit cost. So the scoped reading is the only coherent one, and it is also the one that matches "move WHERE the gate runs, not WHAT it runs": the delegated gate owes exactly what the committed recipe arms, neither less nor more.

**An earlier draft anchored this set to the pushing host, and that was wrong in a way worth recording, because it was wrong only in the end state the ruling is trying to reach.** It read "every verification the recipe would perform for that tree ON THE PUSHING HOST without delegation", and defended the host-relativity as deliberate parity: a contributor whose host has no `gh` credential has a local gate that does not perform these two either, so their delegated gate owes no more. That reasoning is internally sound and still fails, because ruling 1's whole point is that hosts become dumb drivers holding NO credentials. In that world the two credentialed checks leave the reference set on every push, and an unprovisioned executor that skip-passes them returns a CONFORMING passing verdict. The clause would have bound the factory only for as long as pushing hosts stayed credentialed — the protection expiring precisely as the ruling succeeded — and "fix the factory" would never have been forced. Host-relative parity and factory-absolute self-sufficiency are different propositions, and the ruling asked for the second. Anchoring to the version-controlled recipe and hook configuration delivers it: the set is the same on every host, so what the executor owes does not shrink when a host stops holding credentials.

The anchoring also removes a second, quieter defect. Run levers are ordinary environment variables and a pre-push hook inherits the invoking shell's environment, so a host-anchored set would have varied with the pushing host's PROCESS ENVIRONMENT at push time — something an executor cannot observe and therefore cannot conform to except by failing on every skip-pass regardless of host. A set derived from committed configuration is one both sides can compute.

So the consequence to ratify with eyes open is that **the first delegated push in either repository FAILS on two members — three if the executor's clone cannot resolve a base ref, per the conditional above** until the executor is deliberately provisioned with a forge credential able to read branch protection and CI status, or those members are removed from the recipe. Under *The credential* both remedies are available and the first is permitted, because a credential a verification requires may be provisioned deliberately and scoped to it. That is the ruling working as intended rather than a defect: the factory is made self-sufficient, at the cost of provisioning it. It is stated here because a maintainer told "this costs nothing" would have ratified a different proposition than the one on the table.

**The design record shares the earlier understatement in the opposite direction** — `research/003` §H prescribes projecting "the least-privilege, read-scoped ones as Secrets", which does not cover the admin scope `check-branch-protection-alignment` actually needs. So the admin-capable-token consequence is a fact the ratification must be informed of rather than a departure from the record.

*The credential ceiling as a least-privilege default rather than an absolute bar (maintainer ruling, 2026-09-08).* An earlier draft barred any forge credential stronger than a least-privilege read-scoped token from being "obtainable by it from any service it can reach". That is an absolute bar, and it forbade the maintainer's own remedy: a credential deliberately projected into the executor's namespace IS obtainable from a service the executor reaches, so under that text "inject the cred" was unavailable and only relocation remained — which inverted the coupling the ruling is about, making the local host hold what the factory was forbidden to have. *The credential* keeps the containment property and rescopes it twice over: the same availability enumeration now defines what counts as available; the ceiling binds to what the executor's verifications REQUIRE rather than to a fixed token class; a stronger credential is permitted exactly when it is provisioned deliberately and scoped to the verifications that need it; and the sub-rule binds every credential CLASS rather than forge credentials alone. That last change is not cosmetic — an earlier draft capped only forge credentials while the proposal's own disclosure told an operator to provision a datastore password, which the sub-rule then left entirely unconstrained: no ceiling, no deliberateness requirement, no bar on incidental acquisition. A Dolt admin password reaching the executor because of where it runs was precisely the shape this ruling rejected, and the forge-only wording exempted it. The rejected alternative was to drop the ceiling entirely in favour of "the factory holds whatever it needs, least-privilege where practical"; it was rejected because an operator would then be free to provision an admin token because that makes everything green, with no sentence objecting. So over-provisioning and incidental acquisition remain forbidden, and deliberate least-privilege provisioning is the named remedy.

**What the credential ceiling costs, stated as a decision rather than left to be discovered.** *The credential* bars any credential stronger than the executor's verifications require, and the deliberate-provisioning path is written for credentials a VERIFICATION requires. Read literally — and it is meant literally — that bars credentials the executor might carry for reasons unrelated to verifying anything: an auto-mounted service-account token it never uses, an authenticated build cache, an authenticated telemetry sink. Two consequences follow, and both are accepted rather than overlooked.

First, an executor conforming to this clause carries nothing it does not need, which for a Kubernetes realization means a Job that does not automount a service-account token. That is a real obligation on whoever builds the executor, and it is the right one: a gate Job runs a check aggregate against a tree and has no business holding cluster API authority. Nothing live collides with it today — the build cache the plan's design uses is an unauthenticated read-only user and the telemetry sink is keyless.

Second, and more honestly: if a future executor legitimately needs an authenticated INFRASTRUCTURE credential — a cache that starts requiring a password, say — this clause forbids it, and the remedy is to revise this clause rather than to reinterpret it. That is a deliberate choice of a strict rule that must be revisited over a loose rule that must be trusted. The alternative considered was to narrow the ceiling to credentials that could influence a verification's outcome, which reads more reasonably and is worse: "could influence an outcome" is exactly the judgement an operator provisioning a convenient token would make in their own favour, and the ruling this clause implements was made because that judgement had gone the wrong way before.

**On the parity line.** *The set* constrains the NARROWING rather than defining a reference set. A narrowing that lives in the recipe itself — such as the `hook_gate=1` omission `livespec-dev-tooling`'s pre-push recipe already carries — remains legal, because it narrows the delegated and non-delegated paths identically and delegation changes nothing about it. A narrowing that applies only on the delegated path does NOT become legal by being committed: a version-controlled executor manifest exporting a skip list narrows what the delegated gate performs and is forbidden however it is expressed. The rejected alternative was to forbid every narrowing, which would have outlawed the existing in-recipe carve-out. Two earlier drafts drew this line elsewhere and both failed under review — first at AUDITABILITY, where a committed executor-side skip list satisfied the line while defeating the clause's purpose; then at a REFERENCE SET defined by a local counterfactual run, which this repository's own recipe cannot satisfy, since `just check-pre-push` first consults a green-token marker stored in `.git/`, outside any tree, so the set it selects differs between hosts for one tree. Attaching parity to the narrowing needs no function-of-the-tree reference set. The reference it does keep is to what the repository's version-controlled recipe and hook configuration select, which is a function of the tree rather than a counterfactual about a host; what makes that tractable where an earlier draft was not is that the gate-skip marker decides whether a gate runs AT ALL rather than which verifications the recipe selects, so it does not vary the set. On that footing: an in-recipe narrowing conforms, a narrowing expressed only for the delegated path is forbidden whether or not it is committed, and a whole-gate skip keyed on a marker outside the tree is, on the executor, a cached result *The verdict* treats as an absent verdict, while on the pushing host it is what *The verdict* calls the pushing host's own gate-skip marker, which that sub-rule says "is read to decide whether a gate runs at all and is never a verdict" — in neither case a narrowing this rule adjudicates.

**On the aggregate's reference point.** *The set* binds to the repository's own gate recipe — the one its pre-push hook invokes — not to what CI runs. This is deliberate: `livespec-dev-tooling`'s pre-push recipe (`scripts/just/check-pre-push.sh`, whose tracked last line is `just hook_gate=1 check`) already omits a single admin-scoped member, `check-fleet-conformance-admin`, that its CI matrix also omits, and binding to CI's set would have silently outlawed that existing carve-out, while binding to a literal full aggregate would make that repository's delegated gate run a superset it cannot satisfy and refuse every delegated push.

**Placement rationale** under the Boundary litmus: a delegated pre-push gate is livespec's own contributor infrastructure and is not inherited by a project merely governed by livespec, so it belongs in `non-functional-requirements.md` rather than `spec.md`, `contracts.md`, or `constraints.md` — and specifically in `### Enforcement-suite invocation`, which already declares the suite invocation-surface-agnostic and enumerates pre-push among its consumers.
