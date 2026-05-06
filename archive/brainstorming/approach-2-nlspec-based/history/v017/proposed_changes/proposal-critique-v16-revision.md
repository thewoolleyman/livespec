---
proposal: proposal-critique-v16.md
decision: modify
revised_at: 2026-04-24T04:00:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v16

## Provenance

- **Proposed change:** `proposal-critique-v16.md` — a
  recreatability-and-cross-doc-consistency critique over v016
  focused on nine items (after one mid-interview retraction):
  - Q1: PROPOSAL.md reserve-suffix algorithm diverges from
    deferred-items.md (malformation / incompleteness).
  - Q2: Pre-seed template resolution has no documented mechanism
    (incompleteness).
  - Q3: Import-Linter raise-discipline contract over-restricts
    vs. its English rule (malformation — self-contradictory rule).
  - Q4: Seed post-step recovery flow doesn't document that
    propose-change's post-step also fails (incompleteness /
    ambiguity).
  - Q5-retracted (originally: fake_claude.py vs. check-no-
    inheritance): RETRACTED mid-interview on user pushback —
    hand-rolled mocks comply with all existing livespec Python
    rules by construction; no rule-vs-feature conflict exists.
  - Q5 (was Q6): Seed wrapper behavior when `.livespec.jsonc` is
    present-but-invalid (ambiguity).
  - Q6 (was Q7): Payload-vs-config `template` mismatch exit code
    (incorrectness — wrong exit code).
  - Q7 (was Q8): Revision filename pairing under collision suffix
    (ambiguity).
  - Q8 (was Q9): Grammar typo at PROPOSAL.md line 853
    (malformation).
  - Q9 (was Q10): project-root detection not documented for
    non-resolve_template wrappers (incompleteness).
- **Revised by:** thewoolleyman (human) in dialogue with Claude
  Opus 4.7 (1M context).
- **Revised at:** 2026-04-24 (UTC).
- **Scope:** v016 `PROPOSAL.md` + `deferred-items.md` +
  `python-skill-script-style-requirements.md` → v017 equivalents.
  `livespec-nlspec-spec.md`, `goals-and-non-goals.md`,
  `prior-art.md`, `subdomains-and-unsolved-routing.md`, and the
  2026-04-19 lifecycle/terminology companion docs remain
  unchanged.

## Pass framing

This pass was a **recreatability-and-cross-doc-consistency**
critique grounded in the NLSpec test: could a competent
implementer produce a working livespec without being forced to
guess between conflicting rules or invent semantics the docs
leave unspecified?

The accepted changes all preserve earlier structural decisions
rather than reopening them:

- **Q1** preserves v016 P3's reserve-suffix mechanism by trimming
  PROPOSAL.md to invariants-only and keeping deferred-items.md
  as the single source of algorithm truth.
- **Q2** preserves v011 K2's template-resolution seam and v014
  N1's pre-seed dialogue by extending `bin/resolve_template.py`
  with an optional `--template` flag that bypasses
  `.livespec.jsonc` lookup without changing the stdout contract.
- **Q3** preserves the raise-discipline intent by retracting
  v012 L15a's over-reach claim and keeping the hand-written
  `check-no-raise-outside-io` as the raise-site enforcement
  surface; type-annotation and match-pattern imports of error
  types are no longer forbidden.
- **Q4** preserves v014 N7's recovery flow and tooling by adding
  an explicit narration contract for propose-change's expected
  exit-3 during recovery and the implicit-until-now git-commit
  obligation between propose-change and revise.
- **Q5** preserves the v016 P2 wrapper-owned bootstrap by adding
  explicit third-branch handling (present-but-invalid → exit 3
  with PreconditionError) that matches the existing non-doctor
  fail-fast rule.
- **Q6** preserves the exit-code classifier's LLM-facing clarity
  by reclassifying the payload-vs-config template mismatch from
  UsageError (2) to PreconditionError (3).
- **Q7** preserves v014 N6's collision-suffix convention and
  v015 O3's canonical-topic separation by clarifying that
  filename stem and front-matter `topic` field are distinct and
  that revision-pairing uses the filename stem.
- **Q8** pure grammatical cleanup.
- **Q9** extends the v011 K2 `--project-root` pattern uniformly
  across every wrapper that operates on project state.

## Governing principles reinforced

