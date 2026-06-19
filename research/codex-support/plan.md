# Codex support plan

Date: 2026-06-19

## Goal

Make livespec usable from OpenAI Codex as a maintainer dogfooding surface
without changing core's architecture: core owns harness-neutral operation prose
and reference wrapper CLIs; per-runtime bindings/adapters stay thin.

## Current state

- Core ships operation prose at `.claude-plugin/prose/<name>.md`.
- Core ships reference wrappers at `.claude-plugin/scripts/bin/<name>.py`.
- Core intentionally ships no `.claude-plugin/skills/` tree.
- Claude Code runtime bindings live in `/data/projects/livespec-driver-claude`.
- This checkout currently has no `.agents/` or `.codex/` project tree.
- Codex CLI 0.141.0 loads project skills from `.agents/skills/*/SKILL.md` when
  each skill has valid YAML frontmatter.
- Codex has no configured or installed `livespec` plugin marketplace entry.
- Existing `SPECIFICATION/non-functional-requirements.md` Codex sections are
  stale because they require `.agents/skills/*` symlinks to the removed
  `.claude-plugin/skills/*` tree.

Detailed evidence: `research/codex-support/audit.md`.

## Corrected architecture

Codex dogfooding should be a thin adapter over core, not a new command model.

The Claude/Codex DRY model is:

- shared behavior source of truth: `.claude-plugin/prose/<operation>.md`;
- shared executable contract: `.claude-plugin/scripts/bin/<operation>.py`;
- runtime-specific adapters only:
  - Claude Driver `SKILL.md` files in `/data/projects/livespec-driver-claude`;
  - Codex project `SKILL.md` files under `.agents/skills/` for local
    dogfooding, or a future Codex Driver repo if distribution becomes a product
    goal.

Do not introduce a second shared skill-body abstraction. The commonality has
already been abstracted into core prose plus wrapper CLIs. Runtime adapters are
allowed to differ only in binding mechanics: trigger descriptions, tool-use
instructions, path resolution, and how they invoke the shared wrapper.

The adapter should:

- live in `.agents/skills/<operation>/SKILL.md` for project-local dogfooding, or
  later in a sibling `livespec-driver-codex` repo if distribution becomes a
  product goal;
- contain only Codex-runtime routing instructions;
- tell Codex to read `.claude-plugin/prose/<operation>.md` completely before
  acting;
- tell Codex to invoke the configured wrapper under
  `.claude-plugin/scripts/bin/` when the prose calls for a CLI;
- preserve the core operation prose as the behavior source of truth;
- avoid symlinking to `.claude-plugin/skills/*`;
- avoid copying Claude Driver `SKILL.md` bodies into core or Codex;
- avoid restating operation-specific steps, failure handling, or output
  interpretation that already live in core prose.

For this repo's first dogfooding slice, prefer committed project-local
`.agents/skills` adapters. A separate `livespec-driver-codex` repo is useful
only after the project-local path is proven and the spec says what should be
distributed.

## Adapter sync checks

After the read-only adapter proof lands, add mechanical checks that keep Claude
and Codex adapters DRY by validating references rather than comparing copied
text.

Minimum checks:

- every Codex adapter must reference an existing
  `.claude-plugin/prose/<operation>.md`;
- every wrapper-backed Codex adapter must reference the expected
  `.claude-plugin/scripts/bin/<operation>.py`;
- Codex adapters must not contain copied core operation sections such as full
  `## Steps`, failure-handling tables, or output-schema narration;
- Codex probes for `help`, `next`, and `doctor` must show that Codex reads the
  adapter and then the core prose;
- if a future `livespec-driver-codex` repo is created, it should reuse the same
  reference checks against core rather than vendoring Claude Driver text.

## Bootstrap file layout

Minimum adapter layout:

```text
.agents/
  skills/
    livespec-help/
      SKILL.md
    livespec-next/
      SKILL.md
    livespec-doctor/
      SKILL.md
```

