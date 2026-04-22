---
proposal: proposal-critique-v07.md
decision: modify
revised_at: 2026-04-22T00:00:00Z
reviser_human: thewoolleyman
reviser_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v07

## Provenance

- **Proposed change:** `proposal-critique-v07.md` (in this directory) — a
  recreatability-focused defect critique evaluating v007 PROPOSAL.md +
  `python-skill-script-style-requirements.md` against the embedded
  `livespec-nlspec-spec.md` guidelines.
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context).
- **Revised at:** 2026-04-22 (UTC).
- **Scope:** v007 PROPOSAL.md + python style doc + deferred-items.md →
  v008 PROPOSAL.md + updated style doc + updated deferred-items.md.
  Bootstrap sys.path correctness, JSONC vendoring, argparse seam in
  io/, canonical SKILL.md body shape, ruff arg-count gate restoration,
  explicit seed/revise wrapper inputs, context-dataclass minimum
  fields, doctor allowed-tools honesty, factory-validator cache
  location, findings-schema split, out-of-band-edits re-run guard,
  directory-README paragraphs, widened static-check-semantics
  deferred item, GFM anchor algorithm, tests/fixtures carve-out,
  canonical seed auto-capture content.

## Pass framing

This pass was a **defect critique with grounded recreatability
review**, continuing v007's framing. 16 items (H1-H16) used the
NLSpec failure-mode framework (ambiguity / malformation /
incompleteness / incorrectness) and were grouped by impact: major
gaps (H1-H4; recreatability-blocking), significant gaps (H5-H12;
load-bearing guesses), smaller cleanup (H13-H16; enumerate / freeze
/ rename).

Two mid-interview corrections materially reshaped items:

1. **H5 reframed after user pushback.** The initial option set
   offered "drop `max-args=6`" (honoring v006 P9) as the
   recommendation. The user asked: *"Is there any reason to ever
   allow more than six? If there are more than that, it should be
   refactored to wrapper objects or structs, correct?"* That
   correctly identified the refactor-to-dataclass guardrail as the
   load-bearing intent. Reframed options distinguished ruff
   `PLR0913` (all args) from `PLR0917` (positional only). User
   selected option C (both at 6) — the strongest gate, reversing
   v006 P9 entirely.
