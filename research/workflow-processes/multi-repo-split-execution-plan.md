# Multi-repo split — execution plan

## Reusable session-start prompt

Paste this verbatim at the start of any new clean session to make
progress on this plan. The prompt is idempotent — running it in
successive sessions advances the work one beads issue at a time.

---

Read `research/workflow-processes/multi-repo-split-execution-plan.md`
for the full execution plan context (you are inside that file already
if you are reading this — the rest of the document is below).

Then:

1. Sync local state: `git checkout master && mise exec -- git pull`
   and `mise exec -- bd dolt pull`. Confirm working tree is clean.

2. Find the next actionable item **from THIS plan** (ignore unrelated
   pre-existing open issues): run `mise exec -- bd ready` and pick the
   lowest-priority-number issue whose ID is one of:
   - `li-ny7` (Phase A — gap refresh; closed)
   - `li-3ax`, `li-5s0`, `li-qit` (Phase B sub-tasks; closed)
   - `li-xjp` (Phase B epic; closed)
   - `li-jsl` (Phase C epic; closed)
   - `li-xgj`, `li-ag3`, `li-d5w`, `li-1ow`, `li-liv`, `li-ekf`,
     `li-716`, `li-9pf`, `li-f1w`, `li-zbd` (Phase D sub-tasks)
   - `li-6t5` (Phase D epic — only after all 10 sub-tasks close)
   - `li-9l5` (Phase E epic — only after Phase D closes;
     decompose at pickup)
   - `li-qyk` (Phase F — deferred indefinitely; skip unless reviving)

   If `bd ready` shows none of these IDs, this plan is complete.

3. `mise exec -- bd show <id>` to read the full description, then
   `mise exec -- bd update <id> --claim` to claim it.

4. Execute the work per the issue description and the plan-doc
   section it references (find via §"Phase X" header). For epics
   with sub-tasks deferred to pickup (Phase C, D, E), the first
   action is to decompose via `mise exec -- bd create` against the
   epic, wire dependencies via `mise exec -- bd dep add <epic> <sub>`,
   then claim the first leaf — DO NOT execute the epic's work
   without first decomposing.

5. When intent is unclear — exact wording, placement, edge cases,
   cross-references — read these authoritative sources before
   deciding:
   - `research/workflow-processes/tool-agnostic-workflow.md`
     (canonical conceptual model + glossary; wins on disagreement)
   - `research/workflow-processes/architecture-summary.html`
     (LiveSpec decisions list — the numbered Executive Summary at
     the top maps to load-bearing decisions)
   - `SPECIFICATION/` (v067 and later — the load-bearing contract)

6. Run `just check` to verify. On green: create a feature branch
   (`git checkout -b <type>(<scope>):<short-desc>`); commit on the
   branch via `mise exec -- git commit` so lefthook fires correctly;
   push; `gh pr create`; `gh pr merge --auto --squash`; close the
   beads issue with `mise exec -- bd close <id>`; then
   `mise exec -- bd dolt push` to sync beads state.

7. STOP after one beads-issue cycle. Each cycle lands as its own PR
   for clean audit-trail granularity.

If you spawned the session via a recurring loop and want to chain to
the next item automatically, that is a separate decision — by default,
stop after one cycle so the user can review each PR independently.

---

**Status:** Phases A, B, C, D complete. The dogfooding cutover at D.10 moved
livespec-core's own tracking from beads to livespec-impl-plaintext;
all 45 historical beads issues are migrated into work-items.jsonl
and the .beads/ scaffolding is retired from this repo. Phase E
(rename livespec → livespec-core) and Phase F (deferred) remain.
**Last updated:** 2026-05-19
**Spec basis:** SPECIFICATION/ as of v067 (the four post-orchestration
proposed-changes landed across v064–v067).
**Beads tracking:** the phase epics listed below have beads issue IDs;
`bd ready` surfaces the next actionable item in any clean session.
**Source-of-truth context for ambiguity:** see
`research/workflow-processes/tool-agnostic-workflow.md` (canonical
conceptual model; wins on disagreement) and
`research/workflow-processes/architecture-summary.html` (LiveSpec
decisions list).

