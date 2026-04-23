---
proposal: proposal-critique-v13.md
decision: modify
revised_at: 2026-04-23T22:00:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v13

## Provenance

- **Proposed change:** `proposal-critique-v13.md` (in this directory)
  — a recreatability-and-integration-gap critique surfacing 11
  items across v013 PROPOSAL.md,
  `python-skill-script-style-requirements.md`, and
  `deferred-items.md`, plus one new item (N9) added mid-interview
  after N1's resolution surfaced the need for an end-to-end
  integration test. The critique was framed as a mix of:
  - recreatability defects (places where a competent implementer
    building from the three brainstorming docs alone would be
    blocked or forced to guess),
  - operational-contract ambiguities, and
  - cross-doc self-consistency residue the v013 careful-review
    passes missed.
- **Revised by:** thewoolleyman (human) in dialogue with Claude
  Opus 4.7 (1M context).
- **Revised at:** 2026-04-23 (UTC).
- **Scope:** v013 PROPOSAL.md + python style doc +
  `deferred-items.md` → v014 equivalents.
  `livespec-nlspec-spec.md` unchanged.
  `goals-and-non-goals.md`, `prior-art.md`, and
  `subdomains-and-unsolved-routing.md` unchanged.
  Focus areas: closing the largest recreatability / self-
  consistency contradictions (N1: `.livespec.jsonc` absence
  behavior vs `resolve_template.py` exit-3-on-missing; N2:
  `finding.py` pairing vs three-way `check-schema-dataclass-
  pairing`); significant gaps (N3: doctor-static bootstrap on
  malformed config; N4: `template-exists` widening; N5: author
  slug transformation; N6: topic collision suffix form; N7: seed
  post-step recovery; N8: prune-history wording fix); one
  mid-interview-introduced significant gap (N9: end-to-end
  integration test); and three smaller cleanups (C1-C3).

## Pass framing

This pass was a **recreatability-and-integration-gap critique**
producing 11 items plus one new item (N9) surfaced mid-
interview. Each item carried one of four NLSpec failure modes
(ambiguity / malformation / incompleteness / incorrectness) and
was grouped by impact:

- major gap (N1, the single largest recreatability /
  self-contradiction blocker);
- significant gaps (N2-N8 + N9, each closing a concrete
  recreatability / contract / self-consistency hole);
- smaller cleanup (C1-C3, cross-doc residue the v013 review
  passes missed).

Two items were reshaped mid-interview:

- **N1** was originally framed as a narrow
  `resolve_template.py`-exit-code-vs-absence-behavior
  contradiction with three resolution options (A:
  resolve_template.py falls back; B: seed SKILL.md prose
  special-cases; C: seed wrapper special-cases). The user's
  clarifying questions reframed the item into two coupled
  concerns: (i) the absence-behavior contradiction proper, and
  (ii) the template-choice affordance for users who want a
  non-default template. With only one built-in (`livespec`), (ii)
  masqueraded as a nonissue. The user proposed bringing a second
  built-in template (`minimal`) into v1 scope, giving the
  user-facing template-choice question a concrete meaning. The
  final disposition bundles both: `minimal` is added as a
  second built-in (single-file `SPECIFICATION.md` at
  `spec_root: "./"`); seed's SKILL.md prose prompts the user
  for template choice when `.livespec.jsonc` is absent
  (dialogue-driven pre-seed selection); `resolve_template.py`
  keeps its strict exit-3-on-missing contract for non-seed
  sub-commands. The `minimal` template also serves as the
  canonical shape for N9's end-to-end integration test.
- **N7** was originally framed as proposing three recovery
  options (A: new seed-specific recovery via the auto-created
  `history/v001/proposed_changes/seed.md`; B: `--force-reseed`;
  C: narrow post-step scope). The disposition-apply phase
  surfaced that the existing `--skip-pre-check` / `--run-pre-
  check` flag pair (v010 J10) was already designed for
  exactly this emergency-recovery case. The final disposition
  (A-revised) documents the recovery path as using existing
  machinery (`propose-change --skip-pre-check` + `revise
  --skip-pre-check`) rather than introducing new flags or
  rules.

One item (N9) was **added mid-interview**, surfaced when the
user's N1 resolution (adding `minimal` as a second built-in)
prompted the question *"does the proposal have any top-of-
pyramid / end-to-end integration test requirements?"* — answer:
no. N9 was appended to the critique document with four design
dimensions (LLM determinism; harness scope; cadence; coverage
surface), each interviewed one at a time. One additional
dimension (D5: invocation mechanism) was raised during the
N9-D3 interview when the user asked *"are we planning to
control this interactive terminal CLI test via tmux?"* —
answered via Claude Code guide research confirming the Agent
SDK is the clean mechanism, tmux is not needed.

Two items (N6, N9-D3) moved from my recommended options to
user-supplied alternatives:

- **N6** moved from recommended "A': always-appended UTC-
  timestamp suffix" to user-supplied "only on conflict;
  monotonic counter starting at `-2`; no zero-padding." The
  user's rationale: readable filenames in the common case;
  starting at `-2` makes the "this is the second file named
  `<topic>`" relationship explicit; alphanumeric sort ordering
  is an extreme edge case. Accepted as the disposition.
- **N9-D1** moved from recommended "D1-c hybrid stub/replay
  + live" to user-supplied "live LLM always; CI must provide
  an Anthropic API key; add future deferred requirement for
  local/bundled-model support." This simplifies the mock
  tier's raison d'être (the mock stays part of the v014
  resolution, but not as a stub-of-LLM-behavior; instead as
  an API-compatible pass-through executable that reads the
  minimal template's prompts with hardcoded delimiter comments
  and invokes wrappers deterministically). Combined with the
  user-supplied N9-D3 "two just targets, same test suite, env
  var selects executable" shape, the mock + real tiers are
  cleanly separated.

