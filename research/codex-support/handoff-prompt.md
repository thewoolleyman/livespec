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
- I did not find a current open Beads item specifically tracking "Codex
  conversion" across the livespec family. The main Codex content appears to be
  the stale spec text above plus generic Driver architecture references.
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
   - Follow-up Beads items needed, if no existing item tracks the stale NFR fix.
5. Only after the plan is solid, decide whether to:
   - file a proposed spec change for the stale Codex NFR sections, or
   - implement a project-local bootstrap adapter first and then revise the spec
     from evidence.

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
