# Codex support handoff prompt

You are starting a new session in `/data/projects/livespec`.

Goal: make livespec usable from OpenAI Codex as a maintainer dogfooding
surface, starting with the minimum skills/bootstrap path. Do not start by
editing broad hooks/plugins machinery. First repair the design and prove the
Codex skill/bootstrap path.

## Context already established

- Current repo architecture:
  - `livespec` core owns `.claude-plugin/prose/<name>.md`, reference CLIs under
    `.claude-plugin/scripts/bin/`, schemas, and templates.
  - Claude Code runtime bindings live in the sibling repo
    `/data/projects/livespec-driver-claude`.
  - Core intentionally has no `.claude-plugin/skills/` tree. This is guarded by
    `tests/test_plugin_distribution.py`.
  - The interactive `/livespec:*` surface is a Driver concern, not core.
- Existing Codex-related spec text is stale:
  - See `SPECIFICATION/non-functional-requirements.md` sections:
    `Codex dogfooding compatibility`, `Codex dogfooding contracts`,
    `Codex dogfooding constraints`, and the Codex scenarios.
  - That text says Codex should map `.agents/skills/*` symlinks to
    `.claude-plugin/skills/*`.
  - That target is impossible in the current architecture because core no
    longer ships `.claude-plugin/skills/*`.
  - `.agents/skills/` does not currently exist in this checkout.
- Git provenance for the stale Codex text:
  - `a4f671b` added `SPECIFICATION/proposed_changes/codex-dogfood-compatibility.md`.
  - `3ac6541` landed the Codex dogfooding NFR text as v057.
  - `49e2d6e` later touched it during the v064 multi-repo/distribution rewrite.
- Beads/research inventory from the prior investigation:
  - I did not find a current open Beads item specifically named "Codex
    conversion" or "Claude memory to instructions".
  - Related Beads items DO exist and must shape this work:
    - `livespec-4moata` is the open v103 contract/reference-implementation
      realization epic. It covers Driver extraction and the broader
      contract/reference split.
    - `livespec-zkmn.1` is the open W7 convergence item. It includes the
      memo-kill direction and retargeting the Driver's `block-auto-memory.sh`
      behavior away from Claude memory toward durable work-item/knowledge flow.
    - `livespec-a8bb` is closed. It retired `/livespec-orchestrate` and required
      relocating normative skill duties before deleting the resident skill.
    - `livespec-gy21` is closed. It project-scoped the livespec plugin family
      so Claude skills/hooks stop leaking globally.
  - Relevant research/spec support:
    - `research/workflow-processes/tool-agnostic-workflow.md` treats persistent
      agent knowledge as something that can live in harness instruction files
      such as `CLAUDE.md`, `AGENTS.md`, `.ai/<topic>.md`, or a long-lived memory
      store.
    - `SPECIFICATION/non-functional-requirements.md` says agent-collaboration
      rules apply to skills, `CLAUDE.md` / `AGENTS.md`, hooks, and ad-hoc agent
      dialogue.
    - `SPECIFICATION/non-functional-requirements.md` already codifies workspace
      cleanup as part of "done".
- Claude-specific state found on disk:
  - `.claude/settings.json` enables `livespec@livespec`,
    `livespec@livespec-driver-claude`, and
    `livespec-impl-beads@livespec-impl-beads`, plus SessionStart/PreToolUse/
    SubagentStop hooks.
  - `/home/ubuntu/.claude/plugins/marketplaces/livespec-driver-claude/` contains
    the installed Claude Driver plugin, including
    `.claude-plugin/skills/{seed,propose-change,critique,revise,doctor,prune-history,next,help}/SKILL.md`.
  - `/home/ubuntu/.claude/projects/-data-projects-livespec/memory/MEMORY.md`
    contains a large livespec-specific memory index. Relevant memories include
    Beads access, ending on main/master, `mise exec --` for git operations,
    worktree orphan/reaper discipline, and multiple prior failure lessons.
  - A sibling memory at
    `/home/ubuntu/.claude/projects/-data-projects-livespec-runtime/memory/feedback_worktree_discipline.md`
    explicitly says every livespec-governed repo change must follow a worktree
    -> PR -> merge -> cleanup cycle.
  - Codex currently does NOT have equivalent livespec project config:
    `/home/ubuntu/.codex/config.toml` marks `/data/projects/livespec` trusted
    and enables generic curated plugins, but does not enable livespec plugins,
    livespec hooks, or a project-local skill bridge. No `.codex/` or `.agents/`
    project skill tree exists in this checkout.
- Important parity conclusion:
  - Migrating useful Claude memory into repo instructions is necessary for Codex
    parity because it removes hidden Claude-only operational knowledge.
  - It is NOT sufficient by itself. Full parity also needs a Codex-loadable
    skill/bootstrap path and mechanical rails where Codex supports them,
    especially a pre-edit worktree discipline.
  - The Claude Bash footgun guard would NOT have prevented a direct `apply_patch`
    into the primary checkout. It blocks only specific Bash footguns
    (`--no-verify`, `LEFTHOOK=0/false`, `core.bare=true`). So the fix cannot be
    "trust memory harder"; it must turn the important memories into explicit
    instructions and, where possible, enforceable checks/hooks.
- Beads access works, but only with the current temporary tenant-secret bridge:
  ```bash
  /data/projects/1password-env-wrapper/with-livespec-env.sh bash -lc \
    'cd /data/projects/livespec && export BEADS_DOLT_PASSWORD="$BEADS_DOLT_PASSWORD_livespec" LIVESPEC_BD_PATH=/usr/local/bin/bd; /usr/local/bin/bd list --status open --json'
  ```
  This bridge is expected to go away under `dolt-server-x6byxj`, which will
  collapse family tenant passwords to one bare `BEADS_DOLT_PASSWORD`.