2. **H11 reframed after user question.** Initial option A ("both
   sides HEAD-committed") claimed the auto-backfill cycle was
   "non-destructive." The user asked: *"How can option A be
   non-destructive if the auto fill writes the same version?"* That
   correctly identified that HEAD-to-HEAD comparison alone doesn't
   handle rerun-before-commit (the second run would overwrite,
   collide, or pile up). Reframed option A' added an explicit
   pre-backfill guard: if uncommitted `history/v(N+1)/` or stale
   `out-of-band-edit-*.md` is on disk, emit "commit existing
   backfill and re-run" without repeating the backfill. The user's
   own reasoning reinforced it: under the commit-after-successful-
   revise workflow discipline, uncommitted history on disk IS
   anomalous, and refusing to proceed is correct behavior.

The pass did NOT re-open any v005/v006/v007 decision about WHAT
livespec does (sub-commands, template architecture, lifecycle,
history shape, proposed-change / revision file formats,
per-sub-command skill structure, ROP all-the-way-down, vendoring of
returns/fastjsonschema/structlog, ruff + pyright + pytest +
coverage, just/lefthook/CI, CLAUDE.md coverage scope). It
clarified, integrated, enumerated, and resolved contradictions.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| H1 | malformation | Accepted as recommended (option A) |
| H2 | incompleteness | Accepted with library choice (option B + jsoncomment) |
| H3 | malformation | Accepted as recommended (option A) |
| H4 | incompleteness | Accepted as recommended (option A) |
| H5 | malformation | Modified-on-accept (option C — both PLR0913+PLR0917 at 6, reversing v006 P9) |
| H6 | ambiguity | Accepted as recommended (option A) |
| H7 | incompleteness | Accepted as recommended (option A) |
| H8 | malformation | Accepted as recommended (option A) |
| H9 | ambiguity | Accepted as recommended (option A) |
| H10 | ambiguity | Accepted as recommended (option A) |
| H11 | ambiguity | Modified-on-accept (option A' — HEAD-to-HEAD + pre-backfill guard) |
| H12 | incompleteness | Accepted as recommended (option A) |
| H13 | incompleteness | Accepted as recommended (option A — widen deferred scope; rename) |
| H14 | ambiguity | Accepted as recommended (option A) |
| H15 | ambiguity | Accepted as recommended (option A) |
| H16 | incompleteness | Accepted as recommended (option A) |

## Governing principles established or reinforced during this pass

Two cross-cutting principles emerged or were sharpened.

### Mechanical refactor-to-dataclass enforcement at 7+ args

User correctly identified that the "Python's keyword-only args and
dataclasses decompose parameter sets naturally" rationale (v006 P9)
presumed voluntary discipline. If the refactor-to-struct pattern is
the intent, it should be enforced mechanically. v008 enables both
ruff `PLR0913` (all args) and `PLR0917` (positional args) at max 6,
reversing v006 P9's "no positional-arg limit" decision. Functions
exceeding 6 args (in either sense) MUST decompose to dataclasses.

This aligns with the v006 guardrails principle ("strongest-possible
guardrails for agent-authored Python") and closes a gap where
voluntary-discipline language was treated as enforcement.

### Non-destructive auto-backfill via explicit state guards

User pushback on H11 established that state-mutating static checks
(in v007's `out-of-band-edits` auto-backfill) MUST guard against
re-running-before-commit. The pattern is: before performing a
stateful action, detect whether the prior run's output is still
uncommitted; if so, emit a "finish prior work first" finding and
skip the action.

This generalizes: any future livespec operation that writes
history directories SHOULD apply the same guard so the
commit-between-runs workflow discipline is enforced by the tool,
not merely assumed.

## Disposition by item

### H1. Bootstrap sys.path vs vendored imports (malformation → accepted, option A)

Style doc's `_bootstrap.py` body adds only `scripts/` to sys.path;
vendored libs at `scripts/_vendor/` don't resolve as `returns.io`,
`fastjsonschema`, `structlog`. `livespec/__init__.py`'s
`import structlog` fails on first package import.

Resolution: `_bootstrap.py:bootstrap()` inserts BOTH `scripts/` and
`scripts/_vendor/` into sys.path. Style doc's `_bootstrap.py` body
and prose updated. `check-wrapper-shape` unchanged (still excludes
`_bootstrap.py`).

### H2. JSONC parser unspecified (incompleteness → accepted with library, option B + jsoncomment)

`.livespec.jsonc` is JSON-with-comments; stdlib `json` can't parse
comments; no deferred-items entry covered it. User chose to vendor a
fourth pure-Python JSONC library: **`jsoncomment`** (MIT, zero deps,
~100 LLOC comment-stripping layer over stdlib `json.loads`).

Resolution:

- Add `jsoncomment` to the vendored-libs list in PROPOSAL.md,
  `python-skill-script-style-requirements.md`, `.vendor.toml`,
  `NOTICES.md`.
- `scripts/livespec/parse/jsonc.py` is a thin pure wrapper over
  `jsoncomment` returning `Result[dict, ParseError]`.
- Add to PROPOSAL.md § "Configuration: `.livespec.jsonc`" the
  dialect definition: "`.livespec.jsonc` uses the JSONC dialect:
  JSON plus `//` line comments and `/* ... */` block comments. No
  trailing commas, no single-quoted strings, no unquoted keys."
- NO new deferred-items entry. Vendoring is ordinary v1 work.

### H3. argparse in commands/main violates check-supervisor-discipline (malformation → accepted, option A)

Argparse's `ArgumentParser.parse_args()` raises `SystemExit` on
usage errors and `--help`. Under the 6-line wrapper shape, argparse
must live in `livespec.commands.<cmd>.main()` — but
`check-supervisor-discipline` rejects `SystemExit` outside `bin/`.

Resolution: a new CLI argument-parsing seam.

- All argparse usage lives in `livespec/io/cli.py`, wrapped with
  `@impure_safe` and `exit_on_error=False` (Python 3.9+).
- Each `livespec/commands/<cmd>.py` exposes a pure `build_parser()
  -> ArgumentParser` factory (no parse; no I/O).
- `io.cli.parse_args(argv, parser) -> IOResult[Namespace,
  UsageError]` is the single parse entry point; it detects
  `-h`/`--help` explicitly and routes to the railway
  (`IOFailure(UsageError("..."))` with usage text attached).
- Supervisor maps `IOFailure(UsageError)` → exit 2.
- `check-supervisor-discipline` scope clarified: `livespec/**` is
  in scope; only `bin/*.py` (including `_bootstrap.py`) is exempt.
- The `static-check-semantics` deferred item (renamed from
  `ast-check-semantics`; see H13) widens to include argparse's
  `SystemExit` disposition and the `-h`/`--help` convention.

### H4. SKILL.md prose body undefined (incompleteness → accepted, option A)

Per-sub-command SKILL.md frontmatter is specified; prose body —
which orchestrates every LLM-driven behavior post-wrapper — is
nowhere and not deferred.

Resolution:

1. Add PROPOSAL.md § "Per-sub-command SKILL.md body structure"
   codifying the canonical body shape:
   - Opening statement (mirrors `description`).
   - "When to invoke" — user-facing trigger phrases.
   - "Inputs" — CLI flags and their meanings.
   - "Steps" — ordered list of LLM-driven steps (each either
     invokes `bin/<cmd>.py` via Bash, references a template prompt
     via `@`-path, validates output against a schema, prompts the
     user, or narrates warnings).
   - "Post-wrapper" — LLM-driven post-step behavior (or its
     absence, e.g., `prune-history`, `help`, post-static-fail
     abort).
   - "Failure handling" — exit-code-to-narration mapping.
2. Add a new `skill-md-prose-authoring` entry to
   `deferred-items.md`:
   - Source: v008 (NEW, H4).
   - Target: `.claude-plugin/skills/<sub-command>/SKILL.md` (one
     per sub-command).
   - How to resolve: author each SKILL.md body per the canonical
     shape; cover trigger phrases, wrapper invocations, template
     prompt `@`-references, schema validation routing, per-proposal
     confirmation (revise), `--skip-pre-check` /
     `--skip-subjective-checks` handling.

### H5. ruff max-args vs no-positional-arg-limit (malformation → modified-on-accept, option C, reversing v006 P9)

User reframed the initial "drop max-args=6" recommendation with
the question *"If more than six, it should be refactored to wrapper
objects or structs, correct?"* That identified the refactor-to-
dataclass discipline as the load-bearing intent, warranting
mechanical enforcement over voluntary discipline.

Resolution:

- `pyproject.toml`'s `[tool.ruff.lint.pylint]` sets both
  `max-args = 6` (PLR0913, all args) and `max-positional-args = 6`
  (PLR0917, positional only).
- Style doc § "Complexity thresholds" rewrites "No positional-arg
  limit" to: "Arguments (positional OR total) MUST NOT exceed 6
  per function. Functions needing more parameters MUST be
  refactored to accept a dataclass. Enforced by ruff `PLR0913` +
  `PLR0917`."
- v006 P9's "no positional-arg limit" decision is explicitly
  reversed. The reason v006 P9 gave (Python's keyword-only args +
  dataclasses) is inverted: those are the REFACTOR TARGETS the
  gate enforces, not reasons to disable the gate.
- `max-branches = 10` and `max-statements = 30` unchanged.

### H6. seed and revise wrapper input contracts (ambiguity → accepted, option A)

v007 G11 resolved propose-change and critique to use
`--findings-json`. Seed said "or equivalent entry path"; revise had
no wrapper input documented. Mid-interview clarification
established that seed and revise JSON inputs have fundamentally
different shapes from findings arrays, so distinct schemas + flags
are warranted.

Resolution:

- `bin/seed.py --seed-json <path>` where `<path>` points at a
  tempfile conforming to `seed_input.schema.json`:
  ```json
  {
    "files": [{"path": "SPECIFICATION/spec.md", "content": "..."}],
    "intent": "<verbatim user intent>"
  }
  ```
- `bin/revise.py --revise-json <path>` where `<path>` conforms to
  `revise_input.schema.json`:
  ```json
  {
    "decisions": [
      {
        "proposal_topic": "foo",
        "decision": "accept|modify|reject",
        "rationale": "...",
        "modifications": "...",
        "resulting_files": [{"path": "...", "content": "..."}]
      }
    ]
  }
  ```
- Both schemas live under `scripts/livespec/schemas/`.
- PROPOSAL.md § "seed" drops "or equivalent entry path" in favor of
  the explicit flag.
- PROPOSAL.md § "revise" adds an explicit paragraph on the wrapper
  input and the LLM-side confirmation flow.
- The new `wrapper-input-schemas` entry in `deferred-items.md`
  covers authoring the two new schemas AND the
  `proposal_findings.schema.json` rename from H10.

### H7. Context dataclass fields undefined (incompleteness → accepted, option A)

The railway payload shape is load-bearing but unspecified.

Resolution: style doc (new subsection under "Package layout" named
"Context dataclasses") enumerates minimum fields for each context:

```python
@dataclass(frozen=True)
class DoctorContext:
    project_root: Path          # repo root containing SPECIFICATION/
    config: LivespecConfig      # parsed .livespec.jsonc
    template_root: Path         # resolved template directory
    run_id: str                 # uuid4 string bound at wrapper startup
    git_head_available: bool    # false when not a git repo or no HEAD commit

@dataclass(frozen=True)
class SeedContext:
    doctor: DoctorContext
    seed_input: SeedInput       # parsed seed_input.schema.json payload

@dataclass(frozen=True)
class ProposeChangeContext:
    doctor: DoctorContext
    findings: ProposalFindings  # parsed proposal_findings.schema.json payload
    topic: str

@dataclass(frozen=True)
class CritiqueContext:
    doctor: DoctorContext
    findings: ProposalFindings
    author: str

@dataclass(frozen=True)
class ReviseContext:
    doctor: DoctorContext
    revise_input: ReviseInput   # parsed revise_input.schema.json payload
    steering_intent: str | None

@dataclass(frozen=True)
class PruneHistoryContext:
    doctor: DoctorContext
```

All contexts embed `DoctorContext` rather than subclassing. The
nested-dataclass shape preserves immutability and type narrowing
through the railway.

### H8. doctor allowed-tools vs out-of-band-edits writes (malformation → accepted, option A)

`doctor`'s `allowed-tools: Bash + Read` with "read-only validation"
framing contradicts the `out-of-band-edits` check's auto-backfill
writes.

Resolution:

- `doctor` skill's `allowed-tools` becomes `Bash + Read + Write`.
- "read-only validation; fixes route through `propose-change`"
  phrasing drops. Replace with: "doctor's static phase MAY write
  to `SPECIFICATION/proposed_changes/` and
  `SPECIFICATION/history/` under the narrow auto-backfill path of
  the `out-of-band-edits` check (see § Static-phase checks)."
- PROPOSAL.md § "Per-sub-command skill frontmatter" updated
  accordingly.

### H9. Factory-validator cache location (ambiguity → accepted, option A)

The documented "cache via `functools.lru_cache` keyed on `$id`"
doesn't work literally (dicts are unhashable; `lru_cache` keys on
args). Module-level dict in `validate/` would trip
`check-global-writes`.

Resolution:

- The compile cache lives in
  `livespec/io/fastjsonschema_facade.py` (impure boundary; already
  confines `Any` and `# type: ignore` for vendored fastjsonschema
  types).
- The facade holds a module-level `_COMPILED: dict[str, Callable]
  = {}` keyed on `$id`.
- The facade's cache read/write is added to the documented
  `check-global-writes` exemption list alongside
  `structlog.configure` and `structlog.contextvars.bind_contextvars`.
  Exemption documented in the renamed `static-check-semantics`
  deferred item (H13).
- `validate/<name>.py` stays strictly pure; it calls the facade's
  `compile_schema(schema_id, schema) -> Callable[[dict], Result[dict,
  ValidationError]]` which handles cache lookup + compile.
- Style doc § "Purity and I/O isolation" gets a note that the
  compile cache is a facade-layer concern, not a validator
  concern.

### H10. findings → Proposal section mapping (ambiguity → accepted, option A)

The mapping was referenced but not defined; `critique_findings.schema.json`
was doing double duty.

Resolution:

- Two distinct schemas in `scripts/livespec/schemas/`:
  - **`doctor_findings.schema.json`** — doctor static-phase
    output: `{findings: [{check_id, status, message, path, line}]}`.
    Used internally by doctor; not passed to propose-change.
  - **`proposal_findings.schema.json`** — propose-change /
    critique template prompt output: `{findings: [{name,
    target_spec_files, summary, motivation, proposed_changes}]}`.
    Each finding maps one-to-one to a `## Proposal` section with
    the four required sub-headings populated from the corresponding
    JSON fields.
- `critique_findings.schema.json` is renamed to
  `proposal_findings.schema.json` everywhere it appears (PROPOSAL.md,
  style doc, layout diagrams).
- PROPOSAL.md § "propose-change" clarifies the one-to-one mapping.
- `wrapper-input-schemas` deferred item covers authoring both
  schemas.

### H11. out-of-band-edits comparison semantics + rerun-before-commit (ambiguity → modified-on-accept, option A')

User's mid-interview clarification revealed that plain HEAD-to-HEAD
comparison doesn't handle the rerun-before-commit edge case.

Resolution (option A'):

- Both sides HEAD-committed: `git show HEAD:SPECIFICATION/spec.md`
  vs `git show HEAD:SPECIFICATION/history/vN/spec.md`. Working-
  tree WIP ignored for the comparison.
- **Pre-backfill guard.** Before running backfill, the check
  inspects the working tree for:
  1. Any `SPECIFICATION/history/v(N+1)/` directory.
  2. Any `SPECIFICATION/proposed_changes/out-of-band-edit-*.md`
     file.
  If either is present, the check emits a fail finding:
  "uncommitted backfill present (at `history/v(N+1)/` and/or
  `proposed_changes/out-of-band-edit-*.md`); commit the existing
  backfill and re-run." The check does NOT overwrite, collide, or
  pile up.
- Under the commit-after-successful-write workflow discipline,
  uncommitted backfill on disk is anomalous; refusing to proceed
  is correct.
- `static-check-semantics` deferred item (H13) covers the detailed
  cycle semantics (the exact glob used for the guard; behavior
  when only the proposed-change but not the history directory is
  present; etc.).

### H12. Skill-owned directory-README content (incompleteness → accepted, option A)

Resolution: freeze both paragraphs verbatim in PROPOSAL.md §
"SPECIFICATION directory structure." The content is committed in
PROPOSAL.md; `seed` hard-codes them in the skill bundle.

`SPECIFICATION/proposed_changes/README.md`:

> # Proposed Changes
>
> This directory holds in-flight proposed changes to the
> specification. Each file is named `<topic>.md` and contains one
> or more `## Proposal: <name>` sections with target specification
> files, summary, motivation, and proposed changes (prose or
> unified diff). Files are processed by `livespec revise` in
> creation-time order (YAML `created_at` front-matter field) and
> moved into `../history/vNNN/proposed_changes/` when revised.
> After a successful `revise`, this directory is empty.

`SPECIFICATION/history/README.md`:

> # History
>
> This directory holds versioned snapshots of the specification
> plus the proposed-changes and revisions that produced each
> version. `vNNN/` directories are zero-padded integer versions
> (`v001`, `v002`, ...); numbering is monotonic and contiguous
> except where `prune-history` has replaced older versions with
> `PRUNED_HISTORY.json`. Each `vNNN/` contains a frozen copy of
> every specification file at that version and a
> `proposed_changes/` subdirectory with the proposal(s) and
> revision(s) processed during the `revise` that cut the version.

### H13. bcp14 typo list (incompleteness → accepted, option A; rename deferred item)

Resolution:

- The `ast-check-semantics` deferred item is **renamed to
  `static-check-semantics`** with widened scope covering:
  - AST enforcement checks (v007 G6 scope, preserved).
  - Markdown-parsing checks (bcp14-keyword-wellformedness,
    gherkin-blank-line-format, anchor-reference-resolution).
  - Doctor static-check cycle semantics (out-of-band-edits
    pre-backfill guard details per H11; git-not-available
    skip behavior).
  - Argparse-`SystemExit` disposition under supervisor-discipline
    (per H3).
- The precise bcp14 misspelling list remains deferred under this
  widened entry.

### H14. Anchor-reference-resolution algorithm (ambiguity → accepted, option A)

Resolution: PROPOSAL.md § `anchor-reference-resolution` adds the
algorithm inline:

> Anchors are generated per GitHub-flavored Markdown (GFM) slug
> rules: the heading text is lowercased; internal whitespace is
> replaced with single hyphens; punctuation is stripped except
> `-` and `_`; multiple consecutive hyphens collapse to one.
> Headings inside fenced code blocks (`` ``` `` or `~~~`) are NOT
> considered headings. Explicit `{#custom-id}` syntax is NOT
> supported in v1.

Edge-case details remain deferred under `static-check-semantics`.

### H15. tests/fixtures/ CLAUDE.md carve-out (ambiguity → accepted, option A)

Resolution:

- Both PROPOSAL.md DoD #13 and style doc §"Agent-oriented
  documentation" add an explicit carve-out: `tests/fixtures/` and
  its entire subtree are excluded from `check-claude-md-coverage`.
- One optional `tests/fixtures/CLAUDE.md` at the fixtures root is
  permitted but not required.
- The `check-claude-md-coverage` description names the carve-out
  explicitly alongside `_vendor/`.

### H16. Auto-generated seed proposed-change content (incompleteness → accepted, option A)

Resolution: PROPOSAL.md § "seed" specifies the auto-capture
verbatim.

`history/v001/proposed_changes/seed.md` contents:

```yaml
---
topic: seed
author: livespec-seed
created_at: <UTC ISO-8601 seconds>
---
```

Then one `## Proposal: seed` with:

- `### Target specification files`: every path written at seed
  time, one per line (repo-root-relative).
- `### Summary`: verbatim string "Initial seed of the
  specification from user-provided intent."
- `### Motivation`: verbatim `<intent>`.
- `### Proposed Changes`: verbatim `<intent>`.

`history/v001/proposed_changes/seed-revision.md` retains the v007
shape: `decision: accept`, `reviser_llm: livespec-seed`, rationale
"auto-accepted during seed."

## Deferred-items inventory (carried forward + new)

Per the v007 deferred-items discipline, every carried-forward item
is enumerated below. Added, renamed, and newly-introduced items are
flagged.

**Carried forward unchanged from v007:**

- `template-prompt-authoring` (v001).
- `python-style-doc-into-constraints` (v005).
- `companion-docs-mapping` (v001).
- `enforcement-check-scripts` (v005).
- `claude-md-prose` (v006).
- `task-runner-and-ci-config` (v006).
- `returns-pyright-plugin-disposition` (v007).
- `front-matter-parser` (v007).

**Renamed + scope-widened in v008:**

- `ast-check-semantics` (v007) → `static-check-semantics` (v008).
  Scope widened to include markdown-parsing checks, the
  out-of-band-edits pre-backfill guard (H11), and the
  argparse-`SystemExit` disposition (H3). The bcp14 misspelling
  list (H13) and anchor-resolution edge cases (H14) now live
  under this item. The exemption list grows: `structlog.configure`,
  `structlog.contextvars.bind_contextvars`, AND the
  `fastjsonschema_facade.py` compile cache (H9).

**New in v008:**

- `skill-md-prose-authoring` (v008, H4) — per-sub-command SKILL.md
  body content per the canonical shape codified in PROPOSAL.md.
- `wrapper-input-schemas` (v008, H6, H10) — authoring of
  `seed_input.schema.json`, `revise_input.schema.json`,
  `proposal_findings.schema.json` (renamed from
  `critique_findings.schema.json`), and `doctor_findings.schema.json`.

**Removed:**

- None.

## Self-consistency check

Post-revision invariants rechecked:

- **Import resolution works.** `_bootstrap.py` now inserts both
  `scripts/` and `scripts/_vendor/`, so every documented import
  (`from returns.io import IOResult`, `from fastjsonschema import
  compile`, `import structlog`, `import jsoncomment`, `from
  livespec.commands.seed import main`) resolves cleanly.
- **Non-interactive execution preserved.** All I/O lives under
  `livespec/io/` including the new `io/cli.py` and the
  `fastjsonschema_facade.py` cache. `argparse` with
  `exit_on_error=False` never raises `SystemExit` inside
  `commands/`.
- **Supervisor discipline honored.** `sys.exit` / `raise SystemExit`
  only in `bin/*.py` (incl. `_bootstrap.py`). The
  `check-supervisor-discipline` scope is narrowed to `livespec/**`
  with `bin/*.py` as the sole exempt subtree.
- **Purity discipline honored.** `parse/` and `validate/` remain
  strictly pure. `fastjsonschema.compile` caching moves to the
  facade (impure by directory convention); `validate/<name>.py`
  signatures stay `(payload: dict, schema: dict) -> Result[T,
  ValidationError]` per v007 G4.
- **Static-check output contract preserved.** `doctor_findings.schema.json`
  is the new explicit schema for doctor static-phase JSON output;
  its shape is unchanged from v007 (just named explicitly).
  `proposal_findings.schema.json` is the separate schema for
  propose-change and critique inputs.
- **CLAUDE.md coverage scope cleanly stated.** `scripts/` (excluding
  `_vendor/`), `tests/` (excluding `fixtures/`), and `dev-tooling/`.
- **Deferred-items.md remains authoritative.** Every carried-forward
  entry enumerated; renames and new entries flagged; no entries
  removed.
- **Recreatability.** A competent implementer can generate the
  v008 livespec plugin + built-in template + sub-commands +
  enforcement suite + dev-tooling from v008 PROPOSAL.md +
  `livespec-nlspec-spec.md` + updated
  `python-skill-script-style-requirements.md` + `deferred-items.md`
  alone.
- **Cross-doc consistency.** PROPOSAL.md and Python style doc
  agree on: two-path `_bootstrap.py`, vendored libs including
  `jsoncomment`, SKILL.md body canonical shape,
  `--seed-json`/`--revise-json`/`--findings-json` wrapper inputs,
  `proposal_findings` schema rename, `doctor`'s `Bash + Read +
  Write` tools, context-dataclass field sets, PLR0913+PLR0917 at
  6, facade-layer compile cache, tests/fixtures/ CLAUDE.md
  carve-out, canonical seed auto-capture content.

## Outstanding follow-ups

Tracked in the updated `deferred-items.md` (see inventory above).

## What was rejected

Nothing was rejected outright. Two reshape patterns occurred during
the interview:

- **Assistant-recommendation-then-revised-by-user-pushback:**
  - H5's initial "drop max-args=6" recommendation (revised to
    both PLR0913+PLR0917 at 6 after user correctly identified
    refactor-to-dataclass as the load-bearing discipline).
  - H11's initial "HEAD-to-HEAD is non-destructive" framing
    (revised to add explicit pre-backfill guard after user
    correctly identified the rerun-before-commit edge case).

- **Library-selection-confirmed-at-category-then-specific:**
  - H2 answered category-level first (vendor, option B), then
    library-specific (jsoncomment). Kept the flow fast without
    forcing the user to choose 2-4 library candidates in one
    question.

No pattern of "premature convergence" or "over-engineering"
occurred this pass; the v007 decisions remained load-bearing and
v008 stayed in its lane (defect critique + grounded research).
