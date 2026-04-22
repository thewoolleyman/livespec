---
proposal: proposal-critique-v06.md
decision: modify
revised_at: 2026-04-22T00:00:00Z
reviser_human: thewoolleyman
reviser_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v06

## Provenance

- **Proposed change:** `proposal-critique-v06.md` (in this directory) — a
  recreatability-focused critique surfacing integration gaps the
  v005→v006 language migration left in PROPOSAL.md and
  `python-skill-script-style-requirements.md`.
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context).
- **Revised at:** 2026-04-22 (UTC).
- **Scope:** v006 PROPOSAL.md + `python-skill-script-style-requirements.md`
  → v007 PROPOSAL.md + updated style doc + new
  `deferred-items.md` companion. Per-sub-command skill restructuring,
  Python invocation orchestration, ROP integration, vendored-lib
  facades, deferred-items tracking mechanism.

## Pass framing

This pass was a **defect critique with grounded research**, distinct
from v006's language-migration pass. The 18 items (G1-G18) used the
NLSpec failure-mode framework (ambiguity / malformation /
incompleteness / incorrectness) and were grouped by impact: major
gaps (G1-G5; recreatability-blocking), significant gaps (G6-G12;
load-bearing guesses), smaller cleanup (G13-G18; wording fixes).

Mid-interview the user surfaced two issues that materially expanded
the pass:

1. **Deferred-items mechanism (around G6).** The user pushed back on
   "defer to first-batch propose-change" by asking what guarantees
   deferred items actually get tracked. Resolution: a new
   `deferred-items.md` companion doc in the brainstorming folder
   becomes the canonical list; future revisions MUST update it.
2. **Skill invocation UX (G13 expanded).** The user corrected an
   incorrect assistant claim about Claude Code skill invocation.
   Research via the claude-code-guide agent confirmed: plugin
   skills MUST be namespaced `/<plugin>:<skill>`; no nested
   subcommand syntax exists; per-sub-command skill structure is the
   recommended pattern for autocomplete UX. This restructured the
   skill bundle from a single skill with internal `commands/` to
   per-sub-command skills with shared scripts at plugin root.

The pass did NOT re-open any settled v005/v006 decision about WHAT
livespec does (sub-commands, template architecture, lifecycle,
history shape, proposed-change / revision file formats, mise-pinned
tooling, vendoring of returns/fastjsonschema/structlog, ruff +
pyright + pytest + coverage, ROP all-the-way-down, just/lefthook/CI,
CLAUDE.md coverage). It clarified, integrated, and resolved
contradictions.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| G1 | incompleteness | Resolved into G3 |
| G2 | incompleteness | Accepted with modification (option a) |
| G3 | malformation | Modified-on-accept (shared `bin/_bootstrap.py` extracts G1+G3) |
| G4 | malformation | Accepted as recommended |
| G5 | ambiguity | Modified-on-accept (option c — Python wrapper ROP chain owns pre+cmd+post static) |
| G6 | incompleteness | Accepted as recommended (defer); new mechanism for tracking |
| G7 | malformation | Accepted as recommended |
| G8 | ambiguity | Modified-on-accept (static registry; drop v005 invariant) |
| G9 | incompleteness | Accepted as recommended |
| G10 | incompleteness | Accepted as recommended |
| G11 | ambiguity | Accepted as recommended |
| G12 | incompleteness | Modified-on-accept (drop the check entirely; pinned versions + no-edit discipline) |
| G13 | ambiguity | Expanded mid-interview, then accepted (per-sub-command skills) |
| G14 | ambiguity | Accepted as recommended |
| G15 | ambiguity | Accepted as recommended |
| G16 | incompleteness | Accepted as recommended |
| G17 | ambiguity | Resolved by G13 (cascading) |
| G18 | ambiguity | Resolved by G3 (cascading) |

## Governing principles established or reinforced during this pass

Three cross-cutting principles emerged or were sharpened. They will
be saved as feedback memories.

### Prefer static enumeration over dynamic discovery

User on G8: *"static, and remove this guidance from the proposal:
'check insert/delete is a non-event'. We absolutely should hardcode
the dependencies of submodules of the static python code tree."*

