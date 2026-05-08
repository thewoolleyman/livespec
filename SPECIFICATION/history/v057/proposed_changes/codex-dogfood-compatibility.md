---
topic: codex-dogfood-compatibility
author: Codex GPT-5
created_at: 2026-05-07T10:03:00Z
---

## Proposal: Add Codex dogfooding compatibility for LiveSpec workflows

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Define a low-duplication OpenAI Codex CLI/TUI dogfooding path for the
`livespec` repository. Codex support for maintainers should work by exposing
the existing Claude Code skill files as Codex project skills, documenting the
same mapping in `AGENTS.md`, and following the same wrapper contracts already
used by Claude Code.

This proposal does NOT require first-class Codex marketplace distribution yet.
It also does NOT duplicate skill bodies, Python wrappers, or specification
templates. The current goal is repository dogfooding: Codex can drive changes
to LiveSpec itself by following the existing `.claude-plugin/skills/*/SKILL.md`
instructions through Codex-native `.agents/skills/*` symlinks or, where needed,
the `AGENTS.md` compatibility bridge.

### Local Test Results

This proposal is based on local tests against OpenAI Codex CLI `0.128.0` in a
separate worktree at `/Users/cwoolley/workspace/livespec-codex-compat`.

Tested but not verified as working:

- Root `.codex-plugin/plugin.json` pointing `skills` to
  `./.claude-plugin/skills/`.
- Root `.agents/plugins/marketplace.json` pointing the local marketplace entry
  at the repository root.
- `policy.installation: "INSTALLED_BY_DEFAULT"` in that marketplace entry.
- Canonical Codex plugin layout under `plugins/livespec/` with symlinked
  `skills`, `scripts`, and `specification-templates` directories pointing back
  to `.claude-plugin/`.

Observed behavior:

- `codex plugin marketplace add /Users/cwoolley/workspace/livespec-codex-compat`
  registered a local marketplace, but did not install or expose the LiveSpec
  skills in model-visible prompt input.
- `codex debug prompt-input` did not show LiveSpec skills for the root
  `.codex-plugin`, root `.agents/plugins/marketplace.json`, or canonical
  `plugins/livespec` symlink package.
- `codex debug prompt-input` also did not print the project-local
  `.agents/skills/*` symlinked skills, but separate slash-command `codex exec`
  probes did auto-load and follow those skills.
- `codex exec --sandbox read-only` did not see a LiveSpec plugin skill when
  testing the marketplace/plugin layouts without `.agents/skills`.
- The current CLI exposes `codex plugin marketplace add/remove/upgrade`, but no
  noninteractive plugin install command was found in `codex plugin --help`.

Verified as working:

- `.agents/skills/*` symlinks pointing at `.claude-plugin/skills/*` caused
  separate `codex exec --sandbox read-only --ephemeral` invocations to
  auto-load `/livespec:help` and `/livespec:propose-change` without an
  `AGENTS.md` command map.
- The verified symlink layout was:
  `.agents/skills/help -> ../../.claude-plugin/skills/help`,
  `.agents/skills/propose-change -> ../../.claude-plugin/skills/propose-change`,
  and the same pattern for the other five core skills.
- A read-only `/livespec:help` symlink test named
  `.claude-plugin/skills/help/SKILL.md` and produced LiveSpec help output.
- A read-only `/livespec:propose-change` symlink dry run read
  `.claude-plugin/skills/propose-change/SKILL.md` and identified
  `bin/propose_change.py <topic> --findings-json <tempfile> [flags]`.
- Adding an `AGENTS.md` section that maps `/livespec:<command>` and
  `livespec <command>` requests to `.claude-plugin/skills/<name>/SKILL.md`
  caused a separate `codex exec` process to follow the mapping.
- A read-only `/livespec:help` test caused Codex to read
  `.claude-plugin/skills/help/SKILL.md` and produce the expected help output.
- A read-only `/livespec:propose-change` dry run caused Codex to read
  `.claude-plugin/skills/propose-change/SKILL.md` and identify the wrapper
  path as `.claude-plugin/scripts/bin/propose_change.py`.

The verified path is therefore Codex-native project skill exposure through
`.agents/skills/*` symlinks, with `AGENTS.md` as the explicit compatibility
map and fallback. A Codex-native plugin registry / marketplace path remains
unverified.

### References

- OpenAI Codex CLI documentation:
  https://developers.openai.com/codex/cli
- OpenAI Codex skills documentation:
  https://developers.openai.com/codex/skills
- OpenAI Codex plugin build documentation:
  https://developers.openai.com/codex/plugins/build
- LiveSpec Claude Code plugin layout in this repository:
  `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`,
  `.claude-plugin/skills/*/SKILL.md`,
  `.claude-plugin/scripts/bin/*.py`
- Previously revised local implementation workflow proposal:
  `SPECIFICATION/proposed_changes/livespec-implementation-workflow.md`

### Proposed Changes

#### Add Codex dogfooding model to `spec.md`

Add a maintainer-development subsection near the existing Claude Code plugin
and dogfooding material:

```markdown
## Codex dogfooding compatibility

The `livespec` repository supports maintainer dogfooding from OpenAI Codex
CLI/TUI through Codex project skills under `.agents/skills/` and through the
repository's `AGENTS.md` instructions.

Codex dogfooding is an adapter for repository development, not a separate
LiveSpec product command model. The authoritative command behavior remains
the existing LiveSpec skill and wrapper contracts. When a Codex session in this
repository receives a request such as `/livespec:revise` or
`livespec revise`, it follows the mapped skill instructions from
`.claude-plugin/skills/<name>/SKILL.md` through the `.agents/skills/<name>`
project-skill symlink or the `AGENTS.md` command map, then invokes the same
wrapper scripts under `.claude-plugin/scripts/bin/`.

This compatibility path intentionally avoids duplicating skill prompts,
wrapper files, or built-in templates. Codex and Claude Code differ only in
how the maintainer enters the workflow; both route to the same repository
implementation.
```

For the repository-local implementation workflow, add:

```markdown
When the project-local `livespec-implementation` layer exists, Codex
dogfooding follows the same adapter rule: requests such as
`/livespec-implementation:refresh-gaps` or
`livespec-implementation refresh-gaps` map to that layer's project-local
skill files. The implementation layer remains repository-local and MUST NOT
be promoted into LiveSpec core by Codex compatibility work.
```

`revise` placement guidance: this belongs in `SPECIFICATION/spec.md` as
developer workflow behavior. It should not be added to the end-user product
description as first-class Codex distribution.

#### Add Codex compatibility contracts to `contracts.md`

Add a new section:

