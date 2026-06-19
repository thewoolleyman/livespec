# Codex support audit

Date: 2026-06-19
Worktree: `/data/projects/livespec-codex-support`
Primary checkout kept read-only for repo changes: `/data/projects/livespec`

## Summary

Codex CLI can load valid project skills from `.agents/skills/*/SKILL.md`, but
this checkout has no `.agents/` or `.codex/` project tree today. Codex has no
installed `livespec` plugin marketplace entry. The existing Codex dogfooding
spec text is stale because it points `.agents/skills/*` at
`.claude-plugin/skills/*`, and core intentionally no longer ships that tree.

The minimum viable Codex dogfooding path should therefore be a Codex-owned
adapter layer that references core's existing operation prose under
`.claude-plugin/prose/` and invokes the existing wrappers under
`.claude-plugin/scripts/bin/`. It must not reintroduce core
`.claude-plugin/skills/` or duplicate the operation prose.

The DRY boundary between Claude and Codex is core's prose-plus-wrapper contract,
not shared `SKILL.md` text. Claude Driver skills and Codex project skills should
both stay thin runtime adapters over the same core files. Keeping them in sync
means mechanically checking adapter references and behavior probes, not copying
Claude `SKILL.md` bodies into Codex or creating a second cross-runtime skill
source.

## Commands and evidence

### Project tree probe

Command:

```bash
find . -maxdepth 4 \( -path './.git' -o -path './.claude/worktrees' \) -prune -o -path './.agents*' -print -o -path './.codex*' -print
```

Result in `/data/projects/livespec`: no output.

Conclusion: the primary checkout currently has no `.agents*` or `.codex*`
project support tree.

### Codex version and prompt assembly

Commands:

```bash
command -v codex
codex --version
codex debug prompt-input 'test'
```

Key results:

- Codex executable: `/home/ubuntu/.local/bin/codex`
- Version: `codex-cli 0.141.0`
- Prompt assembly included generic Codex/system skills plus injected
  `AGENTS.md` repository instructions.
- No livespec-specific skill or plugin entry appeared in the available skills
  list.

Conclusion: current Codex sessions learn livespec rules from `AGENTS.md`, not
from a livespec Codex skill/plugin.

### Read-only `/livespec:help` probe

Command:

```bash
codex exec --sandbox read-only '/livespec:help. Do not edit files. Tell me exactly which local instruction/prose file you read.'
```

Key result: the separate Codex process read
`/data/projects/livespec/.claude-plugin/prose/help.md` and produced the help
overview. It did this by reasoning from repository instructions, not through a
registered slash-command binding.

Conclusion: Codex can reach core prose when prompted, but this is not proof of
a real `/livespec:*` command surface.

### Read-only `next` dry-run probe

Command:

```bash
codex exec --sandbox read-only 'livespec next dry run only. Do not edit files. Tell me exactly which wrapper you would invoke.'
```

Key result: the separate Codex process inspected `.claude-plugin/prose/next.md`,
`SPECIFICATION/contracts.md`, `.livespec.jsonc`, and
`.claude-plugin/scripts/bin/next.py`, then identified this wrapper invocation:

```bash
/data/projects/livespec/.claude-plugin/scripts/bin/next.py \
  --project-root /data/projects/livespec \
  --spec-target /data/projects/livespec/SPECIFICATION \
  --limit 5 \
  --offset 0
```

It also noted that `next` has no `--dry-run` flag because the wrapper is already
advisory and read-only.

Conclusion: Codex can infer the correct wrapper path from repo files, but this
still depends on ad-hoc prompting rather than a maintained adapter.

### Project `.agents/skills` loading probe

Scratch directory: `/tmp/codex-agents-skill-probe`

Invalid-skill command:

```bash
codex exec --skip-git-repo-check --sandbox read-only 'project skill sentinel. If a project skill is loaded, follow it. Also state whether you saw any .agents/skills entry in your available skills list.'
```

Invalid-skill result:

```text
failed to load skill /tmp/codex-agents-skill-probe/.agents/skills/probe-skill/SKILL.md: missing YAML frontmatter delimited by ---
```

Valid skill frontmatter:

```markdown
---
name: probe-skill
description: Use when the user says `project skill sentinel`.
---
```

Valid-skill key prompt assembly result:

```text
- `r9` = `/tmp/codex-agents-skill-probe/.agents/skills`
- probe-skill: Use when the user says `project skill sentinel`. (file: r9/probe-skill/SKILL.md)
```

Valid-skill `codex exec` result:

```text
PROJECT_SKILL_SENTINEL_LOADED
```

Conclusion: Codex CLI 0.141.0 does load project-local `.agents/skills` entries
when each `SKILL.md` has valid YAML frontmatter with `name` and `description`.
This makes `.agents/skills` a viable project-local adapter path.

### Codex plugin marketplace state

Commands:

```bash
codex plugin marketplace list
codex plugin list
```

Key results:

- Marketplace list contains only:
  - `openai-curated`
  - root `/home/ubuntu/.codex/.tmp/plugins`
