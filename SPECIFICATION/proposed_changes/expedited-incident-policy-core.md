---
topic: expedited-incident-policy-core
author: codex:expedited-incident-response-flag/core-incident-carrier
created_at: 2026-11-03T19:12:24Z
---

## Proposal: Inherited incident exception

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Introduce the maintainer-directed incident-only exception while preserving complete normal validation and the owning-repository boundaries.

### Motivation

Priority-1 plan livespec-dev-tooling-bqnzcm requires a local fast repair and immediate no-check incident recovery followed by same-item normal factory repayment. The reviewed design is in livespec-dev-tooling plan/expedited-incident-response-flag/research/001-charter-expedited-incident-response-flag.md and 002-override-surface-inventory.md. Generated templates templates/orchestrator-plugin/justfile.jinja and lefthook.yml.jinja and operator guidance AGENTS.md/.ai/ci-gate-discipline.md are implementation follow-ups, not changes this proposal silently activates.

### Proposed Changes

Apply the following exact diff through revise. New H2 headings MUST co-edit tests/heading-coverage.json and its generated debt register with implementing owners in that same revision.

```diff
--- SPECIFICATION/contracts.md
+++ SPECIFICATION/contracts.md
@@ -338,9 +338,11 @@
 
 ## Pre-commit step ordering
 
+The ordering, full-aggregate and PR/master parity rules below govern normal execution. The sole incident-only exception is §"Expedited incident response policy"; its trusted execution context MUST be resolved before these hook members, evidence or delegation are selected. Installation of structural worktree hooks and ordinary mutation authorization remain required.
+
 Lefthook pre-commit runs these commands in order: `00-install-worktree-pack` (delegates to `just install-worktree-pack`; materializes the canonical worktree-discipline pack into the checkout's gitignored `dev-tooling/` from the `livespec-dev-tooling` package that checkout resolves, so every later gate member that reads the pack finds it present and current whether the worktree was created by `just worktree-create`, by a raw `git worktree add`, or before a pin bump; the installer MUST be idempotent, MUST write only files the repository ignores, and MUST NOT relax the byte-identity verifier, which still asserts the installed bytes after the install); `01-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `02-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `03-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest. Commit-msg stage runs two gates in order: first `just check-conventional-commits {1}` (validates the subject prefix matches Conventional Commits 1.0; rejects non-conformant subjects with a structured diagnostic naming the canonical type set per `non-functional-requirements.md` §"Commit and merge discipline"); then `just check-red-green-replay {1}` (the v034 D3 replay hook; where the repository has delegated its commit-time test runs per `non-functional-requirements.md` §"Enforcement-suite invocation" and the commit is from a delegating host, the replay gate's test runs are obtained from the executor against the staged tree, falling back to a run on the committing host when the executor returns no verdict, and the Red/Green judgement and trailer recording remain on the committing host). The Conventional Commits gate runs FIRST so non-conformant subjects fail fast before the heavier replay-mode dispatch. Pre-push runs these commands in order: `00-install-worktree-pack` (the same installer, for the same reason) then `01-check-pre-push` (delegates to `just check-pre-push`, which runs `just check` — the full aggregate — behind the memoizing short-circuit described below, unless the repository has delegated its pre-push gate per `non-functional-requirements.md` §"Enforcement-suite invocation", in which case that recipe, behind the same short-circuit and from a delegating host, obtains the same aggregate's verdict from the executor against the pushed tree, and runs on the pushing host the members that read an authorization held outside the tree, while from a host that is not a delegating host it runs `just check` as above). A repository governed by this contract MUST NOT place any hook command that reads the worktree-discipline pack ahead of `00-install-worktree-pack`.
 