- **PROPOSAL.md owns contracts; deferred-items.md owns
  algorithms.** Q1 re-applies the architecture-vs-mechanism
  discipline: PROPOSAL.md states invariants; the algorithm is
  codified in the `static-check-semantics` deferred entry.
- **Template resolution stays in one executable.** Q2 extends
  the existing `bin/resolve_template.py` seam rather than adding
  a second wrapper or migrating resolution logic into SKILL.md
  prose.
- **English rules and their mechanical encodings must agree.**
  Q3 retracts a contract whose English rule was self-
  contradictory and whose illustrative TOML encoded only one
  reading. Hand-written `check-no-raise-outside-io` carries the
  raise-site work alone; the import-surface portion of that
  discipline is not enforceable via Import-Linter.
- **Recovery flows MUST be fully narrated.** Q4 surfaces the
  exit-3-during-recovery behavior that was previously implicit
  and names the git-commit obligation that was previously
  unstated.
- **Central canonicalization stays central.** Q7 clarifies the
  filename-stem vs. front-matter `topic` distinction without
  changing either convention's shape.
- **Uniform flag surfaces across wrappers.** Q9 extends the
  v011 K2 `--project-root` pattern uniformly so every wrapper
  presents the same project-root detection contract.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| Q1 | malformation (self-contradiction) / incompleteness | Accept A — trim PROPOSAL.md §"propose-change → Reserve-suffix canonicalization" to a terse invariants-only statement (≤64 chars, suffix preserved intact regardless of pre-attachment or truncation-clip, empty → UsageError). Delegate the algorithm (pre-strip, truncate-and-hyphen-trim, re-append) to `deferred-items.md`'s `static-check-semantics` entry. |
| Q2 | incompleteness | Accept A — extend `bin/resolve_template.py` with an optional `--template <value>` flag. When supplied, the wrapper bypasses `.livespec.jsonc` lookup entirely and resolves the value directly (built-in name → `<bundle-root>/specification-templates/<name>/`; path → relative to `--project-root`). `seed/SKILL.md` prose uses the flag for pre-seed template resolution. v011 K2 v2+ extensibility shield extended to cover `--template`'s stability contract. |
| Q3 | malformation (self-contradictory English rule) | Accept A — retract v012 L15a's "replaces the import-surface portion of `check-no-raise-outside-io`" claim. Drop the third Import-Linter contract (`livespec-errors-raise-discipline-imports`) from the style doc's illustrative TOML. Rewrite rule 3 to scope raise-discipline to raise-site enforcement only (hand-written `check-no-raise-outside-io`). Error types MAY be imported anywhere they are referenced in annotations, match patterns, or attribute access. |
| Q4 | incompleteness / ambiguity | Accept A — extend PROPOSAL.md §"seed → Post-step doctor-static failure recovery" with an explicit narration contract: propose-change's post-step will fail during recovery and exit 3, but the proposed-change file IS on disk; the user MUST commit the partial state before running revise (so `doctor-out-of-band-edits` doesn't trip the pre-backfill guard); propose-change's SKILL.md prose narrates the exit-3 path distinctly when seed-recovery-in-progress is detectable. Widen `skill-md-prose-authoring` deferred entry. |
| Q5 | ambiguity | Accept A — add explicit third-branch handling in PROPOSAL.md §"seed" below the v016 P2 paragraph: if `.livespec.jsonc` is present but malformed or schema-invalid, seed exits 3 with `PreconditionError` citing the specific parse error or schema-violation path. Preserves the existing non-doctor fail-fast rule (§"Doctor → Bootstrap lenience"); never silently overwrites a user's manual edit. |
| Q6 | incorrectness (wrong exit code) | Accept A — update the v016 P2 mismatch clause: "the payload's `template` value MUST match the on-disk `template` value or the wrapper exits `3` with a `PreconditionError` describing the conflict." Payload is a wire-format input, not a CLI-argument surface; mismatch is an incompatible state between two validated inputs. |
| Q7 | ambiguity | Accept A — add explicit clarification in PROPOSAL.md §"revise" and §"Proposed-change file format": collision-suffix lives in the filename stem; paired revision uses the full filename stem (`foo-2-revision.md`, `foo-3-revision.md`). Front-matter `topic` field carries the canonical topic without the `-N` suffix — the suffix is filename-level disambiguation only. Widen `deferred-items.md`'s `static-check-semantics` entry to codify that `revision-to-proposed-change-pairing` walks filename stems. |
| Q8 | malformation (grammar typo) | Accept A — rewrite PROPOSAL.md line 853 as "Every doctor-static check's path references are parameterized against `DoctorContext.spec_root` (per v009 I7)…" |
| Q9 | incompleteness | Accept A — add a uniform project-root detection contract to PROPOSAL.md §"Sub-command dispatch and invocation chain": every wrapper operating on project state (`bin/seed.py`, `bin/propose_change.py`, `bin/critique.py`, `bin/revise.py`, `bin/prune_history.py`, `bin/doctor_static.py`, and `bin/resolve_template.py`) accepts `--project-root <path>` with default `Path.cwd()`. Upward-walk logic for `.livespec.jsonc` lives in `livespec.io.fs` as a shared helper. |

