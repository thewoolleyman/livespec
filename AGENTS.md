# livespec — repo orientation

`livespec` is a Claude Code plugin that governs a living natural-language
specification. The repo dogfoods its own design: the plugin's own spec
lives at `SPECIFICATION/` and is itself maintained via the plugin's
`/livespec:*` slash commands.

## Repo layout

| Path | Purpose |
|---|---|
| `.claude-plugin/` | Plugin manifest, skill prompts, Python scripts, vendored libs, built-in templates |
| `.claude/skills/livespec-orchestrate/SKILL.md` | The Layer 3 cross-repo orchestration driver (project-local skill loaded as `/livespec-orchestrate` when working inside this repo; NOT a namespaced plugin skill — the `livespec-` prefix is a manual visual scoping convention to avoid colliding with the harness's built-in `/loop`). Single driver across the livespec family. |
| `SPECIFICATION/` | The live livespec specification (dogfooded; `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, `history/`) |
| `dev-tooling/` | Standalone enforcement-suite Python scripts (run via `just check`) |
| `tests/` | pytest suite — mirrors the `.claude-plugin/scripts/` and `dev-tooling/` trees one-to-one |
| `prior-art/` | Reference source material adapted into the shipped livespec template |
| `archive/` | Frozen historical artifacts from the bootstrap process — do not edit |
| `pyproject.toml`, `justfile`, `lefthook.yml`, `.mise.toml`, `.python-version`, `.vendor.jsonc`, `.livespec.jsonc` | Toolchain configuration |
| `NOTICES.md` | Third-party vendoring notices |

## Slash commands and skills

The plugin exposes eight sub-commands; each is backed by a skill at
`.claude-plugin/skills/<name>/SKILL.md`:

| Command | Skill | Purpose |
|---|---|---|
| `/livespec:seed` | `skills/seed/SKILL.md` | Author the initial natural-language spec |
| `/livespec:propose-change` | `skills/propose-change/SKILL.md` | File a proposed change against an existing spec |
| `/livespec:critique` | `skills/critique/SKILL.md` | Surface issues in an existing spec |
| `/livespec:revise` | `skills/revise/SKILL.md` | Accept, modify, or reject pending proposed changes |
| `/livespec:doctor` | `skills/doctor/SKILL.md` | Run static + LLM-driven validation against a spec tree |
| `/livespec:prune-history` | `skills/prune-history/SKILL.md` | Collapse old `history/vNNN/` entries into a pruned-marker |
| `/livespec:next` | `skills/next/SKILL.md` | Rank the next spec-side action (revise, propose-change, critique, prune-history, or none) over the current proposed_changes/ and history/ state |
| `/livespec:help` | `skills/help/SKILL.md` | Overview + routing to the right sub-command |

Each skill orchestrates dialogue capture, prompt-driven content
generation, wrapper invocation against `.claude-plugin/scripts/bin/<sub-command>.py`,
and structured-finding interpretation.

### Layer 3 orchestration driver — `.claude/skills/livespec-orchestrate/`

Per `SPECIFICATION/spec.md` §"Three-layer orchestration architecture",
this repo ALSO carries a project-local Layer 3 loop driver at
`.claude/skills/livespec-orchestrate/SKILL.md`. This is the single
cross-repo orchestrator across the livespec family of repos
(livespec, livespec-impl-*, livespec-dev-tooling, livespec-runtime);
sibling repos do NOT carry their own. It is invoked as
`/livespec-orchestrate` when working inside this repo (project-local
skill discovery, not namespaced — the `livespec-` prefix is a manual
visual scoping convention to avoid colliding with the harness's
built-in `/loop` recurring-task skill).

The driver composes the eight `/livespec:*` Layer 2 skills above
with the active impl-plugin's `next` / `implement` / `capture-*` /
`process-memos` skills, dispatches sub-agents with worktree
isolation into the sibling repos for end-to-end PR-merging
execution, runs `just check` plus `/livespec:doctor` as a hard
janitor gate, and emits a structured iteration journal. See the
skill body for inputs (`mode`, `budget`, `epic`, `scope-file`),
dispatch table, halt conditions, resume protocol, and the
wave-plan grammar used to author epic `scope-file`s.

## Agent prerequisites for plugin work

When investigating issues or making changes related to the Claude Code plugin installation, marketplace, or distribution:

1. **Establish execution context first** — Do NOT assume or make changes based on how you think the system works. Instead:
   - Run `claude plugin marketplace list` to see which marketplaces are configured and whether they point to local files or remote repos
   - Understand that changes to local `marketplace.json` will NOT affect installations from remote GitHub marketplaces
   - Read `SPECIFICATION/contracts.md` §"Plugin distribution" to understand the intended contract

2. **Map the execution flow before making changes**:
   - Trace where the actual install command is fetching from (local or remote)
   - Verify that any changes you make will actually affect that code path
   - If the marketplace points to remote GitHub, local changes are irrelevant — you either need to push to GitHub first or test against the local marketplace

3. **Use the correct testing approach**:
   - For remote marketplaces: push changes to GitHub, then test
   - For local marketplaces: use `/plugin marketplace add ./.claude-plugin/marketplace.json` and test against that
   - Never test local changes against a remote marketplace and assume they will work

This prevents wasted effort on changes that have no effect on the actual problem.

## Plugin install (end users)

The plugin is distributed via a Claude Code marketplace at
`.claude-plugin/marketplace.json` (per `SPECIFICATION/contracts.md`
§"Plugin distribution"). Install with:

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec@livespec
```

After install, the eight `/livespec:*` slash commands become available
with the `livespec:` namespace prefix.

## Daily dogfooding (maintainer development)

When editing the plugin source in this repo, two workflows:

- **Live-reload mode**: launch Claude Code with `claude --plugin-dir .`
  from the repo root. Plugin loads directly from local source; edits to
  `.claude-plugin/skills/<name>/SKILL.md` and `.claude-plugin/scripts/...`
  are picked up via `/reload-plugins` without re-installing. This is the
  daily-edit path.
- **Marketplace install path** (verifies the published flow): use the
  install commands above, or
  `/plugin marketplace add ./.claude-plugin/marketplace.json` for the
  local variant. Either copies the plugin into `~/.claude/plugins/cache/`
  and does NOT live-reload — run `/plugin update livespec@livespec` to
  pull changes after editing. Use this path to verify the install flow
  end-to-end before pushing.

The `.claude/skills` symlink (which used to load the plugin's skills as
PROJECT-level without the namespace prefix) was removed in v049. The
marketplace install or `--plugin-dir` is now the only way the plugin's
skills load with the correct `/livespec:*` namespace.

## Daily commands

- `just bootstrap` — first-touch setup on fresh clones; idempotently sets `core.bare = true` on the primary checkout (per `SPECIFICATION/non-functional-requirements.md` §"Bare-flag bootstrap procedure") plus installs lefthook hooks and resolves plugin dependencies.
- `just check` — full enforcement aggregate (lint, types, tests, coverage, AST checks).
- `just check-pre-commit-doc-only` — fast subset for doc-only commits.
- `/livespec-orchestrate` — invoke the Layer 3 cross-repo orchestration driver to drive an epic (or the open queue across all family repos) end-to-end. See `.claude/skills/livespec-orchestrate/SKILL.md` for inputs and behavior.

`just check` is the load-bearing safety net; it runs locally, in
pre-push, and in CI. The doc-only subset is invoked only by lefthook
pre-commit when zero `.py` files are staged.

## Revise co-edit discipline — `tests/heading-coverage.json`

Per `SPECIFICATION/spec.md` §"Self-application", every revise pass
that adds, changes, or removes a `## ` heading in any spec file MUST
update `tests/heading-coverage.json` via the same `resulting_files[]`
mechanism so the test-coverage map stays in lockstep with the spec.
When drafting a revise payload that touches a spec file's H2 set:

1. Diff the proposed `## ` heading set against the current spec
   file's H2 set.
2. For each added heading, include a `TODO` + `reason` entry in
   `tests/heading-coverage.json` (the v064 pattern); for each
   removed heading, drop the corresponding entry; for renamed
   headings, update the `heading` field.
3. Include `tests/heading-coverage.json` in the revise payload's
   `resulting_files[]` (path spelled as `../tests/heading-coverage.json`
   when `--spec-target` is the main `SPECIFICATION/` tree, so the
   wrapper's `spec_target / path` join resolves it to the project-
   root-relative file). Pre-commit's `check-heading-coverage` is the
   mechanical guard, but catching the omission at payload-assembly
   time keeps the revise commit atomic.

## Historical context

`archive/` contains the bootstrap-process artifacts: the design
brainstorming archive, the bootstrap PLAN, the bootstrap skill bundle
(removed at Phase 11), the per-phase STATUS / decisions / open-issues
logs, and the v032 quality-comparison report. The live spec at
`SPECIFICATION/` is the canonical authoritative source for current
design intent — `archive/` is reference-only.
