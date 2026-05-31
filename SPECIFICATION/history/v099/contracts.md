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
| `next` | (none) | `--spec-target <path>`, `--limit <count>`, `--offset <count>`, `--project-root <path>` |

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

Every contract-surface API a livespec plugin exposes MUST be exposed as a Claude Code skill (heavyweight authored or thin-transport per the terminology in `spec.md` §"Terminology"), NOT as a CLI-only surface or any other non-skill mechanism. This applies uniformly to `livespec` and to every `livespec-impl-*` plugin.

Thin-transport skills MUST delegate to a backing Python wrapper at `.claude-plugin/scripts/bin/<cmd>.py` following the wrapper-shape contract codified in §"Wrapper CLI surface"; the wrapper performs the work and the SKILL.md is a transport. The SKILL.md MUST stay short and MUST NOT accrete prompt content over time — all ranking, filtering, and formatting logic MUST live in the backing Python implementation. Mechanical enforcement (lint rule, line-count check, or SKILL.md schema) is deferred to a follow-on refinement, but the discipline is load-bearing for the doctrine.

Cross-plugin invocation (doctor invoking the active impl-plugin's `list-memos`, livespec's Layer 3 loop driver invoking `livespec:next` and `<impl-plugin>:next`, etc.) MUST go through the skill namespace (e.g., `/livespec-impl-plaintext:list-memos --filter=untriaged --json`), NOT through a direct CLI path. This makes the contract surface discoverable, namespaced, and agent-aware uniformly.

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

The doctor static phase runs once per spec tree. The wrapper's main loop enumerates the main spec plus every `<spec_root>/templates/<name>/` sub-spec, runs the static checks against each, and emits per-tree findings on stdout. The wrapper's overall exit code is the worst per-tree code derived from the four-value Finding `status` enum (`pass`, `fail`, `skipped`, `warn` per `finding.schema.json`): any `fail` finding lifts the wrapper to exit 3; `pass`, `skipped`, and `warn` findings all yield exit 0. The `warn` status is reserved for productivity-grade housekeeping nudges (`no-stale-gap-tied`, the three `Impl-side cleanup invariants`, and the optional pinned-tag drift check under `contract-version-compatibility`); the SKILL.md narration phase surfaces `warn` findings to the user but the Python layer MUST NOT emit ad-hoc stderr text for them (per the existing rule in `spec.md` §"Sub-command lifecycle" that the Python layer never prints warning text outside the structured-findings contract).

The static-check registry per v022 D7 is a narrowed enumeration in `livespec/doctor/static/__init__.py`. Each registered check exports `run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]`; the `ctx.spec_root` attribute carries the per-tree root. Per-check applicability dispatch (some checks apply only to main specs, some only to sub-specs) is finalized via the `DoctorContext`'s template-config inspection per v021 Q1.

## Doctor per-finding disposition dialogue

The `doctor` skill MUST offer a per-finding disposition dialogue for every non-`pass` finding surfaced during a single invocation, regardless of which phase produced it (static phase `fail` or `warn`, or any of the four LLM-driven phase categories — skill-baked objective, template-extension objective, skill-baked subjective, template-extension subjective). The disposition menu MUST present at minimum these five options:

- `fix-now` — apply the corrective action implied by the finding's `message`. OPTIONAL on a per-finding basis: only offered when the corrective action is mechanically describable from `message` (text edits, `mkdir`, single-shell-command cleanups). When the corrective action is not mechanically describable, this option MUST NOT be offered for that finding (the menu surfaces the remaining four).
- `capture-as-work-item` — file a freeform work item in the active impl-plugin's Work Items store via the impl-plugin's `capture-work-item` skill. The active impl-plugin is resolved via `.livespec.jsonc`'s `implementation.plugin` field; the cross-plugin invocation MUST go through the skill namespace per §"Thin-transport skill doctrine". The filed work item carries `origin: freeform` and embeds the finding's `check_id`, `spec_root`, optional `path`, and `message` in its body so the trail back to the originating doctor finding is preserved. This disposition MUST ALWAYS be offered for every non-`pass` finding.
- `propose-change` — invoke `/livespec:critique` against the appropriate `--spec-target` (the tree whose `spec_root` surfaced the finding) and thread a `proposed_change_hint` as the user-described change. For LLM-driven phase findings the hint is the one produced inline by the check. For static-phase findings the hint is generated fresh from the finding's `message` and `path`/`line` fields. This disposition MUST ALWAYS be offered.
- `defer` — record the finding in the session's narration; take no durable action. The finding MAY surface again on the next invocation.
- `dismiss` — the user judges the finding does not apply. No durable action. No cross-invocation persistence of dismissals in v1; the finding MAY surface again on the next invocation and the user dismisses again or chooses a different disposition.

The dialogue MUST run BEFORE the skill aborts on a static-phase `fail` (Exit 3 from the wrapper). The pre-existing safety contract that the LLM-driven phase MUST NOT run after a static-phase `fail` is PRESERVED: the dialogue handles disposition of the already-surfaced static findings only, with NO additional LLM-driven check generation. This narrows the scope of "abort" from "stop interacting with the user" to "do not run further check generation"; disposition of already-surfaced findings is not check generation.

The dialogue MUST run for static-phase `warn` findings too (today they are narrated in Step 3 without a disposition surface). The `warn` status retains its current semantics with respect to wrapper exit code (a `warn` finding does NOT lift the wrapper to exit 3); only the user-facing dispositioning is affected.

Findings with status `pass` and `skipped` are NOT dispositioned. They are surfaced via the existing Step 3 narration only.

A finding's disposition menu MUST present its five options in the canonical order listed above. The LLM prose surface MAY render the options as a single picker, MAY render them per-finding sequentially, or MAY batch all findings into a multi-disposition picker — the choice is a SKILL.md prose decision, not a contract one. The contract is the menu's CONTENT and AVAILABILITY guarantees.

## Doctor cross-boundary invariants

Doctor's responsibilities MUST include structural invariants that cross the spec / impl boundary by querying the active impl-plugin's machine surface (the `<impl-plugin>:list-work-items --json` and `<impl-plugin>:detect-impl-gaps --json` thin-transport skills defined by §"Implementation-plugin contract — the 10-skill surface"), plus a cross-repo coordination invariant that reads the active impl-plugin's `compat` block from `.livespec.jsonc` per §"Cross-repo coordination — pin-and-bump". All entries in this catalogue are STRUCTURAL invariants per the **transient vs durable-pending** principle articulated in `spec.md` §"Terminology" — binary, contract-level, mechanically checkable. Doctor MUST NOT add productivity-heuristic invariants (work-item staleness, work-item pile-up counts, etc.); those concerns belong to the impl-plugin's `next` skill and to the project-local orchestration layer.

The catalogue MUST include the five work-item invariants, the contract-version-compatibility invariant, and the `depends_on-ref-wellformedness` invariant defined below.

### `gap-tracking-one-to-one`

Every gap surfaced by a fresh impl-plugin gap-detection run (i.e., invoking the active impl-plugin's `detect-impl-gaps --json` thin-transport skill at check time) MUST correspond to exactly one tracked work item across all statuses (open, in-progress, closed). The check is a SNAPSHOT — gap detection runs at check time and the resulting gap-id set is compared against the work-items store's current set of gap-id labels. The check fires `fail` when a gap-id appears zero times (untracked gap) or two-or-more times (duplicated tracking) in the work-items store. This invariant replaces the gap-tied invariant content previously embedded in the pre-`multi-repo-distribution-and-coordination` "Beads invariants" / "Gap-tied issue closure verification" sections (removed by that propose-change cycle).

### `no-orphan-dependency`

Every work item's declared `depends_on` entries MUST resolve cleanly. The check fires `fail` when any `DependsOnEntry` with `kind == "local"` references a `work_item_id` that does not exist in the materialized work-items store. For `kind` values `sibling_work_item`, `pull_request`, and `branch`, the invariant defers to `livespec_runtime.cross_repo.resolve_ref` and fires `fail` only when the runtime returns `unknown` AND the target is declared resolvable (i.e., the entry's `repo` key is present in `cross_repo_targets`); a successful `open` or `closed` resolution is NOT a doctor failure (open dependencies are expected during in-flight work). Closed dependencies are NOT orphans — their depends-on relationship is historically valid. The `kind`-discriminator and the per-kind required-fields well-formedness are enforced separately by `### depends_on-ref-wellformedness`.

### `no-stale-gap-tied`

A gap-tied open work item whose underlying gap no longer surfaces in a fresh impl-plugin gap-detection run MUST be closed via a non-fix disposition (`spec-revised`, `no-longer-applicable`, `resolved-out-of-band`, or equivalent administrative reason). The check fires `warn` (NOT `fail`) when an open gap-tied work item's gap-id is absent from a fresh detection run, with narration directing the user to close the item via the appropriate non-fix path. The `warn`-not-`fail` classification reflects that a stale gap-tied item is a productivity-grade nudge to administratively close the item, not a structural contract violation that should block the wrapper exit.

### `no-duplicate-gap-id`

No two open work items MAY claim the same gap-id label. The check fires `fail` when two or more open items share a gap-id. Closed items sharing a historical gap-id with an open item are exempt; this is the dual of `gap-tracking-one-to-one` viewed from the work-items-store side.

### `no-stalled-epic`

