---
topic: prompt-qa-harness-machinery
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-05T21:54:26Z
---

## Proposal: Prompt-QA tier in the test pyramid

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify the prompt-QA tier as a layer in the test pyramid in SPECIFICATION/spec.md §"Testing approach". The prompt-QA tier exercises every built-in template's REQUIRED prompts via deterministic replay-and-assert against canonical fixtures and is scope-distinct from both the unit tier (which gates 100% per-file coverage) and the future v014 N9 e2e harness (which drives wrappers via the Claude Agent SDK). The seeded §"Testing approach" currently describes only the unit-test pyramid; Phase 7 sub-step (f) widens it to acknowledge the prompt-QA layer being landed.

### Motivation

PROPOSAL.md §"Test pyramid" lines 3549-3567 and §"Prompt-QA tier (per-prompt verification, v018 Q5)" lines 3987-4047, joint-resolved with deferred-items.md `prompt-qa-harness`, define the prompt-QA tier as a separate layer above the unit tier, asserted before any e2e harness test runs. The seeded SPECIFICATION/spec.md §"Testing approach" describes only the unit-test pyramid (mirror-pairing rule + 100% per-file line+branch coverage). Phase 7 sub-step (f) introduces the tests/prompts/ infrastructure required by v018 Q5; the spec MUST codify the tier so future maintainers and downstream doctor checks understand its role and coverage scope. Because tests/prompts/ is OUT OF SCOPE for the per-file 100% coverage gate per PROPOSAL.md line 3552-3567 (only tests/livespec/, tests/bin/, tests/dev-tooling/checks/ contribute to the unit tier), this distinction MUST be codified explicitly to avoid future confusion about which tests gate coverage.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Testing approach"**: append a new paragraph after the existing v034 D2-D3 paragraph (currently the second paragraph of the section) codifying the prompt-QA tier:

> **Prompt-QA tier (PROPOSAL.md §"Prompt-QA tier (per-prompt verification, v018 Q5)" lines 3987-4047).** Above the unit-test layer (which gates 100% per-file line+branch coverage on `livespec/`, `bin/`, `dev-tooling/checks/`), every built-in template's REQUIRED prompts (`prompts/seed.md`, `prompts/propose-change.md`, `prompts/revise.md`, `prompts/critique.md`) are exercised by per-prompt tests under `tests/prompts/<template>/`. Each test loads one or more fixture files capturing a prompt-input + canonical-LLM-response pair, validates the canonical response against its named JSON Schema (`seed_input.schema.json`, `proposal_findings.schema.json`, `revise_input.schema.json`), and asserts every declared semantic-property name in the fixture against per-template assertion functions. The prompt-QA tier is invoked via `just check-prompts` (included in `just check`); each built-in template MUST ship at least one prompt-QA test per REQUIRED prompt (4 prompts × 2 built-in templates = 8 minimum cases). The prompt-QA tier is scope-distinct from the v014 N9 end-to-end harness at `tests/e2e/` (which drives wrappers via the Claude Agent SDK surface) — the prompt-QA harness performs no LLM round-trip and no wrapper invocation, only deterministic replay-and-assert against canonical fixtures. Per the unit-tier coverage scope codified above, `tests/prompts/` is NOT measured for line+branch coverage; the prompt-QA tier provides additional confidence but does not contribute to the 100% gate.


## Proposal: Prompt-QA harness contract

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Codify the prompt-QA harness contract in SPECIFICATION/contracts.md as a new section: harness file location (`tests/prompts/_harness.py` — a dedicated test-infrastructure module, NOT a stripped-down `tests/e2e/fake_claude.py` variant), fixture file path convention (`tests/prompts/<template>/<prompt>/<case>.json`), the fixture-format schema (`tests/prompts/_fixture.schema.json`) with named required fields, and the per-template assertion-registry mechanism (`tests/prompts/<template>/_assertions.py` exporting `ASSERTIONS: dict[str, Callable[..., None]]` via static enumeration with explicit imports, NOT dynamic discovery).

### Motivation

PROPOSAL.md §"Prompt-QA tier (per-prompt verification, v018 Q5)" lines 3987-4047 and the deferred-items.md `prompt-qa-harness` entry leave the implementation choice between (a) reusing a stripped-down `fake_claude.py` variant and (b) a dedicated helper module open as implementer choice under architecture-level constraints. Phase 7 sub-step (f) finalizes the choice as (b) a dedicated helper module: the prompt-QA tier has no Claude Agent SDK dependency and no wrapper invocation — both are scope-distinct from tests/e2e/. The fixture format pins six required fields enumerated in the deferred-items.md entry: `prompt_name`, `schema_id`, `input_context`, `replayed_response`, `expected_schema_valid`, `expected_semantic_properties`. Fixtures are themselves JSON-Schema-validated at load time so malformed fixtures fail fast. Per-template semantic-property assertions live in `tests/prompts/<template>/_assertions.py` exporting `ASSERTIONS: dict[str, Callable[..., None]]` populated via explicit imports per the static-enumeration-over-dynamic-discovery discipline (no `glob+importlib`; the type system can verify completeness). The harness module itself satisfies every livespec Python rule that applies to test infrastructure (style-doc compliance, `__all__` declaration, return-type annotations, keyword-only args via the `*` separator) per the plan's harness-quality clause.