Why `livespec-<name>` rather than bare `<name>`:

- Codex skill names are global within a session's available skills list.
- Bare names like `next` and `help` are too generic.
- The user-facing command can still be `/livespec:help` or `livespec help`
  because the skill description can trigger on those phrases.

Each `SKILL.md` needs Codex YAML frontmatter:

```markdown
---
name: livespec-help
description: Use when the user invokes `/livespec:help`, says `livespec help`, or asks how to use livespec in this repository.
---
```

Adapter body shape:

1. Resolve the repository root as the current working tree.
2. Read the relevant core prose file:
   - `help` -> `.claude-plugin/prose/help.md`
   - `next` -> `.claude-plugin/prose/next.md`
   - `doctor` -> `.claude-plugin/prose/doctor.md`
3. Follow that prose.
4. When invoking a CLI, use the matching wrapper from
   `.claude-plugin/scripts/bin/`.
5. Do not add operation-specific behavior that is not in core prose.

The first adapter PR should implement only:

- `livespec-help`: pure prose, no wrapper.
- `livespec-next`: read-only wrapper
  `.claude-plugin/scripts/bin/next.py`.
- `livespec-doctor`: static check wrapper
  `.claude-plugin/scripts/bin/doctor_static.py`, initially verified with
  `--help` or other non-mutating invocation.

Do not implement mutating operations (`seed`, `propose-change`, `critique`,
`revise`, `prune-history`) until the read-only adapters are proven.

## Verification commands

Run from a feature worktree, not from the primary checkout.

Project tree:

```bash
find .agents/skills -maxdepth 2 -type f -name SKILL.md -print
```

Prompt assembly:

```bash
codex debug prompt-input '/livespec:help'
```

Help adapter:

```bash
codex exec --sandbox read-only '/livespec:help. Do not edit files. Tell me exactly which local instruction/prose file you read.'
```

Expected result:

- available skills list includes `livespec-help` from `.agents/skills`;
- Codex reads `.agents/skills/livespec-help/SKILL.md`;
- Codex reads `.claude-plugin/prose/help.md`;
- no files are edited.

Next adapter:

```bash
codex exec --sandbox read-only 'livespec next dry run only. Do not edit files. Tell me exactly which wrapper you would invoke.'
```

Expected wrapper:

```bash
.claude-plugin/scripts/bin/next.py \
  --project-root <repo-root> \
  --spec-target <repo-root>/SPECIFICATION \
  --limit 5 \
  --offset 0
```

Doctor adapter:

```bash
codex exec --sandbox read-only 'livespec doctor help only. Do not edit files. Tell me exactly which wrapper you would invoke.'
```

Expected wrapper:

```bash
.claude-plugin/scripts/bin/doctor_static.py --help
```

Do not claim success from the current ad-hoc probes alone. Success requires a
separate `codex exec` process using the committed `.agents/skills` adapter.

## Mechanical parity

Priority mechanical gap: Codex can write directly to the primary checkout via
file-edit tools. Current Claude hooks and git commit hooks do not prevent that
class of error.

Minimum first rail:

- Put a committed, explicit Codex-facing pre-edit rule in `AGENTS.md`:
  before edits in a livespec-governed repo, confirm `git config --get
  livespec.primaryPath`; if the current directory is that path on master/main,
  create a worktree and edit there.

Better follow-up rail:

- Add a lightweight repo check or wrapper that detects dirty primary checkout
  edits and fails loudly.
- Consider a Codex adapter checklist for mutating `livespec` operations before
  enabling `seed`, `propose-change`, `critique`, `revise`, or `prune-history`.

## Claude memory to instructions migration

Do not dump Claude memory into `AGENTS.md`. Route durable operational rules by
audience and authority.

First slice:

| Rule | Source memory | Target |
|---|---|---|
| Worktree -> PR -> merge -> cleanup for every livespec-governed repo change | `/home/ubuntu/.claude/projects/-data-projects-livespec-runtime/memory/feedback_worktree_discipline.md` | `AGENTS.md`; later spec/non-functional rule if not already covered |
| Use `mise exec --` for git commit/push so hooks fire | `/home/ubuntu/.claude/projects/-data-projects-livespec/memory/feedback_mise_exec_for_git_hooks.md` | Already in `AGENTS.md`; keep in any Codex bootstrap checklist |
| Never use `--no-verify` | `/home/ubuntu/.claude/projects/-data-projects-livespec/memory/feedback_sub_agent_dispatch_no_verify_ban.md` | Already in `AGENTS.md`; keep in Codex mutating adapters |
| End on main/master and refresh primary checkout after PR merge | `/home/ubuntu/.claude/projects/-data-projects-livespec/memory/feedback_end_on_main_branch.md` | `AGENTS.md` or progressive operational instruction file |
| Beads access via `with-livespec-env.sh`, `LIVESPEC_BD_PATH`, and tenant password mapping | `/home/ubuntu/.claude/projects/-data-projects-livespec/memory/feedback_no_beads_lookup.md` | Already in `AGENTS.md`; consider `.ai/beads.md` if `AGENTS.md` becomes too large |
| No orphaned worktrees; run cleanup after merge | `/home/ubuntu/.claude/projects/-data-projects-livespec/memory/feedback_worktree_orphan_reaper_enforcement.md` | Cleanup checklist and possible repo check |

Discard or quarantine:

- `/home/ubuntu/.claude/projects/-data-projects-livespec-runtime/memory/reference_livespec_repo_is_bare.md`
  appears stale for current `/data/projects/livespec`; do not migrate without
  fresh verification.
- Closed-epic status summaries and transient session lessons should stay out of
  repo instructions unless they encode a durable rule.

## Spec cleanup sequence

1. Land project-local evidence and this plan under `research/codex-support/`.
2. Implement the read-only `.agents/skills` adapters in a worktree.
3. Prove them with separate `codex exec` processes and record outputs.
4. File a formal proposed spec change replacing stale Codex dogfooding text:
   - remove symlink requirements to `.claude-plugin/skills/*`;
   - state Codex adapters read `.claude-plugin/prose/<name>.md`;
   - state wrappers come from `.claude-plugin/scripts/bin/`;
   - state Codex plugin marketplace support is not claimed until separately
     proven.
5. Use the governed `/livespec:propose-change` -> `/livespec:revise` lifecycle
   once Codex can safely drive it, or hand off formal spec mutation to Claude
   Code with the Driver loaded if Codex bootstrap is still incomplete.

## Follow-up Beads items

Open Beads items checked on 2026-06-19:

- `livespec-4moata`: broad v103 contract/reference implementation realization.
- `livespec-zkmn.1`: W7 convergence, including memo-kill/durable knowledge
  flow.

No dedicated open item was found for:

1. Repair stale Codex dogfooding spec sections.
2. Implement Codex project-skill bootstrap adapters.
3. Migrate Claude-only operational memory into committed instructions.

Recommended work-items:

1. `Codex dogfooding spec repair`
   - Scope: update `SPECIFICATION/non-functional-requirements.md` Codex
     compatibility/contracts/constraints/scenarios from `.claude-plugin/skills`
     symlinks to Codex adapters over core prose and wrappers.
   - Parent candidate: `livespec-4moata`.
2. `Codex read-only adapter proof`
   - Scope: add `.agents/skills/livespec-help`, `livespec-next`, and
     `livespec-doctor`; verify with separate `codex exec`.
   - Parent candidate: `livespec-4moata`.
3. `Claude memory to committed instructions slice`
   - Scope: migrate only parity-critical operational rules with provenance;
     explicitly discard stale/transient memory.
   - Parent candidate: `livespec-zkmn.1` if framed as memo-kill/knowledge-flow
     convergence; otherwise a standalone maintenance task.