- Installed/enabled plugins are generic curated plugins such as GitHub, Gmail,
  Google Calendar, Google Drive, Slack, Box, Notion, and Vercel.
- No `livespec` plugin entry is installed or available from configured Codex
  marketplaces.

Conclusion: do not claim Codex plugin support for livespec. The proven path is
project-local `.agents/skills`, not Codex marketplace distribution.

### Current core layout

Core prose files:

```text
critique.md
doctor.md
help.md
next.md
propose-change.md
prune-history.md
revise.md
seed.md
```

Wrapper files:

```text
critique.py
doctor_static.py
next.py
propose_change.py
prune_history.py
resolve_template.py
revise.py
seed.py
```

Conclusion: a Codex adapter can map the eight operations to existing prose and
wrappers without copying operation behavior.

### Stale spec text

`SPECIFICATION/non-functional-requirements.md` currently says:

- Codex maps `.agents/skills/*` to `.claude-plugin/skills/*`.
- `.agents/skills/*` should be symlinks to `.claude-plugin/skills/*`.
- Expected probes should name `.claude-plugin/skills/.../SKILL.md`.

That conflicts with current architecture:

- Core has no `.claude-plugin/skills/` tree.
- Claude runtime bindings live in `/data/projects/livespec-driver-claude`.
- Core owns `.claude-plugin/prose/<name>.md` and
  `.claude-plugin/scripts/bin/<name>.py`.

### Beads ledger check

Command:

```bash
/data/projects/1password-env-wrapper/with-livespec-env.sh bash -lc \
  'cd /data/projects/livespec-codex-support && export BEADS_DOLT_PASSWORD="$BEADS_DOLT_PASSWORD_livespec" LIVESPEC_BD_PATH=/usr/local/bin/bd; /usr/local/bin/bd list --status open --json'
```

Key results:

- `livespec-4moata` remains the broad v103 contract/reference implementation
  realization epic.
- `livespec-zkmn.1` remains the W7 convergence item, including memo-kill and
  durable knowledge flow.
- No open item specifically tracks:
  - stale Codex dogfooding spec repair;
  - Codex project-skill bootstrap adapter;
  - Claude-memory-to-repo-instructions migration.

Conclusion: this work should file or attach follow-up Beads items rather than
assuming an existing dedicated tracker.

## Operational memory inventory

Source files inspected:

- `/home/ubuntu/.claude/projects/-data-projects-livespec/memory/MEMORY.md`
- `/home/ubuntu/.claude/projects/-data-projects-livespec-runtime/memory/feedback_worktree_discipline.md`
- `/home/ubuntu/.claude/projects/-data-projects-livespec-runtime/memory/MEMORY.md`

Parity-critical entries to route first:

| Memory | Source | Initial disposition |
|---|---|---|
| Worktree -> PR -> merge -> cleanup discipline | `...livespec-runtime/memory/feedback_worktree_discipline.md` | Move into committed repo instructions and/or a mechanical pre-edit check; already partially reflected in `AGENTS.md`, but should be canonical and explicit for all agents. |
| Use `mise exec --` for git operations that fire hooks | `...livespec/memory/feedback_mise_exec_for_git_hooks.md` via `MEMORY.md` | Already in `AGENTS.md`; keep and ensure any Codex adapter or bootstrap docs repeat the rule for commit/push flows. |
| End on main/master and pull after closing work | `...livespec/memory/feedback_end_on_main_branch.md` via `MEMORY.md` | Move into committed agent instructions for all harnesses. |
| Beads access through `with-livespec-env.sh` and per-tenant env mapping | `...livespec/memory/feedback_no_beads_lookup.md` via `MEMORY.md` | Already in `AGENTS.md`; should remain there and possibly move to a focused `.ai/beads.md` or equivalent progressive instruction file. |
| No `--no-verify` for commits/pushes | `...livespec/memory/feedback_sub_agent_dispatch_no_verify_ban.md` via `MEMORY.md` | Already partly in `AGENTS.md`; should be included in Codex bootstrap/worktree discipline instructions. |
| No direct primary-checkout edits | `...livespec-runtime/memory/feedback_worktree_discipline.md` | Needs stronger committed instruction and possible mechanical pre-flight rail; current hooks cannot prevent direct `apply_patch` edits. |
| No orphaned worktrees | `...livespec/memory/feedback_worktree_orphan_reaper_enforcement.md` via `MEMORY.md` | Already partially represented by doctor/no-stale-worktree; add to cleanup checklist and bootstrap plan. |

Entries to treat carefully:

- `/home/ubuntu/.claude/projects/-data-projects-livespec-runtime/memory/reference_livespec_repo_is_bare.md`
  appears stale for this checkout. Current `git config --get core.bare` did not
  show a bare primary, and `livespec.primaryPath` points to
  `/data/projects/livespec`.
- Large numbers of memory entries are project history, style feedback, or
  closed-epic state. They should not be dumped wholesale into `AGENTS.md`; route
  only durable operational rules.
