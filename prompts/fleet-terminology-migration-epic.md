# Epic: converge livespec domain language on fleet

## Objective

Converge livespec's ubiquitous domain language on **fleet** and retire the
legacy domain term **family** across the active livespec repos.

The migration is not a blind string replacement. Every occurrence of `family`
must be classified and either:

- migrated to `fleet` when it refers to the livespec-governed set of repos,
  shared infrastructure, shared secrets, shared operational discipline, or a
  member tenant;
- rewritten to a neutral non-domain word such as `group`, `category`, `class`,
  or `set` when it is generic English, such as "the AST-shape family"; or
- left only in immutable/historical records that the epic explicitly excludes
  from active terminology gates.

## Product Rationale

`fleet` is the better product/domain term for livespec because it describes an
operational set of managed things: manifest membership, conformance,
dispatching, release fan-out, shared automation, and shared observability.
`family` currently mixes product meaning with social/internal meaning and is
overloaded across secrets, hooks, templates, tenants, conventions, and generic
English groupings.

After this epic, users and agents should see one domain model:

- fleet
- fleet member
- fleet manifest
- fleet conformance
- fleet-wide obligation
- fleet-scoped secret
- fleet tenant
- non-fleet tenant

## Scope

Repos to audit and migrate:

- `livespec`
- `livespec-dev-tooling`
- `livespec-driver-claude`
- `livespec-driver-codex`
- `livespec-orchestrator-beads-fabro`
- `livespec-orchestrator-git-jsonl`
- `livespec-runtime`

Active artifacts in scope:

- specs, non-functional-requirements, contracts, constraints, scenarios
- `AGENTS.md`, `CLAUDE.md`, templates, prompts, research that serves as current
  handoff or operating guidance
- Python, shell, justfile, CI workflow text, tests, fixtures, comments, and
  user-facing messages
- docs and README content

Historical artifacts are out of default edit scope:

- `SPECIFICATION/history/**`
- `archive/**`
- dated historical research snapshots that are not current operating guidance

If a future operator wants a literal zero-result `rg '\bfamily\b'` over the
entire checkout including history, that is a separate history-rewrite decision
and must be called out explicitly before execution.

## Work Breakdown

### 1. Inventory and Classification

Create a repo-by-repo inventory of every active `family` occurrence, excluding
history/archive by default. Classify each occurrence as one of:

- domain-fleet: migrate to `fleet`
- generic-grouping: rewrite to `group`, `category`, `class`, `set`, or another
  local word that preserves meaning
- historical-immutable: leave unchanged and record why it is out of active
  scope
- ambiguous: inspect surrounding spec/code and resolve before editing

Deliverable: a short inventory note committed with the migration or included in
the PR body.

### 2. Core Specification and Agent Instructions

In `livespec`, migrate active spec and agent-instruction language first. This
sets the upstream vocabulary for the rest of the fleet.

Expected replacements include:

- `livespec family` -> `livespec fleet`
- `family-wide` -> `fleet-wide`
- `family-scoped` -> `fleet-scoped`
- `family-standard` -> `fleet-standard`
- `family infrastructure` -> `fleet infrastructure`
- `Family secrets` -> `Fleet secrets`
- `family tenant` -> `fleet tenant`
- `non-family tenant` -> `non-fleet tenant`
- `family-universal agent-instruction core` -> `fleet-universal
  agent-instruction core`

Do not change generated history snapshots unless the epic is explicitly
expanded to include history rewriting.

### 3. Shared Tooling and Conformance Surface

In `livespec-dev-tooling`, migrate active text in:

- `SPECIFICATION/**`
- `AGENTS.md` / `.claude/CLAUDE.md` template material
- `livespec_dev_tooling/fleet/**`
- tests and failure messages
- CI, justfile, comments, and docs

The code package remains `livespec_dev_tooling.fleet`; do not rename the already
correct `fleet` surface. The goal is to remove legacy terminology around that
surface.

### 4. Driver Plugins

In both Driver repos, migrate active text from "livespec family" and
"family-standard" to the fleet vocabulary. The Driver specs should point to the
upstream fleet vocabulary in `livespec/SPECIFICATION/spec.md` or
`non-functional-requirements.md`.

### 5. Orchestrators and Runtime

In orchestrator and runtime repos, migrate active docs, specs, tests, and user
messages. Preserve precise technical meaning:

- A fleet is the set of repos/resources governed together.
- A tenant is fleet-scoped only when it shares the livespec fleet's configured
  Beads/Dolt runtime and secret projection.
- Independent tenants become `non-fleet`, not `independent family`.

### 6. Verification and Guardrail

Run the repo's normal checks for every touched repo. At minimum:

- active terminology scan:
  `rg -n '\bfamily\b' --glob '!SPECIFICATION/history/**' --glob '!archive/**' --glob '!**/history/**' --glob '!.git/**'`
- active inverse sanity scan for accidental nonsense:
  `rg -n 'fleet of checks|AST-shape fleet|style fleet|test-infrastructure fleet|non-fleet-owned'`
- repo-local format/lint/test gates required by each repo
- for Python changes, follow that repo's Red-Green-Replay protocol

The active terminology scan must either return no results or only documented
historical/quoted occurrences that are intentionally out of active domain scope.

## Acceptance Criteria

- Active user-facing and agent-facing domain language uses `fleet`, not
  `family`.
- No active code, docs, tests, templates, prompts, or specs use `family` for the
  livespec-governed repo set or shared infrastructure.
- Generic English usages of `family` are removed or rewritten to a clearer
  non-domain term, rather than converted mechanically to `fleet`.
- The fleet manifest remains `.livespec-fleet-manifest.jsonc`; no filenames or
  APIs regress to the old manifest name.
- All touched repos are clean on `master` after PR merge and worktree cleanup.
- Any remaining `family` matches are documented as historical exclusions.

## Suggested Slice Plan

This is a cross-repo epic. Do not land it as one unreviewable megachange if the
inventory is large.

Recommended slices:

1. Core vocabulary slice: `livespec` active specs, templates, and agent docs.
2. Shared tooling slice: `livespec-dev-tooling` docs/tests/messages.
3. Driver slice: `livespec-driver-claude` and `livespec-driver-codex`.
4. Orchestrator/runtime slice: both orchestrators plus `livespec-runtime`.
5. Final scan slice: active terminology guard, residual documentation, and any
   missed prompt/template references.

Each slice should land through the repo's normal worktree -> PR -> merge ->
cleanup path.
