# `livespec` Proposal

`livespec` is a Claude Code plugin that delivers a skill for governing
a living `SPECIFICATION`: seeding it, proposing changes, critiquing,
revising, validating, pruning history, and versioning. It standardizes
lifecycle and governance; it leaves on-disk shape to a template.

This proposal uses BCP 14 / RFC 2119 / RFC 8174 keywords (`MUST`,
`MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`,
`OPTIONAL`) for normative requirements.

---

## Runtime and packaging

### Plugin delivery

- `livespec` MUST be delivered as a **Claude Code plugin** that
  contains a single `livespec` skill. The plugin root is
  `.claude-plugin/`.
- `.claude-plugin/plugin.json` MUST be present and fully populated
  (plugin metadata, skill manifest). Publishing to a Claude Code
  plugin marketplace is a v2 non-goal.
- During dogfooded development in the livespec repo,
  `.claude-plugin/skills/livespec/` is symlinked to
  `.claude/skills/livespec/` so the live plugin skill is usable
  in-repo without an install step.
- Future v2 extension: parallel plugin packaging for the `opencode`
  and `pi-mono` agent runtimes. This proposal does not specify that
  packaging.

### Skill layout inside the plugin

The skill MUST be organized as multiple files under
`.claude-plugin/skills/livespec/`, not a single monolithic file:

```
.claude-plugin/skills/livespec/
├── SKILL.md                           # entry point; delegates to commands/
├── commands/                          # one file per sub-command
│   ├── help.md
│   ├── seed.md
│   ├── propose-change.md
│   ├── critique.md
│   ├── revise.md
│   ├── doctor.md
│   └── prune-history.md
├── shared/                            # shared prose/logic referenced by commands
│   ├── template-loading.md
│   ├── lifecycle-invariants.md
│   └── ...
├── scripts/
│   └── doctor-static.sh               # doctor's static phase (bash)
├── livespec-nlspec-spec.md            # embedded grounding guidelines
└── specification-templates/           # built-in templates (see "Templates" below)
    └── livespec/
        ├── template.json
        ├── livespec-nlspec-spec.md
        ├── prompts/
        │   ├── seed.md
        │   ├── revise.md
        │   └── critique.md
        └── specification-template/
            └── SPECIFICATION/
                ├── README.md
                ├── spec.md
                ├── contracts.md
                ├── constraints.md
                └── scenarios.md
```

- Sub-command dispatch: a bundled shell parser tokenizes
  `args` (POSIX-style) and routes to the relevant
  `commands/<sub-command>.md` instruction file. The LLM is
  instructed after routing.
- Command files use `@`-reference syntax to force deterministic
  reading of critical files (e.g., `@shared/template-loading.md`).
