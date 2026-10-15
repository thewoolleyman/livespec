---
topic: red-master-self-healing-revert-by-default
author: claude-opus-5-5
created_at: 2026-10-14T02:42:06Z
---

## Proposal: Red master heals by revert-by-default, with a progress-bounded fix-forward claim

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Amend §"CI as a merge gate (branch protection)" so that the post-merge half of the no-`strict` decision has a mechanism: a deterministic, LLM-free master-health reconciler, shipped from livespec-dev-tooling and installed in every fleet repository by committed automation, heals a red `master` by reverting the culprit merge by default. The one sanctioned alternative is a fix-forward CLAIM, which holds the revert only while the claimed fix makes measurable progress and never beyond a hard cap. Flake and infrastructure failures never produce a revert. Three scenarios state the behaviour.

### Motivation

v126 dropped `strict` and accepted that a semantic conflict between two individually-green pull requests is "caught by CI on `master` after the merge", but specified nothing about what happens next. On 2026-10-14 livespec-orchestrator-beads-fabro master was red for ~38 minutes (PR #2917, run 38494465107) while every factory dispatch from that repository was refused by the green-master gate; a fix-forward was still in its pre-push gate when a manual server-side revert (#2918) landed, and the reverted work then had to be re-landed. Revert-vs-fix-forward was decided by whichever actor happened to be fastest. An August 2026 overseer incident (two green PRs merged 87 s apart, master red ~70 min) has the same shape. The maintainer has ruled out a merge queue (repositories are personal), `strict` with an eager rebase-updater (up to N^2 CI runs per merge burst), and a serialized merge train (loses parallelism and deadlocks exactly when master is broken); the remedy is to make red master self-healing. Plan red-master-self-healing (livespec-dev-tooling epic livespec-dev-tooling-zcp5vb, child livespec-dev-tooling-4v2yrw) carries the design. THIS PROPOSAL REQUIRES THE MAINTAINER'S OWN RATIFICATION: it changes ratified fleet policy, so a delegated or autonomous revise MUST NOT accept it; the revise is walked with the maintainer. The four values below marked (maintainer call) are this session's recommendations, stated explicitly so the proposal is complete; the maintainer accepts or modifies each in that revise: (1) who may claim a fix-forward, (2) the hard-cap value, (3) how stall step durations are set, (4) whether a merely 'likely' revert may merge at the cap. Calibration data for (3) is being measured by livespec-dev-tooling-s7ctpr and will be cited on the plan epic when it lands.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"CI as a merge gate (branch protection)", insert the following paragraphs immediately after the paragraph that ends "...is accepted and caught by CI on `master` after the merge." (the merge-queue rejection sentence and what follows stay unchanged):

**Red master heals itself: revert by default.** Because a semantic conflict is caught only after the merge, every fleet repository MUST carry a master-health reconciler that returns a red `master` to green without a human or agent session acting. The reconciler MUST be a single deterministic module shipped from `livespec-dev-tooling` per §"Shared code sync — livespec-dev-tooling", run by a thin per-repository workflow shim on GitHub-hosted runners (so it works when self-hosted capacity is the failure), triggered on completion of `master` CI, on events of the pull requests it manages, and on a schedule of at most five minutes. The shim MUST be installed and reconciled by committed fleet automation (`wire-fleet-member`) and MUST NOT be configured by hand; a fleet conformance row MUST fail a repository whose shim is missing or drifted. The reconciler MUST be stateless: each run MUST read current truth from the forge (per-commit `master` CI status, open revert pull request, fix-forward claim, fix pull request state and CI) and take AT MOST ONE next step, so a crashed, missed or duplicated run cannot wedge it. No decision the reconciler takes MAY depend on an LLM call; an LLM MAY only author optional advisory text that no decision reads.

On a red `master` the reconciler MUST: (a) re-run the failed jobs once and classify the failure as flake or infrastructure when the re-run passes, when the same failure also appears on unrelated commits, or when the failure names an outage (no runner, expired credential, unreachable registry) — a flake or infrastructure failure MUST NOT produce a merged revert and MUST instead raise a needs-attention signal; (b) identify the culprit as the earliest red `master` commit whose parent was green; (c) open a revert pull request of the culprit merge through the forge's own revert API, so the revert is web-flow signed and qualifies for the server-side-revert exemption of the Red-Green-Replay range gate; the revert pull request MAY be opened while classification is pending, but MUST NOT be merged before the failure is classified as a genuine regression. With no fix-forward claim in force, the reconciler MUST release the revert pull request for merge as soon as its own CI is green. A revert whose own CI is not green MUST NOT be merged; the reconciler MUST raise a needs-attention signal instead. The needs-attention signal MUST be one idempotent forge issue per red episode carrying a fixed label, so it is reachable from a hosted runner without ledger access.

**The one sanctioned alternative: a progress-bounded fix-forward claim.** A fix-forward claim MUST be mechanical: a comment on the reconciler's revert pull request naming the fix pull request. (maintainer call 1) A claim is valid only when posted by the maintainer's forge login, or by the identity that opened the culprit pull request carrying a `Claimed-By:` line naming the owning session; any other claim MUST be ignored. A valid claim HOLDS the revert while the fix makes PROGRESS, where progress is a forward transition through: fix pull request opened or a new commit pushed; fix CI started; fix CI green or reporting fewer failing checks than before; auto-merge armed; fix merged; `master` CI on the fix started; `master` CI green. The reconciler MUST release the held revert when the fix THRASHES: the same check fails repeatedly; a new commit does not reduce the failing set; new checks start failing; the fix merged and `master` is still red; more than one fix pull request is claimed; or no forward transition occurs within the stall duration of the current step. (maintainer call 3) Each step's stall duration MUST be derived from the measured distribution of that step across past fleet red-master episodes — the p90 of the step multiplied by a recorded margin — and MUST be recorded in committed configuration, never set by hand.

**The hard cap.** (maintainer call 2) Once `master` has been red for the hard cap — two hours by default, overridable per repository only through committed configuration — the reconciler MUST land the revert regardless of fix-forward progress, but ONLY when the revert is proven: its own CI is green. (maintainer call 4) A revert that is merely expected to fix the failure MUST NOT be merged on that expectation; when the revert's CI is not green at the cap, the reconciler MUST NOT merge it and MUST raise a needs-attention signal for a human. A `master` red longer than a configured threshold with no revert pull request in flight MUST itself surface as a needs-attention item, and a scheduled drill MUST prove the revert path end to end on a throwaway branch, surfacing a failed drill as needs-attention.

**Re-landing reverted work.** When the reconciler, rather than a session, reverts a merge, the revert pull request MUST link the culprit pull request, and the owning session of the culprit pull request MUST file the re-land work item that the revert-and-reland remedy requires; when the culprit belongs to no live session, the needs-attention issue for the episode MUST name the re-land obligation so the maintainer files it.

These two paths — the reconciler's automatic revert and the progress-bounded fix-forward claim — are the ONLY sanctioned ways past a red `master`. Every other lever, flag, severity knob or carve-out that lets a commit, push, merge or dispatch proceed while the green-master gate reports red remains forbidden. No merge queue, no `strict`, no serialized merge train, and no additional CI on the happy path is introduced by this rule.

Consequential non-spec edit (outside the spec tree, so not a target file here): after this proposal is ratified, livespec `.ai/ci-gate-discipline.md` MUST be amended by its own pull request to name the reconciler's automatic revert and the progress-bounded fix-forward claim as the sanctioned remedies while still forbidding every other lever; the directive edit MUST NOT land before ratification.

In SPECIFICATION/scenarios.md, append three H2 scenarios:

## A red master with no fix-forward claim heals by revert

Given a fleet repository whose `master` CI fails on a merged pull request
And the failure fails again on re-run and names no outage
When the master-health reconciler runs
Then it opens a web-flow revert pull request of the culprit merge without any session acting
And it merges that revert once the revert's own CI is green
And `master` returns to green.

## A progressing fix-forward holds the revert and a thrashing one releases it

Given a red `master` with an open reconciler revert pull request
And a valid fix-forward claim naming a fix pull request
When the fix pull request advances through its forward transitions within each step's stall duration
Then the revert stays held and `master` turns green through the fix
But when the fix stalls past a step's stall duration or its failing set does not shrink
Then the reconciler releases the revert, which merges once its own CI is green.

## A flaky or infrastructure failure, or an unproven revert at the cap, raises needs-attention instead of merging

Given a red `master`
When the failure passes on re-run or names an outage
Then no revert is merged and one needs-attention issue for the episode is raised
And given a genuine regression red for the hard cap whose revert CI is not green
Then the reconciler does not merge the revert and raises a needs-attention issue.

The revise that accepts this proposal MUST add `tests/heading-coverage.json` entries for the three new `scenarios.md` H2 headings and `clauses[]` links from the new clauses' gap-ids to them, in the same change.

## Proposal: Every fleet CI check is invariant under rebase-merge metadata

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Add a rule to §"Commit and merge discipline" that no fleet CI check may depend on a commit's SHA, committer date or committer timezone, because rebase-merge mints a new commit whose metadata differs from the one the pull request's CI judged. A check reads tree content, author date, or UTC instants instead.

### Motivation

The 2026-10-14 red master in livespec-orchestrator-beads-fabro was caused by metadata alone: PR #2917 passed PR CI, rebase-merge minted commit 35fea321 with a committer date of 2026-10-13T18:12:41-07:00, and `check-heading-coverage-debt-register` read `%cs` (the committer date in the commit's own timezone), flipping its verdict on `master`. Nothing anyone could do at PR time would have caught it, and it is the one class of red master the self-healing reconciler should never have to heal. Filed as livespec-dev-tooling-a6gq5n (first instance) and livespec-dev-tooling-yfqvqm (fleet audit and repair). This proposal is the spec rule that prevents reintroduction.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Commit and merge discipline", append after the paragraph beginning "`master` accepts only **rebase-merge**.":

**Rebase-merge metadata invariance.** Because rebase-merge replays every pull-request commit onto `master` as a NEW commit — with a new SHA and a new committer date and timezone — a CI check whose verdict depends on that metadata can pass on the pull request and fail on `master` with no code change. Every fleet CI check MUST therefore be invariant under rebase-merge metadata: no check MAY derive its verdict from a commit SHA, a committer date, or a committer timezone. A check that needs time MUST read the author date or an instant normalized to UTC; a check that needs identity MUST read tree content or commit-message trailers, which rebase-merge preserves. A pull request that is green before rebase-merge MUST NOT turn `master` red through commit-metadata differences alone.

In SPECIFICATION/scenarios.md, append one H2 scenario:

## A green pull request stays green after rebase-merge

Given a fleet pull request whose CI is green
And whose commits carry a committer timezone that differs from UTC
When it is rebase-merged and `master` CI runs on the newly minted commits
Then every check returns the same verdict it returned on the pull request.

The revise that accepts this proposal MUST add a `tests/heading-coverage.json` entry for the new `scenarios.md` H2 heading and a `clauses[]` link from the new clause's gap-id to it, in the same change.
