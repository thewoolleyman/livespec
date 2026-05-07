# Contracts — `livespec` template

This sub-spec's contracts file enumerates the template-internal JSON contracts plus the per-prompt semantic-property catalogue. Contracts are wire-level; the catalogue is the testable-property surface that the v018 Q5 prompt-QA harness exercises.

## Template-internal JSON contracts

The `livespec` template's prompts populate the following payload fields:

- `prompts/seed.md` populates `seed_input.schema.json`'s `template`, `intent`, `files[]`, and `sub_specs[]` fields. The `template` field MUST equal the literal string the user chose in the pre-seed dialogue (e.g., `"livespec"`). The `intent` field MUST carry the verbatim free-text intent. The `files[]` array MUST contain one entry per template-declared spec-file path. The `sub_specs[]` array MUST be empty on "no" to the v020 Q2 question and MUST carry one `SubSpecPayload` entry per named template on "yes".
- `prompts/critique.md` populates `proposal_findings.schema.json`'s `findings[]` array. Each finding MUST carry `name`, `target_spec_files`, `summary`, `motivation`, and `proposed_changes` fields.

The `prompts/propose-change.md` and `prompts/revise.md` prompts each consume a paired payload schema (`proposal_findings.schema.json` and `revise_input.schema.json` respectively). The schemas MUST stay co-authoritative with their dataclass pairs under `livespec/schemas/dataclasses/`.

## Per-prompt semantic-property catalogue

This catalogue enumerates the testable semantic properties for each REQUIRED prompt in the `livespec` template. Phase 6 lands bootstrap-minimum (1-2 properties per prompt); Phase 7's first propose-change against this sub-spec widens the catalogue to the full assertion surface that the v018 Q5 prompt-QA harness asserts against.

### `prompts/seed.md`

- `headings_derived_from_intent` — the prompt MUST derive top-level `#` headings within each spec file from intent nouns, NOT from a fixed taxonomy. (Asserts the v020 Q4 starter-content policy; aligns with SPECIFICATION/constraints.md §"Heading taxonomy" line 47 which pins intent-derivation to level 1.) **Assertion function**: every entry in `replayed_response.files[]` has a non-empty content body whose first non-blank line begins with `# ` (an H1 header).
- `asks_v020_q2_question` — the prompt MUST ask the v020 Q2 sub-spec-emission question and route emission by the user's answer — `sub_specs: []` on "no", one `SubSpecPayload` per named template on "yes". **Assertion function**: when `input_context.ships_own_templates` is true (with `input_context.named_templates` listing N entries), `replayed_response.sub_specs` carries exactly N entries; otherwise `replayed_response.sub_specs` is the empty list.
- **Assertion-function contract.** Each property's assertion function lives in `tests/prompts/livespec/_assertions.py` keyed by the property's string name in the `ASSERTIONS` dict. The function accepts keyword-only arguments `*, replayed_response: object, input_context: object` per SPECIFICATION/contracts.md §"Prompt-QA harness contract" (v014); it raises `AssertionError` on any property violation. The fixture's `expected_semantic_properties` list MAY contain any subset of the property names above; absent properties are not asserted.
- **Catalogue widening rule.** Future per-prompt regeneration cycles MAY add properties to this list; each new property's assertion function MUST land in `_assertions.py` in the same revise commit per the in-line widening rule (Plan §3543-3550).

### `prompts/propose-change.md`

