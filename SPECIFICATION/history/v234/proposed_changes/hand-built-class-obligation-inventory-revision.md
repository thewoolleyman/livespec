---
proposal: hand-built-class-obligation-inventory.md
decision: modify
revised_at: 2026-10-30T21:11:27Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

MODIFY. Names, in the Obligations per repo class rule, the construction inventory that a hand-built member (a class outside the enforcement suite's template-born set) must satisfy in place of copier generation, and adds the New-obligation discipline sentence verbatim. The inventory is corrected to what the orchestrator-plugin copier template actually ships, and scoped to construction so it does not contradict contracts.md's statement that .ai topic files are optional. Delegated decision; the independent reviewer returned NO BLOCKERS on these exact bytes. Reviewer: separately spawned read-only Sonnet 5.5 agent aeb10f04a8d1ab5b7.

## Modifications

(1) Inventory corrected to what the copier template (templates/orchestrator-plugin/) actually ships. Dropped: the repo-root CLAUDE.md symlink, the plan/ store, and tests/heading-coverage.json, none of which the template carries, and the retired cross_repo_targets key. Kept: the AGENTS.md .ai/ convention block plus a referenced seed .ai/<topic>.md, the .claude/CLAUDE.md symlink, a committed .claude/settings.json, and external_references, which is now cited to constraints.md Allowlist mechanism, where it is already required. (2) Scoped to construction, stating explicitly that it does not make .ai/<topic>.md files mandatory afterwards, to stay consistent with contracts.md Fleet agent-instruction core. (3) Dropped the expiring 'two retrofits are already known to be outstanding at the time of writing' sentence. (4) The two inserted paragraphs merged into the single-paragraph Obligations per repo class rule. The New-obligation discipline sentence is verbatim.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-30T21:09:51Z
verdict: NO BLOCKERS
proposal_stem: hand-built-class-obligation-inventory
content_digest: 45445e2f3826d4dcb66aa8402d20baf7923624c799cb7761499d9555bb0596d3
