---
proposal: proposal-critique-v15.md
decision: modify
revised_at: 2026-04-24T02:00:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v15

## Provenance

- **Proposed change:** `proposal-critique-v15.md` — a
  recreatability-and-cross-doc-consistency critique over v015
  focused on five items:
  - P1: `anchor-reference-resolution` scope under `minimal`'s
    `spec_root: "./"` walks the entire repo root
    (incorrectness / cross-template malformation).
  - P2: seed's `.livespec.jsonc` creation timing under N1's
    pre-seed dialogue was unspecified (ambiguity /
    incompleteness).
  - P3: author-derived topic-hint truncation can chop the
    `-critique` suffix under v015 O3's central canonicalization
    (incompleteness).
  - P4: `topic` YAML front-matter field was under-specified for
    skill-auto-generated `out-of-band-edit-<UTC-seconds>.md`
    files (ambiguity).
  - P5: Shebang-wrapper "6-line shape" contradicts the 7-line
    example (malformation / self-contradiction).
- **Revised by:** thewoolleyman (human) in dialogue with Claude
  Opus 4.7 (1M context).
- **Revised at:** 2026-04-24 (UTC).
- **Scope:** v015 `PROPOSAL.md` + `deferred-items.md` +
  `python-skill-script-style-requirements.md` → v016 equivalents.
  `livespec-nlspec-spec.md`, `goals-and-non-goals.md`,
  `prior-art.md`, `subdomains-and-unsolved-routing.md`, and the
  2026-04-19 lifecycle/terminology companion docs remain
  unchanged.

## Pass framing

This pass was a **recreatability-and-cross-doc-consistency**
critique grounded in the NLSpec test: could a competent
implementer produce a working livespec without being forced
to guess between conflicting rules or invent semantics the
docs leave unspecified?

The accepted changes all preserve earlier structural decisions
rather than reopening them:

- **P1** preserves v014 N1's `minimal` template (with
  `spec_root: "./"`) and v009 I7's `spec_root` parameterization
  by scoping doctor-static walks to the template-declared file
  set instead of walking the full repo root.
- **P2** preserves v014 N1's pre-seed template-selection
  dialogue and v014 N3's bootstrap lenience by codifying that
  the wrapper (not the LLM) writes `.livespec.jsonc` before
  post-step doctor-static runs, so every bootstrap scenario
  reaches post-step with a coherent config file.
- **P3** preserves v015 O3's wrapper-centralized canonicalization
  rule and v014 N5's author→slug transformation by adding a
  reserve-suffix mechanism that guarantees the `-critique`
  suffix survives truncation without loosening the 64-char cap.
- **P4** preserves v014 N6's deliberate two-filename-convention
  carve-out while closing the proposed-change file format's
  gap on the `topic` YAML field: the rule is lifted to a
  MUST-level single-canonicalization requirement across all
  derivation paths, without prescribing the exact value or
  mechanism.
- **P5** preserves v007 G2 / v011 K3's wrapper-shape contract
  by cleaning up the stale "6-line" phrasing to match the
  example's visible 6-statements-with-optional-blank shape.

## Governing principles reinforced

- **Template-governed structure stays real.** P1 reinforces
  that doctor-static checks walk the template-declared spec
  file set, not an incidental "everything under spec-root"
  semantic that happens to collide with `minimal`'s `"./"`.
- **Deterministic wrapper bootstrap.** P2 keeps the wrapper
  responsible for shaping the on-disk state that post-step
  validates. LLM payloads supply content and intent; wrappers
  own file layout, versioned history, and config bootstrap.
- **Central canonicalization stays central.** P3 fixes a
  silent edge case without fragmenting the single
  canonicalization rule. P4 lifts the canonicalization-
  consistency requirement into a MUST without prescribing
  implementation mechanism — "architecture, not mechanism."