A work item with `type == "epic"` and `status` in `{open, in_progress}` MUST be closed (or its `depends_on` extended) when every entry in its `depends_on` array resolves to an existing work-item with `status == "closed"`. The check fires `fail` when an open or in-progress epic has a NON-EMPTY `depends_on` array AND every resolved entry is closed. The check MUST NOT fire when `depends_on` is the empty list — a freshly filed epic with no declared sub-tasks is not in the same logical state as an epic whose declared sub-tasks have all closed, and the vacuous-truth case would otherwise flag every newly-filed open epic. Unresolvable `depends_on` entries (referenced ids missing from the store) MUST NOT fire `no-stalled-epic`; that drift class is the existing `no-orphan-dependency` invariant's domain and continues to surface there. When the epic's own `depends_on` array includes entries with `kind` other than `local`, the invariant MUST walk those entries via `livespec_runtime.cross_repo.resolve_ref` and treat any `open` external dependency as a legitimate stall reason (suppressing the fail). The `fail` (not `warn`) classification reflects that this is a structural contract violation rather than a productivity-grade nudge: the epic↔sub-task aggregation is a load-bearing data-model invariant, and `warn` is reserved per the existing `no-stale-gap-tied` precedent for productivity heuristics. On `fail`, the check's narration MUST direct the user to either close the epic with an appropriate `resolution` (when the work is genuinely complete) OR add fresh `depends_on` entries (when the original sub-tasks were not the complete set of blockers).

### `contract-version-compatibility`

The `contract-version-compatibility` doctor invariant reads the active impl-plugin's `compat` block from `.livespec.jsonc` (the block defined by §"Cross-repo coordination — pin-and-bump") and enforces two derivations:

1. The `livespec` semver range against the actually-installed `livespec` version (read from `livespec`'s `plugin.json.version`). When the installed version falls OUTSIDE the declared range, the check MUST fire `fail`.
2. The `pinned` tag value against the most-recent published `livespec` release tag. When the pinned tag is older than a configured drift threshold (measured in number of intermediate releases — exact threshold value deferred to a configuration key under `livespec`'s top-level `.livespec.jsonc` section, default value to be set by a follow-on refinement), the check MUST fire `warn` with narration directing the user to open a bump-pin PR.

A missing or malformed `compat` block on the active impl-plugin MUST fire `fail` — the pin-and-bump mechanism is REQUIRED, not optional. Consumers using a `livespec-impl-*` plugin without declaring `compat` are running out-of-contract.

A missing `livespec` installation MUST be detected by doctor's existing pre-step lifecycle (the `pre_check` static phase that runs before each invariant check; doctor's wrapper resolves the installed `livespec` version once and fails fast if it cannot be located), NOT by this invariant. This invariant assumes `livespec` is installed and reports the version it finds via the pre-step resolution.

### `depends_on-ref-wellformedness`

For every open work-item's `depends_on` array, the invariant enforces:

1. **Discriminator present.** Every entry MUST have a `kind` field whose value is one of `local`, `sibling_work_item`, `pull_request`, `branch`. Missing or unknown `kind` fires `fail`.
2. **Per-kind required fields present.** `local` requires `work_item_id`; `sibling_work_item` requires `repo` and `work_item_id`; `pull_request` requires `repo` and `number`; `branch` requires `repo` and `name`. Missing required fields fire `fail` with the entry's index in the array.
3. **`repo` resolves to a configured target.** For every entry with a `repo` field, the value MUST be a key in `.livespec.jsonc`'s `cross_repo_targets` block. Unresolvable `repo` values fire `fail` with the value and a hint pointing to the manifest.

This invariant is structural per the catalogue's intro principles (binary, contract-level, mechanically checkable); it does NOT rank or judge work-item readiness, only the well-formedness of the typed dependency machinery.

### `unresolved-spec-commitment`

Every accepted propose-change's declared cross-boundary obligation MUST resolve to a filed work-item. The check walks every `<spec-target>/history/vNNN/proposed_changes/<stem>.md` whose paired `<stem>-revision.md` carries `decision: accept` or `decision: modify`, reads the `<stem>.md`'s front-matter `spec_commitments.impl_followups[]` (per `spec.md` §"Proposed-change and revision file formats" → "Spec→impl commitment declaration"), and for each entry's `id_hint` queries the active impl-plugin's `list-work-items --json` thin-transport skill for a work-item carrying `spec_commitment_hint: <id_hint>`. The check fires `fail` when any entry's `id_hint` is absent from the work-items store, with narration directing the user to file the work-item via the active impl-plugin's `capture-work-item` skill.

Work-items matched against the commitment MAY be in any status (`open`, `in_progress`, `blocked`, `closed`, `deferred`, `superseded`). The invariant verifies the work-item exists; per-item closure timing is the impl-plugin's `next` ranker's concern, not doctor's. A work-item with `status: deferred` is acceptable proof that the commitment is tracked.

The check runs at every doctor static invocation, including revise's post-step doctor. When revise's post-step doctor fires `fail` on this invariant, the revise wrapper exits `3` per the existing exit-code table — revise MUST NOT cut a new `vNNN/` snapshot until the commitments resolve. The user's corrective action is to file the declared work-items via the active impl-plugin's `capture-work-item` skill, then re-invoke revise.

Propose-changes with `decision: reject` are exempt: a rejected propose-change creates no spec→impl obligation, so no `spec_commitments` entry it declares is checked. Propose-changes that omit `spec_commitments` entirely are exempt vacuously (zero-commitment payload).

Supersession: when a later propose-change accepted in a subsequent `vNNN/` carries `spec_commitments.supersedes: [<earlier-id_hint>, ...]`, the listed `id_hint`s are no longer subject to this check — the later propose-change has either absorbed the obligation or revoked it; the supersession declaration is the spec-side acknowledgement. The `supersedes` sub-field is OPTIONAL and is defined in `spec.md` §"Proposed-change and revision file formats" alongside the `impl_followups` sub-field.

Cross-repo: when the active project's `.livespec.jsonc` lacks an impl-plugin (e.g., spec-only repos that do not adopt an impl-plugin), this invariant is `skipped` rather than `fail`. The `spec_commitments` field's semantic is impl-plugin-relative; without an impl-plugin the declaration has no destination to land in. Spec-only repos relying on propose-change declarations for impl follow-ups in a separate repo SHOULD route those declarations through the consuming repo's own propose-change cycle, not this repo's `spec_commitments` field.

### `primary-checkout-commit-refuse-hook-installed`

Every livespec-governed primary checkout MUST install a `.git/hooks/pre-commit` and `.git/hooks/pre-push` hook whose body refuses to run when invoked at the primary checkout. The rule is family-wide: it applies to `livespec` itself, every `livespec-impl-*` plugin's primary checkout, `livespec-dev-tooling`'s primary checkout, `livespec-runtime`'s primary checkout, and every future sibling repo generated from the copier template per §"Shared content sync — copier template". The check reads `<project-root>/.git/hooks/pre-commit` and `<project-root>/.git/hooks/pre-push`, verifies each exists and is executable, and verifies each contains the canonical livespec commit-refuse hook body (recognized via a stable marker comment string the canonical body MUST carry). The check fires `fail` when either hook is missing, non-executable, or contains a non-canonical body (including the empty file case). The narration directs the user to invoke the repo's documented bootstrap step (per `non-functional-requirements.md` §"Commit-refuse hook bootstrap procedure"), which idempotently installs the hook.

The canonical implementation of this check ships in `livespec-dev-tooling` at `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed`. The check is layout-independent (no `[tool.livespec_dev_tooling]` role keys consumed) and so belongs to the shared inventory per §"Shared code sync — livespec-dev-tooling" → §"Shared check inventory" partition criterion: its intent and CLI surface are stable across every livespec-governed project, making a single implementation correct for the whole family. Every consumer repo MUST run the shared check in their `just check` aggregate AND CI matrix per the wiring-completeness invariant codified in §"Shared code sync — livespec-dev-tooling" (added by v094) and per the same invocation-agnostic discipline that governs every other shared check (per `non-functional-requirements.md` §"Enforcement suite" — the check ships from the shared inventory, the consumer repo decides only the recipe naming and the per-repo aggregate-list entry).

The shared check runs once per `just check`/CI invocation against the project root. Repo-local plugin-doctor catalog instances of the same check — e.g., `livespec`'s plugin-doctor static-phase entry that runs per spec tree under each `/livespec:doctor` invocation — remain valid and MAY coexist with the shared check: the two scopes/cadences are complementary (the shared check is a CI-time backstop against the project root; the plugin-doctor entry runs per-spec-tree under the wrapper-lifecycle of every `/livespec:*` sub-command). Defense-in-depth: both are retained.

The invariant is structural per the catalogue's intro principles (binary, contract-level, mechanically checkable); the canonical hook body is either installed at both paths or it isn't. The check MUST NOT distinguish between "hook missing" and "hook present but body is non-canonical" at the contract level — both fire equally; both are corrected by the same bootstrap invocation. The narration MAY name the specific failure mode for diagnostic clarity, but the structural `fail` finding is identical.

The check applies to the primary checkout's `.git/hooks/` directory only. Secondary worktrees share the `.git/` directory and therefore inherit the same hook scripts; the check does NOT need to inspect each worktree separately, and worktrees MUST NOT carry their own divergent `pre-commit` / `pre-push` hooks. Per-worktree hook overrides via the `core.hooksPath` config in a worktree are forbidden by this contract.

Fresh clones that have not yet had the bootstrap step run fail this invariant immediately. This is intentional: the failure is the mechanism by which a fresh contributor discovers the discipline. The narration includes the corrective bootstrap command verbatim so the resolution path is one terminal invocation away.

`core.bare` MUST NOT be set on the primary checkout. The v091–v094 bare-flag mechanism is superseded by this hook mechanism (see `non-functional-requirements.md` §"Primary-checkout commit-refuse hook" for the motivation: the bare-flag mechanism caused stale-on-disk-read failures at primaries that the hook mechanism does not). The doctor invariant MAY additionally surface a `fail` when `core.bare = true` is set on the primary, to catch the legacy-state case during the transition from the bare-flag mechanism to the hook mechanism.

### `master-direct-uncommitted-spec-edits`

Every worktree (primary or secondary, per `git worktree list --porcelain`) whose HEAD points at the default branch MUST NOT carry uncommitted modifications under `<spec-root>/`. The check enumerates every worktree, identifies the subset whose HEAD is the default branch (typically `master`), and for each invokes `git status --porcelain` scoped to `<spec-root>/`. Any non-empty output fires `warn` with corrective action narration that:

1. Names the offending worktree path.
2. Names the modified files under `<spec-root>/`.
3. Directs the user to commit-into-a-feature-branch (`git checkout -b <branch>` then commit) per the workflow discipline, OR to discard the edits if they were unintentional (`git checkout -- <files>`).

The check fires `warn` (not `fail`) consistent with the v079 prose at `non-functional-requirements.md:746` ("a `warn` finding"). Spec edits on master are a discipline violation, but the violating commit is not yet pushed — the warning gives the user time to recover.

The check covers the secondary-worktree-on-master bypass that the sibling `primary-checkout-commit-refuse-hook-installed` invariant cannot physically prevent (the commit-refuse hook fires only when `git rev-parse --show-toplevel` equals the primary path; secondary worktrees on master pass that comparison and proceed to commit, so a `git worktree add /path master` + edit + commit at the secondary worktree bypasses the hook). The two checks together close the enforcement loop.

Committed-and-then-discovered violations (the user committed on master and now the commit needs to be moved) are out of scope for this invariant; the existing `out-of-band-edits` check surfaces those via the snapshot-mismatch invariant.

### `copier-template-workflow-coverage`

Every consumer repository governed by livespec MUST contain a `.github/workflows/` directory whose set of workflow files is a SUPERSET of the required-file list enumerated in §"Shared content sync — copier template". The check fires `fail` for every required workflow file that is missing from the consumer's `.github/workflows/`. Each `fail` finding MUST name the specific missing file and MUST direct the user to run `copier update` to re-sync from the template.

The invariant complements `copier update --dry-run` (which catches divergence in files that DO exist in both the template and the consumer): `copier-template-workflow-coverage` catches files that exist in the template but NOT in the consumer (the "file was added to the template after the consumer was generated, and `copier update` was never run" case AND the "file was present in livespec but never made it into the template, and the consumer therefore lacks it" case). The two checks together close the workflow-coverage hole.

Workflow files in the consumer's `.github/workflows/` that are NOT in the required-list (consumer-local workflows) MUST NOT fire `fail` — they are out of scope for this invariant. Consumer-local workflows are catalogued by the consumer's own spec, not by livespec.

The invariant runs in doctor's static phase (no LLM in the path); the required-file list is read directly from `contracts.md`'s enumerated scaffold list in §"Shared content sync — copier template". Drift between the contract list and the doctor invariant's hard-coded list MUST be caught by a paired enforcement-suite check that ships in `livespec-dev-tooling` (TBD in a parallel propose-change against that sibling's spec); for v1, the doctor invariant MAY hard-code the list and rely on PR review to catch drift.

