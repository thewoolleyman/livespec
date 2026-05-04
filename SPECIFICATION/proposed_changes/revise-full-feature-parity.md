---
topic: revise-full-feature-parity
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-04T07:05:00Z
---

## Proposal: revise CLI surface

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Replace the `revise` row of the wrapper-CLI surface table in contracts.md (currently `(varies; Phase 7 widens)`) with the full enumerated flag set: required `--revise-json <path>`; optional `--author <id>`, `--spec-target <path>`, `--project-root <path>`. No positional argument.

Also fix the `--revise-input <tempfile>` flag-name typo on scenarios.md line 55 to `--revise-json <tempfile>` so the seeded scenarios match the wrapper's actual CLI surface.

### Motivation

PROPOSAL.md §"`revise`" lines 2445-2447 specify that `bin/revise.py` accepts `--revise-json <path>` (required) and `--author <id>` (optional). The two universal flags `--spec-target <path>` and `--project-root <path>` are inherited from the wrapper-CLI baseline at contracts.md line 7 and the multi-tree mechanism at contracts.md line 50, both of which already explicitly include `revise` in their applicability lists. The contracts.md table row was deliberately left as a placeholder at v001 because the Phase-3 minimum-viable wrapper exposed only the experimental shape with `--revise-json` already wired but no other widening commitments. Phase 7 sub-step 5 widens the wrapper to the full PROPOSAL contract, so the table row must enumerate the flags.

The `<topic>` positional that `propose-change` takes is intentionally absent from `revise`: revise processes every in-flight proposal under `<spec-target>/proposed_changes/` in creation-time order (see the companion finding "revise lifecycle and responsibility separation"), so the user-facing shape exposes no per-proposal selector.

The scenarios.md line-55 flag-name typo (`--revise-input`) is a slip in the seeded content; the canonical name `--revise-json` matches PROPOSAL.md §"`revise`" lines 2445-2474, the Phase-3 minimum-viable implementation at `livespec/commands/revise.py`, and Plan Phase 3 lines 1845-1846. The fix rides along with the contracts.md row replacement since both touch the same wire-level CLI naming.

### Proposed Changes

One atomic edit to **SPECIFICATION/contracts.md §"Wrapper CLI surface"**.

Replace the existing `revise` row at line 14 (currently: `| \`revise\` | (varies; Phase 7 widens) | \`--spec-target <path>\`, \`--project-root <path>\` |`) with:

> | `revise` | `--revise-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |

One atomic edit to **SPECIFICATION/scenarios.md §"Happy-path revise"**.

Replace line 55 (currently: `  And invokes \`bin/revise.py --revise-input <tempfile>\``) with:

> &nbsp;&nbsp;And invokes `bin/revise.py --revise-json <tempfile>`

## Proposal: revise payload validation

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify in spec.md that `bin/revise.py` validates its `--revise-json` payload against `revise_input.schema.json` at the wrapper boundary, that schema or wire-format failures exit 4 with structured findings on stderr, and that the calling skill SHOULD interpret exit 4 as a retryable malformed-payload signal per the unified retry-on-exit-4 contract already enumerated in contracts.md §"Lifecycle exit-code table".

### Motivation

PROPOSAL.md §"`revise`" lines 2474-2480 require the wrapper to load the JSON tempfile written by the LLM and validate it against `revise_input.schema.json` before any deterministic file-shaping work. On validation failure the wrapper MUST exit 4 with structured findings on stderr; the calling SKILL.md prose treats that as a retryable signal and re-assembles (or re-prompts) accordingly. The retry count is intentionally unspecified in v1.

The Phase-3 minimum-viable wrapper already implements this contract end-to-end (see `livespec/commands/revise.py` lines 99-139 — the `_validate_payload` helper composes `fs.read_text(schema)` → `jsonc.loads(schema-text)` → `validate_revise_input(payload, schema-dict)` and lifts schema-violation, JSON-malformation, and absent-payload-file failures uniformly to exit 4). spec.md does not yet codify the architecture-level rule, so a clean re-implementation against the spec alone could not derive the wire-level retry handshake. Phase 7's widening must surface the contract in spec.md before the implementation is considered at full feature parity.

The retry semantics themselves are already covered by contracts.md §"Lifecycle exit-code table" line 31 (exit 4 = "ValidationError — schema or wire-format validation failure on inbound payload (retryable per the calling SKILL.md's retry-on-exit-4 contract)"); this proposal does not duplicate that table — it only adds the revise-specific binding sentence in spec.md, mirroring the critique-side payload-validation paragraph already codified in this section.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Sub-command lifecycle"**: append a new paragraph immediately after the existing `critique` internal-delegation paragraph codifying the revise wrapper's payload-validation contract:

> **`revise` payload validation.** `bin/revise.py` validates the inbound `--revise-json` payload against `revise_input.schema.json` at the wrapper boundary before any deterministic file-shaping. Schema-violation, JSON-malformation, and absent-payload-file failures all lift to exit 4 with structured findings emitted on stderr per the `LivespecError` envelope. Per contracts.md §"Lifecycle exit-code table", the calling `revise/SKILL.md` prose SHOULD interpret exit 4 as a retryable malformed-payload signal and re-assemble (or re-prompt) accordingly; the retry count is intentionally unspecified in v1. The skill MAY surrender after a bounded number of retries by surfacing the structured findings to the user.

## Proposal: revise lifecycle and responsibility separation

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify in spec.md the architecture-level split of responsibility between the `revise` wrapper (deterministic file-shaping work, no LLM, no interactive dialogue) and the `revise/SKILL.md` prose (LLM-driven per-proposal acceptance dialogue, modify-decision iteration, the apply-to-all-remaining delegation toggle, and the optional steering-intent disambiguation). Codify the wrapper's preconditions, processing order, version-cut rule (v038 D1 Statement B: every successful revise cuts a new version), file-shaping outputs, and post-success state.

### Motivation

PROPOSAL.md §"`revise`" lines 2405-2522 define the architecture of how `revise` produces a new spec version from a set of in-flight proposed changes. The contract has two architecturally distinct halves: (a) the LLM-driven per-proposal decision flow lives entirely in skill prose — the wrapper never invokes the template prompt, the LLM, or the interactive confirmation dialogue; (b) once the skill assembles a payload conforming to `revise_input.schema.json`, the wrapper performs deterministic file-shaping work that does not branch on LLM judgment.

Per v038 D1 (codified at PROPOSAL.md §"Versioning" line 1734-1745 + §"`revise`" line 2483-2484), the version-cut rule is Statement B: a new `<spec-target>/history/vNNN/` is cut on every successful revise invocation (i.e., whenever revise processes at least one proposal). When at least one decision is `accept` or `modify`, the working-spec files named in those decisions' `resulting_files[]` are updated in place before the snapshot. When every decision is `reject`, the new version's spec files are byte-identical copies of the prior version's spec files (preserving the audit trail in the new `history/vNNN/proposed_changes/` directory regardless of decision mix).

