---
proposal: finding-schema-warn-status.md
decision: accept
revised_at: 2026-05-24T03:16:00Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Path A from memo mm-twt0yw: extend the Finding `status` enum to include `warn`, codify the warn-status exit-code contract in contracts.md, and update the schemas + dataclass + doctor supervisor docstring in lockstep. The proposal's diffs are applied verbatim; no modifications are required. This unblocks li-f5wmjr piece 2 (the three impl-side cleanup invariants) and also unblocks `no-stale-gap-tied` (independent of li-f5wmjr) with a single schema extension.

## Resulting Changes

- contracts.md
- ../.claude-plugin/scripts/livespec/schemas/finding.schema.json
- ../.claude-plugin/scripts/livespec/schemas/doctor_findings.schema.json
- ../.claude-plugin/scripts/livespec/schemas/dataclasses/finding.py
- ../.claude-plugin/scripts/livespec/doctor/run_static.py
