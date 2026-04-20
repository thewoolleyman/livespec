# `livespec` Proposal

`livespec` is a Claude Code skill for governing a living `SPECIFICATION`:
seeding it, proposing changes, critiquing, revising, validating, and
versioning. It standardizes lifecycle and governance; it leaves on-disk
shape to a template.

This proposal uses BCP 14 / RFC 2119 / RFC 8174 keywords (`MUST`,
`MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`,
`OPTIONAL`) for normative requirements.

---

## Runtime and packaging

- `livespec` MUST be delivered as a Claude Code skill.
- The skill MAY be installed project-local under
  `<project-root>/.claude/skills/livespec/` or user-global under
  `~/.claude/skills/livespec/`. Project-local installation, when
  present, takes precedence.
- The skill is a single entry point. Sub-commands are dispatched via
  the `args` parameter — the user invokes `/livespec <sub-command>
  [args...]`.
- The skill MUST rely only on capabilities the Claude Code host
  already provides: file I/O within the project tree, shell execution
  for the `doctor` static phase, and LLM access through the host.
- The skill MUST NOT invoke `git`, write outside the project tree, or
  require network access beyond what the Claude Code host already
  uses.
- The skill MUST be operable when the project has no
  `.livespec.jsonc` file (the `seed` sub-command creates one when
  absent; all other sub-commands fall back to documented defaults).

---

## Specification model

The specification model has two layers: principles that hold across
**any** template, and choices specific to the default **`livespec`**
template. They are split below so that template authors and reviewers
can see at a glance which rules they MUST honor and which they MAY
revise.

### Template-agnostic principles (apply to ANY template)

These hold for the `livespec` template, the (sketched) `openspec`
template, and any future custom template.

- The specification is conceptually one logical living specification,
  whether it is physically represented as one file or many.
- Normative requirements in any partition that contains them MUST
  use BCP 14 / RFC 2119 / RFC 8174 requirement language (`MUST`,
  `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`,
  `OPTIONAL`). The rule applies regardless of how many files the
  active template uses, including single-file templates.
- `intent` is not the name of any spec file in any built-in
  template, and a custom template SHOULD NOT use it as a filename.
  The term is reserved for inputs feeding into specification
  revision: seeds, requests, critiques, external requirements,
  observations, and implementation feedback.
- Every normative heading in any spec file MUST be uniquely named
  within that file.
- When a heading is renamed, the same `revise` MUST update every
  reference to it. Doctor MUST detect dangling references in its
  static phase.

### `livespec` template specifics (default template only)

These apply only when `template` is `livespec` (the default). A
different template MAY revise any of the rules in this subsection.

- The specification is represented as multiple files to create
  explicit boundaries for LLMs and tools.
- `spec.md` is the primary source surface of the living
  specification.
- `contracts.md`, `constraints.md`, and `scenarios.md` are
  specialized operational partitions of the same specification.
- The split is intentional because those partitions can be
  processed with lower nondeterminism and stronger checking than
  the general spec surface.
