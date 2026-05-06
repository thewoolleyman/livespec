# Contracts — `minimal` template

This sub-spec's contracts enumerate the template-internal JSON contracts plus the per-prompt semantic-property catalogue, scoped to the `minimal` template's reduced prompt surface.

## Delimiter-comment format

The `minimal` template's single-file `SPECIFICATION.md` end-user output uses HTML-comment delimiter markers to define named regions that propose-change/revise cycles can target precisely.

### Concrete syntax

- **Open marker**: `<!-- region:<name> -->` on its own line.
- **Close marker**: `<!-- /region:<name> -->` on its own line.
- **Regex pin** (for parsers that need it): `<!--\s*(?:/)?region:([a-z0-9-]+)\s*-->` — the optional `/` distinguishes close from open; the captured group is the region name.

### Invariants

- Markers MUST be HTML comments so they are invisible in rendered Markdown.
- Each region MUST have a paired open + close marker carrying the same region name.
- Region names MUST be kebab-case alphanumeric (`[a-z0-9-]+`) — matches the propose-change topic-format constraint so a region's name MAY directly mirror the topic that landed it.
- Nested regions MUST NOT cross boundaries (well-formed open/close balance). A `region:foo` open MUST be closed before any enclosing `region:<other>` close.
- Markers MUST appear on their own line (no inline text on the same line) to keep the parser regex single-line and to keep rendered Markdown clean.

### Worked example

```markdown
# `<title>`

<!-- region:project-intent -->

The project ...

<!-- /region:project-intent -->

<!-- region:cadence -->

The maintainer MUST review issues at least once per month.

<!-- /region:cadence -->
```

A propose-change targeting the `cadence` region replaces the body between `<!-- region:cadence -->` and `<!-- /region:cadence -->`; the rest of `SPECIFICATION.md` is byte-identical.

### Consumers

The `minimal` template's `prompts/propose-change.md` and `prompts/revise.md` reference this format when emitting region-targeted edits. The Phase 9 `tests/e2e/fake_claude.py` mock harness parses against this same format. Future custom-template authors MAY adopt the same format unchanged or define their own; the format is not livespec-wide policy.

## Template-internal JSON contracts

The `minimal` template's prompts populate the following payload fields:

- `prompts/seed.md` populates `seed_input.schema.json`'s `template`, `intent`, `files[]`, and `sub_specs[]` fields. The `template` field MUST equal `"minimal"`. The `files[]` array MUST contain exactly one entry with path `"SPECIFICATION.md"` (per the template's `spec_root: "./"` plus single-file positioning). The `sub_specs[]` field MUST be the empty list `[]` regardless of any user input — the `minimal` template does NOT implement v020 Q2 sub-spec emission.

The other REQUIRED prompts (`propose-change`, `critique`, `revise`) consume and emit the same payload schemas as the `livespec` template's corresponding prompts. Bootstrap-minimum scope at Phase 6: stubs with the v014-N9-style placeholder shape; Phase 7 widens to full operational prompts.

## Per-prompt semantic-property catalogue

This catalogue enumerates the testable semantic properties for the `minimal` template's REQUIRED prompts. Phase 6 lands bootstrap-minimum (1-2 properties per prompt); Phase 7 widens.

### `prompts/seed.md`

- `sub_specs_always_empty` — the prompt MUST emit `sub_specs: []` regardless of any pre-seed dialogue input. Asserts the v020 Q2 opt-out for the `minimal` template. **Assertion function**: `replayed_response.sub_specs` is the empty list, regardless of `input_context.ships_own_templates` or `input_context.named_templates`.
- `single_specification_md_file` — the prompt MUST emit a single `files[]` entry whose path is `SPECIFICATION.md` per the template's `spec_root: "./"` + single-file positioning. **Assertion function**: `replayed_response.files[]` has exactly one entry whose `path` field equals `"SPECIFICATION.md"`.
- **Assertion-function contract.** Same shape as the livespec-template catalogue contracts (sub-spec v003+): each property's assertion function lives in `tests/prompts/minimal/_assertions.py` keyed by the property's string name in the `ASSERTIONS` dict, accepts keyword-only `*, replayed_response: object, input_context: object`, and raises `AssertionError` on violation.
- **Catalogue widening rule.** Same shape as the livespec-template rule.

### `prompts/propose-change.md`

- `target_is_single_specification_md` — the prompt MUST emit per-finding `target_spec_files` containing exactly `["SPECIFICATION.md"]` (the minimal template's single-file output). **Assertion function**: every entry in `replayed_response.findings[]`'s `target_spec_files` array equals exactly `["SPECIFICATION.md"]` (length 1, single element matching the literal string).
- `bcp14_in_proposed_changes` — the prompt SHOULD apply BCP14 normative language (`MUST`, `SHOULD`, `MAY`, `MUST NOT`, `SHOULD NOT`, `MAY NOT`) in the `proposed_changes` prose so the resulting propose-change file flows into the spec under the same discipline. **Assertion function**: every entry in `replayed_response.findings[]`'s `proposed_changes` string contains at least one BCP14 keyword (whole-word match, uppercase).
- **Assertion-function contract.** Same shape as the livespec-template catalogue contracts.
- **Catalogue widening rule.** Same shape as the livespec-template rule.

### `prompts/revise.md`

- `walks_every_pending_proposal` — the prompt MUST walk every pending proposed-change file under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`) before composing the revise-input JSON. Skipping a pending proposal is a silent-data-loss bug. **Assertion function**: the set of topic-stems extracted from `input_context.pending_proposals[]` is a subset of `replayed_response.decisions[].proposal_topic`'s set. Same assertion shape as the livespec-template `walks_every_pending_proposal` property; per-template `_assertions.py` registries hold independent function definitions (with identical behavior) per the v014 fixture-pattern.
- `per_proposal_disposition_with_rationale` — the prompt MUST emit a per-proposal disposition (`accept`, `reject`, or `modify`) with a non-empty rationale per disposition. **Assertion function**: every entry in `replayed_response.decisions[]` has a `decision` field in `{"accept", "modify", "reject"}` AND a non-empty whitespace-stripped `rationale` field.
- **Assertion-function contract** + **Catalogue widening rule.** Same shape as the livespec-template catalogue contracts.

### `prompts/critique.md`

Bootstrap-minimum at Phase 6 (continued): the prompt's catalogue is a single placeholder property — "the prompt MUST emit valid `<schema>`-conforming JSON when given a well-formed user-described change". Phase 7 sub-step (d).5 widens this subsection independently per the in-line widening rule.

## Doctor-LLM-driven phase opt-out

The `minimal` template's `template.json` declares `doctor_llm_objective_checks_prompt: null` and `doctor_llm_subjective_checks_prompt: null`. The doctor wrapper MUST recognize these null values and skip the LLM-driven phases for `minimal`-rooted projects. Only the static phase runs.

This opt-out is intentional: the `minimal` template optimizes for the simplest spec lifecycle. Projects that want LLM-driven doctor phases SHOULD use the `livespec` template instead, OR ship their own custom template with the prompt fields populated.
