---
topic: spec-amendments-from-doctor-bug-investigation
author: claude-opus-4-7
created_at: 2026-05-25T16:42:13Z
---

## Proposal: add-livespec-runtime-to-locked-vendored-libs

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Add livespec_runtime as a 6th entry to constraints.md §"Locked vendored libs". The doctor static-phase wrapper bin/doctor_static.py and 5+ static check modules import livespec_runtime.cross_repo.types but the plugin bundle's _vendor/ does not currently include it, silently violating constraints.md §"End-user runtime dependencies" promise that python3 >= 3.10 is the sole runtime dependency. The cross-repo coordination automation surface (livespec-dev-tooling v0.2.0) mitigates the operational toil of re-vendoring on every livespec-runtime release via automated bump-pin PRs that detect .vendor.jsonc entries and invoke just vendor-update.

### Motivation

Detailed in work-item li-tvi7lm filed in this repo via PR #236. The bare invocation `bin/doctor_static.py --project-root <path>` fails immediately with ModuleNotFoundError: No module named 'livespec_runtime' because the bundle's bootstrap only adds scripts/ and scripts/_vendor/ to sys.path, and the vendor tree ships only 5 libs (fastjsonschema, jsoncomment, returns, structlog, typing_extensions). Recovery requires `uv run` from a project venv that has livespec-runtime installed, but SKILL.md prose for seed and doctor doesn't document this precondition. The current spec at constraints.md §"End-user runtime dependencies" promises python3 >= 3.10 is sufficient; the impl violates this promise silently. Adding livespec_runtime to the vendored-libs enumeration brings the impl into compliance with the spec's existing promise rather than relaxing it. The cross-repo coordination automation surface landed earlier (v076 / dev-tooling v0.2.0) provides the version-sync mechanism that makes the operational re-vendoring toil objection moot.

### Proposed Changes

Add a 6th entry to the bulleted list at `constraints.md:63-69` §"Locked vendored libs":

> - **`livespec_runtime`** (thewoolleyman/livespec-runtime, BSD-3-Clause) — typed `DependsOnEntry` union, `CrossRepoManifest`, `resolve_ref`, and the `livespec_runtime.cross_repo.{types, providers.github, retry, resolve_ref}` subpackages per livespec-runtime's own `contracts.md`. Vendored as the canonical mechanism for livespec to consume its own sibling runtime library at impl-plugin-agnostic invocation time, satisfying `constraints.md` §"End-user runtime dependencies" promise that `python3 ≥ 3.10` is the sole runtime dependency. Operational re-vendoring on every livespec-runtime release is automated by livespec-dev-tooling's `reusable-bump-pin-from-dispatch.yml` workflow (which detects `.vendor.jsonc` entries and invokes the consumer's `just vendor-update <lib>` recipe).

ALSO update `.vendor.jsonc` at the repo root with the corresponding entry at vendoring time:

```jsonc
{
  "name": "livespec_runtime",
  "upstream_url": "https://github.com/thewoolleyman/livespec-runtime",
  "upstream_ref": "v0.3.0",
  "vendored_at": "<ISO timestamp at vendoring time>"
}
```

The `just vendor-update` recipe and `dev-tooling/checks/vendor_manifest.py` validation gate already accommodate adding new entries to `.vendor.jsonc`; no recipe-level or check-level change should be required beyond the manifest data itself.

This propose-change documents the SPEC change. The IMPLEMENTATION work — actually running `just vendor-update livespec_runtime`, validating that bare `bin/doctor_static.py` invocation now succeeds without `uv run`, and confirming the bump-pin automation correctly handles the new `.vendor.jsonc` entry on the next `livespec-runtime` release — tracks separately under work-item `li-tvi7lm` (filed in this same repo's `work-items.jsonl` via PR #236).


## Proposal: narrow-bcp14-static-rule-scope-defer-ambiguous-to-llm-phase

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Narrow the bcp14_keyword_wellformedness static check's detection scope to keywords vanishingly rare as descriptive English (Shall only); defer Must, Should, May to the LLM-driven phase where sentence-level context can disambiguate normative vs descriptive usage. The current static rule produces false-positives on prose like 'array of id strings. May be empty.' where May is descriptive English, not a malformed BCP 14 normative keyword. The check's own docstring already acknowledges that sentence-level case-inconsistency detection belongs in the LLM phase; this propose-change makes that intent normative.

### Motivation

Detailed in work-item li-mrtoei filed in this repo via PR #236. The static rule at bcp14_keyword_wellformedness.py applies a naive \b(Must|Shall|Should|May)\b regex with no sentence-level context discrimination. May is the worst false-positive offender because it's also a common English word that legitimately begins sentences. The narrower static rule (just Shall, the unambiguous case) preserves the high-signal cases while removing the false-positive class. Must, Should, May continue to be enforced but at the LLM-driven phase where the objective-checks prompt can apply sentence-level discrimination.

### Proposed Changes

Update `constraints.md` §"BCP14 normative language" (currently at lines 236-238) to clarify the static-vs-LLM phase split. Replace the existing single-paragraph content:

> Spec-file prose MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, `OPTIONAL`. The keywords MUST be uppercase to be normative; lowercase use is non-normative descriptive prose. The `livespec`-template's NLSpec discipline doc enumerates BCP14 well-formedness rules in detail; this constraints file states only the meta-rule.

with the expanded version:

> Spec-file prose MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, `OPTIONAL`. The keywords MUST be uppercase to be normative; lowercase use is non-normative descriptive prose. The `livespec`-template's NLSpec discipline doc enumerates BCP14 well-formedness rules in detail; this constraints file states only the meta-rule.
>
> **Static-phase enforcement scope.** Doctor's static-phase `bcp14_keyword_wellformedness` check MUST detect mixed-case `Shall` as the unambiguous-mismatch case — no descriptive English usage of "Shall" is realistic at sentence boundaries. Mixed-case `Must`, `Should`, and `May` MUST be deferred to the LLM-driven phase, where sentence-level context discriminates normative misuse from descriptive English (e.g., "May be empty" as data-shape description vs. a malformed normative "May implementations support X"). The static rule's first-violation short-circuit behavior MUST be preserved within the narrowed keyword set. The static rule's exemption from sub-trees (`history/`, `proposed_changes/`, `templates/`) and its single-top-level-`.md`-files-only walk MUST be preserved.

The narrowing matches the check module's own docstring intent at `bcp14_keyword_wellformedness.py:6-8`, which already acknowledges that "sentence-level case-inconsistency detection moves to the LLM-driven phase" but the static rule does not yet honor that split.

NO change required to `contracts.md:625-628`'s test reference (`test_doctor_fail_then_fix.py`); the test exercises a Shall-class violation which remains in scope. Per the spec's own template-extension test discipline, equivalent coverage of Must/Should/May misuse SHOULD land in the LLM-driven phase's `doctor-llm-objective-checks` template prompt as part of the implementation work.

This propose-change documents the SPEC change. The IMPLEMENTATION work — narrowing `bcp14_keyword_wellformedness.py`'s `_MIXED_CASE_KEYWORDS` tuple to `("Shall",)`, updating `tests/livespec/doctor/static/test_bcp14_keyword_wellformedness.py` to remove the dropped-keyword cases and add a regression test asserting that descriptive sentence-initial "May" does NOT trip the static check, and authoring the LLM-driven coverage in the template prompt — tracks separately under work-item `li-mrtoei` (filed in this same repo's `work-items.jsonl` via PR #236).

