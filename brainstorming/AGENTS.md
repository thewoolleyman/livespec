# brainstorming/ orientation

Pre-bootstrap design and process artifacts. **Frozen at Phase 0** —
no further edits to anything under `brainstorming/` once the Phase 0
freeze commit lands. From Phase 0 onward, `SPECIFICATION/` (created
in Phase 6) is the living oracle for livespec design.

## Where to look

| Subdirectory | Status | What's there |
|---|---|---|
| `approach-2-nlspec-based/` | **Active design**, frozen at v022 | The frozen PROPOSAL.md, the bootstrap PLAN, companion docs (style discipline, deferred items, lifecycle diagrams), and per-version history. **Start here.** |
| `approach-1-openspec-inspired/` | Abandoned alternative | An earlier OpenSpec-inspired design direction that was set aside in favor of the NLSpec-based approach. Reference-only. |

## Editing rules

- During pre-Phase-0: edits via formal `vNNN/` revisions inside
  `approach-2-nlspec-based/history/`. The bootstrap skill's
  halt-and-revise sub-flow walks through this mechanism if drift
  surfaces during pre-bootstrap critique.
- After Phase 0: this directory tree is **immutable**. Hand-editing
  any file under `brainstorming/` is a bug in execution per Plan §3.
  If you spot drift, route through the bootstrap skill's "Report an
  issue first" gate; the skill chooses between halt-and-revise
  (pre-Phase-6) or propose-change against `SPECIFICATION/`
  (post-Phase-6).

## After bootstrap completes

This directory stays in place as historical reference. The production
app — `.claude-plugin/`, `SPECIFICATION/`, `dev-tooling/`, `tests/`,
`pyproject.toml`, `justfile`, `lefthook.yml`, etc. — does NOT
reference anything under `brainstorming/`. Phase 11 verifies that
invariant.
