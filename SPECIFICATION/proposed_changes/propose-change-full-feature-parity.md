## Proposal: Topic canonicalization rules

### Target specification files

- SPECIFICATION/spec.md

### Summary

Replace the placeholder sentence "Topic-canonicalization rules widen in Phase 7." in spec.md §"Proposed-change and revision file formats" with the v015 O3 canonicalization algorithm, codifying the canonical-topic derivation invariant uniformly across direct callers and internal delegates.

### Motivation

Phase 7 sub-step 3 widens `livespec/commands/propose_change.py` to full feature parity with the PROPOSAL.md contract. PROPOSAL.md §"propose-change" v015 O3 (lines 2232-2243) defines the canonicalization rule that governs how an inbound `<topic>` hint becomes the canonical artifact identifier driving filename selection, collision lookup, and front-matter population. The v001 seed left this as a placeholder pending Phase 7; this revision lands the architecture-level rule in spec.md so the wrapper and any future re-implementation are bound to the same invariant.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Proposed-change and revision file formats"**.

Replace the existing placeholder sentence at the end of the first paragraph (currently: "`<spec-target>/proposed_changes/<topic>.md` holds an in-flight change request. The file MUST contain one or more `## Proposal: <name>` sections with `### Target specification files`, `### Summary`, `### Motivation`, and `### Proposed Changes` subsections per PROPOSAL.md §"propose-change". Topic-canonicalization rules widen in Phase 7.") with the full v015 O3 algorithm:

> `<spec-target>/proposed_changes/<topic>.md` holds an in-flight change request. The file MUST contain one or more `## Proposal: <name>` sections with `### Target specification files`, `### Summary`, `### Motivation`, and `### Proposed Changes` subsections per PROPOSAL.md §"propose-change".
>
> **Topic canonicalization (v015 O3).** `propose-change` treats the inbound `<topic>` as a user-facing topic hint, not yet the canonical artifact identifier. Before collision lookup, filename selection, or front-matter population, the wrapper canonicalizes the topic via: lowercase → replace every run of non-[a-z0-9] characters with a single hyphen → strip leading and trailing hyphens → truncate to 64 characters. If the result is empty, the wrapper exits 2 with `UsageError`. The canonicalized topic is used uniformly for the output filename, the proposed-change front-matter `topic` field, and the collision-disambiguation namespace. This applies to direct callers and to internal delegates such as `critique`.

## Proposal: Reserve-suffix canonicalization and CLI flag

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Add the `--reserve-suffix <text>` flag to the `propose-change` row of the wrapper-CLI surface table in contracts.md, and codify the v016 P3 / v017 Q1 architecture-level reserve-suffix invariants in spec.md alongside the v015 O3 topic-canonicalization rule.

### Motivation

PROPOSAL.md §"propose-change" v016 P3 (with v017 Q1 trim to invariants-only; lines 2244-2263) requires `bin/propose_change.py` to accept an optional `--reserve-suffix <text>` flag and guarantees that when supplied the canonicalized topic stays within the 64-character cap AND preserves the suffix intact at the end of the result. The CLI surface table in contracts.md does not yet list this flag, and spec.md does not yet codify the invariants. Phase 7 sub-step 3 widens the wrapper to full parity, so both files must reflect the contract. Per the architecture-vs-mechanism discipline, the algorithm details (pre-strip, truncate-and-hyphen-trim, re-append) are deferred to `deferred-items.md` and NOT duplicated here.

### Proposed Changes

Two atomic edits, one per target file.

**SPECIFICATION/contracts.md §"Wrapper CLI surface".** Update the `propose-change` row of the CLI-flags table to list the new `--reserve-suffix` flag among the optional flags. Replace the current row (currently: `| \`propose-change\` | \`--findings-json <path>\`, \`<topic>\` (positional) | \`--author <id>\`, \`--spec-target <path>\`, \`--project-root <path>\` |`) with:

> | `propose-change` | `--findings-json <path>`, `<topic>` (positional) | `--author <id>`, `--reserve-suffix <text>`, `--spec-target <path>`, `--project-root <path>` |

**SPECIFICATION/spec.md §"Proposed-change and revision file formats".** Append a new paragraph immediately after the v015 O3 "Topic canonicalization" paragraph (added by the companion finding above) codifying the v016 P3 / v017 Q1 reserve-suffix invariants:

> **Reserve-suffix canonicalization (v016 P3; PROPOSAL.md scope trimmed to invariants-only in v017 Q1).** `propose-change` accepts an optional `--reserve-suffix <text>` flag (also exposed as a keyword-only parameter on the Python internal API path used by `critique`'s internal delegation). When supplied, canonicalization guarantees that the resulting topic is at most 64 characters AND that the caller-supplied suffix is preserved intact at the end of the result, even when the inbound hint already ends in that suffix (pre-attached case) or when truncation would otherwise clip the suffix. When `--reserve-suffix` is NOT supplied, canonicalization behaves exactly as the v015 O3 rule above. The empty-after-canonicalization `UsageError` (exit 2) continues to apply to the final composed result. The exact algorithm (pre-strip, truncate-and-hyphen-trim, re-append) is codified in `deferred-items.md`'s `static-check-semantics` entry; this spec deliberately does not duplicate the algorithm here, per the architecture-vs-mechanism discipline.

## Proposal: Author identifier resolution and slug transformation

### Target specification files

- SPECIFICATION/spec.md

### Summary

Add a new subsection to spec.md codifying the unified author-precedence chain across `propose-change`/`critique`/`revise`, the v014 N5 author-slug filename transformation, and the `livespec-` prefix convention for skill-auto-generated artifacts.

### Motivation

PROPOSAL.md §"propose-change" lines 2264-2283 define a unified four-step author-identifier precedence chain across all three LLM-driven wrappers, and lines 2284-2301 (v014 N5) define the slug transformation that converts a resolved author value into a filename component while preserving the un-slugged original in YAML front-matter. PROPOSAL.md lines 3057-3068 codify the `livespec-` prefix as a convention (NOT mechanically enforced) so audit trails can visually distinguish skill-auto artifacts from user/LLM-authored ones. None of these are present in the v001 seed. Phase 7 sub-step 3 widens the wrapper to full parity, so spec.md must codify them.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md**: insert a new top-level section `## Author identifier resolution` immediately after the existing `## Proposed-change and revision file formats` section and before the existing `## Testing approach` section.

> ## Author identifier resolution
>
> The file-level `author` field in the resulting proposed-change front-matter is resolved by the unified precedence used across all three LLM-driven wrappers (`propose-change`, `critique`, `revise`):
>
> 1. If `--author <id>` is passed on the CLI and non-empty, use its value.
> 2. Otherwise, if the `LIVESPEC_AUTHOR_LLM` environment variable is set and non-empty, use its value.
> 3. Otherwise, if the LLM self-declared an `author` field in the `proposal_findings.schema.json` payload (file-level, optional) and it is non-empty, use that value.
> 4. Otherwise, use the literal `"unknown-llm"`.
>
> A warning is surfaced via LLM narration whenever fallback (4) is reached.
>
> **Author identifier → filename slug transformation (v014 N5).** When the resolved `author` value is used as a filename component (the raw topic stem passed from `critique`, or any other author-derived filename use in the future), the wrapper transforms it via the following rule: lowercase → replace every run of non-[a-z0-9] characters with a single hyphen → strip leading and trailing hyphens → truncate to 64 characters. The **slug form** is used as the filename component; the **original un-slugged value** is preserved in the YAML front-matter `author` / `author_human` / `author_llm` fields for audit-trail fidelity. The slug rule matches the GFM slug algorithm already used by the `anchor-reference-resolution` doctor-static check. This transformation applies whenever a resolved author value is used to derive a topic hint or filename component. Full semantics (edge cases, interaction with topic canonicalization, collision with already-slugged topic values) are codified in `deferred-items.md`'s `static-check-semantics` entry.
>
> **`livespec-` prefix convention.** Identifiers with the prefix `livespec-` (e.g., `livespec-seed`, `livespec-doctor`) are used by skill-auto-generated artifacts (seed auto-capture, doctor-`out-of-band-edits` backfill). Human authors and LLMs SHOULD NOT use this prefix for their own artifacts so that the audit trail can visually distinguish skill-auto artifacts from user/LLM-authored ones. This is a convention; no mechanical enforcement exists — no schema pattern rejects `livespec-`-prefixed values from user-supplied sources, and no wrapper rejects them on input. Users who deliberately type `livespec-`-prefixed identifiers create self-inflicted audit-trail confusion but nothing breaks.

## Proposal: Collision disambiguation

### Target specification files

- SPECIFICATION/spec.md

### Summary

Extend spec.md §"Proposed-change and revision file formats" to codify the v014 N6 monotonic-integer-suffix collision rule, including the suffix-less-first-file convention, the no-zero-padding rule, and the explicit non-unification with the `out-of-band-edit-<UTC-seconds>.md` naming convention.

### Motivation

PROPOSAL.md §"propose-change" v014 N6 (lines 2326-2343) defines the auto-disambiguation rule when a canonical-topic filename collides with an existing file: append a hyphen-separated monotonic integer suffix starting at `2`, no zero-padding, no user prompt. The note also explicitly distinguishes this convention from the always-appended UTC-timestamp form used by `doctor-out-of-band-edits`. The v001 seed does not codify this; Phase 7 sub-step 3 widens the wrapper to full parity, so spec.md must codify it.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Proposed-change and revision file formats"**: append a new paragraph immediately after the v016 P3 / v017 Q1 reserve-suffix paragraph (added by the companion finding above) codifying the v014 N6 collision-disambiguation rule:

> **Collision disambiguation (v014 N6).** If a file with topic `<canonical-topic>.md` already exists, the wrapper MUST auto-disambiguate by appending a hyphen-separated **monotonic integer suffix starting at `2`**: the first collision becomes `<canonical-topic>-2.md`, the second `<canonical-topic>-3.md`, and so on. No zero-padding is applied (so the tenth collision is `<canonical-topic>-10.md`; alphanumeric sort misordering past nine duplicates is accepted as an extreme edge case). No user prompt for collision. Starting the counter at `2` (not `1`) makes the "this is the second file named `<canonical-topic>`" relationship explicit; the first file is suffix-less by convention. Note: this convention applies to `propose-change` and `critique` filenames. The `out-of-band-edit-<UTC-seconds>.md` filename form used by the `doctor-out-of-band-edits` check is a separate always-appended UTC-timestamp convention (each backfill is a distinct timed event); the two conventions are not unified.

## Proposal: Single-canonicalization invariant and filename-stem distinction

### Target specification files

- SPECIFICATION/spec.md

### Summary

Add an architectural-invariant subsection to spec.md §"Proposed-change and revision file formats" codifying both the v016 P4 single-canonicalization invariant (every `topic` derivation across all creation paths routes through one shared canonicalization) and the v017 Q7 filename-stem-vs-front-matter-`topic` distinction.

### Motivation

PROPOSAL.md lines 3030-3042 (v016 P4) require that the `topic` field's value MUST derive via the same canonicalization rule across ALL creation paths — user-invoked `propose-change`, `critique`'s internal delegation with `-critique` reserve-suffix, and the skill-auto-generated paths (`seed` auto-capture, `doctor-out-of-band-edits` backfill). PROPOSAL.md lines 3044-3055 (v017 Q7) clarify that under v014 N6 the proposed-change filename stem MAY include a `-N` suffix BUT the front-matter `topic` field carries ONLY the canonical topic without the `-N` suffix; revision-pairing walks filename stems, not front-matter `topic` values. Both invariants are architecture-level requirements on the interface (not code-mechanism prescriptions) and must land in spec.md alongside the canonicalization, reserve-suffix, and collision-disambiguation rules already covered by the companion findings.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Proposed-change and revision file formats"**: append a new paragraph immediately after the v014 N6 collision-disambiguation paragraph (added by the companion finding above) codifying the v016 P4 single-canonicalization invariant and the v017 Q7 filename-stem distinction:

> **Single-canonicalization invariant (v016 P4).** The `topic` field's value MUST be derived via the same canonicalization rule across ALL creation paths — user-invoked `propose-change`, `critique`'s internal delegation (which adds the `-critique` reserve-suffix; see the v016 P3 reserve-suffix paragraph above), and skill-auto-generated artifacts (`seed` auto-capture, `doctor-out-of-band-edits` backfill). Implementations MUST route every `topic` derivation through a single shared canonicalization so two `livespec` implementations cannot diverge on the `topic` value for semantically-identical inputs. This is an architecture-level requirement on the interface; the exact code-path mechanism (single helper function vs. anything else) is an implementation choice.
>
> **Filename stem vs. front-matter `topic` distinction (v017 Q7).** Under the v014 N6 collision-disambiguation rule, the proposed-change filename stem may include a `-N` suffix (`foo.md`, `foo-2.md`, `foo-3.md`). The front-matter `topic` field carries ONLY the canonical topic WITHOUT the `-N` suffix — every file sharing a canonical topic shares the same front-matter `topic` value. The `-N` suffix is filename-level disambiguation only. Revision-pairing (per the `revision-to-proposed-change-pairing` doctor-static check) walks filename stems (not front-matter `topic` values); each `<stem>-revision.md` pairs with `<stem>.md` in the same directory.
