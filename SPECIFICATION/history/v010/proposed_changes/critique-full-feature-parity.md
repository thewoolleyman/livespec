---
topic: critique-full-feature-parity
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-04T02:40:48Z
---

## Proposal: critique CLI surface

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Replace the `critique` row of the wrapper-CLI surface table in contracts.md (currently `(varies; Phase 7 widens)`) with the full enumerated flag set: required `--findings-json <path>`; optional `--author <id>`, `--spec-target <path>`, `--project-root <path>`. No positional argument.

### Motivation

PROPOSAL.md §"`critique`" line 2357 specifies that the LLM invokes `bin/critique.py --findings-json <tempfile> [--author <id>]`. The two universal flags `--spec-target <path>` and `--project-root <path>` are inherited from the wrapper-CLI baseline at contracts.md line 7 and the multi-tree mechanism at contracts.md line 50, both of which already explicitly include `critique` in their applicability lists. The contracts.md table row was deliberately left as a placeholder at v001 because the Phase-3 minimum-viable wrapper exposed only an experimental shape. Phase 7 sub-step 4 widens the wrapper to the full PROPOSAL contract, so the table row must enumerate the flags.

The `<topic>` positional that `propose-change` takes is intentionally absent from `critique`'s CLI: critique derives its topic hint internally from the resolved author identifier (codified by the companion finding "critique internal delegation contract" in this file), so the user-facing shape exposes no topic argument.

### Proposed Changes

One atomic edit to **SPECIFICATION/contracts.md §"Wrapper CLI surface"**.

Replace the existing `critique` row at line 13 (currently: `| \`critique\` | (varies; Phase 7 widens) | \`--spec-target <path>\`, \`--project-root <path>\` |`) with:

> | `critique` | `--findings-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |

## Proposal: critique schema-validation contract

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify in spec.md that `bin/critique.py` validates its `--findings-json` payload against `proposal_findings.schema.json` at the wrapper boundary, that schema or wire-format failures exit 4 with structured findings on stderr, and that the calling skill SHOULD interpret exit 4 as a retryable malformed-payload signal per the unified retry-on-exit-4 contract already enumerated in contracts.md §"Lifecycle exit-code table".

### Motivation

PROPOSAL.md §"`critique`" lines 2352-2363 require the wrapper to load the JSON tempfile written by the LLM and validate it against the proposal-findings schema before any delegation to `propose_change`'s internal logic. On validation failure the wrapper MUST exit 4 with structured findings on stderr; the calling SKILL.md prose treats that as a retryable signal and re-invokes the template prompt with error context. The retry count is intentionally unspecified in v1.

The Phase-3 minimum-viable wrapper already implements this contract end-to-end (cycle 121 of the v033 D5b second-redo per `bootstrap/STATUS.md`'s sub-step 3.c history; currently in `livespec/commands/critique.py` lines 136-157 via the shared `_validate_payload` helper). spec.md does not yet codify the architecture-level rule, so a clean re-implementation against the spec alone could not derive the wire-level retry handshake. Phase 7's widening must surface the contract in spec.md before the implementation is considered at full feature parity.

The retry semantics themselves are already covered by contracts.md §"Lifecycle exit-code table" line 31 (exit 4 = "ValidationError — schema or wire-format validation failure on inbound payload (retryable per the calling SKILL.md's retry-on-exit-4 contract)"); this proposal does not duplicate that table — it only adds the critique-specific binding sentence in spec.md.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Sub-command lifecycle"**: append a new paragraph immediately after the existing pre/post-doctor-cycle paragraph at line 29 codifying the critique wrapper's payload-validation contract:

> **`critique` payload validation.** `bin/critique.py` validates the inbound `--findings-json` payload against `proposal_findings.schema.json` at the wrapper boundary before any internal delegation. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per contracts.md §"Lifecycle exit-code table", the calling `critique/SKILL.md` prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-invoke the template prompt with error context; the retry count is intentionally unspecified in v1. The skill MAY surrender after a bounded number of retries by surfacing the structured findings to the user.

## Proposal: critique internal delegation contract

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify in spec.md that `bin/critique.py` delegates internally to `propose-change`'s Python logic with two architectural-level invariants: (a) the topic hint passed to `propose-change` is the resolved author value itself (the un-slugged author stem, NOT the resolved-author with the `-critique` suffix pre-attached); (b) the `reserve_suffix` parameter is set to the literal string `"-critique"`, which is the canonical critique-delegation suffix. Also codify that the internal delegation skips the inner pre/post `doctor`-static cycle (the outer `critique` invocation's wrapper ROP chain already covers the whole operation), and that `critique` does not run `revise` — the user reviews and runs `revise` separately to process the resulting file.

### Motivation

PROPOSAL.md §"`critique`" lines 2364-2403 define the architecture of how `critique` produces a proposed-change file: it resolves the author identifier via the unified four-step precedence (already codified in spec.md §"Author identifier resolution"), then delegates to `propose-change`'s internal Python logic with the resolved-author stem as topic hint and `"-critique"` as the reserve-suffix parameter. `propose-change` then composes them via its v016 P3 / v017 Q1 reserve-suffix canonicalization (already codified in spec.md §"Proposed-change and revision file formats"). The composite invariant — pre-attached `-critique` does not double, long author stems are truncated on the non-suffix portion, the `-critique` suffix survives at the 64-char cap intact — is already covered by the existing reserve-suffix paragraph; what is missing in spec.md is the explicit critique-side architectural rule that critique passes the resolved-author stem (NOT a pre-composed `<author>-critique`) and that `-critique` is the canonical critique-delegation suffix.

The Phase-3 minimum-viable wrapper currently pre-attaches `-critique` to the resolved-author stem and passes the composite as the topic hint without using the reserve-suffix parameter (`livespec/commands/critique.py` line 127: `topic = f"{_resolve_author(namespace=namespace)}-critique"`). That shape produces correct filenames for short author stems but diverges from the PROPOSAL contract for long stems and for hints whose canonical form already ends in `-critique`. The widening replaces that shape with delegation through the reserve-suffix parameter.

The "skip inner pre/post doctor cycle" rule is already implied for `critique` by the universal "every command except `help`, `doctor`, and `resolve_template`" paragraph at spec.md line 29 (critique's own wrapper ROP chain runs the pre/post doctor cycle once at the outer boundary; the internal delegation to propose-change is internal, not a fresh CLI invocation, so it does not retrigger the pre/post cycle), but the critique-specific binding is worth surfacing explicitly so a clean re-implementation does not double-run the cycle when it composes the two wrappers.

The "does not run revise" rule is a behavioral consequence: `critique` writes a proposed-change file and stops. The user reviews the file (typically with the LLM's narration of the findings) and invokes `/livespec:revise` separately to process it. This separation is what lets the user accept, reject, edit, or augment the LLM's findings before the spec mutates.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Sub-command lifecycle"**: append a new paragraph immediately after the `critique` payload validation paragraph (added by the companion finding above) codifying the internal-delegation contract:

> **`critique` internal delegation (PROPOSAL.md §"`critique`" lines 2364-2403).** After successful payload validation, `bin/critique.py` resolves the author identifier via the unified precedence already codified in §"Author identifier resolution" and delegates to `propose-change`'s internal Python logic with the resolved-author stem as topic hint and the literal string `"-critique"` as the reserve-suffix parameter. The topic hint passed in is the un-slugged resolved-author stem itself; `critique` MUST NOT pre-attach `-critique` to the hint. `propose-change`'s reserve-suffix canonicalization (codified in §"Proposed-change and revision file formats" under "Reserve-suffix canonicalization (v016 P3...)") composes the two into the canonical critique-delegation topic, guaranteeing the `-critique` suffix is preserved intact at the 64-char cap and pre-attached `-critique` does not double. `-critique` is the canonical critique-delegation suffix; no other suffix value is permitted on this code path. The internal delegation MUST NOT retrigger the pre/post `doctor`-static cycle described above — the outer `critique` invocation's wrapper ROP chain already covers the whole operation; only one pre-step and one post-step `doctor` run per outer CLI invocation, regardless of how many internal wrapper compositions occur. After the delegation writes the proposed-change file, `critique` exits with `propose-change`'s exit code; `critique` does NOT run `revise`. The user reviews the resulting proposed-change file and invokes `/livespec:revise` separately to process it.