## Goal

Evolve the current single-`livespec` repository into the post-orchestration
multi-repo plugin ecosystem the v064–v067 spec describes:

- `livespec-core` — renamed from `livespec`; ships spec lifecycle skills
  only; owns the published contract for everything else.
- `livespec-impl-plaintext` — new sibling repo; ships the 9-skill
  implementation plugin (6 heavyweight authored + 3 thin-transport)
  with a JSONL backend; is `livespec-core`'s designated dogfood target.
- `livespec-core/templates/impl-plugin/` — copier template scaffolding
  every `livespec-impl-*` plugin derives from (justfile, lefthook,
  mise, ruff/pyright, CI, starter `.claude/skills/loop/SKILL.md`).
- Project-local `.claude/skills/loop/SKILL.md` in every consuming repo
  — the Layer 3 orchestration driver; hand-tuned per repo.
- Beads tracking in this repo migrates to `livespec-impl-plaintext`'s
  JSONL backend (the dogfooding milestone).

The architectural decisions live in v064–v067 of `SPECIFICATION/`; this
document is execution sequencing only.

## Phases

### Phase A — Refresh implementation gaps against v067

**Beads:** see `bd ready` (PHASE-A issue). Priority P1.

The last `implementation-gaps/current.json` refresh was after v063
(commit `c69a486`). v064–v067 introduced substantial new requirements
that aren't yet in the gap inventory. Phase A produces the audit-trail
input that drives the work breakdown for Phases B–E.

**Acceptance:** `just implementation:refresh-gaps` runs cleanly against
v067; `current.json` reflects the v067 spec; any newly-surfaced gaps
that aren't already captured by Phase B/C/D/E epics get filed as
additional beads issues. Commit + push the refreshed JSON.

### Phase B — Add `/livespec:next` skill to livespec-core

**Beads:** PHASE-B epic + sub-tasks. Priority P2.

The first new skill on the post-rename surface (8 total once it lands).
Thin-transport per the doctrine in v065: SKILL.md is a pass-through
wrapper around a Python implementation. Reads spec-side state (Proposed
Changes queue, History recency, unresolved doctor findings) and emits
structured JSON. Pure function of file state; no LLM in the ranking
path. Does NOT read impl-side stores — cross-side composition is the
project-local Layer 3 loop driver's job.

**Sub-tasks (already filed in beads):**

1. `bin/next.py` — Python implementation; reads spec-side state; emits
   the structured-JSON schema (`action`, `reason`, `urgency`); unit
   tests under `tests/`.
2. `skills/next/SKILL.md` — thin-transport wrapper invoking `bin/next.py`;
   short body; no logic accretion (per thin-transport doctrine).
3. Manifest updates — `.claude-plugin/marketplace.json` and `plugin.json`
   description, `SPECIFICATION/spec.md` §"Sub-command lifecycle"
   exemption list, `SPECIFICATION/contracts.md` enumeration (the spec
   already requires the skill per v065; these touch-ups verify the
   advertised surface matches the implementation).

**Acceptance:** `/livespec:next` (still under the un-renamed namespace
during this phase) returns valid JSON when invoked against the live
repo; doctor static passes; tests in `just check` are green; commit and
push as `feat(spec-side): /livespec:next thin-transport skill`.

### Phase C — Build copier template at `templates/impl-plugin/`

**Beads:** PHASE-C epic. Priority P2.

Per v064, `livespec-core` publishes a copier template at
`templates/impl-plugin/` containing the canonical scaffolding every
`livespec-impl-*` repo inherits. No new repo is created in this phase
— just the template lives inside livespec-core.

**Scope:**