-When the staged tree contains ZERO `.py` files, `just check-pre-commit` runs a CONSERVATIVE doc-only subset (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full aggregate, since the Python-related gates have no work to do on doc-only commits. The classification trigger is the strict "zero `.py` staged" predicate; any `.py` file in the staged tree (even a single test file in Red mode) routes through the full aggregate. This pre-commit subsetting is a LOCAL developer-speed optimization ONLY and is explicitly NOT a merge gate: the pre-commit doc-only subset MAY be wrong or drift out of sync without endangering `master`, because the load-bearing gate that protects `master` — the required CI gate (`non-functional-requirements.md` §"CI as a merge gate (branch protection)") — NEVER subsets, and pre-push is defense-in-depth that runs the same full aggregate — on the pushing host, or, where the repository has delegated its pre-push gate and the push is from a delegating host, on the executor against the pushed tree, save the members that read an authorization held outside the tree, which the pushing host runs. The categorization the pre-commit subset depends on is confined to pre-commit and gates nothing on `master`.
+When the staged tree contains ZERO `.py` files, `just check-pre-commit` runs a CONSERVATIVE doc-only subset (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full aggregate, since the Python-related gates have no work to do on doc-only commits. The classification trigger is the strict "zero `.py` staged" predicate; any `.py` file in the staged tree (even a single test file in Red mode) routes through the full aggregate. This pre-commit subsetting is a LOCAL developer-speed optimization ONLY and is explicitly NOT a merge gate: the pre-commit doc-only subset MAY be wrong or drift out of sync without endangering `master`, because the load-bearing gate that protects `master` — the required CI gate (`non-functional-requirements.md` §"CI as a merge gate (branch protection)") — NEVER subsets on normal master or ordinary PRs, and pre-push is defense-in-depth that runs the same full aggregate — on the pushing host, or, where the repository has delegated its pre-push gate and the push is from a delegating host, on the executor against the pushed tree, save the members that read an authorization held outside the tree, which the pushing host runs. The categorization the pre-commit subset depends on is confined to pre-commit and gates nothing on `master`.
 
 Pre-push and CI run the full aggregate rather than the zero-`.py` subset. Pre-push delegates to `just check` (a pre-push short-circuit on a working tree byte-identical to one that already passed the full aggregate is memoization of the identical check set, not subsetting); where the repository has delegated its pre-push gate and the push is from a delegating host, the same aggregate runs on the executor instead, save the members that read an authorization held outside the tree, which the pushing host runs, and this changes WHERE it runs and not WHAT it verifies. CI in `.github/workflows/ci.yml` MUST run every gating check on a `pull_request` exactly as it runs on `push` to `master` and `merge_group`: no gating job (any job the required all-green gate job lists in its `needs:`) and no `just check` target may be conditioned on the triggering event or on a changeset predicate (such as a `.py`-changed gate) so that it runs on a `master` push but is skipped, or runs a smaller check set, on a pull request. This establishes the **PR gate ≡ master gate** invariant codified in `non-functional-requirements.md` §"CI as a merge gate (branch protection)": the set of checks a change must pass before it merges is identical to the set `master` enforces after it merges, so "nothing can break `master`" is a property of the definitions rather than of anyone's diligence. The earlier zero-`.py` subsetting of pre-push and CI is RETIRED: it rested on the false premise that every `just check` target is a deterministic function of the Python source tree, which ceased to hold the moment a check read a non-Python input (the CI workflow file, `plan/`, the ledger) — letting a change whose only skipped check read such an input merge green and redden `master`.
 
@@ -562,3 +564,19 @@
 `[tool.coverage.run]` is anchored at `livespec/`, `bin/`, `dev-tooling/`, so
 the unit-tier per-file 100% coverage gate does not extend to E2E test
 infrastructure.
+
+## Expedited incident response policy
+
+A governed repository MAY provide the explicit incident-only execution path defined here. EXPEDITED_INCIDENT_RESPONSE selects an authorized repair of one identified incident work item; EXPEDITED_INCIDENT_RESPONSE_REVERT selects an emergency inverse of a recorded incident change and takes precedence. Neither flag grants credentials or changes host, workflow-edit or mutation authorization. The implementation MUST resolve trusted event, incident identity, attempt, phase, repository and base/head before selecting gates, reading evidence, delegating work or applying fallbacks. A marker or ambient flag without the required incident receipt MUST NOT confer an exemption. Malformed values in an ordinary invocation MUST produce a named configuration refusal. Trusted normal master and normal factory follow-up MUST force both flags absent before interpreting inherited values, including malformed ones.
+
+For that authorized repair only, an operator MAY implement in a local secondary worktree without a factory run or green-master precondition. Applicable local gates that finish in less than sixty seconds MUST run and retain real failures; known slow or unclassified work MUST be explicitly deferred before launch. A selected unknown gate reaching sixty seconds MUST terminate its owned children and report deferred-timeout. No hook, replay, delegation or fallback MAY restore the full normal aggregate for the incident repair. A slow suite MUST NOT be divided into nominally fast wrappers. The local repair MUST record changed or directly related tests, existing coverage thresholds scoped to cumulative touched executable files, and one manual reproduction with expected and actual outcomes. Missing focused evidence MUST remain visible risk with an operator disposition; a failing assertion MUST require correction. Incident evidence MUST NOT satisfy normal green-token, coverage, TDD or factory-proof requirements.
+
+The repair MUST carry the exact adjacent legal code or test comment `EXPEDITED_INCIDENT_RESPONSE flag: <incident work-item id>`, including a valid comment carrier for deletion-only or non-commentable changes. Its provenance MUST honestly record deferred replay rather than fabricate normal TDD evidence; historical receipt verification on normal master MUST survive loss of the old environment and PR label. Declared specification amendments MAY be deferred on that same incident, but normal master conformance remains mandatory.
+
+A trusted PR-specific signal and structured incident receipt MUST select only that repair PR and current head. Its CI MUST retain declared fast checks, omit coverage and specification-enforcement execution and dependencies, and disclose each intentional deferral in its stable required aggregate. Head or mode changes MUST invalidate earlier verdicts. An intentionally deferred check MUST NOT be represented as executed or passed. Every master push, normal factory follow-up and ordinary operation MUST retain its complete normal policy with both incident flags disabled.
+
+An incident merge MUST have an independently available, known-good released observer and a durable recovery receipt before merge. The first failing required master leaf job MUST trigger immediate incident recovery without waiting for workflow completion, failure classification, reruns, fix-forward claims, factory work, local quality gates or revert-PR CI. The original master run MUST remain available to completion, including records of failed, skipped, cancelled and never-created required work. Corrected repair attempts MUST retain the same incident identity and require new correction or resolution evidence. An independently provisioned recovery principal MUST merge only the validated complete inverse of the recorded incident change against current master, preserving later unrelated edits, revalidating the expected head, and recording an owned overlap conflict rather than overwriting descendants. The recovery operation MUST remain available through failure of the ledger, credential wrapper, factory or gate runners, reconcile exact receipts afterwards, and fence duplicate or stale actions. This capability MUST be provisioned and proven through the normal rollout; it MUST NOT disable ordinary protection or use a skipped-green CI stub as a substitute for no-check recovery authority.
+
+A successful normal master run MUST cause an unexpedited factory follow-up on the same incident work item that removes the marker and verifies the cumulative original change, evidence and deferred specification debt under normal factory and PR policy. A defect isolated to deferred proof MUST be fixed in that follow-up without reverting otherwise healthy master solely for that finding. A related regression observed on master, another PR or an adopted consumer MUST trigger incident recovery and fence stale cleanup; attribution MUST remain recoverable after closure. The incident MUST remain open until the final normal factory PR and subsequent normal master CI succeed, the marker is removed and deferred debt is repaid. The selected orchestrator owns its store, claims, cancellation, attempt identities and same-item lifecycle realization; this policy does not prescribe those mechanisms.
+
+Generated scaffolds and inherited operator/Driver guidance MUST preserve this exception and the complete normal path through the normally released shared execution interfaces. Implementations MUST inventory actual fleet consumers, custom workflows, alternate stores and runtime boundaries, record implemented, deliberately-normal or not-applicable dispositions, and prove the installed serving versions before enabling use. This feature's own development, release and rollout MUST be normal and unexpedited.
```

## Proposal: Scoped protection and ordinary-policy precedence

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Introduce the maintainer-directed incident-only exception while preserving complete normal validation and the owning-repository boundaries.

### Motivation

Priority-1 plan livespec-dev-tooling-bqnzcm requires a local fast repair and immediate no-check incident recovery followed by same-item normal factory repayment. The reviewed design is in livespec-dev-tooling plan/expedited-incident-response-flag/research/001-charter-expedited-incident-response-flag.md and 002-override-surface-inventory.md. Generated templates templates/orchestrator-plugin/justfile.jinja and lefthook.yml.jinja and operator guidance AGENTS.md/.ai/ci-gate-discipline.md are implementation follow-ups, not changes this proposal silently activates.

### Proposed Changes

Apply the following exact diff through revise. New H2 headings MUST co-edit tests/heading-coverage.json and its generated debt register with implementing owners in that same revision.

```diff
--- SPECIFICATION/non-functional-requirements.md
+++ SPECIFICATION/non-functional-requirements.md
@@ -1306,6 +1306,8 @@
 
 ### CI as a merge gate (branch protection)
 
+**Incident-only precedence.** The ordinary protection, all-green aggregate, reconciler and parity obligations below apply except for an authorized incident repair or recorded emergency revert under `contracts.md` §"Expedited incident response policy". That policy MUST govern only those exact incident operations. Recovery-principal authorization MUST be explicit, narrow and proven against every overlapping protection rule before activation; ordinary actors, including administrators, MUST remain subject to their existing required checks. A normal master push and normal factory follow-up MUST always run the complete normal job graph.
+
 **CI as a merge gate.** Every livespec-governed primary repo's `master` branch MUST have GitHub branch protection configured so that a single all-green gate job is the sole REQUIRED status check. A pull request MUST NOT be mergeable while CI is red: the required-check gate MUST block the merge until that gate job reports success, and the gate job reports success only when every CI job it depends on succeeded — so requiring the one gate job gates the merge on the entire CI matrix. The rule is fleet-wide-by-intent: it applies UNIFORMLY to `livespec` itself, every `livespec-orchestrator-*` plugin, `livespec-dev-tooling`, `livespec-runtime`, and every future sibling repo generated from the copier template per §"Shared content sync — copier template". A repo whose `master` lacks required-check branch protection is out-of-contract regardless of which fleet role it plays.
 
 The protection MUST set `enforce_admins` (no admin bypass — repository administrators are subject to the same red-CI block as every other contributor). The protection MUST NOT enable `strict` (require-branches-up-to-date). Rationale: under `gh pr merge --auto`, `strict` makes GitHub keep a behind PR current by **merging** `master` into its branch, injecting a `Merge branch 'master'` commit that both violates `required_linear_history` and buries the per-commit Red-Green-Replay TDD trailers beneath a trailerless tip — forcing a corrective force-push. Since `master` accepts only rebase-merges (§"Commit and merge discipline"), every PR is replayed onto the current `master` tip at merge time regardless of whether its branch was up to date, so `strict` adds no correctness guarantee. The one case it would have caught — a PR that was CI-green against an older `master` and SEMANTICALLY (not textually) conflicts with the newer tip — is accepted and caught by CI on `master` after the merge. The fleet deliberately does NOT substitute a merge queue: GitHub merge queues are organization-only, and a hand-rolled serialized auto-rebase driver would trade robust per-PR `gh pr merge --auto` (which never orphans a PR and lets GitHub serialize the merge op) for a fragile central loop that can orphan, mis-order, or wedge PRs. The required-check set MUST be exactly the single all-green gate job (the fleet convention names it `ci-green`): a summary CI job whose `needs:` lists every gating job — any job that runs a `just <target>` command or carries a `strategy.matrix.target` list, canonical or not — and which fails whenever any of those dependencies failed or was cancelled. Requiring only the gate job blocks merges on the whole matrix (the gate cannot report success unless every check it depends on did) while keeping the required-check set a single stable context that never churns as checks are added or renamed, so per-check branch-protection edits are never needed again. This is the deliberate replacement for a per-check required set: because branch-protection membership is out-of-band settings (below) with no committed-file record, a per-check required set drifts silently against the CI matrix, whereas the single gate job removes that drift surface by construction. The gate job's guarantee is enforced structurally by `branch_protection_alignment` (below), which reads the live protection via `gh api` and fails on absent protection, an enabled `strict`, or a phantom required check that names no real CI job (a required top-level gate job is accepted), and — from committed files alone — by the companion `ci_matrix_completeness` check, which confirms CI actually runs and gates the whole aggregate: (a) the set of canonical `just check` slugs CI runs is a superset of the tracked static check-target inventory reached by the one-line justfile `check:` recipe — excluding the declared pre-push-only world-gate checks, which assert master/world state rather than the changeset and enforce out-of-band under an admin token — and MUST NOT infer that inventory from the one-line recipe body; and (b) the gate job's `needs:` covers every gating job. A canonical slug that runs at pre-push but never in CI, or a gating job the gate job omits from its `needs:`, therefore FAILS CI once the repo arms the guard (the `LIVESPEC_FAIL_IF_CI_MATRIX_GAPS_EXIST` lever; until then the same finding warns without reddening, so the check can propagate to a not-yet-wired repo safely).
@@ -1320,7 +1322,7 @@
 
 **Re-landing reverted work.** When the reconciler, rather than a session, reverts a merge, the revert pull request MUST link the culprit pull request, and the owning session of the culprit pull request MUST file the re-land work item that the revert-and-reland remedy requires; when the culprit belongs to no live session, the needs-attention issue for the episode MUST name the re-land obligation so the maintainer files it.
 
-These two paths — the reconciler's automatic revert and the progress-bounded fix-forward claim — are the ONLY sanctioned ways past a red `master`. Every other lever, flag, severity knob or carve-out that lets a commit, push, merge or dispatch proceed while the green-master gate reports red remains forbidden. This rule introduces no merge queue, no `strict`, no serialized merge train, and no additional CI on the happy path.
+Outside the explicit incident-only policy above, these two paths — the reconciler's automatic revert and the progress-bounded fix-forward claim — are the ONLY sanctioned ways past a red `master`. Every other lever, flag, severity knob or carve-out that lets a commit, push, merge or dispatch proceed while the green-master gate reports red remains forbidden. This rule introduces no merge queue, no `strict`, no serialized merge train, and no additional CI on the happy path.
 
 **PR gate ≡ master gate.** The set of gating checks a `pull_request` must pass MUST be identical to the set that runs on `push` to `master` (and `merge_group`): no gating job — any job the required all-green gate job lists in its `needs:` — and no `just check` target may be conditioned on the triggering event or on a changeset predicate (such as a `.py`-changed gate) so that it runs on a `master` push but is skipped, or runs a smaller check set, on a pull request. A pull request MAY run ADDITIONAL checks a `master` push does not (for example a release-PR-only stricter gate that skips harmlessly on ordinary PRs); what is forbidden is a pull request running FEWER gating checks than `master`. Non-gating jobs — telemetry export, notifications, any job absent from the gate job's `needs:` — are exempt. Without this invariant a PR gate is a strict SUBSET of the master gate, and a change whose only skipped check reads a non-Python input (the CI workflow file, `plan/`, the ledger) can merge green and redden `master`; that exact failure occurred on 2026-09-04, when a CI-workflow-only pull request merged green and reddened `master` seconds later because the skipped check read the workflow file it changed. This invariant is enforced by the companion `ci_gate_parity` shared check from `livespec-dev-tooling` (§"Shared code sync — livespec-dev-tooling"), which reads `.github/workflows/ci.yml` statically and FAILS when a gating job — at the job level or in its real steps — is conditioned on the triggering event or on a changeset predicate in the FORBIDDEN DIRECTION: so that it runs on a `push` to `master` but is skipped, or runs a smaller check set, on a `pull_request` (a job conditioned to run pull-request-only, which ADDS strictness rather than removing it, is not flagged); like `ci_matrix_completeness` it warns without reddening until the repo arms it via the `LIVESPEC_FAIL_IF_CI_GATE_PARITY_GAPS_EXIST` lever, so the check propagates to a not-yet-fixed repo safely. The two are complementary: `ci_matrix_completeness` confirms every gating check is PRESENT in CI and covered by the gate job's `needs:`; `ci_gate_parity` confirms every such gating check actually RUNS on a pull request rather than being conditionally skipped.
 
```

## Proposal: Incident policy scenarios

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Introduce the maintainer-directed incident-only exception while preserving complete normal validation and the owning-repository boundaries.

### Motivation

Priority-1 plan livespec-dev-tooling-bqnzcm requires a local fast repair and immediate no-check incident recovery followed by same-item normal factory repayment. The reviewed design is in livespec-dev-tooling plan/expedited-incident-response-flag/research/001-charter-expedited-incident-response-flag.md and 002-override-surface-inventory.md. Generated templates templates/orchestrator-plugin/justfile.jinja and lefthook.yml.jinja and operator guidance AGENTS.md/.ai/ci-gate-discipline.md are implementation follow-ups, not changes this proposal silently activates.

### Proposed Changes

Apply the following exact diff through revise. New H2 headings MUST co-edit tests/heading-coverage.json and its generated debt register with implementing owners in that same revision.

```diff
--- SPECIFICATION/scenarios.md
+++ SPECIFICATION/scenarios.md
@@ -831,3 +831,74 @@
   Then the replay gate's test runs execute on the committing host
   And the hook reports that it gated locally
 ```
+
+## Scenario: an authorized incident repair uses the inherited fast path
+
+```gherkin
+Given a governed repository has installed and proven its released incident capability
+And an operator holds a trusted receipt for one incident work item and current repair attempt
+When the operator selects EXPEDITED_INCIDENT_RESPONSE in a secondary worktree
+Then no factory run or green-master precondition blocks the local repair
+And selected fast local checks retain real failures while slow work is recorded as deferred
+And focused related tests, touched-file coverage and one manual reproduction are recorded
+And the legal adjacent incident marker names the same work item
+```
+
+## Scenario: incident PR selection cannot weaken normal master validation
+
+```gherkin
+Given a trusted signal and receipt select one incident repair PR and exact head
+When that PR runs its declared retained fast checks
+Then its stable required aggregate discloses omitted coverage and specification work
+And a changed head invalidates its prior verdicts
+When the repair merges and master CI starts with malformed inherited incident flags
+Then the trusted master context disables both flags before parsing them
+And the complete normal master job graph runs
+And partial incident evidence cannot satisfy normal validation
+```
+
+## Scenario: an incident master failure takes immediate scoped recovery
+
+```gherkin
+Given an incident merge has a durable receipt and an independently running released observer
+And a later unrelated change is present on master
+When the first required master leaf job fails while sibling jobs still run
+Then the recorded incident's complete inverse is applied against the current expected head
+And unrelated later changes are preserved or an owned overlap conflict is recorded
+And the narrowly authorized recovery principal requires no local quality gate, factory run or pre-merge CI wait
+And the original master run is retained through its remaining terminal results
+And stale or duplicate actions cannot mutate a corrected incident attempt
+```
+
+## Scenario: incident repayment uses the same item and complete original scope
+
+```gherkin
+Given the incident repair's normal master CI succeeds
+When the selected orchestrator routes its normal factory follow-up
+Then the same incident work item carries a new unexpedited PR removing the marker
+And normal factory and PR validation include the cumulative original change and deferred debt
+And a defect isolated to that deferred proof is repaired in the follow-up without reverting healthy master solely for it
+And the incident cannot close before the normal follow-up merge and subsequent normal master CI succeed
+```
+
+## Scenario: a related regression resumes incident recovery after closure
+
+```gherkin
+Given incident attribution survives normal completion and process restarts
+When a related regression is observed on master, another PR or an adopted consumer
+Then recovery resumes for the same incident identity
+And stale cleanup and queued adoption are fenced
+And affected adopted consumers receive owned corrective rollout
+```
+
+## Scenario: an ordinary operation does not inherit an incident exemption
+
+```gherkin
+Given an ordinary operation contains a historical incident marker or unrelated incident flag
+When it lacks the authorized receipt for the selected incident operation
+Then it receives no incident exemption
+And ordinary work retains complete gate and authorization obligations
+When a trusted normal factory follow-up inherits malformed incident values
+Then it forces both flags absent before parsing them
+And no expedited cache or partial proof satisfies its normal validation
+```
```
