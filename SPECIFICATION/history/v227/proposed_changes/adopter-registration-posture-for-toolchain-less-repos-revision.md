---
proposal: adopter-registration-posture-for-toolchain-less-repos.md
decision: modify
revised_at: 2026-10-21T07:25:52Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5 (petri-factory-on-gmktec f6cc18a6)
---

## Decision and Rationale

Both findings are accepted in substance. Finding 1 reconciles the register-before-wiring guide with the fail-loud adopter plugin-currency row that reddened every livespec-dev-tooling world gate when livespec PR #2913 registered seven unwired released adopters (reverted by #2915): a released adopter is registered only after its wiring satisfies the sweep, and an unwired one may be registered with posture none. Finding 2 names the instruction-only class for toolchain-less host and deploy repositories, held to Plugin-currency only and satisfied through the already-implemented livespecPluginCurrencySuccessor declaration (livespec-dev-tooling fleet/_rows_claude_plugin.py). The text is modified, not accepted verbatim, because as filed it contradicted the existing definitions: every adopter was defined as a governed repo carrying a .livespec.jsonc and a justfile, and the Shell-and-Justfile section had no binding sentence to amend. Session-ratifiable under the standing R100 scope after an independent review, by a separately spawned read-only opus subagent (a023ec3b16bc0c7ec, no role in drafting), which returned NO BLOCKERS on round 4 at 2026-10-21T07:25:05Z after blockers in rounds 1 and 2 were fixed. Implementing the profile value in livespec-dev-tooling's manifest parser and sweep (today's parser rejects instruction-only as malformed-adopter) is follow-up work owned by livespec-zyh7uo.

## Modifications

1. Scenarios are written in this spec's house form (gherkin fence, Feature plus Scenario blocks); finding 1's scenario is split into two Scenario blocks. 2. The instruction-only exception is attached where the binding statements actually live: both member descriptions in the Conformance Pattern named-members paragraph, the Request-budget discipline binding sentence, and a new explicit binding sentence at the head of Shell and Justfile discipline (which had none). 3. Ubiquitous language defines an instruction-only adopter as the one kind of adopter that is not a governed repo; the Adopters paragraph's opening and profile description, the Profiles paragraph tail, the just keystone, the onboarding verb paragraph and the tenant credential set each gain a matching qualifier. 4. The inserted profile sentence no longer claims SessionStart ensure-plugins wiring can satisfy currency for a repository without a justfile; the successor declaration in the committed .claude/settings.json is the only route, and the Plugin-currency Installer slot says so. 5. tests/heading-coverage.json and the shrink-only tests/heading-coverage-debt.json each gain two TODO rows owned by livespec-zyh7uo for the two new scenario headings (spec-first admission).

## Resulting Changes

- non-functional-requirements.md
- scenarios.md
- ../tests/heading-coverage.json
- ../tests/heading-coverage-debt.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-21T07:25:05Z
verdict: NO BLOCKERS
proposal_stem: adopter-registration-posture-for-toolchain-less-repos
content_digest: 828b2b1ea5e45cbe03385d2b40ae1948eb6b2de9db45616118041fd442f7a500