## Important constraints

- Do not reintroduce `.claude-plugin/skills/` into core.
- Do not symlink `.agents/skills/*` to `.claude-plugin/skills/*`; that path is
  obsolete.
- Do not claim Codex plugin/marketplace support unless it is actually proven in
  a separate `codex exec` process.
- Do not assume Claude Code plugin marketplace mechanics apply to Codex.
- Do not duplicate the operation prose. The source of behavior should remain
  core prose plus the existing wrapper CLIs.
- Spec mutations in `SPECIFICATION/` normally flow through
  `/livespec:propose-change` -> `/livespec:revise`. If you are in Codex and the
  LiveSpec skills are not yet bootstrapped, produce research/design first and
  either use the verified CLI path where appropriate or hand off the formal spec
  revision to a Claude Code session with the Driver loaded.

## Recommended first work

1. Audit current Codex mechanics in this repo:
   - Check whether Codex supports project skills from `.agents/skills/` in this
     environment.
   - Probe with separate read-only Codex processes, not assumptions.
   - Record exact commands and outputs in `research/codex-support/`.
2. Define the corrected bootstrap target:
   - Codex should read core operation prose from `.claude-plugin/prose/<name>.md`.
   - Codex should invoke the existing wrappers under `.claude-plugin/scripts/bin/`.
   - If Codex requires `SKILL.md` files, create a Codex-owned adapter layer that
     references core prose rather than copying it. Decide whether that adapter
     belongs in this repo as project dogfooding (`.agents/skills/`) or in a
     future sibling `livespec-driver-codex` repo.
3. Start with the smallest verified command set:
   - `help`: no wrapper, pure prose.
   - `next`: thin transport to `.claude-plugin/scripts/bin/next.py`.
   - `doctor` or `propose-change` dry-run/read-only verification: enough to
     prove wrapper identification without mutating files.
4. Draft a concrete plan under `research/codex-support/plan.md` that includes:
   - Current-state audit.
   - Corrected architecture.
   - Bootstrap file layout.
   - Verification commands.
   - The Claude-memory-to-instructions migration slice:
     - inventory the Claude project memories that are actually operational rules;
     - classify each as already codified, should move to repo instructions,
       should move to spec, should move to an orchestrator/Driver repo, or
       should be discarded as stale/transient;
     - prioritize the parity-critical entries first: worktree discipline, Beads
       access, `mise exec --` git operations, end-on-main cleanup, no
       `--no-verify`, no primary-checkout edits, and no orphaned worktrees;
     - preserve provenance by linking the source memory file/path in the plan.
   - Follow-up Beads items needed if no existing item tracks the stale NFR fix,
     the Codex bootstrap adapter, or the memory-to-instructions migration.
5. Only after the plan is solid, decide whether to:
   - file a proposed spec change for the stale Codex NFR sections, or
   - implement a project-local bootstrap adapter first and then revise the spec
     from evidence.

## Parity scope to carry forward

Treat "Claude memory -> instructions" as one slice of a larger Codex parity
effort, not the whole effort.

The minimum credible parity scope is:

1. **Instruction parity**: move durable Claude-only project memories into
   committed, agent-readable instruction files or the appropriate sibling repo
   instructions. Do not blindly dump memory into AGENTS.md. Classify and route.
2. **Skill/bootstrap parity**: make Codex able to reach the livespec operation
   surface from committed project files. In the current architecture, this
   likely means Codex adapters that reference `.claude-plugin/prose/<name>.md`
   and `.claude-plugin/scripts/bin/<name>.py`, not symlinks to nonexistent
   `.claude-plugin/skills/*`.
3. **Mechanical parity**: identify which Claude hooks/checks have Codex
   equivalents. Where Codex cannot run an equivalent hook, add a visible
   pre-flight checklist or repo check. Worktree-before-edit is the priority
   because neither the current Claude footgun guard nor git commit hooks prevent
   untracked primary-checkout edits.
4. **Spec cleanup**: repair or replace the stale Codex dogfooding NFR sections
   once evidence from actual Codex probes exists.
5. **Verification parity**: prove behavior from separate Codex processes and
   record the outputs under `research/codex-support/`. Do not accept "works in
   Claude" as proof of Codex support.

## Suggested verification commands

Run these or their current Codex equivalents and record results:

```bash
find . -maxdepth 4 \( -path './.git' -o -path './.claude/worktrees' \) -prune -o -path './.agents*' -print -o -path './.codex*' -print
codex debug prompt-input 'test'
codex exec --sandbox read-only '/livespec:help. Do not edit files. Tell me exactly which local instruction/prose file you read.'
codex exec --sandbox read-only 'livespec next dry run only. Do not edit files. Tell me exactly which wrapper you would invoke.'
```

If those commands fail because Codex does not auto-load `.agents/skills/`, that
is useful evidence. Do not paper over it.

## Recommendation on where to run this

Run the next investigation session in **Codex**, not Claude Code, because the
first task is to prove what Codex can and cannot load before designing the
adapter. Claude Code is better for later formal `/livespec:*` spec lifecycle
work once the Codex-side evidence has been captured.

If you switch to Claude Code immediately, it may hide the actual bootstrap
problem by giving you the already-working Claude Driver surface. Use Claude
Code later for governed spec mutation if Codex is not yet able to drive the
LiveSpec lifecycle safely.
