# Contracts — `livespec`

This file enumerates `livespec`'s contract surfaces: the cross-boundary CLI contract wired by `.livespec.jsonc` (per `spec.md` §"Contract + reference implementations architecture") and the wire-level interfaces of core's reference implementation — harness-neutral operation prose, Python wrappers, schemas, and templates. Per `livespec`'s repo-native principle, contracts MUST be language-neutral (JSON or CLI argument shapes), so any tool authored against the contracts works regardless of which language internalizes them.

## Wrapper CLI surface

The wrappers in this section are core's REFERENCE IMPLEMENTATION of the spec-side CLI contract (per §"Spec-side CLI contract"). The decomposition of each operation into harness-neutral prose plus a wrapper CLI has landed; these wrapper shapes are the concrete spec-side CLI surface that every Driver binding invokes.

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
| `4` | `ValidationError` — schema or wire-format validation failure on inbound payload (retryable per the calling operation prose's retry-on-exit-4 contract) |
| `127` | too-old Python or missing tool — `_bootstrap.py` early exit |

Domain errors flow as `Failure(<LivespecError>)` payloads on the railway; the supervisor `main()` pattern-matches and lifts the exit code from the error's `exit_code` ClassVar. Bugs propagate as raised exceptions to the supervisor's bug-catcher and result in exit 1.

## Operation prose ↔ template JSON contracts

The seed flow exchanges a JSON payload conforming to `seed_input.schema.json`. The schema is co-authoritative with its paired dataclass at `livespec/schemas/dataclasses/seed_input.py` per the schema-dataclass-pairing convention (v013 M6). Drift is caught by `dev-tooling/checks/schema_dataclass_pairing.py`.

The propose-change flow ingests `proposal_findings.schema.json`-conforming JSON via `--findings-json <path>`. The critique flow emits `proposal_findings.schema.json`-conforming JSON for downstream propose-change consumption. The doctor flow emits `doctor_findings.schema.json`-conforming JSON to stdout for the supervisor's exit-code derivation.

The revise flow ingests `revise_input.schema.json`-conforming JSON describing per-proposal accept/reject decisions and the resulting spec edits. Future widening MAY add additional payload schemas; each new schema MUST land with its paired dataclass in the same revision.

**Path-relativity documentation requirement.** Every wire-contract schema field that names a spec file path MUST document its path-relativity convention in the field `description`: either *project-root-relative* (e.g., `"SPECIFICATION/contracts.md"`) OR *spec-target-relative* (e.g., `"contracts.md"`). The two conventions MUST NOT be mixed within a single schema. Specifically: `proposal_findings.schema.json` `target_spec_files[]` items are project-root-relative; `revise_input.schema.json` `decisions[].resulting_files[].path` is spec-target-relative. Schema description text is the v1 enforcement surface; the description MUST appear directly on the field (not only in the surrounding human-prose contracts) so it is visible to any LLM or tool inspecting the loaded schema. A future revise cycle MAY add a doctor static check that grep-asserts every schema field whose JSON-pointer path matches `/path/i` or `/file/i` carries one of the two convention strings in its description.

## Orchestrator CLI contract — the three named CLIs

LiveSpec is agnostic to the orchestrator that consumes the spec and produces the implementation (per `spec.md` §"Contract + reference implementations architecture"). The cross-boundary contract is a CLI surface wired by `.livespec.jsonc`: three orchestrator-side CLIs are NAMED in config and otherwise behaviorally undefined. LiveSpec defines NONE of their behavior, only that they are named in `.livespec.jsonc` and callable (verified by the `config-named-cli-callability` invariant per §"Doctor cross-boundary invariants"):

- **Spec-reader CLI** — reads the spec however it wants (plain reads, cached, indexed, embedded, RAG, …). Its API is undefined — the same orchestrator writes both the reader and everything that consumes it, so their shared interface is private. It MUST expose spec content **by template category** (spec / contracts / constraints / scenarios / …) so a consumer can tell what is a scenario: it **categorizes, never conceals** — holdout is the orchestrator's policy choice, not the contract's. The category-exposure rule is the one normative property, stated on the CLI; the formerly-required capability set (read the current spec, read the history, report the current spec version, diff two versions) is downgraded to non-normative guidance for spec-reader implementers.
- **Gap-capture CLI** — a capture interface. Detects spec → impl gaps and writes them to whatever work-item mechanism the orchestrator has. The spec-reader CLI is injected as a reference. LiveSpec never sees the gaps or the store. Detection method is mechanical / LLM / human at the orchestrator's private choice — usually LLM (comparing a large prose spec to an implementation); this explicitly corrects the prior contract's "no LLM in the detection path" clause, which is wrong for real semantic gap detection.
- **Drift-capture CLI** — a capture interface. The spec-reader CLI and the propose-change CLI are injected as references. Routes impl → spec drift to propose-change. Filing is a machine path; acceptance is human, per the two-flow doctrine of `spec.md` §"Contract + reference implementations architecture".

**Orchestrator discipline invariant.** An orchestrator MUST depend only on the config-named CLI surface plus project configuration; it MUST NOT read spec-side internals beyond what the spec-side CLIs expose. Symmetrically, LiveSpec MUST NOT read the orchestrator's work-item store, prompts, or internal state. Every config-named CLI is dispatchable directly from the config value, with no out-of-band name → invocation mapping.

## Spec-side CLI contract

The spec-side lifecycle operations — `seed`, `propose-change`, `revise`, `critique`, `doctor`, `prune-history`, and `next` — are each named in `.livespec.jsonc`, pre-populated with core's reference defaults, and individually overridable: an alternate implementation of any one operation is selected by overriding its name in config. `propose-change` is the one spec-side CLI injected into the orchestrator (into the drift-capture CLI per §"Orchestrator CLI contract — the three named CLIs"). `doctor` is NOT privileged: it is config-named and overridable like any other spec-side CLI. Core's config schema also carries an optional `credential_wrapper` — a JSON array of literal argv tokens naming the project's conforming credential-injection CLI per `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source". Like the other named CLIs, its resolvability is verified by the `config-named-cli-callability` invariant per §"Doctor cross-boundary invariants" (its first token's callability carries a warn-vs-fail severity lever unique to this optional key — a present-but-non-executable first token fires `fail`, while an unresolvable first token fires `warn`, because the host-provisioned wrapper is legitimately absent on some runners; see §"Doctor cross-boundary invariants").

Core's config schema carries spec-tier facts (`template`, `spec_root`), the orchestrator selection, and the named CLIs — exact key naming is Phase-2 implementation detail; the contract is that config names an orchestrator and the CLIs. Orchestrator-private configuration (store formats, store paths, and the like) lives in the orchestrator's own config section, which core's schema does not know.

## CLI shape conventions

Every contract CLI — spec-side and orchestrator-side — follows these shape conventions:

- **One binary per side with subcommands**, NOT slash commands. Slash commands are a Driver-surface convenience layered on top, never the contract itself.
- **`--json` everywhere**, with stable schemas; human-readable text otherwise.
- **stdin/stdout plus files for payloads**, so any language can drive the CLI.
- **Stable exit codes** — the existing §"Lifecycle exit-code table" is reused unchanged.
- **Explicit project-root addressing** — every CLI accepts an explicit project-root, so a consumer can address any repository's state through the named CLI rather than by reading anything directly.

## Template manifest wire contract

`template.json` carries a `template_format_version` field bumped from `1` to `2` for templates that declare the `spec_files` manifest. v1 templates omit `spec_files`; the loader MUST treat v1 templates as if they declared `kind: markdown` for each well-known file the template's seed prompt enumerates. v2 templates MUST declare `spec_files` as an object mapping spec-target-relative paths to per-file declaration objects.