- **Examples and rules agree.** P5 is pure malformation
  cleanup: the rule and the example must say the same thing.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| P1 | incorrectness (cross-template malformation) | Accept A — `anchor-reference-resolution` (and any future `<spec-root>/`-walking doctor-static check) is scoped to the template-declared spec file set: template's spec files, spec-root `README.md` where the template declares one, `<spec-root>/proposed_changes/**`, `<spec-root>/history/**/proposed_changes/**`, and per-version snapshots of each template-declared spec file. Walk algorithm codified in `deferred-items.md`'s `static-check-semantics`. |
| P2 | ambiguity / incompleteness | Accept A — `bin/seed.py` writes `.livespec.jsonc` (from full commented schema + chosen `template` value) as part of deterministic file-shaping work, BEFORE post-step doctor-static. `seed_input.schema.json` gains a required top-level `template: string` field carrying the user-chosen template value from the pre-seed dialogue. `wrapper-input-schemas` deferred entry widened accordingly. |
| P3 | incompleteness | Accept A — `bin/propose_change.py` gains a `--reserve-suffix <text>` flag (also usable via its Python internal API). When supplied: canonicalization steps 1-3 are applied to the full inbound string; step 4 truncates the non-suffix portion to `64 − len(<suffix>)`; the suffix is re-appended verbatim. `critique` uses the mechanism with suffix `-critique`. `static-check-semantics` deferred entry codifies the algorithm. |
| P4 | ambiguity | Reshaped — lift to a MUST-level single-canonicalization requirement in PROPOSAL.md §"Proposed-change file format": the `topic` YAML front-matter field MUST be derived via the same canonicalization rule across all creation paths (user-invoked `propose-change`, `critique`'s internal delegation, skill-auto-generated artifacts like `seed` auto-capture and `out-of-band-edits` backfill). Implementations MUST route all `topic` derivations through a single shared canonicalization so two livespec implementations cannot diverge on the `topic` value for semantically-identical inputs. No mechanism detail (no hardcode-vs-helper prescription); no `deferred-items.md` subsection added. |
| P5 | malformation (self-contradiction) | Accept A — rewrite the Shebang-wrapper contract as "exactly the following shape, comprising 6 statements (no other statements, no other lines beyond the optional blank between the import block and `raise SystemExit`)". Apply the matching edit in `python-skill-script-style-requirements.md`. Codify the optional-blank allowance in `deferred-items.md`'s `static-check-semantics` entry under `check-wrapper-shape`. |

## Disposition by item

### P1. `anchor-reference-resolution` scope under `minimal`'s `spec_root: "./"` (incorrectness → accepted, option A)

Accepted as proposed.

The accepted repair scopes every `<spec-root>/`-walking
doctor-static check (today: `anchor-reference-resolution`;
in general: any future static check that walks `<spec-root>/`
recursively) to a precisely-defined file set:

- every template-declared spec file (resolved from the active
  template's `specification-template/` walk + the spec-root-
  relative paths),
- the spec-root `README.md` when the template declares one
  (`livespec` does; `minimal` does not),
- every file under `<spec-root>/proposed_changes/**`,
- every file under `<spec-root>/history/**/proposed_changes/**`,
- every per-version copy of a template-declared spec file
  under `<spec-root>/history/**/<spec-file>` for each
  template-declared spec file.

The walk algorithm is codified in `deferred-items.md`'s
`static-check-semantics` entry so the implementer pass cannot
diverge. Under `minimal` the walk covers `SPECIFICATION.md`
(the sole template-declared spec file) plus the two
versioned-history subtrees.

Implications for user source trees: the project's top-level
`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and any
markdown elsewhere under the repo root (`docs/**`, `src/**`,
`.github/**`, `node_modules/**` etc.) are NOT inspected by
`anchor-reference-resolution` even under `minimal`'s
`spec_root: "./"`. This preserves the v014 N1 "single file
at repo root" decision without smuggling repo-wide
Markdown-link validation into `doctor`.

### P2. Seed's `.livespec.jsonc` creation timing (ambiguity / incompleteness → accepted, option A)

Accepted as proposed.

The accepted repair codifies that `bin/seed.py` (the wrapper)
writes `.livespec.jsonc` as part of its deterministic
file-shaping work, in the following order, before post-step
doctor-static runs:

1. Write `.livespec.jsonc` (full commented schema +
   `template: "<chosen-value>"` from the pre-seed dialogue).
2. Write each `files[]` entry to its declared path.
3. Write `<spec-root>/history/v001/` and the seed
   auto-capture artifacts (`proposed_changes/seed.md` + paired
   revision).
4. Invoke post-step doctor-static against a fully-bootstrapped
   project tree.

To convey the chosen template name to the wrapper,
`seed_input.schema.json` gains a required top-level field:

```json
{
  "template": "<chosen-template-name-or-path>",
  "files": [...],
  "intent": "<verbatim user intent>"
}
```

The LLM includes the user-selected template value (chosen in
the pre-seed SKILL.md-prose dialogue from options `livespec` /
`minimal` / custom path) in the payload. The wrapper validates
the payload, writes `.livespec.jsonc` first, then proceeds with
the file and history writes.

`wrapper-input-schemas` deferred entry is widened to add the
required `template` field to `seed_input.schema.json` and the
paired `SeedInput` dataclass.

Eliminated interpretation: the `.livespec.jsonc` file is NOT
written by the LLM as a separate post-wrapper Write-tool call
(which would leave post-step running against an absent
config, defeating v014 N3 bootstrap lenience's actual purpose
which is handling user-broken configs, not masking a
seed-time gap).

### P3. Author-derived topic-hint truncation chops `-critique` suffix (incompleteness → accepted, option A)

Accepted as proposed.

The accepted repair adds a `--reserve-suffix <text>` flag to
`bin/propose_change.py` (also callable via the equivalent
Python internal API path used by `critique`'s internal
delegation). Semantics:

- When `--reserve-suffix <suffix>` is NOT supplied, topic
  canonicalization behaves exactly as v015 O3 defined.
- When supplied: steps 1-3 (lowercase, non-`[a-z0-9]` →
  single hyphen, strip leading/trailing hyphens) apply to the
  full inbound topic hint. Step 4 truncates the non-suffix
  portion to `64 − len(<canonicalized-suffix>)` characters,
  then re-appends the canonicalized suffix verbatim. The
  resulting topic is at most 64 characters, and the suffix is
  preserved intact.
- `critique`'s internal delegation uses
  `--reserve-suffix -critique` (or the equivalent internal
  API parameter) so that long author slugs do NOT eat the
  `-critique` suffix.
- The empty-after-canonicalization `UsageError` (exit 2) rule
  continues to apply to the final result.

PROPOSAL.md §"propose-change → Topic canonicalization" is
updated to document the reserve-suffix rule; PROPOSAL.md
§"critique" is updated to state that `critique` uses the
reserve-suffix mechanism. The `static-check-semantics`
deferred entry codifies the exact algorithm.

Rejected: truncate-before-suffix-re-application (option B)
was rejected because it fragmented v015 O3's single-rule
clean boundary. Advisory-limit doc-only (option C) was
rejected because it documents the bug without fixing it.

### P4. `topic` YAML field for `out-of-band-edit-` files (ambiguity → reshaped to MUST-level requirement)

**Accepted in reshaped form after user pushback.**

The critique as originally written (options A/B) asked
"what exact value does the `out-of-band-edits` auto-backfill
write into the `topic` front-matter field?" and debated
hardcode-vs-route-through-canonicalization. The user
correctly pushed that this was drifting into implementation
mechanism — and that the NLSpec principle is "specify
architecture, not mechanism; let the enforcement suite
enforce."

The reshaped disposition lifts the concern to the
architecture layer:

- Add to PROPOSAL.md §"Proposed-change file format" a
  MUST-level single-canonicalization requirement: the
  `topic` YAML front-matter field MUST be derived via the
  same canonicalization rule across ALL creation paths —
  user-invoked `propose-change`, `critique`'s internal
  delegation, and skill-auto-generated artifacts
  (today: `seed` auto-capture, `out-of-band-edits`
  backfill).
- Implementations MUST route all `topic` derivations
  through a single shared canonicalization so two
  livespec implementations cannot diverge on the `topic`
  value for semantically-identical inputs.

Explicitly NOT done:

- No prescription of the exact `topic` value for
  `out-of-band-edit-<UTC-seconds>.md` files (implementation
  choice).
- No prescription of the mechanism (single helper function
  vs. anything else).
- No new subsection in `deferred-items.md`'s
  `static-check-semantics`.

Rationale: the existing filename-convention MUSTs
(propose-change `<topic>.md` + `-2`/`-3` suffix; critique
`<author>-critique.md`; out-of-band-edits
`out-of-band-edit-<UTC-seconds>.md` via v014 N6) already
cover the observable file-shape contract. The `topic`
field's inner canonicalization mechanism is
implementation-layer; the user-facing MUST is consistency
across paths, not a specific value.

### P5. Shebang-wrapper "6-line shape" vs. 7-line example (malformation → accepted, option A)

Accepted as proposed.

The accepted repair rewrites the contract sentence in
PROPOSAL.md §"Shebang-wrapper contract" (lines ~339-352)
as:

> Each `bin/<cmd>.py` MUST consist of exactly the following
> shape, comprising 6 statements (no other statements, no
> other lines beyond the optional blank between the import
> block and `raise SystemExit`):

The canonical example stays at 7 lines including the blank.
The optional-blank allowance is codified in `deferred-items.md`'s
`static-check-semantics` entry under `check-wrapper-shape`
so the AST-lite check cannot be implemented with a strict
6-literal-line semantic.

The matching edit is applied in
`python-skill-script-style-requirements.md` §"Shebang-wrapper
contract".

Retroactive effect: v011 K3 wrapper-coverage tests (which
import wrappers matching the example's shape) continue to
pass unchanged.

## Deferred-items inventory (carried forward + scope-widened + new)

Per the deferred-items discipline, every carried-forward
item is enumerated below.

**Carried forward unchanged from v015:**

- `python-style-doc-into-constraints`
- `returns-pyright-plugin-disposition`
- `claude-md-prose`
- `basedpyright-vs-pyright`
- `user-hosted-custom-templates`
- `companion-docs-mapping`
- `front-matter-parser`
- `local-bundled-model-e2e`
- `end-to-end-integration-test`
- `task-runner-and-ci-config`

**Scope-widened in v016:**

- `static-check-semantics`
  P1: `anchor-reference-resolution` walk-set algorithm
  codified (template-declared spec files + spec-root
  README if declared + proposed_changes/** +
  history/**/proposed_changes/** +
  history/**/<spec-file>).
  P3: reserve-suffix canonicalization algorithm codified
  (`--reserve-suffix <text>` flag + Python internal API
  parameter; steps 1-3 on full string; step 4 truncates
  non-suffix portion to `64 − len(canonicalized-suffix)`;
  re-append canonicalized suffix verbatim).
  P5: `check-wrapper-shape` explicitly allows an optional
  blank line between the import block and `raise SystemExit`.
  Also widened the "Author identifier → filename slug
  transformation" subsection's critique-path description to
  reflect that critique now passes the author stem +
  reserve-suffix, not a pre-composed `-critique`-suffixed
  topic hint.
