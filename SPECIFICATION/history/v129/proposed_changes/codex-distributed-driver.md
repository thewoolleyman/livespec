---
topic: codex-distributed-driver
author: claude-opus-4-8
created_at: 2026-06-22T23:04:45Z
---

## Proposal: Name the distributed Codex Driver alongside the Claude Driver in the per-runtime Driver architecture

### Target specification files

- SPECIFICATION/spec.md

### Summary

Update spec.md to establish a TRUE distributed Codex Driver — a per-runtime Driver plugin repository `livespec-driver-codex` (the analogue of `livespec-driver-claude`) shipping thin Codex SKILL.md bindings over CORE's harness-neutral prose and wrapper CLIs — as the supported Codex path, and retire the stale claim that Codex dogfooding uses project-local `.agents/skills/` adapters rather than a Codex marketplace entry.

### Motivation

We are establishing a true distributed Codex driver analogous to the Claude driver. Codex has a real custom plugin marketplace (a repo carrying `.agents/plugins/marketplace.json` + per-plugin `.codex-plugin/plugin.json`, installed host-wide via `codex plugin marketplace add` + `codex plugin add`). The spec.md architecture text already names Codex in the agnostic-Driver list and in the canonical diagram's `livespec-driver-{claude,codex,opencode,pi}` Driver subgraph, but one prose line (the Plugin-distribution cross-reference) still asserts the project-local-adapter model as the current Codex path. That line must be re-pointed at the distributed Codex Driver so the architecture text is internally consistent.

### Proposed Changes

Two edits in `SPECIFICATION/spec.md`. No `## ` (H2) heading is added, removed, or renamed (the edits are prose inside existing H2 sections), so `tests/heading-coverage.json` is untouched.

**Edit 1 — §"Specification model" cross-reference line (currently "Codex dogfooding currently uses project-local `.agents/skills/` adapters rather than a Codex marketplace entry.").** Re-point it at the distributed Codex Driver and its marketplace install path:

```diff
-The core artifact is distributed via the Claude Code marketplace catalog declared at `.claude-plugin/marketplace.json` at the repo root; see `contracts.md` §"Plugin distribution" for the core install path and for how the Claude Driver plugin supplies the slash-command surface. Codex dogfooding currently uses project-local `.agents/skills/` adapters rather than a Codex marketplace entry.
+The core artifact is distributed to BOTH supported agent runtimes via marketplace catalogs declared at the repo root: a Claude Code marketplace at `.claude-plugin/marketplace.json` and a Codex marketplace at `.agents/plugins/marketplace.json` (with a paired `.codex-plugin/plugin.json`), both carrying the SAME `prose/` and `scripts/` over which each runtime's Driver plugin binds. See `contracts.md` §"Plugin distribution" for both core install paths and for how each runtime's Driver plugin (`livespec-driver-claude`, `livespec-driver-codex`) supplies its interactive command surface.
```

**Edit 2 — §"Contract + reference implementations architecture", the opening paragraph that enumerates the reference implementations at each seam.** Add a concrete sentence naming the two reference Driver bindings so the Codex Driver is established by name as a reference implementation alongside the Claude Driver. Insert immediately AFTER the existing first paragraph (the one ending "reference spec-side CLIs, reference Driver bindings, and reference orchestrators."):

```
**Reference Driver bindings.** Two per-runtime Driver plugin repositories are current reference work, each shipping THIN agent-runtime SKILL.md bindings over CORE's prose and wrapper CLIs and adding no operation behavior of its own: `livespec-driver-claude` (Claude Code) and `livespec-driver-codex` (OpenAI Codex CLI/TUI). Both expose the same eight spec-side operations; each resolves CORE's plugin root at runtime, reads the named core prose, and invokes the config-named spec-side CLI. Other runtimes (OpenCode, Pi) are recognized future Driver targets the contract admits, not commitments.
```

The canonical Mermaid diagram already names `livespec-driver-{claude,codex,opencode,pi}` in its DRIVER subgraph; no diagram edit is required.

