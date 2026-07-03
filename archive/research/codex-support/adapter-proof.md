> **STATUS: SUPERSEDED (2026-06-23).** This document describes the
> **retired** repo-local `.agents/skills/livespec-*` Codex adapter model.
> Core no longer ships any repo-local `.agents/skills/livespec-*` adapter
> directory — that model was RETIRED in livespec PR #528 (the v129 spec
> cut adopted the distributed Codex driver contract). The proof captured
> below was real for the repo-local model at the time; it is preserved as
> a record of the research journey, NOT as a description of current
> behavior.
>
> **Current Codex support is the DISTRIBUTED model:**
> - Core `livespec` is itself Codex-installable as an artifact carrier
>   (ships `prose/` + wrappers, NO skills): `codex plugin marketplace add
>   thewoolleyman/livespec` + `codex plugin add livespec@livespec`.
> - The interactive `/livespec:*` surface ships from the Codex **Driver**
>   `livespec-driver-codex` (`livespec@livespec-driver-codex`); each thin
>   Codex `SKILL.md` resolves core's install root and reads
>   `<core-root>/prose/<name>.md`.
> - Each orchestrator ships its OWN cross-runtime Codex surface (e.g.
>   `livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro`);
>   its heavyweight ops are shared-prose-backed, with both Claude and Codex
>   runtimes binding thin to the same `prose/<op>.md`.
> - Codex names the bound core prose file and (for wrapper-backed ops) the
>   `scripts/bin/...` wrapper directly — NO `.agents/skills/*` adapter
>   directory and NO `AGENTS.md` skill-mapping is involved.
>
> **Authoritative sources** (these are current; this file is not):
> `SPECIFICATION/contracts.md` §"Plugin distribution";
> `SPECIFICATION/non-functional-requirements.md` §"Codex dogfooding
> compatibility" and §"Codex dogfooding contracts". The
> `livespec-driver-codex` build record lives in the local scratch handoff
> `tmp/livespec-driver-codex-build-handoff.md` (gitignored; present only in
> the build checkout).

# Codex read-only adapter proof

Date: 2026-06-19
Worktree: `/data/projects/livespec-codex-readonly-adapters`
Branch: `codex-readonly-adapters`

## Summary

The first project-local Codex adapter slice exists under `.agents/skills/` for
the read-only `help`, `next`, and `doctor` livespec operations. Each adapter has
valid Codex YAML frontmatter and delegates behavior to the core prose under
`.claude-plugin/prose/`, with wrapper-backed operations naming the existing core
wrapper under `.claude-plugin/scripts/bin/`.

## Commands and evidence

### Project skills present

Command:

```bash
find .agents/skills -maxdepth 2 -type f -name SKILL.md -print
```

Result:

```text
.agents/skills/livespec-help/SKILL.md
.agents/skills/livespec-doctor/SKILL.md
.agents/skills/livespec-next/SKILL.md
```

### Prompt assembly

Command:

```bash
codex debug prompt-input '/livespec:help'
```

Key result: Codex prompt assembly listed project skill root
`/data/projects/livespec-codex-readonly-adapters/.agents/skills` and the three
skills:

```text
livespec:livespec-doctor
livespec:livespec-help
livespec:livespec-next
```

### Help adapter probe

Command:

```bash
codex exec --sandbox read-only '/livespec:help. Do not edit files. Tell me exactly which local instruction/prose file you read.'
```

Key result: the separate Codex process selected `livespec:livespec-help` and
read:

```text
/data/projects/livespec-codex-readonly-adapters/.agents/skills/livespec-help/SKILL.md
/data/projects/livespec-codex-readonly-adapters/.claude-plugin/prose/help.md
```

No files were edited.

### Next adapter probe

Command:

```bash
codex exec --sandbox read-only 'livespec next dry run only. Do not edit files. Tell me exactly which wrapper you would invoke.'
```

Key result: the separate Codex process selected `livespec:livespec-next`, read
the adapter and `.claude-plugin/prose/next.md`, and identified this dry-run
wrapper invocation:

```bash
python3 /data/projects/livespec-codex-readonly-adapters/.claude-plugin/scripts/bin/next.py \
  --project-root /data/projects/livespec-codex-readonly-adapters \
  --spec-target /data/projects/livespec-codex-readonly-adapters/SPECIFICATION \
  --limit 5 \
  --offset 0
```

No files were edited.

### Doctor adapter probe

Command:

```bash
codex exec --sandbox read-only 'livespec doctor help only. Do not edit files. Tell me exactly which wrapper you would invoke.'
```

Key result: the separate Codex process selected `livespec:livespec-doctor`,
read the adapter and `.claude-plugin/prose/doctor.md`, and identified:

```bash
.claude-plugin/scripts/bin/doctor_static.py --help
```

The subprocess noted there is no separate `bin/doctor.py` wrapper.

Observation: direct shebang execution first hit the untrusted `mise` shim in the
fresh worktree. The Codex subprocess then used the same wrapper via
`/usr/bin/python3 .claude-plugin/scripts/bin/doctor_static.py --help`, which
printed argparse help but exited `2`. That appears to be pre-existing
`--help` handling behavior in the wrapper path, not caused by the adapter.

No files were edited by the probe.