Applied: `livespec/doctor/static/__init__.py` becomes a static
registry that imports every check module by name and re-exports
the `(SLUG, run)` mapping. Dropped the v005-era "insert/delete is
a non-event" invariant (which existed to avoid v004's stable-number
problem; with slug-keyed checks + a static type system, mechanical
enumeration is the better trade-off). Sets precedent for other
skill-bundled Python: prefer static enumeration when the type
system can verify completeness.

### Prefer per-sub-command skill structure for plugins

User confirmed on G13: *"1 is good. And it's also good because
then the skill frontmatter can be more targeted about when it
should be auto-invoked, and have granular permissions/tools."*

Applied: livespec ships one `.claude-plugin/skills/<sub-command>/
SKILL.md` per sub-command (instead of a single `livespec` skill
with internal `commands/`). Each skill's frontmatter:
- `description` is tightly scoped per sub-command (the LLM
  auto-invokes only on narrow intent matches).
- `allowed-tools` declares only the tools that sub-command needs
  (principle of least privilege per skill).
- `disable-model-invocation` is set on destructive sub-commands
  (e.g., `prune-history`) so they require explicit `/livespec:
  prune-history` invocation.

Shared resources (Python package, vendored libs, wrappers, schemas)
move to plugin root: `.claude-plugin/scripts/...`.

### Each brainstorming revision MUST enumerate carried-forward deferred items

User pushed back on informal prose-only tracking of deferred items.
Resolution: a `brainstorming/approach-2-nlspec-based/
deferred-items.md` companion doc is the canonical list. Each
revision pass MUST enumerate every deferred item carried forward
from the previous version, plus any new ones; if any are removed,
the revision MUST explain why. The mechanism applies to the
brainstorming process; livespec's runtime is unaffected.

## Disposition by item

### G1. Python import-path bootstrap (incompleteness → resolved into G3)

`python3 bin/seed.py` puts `bin/` on sys.path[0], not `scripts/`,
so `from livespec.commands.seed import main` fails. Original
recommendation was a `sys.path` insert in each wrapper. The user
correctly objected this duplicates the same code across 6 wrappers.
Resolved by extracting bootstrap into a shared module — see G3.

### G2. YAML front-matter parser (incompleteness → accepted-with-restriction)

The three vendored libs don't parse YAML; the proposal forbids any
other runtime dep. Decision: hand-roll a restricted-YAML parser at
`livespec/parse/front_matter.py` (~50 LLOC). PROPOSAL.md codifies
the format restriction so the parser stays narrow forever:

- Front-matter values MUST be JSON-compatible scalars (strings,
  ints, booleans, null).
- No lists, no nested dicts, no anchors, no flow style.
- Unknown keys are a parse error.
- Keys MUST be the documented set per file type.

The parsed dict is then validated against `front_matter.schema.json`
via `fastjsonschema` (factory-shape per G4).

### G3. `__init__.py` version check vs check-no-raise-outside-io (malformation → modified-on-accept)

`livespec/__init__.py` raising `ToolMissingError` violates
`check-no-raise-outside-io`; `sys.exit` violates
`check-supervisor-discipline`; every exit mechanism is forbidden.

Resolution: extract a shared `bin/_bootstrap.py` module that:

- Lives under `bin/` (so `raise SystemExit(127)` is allowed by
  `check-supervisor-discipline`).
