# approach-2-nlspec-based/ orientation

The active design approach for livespec. **Frozen at v022.** Do not
modify any file in this directory or under `history/` once Phase 0
completes; further evolution happens in `SPECIFICATION/` via the
governed propose-change/revise loop.

## Key files

| File | Purpose |
|---|---|
| `PROPOSAL.md` | The v022-frozen design specification. Source of truth for Phase 1-5 of the bootstrap; superseded by `SPECIFICATION/` from Phase 6 onward. |
| `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` | The execution plan. The bootstrap skill reads this as the oracle for what to do in each phase. |
| `livespec-nlspec-spec.md` | NLSpec discipline rubric (BCP14, Gherkin, conceptual fidelity, error handling, etc.). Migrated to the `livespec` template at template root in Phase 2; classified as template-bundled prompt-reference material per v022. |
| `python-skill-script-style-requirements.md` | ~92KB Python style discipline. Migrated section-by-section into `SPECIFICATION/constraints.md` (or `spec.md`) in Phase 8 item 2 (one propose-change/revise per source-doc top-level section). |
| `deferred-items.md` | 17 deferred items processed in Phase 8 (one propose-change/revise per item). |
| `goals-and-non-goals.md` | Project intent. Seeded into `SPECIFICATION/` in Phase 6 alongside PROPOSAL.md. |
| `subdomains-and-unsolved-routing.md` | Companion doc; migration class per PROPOSAL §"Companion documents and migration classes". |
| `prior-art.md` | Companion doc (project-internal prior-art summary). |
| `2026-04-19-nlspec-*.md` | Lifecycle diagrams + terminology summary; companion docs. |
| `critique-interview-prompt.md` | Brainstorming-process artifact (used during the v018-v021 critique passes). Archived. |

## Subdirectory

| Path | What's there |
|---|---|
| `history/vNNN/` | Per-version PROPOSAL.md snapshots (v001-v022) plus their `proposed_changes/` directories. Each `vNNN/` is the frozen artifact for that revision. |

## How the bootstrap consumes this directory

| Phase | Consumed |
|---|---|
| 0 | Confirms `PROPOSAL.md` is byte-identical to `history/v022/PROPOSAL.md`; adds a "Frozen at v022" header note (the only permitted edit under `brainstorming/` post-Phase-0). |
| 1 | Reads `python-skill-script-style-requirements.md` and PROPOSAL §"Developer tooling layout" to author repo-root tooling (`.mise.toml`, `pyproject.toml`, `justfile`, `lefthook.yml`, CI workflows, `NOTICES.md`, `.vendor.jsonc`). |
| 2 | Copies `livespec-nlspec-spec.md` verbatim to the `livespec` template's root. |
| 6 | Seeds `SPECIFICATION/` from `PROPOSAL.md` + `goals-and-non-goals.md`. Other companion docs migrate via Phase 8 propose-changes. |
| 8 | Walks `deferred-items.md` items (per PROPOSAL §"Companion documents and migration classes" assignment table) and processes each via one or more propose-change/revise cycles against `SPECIFICATION/`. Item 2 (`python-skill-script-style-requirements.md`) is a per-section split. |

## Editing rules

- **Pre-Phase-0:** edits via formal `vNNN/` revisions, mirrored to
  `history/vNNN/`. The bootstrap skill's halt-and-revise sub-flow
  (per Plan §8) drives this mechanism.
- **Phase 0 onward:** this directory is immutable. Plan §3 cutover
  enforces. The bootstrap skill's "Report an issue first" gate
  routes drift to either halt-and-revise (pre-Phase-6) or
  propose-change against `SPECIFICATION/` (post-Phase-6).

## After bootstrap completes

Stays in place as historical reference. The production app does not
reference this directory.
