---
topic: family-universal-agent-instruction-core
author: claude-opus-groom-livespec-ad4ov7
created_at: 2026-06-22T05:15:56Z
---

## Proposal: family-universal-agent-instruction-core

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Every livespec-family member MUST carry the family-universal agent-instruction core (the shared sections of the canonical AGENTS.md, including the Beads runtime prerequisites) and the beads-access guard, with .claude/CLAUDE.md as a symlink to ../AGENTS.md; the dev-tooling fleet MUST mechanically enforce their presence. This gives the inheritance pipeline (copier template -> per-repo AGENTS.md) a contract backing so the agent-instruction surface stops drifting silently.

### Motivation

An agent operating in an impl/orchestrator plugin repo could not find the rule 'all beads/Dolt access goes through the 1Password wrapper with-livespec-env.sh; an auth failure means you are outside the wrapper; never touch the DB directly' because that rule lives only in upstream livespec/AGENTS.md (the 'Beads runtime prerequisites' section) and was never propagated: the copier template's AGENTS.md is near-empty (~30 lines vs upstream ~325), so every impl repo inherits a thin AGENTS.md. The result was a multi-turn interactive bd access failure. The same gap left .claude/CLAUDE.md drifting (one repo regressed the ../AGENTS.md symlink into a divergent real file). The spec inherits cleanly but the agent-instruction surface does not, and nothing mechanically catches the drift.

### Proposed Changes

Add a family-contract clause (contracts.md, with the mechanically-checkable invariant cross-referenced in constraints.md) stating:

1. There is a designated family-universal agent-instruction core: the subset of the canonical upstream AGENTS.md sections that apply to every family member (at minimum: Beads runtime prerequisites, Repository mutation protocol, Agent prerequisites for plugin work, Daily commands, Revise co-edit discipline). The impl-plugin copier template MUST ship this core so generated repos inherit it; repo-specific sections are additive on top.

2. Every family member MUST expose its agent instructions as a canonical AGENTS.md with .claude/CLAUDE.md a symlink to ../AGENTS.md (single source of truth; no hand-maintained divergent duplicate).

3. Beads-backed members MUST carry the Beads runtime prerequisites section describing the collapsed shared bare BEADS_DOLT_PASSWORD model and the with-livespec-env.sh wrapper (authored once upstream and referenced, not re-written per repo).

4. A beads-access guard (a PreToolUse hook shipped in the template) MUST block bare bd / dolt / mysql against the tenant unless run under with-livespec-env.sh.

5. The dev-tooling fleet OBLIGATION_ROWS MUST mechanically assert (1)-(4) so any drift is un-mergeable, mirroring the existing beads tenant-connection consistency row.

Realization is tracked under impl-side coordinating epic livespec-ad4ov7 (grooming filed the ready slices: template enrichment, guard hook, fleet rows, copier propagation).
