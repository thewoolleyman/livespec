---
proposal: proposal-critique-v09.md
decision: modify
revised_at: 2026-04-22T23:30:00Z
reviser_human: thewoolleyman
reviser_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v09

## Provenance

- **Proposed change:** `proposal-critique-v09.md` (in this directory) — a
  recreatability-focused defect critique surfacing 14 integration gaps
  (J1-J14) left in v009 PROPOSAL.md,
  `python-skill-script-style-requirements.md`, and `deferred-items.md`.
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context).
- **Revised at:** 2026-04-22 (UTC).
- **Scope:** v009 PROPOSAL.md + python style doc + `deferred-items.md`
  → v010 equivalents. `livespec-nlspec-spec.md` unchanged this pass
  (v009's Architecture-Level Constraints + Error Handling Discipline
  sections are load-bearing as-is). Focus: clean up residual references
  to v009-retired concepts (`DoctorInternalError`, `Fold.collect`),
  align cross-document disagreements (`git.get_git_user()` semantics,
  `build_parser` return-type exemption, coverage scope), and add a
  handful of forward-looking clarifications (exit code 4 for
  validation retries, HelpRequested vs UsageError distinction,
  `.vendor.jsonc` format, inverse `--run-pre-check` flag, template
  path resolution via wrapper, dogfood symlink git-tracking,
  `template_format_version` supported set, prune-history
  idempotency).

## Pass framing

This pass was a **recreatability-focused defect critique** producing
14 items (J1-J14). No meta-items were added mid-interview; the
architecture-vs-mechanism and domain-vs-bugs disciplines established
in v009 I0/I10 held as expected. Two items departed from the
recommended disposition based on user pushback:

- **J4** moved from recommended A (`finding_class` kwarg on stderr
  structlog events) to chosen B (new exit code `4` for schema
  validation), following the user's probe on exit-code standards.
  The user correctly flagged that the simpler exit-code discriminator
  is more LLM-reliable than parsing stderr structlog events; no POSIX
  / sysexits.h standard is broken by adding `4` below the signal-
  reserved range.