- `wrapper-input-schemas`
  P2: `seed_input.schema.json` gains a required top-level
  `template: string` field; paired `SeedInput` dataclass
  gains the field with `TemplateName` NewType.
- `skill-md-prose-authoring`
  P2: seed SKILL.md prose MUST include the chosen template
  value in the seed-input payload's new top-level
  `template` field; MUST NOT write `.livespec.jsonc` via
  the Write tool (wrapper owns it).
  P3: critique SKILL.md prose description updated —
  critique passes author stem + reserve-suffix to
  propose_change's internal canonicalization (no
  pre-composed `-critique` topic hint).
- `template-prompt-authoring`
  P2: every template's `prompts/seed.md` MUST emit the new
  top-level `template` field in its JSON output (the
  schema is shared across templates via
  `seed_input.schema.json`).
- `enforcement-check-scripts`
  P5: `dev-tooling/checks/check_wrapper_shape.py` gets the
  optional-blank algorithm codified in
  `static-check-semantics`; the script's implementation
  MUST NOT enforce a literal 6-line text count (AST module
  body traversal is the prescribed mechanism family).
  P1 and P3 note-only: affect sibling entry
  `static-check-semantics` without adding a new check
  script.

**New in v016:**

None.

**Removed in v016:**

None.

## Self-consistency check

