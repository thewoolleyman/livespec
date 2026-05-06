# Acknowledgement: proposal-critique-v01

## Provenance

- **Proposed change:** `proposal-critique-v01.md` (in this directory)
- **Author of critique:** Claude Opus 4.7 (1M context)
- **Revised by:** Claude Opus 4.7 (1M context), acting as spec author
- **Revised at:** 2026-04-20 (UTC)
- **History:** omitted per instruction. This revision is applied to
  pre-seed brainstorming material, not yet a versioned spec, so no
  `vNNN/` history entry is created. The critique file remains in place
  rather than being moved to history.

## Summary of dispositions

| Severity | Count | Accepted | Modified-on-accept | Deferred to v2 | Rejected |
|---|---|---|---|---|---|
| Major (blocks seeding) | 12 | 11 | 0 | 1 | 0 |
| Significant | 8 | 6 | 0 | 2 | 0 |
| Smaller / cleanup | 14 | 14 | 0 | 0 | 0 |

Where a change is accepted it has been applied to `PROPOSAL.md` and,
where the lifecycle is involved, to
`2026-04-19-nlspec-lifecycle-diagram.md`. Deferred items are recorded
as explicit v1 non-goals in the revised proposal.

## Disposition by item

### Major gaps

**M1. Runtime / packaging model is undefined.**
Decision: **Accepted.** Rationale: Without this, no other behavior is
anchored. Resolution: `livespec` is specified as a Claude Code skill
delivered project-local under `.claude/skills/livespec/` or
user-global under `~/.claude/skills/livespec/`, with a single skill
entry point that accepts a sub-command argument. Documented in the new
"Runtime and packaging" section.

**M2. Template mechanism is deferred but already required.**
Decision: **Accepted with scope split.** Rationale: The critique
correctly identifies the contradiction. Resolution: the *pluggable*
template mechanism remains a v1 non-goal, but the *built-in* `livespec`
template is now specified in full. The `template` config field accepts
either a built-in name (`livespec`, `openspec`) or a path to a custom
template directory; `custom` is removed as an enum value.

**M3. `.livespec.jsonc` schema underspecified.**
Decision: **Accepted.** Rationale: Required for both static checks and
seed behavior. Resolution: full schema, defaults, and absence-behavior
documented in the new "Configuration" section.

**M4. Versioning semantics are undefined.**
Decision: **Accepted.** Rationale: Versioning is load-bearing for
history, doctor's diff check, and acknowledgement filenames.
Resolution: cadence, format, and edge cases (empty revise, all-rejected
revise) all specified in the new "Versioning" section.

**M5. Proposed-change and acknowledgement formats undefined.**
Decision: **Accepted.** Rationale: Without a contract there is nothing
for `doctor` to check and no consistent input for `revise`. Resolution:
both file formats specified with required front-matter and section
headings.

**M6. `revise` decision authority is ambiguous.**
Decision: **Accepted.** Rationale: This is the most consequential
human-in-the-loop question; resolution required. Resolution: the LLM
proposes accept/reject/modify decisions per proposal; the user is
prompted to confirm or override before any history is written.
Documented in the revised `revise` sub-command section.

**M7. Doctor static-check inventory is illustrative.**
Decision: **Accepted.** Rationale: Doctor cannot be implemented from a
list ending in `etc.`. Resolution: full enumeration with exit-code
semantics and the "doctor before/after" rule narrowed to exclude
`help`, `doctor` itself, and the static-check phase of any command.

**M8. `seed` post-state is unspecified.**
Decision: **Accepted.** Rationale: `seed` is the bootstrap-of-the-
bootstrap and currently nondeterministic. Resolution: the post-state
file inventory, content contract, idempotency behavior, and version
relationship (seed creates `v001` directly) are specified.

**M9. NLSpec progressive disclosure is hand-waved.**
Decision: **Accepted.** Rationale: Without a sub-command-to-subset
mapping, "progressive disclosure" is aspirational only. Resolution:
explicit mapping table added (the proposal's own embedded guidelines
recommend tables for mappings).

**M10. Testing approach is under-defined and language-coupled.**
Decision: **Accepted.** Rationale: Hard-coding python and `claude
code` couples the spec to current dev environment. Resolution: testing
section pulled out and reframed in language-neutral terms; the
`section_drift_prevention` meta-test is given a concrete contract.

**M11. Holdout scenarios are mentioned but not modeled.**
Decision: **Accepted.** Rationale: If the rationale for splitting
`scenarios.md` cites holdouts, the marking mechanism must follow.
Resolution: holdout marking specified via per-scenario annotation. The
*evaluation runner* for holdouts remains a v1 non-goal.

**M12. Drift checks have no referent.**
Decision: **Accepted.** Rationale: "Drift" is meaningless without
named endpoints. Resolution: three drift kinds defined (spec ↔
implementation, spec ↔ history, internal self-consistency).

### Significant gaps

**S13. Multi-specification per project.**
Decision: **Deferred to v2.** Rationale: The critique is correct that
this is currently underspecified, but adding it now expands v1 surface
significantly. Resolution: explicit non-goal in revised proposal;
schema retains a single `specification_dir` field rather than an array,
to avoid baking-in a model that v2 may need to revise.