- Deterministic logic (file walking, JSON structural checks,
  doctor's static phase) MUST be implemented as bash scripts under
  `scripts/`. LLM-driven behavior MUST NOT replace bash where a
  deterministic check is possible.

### Dependencies

- `jq` is a hard runtime dependency. The skill MUST check for its
  presence at start and, if missing, MUST abort with an
  OS-appropriate install instruction (e.g., `brew install jq`,
  `apt-get install jq`, `choco install jq`).
- LLM-bundled prompts MAY rely on `jq` for JSON parsing and field
  extraction within their instructions.
- No other runtime dependencies. The skill MUST NOT require
  Python, Node.js, or any language runtime beyond bash+jq.

### Host capabilities required

- File I/O within the project tree.
- Shell execution for the `doctor` static phase and other bundled
  scripts.
- LLM access through the host.

### Git

- `livespec` MUST NOT write to git (no commits, pushes, branches,
  tags).
- `livespec` MAY read git state (read-only `git status` /
  `git ls-files`) only where documented. The single documented
  reader in v1 is doctor check #9 (out-of-band edit detection),
  which uses it to distinguish WIP edits from committed edits.

### Skill-level vs template-level responsibilities

The skill owns **lifecycle and invariants**:
- Sub-command dispatch and arg parsing.
- All file I/O in `SPECIFICATION/`, `proposed_changes/`,
  `history/`.
- Versioning, history directory creation, version-number
  contiguity.
- Doctor's static phase invocation and result handling.
- File-format validation (proposed-change format, revision format,
  YAML front-matter schemas).
- JSON Schemas that template-emitted JSON must conform to; LLM
  re-prompting on malformed output; abort after N retries.
- Human-in-the-loop prompting (per-proposal decisions, delegation
  toggles).

The active template owns **content generation**:
- `prompts/seed.md` — given `<intent>`, produce initial contents for
  each specification file.
- `prompts/revise.md` — given proposed-change + current spec +
  optional `<revision-steering-intent>`, produce modified
  specification-file contents.
- `prompts/critique.md` — given current spec + critique author,
  produce a JSON `findings` array conforming to the skill's
  schema.
- `specification-template/` — the starter content copied to the
  user's repo at seed time.

The skill does NOT decide what content goes in which
specification file (template's job), generate any specification
text (template's job), or interpret intent (template's job).

The template does NOT write files (skill's job), manage version
history (skill's job), validate file formats via doctor (skill's
job), or prompt the user (skill's job).

---

## Specification model

### Template-agnostic principles (apply to ANY template)

- The specification is conceptually one logical living
  specification, whether it is physically represented as one file
  or many.
- Normative requirements in any specification file that contains
  them MUST use BCP 14 / RFC 2119 / RFC 8174 requirement language
  (`MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`,
  `SHOULD NOT`, `MAY`, `OPTIONAL`). The rule applies regardless of
  how many files the active template uses, including single-file
  templates.
- `intent` is not the name of any specification file in any built-in
  template, and custom templates SHOULD NOT use it as a filename.
  Reason: `intent` is the skill-level domain term for revision
  inputs; using it as a spec file name creates conceptual drag.
- Every normative heading in any specification file MUST be
  uniquely named within that file.
- When a heading is renamed, the same `revise` MUST update every
  markdown reference to it. Doctor MUST detect dangling references
  in its static phase.
- All intent (observations, critiques, external requirements,
  implementation feedback) flows through `propose-change` or
  `critique`. No other ingress paths to the spec lifecycle are
  defined.

### `livespec` template specifics (default template only)

These apply only when `template` is `livespec` (the default). A
different template MAY revise any of the rules in this subsection.

- The specification is represented as multiple files to create
  explicit boundaries for LLMs and tools.
- `spec.md` is the primary source surface of the living
  specification.
- `contracts.md`, `constraints.md`, and `scenarios.md` are
  specialized operational specification files of the same living
  specification.
- The split is intentional because those specialized files can be
  processed with lower nondeterminism and stronger checking than
  the general spec surface.
- `scenarios.md` is intentionally isolated so it can support
  holdout scenario usage in the StrongDM Dark Factory style.
  (Forward-looking rationale only; livespec v1 defines no holdout
  mechanism — that is an external evaluation system's concern.)
- Scenario examples and acceptance criteria in `scenarios.md` MUST
  use the standard Gherkin keywords `Scenario:`, `Given`, `When`,
  `Then`, `And`, `But`. Within a scenario block (from a `Scenario:`
  line up to the next `Scenario:` or end-of-file), each keyword
  line MUST be preceded and followed by a blank line so that every
  step renders as its own Markdown paragraph under GitHub-Flavored
  Markdown (GFM). Fenced code blocks MUST NOT be used to contain
  Gherkin steps: the `gherkin` info-string is not part of GFM or
  GLFM and renders inconsistently. No specific Gherkin runner is
  pinned; the contract is rendering predictability under GFM.
  Doctor enforces this format statically (see check #11).
- Cross-file references in any file inside `SPECIFICATION/` MUST
  use the GitHub-flavored anchor form
  `[link text](relative/path.md#section-name)`. The rule covers
  specification files, `SPECIFICATION/README.md`, proposed-change
  files, revision files, and within-file anchors.

---

## SPECIFICATION directory structure (livespec template)

The default (`livespec`) template produces:

```
<project-root>/
├── .livespec.jsonc                    (created by seed with full commented schema)
└── SPECIFICATION/
    ├── README.md                      (generated from template at seed; then a normal spec file)
    ├── spec.md
    ├── contracts.md
    ├── constraints.md
    ├── scenarios.md
    ├── proposed_changes/
    │   ├── README.md                  (skill-owned; written only at seed)
    │   └── <topic>.md                 (zero or more in-flight proposed-change files)
    └── history/
        ├── README.md                  (skill-owned; written only at seed)
        └── vNNN/                      (one directory per version)
            ├── README.md              (copy of SPECIFICATION/README.md at this version)
            ├── spec.md
            ├── contracts.md
            ├── constraints.md
            ├── scenarios.md
            └── proposed_changes/
                ├── <topic>.md                 (each proposal processed during the revise that produced this version)
                └── <topic>-revision.md        (paired revision decision record)
```

Notes:

- Historic files under `history/vNNN/` use plain filenames (no
  `vNNN-` prefix). The parent directory name conveys the version.
  Dropping the prefix preserves relative markdown links: an
  archived proposed-change containing `[Foo](../spec.md#foo)`
  resolves to `history/vNNN/spec.md` (the archived spec at that
  version), not to the current working spec.
- The parallel structure (`proposed_changes/` subdir under each
  `history/vNNN/`) mirrors the active `SPECIFICATION/` tree shape.
- The working `proposed_changes/` directory MUST be empty after a
  successful `revise` (every proposal is moved into the new
  history version).
- The directory-README files in top-level `proposed_changes/` and
  `history/` are **skill-owned**: hard-coded inside the skill,
  written by `seed` only, not regenerated on every `revise`. Their
  content is a one-paragraph description of the directory's
  purpose and the filename convention used there.
- `SPECIFICATION/README.md` is generated from the active
  template's `specification-template/SPECIFICATION/README.md` at
  seed time, then treated as a normal spec file (editable via
  `propose-change` / `revise`, not touched by the skill
  afterwards).
- When `prune-history` has been run, the oldest surviving version
  directory `vN-1` contains only a single `PRUNED_HISTORY.json`
  file instead of full content (see "Pruning history" below).

---

## Configuration: `.livespec.jsonc`

`.livespec.jsonc` lives at the project root. It is OPTIONAL; when
absent, all documented defaults apply.

### Schema

```jsonc
{
  // Active template. Accepts either a built-in name ("livespec") or
  // a path (relative to project root) to a custom template directory.
  // Default: "livespec"
  "template": "livespec",

  // Expected template format version. Belt-and-suspenders check
  // against the template's own declared `template_format_version`
  // in its `template.json`. Doctor validates they match.
  // Default: 1
  "template_format_version": 1,

  // If true, post-step doctor (run automatically after successful
  // seed / propose-change / critique / revise) skips the LLM-driven
  // phase's subjective checks. Explicit `livespec doctor` runs are
  // unaffected by this key unless overridden at invocation.
  // Default: false
  "post_step_skip_subjective_checks": false,

  // If true, sub-commands skip the pre-step static check. Intended
  // for emergency recovery when the project is in a broken state
  // that normal commands cannot repair. The skill MUST print a
  // warning every time pre-step is skipped.
  // Default: false
  "pre_step_skip_static_checks": false
}
```

`seed` MUST create `.livespec.jsonc` with this full schema inline,
including comments and defaults, so the configuration is
self-documenting on disk. Subsequent writes (if any) preserve
commentary.

### Validation

The skill MUST validate `.livespec.jsonc` against this schema on
every read. Schema file ships with the skill; LLM and bash
validate against it (`jq`-structural checks in bash; LLM
self-validation for richer constraints).

### Absence behavior

- If `.livespec.jsonc` is missing, the skill MUST behave as if it
  contained the schema defaults above.
- `seed` MUST create `.livespec.jsonc` with explicit defaults on
  first run.
- `doctor` MUST NOT fail when `.livespec.jsonc` is missing; it
  MUST fail (static phase) when present and malformed.

### Per-invocation CLI overrides

- `--skip-subjective-checks` on any sub-command that runs
  post-step doctor (and on `livespec doctor` itself) acts as a
  per-invocation equivalent of
  `post_step_skip_subjective_checks: true`. Effective skip =
  config OR CLI flag.
- `--skip-pre-check` on any sub-command acts as a per-invocation
  equivalent of `pre_step_skip_static_checks: true`. Effective
  skip = config OR CLI flag. Skill MUST print a warning.

### Multi-specification per project

Out of scope for v1. The schema intentionally has no
`specification_dir` field — the template controls placement.

---

## Templates

A template is a self-contained directory that defines both the
initial on-disk spec content and the LLM-driven behavior for each
command. Templates live under
`.claude-plugin/skills/livespec/specification-templates/<name>/`
for built-in templates, or at a user-provided path for custom
templates.

### Template directory layout (MUST)

```
<template-root>/
├── template.json
├── livespec-nlspec-spec.md               (OPTIONAL: discipline doc the skill injects)
├── prompts/
│   ├── seed.md
│   ├── revise.md
│   └── critique.md
└── specification-template/
    └── ...                                (mirrors intended repo-root layout)
```

- `template.json` is REQUIRED and MUST contain at minimum
  `{"template_format_version": 1}`. No other fields are defined
  in v1.
- `prompts/` is a fixed-by-convention path.
  `prompts/seed.md`, `prompts/revise.md`, and `prompts/critique.md`
  are REQUIRED.
- `specification-template/` is a fixed-by-convention path. Its
  contents mirror the repo-root structure the template intends to
  produce. At seed time, the skill copies/processes these into
  the user's repo at corresponding paths. A template MAY place
  spec files directly at the repo root (e.g.,
  `specification-template/SPEC.md` mirrors to
  `<repo-root>/SPEC.md`) or under any subdirectory structure.
- `livespec-nlspec-spec.md` at the template root is OPTIONAL; when
  present, the skill concatenates it as reference context with
  every template prompt invocation.

### Custom templates are in v1 scope

- `.livespec.jsonc`'s `template` field accepts either a built-in
  name or a path to a template directory.
- Doctor check #13 validates the resolved template directory has
  the required layout and that `template_format_version` matches
  what livespec supports.

### Skill↔template communication layer

All communication between the skill and template prompts is JSON
with schemas. Each template prompt has a documented input schema
(variables the skill provides) and output schema (what the prompt
emits). The skill validates output against the schema and
re-invokes on malformed output with error context. After a
configured number of retries (3), the skill aborts the
sub-command with an error and preserves partial state for
investigation.

Schemas for the JSON contracts ship as part of the skill in
`.claude-plugin/skills/livespec/schemas/`. Authoring the full
schemas and prompt input/output details is an implementation
task filed as a post-seed `propose-change`.

### Built-in template: `livespec`

The `livespec` template is the only built-in for v1. It produces
the SPECIFICATION directory structure shown above. Its starter
content for each specification file is described below.

Seed-time starter content:

- `SPECIFICATION/README.md`: overview listing the specification
  files, their purpose, the BCP 14 convention, and the Gherkin
  convention; boilerplate populated from intent.
- `spec.md`: top-level headings derived from the seed intent by
  the template's `prompts/seed.md` (template-controlled behavior).
  A "Definition of Done" heading at the bottom, even if initially
  empty.
- `contracts.md`: header and placeholder section(s).
- `constraints.md`: header and placeholder section(s).
- `scenarios.md`: header, an explanatory paragraph about the
  blank-line-separated Gherkin step convention (no fenced code
  blocks), and one placeholder scenario. Exact stub content:

  ```markdown
  # Scenarios

  This file holds acceptance scenarios in Gherkin form.
  Each Gherkin keyword line is preceded and followed by a blank
  line so that every step renders as its own Markdown paragraph
  under GitHub-Flavored Markdown. Fenced code blocks are not used
  to hold Gherkin steps.

  ## Scenario: <placeholder scenario name>

  Given a placeholder precondition

  When a placeholder action is taken

  Then a placeholder outcome is observed
  ```

The template's `prompts/livespec-nlspec-spec.md` at the template
root is the adapted NLSpec guidelines document; the skill injects
it as reference context with every command invocation.

---

## Versioning

- Versions are integer-numbered, zero-padded to three digits as
  `vNNN`. Version numbers MUST be monotonic and contiguous in
  the set of versions that exist on disk.
- Version numbers MUST always be parsed and compared numerically,
  never lexically. Doctor's contiguity check uses numeric
  parsing.
- Width starts at 3 digits. New versions are zero-padded to
  `max(3, width-of-previous-highest-on-disk)`. When `v999` is
  exceeded, the next version is `v1000` and all subsequent
  versions use ≥4-digit widths. Historic version directories and
  files keep their original widths forever (no retroactive
  renames). Mixed widths within `history/` are valid.
- The current working spec content lives at the paths produced
  by the template (for the `livespec` template: `SPECIFICATION/`
  plus partition files). Working files do NOT carry any
  version prefix.
- **v000 is the implicit empty pre-seed state.** It never exists
  on disk. `seed` models itself as the proposal that transforms
  v000 into v001.
- A new version is cut when, and only when, `revise` either
  accepts or modifies at least one proposal in
  `proposed_changes/`. A `revise` invocation that finds no
  proposals MUST fail hard and direct the user to
  `propose-change`.
- A `revise` invocation that processes proposals but rejects all
  of them MUST still cut a new version. The version's
  specification files are byte-identical copies of the prior
  version's specification files; the version's `history/vNNN/`
  directory contains the proposed-change files and rejection
  revisions. This preserves the audit trail for every proposal
  that ever reached `revise`.
- `seed` creates `v001` directly: it writes both the working
  specification files AND `history/v001/` including the seed's
  auto-created proposed-change and revision (see `seed` below).

---

## Pruning history

A dedicated `prune-history` sub-command removes older history
while preserving auditable continuity.

Operation:

1. Identify the current highest version `vN`.
2. Delete every `history/vK/` directory where `K < N-1`.
3. Replace the contents of `history/v(N-1)/` with a single file:
   `history/v(N-1)/PRUNED_HISTORY.json`, containing only
   `{"pruned_range": [first, N-1]}` (where `first` is the
   earliest version number that existed before this prune).
4. Leave `history/vN/` fully intact.

Invariants:

- Version numbers MUST NEVER be re-used. `prune-history` does
  not reset the counter.
- `PRUNED_HISTORY.json` MUST NOT contain timestamps, git SHAs,
  or identity fields. These are fragile under git rebase/merge,
  and git commit metadata already provides that audit context.
- Doctor's contiguity check (static check #6) reads the marker
  file and applies contiguity only to surviving versions (those
  with filename ≥ `N-1`). The pruned range is treated as
  intentional missing history.
- Running `prune-history` on a project with only `v001`
  (nothing to prune) is a no-op.

Users MAY run `prune-history` at any time to reduce repository
clutter.

---

## `livespec` skill sub-commands

Every sub-command MUST run `doctor`'s static phase as its first
step (the LLM-driven phase is run only by `doctor` itself). If
the static phase exits nonzero, the sub-command MUST abort with
the doctor output. Exceptions: `help` and `doctor` itself; plus
any sub-command invocation where pre-step is skipped via config
or CLI flag (which MUST print a warning).

After `seed`, `propose-change`, `critique`, and `revise` complete
successfully, they MUST run the full `doctor` (static phase +
LLM-driven phase) as a post-step. If
`post_step_skip_subjective_checks` is `true` (or its CLI
equivalent is passed), the LLM-driven phase's subjective checks
are skipped. Doctor's post-step output is reported to the user
but does not retroactively undo the sub-command's effects.

### `help`

- `help` shows usage and the sub-command list.
- `help <sub-command>` shows help for that sub-command.
- MUST NOT run `doctor` (pre- or post-step).

### `seed <intent>`

- With no args, prompts the user for `<intent>` in dialogue.
- `<intent>` is freeform text and MAY include references to
  existing specifications, examples, projects, or other
  context. Path references and `@`-mentions in the intent are
  handled by the LLM's natural file-reading capability; the
  skill requires no special path-dereference logic.
- Creates `.livespec.jsonc` with full commented defaults if
  absent.
- Invokes the active template's `prompts/seed.md` with
  `<intent>` and the template's `specification-template/`
  starter content as input. Writes the resulting files to the
  repo at the paths dictated by the template's
  `specification-template/` structure.
- Creates `history/v001/` (including a `README.md` copy, the
  initial spec files, and a `proposed_changes/` subdir).
- Captures the seed itself as a proposed-change in
  `history/v001/proposed_changes/seed.md` (one `## Proposal`
  with `<intent>` as its `### Proposed Changes` section) plus
  a paired auto-created
  `history/v001/proposed_changes/seed-revision.md` with
  `decision: accept`, `reviser_llm: livespec-seed`, and
  rationale "auto-accepted during seed."
- Idempotency: if any of the template-declared target files
  already exist at their target paths, `seed` MUST refuse and
  direct the user to `propose-change` or `critique` instead.

### `propose-change <topic> <intent>`

- Creates a new file
  `SPECIFICATION/proposed_changes/<topic>.md` containing one or
  more `## Proposal: <name>` sections (see "Proposed-change
  file format" below).
- `<intent>` is EITHER raw freeform text (CLI-user input) OR
  structured JSON findings (from programmatic callers like
  `critique`). The skill distinguishes by content shape:
  - Structured findings JSON conforming to the schema
    → short-circuit: skill maps each finding to one
    `## Proposal` section directly.
  - Raw `<intent>` text → skill invokes the active template's
    `prompts/propose-change.md` (if present; else a bundled
    default), which produces a JSON findings array, which the
    skill then maps to `## Proposal` sections.
- If a file with topic `<topic>` already exists, the skill MUST
  auto-disambiguate by appending a short suffix. No user prompt
  for collision.
- The proposed-change file MUST conform to the format defined in
  "Proposed-change file format" below.
- A `## Proposal` MAY include an inline diff in its `### Proposed
  Changes` section. Diff format is unified diff (`---`/`+++`/
  `@@`). Paths in diff headers are relative to the repo root.
- A proposal MUST be explicit about the intent it specifies. It
  MUST NOT defer sub-decisions to `revise`; `revise`'s only
  choice per proposal is accept / modify / reject. Open
  questions, alternatives, and "we should decide X later"
  content do NOT belong in a proposal. If those exist, resolve
  them before filing, or file a separate `critique`.

### `critique <author>`

- `<author>` defaults to a string identifying the current LLM
  context, derived from the host's available metadata. If no
  identifier is available, the literal `unknown-llm` MUST be
  used and a warning surfaced.
- Generates a critique of the current spec using the active
  template's `prompts/critique.md`. The prompt MUST emit JSON
  conforming to the findings schema (skill-owned; under
  `.claude-plugin/skills/livespec/schemas/critique-findings.json`).
- The skill validates the JSON against the schema; re-invokes
  the prompt on malformed output (up to 3 retries) with error
  context; aborts on repeated failure.
- The skill then invokes `propose-change` with topic
  `<author>-critique` and the structured findings as input.
  `propose-change`'s dual-input path recognizes structured JSON
  and short-circuits the reshape step.
- If a file with topic `<author>-critique` already exists, the
  skill MUST auto-disambiguate by appending a short suffix. No
  user prompt.
- Does not run `revise`; the user reviews and runs `revise` to
  process.

### `revise <revision-steering-intent>`

- `<revision-steering-intent>` is OPTIONAL. Its primary role is
  standing guidance on how existing proposals should be decided
  (e.g., "reject anything touching the auth section"). If the
  user uses it to inject new spec content without first filing
  a proposed-change, that is their choice and responsibility;
  the name discourages but does not forbid it.
- **`revise` MUST fail hard when `proposed_changes/` contains no
  proposal files**, directing the user to run `propose-change`
  first. No auto-creation of ephemeral proposals.
- For each `## Proposal` across all files in `proposed_changes/`,
  the LLM (invoked via the active template's `prompts/revise.md`)
  proposes an acceptance decision: `accept`, `modify`, or
  `reject`, with rationale.
- The user is presented with the per-proposal decision and MUST
  confirm or override before any history is written. At any
  point the user MAY toggle "delegate remaining proposals in
  this file to the LLM", in which case the skill
  auto-accepts/modifies/rejects remaining proposals in the
  same file without further confirmation.
- On `modify`, the LLM drafts the modification; user iterates in
  dialogue to convergence, then confirms. Auto-handled when
  the file is delegated.
- On user confirmation:
  - If any decision across all processed proposals is `accept`
    or `modify`, a new version `vN` is cut.
  - The current specification files are updated in place.
  - `history/vN/` is created with copies of the README and spec
    files at this new version.
  - A `history/vN/proposed_changes/` subdirectory is created.
  - Each processed proposal file is moved
    **byte-identical** from `SPECIFICATION/proposed_changes/`
    into `history/vN/proposed_changes/<topic>.md`. Relative
    markdown links preserved.
  - Each processed proposal gets a paired revision at
    `history/vN/proposed_changes/<topic>-revision.md`,
    conforming to the format defined in "Revision file format"
    below.
- After successful completion, `SPECIFICATION/proposed_changes/`
  MUST be empty.

### `prune-history`

- Runs the pruning operation defined in the "Pruning history"
  section above.
- Accepts no arguments in v1.
- Post-step doctor runs normally after pruning.

### `doctor`

`doctor` runs in two phases. The static phase is a bash script
at `.claude-plugin/skills/livespec/scripts/doctor-static.sh`.
The LLM-driven phase runs only after the static phase passes.

#### Static-phase output contract

The script writes structured JSON to stdout and returns exit
code 0 (all checks passed) or 1 (one or more checks failed).
Output shape:

```json
{
  "findings": [
    { "check_id": "doctor-06", "status": "fail", "message": "...", "path": "SPECIFICATION/history", "line": null }
  ]
}
```

No human-readable output is produced; the skill's LLM narrates
the findings to the user from the JSON.

#### Static-phase checks (exit nonzero on any failure)

1. `.livespec.jsonc`, if present, validates against its schema.
2. The active template (built-in or at the configured path)
   exists and has the required layout (`template.json`,
   `prompts/`, `specification-template/`). `template.json`'s
   `template_format_version` matches `.livespec.jsonc`'s
   `template_format_version` and is supported by livespec.
3. All template-required files (derived by walking the
   template's `specification-template/` directory) are present
   at their expected repo-root-relative paths.
4. `proposed_changes/` and `history/` directories exist under
   `SPECIFICATION/` and contain their skill-owned `README.md`.
5. Every `history/vNNN/` directory that is not the pruned-marker
   directory contains the full set of template-required files,
   a `README.md`, and a `proposed_changes/` subdir. The
   pruned-marker directory (the oldest surviving, when
   `PRUNED_HISTORY.json` is present) contains ONLY
   `PRUNED_HISTORY.json`.
6. Version numbers in `history/` are contiguous from
   `pruned_range.end + 1` (if `PRUNED_HISTORY.json` exists at
   the oldest surviving `vN-1` directory) or from `v001`
   upward. Numeric parsing.
7. Every revision file in `history/vNNN/proposed_changes/` has
   a corresponding proposed-change file with the same topic in
   the same directory.
8. Every file in the working `proposed_changes/` has a name
   conforming to `<topic>.md`.
9. **Out-of-band edit detection.** The diff between current
   specification files and the latest `history/vN/` copies is
   empty. Behavior if non-empty:
   - If the project is not a git repo: skip this check with a
     JSON finding marked `status: "skipped"`.
   - If git says the spec files have uncommitted changes (WIP
     by the user): skip with a JSON finding marked
     `status: "skipped"`.
   - Otherwise: the script auto-backfills a missing version.
     It creates
     `SPECIFICATION/proposed_changes/out-of-band-edit-<UTC-seconds>.md`
     containing one `## Proposal` with the diff as
     `### Proposed Changes`. It creates a paired revision in
     the corresponding location. It writes
     `history/v(N+1)/` with the current spec content. It then
     moves the proposed-change and revision into
     `history/v(N+1)/proposed_changes/`. Author identifier:
     `livespec-doctor`. Script exits 1 with a finding
     instructing the user to commit the changes and re-run.
10. BCP 14 keyword usage well-formedness:
    - **Static fail (a)**: misspelled uppercase BCP 14 keywords
      from a finite list (`MUSNT`, `SHOLD`, `SHAL`, etc.).
    - **Static fail (b)**: mixed-case BCP 14 keywords appearing
      as standalone words (`Must`, `Should`, `May`).
    - Sentence-level context-dependent checks move to the
      LLM-driven phase (see below).
11. **(Conditional: only when the active template is `livespec`.)**
    In `scenarios.md`, within any scenario block (from a
    `Scenario:` line through the next `Scenario:` or
    end-of-file), every line whose first non-whitespace token is
    a Gherkin keyword (`Scenario:`, `Given`, `When`, `Then`,
    `And`, `But`) MUST be preceded and followed by a blank line.
    Fenced code blocks containing Gherkin steps MUST NOT be
    present. Prose outside scenario blocks is unaffected.
12. All Markdown links in all files under `SPECIFICATION/` (spec
    files, READMEs, proposed-change files, revision files) with
    anchor references resolve to existing headings in the
    referenced files.
13. The resolved active template directory has the required
    layout and matching version (see check #2). Any unresolved
    or mismatched template configuration is a static failure
    naming the offending field, its value, and the path to
    `.livespec.jsonc`.

#### Static-phase exit codes

- `0`: all checks pass; LLM-driven phase MAY proceed.
- `1`: at least one check failed; LLM-driven phase MUST NOT run;
  the invoking sub-command MUST abort.

Static checks are pass-or-fail only. There is no warning tier.

#### LLM-driven phase

The LLM-driven phase is skill behavior, not a script. It has
no exit codes. Its findings are split into two categories;
both run by default.

**Objective checks** (always run; findings are deterministic in
principle):

- Internal contradiction detection (section A says X, section B
  says not-X).
- Undefined term detection (a requirement references a term
  not defined anywhere).
- Dangling / unresolvable references that escaped static check
  #12 (e.g., case-variant spellings).
- Spec↔history semantic drift (content moved between
  specification files without trace).
- BCP 14 case-inconsistency within a sentence (per static check
  #10's deferred case).
- Gherkin step semantic validity (each step is actually a step,
  not prose).

Objective checks produced by an LLM MUST be deterministic in
principle; if the LLM produces inconsistent findings across
runs, that is a logic error (LLM bug) reportable as such,
remediable by re-run or different model. The skill's error
messages for objective-check failures MUST name that
possibility.

**Subjective checks** (run by default; skippable via
`post_step_skip_subjective_checks` config or
`--skip-subjective-checks` CLI):

- NLSpec conformance evaluation beyond hard rules (economy,
  conceptual fidelity, spec readability).
- Template compliance semantic judgments (e.g., "contracts
  should go in contracts.md, not spec.md").
- Spec↔implementation drift (comparing spec content to the
  surrounding repo's source code).
- Prose quality / structural suggestions.

For any finding it surfaces, the skill prompts the user with a
description and asks whether to address it via a `critique`
call. The user MAY accept (which invokes `critique`), defer, or
dismiss each finding individually. No cross-invocation
persistence of dismissals in v1.

---

## Proposed-change file format

A proposed-change file MUST contain, in order:

1. YAML front-matter (file-level):
   ```yaml
   ---
   topic: <kebab-case-topic>
   author: <author-id>                # LLM identifier or human handle
   created_at: <UTC ISO-8601 seconds>
   ---
   ```
2. One or more `## Proposal: <short-name>` sections, each with
   the following sub-headings in order:
   - `### Target specification files` — list of file paths
     (repo-root-relative) this proposal touches.
   - `### Summary` — one paragraph stating what changes and
     why.
   - `### Motivation` — the intent input that produced this
     proposal.
   - `### Proposed Changes` — prose describing the changes, or a
     unified diff in fenced ` ```diff ` blocks, or both.

Each `## Proposal` is independently evaluated by `revise`
(accept / modify / reject). A proposal MUST NOT contain nested
`## Proposal:` headings.

A proposed-change file MUST NOT contain open questions,
alternatives, or "we should decide X later" content. If those
exist, resolve them before filing or file a separate `critique`.

---

## Revision file format

Each `<topic>-revision.md` in `history/vNNN/proposed_changes/`
MUST contain, in order:

1. YAML front-matter:
   ```yaml
   ---
   proposal: <topic>.md
   decision: accept | modify | reject
   revised_at: <UTC ISO-8601 seconds>
   reviser_human: <git user.name and user.email, or "unknown">
   reviser_llm: <host-provided LLM id, or "unknown-llm">
   ---
   ```
2. `## Decision and Rationale` — one paragraph explaining the
   decision.
3. `## Modifications` (REQUIRED when `decision: modify`) — prose
   describing how the proposal was changed before incorporation.
   Unified diffs are NOT used here (line-number anchors are
   fragile across multi-proposal revises). Optional short fenced
   before/after excerpts are permitted for hyper-local clarity.
4. `## Resulting Changes` (REQUIRED when `decision: accept` or
   `modify`) — names the specification files modified and lists
   the sections changed.
5. `## Rejection Notes` (REQUIRED when `decision: reject`) —
   explains what would need to change about the proposal for it
   to be acceptable in a future revision.

Note: historical versions of this format used the term
`acknowledgement`. That term is retired in favor of `revision`,
which better captures the role of the file (the outcome of a
revise decision) and matches the command name.

---

## NLSpec conformance

- The active template MAY ship a `livespec-nlspec-spec.md` (or
  equivalent discipline doc) at its root. When present, the
  skill MUST concatenate its contents as reference context
  before invoking ANY template prompt (seed, revise, critique).
- The `livespec` built-in template ships
  `livespec-nlspec-spec.md` — the adapted NLSpec guidelines
  document — enforcing NLSpec discipline for projects using the
  default template.
- Templates that ship no discipline doc get no injection. This
  keeps NLSpec a template-choice, not a skill-wide mandate.

---

## Testing approach

- Tests live in `<project-root>/tests/`. Implementation language
  is not pinned by this proposal; a companion
  `bash-skill-script-style-requirements.md`
  (destined for `SPECIFICATION/constraints.md`) will define
  bash-specific constraints including shellcheck and other
  static-analysis compliance enforced via git hooks / CI.
- A `tests/CLAUDE.md` MUST exist to enforce consistency between
  tests and the actual specification (instructing the LLM that
  test coverage tracks specification files, not implementation
  files).
- Tests MUST be split into separate files per specification file:
  `test_spec.*`, `test_contracts.*`, `test_constraints.*`,
  `test_scenarios.*`.
- Each test MUST execute the skill against fixtures in a
  throwaway temporary directory and compare results to expected
  outputs. The test runner MUST NOT mutate the project's own
  `SPECIFICATION/`.
- A meta-test, `test_meta_section_drift_prevention.*`, MUST
  verify that every top-level (`##`) heading in each
  specification file has at least one corresponding test case in
  the coverage registry.
- **Coverage registry**: `tests/heading-coverage.json` maps
  headings to test identifiers:
  ```json
  [
    { "heading": "Proposed-change file format", "test": "test_propose_change.sh::test_multi_proposal_write" }
  ]
  ```
  The meta-test fails in both directions:
  - Uncovered headings (in spec, not in registry): "heading X
    has no test."
  - Orphaned registry entries (heading in registry, not in
    spec): "registry entry for heading 'OldName' is orphaned.
    Update the registry or the test."

The workflow for creating/updating tests and the registry is an
implementation concern, not specified here.

---

## Definition of Done (v1)

`livespec` v1 is complete when all of the following are true:

1. All sub-commands implemented and exposed via the skill
   entry point: `help`, `seed`, `propose-change`, `critique`,
   `revise`, `doctor`, `prune-history`.
2. The plugin layout (`.claude-plugin/plugin.json` +
   `.claude-plugin/skills/livespec/` with `SKILL.md`, per-command
   files, shared files, scripts, schemas, and the built-in
   `specification-templates/livespec/` template) is complete and
   self-consistent.
3. The `livespec` built-in template is fully implemented
   (`template.json` declaring `template_format_version: 1`,
   prompts for seed/revise/critique producing schema-valid JSON,
   full starter content under `specification-template/`).
4. `.livespec.jsonc` schema validation is implemented.
5. Custom templates (template values pointing at a directory
   path) load successfully and pass all applicable doctor checks.
6. The full `doctor` static-check suite (13 checks above) is
   implemented with documented exit-code semantics and the JSON
   output contract.
7. The `doctor` LLM-driven phase's objective and subjective
   check categories are implemented with the skip-mechanism for
   subjective.
8. Every sub-command that does spec work loads the active
   template's discipline doc (if present) as reference context
   and invokes template prompts with schema-validated I/O.
9. The proposed-change and revision file formats are enforced
   by doctor's static phase (YAML front-matter validated;
   required headings present per decision type).
10. The test suite covers every sub-command, both doctor phases,
    the `prune-history` flow, and the meta
    `section_drift_prevention` test.
11. `jq` presence check is implemented; the skill aborts at
    start with an OS-appropriate message if absent.
12. `livespec` dogfoods itself: `<project-root>/SPECIFICATION/`
    exists, was generated by `livespec seed`, has been revised
    at least once through `propose-change` + `revise`, and
    passes `livespec doctor` cleanly.
13. The skill bundle includes its own `help` text covering every
    sub-command.

---

## v1 non-goals (stated explicitly)

The following are intentionally out of scope for v1. The proposal
calls them out so their absence is recognized as a deliberate
boundary, not an accidental gap.

- **Subdomain ownership and cross-cutting routing.** As argued
  in `subdomains-and-unsolved-routing.md`, no public consensus
  exists. Templates and prompt conventions handle this; livespec
  does not.
- **Multi-specification per project.** `.livespec.jsonc` has no
  `specification_dir` field; one specification per project.
- **Writing to git.** `livespec` MUST NOT invoke `git commit`,
  `git push`, or any write operations. Read-only `git status` is
  the narrow exception for doctor check #9.
- **Claude Code plugin marketplace publishing.** Plugin is
  manually installable in v1; marketplace distribution is v2.
- **Alternate agent runtime packaging (`opencode`, `pi-mono`).**
  Plugin targets Claude Code only in v1.
- **Cross-invocation suppression / allow-listing of LLM-driven
  findings.** The subjective-checks skip flag is the only
  suppression mechanism in v1.
- **Scripted non-interactive revise.** `revise` is designed for
  interactive confirmation.
- **Additional built-in templates beyond `livespec`.** `openspec`
  is not reserved; any alternate template is user-provided via a
  path.

---

## Self-application

`livespec` MUST be developed by dogfooding itself. The bootstrap
order is:

1. Author this proposal, `PROPOSAL.md`, to a state that passes
   the recreatability test against `livespec-nlspec-spec.md`.
2. Implement the plugin skeleton: `plugin.json`, `SKILL.md`,
   per-command files, `doctor-static.sh` implementing the static
   checks, the jq dependency check, and the minimum subset of
   the `livespec` template needed to consume PROPOSAL.md as
   seed input.
3. Run `livespec seed` against this project, producing
   `<project-root>/SPECIFICATION/` and `history/v001/`.
4. Implement remaining sub-commands (`propose-change`,
   `critique`, `revise`, `prune-history`, doctor's LLM-driven
   phase), using `propose-change` / `revise` cycles against the
   seeded spec.
5. Land the v1 Definition of Done items as the spec evolves.
   Move companion documents (`subdomains-and-unsolved-routing.md`,
   `prior-art.md`, etc.) into appropriate appendices or
   references within the seeded `SPECIFICATION/`.

Items in step (1) that this revised proposal does not yet
resolve become the first batch of `propose-change` filings after
step (3). Known such items:

- Full authoring of each template prompt's input/output JSON
  schemas and the prompts themselves.
- Full authoring of `bash-skill-script-style-requirements.md`
  and its incorporation into `SPECIFICATION/constraints.md`.
- Detailed mapping of brainstorming-folder companion documents
  to their destinations in the seeded spec.