## Disposition by item

### Q1. Reserve-suffix canonicalization algorithm diverges (malformation / incompleteness → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"propose-change → Reserve-suffix canonicalization"
is rewritten to state invariants without sketching the
algorithm. The new text:

> `bin/propose_change.py` accepts an optional
> `--reserve-suffix <text>` flag (also exposed as a
> keyword-only parameter on the Python internal API used by
> `critique`'s internal delegation). When supplied,
> canonicalization guarantees that the resulting topic is at
> most 64 characters AND that the caller-supplied suffix is
> preserved intact at the end of the result, even when the
> inbound hint already ends in that suffix or when truncation
> would otherwise clip it. When `--reserve-suffix` is NOT
> supplied, canonicalization behaves exactly as v015 O3
> defined. The empty-after-canonicalization `UsageError`
> (exit 2) rule continues to apply to the final composed
> result. The exact algorithm (pre-strip, truncate-and-
> hyphen-trim, re-append) is codified in `deferred-items.md`'s
> `static-check-semantics` entry.

`deferred-items.md`'s `static-check-semantics` entry remains
the single source of algorithm truth. No changes to the
algorithm itself; the pre-strip and trailing-hyphen-strip
steps plus the worked examples stay as they are.

### Q2. Pre-seed template resolution mechanism (incompleteness → accepted, option A)

Accepted as proposed.

`bin/resolve_template.py` gains an optional `--template <value>`
flag. Contract:

- When supplied: the wrapper bypasses `.livespec.jsonc` lookup
  entirely and resolves `<value>` directly. Built-in names
  (`livespec`, `minimal`) resolve to
  `<bundle-root>/specification-templates/<name>/`. Any other
  string is treated as a path relative to `--project-root` and
  validated the same way the on-disk-config path is validated
  today (directory exists AND contains `template.json`).
- When not supplied: the wrapper behaves exactly as v011 K2
  defines (walks upward from `--project-root` looking for
  `.livespec.jsonc`; exits 3 if not found).

Stdout contract unchanged: exactly one line, the resolved
absolute POSIX path, trailing `\n`. Exit codes unchanged.

`seed/SKILL.md` prose invokes
`bin/resolve_template.py --project-root . --template <chosen>`
as its pre-seed template-resolution step. Then follows the
normal two-step dispatch: Read `<resolved-path>/prompts/seed.md`
and use it as the template prompt.

v011 K2's v2+-extensibility-shield paragraph is extended to
cover `--template`'s stability contract.

`skill-md-prose-authoring` and `template-prompt-authoring`
deferred entries are widened to reference the pre-seed
`--template` flag path.

### Q3. Import-Linter raise-discipline contract over-restricts (malformation → accepted, option A)

Accepted as proposed.

The style doc §"Import-Linter contracts (minimum
configuration)" is rewritten:

- The third contract (`livespec-errors-raise-discipline-imports`)
  is removed from the illustrative TOML. The minimum-
  configuration example now has two contracts: purity (first)
  and layered architecture (second).
- English rule 3 is rewritten:

  > 3. `LivespecError` raise-sites are restricted to
  >    `livespec.io.*` and `livespec.errors` (enforced by the
  >    hand-written `check-no-raise-outside-io` raise-site
  >    check). `livespec.errors` MAY be imported from any module
  >    that needs to reference `LivespecError` or a subclass in
  >    a type annotation, `match` pattern, or attribute access
  >    (e.g., `err.exit_code`). Import-Linter is NOT used for
  >    the raise-discipline import surface; raise-site AST
  >    enforcement is the single enforcement point.