- `templates/impl-plugin/justfile.jinja`
- `templates/impl-plugin/.mise.toml.jinja`
- `templates/impl-plugin/lefthook.yml.jinja`
- `templates/impl-plugin/pyproject.toml.jinja` (ruff/pyright config,
  Python pins, dev-dependencies including `copier` itself per v064
  Finding 3's pinning rule)
- `templates/impl-plugin/.github/workflows/*.yml.jinja`
- `templates/impl-plugin/.claude-plugin/marketplace.json.jinja`
- `templates/impl-plugin/.claude-plugin/plugin.json.jinja`
- `templates/impl-plugin/SPECIFICATION/` (starter spec tree)
- `templates/impl-plugin/.claude/skills/loop/SKILL.md.jinja` (starter
  Layer 3 loop driver; v067 Finding 2 deferred the exact starter
  content — Phase C lands a working default)
- `templates/impl-plugin/copier.yml` — template metadata (variables:
  plugin name, namespace, backend kind, etc.)

**Acceptance:** `copier copy templates/impl-plugin/ /tmp/test-impl/` in
a scratch directory produces a buildable scaffold; running `just check`
inside the scaffold passes the doc-only checks (Python checks pass
trivially with no `.py` files yet); commit and push.

### Phase D — Split out `livespec-impl-plaintext` as sibling repo

**Beads:** PHASE-D epic. Priority P2. Depends on Phase C.

The biggest single piece of work. Creates the new GitHub repository
`thewoolleyman/livespec-impl-plaintext`, generates it from the copier
template, ports the existing project-local impl-skill bodies into the
new repo (retargeting them at the JSONL backend), implements the three
thin-transport query skills (`list-memos`, `list-work-items`, `next`),
wires `livespec.compat.json` pinning a livespec-core release tag, and
ships v0.1.0 to its own marketplace.

**Sub-scope** (decomposed 2026-05-19 into ten beads sub-tasks
`li-xgj` D.1, `li-ag3` D.2, `li-d5w` D.3, `li-1ow` D.4, `li-liv` D.5,
`li-ekf` D.6, `li-716` D.7, `li-9pf` D.8, `li-f1w` D.9, `li-zbd` D.10
— wired in a dependency chain; D.1 unblocked, others blocked on
predecessors):

- Generate the repo from the copier template.
- Port the 6 heavyweight authored skills: `capture-impl-gaps`,
  `capture-spec-drift`, `capture-work-item`, `implement`, `capture-memo`,
  `process-memos`. Each retargeted at JSONL work-items and JSONL memos.
- Implement the 3 thin-transport query skills: `list-memos`,
  `list-work-items`, `next` (impl-side). Per v065's doctrine each is a
  short SKILL.md pass-through over a Python `bin/` implementation.
- Implement the Spec Reader internal API per v065 Finding 4 (four
  required capabilities; can start as a thin pass-through over file
  reads).
- Wire `livespec.compat.json` declaring `livespec_core` semver range and
  `pinned` tag.
- Initial CI green via the copier-template scaffolding.
- First release tag and marketplace registration.

**Migration to plaintext for livespec-core's own tracking — the
dogfooding milestone (end of Phase D):**

Once `livespec-impl-plaintext` is functional enough to host a real
backlog, migrate livespec-core's own tracking from beads to the new
plugin. Specifically:

1. Install `livespec-impl-plaintext` in the livespec-core repo as a
   dev dependency.
2. Update `.livespec.jsonc` to switch `implementation.plugin` from
   the current beads-backed config to `livespec-impl-plaintext`.
3. Translate **ALL** beads issues — open, closed, and deferred —
   into JSONL records in livespec-impl-plaintext's new format,
   preserving the complete historical record. Closed issues become
   `status:closed` JSONL records carrying their closure reason, audit
   fields (resolution method, verification timestamp, commits, files
   changed), and original IDs for cross-reference; open issues become
   the live queue; deferred issues retain their deferred state and
   defer-until dates. **No beads data is orphaned in Dolt** — the
   migrated JSONL is the new audit-trail source of truth for this
   repo's complete historical impl tracking. A one-shot migration
   script (likely living in livespec-impl-plaintext itself as a
   utility, callable via `just`) handles the export → translate →
   import flow; the script reads from the `.beads/` Dolt store via
   `bd list --status=all --format=json` (or equivalent), maps the
   beads schema fields to the JSONL record schema, and writes the
   resulting records into livespec-impl-plaintext's configured
   work-items + memos paths.
4. Switch the project-local impl-tracking workflow from
   `livespec-implementation-beads:*` skills to
   `livespec-impl-plaintext:*` skills.
5. Retire the project-local beads workflow scaffolding from this repo
   AFTER step 3's migration verifies all data crossed over:
   `.claude/skills/livespec-implementation-beads:*`, the
   `just implementation:*` beads-specific recipes, the
   `setup-beads.sh` / `bd-doctor.sh` scripts, and the `.beads/`
   directory. The `.beads/` directory deletion is safe at this point
   because the migration has copied every record into the new store;
   the old Dolt store can be archived separately if a defensive
   point-in-time backup is wanted.

This migration is the validation gate that Phase D is done. It must
happen here, not in Phase E, because Phase E (the rename) is destructive
on its own and shouldn't be combined with a backend swap.

**Acceptance:** `livespec-impl-plaintext` is installable from its
marketplace; livespec-core's `.livespec.jsonc` points at it; **ALL
beads issues — open + closed + deferred — have been translated into
JSONL records in the new store, preserving the complete historical
audit trail** (no orphaned data in Dolt); livespec-core's remaining
backlog and historical issue history are both queryable via
livespec-impl-plaintext's skills; the project's beads dependency is
removed from livespec-core; doctor static across both repos is green.

### Phase E — Rename `livespec` → `livespec-core`

**Beads tracking moves to livespec-impl-plaintext at end of D; this
phase's tracking is in JSONL.** Priority P3. Depends on Phase D.

Most disruptive externally but mechanically simple. Touches:

- `.claude-plugin/marketplace.json` — name `livespec-core`.
- `.claude-plugin/plugin.json` — name `livespec-core`, description.
- GitHub repository rename `thewoolleyman/livespec` →
  `thewoolleyman/livespec-core` (GitHub auto-redirect preserves the
  old URL for some grace period).
- All 8 slash commands renamespace from `/livespec:*` to
  `/livespec-core:*` — affects skill prompt cross-references and any
  agent-facing documentation.
- The Codex dogfooding compatibility section.
- README, contributing docs, install instructions.

**Acceptance:** `/plugin marketplace add thewoolleyman/livespec-core`
followed by `/plugin install livespec-core@livespec-core` works
end-to-end against the new install path; the eight `/livespec-core:*`
commands work as before; release-please cuts the rename as a major
version bump per Conventional Commits.

### Phase F — `livespec-impl-beads` sibling repo (deferred)

**Tracking:** in the migrated JSONL system. Priority P4. Deferred until
adopter demand or maintainer choice surfaces. Not blocked by anything;
just not on the immediate roadmap per v064's decision to focus on
plaintext.

If revived, mirrors the Phase D shape but with `bd`/Dolt as the
backend instead of JSONL. The beads-specific invariants currently
described in this spec's removed sections (per v064) belong in this
plugin's own `SPECIFICATION/`.

## Dependency graph

```
Phase A (P1, no deps)
   ↓ (informational, not hard dep)
Phase B (P2)        Phase C (P2)        — independent of each other; can run in parallel
                          ↓
                       Phase D (P2; depends on C)
                          ↓
                       Phase E (P3; depends on D)

Phase F (P4, deferred)
```

## Entry points for a clean session

- `bd ready` — surfaces the next actionable issue. Filter on P0/P1
  first.
- This document — the narrative for "why" any decision in the issues.
- `SPECIFICATION/` (v067 and later) — the load-bearing contract.
- `research/workflow-processes/tool-agnostic-workflow.md` — canonical
  glossary and conceptual model. Wins on any disagreement.

When picking up a phase that's still an epic with no sub-tasks
(Phase C, D, E, F), the first thing to do is decompose it into sub-tasks
via `bd create` against the epic, wire dependencies, then claim the
first leaf.

## What this document is not

Not a re-statement of architecture (that's `SPECIFICATION/` v067 plus
the research/ background docs). Not a permanent record of every issue
(beads is the queue). Not a substitute for `bd ready` in a clean
session.