The Phase-3 minimum-viable wrapper already implements a subset of the deterministic file-shaping (see `livespec/commands/revise.py`'s `_process_decisions` and `_write_and_move_per_decision` helpers — the wrapper composes per-decision revision-write + proposed-change-move, with `_bind_resulting_files` extending the chain on `accept`/`modify` decisions to materialize `resulting_files` into the working spec). The Phase-3 carve-out per Plan Phase 3 lines 1860-1865 is that the SKILL.md prose narrates but does not yet implement the delegation toggle and the rejection-flow audit-trail richness beyond the simplest "decision: reject" front-matter line. Phase 7 widening surfaces the full contract in spec.md so a clean re-implementation against the spec alone derives both halves correctly.

This proposal codifies the architecture-level split. Mechanism details (specific file-system call sequencing, IOResult composition primitives, the `_write_and_move_per_decision` accumulator shape) remain implementation choices per the existing architecture-vs-mechanism discipline at constraints.md §"Code style".

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Sub-command lifecycle"**: append a new paragraph immediately after the `revise` payload-validation paragraph (added by the companion finding above) codifying the lifecycle and responsibility separation:

> **`revise` lifecycle and responsibility separation (PROPOSAL.md §"`revise`" lines 2405-2522).** The `revise` LLM-driven per-proposal acceptance dialogue, the per-`## Proposal` accept/modify/reject decision-and-rationale capture, the `modify`-decision iteration to convergence, the apply-to-all-remaining-proposals delegation toggle, the optional `<revision-steering-intent>` disambiguation (warn-and-proceed when steering-intent contains spec content rather than per-proposal decision-steering), and the retry-on-exit-4 handshake are skill-prose responsibilities under `revise/SKILL.md`; `bin/revise.py` MUST NOT invoke the template prompt, the LLM, or the interactive confirmation flow. After the skill assembles a `revise_input.schema.json`-conforming payload, the wrapper performs deterministic file-shaping: (a) it MUST fail hard with `PreconditionError` (exit 3) when `<spec-target>/proposed_changes/` contains no in-flight proposal files (the skill-owned `proposed_changes/README.md` does not count); (b) proposals are processed in YAML front-matter `created_at` creation-time order (oldest first), with lexicographic filename as tiebreaker; within each file, `## Proposal` sections are processed in document order; (c) per v038 D1 (Statement B), a new `<spec-target>/history/vNNN/` is cut on every successful revise invocation — when at least one decision is `accept` or `modify`, the working-spec files named in those decisions' `resulting_files[]` are updated in place before the snapshot; when every decision is `reject`, the new version's spec files are byte-identical copies of the prior version's spec files (rejection-flow audit trail per Plan Phase 7 line 3383); (d) on every cut, `<spec-target>/history/vNNN/` snapshots every template-declared spec file byte-identically as it stands post-update (or post-no-update, on all-reject); (e) every processed proposal moves byte-identically from `<spec-target>/proposed_changes/<stem>.md` to `<spec-target>/history/vNNN/proposed_changes/<stem>.md` — the filename stem is preserved including any `-N` collision-disambiguation suffix per the §"Proposed-change and revision file formats" filename-stem rule (v017 Q7); (f) every processed proposal gets a paired `<stem>-revision.md` written to the same `history/vNNN/proposed_changes/` directory using the same stem; (g) after successful completion `<spec-target>/proposed_changes/` MUST be empty of in-flight proposals (the skill-owned `proposed_changes/README.md` persists). The author identifier for the revision-file `author_llm` field follows the unified precedence already codified in §"Author identifier resolution".

## Proposal: Revision file format

### Target specification files

- SPECIFICATION/spec.md

### Summary

Extend spec.md §"Proposed-change and revision file formats" with the architecture-level required content of `<topic>-revision.md`: the YAML front-matter fields (proposal, decision, revised_at, author_human, author_llm), the always-required `## Decision and Rationale` section, and three decision-type-conditional sections — `## Modifications` when `decision: modify`, `## Resulting Changes` when `decision: accept` or `modify`, and `## Rejection Notes` when `decision: reject`. The `## Rejection Notes` requirement is what gives the rejection flow its preserved audit-trail richness per Plan Phase 7 line 3383 ("rejection flow preserving audit trail").

### Motivation

PROPOSAL.md §"Revision file format" lines 3107-3167 define the canonical revision-file shape. The seeded SPECIFICATION/spec.md currently carries only the one-sentence summary at line 59 ("It records the per-proposal accept/reject decision plus the resulting spec edits"). That summary is too thin for a clean re-implementation: the per-decision-type section requirements, the author-identifier precedence binding for `author_llm`, and the rejection-flow audit-trail expectation cannot be derived from the summary alone. Phase 7's widening must surface the full architecture-level format in spec.md.

The Phase-3 minimum-viable wrapper currently writes a three-key front-matter (`proposal`, `decision`, `topic`-derived from the input dict's `proposal_topic` key) plus a `## Decision and Rationale` section, per `livespec/commands/revise.py`'s `_compose_revision_body` helper (lines 198-221). The widened wrapper MUST emit the full front-matter triple (`revised_at`, `author_human`, `author_llm`) plus the decision-type-conditional sections; the v033 D5b implementation cycles in sub-step 5.c land that widening Red→Green per behavior.

The unified file-level vs. line-level audit-trail discipline (revisions emit prose-form Modifications and Resulting Changes; line-level unified diffs are explicitly out of scope per PROPOSAL §"Revision file format" line 3154 — "line-number anchors are fragile across multi-proposal revises") is captured here so the spec is implementation-language-neutral and a future re-implementation in another language cannot mistakenly emit unified-diff-style modifications.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Proposed-change and revision file formats"**: replace the existing one-sentence summary paragraph at line 59 (currently: `<spec-target>/proposed_changes/<topic>-revision.md is the paired revision record produced by revise. It records the per-proposal accept/reject decision plus the resulting spec edits. After the revise commit lands, both files move atomically into <spec-target>/history/v<NNN>/proposed_changes/.`) with the full architecture-level format paragraph and a new sub-paragraph titled **Revision file format**:

> `<spec-target>/proposed_changes/<topic>-revision.md` is the paired revision record produced by `revise`. After the revise commit lands, both files move atomically into `<spec-target>/history/v<NNN>/proposed_changes/`.
>
> **Revision file format (PROPOSAL.md §"Revision file format" lines 3107-3167).** Each `<topic>-revision.md` MUST contain, in order: (1) YAML front-matter with the keys `proposal: <stem>.md` (the paired proposed-change filename stem, including any `-N` collision-disambiguation suffix per the filename-stem rule above), `decision: accept | modify | reject`, `revised_at: <UTC ISO-8601 seconds>`, `author_human: <git user.name and user.email per livespec.io.git.get_git_user(), or the literal "unknown" when git is available but either config value is unset>`, and `author_llm: <resolved author id per the unified precedence in §"Author identifier resolution">`; (2) `## Decision and Rationale` — always required; one paragraph explaining the decision; (3) `## Modifications` — REQUIRED when `decision: modify`; prose-form description of how the proposal was changed before incorporation, with optional short fenced before/after excerpts permitted for hyper-local clarity (line-number-anchored unified diffs are NOT used here per PROPOSAL §"Revision file format" line 3154 — they are fragile across multi-proposal revises); (4) `## Resulting Changes` — REQUIRED when `decision: accept` or `modify`; names the specification files modified and lists the sections changed; (5) `## Rejection Notes` — REQUIRED when `decision: reject`; explains what would need to change about the proposal for it to be acceptable in a future revision (this is the rejection-flow audit-trail richness Plan Phase 7 line 3383 mandates). For automated skill-tool-authored revisions (e.g., `seed` auto-capture, `out-of-band-edits` auto-backfill), `author_llm` takes the convention value `livespec-seed` / `livespec-doctor`, hardcoded by the wrapper and bypassing the precedence above.