- **J9** moved from recommended A (strip the "or per-lib VERSION
  files" parenthetical from PROPOSAL.md / deferred-items) to chosen
  B (switch `.vendor.toml` → `.vendor.jsonc` reusing already-vendored
  `jsoncomment`), after the user asked whether TOML was Python-
  standard. It is not: `tomllib` is 3.11+ only (forbidden per style
  doc targeting 3.10+), so `.vendor.toml` would need a new vendored
  `tomli`. `.vendor.jsonc` avoids the new dependency by reusing the
  JSONC parser already in the bundle.

- **J3** was mid-interview-enriched: the user asked me to record
  explicitly that user-hosted custom specification templates at
  arbitrary non-plugin locations — and/or a template-discovery
  extension mechanism — is a deferred future feature. The chosen
  `bin/resolve_template.py` wrapper is the seed for that
  extensibility surface; a new `deferred-items.md` entry
  (`user-hosted-custom-templates`) captures the future scope.

- **J10** moved from recommended B (leave as-is; document the
  limitation) to chosen A (add inverse CLI flag `--run-pre-check`).
  The user preferred bidirectional CLI control over a documentation-
  only limitation.

Each J item carried one of four NLSpec failure modes (ambiguity /
malformation / incompleteness / incorrectness) and was grouped by
impact: major gaps (J1-J5; recreatability-blocking), significant
gaps (J6-J10; load-bearing guesses or wrong behavior), smaller
cleanup (J11-J14; enumerate / clarify / freeze).

No item reopened any v005-v009 decision about what livespec does.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| J1 | malformation | Accepted as recommended (option A — rewrite both DoctorInternalError + Fold.collect residuals in PROPOSAL.md + style doc) |
| J2 | malformation | Accepted as recommended (option A — fail on missing git binary; fall back on missing config) |
| J3 | incompleteness | Accepted with alternate option (option B — wrapper emits resolved template path) + new `user-hosted-custom-templates` deferred-items entry |
| J4 | ambiguity | Accepted with alternate option (option B — new exit code 4 for schema validation) |
| J5 | malformation | Accepted as recommended (option A — add `build_parser` to `check-public-api-result-typed` exemption list) |
| J6 | incompleteness | Accepted as recommended (option A — mirror I13 precedence for propose-change author) |
| J7 | incorrectness | Accepted as recommended (option A — `HelpRequested` marker; supervisor exits 0) |
| J8 | ambiguity | Accepted as recommended (option A — include `scripts/bin/` explicitly in coverage) |
| J9 | ambiguity | Accepted with alternate option (option B — switch `.vendor.toml` → `.vendor.jsonc`; reuse vendored jsoncomment) |
| J10 | incompleteness | Accepted with alternate option (option A — add inverse CLI flag `--run-pre-check`) |
| J11 | ambiguity | Accepted as recommended (option A — move `Finding` to `schemas/dataclasses/finding.py`) |
| J12 | ambiguity | Accepted as recommended (option A — committed tracked symlink) |
| J13 | ambiguity | Accepted as recommended (option A — enumerate `template_format_version: 1` as v1's sole supported value) |
| J14 | ambiguity | Accepted as recommended (option A — extend idempotency rule for repeat prune-history) |

## Governing principles reinforced (not newly established) during this pass

- **Architecture-vs-mechanism (v009 I0).** Reconfirmed at J1 via the
  `Fold.collect` residual strip: naming specific composition primitives
  is mechanism, not architecture. v010 PROPOSAL.md and style doc
  stop naming `Fold.collect` as normative.
- **Domain-vs-bugs (v009 I10).** Reconfirmed at J1 via the
  `DoctorInternalError` residual retire: the class is genuinely gone
  from every document; static check signatures uniformly use "any
  `LivespecError` subclass" (via the shorthand `DomainError` in the
  style doc's Exit code contract block).
- **Minimize new dependencies.** J9's disposition preferred reusing
  the already-vendored `jsoncomment` over forcing a new `tomli`
  vendored lib. Format choices should default to what's already in
  the bundle when the ergonomic difference is marginal.

## Disposition by item

### J1. DoctorInternalError + Fold.collect residuals (malformation → accepted, option A)

v009 I10 retired `DoctorInternalError`; v009 I2/I6 backed off from
naming `Fold.collect` as normative mechanism. But the implementer
pass missed four sites: PROPOSAL.md line 1284 (per-check signature),
line 1303 (orchestrator composition), line 1928 (DoD #6), and style
doc §"Package layout" per-check module contract.

Resolution:

- PROPOSAL.md line 1284: `IOResult[Finding, DoctorInternalError]` →
  `IOResult[Finding, E]` where `E` is any `LivespecError` subclass
  (match the style doc's Exit code contract block).
- PROPOSAL.md line 1303: strip `Fold.collect` naming. Replace with
  behavioral prose: "Composes all check results into one
  `IOResult[FindingsReport, E]` via the composition primitives from
  `dry-python/returns` — specific primitive is implementer choice
  under the architecture-level constraints."
- PROPOSAL.md line 1928 (DoD #6): drop `(Fold.collect)` parenthetical.
- Style doc §"Package layout" per-check module contract: change
  `IOResult[Finding, DoctorInternalError]` → `IOResult[Finding, E]`
  and cross-reference §"Exit code contract."

### J2. io/git.get_git_user() semantics disagreement (malformation → accepted, option A)

PROPOSAL.md (implementer pass): "git-unavailable → `IOSuccess('unknown')`
(domain fallback, not failure)."
deferred-items + v009 revision: "git-binary absent → `IOFailure(GitUnavailableError)`
exit 3; missing config → `IOSuccess('unknown')`."

Resolution:

- PROPOSAL.md §"Git" rewritten to match the v009 revision intent:
  "The function returns `IOSuccess('<name> <email>')` on success,
  `IOSuccess('unknown')` when git is available but either config
  value is unset (domain fallback), and
  `IOFailure(GitUnavailableError)` when the git binary is absent
  from PATH (domain error; supervisor maps to exit 3)."
- deferred-items + revision file already correct; no change needed.
- `GitUnavailableError` remains in the style doc `LivespecError`
  hierarchy with `exit_code = 3`.

### J3. Custom-template prompt-path unresolvable from SKILL.md (incompleteness → accepted, option B)

SKILL.md `@`-references are literal/static; custom templates at
arbitrary user-provided paths (via `.livespec.jsonc`'s `template`
field) have no defined access mechanism.

Resolution:

- New wrapper `bin/resolve_template.py` + Python module
  `livespec/commands/resolve_template.py` (pure `run()` + `main()`
  supervisor; returns exit 0 on success with the resolved template
  path on stdout, exit 3 with structured error on invalid template
  config).
- PROPOSAL.md skill layout tree adds `resolve_template.py` under
  `bin/`; commands tree adds `resolve_template.py`.
- Per-sub-command SKILL.md body structure step 4 rewrites: "Invoke
  `bin/resolve_template.py` via Bash; capture the resolved template
  path from stdout. Then use the Read tool to read
  `<resolved-path>/prompts/<name>.md`."
- PROPOSAL.md §"Per-sub-command SKILL.md body structure" explicitly
  drops the literal `@`-reference syntax recommendation in favor of
  the two-step dispatch.
- `skill-md-prose-authoring` deferred-items entry widens to cover
  the two-step dispatch prose per sub-command.

**New deferred-items entry: `user-hosted-custom-templates`.**
Documents that user-hosted custom specification templates at
arbitrary non-plugin locations — and any future template-discovery
extension mechanism (plugin-path hints, remote template fetch,
template registry, etc.) — are deferred v2+ work. The
`bin/resolve_template.py` wrapper is the seed for this
extensibility surface and should not ossify against future
extensions.

### J4. Retry-on-exit-3 class ambiguity (ambiguity → accepted, option B)

All four exit-3 classes (schema validation, pre-step static, sub-
command precondition, post-step static) share the same exit code;
LLM has no discriminator for retry classification.

Resolution:

- **New exit code `4`: "Schema validation failed (retryable)."**
  Emitted only when the wrapper's internal JSON validation against
  a schema fails; e.g., `seed_input.schema.json`,
  `proposal_findings.schema.json`, `revise_input.schema.json`.
- Style doc §"Exit code contract" table gains a new row:
  `| 4 | Schema validation failed: LLM-provided JSON payload does
  not conform to the wrapper's input schema (retryable). |`.
- PROPOSAL.md §"Per-sub-command SKILL.md body structure" step 4
  "Retry-on-exit-3" renamed → "Retry-on-exit-4": "on wrapper exit
  code 4, re-invoke the relevant template prompt with the
  structured error context from stderr and re-assemble the JSON
  payload. Up to 3 retries; abort on repeated failure."
- PROPOSAL.md §"propose-change" / §"seed" / §"critique" / §"revise"
  each update the "on validation failure, it exits 3" wording to
  "on validation failure, it exits 4."
- Style doc §"CLI argument parsing seam" supervisor derive-exit-code
  behavior extends: on `IOFailure(ValidationError)`, the supervisor
  returns 4 (not err.exit_code per se — the ValidationError's
  exit_code class attribute is set to 4 in errors.py).
- `errors.py` hierarchy: `ValidationError.exit_code: ClassVar[int] = 4`
  (was 3 in v009).
- `static-check-semantics` deferred item widens to cover exit-code
  4 vs 3 disposition in the supervisor's `derive_exit_code`.

### J5. build_parser() return-type exemption (malformation → accepted, option A)

`commands/<cmd>.py`'s `build_parser() -> ArgumentParser` violates
`check-public-api-result-typed` as narrowed by I4 (exempts only
functions named `main`).

Resolution:

- Style doc §"Type safety" Result/IOResult rule exempts
  `build_parser` by function name in addition to `main`. Rewrite:
  "Every public function's return annotation MUST be `Result[_, _]`
  or `IOResult[_, _]`, UNLESS the function is a supervisor at a
  deliberate side-effect boundary (`main` in `commands/**.py` and
  `doctor/run_static.py`) OR the `build_parser` factory in
  `commands/**.py` (pure argparse constructor, no effects, cannot
  fail)."
- `static-check-semantics` deferred item widens to cover the AST
  name-match exemption for `build_parser` alongside `main`.

### J6. propose-change author precedence rule (incompleteness → accepted, option A)

v009 I13 established env var → payload → `"unknown-llm"` precedence
for `reviser_llm` on revise/critique/seed auto-capture. Propose-
change's `author` field was uncovered.

Resolution:

- PROPOSAL.md §"propose-change" adds an Author-resolution paragraph
  mirroring I13: precedence (1) CLI `--author <id>` if set;
  (2) `LIVESPEC_REVISER_LLM` env var if set and non-empty; (3) LLM
  self-declared `author` field in the proposal-findings JSON payload
  if present and non-empty; (4) literal `"unknown-llm"` fallback.
- PROPOSAL.md §"Configuration: `.livespec.jsonc` → Environment
  variables" updates `LIVESPEC_REVISER_LLM` entry to name
  propose-change alongside revise and critique.
- `proposal_findings.schema.json` gains optional file-level `author`
  field (string). `wrapper-input-schemas` deferred-items entry
  widens to cover the schema extension.
- `bin/propose_change.py` accepts a new optional CLI flag
  `--author <id>`.

### J7. --help exits 2 as usage error (incorrectness → accepted, option A)

Style doc §"CLI argument parsing seam" routed `-h`/`--help` through
`IOFailure(UsageError)` → exit 2. A user asking for help isn't a
usage error. Standard CLI: `--help` exits 0.

Resolution:

- New class `HelpRequested` added to `livespec/errors.py`. It is
  NOT a `LivespecError` subclass (not a domain error; not a bug —
  a third informational-early-exit category). Subclasses `Exception`
  directly but with a class attribute `exit_code: ClassVar[int] = 0`
  for supervisor pattern-matching convenience.
- `io/cli.py`'s argparse wrapper returns
  `IOResult[Namespace, UsageError | HelpRequested]`. `-h`/`--help`
  detection before `parse_args` returns `IOFailure(HelpRequested("<help text>"))`.
- Supervisor pattern-match (style doc §"Exit code contract"):
  - On `IOFailure(HelpRequested(text))`: emit `text` to stdout →
    return 0.
  - On `IOFailure(UsageError)`: emit to stderr → return 2.
  - Otherwise continue per existing rules.
- Style doc §"Exit code contract" table header note adds "Exit code
  0 also covers intentional `--help` output (not treated as error)."
- `static-check-semantics` deferred item picks up the supervisor's
  three-way pattern match disposition.

### J8. Coverage scope silence on scripts/bin/ (ambiguity → accepted, option A)

Resolution:

- PROPOSAL.md §"Testing approach" and style doc §"Code coverage"
  both revise: "100% line + branch coverage is mandatory across
  `scripts/livespec/**`, `scripts/bin/**`, and
  `<repo-root>/dev-tooling/**`."
- `pyproject.toml`'s `[tool.coverage.run]` sets
  `source = ["livespec", "<bin-path-relative-to-pyproject>"]`
  (exact path TBD during config authoring).
- Wrapper bodies' `# pragma: no cover` acknowledgements remain
  (wrappers are trivial pass-throughs; wrapper-shape meta-test
  verifies shape).
- `_bootstrap.py` has no pragma — it's fully covered by
  `tests/bin/test_bootstrap.py`.

### J9. .vendor.toml → .vendor.jsonc switch (ambiguity → accepted, option B)

`.vendor.toml` would require Python TOML parser; `tomllib` is 3.11+
only (forbidden on the 3.10+ floor). Rather than vendor `tomli` for
a narrow config, switch to JSONC (already handled by vendored
`jsoncomment`).

Resolution:

- Rename everywhere: `.vendor.toml` → `.vendor.jsonc`. PROPOSAL.md,
  style doc, deferred-items, DoD, developer-tooling layout.
- PROPOSAL.md line 325 strips the "or per-lib VERSION files"
  parenthetical (now unambiguous).
- Shape: one JSONC file at repo root. Schema:
  ```jsonc
  {
    // Vendored library version records.
    "returns": {
      "upstream_url": "https://github.com/dry-python/returns",
      "upstream_ref": "0.22.0",
      "vendored_at": "2026-04-22T23:00:00Z"
    },
    "fastjsonschema": { /* ... */ },
    "structlog": { /* ... */ },
    "jsoncomment": { /* ... */ }
  }
  ```
- Consumer: `just vendor-update <lib>` recipe reads/updates via a
  tiny Python script at `dev-tooling/vendor_update.py` (or inline
  via `python3 -c`) that parses through `livespec.parse.jsonc` (or
  directly through jsoncomment) — no new deps.
- Future checks that want to programmatically read the file go
  through `livespec.parse.jsonc` like `.livespec.jsonc`.

### J10. --run-pre-check inverse CLI flag (incompleteness → accepted, option A)

Resolution:

- PROPOSAL.md §"Pre-step skip control" documents bidirectional
  control:
  - `--skip-pre-check` flag sets skip = true.
  - `--run-pre-check` flag sets skip = false.
  - Neither flag set → use config's `pre_step_skip_static_checks`.
  - Both flags set → argparse usage error (mutually exclusive flag
    pair; exit 2).
- Per-sub-command SKILL.md body structure step 3 (Inputs) for
  every pre-step-having sub-command (propose-change, critique,
  revise, prune-history) lists both flags.
- `bin/doctor_static.py` continues to reject BOTH `--skip-pre-check`
  AND `--run-pre-check` (exit 2); it IS the static phase.
- `static-check-semantics` deferred item widens to cover the
  mutually-exclusive flag pair and the doctor_static rejection.

### J11. Finding dataclass pairing (ambiguity → accepted, option A)

Resolution:

- Move `Finding` dataclass to
  `scripts/livespec/schemas/dataclasses/finding.py` (from previous
  `scripts/livespec/doctor/finding.py`).
- Constructor helpers (`pass_finding`, `fail_finding`) move to
  the same file as the dataclass.
- `scripts/livespec/doctor/finding.py` deleted OR becomes a
  re-export shim (`from livespec.schemas.dataclasses.finding import
  Finding, pass_finding, fail_finding`). PROPOSAL.md and style doc
  skill-layout trees updated to reflect the move.
- `doctor_findings.schema.json` is paired with `DoctorFindings`
  dataclass at `schemas/dataclasses/doctor_findings.py`;
  `DoctorFindings.findings: list[Finding]` imports `Finding` from
  its new home.
- `check-schema-dataclass-pairing` walks `schemas/dataclasses/*.py`
  only (unchanged scope); now finds both `Finding` and
  `DoctorFindings` in the same tree.
- New schema `finding.schema.json` (optional — the `Finding` shape
  could instead be embedded as the `items` schema of
  `doctor_findings.schema.json`'s `findings` array; implementer
  choice). `static-check-semantics` deferred item picks up the
  embedded-vs-standalone decision; either is acceptable.

### J12. Dogfood symlink git-tracking (ambiguity → accepted, option A)

Resolution:

- PROPOSAL.md §"Plugin delivery" codifies: "`.claude/skills/` is
  committed to git as a tracked symbolic link pointing at
  `../.claude-plugin/skills/`. Fresh clones pick up the symlink
  immediately (git tracks symlinks on Linux and macOS, both in v1
  scope). `just bootstrap` re-creates the symlink defensively if
  a developer accidentally removes it; it is not required before
  Claude Code can load the skills on a fresh clone."
- No `.gitignore` entry for `.claude/skills/`.

### J13. template_format_version supported set enumeration (ambiguity → accepted, option A)

Resolution:

- PROPOSAL.md §"Templates → Custom templates are in v1 scope" (or
  §"Static-phase checks → template-exists") adds: "v1 livespec
  supports only `template_format_version: 1`. The `template-exists`
  check MUST reject any other value as unsupported, naming the
  offending field, its value, and the template path."
- Style doc is unaffected (not a code-quality invariant).

### J14. prune-history repeat-no-op rule (ambiguity → accepted, option A)

Resolution:

- PROPOSAL.md §"Pruning history → Invariants" adds: "Running
  `prune-history` on a project where the oldest surviving history
  entry is already a `PRUNED_HISTORY.json` marker (i.e., no full
  versions to prune) is a no-op. The existing marker is not
  re-written; no new commit-worthy diff is produced."
- Implementation: `prune-history` short-circuits before step 4
  when the preconditions match.

## Deferred-items inventory (carried forward + new + scope-widened)

Per the deferred-items discipline, every carried-forward item is
enumerated below. Additions, scope-widenings, and renames are
flagged.

**Carried forward unchanged from v009:**

- `template-prompt-authoring` (v001).
- `python-style-doc-into-constraints` (v005).
- `companion-docs-mapping` (v001).
- `enforcement-check-scripts` (v005).
- `claude-md-prose` (v006).
- `returns-pyright-plugin-disposition` (v007).

**Scope-widened in v010:**

- `static-check-semantics` (v007; renamed v008; widened every pass
  since). v010 additions:
  - J4: exit-code 4 disposition in the supervisor's
    `derive_exit_code` (ValidationError → 4; all other LivespecError
    subclasses → their class-attribute exit_code).
  - J5: `check-public-api-result-typed` name-match exemption for
    `build_parser` alongside `main`.
  - J7: supervisor three-way pattern match for `HelpRequested` /
    `UsageError` / other `LivespecError` subclasses.
  - J10: mutually-exclusive `--skip-pre-check` / `--run-pre-check`
    flag pair in argparse for pre-step-having sub-commands;
    `bin/doctor_static.py` rejects both.
  - J11: `check-schema-dataclass-pairing` walks
    `schemas/dataclasses/*.py` (unchanged scope); `Finding` now in
    that tree. Optional: standalone `finding.schema.json` vs
    embedded-in-`doctor_findings.schema.json` items shape.
  - J14: `prune-history` short-circuit precondition detection.
- `front-matter-parser` (v007; widened v009). v010 additions: none
  directly, but the reserved `livespec-` prefix discipline from I9
  continues to govern the proposed_change_front_matter schema.
- `wrapper-input-schemas` (v008; widened v009). v010 additions:
  - J6: optional file-level `author` field in
    `proposal_findings.schema.json`; validation-error finding
    shape now exit-code 4 (J4).
- `task-runner-and-ci-config` (v006; widened v009; widened v010).
  v010 additions:
  - J8: `pyproject.toml`'s `[tool.coverage.run]` `source` list
    must include the `scripts/bin/` path (exact form TBD during
    config authoring).
  - J9: rename `.vendor.toml` → `.vendor.jsonc` throughout;
    `just vendor-update <lib>` recipe reads/updates JSONC via a
    tiny Python script (or inline `python3 -c` through vendored
    `jsoncomment`).
  - J10: `lefthook.yml` pre-commit/pre-push hook invocations of
    pre-step-having commands pass `--skip-pre-check` or
    `--run-pre-check` as appropriate (implementer choice; default
    follows `.livespec.jsonc` config).
- `skill-md-prose-authoring` (v008 H4; widened v009; widened v010).
  v010 additions:
  - J3: two-step template-prompt dispatch prose (invoke
    `bin/resolve_template.py`; capture stdout; Read
    `<path>/prompts/<name>.md`) per sub-command that uses a
    template prompt.
  - J4: retry prose references exit code 4 (not 3) as the retry
    trigger.
  - J10: Inputs section enumerates `--skip-pre-check` and
    `--run-pre-check` for pre-step-having sub-commands.

**New in v010:**

- **`user-hosted-custom-templates`** (v010 J3):
  - **Source:** v010 (J3)
  - **Target spec file(s):** `SPECIFICATION/spec.md` v2+ non-goals
    note; potentially a new v2 `SPECIFICATION/spec.md` section on
    template discovery
  - **How to resolve:** Codify in v2 scope (post-v1) that the
    `bin/resolve_template.py` wrapper is the extensibility seam
    for future template-discovery mechanisms — user-hosted
    templates at arbitrary non-plugin locations (e.g., remote
    URLs, template registries, plugin-path hints, per-environment
    template overrides). The v1 wrapper accepts only built-in
    names (`"livespec"`) or project-root-relative paths; v2 may
    extend the resolution algorithm without breaking the wrapper's
    output contract (stdout = resolved template path). Keep
    wrapper output format stable as the v1 → v2 migration shield.

**Removed:**

None.

## Self-consistency check

Post-revision invariants rechecked:

- **DoctorInternalError fully retired.** No references remain in
  PROPOSAL.md or the style doc (only the historical footnote in
  the style doc's Exit code contract block explaining the retirement).
- **Fold.collect no longer named as normative mechanism.**
  Orchestrator description in PROPOSAL.md and DoD is behavioral
  only; style doc §"Railway-Oriented Programming" already had the
  "implementer choice under architecture-level constraints" clause.
- **io/git.get_git_user() semantics unified.** PROPOSAL.md, deferred-
  items, and v009 revision file all say "missing binary = IOFailure;
  missing config = IOSuccess('unknown')." Cross-document alignment.
- **Exit codes 0/1/2/3/4/126/127.** New code 4 for retryable schema
  validation; doctor static still uses 3 for precondition failures;
  bugs still 1; usage 2; permission 126; tool-missing 127.
- **HelpRequested clean.** Separate class; `Exception` base (not
  `LivespecError`); supervisor pattern-matches into three paths
  (HelpRequested → 0, LivespecError → err.exit_code, else continue).
- **build_parser exemption surgical.** Named by function identifier
  in the style doc rule and the AST check; does not widen
  `check-public-api-result-typed` more broadly.
- **Coverage scope explicit.** `scripts/livespec/**` +
  `scripts/bin/**` + `dev-tooling/**` at 100% line+branch.
- **.vendor.jsonc.** All references renamed; `jsoncomment` remains
  the sole JSONC parser; no `tomli` or other new vendored lib.
- **Inverse --run-pre-check flag.** Three-valued semantics documented;
  mutually-exclusive pair validated at argparse level;
  `bin/doctor_static.py` rejects both.
- **Finding in schemas/dataclasses/.** Single location for paired
  dataclasses; `check-schema-dataclass-pairing` walks one tree.
- **Symlink committed as tracked.** Fresh-clone dogfood works
  without `just bootstrap`; bootstrap is defensive.
- **template_format_version: {1}.** Enumerated invariant in
  PROPOSAL.md.
- **prune-history repeat-no-op.** Idempotency rule explicit.
- **New deferred-items entry user-hosted-custom-templates.** Captures
  v2+ template-discovery extensibility intent.
- **Author identifier reservations intact.** `livespec-` prefix
  reserved (v009 I9); propose-change author resolves via same
  precedence as I13 (env → payload → "unknown-llm").
- **Recreatability.** A competent implementer can generate the
  v010 livespec plugin + built-in template + sub-commands +
  enforcement suite + dev-tooling from v010 PROPOSAL.md +
  `livespec-nlspec-spec.md` + updated
  `python-skill-script-style-requirements.md` + updated
  `deferred-items.md` alone. All residual stale references cleaned;
  cross-document disagreements resolved; future-feature seams
  (template resolution, validation-class discriminator) codified at
  the architecture level with mechanism details implementer-chosen
  under the enforcement suite.

## Outstanding follow-ups

Tracked in the updated `deferred-items.md` (see inventory above).
The v010 pass touched 6 existing entries (adding scope-widenings)
and added 1 new entry (`user-hosted-custom-templates`). No entries
were removed.

## What was rejected

Nothing was rejected outright. Three items moved from recommended
option to alternate option based on user input:

- **J4** (exit-code discriminator) — moved A → B after user probed
  whether introducing exit code 4 would break any standards. No
  standard is broken; exit-code granularity is cleaner for LLM
  retry classification than parsing stderr structlog events.
- **J9** (`.vendor.toml` cleanup) — moved A → B after user asked
  whether TOML is Python-standard. It is not on 3.10+ (`tomllib` is
  3.11+-only, forbidden per style doc); rather than vendor `tomli`,
  switch to JSONC using already-vendored `jsoncomment`.
- **J10** (pre-step skip CLI override) — moved B → A; user preferred
  bidirectional CLI control over documenting the "config is sticky"
  limitation.

One item (J3) was mid-interview-enriched: the user asked for an
explicit deferred-items entry (`user-hosted-custom-templates`)
capturing the future flexibility for user-hosted templates at
arbitrary non-plugin locations. The `bin/resolve_template.py`
wrapper is the seed for that extensibility surface.

No item "pulled threads" into reopening prior-version decisions.
Architecture-level constraint discipline (v009 I0) + error-handling
discipline (v009 I10) held throughout the pass. v010 is a cleanup
pass that leaves v009's structural architecture intact.
