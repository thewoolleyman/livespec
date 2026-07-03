# 01 — Residual map: what still lives in root `research/` and how each piece retires

Evidence base for the `retire-research-dirs` thread (epic anchor
`livespec-gt7crt`, livespec tenant). This epic supersedes the
`cleanup-research-and-prompt-cruft` (epic `livespec-ztepy5`) D1
end-state: that epic deliberately KEPT code/AGENTS.md/runtime-referenced
docs in `research/`; on 2026-07-04 the maintainer directed full
retirement — after this epic, no fleet repo (nor the openbrain adopter)
carries a root `research/` directory. Deep per-item evidence (merge
SHAs, accepted spec versions, reference verification) lives in the
predecessor thread's archived tables:
`plan/archive/cleanup-research-and-prompt-cruft/research/02-dispositions-<repo>.md`
in the `livespec` repo — this map carries only what execution needs.

Disposition vocabulary (three verbs, defined once):

- **ARCHIVE** — `git mv` to `archive/research/<same-subpath>` in the
  same repo; every inbound reference is retargeted to the archive path
  in the same PR. For rationale/record docs whose contractual content
  already lives in the spec.
- **RELOCATE** — `git mv` to a LIVING home (not archive) because the
  file is still actively read or written; all inbound references and
  any gate configuration retarget in the same PR.
- **REVISE** — a `SPECIFICATION/` text change; goes through that repo's
  propose-change → revise cycle, never a raw edit. (Plugin prose under
  `.claude-plugin/prose/` is NOT spec and is edited directly.)
- **delete** (lowercase, directory readmes only) — a `research/CLAUDE.md`
  that dies when its directory empties; no target, no retargets.
- **edit** (lowercase) — an in-place wording change in a file that is
  not itself moving (e.g. a README layout row).

## Phase 0 design gates (maintainer decisions, taken one per turn)

1. **New home for the dispatcher's runtime-written `lessons.md`** —
   **DECIDED (maintainer, 2026-07-04): the WHOLE
   `research/loop-reflection-gate/` directory moves to top-level
   `loop-reflection-gate/` "for now"** (lessons.md stays markdown; the
   three design docs move WITH it rather than archiving — this
   supersedes the ARCHIVE rows below for those docs). Executed
   immediately via a dedicated orchestrator-repo PR (TDD path change at
   `_dispatcher_reflector_oob.py:688` + `git mv` + full reference
   sweep) together with the creation of the orchestrator repo's own
   `plan/loop-reflection-gate/` thread (anchored on epic
   `livespec-impl-beads-29f`) driving the remaining reflection-gate
   work (the unimplemented ratified-lessons brief-injection consumer;
   related: `bd-ib-umno37`, cross-tenant `livespec-dev-tooling-e60`).