- Owns sys.path setup (subsumes G1).
- Owns the Python-version check.
- Is automatically importable from each wrapper (Python adds
  the script's directory to sys.path[0]).

Wrapper shape becomes a deterministic 6-line template (resolves
G18):

```python
#!/usr/bin/env python3
"""Shebang wrapper for <description>. No logic; see livespec.<module> for implementation."""
from _bootstrap import bootstrap
bootstrap()
from livespec.<module>.<submodule> import main

raise SystemExit(main())
```

`check-wrapper-shape` updated to match. `__init__.py` does no
version check.

### G4. Pure validators load schemas from disk (malformation → accepted)

`validate/` is pure (no filesystem I/O), but the doc previously
said validators load schemas from disk. Decision: factory shape.

- `validate/<name>.py` exposes `validate_<name>(payload: dict,
  schema: dict) -> Result[T, ValidationError]`.
- Callers in `commands/` or `doctor/` read schemas via `io/`
  wrappers, then pass the parsed dict to the validator.
- `fastjsonschema.compile(...)` is cached via `functools.lru_cache`
  keyed on the schema's `$id` field.
- `validate/` stays strictly pure; tests can hand a schema dict to
  validators without touching the filesystem.

### G5. Pre/post-step doctor orchestration (ambiguity → modified-on-accept)

PROPOSAL.md mandated pre-step doctor static and post-step doctor
(static + LLM-driven), but never said who runs them. Initial
recommendation was "LLM owns all three steps." User correctly
pushed back: option C (Python wrapper's ROP chain composes
pre-static + sub-command + post-static) is cleaner because the
post-step LLM-driven phase doesn't run *from inside* the wrapper —
it runs *after* the wrapper exits, driven by skill prose.

Resolution:

- `bin/<cmd>.py` (for seed, propose-change, critique, revise,
  prune-history) composes one ROP chain: `run_static` →
  sub-command logic → `run_static`. Failures short-circuit; non-
  zero exit aborts.
- `--skip-pre-check` is a wrapper-parsed flag (passed by the LLM
  in dialogue) that elides the first `run_static` from the chain;
  same for `pre_step_skip_static_checks` config.
- `bin/doctor_static.py` stays standalone (it IS the static phase;
  no pre/post wrap).
- For `livespec doctor` invocation: skill prose invokes
  `bin/doctor_static.py`, then runs the LLM-driven phase from
  `commands/doctor.md` prose.
- For seed/propose-change/critique/revise: skill prose says
  "invoke `bin/<cmd>.py`; if exit 0, run the LLM-driven phase per
  `commands/doctor.md`" (honoring `--skip-subjective-checks` /
  `post_step_skip_subjective_checks`, both LLM-layer flags).
- `prune-history` has no LLM-driven post-step.

PROPOSAL.md adds a new "Sub-command lifecycle orchestration"
section codifying this.

### G6. AST check semantics (incompleteness → defer + new tracking mechanism)

The named AST checks (`check-purity`, `check-private-calls`, etc.)
have undefined edge-case semantics (`pathlib` ban scope; deferred
imports; `__all__` re-exports; `assert` statements; etc.).

Decision: defer the precise AST semantics, scope globs, and
edge-case dispositions to a first-batch post-seed propose-change.
v007 PROPOSAL.md and the style doc keep names and one-sentence
purposes only.

The user surfaced the meta-question "how do we ensure these
deferred items aren't forgotten?" Answer: see the new
`deferred-items.md` companion doc described in the governing
principles. Item id: `ast-check-semantics`. Target spec file:
`SPECIFICATION/constraints.md`. How-to-resolve: per-check AST
node types, scope globs, edge-case dispositions.

### G7. CLAUDE.md coverage rule disagreement (malformation → accepted)

Five sources disagreed on the scope. Canonical resolution:
**every directory under `<bundle>/scripts/` (with `_vendor/` and
its entire subtree explicitly excluded), every directory under
`<repo-root>/tests/`, and every directory under
`<repo-root>/dev-tooling/`.** Updates propagate to:

- PROPOSAL.md "Skill layout" (now reads "every directory under
  `scripts/` except `_vendor/`").
- PROPOSAL.md "Developer tooling layout" (clarified scope).
- PROPOSAL.md DoD #13 (already correct).
- Style doc § "Agent-oriented documentation" (adds dev-tooling/;
  excludes _vendor/).
- Style doc § "Enforcement suite" `check-claude-md-coverage`
  description (matches).

### G8. Orchestrator discovery and typing (ambiguity → modified-on-accept; v005 invariant dropped)

User: *"static, and remove this guidance from the proposal: 'check
insert/delete is a non-event'. We absolutely should hardcode the
dependencies of submodules of the static python code tree."*

Resolution: `livespec/doctor/static/__init__.py` is a static
registry that imports every check module by name and re-exports
`(SLUG, run)` tuples. Adding/removing a check is one explicit
edit to the registry. The "insert/delete is a non-event" invariant
is dropped from PROPOSAL.md (lines 866-868 in v006). Pyright
strict happily type-checks the static imports; the orchestrator's
`Fold.collect` has fully-typed inputs.

The slug↔module-name mapping is no longer derived dynamically
(no hyphen-to-underscore conversion loop) — it lives literally in
the registry's import statements.

### G9. Supervisor exit-code derivation (incompleteness → accepted)

Codified in PROPOSAL.md § "Static-phase exit codes":

> The supervisor derives the exit code as follows:
> - On `IOFailure(err)`: exit `err.exit_code` (typically `1`).
> - On `IOSuccess(report)`: emit `{"findings": [...]}` to stdout,
>   then exit `3` if any finding has `status: "fail"`, else exit
>   `0`. `status: "skipped"` does not trigger a fail exit.

Same in style doc's exit-code-contract section.

### G10. Pyright strict with vendored libs (incompleteness → accepted)

Resolution: vendored libs are touched only via thin typed facades
under `livespec/io/<lib>_facade.py`. The facade is the only place
`Any` and `# type: ignore` for vendored types are permitted.
`pyrightconfig.json` (via `[tool.pyright]` in `pyproject.toml`)
excludes `_vendor/**` from strict mode but enables
`useLibraryCodeForTypes = true`.

Special note for `dry-python/returns`: its types (`Result`,
`IOResult`) are used pervasively, not just at boundaries, so the
"facade" pattern doesn't apply uniformly. The style doc clarifies:
either vendor the returns pyright plugin and document its
configuration, or rely on returns' own types if sufficient for our
usage. Determination is deferred to first-batch (item id:
`returns-pyright-plugin-disposition`).

### G11. Propose-change orchestration (ambiguity → accepted)

Rewrite `### propose-change <topic> <intent>` to make explicit:

> `bin/propose_change.py` only accepts `--findings-json <path>`;
> it never invokes the template prompt or the LLM. The freeform
> `<intent>` path is driven by the LLM per
> `commands/propose-change.md`: LLM invokes the active template's
> `prompts/propose-change.md`, captures output, validates it via
> `livespec.validate.findings.validate`, writes the validated
> JSON to a temp file, then invokes `bin/propose_change.py
> --findings-json <tempfile> <topic>`.

Same pattern applied to `### critique <author>`. This consequence
follows directly from G5's resolution (Python doesn't invoke the
LLM; LLM-driven work lives in skill prose).

### G12. Vendor audit detail (incompleteness → drop the check entirely)

User: *"Why do we even care about the vendoring check? Just have
the specification dictate exactly what version should be vendored
and leave it at that."*

Decision: `check-vendor-audit` removed entirely. Replacement
discipline:

- PROPOSAL.md and style doc specify the exact pinned version of
  each vendored lib (returns: TBD; fastjsonschema: TBD; structlog:
  TBD — pinned by the implementer at vendor time).
- Style doc documents the no-edit rule: `_vendor/` files are
  never edited directly; re-vendoring goes through `just
  vendor-update <lib>`.
- A simple `.vendor.toml` (or per-lib `VERSION` file) records the
  pinned upstream ref so re-vendoring is reproducible. Schema is
  trivial: `{upstream_url, upstream_ref, vendored_at}`. No hash,
  no audit script.
- Code review and git diff visibility catch accidental edits;
  `just vendor-update` is the only blessed mutation path.

Removes one enforcement target, one dev-tooling check script
(`vendor_audit.py`), and an entire spec sub-section's worth of
audit-mechanism ambiguity.

### G13. Skill invocation UX (ambiguity → restructured)

The assistant initially gave incorrect guidance about Claude Code
skill invocation. User correction + agent research established:

- Plugin skills MUST be namespaced `/<plugin-name>:<skill-name>`
  for slash-command invocation.
- No nested subcommand syntax exists in Claude Code.
- The recommended pattern for sub-command autocomplete is multiple
  skills (one per sub-command) within the plugin.

Resolution: restructure from "single `livespec` skill with
internal `commands/`" to "per-sub-command skills":

