# Specification — `minimal` template

This sub-spec governs the `minimal` built-in template's user-visible behavior. The template ships with `livespec` itself at `.claude-plugin/specification-templates/minimal/` and serves two roles: (a) a reference-minimum exemplar for custom-template authors who want a pared-down starting point, and (b) the canonical fixture for the end-to-end integration test at `tests/e2e/`. Mutations to the template's prompts, starter content, or delimiter-comment format MUST flow through this sub-spec.

## Template root layout

The `minimal` template root MUST contain `template.json` with `template_format_version: 1`, `spec_root: "./"`, and `null` for both LLM-driven doctor prompt fields (the minimal template does NOT ship doctor-LLM prompts; the doctor static phase is the only phase active for minimal-rooted projects). The template MAY ship a `prompts/seed.md` for the seed flow, but the other REQUIRED prompts (`propose-change`, `critique`, `revise`) are stubbed at this revision and widen in Phase 7.

## Single-file positioning

End-user output of the `minimal` template MUST be a single `SPECIFICATION.md` file at the project root rather than a multi-file `SPECIFICATION/` directory. The `template.json` `spec_root: "./"` value plus a single declared file path achieves this. The `minimal` template is the right choice for projects whose specs are small enough to fit comfortably in one file or for projects that want to demonstrate `livespec`'s lifecycle on the simplest possible spec layout.

The single-file constraint applies only to end-user output. This sub-spec — internal to `livespec` — uses the multi-file livespec layout uniformly per v020 Q1, decoupled from the end-user convention.

## Reduced prompt interview intents

The `minimal` template's seed prompt MUST capture user intent and emit `seed_input.schema.json`-conforming JSON. Unlike the `livespec` template, the `minimal` template's seed prompt does NOT implement the v020 Q2 sub-spec-emission capability. `minimal`-rooted projects always get `sub_specs: []` regardless of any sub-spec-emission question; the prompt MAY skip the sub-spec-emission dialogue entirely.

The other REQUIRED prompts (`propose-change`, `critique`, `revise`) at Phase 6 are stubbed at the bootstrap-minimum scope; Phase 7 widens them to full feature parity with the `livespec` template's prompts, adapted for single-file specs.

## End-to-end integration test fixture

The `minimal` template is the canonical fixture for `tests/e2e/`'s end-to-end integration test (Phase 9 work). The test MUST exercise (a) seed against an empty fixture repo, (b) propose-change → revise round-trip, (c) doctor static phase, (d) retry-on-exit-4 path, (e) doctor-static-fail-then-fix recovery, and (f) prune-history no-op against a single-version history. `tests/e2e/fake_claude.py` is the test harness's mock Claude Code surface; Phase 5 lands the placeholder, Phase 9 fills in the real e2e content.

## Starter-content policy

The `minimal` template's `specification-template/SPECIFICATION.md` (Phase 7 widening; Phase 6 placeholder) provides a starter shape: heading skeleton plus delimiter-comment markers per the format defined in this sub-spec's contracts file. End users SHOULD overwrite the placeholder content with their domain prose; the delimiter comments MUST be preserved so subsequent propose-change/revise cycles can target named regions of the file.