Each declaration object MUST carry `{"kind": "markdown"}` — a textual markdown spec file (subject to markdown-shaped checks and full LLM-context inclusion). `markdown` is the ONLY file kind: livespec manages no diagram-source or rendered-output kinds. Diagrams are fenced Mermaid blocks authored inside markdown spec files (per `spec.md` §"Template manifest"); an alternate diagram tool's rendered image, if any, is committed as an opaque asset that the manifest does not enumerate.

The schema bump from v1 to v2 lands in `.claude-plugin/scripts/livespec/schemas/template_config.schema.json`; the paired dataclass under `livespec/schemas/dataclasses/template_config.py` MUST stay co-authoritative per the schema-dataclass-pairing convention (v013 M6). Drift is caught by `dev-tooling/checks/schema_dataclass_pairing.py`.

## Built-in template contracts

`livespec` ships two built-in templates — `livespec` (multi-file) and `minimal` (single-file) — whose template-internal behavior is part of the contract a consumer inherits when selecting that template.

**`livespec` template.** The template root ships `livespec-nlspec-spec.md`, the canonical NLSpec-discipline reference document. Each REQUIRED prompt internalizes it at seed/use time; the document MUST NOT be copied into a project's end-user spec output (it ships with the template, not with generated content). The template's `template.json` declares `doctor_llm_objective_checks_prompt` and `doctor_llm_subjective_checks_prompt` as prompt paths (template-root-relative); the doctor LLM-driven phases invoke them, and each prompt MUST emit `doctor_findings.schema.json`-conforming output.

**`minimal` template.** End-user output is a single `SPECIFICATION.md` file at the project root rather than a multi-file `SPECIFICATION/` directory; the template's `template.json` declares `spec_root: "./"` plus a single declared file path to achieve this. For a `spec_root: "./"` (single-file) shape, the doctor static phase MUST resolve `SPECIFICATION.md` relative to the project root rather than `<spec_root>/SPECIFICATION/`. The `minimal` `template.json` declares `doctor_llm_objective_checks_prompt: null` and `doctor_llm_subjective_checks_prompt: null`; a `null` value for either field opts the template OUT of that LLM-driven phase, and the doctor wrapper MUST skip it — only the static phase runs for `minimal`-rooted projects.

The single-file `SPECIFICATION.md` body is partitioned by HTML-comment region markers so propose-change/revise cycles can target regions precisely: an open marker `<!-- region:<name> -->` and a close marker `<!-- /region:<name> -->` (matched by `<!--\s*(?:/)?region:([a-z0-9-]+)\s*-->`). The format invariants: markers MUST be HTML comments; each region MUST have a paired open + close marker; region names MUST be kebab-case `[a-z0-9-]+`; regions MUST NOT nest across boundaries; and each marker MUST appear on its own line.

The doctor static `gherkin-blank-line-format` check MUST exempt `minimal`-shape spec_roots whose `SPECIFICATION.md` contains no fenced ` ```gherkin ` blocks (emitting `status='skipped'`); when `SPECIFICATION.md` does contain gherkin blocks, the check applies normally.

## Sub-spec structural mechanism

Sub-spec emission is opt-in per v020 Q2: the seed prompt's pre-seed dialogue asks "Does this project ship its own livespec templates that should be governed by sub-spec trees?" On "yes", the prompt emits one `sub_specs[]` entry per template named in the dialogue, each carrying a per-template `files[]` array with its own spec-file paths under `<spec_root>/templates/<template_name>/`.

The seed wrapper materializes the main spec tree AND each sub-spec tree atomically per v018 Q1: a single `bin/seed.py --seed-json <payload>` invocation writes, for every spec tree, (a) every template-declared spec file, (b) the operation-owned `proposed_changes/README.md` and `history/README.md` directory-description files, (c) the `history/v001/` snapshot of every template-declared spec file, and (d) the `history/v001/proposed_changes/` subdirectory marker preserved in git via `.gitkeep` when the directory would otherwise be empty. The auto-captured `history/v001/proposed_changes/seed.md` + `seed-revision.md` are emitted for the main spec only; sub-specs do NOT receive auto-captured seed proposals per v018 Q1 — the main-spec `seed.md` documents the multi-tree creation as a whole, and each sub-spec's `history/v001/proposed_changes/` is consequently empty (the `.gitkeep` is the marker).

The `propose-change`, `revise`, and `critique` sub-commands accept `--spec-target <path>` to scope their operation to one specific spec tree. `--spec-target <project-root>/SPECIFICATION/templates/<name>/` targets a sub-spec tree; `--spec-target <project-root>/SPECIFICATION/` targets the main spec; etc. The `doctor` sub-command takes only `--project-root`; its multi-tree enumeration is internal (see §"Per-sub-spec doctor parameterization").

## Per-sub-spec doctor parameterization

The doctor static phase runs once per spec tree. The wrapper's main loop enumerates the main spec plus every `<spec_root>/templates/<name>/` sub-spec, runs the static checks against each, and emits per-tree findings on stdout. The wrapper's overall exit code is the worst per-tree code derived from the four-value Finding `status` enum (`pass`, `fail`, `skipped`, `warn` per `finding.schema.json`): any `fail` finding lifts the wrapper to exit 3; `pass`, `skipped`, and `warn` findings all yield exit 0. The `warn` status is reserved for productivity-grade housekeeping nudges (e.g., `master-direct-uncommitted-spec-edits`); the Driver-bound narration phase surfaces `warn` findings to the user but the Python layer MUST NOT emit ad-hoc stderr text for them (per the existing rule in `spec.md` §"Sub-command lifecycle" that the Python layer never prints warning text outside the structured-findings contract).

The static-check registry per v022 D7 is a narrowed enumeration in `livespec/doctor/static/__init__.py`. Each registered check exports `run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]`; the `ctx.spec_root` attribute carries the per-tree root. Per-check applicability dispatch (some checks apply only to main specs, some only to sub-specs) is finalized via the `DoctorContext`'s template-config inspection per v021 Q1.

## Doctor per-finding disposition dialogue

The `doctor` operation prose, through the active Driver binding, MUST offer a per-finding disposition dialogue for every non-`pass` finding surfaced during a single invocation, regardless of which phase produced it (static phase `fail` or `warn`, or any of the four LLM-driven phase categories — operation-prose objective, template-extension objective, operation-prose subjective, template-extension subjective). The disposition menu MUST present at minimum these five options:

- `fix-now` — apply the corrective action implied by the finding's `message`. OPTIONAL on a per-finding basis: only offered when the corrective action is mechanically describable from `message` (text edits, `mkdir`, single-shell-command cleanups). When the corrective action is not mechanically describable, this option MUST NOT be offered for that finding (the menu surfaces the remaining four).
- `capture-as-work-item` — route the finding to the active orchestrator's work-item machinery via the interactive front-end the orchestrator ships (the interactive consent dialogue is orchestrator-owned, not part of core's contract). Core's contract does not name the destination surface — work-item stores are orchestrator-private per §"Orchestrator CLI contract — the three named CLIs". The handed-off finding embeds the finding's `check_id`, `spec_root`, optional `path`, and `message` in its body so the trail back to the originating doctor finding is preserved. This disposition MUST ALWAYS be offered for every non-`pass` finding.
- `propose-change` — invoke `/livespec:critique` against the appropriate `--spec-target` (the tree whose `spec_root` surfaced the finding) and thread a `proposed_change_hint` as the user-described change. For LLM-driven phase findings the hint is the one produced inline by the check. For static-phase findings the hint is generated fresh from the finding's `message` and `path`/`line` fields. This disposition MUST ALWAYS be offered.
- `defer` — record the finding in the session's narration; take no durable action. The finding MAY surface again on the next invocation.
- `dismiss` — the user judges the finding does not apply. No durable action. No cross-invocation persistence of dismissals in v1; the finding MAY surface again on the next invocation and the user dismisses again or chooses a different disposition.

The dialogue MUST run BEFORE the Driver binding aborts on a static-phase `fail` (Exit 3 from the wrapper). The pre-existing safety contract that the LLM-driven phase MUST NOT run after a static-phase `fail` is PRESERVED: the dialogue handles disposition of the already-surfaced static findings only, with NO additional LLM-driven check generation. This narrows the scope of "abort" from "stop interacting with the user" to "do not run further check generation"; disposition of already-surfaced findings is not check generation.

The dialogue MUST run for static-phase `warn` findings too (today they are narrated in Step 3 without a disposition surface). The `warn` status retains its current semantics with respect to wrapper exit code (a `warn` finding does NOT lift the wrapper to exit 3); only the user-facing dispositioning is affected.

Findings with status `pass` and `skipped` are NOT dispositioned. They are surfaced via the existing Step 3 narration only.

A finding's disposition menu MUST present its five options in the canonical order listed above. The LLM prose surface MAY render the options as a single picker, MAY render them per-finding sequentially, or MAY batch all findings into a multi-disposition picker — the choice is a Driver-bound prose decision, not a contract one. The contract is the menu's CONTENT and AVAILABILITY guarantees.

## Doctor cross-boundary invariants

Doctor's entire cross-boundary job is wiring soundness: every config-named CLI resolves and is callable. Doctor MUST NOT inspect gaps, work-items, dependency graphs, memos, or any other orchestrator-private state — those disciplines are owned by the orchestrator, whose Ledger can enforce far richer invariants natively (per `spec.md` §"Contract + reference implementations architecture"). All entries in this catalogue are STRUCTURAL invariants per the **transient vs durable-pending** principle articulated in `spec.md` §"Terminology" — binary, contract-level, mechanically checkable. Doctor MUST NOT add productivity-heuristic invariants; spec-side productivity concerns belong to `/livespec:next`.

The catalogue comprises the single cross-boundary invariant `config-named-cli-callability` plus the repo-tier invariants defined below. The static-phase spec-tree catalogue (version contiguity, out-of-band edits, heading taxonomy, etc.) is unaffected by the cross-boundary shrink.

### `config-named-cli-callability`

For every CLI named in `.livespec.jsonc` — spec-side per §"Spec-side CLI contract", orchestrator-side per §"Orchestrator CLI contract — the three named CLIs", and the `credential_wrapper` credential-injection prefix per `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source" — the named entry MUST resolve and be executable. A missing or non-executable resolution fires `fail` naming the config key and value. When `credential_wrapper` is present and non-empty, its first token is resolved with the same semantics as every other named CLI, but the callability finding carries a severity lever unique to this OPTIONAL key: if the first token resolves to a file that is not executable (a real misconfiguration) the finding is `fail`; if the first token does not resolve at all — the host-provisioned wrapper is legitimately absent, e.g. on a CI runner that does not install it — the finding is `warn` (non-fail, so CI stays green); when the key is absent or empty the invariant is a no-op. The lever applies ONLY to `credential_wrapper`; the spec-side and orchestrator-side named CLIs keep their hard-fail semantics. The callability test is zero-shape: the named CLI resolves and is executable; no probe convention (no required `--version`, `--help`, or ping subcommand) is part of this invariant. If a probe convention later proves necessary it is a follow-on refinement, not part of this contract.

