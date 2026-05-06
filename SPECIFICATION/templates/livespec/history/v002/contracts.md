# Contracts — `livespec` template

This sub-spec's contracts file enumerates the template-internal JSON contracts plus the per-prompt semantic-property catalogue. Contracts are wire-level; the catalogue is the testable-property surface that the v018 Q5 prompt-QA harness exercises.

## Template-internal JSON contracts

The `livespec` template's prompts populate the following payload fields:

- `prompts/seed.md` populates `seed_input.schema.json`'s `template`, `intent`, `files[]`, and `sub_specs[]` fields. The `template` field MUST equal the literal string the user chose in the pre-seed dialogue (e.g., `"livespec"`). The `intent` field MUST carry the verbatim free-text intent. The `files[]` array MUST contain one entry per template-declared spec-file path. The `sub_specs[]` array MUST be empty on "no" to the v020 Q2 question and MUST carry one `SubSpecPayload` entry per named template on "yes".
- `prompts/critique.md` populates `proposal_findings.schema.json`'s `findings[]` array. Each finding MUST carry `name`, `target_spec_files`, `summary`, `motivation`, and `proposed_changes` fields per the field-copy mapping at PROPOSAL.md lines 2232-2242.

The `prompts/propose-change.md` and `prompts/revise.md` prompts each consume a paired payload schema (`proposal_findings.schema.json` and `revise_input.schema.json` respectively). The schemas MUST stay co-authoritative with their dataclass pairs under `livespec/schemas/dataclasses/`.

## Per-prompt semantic-property catalogue

This catalogue enumerates the testable semantic properties for each REQUIRED prompt in the `livespec` template. Phase 6 lands bootstrap-minimum (1-2 properties per prompt); Phase 7's first propose-change against this sub-spec widens the catalogue to the full assertion surface that the v018 Q5 prompt-QA harness asserts against.

### `prompts/seed.md`

- The prompt MUST derive top-level `#` headings within each spec file from intent nouns, NOT from a fixed taxonomy. (Asserts the v020 Q4 starter-content policy; aligns with SPECIFICATION/constraints.md §"Heading taxonomy" line 47 which pins intent-derivation to level 1.)
- The prompt MUST ask the v020 Q2 sub-spec-emission question and route emission by the user's answer — `sub_specs: []` on "no", one `SubSpecPayload` per named template on "yes".

### `prompts/propose-change.md`

- The prompt MUST elicit per-finding `target_spec_files` referencing the spec-file paths under the `--spec-target` tree. Findings whose `target_spec_files` reference paths outside `--spec-target` are malformed.
- The prompt SHOULD apply BCP14 normative language (`MUST`, `SHOULD`, `MAY`) in the `proposed_changes` prose so the resulting propose-change file flows into the spec under the same discipline.

### `prompts/revise.md`

- The prompt MUST walk every pending proposed-change file under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`) before composing the revise-input JSON. Skipping a pending proposal is a silent-data-loss bug; the v018 Q5 harness MUST detect missing per-proposal entries.
- The prompt MUST emit a per-proposal disposition (`accept` or `reject`) with a one-line rationale per disposition.

### `prompts/critique.md`

- The prompt MUST ground each finding against the spec target's current state. Critique findings MUST carry `target_spec_files` referencing files that exist in the target tree.
- The prompt SHOULD prioritize ambiguities and contradictions over wording-style suggestions; the latter belong in a separate cleanup-style propose-change cycle.

## Doctor-LLM-subjective-checks prompt

The `template.json` `doctor_llm_subjective_checks_prompt: "prompts/doctor-llm-subjective-checks.md"` field declares the prompt the doctor LLM-driven subjective phase invokes. The prompt MUST emit `doctor_findings.schema.json`-conforming output. Phase 7 brings this prompt to operability; Phase 6's bootstrap-minimum stub at `prompts/doctor-llm-subjective-checks.md` documents the contract without implementing the full subjective check logic.
