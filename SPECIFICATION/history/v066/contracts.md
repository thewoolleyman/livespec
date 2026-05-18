# Contracts — `livespec`

This file enumerates the wire-level interfaces between `livespec`'s skill prompts, Python wrappers, and templates. Per `livespec`'s repo-native principle, contracts MUST be language-neutral (JSON or CLI argument shapes), so any tool authored against the contracts works regardless of which language internalizes them.

## Wrapper CLI surface

Every Python wrapper under `.claude-plugin/scripts/bin/<sub-command>.py` MUST accept `--project-root <path>`, defaulting to `Path.cwd()`. Each sub-command adds its own flags above that baseline.

| Sub-command | Required flags | Optional flags |
|---|---|---|
| `seed` | `--seed-json <path>` | `--project-root <path>` |
| `propose-change` | `--findings-json <path>`, `<topic>` (positional) | `--author <id>`, `--reserve-suffix <text>`, `--spec-target <path>`, `--project-root <path>` |
| `critique` | `--findings-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |
| `revise` | `--revise-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |
| `prune-history` | (none) | `--skip-pre-check`, `--run-pre-check`, `--project-root <path>` |
| `doctor` (static) | (none) | `--project-root <path>` |
| `resolve-template` | `--template <value>` | `--project-root <path>` |
| `next` | (none) | `--spec-target <path>`, `--project-root <path>` |

The `--spec-target <path>` flag MUST select a spec tree (the main spec or a sub-spec) explicitly. When omitted, the wrapper SHOULD default to `<project-root>/SPECIFICATION/` (the main spec).

## Lifecycle exit-code table

Every wrapper MUST emit one of the following exit codes:

| Code | Meaning |
|---|---|
| `0` | success — operation completed and any documented stdout was emitted |
| `1` | internal bug — uncaught exception; structured traceback on stderr |
| `2` | `UsageError` — bad CLI invocation (unknown flag, missing required arg, wrong arg count) |
| `3` | `PreconditionError` — project-state precondition not met (missing config, malformed file, idempotency conflict) |
| `4` | `ValidationError` — schema or wire-format validation failure on inbound payload (retryable per the calling SKILL.md's retry-on-exit-4 contract) |
| `127` | too-old Python or missing tool — `_bootstrap.py` early exit |

Domain errors flow as `Failure(<LivespecError>)` payloads on the railway; the supervisor `main()` pattern-matches and lifts the exit code from the error's `exit_code` ClassVar. Bugs propagate as raised exceptions to the supervisor's bug-catcher and result in exit 1.

## Skill ↔ template JSON contracts

The seed flow exchanges a JSON payload conforming to `seed_input.schema.json`. The schema is co-authoritative with its paired dataclass at `livespec/schemas/dataclasses/seed_input.py` per the schema-dataclass-pairing convention (v013 M6). Drift is caught by `dev-tooling/checks/schema_dataclass_pairing.py`.

The propose-change flow ingests `proposal_findings.schema.json`-conforming JSON via `--findings-json <path>`. The critique flow emits `proposal_findings.schema.json`-conforming JSON for downstream propose-change consumption. The doctor flow emits `doctor_findings.schema.json`-conforming JSON to stdout for the supervisor's exit-code derivation.

The revise flow ingests `revise_input.schema.json`-conforming JSON describing per-proposal accept/reject decisions and the resulting spec edits. Future widening MAY add additional payload schemas; each new schema MUST land with its paired dataclass in the same revision.

**Path-relativity documentation requirement.** Every wire-contract schema field that names a spec file path MUST document its path-relativity convention in the field `description`: either *project-root-relative* (e.g., `"SPECIFICATION/contracts.md"`) OR *spec-target-relative* (e.g., `"contracts.md"`). The two conventions MUST NOT be mixed within a single schema. Specifically: `proposal_findings.schema.json` `target_spec_files[]` items are project-root-relative; `revise_input.schema.json` `decisions[].resulting_files[].path` is spec-target-relative. Schema description text is the v1 enforcement surface; the description MUST appear directly on the field (not only in the surrounding human-prose contracts) so it is visible to any LLM or tool inspecting the loaded schema. A future revise cycle MAY add a doctor static check that grep-asserts every schema field whose JSON-pointer path matches `/path/i` or `/file/i` carries one of the two convention strings in its description.
## Thin-transport skill doctrine

Every contract-surface API a livespec plugin exposes MUST be exposed as a Claude Code skill (heavyweight authored or thin-transport per the terminology in `spec.md` §"Terminology"), NOT as a CLI-only surface or any other non-skill mechanism. This applies uniformly to `livespec-core` and to every `livespec-impl-*` plugin.

Thin-transport skills MUST delegate to a backing Python wrapper at `.claude-plugin/scripts/bin/<cmd>.py` following the wrapper-shape contract codified in §"Wrapper CLI surface"; the wrapper performs the work and the SKILL.md is a transport. The SKILL.md MUST stay short and MUST NOT accrete prompt content over time — all ranking, filtering, and formatting logic MUST live in the backing Python implementation. Mechanical enforcement (lint rule, line-count check, or SKILL.md schema) is deferred to a follow-on refinement, but the discipline is load-bearing for the doctrine.

Cross-plugin invocation (doctor invoking the active impl-plugin's `list-memos`, the project-local loop driver invoking `livespec-core:next` and `<impl-plugin>:next`, etc.) MUST go through the skill namespace (e.g., `/livespec-impl-plaintext:list-memos --filter=untriaged --json`), NOT through a direct CLI path. This makes the contract surface discoverable, namespaced, and agent-aware uniformly.

The thin-transport classification is internal to each skill's design and SHOULD be reflected in inline SKILL.md metadata or a tagging convention; the exact mechanism is deferred to a follow-on refinement. Diagram rendering treats thin-transport and heavyweight skills identically (both render as light-blue rounded rectangles per the diagram vocabulary).

## Template manifest wire contract

`template.json` carries a `template_format_version` field bumped from `1` to `2` for templates that declare the `spec_files` manifest. v1 templates omit `spec_files`; the loader MUST treat v1 templates as if they declared `kind: markdown` for each well-known file the template's seed prompt enumerates. v2 templates MUST declare `spec_files` as an object mapping spec-target-relative paths to per-file declaration objects.

Each declaration object MUST carry exactly one of:

- `{"kind": "markdown"}` — a textual markdown spec file (subject to markdown-shaped checks and full LLM-context inclusion).
- `{"kind": "diagram_source"}` — a textual diagram-language source file (LLM-readable; rendered via the project's render command). PlantUML and Mermaid are the canonical kinds; livespec MUST NOT enforce a specific diagram language at the schema level.
- `{"kind": "diagram_rendered", "derived_from": "<path>"}` — an opaque rendered artifact produced by the render command from the file at `derived_from`. The `derived_from` value MUST be a path string that appears as a `kind: diagram_source` entry in the same manifest. Multiple `diagram_rendered` entries MAY share the same `derived_from` value.

The schema bump from v1 to v2 lands in `.claude-plugin/scripts/livespec/schemas/template_config.schema.json`; the paired dataclass under `livespec/schemas/dataclasses/template_config.py` MUST stay co-authoritative per the schema-dataclass-pairing convention (v013 M6). Drift is caught by `dev-tooling/checks/schema_dataclass_pairing.py`.

### `.livespec.jsonc` render-commands shape

Projects whose active template declares any `diagram_source` entry MUST declare a `render_commands` object in `.livespec.jsonc` keyed by source kind. The v2 shape:

```jsonc
{
  "template": "<template-name>",
  "render_commands": {
    "diagram_source": ["plantuml", "-tsvg", "-o", "{output_dir}", "{source}"]
  }
}
```

The render command is an argv-form array (NOT a shell-string), so livespec MUST NOT invoke a shell to interpret it. Livespec MUST substitute `{source}` (project-root-relative path to the changed source file) and `{output_dir}` (the directory containing the source, project-root-relative) literally in the argv before invocation. The render command MUST run with `cwd` set to the project root. The exit code, stdout, and stderr capture follow the standard subprocess convention; non-zero exit fails the revise per `spec.md` §"Template manifest" rendering-lifecycle paragraph.

The render command is arbitrary executable code the project trusts; this trust boundary is the same as any project-config file in a Claude Code workflow, but the wire contract states it explicitly so the surface is not silently introduced.

## Sub-spec structural mechanism

Sub-spec emission is opt-in per v020 Q2: the seed prompt's pre-seed dialogue asks "Does this project ship its own livespec templates that should be governed by sub-spec trees?" On "yes", the prompt emits one `sub_specs[]` entry per template named in the dialogue, each carrying a per-template `files[]` array with its own spec-file paths under `<spec_root>/templates/<template_name>/`.

The seed wrapper materializes the main spec tree AND each sub-spec tree atomically per v018 Q1: a single `bin/seed.py --seed-json <payload>` invocation writes, for every spec tree, (a) every template-declared spec file, (b) the skill-owned `proposed_changes/README.md` and `history/README.md` directory-description files, (c) the `history/v001/` snapshot of every template-declared spec file, and (d) the `history/v001/proposed_changes/` subdirectory marker preserved in git via `.gitkeep` when the directory would otherwise be empty. The auto-captured `history/v001/proposed_changes/seed.md` + `seed-revision.md` are emitted for the main spec only; sub-specs do NOT receive auto-captured seed proposals per v018 Q1 — the main-spec `seed.md` documents the multi-tree creation as a whole, and each sub-spec's `history/v001/proposed_changes/` is consequently empty (the `.gitkeep` is the marker).

The `propose-change`, `revise`, and `critique` sub-commands accept `--spec-target <path>` to scope their operation to one specific spec tree. `--spec-target <project-root>/SPECIFICATION/templates/livespec/` targets the `livespec` template's sub-spec; `--spec-target <project-root>/SPECIFICATION/` targets the main spec; etc. The `doctor` sub-command takes only `--project-root`; its multi-tree enumeration is internal (see §"Per-sub-spec doctor parameterization").

## Per-sub-spec doctor parameterization

The doctor static phase runs once per spec tree. The wrapper's main loop enumerates the main spec plus every `<spec_root>/templates/<name>/` sub-spec, runs the static checks against each, and emits per-tree findings on stdout. The wrapper's overall exit code is the worst per-tree code: any `fail` finding lifts the wrapper to exit non-zero.

The static-check registry per v022 D7 is a narrowed enumeration in `livespec/doctor/static/__init__.py`. Each registered check exports `run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]`; the `ctx.spec_root` attribute carries the per-tree root. Per-check applicability dispatch (some checks apply only to main specs, some only to sub-specs) is finalized via the `DoctorContext`'s template-config inspection per v021 Q1.

## Doctor cross-boundary invariants

Doctor's responsibilities MUST include structural invariants that cross the spec / impl boundary by querying the active impl-plugin's machine surface (the `<impl-plugin>:list-work-items --json` and `<impl-plugin>:capture-impl-gaps` thin-transport / heavyweight skills defined by §"Implementation-plugin contract — the 9-skill surface"), plus a cross-repo coordination invariant that reads the active impl-plugin's `compat` block from `.livespec.jsonc` per §"Cross-repo coordination — pin-and-bump". All entries in this catalogue are STRUCTURAL invariants per the **transient vs durable-pending** principle articulated in `spec.md` §"Terminology" — binary, contract-level, mechanically checkable. Doctor MUST NOT add productivity-heuristic invariants (work-item staleness, work-item pile-up counts, etc.); those concerns belong to the impl-plugin's `next` skill and to the project-local orchestration layer.

The catalogue MUST include the four work-item invariants and the contract-version-compatibility invariant below.

### `gap-tracking-one-to-one`

Every gap surfaced by a fresh impl-plugin gap-detection run (i.e., invoking the active impl-plugin's `capture-impl-gaps` skill in a non-mutating dry-run mode at check time) MUST correspond to exactly one tracked work item across all statuses (open, in-progress, closed). The check is a SNAPSHOT — gap detection runs at check time and the resulting gap-id set is compared against the work-items store's current set of gap-id labels. The check fires `fail` when a gap-id appears zero times (untracked gap) or two-or-more times (duplicated tracking) in the work-items store. This invariant replaces the gap-tied invariant content previously embedded in the pre-`multi-repo-distribution-and-coordination` "Beads invariants" / "Gap-tied issue closure verification" sections (removed by that propose-change cycle).

### `no-orphan-blocker`

Every work item's declared `blocked_by` reference MUST resolve to an existing work item in the same impl-plugin's store. The check fires `fail` when a `blocked_by` reference targets a non-existent work-item id. Closed blockers are NOT orphans (their blocked-by relationship is historically valid); only missing-from-store ids fire the check.

### `no-stale-gap-tied`

A gap-tied open work item whose underlying gap no longer surfaces in a fresh impl-plugin gap-detection run MUST be closed via a non-fix disposition (`spec-revised`, `no-longer-applicable`, `resolved-out-of-band`, or equivalent administrative reason). The check fires `warn` (NOT `fail`) when an open gap-tied work item's gap-id is absent from a fresh detection run, with narration directing the user to close the item via the appropriate non-fix path. The `warn`-not-`fail` classification reflects that a stale gap-tied item is a productivity-grade nudge to administratively close the item, not a structural contract violation that should block the wrapper exit.

### `no-duplicate-gap-id`

No two open work items MAY claim the same gap-id label. The check fires `fail` when two or more open items share a gap-id. Closed items sharing a historical gap-id with an open item are exempt; this is the dual of `gap-tracking-one-to-one` viewed from the work-items-store side.

### `contract-version-compatibility`

The `contract-version-compatibility` doctor invariant reads the active impl-plugin's `compat` block from `.livespec.jsonc` (the block defined by §"Cross-repo coordination — pin-and-bump") and enforces two derivations:

1. The `livespec_core` semver range against the actually-installed `livespec-core` version (read from `livespec-core`'s `plugin.json.version`). When the installed version falls OUTSIDE the declared range, the check MUST fire `fail`.
2. The `pinned` tag value against the most-recent published `livespec-core` release tag. When the pinned tag is older than a configured drift threshold (measured in number of intermediate releases — exact threshold value deferred to a configuration key under `livespec-core`'s top-level `.livespec.jsonc` section, default value to be set by a follow-on refinement), the check MUST fire `warn` with narration directing the user to open a bump-pin PR.

A missing or malformed `compat` block on the active impl-plugin MUST fire `fail` — the pin-and-bump mechanism is REQUIRED, not optional. Consumers using a `livespec-impl-*` plugin without declaring `compat` are running out-of-contract.

A missing `livespec-core` installation MUST be detected by doctor's existing pre-step lifecycle (the `pre_check` static phase that runs before each invariant check; doctor's wrapper resolves the installed `livespec-core` version once and fails fast if it cannot be located), NOT by this invariant. This invariant assumes `livespec-core` is installed and reports the version it finds via the pre-step resolution.

## Resolved-template stdout contract

`bin/resolve_template.py` MUST emit on success exactly one line: the resolved template directory as an absolute POSIX path, followed by `\n`. Paths containing spaces are emitted literally; callers MUST NOT pipe through shells that re-split on whitespace. The contract is frozen in v1; future template-discovery extensions MUST extend, not replace, the stdout shape and CLI flag set.

## Help-requested escape

Every wrapper MUST treat `-h` / `--help` as a `HelpRequested` signal, emit the argparse-rendered help text on stdout, and exit 0 (NOT exit 2). Per `commands/CLAUDE.md`, `HelpRequested.text` is one of two `commands/`-layer stdout-write exemptions (the other being `resolve_template`'s resolved-path emission).

## Plugin distribution

`livespec-core` is distributed as a Claude Code plugin via a marketplace catalog at the repo-root path `.claude-plugin/marketplace.json`. The marketplace lists the single plugin declared by `.claude-plugin/plugin.json`. The plugin and marketplace names share the value `livespec-core` by deliberate choice; both names are stable v1 contracts and renaming either MUST flow through a propose-change cycle.

End-user install path:

```
/plugin marketplace add thewoolleyman/livespec-core
/plugin install livespec-core@livespec-core
```

The GitHub repository SHOULD be renamed from `thewoolleyman/livespec` to `thewoolleyman/livespec-core` as part of this proposal's adoption so that the repo name, marketplace name, and plugin name all share the same value. GitHub's automatic redirect mechanism preserves access via the old `thewoolleyman/livespec` URL after rename, but the canonical install path MUST use the new name.

Consumer projects MUST install `livespec-core` plus exactly one `livespec-impl-<X>` plugin (the active implementation choice). The active implementation MUST be declared in `.livespec.jsonc` via a top-level `implementation.plugin` key naming the active plugin. `.livespec.jsonc`'s schema root is `additionalProperties: true`; each plugin owns a top-level section named for the plugin and MUST validate its own section on read and MUST tolerate unknown sections. Secrets MUST NOT live in `.livespec.jsonc`; external-tracker implementations needing credentials MUST use a separate credentials channel (environment variables, OS keyring, secret manager).

After install, `livespec-core` exposes eight slash commands, namespaced under the plugin name: `/livespec-core:seed`, `/livespec-core:propose-change`, `/livespec-core:critique`, `/livespec-core:revise`, `/livespec-core:doctor`, `/livespec-core:prune-history`, `/livespec-core:help`, `/livespec-core:next`. The renamespace from the prior `/livespec:*` surface is a one-for-one rename with behavior unchanged; renaming any command requires a propose-change cycle.

The `marketplace.json` `description` field is a manual duplicate of `plugin.json`'s `description`; `plugin.json` is the source of truth. v1 does NOT enforce equality mechanically; future revise cycles MAY add a doctor static check to detect drift if it becomes operationally relevant.

Plugin uninstall and update flows are Claude Code platform behaviors and are not part of this contract.

### Daily dogfooding path

For maintainer development of the `livespec-core` plugin source in this repo, launch Claude Code with `--plugin-dir .` to load the plugin directly from the local source. Live edits to `.claude-plugin/skills/<name>/SKILL.md` and `.claude-plugin/scripts/...` are picked up via `/reload-plugins` without re-installing. The marketplace install path (`/plugin install livespec-core@livespec-core`) is for verifying the published install flow; it copies the plugin into `~/.claude/plugins/cache/` and does NOT live-reload.

## Cross-repo coordination — pin-and-bump

The cross-repo coordination mechanism between `livespec-core` and its sibling `livespec-impl-*` plugins is pin-and-bump: every consumer project MUST declare which `livespec-core` release tag the active impl plugin is currently pinned against. The pin lives in a per-plugin `compat` block inside `.livespec.jsonc` (Obsidian-style per-plugin compatibility manifest). The active impl plugin's autonomous loop runs against the pinned `livespec-core` release, never against HEAD. When `livespec-core` ships a new release, a bump-pin pull request fires in each consumer project (and in each impl plugin's own repository when relevant), and the migration to the new pinned version is the explicit scope of that PR.

The compat block carries two required fields: `livespec_core` (a semver range describing supported `livespec-core` versions, e.g., `>=2.0.0,<3.0.0`) and `pinned` (the specific `livespec-core` release tag the consumer currently runs against, e.g., `v2.3.0`). Both fields live on the active impl plugin's top-level section.

The active impl plugin's automation and the consumer project's autonomous workflows MUST run against the pinned `livespec-core` release, NOT against HEAD. Running against HEAD bypasses the audited coordination mechanism and MUST be considered an out-of-contract operation.

When `livespec-core` ships a new release tag, a bump-pin pull request MAY be opened automatically (auto-merge bot architecture deferred; v1 MAY rely on manual bump-pin PRs). The bump-pin PR's acceptance criterion is that the active impl plugin and the consumer project both continue to pass the post-bump invariant suite.

Breaking contract changes in `livespec-core` MUST be landed additively: the old contract surface stays valid for one or more releases; impl plugins migrate at their own cadence; only after the active impl plugin's release adopting the new surface ships MAY the old surface be removed in a subsequent `livespec-core` release. This mirrors the Kubernetes CRD multi-version-served pattern and the GCC `N` / `N-1` support window.

`.livespec.jsonc` MUST NOT carry secrets; the `compat` block contains only non-sensitive version metadata.

Example `.livespec.jsonc` excerpt (illustrative; the canonical schema lives in `livespec-core`'s JSON Schema fragment):

```jsonc
{
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "implementation": { "plugin": "livespec-impl-plaintext" },
  "livespec-impl-plaintext": {
    "format": "jsonl",
    "compat": {
      "livespec_core": ">=2.0.0,<3.0.0",
      "pinned": "v2.3.0"
    }
  }
}
```

A subsequent propose-change cycle defining doctor's expanded invariant catalog MUST include a `contract-version-compatibility` invariant that fires when `livespec_core` semver range OR `pinned` tag drift exceeds the configured threshold; the threshold value itself is out of scope for this proposal.

## Implementation-plugin contract — the 9-skill surface

Every `livespec-impl-*` plugin MUST expose these nine skills under its own namespace prefix (`/livespec-impl-<X>:<skill>`). Six are heavyweight authored skills (dialogue, detection logic, judgment calls); three are thin-transport skills (CLI pass-through per §"Thin-transport skill doctrine"). Consumer projects, doctor's cross-boundary invariants, and the project-local orchestration layer all consume the surface uniformly via skills.

### Heavyweight authored skills (6)

- **`capture-impl-gaps`** — detect spec → impl gaps mechanically via the Spec Reader; file gap-tied work items into the plugin's Work Items store with per-gap user consent. Collapses the prior `refresh-gaps` + `plan` skill pair into one ephemeral-detection skill. Detection state is in-memory and discarded at skill exit; no persistent intermediate artifact.
- **`capture-spec-drift`** — detect impl → spec drift heuristically (LLM-driven); per finding, with user consent, route to `/livespec-core:propose-change` via the cross-boundary handoff. Asymmetric counterpart to `capture-impl-gaps`: mechanical detection is on the spec → impl side; heuristic detection is on the impl → spec side.
- **`capture-work-item`** — freeform direct filing of an impl-side work item (bugs, refactors, tactical tasks). The resulting work item carries NO `gap-id` label and closes via the freeform fix path.
- **`implement`** — drive Red → Green for a single work item. For gap-tied items, verify closure by re-running `capture-impl-gaps` in dry-run mode and confirming the `gap-id` is no longer detected; for freeform items, close with a simple `--reason`. Closure branches on origin × disposition: gap-tied fix (verify + audit fields), freeform fix (simple reason), non-fix (administrative — `wontfix`, `duplicate`, `spec-revised`, `no-longer-applicable`, `resolved-out-of-band`).
- **`capture-memo`** — low-friction free-text deposit of an in-flight observation that the user is not yet ready to classify. Memos are transient by construction.
- **`process-memos`** — per-memo handholding dialogue with four dispositions: spec-bound (→ `/livespec-core:propose-change` cross-boundary handoff), impl-bound (→ freeform work item in the plugin's Work Items store), persistent-knowledge (→ Persistent Agent Knowledge store; the form is implementation-dependent), discard.

### Thin-transport skills (3) — required machine query surface

- **`list-memos`** — required (promoted from discretionary). Supports `--filter` flags (most notably `--filter=untriaged`) and `--json` output. Consumed by doctor's memo-hygiene invariant and by users for queue inspection.
- **`list-work-items`** — required (new). Supports filter flags (`--gap-tied`, `--blocked`, `--with-gap-id`, etc.) and `--json` output. Consumed by doctor's four work-item structural invariants (defined by a subsequent propose-change cycle), by the project-local loop driver for routing decisions, and by users for queue inspection.
- **`next`** — required (new). Ranks the most ripe impl-side action using whatever native primitives the backend provides (e.g., `bd ready` for a beads-backed impl, JSONL traversal for a plaintext impl, GitLab API for a gitlab impl). Returns structured JSON with at minimum `action`, `work_item_ref`, `urgency`, and `reason` fields. Pure function of impl-side state; no LLM in the ranking path. Asymmetric counterpart to `/livespec-core:next`.

### Cross-boundary handoffs (red edges in the workflow diagrams)

1. `<impl-plugin>:capture-spec-drift` → `/livespec-core:propose-change` (drift findings).
2. `<impl-plugin>:process-memos` → `/livespec-core:propose-change` (spec-bound memo disposition).
3. `/livespec-core:doctor` → `<impl-plugin>:list-memos --filter=untriaged --json` (memo-hygiene invariant).
4. `/livespec-core:doctor` → `<impl-plugin>:list-work-items --json` (work-item structural invariants).
5. The project-local Layer 3 loop driver invokes both `/livespec-core:next` and `<impl-plugin>:next` to compose cross-side recommendations; the cross-side composition itself is defined by a separate propose-change cycle for the orchestration layer.

### Backend-variability asymmetry

The impl-side query skills exist because impl backends are pluggable (plaintext / beads / gitlab / ...) and cross-side consumers (doctor, the loop driver, core's `next`) need a uniform abstraction across those variants. The spec side has the opposite property: the spec backend is fixed (the canonical `SPECIFICATION/` tree shape). Doctor's static phase already reads `<spec-root>/proposed_changes/` and `<spec-root>/history/` directly from the filesystem — no abstraction needed. Symmetric `list-proposed-changes` / `list-history` skills would be pure ceremony. This is the principled reason the spec-side surface grows only by `next`, while the impl-side surface grows by three.

## `/livespec-core:next` spec-side thin-transport skill

`/livespec-core:next` is a thin-transport skill per §"Thin-transport skill doctrine". The backing Python wrapper lives at `.claude-plugin/scripts/bin/next.py` following the wrapper-shape contract codified in §"Wrapper CLI surface". The SKILL.md MUST be a pass-through.

The skill MUST read spec-side state — the Proposed Changes queue under `<spec-root>/proposed_changes/`, the Specification History under `<spec-root>/history/`, and any cached unresolved doctor findings — and emit structured JSON. The output schema MUST include at minimum:

- `action` — one of `revise`, `propose-change`, `critique`, `prune-history`, `none`.
- `reason` — human-readable narration.
- `urgency` — one of `high`, `medium`, `low`.

Additional fields MAY be added by follow-on refinements.

The skill MUST NOT read impl-side stores; cross-side ranking composition (combining `/livespec-core:next` and `<impl-plugin>:next`) is the responsibility of the project-local orchestration layer, NOT of `livespec-core`. The skill MUST NOT mutate any spec-side state — it is purely advisory.

The skill MUST be exempt from the pre-step / post-step doctor static lifecycle (no mutation, no precondition risk) per the existing exemption convention for `help`, `doctor`, and `resolve-template`. See `spec.md` §"Sub-command lifecycle".

## Spec Reader required-capability surface

Every `livespec-impl-*` plugin MUST expose a Spec Reader adapter internally — an impl-side API surface that unifies spec-content access for the plugin's own skills. The Spec Reader is NOT a slash command and NOT a cross-boundary surface; it is a within-plugin contract that the plugin's skill authors implement and consume.

The Spec Reader MUST implement exactly the following four required capabilities. The API shape (function names, return types, language) is implementation-dependent and MUST be documented in the plugin's own `SPECIFICATION/`:

1. **Read the current Specification.** Return the full content (or section-level addressable subset) of every spec_root file the active template manifest declares (per the `spec_files` mechanism in §"Template manifest wire contract"). The set is template-dependent; the Spec Reader MUST consult the active template's manifest rather than hardcoding the well-known file list.
2. **Read the Specification History.** Return the content of any `vNNN/` directory under `<spec-root>/history/` for `NNN` in the contiguous range. MUST surface the pruned-marker exemption (`PRUNED_HISTORY.json`) for any version that has been pruned per the existing `version-directories-complete` exemption.
3. **Report the current spec version.** Return the latest `vNNN` integer under `<spec-root>/history/`. This is the canonical version the impl currently corresponds to.
4. **Read or summarize differences between specified versions.** Given two version numbers `vA` and `vB`, return a representation of what changed between them. The representation form is implementation-dependent (raw diff, structured change list, semantic summary, etc.); the contract is that the consumer skill MUST be able to answer "what is different between vA and vB."

The Spec Reader's internals MAY be a thin file pass-through (plain-text reads of the `spec_root` tree), a cached layer, a section-level index, an embedding-based retrieval, a RAG-style adapter, a denormalized graph, or anything in between. The required-capability surface defines WHAT the adapter MUST provide; the HOW is per plugin.

The Spec Reader MUST exclude content from `<spec-root>/proposed_changes/` from its returned spec content; only ratified canonical content is exposed. Pending proposals are not yet intent.

Skills that consume the Spec Reader include `capture-impl-gaps` (gap-rule enumeration; also uses the version query to detect what has changed since the skill's own last-checked marker, an impl-internal state), `capture-spec-drift` (comparison baseline), `implement` (work-item context resolution), and `process-memos` (spec-vs-impl disposition decisions). Other impl-side operations MAY consume it as needed.

The Spec Reader is NOT a Claude Code skill (no slash command, no namespace surface); it is an internal API within each `livespec-impl-*` plugin. This distinguishes it from the nine cross-boundary contract skills defined in §"Implementation-plugin contract — the 9-skill surface".

## Shared content sync — copier template

The shared-content sync mechanism between `livespec-core` and its sibling `livespec-impl-*` repos is `copier`: `livespec-core/templates/impl-plugin/` is the canonical scaffold for shared non-functional content (justfile, lefthook, mise, ruff/pyright, GitHub Actions workflows, and a starter project-local loop skill). Every `livespec-impl-*` repo MUST be generated from this template via `copier copy` and re-synced via `copier update`; each MUST carry a `.copier-answers.yml` tracking the template version it was last generated from. CI in each impl repo SHOULD run `copier update --dry-run` to surface drift, with `.claude/skills/loop/SKILL.md` explicitly excluded from drift detection because local divergence there is expected by the orchestration-layer design.

`livespec-core` MUST publish a copier template at `templates/impl-plugin/` (project-root-relative) containing the canonical scaffolding every `livespec-impl-*` repo derives from: `justfile`, `lefthook.yml`, `.mise.toml`, `pyproject.toml` (with the ruff/pyright config), `.github/workflows/*.yml`, `.claude-plugin/marketplace.json` and `plugin.json` skeletons, a starter `SPECIFICATION/` skeleton, and a starter `.claude/skills/loop/SKILL.md` orchestration driver.

Every `livespec-impl-*` repository MUST be generated from this template via `copier copy gh:thewoolleyman/livespec-core/templates/impl-plugin <target> --vcs-ref=<core-release-tag>` and MUST carry a `.copier-answers.yml` at the repo root tracking the template version it was last generated from.

When `livespec-core`'s `templates/impl-plugin/` changes, each impl repo SHOULD run `copier update` to re-sync; the 3-way merge preserves local divergence where possible and surfaces conflicts as merge markers. Each impl repo's CI SHOULD run `copier update --dry-run` and fail or warn on detected drift. `.claude/skills/loop/SKILL.md` MUST be excluded from drift detection because local divergence there is expected by the orchestration-layer design (a later propose-change cycle defines that layer in detail).

Secrets MUST NOT be templated through `copier`; secret material lives only in environment variables, OS keyring, or a secret manager.

## Pre-commit step ordering

Lefthook pre-commit runs three commands in order: `00-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `01-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `02-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest. Commit-msg stage runs two gates in order: first `just check-conventional-commits {1}` (validates the subject prefix matches Conventional Commits 1.0; rejects non-conformant subjects with a structured diagnostic naming the canonical type set per `non-functional-requirements.md` §"Constraints → Commit and merge discipline"); then `just check-red-green-replay {1}` (the v034 D3 replay hook). The Conventional Commits gate runs FIRST so non-conformant subjects fail fast before the heavier replay-mode dispatch. Pre-push runs `just check` (the full aggregate).

When the staged tree contains ZERO `.py` files, `just check-pre-commit` runs a CONSERVATIVE doc-only subset (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full aggregate, since the Python-related gates have no work to do on doc-only commits. The classification trigger is the strict "zero `.py` staged" predicate; any `.py` file in the staged tree (even a single test file in Red mode) routes through the full aggregate. Pre-push and CI MUST apply the same zero-`.py` subsetting predicate as pre-commit. (a) Pre-push delegates to a new `just check-pre-push` recipe (mirroring `check-pre-commit`) that computes the changeset via `git diff --name-only @{upstream}..HEAD` (falling back to `git diff --name-only origin/master..HEAD` when no upstream is configured); when zero `.py` paths appear in the diff, the recipe delegates to `check-pre-commit-doc-only`; otherwise it delegates to `just check`. (b) CI in `.github/workflows/ci.yml` MUST add a `setup` job that runs `git diff --name-only origin/${{ github.base_ref }}...HEAD` for `pull_request` events (and outputs `py_changed=true` for `push` and `merge_group` events unconditionally, since master/merge-queue must always run the full safety net), exposes `outputs.py_changed`, and the Python-code matrix entries gate on `if: needs.setup.outputs.py_changed == 'true'`. The repo-metadata matrix entries (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) MUST run unconditionally in CI to preserve the metadata safety net. (c) The lefthook `pre-push` stanza in `lefthook.yml` MUST be updated from `run: just check` to `run: just check-pre-push`. (d) The categorization of every `just check` target into either `python-code-checks` or `repo-metadata-checks` MUST be kept synchronized between justfile, lefthook, and CI without drift. The repo-metadata subset is exactly the current `check-pre-commit-doc-only` body: `check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`. Every other target in `just check` is a python-code check.

The zero-`.py` subsetting is sound because the Python-code checks are deterministic functions of the Python source tree; with no `.py` delta in the changeset, every Python-code check would pass-or-fail identically against the merge-base, and any pre-existing failure is a master-branch-state concern (covered by `check-master-ci-green`), not a per-PR concern. Master-branch CI runs (`push` to `master`, `merge_group`) MUST still run the full aggregate as the merge-queue safety net.

## Plugin versioning

`plugin.json.version` is the single source of truth for the shipped plugin's version. `marketplace.json` MUST NOT carry a `version` field — per Claude Code's manifest resolution order, `plugin.json.version` wins regardless, and duplication invites drift.

The `plugin.json.version` field is auto-managed by `release-please` from per-commit Conventional Commits via the `release-please-action` GitHub Action. release-please opens a release PR on every push to `master` carrying the next-version bump per the Conventional Commits → semver mapping:

- `feat:` → MINOR bump
- `fix:` → PATCH bump
- `feat!:`, `fix!:`, or any commit with a `BREAKING CHANGE:` footer → MAJOR bump
- All other types (`chore:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`, `revert:`) → no bump

The release-please configuration lives at `release-please-config.json` and `.release-please-manifest.json` at the repo root (per release-please's documented default). `CHANGELOG.md` is auto-maintained by release-please at the repo root.

The per-commit Conventional Commits → semver mapping requires every commit on `master` to carry a valid Conventional Commits subject prefix; the master merge strategy (rebase-merge only, codified in `non-functional-requirements.md` §"Constraints → Commit and merge discipline") preserves per-cycle commit subjects intact on master, ensuring release-please reads each commit's type directly without squash flattening.

## Sub-command wire contracts

The CLI-level wire contracts each sub-command's wrapper enforces at its argv boundary, beyond the schemas already declared in `## Skill ↔ template JSON contracts` and the exit-code semantics declared in `## Lifecycle exit-code table`.

### `critique` payload validation

`bin/critique.py` validates the inbound `--findings-json` payload against `proposal_findings.schema.json` at the wrapper boundary before any internal delegation. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per `## Lifecycle exit-code table`, the calling `critique/SKILL.md` prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-invoke the template prompt with error context; the retry count is intentionally unspecified in v1. The skill MAY surrender after a bounded number of retries by surfacing the structured findings to the user.

### `critique` internal delegation

After successful payload validation, `bin/critique.py` resolves the author identifier via the unified precedence codified in `spec.md` §"Author identifier resolution" and delegates to `propose-change`'s internal Python logic with the resolved-author stem as topic hint and the literal string `"-critique"` as the reserve-suffix parameter. The topic hint passed in is the un-slugged resolved-author stem itself; `critique` MUST NOT pre-attach `-critique` to the hint. `propose-change`'s reserve-suffix canonicalization (codified in `spec.md` §"Proposed-change and revision file formats" under "Reserve-suffix canonicalization") composes the two into the canonical critique-delegation topic, guaranteeing the `-critique` suffix is preserved intact at the 64-char cap and pre-attached `-critique` does not double. `-critique` is the canonical critique-delegation suffix; no other suffix value is permitted on this code path. The internal delegation MUST NOT retrigger the pre/post `doctor`-static cycle described in `spec.md` §"Sub-command lifecycle" — the outer `critique` invocation's wrapper ROP chain already covers the whole operation; only one pre-step and one post-step `doctor` run per outer CLI invocation, regardless of how many internal wrapper compositions occur. After the delegation writes the proposed-change file, `critique` exits with `propose-change`'s exit code; `critique` does NOT run `revise`. The user reviews the resulting proposed-change file and invokes `/livespec-core:revise` separately to process it.

### `revise` payload validation

`bin/revise.py` validates the inbound `--revise-json` payload against `revise_input.schema.json` at the wrapper boundary before any deterministic file-shaping. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per `## Lifecycle exit-code table`, the calling `revise/SKILL.md` prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-assemble (or re-prompt) accordingly; the retry count is intentionally unspecified in v1. The skill MAY surrender after a bounded number of retries by surfacing the structured findings to the user.

### `revise` resulting_files path-relativity guard

`bin/revise.py` MUST reject any `resulting_files[].path` that is (a) absolute (begins with `/`) or (b) begins with the spec-target directory's basename followed by `/` (e.g., `SPECIFICATION/contracts.md` when `spec_target` is `SPECIFICATION/`). These shapes indicate the LLM emitted a project-root-relative path where a spec-target-relative path is required. The wrapper MUST reject via `UsageError` (exit 2) at the same validation boundary as the schema check, before any file-shaping work runs. The narrowed predicate — basename + `/` at the start of the path, not a substring match — avoids false positives for legitimate paths that contain the spec-target stem internally (e.g., a hypothetical `templates/SPECIFICATION/foo.md`). The error message MUST name the offending path and state that paths MUST be relative to `<spec-target>/` with no leading prefix.

### Pre-step skip control

The `propose-change`, `critique`, `revise`, and `prune-history` wrappers each support a mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag pair via argparse's `add_mutually_exclusive_group`. Effective skip resolution: (1) `--skip-pre-check` present → skip = true; (2) `--run-pre-check` present → skip = false (overrides config); (3) neither flag → use the `.livespec.jsonc` config key `pre_step_skip_static_checks` (default `false`); (4) both flags present → argparse rejects with a usage error and the wrapper exits 2 via `IOFailure(UsageError)`. When the resolved value is `true`, the wrapper MUST emit a single-finding `{"findings": [{"check_id": "pre-step-skipped", "status": "skipped", "message": "pre-step checks skipped by user config or --skip-pre-check"}]}` JSON document to stdout and proceed without invoking the pre-step doctor static phase. The Python layer MUST NOT print warning text outside the structured-findings contract or as ad-hoc stderr text — LLM narration in the SKILL.md prose surfaces the warning to the user. `bin/doctor_static.py` rejects BOTH `--skip-pre-check` AND `--run-pre-check` (it IS the static phase); passing either to it results in argparse usage error, exit 2.

## Prompt-QA harness contract

The prompt-QA harness lives at `tests/prompts/_harness.py` as a dedicated test-infrastructure module, NOT a stripped-down `tests/e2e/fake_claude.py` variant. The two harnesses are scope-distinct: the prompt-QA harness performs no LLM round-trip and no wrapper invocation; the e2e harness drives wrappers end-to-end via the Claude Agent SDK surface. The leading underscore on `_harness.py` marks it as test-internal; it is not imported outside `tests/prompts/`.

### Fixture format

Each prompt-QA test case ships under `tests/prompts/<template>/<prompt>/<case>.json` as a JSON document conforming to the fixture-format schema at `tests/prompts/_fixture.schema.json` (validated at load time via `fastjsonschema`). The fixture's required fields are:

- `prompt_name` (string): the REQUIRED-prompt name, one of `"seed"`, `"propose-change"`, `"revise"`, `"critique"`.
- `schema_id` (string): the named wire-contract schema the `replayed_response` MUST validate against — one of `"seed_input.schema.json"`, `"proposal_findings.schema.json"`, `"revise_input.schema.json"`.
- `input_context` (object): the variables the skill prose would pass to the prompt at invocation time. Shape is template-specific.
- `replayed_response` (object): the canonical LLM-output JSON the harness asserts against. Authored alongside the fixture by hand or via a per-prompt regeneration cycle.
- `expected_schema_valid` (boolean): whether `replayed_response` is expected to validate against `schema_id`. The default-true case asserts schema conformance; the false case is reserved for negative-test fixtures (malformed-payload regression coverage).
- `expected_semantic_properties` (array of strings): each entry names a per-template assertion function the harness MUST invoke against `replayed_response`.

### Per-template assertion registry

Each built-in template ships `tests/prompts/<template>/_assertions.py` exporting a module-level `ASSERTIONS: dict[str, Callable[..., None]]` populated via explicit imports per the static-enumeration discipline. Dynamic discovery via `glob+importlib` is forbidden — the dict's contents MUST be visible to pyright strict so registry completeness is type-checkable. Each assertion function MUST accept keyword-only arguments `*, replayed_response: object, input_context: object` and raise `AssertionError` on any property violation. The harness invokes each name listed in `expected_semantic_properties` by lookup against the per-template `ASSERTIONS` dict; an unknown name MUST fail the test with a clear "unknown property name" diagnostic that names the missing assertion.

### Harness behavior

The harness exposes a single primary entry point with keyword-only arguments. Its behavior, in order:

1. Load the fixture file and validate it against `_fixture.schema.json`. Validation failure → `AssertionError`.
2. When `expected_schema_valid` is true, validate `replayed_response` against the JSON Schema named by `schema_id`. Validation failure → `AssertionError`.
3. When `expected_schema_valid` is false, assert that schema validation FAILS (negative-test coverage). Validation pass on a negative-test fixture → `AssertionError`.
4. For each name in `expected_semantic_properties`, look up the function in the per-template `ASSERTIONS` dict and invoke it with `replayed_response` and `input_context` keyword arguments. Any raised `AssertionError` propagates.

The harness does NOT execute the prompt against any LLM; it asserts that the canonical `replayed_response` continues to satisfy the contract. When per-prompt regeneration cycles update fixtures alongside their prompts, the prompt-QA test fails the regeneration if the regenerated prompt no longer satisfies the per-template catalogue's properties.

### Python-rule compliance

The harness module, the fixture-format schema, the per-template assertion modules, and the per-prompt test modules MUST satisfy every livespec Python rule that applies to test infrastructure: each `.py` file declares `__all__`; functions take keyword-only arguments per the universal `*` separator; function and method signatures carry full return-type annotations; dataclasses are `frozen=True, slots=True, kw_only=True`; private helpers carry the leading `_` prefix. Coverage measurement does NOT include `tests/prompts/` — the source list for `[tool.coverage.run]` is anchored at `livespec/`, `bin/`, `dev-tooling/`, so the unit-tier per-file 100% coverage gate does not extend to test infrastructure.

## E2E harness contract

The E2E integration test harness lives at `tests/e2e/fake_claude.py` as a
deterministic mock of the Claude Agent SDK's query-interface surface. It is
NOT the prompt-QA harness (`tests/prompts/_harness.py`); the two harnesses
are scope-distinct: the prompt-QA harness replays prompt-response pairs for
schema + semantic assertions; the E2E harness drives real wrappers end-to-end.

### Harness mode selection

The env var `LIVESPEC_E2E_HARNESS=mock|real` selects the harness tier:

- `mock` — uses `tests/e2e/fake_claude.py`. Invoked by
  `just e2e-test-claude-code-mock` (included in `just check`). Deterministic,
  instant, no LLM API cost. All mock-only scenarios run in this tier.
- `real` — uses the real `claude-agent-sdk` Python library. Invoked by
  `just e2e-test-claude-code-real` (NOT in `just check`). Requires
  `ANTHROPIC_API_KEY` env var. Mock-only scenarios MUST carry explicit pytest
  markers or `skipif` annotations and MUST be skipped in real mode.

### Mock-tier harness interface

`tests/e2e/fake_claude.py` exports one function per livespec sub-command. Each
function:

1. Generates a deterministic JSON payload conforming to the sub-command's
   wire-contract schema (per `SPECIFICATION/contracts.md` §"Skill ↔ template
   JSON contracts").
2. Writes the payload to a temporary file.
3. Invokes the corresponding `bin/<cmd>.py` wrapper as a subprocess via
   `sys.executable`.
4. Returns the `subprocess.CompletedProcess[str]` result.

All functions accept keyword-only arguments and carry full return-type
annotations. The mock DOES NOT stub any wrapper Python code; wrappers always
run for real. The mock replaces ONLY the payload-generation step that a real
LLM would perform.

### Seed-payload path convention

The mock's `seed` function generates a seed payload with the spec file at
`SPECIFICATION/spec.md` (path parts: `["SPECIFICATION", "spec.md"]`). This
two-part path satisfies the seed wrapper's `_MIN_PARTS_MAIN_SPEC = 2`
constraint so that `history/v001/` and `proposed_changes/` are materialized
under `SPECIFICATION/`. The doctor static phase and `prune-history` both
resolve the main spec root as `<project_root>/SPECIFICATION/` by default,
matching this convention.

### Test structure

The E2E test suite lives under `tests/e2e/test_*.py`. Shared tests run in
both mock and real tiers; mock-only scenarios carry explicit pytest markers.

**Happy path** (`test_happy_path.py`): seed → propose-change → critique →
revise → doctor → prune-history against a `tmp_path`-scoped git repo.
Each wrapper step is followed by `git add && git commit` so the
`out-of-band-edits` doctor check sees HEAD-committed spec state. Asserts on
filesystem state after each step (files exist, exit codes 0).

**Error paths**:
- `test_retry_on_exit_4.py` — first propose-change payload is schema-invalid
  (exit 4); second is well-formed (exit 0). Mock-only; real tier skips via
  `pytest.mark.mock_only`.
- `test_doctor_fail_then_fix.py` — pre-seeded `SPECIFICATION/spec.md` containing a normative keyword
  in non-standard capitalization trips `bcp14-keyword-wellformedness`; propose-change +
  revise with `--skip-pre-check` fixes it; second doctor invocation exits 0.
  Runs in both tiers.
- `test_prune_history_noop.py` — project with only `v001` history; prune-history
  emits a `prune-history-no-op` skipped Finding and exits 0. Runs in both tiers.

### Python-rule compliance

`tests/e2e/fake_claude.py` and `tests/e2e/test_*.py` MUST satisfy every
livespec Python rule that applies to test infrastructure: each `.py` file
declares `__all__`; functions take keyword-only arguments per the universal
`*` separator; function and method signatures carry full return-type
annotations; private helpers carry the leading `_` prefix. Coverage
measurement does NOT include `tests/e2e/` — the source list for
`[tool.coverage.run]` is anchored at `livespec/`, `bin/`, `dev-tooling/`, so
the unit-tier per-file 100% coverage gate does not extend to E2E test
infrastructure.