- The v012 L15a "replaces the import-surface portion of
  `check-no-raise-outside-io`" claim is retracted. Style doc's
  Enforcement-suite target list updates
  `check-no-raise-outside-io`'s scope description to "raise-site
  enforcement only (no import-surface coverage; LivespecError
  type-annotation and match-pattern imports are permitted
  anywhere)."

- `deferred-items.md`'s `static-check-semantics` entry
  (Import-Linter contract semantics subsection) drops the third
  contract and updates the text to reflect that Import-Linter
  covers only purity and layered-architecture now.

- `deferred-items.md`'s `enforcement-check-scripts` entry
  widens `check-no-raise-outside-io`'s scope note accordingly.

### Q4. Seed post-step recovery flow — propose-change post-step also fails (incompleteness / ambiguity → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"seed → Post-step doctor-static failure recovery"
is extended with an explicit narration contract:

> **Recovery-flow expectations.** Propose-change's own post-step
> doctor-static will trip the same findings that tripped seed's
> post-step, so propose-change ALSO exits 3. This is the expected
> behavior in the sequential-lifecycle flow: sub-command logic
> has already written the proposed-change file to
> `<spec-root>/proposed_changes/`, and the
> partial-state-commit-and-proceed pattern from §"Wrapper-side:
> deterministic lifecycle" applies.
>
> Before running revise, the user MUST `git commit` the partial
> state (the just-written proposed-change file plus any earlier
> seed-written files) so that the `doctor-out-of-band-edits`
> check on the next invocation does not trip its pre-backfill
> guard. livespec does NOT write to git itself (per §"Git"); the
> commit is a user action.
>
> Then `/livespec:revise --skip-pre-check` applies the
> proposed-change and cuts `v002`; revise's post-step runs
> against the now-fixed state and passes.
>
> `propose-change/SKILL.md` prose narrates the exit-3 path
> distinctly when the narrator can detect the seed-recovery-in-
> progress state (heuristic: no `vNNN` beyond `v001` exists AND
> pre-check was skipped). When that state cannot be detected,
> the generic exit-3 narration is used; the user is expected to
> recognize the recovery path from the narration seed's
> SKILL.md emitted earlier.

`skill-md-prose-authoring` deferred entry widens to cover this
dual narration contract.

### Q5. Seed wrapper behavior when `.livespec.jsonc` is present-but-invalid (ambiguity → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"seed" gains an explicit third-branch clause
immediately below the v016 P2 paragraph:

> **Present-but-invalid `.livespec.jsonc`.** If
> `.livespec.jsonc` is present at the project root but
> malformed (JSONC parse failure) or schema-invalid (parses but
> fails `livespec_config.schema.json`), the wrapper exits `3`
> with a `PreconditionError` citing the specific parse error or
> schema-violation path. The user's corrective action is to fix
> or delete the broken `.livespec.jsonc` before re-running
> seed. (Seed's idempotency refusal may also prevent re-running
> if template-declared target files already exist — the user
> fixes both conditions.) This preserves the non-doctor
> fail-fast rule (see §"Doctor → Bootstrap lenience") and never
> silently overwrites a user's manual edit.

### Q6. Payload-vs-config `template` mismatch exit code (incorrectness → accepted, option A)

Accepted as proposed.

The v016 P2 mismatch clause in PROPOSAL.md §"seed" is updated:

> …the payload's `template` value MUST match the on-disk
> `template` value or the wrapper exits `3` with a
> `PreconditionError` describing the conflict.

Exit 2 (UsageError) is reserved for flag / arg-count / malformed-
invocation errors. A validated JSON payload disagreeing with a
validated on-disk config is the "incompatible state" category
covered by exit 3.

### Q7. Revision filename pairing under collision suffix (ambiguity → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"revise" gains a clarification subsection (or a
clarifying paragraph in the existing revise body), and
§"Proposed-change file format" gains matching text:

> **Filename stem vs. front-matter `topic` distinction.** Under
> v014 N6 collision disambiguation, the proposed-change
> filename stem includes the `-N` suffix (`foo-2.md`,
> `foo-3.md`, …). The paired revision's filename uses the full
> filename stem: `foo-2-revision.md`, `foo-3-revision.md`. This
> is distinct from the front-matter `topic` field, which carries
> the canonical topic WITHOUT the `-N` suffix per v016 P4
> (the `-N` suffix is filename-level disambiguation only; every
> file of a given canonical topic shares the same front-matter
> `topic` value).