### `primary-checkout-commit-refuse-hook-installed`

Every livespec-governed primary checkout MUST install a `.git/hooks/pre-commit` and `.git/hooks/pre-push` hook whose body refuses to run when invoked at the primary checkout. The rule is fleet-wide: it applies to `livespec` itself, every `livespec-orchestrator-*` plugin's primary checkout, `livespec-dev-tooling`'s primary checkout, `livespec-runtime`'s primary checkout, and every future sibling repo generated from the copier template per `non-functional-requirements.md` §"Shared content sync — copier template". The check reads `<project-root>/.git/hooks/pre-commit` and `<project-root>/.git/hooks/pre-push`, verifies each exists and is executable, and verifies each contains the canonical livespec commit-refuse hook body (recognized via a stable marker comment string the canonical body MUST carry). The check fires `fail` when either hook is missing, non-executable, or contains a non-canonical body (including the empty file case). The narration directs the user to invoke the repo's documented bootstrap step (per `non-functional-requirements.md` §"Commit-refuse hook bootstrap procedure"), which idempotently installs the hook.

The canonical implementation of this check ships in `livespec-dev-tooling` at `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed`. The check is layout-independent (no `[tool.livespec_dev_tooling]` role keys consumed) and so belongs to the shared inventory per `non-functional-requirements.md` §"Shared code sync — livespec-dev-tooling" and the partition criterion in `livespec-dev-tooling/SPECIFICATION/contracts.md §"Shared check inventory"`: its intent and CLI surface are stable across every livespec-governed project, making a single implementation correct for the whole fleet. Every consumer repo MUST run the shared check in their `just check` aggregate AND CI matrix per the wiring-completeness invariant codified in `non-functional-requirements.md` §"Shared code sync — livespec-dev-tooling" (added by v094) and per the same invocation-agnostic discipline that governs every other shared check (per `non-functional-requirements.md` §"Enforcement-suite invocation" — the check ships from the shared inventory, the consumer repo decides only the recipe naming and the per-repo aggregate-list entry).

The shared check runs once per `just check`/CI invocation against the project root. Repo-local plugin-doctor catalog instances of the same check — e.g., `livespec`'s plugin-doctor static-phase entry that runs per spec tree under each `/livespec:doctor` invocation — remain valid and MAY coexist with the shared check: the two scopes/cadences are complementary (the shared check is a CI-time backstop against the project root; the plugin-doctor entry runs per-spec-tree under the wrapper-lifecycle of every `/livespec:*` sub-command). Defense-in-depth: both are retained.

The invariant is structural per the catalogue's intro principles (binary, contract-level, mechanically checkable); the canonical hook body is either installed at both paths or it isn't. The check MUST NOT distinguish between "hook missing" and "hook present but body is non-canonical" at the contract level — both fire equally; both are corrected by the same bootstrap invocation. The narration MAY name the specific failure mode for diagnostic clarity, but the structural `fail` finding is identical.

The check applies to the primary checkout's `.git/hooks/` directory only. Secondary worktrees share the `.git/` directory and therefore inherit the same hook scripts; the check does NOT need to inspect each worktree separately, and worktrees MUST NOT carry their own divergent `pre-commit` / `pre-push` hooks. Per-worktree hook overrides via the `core.hooksPath` config in a worktree are forbidden by this contract.

Fresh clones that have not yet had the bootstrap step run fail this invariant immediately. This is intentional: the failure is the mechanism by which a fresh contributor discovers the discipline. The narration includes the corrective bootstrap command verbatim so the resolution path is one terminal invocation away.

`core.bare` MUST NOT be set on the primary checkout. The v091–v094 bare-flag mechanism is superseded by this hook mechanism (see the **Primary-checkout commit-refuse hook** rule under `non-functional-requirements.md` §"Workflow discipline — spec-side changes" for the motivation: the bare-flag mechanism caused stale-on-disk-read failures at primaries that the hook mechanism does not). The doctor invariant MAY additionally surface a `fail` when `core.bare = true` is set on the primary, to catch the legacy-state case during the transition from the bare-flag mechanism to the hook mechanism.

### `master-direct-uncommitted-spec-edits`

Every worktree (primary or secondary, per `git worktree list --porcelain`) whose HEAD points at the default branch MUST NOT carry uncommitted modifications under `<spec-root>/`. The check enumerates every worktree, identifies the subset whose HEAD is the default branch (typically `master`), and for each invokes `git status --porcelain` scoped to `<spec-root>/`. Any non-empty output fires `warn` with corrective action narration that:

1. Names the offending worktree path.
2. Names the modified files under `<spec-root>/`.
3. Directs the user to commit-into-a-feature-branch (`git checkout -b <branch>` then commit) per the workflow discipline, OR to discard the edits if they were unintentional (`git checkout -- <files>`).

