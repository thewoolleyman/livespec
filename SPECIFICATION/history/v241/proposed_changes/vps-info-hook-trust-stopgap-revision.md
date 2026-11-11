---
proposal: vps-info-hook-trust-stopgap.md
decision: modify
revised_at: 2026-11-11T21:08:35Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Modified under delegated revise authority (legacy-coordinator-agent, ruling R301 under delegation R493; --only-topic, so gitops-deployment-topic and orchestrator-roll-currency-exception stay pending). A first cut of this pass accepted the proposal as filed (draft livespec#3175, superseded). The coordinator graded that cut PASS-WITH-FIXES, adopting the first independent review's non-blocking observations as two required and two recommended changes, and this decision applies all four. The rule is unchanged: an automated Codex hook-trust writer other than livespec-driver-codex stays out of every plugin whose marketplace the installed Driver can release-verify. It may trust user-level hooks and plugins the Driver cannot release-verify, and it leaves a plugin's hooks to the Driver whenever it cannot tell. That is what thewoolleyman/vps-info#77 (last commit 2e912f77) shipped in services/codex-config/. It is a host-observable invariant about who may establish trust, so it belongs in core beside the Codex Driver guards; the systemd units and reconciler stay in vps-info. Marketplace versus plugin granularity (review observation 4, noted only, at the coordinator's direction): the paragraph keys coverage on the marketplace, while livespec-driver-codex verifies per plugin against the release tag of the installed version. The paragraph leaves that determination to the installed Driver and never fixes a list in the writer. Its fail-to-the-Driver rule for every undeterminable case is the conservative reading of that difference, so no spec change is made for it. The heading-coverage co-edit adds an integration-tier TODO row owned by livespec-75ttpw. A fresh independent sonnet review of these final bytes reported NO BLOCKERS.

## Modifications

Four changes relative to the proposal's text, from the coordinator's PASS-WITH-FIXES grade of the accept-as-filed cut. (1) Required: the contracts.md paragraph is scoped to an AUTOMATED host-level writer (a timer, script, or reconciler). The over-reaching purpose clause "so that trust in such a plugin's hooks is established only by the Driver, from release-verified bytes" becomes "so that no automated writer substitutes for the Driver's release verification of such a plugin's hooks". A sentence states that an operator's interactive answer to Codex's own hook-trust prompt is not an automated writer and is outside the paragraph. This matches the maintainer's 2026-11-02 ruling that the coordinator may always answer such a prompt with trust to unblock a Codex pane. (2) Required: both scenarios are scoped to an automated writer configured to trust automatically every hook it is permitted to trust, so the Then that asserts trust records no longer exceeds the contract's MAY. The MUST NOT assertion stays unconditional. The Feature, both Scenario names and the H2 are reworded to match, and the H2 is now "An automated non-Driver Codex hook-trust writer leaves release-verifiable plugins to the Driver". (3) Recommended: "the Driver's own release-verification resolver cannot be loaded or raises" becomes "the installed Codex Driver's release verification cannot be consulted (the writer cannot load it, or it raises an error)". That wording has an antecedent in livespec-driver-codex's spec, and the scenario's Given follows it. (4) Recommended: one clause states that the paragraph does not govern trust in project-level hooks. The tests/heading-coverage.json row carries the reworded heading.

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-11T21:08:02Z
verdict: NO BLOCKERS
proposal_stem: vps-info-hook-trust-stopgap
content_digest: 62617dab2b914bacfe7b1b177be85cbdeeaf3847ff566a228a55b74ec9049325