`deferred-items.md`'s `static-check-semantics` entry is widened
to codify that the `revision-to-proposed-change-pairing` check
walks filename stems (not front-matter `topic` values) for
pairing. The pairing algorithm: for every
`<stem>-revision.md`, verify `<stem>.md` exists in the same
directory.

### Q8. Grammar typo at PROPOSAL.md line 853 (malformation → accepted, option A)

Accepted as proposed.

Rewrite:

- **Before:** "The every doctor-static check's path references
  parameterize against `DoctorContext.spec_root` (per v009
  I7)…"
- **After:** "Every doctor-static check's path references are
  parameterized against `DoctorContext.spec_root` (per v009
  I7)…"

### Q9. Project-root detection for every wrapper (incompleteness → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"Sub-command dispatch and invocation chain" gains
a uniform project-root detection contract:

> **Project-root detection contract.** Every wrapper that
> operates on project state (`bin/seed.py`,
> `bin/propose_change.py`, `bin/critique.py`, `bin/revise.py`,
> `bin/prune_history.py`, `bin/doctor_static.py`, and
> `bin/resolve_template.py`) accepts `--project-root <path>` as
> an optional CLI flag with default `Path.cwd()`. The project
> root anchors `<spec-root>/` resolution and (for every wrapper
> except `bin/seed.py`, which runs before `.livespec.jsonc`
> exists) the upward walk to find `.livespec.jsonc`. The
> upward-walk logic lives in `livespec.io.fs` as a shared
> helper reused by every wrapper and by
> `livespec.doctor.run_static`.

`resolve_template.py`'s existing `--project-root` contract
(PROPOSAL.md §"Template resolution contract") is unchanged;
every other wrapper matches the same flag name, default, and
semantics.

## Deferred-items inventory (carried forward + scope-widened + new)

Per the deferred-items discipline, every carried-forward item is
enumerated below.

**Carried forward unchanged from v016:**

- `python-style-doc-into-constraints`
- `returns-pyright-plugin-disposition`
- `claude-md-prose`
- `basedpyright-vs-pyright`
- `user-hosted-custom-templates`
- `companion-docs-mapping`
- `front-matter-parser`
- `local-bundled-model-e2e`
- `end-to-end-integration-test`

**Scope-widened in v017:**

- `static-check-semantics`
  - Q1: reserve-suffix algorithm is now the sole source-of-
    truth for the pre-strip + truncate-and-hyphen-trim +
    re-append procedure (PROPOSAL.md's sketch is trimmed to
    invariants-only). No algorithm change; the scope-widening
    is that PROPOSAL.md no longer duplicates the algorithm.
  - Q3: Import-Linter contract-semantics subsection updated —
    only two contracts now (purity + layered architecture).
    The third (raise-discipline-imports) was removed. Updated
    text notes that `check-no-raise-outside-io` covers
    raise-site enforcement only and type-annotation / match-
    pattern imports of error types are permitted anywhere.
  - Q7: `revision-to-proposed-change-pairing` algorithm
    codified as filename-stem walk — for every
    `<stem>-revision.md` in a `history/vNNN/proposed_changes/`
    directory, verify `<stem>.md` exists. Note explicitly that
    `<stem>` is the filename stem (including any collision
    `-N` suffix), distinct from the front-matter `topic`
    field's canonical value.
  - Q9: uniform `--project-root` contract across every wrapper
    recorded (the upward-walk helper in `livespec.io.fs` is
    cross-referenced; shared between all wrappers and the
    doctor-static orchestrator).

- `skill-md-prose-authoring`
  - Q2: `seed/SKILL.md` pre-seed prose MUST invoke
    `bin/resolve_template.py --project-root . --template
    <chosen>` to resolve the template path before Read-fetching
    `prompts/seed.md`. The v014 N1 pre-seed dialogue path is
    codified as using this flag.
  - Q4: recovery-flow narration contract — propose-change's
    SKILL.md prose narrates the exit-3 path distinctly when
    seed-recovery-in-progress is detectable (no vNNN beyond
    v001 AND pre-check was skipped); otherwise generic exit-3
    narration applies and the user recognizes the recovery path
    from seed's earlier narration. Seed's SKILL.md prose in
    the post-step-failure recovery narration MUST state the
    explicit git-commit step between propose-change and
    revise.

