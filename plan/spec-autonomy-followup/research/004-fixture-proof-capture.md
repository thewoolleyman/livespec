# 004 — Fixture proof, captured

Written 2026-10-30 by Claude Code session `ce19c72a-238e-4973-bbde-0a4f85197eb8` (plan owner). This
is the capture for plan assertions 4 and 5. The design is in note 002. The kit that rebuilds and
reruns it is `fixture/` beside this note: `fixture/build-and-run.sh <empty-dir>`.

## Build under test

- `livespec@livespec` **0.44.3** (git `7ec25c43`, tag `v0.44.3`), installed at project scope from the
  `release` ref.
- `livespec@livespec-driver-claude` **0.12.1** (git `0a3e2f78`, tag `v0.12.1`), installed the same way.
- The installation record (`~/.claude/plugins/installed_plugins.json`) showed both entries with
  `projectPath` equal to the fixture root.
- Claude Code 2.1.314.

The fixture's `.livespec.jsonc` sets `revise_decision_mode: delegated`, `ratification_review:
manual-spawn` (deliberately), and `ratification_reviewer_model: ["sonnet"]`.

## What was observed

| Probe | Input | Observed |
|---|---|---|
| A | `greeting-trailing-period` — a plain, non-drift proposal with no `decision_policy` | The run asked the user nothing. It spawned one separate read-only `Agent` reviewer (`sonnet`) even though `ratification_review` is `manual-spawn`. The reviewer returned `NO BLOCKERS`. The decision was `modify` (the decider added a matching scenario). `history/v002/` was written. The revision record's `## Ratification Review` and the governance journal's `revise_decision` event carry the same `content_digest` `32bb3153ca80a07fb7052c26ab2d8a42f5394dabb2ea2efe9a5e3c044bf69109`; the journal shows `effective_mode: delegated`, `effective_source: global`, `review_outcome: NO BLOCKERS`, `final_outcome: proceed`. |
| B | `unknown-name-wording` — same shape, `decision_policy: manual` | The run drafted a decision and stopped, asking the maintainer to confirm it and to supply or authorise review evidence. It did NOT auto-spawn the reviewer (correct: the proposal is manually owned, so `manual-spawn` applies). No `v003`; the journal is byte-identical to its state after A. |
| C | `latency-matches-implementation` — an implementation-to-spec drift proposal | The run identified it as drift, drafted `accept`, and stopped for explicit maintainer confirmation and review evidence, stating it would set `drift_origin: true` and `human_decision_confirmed: true` only after confirmation. Zero reviewer spawns. No `v003`; the journal is unchanged. |
| D | The released `revise.py` given a `drift_origin: true` decision with COMPLETE, digest-exact reviewer and delegated-decider evidence and no `human_decision_confirmed` | Exit code 4: `revise: human decision input required: consensus-tier evidence is absent, stale, or non-conforming`. No revision written; the clone's tree is unchanged. |

Cost: A $1.18, B $0.67, C $0.52 (headless session totals).

## The one interpretation this proof depends on

In probe A the delegated decider is the session driving `revise`; the journal names it
`claude-opus-5-5`. The ratified clause asks for "an independent delegated decider's acceptance"
beside the auto-spawned reviewer. The governing design record (`plan/archive/spec-side-autonomy/
research/brainstorm.md`, "The delegated path composes review + decision as two independent AIs")
defines the two independent AIs as the auto-spawned adversarial reviewer and the delegated decider,
where the decider is the LLM that the old in-dialogue "delegate remaining proposals to the LLM" toggle
handed the decision to. Read that way, A satisfies the contract: the reviewer is a separately spawned
agent and the decider is the revise LLM. A reading that requires a THIRD agent as decider would make
A a finding against the shipped core, not against this plan's wording repairs, and would route to a
proposed change.

## Assertions 1–3 at release

- Assertion 1: `thewoolleyman/livespec` `release` branch, `.claude-plugin/prose/revise.md`, carries
  "only when the resolved mode or a floor requires it" (v0.44.3).
- Assertion 2: the three Drivers' `release` branches carry "Accept, modify, or reject" in the revise
  binding description and the confirmation-dialogue scoping sentence (v0.12.1, v0.8.4, v0.6.2).
- Assertion 3: `livespec-orchestrator-beads-fabro` PR #3992 (`0f2cfd89`) merged; NOT yet released.
  By coordinator ruling it ships with that repository's next organic release, not a manufactured one.
