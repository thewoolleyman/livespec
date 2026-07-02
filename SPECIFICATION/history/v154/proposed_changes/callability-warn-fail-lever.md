---
topic: callability-warn-fail-lever
author: claude-fable-5
created_at: 2026-07-02T04:53:50Z
---

## Proposal: credential_wrapper callability carries a warn-vs-fail severity lever

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Reconcile contracts.md with the shipped config-named-cli-callability check. Two spots — the invariant paragraph in §"Doctor cross-boundary invariants" and an earlier parenthetical in §"Spec-side CLI contract" — state that a credential_wrapper first token that fails to resolve fires `fail`. The implemented check instead WARNS on an unresolvable credential_wrapper (the host-provisioned wrapper is legitimately absent on CI runners that do not install it, so a hard fail would redden every fleet CI once repos set the key) and reserves `fail` for a first token that resolves to a present-but-non-executable file (a real misconfiguration). This proposal replaces the credential_wrapper-specific callability sentence with the warn-vs-fail lever clause and softens the earlier parenthetical to match, keeping hard-fail semantics unchanged for the spec-side and orchestrator-side named CLIs.

### Motivation

Impl->spec drift relocated from the closed credential-wrapper epic (livespec-zd8h) into the fleet-followups planning thread as inventory item C15, then verified live 2026-07-02 against origin/master and the shipped check .claude-plugin/scripts/livespec/doctor/static/config_named_cli_callability.py: its `_evaluate` classifies a credential_wrapper first token as `_RESOLVE_UNRESOLVABLE` -> `warn` and `_RESOLVE_NOT_EXECUTABLE` -> `fail`, and its module docstring already describes exactly this lever. The lever shipped in PR #746 (livespec-zd8h.3) so CI stays green on runners that do not install the host wrapper; the contract prose was never updated to match. This proposal closes that drift.

### Proposed Changes

Two prose edits to `SPECIFICATION/contracts.md`, both scoped to the credential_wrapper OPTIONAL key. No `## ` or `### ` headings are added, renamed, or removed (so tests/heading-coverage.json is unaffected); the spec-side and orchestrator-side named-CLI hard-fail semantics are unchanged.

--- EDIT 1: §"Doctor cross-boundary invariants", the `config-named-cli-callability` paragraph ---

The paragraph's opening general sentence stays as-is for the always-hard-fail CLIs:

> For every CLI named in `.livespec.jsonc` [...] the named entry MUST resolve and be executable. A missing or non-executable resolution fires `fail` naming the config key and value.

REPLACE the credential_wrapper-specific sentence that currently follows it:

> When `credential_wrapper` is present and non-empty, its first token MUST resolve and be executable; a missing or non-executable resolution fires `fail` naming the config key. When absent or empty, the invariant is a no-op for that OPTIONAL key.

WITH the warn-vs-fail lever clause:

> When `credential_wrapper` is present and non-empty, its first token is resolved with the same semantics as every other named CLI, but the callability finding carries a severity lever unique to this OPTIONAL key: if the first token resolves to a file that is not executable (a real misconfiguration) the finding is `fail`; if the first token does not resolve at all — the host-provisioned wrapper is legitimately absent, e.g. on a CI runner that does not install it — the finding is `warn` (non-fail, so CI stays green); when the key is absent or empty the invariant is a no-op. The lever applies ONLY to `credential_wrapper`; the spec-side and orchestrator-side named CLIs keep their hard-fail semantics.

(The lever clause's closing sentence disambiguates the opening general sentence: credential_wrapper is the sole exception to hard-fail-on-any-non-callable.)

--- EDIT 2: §"Spec-side CLI contract", the sentence introducing credential_wrapper resolvability ---

The current sentence reads:

> Like the other named CLIs, its resolvability is verified by the `config-named-cli-callability` invariant per §"Doctor cross-boundary invariants" (its first token MUST resolve to an executable).

REPLACE the trailing parenthetical `(its first token MUST resolve to an executable)` WITH:

> (its first token's callability carries a warn-vs-fail severity lever unique to this optional key — a present-but-non-executable first token fires `fail`, while an unresolvable first token fires `warn`, because the host-provisioned wrapper is legitimately absent on some runners; see §"Doctor cross-boundary invariants")

The surrounding sentence text is otherwise unchanged.