- `template-prompt-authoring`
  - Q2: the pre-seed flow's reliance on
    `resolve_template.py --template <chosen>` is a template-
    agnostic surface; every template's `prompts/seed.md`
    authoring proceeds unchanged, but the SKILL.md prose that
    dispatches to the template's seed prompt is the Q2-aware
    path.

- `enforcement-check-scripts`
  - Q3: `dev-tooling/checks/no_raise_outside_io.py`'s scope
    expands back to cover the raise-discipline fully (raise-
    site enforcement is the sole enforcement point; the v012
    L15a import-surface delegation to Import-Linter is
    retracted). Style doc §"Enforcement suite" target list
    updates `check-no-raise-outside-io`'s description.

- `task-runner-and-ci-config`
  - Q3: `pyproject.toml`'s `[tool.importlinter]` section
    narrows from three contracts to two. The third L15a-
    proposed contract (raise-discipline import surface) is
    retracted.

**New in v017:**

None.

**Removed in v017:**

None.

## Self-consistency check

Post-apply invariants rechecked against the working docs:

- PROPOSAL.md §"propose-change → Reserve-suffix canonicalization"
  states invariants only; algorithm is cross-referenced to
  `deferred-items.md`'s `static-check-semantics` entry.
- `bin/resolve_template.py`'s v011 K2 §"Template resolution
  contract" and the §"Per-sub-command SKILL.md body structure"
  step 4 documentation are updated to cover the pre-seed
  `--template <value>` flag.
- Style doc §"Import-Linter contracts (minimum configuration)"
  lists two contracts (not three); authoritative-rules
  enumeration has only two rules; rule 3 retires to a pure
  cross-reference to `check-no-raise-outside-io`.
- Style doc §"Enforcement suite" target list text for
  `check-no-raise-outside-io` reflects the raise-site-only
  scope.
- PROPOSAL.md §"seed" has the v016 P2 paragraph plus the new
  third-branch present-but-invalid handling (Q5) and the
  updated payload-vs-config mismatch exit code (Q6, exit 3).
- PROPOSAL.md §"seed → Post-step doctor-static failure
  recovery" documents the propose-change exit-3-during-recovery
  expectation and the git-commit obligation.
- PROPOSAL.md §"revise" and §"Proposed-change file format" both
  carry the filename-stem vs. front-matter `topic` distinction.
- PROPOSAL.md line 853 reads "Every doctor-static check's…
  are parameterized against…".
- PROPOSAL.md §"Sub-command dispatch and invocation chain"
  carries the uniform `--project-root` contract; every wrapper's
  section either cross-references it or states the flag's
  availability.

Follow-up review passes after the initial apply phase:

- **Careful-review pass 1** (4 findings, all landed):
  1. Revision-file "touched 5 existing entries" claim was
     off-by-one (Q5 affects seed wrapper behavior, not
     schemas). Corrected to "touched 4" initially (later
     re-revised to 5 once pass 3 identified
     `task-runner-and-ci-config` as a scope-widened entry).
  2. PROPOSAL.md §"critique" still duplicated the reserve-
     suffix algorithm (steps 1-3, step 4 truncation math,
     worked examples) despite Q1's invariants-only trim.
     Rewrote the critique section to reference
     `deferred-items.md` for the algorithm and keep only
     informal summary (short-stem / long-stem / pre-attached-
     suffix behaviors).
  3. `deferred-items.md` item-schema version range stopped
     at v014 (same drift pattern v012 pass 3 fixed for other
     entries). Extended to include v015 / v016 / v017.
  4. Revision-file deferred-items inventory removed the
     spurious `wrapper-input-schemas` entry (no widening
     occurs there in v017).

- **Careful-review pass 2** (3 findings, all landed):
  1. PROPOSAL.md §"Per-sub-command SKILL.md body structure"
     step 4 ("Resolve + invoke a template prompt") did not
     mention the v017 Q2 `--template` flag path used
     pre-seed. Updated the dispatch description to cover
     both normal and pre-seed flows.
  2. `deferred-items.md`'s `static-check-semantics` entry
     AST-checks list described `check-no-raise-outside-io`
     as "(raise-site portion only per v012 L15a; import-
     surface portion delegated to `check-imports-architecture`)"
     — stale post-v017 Q3. Rewrote to note the v017 Q3
     retraction and `check-no-raise-outside-io`'s full
     raise-discipline ownership.
  3. `deferred-items.md`'s `task-runner-and-ci-config` body
     paragraph on Import-Linter mise-pin still described
     three contracts including the raise-discipline one.
     Rewrote to two contracts + retraction note.