**S14. Out-of-band edits.**
Decision: **Accepted.** Rationale: Real-world editing happens; doctor
should make the recovery deterministic. Resolution: doctor's "diff
between current and latest history version" check now includes the
prompted-proposed-change flow with full content contract.

**S15. Critique authorship and topic collisions.**
Decision: **Accepted.** Rationale: Small but ambiguous as written.
Resolution: author detection and topic-collision rules specified in
the revised `critique` section.

**S16. Per-template critique prompts.**
Decision: **Accepted.** Rationale: Small. Resolution: critique prompt
loading order documented (`.livespec.jsonc` → template default →
built-in default).

**S17. Identity / git integration.**
Decision: **Deferred to v2.** Rationale: The critique offers two
options; for v1 the explicit position is *livespec writes files only,
never invokes git*. The user's git workflow remains entirely external.
Resolution: stated as an explicit non-goal.

**S18. Cross-file referencing within a single spec.**
Decision: **Accepted.** Rationale: Without referencing rules the
multi-file partitioning re-introduces drift. Resolution: heading-anchor
convention specified for stable cross-file references.

**S19. Definition of Done for v1.**
Decision: **Accepted.** Rationale: The embedded guidelines insist on
this; the proposal must hold itself to its own standard. Resolution:
explicit DoD section added.

**S20. Self-application.**
Decision: **Accepted.** Rationale: Implicit throughout; making it
explicit fixes bootstrap ordering. Resolution: stated as a hard
requirement in DoD.

### Smaller issues

All accepted as cleanups. Specifically:

- Default template name `livespec` confirmed; renaming considered and
  rejected (no obviously better candidate; "livespec template within
  livespec" is acceptable when the context distinguishes them).
- OpenSpec compatibility target version pinned to current public
  OpenSpec at time of writing, with a note that the OpenSpec template
  is sketched only in v1.
- Proposed-change naming at write time uses
  `vNNN-proposed-change-<topic>.md`, where `NNN` is
  `latest_history_version + 1`. Because `revise` MUST process every
  in-flight proposal before a new version can be cut, the version
  prefix is unambiguous at `propose-change` time and no
  intermediate `pending-` prefix is needed.
- Gherkin: ` ```gherkin ` fenced blocks; no specific tooling pinned;
  contract is "renders predictably in Markdown".
- BCP 14 scope: applies wherever a partition contains normative
  requirements, regardless of how many files the template uses.
- `revise <freeform text>`: freeform text is an additional intent
  input applied alongside (not overriding) accept/reject decisions.
- Auto-generated READMEs in `proposed_changes/` and `history/` have a
  defined content contract (purpose paragraph + filename convention
  reference).
- Adaptation list of `livespec-nlspec-spec.md` vs upstream is
  removed from `PROPOSAL.md` and lives only in the guidelines file's
  header (single source of truth).
- Lifecycle diagram updated to include `critique → proposed_changes`
  and `doctor` edges.
- `proposed_changes/` is always empty after a successful `revise`
  (every proposal is either moved to history or, if rejected, recorded
  as a rejection acknowledgement and removed from the working set).
- Acknowledgements record a UTC ISO-8601 `revised_at` timestamp.
- The proposal's own restatement of the embedded guidelines'
  adaptation list is removed (drift risk per the guidelines'
  define-once principle).

## What was rejected

Nothing was rejected outright. Two items (S13, S17) were deferred to
v2 with explicit non-goal annotation rather than accepted, because
adopting them now would significantly expand v1 surface and the
critique itself flagged them as lower-severity.

## Self-consistency check

After applying these revisions to `PROPOSAL.md`, the following
guideline-derived properties were rechecked manually:

- **Two-implementer test on each new normative section:** all sections
  added or revised use BCP 14 keywords or schema-style precision and
  are believed to pass.
- **Recreatability:** with these changes, a competent implementer can
  generate the `livespec` skill and its built-in template from
  `PROPOSAL.md` plus `livespec-nlspec-spec.md` alone, without
  consulting the brainstorming companion files. (The companion files
  remain useful as rationale and prior-art context, but are no longer
  load-bearing for implementation.)
- **Define-once:** the adaptation list for `livespec-nlspec-
  guidelines.md` is now stated only inside that file. The lifecycle
  diagram is the only source for the loop visualization. Versioning
  rules are stated only in the "Versioning" section.
- **Definition of Done present:** yes, in the new "Definition of Done
  (v1)" section.

## Outstanding follow-ups

These are accepted in principle but were not done in this revision and
should be filed as the first batch of `propose-change`s after `seed`:

- Move `subdomains-and-unsolved-routing.md` content into a Boundary
  Clarification appendix in the seeded `spec.md` (per critique's
  closing note).
- Move `prior-art.md` content into `SPECIFICATION/README.md`
  references or a dedicated appendix.
- Collapse `2026-04-19-nlspec-terminology-and-structure-summary.md`
  into a glossary plus a rationale appendix.
- Move `nlspec-spec.md` into `SPECIFICATION/prior-art/` once the
  SPECIFICATION/ directory exists.

These are deliberately not done now because they are spec-content
moves that should happen as part of `seed`, not as part of revising
the proposal itself.
