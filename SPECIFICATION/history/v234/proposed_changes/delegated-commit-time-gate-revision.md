---
proposal: delegated-commit-time-gate.md
decision: modify
revised_at: 2026-10-30T21:11:27Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

MODIFY. Ratifies delegation of the commit-msg replay gate's test runs to the remote executor, against the staged tree, with the Red/Green judgement and trailer recording kept on the committing host. Modified to the later design record, livespec-dev-tooling plan delegated-commit-time-gates (research/001 charter; epic livespec-dev-tooling-2fekp6, carrier livespec-dev-tooling-sewnfp). That record holds a coordinator ruling that this revise take the proposal as a MODIFY. On an absent verdict, a commit-time leg falls back to a real local run and is never refused for the executor's absence alone; that departs from the proposal's 'Refusal, not fall-through', and from The verdict for commits only, while pre-push keeps the v229 refusal. Trailers identify the executor run and the staged tree. Commit-time delegation of the pre-commit check aggregate is deferred, so it stays undelegated. Adds the four-scenario section '## Delegated commit-time replay test runs', with a TODO coverage row and a debt-register row owned by livespec-3zug5z. Delegated decision; a first review returned NO BLOCKERS with nits, two of which were folded in, and a fresh review returned NO BLOCKERS on these exact bytes. Reviewer: separately spawned read-only Sonnet 5.5 agent a1ad27fc62e8586aa.

## Modifications

(1) Scope narrowed to the commit-msg replay gate's test runs (Red, Green and any suite run). The pre-commit check aggregate is stated as not delegated, contracts.md 03-check-pre-commit is unchanged, and the doc-only-subset sentence is dropped as moot. (2) 'Refusal, not fall-through' replaced by 'An absent verdict falls back to a local run, never to a refusal'. The local run executes the tests, trailers come only from it, the host reports that it gated locally, and the departure from The verdict is stated as covering commits only. (3) The read-through of the pre-push properties is made explicit: The set reads as the replay gate's test runs for the staged tree, and only The verdict's definition of when a verdict exists applies, so an expected Red failure is judged, not refused. (4) Trailers must identify the executor run and the staged tree. (5) Scenarios rewritten to match: the refusal scenario becomes a fallback scenario, under one new H2, with heading-coverage and debt-register rows owned by livespec-3zug5z.

## Resulting Changes

- non-functional-requirements.md
- contracts.md
- scenarios.md
- ../tests/heading-coverage.json
- ../tests/heading-coverage-debt.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-30T21:09:51Z
verdict: NO BLOCKERS
proposal_stem: delegated-commit-time-gate
content_digest: 68239b73be18915d219566e8baeab0e02b83841c19a0548321b85f662ef71b4a
