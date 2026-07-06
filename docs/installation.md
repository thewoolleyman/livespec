# Installing livespec on a project

livespec is installed by an agent, not by hand: a single paste-able,
**idempotent** installation prompt walks your coding agent through
everything needed to reach the start of the spec lifecycle —
`/livespec:seed` for a project with no spec yet (greenfield or
brownfield), or a clean `/livespec:doctor` run for an
already-governed one. Re-running the prompt is safe: whatever is
already set up is left alone; whatever is missing or drifted is
added or repaired.

The prompt lives in
[`livespec-installation-prompt.md`](livespec-installation-prompt.md)
(everything below its horizontal rule is the prompt). It asks you two
questions along the way — which Driver(s) to install (Claude Code /
Codex / both) and which orchestrator backend to use
(`livespec-orchestrator-beads-fabro`, recommended, or the
zero-infrastructure `livespec-orchestrator-git-jsonl`) — each with a
recommendation and the trade-offs spelled out.

## Run it

From the root of the project you want governed:

**Claude Code** — start a session and paste the prompt, or hand it
the file by reference:

```text
Fetch https://raw.githubusercontent.com/thewoolleyman/livespec/master/docs/livespec-installation-prompt.md
and follow the instructions below its horizontal rule.
```

**OpenAI Codex** — paste the prompt into the TUI, or run it headless:

```bash
codex exec "$(curl -fsSL https://raw.githubusercontent.com/thewoolleyman/livespec/master/docs/livespec-installation-prompt.md)"
```

Those are the two supported harnesses today; a new Driver plugin adds
a harness.

## After the prompt finishes

- No spec yet: run `/livespec:seed` — the attended interview that
  authors the initial specification and writes `.livespec.jsonc`.
- Already governed: `/livespec:doctor` validates the existing tree.
- Chose the `livespec-orchestrator-beads-fabro` backend and will
  dispatch implementation work into the factory? The prompt's final
  phase (post-seed factory-infrastructure prerequisites) walks the
  project's own GitHub App, the full dispatch credential set, the
  work-items tenant, and the per-tenant Fabro server that unattended
  dispatch needs — none of which blocks seeding. A
  `livespec-orchestrator-git-jsonl` adopter has no such infrastructure
  and is done once the spec lifecycle runs.

Authoritative contract surface: `SPECIFICATION/contracts.md` §"Plugin
distribution" and `SPECIFICATION/non-functional-requirements.md`; the
spec wins on any conflict with the prompt's procedural narrative.