## Proposal: Add the Codex marketplace to the Plugin distribution contract and require a Codex footgun-guard hook for mutating Codex automation

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Extend contracts.md §"Plugin distribution" to state that core is distributed to Codex via a `.agents/plugins/marketplace.json` + `.codex-plugin/plugin.json` over the SAME prose and scripts as the Claude marketplace, noting the host-wide Codex install model and its asymmetry versus Claude's project-scoped enablement; and extend §"Driver-shipped hooks" so the Codex Driver carries a Codex `pre_tool_use` hook port of the Claude footgun guard, REQUIRED before mutating Codex automation is claimed.

### Motivation

For a Codex Driver to resolve CORE's prose and CLIs from ANY governed repo (not only inside the core checkout), core must itself be installable as a Codex plugin — so core must ship a Codex marketplace over its existing `.claude-plugin/prose/` and `.claude-plugin/scripts/`. Codex plugin enablement is persisted HOST-WIDE in `~/.codex/config.toml`; there is no project-scoped committed-settings enablement like Claude's `.claude/settings.json`, an asymmetry the contract must record. Separately, the maintainer requires that the Codex Driver expose the FULL eight operations INCLUDING the mutating ones (seed, propose-change, critique, revise, prune-history); lifting the prior read-only restriction is only safe if a Codex `pre_tool_use` equivalent of the Claude `livespec_footgun_guard` (refuses `--no-verify`, `LEFTHOOK=0/false`, `core.bare=true`, and primary-checkout edits) is in place first.

### Proposed Changes

Two edits in `SPECIFICATION/contracts.md`. No `## ` (H2) heading is added, removed, or renamed (§"Plugin distribution" is an existing H2; §"Driver-shipped hooks" is an existing H3; the edits are body prose), so `tests/heading-coverage.json` is untouched.

**Edit 1 — §"Plugin distribution", after the opening paragraph that names the Claude marketplace (the paragraph ending "renaming either MUST flow through a propose-change cycle.").** Insert a new paragraph establishing the Codex marketplace:

```
`livespec` is ALSO distributed as a Codex plugin: core ships a Codex marketplace catalog at the repo-root path `.agents/plugins/marketplace.json` plus a paired `.codex-plugin/plugin.json`, both pointing at the SAME `prose/` and `scripts/` the Claude marketplace ships (a single cross-runtime artifact; no prose, wrapper, schema, or template is duplicated). The `.agents/plugins/marketplace.json` name and the `.codex-plugin/plugin.json` plugin name are stable v1 contracts; renaming either MUST flow through a propose-change cycle. A consumer installs core into Codex with `codex plugin marketplace add <owner>/<repo>` followed by `codex plugin add livespec@livespec`. Codex plugin enablement is HOST-WIDE: it is persisted in `~/.codex/config.toml` (a `[marketplaces.<name>]` entry plus a `[plugins."<plugin>@<marketplace>"] enabled = true` entry) and applies to every project on the host. This is asymmetric to the Claude path above, which enables plugins PER PROJECT via a committed `.claude/settings.json`; Codex offers no project-scoped plugin enablement, so the contract for Codex is the host-wide registration, not a committed per-project settings file.
```

**Edit 2 — §"Plugin distribution", the paragraph that currently begins "After installing core plus the Claude Code Driver, the Driver exposes eight slash commands...".** Generalize it so the Codex Driver's command surface is named alongside the Claude Driver's, without re-specifying mechanism:

```diff
-After installing core plus the Claude Code Driver, the Driver exposes eight slash commands, namespaced under the Driver plugin name: `/livespec:seed`, `/livespec:propose-change`, `/livespec:critique`, `/livespec:revise`, `/livespec:doctor`, `/livespec:prune-history`, `/livespec:help`, `/livespec:next`. Renaming any command requires a propose-change cycle. The slash-command surface is Driver-owned runtime mechanics; core supplies the harness-neutral prose, wrapper CLIs, templates, and schemas that the Driver binds.
+After installing core plus a runtime Driver, the Driver exposes the same eight operations as that runtime's interactive command surface: `seed`, `propose-change`, `critique`, `revise`, `doctor`, `prune-history`, `help`, `next`. The Claude Code Driver exposes them as `/livespec:*` slash commands namespaced under the Driver plugin name; the Codex Driver (`livespec-driver-codex`) exposes the same eight via Codex plugin skills resolving the same operations. Renaming any operation's command surface requires a propose-change cycle. The command surface is Driver-owned runtime mechanics; core supplies the harness-neutral prose, wrapper CLIs, templates, and schemas that each Driver binds.
```