```
.claude-plugin/
├── plugin.json
├── skills/
│   ├── seed/SKILL.md           # /livespec:seed
│   ├── propose-change/SKILL.md # /livespec:propose-change
│   ├── critique/SKILL.md       # /livespec:critique
│   ├── revise/SKILL.md         # /livespec:revise
│   ├── doctor/SKILL.md         # /livespec:doctor
│   ├── prune-history/SKILL.md  # /livespec:prune-history
│   └── help/SKILL.md           # /livespec:help
└── scripts/                    # shared across all skills (plugin root)
    ├── bin/                    # shebang-wrapper executables (G3 shape)
    │   ├── _bootstrap.py
    │   ├── seed.py
    │   ├── propose_change.py
    │   ├── critique.py
    │   ├── revise.py
    │   ├── doctor_static.py
    │   └── prune_history.py
    ├── _vendor/
    │   ├── returns/
    │   ├── fastjsonschema/
    │   └── structlog/
    └── livespec/               # the Python package
        ├── __init__.py
        ├── commands/
        ├── doctor/
        │   ├── run_static.py
        │   ├── finding.py
        │   └── static/
        │       ├── __init__.py     # static registry (G8)
        │       └── <check>.py
        ├── io/                  # impure wrappers + vendored-lib facades (G10)
        ├── parse/
        │   └── front_matter.py  # restricted YAML parser (G2)
        ├── validate/            # factory-shape validators (G4)
        ├── schemas/
        ├── context.py
        └── errors.py
```

Each `<sub-command>/SKILL.md`'s frontmatter:

- `description` is tightly scoped per sub-command.
- `allowed-tools` declares only what's needed:
  - `help`: read-only.
  - `doctor`: Bash + Read.
  - `seed` / `propose-change` / `critique` / `revise` /
    `prune-history`: Bash + Read + Write.
- `disable-model-invocation: true` on `prune-history` (destructive
  — explicit invocation only).

The v006 `commands/<cmd>.md` files become these `SKILL.md` files
(content-equivalent, just renamed/relocated and with frontmatter
added).

This dissolves G17 entirely (skill-side `commands/` directory
no longer exists; only the Python `livespec.commands` namespace
remains).

User invocation patterns documented in PROPOSAL.md:

- Slash command: `/livespec:doctor`, `/livespec:seed`, etc. —
  user-typed, autocompleted in Claude Code's slash menu.
- Dialogue-mediated: user says "run livespec doctor" or
  equivalent; LLM auto-activates the matching skill via its
  tightly-scoped description.
- `disable-model-invocation` skills require explicit slash invocation.

### G14. Structlog bootstrap location (ambiguity → accepted)

`scripts/livespec/__init__.py` calls `structlog.configure(...)`
exactly once, then binds `run_id` (UUID) via
`structlog.contextvars.bind_contextvars(run_id=str(uuid.uuid4()))`
in the same block. Documented exemption (filed against the
deferred AST-semantics work): `structlog.configure` and
`structlog.contextvars.bind_contextvars` calls in `__init__.py`
are not livespec module-level state writes and do not violate
`check-global-writes`.

### G15. `just check` failure aggregation (ambiguity → accepted)

`just check` runs every target sequentially, continues on failure,
exits non-zero if any target failed, listing which failed at the
end. Matches CI's `fail-fast: false`; one local run reproduces
full CI feedback.

### G16. lefthook install bootstrap (incompleteness → accepted)

Add `just bootstrap` to the canonical target list. After `mise
install`, developer runs `just bootstrap` which executes
`lefthook install` and any other one-time setup.

### G17. commands/ namespace overload (ambiguity → resolved by G13)

Skill-side `commands/` directory eliminated by G13's restructure.
Python `livespec.commands.<cmd>` namespace is the only remaining
`commands/` and is unambiguous.

### G18. Wrapper shape line count (ambiguity → resolved by G3)

The 6-line deterministic wrapper template (G3) replaces the
"≤ 5 lines" rule. `check-wrapper-shape` AST check verifies the
exact 6-line shape (shebang, docstring, `from _bootstrap import
bootstrap`, `bootstrap()`, `from livespec... import main`, `raise
SystemExit(main())`). No other lines, no other statements.

## Self-consistency check

Post-revision invariants rechecked:

- **Per-sub-command skill structure compatible with Claude Code
  plugin format.** Per the agent's research:
  https://code.claude.com/docs/en/skills.md and
  https://code.claude.com/docs/en/plugins.md confirm the namespaced
  invocation pattern and per-skill frontmatter scoping.
- **ROP all-the-way-down preserved.** The wrapper's ROP chain
  composes pre-static + sub-command + post-static; failures
  short-circuit cleanly; the LLM-driven phase remains strictly
  outside Python.