Post-apply invariants rechecked against the working docs:

- `anchor-reference-resolution` no longer walks "all files
  under `<spec-root>/`". PROPOSAL.md §"static checks" names
  the explicit walk set; `deferred-items.md`'s
  `static-check-semantics` codifies the algorithm.
- Seed's wrapper-side deterministic work documents the
  `.livespec.jsonc` write step before post-step doctor-static
  in §"seed"; `seed_input.schema.json` in `wrapper-input-schemas`
  includes the required `template` field; the paired
  `SeedInput` dataclass is consistent.
- PROPOSAL.md §"propose-change → Topic canonicalization"
  documents the `--reserve-suffix` flag; PROPOSAL.md
  §"critique" states critique uses reserve-suffix with
  `-critique`; `static-check-semantics` covers the
  algorithm.
- PROPOSAL.md §"Proposed-change file format" contains the
  MUST-level single-canonicalization requirement; no
  mechanism-level detail was added.
- PROPOSAL.md §"Shebang-wrapper contract" and the style
  doc's matching section both say "6 statements" (with
  optional-blank clause); `static-check-semantics` names
  the optional blank in `check-wrapper-shape`.

Follow-up review passes after the initial apply phase:

- **Careful-review pass 1** (9 findings, all landed):
  1. Stale `6-line` phrasing remaining at PROPOSAL.md line
     317 (argparse-seam rationale) — updated to `6-statement`.
  2. Stale `6-line` phrasing in PROPOSAL.md's package-layout
     tree comment for `tests/bin/test_wrappers.py` — updated
     to `6-statement`.
  3-7. Five stale `6-line` phrasings in
     `python-skill-script-style-requirements.md` (lines 227,
     388, 1149, 1173, 1176) — all updated to the 6-statement
     framing with the P5 optional-blank clause where
     contextually appropriate.
  8. Pre-existing typo in PROPOSAL.md line 1960
     (`python-skill-script-script-style-requirements.md` →
     `python-skill-script-style-requirements.md`) — fixed
     opportunistically during the pass.
  9. v015 O2 ripple not resolved in v015's passes:
     `version-directories-complete` still required a
     per-version `README.md` unconditionally, contradicting
     v014 N1's explicit "`minimal` has no per-version README"
     rule. Fixed: the check now requires `README.md` only
     when the active template declares one. This fix also
     tightened the carried-forward "Carried forward
     unchanged from v015" list below because the ripple
     originated in v015 O2 but was not caught.
  Also updated PROPOSAL.md §"critique → Author identifier
  resolution" final sentence to reflect that critique now
  passes the author stem plus reserve-suffix, not a
  pre-composed `<author>-critique` topic hint. Updated the
  corresponding `static-check-semantics` entries ("Author
  identifier → filename slug transformation" and
  `skill-md-prose-authoring`'s critique-body paragraph) to
  match.
- **Careful-review pass 2** (2 findings, both landed):
  1. §"Proposed-change file format" preceding paragraph only
     mentioned `propose-change` and `critique` as `topic`
     sources; broadened to also name the skill-auto paths
     (seed auto-capture, out-of-band-edits backfill) so the
     MUST-level invariant that follows it is scoped
     consistently with its preamble.
  2. Caught a self-violation of the P4 disposition during
     the finding-1 expansion: the first draft prescribed an
     exact value `topic: out-of-band-edit-<UTC-seconds>` for
     `doctor-out-of-band-edits` backfill. Per P4's explicit
     reshaping, the exact value is implementation choice and
     MUST NOT be prescribed here. Corrected to "assigns a
     canonical value of its own choosing". Preserves the
     architecture-level MUST while leaving the mechanism
     unspecified.
- **Careful-review pass 3** (0 load-bearing findings):
  end-to-end re-read confirms all three working docs are
  self-consistent; `6-line` phrasing is gone except the
  intentional retrospective quote in the
  `check-wrapper-shape` algorithm subsection; every v016 P#
  marker is present where the disposition calls for it; the
  reserve-suffix mechanism is consistently described across
  PROPOSAL.md's propose-change / critique sections and
  `deferred-items.md`'s `static-check-semantics` +
  `skill-md-prose-authoring` entries.
- **Dedicated deferred-items-consistency pass** (5 findings,
  all landed):
  1. `skill-md-prose-authoring` Source line was stale at
     "widened v015 per O3 and O4" despite the v016 P3 update
     to the critique-body paragraph and the v016 P2
     requirement that seed's SKILL.md populate the payload's
     new `template` field and NOT write `.livespec.jsonc`.
     Updated to "widened v016 per P2 and P3".
  2. The v014 N1 sub-section under `skill-md-prose-authoring`
     still said seed's SKILL.md prose "writes
     `.livespec.jsonc` at the end of the seed flow" — stale
     after v016 P2 moved that responsibility to the wrapper.
     Rewrote the sub-section to name the payload `template`
     field, the wrapper-owned file-shaping guarantee, and
     the explicit "SKILL.md prose MUST NOT write
     `.livespec.jsonc` via the Write tool" rule. Also
     flagged that v016 P2 updates this sub-section.
  3. `template-prompt-authoring` Source line didn't record
     any v016 widening despite P2's schema addition requiring
     every template's `prompts/seed.md` to emit the new
     top-level `template` field. Updated to "widened in
     v016 per P2".
  4. `enforcement-check-scripts` Source line didn't record
     v016's affect on `check_wrapper_shape.py`. Updated to
     note P5's algorithm change plus the P1/P3 notes-only
     position.
  5. Cross-reference drift: two `see PROPOSAL.md §"seed —
     ..."` references in `deferred-items.md` pointed at
     bolded bullet labels, not actual `##`/`###` headings.
     Rewrote both to `§"seed" bullet "..."` form so the
     reference accurately describes the target structure.
  Layout-tree drift check: PROPOSAL.md's package-layout
  tree (lines ~75-200) and tests tree (lines ~2499-2540)
  show no new files introduced by v016 — the v016 changes
  are all in-place contract tightenings or schema-field
  additions to existing files. No tree edits required.
  Example-vs-rule alignment: verified the reserve-suffix
  worked examples in `static-check-semantics` pass the
  literal character-count arithmetic (26-char input +
  9-char suffix = 35-char output; 73-char input truncated
  to 55-char stem + 9-char suffix = 64-char output; pre-
  attached suffix correctly strips and re-appends).

## Outstanding follow-ups

Tracked in the updated `deferred-items.md`.

The v016 pass touched 2 existing entries with scope-widenings:

- `static-check-semantics` (P1 + P3 + P5)
- `wrapper-input-schemas` (P2)

No new deferred items were added and none were removed.

## What was rejected

No item was rejected outright.

- P3 option B (truncate-before-suffix-re-application) was
  rejected because it fragmented v015 O3's single-rule clean
  boundary.
- P3 option C (advisory doc-only) was rejected because it
  documents the bug without fixing it.
- P4 options A/B-as-originally-framed (hardcode vs. route
  through propose-change) were both rejected during
  interview because both were implementation-mechanism
  questions; the reshaped MUST-level architecture
  requirement replaces them.
- P5 option B (strict 6 literal lines, drop the blank) was
  rejected because it contradicted the canonical example's
  readability and would have required touching existing
  v011 K3 wrapper tests.