- `scenarios.md` is intentionally isolated so it can support
  holdout scenario usage in the StrongDM Dark Factory style.
  (Forward-looking rationale only; livespec v1 defines no holdout
  mechanism — that is an external evaluation system's concern.)
- Scenario examples and acceptance criteria in `scenarios.md` MUST
  use the standard Gherkin keywords `Scenario:`, `Given`, `When`,
  `Then`, `And`, and `But`. Each keyword line MUST be separated
  from adjacent content by a blank line above and below, so that
  every step renders as its own Markdown paragraph. Fenced code
  blocks MUST NOT be used: the `gherkin` info-string is not part of
  GFM or GLFM and renders inconsistently. No specific Gherkin
  runner is pinned; the contract is rendering predictability.
  Doctor enforces this format statically when the active template
  is `livespec` (see check #11 below).
- Cross-file references between partitions MUST use the
  GitHub-flavored anchor form
  `[link text](contracts.md#section-name)`. (The template-agnostic
  renamed-heading rule above ensures these don't silently rot.)

---

## SPECIFICATION directory structure

The default (`livespec`) template produces:

```
<project-root>/
├── .livespec.jsonc                    (optional config; created by seed if absent)
└── SPECIFICATION/
    ├── README.md                      (overview of the SPECIFICATION; auto-generated)
    ├── spec.md
    ├── contracts.md
    ├── constraints.md
    ├── scenarios.md
    ├── proposed_changes/
    │   ├── README.md                  (purpose + naming convention; auto-generated)
    │   └── vNNN-proposed-change-<topic>.md   (zero or more in-flight proposals; NNN = latest_history_version + 1)
    └── history/
        ├── README.md                  (purpose + naming convention; auto-generated)
        └── vNNN/                      (one directory per version)
            ├── vNNN-spec.md
            ├── vNNN-contracts.md
            ├── vNNN-constraints.md
            ├── vNNN-scenarios.md
            ├── vNNN-proposed-change-<topic>.md           (one per accepted/modified/rejected proposal in this revise)
            └── vNNN-proposed-change-<topic>-acknowledgement.md
```

Notes:

- Historic version files MUST be prefixed with `vNNN-` to prevent
  them from being mistaken for current spec content by humans or
  LLMs.
- The working `proposed_changes/` directory MUST be empty after a
  successful `revise` (every proposal is moved to the new history
  version, regardless of accept/reject outcome).
- Auto-generated `README.md` files have a fixed content contract: a
  one-paragraph description of the directory's purpose, the filename
  convention used in that directory, and a pointer back to
  `SPECIFICATION/README.md`. Their content is regenerated on every
  `revise` and on `seed`; humans SHOULD NOT edit them.

---

## Configuration: `.livespec.jsonc`

`.livespec.jsonc` lives at the project root. It is OPTIONAL.

### Schema

```jsonc
{
  // Path to the SPECIFICATION directory, relative to project root.
  // Default: "SPECIFICATION"
  "specification_dir": "SPECIFICATION",

  // Active template. Built-in values: "livespec", "openspec".
  // Any other value is treated as a path (relative to project root)
  // to a custom template directory.
  // Default: "livespec"
  "template": "livespec",

  // Optional path (relative to project root) to a custom critique
  // prompt that overrides the active template's default critique
  // prompt. Null disables override.
  // Default: null
  "custom_critique_prompt": null
}
```

The skill MUST validate `.livespec.jsonc` against this schema on every
read and every write. Validation failure is a doctor static-phase
hard fail.

### Absence behavior

- If `.livespec.jsonc` is missing, the skill MUST behave as if it
  contained the schema defaults above.
- `seed` MUST create `.livespec.jsonc` with explicit defaults, so
  that a project's configuration is always discoverable on disk after
  the first seed.
- `doctor` MUST NOT fail when `.livespec.jsonc` is missing; it MUST
  fail when present and malformed.

### Multi-specification per project

Out of scope for v1. The `specification_dir` field is a single string
in v1 to avoid baking in a model that v2 may need to revise.

---

## Versioning

- Versions are integer-numbered, zero-padded to three digits as
  `vNNN`. Numbers MUST be monotonic and contiguous (no gaps); width
  MAY grow beyond three digits as needed.
- The current working spec content lives in `SPECIFICATION/spec.md`
  (and partition files). The working files MUST NOT carry a `vNNN-`
  prefix; only the copies in `history/vNNN/` do.
- A new version is cut when, and only when, `revise` either accepts
  or modifies at least one proposal, OR processes non-empty freeform
  intent text that results in modifications to the specification. A
  `revise` invocation that finds no proposals, and whose freeform
  text (if any) produces no spec modifications, MUST be a no-op and
  MUST NOT bump the version.
- A `revise` invocation that processes proposals but rejects all of
  them MUST cut a new version. The version's spec partition files
  are byte-identical copies of the prior version's spec partition
  files; the version's history directory contains the proposed-change
  files and rejection acknowledgements. This preserves the audit
  trail for every proposal that ever reached `revise`.
- `seed` creates `v001` directly: it writes both the working spec
  files and `history/v001/` with the same content.

---

## Built-in templates

### `livespec` (default, fully specified)

This is the template described under "SPECIFICATION directory
structure" above. It is the only built-in template that is fully
specified for v1.

The `livespec` template's seed-time content for each file:

- `spec.md`: a stub containing top-level headings derived from the
  seed input (one heading per major topic identified by the LLM),
  each with a one-sentence description placeholder. The stub MUST
  include a "Definition of Done" heading at the bottom, even if
  initially empty.
- `contracts.md`: header and a placeholder section for the first
  contract.
- `constraints.md`: header and a placeholder section.
- `scenarios.md`: header, an explanatory paragraph about the
  blank-line-separated Gherkin step convention (no fenced code
  blocks), and one placeholder `Scenario:` followed by placeholder
  `Given` / `When` / `Then` steps, each separated by blank lines.
- `README.md`: an overview that lists the partition files, their
  purpose, the BCP 14 convention, and the Gherkin convention.

The default critique prompt for the `livespec` template is bundled
inside the skill and applies the embedded NLSpec guidelines to the
current spec.

### `openspec` (sketch only)

The `openspec` value selects an OpenSpec-compatible on-disk layout.
For v1 only the value is reserved and a sketch is provided; full
specification is deferred. Implementations of the `openspec`
template MUST still respect the `livespec` lifecycle:
`proposed_changes/` and `history/` semantics are governance concerns
and apply across templates.

### Custom templates

Any `template` value other than `livespec` or `openspec` is treated
as a path to a custom template directory. The on-disk format of a
custom template — what files it contains, how they are loaded, how
its critique prompt is provided — is **deferred to v2**. In v1,
setting a custom template path is rejected: doctor's static phase
fails (check #13) when `.livespec.jsonc` configures one.

---

## `livespec` skill sub-commands

Every sub-command MUST run `doctor`'s static phase as its first step
(the LLM-driven phase is run only by `doctor` itself). If the static
phase exits nonzero, the sub-command MUST abort with the doctor
output. Exceptions: `help` and `doctor` itself.

After `seed`, `propose-change`, `critique`, and `revise` complete
successfully, they MUST run the full `doctor` (both phases) as a
post-step. Doctor's post-step output is reported to the user but does
not retroactively undo the sub-command's effects.

### `help`

- `help` shows usage and the sub-command list.
- `help <sub-command>` shows help for that sub-command.
- MUST NOT run `doctor`.

### `seed <freeform text>`

- With no args, prompts the user for a seed. The seed is freeform
  text and MAY include references to existing specifications,
  examples, projects, or other context.
- Creates `.livespec.jsonc` with defaults if absent.
- Creates the `SPECIFICATION/` directory and all template-required
  files using the active template's seed-time content contract (see
  "Built-in templates" above).
- Creates `history/v001/` containing byte-identical copies of the
  initial spec partition files, with `v001-` prefixes.
- Idempotency: if `SPECIFICATION/` already exists, `seed` MUST
  refuse and direct the user to `propose-change` or `critique`
  instead.

### `propose-change <topic> <freeform text>`

- Creates a new file
  `SPECIFICATION/proposed_changes/vNNN-proposed-change-<topic>.md`,
  where `NNN` is the latest version present in `history/` plus one.
  Because `revise` MUST process every in-flight proposal before a
  new version can be cut, this prefix is unambiguous at the moment
  of `propose-change`.
- If a file with the same name already exists, `propose-change`
  MUST confirm with the user before overwriting.
- The proposed-change file MUST conform to the format defined in
  "Proposed-change file format" below.
- A proposal MAY include an inline diff against the latest spec
  version, to make targeted and deterministic edits. Diff format is
  unified diff (`---`/`+++`/`@@`).
- At `revise` time, the file is moved into `history/vNNN/`
  unchanged (the prefix already matches the version it targeted).

### `critique <author>`

- `<author>` defaults to a string identifying the current LLM
  context, derived from the host's available metadata. If no
  identifier is available, the literal `unknown-llm` MUST be used
  and a warning surfaced.
- Generates a critique of the current spec using the active
  template's critique prompt (resolved in this order:
  `.livespec.jsonc.custom_critique_prompt` → template default →
  built-in default).
- `critique` MUST then call the `propose-change` sub-command with
  topic `<author>-critique` and the critique content, so that the
  change proposal is created (or updated) through the single
  proposal-creation path. There is no separate write path from
  `critique` into `proposed_changes/`.
- If a proposal or history entry with topic `<author>-critique`
  already exists for the current target version, `critique` MUST
  generate a unique `<author>` value (e.g., by appending a short
  disambiguator) and proceed. Conflicts are expected to be rare,
  so the default-case topic is just `<author>-critique` with no
  suffix — disambiguation only kicks in on actual collision.
- Does not run `revise`; the user reviews and runs `revise` to
  process.

### `revise <freeform text>`

- For each file in `proposed_changes/`, the LLM proposes an
  acceptance decision: `accept`, `modify`, or `reject`, with
  rationale.
- The user MUST be presented with the per-proposal decisions and MUST
  confirm or override before any history is written. This is the
  human-in-the-loop confirmation step.
- Optional `<freeform text>` is treated as an additional intent
  input applied alongside (not overriding) the per-proposal
  decisions. Use cases include "and also tighten the timeout
  default to 5s" or "reject anything touching the auth section".
- On user confirmation:
  - If any decision is `accept` or `modify`, OR if non-empty
    freeform text is processed that would result in modifications
    to the specification, a new version is cut (see "Versioning").
  - The current spec partition files are updated in place.
  - `history/vNNN/` is created with `vNNN-`-prefixed copies of the
    new spec partition files.
  - Each processed proposal is moved into `history/vNNN/` as
    `vNNN-proposed-change-<topic>.md`.
  - Each processed proposal gets an acknowledgement at
    `history/vNNN/vNNN-proposed-change-<topic>-acknowledgement.md`,
    conforming to the format defined in "Acknowledgement file
    format" below.
- After successful completion, `proposed_changes/` MUST be empty.

### `doctor`

`doctor` runs in two phases. The static phase is a code script. The
LLM-driven phase runs only after the static phase passes.

**Static phase (exits nonzero on failure):**

1. `.livespec.jsonc`, if present, validates against the schema.
2. The configured `specification_dir` exists.
3. All template-required files are present in
   `<specification_dir>/`.
4. `proposed_changes/` and `history/` directories exist and contain
   the auto-generated `README.md`.
5. Every `history/vNNN/` directory contains the full set of template-
   required files, each prefixed with `vNNN-`.
6. Version numbers in `history/` are contiguous from `v001` upward.
7. Every acknowledgement file in `history/vNNN/` has a corresponding
   `vNNN-proposed-change-<topic>.md` in the same version.
8. Every file in `proposed_changes/` follows the
   `vNNN-proposed-change-<topic>.md` naming convention, and `NNN`
   equals `latest_history_version + 1`.
9. The diff between current spec partition files and the latest
   `history/vNNN/vNNN-*` files is empty. If non-empty, doctor SHOULD
   prompt the user to auto-create a
   `vNNN-proposed-change-out-of-band-edit-<timestamp>.md` proposed
   change (with `NNN` = `latest_history_version + 1`) containing the
   diff and a one-line summary.
10. BCP 14 keyword usage is well-formed in `spec.md`,
    `contracts.md`, and `constraints.md` (no lowercase `must`/
    `should`/etc. used as a normative term outside code blocks; no
    misspellings of the canonical keywords).
11. **(Conditional: only when the active template is `livespec`.)**
    In `scenarios.md`, every line whose first non-whitespace token
    is a Gherkin keyword (`Scenario:`, `Given`, `When`, `Then`,
    `And`, `But`) MUST be preceded and followed by a blank line, so
    each step renders as its own Markdown paragraph. Fenced code
    blocks tagged ` ```gherkin ` (or any other info-string wrapping
    Gherkin steps) MUST NOT be present. Doctor MUST flag any
    Gherkin keyword line that violates the spacing rule, and any
    fenced code block whose content begins with a Gherkin keyword.
12. All Markdown anchor references between partition files resolve
    to existing headings.
13. The `template` field in `.livespec.jsonc` MUST be one of the
    built-in values (`livespec` or `openspec`). Any other value
    (i.e., a path to a custom template directory) is a static
    failure, because custom-template loading is a v1 non-goal. The
    failure message MUST name the offending field, its value, and
    the path to `.livespec.jsonc`.

**Static-phase exit codes:**

- `0`: all checks pass; LLM-driven phase MAY proceed.
- `1`: at least one check failed; LLM-driven phase MUST NOT run; the
  invoking sub-command MUST abort.

Static checks are pass-or-fail only. There is no warning tier in the
static phase: every static check has been chosen to be deterministic
enough that "almost passing" is not a meaningful state. Anything that
would otherwise be a warning belongs in the LLM-driven phase.

**LLM-driven phase:**

The LLM-driven phase is skill behavior, not a script. It has no exit
codes and no pass/fail tier — those concepts only apply to the
static phase. The skill performs the checks below in-context. For
any finding it surfaces, it prompts the user with a description of
the finding and asks whether to address it via a `critique` call.
The user MAY accept (which invokes `critique`), defer, or dismiss
each finding individually.

Checks performed:

- **NLSpec conformance check:** evaluates each spec partition
  against the embedded `livespec-nlspec-spec.md` per the
  progressive-disclosure mapping below.
- **Template compliance (semantic):** checks that each partition
  contains the kinds of content the active template expects (e.g.,
  contracts in `contracts.md`, not in `spec.md`).
- **Drift checks (three kinds):**
  - *Spec ↔ implementation drift:* compares spec content to the
    surrounding repo's source code. Surfaces requirements the code
    doesn't satisfy and code behavior the spec doesn't describe.
  - *Spec ↔ history drift:* compares the latest history version's
    content to the working spec content (semantic, not byte-level
    — the byte-level check is in the static phase).
  - *Internal self-consistency:* checks for contradictions across
    partition files, per the embedded guidelines' insistence on
    self-consistency.

Because the LLM-driven phase relies on LLM judgment, it MAY produce
non-deterministic findings and the resulting prompts MAY be blocking
or effectively unresolvable (e.g., the LLM repeatedly raises a
finding the user does not consider valid). This is accepted for v1
as a deliberate trade for richer semantic checking; structured
remediation paths (suppression files, finding allow-lists,
reproducibility guarantees) are deferred to a later version.

---

## Proposed-change file format

A `vNNN-proposed-change-<topic>.md` MUST contain, in order:

1. YAML front-matter:
   ```yaml
   ---
   topic: <kebab-case-topic>
   author: <author-id>            # LLM identifier or human handle
   created_at: <UTC ISO-8601>
   target_partitions:             # which spec files this proposal touches
     - spec.md
     - contracts.md
   ---
   ```
2. `## Summary` — one paragraph stating what changes and why.
3. `## Motivation` — the intent input that produced this proposal
   (which observation, critique, requirement, or feedback).
4. `## Proposed Changes` — either prose describing the changes per
   partition, or a unified diff in fenced ` ```diff ` blocks, or
   both.

A proposed change MUST be explicit about the intent it specifies. It
MUST NOT defer sub-decisions to `revise`; `revise`'s only choice is
accept / modify / reject on the proposal as written. Open questions,
alternatives, and "we should decide X later" content do NOT belong
in a proposed change. If those exist, resolve them before filing, or
file a separate `critique` to surface them.

Doctor MUST validate the front-matter and the presence of the
required headings.

---

## Acknowledgement file format

Each `vNNN-proposed-change-<topic>-acknowledgement.md` MUST contain,
in order:

1. YAML front-matter:
   ```yaml
   ---
   proposal: vNNN-proposed-change-<topic>.md
   decision: accept | modify | reject
   revised_at: <UTC ISO-8601>
   reviser: <author-id>           # whoever ran `revise`
   ---
   ```
2. `## Decision and Rationale` — one paragraph explaining the
   decision.
3. `## Modifications` (REQUIRED when `decision: modify`) — describes
   how the proposal was changed before incorporation.
4. `## Resulting Changes` (REQUIRED when `decision: accept` or
   `modify`) — names the spec partitions modified and lists the
   sections changed.
5. `## Rejection Notes` (REQUIRED when `decision: reject`) — explains
   what would need to change about the proposal for it to be
   acceptable in a future revision.

---

## NLSpec conformance

- The skill enforces conformance with the embedded NLSpec guidelines
  (`livespec-nlspec-spec.md`).
- The full guidelines document is in context for every sub-command
  that does any spec authoring, evaluation, or revision work
  (`seed`, `propose-change`, `critique`, `revise`, `doctor`'s
  LLM-driven phase). At ~40 KB it is cheap enough to load
  unconditionally; partitioning it for selective load is not a v1
  concern.
- The embedded guidelines file is the single source of truth for
  the adaptation diff against upstream NLSpec; this proposal does
  not restate that diff.

---

## Testing approach

- Tests live in `<project-root>/tests/`. Implementation language is
  not pinned by this proposal.
- A `tests/CLAUDE.md` MUST exist to enforce consistency between tests
  and the actual specification (instructing the LLM that test
  coverage tracks spec partitions, not implementation files).
- Tests MUST be split into separate files per spec partition:
  `test_spec.*`, `test_contracts.*`, `test_constraints.*`,
  `test_scenarios.*`.
- Each test MUST execute the skill against fixtures in a throwaway
  temporary directory and compare results to expected outputs. The
  test runner MUST NOT mutate the project's own `SPECIFICATION/`.
- A meta-test, `test_meta_section_drift_prevention.*`, MUST verify
  that every top-level (`##`) heading in each spec partition file
  has at least one corresponding test case that references that
  heading by name. The reference is by exact heading text. New
  headings without tests fail the meta-test.

---

## Definition of Done (v1)

`livespec` v1 is complete when all of the following are true:

1. All sub-commands implemented and exposed via the skill entry
   point: `help`, `seed`, `propose-change`, `critique`, `revise`,
   `doctor`.
2. The `livespec` built-in template is fully implemented and
   produces a complete `SPECIFICATION/` from `seed`.
3. The `openspec` template value is reserved (selecting it produces
   a clear "not yet implemented" message).
4. `.livespec.jsonc` schema validation is implemented.
5. The full `doctor` static-check suite (13 checks above) is
   implemented with the documented exit-code semantics.
6. The four LLM-driven `doctor` check categories are implemented and
   produce findings with optional critique offers.
7. Every sub-command that does spec work loads `livespec-nlspec-
   spec.md` and applies its conformance criteria.
8. The proposed-change and acknowledgement file formats are enforced
   by `doctor`'s static phase.
9. The test suite covers each sub-command, both `doctor` phases, and
   the meta `section_drift_prevention` test.
10. `livespec` dogfoods itself: `<project-root>/SPECIFICATION/`
    exists, was generated by `livespec seed`, has been at least
    once revised through `propose-change` + `revise`, and passes
    `livespec doctor` cleanly.
11. The skill bundle includes its own `help` text covering every
    sub-command.

---

## v1 non-goals (stated explicitly)

The following are intentionally out of scope for v1. The proposal
calls them out so their absence is recognized as a deliberate
boundary, not an accidental gap.

- **Subdomain ownership and cross-cutting routing.** As argued in
  `subdomains-and-unsolved-routing.md`, no public consensus exists.
  Templates and prompt conventions handle this; `livespec` does not.
- **The pluggable template mechanism.** A template value pointing at
  a custom directory is configurable but not loadable in v1; doctor
  warns when one is set.
- **Multi-specification per project.** `specification_dir` is a
  single string in v1.
- **Git integration.** `livespec` writes files; the user's git
  workflow is entirely external.
- **OpenSpec template implementation.** Reserved value only.

---

## Self-application

`livespec` MUST be developed by dogfooding itself. The bootstrap
order is:

1. Author this proposal, `PROPOSAL.md`, to a state that passes the
   recreatability test against `livespec-nlspec-spec.md`.
2. Implement the minimal `seed` sub-command sufficient to consume
   this proposal as the seed input.
3. Run `livespec seed` against this project, producing
   `<project-root>/SPECIFICATION/`.
4. Implement remaining sub-commands, using `propose-change` /
   `revise` cycles against the seeded spec.
5. Land the v1 Definition of Done items above as the spec evolves.

Items in step (1) that this revised proposal does not yet resolve
become the first batch of `propose-change` filings after step (3).