**Edit 3 — §"Driver-shipped hooks".** This section currently names only the Claude Driver's two-hook bundle. Add a Codex footgun-guard requirement so mutating Codex automation is gated. Insert a new paragraph immediately BEFORE the closing "Adding or removing a hook in the Driver bundle..." paragraph:

```
**Codex footgun guard (required for mutating Codex automation).** The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the behavioral port of the Claude Driver's footgun guard: it MUST refuse a tool call that would (a) pass `--no-verify` to `git commit` / `git push`, (b) set `LEFTHOOK=0` or `LEFTHOOK=false` to disable lefthook, (c) set `core.bare = true` on a checkout, or (d) edit files at a livespec primary checkout. The guard MUST be in place before the Codex Driver claims any MUTATING operation (`seed`, `propose-change`, `critique`, `revise`, `prune-history`); read-only operations (`help`, `next`, `doctor`) do not depend on it. Like the Claude hook bundle, the script implementation and its tests live in the Driver repo; this section states only the required surface and its behavioral discipline. The fail-open discipline above applies: a hook failure (missing interpreter, malformed input, missing config) MUST be a silent pass-through, and the guard acts only when it POSITIVELY identifies a forbidden invocation. The destructive-command controls the operation prose already carries are PRESERVED and additive to this guard — in particular `prune-history` remains explicit-user-invocation only and MUST NOT be auto-activated.
```

The "Adding or removing a hook...requires a propose-change cycle" closing paragraph then governs this Codex hook surface as well.

## Proposal: Retire the repo-local Codex adapter model and lift the read-only restriction in the Codex dogfooding sections

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Rewrite the three Codex sections in non-functional-requirements.md — §"Codex dogfooding compatibility", §"Codex dogfooding contracts", and §"Codex dogfooding constraints" — plus the four Codex scenarios, so the supported Codex path is the distributed `livespec-driver-codex` plugin (thin Codex SKILL.md bindings over core prose + wrappers) rather than repo-local `.agents/skills/livespec-*` adapters; remove the hardcoded verified-adapter table that admits only help/next/doctor and the language forbidding Codex marketplace support; lift the read-only-only restriction so the Codex Driver exposes all eight operations including the mutating ones; require the Codex footgun-guard hook before mutating Codex automation; and re-point the acceptance/verification ceremony at the distributed driver while retaining its no-`.agents/skills/*`/no-`AGENTS.md` proof bar.

### Motivation

