# Constraints — `livespec` template

This sub-spec's constraints enumerate the NLSpec discipline rules every prompt and starter-content authoring step MUST apply. The full discipline lives in the template-bundled `livespec-nlspec-spec.md` reference doc; this constraints file states the meta-rules and the structural well-formedness invariants the doctor static phase enforces.

## BCP14 normative-keyword well-formedness

Every spec-file `.md` under a `livespec`-template-rooted spec tree MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language for normative statements: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, `OPTIONAL`. The keywords MUST appear in uppercase to be normative; lowercase use is non-normative descriptive prose only.

The `livespec-nlspec-spec.md` doc enumerates the keyword-matching rules in detail (token boundaries, embedded-uppercase-word distinctions, etc.). The doctor static phase's BCP14 well-formedness check (Phase 7 widening; Phase 6 stub) MUST detect malformed normative usage.

## Gherkin blank-line convention

Fenced ` ```gherkin ` blocks within `scenarios.md` (or any other spec file) MUST follow the gherkin blank-line convention: `Feature:` paragraph, blank line, `Scenario:` paragraph, blank line, `Given`/`When`/`Then` steps without intervening blank lines. The convention preserves readability AND parseability for downstream validation tooling.

The `dev-tooling/checks` layer's gherkin-blank-line-format check (Phase 7 widening) MUST detect violations of the convention. Sub-specs that reuse the gherkin format inherit the constraint via this sub-spec's NLSpec discipline.

## Heading taxonomy guidance

Top-level `##` headings within each spec file SHOULD reflect the file's subject matter rather than a fixed organizational taxonomy. The `livespec` template's seed prompt MUST derive heading nouns from the user's free-text intent so the resulting headings are domain-grounded.

`###` and deeper headings MAY be used freely for structural depth within a section. The `tests/heading-coverage.json` test-anchor surface targets `##` headings only; `###` and deeper are not bound to coverage entries.

## Spec-file-set well-formedness

Every `livespec`-template-rooted spec tree MUST contain the file set `{README.md, spec.md, contracts.md, constraints.md, non-functional-requirements.md, scenarios.md}` at the spec root. Missing any of these files is a doctor static-phase `template-files-present` failure. Sub-spec trees under `<spec_root>/templates/<name>/` follow the same file-set requirement uniformly per v020 Q1.

## Non-functional-requirements scope

`non-functional-requirements.md` content covers dev-environment and contributor-facing requirements only. The boundary against the other spec files is:

- User-facing intent and behavior MUST stay in `spec.md`.
- User-facing wire contracts MUST stay in `contracts.md`.
- Constraints whose violation an end user could observe MUST stay in `constraints.md`. Examples: Python runtime version, end-user dependency envelope, exit-code contract, structured-logging schema, vendored-library discipline (because vendoring affects shipped artifacts).
- Constraints that bind only the project's contributors MUST move to `non-functional-requirements.md`. Examples: linter and formatter rules, code-coverage targets, complexity thresholds, comment discipline, hook configuration, enforcement-suite invocation, repo-local task tracking, contributor commit discipline.

Doctor static-phase `template-files-present` check MUST treat `non-functional-requirements.md` as required and MUST fail when it is missing.

## Propose-change topic-format constraint

`<spec-target>/proposed_changes/<topic>.md` filenames MUST use kebab-case alphanumeric topics. The `dev-tooling/checks` propose-change-topic-format check enforces this. Reserved suffixes (`-revision.md`) MUST NOT appear in propose-change filenames; the suffix is reserved for the revise-emitted paired record.

## Version-contiguity invariant

`<spec-target>/history/v<NNN>/` directories MUST form a contiguous version sequence starting at `v001` with no gaps. The doctor static-phase `version-contiguity` check enforces this. `prune-history` MUST preserve contiguity for the remaining tail when removing the oldest block of versions.

## NLSpec-discipline reference document

The `livespec-nlspec-spec.md` doc at the template root is the canonical reference for BCP14 well-formedness, gherkin blank-line convention, heading taxonomy, and the broader natural-language-spec hygiene rules. The doc is a SEED-time reference: each REQUIRED prompt internalizes it before generating any output. The doc itself is NOT seeded into a project's `SPECIFICATION/` tree (it ships with the template, not with end-user spec output). Mutations to the discipline doc flow through this sub-spec's propose-change cycle, NOT through end-user project propose-change cycles.