The check fires `warn` (not `fail`) consistent with the v079 prose at `non-functional-requirements.md:746` ("a `warn` finding"). Spec edits on master are a discipline violation, but the violating commit is not yet pushed — the warning gives the user time to recover.

The check covers the secondary-worktree-on-master bypass that the sibling `primary-checkout-commit-refuse-hook-installed` invariant cannot physically prevent (the commit-refuse hook refuses only at the primary checkout — where `git rev-parse --git-dir` equals `git rev-parse --git-common-dir`; a secondary worktree's git-dir differs, so the refuse branch is skipped and the commit proceeds, meaning a `git worktree add /path master` + edit + commit at the secondary worktree bypasses the hook). The two checks together close the enforcement loop.

Committed-and-then-discovered violations (the user committed on master and now the commit needs to be moved) are out of scope for this invariant; the existing `out-of-band-edits` check surfaces those via the snapshot-mismatch invariant.

### `copier-template-workflow-coverage`

Every consumer repository governed by livespec MUST contain a `.github/workflows/` directory whose set of workflow files is a SUPERSET of the required-file list enumerated in `non-functional-requirements.md` §"Shared content sync — copier template". The check fires `fail` for every required workflow file that is missing from the consumer's `.github/workflows/`. Each `fail` finding MUST name the specific missing file and MUST direct the user to run `copier update --vcs-ref=master` to re-sync from the template.

The invariant applies ONLY to project roots that are copier-template consumers, detected by the presence of a `.copier-answers.yml` file at the project root. A project root that does NOT carry `.copier-answers.yml` is out of scope: the check MUST emit a single non-failing `skipped` finding and MUST NOT inspect `.github/workflows/`. Only `livespec-orchestrator-*` consumers generated from the orchestrator-plugin copier template carry `.copier-answers.yml`; `livespec` itself, `livespec-dev-tooling`, `livespec-runtime`, and other non-consumer repos legitimately carry a different workflow set and are exempt. Consumer repos that DO carry `.copier-answers.yml` remain fully in scope and the `fail`-on-missing-required-file behavior above applies to them unchanged.

The invariant complements `copier update --dry-run --vcs-ref=master` (which catches divergence in files that DO exist in both the template and the consumer): `copier-template-workflow-coverage` catches files that exist in the template but NOT in the consumer (the "file was added to the template after the consumer was generated, and `copier update` was never run" case AND the "file was present in livespec but never made it into the template, and the consumer therefore lacks it" case). The two checks together close the workflow-coverage hole.

Workflow files in the consumer's `.github/workflows/` that are NOT in the required-list (consumer-local workflows) MUST NOT fire `fail` — they are out of scope for this invariant. Consumer-local workflows are catalogued by the consumer's own spec, not by livespec.

The invariant runs in doctor's static phase (no LLM in the path); the required-file list is read directly from `non-functional-requirements.md`'s enumerated scaffold list in §"Shared content sync — copier template". Drift between the contract list and the doctor invariant's hard-coded list MUST be caught by a paired enforcement-suite check that ships in `livespec-dev-tooling` (TBD in a parallel propose-change against that sibling's spec); for v1, the doctor invariant MAY hard-code the list and rely on PR review to catch drift.

### `wiring-completeness-cross-repo`