- **Careful-review pass 3** (3 findings, all landed —
  interlocking fixes for `task-runner-and-ci-config`):
  1. `task-runner-and-ci-config` Source line hadn't been
     updated with a v017 Q3 widening notation despite its
     body having been edited in pass 2. Added the v017 Q3
     widening note.
  2. Revision-file "Carried forward unchanged from v016"
     list included `task-runner-and-ci-config`, but pass 2
     had widened its body. Moved it to "Scope-widened in
     v017" with Q3 bullet.
  3. Revision-file "touched 4 existing entries" claim was
     now incorrect (5 entries). Re-revised to "touched 5".

- **Careful-review pass 4** (3 findings, all landed):
  1. `deferred-items.md`'s `task-runner-and-ci-config` v013
     M7 subsection still said the style-doc configuration
     codifies "three contracts" — stale post-Q3. Rewrote
     to "two contracts" with v013 M7 historical note +
     v017 Q3 narrowing.
  2. PROPOSAL.md's `dev-tooling/checks/` layout tree
     annotation still said "import-surface portion of
     no_raise_outside_io ... replaced by Import-Linter".
     Rewrote to note the v017 Q3 retraction of the
     delegation. `no_raise_outside_io.py`'s inline comment
     also updated to note raise-site is the sole
     enforcement point post-Q3.
  3. PROPOSAL.md DoD item 12 said "Import-Linter contracts
     per L15a + v013 M7 minimum-configuration example".
     Extended with "narrowed in v017 Q3 to two contracts".
     Also updated PROPOSAL.md's `pyproject.toml` layout
     entry to match.

- **Careful-review pass 5** (0 load-bearing findings):
  end-to-end re-read confirms all working docs are
  self-consistent. Cross-doc references align (every
  "three contracts" mention is accompanied by its v017 Q3
  narrowing note; every v017 Q# marker is in place; the
  revision-file inventory arithmetic matches the
  deferred-items.md Source-line widenings; PROPOSAL.md's
  reserve-suffix section is invariants-only and no longer
  duplicates the algorithm; the filename-stem vs. front-
  matter `topic` distinction is consistent across
  PROPOSAL.md §"revise", §"Proposed-change file format",
  and §"doctor → Static-phase checks"). Pass 5 is the
  final general careful-review pass per the "continue
  until a pass lands no load-bearing fixes" rule.

**Cumulative across 5 general careful-review passes: 13
inconsistencies caught and fixed (4 + 3 + 3 + 3 + 0).**

- **Dedicated deferred-items-consistency pass** (3 findings,
  all landed). Walked every deferred-items entry, verified
  Source line + body against every v017 decision and every
  prior-version decision that touched the entry.
  1. `template-prompt-authoring` Source line said v017 Q2 was
     "note-only", but Q2's pre-seed
     `bin/resolve_template.py --template <chosen>` invocation
     is a new wrapper call that the built-in `minimal`
     template's `prompts/seed.md` delimiter comments must
     cover (per the v014 N9 delimiter-comment requirement).
     Rewrote the Source line to mark Q2 as a substantive
     widening of the minimal template's prompt-authoring
     obligations.
  2. `user-hosted-custom-templates` body stated the v2+
     extensibility shield covers "the wrapper's output
     contract" but did not mention the CLI flag surface
     (`--project-root` + the v017-added `--template`). Added
     an explicit "v017 Q2 addition" paragraph noting that
     BOTH the stdout contract and the flag shape are v1-
     frozen and that v2+ extensions must EXTEND (not replace)
     the flag set. Source line updated with the v017 Q2
     note-only widening.
  3. `claude-md-prose` had no mention of the v017 Q9
     shared upward-walk helper in `livespec.io.fs`. Added a
     Source-line note-only widening covering the
     `livespec/io/CLAUDE.md` obligation to mention the
     shared helper.

  **Layout-tree drift check.** PROPOSAL.md's
  `.claude-plugin/scripts/` tree (lines ~72-192), `tests/`
  tree (~2499-2548), and `dev-tooling/` tree (~2901-2938)
  show no new files introduced by v017. Q3 retracts an
  Import-Linter contract (no file change); Q2 adds a CLI
  flag to an existing wrapper (no file change); Q9 adds a
  shared helper inside the already-tracked `livespec/io/fs`
  module (no new file). No tree edits required.

  **Cross-reference validity.** Every `§"..."` cross-
  reference introduced by v017 Q# items (`§"Template
  resolution contract"`, `§"Doctor → Bootstrap lenience"`,
  `§"Pre-step skip control"`, `§"Proposed-change file
  format"`, `§"Sub-command dispatch and invocation chain"`,
  `§"Wrapper-side: deterministic lifecycle"`) resolves to an
  existing `##`/`###` heading in PROPOSAL.md.

  **Example-vs-rule alignment.** The reserve-suffix worked
  examples (in `deferred-items.md` only after Q1's
  PROPOSAL.md trim) still pass the literal arithmetic
  (26+9=35; 73→55+9=64; pre-attached suffix strips cleanly).
  PROPOSAL.md §"critique"'s informal description of the
  short-stem / long-stem / pre-attached cases is consistent
  with the full algorithm in deferred-items.md.