### Proposed Changes

One atomic edit to **SPECIFICATION/contracts.md**: append a new top-level section "## Prompt-QA harness contract" at the end of the file (after the existing "## Pre-commit step ordering" section) with the following body:

> ## Prompt-QA harness contract
>
> The prompt-QA harness lives at `tests/prompts/_harness.py` as a dedicated test-infrastructure module, NOT a stripped-down `tests/e2e/fake_claude.py` variant. The two harnesses are scope-distinct: the prompt-QA harness performs no LLM round-trip and no wrapper invocation; the e2e harness drives wrappers end-to-end via the Claude Agent SDK surface. The leading underscore on `_harness.py` marks it as test-internal; it is not imported outside `tests/prompts/`.
>
> ### Fixture format
>
> Each prompt-QA test case ships under `tests/prompts/<template>/<prompt>/<case>.json` as a JSON document conforming to the fixture-format schema at `tests/prompts/_fixture.schema.json` (validated at load time via `fastjsonschema`). The fixture's required fields are:
>
> - `prompt_name` (string): the REQUIRED-prompt name, one of `"seed"`, `"propose-change"`, `"revise"`, `"critique"`.
> - `schema_id` (string): the named wire-contract schema the `replayed_response` MUST validate against — one of `"seed_input.schema.json"`, `"proposal_findings.schema.json"`, `"revise_input.schema.json"`.
> - `input_context` (object): the variables the skill prose would pass to the prompt at invocation time. Shape is template-specific.
> - `replayed_response` (object): the canonical LLM-output JSON the harness asserts against. Authored alongside the fixture by hand or via a per-prompt regeneration cycle.
> - `expected_schema_valid` (boolean): whether `replayed_response` is expected to validate against `schema_id`. The default-true case asserts schema conformance; the false case is reserved for negative-test fixtures (malformed-payload regression coverage).
> - `expected_semantic_properties` (array of strings): each entry names a per-template assertion function the harness MUST invoke against `replayed_response`.
>
> ### Per-template assertion registry
>
> Each built-in template ships `tests/prompts/<template>/_assertions.py` exporting a module-level `ASSERTIONS: dict[str, Callable[..., None]]` populated via explicit imports per the static-enumeration discipline. Dynamic discovery via `glob+importlib` is forbidden — the dict's contents MUST be visible to pyright strict so registry completeness is type-checkable. Each assertion function MUST accept keyword-only arguments `*, replayed_response: object, input_context: object` and raise `AssertionError` on any property violation. The harness invokes each name listed in `expected_semantic_properties` by lookup against the per-template `ASSERTIONS` dict; an unknown name MUST fail the test with a clear "unknown property name" diagnostic that names the missing assertion.
>
> ### Harness behavior
>
> The harness exposes a single primary entry point with keyword-only arguments. Its behavior, in order:
>
> 1. Load the fixture file and validate it against `_fixture.schema.json`. Validation failure → `AssertionError`.
> 2. When `expected_schema_valid` is true, validate `replayed_response` against the JSON Schema named by `schema_id`. Validation failure → `AssertionError`.
> 3. When `expected_schema_valid` is false, assert that schema validation FAILS (negative-test coverage). Validation pass on a negative-test fixture → `AssertionError`.
> 4. For each name in `expected_semantic_properties`, look up the function in the per-template `ASSERTIONS` dict and invoke it with `replayed_response` and `input_context` keyword arguments. Any raised `AssertionError` propagates.
>
> The harness does NOT execute the prompt against any LLM; it asserts that the canonical `replayed_response` continues to satisfy the contract. Per-prompt regeneration cycles in Phase 7 items (c) and (d) update fixtures alongside their prompts — if a regenerated prompt no longer satisfies the per-template catalogue's properties, the prompt-QA test fails and the regeneration is rejected.
>
> ### Python-rule compliance
>
> The harness module, the fixture-format schema, the per-template assertion modules, and the per-prompt test modules MUST satisfy every livespec Python rule that applies to test infrastructure: each `.py` file declares `__all__`; functions take keyword-only arguments per the universal `*` separator; function and method signatures carry full return-type annotations; dataclasses are `frozen=True, slots=True, kw_only=True`; private helpers carry the leading `_` prefix. Coverage measurement does NOT include `tests/prompts/` — the source list for `[tool.coverage.run]` is anchored at `livespec/`, `bin/`, `dev-tooling/`, so the unit-tier per-file 100% coverage gate does not extend to test infrastructure.