A `wiring-completeness-cross-repo` check (a repo-tier check: it reads sibling repos' `justfile`s, never any orchestrator-private state) MUST walk every registered sibling repo (per the `livespec-dev-tooling` and `livespec-runtime` and `livespec-orchestrator-*` registries declared in `non-functional-requirements.md` §"Shared code sync — livespec-dev-tooling" / §"Shared runtime — livespec-runtime" / §"Sibling spec ownership"), read its `justfile`'s `check` recipe, compute the canonical-set difference, and fire `fail` on any aggregate lacking any canonical slug. The check MAY use a sibling's `local_clone` path when configured or fall back to a GitHub query against the sibling's default-branch `justfile`. The invariant covers the adversarial-drift case in which a consumer drops both a canonical slug AND `check-aggregate-completeness` from its aggregate in the same change — the in-repo gate cannot catch that combination (the gate is gone before it next runs), but the cross-repo backstop can. The canonical set the check compares against is the `livespec_dev_tooling.canonical_checks` source of truth and the three-layer wiring-completeness invariant defined in `non-functional-requirements.md` §"Shared code sync — livespec-dev-tooling".

## Resolved-template stdout contract

`bin/resolve_template.py` MUST emit on success exactly one line: the resolved template directory as an absolute POSIX path, followed by `\n`. Paths containing spaces are emitted literally; callers MUST NOT pipe through shells that re-split on whitespace. The contract is frozen in v1; future template-discovery extensions MUST extend, not replace, the stdout shape and CLI flag set.

## Help-requested escape

Every wrapper MUST treat `-h` / `--help` as a `HelpRequested` signal, emit the argparse-rendered help text on stdout, and exit 0 (NOT exit 2). Per `commands/CLAUDE.md`, `HelpRequested.text` is one of two `commands/`-layer stdout-write exemptions (the other being `resolve_template`'s resolved-path emission).

## Plugin distribution

`livespec` is distributed as a Claude Code plugin via a marketplace catalog at the repo-root path `.claude-plugin/marketplace.json`. The marketplace lists the single plugin declared by `.claude-plugin/plugin.json`. The plugin and marketplace names share the value `livespec` by deliberate choice; both names are stable v1 contracts and renaming either MUST flow through a propose-change cycle.

`livespec` is ALSO distributed as a Codex plugin: core ships a Codex marketplace catalog at the repo-root path `.agents/plugins/marketplace.json` plus a paired `.codex-plugin/plugin.json`, both pointing at the SAME `prose/` and `scripts/` the Claude marketplace ships (a single cross-runtime artifact; no prose, wrapper, schema, or template is duplicated). The `.agents/plugins/marketplace.json` name and the `.codex-plugin/plugin.json` plugin name are stable v1 contracts; renaming either MUST flow through a propose-change cycle. A consumer installs core into Codex with `codex plugin marketplace add <owner>/<repo>` followed by `codex plugin add livespec@livespec`. Codex plugin enablement is HOST-WIDE: it is persisted in `~/.codex/config.toml` (a `[marketplaces.<name>]` entry plus a `[plugins."<plugin>@<marketplace>"] enabled = true` entry) and applies to every project on the host. This is asymmetric to the Claude path above, which enables plugins PER PROJECT via a committed `.claude/settings.json`; Codex offers no project-scoped plugin enablement, so the contract for Codex is the host-wide registration, not a committed per-project settings file.

End-user install path. Consumer projects enable `livespec` **at project scope** by committing a `.claude/settings.json` that declares the remote-GitHub marketplaces it needs under `extraKnownMarketplaces` and turns the plugins on under `enabledPlugins`, so the skills (and the Driver's bundled hooks) load ONLY in the governed project — never machine-wide. The committed settings file is NECESSARY BUT NOT SUFFICIENT: `enabledPlugins` enables a plugin that is ALREADY installed and installs nothing by itself. Every enabled plugin MUST ALSO be installed into project scope by an explicit `claude plugin install <plugin>@<marketplace> -s project`, run from the project root. An adopter that commits only the settings file reaches an enabled-but-not-installed state in which no operation resolves; recent Claude Code versions surface a not-installed notice in interactive sessions, but non-interactive and headless runs surface no failure at all, so this state MUST NOT be detected by waiting for an error:

```jsonc
{
  "extraKnownMarketplaces": {
    "livespec":               { "source": { "source": "github", "repo": "thewoolleyman/livespec" } },
    "livespec-driver-claude": { "source": { "source": "github", "repo": "thewoolleyman/livespec-driver-claude" } },
    "livespec-orchestrator-beads-fabro": { "source": { "source": "github", "repo": "thewoolleyman/livespec-orchestrator-beads-fabro" } }
  },
  "enabledPlugins": {
    "livespec@livespec": true,
    "livespec@livespec-driver-claude": true,
    "livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro": true
  }
}
```

Consumer projects MUST enable `livespec` (core) plus the Claude Code Driver plus the orchestrator plugin named by the project's `.livespec.jsonc` `implementation.plugin` key — substitute that orchestrator (e.g. `livespec-orchestrator-git-jsonl`) for `livespec-orchestrator-beads-fabro` in both blocks above. Committing enablement at project scope keeps clones, CI, and sandboxes resolving the same remote marketplaces while leaving unrelated projects on the host untouched. Installing is distinct from enabling, and install carries its own scope. `claude plugin install <plugin>@<marketplace> -s project` is the contract default and is REQUIRED alongside the committed settings file. The machine-wide form (`/plugin marketplace add thewoolleyman/livespec` + `/plugin install livespec@livespec`, equivalently `-s user`) remains supported but installs into EVERY project on the host. A zero exit status from a scoped plugin command does not establish that the invoking project was affected: `claude plugin update <plugin> -s project`, issued from a project holding no install record of its own, has been observed to act on ANOTHER project's record and report success. Tooling MUST therefore verify the resulting record per the invariant below rather than trust an exit status. The orchestrator that produces the implementation is selected in `.livespec.jsonc`, which names the orchestrator and its three orchestrator-side CLIs per §"Orchestrator CLI contract — the three named CLIs" alongside the spec-side CLI names per §"Spec-side CLI contract" (exact key naming is Phase-2 implementation detail; the contract is that config names an orchestrator and the CLIs). `.livespec.jsonc`'s schema root is `additionalProperties: true`; each plugin or sibling consumer owns a top-level section named for itself and MUST validate its own section on read and MUST tolerate unknown sections. Secrets MUST NOT live in `.livespec.jsonc`; orchestrators and integrations needing credentials MUST use a separate credentials channel (environment variables, OS keyring, secret manager).

Install verification. A project is correctly provisioned only when, for EVERY key in its committed `enabledPlugins`, `~/.claude/plugins/installed_plugins.json` holds an entry for that plugin whose `projectPath` equals the project root. Enabled-without-installed, and installed-against-a-different-`projectPath`, are both defective states that any provisioning or currency tooling MUST detect and report loudly; neither may be inferred from a command's exit status. Reference implementation: `livespec_dev_tooling/fleet/ensure_plugins.py`, which derives the marketplace and plugin set from the committed `.claude/settings.json` and issues `claude plugin install ... -s project` followed by `claude plugin update ... -s project` for each.

After installing core plus a runtime Driver, the Driver exposes the same eight operations as that runtime's interactive command surface: `seed`, `propose-change`, `critique`, `revise`, `doctor`, `prune-history`, `help`, `next`. The Claude Code Driver exposes them as `/livespec:*` slash commands namespaced under the Driver plugin name; the Codex Driver (`livespec-driver-codex`) exposes the same eight via Codex plugin skills resolving the same operations. Renaming any operation's command surface requires a propose-change cycle. The command surface is Driver-owned runtime mechanics; core supplies the harness-neutral prose, wrapper CLIs, templates, and schemas that each Driver binds.

The `marketplace.json` `description` field is a manual duplicate of `plugin.json`'s `description`; `plugin.json` is the source of truth. v1 does NOT enforce equality mechanically; future revise cycles MAY add a doctor static check to detect drift if it becomes operationally relevant.

Plugin uninstall remains a Claude Code platform behavior outside this contract; plugin update mechanics are likewise platform-owned, constrained here only by the install-verification invariant above — a scoped update's exit status does not establish which project's record it touched.

### Driver-shipped hooks

The Claude Code Driver plugin (`livespec-driver-claude`) SHIPS an agent-runtime hook bundle at `.claude-plugin/hooks/`: a `hooks.json` registration plus one executable hook entry per hook. The auto-memory redirect and plan-persistence WARN hooks MAY be shell scripts invoked by the harness as `"${CLAUDE_PLUGIN_ROOT}/hooks/<name>.sh"` or Python scripts invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.py"`; the cross-Driver no-shadow-ledger hook is a Python script invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/no_shadow_ledger.py"` so its one neutral body can ship byte-identically in both Drivers' bundles. The bundle is Driver-owned runtime mechanics per the Driver-binding partition (`spec.md` §"Contract + reference implementations architecture"): this section states the required hook surfaces and their behavioral disciplines; the script implementations and their tests live in the Driver repo. The bundle carries three hooks:

- **PreToolUse auto-memory redirect** (Claude hook surface; the Driver file MAY be a shell entry such as `block-auto-memory.sh` or a Python entry such as `block_auto_memory.py`). Registered on the `Write` tool; the effective matcher is `Write(**/memory/*.md)` — the hook acts only when the written file's immediate parent directory is `memory` and the filename ends in `.md` (the Claude Code auto-memory layout, `~/.claude/projects/<slug>/memory/*.md`). When such a write occurs AND the governed project (resolved via `CLAUDE_PROJECT_DIR`) carries a `.livespec.jsonc` whose `implementation.plugin` key names an active orchestrator plugin, the hook emits a block decision (PreToolUse `permissionDecision: deny`) whose reason INTENT-ROUTES the blocked content by its kind — rather than assuming it is always trackable work or silently dropping it: an in-flight trackable observation routes to the active orchestrator plugin's `/<plugin>:capture-work-item` skill (the work-item ledger); a durable specification rule routes to `/livespec:propose-change`; durable non-work-item agent guidance (a learned preference, convention, or discipline) routes to the member's `AGENTS.md` or a referenced progressively-disclosed `.ai/<topic>.md` file per §"Fleet agent-instruction core"; and only genuinely session-ephemeral scratch is dropped. The reason MUST NOT silently drop durable guidance and MUST NOT present `capture-work-item` as the sole destination. The orchestrator-ledger redirect target (the `capture-work-item` route) MUST be resolved from `implementation.plugin` — never hardcoded to any one orchestrator plugin; the `/livespec:propose-change` and `AGENTS.md` / `.ai/<topic>.md` routes are runtime-static destinations that do not depend on the orchestrator plugin's identity. The presence of a non-empty `implementation.plugin` value is the SOLE config gate (the `memos_path` gate named in the originating work-item predates the orchestrator-substrate migration and is retired; the work-item ledger is orchestrator-private).

- **Stop plan-persistence WARN** (Claude hook surface; the Driver file MAY be a shell entry such as `warn-plan-persistence.sh` or a Python entry such as `warn_plan_persistence.py`). Registered on the `Stop` event; scans the agent's last turn — the transcript entries after the last REAL user message (tool-result deliveries do not reset the window) — for substantial planning artifacts via mechanical thresholds (3+ markdown headings, 5+ table rows, or 10+ list items in the aggregated assistant text). When such an artifact exists and NO file-persisting tool call (`Write` / `Edit` / `MultiEdit` / `NotebookEdit`) happened in the same window, the hook emits a `systemMessage` warning directing the agent to persist the plan (a plan/doc file, or work-items via the active orchestrator plugin) before moving on. The hook is WARN-ONLY by contract: it MUST NOT block the stop (it never emits a `decision` key and never exits non-zero) and MUST NOT auto-file anything. It is the agent-runtime nudge realizing `non-functional-requirements.md` §"Completion includes persistence and workspace cleanup".

- **Stop no-shadow-ledger WARN** (`no_shadow_ledger.py`). Registered on the `Stop` event; scans the agent's last turn (the same last-real-user-message window as the plan-persistence hook) for a file-persisting tool call (`Write` / `Edit` / `MultiEdit`) that wrote a PLANNING ARTIFACT — a handoff, or any markdown file under a `plan/` or `prompts/` directory — whose written content carries markdown checkbox task-list items (`[ ]` / `[x]`) at or above a mechanical threshold. When such an artifact is found, the hook emits a `systemMessage` warning that the artifact embeds a parallel work queue and directs the agent to the no-shadow-ledger rule (`non-functional-requirements.md` §"Planning Lane guidance" → "No shadow ledger"): a planning artifact derives its status from the work-item ledger as its first action, so each checklist item is a session-local step OR a pointer to a real ledger id, never an embedded `[ ]`/`[x]` task queue. Like the plan-persistence hook it is WARN-ONLY (it never emits a `decision` key and never exits non-zero) and never auto-edits anything. Unlike the plan-persistence WARN hook, which the Claude bundle carries alone, the no-shadow-ledger hook is REQUIRED in BOTH Drivers' bundles (see the cross-Driver single-sourcing paragraph below); the auto-memory-write guard is likewise present in BOTH bundles, but as a PER-RUNTIME pair rather than a single shared body — the Claude auto-memory redirect targets the Claude layout (`~/.claude/.../memory/*.md`), and the Codex Driver ships its own guard targeting the Codex local-memory store (`~/.codex/memories/`), per the Codex auto-memory-write-guard paragraph below.

**Fail-open discipline (every hook).** ANY hook failure — `python3` absent from `PATH`, malformed hook-input JSON on stdin, unset `CLAUDE_PROJECT_DIR`, missing/unreadable/unparseable `.livespec.jsonc`, missing or malformed transcript — MUST be a silent pass-through with exit 0. A hook acts only when it POSITIVELY identifies its gating condition. Each Python hook body SHOULD expose an importable `main() -> int` that owns stdin/stdout at the hook boundary, catches expected and unexpected failures, returns `0` on every path, and does not call `sys.exit()` internally; the script entry tail MAY translate that return code into process exit. This keeps the body testable in-process for real per-file coverage while retaining a subprocess smoke test for the real hook I/O contract. Because the Driver plugin is enabled at PROJECT scope (a committed `.claude/settings.json` `enabledPlugins` entry, paired with the project-scoped install required by §"Plugin distribution"), its skills and this hook bundle load ONLY in repos that opt in; within such a repo the `.livespec.jsonc` config gate further scopes hook BEHAVIOR to livespec-governed state. The hooks MUST NOT disturb non-livespec projects (defense in depth, should a consumer enable the Driver more broadly) and MUST NOT break a degraded agent session.

**Cross-Driver single-sourcing (no-shadow-ledger).** The no-shadow-ledger hook's detection body MUST be single-sourced and ship BYTE-IDENTICALLY in BOTH Driver bundles — `livespec-driver-claude` (`.claude-plugin/hooks/`) and `livespec-driver-codex` (`livespec/hooks/`) — with each bundle's `hooks.json` `Stop` registration the thin per-runtime adapter. Codex consumes the Claude `Stop` hook I/O format, so one neutral body serves both runtimes. Byte-identity is mandatory ONLY for hook bodies this contract declares to be neutral shared bodies, currently `no_shadow_ledger.py`. Runtime-specific hooks — the per-runtime auto-memory guards, the Codex footgun guard, and the Claude-only plan-persistence WARN hook — share behavior where their contracts say so, not bytes, and are NOT byte-identity-bound. This section requires the single-sourced-and-byte-identical disposition for the declared neutral shared body; the mechanical guarantee that the Driver copies do not drift is realized by a consumer-side byte-identity Verifier pinned-and-imported from `livespec-dev-tooling` — each Driver's `just check` asserts its bundled copy is byte-identical to the packaged canonical body — per the Conformance Pattern's reuse-by-default rule (the commit-refuse hook body is the precedent). Its full five-slot expansion lives in `livespec-dev-tooling`'s own spec and is not pinned here to any one source-copying or synchronization mechanism. The mechanical detection internals (the planning-artifact path predicate, the checkbox threshold, the persisting-tool set) remain Driver implementation detail tunable without a core spec cycle per the closing paragraph, provided the WARN-only `Stop` posture and fail-open discipline hold.

**Codex footgun guard (required for mutating Codex automation).** The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the behavioral port of the Claude Driver's footgun guard: it MUST refuse a tool call that would (a) pass `--no-verify` to `git commit` / `git push`, (b) set `LEFTHOOK=0` or `LEFTHOOK=false` to disable lefthook, (c) set `core.bare = true` on a checkout, or (d) edit files at a livespec primary checkout. The guard MUST be in place before the Codex Driver claims any MUTATING operation (`seed`, `propose-change`, `critique`, `revise`, `prune-history`); read-only operations (`help`, `next`, `doctor`) do not depend on it. Like the Claude hook bundle, the script implementation and its tests live in the Driver repo; this section states only the required surface and its behavioral discipline. The fail-open discipline above applies: a hook failure (missing interpreter, malformed input, missing config) MUST be a silent pass-through, and the guard acts only when it POSITIVELY identifies a forbidden invocation. The destructive-command controls the operation prose already carries are PRESERVED and additive to this guard — in particular `prune-history` remains explicit-user-invocation only and MUST NOT be auto-activated.

**Codex auto-memory-write guard (required).** The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the per-runtime sibling of the Claude auto-memory redirect: in a livespec-governed project it MUST intercept a tool call that would write a file into the Codex local-memory store (`~/.codex/memories/`) — a manual `apply_patch` / `Edit` / `Write` whose target path is under that store — and emit `permissionDecision: deny` with a reason that INTENT-ROUTES the would-be write by what it IS, identically to the Claude hook: an in-flight trackable observation to the active orchestrator plugin's `/<plugin>:capture-work-item` skill (resolved from `implementation.plugin`); a spec-level rule to `/livespec:propose-change`; durable non-work-item agent guidance to the member's `AGENTS.md` or a referenced progressively-disclosed `.ai/<topic>.md` file; and only genuinely session-ephemeral scratch may be dropped. The reason MUST NOT silently drop durable guidance. KNOWN LIMITATION (stated by contract, not a defect): Codex's PRIMARY memories are GENERATED IN THE BACKGROUND by Codex itself and are OUTSIDE the `pre_tool_use` hook lifecycle, so this guard CANNOT intercept them — it covers the manual-write path only. Codex's background-generated memories are governed instead by Codex's own memory configuration (off-by-default; the `[features] memories` flag and `memories.*` settings) together with the runtime-agnostic `AGENTS.md` / `.ai/<topic>.md` convention §"Fleet agent-instruction core" establishes, which Codex loads. Like the footgun guard, the script implementation and its tests live in the Driver repo; this section states only the required surface and its behavioral discipline. The fail-open discipline above applies: a hook failure MUST be a silent pass-through, and the guard acts only when it POSITIVELY identifies a write into the Codex local-memory store.

Adding or removing a hook in the Driver bundle, renaming a hook surface, or changing a hook's posture (block vs. warn) requires a propose-change cycle against this section. The mechanical detection internals (matcher predicates, artifact thresholds, persisting-tool set) are Driver implementation detail and MAY be tuned Driver-side without a core spec cycle, provided the posture and gating disciplines above hold.

### Daily dogfooding path

For maintainer development of the `livespec` plugin source in this repo, launch Claude Code with `--plugin-dir .` to load the core plugin directly from the local source. Live edits to core-owned `.claude-plugin/prose/<name>.md` and `.claude-plugin/scripts/...` are picked up via `/reload-plugins` without re-installing. Claude Driver binding edits happen in the `livespec-driver-claude` repository, not in core. The marketplace install path (`/plugin install livespec@livespec`) is for verifying the published install flow; it copies the plugin into `~/.claude/plugins/cache/` and does NOT live-reload.

## Fleet agent-instruction core

Every livespec-governed repo — `livespec` itself, every `livespec-orchestrator-*` plugin, `livespec-dev-tooling`, `livespec-runtime`, and every future sibling generated from the copier template per `non-functional-requirements.md` §"Shared content sync — copier template" — MUST carry a **fleet-universal agent-instruction core**: the subset of canonical agent-orientation prose that applies to every member, shipped from the orchestrator-plugin copier template so generated repos inherit it. Repo-specific agent prose is additive on top of the core; it MUST NOT replace or shadow the core.

The core MUST include, at minimum: the repository mutation protocol (worktree → PR → merge → cleanup), the agent prerequisites for plugin work, the daily-commands surface, the revise co-edit discipline, and — for beads-backed members — the **beads runtime prerequisites**. The beads-runtime prose states that every beads tenant injects a single bare `BEADS_DOLT_PASSWORD` via its configured per-project credential-injection wrapper — the `.livespec.jsonc` `credential_wrapper` key (per `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source"): livespec fleet tenants share ONE fleet Dolt password injected by the fleet wrapper `with-livespec-env.sh` (the fleet reference default), while an INDEPENDENT (non-fleet) tenant declares its own `credential_wrapper` injecting its own tenant password from its own 1Password Environment (e.g. its own `with-<project>-env.sh` wrapper). Either way `bd` consumes the same bare variable; there is NO per-tenant `BEADS_DOLT_PASSWORD_<tenant>` variable and NO per-call mapping. Tenant isolation comes from the per-tenant SQL user plus DB-scoped grant rather than from password distinctness or wrapper identity. The beads-runtime prose is authored ONCE in the canonical core and referenced by members — never re-authored per repo — so the model cannot drift between members.

A member's agent instructions MUST live in a canonical `AGENTS.md` at the repo root, and `.claude/CLAUDE.md` MUST be a symlink to `../AGENTS.md` — a single source of truth, never a hand-maintained divergent duplicate.

A member's `AGENTS.md` MAY progressively disclose detailed agent guidance into sibling **`.ai/<topic>.md`** files that it references, so the always-loaded `AGENTS.md` stays small and topic detail loads only when the agent is working on that topic. A `.ai/` directory is supported at ANY directory level: it sits beside that level's `AGENTS.md` (and its symlinked `.claude/CLAUDE.md`) and is scoped to it, mirroring the nested-`AGENTS.md` pattern Claude Code and Codex already honor. Nested `.ai/` topics are ADDITIVE — a deeper-level `.ai/<topic>.md` augments, never silently overrides, an ancestor-level topic of the same name, exactly as nested `AGENTS.md` composes additively.

Durable, non-ephemeral agent guidance — a learned maintainer preference, a convention, or a cross-cutting discipline — routes to `AGENTS.md` and its referenced `.ai/<topic>.md` files. The harness-private per-session local-memory store — the per-runtime ephemeral memory layout, whether the Claude Code auto-memory layout (`~/.claude/projects/<slug>/memory/*.md`) or the Codex local-memory store (`~/.codex/memories/`) — is NEVER the home for durable guidance in a livespec-governed member: it is ephemeral, per-user, per-machine, and invisible to other agents and runtimes, so anything durable written there is lost to the project. `AGENTS.md` is the guaranteed durable-guidance home in every member; the `.ai/<topic>.md` files are OPTIONAL progressive-disclosure overflow. Every `.ai/<topic>.md` path an `AGENTS.md` references MUST resolve to an existing file, at every directory level that declares one — so the destination the auto-memory redirect (§"Driver-shipped hooks") points to actually exists.

Beads-backed members MUST ship a **beads-access guard**: a Claude Code `PreToolUse` hook, carried in the copier template, that blocks a bare `bd`, `dolt`, or direct tenant `mysql` invocation unless it runs under the project's configured `credential_wrapper` (per §"Spec-side CLI contract"). The guard recognizes a wrapped invocation by the resolved `credential_wrapper`'s first token, with `with-<id>-env.sh` retained as the reference-default fallback pattern. The guard's matching is best-effort string-level interception; the guard is footgun-prevention, not the isolation boundary (the isolation boundary is the per-tenant SQL user plus DB-scoped grant). Its purpose is to convert the silent "ran outside the wrapper → tenant auth failure" footgun into an actionable block that names the wrapper.

Presence of the core, the `AGENTS.md` / `.claude/CLAUDE.md` symlink shape, the resolvability of every `AGENTS.md`-declared `.ai/<topic>.md` reference at each directory level, the beads-runtime section in beads-backed members, and the beads-access guard MUST be enforced fleet-wide by the shared fleet-membership obligation suite per `non-functional-requirements.md` §"Shared code sync — livespec-dev-tooling", so that drift in any member is un-mergeable — mirroring the suite's existing beads tenant-connection consistency obligation. The `AGENTS.md` convention block and a seed `.ai/<topic>.md` scaffold ship from the copier template per `non-functional-requirements.md` §"Shared content sync — copier template", so every adopter repo inherits the convention with a concrete example.

## `/livespec:next` spec-side thin-transport binding

`/livespec:next` is a thin-transport pass-through Driver binding ("thin-transport" is core-internal design vocabulary per `spec.md` §"Terminology", not a cross-plugin contract category). The backing Python wrapper lives at `.claude-plugin/scripts/bin/next.py` following the wrapper-shape contract codified in §"Wrapper CLI surface". `next` participates in the spec-side CLI contract like every other spec-side operation: it is config-named, pre-populated with core's reference default, and individually overridable per §"Spec-side CLI contract". The Driver binding MUST be a pass-through: all ranking, filtering, and formatting logic lives in the backing Python implementation, and the wrapper MUST NOT accrete a confirmation dialogue, an opt-in flag, or any other interactive layer.

The binding MUST read spec-side state — the Proposed Changes queue under `<spec-root>/proposed_changes/`, the Specification History under `<spec-root>/history/`, and any cached unresolved doctor findings — and emit structured JSON. Spec-side ranking is a spec-tier concern and remains in core's lifecycle; impl-side ranking is orchestrator-private (a Dispatcher concern over the orchestrator's Ledger, per `spec.md` §"Contract + reference implementations architecture"), and the spec ↔ impl adjudication is handled by the two flows — core performs no cross-side ranking composition. The binding MUST NOT mutate any spec-side state — it is purely advisory — and is exempt from the pre-step / post-step doctor static lifecycle (no mutation, no precondition risk) per the existing exemption convention for `help`, `doctor`, and `resolve-template`; see `spec.md` §"Sub-command lifecycle".

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

### `prune-history` ordering invariant

The `next` ranker MUST rank `prune-history` strictly below every other action in the `action` enumeration. When ANY ripe candidate exists with `action != prune-history` (i.e., `revise`, `propose-change`, or `critique`), the ranker MUST NOT emit `prune-history` as the primary recommendation. The `urgency: "low"` label on `prune-history` is a soft signal; this ordering invariant is a hard constraint independent of urgency.

### `.livespec.jsonc` configuration

The `next` wrapper MUST read a `next.prune_history_threshold` key from `.livespec.jsonc` on each invocation. The key value MUST be a positive integer; a non-positive value MUST cause the wrapper to exit `3` with a `PreconditionError` naming the offending key and value. When the key is absent, the wrapper MUST fall back to a default value of `20`. Projects MAY raise the threshold to defer prune-history recommendations on long-lived specs; projects MAY lower it to surface pruning sooner.

## Pre-commit step ordering

Lefthook pre-commit runs three commands in order: `00-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `01-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `02-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest. Commit-msg stage runs two gates in order: first `just check-conventional-commits {1}` (validates the subject prefix matches Conventional Commits 1.0; rejects non-conformant subjects with a structured diagnostic naming the canonical type set per `non-functional-requirements.md` §"Commit and merge discipline"); then `just check-red-green-replay {1}` (the v034 D3 replay hook). The Conventional Commits gate runs FIRST so non-conformant subjects fail fast before the heavier replay-mode dispatch. Pre-push runs `just check` (the full aggregate).

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

The per-commit Conventional Commits → semver mapping requires every commit on `master` to carry a valid Conventional Commits subject prefix; the master merge strategy (rebase-merge only, codified in `non-functional-requirements.md` §"Commit and merge discipline") preserves per-cycle commit subjects intact on master, ensuring release-please reads each commit's type directly without squash flattening.

## Sub-command wire contracts

The CLI-level wire contracts each sub-command's wrapper enforces at its argv boundary, beyond the schemas already declared in `## Operation prose ↔ template JSON contracts` and the exit-code semantics declared in `## Lifecycle exit-code table`. These wrappers are core's reference implementation of the spec-side CLI contract (per §"Spec-side CLI contract").

### `propose-change` payload validation

`bin/propose_change.py` validates the inbound `--findings-json` payload against `proposal_findings.schema.json` at the wrapper boundary before writing the proposed-change file. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per `## Lifecycle exit-code table`, the calling operation prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-invoke the template prompt with error context; the retry count is intentionally unspecified in v1.

The `spec_commitments` top-level field (when present) MUST validate against the structured shape codified in `spec.md` §"Proposed-change and revision file formats" before the propose-change file is written. A propose-change payload declaring a malformed `spec_commitments` block (missing `id_hint`, empty `description`, non-kebab-case slug) MUST cause the wrapper to exit `4`, retryable via the LLM regeneration path. The block is OPTIONAL informational provenance per that spec.md section; no cross-boundary enforcement attaches to it.

### `critique` payload validation

`bin/critique.py` validates the inbound `--findings-json` payload against `proposal_findings.schema.json` at the wrapper boundary before any internal delegation. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per `## Lifecycle exit-code table`, the calling operation prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-invoke the template prompt with error context; the retry count is intentionally unspecified in v1. The Driver binding MAY surrender after a bounded number of retries by surfacing the structured findings to the user.

### `critique` internal delegation

After successful payload validation, `bin/critique.py` resolves the author identifier via the unified precedence codified in `spec.md` §"Author identifier resolution" and delegates to `propose-change`'s internal Python logic with the resolved-author stem as topic hint and the literal string `"-critique"` as the reserve-suffix parameter. The topic hint passed in is the un-slugged resolved-author stem itself; `critique` MUST NOT pre-attach `-critique` to the hint. `propose-change`'s reserve-suffix canonicalization (codified in `spec.md` §"Proposed-change and revision file formats" under "Reserve-suffix canonicalization") composes the two into the canonical critique-delegation topic, guaranteeing the `-critique` suffix is preserved intact at the 64-char cap and pre-attached `-critique` does not double. `-critique` is the canonical critique-delegation suffix; no other suffix value is permitted on this code path. The internal delegation MUST NOT retrigger the pre/post `doctor`-static cycle described in `spec.md` §"Sub-command lifecycle" — the outer `critique` invocation's wrapper ROP chain already covers the whole operation; only one pre-step and one post-step `doctor` run per outer CLI invocation, regardless of how many internal wrapper compositions occur. After the delegation writes the proposed-change file, `critique` exits with `propose-change`'s exit code; `critique` does NOT run `revise`. The user reviews the resulting proposed-change file and invokes `/livespec:revise` separately to process it.

### `revise` payload validation

`bin/revise.py` validates the inbound `--revise-json` payload against `revise_input.schema.json` at the wrapper boundary before any deterministic file-shaping. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per `## Lifecycle exit-code table`, the calling operation prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-assemble (or re-prompt) accordingly; the retry count is intentionally unspecified in v1. The Driver binding MAY surrender after a bounded number of retries by surfacing the structured findings to the user.

### `revise` resulting_files path-relativity guard

`bin/revise.py` MUST reject any `resulting_files[].path` that is (a) absolute (begins with `/`) or (b) begins with the spec-target directory's basename followed by `/` (e.g., `SPECIFICATION/contracts.md` when `spec_target` is `SPECIFICATION/`). These shapes indicate the LLM emitted a project-root-relative path where a spec-target-relative path is required. The wrapper MUST reject via `UsageError` (exit 2) at the same validation boundary as the schema check, before any file-shaping work runs. The narrowed predicate — basename + `/` at the start of the path, not a substring match — avoids false positives for legitimate paths that contain the spec-target stem internally (e.g., a hypothetical `templates/SPECIFICATION/foo.md`). The error message MUST name the offending path and state that paths MUST be relative to `<spec-target>/` with no leading prefix.

### Pre-step skip control

The `propose-change`, `critique`, `revise`, and `prune-history` wrappers each support a mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag pair via argparse's `add_mutually_exclusive_group`. Effective skip resolution: (1) `--skip-pre-check` present → skip = true; (2) `--run-pre-check` present → skip = false (overrides config); (3) neither flag → use the `.livespec.jsonc` config key `pre_step_skip_static_checks` (default `false`); (4) both flags present → argparse rejects with a usage error and the wrapper exits 2 via `IOFailure(UsageError)`. When the resolved value is `true`, the wrapper MUST emit a single-finding `{"findings": [{"check_id": "pre-step-skipped", "status": "skipped", "message": "pre-step checks skipped by user config or --skip-pre-check"}]}` JSON document to stdout and proceed without invoking the pre-step doctor static phase. The Python layer MUST NOT print warning text outside the structured-findings contract or as ad-hoc stderr text — LLM narration in the operation prose surfaces the warning to the user. `bin/doctor_static.py` rejects BOTH `--skip-pre-check` AND `--run-pre-check` (it IS the static phase); passing either to it results in argparse usage error, exit 2.

## Prompt-QA harness contract

The prompt-QA harness lives at `tests/prompts/_harness.py` as a dedicated test-infrastructure module, NOT a stripped-down `tests/e2e/fake_claude.py` variant. The two harnesses are scope-distinct: the prompt-QA harness performs no LLM round-trip and no wrapper invocation; the e2e harness drives wrappers end-to-end via the Claude Agent SDK surface. The leading underscore on `_harness.py` marks it as test-internal; it is not imported outside `tests/prompts/`.

### Fixture format

Each prompt-QA test case ships under `tests/prompts/<template>/<prompt>/<case>.json` as a JSON document conforming to the fixture-format schema at `tests/prompts/_fixture.schema.json` (validated at load time via `fastjsonschema`). The fixture's required fields are:

- `prompt_name` (string): the REQUIRED-prompt name, one of `"seed"`, `"propose-change"`, `"revise"`, `"critique"`.
- `schema_id` (string): the named wire-contract schema the `replayed_response` MUST validate against — one of `"seed_input.schema.json"`, `"proposal_findings.schema.json"`, `"revise_input.schema.json"`.
- `input_context` (object): the variables the operation prose would pass to the prompt at invocation time. Shape is template-specific.
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

The harness module, the fixture-format schema, the per-template assertion modules, and the per-prompt test modules MUST satisfy every livespec Python rule that applies to test infrastructure: each `.py` file declares `__all__`; functions take keyword-only arguments per the universal `*` separator; function and method signatures carry full return-type annotations; dataclasses are `frozen=True, slots=True, kw_only=True`; private helpers carry the leading `_` prefix. Coverage measurement does NOT include `tests/prompts/` — the first-party trees measured by `[tool.coverage.run]` are `livespec/`, `bin/`, and `dev-tooling/` (selected via an `omit`-only blocklist rather than a `source` allowlist, per `non-functional-requirements.md` §"Code coverage thresholds"), so the unit-tier per-file 100% coverage gate does not extend to test infrastructure.

## E2E harness contract

This is the **wrapper-chain tier** of the fleet's end-to-end testing — the
second-tier integration test (faster, deterministic, mock-LLM), a sibling to
and NOT a superset of the Claude Driver's CLI-driven end-to-end tier (which
drives the `claude` CLI binary itself, as a real end user does; that tier's
contract is owned by `livespec-driver-claude`). Both tiers coexist in CI;
neither replaces the other.

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