## Resolved-template stdout contract

`bin/resolve_template.py` MUST emit on success exactly one line: the resolved template directory as an absolute POSIX path, followed by `\n`. Paths containing spaces are emitted literally; callers MUST NOT pipe through shells that re-split on whitespace. The contract is frozen in v1; future template-discovery extensions MUST extend, not replace, the stdout shape and CLI flag set.

## Help-requested escape

Every wrapper MUST treat `-h` / `--help` as a `HelpRequested` signal, emit the argparse-rendered help text on stdout, and exit 0 (NOT exit 2). Per `commands/CLAUDE.md`, `HelpRequested.text` is one of two `commands/`-layer stdout-write exemptions (the other being `resolve_template`'s resolved-path emission).

## Plugin distribution

`livespec` is distributed as a Claude Code plugin via a marketplace catalog at the repo-root path `.claude-plugin/marketplace.json`. The marketplace lists the single plugin declared by `.claude-plugin/plugin.json`. The plugin and marketplace names share the value `livespec` by deliberate choice; both names are stable v1 contracts and renaming either MUST flow through a propose-change cycle.

End-user install path:

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec@livespec
```

Consumer projects MUST install `livespec` plus exactly one `livespec-impl-<X>` plugin (the active implementation choice). The active implementation MUST be declared in `.livespec.jsonc` via a top-level `implementation.plugin` key naming the active plugin. `.livespec.jsonc`'s schema root is `additionalProperties: true`; each plugin owns a top-level section named for the plugin and MUST validate its own section on read and MUST tolerate unknown sections. Secrets MUST NOT live in `.livespec.jsonc`; external-tracker implementations needing credentials MUST use a separate credentials channel (environment variables, OS keyring, secret manager).

After install, `livespec` exposes eight slash commands, namespaced under the plugin name: `/livespec:seed`, `/livespec:propose-change`, `/livespec:critique`, `/livespec:revise`, `/livespec:doctor`, `/livespec:prune-history`, `/livespec:help`, `/livespec:next`. Renaming any command requires a propose-change cycle.

The `marketplace.json` `description` field is a manual duplicate of `plugin.json`'s `description`; `plugin.json` is the source of truth. v1 does NOT enforce equality mechanically; future revise cycles MAY add a doctor static check to detect drift if it becomes operationally relevant.

Plugin uninstall and update flows are Claude Code platform behaviors and are not part of this contract.

### Daily dogfooding path

For maintainer development of the `livespec` plugin source in this repo, launch Claude Code with `--plugin-dir .` to load the plugin directly from the local source. Live edits to `.claude-plugin/skills/<name>/SKILL.md` and `.claude-plugin/scripts/...` are picked up via `/reload-plugins` without re-installing. The marketplace install path (`/plugin install livespec@livespec`) is for verifying the published install flow; it copies the plugin into `~/.claude/plugins/cache/` and does NOT live-reload.

## Cross-repo coordination — pin-and-bump

The cross-repo coordination mechanism between `livespec` and every livespec-governed sibling consumer (`livespec-impl-*` plugins AND sibling libraries such as `livespec-dev-tooling` per §"Shared code sync — livespec-dev-tooling" AND `livespec-runtime` per §"Shared runtime — livespec-runtime") is pin-and-bump: every consumer project MUST declare which `livespec` release tag the consumer is currently pinned against. The pin lives in a per-consumer `compat` block inside `.livespec.jsonc` (Obsidian-style per-consumer compatibility manifest). Each consumer's autonomous workflows run against the pinned `livespec` release, never against HEAD. When `livespec` ships a new release, a bump-pin pull request fires in each consumer project (and in each consumer's own repository — impl-plugin or sibling library — when relevant), and the migration to the new pinned version is the explicit scope of that PR.

The compat block carries two required fields: `livespec` (a semver range describing supported `livespec` versions, e.g., `>=2.0.0,<3.0.0`) and `pinned` (the specific `livespec` release tag the consumer currently runs against, e.g., `v2.3.0`). Both fields live on each consumer's top-level section in `.livespec.jsonc`, keyed by the consumer name — on the `livespec-impl-plaintext` key for impl-plugins, on the `livespec-dev-tooling` key for the enforcement-suite sibling library, on the `livespec-runtime` key for the runtime sibling library, and on whatever key names a future sibling consumer registers.

Each consumer's automation and the consumer project's autonomous workflows MUST run against the pinned `livespec` release, NOT against HEAD. Running against HEAD bypasses the audited coordination mechanism and MUST be considered an out-of-contract operation.

When `livespec` ships a new release tag, a bump-pin pull request MUST be opened automatically in every consumer per the cross-repo coordination automation surface specified in `livespec-dev-tooling`'s own `contracts.md` §"Cross-repo coordination automation surface". The bump-pin PR's acceptance criterion is that the consumer and the consumer project both continue to pass the post-bump invariant suite. The dispatch mechanism, autodiscovery rules, payload contract, auth model, and fallback procedures are all owned by `livespec-dev-tooling`'s spec; the policy this section establishes (the requirement that bumps happen and the acceptance criterion) is the consumer-facing contract `livespec` owns.

Breaking contract changes in `livespec` MUST be landed additively: the old contract surface stays valid for one or more releases; every consumer (impl-plugin or sibling library) migrates at its own cadence; only after the active consumer's release adopting the new surface ships MAY the old surface be removed in a subsequent `livespec` release. This mirrors the Kubernetes CRD multi-version-served pattern and the GCC `N` / `N-1` support window.

`.livespec.jsonc` MUST NOT carry secrets; the `compat` block contains only non-sensitive version metadata.

Example `.livespec.jsonc` excerpt (illustrative; the canonical schema lives in `livespec`'s JSON Schema fragment):

```jsonc
{
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "implementation": { "plugin": "livespec-impl-plaintext" },
  "livespec-impl-plaintext": {
    "format": "jsonl",
    "compat": {
      "livespec": ">=2.0.0,<3.0.0",
      "pinned": "v2.3.0"
    }
  }
}
```

A subsequent propose-change cycle defining doctor's expanded invariant catalog MUST include a `contract-version-compatibility` invariant that fires when `livespec` semver range OR `pinned` tag drift exceeds the configured threshold; the threshold value itself is out of scope for this proposal.

## Cross-repo dependency awareness

The mechanism is parallel-and-complementary to the cross-repo version coordination of §"Cross-repo coordination — pin-and-bump": version pin-and-bump is the coarse-grained release-level coordination; this section codifies the fine-grained per-work-item coordination for cases when an in-flight work-item depends on specific state in another repo. The two operate at different granularities and are independent.

v1 supports GitHub-hosted repos exclusively. GitLab and other forges are deferred to a future propose-change cycle; the `providers` package shape in `livespec_runtime.cross_repo` is structured so adding a `providers.gitlab` module is a non-breaking extension.

### `cross_repo_targets` manifest in `.livespec.jsonc`

Projects participating in cross-repo work-item dependency coordination MUST declare a top-level `cross_repo_targets` block in `.livespec.jsonc`. The block is an object whose keys are short repo slugs (used as the `repo` field in every typed `depends_on` entry) and whose values are objects with the following fields:

- `github_url` — string, REQUIRED. The canonical `https://github.com/<owner>/<name>` URL (no trailing `.git`). Doctor's `cross-repo-targets-wellformedness` invariant MUST verify it parses as a GitHub URL.
- `local_clone` — string, OPTIONAL. Filesystem path to the consumer's local clone of the target repo. MAY be absolute or relative to the containing project's root. When set, the runtime walks the local clone for branch and worktree state. When absent (CI case), the runtime silently drops the local-clone view and falls back to GitHub-only queries. The path is NOT required to exist at config-load time; missing-path is a runtime-degraded-view condition, not a precondition failure.
- `default_branch` — string, OPTIONAL, default `"master"`. The repo's default branch name used by the runtime for "branch merged into default" derivations. Projects whose default branch is not `master` MUST set this explicitly.

The `cross_repo_targets` block is OPTIONAL at the top level — projects with no cross-repo work-item dependencies omit it entirely.

The `cross_repo_targets` block MUST NOT be conflated with the per-consumer `compat` block defined in §"Cross-repo coordination — pin-and-bump", which handles version pin-and-bump.

### Typed `DependsOnEntry` union for the work-item `depends_on` field

The impl-plugin contract's work-item record schema (per §"Implementation-plugin contract — the 10-skill surface") gains a typed object shape for entries in the existing `depends_on` array, replacing the prior string-only `<work-item-id>` shape. Each entry MUST be one of the four typed variants below, discriminated on the `kind` field:

- `kind: "local"` — a same-repo work-item dependency. Carries `work_item_id` (string, e.g. `"li-abc123"`). The runtime resolves this against the active impl-plugin's local work-items store; no cross-repo walk.
- `kind: "sibling_work_item"` — a work-item in a configured sibling repo. Carries `repo` (string, MUST match a key in `.livespec.jsonc`'s `cross_repo_targets` block) and `work_item_id` (string). Resolved via the sibling repo's `local_clone/<impl-plugin>.work_items_path` if available, falling back to dropping the dependency view if neither local nor GitHub-queryable.
- `kind: "pull_request"` — a specific GitHub pull request. Carries `repo` (string, MUST match `cross_repo_targets`) and `number` (positive integer). Resolved via `gh pr view <number> --repo <github_url>`.
- `kind: "branch"` — a specific GitHub branch. Carries `repo` (string, MUST match `cross_repo_targets`) and `name` (string, the branch name without the `refs/heads/` prefix). Resolved via the exhaustive walk's branch-tip query.

A `depends_on` entry's `kind` field is REQUIRED non-null. The previous string-only shape (`"li-abc123"`) is NOT a valid v1 entry; the impl-side data-migration step MUST convert every prior string entry to `{"kind": "local", "work_item_id": "li-abc123"}` form before this contract takes effect.

The `blocked_by` field is REMOVED from the work-item record schema. Its prior role — "this work-item is currently blocked by N other work-items / PRs / branches" — folds into the typed `depends_on` union; the runtime's open/closed derivation per entry is what the consumer's ranker, doctor invariants, and hooks consult. The alternative of keeping `blocked_by` as a parallel field was rejected because it would have required two stores of truth that could drift.

### Exhaustive live-walk resolution semantics

The runtime's `resolve_ref(entry, manifest)` function MUST return a `RefStatus` (`open` | `closed` | `unknown`) for every `DependsOnEntry`, computed from an exhaustive query of every extant view the runtime can access:

- For `kind: "local"` — read the local work-items store via the active impl-plugin's list-work-items interface; return `closed` iff the materialized status is `closed`, else `open`.
- For `kind: "sibling_work_item"` — when `local_clone` is configured AND the path exists AND the path contains a parseable `.livespec.jsonc` with an impl-plugin config, walk the sibling's work-items store. Otherwise fall back to GitHub-queried state when the impl-plugin surface exposes a remote-queryable form (impl-plugin-dependent; the runtime calls into the impl-plugin's surface when present, returns `unknown` when not). The runtime MUST NOT cache; each call walks fresh state.
- For `kind: "pull_request"` — query `gh pr view <number> --repo <github_url> --json state`. Return `closed` iff `state == "MERGED"` OR `state == "CLOSED"` (the work-item depending on the PR is unblocked when the PR is resolved either way; the consumer ranker decides whether closed-but-unmerged warrants a different urgency). Return `open` for any other state. Return `unknown` if the GitHub query exits non-zero after retry exhaustion.
- For `kind: "branch"` — walk in this order until a derivation succeeds: (a) when `local_clone` is configured, query `git -C <local_clone> rev-parse refs/heads/<name>` to determine if the branch exists locally and has merged into `default_branch`; (b) query `gh api repos/<owner>/<name>/branches/<name>` for the remote branch tip + `gh api repos/<owner>/<name>/compare/<default_branch>...<name>` for the merged-into-default determination. Return `closed` iff the branch's tip is reachable from `default_branch` (i.e., merged) OR the branch is absent on the remote AND was previously seen merged in a local fetch. Return `open` otherwise; `unknown` on retry exhaustion.

The runtime MUST include the CURRENT repo's uncommitted state when relevant (e.g., for `kind: "local"` against the current repo, the materialized view is the latest JSONL line, including the just-appended one if the consumer is mid-revise).

Missing local clones, missing remote branches, and `gh` CLI auth failures are NOT precondition errors — they degrade the view (the runtime returns `unknown` for that entry and the consumer surfaces the degradation). The exhaustive-walk discipline tolerates partial visibility.

### `livespec_runtime.cross_repo` contract surface

The `livespec_runtime.cross_repo` subpackage's public API is the contract surface for this section. The subpackage exports:

- `DependsOnEntry` union types — one dataclass per `kind` value (`local`, `sibling_work_item`, `pull_request`, `branch`) per the typed-union shape defined above.
- `CrossRepoManifest` dataclass — the in-memory representation of the `.livespec.jsonc` `cross_repo_targets` block.
- `RefStatus` enum — `open` | `closed` | `unknown`.
- `resolve_ref(entry: DependsOnEntry, manifest: CrossRepoManifest) -> RefStatus` — the exhaustive-live-walk resolver entry point.

Module structure: `livespec_runtime.cross_repo.{types, providers.github, retry, resolve_ref}`. Breaking changes to these exported names or shapes require a MAJOR version bump per the semver discipline codified in §"Shared runtime — livespec-runtime".

Library-level concerns (governance, dependency consumption shape, network-I/O policy, Python floor, semver discipline) are codified in §"Shared runtime — livespec-runtime" and are NOT restated here.

### Retry policy

The `livespec_runtime.cross_repo` retry policy is fixed at three attempts with 1s / 2s / 4s exponential backoff between attempts. On every-attempt failure (including subprocess timeouts on `gh` CLI calls), the runtime returns `RefStatus.unknown` rather than raising; the consumer is responsible for surfacing degraded-view findings.

The retry policy is NOT user-configurable in v1. Projects with bandwidth-constrained CI environments MAY pre-fetch sibling repos to local clones to avoid the GitHub-query path entirely.

### Consumer surface (livespec core + impl-plugins)

The runtime is consumed by:

- The spec-side `/livespec:doctor` invariants (per the doctor catalogue extensions in §"Doctor cross-boundary invariants").
- The impl-side `<impl-plugin>:next` ranker — which MUST exclude any work-item with at least one open `DependsOnEntry` from the candidate list. Excluded candidates do NOT appear in the ranked list (they are not surfaced with lower urgency; they are absent entirely).
- Project-local hooks and CI workflows that need to gate behavior on cross-repo state (e.g., a pre-merge hook that refuses to merge a PR whose underlying work-item still has open external dependencies).

Consumer projects MUST declare `livespec-runtime` as a dependency in `pyproject.toml` via `[tool.uv.sources]` pinning the target tag, identical to how they consume `livespec-dev-tooling`.

### GitHub CLI authentication

The runtime invokes the `gh` CLI for all GitHub queries. The CLI MUST be installed and authenticated (`gh auth status` returning success) in any environment where the runtime is consumed.

In CI environments, the standard pattern is `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` (for read-only queries) or an App installation token (for queries against private sibling repos or higher rate-limit needs). The runtime does NOT manage auth; it surfaces auth-failure findings via `RefStatus.unknown` and lets the consumer decide how to handle.

### Hook integration

Project-local hooks (lefthook pre-push, pre-merge, etc.) MAY invoke `python -m livespec_runtime.cross_repo.resolve --work-item-id <id> --manifest <path>` to gate hook behavior on the work-item's external-dependency state. The CLI emits a JSON status object suitable for shell-level dispatch. This CLI is the same surface the impl-plugin `next` ranker invokes internally; no parallel CLI is required.

## Implementation-plugin contract — the 10-skill surface

Every `livespec-impl-*` plugin MUST expose these ten skills under its own namespace prefix (`/livespec-impl-<X>:<skill>`). Six are heavyweight authored skills (dialogue, judgment calls); four are thin-transport skills (CLI pass-through per §"Thin-transport skill doctrine"). Consumer projects, doctor's cross-boundary invariants, and the project-local orchestration layer all consume the surface uniformly via skills.

### Heavyweight authored skills (6)

- **`capture-impl-gaps`** — file gap-tied work items into the plugin's Work Items store with per-gap user consent. The detection step MUST consume the plugin's `detect-impl-gaps --json` thin-transport sibling (no in-skill duplication of the detection logic); the filing step is the interactive, judgment-bearing workflow that `capture-impl-gaps` owns. Collapses the prior `refresh-gaps` + `plan` skill pair into one ephemeral-detection skill. Detection state is in-memory and discarded at skill exit; no persistent intermediate artifact.
- **`capture-spec-drift`** — detect impl → spec drift heuristically (LLM-driven); per finding, with user consent, route to `/livespec:propose-change` via the cross-boundary handoff. Asymmetric counterpart to `capture-impl-gaps`: mechanical detection is on the spec → impl side; heuristic detection is on the impl → spec side.
- **`capture-work-item`** — freeform direct filing of an impl-side work item (bugs, refactors, tactical tasks). The resulting work item carries NO `gap-id` label and closes via the freeform fix path. Work-items carry a typed `depends_on` array per §"Cross-repo dependency awareness"; the prior string-only `<work-item-id>` shape and the parallel `blocked_by` field are NOT v1 valid forms. The impl-plugin's data-migration step MUST convert prior records before this contract takes effect.
- **`implement`** — drive Red → Green for a single work item. For gap-tied items, verify closure by invoking `detect-impl-gaps --json` and confirming the `gap-id` is no longer present in the returned set; for freeform items, close with a simple `--reason`. Closure branches on origin × disposition: gap-tied fix (verify + audit fields), freeform fix (simple reason), non-fix (administrative — `wontfix`, `duplicate`, `spec-revised`, `no-longer-applicable`, `resolved-out-of-band`).
- **`capture-memo`** — low-friction free-text deposit of an in-flight observation that the user is not yet ready to classify. Memos are transient by construction.
- **`process-memos`** — per-memo handholding dialogue with four dispositions: spec-bound (→ `/livespec:propose-change` cross-boundary handoff), impl-bound (→ freeform work item in the plugin's Work Items store), persistent-knowledge (→ Persistent Agent Knowledge store; the form is implementation-dependent), discard.

### Thin-transport skills (4) — required machine query surface

- **`list-memos`** — required (promoted from discretionary). Supports `--filter` flags (most notably `--filter=untriaged`) and `--json` output. Consumed by doctor's memo-hygiene invariant and by users for queue inspection.
- **`list-work-items`** — required (new). Supports filter flags (`--gap-tied`, `--blocked`, `--with-gap-id`, etc.) and `--json` output. Consumed by doctor's five work-item structural invariants (defined by a subsequent propose-change cycle), by the project-local loop driver for routing decisions, and by users for queue inspection. Work-items carry a typed `depends_on` array per §"Cross-repo dependency awareness"; the prior string-only `<work-item-id>` shape and the parallel `blocked_by` field are NOT v1 valid forms. The impl-plugin's data-migration step MUST convert prior records before this contract takes effect.
- **`next`** — required (new). Ranks the most ripe impl-side action using whatever native primitives the backend provides (e.g., `bd ready` for a beads-backed impl, JSONL traversal for a plaintext impl, GitLab API for a gitlab impl). Pure function of impl-side state; no LLM in the ranking path. Asymmetric counterpart to `/livespec:next`. The ranker MUST consult `livespec_runtime.cross_repo.resolve_ref` for every candidate work-item's `depends_on` entries and MUST exclude any candidate with at least one entry resolving to `open`. Excluded candidates do NOT appear in the ranked list (they are not surfaced with a lower urgency; they are absent entirely). MUST accept the same `--limit <count>` (default `5`) and `--offset <count>` (default `0`) flags as the spec-side `next` skill, with the same validation rules and exit-2-on-bad-flags behavior. MUST emit a JSON object of the same shape as the spec-side `next` skill's output (per §"`/livespec:next` spec-side thin-transport skill" → "Output schema"): top-level `candidates[]` and `pagination` keys. Each candidate object MUST carry at minimum `action`, `reason`, `urgency`, AND the impl-side-specific `work_item_ref` field. The candidate object MAY include additional impl-side-specific fields (e.g., `blocked_by`, `epic`) provided they are documented by the impl-plugin's own per-implementation contract. The cross-plugin contract MUST NOT prescribe `additionalProperties` discipline on the candidate object: impl-plugin authors own their per-implementation schema, and the cross-plugin contract surface MUST remain agnostic to per-implementation field additions. The wrapper at `<impl-plugin>'s` `.claude-plugin/scripts/bin/next.py` MUST remain a pure thin-transport pass-through. The Layer 3 discoverability nudge discipline (per §"`/livespec:next` spec-side thin-transport skill" → §"Layer 3 discoverability nudge") does NOT apply to impl-plugin `next` skills under the recast architecture, because impl-plugin repos do NOT carry their own Layer 3 driver and a nudge from an impl-plugin's `next` would have no in-repo Layer 3 surface to point at.
- **`detect-impl-gaps`** — required (new). Reads the live Specification via the Spec Reader and emits the current set of spec → impl gap-ids as JSON. Pure function of spec state and the gap-rule enumeration; no LLM in the detection path; no mutation of any impl-side store. The skill is the canonical gap-detection surface — both doctor (for `gap-tracking-one-to-one` and `no-stale-gap-tied` invariants) and the heavyweight `capture-impl-gaps` sibling consume the same surface uniformly. Wrapper CLI surface: `detect-impl-gaps [--spec-target <path>] [--project-root <path>] [--json]`. The `--json` output shape is a top-level object `{"gap_ids": ["<gap-id>", ...]}`; default human output is a one-line-per-gap summary. The skill MUST exclude `<spec-root>/proposed_changes/` content from detection (the Spec Reader already enforces this exclusion at its boundary; the skill MUST NOT bypass it).

### Cross-boundary handoffs (red edges in the workflow diagrams)

1. `<impl-plugin>:capture-spec-drift` → `/livespec:propose-change` (drift findings).
2. `<impl-plugin>:process-memos` → `/livespec:propose-change` (spec-bound memo disposition).
3. `/livespec:doctor` → `<impl-plugin>:list-memos --filter=untriaged --json` (memo-hygiene invariant).
4. `/livespec:doctor` → `<impl-plugin>:list-work-items --json` (work-item structural invariants).
5. `/livespec:doctor` → `<impl-plugin>:detect-impl-gaps --json` (gap-detection invariants `gap-tracking-one-to-one` and `no-stale-gap-tied`).
6. livespec's Layer 3 loop driver invokes both `/livespec:next` and `<impl-plugin>:next` to compose cross-side recommendations across the livespec family of repos.

### Impl-side cleanup invariants (cross-boundary)

The active impl-plugin MUST realize three impl-side cleanup invariants that surface stale local-Git or local-worktree state. Each fires `warn` (not `fail`) because the underlying state is recoverable by user action; the invariants' role is to surface the housekeeping items to the user, not to block the build.

- **`no-stale-merged-branch`** — for every local branch whose tip is reachable from the default branch (i.e., merged), the invariant fires `warn` with corrective action `git branch -d <name>`. Excludes the default branch itself. Excludes any branch the user has explicitly tagged via project-local config to skip.
- **`no-stale-merged-pr-branch`** — for every GitHub branch in `gh api repos/<owner>/<name>/branches` that is fronted by a `state == "MERGED"` PR (queried via `gh pr list --state merged --json headRefName,state`), the invariant fires `warn` with corrective action `gh api -X DELETE repos/<owner>/<name>/git/refs/heads/<name>`. The check runs against the CURRENT repo only; sibling-repo cleanup is the sibling-repo project's responsibility.
- **`no-stale-worktree`** — for every git worktree (per `git worktree list --porcelain`) whose underlying branch is either (a) merged into default and locally deleted, or (b) absent from the remote, the invariant fires `warn` with corrective action `git worktree remove <path>`. Excludes the primary worktree.

The three invariants MAY be implemented entirely within the impl-plugin's doctor-realization surface (extending the `<impl-plugin>:list-work-items` consumers' invariant set), OR may dispatch to a `livespec_runtime` helper module if a future version provides one — the choice is the impl-plugin author's. The contract is the invariant set and its narration shape; the implementation seam is implementation-dependent.

### Backend-variability asymmetry

The impl-side query skills exist because impl backends are pluggable (plaintext / beads / gitlab / ...) and cross-side consumers (doctor, the loop driver, core's `next`) need a uniform abstraction across those variants. The spec side has the opposite property: the spec backend is fixed (the canonical `SPECIFICATION/` tree shape). Doctor's static phase already reads `<spec-root>/proposed_changes/` and `<spec-root>/history/` directly from the filesystem — no abstraction needed. Symmetric `list-proposed-changes` / `list-history` skills would be pure ceremony. This is the principled reason the spec-side surface grows only by `next`, while the impl-side surface grows by three.

### Work-item `spec_commitment_hint` field

Every impl-plugin's work-item record schema MUST carry an OPTIONAL `spec_commitment_hint: string | null` field. The field is populated by the `capture-work-item` skill when the work-item is filed in response to a propose-change's `spec_commitments.impl_followups[].id_hint` declaration (per `spec.md` §"Proposed-change and revision file formats"); its value MUST equal the originating `id_hint` verbatim. The field is `null` for freeform work-items not tied to any propose-change commitment.

The field is the impl-plugin-side surface the `unresolved-spec-commitment` doctor invariant queries to verify each declared spec→impl commitment maps to a filed work-item. Impl-plugins MUST surface the field in their `list-work-items --json` output so doctor's invariant can match without invoking implementation-private machinery.

The `capture-work-item` skill MUST accept an optional `--spec-commitment-hint <id_hint>` CLI flag (or the equivalent in backends that use a different invocation surface) that populates the field on write. When the user invokes `capture-work-item` without the flag, the resulting work-item carries `spec_commitment_hint: null` (the freeform case). When the user invokes it WITH the flag, the resulting work-item is paired against the named commitment for the duration of its lifetime.

Renaming or removing this field on any future impl-plugin schema evolution is a major-version bump of the impl-plugin's contract pin (per §"Cross-repo coordination — pin-and-bump"). The field's presence + value semantics are part of the load-bearing 10-skill surface.

### Persistent Agent Knowledge realization

Per `spec.md` §"Terminology" → **Persistent Agent Knowledge**, every `livespec-impl-*` plugin MUST realize a Persistent Agent Knowledge store and route the `process-memos` persistent-knowledge disposition into it.

- Each `livespec-impl-*` plugin MUST realize a **Persistent Agent Knowledge** store per the spec terminology. The plugin's own `SPECIFICATION/` MUST document the realization (harness instruction files, long-lived memory store, or other).
- The `process-memos` skill's persistent-knowledge disposition MUST route into this store; the routing mechanism is implementation-dependent but the disposition MUST NOT silently drop the memo content.
- Persistent Agent Knowledge content is NOT subject to doctor's memo-hygiene invariant (it is a store, not a queue/archive; the transient rule applies to memos in their pre-disposition state, not to dispositioned content that has graduated to the persistent store).
- The store MUST be readable by the agent at relevant points (skill invocation, dialogue context resolution, etc.); the loading mechanism (harness-loaded files, on-demand query, embedding-based retrieval) is per-plugin.

## `/livespec:next` spec-side thin-transport skill

`/livespec:next` is a thin-transport skill per §"Thin-transport skill doctrine". The backing Python wrapper lives at `.claude-plugin/scripts/bin/next.py` following the wrapper-shape contract codified in §"Wrapper CLI surface". The SKILL.md MUST be a pass-through.

The skill MUST read spec-side state — the Proposed Changes queue under `<spec-root>/proposed_changes/`, the Specification History under `<spec-root>/history/`, and any cached unresolved doctor findings — and emit structured JSON.

### Wrapper CLI flags

In addition to `--spec-target <path>` and `--project-root <path>` per §"Wrapper CLI surface", the `next` wrapper MUST accept:

- `--limit <count>` — positive integer, default `5`. Maximum number of candidates returned in the `candidates` array.
- `--offset <count>` — non-negative integer, default `0`. Number of ranked candidates to skip from the front of the ranked list before returning.

Non-positive `--limit` or negative `--offset` MUST cause the wrapper to exit `2` with a `UsageError`.

### Output schema

The output is a JSON object with two top-level keys:

```jsonc
{
  "candidates": [
    {
      "action": "revise",
      "reason": "<human-readable narration>",
      "urgency": "high",
      "target": "proposed_changes/foo.md"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 5,
    "total": 12,
    "has_more": true
  }
}
```

Field semantics:

- `candidates[]` — array of candidate objects. Each candidate MUST carry `action` (one of `revise`, `propose-change`, `critique`, `prune-history`, `none`), `reason` (non-empty human-readable narration), and `urgency` (one of `high`, `medium`, `low`). Each candidate MAY include `target` — a spec-target-relative path or identifier naming the specific item the candidate refers to (e.g., the proposed_change filename for a `revise` candidate, a specific history version for a `prune-history` candidate). `target` MAY be omitted when the candidate has no specific target (e.g., `action: "none"`).
- `pagination.offset` — echoed from `--offset`.
- `pagination.limit` — echoed from `--limit`.
- `pagination.total` — total count of ripe candidates BEFORE `offset` and `limit` are applied.
- `pagination.has_more` — `true` iff `offset + len(candidates) < total`.

When `offset >= total`, the wrapper MUST emit `candidates: []` and `has_more: false`. The wrapper MUST always emit a valid (possibly empty) `candidates` array; an empty array IS the no-work signal — it does NOT degrade to any legacy single-output shape.

### Ranker semantics

The ranker MUST enumerate ALL ripe candidates across the active spec target (not just the top one). It MUST sort within each action tier by urgency descending, then by a deterministic secondary key (e.g., `target` lexicographic). Finally, it MUST apply `offset` and `limit` to produce the returned slice.

The ranker MUST NOT emit `revise` candidates whose pre-step doctor would `fail` on the `unresolved-spec-commitment` invariant. A propose-change with unresolved cross-boundary commitments is not yet ripe for revise — the user MUST file the declared work-items via the active impl-plugin first. The ranker surfaces this as a `capture-work-item` candidate (action: the impl-plugin's `capture-work-item` skill, not a livespec-side action), with narration naming the unresolved `id_hint`s and the originating propose-change topic.

### `prune-history` ordering invariant

The `next` ranker MUST rank `prune-history` strictly below every other action in the `action` enumeration. When ANY ripe candidate exists with `action != prune-history` (i.e., `revise`, `propose-change`, or `critique`), the ranker MUST NOT emit `prune-history` as the primary recommendation. The `urgency: "low"` label on `prune-history` is a soft signal; this ordering invariant is a hard constraint independent of urgency.

### `.livespec.jsonc` configuration

The `next` wrapper MUST read a `next.prune_history_threshold` key from `.livespec.jsonc` on each invocation. The key value MUST be a positive integer; a non-positive value MUST cause the wrapper to exit `3` with a `PreconditionError` naming the offending key and value. When the key is absent, the wrapper MUST fall back to a default value of `20`. Projects MAY raise the threshold to defer prune-history recommendations on long-lived specs; projects MAY lower it to surface pruning sooner.

### Layer 3 discoverability nudge

The `/livespec:next` SKILL.md prose MUST surface a one-time discoverability nudge before invoking the wrapper on direct user invocation. The nudge MUST:

1. Inform the user that `.claude/skills/livespec-orchestrate/SKILL.md` (the project-local Layer 3 loop driver per `spec.md` §"Three-layer orchestration architecture" → "Layer 3 — Project-local composition") is the cohesive cross-side composition surface that combines `/livespec:next` with the active impl-plugin's `next`.
2. Ask the user to confirm they want to run `/livespec:next` directly rather than via the project's Layer 3 driver.
3. Skip the nudge when `/livespec:next` is invoked by another skill (e.g., the Layer 3 driver itself, the `doctor` cross-boundary surface) rather than by a direct user request. The skill MAY detect the calling context via the standard SKILL.md invocation-context conventions; the detection mechanism is per-harness and out of scope here.

The nudge lives entirely in SKILL.md prose. The wrapper at `.claude-plugin/scripts/bin/next.py` MUST NOT accrete a confirmation dialogue, an opt-in flag, or any other interactive layer — the wrapper remains a pure thin-transport pass-through per §"Thin-transport skill doctrine". The nudge is informational: it points the user at the Layer 3 surface but never selects the cross-side weighting itself, preserving the §"Cross-side composition exclusion" invariant.

### Cross-side composition exclusion

The skill MUST NOT read impl-side stores; cross-side ranking composition (combining `/livespec:next` and `<impl-plugin>:next`) is the responsibility of the project-local orchestration layer, NOT of `livespec`. The skill MUST NOT mutate any spec-side state — it is purely advisory.

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

Skills that consume the Spec Reader include `detect-impl-gaps` (gap-rule enumeration; also uses the version query to detect what has changed since the impl's last-checked marker, an impl-internal state), `capture-spec-drift` (comparison baseline), `implement` (work-item context resolution), and `process-memos` (spec-vs-impl disposition decisions). Other impl-side operations MAY consume it as needed.

The Spec Reader is NOT a Claude Code skill (no slash command, no namespace surface); it is an internal API within each `livespec-impl-*` plugin. This distinguishes it from the ten cross-boundary contract skills defined in §"Implementation-plugin contract — the 10-skill surface".

## Shared content sync — copier template

The shared-content sync mechanism between `livespec` and its sibling `livespec-impl-*` repos is `copier`: `livespec/templates/impl-plugin/` is the canonical scaffold for shared non-functional content (justfile, lefthook, mise, ruff/pyright, GitHub Actions workflows). Every `livespec-impl-*` repo MUST be generated from this template via `copier copy` and re-synced via `copier update`; each MUST carry a `.copier-answers.yml` tracking the template version it was last generated from. CI in each impl repo SHOULD run `copier update --dry-run` to surface drift.

`livespec` MUST publish a copier template at `templates/impl-plugin/` (project-root-relative) containing the canonical scaffolding every `livespec-impl-*` repo derives from: `justfile`, `lefthook.yml`, `.mise.toml`, `pyproject.toml` (with the ruff/pyright config), `.claude-plugin/marketplace.json` and `plugin.json` skeletons, a starter `SPECIFICATION/` skeleton, and the following `.github/workflows/` files:

- `ci.yml` — the per-repo CI pipeline (matrix of static-phase checks; `pull_request` + `push` + `merge_group` triggers).
- `copier-update-drift.yml` — the periodic `copier update --dry-run` drift detector that surfaces template divergence.
- `auto-enable-merge.yml` — auto-enables REBASE auto-merge on PR open. Required so that propose-change PRs in every impl-plugin repo merge with the same cadence as upstream `livespec` PRs (incident 2026-05-26: `livespec-impl-plaintext` PR #26 sat OPEN/CLEAN for 10+ minutes because this file was absent).
- `auto-update-branches.yml` — auto-updates open-PR branches against `master` when the base advances. Paired with `auto-enable-merge.yml`; together they make merging a hands-free operation for green PRs.
- `bump-pin-from-dispatch.yml` — accepts the bump-pin dispatch payload from `livespec`'s release flow per `livespec-dev-tooling`'s cross-repo coordination automation surface.
- `pin-freshness.yml` — the periodic check that the pin tag in `.livespec.jsonc` is not older than the drift threshold per the `contract-version-compatibility` doctor invariant.
- `release-dispatch.yml` — accepts the release-dispatch payload from `livespec`'s release flow.

The list is EXHAUSTIVE for the impl-plugin scaffold: any workflow file added to `templates/impl-plugin/.github/workflows/` requires a contract-clause amendment (this section) and a corresponding update to the `copier-template-workflow-coverage` doctor invariant (codified in §"Doctor cross-boundary invariants"). Livespec-private workflow files (e.g., `release-tag.yml` for livespec's own marketplace release flow, `e2e-real.yml` for livespec-private smoke tests) MUST NOT be added to the template and MUST NOT appear in the required-list.

Each enumerated file MAY be a Jinja-templated thin pass-through that delegates to a reusable workflow at `thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z` (per §"Shared code sync — livespec-dev-tooling") — the reusable-workflow consumption pattern is the canonical sharing mechanism for any workflow whose implementation is uniform across livespec-governed repos. The contract-level requirement is that the file EXISTS in each impl-plugin's `.github/workflows/`; whether the file's body inlines logic or `uses:` a reusable workflow is the template author's choice.

Every `livespec-impl-*` repository MUST be generated from this template via `copier copy gh:thewoolleyman/livespec/templates/impl-plugin <target> --vcs-ref=<core-release-tag>` and MUST carry a `.copier-answers.yml` at the repo root tracking the template version it was last generated from.

When `livespec`'s `templates/impl-plugin/` changes, each impl repo SHOULD run `copier update` to re-sync; the 3-way merge preserves local divergence where possible and surfaces conflicts as merge markers. Each impl repo's CI SHOULD run `copier update --dry-run` and fail or warn on detected drift.

Secrets MUST NOT be templated through `copier`; secret material lives only in environment variables, OS keyring, or a secret manager.

## Shared code sync — livespec-dev-tooling

The shared-code sync mechanism between `livespec` and every livespec-governed consumer is `livespec-dev-tooling`: a versioned Python package plus a set of GitHub composite Actions and reusable workflows, both published from `github.com/thewoolleyman/livespec-dev-tooling`. The mechanism is sibling-and-complementary to `copier` (which remains the shared-SCAFFOLD mechanism per §"Shared content sync — copier template"); `copier` MUST NOT deliver executable Python or shell code, and `livespec-dev-tooling` MUST NOT deliver static scaffolds. The two channels partition livespec's shared content along the static-vs-executable axis.

`livespec-dev-tooling` MUST be governed by livespec via its own seeded `SPECIFICATION/` tree (the `livespec` 4-file template plus `non-functional-requirements.md`) and MUST track its own work via the active `livespec-impl-*` plugin per `.livespec.jsonc`. The sibling library MUST declare a `compat` block pinning its `livespec` semver range and its currently-pinned `livespec` release tag, on a `livespec-dev-tooling` top-level key in its own `.livespec.jsonc`, structurally identical to how every `livespec-impl-*` consumer declares its block per §"Cross-repo coordination — pin-and-bump".

Consumers MUST consume `livespec-dev-tooling` via two parallel surfaces:

- **Python package.** Added to `pyproject.toml` `[dependency-groups].dev` via `[tool.uv.sources]` declaring a `git = "https://github.com/thewoolleyman/livespec-dev-tooling.git"` plus `tag = "vX.Y.Z"`. Invocation MUST take the form `uv run python -m livespec_dev_tooling.checks.<slug>`. PyPI publishing is NOT required in v1; the uv git-source path is sufficient for tag-pinned reproducible builds.
- **Composite Actions and reusable workflows.** Invoked via `uses: thewoolleyman/livespec-dev-tooling/.github/actions/<name>@vX.Y.Z` and `uses: thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z` from each consumer's `.github/workflows/ci.yml`.

Enforcement-suite checks that ship in `livespec-dev-tooling` MUST be those whose intent and CLI surface are stable across every livespec-governed project (e.g., style gates, coverage-pairing gates, AST gates, CI-alignment gates, red-green-replay gates). Checks whose intent is specific to `livespec` itself (e.g., checks asserting properties of the `templates/impl-plugin/` scaffold, checks asserting schema/dataclass pairing in `livespec`'s own package layout) MUST remain `livespec`-private and MUST NOT migrate. The canonical partition list MUST live in `livespec-dev-tooling`'s own `contracts.md` and is established by a subsequent propose-change cycle against that spec.

**Wiring-completeness invariant.** Every check in `livespec-dev-tooling`'s canonical set MUST appear in every consumer's `just check` aggregate, in alphabetical order. Consumer-private checks MAY appear after the canonical set. The canonical set is dynamically derived from `livespec_dev_tooling/checks/*.py` (excluding `_*`-prefixed helper modules and `__init__.py`) by the `livespec_dev_tooling.canonical_checks` module, which is the single source of truth for the canonical slug list. Manual lists of "the canonical checks" elsewhere in any consumer (e.g., hand-maintained justfile arrays, READMEs, CI matrix snippets) MUST be replaced by mechanical derivation from `livespec_dev_tooling.canonical_checks` or by a check that compares the manual list to the canonical list and fails on drift.

The invariant is enforced via three layers, designed as defense-in-depth so that no single layer's failure leaves the discipline unenforced:

1. **In-repo gate.** Every consumer MUST wire `check-aggregate-completeness` — the `livespec-dev-tooling` check (shipped at `livespec_dev_tooling.checks.aggregate_completeness`) that compares the consumer's own `just check` aggregate body against the canonical set and fails on any missing canonical slug or any non-alphabetical ordering within the canonical-set range. The gate is self-bootstrapping: `check-aggregate-completeness` is itself one of the canonical checks, so a consumer that drops it from its aggregate fails the invariant on the next `just check` run (because the canonical slug is now missing) and on every subsequent run until the gate is re-wired.

2. **Template gate.** `livespec/templates/impl-plugin/justfile.jinja` MUST stamp the full canonical aggregate at `copier copy` time so every newly-generated `livespec-impl-*` sibling inherits the wiring-completeness state from inception. The template MUST derive the stamped list from `livespec_dev_tooling.canonical_checks` at copy time (via a copier `_jinja_extension` or equivalent), NOT from a hand-maintained list in the template, so that template-generated repos pick up canonical-set growth automatically as new checks land in `livespec-dev-tooling`. For existing siblings, `copier update`'s 3-way merge surfaces canonical-set drift as merge conflicts in the regenerated `justfile`, giving an additional human-review checkpoint on top of the in-repo gate.

3. **Cross-repo backstop.** A doctor invariant `wiring-completeness-cross-repo` (see §"Doctor cross-boundary invariants") MUST walk every registered sibling repo (per the `livespec-dev-tooling` and `livespec-runtime` and `livespec-impl-*` registries declared in this contracts.md), read its `justfile`'s `check` recipe, compute the canonical-set difference, and fire `fail` on any aggregate lacking any canonical slug. The check MAY use a sibling's `local_clone` path when configured or fall back to a GitHub query against the sibling's default-branch `justfile`. The invariant covers the adversarial-drift case in which a consumer drops both a canonical slug AND `check-aggregate-completeness` from its aggregate in the same change — the in-repo gate cannot catch that combination (the gate is gone before it next runs), but the cross-repo doctor backstop can.

The canonical-checks Python module (`livespec_dev_tooling.canonical_checks`) lands in `livespec-dev-tooling` per the work-item `li-canon` (epic li-univck Phase 1.2). The `aggregate_completeness` check that powers the in-repo gate lands per the work-item `li-aggchk` (epic li-univck Phase 1.3). The template stamp and the cross-repo doctor invariant land in subsequent phases of the same epic.

Consumer-private checks (checks whose intent is specific to a single consumer per the partition rule above) MAY appear in a consumer's `just check` aggregate after the canonical set, in any order convenient to the consumer. The wiring-completeness invariant applies only to the canonical-set range; consumer-private extensions are unconstrained by it.

`livespec-dev-tooling` MUST declare a semver-stable surface covering its check invocation set, composite Action contracts, reusable workflow contracts, and any additional cross-repo coordination surface elements it ships. The canonical surface enumeration (the specific list of covered elements, the MAJOR/MINOR/PATCH bump rules, and the Conventional Commits → semver mapping) MUST live in `livespec-dev-tooling`'s own `contracts.md` §"Semver discipline" — the principle (semver-stable surface, no breaking changes outside MAJOR bumps) is `livespec`'s policy; the specific surface enumeration is the sibling's implementation contract.

`livespec-dev-tooling` MUST NOT perform network I/O from any check; MUST target Python 3.10+ exclusively (matching `livespec`'s floor per `non-functional-requirements.md` §"Toolchain pins"); MUST NOT take a runtime dependency on `livespec` itself (the library is consumed by `livespec`, not the other way around); MUST follow the comment, type, and coverage disciplines codified in `livespec`'s `non-functional-requirements.md` §"Linter rule set", §"Typechecker rule set", and §"Code coverage thresholds".

## Shared runtime — livespec-runtime

The shared-runtime mechanism between `livespec` and every livespec-governed consumer is `livespec-runtime`: a versioned Python package published from `github.com/thewoolleyman/livespec-runtime`. The mechanism is sibling-and-complementary to `livespec-dev-tooling` (which owns enforcement-suite code per §"Shared code sync — livespec-dev-tooling") and to `copier` (which owns static scaffolds per §"Shared content sync — copier template"). The three channels partition livespec's shared content along the static-vs-buildtime-vs-runtime axis: `copier` ships static files; `livespec-dev-tooling` ships build-time check modules consumed via `[dependency-groups].dev`; `livespec-runtime` ships runtime modules consumed by skills, doctor invariants, hooks, and CI workflows at invocation time.

`livespec-runtime` MUST be governed by livespec via its own seeded `SPECIFICATION/` tree (the `livespec` 4-file template plus `non-functional-requirements.md`) and MUST track its own work via the active `livespec-impl-*` plugin per `.livespec.jsonc`. The sibling library MUST declare a `compat` block pinning its `livespec` semver range and its currently-pinned `livespec` release tag, on a `livespec-runtime` top-level key in its own `.livespec.jsonc`, structurally identical to how every `livespec-impl-*` consumer and `livespec-dev-tooling` declare their blocks per §"Cross-repo coordination — pin-and-bump".

Consumers consume `livespec-runtime` via one surface: the Python package added to `pyproject.toml` either as a runtime dependency under `[project].dependencies` or as a dev dependency under `[dependency-groups].dev`, with `[tool.uv.sources]` declaring `git = "https://github.com/thewoolleyman/livespec-runtime.git"` plus `tag = "vX.Y.Z"`. Invocation MUST take the form `import livespec_runtime.<subpackage>` or `python -m livespec_runtime.<entry>`. PyPI publishing is NOT required in v1; the uv git-source path is sufficient for tag-pinned reproducible builds. There is NO reusable GitHub Actions surface (consumers invoke `livespec-runtime` from their own workflow steps directly, since the call sites are inside skill / hook / wrapper code that the consumer composes itself).

The initial subpackage scope at `v0.1.0` is the empty `livespec_runtime.cross_repo` skeleton; the implementation lands as `v0.2.0` per the typed `DependsOnEntry` union and `resolve_ref` contract defined in §"Cross-repo dependency awareness" (subject to that section's propose-change cycle landing). Future subpackages MAY be added under `livespec_runtime/<name>/`; each new subpackage's public surface MUST be defined in `livespec-runtime`'s own `contracts.md`.

`livespec-runtime` MUST declare a semver-stable public API: each subpackage's exported names, dataclass shapes, function signatures, and `python -m` entry points MUST NOT change without a MAJOR version bump. Internal module layout MAY change at any version increment.

`livespec-runtime` MUST target Python 3.10+ exclusively (matching `livespec`'s floor per `non-functional-requirements.md` §"Toolchain pins"); MUST NOT take a runtime dependency on `livespec` itself (the library is consumed by `livespec`, not the other way around); MUST follow the comment, type, and coverage disciplines codified in `livespec`'s `non-functional-requirements.md` §"Linter rule set", §"Typechecker rule set", and §"Code coverage thresholds". Unlike `livespec-dev-tooling`, `livespec-runtime` MAY perform network I/O (the cross-repo subpackage's GitHub queries depend on it); the no-network-I/O rule is specific to enforcement-suite code.

## Sibling spec ownership

Implementation surfaces hosted by livespec-governed sibling libraries — `livespec-dev-tooling`'s composite Action / reusable workflow / Python check inventory, `livespec-runtime`'s subpackage public APIs, and any future sibling library's contractual surface — MUST be specified in those siblings' own `contracts.md` files. `livespec`'s spec states the policy (the requirement that the surface exists, the consumer-facing shape, the semver discipline principle); the sibling's spec owns the specific surface enumeration and the implementation contract.

This partition mirrors the existing precedent at §"Shared code sync — livespec-dev-tooling" ("The canonical partition list MUST live in `livespec-dev-tooling`'s own `contracts.md`") and generalizes it across every sibling library. When a future sibling library joins the livespec family, its own seeded `SPECIFICATION/` tree becomes the authoritative location for its implementation contract; `livespec`'s own spec MUST NOT duplicate that content.

The rule applies symmetrically to automation surfaces hosted in `livespec-dev-tooling`'s `.github/` (per its `contracts.md` §"Cross-repo coordination automation surface"). `livespec`'s spec MAY cross-reference these surfaces but MUST NOT specify their input/output schemas, dispatch payload shapes, auth models, or any other implementation detail — those live in the owning sibling's spec.

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

### `propose-change` payload validation

`bin/propose_change.py` validates the inbound `--findings-json` payload against `proposal_findings.schema.json` at the wrapper boundary before writing the proposed-change file. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per `## Lifecycle exit-code table`, the calling `propose-change/SKILL.md` prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-invoke the template prompt with error context; the retry count is intentionally unspecified in v1.

The `spec_commitments` top-level field (when present) MUST validate against the structured shape codified in `spec.md` §"Proposed-change and revision file formats" → "Spec→impl commitment declaration" before the propose-change file is written. A propose-change payload declaring a malformed `spec_commitments` block (missing `id_hint`, empty `description`, non-kebab-case slug) MUST cause the wrapper to exit `4`, retryable via the LLM regeneration path. The wrapper does NOT validate that the declared `id_hint` is unique across the spec tree; collisions are surfaced post-revise by the `unresolved-spec-commitment` doctor invariant when two distinct declarations point at conflicting work-items.

### `critique` payload validation

`bin/critique.py` validates the inbound `--findings-json` payload against `proposal_findings.schema.json` at the wrapper boundary before any internal delegation. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per `## Lifecycle exit-code table`, the calling `critique/SKILL.md` prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-invoke the template prompt with error context; the retry count is intentionally unspecified in v1. The skill MAY surrender after a bounded number of retries by surfacing the structured findings to the user.

### `critique` internal delegation

After successful payload validation, `bin/critique.py` resolves the author identifier via the unified precedence codified in `spec.md` §"Author identifier resolution" and delegates to `propose-change`'s internal Python logic with the resolved-author stem as topic hint and the literal string `"-critique"` as the reserve-suffix parameter. The topic hint passed in is the un-slugged resolved-author stem itself; `critique` MUST NOT pre-attach `-critique` to the hint. `propose-change`'s reserve-suffix canonicalization (codified in `spec.md` §"Proposed-change and revision file formats" under "Reserve-suffix canonicalization") composes the two into the canonical critique-delegation topic, guaranteeing the `-critique` suffix is preserved intact at the 64-char cap and pre-attached `-critique` does not double. `-critique` is the canonical critique-delegation suffix; no other suffix value is permitted on this code path. The internal delegation MUST NOT retrigger the pre/post `doctor`-static cycle described in `spec.md` §"Sub-command lifecycle" — the outer `critique` invocation's wrapper ROP chain already covers the whole operation; only one pre-step and one post-step `doctor` run per outer CLI invocation, regardless of how many internal wrapper compositions occur. After the delegation writes the proposed-change file, `critique` exits with `propose-change`'s exit code; `critique` does NOT run `revise`. The user reviews the resulting proposed-change file and invokes `/livespec:revise` separately to process it.

### `revise` payload validation

`bin/revise.py` validates the inbound `--revise-json` payload against `revise_input.schema.json` at the wrapper boundary before any deterministic file-shaping. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per `## Lifecycle exit-code table`, the calling `revise/SKILL.md` prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-assemble (or re-prompt) accordingly; the retry count is intentionally unspecified in v1. The skill MAY surrender after a bounded number of retries by surfacing the structured findings to the user.

Revise's post-step doctor MUST run the `unresolved-spec-commitment` invariant against the freshly-cut `vNNN/` snapshot. Pre-step doctor runs the same invariant against the pre-revise state, surfacing any previously-accepted commitments that have lost their work-item coverage between the prior revise and this one (e.g., a work-item deleted out-of-band, or a propose-change accepted in an earlier revise whose commitments were never filed). The post-step run is the gating point; pre-step provides early visibility but does NOT block revise's execution.

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

This is the **wrapper-chain tier** of the family's end-to-end testing — the
second-tier integration test (faster, deterministic, mock-LLM), a sibling to
and NOT a superset of the §"CLI end-to-end harness contract" below (which drives
the `claude` CLI binary itself, as a real end user does). Both tiers coexist in
CI; neither replaces the other.

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

## CLI end-to-end harness contract

Every plugin in the livespec family MUST be covered by a top-of-pyramid,
user-surface end-to-end test whose sole interaction surface is the `claude` CLI
binary. This contract is a sibling to §"E2E harness contract" (the wrapper-chain
tier): it adds a higher tier, replaces neither, and both coexist in CI.

1. **Sole entry point is the `claude` CLI binary.** Setup MUST pre-populate a
   tmp `HOME` with `~/.claude/settings.json` declaring the marketplace and the
   enabled plugin (or run `claude -p "/plugin install …"` as the first step).
   Every workflow step MUST be a `claude -p` subprocess invocation issuing a
   slash command, multi-turn via `--continue` / `--resume <id>`. The harness
   MUST NOT reach around to wrapper Python files and MUST NOT depend on cache
   layout. The claude-agent-sdk programmatic surface MUST NOT be used here — the
   SDK is the wrapper-chain tier, not this tier.

2. **Pluggable implementation.** The harness MUST drive the upstream `livespec`
   plugin in lockstep with one *impl* plugin (today `livespec-impl-plaintext`;
   tomorrow alternate implementations). The impl-plugin id MUST be a parameter to
   the harness. The spec-side skill set is fixed; the impl-side skill set is
   whatever the installed impl plugin exposes.

3. **Structural skill discovery.** Skill enumeration MUST walk
   `<installed-plugin>/skills/*/SKILL.md` in each plugin's installed location, and
   the plugin slash-command prefix MUST be read from `plugin.json`'s `name`
   field. There MUST be no parallel manifest file; the Claude Code plugin
   directory structure is the canonical source of truth.

4. **Per-skill fixtures as a parallel filesystem convention.** A fixtures
   directory (suggested `<consumer-repo>/tests/e2e-cli/fixtures/<skill>/`) MUST
   hold a `prompt.md` (text piped to `claude -p`) and an `expected_files.txt`
   (paths that MUST exist afterward) per skill. Discovery walks the same way:
   directory present == fixture exists.

5. **Time-bomb coverage gate (fail-closed).** The harness MUST assert that every
   discovered skill has a fixture — i.e. the set difference
   `discovered_skills − fixtured_skills` is empty — and MUST fail the run
   otherwise. A new skill added to either plugin trips the gate until either
   (a) a fixture directory is added, or (b) the skill is explicitly listed in an
   `EXEMPT_SKILLS` table in the consumer repo with a written justification.

6. **Single canonical implementation in `livespec-dev-tooling`.** The harness
   itself (driver, fixtures loader, discovery, coverage gate, step orchestrator)
   MUST ship from `livespec-dev-tooling` and be consumed by every plugin repo via
   the existing pin-bump dependency flow. Each consumer repo wires the imported
   test function into its own pytest collection.

7. **Consumer obligations.** Each plugin claiming livespec-family membership
   MUST: (a) be installable solely via the `claude` CLI plugin-install surface;
   (b) ship a `tests/e2e-cli/` directory with per-skill fixtures; and (c) pass
   the imported harness against itself and, where applicable, against the
   upstream `livespec` plugin paired in lockstep.
