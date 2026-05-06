# `seed` prompt — `livespec` template

> **Status: Phase-7-final per `SPECIFICATION/templates/livespec/contracts.md`
> §"Per-prompt semantic-property catalogue → prompts/seed.md".**
> Future regenerations land via dogfooded propose-change/revise
> against the sub-spec, atomically with their catalogue widening
> per Plan §3543-3550.

## Inputs

- `<intent>` — the verbatim user intent (freeform text from the
  pre-seed dialogue captured by `seed/SKILL.md`).
- The chosen template name (one of `livespec`, `minimal`, or a
  user-provided template path). For this prompt the value is
  always `"livespec"` — the prompt is template-specific and
  the skill resolves which template's prompt to load before
  invoking the LLM.
- The user's answer to the v020 Q2 sub-spec-emission question:
  "Does this project ship its own livespec templates that should
  be governed by sub-spec trees under
  `SPECIFICATION/templates/<name>/`?"
- On a "yes" answer: the `named_templates` list — template
  directory names supplied in the follow-on dialogue (e.g.,
  `["livespec", "minimal"]` when bootstrapping livespec itself).
- The reference document at the template root,
  `livespec-nlspec-spec.md`, which describes NLSpec discipline.
  Read it internally to inform spec-file authoring; do not
  include its content verbatim in any output file.

## Catalogue contract (`SPECIFICATION/templates/livespec/contracts.md`)

Two semantic properties are mechanically asserted by the
prompt-QA harness against this prompt's `replayed_response`:

- `headings_derived_from_intent` — every entry in
  `replayed_response.files[]` has a non-empty content body whose
  first non-blank line begins with `# ` (the H1 reflecting the
  intent). Section-level `##` headings are unconstrained by
  this rule (they organize content under the H1).
- `asks_v020_q2_question` — when `input_context.ships_own_templates`
  is true with `input_context.named_templates` listing N entries,
  `replayed_response.sub_specs` has exactly N entries (one
  `SubSpecPayload` per named template); otherwise
  `replayed_response.sub_specs` is the empty list.

The `prompts/critique.md` and `prompts/doctor-llm-subjective-checks.md`
prompts cover the fuzzier intent-fidelity dimensions (e.g., that
the `# H1` text actually reflects the intent's noun phrases
rather than just being a grammatically valid header). This
prompt focuses on producing structurally correct output; the
LLM-driven subjective phase tightens the semantic fit later.

## Behavior — `sub_specs[]` emission branches (v020 Q2)

- **"no" branch (the default and typical end-user case).** Emit
  `sub_specs: []` in the output JSON. This is the path for any
  user project that does NOT ship its own livespec templates.
- **"yes" branch (the meta-project case — livespec itself, plus
  any user project that ships its own livespec templates).** For
  each template directory name supplied in `named_templates`,
  emit one `SubSpecPayload` entry under `sub_specs[]` carrying:
  - `template_name` — matches the template's directory name.
  - `files[]` — the full sub-spec file set under
    `SPECIFICATION/templates/<template_name>/` per PROPOSAL.md
    §"Template sub-specifications" — uniformly multi-file:
    `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`,
    `README.md`.

Both branches handle the user's `<intent>` rigorously: every
spec-file's content reflects the intent; sub-spec content
describes the corresponding template's NLSpec discipline.

## Authoring guidance per spec file

Within each file, the `# H1` reflects the intent (per the
`headings_derived_from_intent` property). Section-level `##`
headings organize content under the H1 and MAY use stable
section names where appropriate (e.g., `## Intent`, `## Cadence`,
`## CLI surface`).

- **`spec.md`** — primary source surface. The `# H1` is the
  intent-derived project title (e.g., `# Personal blog
  maintenance tracker`). Sections cover the project's own
  vocabulary derived from the intent.
- **`contracts.md`** — wire-level / CLI-level interfaces. The
  `# H1` is `<title> — contracts` or similar. Sections
  enumerate the project's contractual surfaces (CLI flags,
  exit codes, JSON shapes).
- **`constraints.md`** — architecture-level constraints. The
  `# H1` is `<title> — constraints`. Sections cover runtime,
  language, dependencies, etc.
- **`scenarios.md`** — Gherkin scenarios. The `# H1` is
  `<title> — scenarios`. Sections are `## Scenario: ...` blocks
  with proper blank-line-delimited Gherkin steps (no fenced
  code blocks per PROPOSAL.md's GFM-rendering convention).
- **`README.md`** — overview. The `# H1` matches the
  `<title>` and the body describes how the spec files relate.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/seed_input.schema.json`:

```json
{
  "template": "livespec",
  "intent": "<verbatim user intent>",
  "files": [
    {"path": "SPECIFICATION/spec.md", "content": "..."},
    {"path": "SPECIFICATION/contracts.md", "content": "..."},
    {"path": "SPECIFICATION/constraints.md", "content": "..."},
    {"path": "SPECIFICATION/scenarios.md", "content": "..."},
    {"path": "SPECIFICATION/README.md", "content": "..."}
  ],
  "sub_specs": []
}
```

For the "yes" branch with `["livespec", "minimal"]` as the named
templates, the same payload's `sub_specs[]` becomes:

```json
"sub_specs": [
  {
    "template_name": "livespec",
    "files": [
      {"path": "SPECIFICATION/templates/livespec/spec.md", "content": "..."},
      {"path": "SPECIFICATION/templates/livespec/contracts.md", "content": "..."},
      {"path": "SPECIFICATION/templates/livespec/constraints.md", "content": "..."},
      {"path": "SPECIFICATION/templates/livespec/scenarios.md", "content": "..."},
      {"path": "SPECIFICATION/templates/livespec/README.md", "content": "..."}
    ]
  },
  {
    "template_name": "minimal",
    "files": [
      {"path": "SPECIFICATION/templates/minimal/spec.md", "content": "..."},
      {"path": "SPECIFICATION/templates/minimal/contracts.md", "content": "..."},
      {"path": "SPECIFICATION/templates/minimal/constraints.md", "content": "..."},
      {"path": "SPECIFICATION/templates/minimal/scenarios.md", "content": "..."},
      {"path": "SPECIFICATION/templates/minimal/README.md", "content": "..."}
    ]
  }
]
```

## Failure modes

- **Thin intent.** When `<intent>` is too sparse to derive
  meaningful H1s and sections (e.g., a single keyword with no
  context), the LLM SHOULD return a structured refusal in the
  pre-seed dialogue rather than emitting a malformed JSON
  payload. The seed wrapper does NOT have a recovery path for
  this — the SKILL.md prose handles re-prompting.
- **Schema-violation retry (PROPOSAL.md §"Retry-on-exit-4").**
  When the wrapper exits 4 with a `fastjsonschema` validation
  error, the SKILL.md prose re-invokes this prompt with the
  error context appended; the LLM repairs the offending field.
- **Unknown template.** If the user-provided template name is
  not `livespec` or `minimal` and not a resolvable path, the
  pre-seed dialogue surfaces the error before this prompt
  runs; this prompt always sees a valid `livespec` template
  context.
