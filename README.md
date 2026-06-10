# livespec

A Claude Code plugin for governing a living natural-language
specification — seeding, proposing changes, critiquing, revising,
validating, and versioning.

## Install

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec@livespec
```

After install, restart Claude Code (or run `/reload-plugins`).
The eight slash commands below become available with the
`livespec:` namespace prefix.

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

```mermaid
flowchart TB
    human(["HUMAN"])

    subgraph driver["DRIVER (one per agent runtime)<br/>livespec-driver-{claude,codex,opencode,pi}"]
        drv["interactive driver<br/>(thin: binds core's spec-side CLIs<br/>+ harness-neutral prose to ONE tool runtime)"]
    end

    subgraph core["CORE — livespec<br/>(agnostic to BOTH Driver and orchestrator)"]
        spec["SPECIFICATION/ tree"]
        scli["spec-side reference CLIs<br/>seed / propose-change / revise /<br/>critique / doctor / prune-history<br/>(config-named, each overridable)"]
        prose["harness-neutral prose"]
        cfg[".livespec.jsonc — single wiring table<br/>names spec-side CLIs (defaulted)<br/>+ the 3 orchestrator CLIs"]
    end

    subgraph orch["ORCHESTRATOR (one of N; self-contained)<br/>reference assemblies: git-jsonl (serial; homegrown logic)<br/>· Beads/Dolt + Fabro (parallel; the dogfood default)"]
        rdr["spec-reader CLI<br/>(API undefined; exposes spec BY CATEGORY —<br/>categorizes, never conceals)"]
        gap["gap-capture CLI<br/>(detection method private:<br/>mechanical / LLM / human)"]
        drift["drift-capture CLI"]
        subgraph internals["INTERNAL — invisible to core AND Driver"]
            dispatcher["DISPATCHER<br/>polls Ledger, invokes Loop,<br/>writes status back; OWNS PARALLELISM"]
            ledger["LEDGER<br/>work-items + depends_on graph;<br/>concurrent-write system of record<br/>(Beads/Dolt or git-jsonl)"]
            loop["LOOP<br/>per-work-item producer<br/>(homegrown or Fabro)"]
            oskills["orchestrator-shipped SKILL.md front-ends<br/>(interactive gap/drift consent dialogue;<br/>in-repo for now, plugin publication deferred)"]
        end
    end

    impl(["IMPLEMENTATION<br/>(the work product: code / tests / config / infra<br/>the spec is FOR)"])

    zerodep["ZERO direct Driver ↔ orchestrator dependencies<br/>(load-bearing invariant; forbidden both ways)"]

    human -->|"drives the spec lifecycle<br/>interactively"| drv
    human -->|"interactive gap/drift consent<br/>(orchestrator-owned)"| oskills

    drv -.->|"[D1] vendors core, reads<br/>prose by relative path"| prose
    drv -->|"[D2] wraps + invokes<br/>spec-side CLIs"| scli
    cfg -.->|"[D3] names the<br/>spec-side CLIs"| drv

    cfg -.->|"[O1] names the 3 orchestrator CLIs<br/>(core knows names + callability ONLY)"| orch
    rdr -->|"[O2] reads BY CATEGORY"| spec
    drift -->|"[O3] invokes the injected propose-change CLI<br/>(files proposed-changes;<br/>machine files, HUMAN accepts)"| scli
    scli -.->|"[O4] doctor: every config-named CLI<br/>resolves + is callable<br/>(callability, nothing more)"| orch

    rdr -.->|"spec-reader injected"| gap
    rdr -.->|"spec-reader injected"| drift
    gap -->|"writes gaps<br/>(gap CORRECTS the implementation)"| ledger
    oskills -.->|"fronts"| gap
    oskills -.->|"fronts"| drift
    dispatcher <-->|"ready items /<br/>status writeback"| ledger
    dispatcher -->|"invokes per<br/>work-item"| loop
    loop -->|"produces"| impl
    impl -.->|"realized artifact teaches back<br/>(drift CORRECTS the spec)"| drift

    driver -.- zerodep
    zerodep -.- orch

    classDef noteStyle fill:#fff8c5,stroke:#b08800,color:#111
    class zerodep noteStyle
```

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
implementations architecture" (the fenced Mermaid block above IS the
canonical architecture diagram, per that section).
Design rationale:
[`research/workflow-processes/livespec-as-contract-and-reference-implementations.md`](research/workflow-processes/livespec-as-contract-and-reference-implementations.md)
(+ the
[reframing follow-up](research/workflow-processes/livespec-as-contract-and-reference-implementations-reframing.md)).
The §"Cross-repo orchestration" section below describes the CURRENT
(pre-migration) state and is superseded as the phases land.

## Cross-repo orchestration

The Layer 3 cross-repo orchestration driver lives at
[`.claude/skills/livespec-orchestrate/SKILL.md`](.claude/skills/livespec-orchestrate/SKILL.md)
per `SPECIFICATION/spec.md` §"Three-layer orchestration architecture". It
is a project-local skill (loaded as `/livespec-orchestrate` when
working inside this repo) — NOT a namespaced plugin skill; the
`livespec-` prefix is a manual visual scoping convention to avoid
colliding with the harness's built-in `/loop` recurring-task skill —
and it is the single Layer 3 driver across the whole livespec family
of repos (livespec, livespec-impl-*, livespec-dev-tooling,
livespec-runtime).

The driver composes `/livespec:next` and the active impl-plugin's
`next` into a cross-side ranking, dispatches sub-agents (with
worktree isolation) into the sibling repos, runs `just check` plus
`/livespec:doctor` as a hard janitor gate, and emits a structured
iteration journal. It accepts `mode` (interactive | autonomous),
`budget` (iteration count | wallclock | tokens), an optional `epic`
work-item ID, and an optional `scope-file` carrying epic-specific
pre-authorization rules.

Halt conditions, dispatch table, and the wave-plan grammar for
`scope-file` are documented in the skill body.

## Fresh-clone setup

After cloning, run `just bootstrap` once. The target idempotently sets `livespec.primaryPath` on the primary checkout and installs the canonical commit-refuse hook at `.git/hooks/pre-commit` + `.git/hooks/pre-push` (per `SPECIFICATION/non-functional-requirements.md` §"Primary-checkout commit-refuse hook" / §"Commit-refuse hook bootstrap procedure"), forcing every edit through `git worktree add` while still allowing reads/fetches at the primary, then installs lefthook hooks and resolves plugin dependencies.

## Dogfooding (editing the plugin source in this repo)

Two paths:

- **Live-reload mode** (daily dev): launch Claude Code with
  `claude --plugin-dir .` from the repo root. The plugin loads
  directly from the local source; edits to `.claude-plugin/skills/<name>/SKILL.md`
  and `.claude-plugin/scripts/...` are picked up via `/reload-plugins`
  without re-installing.
- **Marketplace install path** (verifies the published flow):
  use the install commands above (or
  `/plugin marketplace add ./.claude-plugin/marketplace.json`
  for the local marketplace variant). Either copies the plugin
  into `~/.claude/plugins/cache/` and does NOT live-reload — run
  `/plugin update livespec@livespec` to pull changes after editing.

## More

- See [AGENTS.md](AGENTS.md) for repo orientation.
- See [SPECIFICATION/](SPECIFICATION/) for the live livespec specification (dogfooded).
- See [archive/](archive/) for bootstrap-process history.