- **Static-phase contract preserved.** JSON `check_id` values
  (`doctor-<slug>`) remain hyphenated per wire contract; module
  filenames are snake_case per Python convention; static registry
  imports them by name.
- **Coverage scope: scripts/livespec/** + dev-tooling/** **
  unchanged from v006. _vendor/** still excluded.
- **Vendoring discipline strengthened.** Pinned versions in
  PROPOSAL.md + no-edit rule + `just vendor-update` as the only
  blessed mutation path. Hash-check audit removed (over-engineered
  for the threat model).
- **Recreatability.** A competent implementer can generate the
  v007 livespec plugin + built-in template + sub-commands +
  enforcement suite + dev-tooling from v007 PROPOSAL.md +
  `livespec-nlspec-spec.md` + updated
  `python-skill-script-style-requirements.md` alone, modulo the
  items explicitly listed in `deferred-items.md`.
- **Cross-doc consistency.** PROPOSAL.md and Python style doc agree
  on: per-sub-command skill structure, shared scripts at plugin
  root, 6-line wrapper shape, ROP integration, factory-shape
  validators, static check registry, exit-code derivation,
  CLAUDE.md scope, vendoring discipline.

## Outstanding follow-ups

Tracked in the new `deferred-items.md` companion doc. Initial
content (carried forward from v006's `Self-application` "Known
such items" plus new items surfaced this pass):

- Authoring of each template prompt's input/output JSON schemas
  and the prompts themselves.
- Migrating `python-skill-script-style-requirements.md` into
  `SPECIFICATION/constraints.md` at seed time.
- Detailed mapping of brainstorming-folder companion documents
  (`subdomains-and-unsolved-routing.md`, `prior-art.md`, etc.) to
  their destinations in the seeded spec.
- Authoring of each enforcement-check script under
  `dev-tooling/checks/` per the canonical target list.
- Authoring of the per-directory `CLAUDE.md` files under
  `scripts/`, `tests/`, and `dev-tooling/`.
- Authoring of the justfile, lefthook.yml, and
  `.github/workflows/ci.yml` per the patterns in
  `python-skill-script-style-requirements.md`.
- **NEW (G6):** Authoring of each AST enforcement check's precise
  AST node types, scope globs, and edge-case dispositions.
  (`ast-check-semantics`)
- **NEW (G10):** Determination of whether the dry-python/returns
  pyright plugin is vendored alongside the lib, or whether
  returns' own types are sufficient for livespec's usage.
  (`returns-pyright-plugin-disposition`)
- **NEW (G2 follow-on):** Authoring of `front_matter.schema.json`
  and the restricted YAML parser at `livespec/parse/front_matter.py`.
  (`front-matter-parser`)

## What was rejected

Nothing was rejected outright. Five reshape patterns occurred during
the interview:

- **Initially-recommended-then-revised by user pushback:** G1's
  per-wrapper duplication (revised into G3's shared bootstrap);
  G5's "LLM owns all four steps" (revised to "Python wrapper's
  ROP chain owns deterministic lifecycle"); G8's
  Protocol+@impure_safe discovery (revised to static registry
  with v005-invariant drop); G12's full vendor audit (dropped
  entirely); G13's skill-only invocation (expanded to
  per-sub-command skills with autocomplete UX).
- **Assistant-was-wrong-and-user-corrected:** G13 specifically —
  initial assistant claim about Claude Code skill invocation was
  factually wrong; user corrected; assistant researched via the
  claude-code-guide agent before proceeding.
- **Drift-into-out-of-scope:** G6's deferred-items mechanism
  question was initially answered as if it were a livespec
  runtime feature; user redirected to the actual scope (the
  brainstorming-to-implementation transfer process).
- **Aggressive-defer-then-track:** G6 (AST-check semantics) and
  G10 (returns plugin) and G2 (front-matter parser) all defer
  implementation work to first-batch propose-changes, but every
  deferral now lands in the new `deferred-items.md` so nothing
  slips silently.
- **Over-engineering-rolled-back:** G12's vendor-audit machinery
  shrank from "schema + diff + audit script" to "specify the
  version, don't edit, re-vendor deliberately."