Codex dogfooding is a contributor-only concern, so all Codex spec content correctly lives in non-functional-requirements.md (the task brief's reference to a constraints.md §"Codex dogfooding constraints" does not match the tree — that section is in non-functional-requirements.md). The current text hardwires the project-local `.agents/skills/livespec-*` adapter model, hardcodes a three-adapter (help/next/doctor) verified table, forbids claiming Codex marketplace support, and keeps mutating operations out of the Codex surface. The maintainer has decided to establish a true distributed Codex Driver shipping the FULL eight operations including the mutating ones, gated by a Codex footgun-guard hook, with core itself Codex-installable via a marketplace. These sections must be re-pointed accordingly while preserving every destructive-command control and the host-isolation acceptance bar.

### Proposed Changes

Edits in `SPECIFICATION/non-functional-requirements.md`. No `## ` (H2) heading is added, removed, or renamed: §"Codex dogfooding compatibility", §"Codex dogfooding contracts", §"Codex dogfooding constraints", and the four `### Scenario: Codex ...` headings are all H3, and the four Codex scenario H3 headings are PRESERVED verbatim (their titles are retained, only their step bodies change). Because `tests/heading-coverage.json` tracks only H2 entries, it is untouched.

**Edit 1 — §"Codex dogfooding compatibility" (replace the section body).** Replace the five existing paragraphs with:

```
The `livespec` repository supports maintainer dogfooding from OpenAI Codex CLI/TUI through the distributed Codex Driver plugin `livespec-driver-codex` (the analogue of `livespec-driver-claude`), installed as a host-wide Codex plugin. The Codex Driver ships THIN Codex SKILL.md bindings over CORE's harness-neutral operation prose and wrapper CLIs; it carries no operation behavior of its own.

Codex dogfooding is a Driver binding, not a separate LiveSpec product command model. The authoritative command behavior remains the core-owned operation prose under `.claude-plugin/prose/<name>.md` plus the spec-side wrapper contracts under `.claude-plugin/scripts/bin/`. Claude Code and Codex differ only in their runtime binding mechanics: each runtime's Driver plugin binds the SAME core prose and wrappers from its own repository. The Codex Driver resolves CORE's plugin root at runtime (so it works from any governed repo, not only inside the core checkout), which requires core to be Codex-installable as a plugin per `contracts.md` §"Plugin distribution".

When a Codex session receives a request for a `/livespec:*` operation, the Codex Driver binding MUST read the matching `.claude-plugin/prose/<name>.md` file completely before acting; when that prose calls for a CLI, it MUST invoke the configured wrapper under `.claude-plugin/scripts/bin/` with explicit argv. The Codex Driver bindings MUST NOT copy operation prose, wrapper files, or built-in templates, and MUST NOT point at `.claude-plugin/skills/*`; core intentionally ships no `.claude-plugin/skills/` tree.

The Codex Driver exposes the FULL eight spec-side operations, INCLUDING the mutating ones (`seed`, `propose-change`, `critique`, `revise`, `prune-history`). Mutating Codex automation is gated on the Codex footgun-guard `pre_tool_use` hook required by `contracts.md` §"Driver-shipped hooks"; until that guard is in place a Codex Driver MUST NOT claim mutating operations. All destructive-command controls from the core prose are preserved — in particular `prune-history` remains explicit-user-invocation only.

Under the sibling-repo topology, each orchestrator plugin's repository is responsible for its own Codex Driver mapping (`/livespec-orchestrator-<ledger>[-<loop>]:*`); implementation-side workflows MUST NOT be promoted into `livespec` by Codex compatibility work.
```

**Edit 2 — §"Codex dogfooding contracts" (replace the section body, including removing the three-adapter table).** Replace the entire section body (the project-local-adapter prose, the verified-adapter table, the AGENTS.md paragraph, and the verification-command list) with:

```
Core is distributed to Codex as a plugin via `.agents/plugins/marketplace.json` + `.codex-plugin/plugin.json` over the same `prose/` and `scripts/` the Claude marketplace ships, per `contracts.md` §"Plugin distribution". The Codex Driver `livespec-driver-codex` is installed host-wide and binds those core files at runtime; this repository ships NO project-local `.agents/skills/livespec-*` adapter directories for the core operations — the repo-local adapter model is retired in favor of the distributed Driver.

Each Codex Driver binding MUST be thin: it reads the named core prose file completely, follows that prose for behavior and failure handling, invokes the named wrapper when wrapper-backed, and does not copy operation-specific prose sections. The Codex Driver carries all eight operations; the mutating subset is gated on the Codex footgun-guard hook per `contracts.md` §"Driver-shipped hooks".

The detailed Codex mapping for `/livespec-orchestrator-<ledger>[-<loop>]:*` commands is owned by each orchestrator plugin's own spec, consistent with §"Codex dogfooding compatibility".

Codex compatibility verification is performed with separate Codex processes against the installed distributed Driver. The acceptance bar is: a registered Codex plugin entry for `livespec@<marketplace>` exists in `~/.codex/config.toml`, and a `codex exec` invocation drives a `/livespec:*` operation through the Codex Driver and core prose WITHOUT relying on any `.agents/skills/*` adapter directory or an `AGENTS.md` mapping. The expected result is that Codex names the bound core prose file (`.claude-plugin/prose/<name>.md`) and, for wrapper-backed operations, the matching `.claude-plugin/scripts/bin/...` wrapper it invokes. Temporary local Codex marketplace registrations used for testing MUST be removed after the test unless the user explicitly asks to keep them.
```

**Edit 3 — §"Codex dogfooding constraints" (replace the section body).** Replace the four existing paragraphs with:

```
Codex compatibility for repository dogfooding MUST NOT duplicate LiveSpec operation prose, Python wrappers, or built-in specification templates. Core prose under `.claude-plugin/prose/<name>.md` and wrapper CLIs under `.claude-plugin/scripts/bin/` are the shared source of truth; the Codex Driver bindings MUST remain thin over those files and MUST NOT copy or restate operation-specific steps, failure handling, output schemas, or wrapper behavior in a way that can drift. The Codex Driver MUST NOT point at `.claude-plugin/skills/*` or require that tree to exist.

Core MAY claim Codex-native plugin support only once the Codex marketplace registration (`.agents/plugins/marketplace.json` + `.codex-plugin/plugin.json`) creates an installed `livespec` plugin entry AND a separate `codex exec` invocation can drive a `/livespec:*` operation through that registered plugin without relying on any `.agents/skills/*` adapter or `AGENTS.md` mapping. The mere existence of a `.codex-plugin/plugin.json` or `.agents/plugins/marketplace.json` file does NOT by itself license the claim.

Codex dogfooding MUST work without installing or modifying global/system packages beyond the host-wide Codex plugin registration the install model requires. Temporary local Codex marketplace registrations used for testing MUST be removed after the test unless the user explicitly asks to keep them.

The Codex Driver surface MUST preserve every destructive-command control from the core prose. In particular, `prune-history` remains explicit-user-invocation only, and Codex MUST NOT infer or auto-activate it from a generic mention of history. Mutating Codex operations (`seed`, `propose-change`, `critique`, `revise`, `prune-history`) MUST NOT be exercised unless the Codex footgun-guard `pre_tool_use` hook required by `contracts.md` §"Driver-shipped hooks" is in place.
```

**Edit 4 — the four `### Scenario: Codex ...` scenarios (rewrite step bodies; keep the four headings).** Re-point the steps from `.agents/skills/livespec-*/SKILL.md` to the distributed Codex Driver and the marketplace-install acceptance, keeping the gherkin-blank-line convention (one step per paragraph, no fenced blocks).

- `### Scenario: Codex help maps through the project adapter to core prose` — keep the heading; replace its steps with: Given a maintainer is running OpenAI Codex CLI/TUI with the `livespec` core plugin and the `livespec-driver-codex` Driver installed host-wide; When the maintainer asks `/livespec:help`; Then the Codex Driver binding reads `.claude-plugin/prose/help.md`; And Codex produces the LiveSpec help overview from that core prose; And Codex resolves the prose through the installed plugin without any `.agents/skills/*` adapter.

- `### Scenario: Codex next dry run identifies the shared wrapper` — keep the heading; replace its steps with: Given a maintainer is running OpenAI Codex CLI/TUI with the core plugin and `livespec-driver-codex` installed; When the maintainer asks for a read-only `livespec next` dry run; Then the Codex Driver binding reads `.claude-plugin/prose/next.md`; And Codex identifies `.claude-plugin/scripts/bin/next.py` as the wrapper it would invoke; And Codex does not duplicate or reimplement the wrapper contract.

- `### Scenario: Codex doctor help identifies the static wrapper` — keep the heading; replace its steps with: Given a maintainer is running OpenAI Codex CLI/TUI with the core plugin and `livespec-driver-codex` installed; When the maintainer asks for `livespec doctor help only`; Then the Codex Driver binding reads `.claude-plugin/prose/doctor.md`; And Codex identifies `.claude-plugin/scripts/bin/doctor_static.py` as the wrapper it would invoke.

- `### Scenario: Codex plugin registry is not assumed from metadata alone` — keep the heading; replace its steps with: Given `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` exist in the core repo; When no `codex plugin add` registration has created an installed `livespec` plugin entry in `~/.codex/config.toml`; Then repository documentation MUST NOT claim Codex-native plugin support; And the claim becomes valid only once marketplace registration creates the installed plugin entry and a `codex exec` invocation drives a `/livespec:*` operation through it without any `.agents/skills/*` adapter or `AGENTS.md` mapping.
