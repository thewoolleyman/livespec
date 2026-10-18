---
proposal: auto-memory-guard-covers-every-write-route.md
decision: modify
revised_at: 2026-10-18T16:31:15Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted with amendments. The ratified Write-only registration let Edit, MultiEdit and shell writes reach the harness-private memory store in governed projects (52 notes on one host, 2026-10-18), contradicting this file's own Fleet agent-instruction core rule that the store is NEVER the home for durable guidance. Widening the Claude redirect to every write route and the Codex guard to shell writes enforces that rule. The independent ratification review found one blocker in the proposal as filed: the Codex paragraph's final sentence still limited the guard to the Codex store, contradicting the widened intercept. The modifications resolve it and fold in the reviewer's four non-blocking notes. Independent read-only reviewer: an Opus sub-agent session named ratification-reviewer-auto-memory, which returned BLOCKERS on the proposal as filed and NO BLOCKERS on the final bytes.

## Modifications

Beyond the proposal's three substitutions: (1) the Codex paragraph's final sentence now reads 'acts only when it POSITIVELY identifies a write into an agent memory directory' (the proposal said the rest of that paragraph must remain unchanged; that instruction is superseded because it left the paragraph self-contradictory); (2) the Codex durable-guidance route uses the same 'short discoverable entry in AGENTS.md pointing at a .ai/<topic>.md file, or AGENTS.md alone when short' wording as the Claude route, since the paragraph says its reason routes identically; (3) 'covers the manual-write path only' becomes 'covers the manual-write and shell-write paths only'; (4) the Claude Bash sentence opens 'under the same governed-project gate stated below'; (5) the Claude file-tool route also acts when the target lies under ~/.codex/memories/, matching the Bash route.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-18T16:30:09Z
verdict: NO BLOCKERS
proposal_stem: auto-memory-guard-covers-every-write-route
content_digest: a34bad7fec93a2f93b7d2a9d9db33ac8e01068a678dfe2fd7f5ef1f28326cdeb