2. **New home for openbrain's live `ob1-fork-patches.md` registry.**
   Append-only patch registry (20 patches) wired into enforcement:
   `lefthook.yml:133` glob and the `scripts/inert-deferral-lint.ts:84`
   allowlist regex, plus ~10 doc/code references. It cannot archive
   (live tracking state) and must not spec-absorb ("the spec is for
   contracts, not tracking"). Recommendation: `docs/ob1-fork-patches.md`
   (openbrain already has a `docs/` directory) with the lefthook glob +
   lint regex + all references retargeted atomically.

## Per-repo retirement map

### livespec (8 files → research/ ceases to exist)

| Item | Verb | Target + reference retargets |
|---|---|---|
| `research/beads/beads-gaps-workarounds.md` | RELOCATE | → `.ai/beads-gaps-workarounds.md` (living agent guidance; the `.ai/` convention is exactly for this). Add the pointer line in `AGENTS.md`'s `.ai/` reference list (the convention REQUIRES every `.ai/` topic to be referenced from AGENTS.md). Cross-repo: openbrain `AGENTS.md:304` retargets to the livespec `.ai/` path (goes in openbrain's changeset). |
| `research/beads/CLAUDE.md` | delete | Directory readme; dies with its directory (content, if any is load-bearing, folds into the relocated doc's header). |
| `research/dark-factory-operability/preconditions.md` | ARCHIVE | → `archive/research/dark-factory-operability/preconditions.md`; retarget livespec `AGENTS.md:81` (one edit — `.claude/CLAUDE.md` is a symlink to AGENTS.md). |
| `research/dark-factory-operability/CLAUDE.md` | ARCHIVE | Moves with its directory. |
| `research/factory-conformance/cross-repo-conformance-pattern.md` | ARCHIVE | → `archive/research/factory-conformance/…`; retarget livespec `templates/orchestrator-plugin/copier-questions.yml:75` (comment). Cross-repo: livespec-dev-tooling `livespec_dev_tooling/worktree_pack/branch-protection.sh:15` (comment; goes in dev-tooling's changeset — single source, propagates via the worktree pack). |
| `research/planning-workflow-gap/` (2 files) | ARCHIVE | → `archive/research/planning-workflow-gap/`; retarget livespec `AGENTS.md:675` and `README.md:148`. |
| `research/CLAUDE.md` | delete | Dies when the directory empties. |
| Planning-Lane language | REVISE | `SPECIFICATION/non-functional-requirements.md` §"Planning Lane guidance": drop/replace "The broader `research/` tree stays for standalone analysis that is not an active planning thread" (line ~174) and "to keep a research file as living reference, copy it to `research/` deliberately" (line ~182) — successor wording: standalone analysis lives in a plan thread or the archive; a living reference doc lives in `docs/` or `.ai/`. H2 set unchanged → no `tests/heading-coverage.json` co-edit expected; verify at payload time. |

### livespec-orchestrator-beads-fabro (5 files → research/ ceases to exist)

| Item | Verb | Target + reference retargets |
|---|---|---|
| `research/loop-reflection-gate/` (ALL 4 files) | RELOCATE (code change) | → top-level `loop-reflection-gate/` per DECIDED gate 1 (whole directory, design docs included — no archive split for now). Red-Green-Replay TDD: Red = test asserting the new default `lessons_path`; Green = `_dispatcher_reflector_oob.py:688` → `Path("loop-reflection-gate/lessons.md")` + `git mv` + retarget the docstring/comment cites in `_dispatcher_cost_pricing.py:11`, `_dispatcher_heartbeat_probe.py:10`, `_dispatcher_reflection.py:3`, `_otel_enrich.py:4`, `_otel_receive.py:5`, `_otel_scrub.py:6`. |
| `research/CLAUDE.md` | delete | Dies when the directory empties; `README.md:157`'s `research/` table row is removed/reworded. |
| Planning-Lane realization language | REVISE + prose edit | `SPECIFICATION/contracts.md` §"Planning Lane realization" (~line 900) same "broader research/ tree stays" sentence via propose-change → revise; `.claude-plugin/prose/plan.md:54,179` (plugin prose, direct edit in the same PR) — successor wording as in livespec. |

### livespec-dev-tooling (3 files → research/ ceases to exist)

| Item | Verb | Target + reference retargets |
|---|---|---|
| `research/justcheck-performance/` (2 files) | ARCHIVE | → `archive/research/justcheck-performance/`; retarget own `.github/workflows/ci.yml:92` comment, `livespec_dev_tooling/red_leg_scope.py:15` docstring, `tests/livespec_dev_tooling/test_red_leg_scope.py:11` docstring (docstring-only `.py` edits; `chore:` subject keeps the changeset Red-Green-Replay-exempt — confirm the repo's hook treats it so, else split). Cross-repo: livespec `.github/workflows/ci.yml:81` comment (goes in livespec's changeset). Also carries the `branch-protection.sh:15` retarget from livespec's factory-conformance ARCHIVE (above). |
| `research/CLAUDE.md` | delete | Dies with the directory. |

### openbrain (2 files → research/ ceases to exist; default branch `main`, own wrapper)

| Item | Verb | Target + reference retargets |
|---|---|---|
| `research/ob1-fork-patches.md` | RELOCATE | → the Phase 0 gate-2 home. Retargets, all in one PR: `lefthook.yml:133` glob, `scripts/inert-deferral-lint.ts:47,84` (header + allowlist regex), `AGENTS.md:214`, `SPECIFICATION/spec.md:1667` + `SPECIFICATION/scenarios.md:1772` (REVISE — spec links move through openbrain's propose-change → revise, revise lands before or atomically with the move), `.ai-instructions/local-gates.md:119`, `.ai-instructions/ob1-fork.md:61`, `.claude/workflows/implement-task-capture-surfaces.mjs:218`, `README.md:147,376`. |
| `research/ob1-inline-autonomous-factory.md` | ARCHIVE | → `archive/research/ob1-inline-autonomous-factory.md`; retarget `scripts/promote.ts:6` comment. |
| README layout rows | edit | `README.md:375` `research/` row removed once the directory is gone. |

Line numbers were verified during the predecessor epic (2026-07-03);
executors re-resolve by CONTENT at execution time — anchors drift.

## Execution-order constraints

- Spec REVISE lands before (or atomically with) any move it
  de-references — same rule the predecessor epic enforced.
- openbrain's `ob1-fork-patches` move must co-edit `lefthook.yml` and
  `inert-deferral-lint.ts` in the SAME commit or the
  `inert-deferral-lint` gate fails on itself.
- The orchestrator `lessons.md` change is the only full-TDD item; the
  three doc archives may ride its PR or a separate doc-only PR.
- livespec's changeset carries the cross-repo `ci.yml:81` retarget;
  dev-tooling's carries `branch-protection.sh:15`; openbrain's carries
  its `AGENTS.md:304` retarget — each repo edits only its own files.

## End-state assertion (Phase 2)

The predecessor's default-branch-aware sweep, tightened: for every
fleet repo and openbrain, `git ls-tree <default-ref>` contains NO
top-level `research` entry (and still no `prompts`); every retarget
resolves (`git grep` for the old paths outside `archive/` and
`SPECIFICATION/history/` returns nothing); the two spec revises are
accepted history versions; `just check` (or the repo's gate) green
everywhere.