```markdown
## Codex dogfooding contracts

The repository's `.agents/skills/` directory is the Codex-native project-skill
entrypoint for LiveSpec dogfooding. It MUST expose one symlink per core
LiveSpec skill:

| Codex project skill path | Symlink target |
|---|---|
| `.agents/skills/seed` | `../../.claude-plugin/skills/seed` |
| `.agents/skills/propose-change` | `../../.claude-plugin/skills/propose-change` |
| `.agents/skills/critique` | `../../.claude-plugin/skills/critique` |
| `.agents/skills/revise` | `../../.claude-plugin/skills/revise` |
| `.agents/skills/doctor` | `../../.claude-plugin/skills/doctor` |
| `.agents/skills/prune-history` | `../../.claude-plugin/skills/prune-history` |
| `.agents/skills/help` | `../../.claude-plugin/skills/help` |

`AGENTS.md` is the explicit Codex dogfooding compatibility map for this
repository. It MUST contain a Codex command mapping table for LiveSpec core
commands:

| Codex-recognized request | Source skill file |
|---|---|
| `/livespec:seed`, `livespec seed` | `.claude-plugin/skills/seed/SKILL.md` |
| `/livespec:propose-change`, `livespec propose-change` | `.claude-plugin/skills/propose-change/SKILL.md` |
| `/livespec:critique`, `livespec critique` | `.claude-plugin/skills/critique/SKILL.md` |
| `/livespec:revise`, `livespec revise` | `.claude-plugin/skills/revise/SKILL.md` |
| `/livespec:doctor`, `livespec doctor` | `.claude-plugin/skills/doctor/SKILL.md` |
| `/livespec:prune-history`, `livespec prune-history` | `.claude-plugin/skills/prune-history/SKILL.md` |
| `/livespec:help`, `livespec help` | `.claude-plugin/skills/help/SKILL.md` |

For each mapped command, Codex MUST read the mapped `SKILL.md` before acting.
Codex MUST treat the mapped skill file as the source of orchestration truth
and MUST use the existing wrapper contracts in `.claude-plugin/scripts/bin/`.

If the project-local `livespec-implementation` plugin exists, `AGENTS.md`
MUST also map:

| Codex-recognized request | Source skill file |
|---|---|
| `/livespec-implementation:refresh-gaps`, `livespec-implementation refresh-gaps` | `.claude/plugins/livespec-implementation/skills/refresh-gaps/SKILL.md` |
| `/livespec-implementation:plan`, `livespec-implementation plan` | `.claude/plugins/livespec-implementation/skills/plan/SKILL.md` |
| `/livespec-implementation:implement`, `livespec-implementation implement` | `.claude/plugins/livespec-implementation/skills/implement/SKILL.md` |

Codex compatibility verification is performed with separate Codex processes.
Required verification commands for the core project-skill path and bridge:

- `find .agents/skills -maxdepth 1 -type l -print -exec readlink {} \;`
- `codex debug prompt-input 'test'`
- `codex exec --sandbox read-only '/livespec:help. Do not edit files. Prove which instruction file you used by naming its path.'`
- `codex exec --sandbox read-only '/livespec:propose-change dry run only. Do not edit files. Read the mapped instruction file and tell me which Python wrapper it would invoke.'`

The expected verification result is that Codex names the mapped
`.claude-plugin/skills/.../SKILL.md` file and, for wrapper-backed commands,
the matching `.claude-plugin/scripts/bin/...` wrapper. `codex debug
prompt-input` is useful negative evidence for marketplace/plugin registry
claims, but in Codex CLI `0.128.0` it did not print project-local
`.agents/skills/*` symlinked skills even when separate slash-command
`codex exec` probes auto-loaded them.
```

`revise` placement guidance: this belongs in `SPECIFICATION/contracts.md`
because it defines file paths, command aliases, and verification commands.

#### Add Codex compatibility constraints to `constraints.md`

Add a section:

```markdown
## Codex dogfooding constraints

Codex compatibility for repository dogfooding MUST NOT duplicate LiveSpec
skill bodies, Python wrappers, or built-in specification templates.

The `.claude-plugin/skills/*/SKILL.md` files remain the shared source of
truth for core LiveSpec command orchestration. Codex project skills MUST expose
those files by symlink from `.agents/skills/*`; they MUST NOT copy or restate
the skill bodies. Codex-specific documentation MAY translate invocation
language and tool names, but MUST NOT restate wrapper behavior in a way that
can drift from the shared skill files.

The current repository MAY claim Codex-native project-skill support only for
the verified `.agents/skills/*` symlink path. It MUST NOT claim Codex-native
plugin marketplace support solely because a `.codex-plugin/plugin.json`,
`.agents/plugins/marketplace.json`, or `plugins/livespec/` package exists. A
Codex-native plugin registry path is accepted only after marketplace
registration creates an installed LiveSpec plugin entry and a separate
`codex exec` invocation can use that registered plugin without relying on
`.agents/skills/*` or `AGENTS.md`.

Codex dogfooding MUST work without installing or modifying global/system
packages. Temporary local Codex marketplace registrations used for testing
MUST be removed after the test unless the user explicitly asks to keep them.

The Codex bridge MUST preserve destructive-command controls from the mapped
skill files. In particular, `prune-history` remains explicit-user-invocation
only, and Codex MUST NOT infer or auto-activate it from a generic mention of
history.
```

For the implementation layer, add:

```markdown
Codex compatibility for `livespec-implementation` MUST preserve the same
project-local boundary defined for Claude Code. Codex MAY refresh gaps, plan,
and implement through the repository-local implementation skill files, but
MUST NOT treat those workflows as shipped LiveSpec product behavior.
```

`revise` placement guidance: these constraints belong in
`SPECIFICATION/constraints.md` near existing developer-tooling and plugin
distribution constraints.

#### Add Codex dogfooding scenarios to `scenarios.md`

Add scenarios:

```markdown
## Codex dogfooding scenarios

Scenario: Codex help maps to the shared LiveSpec skill

Given a maintainer is running OpenAI Codex CLI/TUI in the `livespec`
repository
And `.agents/skills/help` points at `.claude-plugin/skills/help`
When the maintainer asks `/livespec:help`
Then Codex reads `.claude-plugin/skills/help/SKILL.md`
And Codex produces the LiveSpec help overview from that skill
And Codex does not require a Codex-native plugin install

Scenario: Codex propose-change dry run identifies the shared wrapper

Given a maintainer is running OpenAI Codex CLI/TUI in the `livespec`
repository
And `.agents/skills/propose-change` points at
`.claude-plugin/skills/propose-change`
When the maintainer asks for a read-only `/livespec:propose-change` dry run
Then Codex reads `.claude-plugin/skills/propose-change/SKILL.md`
And Codex identifies `.claude-plugin/scripts/bin/propose_change.py` as the
wrapper it would invoke
And Codex does not duplicate or reimplement the wrapper contract

Scenario: AGENTS bridge documents the same shared mapping

Given a maintainer is running OpenAI Codex CLI/TUI in the `livespec`
repository
And `AGENTS.md` contains the Codex dogfooding command map
When the maintainer asks `/livespec:help`
Then Codex can prove the mapping by naming `AGENTS.md`
And Codex can name `.claude-plugin/skills/help/SKILL.md`

Scenario: Codex plugin registry is not assumed from metadata alone

Given `.codex-plugin/plugin.json` or `.agents/plugins/marketplace.json` exists
When marketplace registration does not create an installed LiveSpec plugin
entry
Then repository documentation must not claim Codex-native plugin support
And Codex dogfooding continues through `.agents/skills/*` and the `AGENTS.md`
compatibility bridge

Scenario: Codex implementation workflow stays project-local

Given the `livespec-implementation` project-local layer exists
And a maintainer asks Codex to run `livespec-implementation refresh-gaps`
When Codex maps the request through `AGENTS.md`
Then Codex follows
`.claude/plugins/livespec-implementation/skills/refresh-gaps/SKILL.md`
And the workflow may inspect implementation state
And the workflow remains outside shipped LiveSpec core
```

### Non-goals

- This proposal does NOT ship a Codex-native LiveSpec plugin.
- This proposal does NOT add `.codex-plugin/` or `.agents/plugins/` files.
- This proposal does NOT require a Codex marketplace install path.
- This proposal does NOT duplicate `.claude-plugin/skills/*`,
  `.claude-plugin/scripts/*`, or specification templates.
- This proposal does NOT change Claude Code slash-command behavior.
- This proposal does NOT make the repo-local `livespec-implementation` layer a
  LiveSpec product feature.