**Cumulative total findings across all 5 careful-review
passes + 1 deferred-items-consistency pass: 16
inconsistencies caught and fixed (4 + 3 + 3 + 3 + 0 + 3).**

## Outstanding follow-ups

Tracked in the updated `deferred-items.md`.

The v017 pass touched 5 existing entries with scope-widenings:

- `static-check-semantics` (Q1, Q3, Q7, Q9)
- `skill-md-prose-authoring` (Q2, Q4)
- `template-prompt-authoring` (Q2 note-only)
- `enforcement-check-scripts` (Q3)
- `task-runner-and-ci-config` (Q3 — pyproject.toml
  `[tool.importlinter]` narrowed)

Q5 (seed wrapper present-but-invalid handling) and Q6
(payload/config mismatch exit code) refine PROPOSAL.md §"seed"
directly and do not touch any deferred-items entry. Q8 (line-853
grammar fix) is a PROPOSAL.md-only cleanup. No new deferred
items were added and none were removed.

## What was rejected

- Q5-original (fake_claude.py vs. check-no-inheritance) was
  **retracted mid-interview** after user pushback. The mock is
  a hand-rolled test fixture that handles input/output streams
  and invokes subprocesses; it complies with every livespec
  Python rule by construction. Tests assert via attribute
  access on livespec-authored message dataclasses, not via
  `isinstance(msg, SDKBaseClass)`. No rule-vs-feature conflict
  exists; the critique item was a false alarm framed from an
  over-strong reading of "API-compatible pass-through mock." A
  feedback memory was saved so future sessions don't surface
  this class of false alarm again.

- Q1 option B (expand PROPOSAL.md to full algorithm) was
  rejected because it re-introduces drift risk — the cause of
  the v016→v017 malformation being fixed.

- Q2 options B (second wrapper) and C (SKILL.md-prose
  resolution) were rejected because B fragments template
  resolution across two wrappers and C makes pre-seed
  resolution a fragile skill-prose concern.

- Q3 options B (broaden ignore_imports) and C (re-export module)
  were rejected because B leaves the contract empty of
  load-bearing work and C adds a module whose only purpose is
  to launder the import surface.

- Q4 options B (`--skip-post-check` flag pair) and C (hand-
  author proposed-change, skip propose-change entirely) were
  rejected because B adds a whole new skip axis whose misuse
  would mask post-step failures in normal flows and C divorces
  recovery from the normal propose-change flow.

- Q5 options B (silently overwrite) and C (delegate to
  deferred-items) were rejected because B silently clobbers a
  user's manual edit and C buries load-bearing behavior in a
  deferred item.

- Q6 option B (keep exit 2) was rejected because the payload is
  structurally a wire-format input, not a CLI-argument surface.

- Q7 option B (restructure `-revision-N.md` convention) was
  rejected because it shifts the established v014 N6 cadence
  mid-version for minor notational gain.

- Q9 options B (implementer choice) and C (transitive
  resolve_template.py calls) were rejected because B invites
  silent divergence and C adds a process-per-invocation cost
  not budgeted for in v017.
