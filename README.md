# livespec

A system for governing a living natural-language specification —
seeding, proposing changes, critiquing, revising, validating, and
versioning. This repo is livespec CORE: the contract, the
harness-neutral driving prose, the reference spec-side CLIs, the
schemas, and the built-in templates. The interactive slash-command
surface ships separately as a per-agent-runtime **Driver** plugin
(the first is [livespec-driver-claude](https://github.com/thewoolleyman/livespec-driver-claude)
for Claude Code).

## Install

Two plugins — core (this repo: prose + CLIs + templates) and the
Claude Code Driver (the `/livespec:*` commands):

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec@livespec
/plugin marketplace add thewoolleyman/livespec-driver-claude
/plugin install livespec@livespec-driver-claude
```

After install, restart Claude Code (or run `/reload-plugins`).
The eight slash commands below become available with the
`livespec:` namespace prefix (the Driver plugin is deliberately
named `livespec` to preserve the established surface).

## Slash commands

- `/livespec:seed` — author the initial natural-language spec
- `/livespec:propose-change` — file a proposed change against the spec
- `/livespec:critique` — surface issues in the spec
- `/livespec:revise` — accept or reject pending proposed changes
- `/livespec:doctor` — run static + LLM-driven validation
- `/livespec:prune-history` — collapse old `history/vNNN/` entries
- `/livespec:next` — rank the next spec-side action (revise, propose-change, critique, prune-history, or none)
- `/livespec:help` — overview + routing to the right sub-command

## Architecture — contract + reference implementations

The **canonical architecture diagram** (Mermaid) is the single source
of truth in
[`SPECIFICATION/spec.md` §"Contract + reference implementations architecture"](SPECIFICATION/spec.md#contract--reference-implementations-architecture)
— it renders inline there on GitHub. To keep it DRY (one source, no
duplication / rot / drift), this README **references** that diagram
rather than embedding a second copy.

The decided target architecture (2026-06-09): LiveSpec core is a
**CLI contract** wired by `.livespec.jsonc`, agnostic to both the
**Driver** (the thin per-agent-runtime wrapper — Claude Code, Codex,
Pi) and the **orchestrator** (the pluggable producer whose work
product is the implementation; internally a Ledger + Loop +
Dispatcher). There are ZERO direct dependencies between Driver and
orchestrator. Reference orchestrators: **git-jsonl** (serial) and
**Beads/Dolt + Fabro** (parallel; dogfooded family-wide).

Three invariants the diagram pins down:

- **ZERO direct Driver ↔ orchestrator dependencies** (load-bearing
  invariant). Forbidden both ways: the Driver never reads
  orchestrator prose; the orchestrator never calls back into the
  Driver.
- **The orchestrator is self-contained**: prose / prompts / store /
  loop are PRIVATE. Interactive dialogue is orchestrator-owned via
  its own in-repo SKILL.md front-ends (decision 2026-06-09). If
  LLM-driven without its own runtime, it shells a model CLI as a
  subprocess — depending on "a model is invokable", NOT on the
  Driver. Ledger/Loop/Dispatcher is internal decomposition guidance,
  never core contract surface.
- **Doctor is NOT privileged**: config-named and overridable like any
  other spec-side CLI. Its entire cross-boundary job is CLI
  callability. Core never sees work-items, gaps, stores, or
  dependency graphs.

Normative home: `SPECIFICATION/spec.md` §"Contract + reference
implementations architecture", which carries the canonical Mermaid
diagram itself (single source of truth).
Design rationale:
[`research/workflow-processes/livespec-as-contract-and-reference-implementations.md`](research/workflow-processes/livespec-as-contract-and-reference-implementations.md)
(+ the
[reframing follow-up](research/workflow-processes/livespec-as-contract-and-reference-implementations-reframing.md)).
The §"Cross-repo orchestration" section below describes the
post-cutover state: the resident Layer-3 loop driver has been retired
in favor of the reference Dispatcher.

## Cross-repo orchestration

Cross-repo orchestration is carried by the reference **Beads/Dolt +
Fabro orchestrator** — a Beads/Dolt Ledger, a Fabro Loop, and a thin
Dispatcher (`livespec-impl-beads`'s `dispatcher.py`). The Dispatcher
polls the ledger, dispatches each ready work-item into its own Fabro
sandbox, runs `just check` plus `/livespec:doctor` as a hard janitor
gate, verifies the merge, and closes the item — carrying routine
cross-repo work unattended across the whole livespec family (livespec,
livespec-impl-*, livespec-dev-tooling, livespec-runtime).

The project-local `/livespec-orchestrate` Layer-3 loop-driver skill
that previously filled this role was **retired at the W6 dark-factory
cutover** (user-declared 2026-06-15), per `SPECIFICATION/spec.md`
§"Contract + reference implementations architecture". No repository is
required to carry a cross-repo loop driver as core contract surface;
the Dispatcher's invocation surface (`mode`, `budget`), janitor
hard-gate, and structured iteration journal are codified in the
orchestrator repo's own specification. The retired skill is
recoverable from git history.

## Fresh-clone setup

After cloning, run `just bootstrap` once. The target idempotently sets `livespec.primaryPath` on the primary checkout and installs the canonical commit-refuse hook at `.git/hooks/pre-commit` + `.git/hooks/pre-push` (per `SPECIFICATION/non-functional-requirements.md` §"Primary-checkout commit-refuse hook" / §"Commit-refuse hook bootstrap procedure"), forcing every edit through `git worktree add` while still allowing reads/fetches at the primary, then installs lefthook hooks and resolves plugin dependencies.

## Dogfooding (editing the plugin source in this repo)

Two paths:

- **Live-reload mode** (daily dev): launch Claude Code with
  `claude --plugin-dir .` from the repo root. The core plugin loads
  directly from the local source; edits to `.claude-plugin/prose/<name>.md`
  and `.claude-plugin/scripts/...` are picked up via `/reload-plugins`
  without re-installing. (The Driver's SKILL.md bindings resolve a
  local core checkout automatically when the governed project IS this
  repo; edit the bindings themselves in the
  [livespec-driver-claude](https://github.com/thewoolleyman/livespec-driver-claude)
  repo.)
- **Marketplace install path** (verifies the published flow):
  use the install commands above (or
  `/plugin marketplace add ./.claude-plugin/marketplace.json`
  for the local marketplace variant). Either copies the plugin
  into `~/.claude/plugins/cache/` and does NOT live-reload — run
  `/plugin update livespec@livespec` to pull changes after editing.

## Observability

The livespec family dogfoods its own telemetry. CI runs, Red→Green commit-gate cycles, the beads+fabro dispatcher, sandbox runs, and harness sub-agents are published to a shared Honeycomb environment:

- **[livespec family — all activity](https://ui.honeycomb.io/thewoolleyweb/environments/livespec/board/krThv8DvcwS)** — the cross-repo activity board (Honeycomb, `livespec` environment).

## More

- See [AGENTS.md](AGENTS.md) for repo orientation.
- See [SPECIFICATION/](SPECIFICATION/) for the live livespec specification (dogfooded).
- See [archive/](archive/) for bootstrap-process history.