- `target_files_within_spec_target` — the prompt MUST elicit per-finding `target_spec_files` referencing the spec-file paths under the `--spec-target` tree. Findings whose `target_spec_files` reference paths outside `--spec-target` are malformed. **Assertion function**: every entry in `replayed_response.findings[]`'s `target_spec_files` array is a path string whose prefix matches `input_context.spec_target` (treating both as POSIX-relative paths).
- `bcp14_in_proposed_changes` — the prompt SHOULD apply BCP14 normative language (`MUST`, `SHOULD`, `MAY`, `MUST NOT`, `SHOULD NOT`, `MAY NOT`) in the `proposed_changes` prose so the resulting propose-change file flows into the spec under the same discipline. **Assertion function**: every entry in `replayed_response.findings[]`'s `proposed_changes` string contains at least one BCP14 keyword (whole-word match, uppercase).
- **Assertion-function contract.** Same shape as the prompts/seed.md catalogue contract (sub-step (c).1, v003): each property's assertion function lives in `tests/prompts/livespec/_assertions.py` keyed by the property's string name in the `ASSERTIONS` dict, accepts keyword-only `*, replayed_response: object, input_context: object`, and raises `AssertionError` on violation.
- **Catalogue widening rule.** Same shape as v003: future per-prompt regeneration cycles MAY add properties; each new property's assertion function lands in `_assertions.py` in the same revise commit.

### `prompts/revise.md`

- `decisions_reference_pending_proposals` — the prompt MAY emit decisions for any subset of pending proposed-change files under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`); selective per-proposal coverage is supported per `SPECIFICATION/spec.md` §"Sub-command lifecycle" (v052) revise lifecycle clause (h). Every entry in `replayed_response.decisions[].proposal_topic` MUST, however, reference an actually-pending proposed-change canonical topic — extras (decisions whose topic does NOT match any pending proposal stem) indicate stale or typo'd topic references and are a bug. **Assertion function**: every entry in `replayed_response.decisions[].proposal_topic` is a member of the topic-stem set extracted from `input_context.pending_proposals[]` (each path's filename stem; e.g., `quiet-flag.md` → `quiet-flag`). Decisions whose topic is NOT in pending fail the assertion; pending proposals NOT covered by decisions are tolerated (selective revise).
- `per_proposal_disposition_with_rationale` — the prompt MUST emit a per-proposal disposition (`accept`, `reject`, or `modify`) with a non-empty rationale per disposition. **Assertion function**: every entry in `replayed_response.decisions[]` has a `decision` field in `{"accept", "modify", "reject"}` AND a non-empty whitespace-stripped `rationale` field. Schema validation already enforces field presence + the enum; this assertion strengthens the rationale check (whitespace-only rationales fail).
- **Assertion-function contract.** Same shape as v003/v004 (sub-steps (c).1 / (c).2 catalogue contracts).
- **Catalogue widening rule.** Same shape as v003/v004.

### `prompts/critique.md`

- `findings_grounded_in_spec_target` — the prompt MUST ground each finding against the spec target's current state. Critique findings MUST carry `target_spec_files` referencing files that exist in the target tree. **Assertion function**: every entry in `replayed_response.findings[]`'s `target_spec_files` array is a path string present in `input_context.current_spec_files[]` (the harness-passed enumeration of files that exist in the spec target at invocation time).
- `prioritizes_ambiguity_over_style` — the prompt SHOULD prioritize ambiguities and contradictions over wording-style suggestions; the latter belong in a separate cleanup-style propose-change cycle. **Assertion function**: every entry in `replayed_response.findings[]`'s `motivation` field contains at least one of the keywords from the ambiguity / contradiction lexicon (`ambiguity`, `ambiguous`, `contradiction`, `contradicts`, `contradictory`, `unclear`, `inconsistent`, `inconsistency`, `silent`, `undefined`) — case-insensitive substring match. The lexicon is heuristic and intentionally permissive; richer semantic checks live in the doctor LLM-driven subjective phase.
- **Assertion-function contract.** Same shape as the v003/v004/v005 catalogue contracts.
- **Catalogue widening rule.** Same shape as v003/v004/v005.

## Doctor-LLM-subjective-checks prompt

The `template.json` `doctor_llm_subjective_checks_prompt: "prompts/doctor-llm-subjective-checks.md"` field declares the prompt the doctor LLM-driven subjective phase invokes. The prompt MUST emit `doctor_findings.schema.json`-conforming output. Phase 7 brings this prompt to operability; Phase 6's bootstrap-minimum stub at `prompts/doctor-llm-subjective-checks.md` documents the contract without implementing the full subjective check logic.