N9 itself bundles five design decisions (D1-D5) captured as
sub-dispositions below.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| N1 | malformation | (reshaped) bring `minimal` into v1 scope as a second built-in template (single-file SPECIFICATION.md at spec_root: "./"); seed's SKILL.md prose prompts for template choice pre-seed; `resolve_template.py` keeps strict exit-3-on-missing contract for non-seed sub-commands |
| N2 | malformation | A — close implementer choice; require standalone `finding.schema.json` + `validate/finding.py`; three-way `check-schema-dataclass-pairing` symmetry stays strict |
| N3 | incompleteness | A — lenient bootstrap for `bin/doctor_static.py`; add `config_load_status` and `template_load_status` fields to `DoctorContext`; `livespec-jsonc-valid` and `template-exists` inspect these to emit fail Findings with actionable diagnostics; preserves K10 fail-Finding discipline uniformly |
| N4 | incompleteness | A — widen `template-exists` to verify required prompt files (`prompts/{seed,propose-change,revise,critique}.md`) exist AND `template.json`-declared paths (`doctor_llm_*_checks_prompt`, `doctor_static_check_modules`) exist; missing file → fail Finding citing offending field, value, and path |
| N5 | ambiguity | A — codify author→slug transformation at `livespec/commands/propose_change.py`; lowercase → non-[a-z0-9]→hyphen → trim/collapse/truncate-64; slug used as filename topic suffix; original preserved in YAML front-matter author/author_llm; reuses GFM slug rule already used in `anchor-reference-resolution` |
| N6 | ambiguity | (user-supplied) only on conflict; monotonic counter starting at `-2`; no zero-padding; alphanumeric sort ordering accepted as extreme edge case |
| N7 | incompleteness | (reshaped) A-revised — document recovery via existing `--skip-pre-check` flag pair; seed's post-step failure message surfaces findings + instructions to run `/livespec:propose-change --skip-pre-check <topic>` then `/livespec:revise --skip-pre-check`; no new machinery; seed idempotency stays strict |
| N8 | malformation | A — update PROPOSAL.md §"prune-history" line 1543 from "Accepts no arguments in v1" to explicit listing of mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag pair per §"Pre-step skip control"; no other arguments in v1 |
| N9 | incompleteness | (added mid-interview; bundle of sub-dispositions) — D1: live LLM always for real tier, deterministic API-compatible pass-through mock for mock tier; D2: Claude Code only for v1; D3: `just e2e-test-claude-code-mock` in `just check` (per-commit, local + CI), `just e2e-test-claude-code-real` NOT in `just check`, CI triggers pre-merge-check + every-master-commit, locally invokable; D4: happy path + three error paths (retry-on-4, doctor fail-then-fix, prune-history no-op); D5: Agent SDK for real, Python API-compatible pass-through executable for mock with hardcoded delimiter comments in minimal template's prompts |
| C1 | incorrectness | A — sweep-replace `scripts/_vendor/` → `.claude-plugin/scripts/_vendor/` at PROPOSAL.md lines 880, 2051, 2501 |
| C2 | ambiguity | A — keep user-facing dialogue-interface headings (`### seed <intent>`, `### propose-change <topic> <intent>`, `### revise <revision-steering-intent>`); add one-sentence parenthetical to each opening paragraph explicitly noting LLM-vs-wrapper split |
| C3 | incompleteness | A — all three template-extension module load failures (syntax error, import error, missing `TEMPLATE_CHECKS` export) route through `IOFailure(PreconditionError)` → exit 3 at livespec's I/O boundary; codify per-failure-mode error messages in `deferred-items.md`'s `static-check-semantics` §"Template-extension doctor-static check loading — failure routing" (v014 addition following the v011 K5 subsection); preserves domain-error/bug split; keeps exit 1 reserved for livespec's own bugs |

## Governing principles reinforced

- **Recreatability discipline.** N1, N2, N3, N4 all close
  concrete gaps where a competent implementer could not proceed
  from the brainstorming docs alone. N5 / N6 close filename-
  generation ambiguities. N7 closes a recovery-path gap. N8
  resolves a one-line self-contradiction. N9 closes the
  harness-level integration-test gap that per-module tests
  cannot cover.
- **Minimal-example second built-in template** (N1 + N9).
  Bringing `minimal` into v1 scope is the single structural
  decision that simultaneously (a) resolves N1's absence-
  behavior contradiction by giving users an actual
  template-selection choice pre-seed, (b) provides a
  canonical single-file `SPECIFICATION.md` at `spec_root: "./"`
  that exercises the v009 I7 `spec_root` parameterization
  end-to-end, and (c) serves as the canonical happy-path shape
  for N9's E2E integration test. The deferred-item scope add
  is modest (~6 files, mostly template-prompt-authoring
  deferred work).
- **Architecture-vs-mechanism** (v009 I0). N9's recommendation
  for the SDK-based mock executable preserves mechanism
  freedom: the mock's delimiter-comment parsing is one valid
  implementation of the "read expected prompts + extract
  script invocations" contract. The real-LLM tier's SDK
  integration is likewise one valid implementation of the
  "live-LLM integration test" contract.
- **Existing-machinery reuse.** N7's recovery disposition
  (use existing `--skip-pre-check`) and N6's convention
  (mirrors the existing counter-less suffix discipline) both
  reuse already-codified mechanisms rather than introducing
  new flags or rules. Keeps the livespec surface area
  monotonic.
- **Domain-vs-bugs discipline** (v009 I10). C3's disposition
  (all three template-extension load failures → exit 3 via
  PreconditionError) preserves the domain-error/bug split at
  livespec's I/O boundary: extension code's malformed-ness is
  a domain-meaningful failure from livespec's perspective
  (fixing the extension resolves it), so it routes through
  the Result track rather than the bug-catcher.
- **Static enumeration over dynamic discovery.** N2's
  disposition (require standalone `finding.schema.json` +
  `validate/finding.py`) keeps the three-way pairing check's
  symmetry strict — no by-name exemption introduces
  implementer-guessable allowances.
- **Fail-Finding discipline preserved at boundaries** (v011
  K10). N3's lenient bootstrap gives bootstrap-critical
  checks (`livespec-jsonc-valid`, `template-exists`) the
  same fail-Finding channel non-bootstrap checks use;
  `/livespec:doctor` becomes a useful diagnostic tool for
  broken-config states.
- **Shipped-vs-not-shipped discipline** (v013 reinforcement).
  N9's mock executable and pre-merge CI workflows are
  livespec-repo-internal artifacts (at `<repo-root>/tests/e2e/`
  and `<repo-root>/.github/workflows/`); they don't ship to
  users via `.claude-plugin/**`. Matches the v013 M8 pattern
  for `check-no-todo-registry`.

## Disposition by item

### N1. `.livespec.jsonc` absence vs `resolve_template.py` exit-3 (malformation → accepted, reshaped)

The v013 malformation: PROPOSAL.md §"Absence behavior" (lines
887-893) says missing `.livespec.jsonc` → use defaults;
§"Template resolution contract — Exit codes" (lines 1068-1072)
says missing `.livespec.jsonc` → exit 3. Every sub-command's
SKILL.md prose invokes `bin/resolve_template.py` first, so on
a fresh project even `seed` (whose job is to create the file)
cannot run.

**Reshaping during interview.** The user's clarifying
questions reframed the item: with only one built-in template
(`livespec`), the absence-behavior rule masqueraded as a
solved problem ("silently default to livespec"); but the real
underlying question is *"how does a user pick a non-default
template pre-seed?"* The user proposed bringing a second
built-in (`minimal`, single-file SPECIFICATION.md at
repo-root) into v1 scope. This makes the template-selection
affordance a concrete design question rather than a
theoretical concern.

Final disposition bundles three coupled changes:

1. **`minimal` template added as second built-in for v1.**
   Scope: ~6 files in `.claude-plugin/specification-templates/
   minimal/`:
   - `template.json` declaring `template_format_version: 1`
     and `spec_root: "./"` (repo-root spec placement).
   - `prompts/seed.md`, `prompts/propose-change.md`,
     `prompts/revise.md`, `prompts/critique.md` (minimal
     prompts; authored under `template-prompt-authoring`
     deferred entry).
   - `specification-template/SPECIFICATION.md` (single
     starter file at repo root).
   `doctor-llm-*-checks-prompt` files are OPTIONAL in
   `template.json` (may be null); minimal template MAY leave
   them unset for v1.
2. **Seed's SKILL.md prose prompts for template choice
   pre-seed.** When `.livespec.jsonc` is absent, seed's
   SKILL.md prose asks the user: *"No `.livespec.jsonc`
   found. Which template do you want? [livespec (multi-file,
   recommended)] / [minimal (single-file)] / [custom path]"*
   After user picks, seed uses that template's `prompts/
   seed.md` and writes `.livespec.jsonc` at the end with the
   chosen `template` value. When `.livespec.jsonc` IS
   present, seed uses its `template` field without
   prompting. This is the only SKILL.md-prose special case
   for pre-seed absence.
3. **`resolve_template.py` contract stays strict.** Exit
   3 on missing `.livespec.jsonc` for every non-seed
   sub-command. A user invoking `/livespec:propose-change`
   on a fresh repo gets a clear "config missing" error
   (not the absence-defaults path).

Resolution:

- PROPOSAL.md §"Built-in template: `livespec`" (lines 1119-
  1165) renamed to §"Built-in templates". Subsection
  documents two built-ins: `livespec` (the existing default)
  and `minimal` (new). For `minimal`: single-file
  `SPECIFICATION.md` at repo root (`spec_root: "./"`);
  minimal prompts; no `contracts.md` / `constraints.md` /
  `scenarios.md`; no Gherkin scenario conventions; no
  `gherkin-blank-line-format` check applicability (that
  check is already conditional: "only when the active
  template is `livespec`" per PROPOSAL.md line 1753).
- PROPOSAL.md §"Custom templates are in v1 scope" (lines
  1081-1100) updates the built-in-names list from
  `{"livespec"}` to `{"livespec", "minimal"}`.
- PROPOSAL.md §"seed `<intent>`" (lines 1276-1344) — add a
  new subsection "Pre-seed template selection":
  - When `.livespec.jsonc` is absent, seed's SKILL.md prose
    MUST prompt the user for template choice (dialogue-
    driven). Options presented: `livespec` (recommended,
    default), `minimal` (single-file), or a custom path.
  - After user selects, seed uses that template's
    `prompts/seed.md` and writes `.livespec.jsonc` at the
    end with the chosen value.
  - When `.livespec.jsonc` IS present, seed invokes
    `bin/resolve_template.py` like any other sub-command
    and uses the configured template.
- PROPOSAL.md §"Template resolution contract" — no change
  to exit codes (strict exit-3-on-missing retained).
- `deferred-items.md` `template-prompt-authoring` entry —
  extend to cover `minimal` template's four required
  prompts PLUS the minimal starter `SPECIFICATION.md`
  content. Note: `minimal`'s prompts are intentionally
  shorter than `livespec`'s (no NLSpec-conformance Read
  requirement; single-file output; no Gherkin conventions).
- `deferred-items.md` `companion-docs-mapping` entry —
  unchanged (still applies to `livespec` template's
  multi-file shape).
- `deferred-items.md` `static-check-semantics` entry —
  note that `gherkin-blank-line-format` check applicability
  is template-conditional (existing v013 spec already
  captures this; no drift).

### N1-dependent clarifications

The disposition introduces a per-template `spec_root`
parameterization edge case the v009 I7 disposition partially
anticipated (`spec_root: "./"` for repo-root templates).
Confirmed unchanged: every doctor-static check that
references paths under `<spec-root>/` parameterizes against
`DoctorContext.spec_root`. For `minimal` with
`spec_root: "./"`:

- `SPECIFICATION/` doesn't exist; spec files live at
  `<repo-root>/SPECIFICATION.md` directly.
- `<repo-root>/proposed_changes/` and `<repo-root>/history/`
  exist; the skill-owned READMEs and version directories live
  at repo root rather than under a `SPECIFICATION/`
  sub-directory.
- Concrete-implementer choice: whether to unify the
  `proposed_changes/` and `history/` directory paths across
  templates (under the chosen `spec_root`) or always place
  them at `<repo-root>/<template-default>/` regardless. v013
  already settled this toward the former (path references
  use `<spec-root>/proposed_changes/` etc.).

### N2. `finding.py` pairing vs three-way check (malformation → accepted, option A)

v010 J11 left an implementer-choice: `finding.schema.json`
MAY be standalone OR embedded in `doctor_findings.schema.json`.
v013 M6 widened `check-schema-dataclass-pairing` to strict
three-way (every dataclass pairs with a schema AND validator).
These are incompatible: if `finding.schema.json` is embedded
rather than standalone, `finding.py` fails the "dataclass
without schema" branch.

Resolution:

- `deferred-items.md` `static-check-semantics` entry's
  `check-schema-dataclass-pairing` subsection (around v010 J11
  quote) — drop "Implementer choice whether `finding.schema.json`
  is a standalone schema OR the `Finding` shape is embedded".
  Replace with: "`finding.schema.json` is REQUIRED in v1;
  paired with `schemas/dataclasses/finding.py` (existing) AND
  `validate/finding.py` (new)."
- PROPOSAL.md §"Skill layout inside the plugin" — extend
  `schemas/` tree to list `finding.schema.json` alongside
  existing entries. Extend `validate/` tree to list
  `finding.py`.
- `deferred-items.md` `wrapper-input-schemas` entry — extend
  target-spec-file list to include `finding.schema.json` and
  `validate/finding.py`.

### N3. Doctor-static bootstrap on malformed config (incompleteness → accepted, option A)

`bin/doctor_static.py` must build `DoctorContext` before
running any check, but `DoctorContext.config: LivespecConfig`
requires successful parse + schema-validate of
`.livespec.jsonc`. On malformed input, strict bootstrap would
emit `IOFailure(PreconditionError)` → exit 3 with no findings,
defeating `livespec-jsonc-valid`'s purpose (to surface the
issue as a fail Finding per K10).

Resolution:

- PROPOSAL.md §"Static-phase structure" (around line 1586) —
  add a new subsection "Bootstrap lenience":

  > The orchestrator MUST construct `DoctorContext` with
  > best-effort defaults when `.livespec.jsonc` is absent,
  > malformed, or schema-invalid, so that `livespec-jsonc-valid`
  > can run and emit a fail Finding citing the specific
  > failure rather than the supervisor aborting without
  > Findings. Same discipline applies to `template.json` →
  > `template-exists`.

- PROPOSAL.md §"Context dataclasses" (style doc; codified
  in PROPOSAL.md's DoctorContext references too) —
  `DoctorContext` gains two new fields:
  - `config_load_status: Literal["ok", "absent", "malformed",
    "schema_invalid"]`
  - `template_load_status: Literal["ok", "absent", "malformed",
    "schema_invalid"]`

- `deferred-items.md` `static-check-semantics` entry —
  new subsection "Orchestrator bootstrap lenience":
  - `bin/doctor_static.py` attempts to parse + schema-validate
    `.livespec.jsonc` leniently.
  - On success: `config = parsed value; config_load_status =
    "ok"`.
  - On absent: `config = LivespecConfig(defaults); config_load_status =
    "absent"`.
  - On parse failure: `config = LivespecConfig(defaults);
    config_load_status = "malformed"`.
  - On schema-validation failure: `config =
    LivespecConfig(best_effort_from_partial_parse); config_load_status =
    "schema_invalid"`.
  - `livespec-jsonc-valid` check inspects `config_load_status`;
    emits fail Finding on `"malformed"` or `"schema_invalid"`
    with specific schema path or parse error; emits skipped
    Finding on `"absent"`; emits pass Finding on `"ok"`.
  - Same pattern for `template.json` → `template-exists`.

### N4. `template-exists` widening (incompleteness → accepted, option A)

v013 `template-exists` validates `template.json`, `prompts/`,
`specification-template/` presence at directory level. It
doesn't verify the four REQUIRED prompt files inside
`prompts/` or the `template.json`-declared optional paths.
Typos manifest as LLM-runtime Read-tool errors.

Resolution:

- PROPOSAL.md §"Static-phase checks — `template-exists`"
  (lines 1674-1680) — extend check scope:
  - Verifies `template.json`, `prompts/`, `specification-
    template/` exist (existing behavior).
  - Verifies `template_format_version` matches and is
    supported (existing behavior).
  - **New:** verifies `prompts/seed.md`,
    `prompts/propose-change.md`, `prompts/revise.md`, and
    `prompts/critique.md` all exist as files (REQUIRED per
    template format).
  - **New:** when `template.json` declares
    `doctor_llm_objective_checks_prompt` or
    `doctor_llm_subjective_checks_prompt` as non-null,
    verifies the declared path exists as a file at the
    template-root-relative path.
  - **New:** when `template.json` declares non-empty
    `doctor_static_check_modules`, verifies each listed path
    exists as a file at the template-root-relative path.
  - Missing file → fail Finding citing the offending
    `template.json` field, its value, and the missing path.

- `deferred-items.md` `static-check-semantics` entry's
  `template-exists` subsection — add the widening details.

### N5. Author identifier slug transformation (ambiguity → accepted, option A)

LLM-self-declared `author` values have no schema constraint
beyond string-type. They flow into filename generation
(`<author>-critique.md` topic suffix) and YAML front-matter.
Filesystem-unsafe characters break markdown-link resolution
and the `anchor-reference-resolution` check's slug
computation.

Resolution:

- PROPOSAL.md §"propose-change → Author identifier
  resolution" (lines 1364-1384) — insert after the
  four-step precedence:

  > **Author identifier → filename slug transformation.**
  > When the resolved `author` value is used as a filename
  > component (topic suffix `<resolved-author>-critique.md`
  > or `<resolved-author>-critique-<N>.md` collision form),
  > the wrapper transforms it via: lowercase; non-[a-z0-9]
  > characters replaced with single hyphens; leading and
  > trailing hyphens stripped; multi-hyphens collapsed to
  > one; result truncated to 64 characters. The slug form
  > matches the GFM anchor-slug rule already used by the
  > `anchor-reference-resolution` check. The YAML
  > front-matter `author` / `author_human` / `author_llm`
  > fields preserve the ORIGINAL (un-slugged) value for
  > audit. This rule applies uniformly across `propose-
  > change`, `critique`, and `revise`.

- `deferred-items.md` `static-check-semantics` entry —
  new subsection "Author identifier → slug transformation"
  codifying the rule; referenced from
  `anchor-reference-resolution` (shared GFM slug algorithm).
- `deferred-items.md` `wrapper-input-schemas` entry —
  note that the `author` field in
  `proposal_findings.schema.json` and
  `revise_input.schema.json` accepts unconstrained string
  values; the slug transformation applies post-validation
  at the wrapper layer.

### N6. Topic collision suffix form (ambiguity → accepted, user-supplied)

v013 says "append a short suffix" on collision without
specifying form. Three candidates diverge (counter,
timestamp, hash); any choice affects `revise`-order
tie-breaker and audit trail.

User-supplied disposition:

- Append only on conflict (keeps v013's "if a file already
  exists" wording).
- Use a monotonic integer counter, starting at `-2`.
  `<topic>.md` → `<topic>-2.md` → `<topic>-3.md` → ... →
  `<topic>-10.md`.
- No zero-padding. Alphanumeric sort misordering for >9
  duplicates is accepted as an extreme edge case.
- Starting at `-2` (not `-1`) makes the "this is the
  second file named `<topic>`" relationship explicit: the
  first file is the suffix-less one by convention.

Resolution:

- PROPOSAL.md §"propose-change" and §"critique" collision
  sentences (lines 1408-1411, 1447-1449) — replace "MUST
  auto-disambiguate by appending a short suffix" with:

  > MUST auto-disambiguate by appending a hyphen-separated
  > monotonic integer suffix starting at `2` (so the first
  > duplicate becomes `<topic>-2.md`, the second `<topic>-
  > 3.md`, etc.). No zero-padding. No user prompt for
  > collision.

- `deferred-items.md` `static-check-semantics` entry —
  new subsection "Collision-suffix semantics":
  - Scope: applies to `propose-change` and `critique`
    filename generation only. `out-of-band-edit-<UTC-
    seconds>.md` uses a separate convention (timestamp
    suffix; always appended; reflects the WHEN-did-drift-
    occur semantic of backfills).
  - Determination: the wrapper enumerates files named
    `<topic>.md`, `<topic>-2.md`, `<topic>-3.md`, ... in
    the target directory; uses the next integer after the
    highest existing suffix (or `2` if only `<topic>.md`
    exists).
  - Race: livespec is single-process; no lock needed.

### N7. Seed post-step recovery (incompleteness → accepted, reshaped option A-revised)

v013 says *"The user is instructed via findings to commit the
partial state and proceed"* on post-step failure, but for
seed specifically, "proceed to what?" is a dead-end: re-seed
is blocked by idempotency; follow-up `propose-change` would
trip its own pre-step with the same findings.

Reshaping during interview: original options (A: new seed-
specific recovery path; B: `--force-reseed`; C: narrow
post-step scope) were reshaped during the apply phase to
reuse the existing `--skip-pre-check` flag pair (v010 J10),
specifically designed for emergency recovery.

Resolution:

- PROPOSAL.md §"seed `<intent>`" — new subsection
  "Post-step doctor-static failure recovery":

  > If seed's post-step doctor-static emits fail Findings
  > (exit 3), the specification and history files are
  > already written. To correct the issues WITHOUT
  > re-seeding (seed's idempotency refusal blocks re-seed):
  >
  > 1. Review the fail Findings surfaced in stderr /
  >    skill-prose narration.
  > 2. Run `/livespec:propose-change --skip-pre-check
  >    <topic> "<fix description>"` to file a
  >    proposed-change that addresses the findings.
  >    `--skip-pre-check` bypasses the pre-step that would
  >    otherwise trip the same findings.
  > 3. Run `/livespec:revise --skip-pre-check` to process
  >    the proposed-change and cut `v002` with corrections.
  >    (`v001` is the seed; `v002` is the first revision
  >    that makes the spec pass its own doctor-static.)
  >
  > Seed's idempotency refusal stays strict; there is no
  > `--force-reseed`.

- `deferred-items.md` `skill-md-prose-authoring` entry —
  extend seed's SKILL.md body to surface the recovery
  path's concrete commands in the post-step-failure
  narration.

### N8. prune-history wording fix (malformation → accepted, option A)

v013 line 1543 says "Accepts no arguments in v1"; v013
§"Pre-step skip control" applies the `--skip-pre-check` /
`--run-pre-check` flag pair to prune-history. These
contradict.

Resolution:

- PROPOSAL.md §"prune-history" line 1543 — replace
  "Accepts no arguments in v1." with:

  > Accepts only the mutually-exclusive `--skip-pre-check`
  > / `--run-pre-check` flag pair per §"Pre-step skip
  > control"; no other arguments in v1.

### N9. End-to-end harness-level integration test (incompleteness → accepted, bundle of sub-dispositions)

Added mid-interview after N1's resolution (bringing
`minimal` into v1 scope) surfaced the natural use of
`minimal` as the E2E test target. v013 PROPOSAL.md has no
top-of-pyramid test requirement; per-module and per-spec-
file tests cover code-level concerns but leave harness-
level behaviors (SKILL.md prose ↔ wrapper ↔ LLM ↔ doctor
integration) unvalidated by any automated gate.

N9 bundles five sub-dispositions (D1-D5):

#### N9-D1. LLM mode

**User-supplied: live LLM always for real tier; deterministic
mock tier via API-compatible pass-through executable.** CI
must provide an Anthropic API key for the real tier; new
deferred-items entry (see below) for future local/bundled-
model support to remove the API-key CI dependency.

#### N9-D2. Harness scope

**D2-a: Claude Code only for v1.** Consistent with the
existing v1 non-goal "Alternate agent runtime packaging
(opencode, pi-mono). Plugin targets Claude Code only in v1."
Second-harness E2E deferred to v2.

#### N9-D3. Cadence (user-supplied two-target approach)

Two `just` targets, same pytest suite, env var selects
executable:

- **`just e2e-test-claude-code-mock`** — invoked by
  `just check` (per-commit, local + CI). Deterministic,
  instant, free. Uses `LIVESPEC_E2E_HARNESS=mock`.
- **`just e2e-test-claude-code-real`** — NOT in `just
  check`. CI triggers via three GitHub Actions events
  (per N9-ambiguity-2 resolution):
  1. **Pre-merge check** on PRs via GitHub merge queue
     (`on: merge_group` event). Fires only when a PR
     enters the merge queue (true pre-merge check against
     latest target); not on every PR commit. Requires
     enabling merge queue in the repo's branch-protection
     settings.
  2. **Every master-branch commit** (`on: push` with
     `branches: [master]`, covering both merged PRs and
     direct pushes).
  3. **Manual invocation on any branch** via
     `on: workflow_dispatch`. Developers can run the real
     E2E via the GitHub Actions UI against any branch
     (useful for validating a WIP PR before putting it in
     the merge queue).
  Uses `LIVESPEC_E2E_HARNESS=real`. Locally invokable for
  developers wanting to validate before opening a PR.

Release-tag CI workflow (unchanged) still runs
`check-mutation` and `check-no-todo-registry`.

#### N9-D4. Coverage surface

**D4-b: happy path + three error paths.** Happy path:
`/livespec:seed` → `/livespec:propose-change` →
`/livespec:critique` → `/livespec:revise` →
`/livespec:doctor` → `/livespec:prune-history` against the
`minimal` template. PLUS three error paths:

1. **Retry-on-exit-4:** wrapper rejects LLM JSON payload
   with schema violation; LLM (or mock) retries with
   corrected payload; assertion = success within 3 attempts
   total.
2. **Doctor-static fail-then-fix:** pre-seed a state that
   trips a content-inspecting doctor-static check (e.g.,
   `bcp14-keyword-wellformedness` on a `Must` token);
   run `/livespec:doctor`; verify fail Finding; apply fix
   via `/livespec:propose-change --skip-pre-check` +
   `/livespec:revise --skip-pre-check`; verify pass
   post-revise.
3. **Prune-history no-op:** run `/livespec:prune-history`
   on a project with only `v001` (nothing to prune); verify
   skipped Finding; verify filesystem unchanged.

#### N9-D5. Invocation mechanism

- **Real tier:** **Claude Agent SDK from Python** —
  `pip install claude-agent-sdk`; test fixture spawns an
  agent via `claude_agent_sdk.query(...)` with
  `plugins=[{"type": "local", "path":
  "/path/to/.claude-plugin/"}]`; chains multiple `query()`
  calls within one session to preserve conversation state
  and benefit from prompt caching; uses `can_use_tool`
  callback or `--permission-mode acceptEdits` to auto-
  approve wrapper invocations. `ANTHROPIC_API_KEY` env var
  for auth.
- **Mock tier:** **Python API-compatible pass-through
  executable** — a livespec-authored mock at
  `<repo-root>/tests/e2e/fake_claude.py` implements the
  Agent SDK's query interface surface livespec uses; on
  each query, reads the `minimal` template's prompt files,
  extracts **hardcoded delimiter comments** identifying
  script paths and arg shapes, invokes the corresponding
  `bin/<cmd>.py` wrapper with fake-LLM-generated JSON
  payloads (generated deterministically per the delimiter
  directives), and returns structured SDK-compatible
  messages to the test. Hard-fails if the delimiter
  comments in minimal's prompts are missing or malformed.

**Mock-scope clarification (N9-ambiguity-1).** The mock
replaces ONLY the Agent SDK / LLM layer. Every wrapper
(`bin/seed.py`, `bin/doctor_static.py`,
`bin/propose_change.py`, `bin/critique.py`,
`bin/revise.py`, `bin/resolve_template.py`,
`bin/prune_history.py`) runs for real in BOTH mock and real
tiers. The mock never stubs wrapper Python code. This
preserves the mock tier's ability to catch wrapper-chain
integration regressions (which is the hardest class for
unit tests to cover). Doctor-static's LLM-driven phase is
handled by the mock (since it's LLM-driven by construction);
doctor-static's Python phase runs for real.

**Delimiter-comment format (v014 does not pin mechanism).**
Per the architecture-vs-mechanism discipline (v009 I0),
v014 codifies only the CONTRACT: minimal template's prompts
MUST contain parseable delimiter-comment directives
identifying the wrapper invocations the mock should perform,
in a form the real LLM treats as inert markdown comments.
The exact format (HTML comment syntax, JSON-in-comment,
key=value, etc.) is implementer choice settled at the
intersection of `template-prompt-authoring` (prompt author
picks the form) and `end-to-end-integration-test` (mock
parser honors the form). Both deferred entries MUST agree
on a single format.

#### N9 cross-cutting implications

- **`minimal` template's prompt authoring carries a new
  requirement:** each of `prompts/{seed,propose-change,
  revise,critique}.md` MUST include hardcoded delimiter
  comments in a documented form (e.g., `<!-- livespec-
  mock:script=bin/seed.py args=--seed-json $TEMPFILE -->`
  — exact syntax TBD in the `template-prompt-authoring`
  deferred entry's resolution). The real LLM treats these
  as natural-language markdown comments; the mock parses
  them as directive contracts. This dual-purpose structure
  becomes part of the minimal template's canonical shape.
- **`livespec` template is NOT required to include
  delimiter comments** — the mock tier doesn't run against
  the livespec template; livespec is tested via the real
  tier (if at all) and via livespec's own dogfooding. The
  mock is strictly tied to minimal.

Resolution (combined for D1-D5):

- PROPOSAL.md §"Testing approach" — add a new subsection
  "End-to-end harness-level integration test":

  > Livespec ships a required end-to-end integration test
  > that exercises the full user workflow (Claude Code ↔
  > SKILL.md ↔ wrapper ↔ doctor) against a temporary git-
  > repo fixture using the `minimal` template.
  >
  > Two invocation tiers:
  >
  > - `just e2e-test-claude-code-mock` (default; in
  >   `just check`; per-commit): uses a livespec-authored
  >   Python API-compatible pass-through mock
  >   (`tests/e2e/fake_claude.py`) that reads the
  >   `minimal` template's prompts with hardcoded
  >   delimiter comments and invokes wrappers
  >   deterministically.
  > - `just e2e-test-claude-code-real` (NOT in
  >   `just check`): uses the real `claude-agent-sdk`
  >   Python library against a live Anthropic API
  >   (`ANTHROPIC_API_KEY` env var required). CI
  >   triggers: (a) pre-merge-check on PRs via GitHub
  >   merge queue (`on: merge_group` event; requires
  >   merge queue enabled in branch-protection settings);
  >   (b) every master-branch commit (`on: push` with
  >   `branches: [master]`); (c) manual invocation on
  >   any branch via `on: workflow_dispatch`. Locally
  >   invokable.
  >
  > Both tiers run the same pytest suite; the env var
  > `LIVESPEC_E2E_HARNESS=mock|real` selects the
  > executable.
  >
  > **Mock scope:** the mock replaces ONLY the Claude
  > Agent SDK / LLM layer. Every wrapper (`bin/*.py`)
  > runs for real in both tiers; the mock never stubs
  > wrapper Python code. Doctor-static's LLM-driven
  > phase is mock-handled (LLM-driven by construction);
  > doctor-static's Python phase runs for real. This
  > preserves the mock tier's ability to catch wrapper-
  > chain integration regressions.
  >
  > Coverage: happy path (`seed → propose-change →
  > critique → revise → doctor → prune-history`) plus
  > three error paths (retry-on-exit-4; doctor-static
  > fail-then-fix; prune-history no-op).
  >
  > Implementation and fixture authoring are tracked in
  > `deferred-items.md`'s `end-to-end-integration-test`
  > entry. The delimiter-comment format in the `minimal`
  > template's prompts is implementer choice settled at
  > the intersection of `template-prompt-authoring` and
  > `end-to-end-integration-test`; v014 codifies only
  > the contract (parseable directives identifying
  > wrapper invocations; real LLM treats as inert
  > markdown comments).

- style doc §"Enforcement suite — Canonical target list"
  — add two new rows:

  > | `just e2e-test-claude-code-mock` | E2E integration test against the `minimal` template via the livespec-authored mock (deterministic pass-through executable that reads delimiter comments from minimal template's prompts). Part of `just check`. |
  > | `just e2e-test-claude-code-real` | E2E integration test against the `minimal` template via the real `claude-agent-sdk`. Requires `ANTHROPIC_API_KEY`. NOT in `just check`. Runs on pre-merge-check + every-master-commit CI workflows. |

- `deferred-items.md` — add new entry
  `end-to-end-integration-test` covering: fixture
  authoring at `tests/e2e/fixtures/`; mock executable
  implementation at `tests/e2e/fake_claude.py`; delimiter-
  comment schema for minimal template's prompts; pytest
  suite at `tests/e2e/test_*.py`; GitHub Actions
  workflow files for pre-merge-check + master-push
  triggers; env-var contract
  (`LIVESPEC_E2E_HARNESS=mock|real`,
  `ANTHROPIC_API_KEY`).
- `deferred-items.md` — add new entry
  `local-bundled-model-e2e` capturing the future option
  to replace the API-key CI dependency with a
  local/bundled model (source: v014 N9-D1). Target spec
  file(s): `<repo-root>/.github/workflows/`.
  How-to-resolve: investigate Ollama / llama.cpp / MLX /
  similar with a small model bundled in the repo or
  fetched at CI-start; mock→real parity preserved;
  `ANTHROPIC_API_KEY` dependency removed. v2+ scope.
- `deferred-items.md` `template-prompt-authoring` entry
  — extend to note that `minimal` template's four
  required prompt files MUST include hardcoded delimiter
  comments for mock-tier parsing (format TBD during
  resolution).
- `deferred-items.md` `task-runner-and-ci-config` entry
  — extend to include: the two new `just` targets; the
  new pre-merge-check GitHub Actions workflow; the new
  master-push GitHub Actions workflow.

### C1. Short-form scripts/_vendor/ sweep-replace (incorrectness → accepted, option A)

PROPOSAL.md lines 880, 2051, and 2501 retain short-form
`scripts/_vendor/` paths from before v013 C5's full-path
canonicalization swept the style doc.

Resolution:

- PROPOSAL.md — sweep-replace `scripts/_vendor/` →
  `.claude-plugin/scripts/_vendor/` at the three cited lines.

### C2. Sub-command heading parenthetical (ambiguity → accepted, option A)

Headings like `### seed <intent>` and `### propose-change
<topic> <intent>` imply positional wrapper argv; the
wrappers actually take `--seed-json` / `--findings-json`
and the `<intent>` is consumed by the LLM in SKILL.md prose.

Resolution:

- PROPOSAL.md — add a one-sentence parenthetical to each
  sub-command section's opening paragraph explicitly
  noting the LLM-vs-wrapper split. Sections touched:
  `### seed <intent>`, `### propose-change <topic>
  <intent>`, `### revise <revision-steering-intent>`.
  Example wording for seed:

  > (The LLM consumes `<intent>` from dialogue in
  > `seed/SKILL.md` prose; the wrapper `bin/seed.py`
  > itself takes `--seed-json <path>` where the freeform
  > `<intent>` is already embedded in the JSON payload.
  > See §"Inputs" in the SKILL.md body structure for the
  > split.)

### C3. Template-extension module load failure routing (incompleteness → accepted, option A)

Syntax error, import error, and missing `TEMPLATE_CHECKS`
export during `doctor_static_check_modules` load had no
documented error routing. With N4's `template-exists`
widening, file-missing is caught earlier as a fail Finding;
these three remaining cases need explicit routing.

Resolution:

- `deferred-items.md` `static-check-semantics` entry's
  "Template-extension doctor-static check loading"
  subsection (around v011 K5 line) — add explicit failure
  routing:

  > **Module load failure modes.** Beyond the
  > `template-exists` widening (v014 N4) which catches
  > missing-file at static-check time, three remaining
  > failure modes during `importlib.util.spec_from_file_location`
  > + `loader.exec_module(...)` route as follows:
  >
  > - **Syntax error** in the extension module →
  >   `IOFailure(PreconditionError)` → exit 3 with error
  >   message naming the template path, module path, and
  >   the `SyntaxError` location.
  > - **Import error** (the module's own imports fail) →
  >   `IOFailure(PreconditionError)` → exit 3 with error
  >   message naming the template path, module path, and
  >   the `ImportError` target.
  > - **Missing `TEMPLATE_CHECKS` export** (module loads
  >   cleanly but doesn't export the required symbol) →
  >   `IOFailure(PreconditionError)` → exit 3 with error
  >   message naming the template path, module path, and
  >   the required export shape (`TEMPLATE_CHECKS:
  >   list[tuple[str, CheckRunFn]]`).
  >
  > All three route through the domain-error track
  > (PreconditionError, exit 3) because from livespec's
  > I/O-boundary perspective, an extension author's
  > malformed module is a domain-meaningful failure
  > (fixing the extension resolves it). Bug-class exit 1
  > remains reserved for livespec's own bugs. Raising/
  > catching discipline: the `importlib` calls are wrapped
  > with `@impure_safe(exceptions=(SyntaxError,
  > ImportError, AttributeError))` at the `livespec/io/`
  > boundary; the mapping from exception type to
  > `PreconditionError` message form lives in
  > `livespec/doctor/run_static.py`'s extension-loader
  > path.

## Deferred-items inventory (carried forward + scope-widened + new)

Per the deferred-items discipline, every carried-forward item
is enumerated below. Additions, scope-widenings, and renames
are flagged.

**Carried forward unchanged from v013:**

- `python-style-doc-into-constraints` (v005; unchanged).
- `returns-pyright-plugin-disposition` (v007; unchanged).
- `claude-md-prose` (v006; unchanged).
- `basedpyright-vs-pyright` (v012 L14; unchanged).
- `user-hosted-custom-templates` (v010 J3; unchanged in body;
  the internal mention of built-in names updated from
  `{"livespec"}` to `{"livespec", "minimal"}` per v014 N1 —
  cross-reference update only; not a scope-widening).
- `companion-docs-mapping` (v001; unchanged).
- `front-matter-parser` (v007; unchanged).
- `enforcement-check-scripts` (v005; v014 N2 and N4 affect
  sibling entries — `wrapper-input-schemas` captures the new
  `finding.schema.json` + `validate/finding.py`;
  `static-check-semantics` captures the `template-exists`
  widening — not this entry's scope. Entry carried forward
  unchanged by v014.).

**Scope-widened in v014:**

- `template-prompt-authoring` (v001; widened every pass since).
  v014 additions:
  - N1: `minimal` template's four required prompts
    (`prompts/{seed,propose-change,revise,critique}.md`)
    and starter `SPECIFICATION.md` content (single-file
    shape; no NLSpec-conformance Read; no Gherkin
    conventions).
  - N9: `minimal` template's prompts MUST include hardcoded
    delimiter comments for mock-tier parsing (format TBD
    during resolution).
- `static-check-semantics` (v007; widened every pass since).
  v014 additions:
  - N2: `check-schema-dataclass-pairing` no longer permits
    embedded-schema implementer choice for `finding.py`;
    standalone `finding.schema.json` + `validate/finding.py`
    mandated.
  - N3: orchestrator bootstrap lenience; `config_load_status`
    and `template_load_status` fields in `DoctorContext`;
    `livespec-jsonc-valid` and `template-exists` inspect
    these to emit fail Findings on malformed config.
  - N4: `template-exists` widened semantics (required
    prompts + `template.json`-declared paths).
  - N5: author identifier → filename slug transformation
    rule (GFM slug algorithm reuse).
  - N6: collision-suffix semantics (monotonic counter from
    2; no zero-padding; enumerate + next-integer
    determination).
  - C3: template-extension module load failure routing
    (syntax / import / missing export → exit 3 via
    PreconditionError).
- `task-runner-and-ci-config` (v006; widened every pass since).
  v014 additions:
  - N9-D3: two new `just` targets (`e2e-test-claude-code-
    mock` and `e2e-test-claude-code-real`).
  - N9-D3: new GitHub Actions workflow for pre-merge-check
    trigger (`merge_group` event).
  - N9-D3: new GitHub Actions workflow for master-push
    trigger (`push` to `master` branch).
  - N9-D5: `claude-agent-sdk` mise-pin as test-time dev
    dep.
- `skill-md-prose-authoring` (v008; widened every pass since).
  v014 additions:
  - N1: seed's SKILL.md prose prompts the user for template
    choice pre-seed (dialogue-driven selection between
    `livespec`, `minimal`, or custom path).
  - N7: seed's SKILL.md post-step-failure narration
    surfaces the recovery path concretely (`propose-change
    --skip-pre-check` → `revise --skip-pre-check`).
- `wrapper-input-schemas` (v008; widened every pass since).
  v014 additions:
  - N2: `finding.schema.json` added as a required v1
    schema; paired validator at `validate/finding.py`.
  - N5: note that `author` field values in
    `proposal_findings.schema.json` / `revise_input.schema.json`
    accept unconstrained strings; slug transformation
    applies post-validation at the wrapper layer.

**New in v014:**

- `end-to-end-integration-test` (v014 N9; new). Target
  spec file(s): `<repo-root>/tests/e2e/`, `<repo-root>/
  justfile`, `<repo-root>/.github/workflows/`. How to
  resolve: author the fixture tree under
  `tests/e2e/fixtures/` (tmp_path-style git repo
  templates); the mock executable at `tests/e2e/
  fake_claude.py` (API-compatible with `claude-agent-sdk`'s
  query interface; reads delimiter comments from minimal
  template's prompts; invokes wrappers deterministically);
  the pytest suite at `tests/e2e/test_*.py` (parameterized
  on `LIVESPEC_E2E_HARNESS=mock|real`; happy path + three
  error paths per D4-b); the two `just` targets; the two
  GitHub Actions workflow files (pre-merge-check via
  `merge_group`; master-push via `push` to `master`);
  `claude-agent-sdk` mise-pin for the real tier.
- `local-bundled-model-e2e` (v014 N9-D1; new). Target
  spec file(s): `<repo-root>/.github/workflows/`,
  `<repo-root>/.mise.toml`. How to resolve: investigate
  local/bundled-model support (Ollama / llama.cpp /
  MLX / similar) to eliminate the `ANTHROPIC_API_KEY` CI
  dependency for the real E2E tier; preserve mock↔real
  parity; scope is v2+ (v014 preserves the live-
  Anthropic-API contract).

**Removed:**

None. The v013-era open follow-ups are all resolved by v013's
own dispositions; no new "open follow-up" item emerges from
v014.

## Self-consistency check

Post-revision invariants rechecked:

- **`minimal` template** added to built-in-templates list;
  PROPOSAL.md layout tree gains `.claude-plugin/
  specification-templates/minimal/`; `template-prompt-
  authoring` deferred entry extended to cover minimal's
  prompts.
- **Seed pre-seed template-choice dialogue** codified in
  PROPOSAL.md §"seed `<intent>`" new subsection; SKILL.md
  prose authoring deferred-entry extended.
- **`resolve_template.py` strict exit-3-on-missing**
  unchanged (v013 contract preserved for non-seed
  sub-commands).
- **`finding.schema.json` + `validate/finding.py`** added
  to PROPOSAL.md layout tree; `check-schema-dataclass-
  pairing` three-way symmetry remains strict; v010 J11
  implementer-choice language dropped.
- **DoctorContext lenient bootstrap** codified in
  PROPOSAL.md §"Static-phase structure"; new fields
  `config_load_status` and `template_load_status` added
  to `DoctorContext` in style doc; `static-check-semantics`
  deferred-entry captures bootstrap semantics.
- **`template-exists` widening** codified in PROPOSAL.md
  §"Static-phase checks"; deferred-entry captures the
  widened scope.
- **Author-identifier slug transformation** codified in
  PROPOSAL.md §"propose-change → Author identifier
  resolution"; GFM slug rule reused.
- **Collision suffix form (monotonic from 2)** codified
  in PROPOSAL.md §"propose-change" and §"critique";
  deferred-entry captures determination rule.
- **Seed post-step recovery** codified in PROPOSAL.md
  §"seed `<intent>`" new subsection; SKILL.md prose
  deferred-entry extended.
- **prune-history wording** updated at PROPOSAL.md line
  1543.
- **E2E integration test** codified in PROPOSAL.md §"Testing
  approach"; style doc canonical target list extended;
  two new deferred-items entries (`end-to-end-integration-
  test` + `local-bundled-model-e2e`); `template-prompt-
  authoring` and `task-runner-and-ci-config` entries
  extended.
- **Scripts/_vendor/ sweep-replace** applied at PROPOSAL.md
  lines 880, 2051, 2501.
- **Sub-command heading parentheticals** added at seed,
  propose-change, revise sections.
- **Template-extension module load failure routing**
  codified in `static-check-semantics` deferred-entry.
- **Recreatability.** A competent implementer can generate
  the v014 livespec plugin + two built-in templates +
  sub-commands + enforcement suite + dev-tooling + E2E
  integration test from v014 PROPOSAL.md +
  `livespec-nlspec-spec.md` + updated
  `python-skill-script-script-style-requirements.md` +
  updated `deferred-items.md` alone.

## Outstanding follow-ups

Tracked in the updated `deferred-items.md` (see inventory
above). The v014 pass touched 5 existing entries (adding
scope-widenings): `template-prompt-authoring`,
`static-check-semantics`, `task-runner-and-ci-config`,
`skill-md-prose-authoring`, `wrapper-input-schemas`. Two new
entries were added: `end-to-end-integration-test` and
`local-bundled-model-e2e`. No entries were removed.
`enforcement-check-scripts` was initially included in the
scope-widened list but reclassified to carried-forward-
unchanged during the dedicated deferred-items-consistency
pass (v014 N2 and N4 affect the sibling entries
`wrapper-input-schemas` and `static-check-semantics`; they
don't add AST enforcement checks under `dev-tooling/checks/`,
which is `enforcement-check-scripts`'s actual scope).

## What was rejected

Nothing was rejected outright. Two items moved from
recommended to alternate option during the interview:

- **N6** — moved from recommended "A': always-appended UTC-
  timestamp suffix" to user-supplied "only on conflict;
  monotonic counter starting at `-2`; no zero-padding."
  Rationale: readable filenames in the common case;
  starting at `-2` makes the "second-file-named-X"
  relationship explicit.
- **N9-D1** — moved from recommended "D1-c hybrid stub/
  replay + live" to user-supplied "live LLM always for real
  tier; deterministic API-compatible pass-through mock for
  mock tier; CI must provide API key; add future deferred
  entry for local/bundled-model." Rationale: cleaner
  separation of concerns (mock isn't simulating LLM
  behavior; it's an API-compatible script-invoker driven by
  delimiter comments in the minimal template's prompts).

Two items were reshaped mid-interview:

- **N1** — originally framed as a narrow `resolve_template.py`
  contradiction; user's clarifying questions reframed it to
  include the template-choice affordance concern, resolved
  by bringing `minimal` into v1 scope + seed's SKILL.md
  prose prompting for template choice pre-seed.
- **N7** — original three options (A: new recovery path;
  B: `--force-reseed`; C: narrow post-step scope) were
  refined during the apply phase to reuse the existing
  `--skip-pre-check` flag pair (v010 J10), specifically
  designed for this emergency-recovery case.

One item was **added mid-interview**:

- **N9** — end-to-end harness-level integration test
  requirement, surfaced after N1's resolution made `minimal`
  the natural E2E target. Five sub-dispositions (D1-D5)
  resolved across subsequent interview turns. One
  additional dimension (D5: invocation mechanism) was
  surfaced during the D3 interview when the user asked about
  tmux; the Claude Code guide research confirmed the Agent
  SDK is the clean mechanism.

No item reopened any v001-v013 decision about what livespec
does. The v009 I0 architecture-vs-mechanism discipline,
I10 domain-vs-bugs discipline, K4 keyword-only discipline,
K5 template-shape decoupling, K10 fail-Finding discipline,
v012 L15b user-provided-extensions-minimal-requirements
principle, and v013 shipped-vs-not-shipped discipline all
held throughout the pass. v014 preserves v013's structural
architecture while closing recreatability gaps (N1, N2, N3,
N4, N5, N6, N7, N8, N9) and adding the E2E integration test
surface (N9).
