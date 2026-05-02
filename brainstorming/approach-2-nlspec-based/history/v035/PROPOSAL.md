# `livespec` Proposal

> **Status:** Frozen at v024. Further evolution happens in
> `SPECIFICATION/` via `propose-change` / `revise`. This file
> and the rest of the `brainstorming/` tree are historical
> reference only.

`livespec` is a Claude Code plugin that delivers a per-sub-command
family of skills for governing a living `SPECIFICATION`: seeding it,
proposing changes, critiquing, revising, validating, pruning history,
and versioning. It standardizes lifecycle and governance; it leaves
on-disk shape to a template.

This proposal uses BCP 14 / RFC 2119 / RFC 8174 keywords (`MUST`,
`MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`,
`OPTIONAL`) for normative requirements.

---

## Runtime and packaging

### Plugin delivery

- `livespec` MUST be delivered as a **Claude Code plugin** named
  `livespec`. The plugin root is `.claude-plugin/`.
- `.claude-plugin/plugin.json` MUST be present and fully populated
  per the Claude Code plugin format current at implementation time.
  `livespec` itself does not validate `plugin.json`; the implementer
  tracks the current Claude Code plugin-format documentation.
  Publishing to a Claude Code plugin marketplace is a v2 non-goal.
- The plugin ships **one skill per sub-command** under
  `.claude-plugin/skills/<sub-command>/SKILL.md` (see "Skill
  layout" below). Plugin skills MUST be invoked via the namespaced
  syntax `/livespec:<sub-command>` (Claude Code plugins do not
  support nested subcommand syntax; e.g., `/livespec doctor` is not
  a valid invocation).
- During dogfooded development in the livespec repo,
  `.claude/skills/` is a relative symlink pointing at
  `../.claude-plugin/skills/` (i.e., `ln -s ../.claude-plugin/skills
  .claude/skills`). The `.claude-plugin/skills/` directory is the
  canonical plugin-delivery location; Claude Code reads the skills
  via the symlink, avoiding a plugin-install step during
  development. **The symlink is committed to git as a tracked
  symbolic link** (no `.gitignore` entry for `.claude/skills/`);
  fresh clones pick it up immediately on Linux and macOS (both in
  v1 scope). `just bootstrap` re-creates the symlink defensively
  if a developer accidentally removes it; it is not required
  before Claude Code can load the skills on a fresh clone.
- Future v2 extension: parallel plugin packaging for the `opencode`
  and `pi-mono` agent runtimes. This proposal does not specify that
  packaging.

### User invocation

- **Slash invocation:** the user types `/livespec:<sub-command>`
  (e.g., `/livespec:doctor`, `/livespec:seed`). Each sub-command
  appears as its own autocomplete entry in Claude Code's slash menu
  because each is a separate skill.
- **Dialogue-mediated invocation:** the user states intent in
  natural language (e.g., "run livespec doctor on this spec");
  Claude auto-activates the matching skill via that skill's
  tightly-scoped `description` frontmatter field.
- **Explicit-only invocation:** sub-commands marked
  `disable-model-invocation: true` in their SKILL.md frontmatter
  (e.g., `prune-history`, which is destructive) MUST be invoked via
  slash command; Claude MUST NOT auto-activate them from dialogue
  context.
- **Allowed-tools per skill:** each SKILL.md declares its
  `allowed-tools` frontmatter following principle of least
  privilege. See "Per-sub-command skill frontmatter" below.

### Skill layout inside the plugin

The plugin MUST be organized as one skill per sub-command, with
shared scripts at the plugin root:

```
.claude-plugin/
├── plugin.json
├── skills/                              # one directory per sub-command
│   ├── seed/SKILL.md                    # /livespec:seed
│   ├── propose-change/SKILL.md          # /livespec:propose-change
│   ├── critique/SKILL.md                # /livespec:critique
│   ├── revise/SKILL.md                  # /livespec:revise
│   ├── doctor/SKILL.md                  # /livespec:doctor
│   ├── prune-history/SKILL.md           # /livespec:prune-history
│   └── help/SKILL.md                    # /livespec:help
├── scripts/                             # shared across all skills
│   ├── bin/                             # Python shebang-wrapper executables
│   │   ├── _bootstrap.py                # shared: sys.path setup + Python version check
│   │   ├── seed.py
│   │   ├── propose_change.py
│   │   ├── critique.py
│   │   ├── revise.py
│   │   ├── doctor_static.py             # static-phase only (LLM-driven phase is skill-layer)
│   │   ├── resolve_template.py          # resolves active template path; echoes to stdout (see J3 / §"Per-sub-command SKILL.md body structure")
│   │   └── prune_history.py
│   ├── _vendor/                         # vendored pure-Python third-party libraries
│   │   ├── returns/                     # dry-python/returns (BSD-3-Clause) — ROP primitives
│   │   ├── fastjsonschema/              # (MIT) — JSON Schema Draft-7 validator
│   │   ├── structlog/                   # (BSD-2 / MIT dual) — structured JSON logging
│   │   ├── jsoncomment/                 # (MIT, derivative) — JSONC parser shim per v013 M1 pattern (v026 D1)
│   │   └── typing_extensions/           # (PSF-2.0) — Python typing backports (vendored upstream per v027 D1; was a hand-authored shim per v013 M1 pre-v027)
│   └── livespec/                        # the Python package
│       ├── __init__.py                  # configures structlog + binds run_id (no version check)
│       ├── commands/                    # one module per sub-command with a Python wrapper; run() + main(). (doctor has no wrapper — see §"Note on `bin/doctor.py`"; its entry lives at doctor/run_static.py.)
│       │   ├── seed.py
│       │   ├── propose_change.py
│       │   ├── critique.py
│       │   ├── revise.py
│       │   ├── resolve_template.py      # resolves active template path (J3)
│       │   └── prune_history.py
│       ├── doctor/
│       │   ├── run_static.py            # static-phase orchestrator (single ROP chain)
│       │   └── static/
│       │       ├── __init__.py          # static registry: imports each check by name, exports (SLUG, run) tuples
│       │       ├── livespec_jsonc_valid.py
│       │       ├── template_exists.py
│       │       ├── template_files_present.py
│       │       ├── proposed_changes_and_history_dirs.py
│       │       ├── version_directories_complete.py
│       │       ├── version_contiguity.py
│       │       ├── revision_to_proposed_change_pairing.py
│       │       ├── proposed_change_topic_format.py
│       │       ├── out_of_band_edits.py
│       │       ├── bcp14_keyword_wellformedness.py
│       │       ├── gherkin_blank_line_format.py
│       │       └── anchor_reference_resolution.py
│       ├── io/                          # impure boundary wrappers + vendored-lib facades
│       │   ├── fs.py                    # filesystem operations (@impure_safe)
│       │   ├── git.py                   # git read-only operations (@impure_safe)
│       │   ├── cli.py                   # argparse wrappers (@impure_safe, exit_on_error=False)
│       │   ├── returns_facade.py        # (typed re-exports of returns primitives, if needed)
│       │   ├── fastjsonschema_facade.py # typed wrapper + compile-cache (Any confined here)
│       │   └── structlog_facade.py      # typed wrapper over structlog (Any confined here)
│       ├── parse/                       # pure parsers (Result-returning)
│       │   ├── jsonc.py                 # thin wrapper over vendored jsoncomment
│       │   └── front_matter.py          # restricted-YAML parser (deferred; see deferred-items.md)
│       ├── validate/                    # pure validators (Result-returning, factory shape); 1:1 paired with schemas/ (v013 M6; v014 N2 adds finding.py)
│       │   ├── doctor_findings.py
│       │   ├── proposal_findings.py
│       │   ├── seed_input.py
│       │   ├── revise_input.py
│       │   ├── livespec_config.py
│       │   ├── template_config.py              # v011 K5
│       │   ├── finding.py                      # v014 N2: paired with finding.schema.json + schemas/dataclasses/finding.py
│       │   ├── proposed_change_front_matter.py # deferred: front-matter-parser
│       │   └── revision_front_matter.py        # deferred: front-matter-parser
│       ├── schemas/                     # JSON Schema Draft-7 files + paired dataclasses
│       │   ├── dataclasses/                       # paired hand-authored dataclasses (see I3)
│       │   │   ├── livespec_config.py
│       │   │   ├── seed_input.py
│       │   │   ├── revise_input.py
│       │   │   ├── proposal_findings.py
│       │   │   ├── doctor_findings.py
│       │   │   ├── finding.py                     # Finding + pass_finding/fail_finding constructors (moved from doctor/ per J11)
│       │   │   ├── template_config.py             # v011 K5
│       │   │   ├── proposed_change_front_matter.py
│       │   │   └── revision_front_matter.py
│       │   ├── doctor_findings.schema.json       # doctor static-phase output contract
│       │   ├── proposal_findings.schema.json     # propose-change / critique template output
│       │   ├── seed_input.schema.json            # seed wrapper input (deferred; see deferred-items.md)
│       │   ├── revise_input.schema.json          # revise wrapper input (deferred; see deferred-items.md)
│       │   ├── livespec_config.schema.json
│       │   ├── template_config.schema.json               # v011 K5: validates template.json (doctor extensibility fields)
│       │   ├── finding.schema.json                       # v014 N2: REQUIRED standalone schema (implementer-choice closed)
│       │   ├── proposed_change_front_matter.schema.json  # (deferred; see deferred-items.md)
│       │   └── revision_front_matter.schema.json         # (deferred; see deferred-items.md)
│       ├── context.py                   # immutable context dataclasses (railway payload)
│       ├── types.py                     # canonical NewType aliases for domain primitives (v012 L8)
│       └── errors.py                    # LivespecError hierarchy (expected-failure classes only; per-subclass exit_code)
└── specification-templates/             # built-in templates (see "Templates" below)
    ├── livespec/                        # default built-in: multi-file SPECIFICATION/ layout
    │   ├── template.json
    │   ├── livespec-nlspec-spec.md
    │   ├── prompts/
    │   │   ├── seed.md
    │   │   ├── propose-change.md
    │   │   ├── revise.md
    │   │   └── critique.md
    │   └── specification-template/
    │       └── SPECIFICATION/
    │           ├── README.md
    │           ├── spec.md
    │           ├── contracts.md
    │           ├── constraints.md
    │           └── scenarios.md
    └── minimal/                         # v014 N1: single-file SPECIFICATION.md at repo root (spec_root: "./")
        ├── template.json                # template_format_version: 1; spec_root: "./"
        ├── prompts/                     # prompts include delimiter comments for the v014 N9 mock harness
        │   ├── seed.md
        │   ├── propose-change.md
        │   ├── revise.md
        │   └── critique.md
        └── specification-template/
            └── SPECIFICATION.md
```

#### Per-sub-command skill frontmatter

Each `<sub-command>/SKILL.md` MUST carry frontmatter with at least:

- `name`: the sub-command name (e.g., `seed`).
- `description`: a tightly-scoped one-line description of when this
  sub-command applies. The description gates auto-invocation.
- `allowed-tools`: the minimal tool set the sub-command needs.
  Suggested defaults:
  - `help`: read-only (no Bash, no Write).
  - `doctor`: Bash + Read + Write. The static phase MAY write to
    `<spec-root>/proposed_changes/` and `<spec-root>/history/`
    under the narrow auto-backfill path of the `out-of-band-edits`
    check (see §"Static-phase checks"). Outside that path, doctor
    does not write to disk.
  - `seed`, `propose-change`, `critique`, `revise`, `prune-history`:
    Bash + Read + Write.
- `disable-model-invocation: true` on `prune-history` (destructive
  pruning MUST require explicit user invocation).

#### Per-sub-command SKILL.md body structure

Each `<sub-command>/SKILL.md` MUST carry a prose body following the
canonical shape below. The body drives every LLM-mediated behavior
that happens before, during, or after wrapper invocation; it is the
authoritative location for instructions the LLM needs in order to
operate the sub-command correctly.

Canonical body sections (in order):

1. **Opening statement.** One or two sentences restating when this
   sub-command applies. Mirrors the frontmatter `description` at
   greater length.
2. **When to invoke.** User-facing trigger phrases (slash command,
   natural-language intents the LLM should recognize). Lists the
   disable-model-invocation boundary for destructive sub-commands.
3. **Inputs.** CLI flags the sub-command accepts and what each
   means. Where the wrapper takes a JSON tempfile flag
   (`--findings-json`, `--seed-json`, `--revise-json`), the schema
   under `.claude-plugin/scripts/livespec/schemas/` is named. The wrapper
   validates the payload internally; the SKILL.md prose does NOT
   invoke a separate validator.
4. **Steps.** An ordered list of LLM-driven steps. Each step is
   one of:
   - Invoke `bin/<cmd>.py` via the Bash tool, with explicit argv.
   - **Resolve + invoke a template prompt.** Two-step dispatch:
     (a) invoke `bin/resolve_template.py` via Bash and capture
     the active template's path from stdout (in the normal
     post-seed flow, the wrapper reads `.livespec.jsonc`'s
     `template` field and resolves built-in names or user-
     provided paths uniformly; in the pre-seed flow used only
     by `seed/SKILL.md`, the wrapper is invoked with
     `--template <chosen>` to bypass the config lookup per
     v017 Q2); (b) use the Read tool to read
     `<resolved-path>/prompts/<name>.md` and use its contents
     as the template prompt. This replaces the literal
     `@`-reference approach from v009 (which only worked for
     the built-in `livespec` template); the two-step dispatch
     works uniformly for built-in and custom templates. See
     J3 in `history/v010/proposed_changes/proposal-critique-v09-revision.md`
     and v017 Q2 for the pre-seed `--template` flag extension.
   - Write LLM-produced JSON to a temp file in preparation for
     a wrapper invocation.
   - Prompt the user for confirmation (only for `revise`'s
     per-proposal dialogue; the frontmatter's
     `disable-model-invocation` and `allowed-tools` settings gate
     tooling access).
   - Narrate a warning (e.g., when pre-step checks are skipped).
   - **Retry-on-exit-4:** on wrapper exit code `4` (schema
     validation failed; LLM-provided JSON payload did not conform
     to the wrapper's input schema), the skill SHOULD treat the
     return code as a retryable malformed-payload signal, re-
     invoke the relevant template prompt with the structured error
     context from stderr, and re-assemble the JSON payload. The
     exact retry count is intentionally unspecified in v1; prompt /
     skill orchestration owns the retry policy. Exit code `3`
     (precondition/doctor-static failure) is NOT retryable — it
     surfaces the findings to the user and aborts.
5. **Post-wrapper.** What the LLM does after the wrapper exits
   code 0. For sub-commands that have a post-step LLM-driven phase
   (seed, propose-change, critique, revise), references
   `doctor/SKILL.md`. For sub-commands that do not (prune-history,
   help), states "no post-step LLM-driven phase."
6. **Failure handling.** Exit-code-to-narration mapping for the
   wrapper:
   - Exit `0` → proceed to the post-wrapper step. This also
     covers intentional `--help` output (user asked for help,
     not an error).
   - Exit `1` → internal bug; surface the error (including
     traceback if structlog emitted one) and abort.
   - Exit `2` → usage error; restate the expected invocation and
     abort.
   - Exit `3` → precondition / doctor-static failure; surface the
     findings from the wrapper's stderr structlog line(s) and
     abort. The user is directed to the corrective action the
     finding describes. NOT retryable via template re-prompt.
   - Exit `4` → schema-validation failure on LLM-provided JSON
     payload; **retryable**. The skill SHOULD inspect the return
     code, re-invoke the template prompt with the error context
     from stderr, and re-assemble corrected JSON. Exact retry
     count is intentionally unspecified in v1 (see step 4
     "Retry-on-exit-4" above).
   - Exit `127` → too-old Python or missing tool; surface the
     install instruction and abort.

Concrete per-sub-command SKILL.md bodies are deferred to
`deferred-items.md`'s `skill-md-prose-authoring` entry.

#### Sub-command dispatch and invocation chain

- Each sub-command's SKILL.md prose names the relevant
  `.claude-plugin/scripts/bin/<cmd>.py` wrapper by path; the LLM invokes it
  directly via the bash tool. No top-level dispatcher script.
- The wrapper is a thin shebang pass-through to
  `livespec.commands.<cmd>.main()` via the shared
  `bin/_bootstrap.py` module.
- **Command files use `@`-reference syntax** to force deterministic
  reading of critical files (e.g., `@../../scripts/livespec/...`).
- **Deterministic logic MUST be implemented in Python** under
  `.claude-plugin/scripts/livespec/**`. LLM-driven behavior MUST NOT replace Python
  where a deterministic check is possible.
- **Python MUST NOT invoke the LLM.** LLM-driven work (template
  prompt invocation, LLM-driven doctor phase, interactive
  per-proposal confirmation) lives in skill prose; Python wrappers
  only handle deterministic work.
- **CLI argument parsing MUST happen in `livespec/io/cli.py`**, not
  in `livespec/commands/<cmd>/main()`. `argparse.ArgumentParser.parse_args`
  raises `SystemExit` on usage errors and `--help`; the wrapper's
  6-statement shape leaves no room for argparse; and
  `check-supervisor-discipline` forbids `SystemExit` outside
  `bin/*.py`. `io/cli.py` exposes `@impure_safe`-wrapped argparse
  calls with `exit_on_error=False`, returning
  `IOResult[Namespace, UsageError]` via the railway. Each
  `commands/<cmd>.py` exposes a pure `build_parser()` factory; the
  supervisor maps `IOFailure(UsageError)` to exit `2`. See
  `python-skill-script-style-requirements.md` §"CLI argument
  parsing seam".
- **Python modules bundled with the skill MUST comply with the
  `python-skill-script-style-requirements.md`** companion document
  (destined for `SPECIFICATION/constraints.md`).
- **CLAUDE.md coverage:** every directory under `scripts/` (with
  `_vendor/` and its entire subtree explicitly excluded) MUST
  contain a `CLAUDE.md` file with directory-local constraints an
  agent working at that level must satisfy. See
  `python-skill-script-style-requirements.md`.
- **Bundle contents are runtime-only.** Developer-time tooling
  (enforcement checks, `justfile`, `.mise.toml`, `lefthook.yml`,
  `.github/workflows/`) lives outside the bundle at
  `<livespec-repo-root>/`. See §"Developer tooling layout" below.
- **Project-root detection contract (v017 Q9).** Every wrapper
  that operates on project state (`bin/seed.py`,
  `bin/propose_change.py`, `bin/critique.py`, `bin/revise.py`,
  `bin/prune_history.py`, `bin/doctor_static.py`, and
  `bin/resolve_template.py`) accepts `--project-root <path>` as
  an optional CLI flag with default `Path.cwd()`. The project
  root anchors `<spec-root>/` resolution and (for every wrapper
  except `bin/seed.py`, which runs before `.livespec.jsonc`
  exists on disk) the upward walk to find `.livespec.jsonc`.
  The upward-walk logic lives in `livespec.io.fs` as a shared
  helper reused by every wrapper and by
  `livespec.doctor.run_static`. `bin/resolve_template.py`'s
  additional `--template <value>` flag (v017 Q2) is wrapper-
  specific; the `--project-root` flag shape is uniform across
  every wrapper.
- **Spec-target selection contract (v018 Q1).**
  `bin/propose_change.py`, `bin/critique.py`, and
  `bin/revise.py` accept an optional `--spec-target <path>`
  CLI flag selecting which spec tree the sub-command operates
  on. Default: the main spec root (resolved from
  `.livespec.jsonc` via the shared upward-walk helper, same as
  the default tree for every wrapper). Supplying
  `--spec-target SPECIFICATION/templates/<name>` routes the
  proposal to a built-in template's sub-spec tree per
  §"SPECIFICATION directory structure — Template
  sub-specifications". The flag value is resolved relative to
  `--project-root` and validated: it MUST name a directory
  whose structure matches the main-spec layout (contains
  `proposed_changes/` and `history/` subdirs, plus at least
  one template-declared spec file at the target tree's
  `<spec-root>/`-relative paths). If validation fails, the
  wrapper exits 3 with `PreconditionError` naming the target
  path and the missing structural requirement.
  `critique`'s internal delegation to `propose_change`
  forwards the `--spec-target` value verbatim. `bin/seed.py`,
  `bin/prune_history.py`, and `bin/resolve_template.py` do NOT
  accept `--spec-target`: seed produces all trees atomically
  (see §"seed"); `prune_history` is a per-tree operation but
  the v1 scope prunes only the main tree (v2+ may widen;
  tracked in `sub-spec-structural-formalization`);
  `resolve_template` is a utility that doesn't operate on
  spec-tree state.
  `bin/doctor_static.py` does NOT accept `--spec-target`
  either; doctor-static iterates over EVERY spec tree
  (main + each sub-spec) per §"doctor → Static-phase
  structure" — targeting a single tree for doctor purposes
  would defeat the cross-tree consistency the check suite
  verifies.

#### Shebang-wrapper contract

Each `bin/<cmd>.py` MUST consist of exactly the following shape,
comprising 6 statements (no other statements, and no other lines
beyond the optional single blank line between the import block and
the `raise SystemExit(main())` statement):

```python
#!/usr/bin/env python3
"""Shebang wrapper for <description>. No logic; see livespec.<module> for implementation."""
from _bootstrap import bootstrap
bootstrap()
from livespec.<module>.<submodule> import main

raise SystemExit(main())
```

`bin/_bootstrap.py` is the shared bootstrap module owning sys.path
setup and the Python-version check. It lives under `bin/` so its
`raise SystemExit(127)` is allowed by `check-supervisor-discipline`.
See `python-skill-script-style-requirements.md` for the
`_bootstrap.py` body and the `check-wrapper-shape` AST check.

### Dependencies

#### Runtime dependencies (end-user install)

- **`python3` >= 3.10** is the sole runtime dependency imposed on
  end-user machines. The shared `bin/_bootstrap.py` checks
  `sys.version_info` at wrapper invocation time and exits `127`
  with an actionable install instruction if older.
- **No other runtime dependencies.** No `jq`. No PyPI install step.
  The skill ships third-party libraries vendored under
  `.claude-plugin/scripts/_vendor/<lib>/`.
- **No bash** is invoked anywhere in the shipped bundle.
- **Vendored pure-Python libraries** bundled with the skill, each
  pinned to an exact upstream version recorded in
  `<repo-root>/.vendor.jsonc` (JSONC format — JSON + `//` and
  `/* */` comments, parsed via the vendored `jsoncomment` library
  so no additional TOML/YAML parser is required). Shape is one
  top-level object keyed by vendored-lib name, each value an
  object with `upstream_url`, `upstream_ref`, and `vendored_at`
  fields; shim libraries additionally carry `shim: true` (see
  v013 M1 typing_extensions shim below). Consumed by
  `just vendor-update <lib>` (a shell recipe that invokes
  Python through `livespec.parse.jsonc` to read/write the file)
  and by human reviewers. `just vendor-update` applies only to
  upstream-sourced libs; shim libraries are widened manually
  via code review (see §"Vendoring discipline" in
  `python-skill-script-style-requirements.md`).
  - `dry-python/returns` (BSD-3-Clause) — ROP primitives
    (`Result`, `IOResult`, `@safe`, `@impure_safe`, `flow`,
    `bind`, `Fold.collect`). Note: pyright has no plugin
    system (microsoft/pyright#607: maintainer rejected plugin
    support in 2020, formalized 2021, reaffirmed 2024) and
    dry-python/returns explicitly does not support pyright
    (dry-python/returns#1513: closed by maintainer 2022 with
    "I don't think it is possible, because we use way too
    many mypy plugins. And pyright does not support them.").
    The `returns-pyright-plugin-disposition` deferred item
    was originally closed in v018 Q4 by vendoring a
    hypothetical `returns_pyright_plugin`; that closure was
    re-opened and re-closed in v025 with the revised
    disposition: **no pyright plugin is vendored.** The
    actual load-bearing guardrails against silent
    `Result` / `IOResult` discards are the seven strict-plus
    diagnostics manually enabled in `[tool.pyright]` —
    `reportUnusedCallResult` in particular forbids calling a
    `Result`-returning function without binding the result.
    Pyright still type-checks `Result[T, E]` generic
    parameters via standard generic inference; without a
    plugin, flow-narrowing through `bind` chains is lossier
    than under mypy-with-plugin, requiring occasional
    explicit annotations or `cast()` calls at combinator
    boundaries. Unnecessary casts are caught by
    `reportUnnecessaryCast` (enabled) and unnecessary
    type-ignores by `reportUnnecessaryTypeIgnoreComment`
    (enabled), so the friction surfaces at call sites rather
    than hiding in opaque `# type: ignore` debt. The
    rejected v025 alternatives (switch typechecker to mypy;
    switch to basedpyright) are documented in
    `history/v025/proposed_changes/critique-fix-v024-revision.md`
    decision D1.
  - `fastjsonschema` (MIT) — JSON Schema Draft-7 validator.
  - `structlog` (BSD-2 / MIT dual) — structured JSON logging.
  - `jsoncomment` (MIT, derivative) — **vendored as a minimal
    shim** at `_vendor/jsoncomment/__init__.py` (v026 D1). The
    shim faithfully replicates jsoncomment 0.4.2's `//` line-
    comment and `/* */` block-comment stripping semantics; multi-
    line strings and trailing-commas support are OPTIONAL —
    implemented only if `livespec/parse/jsonc.py` requires them
    (matching v013 M1's minimalism principle). Used by
    `livespec/parse/jsonc.py` to parse `.livespec.jsonc` and any
    other JSONC input. Module-named `jsoncomment` so existing
    `import jsoncomment` statements work unchanged. The shim's
    `LICENSE` carries verbatim MIT attribution to Gaspare Iengo
    (citing jsoncomment 0.4.2's `COPYING` file as the
    derivative-work source); livespec's shim is a derivative
    work under MIT. `upstream_ref = "0.4.2"` cites the upstream
    release whose comment-stripping semantics the shim
    replicates, giving reviewers a concrete comparison target.
    The v018 Q3 git-based initial-vendoring procedure does not
    apply: the canonical upstream
    (`bitbucket.org/Dando_Real_ITA/json-comment`) was sunset by
    Atlassian circa 2020 and no live git mirror exists; the PyPI
    sdist (`https://pypi.org/project/jsoncomment/`) is the only
    surviving source-of-record. The bootstrap-circularity that
    initially required vendoring jsoncomment ahead of
    `just vendor-update` is now resolved by hand-authoring the
    shim at Phase 2 of the bootstrap plan (see
    §"Initial-vendoring exception" below).
  - `typing_extensions` (PSF-2.0) — **vendored full upstream**
    at `_vendor/typing_extensions/__init__.py` (v027 D1). The
    vendored content is a verbatim copy of upstream
    `typing_extensions/src/typing_extensions.py` at tag
    `4.12.2`. Provides livespec's own canonical-import-path needs
    (`override` for pyright's `reportImplicitOverride` per
    style-doc L2; `assert_never` for the Never-narrowing per
    style-doc L7) plus the variadic-generics + Self + Never +
    TypedDict + ParamSpec + TypeVarTuple + Unpack symbols that
    the vendored returns + structlog + fastjsonschema sources
    transitively require at import time. The verbatim PSF-2.0
    `LICENSE` file is preserved at
    `_vendor/typing_extensions/LICENSE`. v013 M1's hand-authored
    minimal-shim approach was applied through v026 with one
    in-band widening cycle at Phase 2 sub-step 5; that approach
    was replaced in v027 D1 with full upstream vendoring because
    `returns/primitives/hkt.py` uses `Generic[..., Unpack[X]]`
    where `X = TypeVarTuple(...)`, which requires actual
    variadic-generics semantics that 3.10 stdlib lacks and a
    minimal shim cannot synthesize (3.10's
    `Generic.__class_getitem__` rejects non-TypeVar /
    non-ParamSpec arguments; subscriptable stubs are insufficient).
    PROPOSAL.md anticipated this exact path at v013 M1
    ("re-vendoring the full upstream is a future option tracked
    as a scope-widening decision, not a v013 default") — v027
    D1 exercises that scope-widening decision. The v018 Q3 git-
    clone-and-copy initial-vendoring procedure applies to
    typing_extensions post-v027.
  - Each preserves its upstream `LICENSE`; a `NOTICES.md` at the
    livespec repo root lists every vendored library.
- **Vendoring discipline:** `_vendor/` files are NEVER edited
  directly. Re-vendoring goes through `just vendor-update <lib>`,
  which is the only blessed mutation path. Code review and git
  diff visibility catch accidental edits.
- **Initial-vendoring exception (one-time, v018 Q3).** The first
  population of every upstream-sourced vendored lib (`returns`,
  `fastjsonschema`, `structlog`, `typing_extensions`) is a
  one-time MANUAL procedure, distinct from the blessed
  `just vendor-update` path above. (The v018 Q4 addition
  `returns_pyright_plugin` was removed from this list in v025 —
  see decision D1 of
  `history/v025/proposed_changes/critique-fix-v024-revision.md`.
  `jsoncomment` was reclassified as a hand-authored shim in v026
  — see decision D1 of
  `history/v026/proposed_changes/critique-fix-v025-revision.md`
  — and is no longer subject to the git-based procedure below.
  `typing_extensions` was reclassified from hand-authored shim
  to upstream-sourced lib in v027 — see decision D1 of
  `history/v027/proposed_changes/critique-fix-v026-revision.md`
  — and IS subject to the git-based procedure below.):
  1. `git clone` the upstream repo at a working ref into a
     throwaway directory.
  2. `git checkout <ref>` matching the `upstream_ref` recorded
     in `.vendor.jsonc`.
  3. Copy the library's source tree under
     `.claude-plugin/scripts/_vendor/<lib>/`.
  4. Copy the upstream `LICENSE` file verbatim to
     `.claude-plugin/scripts/_vendor/<lib>/LICENSE`.
  5. Record the lib's provenance in `.vendor.jsonc`:
     `upstream_url`, `upstream_ref`, `vendored_at` (ISO-8601
     UTC).
  6. Delete the throwaway clone.
  7. Smoke-test: the wrapper bootstrap imports the vendored
     lib successfully.
  Once the `jsoncomment` shim is hand-authored at Phase 2 of the
  bootstrap plan, `just vendor-update <lib>` becomes the only
  permitted path for subsequent re-vendoring of upstream-sourced
  libs. The initial procedure applies ONCE per livespec repo, at
  Phase 2 of the bootstrap plan; thereafter all upstream-sourced-
  lib mutations flow through the blessed recipe. Shim libraries
  (`jsoncomment` per v026 D1) follow the separate "widened
  manually via code review" rule — initial-vendoring of a shim
  is "the author writes the shim file by hand and authors a
  derivative-work LICENSE with attribution to the upstream
  author (e.g., `jsoncomment` under MIT with attribution to
  Gaspare Iengo)." (Pre-v027, `typing_extensions` was also a
  shim per v013 M1; v027 D1 reclassified it to upstream-sourced
  because vendored libs' transitive use of variadic generics
  required full upstream typing_extensions backports that a
  minimal shim cannot provide on Python 3.10.) The circularity
  the initial-vendoring exception resolves:
  `just vendor-update <lib>` invokes Python through
  `livespec.parse.jsonc` to read/write `.vendor.jsonc`, and
  `livespec.parse.jsonc` imports `jsoncomment`; the recipe
  cannot run before `jsoncomment` exists. Pre-v026 the satisfying
  mechanism was "git-clone-and-copy of upstream"; post-v026 it is
  "hand-author the shim at Phase 2." The circularity argument
  itself stands.
- LLM-bundled prompts MAY reference Python helpers from
  `.claude-plugin/scripts/livespec/**` (e.g., for JSON structural checks); they MUST
  NOT assume any non-vendored dependency.

#### Developer-time dependencies (livespec repo only)

Every tool the enforcement suite requires is managed by a
combination of `mise` ([github.com/jdx/mise](https://github.com/jdx/mise))
and `uv` ([github.com/astral-sh/uv](https://github.com/astral-sh/uv)),
pinned to exact versions in committed configs at the livespec
repository root. **Mise pins non-Python binaries only:** `uv`
itself, `just`, `lefthook` — recorded in `.mise.toml`. **UV pins
Python and every Python package:** the interpreter version
(recorded in `pyproject.toml` `[project.requires-python]` plus a
committed `.python-version` produced by `uv python pin`), and the
dev packages `ruff`, `pyright`, `pytest`, `pytest-cov`,
`pytest-icdiff`, `hypothesis`, `hypothesis-jsonschema`, `mutmut`,
`import-linter` — declared in `pyproject.toml`
`[dependency-groups.dev]` with exact versions, resolved into a
committed `uv.lock`, and installed into a project-local `.venv`
via `uv sync --all-groups`. Running `mise install` followed by
`uv sync --all-groups` followed by `just bootstrap` (which
executes `lefthook install` and any other one-time setup)
produces a ready-to-run environment. Developer tooling is NOT
installed into user projects; it is purely livespec-maintainer-
facing.

**Typechecker decision (v018 Q4).** Livespec uses
`pyright` (microsoft/pyright) as its typechecker, NOT the
`basedpyright` community fork. Rationale: the v012 L1 + L2
strict-plus diagnostics are manually enabled in
`[tool.pyright]`; pyright strict-plus provides the load-bearing
guardrails against agent-authored-code failure patterns
(silent `Result`/`IOResult` discards, implicit overrides,
uninitialized instance variables, unnecessary type-ignores,
unnecessary casts, unnecessary isinstance, implicit string
concatenation). basedpyright's defaults-are-stricter advantage
is marginal given livespec's v012 manual strict-plus
configuration already enables every diagnostic that matters;
basedpyright's baselining system is valuable for legacy-code
adoption but livespec starts strict from Phase 2 (no legacy
baseline). Community-fork maintainer-pool risk (smaller pool
than upstream; semantic-drift potential over time) outweighs
the incremental defaults-simplification benefit. Closes the
`basedpyright-vs-pyright` deferred item in v018.

The v012-added dev tools (uv-managed per v024, NOT vendored in the bundle):

- **`hypothesis`** (HypothesisWorks/hypothesis, MPL-2.0) — property-
  based testing, mandatory for tests of pure modules
  (`livespec/parse/`, `livespec/validate/`). See
  `python-skill-script-style-requirements.md` §"Property-
  based testing for pure modules". MPL-2.0 license is acceptable
  for uv-managed dev-time deps (per v024); the vendored-libs license policy
  (which restricts to MIT / BSD / Apache-2.0) does NOT apply
  because `hypothesis` is not vendored.
- **`hypothesis-jsonschema`** (MIT) — auto-generates Hypothesis
  strategies from JSON Schema definitions; pairs with the schema-
  driven validators.
- **`mutmut`** (MIT) — mutation testing on a release-gate schedule;
  see `python-skill-script-style-requirements.md` §"Mutation
  testing as release-gate".
- **`import-linter`** (seddonym/import-linter, BSD-2) — declarative
  architecture enforcement via `[tool.importlinter]` contracts in
  `pyproject.toml`. Replaces v011's planned hand-written
  `check-purity` + `check-import-graph` + import-surface portion
  of `check-no-raise-outside-io`. See
  `python-skill-script-style-requirements.md` §"Enforcement
  suite" for the new `check-imports-architecture` target.

These are uv-managed (per v024) because they are test-time /
dev-tool-only deps and follow the same packaging convention as
`pytest`, `pytest-cov`, `pytest-icdiff`. They are NOT imported by
`.claude-plugin/scripts/livespec/**` at user-runtime, so bundle vendoring would be
mis-applied.

Note: `typing_extensions` is NOT in this uv-managed list. It is
vendored in `_vendor/typing_extensions/` (see "Vendored
pure-Python libraries" above) because `.claude-plugin/scripts/livespec/**` imports
`@override` and `assert_never` from it at user runtime — see
v013 M1 disposition.

### Host capabilities required

- File I/O within the project tree.
- Shell execution for running Python scripts via Claude Code's bash
  tool.
- LLM access through the host.

### Git

- `livespec` MUST NOT write to git (no commits, pushes, branches,
  tags).
- `livespec` MAY read git state (read-only `git status` /
  `git show HEAD:…` / `git ls-files` / `git config --get`) only
  where documented. The documented readers in v1 are:
  1. The `doctor-out-of-band-edits` check (out-of-band edit
     detection), which uses `git show HEAD:` to compare
     committed spec state to history.
  2. The `revise` and `seed` wrappers, which read
     `git config --get user.name` and `git config --get user.email`
     to populate `author_human` on auto-captured revisions.
     Implemented as `livespec.io.git.get_git_user() ->
     IOResult[str, GitUnavailableError]`. Fallback semantics:
     - `IOSuccess("<name> <email>")` on full success (git binary
       present, both config values set).
     - `IOSuccess("unknown")` when the git binary is present but
       either `user.name` or `user.email` is unset (domain
       fallback — continue the write with an anonymous attribution).
     - `IOFailure(GitUnavailableError)` when the git binary is
       absent from PATH. This is a domain error (exit 3);
       `revise` / `seed` abort and direct the user to install git
       (or set `LIVESPEC_AUTHOR_LLM` and proceed if human
       attribution is not required). The further edge cases are
       codified in `deferred-items.md`'s `static-check-semantics`
       entry (`io/git.get_git_user()` semantics).

### Skill-level vs template-level responsibilities

The skill owns **lifecycle and invariants**:
- Sub-command dispatch and arg parsing (in Python).
- All file I/O in the template-declared specification files plus
  `<spec-root>/proposed_changes/` and `<spec-root>/history/`.
- Versioning, history directory creation, version-number contiguity.
- Doctor's static phase invocation and result handling (composed
  via the wrapper's ROP chain — see "Sub-command lifecycle
  orchestration" below).
- File-format validation (proposed-change format, revision format,
  YAML front-matter schemas).
- JSON Schemas that template-emitted JSON must conform to; LLM
  re-prompting on malformed output; abort after N attempts.
- Human-in-the-loop prompting via the LLM (per-proposal decisions,
  delegation toggles) — the LLM layer, not Python, prompts the user.

Sub-commands MAY internally delegate to other sub-commands' logic
without re-triggering pre-step or post-step doctor; the outer
sub-command's doctor lifecycle already covers the whole invocation.

The active template owns **content generation**:
- `prompts/seed.md` — given `<intent>`, produce initial contents for
  each specification file.
- `prompts/propose-change.md` — given raw `<intent>` text, produce
  a JSON findings array conforming to the skill's schema.
- `prompts/revise.md` — given proposed-change + current spec +
  optional `<revision-steering-intent>`, produce modified
  specification-file contents.
- `prompts/critique.md` — given current spec + critique author,
  produce a JSON `findings` array conforming to the skill's
  schema.
- `specification-template/` — the starter content copied to the
  user's repo at seed time.

The skill does NOT decide what content goes in which
specification file (template's job), generate any specification
text (template's job), or interpret intent (template's job).

The template does NOT write files (skill's job), manage version
history (skill's job), validate file formats via doctor (skill's
job), or prompt the user (skill's job).

---

## Sub-command lifecycle orchestration

Each sub-command's deterministic lifecycle (pre-step doctor static
+ sub-command logic + post-step doctor static) is composed inside
the Python wrapper. The post-step LLM-driven phase, where
applicable, runs from skill prose **after** the wrapper exits.

### Wrapper-side: deterministic lifecycle

The wrapper runs pre-step doctor static, sub-command logic, and
post-step doctor static in that order. On any `status: "fail"`
finding from pre-step, the wrapper aborts with exit 3 and
sub-command logic does not run. On any `status: "fail"` finding
from post-step, the wrapper aborts with exit 3 after sub-command
logic has already mutated on-disk state (the user is instructed
via findings to commit the partial state and proceed).

Pre-step/post-step applicability:

- **`seed` is exempt from pre-step** doctor static. Seed's
  purpose is to create the very files the static checks look for;
  running pre-step on a green-field repo would fail
  `template-files-present` and `proposed-changes-and-history-dirs`
  before `seed_run` ever executed. Seed runs post-step only.
  Seed's idempotency refusal (existing target files) still
  applies and is checked inside `seed_run`.
- **`help`, `doctor`, and `resolve_template` have neither pre-step
  nor post-step** wrapper-side static. `help` does no spec work;
  `doctor` IS the static phase; `resolve_template` is a utility
  wrapper that reads `.livespec.jsonc` and resolves the active
  template's path — running doctor-static before template resolution
  would recurse (the `livespec-jsonc-valid` check itself needs to
  load `.livespec.jsonc` to validate it, which is what
  `resolve_template.py` already does).
- **`prune-history`** has pre-step doctor static, no post-step
  LLM-driven phase, but post-step static still runs.
- **`propose-change`, `critique`, `revise`** have both pre-step
  and post-step doctor static.

Behavioral contract of each static phase in the wrapper chain:

- The check registry runs; every check produces a `Finding`
  (`pass` / `fail` / `skipped`).
- On any `status: "fail"` the wrapper aborts with exit 3.
  Findings are emitted to stderr via structlog for LLM narration.
  Sub-command wrappers (other than `bin/doctor_static.py`) do
  NOT use stdout for findings; stdout is reserved for the
  wrapper's documented output contract (e.g., none, in most
  cases).
- `bin/doctor_static.py` is the sole wrapper that emits
  `{"findings": [...]}` JSON to stdout per its documented
  contract. It does NOT have pre/post wrap.

Pre-step skip control:

- The wrapper accepts a mutually-exclusive `--skip-pre-check` /
  `--run-pre-check` flag pair for sub-commands that have a
  pre-step (`propose-change`, `critique`, `revise`,
  `prune-history`). Effective skip resolution:
  1. `--skip-pre-check` on the CLI → skip = true.
  2. `--run-pre-check` on the CLI → skip = false (overrides config).
  3. Neither flag → use config key
     `pre_step_skip_static_checks` (default `false`).
  4. Both flags set → argparse usage error (exit 2 via
     `IOFailure(UsageError)`); treated as mutually exclusive.

  The skill MUST surface a warning via LLM narration whenever
  pre-step is skipped (cases 1 and 3-with-config-true). The raw
  record at the skill's structural layer is a JSON finding
  (`status: "skipped"`, `message: "pre-step checks skipped by
  user config or --skip-pre-check"`). The Python layer MUST NOT
  print the warning to stdout (stdout is reserved for the
  structured-findings contract) or as ad-hoc stderr text; LLM
  narration is the user-facing channel.
- `bin/doctor_static.py` rejects BOTH `--skip-pre-check` AND
  `--run-pre-check`; it IS the static phase and has no pre/post
  wrap. Passing either flag to `doctor_static.py` results in an
  argparse usage error (exit 2). The skill prose for `doctor`
  does not forward either flag.

Python composition mechanism for the lifecycle chain is
implementer choice under the architecture-level constraints
(public functions return `Result` or `IOResult`; purity by
directory; `dry-python/returns` ROP primitives; error-handling
discipline per `livespec-nlspec-spec.md` §"Architecture-Level
Constraints — Error Handling Discipline" — expected failures on
the Result track, bugs raise to the supervisor bug-catcher). See
`python-skill-script-style-requirements.md` for the enforcement
rules.

### Skill-prose-side: LLM-driven post-step

For `seed`, `propose-change`, `critique`, `revise`, the SKILL.md
prose MUST follow this pattern after the wrapper exits with code 0:

1. Run the LLM-driven phase per `doctor/SKILL.md` prose.
2. Honor the two LLM-layer flag pairs
   (`--skip-doctor-llm-objective-checks` /
   `--run-doctor-llm-objective-checks` and their subjective
   equivalents) and their corresponding config keys per
   §"LLM-driven phase." **These flags are LLM-layer only**; they
   are never passed to Python wrappers, and Python wrappers never
   see them.
3. Findings from the LLM-driven phase are surfaced to the user
   per the rules in §"LLM-driven phase".

For `livespec doctor` invocation:

1. Skill prose invokes `bin/doctor_static.py`.
2. If exit 0, skill prose runs the LLM-driven phase per
   `commands/doctor.md`.
3. If exit non-zero (1 or 3), skill prose surfaces the failure to
   the user; LLM-driven phase MUST NOT run.

### Note on `bin/doctor.py`

There is no `bin/doctor.py` wrapper. The user invokes
`/livespec:doctor` (or expresses intent in dialogue); the LLM
follows `doctor/SKILL.md`, which calls `bin/doctor_static.py` for
the static phase, then runs the LLM-driven phase from prose. The
asymmetry is intentional: the LLM-driven phase has no Python entry
because Python doesn't invoke the LLM.

---

## Specification model

### Template-agnostic principles (apply to ANY template)

- The specification is conceptually one logical living
  specification, whether it is physically represented as one file
  or many.
- Normative requirements in any specification file that contains
  them MUST use BCP 14 / RFC 2119 / RFC 8174 requirement language
  (`MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`,
  `SHOULD NOT`, `MAY`, `OPTIONAL`). The rule applies regardless of
  how many files the active template uses, including single-file
  templates.
- `intent` is not the name of any specification file in any built-in
  template, and custom templates SHOULD NOT use it as a filename.
  Reason: `intent` is the skill-level domain term for revision
  inputs; using it as a spec file name creates conceptual drag.
- Every normative heading in any specification file MUST be
  uniquely named within that file.
- When a heading is renamed, the same `revise` MUST update every
  markdown reference to it. Doctor MUST detect dangling references
  in its static phase.
- All intent (observations, critiques, external requirements,
  implementation feedback) flows through `propose-change` or
  `critique`. No other ingress paths to the spec lifecycle are
  defined.

### `livespec` template specifics (default template only)

These apply only when `template` is `livespec` (the default). A
different template MAY revise any of the rules in this subsection.

- The specification is represented as multiple files to create
  explicit boundaries for LLMs and tools.
- `spec.md` is the primary source surface of the living
  specification.
- `contracts.md`, `constraints.md`, and `scenarios.md` are
  specialized operational specification files of the same living
  specification.
- The split is intentional because those specialized files can be
  processed with lower nondeterminism and stronger checking than
  the general spec surface.
- `scenarios.md` is intentionally isolated so it can support
  holdout scenario usage in the StrongDM Dark Factory style.
  (Forward-looking rationale only; livespec v1 defines no holdout
  mechanism — that is an external evaluation system's concern.)
- Scenario examples and acceptance criteria in `scenarios.md` MUST
  use the standard Gherkin keywords `Scenario:`, `Given`, `When`,
  `Then`, `And`, `But`. Within a scenario block (from a `Scenario:`
  line up to the next `Scenario:` or end-of-file), each keyword
  line MUST be preceded and followed by a blank line so that every
  step renders as its own Markdown paragraph under GitHub-Flavored
  Markdown (GFM). Fenced code blocks MUST NOT be used to contain
  Gherkin steps: the `gherkin` info-string is not part of GFM or
  GLFM and renders inconsistently. No specific Gherkin runner is
  pinned; the contract is rendering predictability under GFM.
  Doctor enforces this format statically (see `gherkin-blank-line-
  format` check below).
- Cross-file references in any file inside the template-declared
  spec root (`<spec-root>/`; default `SPECIFICATION/`) MUST use the
  GitHub-flavored anchor form
  `[link text](relative/path.md#section-name)`. The rule covers
  specification files, the spec-root `README.md`, proposed-change
  files, revision files, and within-file anchors.

---

## SPECIFICATION directory structure (livespec template)

The default (`livespec`) template produces:

```
<project-root>/
├── .livespec.jsonc                    (created by seed with full commented schema)
└── SPECIFICATION/
    ├── README.md                      (generated from template at seed; then a normal spec file)
    ├── spec.md
    ├── contracts.md
    ├── constraints.md
    ├── scenarios.md
    ├── proposed_changes/
    │   ├── README.md                  (skill-owned; one-paragraph directory description; written only at seed)
    │   └── <topic>.md                 (zero or more in-flight proposed-change files)
    └── history/
        ├── README.md                  (skill-owned; one-paragraph directory description; written only at seed)
        └── vNNN/                      (one directory per version)
            ├── README.md              (archived copy of SPECIFICATION/README.md at this version; user content, versioned)
            ├── spec.md
            ├── contracts.md
            ├── constraints.md
            ├── scenarios.md
            └── proposed_changes/
                ├── <topic>.md                 (each proposal processed during the revise that produced this version)
                └── <topic>-revision.md        (paired revision decision record)
```

Notes:

- Historic files under `history/vNNN/` use plain filenames (no
  `vNNN-` prefix). The parent directory name conveys the version.
  Dropping the prefix preserves relative markdown links: an
  archived proposed-change containing `[Foo](../spec.md#foo)`
  resolves to `history/vNNN/spec.md` (the archived spec at that
  version), not to the current working spec.
- The parallel structure (`proposed_changes/` subdir under each
  `history/vNNN/`) mirrors the active `SPECIFICATION/` tree shape.
- The working `proposed_changes/` directory MUST be empty after a
  successful `revise` (every proposal is moved into the new
  history version).
- The directory-README files in top-level `proposed_changes/` and
  `history/` are **skill-owned**: hard-coded inside the skill,
  written by `seed` only, not regenerated on every `revise`. Their
  exact content is frozen as follows.

  `SPECIFICATION/proposed_changes/README.md`:

  > # Proposed Changes
  >
  > This directory holds in-flight proposed changes to the
  > specification. Each file is named `<topic>.md` and contains
  > one or more `## Proposal: <name>` sections with target
  > specification files, summary, motivation, and proposed
  > changes (prose or unified diff). Files are processed by
  > `livespec revise` in creation-time order (YAML `created_at`
  > front-matter field) and moved into
  > `../history/vNNN/proposed_changes/` when revised. After a
  > successful `revise`, this directory is empty.

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
  > revision(s) processed during the `revise` that cut the
  > version.
- Per-version `history/vNNN/README.md` is a versioned copy of
  `SPECIFICATION/README.md` at that version. It is user content,
  not skill-owned, and is snapshotted by `revise` like any other
  spec file.
- `SPECIFICATION/README.md` is generated from the active
  template's `specification-template/SPECIFICATION/README.md` at
  seed time, then treated as a normal spec file (editable via
  `propose-change` / `revise`, not touched by the skill
  afterwards).
- When `prune-history` has been run, the oldest surviving version
  directory `vN-1` contains only a single `PRUNED_HISTORY.json`
  file instead of full content (see "Pruning history" below).

### SPECIFICATION directory structure (minimal template, v014 N1)

The `minimal` template declares `spec_root: "./"` (repo-root
placement). With `spec_root` set this way, the directory tree
is flat:

```
<project-root>/
├── .livespec.jsonc                    (created by seed with full commented schema)
├── SPECIFICATION.md                   (single spec file; user-editable)
├── proposed_changes/
│   ├── README.md                      (skill-owned; written only at seed)
│   └── <topic>.md                     (zero or more in-flight proposals)
└── history/
    ├── README.md                      (skill-owned; written only at seed)
    └── vNNN/                          (one directory per version)
        ├── SPECIFICATION.md           (archived copy at this version)
        └── proposed_changes/
            ├── <topic>.md
            └── <topic>-revision.md
```

Every doctor-static check's path references are parameterized
against `DoctorContext.spec_root` (per v009 I7); with
`spec_root = Path("./")`, paths like
`<spec-root>/proposed_changes/` resolve to
`<project-root>/proposed_changes/`. The skill-owned README
paragraphs in `proposed_changes/README.md` and
`history/README.md` are template-agnostic (same contents as
the `livespec` template's; only the `<spec-root>/` base
differs).

**No per-version `README.md` in `history/vNNN/` for minimal.**
The `livespec` template's per-version README is a versioned
snapshot of `SPECIFICATION/README.md` (a separate file); the
`minimal` template has no separate README file — the only
spec file IS `SPECIFICATION.md`, which gets snapshotted.

### Template sub-specifications (v018 Q1)

Livespec-shipped sub-artifacts (the two built-in templates)
each carry their own sub-specification tree under
`SPECIFICATION/templates/<template-name>/`. The purpose is to
place the content of every livespec-shipped template
(`template.json`, `prompts/*.md`, starter content under
`specification-template/`) under the same governed loop as
core livespec code: prompt interview flows, starter-content
policies, NLSpec-discipline injection, delimiter-comment
formats, and every other template-internal decision is
specified in the sub-spec; template content is agent-generated
from that sub-spec via the standard propose-change → revise
loop (with `--spec-target <path>` selecting the sub-spec tree
instead of the main spec tree).

Sub-spec tree shape (v020 Q1: sub-specs are livespec-internal
spec trees and use the multi-file livespec layout uniformly).
Sub-spec layout decouples from the end-user-facing convention
of the template the sub-spec describes — a sub-spec governs
the template's behavior under livespec, not the shape of specs
end users author with that template. Every v1 sub-spec ships
`spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, a
sub-spec-root `README.md`, `proposed_changes/`, and `history/`
(with per-version `README.md` snapshots), uniformly:

```
<project-root>/
└── SPECIFICATION/                          (main spec, described above)
    ├── spec.md
    ├── contracts.md
    ├── constraints.md
    ├── scenarios.md
    ├── proposed_changes/
    ├── history/
    └── templates/                          (v018 Q1 addition)
        ├── livespec/                       (sub-spec for the livespec built-in template)
        │   ├── README.md                   (sub-spec-root orientation; livespec-internal)
        │   ├── spec.md                     (the livespec template's user-visible behavior)
        │   ├── contracts.md                (skill↔template I/O contracts at template level)
        │   ├── constraints.md              (NLSpec discipline constraints for this template)
        │   ├── scenarios.md                (Gherkin per livespec-template convention)
        │   ├── proposed_changes/           (per-sub-spec in-flight proposals)
        │   └── history/                    (per-sub-spec versioned snapshots, with per-version README)
        └── minimal/                        (sub-spec for the minimal built-in template)
            ├── README.md                   (sub-spec-root orientation; livespec-internal — present uniformly per v020 Q1, decoupled from minimal's end-user no-README convention)
            ├── spec.md                     (the minimal template's positioning + interview intents)
            ├── contracts.md                (including the delimiter-comment format contract)
            ├── constraints.md              (single-file constraint; doctor-check exemptions)
            ├── scenarios.md                (per minimal-template conventions — no Gherkin)
            ├── proposed_changes/
            └── history/                    (per-sub-spec versioned snapshots, with per-version README)
```

v1 scope: ONLY the `livespec` and `minimal` built-ins ship
sub-specs. Custom templates MAY carry their own sub-spec but
are NOT required to; livespec imposes no sub-spec requirement
on extension authors (consistent with the user-provided-
extensions minimal-requirements principle per §"User-provided
extension scope" — extension authors owe only the calling-API
contract).

Structural implications (see the deferred entry
`sub-spec-structural-formalization` for the formalization
work):

- **`seed` produces main + sub-specs atomically.** One `seed`
  invocation writes main `spec.md`/`contracts.md`/etc. AND
  each built-in template's sub-spec tree plus each sub-spec's
  `history/v001/`. The `seed_input.schema.json` widens to
  carry a `sub_specs: list[SubSpecPayload]` field, each entry
  carrying the sub-spec's spec-file content AND the sub-spec's
  template-name marker used by doctor-static per-tree check
  scoping.
- **`propose-change` and `revise` accept `--spec-target
  <path>`.** Flag defaults to the main spec root (resolved via
  `.livespec.jsonc` at `--project-root`). Supplying
  `--spec-target SPECIFICATION/templates/livespec` (or any
  sub-spec root) routes the proposal to that sub-spec's
  `proposed_changes/` and `history/`. `critique`'s internal
  delegation to `propose-change` forwards `--spec-target`
  uniformly. The flag is the v018 Q1 seam between main-spec
  work and sub-spec work; the same wrapper code path handles
  both.
- **Doctor parameterizes per-tree.** `run_static.py` discovers
  sub-spec trees by enumerating
  `<main-spec-root>/templates/<name>/` at startup (building a
  list of `(spec_root, template_name)` pairs — the main tree
  uses template-name `main`). Each per-tree iteration runs
  the applicable check subset with `DoctorContext.spec_root`
  set to the tree's root. Per-tree applicability: every check
  walks every tree EXCEPT that `gherkin-blank-line-format`
  applies to the main spec + the `livespec` sub-spec but NOT
  the `minimal` sub-spec (matching the top-level conventions
  — the `minimal` sub-spec's `scenarios.md` follows the
  minimal template's no-Gherkin convention, not the livespec
  template's Gherkin convention).
- **`tests/heading-coverage.json` entries carry a `spec_root`
  field.** Each entry's `{spec_file, heading, test, reason?}`
  tuple extends to `{spec_root, spec_file, heading, test,
  reason?}`. The meta-test scopes its walk per
  (spec_root, spec_file) pair. Existing main-spec entries
  default to `spec_root: "SPECIFICATION"`.
- **Template content is agent-generated from each sub-spec,
  not hand-authored.** Phase 7 of the bootstrap plan runs a
  propose-change → revise cycle against each sub-spec; the
  revise decision's `resulting_files[]` carries the generated
  template content paths (`template.json`, `prompts/*.md`,
  `specification-template/**`) alongside the sub-spec's own
  file updates. Post-Phase-7, template content mutations flow
  through the same cycle; hand-editing
  `.claude-plugin/specification-templates/<name>/**` is a bug
  in execution per the v018 Q2 bootstrap-exception clause.

Does NOT re-open the v1 "Multi-specification per project"
non-goal. That non-goal (see §"v1 non-goals") is about
unrelated independent specs co-existing in one repo with
independent governance. This is hierarchical sub-specs of a
single primary spec — a narrower, strictly smaller model.
Sub-specs share the main `.livespec.jsonc`; custom templates
that choose to ship their own sub-spec do not gain a
second `.livespec.jsonc`.

---

## Configuration: `.livespec.jsonc`

`.livespec.jsonc` lives at the project root. It is OPTIONAL; when
absent, all documented defaults apply.

### JSONC dialect

`.livespec.jsonc` uses the JSONC dialect: JSON plus `//` line
comments and `/* ... */` block comments. Trailing commas,
single-quoted strings, and unquoted keys (features that would
qualify as JSON5) are NOT supported. Parsing is implemented at
`.claude-plugin/scripts/livespec/parse/jsonc.py` as a thin pure wrapper over the
vendored `jsoncomment` library (comment-stripping pre-pass into
stdlib `json.loads`).

### Schema

```jsonc
{
  // Active template. Accepts either a built-in name ("livespec") or
  // a path (relative to project root) to a custom template directory.
  // Default: "livespec"
  "template": "livespec",

  // Expected template format version. Belt-and-suspenders check
  // against the template's own declared `template_format_version`
  // in its `template.json`. Doctor validates they match.
  // Default: 1
  "template_format_version": 1,

  // If true, post-step doctor (run automatically after successful
  // seed / propose-change / critique / revise) skips the LLM-driven
  // objective-checks phase. Explicit `livespec doctor` runs are
  // unaffected by this key unless overridden at invocation. See
  // §"LLM-driven phase" for the full flag/config precedence.
  // Default: false
  "post_step_skip_doctor_llm_objective_checks": false,

  // If true, post-step doctor skips the LLM-driven subjective-checks
  // phase. Same scope and precedence as the objective-checks key.
  // Default: false
  "post_step_skip_doctor_llm_subjective_checks": false,

  // If true, sub-commands skip the pre-step static check. Intended
  // for emergency recovery when the project is in a broken state
  // that normal commands cannot repair. The skill MUST print a
  // warning every time pre-step is skipped.
  // Default: false
  "pre_step_skip_static_checks": false
}
```

`seed` MUST create `.livespec.jsonc` with this full schema inline,
including comments and defaults, so the configuration is
self-documenting on disk. Subsequent writes (if any) preserve
commentary.

### Validation

The skill MUST validate `.livespec.jsonc` against a JSON Schema
Draft-7 file at `.claude-plugin/scripts/livespec/schemas/livespec_config.schema.json`
on every read. Validation uses the vendored `fastjsonschema` library
from `.claude-plugin/scripts/_vendor/fastjsonschema/` via the factory-shape
validator pattern (see "Validators" in
`python-skill-script-style-requirements.md`): `io/` reads the schema
from disk, `validate/` is pure and accepts the parsed schema dict
as a parameter.

### Absence behavior

- If `.livespec.jsonc` is missing, the skill MUST behave as if it
  contained the schema defaults above.
- `seed` MUST create `.livespec.jsonc` with explicit defaults on
  first run.
- `doctor` MUST NOT fail when `.livespec.jsonc` is missing; it
  MUST fail (static phase) when present and malformed.

### Per-invocation CLI overrides

- `--skip-pre-check` is a wrapper-parsed flag (the user passes it
  in dialogue; the LLM forwards it to `bin/<cmd>.py`). It elides
  the first `run_static` step from the wrapper's ROP chain.
  Effective skip = config OR wrapper flag. The skill MUST surface
  a warning to the user via LLM narration whenever pre-step is
  skipped. The raw record at the skill's structural layer is a
  JSON finding (`status: "skipped"`, `message: "pre-step checks
  skipped by user config or --skip-pre-check"`). The Python layer
  MUST NOT print the warning to stdout (stdout is reserved for the
  structured-findings contract) or as ad-hoc stderr text; LLM
  narration is the user-facing channel.
- `--skip-doctor-llm-objective-checks` / `--run-doctor-llm-objective-checks`
  and `--skip-doctor-llm-subjective-checks` / `--run-doctor-llm-subjective-checks`
  are **LLM-layer flags only**. They are never passed to Python
  wrappers. Each pair is mutually exclusive (both set → argparse
  usage error, exit 2). Precedence for each category: CLI flag →
  config key (`post_step_skip_doctor_llm_objective_checks` or
  `post_step_skip_doctor_llm_subjective_checks`) → hardcoded
  default `false`. The narration rule of §"LLM-driven phase"
  applies: silent skip → warning; explicit CLI flag (either
  direction) → self-evident, no narration.

### Environment variables

- **`LIVESPEC_LOG_LEVEL`** (default `WARNING`). Sets the skill's
  structlog log level. Accepted values: `DEBUG`, `INFO`, `WARNING`,
  `ERROR`, `CRITICAL`. CLI flag `-v` / `-vv` overrides the env var
  per the style doc §"Structured logging".
- **`LIVESPEC_AUTHOR_LLM`** (default unset). When set and non-
  empty, the `propose-change`, `critique`, and `revise` wrappers
  use this value for the `author` payload/file-front-matter field
  (and for the `author_llm` field on revision-file front-matter,
  where applicable), overriding the LLM-self-declared `author` in
  the JSON payload and the `"unknown-llm"` fallback. A
  `--author <id>` CLI flag on the invocation still wins over the
  env var per the unified precedence rules — see
  §"propose-change → Author identifier resolution", §"critique",
  §"revise", and §"Revision file format".

### Multi-specification per project

Out of scope for v1 in its general form. The schema
intentionally has no `specification_dir` field — the template
controls placement. v018 Q1 introduces a narrower, strictly
smaller sub-specification mechanism (`SPECIFICATION/templates/
<name>/` per §"SPECIFICATION directory structure — Template
sub-specifications") for livespec-shipped sub-artifacts
(built-in templates); that mechanism is hierarchical sub-specs
of a single primary spec, NOT independent multi-spec. The v1
non-goal is about unrelated independent specs co-existing in
one repo with independent governance (distinct `.livespec.jsonc`
files; independent versioning; no primary/sub relationship)
— which remains out of scope.

---

## Templates

A template is a self-contained directory that defines both the
initial on-disk spec content and the LLM-driven behavior for each
command. Templates live under
`.claude-plugin/specification-templates/<name>/`
for built-in templates, or at a user-provided path for custom
templates.

### Template directory layout (MUST)

```
<template-root>/
├── template.json
├── prompts/
│   ├── seed.md
│   ├── propose-change.md
│   ├── revise.md
│   ├── critique.md
│   ├── doctor-llm-objective-checks.md    (OPTIONAL; path named by template.json)
│   └── doctor-llm-subjective-checks.md   (OPTIONAL; path named by template.json)
└── specification-template/
    └── ...                                (mirrors intended repo-root layout)
```

- `template.json` is REQUIRED. Recognized fields:
  - `template_format_version: integer` (REQUIRED). v1 livespec
    supports only `template_format_version: 1`.
  - `spec_root: string` (OPTIONAL; default `"SPECIFICATION/"`). Names
    the directory under the repo root containing the spec files,
    `proposed_changes/`, and `history/`. Doctor-static checks read
    `spec_root` from the resolved template's `template.json` via
    `DoctorContext.spec_root` and parameterize all path references
    against it. A template that places spec files directly at the
    repo root sets `"spec_root": "./"`.
  - `doctor_static_check_modules: list[string]` (OPTIONAL; default
    `[]`). Paths relative to the template root naming Python modules
    that contribute additional doctor-static checks. Each module
    MUST export `TEMPLATE_CHECKS: list[tuple[str, CheckRunFn]]`
    (same shape as the skill-internal static registry). Loaded at
    doctor-static invocation time via
    `importlib.util.spec_from_file_location`. See §"Doctor static-
    phase" for the composition rules.

    **User-provided extension scope.** Modules loaded via this
    field carry MINIMAL requirements: only the calling-API
    contract (the `TEMPLATE_CHECKS` export shape, `CheckRunFn`
    signature, `Finding` payload shape — all defined inside
    `livespec/`). livespec imposes NO library-usage,
    architecture, pattern, style, or quality expectations on
    extension code beyond invocability per the contract.
    livespec's enforcement suite (pyright, ruff, the AST
    checks, Import-Linter, Hypothesis, mutmut) does NOT scope
    to extension-loaded modules. Extension authors bring their
    own dependency-resolution mechanism; livespec does NOT
    vendor third-party libraries on extension authors' behalf.
    The same minimal-requirements principle applies to any
    future template-extension hook livespec may declare.
  - `doctor_llm_objective_checks_prompt: string | null` (OPTIONAL;
    default `null`). Path relative to the template root naming a
    Markdown prompt file whose contents drive the LLM-driven
    objective-checks phase for this template. When null, the skill
    runs only its baked-in LLM-objective checks.
  - `doctor_llm_subjective_checks_prompt: string | null` (OPTIONAL;
    default `null`). Path relative to the template root naming a
    Markdown prompt file whose contents drive the LLM-driven
    subjective-checks phase for this template. When null, the
    skill runs only its baked-in LLM-subjective checks.

  No other fields are defined in v1. The skill is unaware of any
  other files the template may ship at its root (e.g., internal
  discipline docs referenced only by the template's own prompts).

- `prompts/` is a fixed-by-convention path. `prompts/seed.md`,
  `prompts/propose-change.md`, `prompts/revise.md`, and
  `prompts/critique.md` are REQUIRED. The two `prompts/doctor-
  llm-*-checks.md` files are OPTIONAL; their specific paths (if
  supplied) are named by the corresponding `template.json` field,
  so templates MAY place them anywhere under the template root
  (the `prompts/` convention is the strongly-recommended default).
- `specification-template/` is a fixed-by-convention path. Its
  contents mirror the repo-root structure the template intends to
  produce. At seed time, the skill copies/processes these into
  the user's repo at corresponding paths. A template MAY place
  spec files directly at the repo root (e.g.,
  `specification-template/SPEC.md` mirrors to
  `<repo-root>/SPEC.md`) or under any subdirectory structure.

### Template resolution contract (`bin/resolve_template.py`)

Per-sub-command SKILL.md prose invokes `bin/resolve_template.py`
via Bash to learn the active template's absolute directory path
(see §"Per-sub-command SKILL.md body structure" step 4). Its
contract is frozen in v1 so the same invocation works uniformly
for built-in and user-provided templates, and so v2+ template-
discovery extensions (`user-hosted-custom-templates` deferred
item) can land as additive functionality without breaking
consumers.

- **Invocation shape.** Zero positional arguments. Two optional
  flags:
  - `--project-root <path>` (default: `Path.cwd()`). When
    `--template` is NOT supplied, the wrapper walks upward from
    `--project-root` looking for `.livespec.jsonc`. When
    `--template` IS supplied, `--project-root` is used only as
    the base for resolving a user-provided relative template
    path.
  - `--template <value>` (OPTIONAL; v017 Q2 addition for
    pre-seed template resolution). When supplied, the wrapper
    bypasses `.livespec.jsonc` lookup entirely and resolves
    `<value>` directly: built-in names (`livespec`, `minimal`)
    resolve to the bundle's built-in path; any other string is
    treated as a path relative to `--project-root`. This path
    exists so that `seed/SKILL.md` prose can resolve the
    user-chosen template's `prompts/seed.md` BEFORE
    `.livespec.jsonc` exists on disk (the normal pre-seed
    state). Non-seed sub-commands never pass `--template` —
    their SKILL.md prose uses the default `.livespec.jsonc`-
    walking behavior.
- **Stdout contract.** On success, exactly one line: the resolved
  template directory as an absolute POSIX path, followed by `\n`.
  Paths containing spaces are emitted literally (the Read tool
  accepts literal paths; callers MUST NOT pipe through shells
  that re-split on whitespace).
- **Built-in resolution.** When the active template name is
  `"livespec"` or `"minimal"` (sourced from `.livespec.jsonc`'s
  `template` field in the default flow, or from `--template
  <value>` in the pre-seed flow), the wrapper emits
  `<bundle-root>/specification-templates/<name>/` as its stdout,
  where `<bundle-root>` is the `.claude-plugin/` directory of the
  installed plugin (the parent of the `scripts/` subtree that
  houses both `bin/` shebang wrappers and the `livespec/` Python
  package). The path is derived inside
  `livespec/commands/resolve_template.py` (where the `main()`
  implementation lives — the 6-statement shebang wrapper at
  `bin/resolve_template.py` has no room for path-computation
  logic per the wrapper-shape contract) via
  `Path(__file__).resolve().parents[3]`: from
  `.claude-plugin/scripts/livespec/commands/resolve_template.py`,
  `parents[0]` is `commands/`, `parents[1]` is `livespec/`,
  `parents[2]` is `scripts/`, `parents[3]` is `.claude-plugin/`.
- **User-provided path resolution.** When the active template
  value is anything other than a built-in name, the value is
  treated as a path relative to `--project-root`. The wrapper
  resolves the path to absolute and validates that (a) the
  directory exists and (b) it contains `template.json`. (Deeper
  validation — e.g., `template_format_version`, prompt-file
  presence — is left to the `template-exists` doctor
  static-check.)
- **Lifecycle applicability.** `resolve_template` has neither
  pre-step nor post-step doctor static (see §"Sub-command
  lifecycle orchestration — Pre-step/post-step applicability").
- **Exit codes.** `0` on success; `3` on any of {`.livespec.jsonc`
  not found above `--project-root` when `--template` is NOT
  supplied, `.livespec.jsonc` malformed or schema-invalid,
  resolved path missing, resolved path lacks `template.json`};
  `2` on bad CLI usage (unknown flag, both-and-neither-flag
  combinations if any, etc.); `127` on too-old Python (via
  `_bootstrap.py`).
- **v2+ extensibility shield.** The stdout contract (one line,
  absolute POSIX path, trailing `\n`) AND the CLI flag shape
  (`--project-root`, `--template`) are frozen in v1. Future
  template-discovery extensions (remote URLs, registries,
  plugin-path hints, per-environment overrides; see
  `user-hosted-custom-templates` in `deferred-items.md`) MUST
  preserve the exact stdout shape AND MUST extend, not replace,
  the v1 flag set so existing SKILL.md prose continues to work
  unchanged.

### Custom templates are in v1 scope

- `.livespec.jsonc`'s `template` field accepts either a
  **built-in name** (`"livespec"` or `"minimal"` in v1) or a
  **path** to a template directory. Built-in names are resolved
  to `.claude-plugin/specification-templates/<name>/` by
  `bin/resolve_template.py`; paths are resolved relative to
  `--project-root`.
- **Supported built-in names in v1:** `{"livespec", "minimal"}`.
  Any other string value is treated as a path. `resolve_template.py`
  validates that the resolved path contains `template.json`.
- Doctor check `template-exists` validates the resolved template
  directory has the required layout and that `template_format_version`
  matches what livespec supports.
- **Supported `template_format_version` values in v1: `{1}`.** The
  `template-exists` check MUST reject any other value as
  unsupported, naming the offending field, its value, and the
  resolved template path. Future livespec versions extend this
  set; an out-of-set value in a forward-dated spec is a hard
  error, never a warning.
- **Deferred future feature: user-hosted custom templates at
  arbitrary non-plugin locations.** The `bin/resolve_template.py`
  wrapper is the seam through which v2+ template-discovery
  extensions (remote URLs, registries, plugin-path hints,
  per-environment overrides) will land without breaking the
  wrapper's output contract. See `deferred-items.md`'s
  `user-hosted-custom-templates` entry. Custom templates MAY ship
  analogous **template-bundled prompt-reference materials** at
  their template root (the file class introduced for the built-in
  `livespec` template's `livespec-nlspec-spec.md`; see
  §"Built-in template: `livespec`"). Such files are governed
  identically: LLM-time read-only references the custom template's
  prompts cite, not parsed by the skill, not subject to sub-spec
  governance even when the custom template ships its own
  sub-spec, and edited directly under PR review post-bootstrap.

### Skill↔template communication layer

All communication between the skill and template prompts is JSON
with schemas. Each template prompt has a documented input schema
(variables the skill provides) and output schema (what the prompt
emits). The skill/wrapper layer validates output against the schema
using the vendored `fastjsonschema` library. When wrapper
validation returns exit code `4`, the prompt / skill orchestration
SHOULD treat that return code as a retryable malformed-output
signal, re-invoke the relevant template prompt with validation
error context, and re-assemble JSON. v1 intentionally does NOT
normatively specify an exact retry budget; that policy remains part
of prompt / skill orchestration rather than the wrapper contract.

Schemas for the JSON contracts ship as part of the skill in
`.claude-plugin/scripts/livespec/schemas/`. Schema authoring
is tracked in `deferred-items.md` (`wrapper-input-schemas`
widened for v018 Q1 with `SubSpecPayload`). Prompt
input/output details — prompt interview flow, starter content
policy, NLSpec-discipline injection per template — are
specified at each built-in template's sub-specification tree
under `SPECIFICATION/templates/<name>/` per v018 Q1 (the
`template-prompt-authoring` deferred entry is closed in favor
of this mechanism; see `sub-spec-structural-formalization`
for the formalization work).

### Built-in templates

Two built-in templates ship in v1: `livespec` (the default,
multi-file spec) and `minimal` (single-file spec at repo root).
Users SHOULD pick the one that matches their intended spec
shape. A custom template (path-valued `template` field) remains
supported.

#### Built-in template: `livespec` (default)

The `livespec` template produces the SPECIFICATION directory
structure shown above in §"SPECIFICATION directory structure".
Its starter content for each specification file is described
below.

Seed-time starter content:

- `SPECIFICATION/README.md`: overview listing the specification
  files, their purpose, the BCP 14 convention, and the Gherkin
  convention; boilerplate populated from intent.
- `spec.md`: top-level headings derived from the seed intent by
  the template's `prompts/seed.md` (template-controlled behavior).
  A "Definition of Done" heading at the bottom, even if initially
  empty.
- `contracts.md`: header and placeholder section(s).
- `constraints.md`: header and placeholder section(s).
- `scenarios.md`: header, an explanatory paragraph about the
  blank-line-separated Gherkin step convention (no fenced code
  blocks), and one placeholder scenario. Exact stub content:

  ```markdown
  # Scenarios

  This file holds acceptance scenarios in Gherkin form.
  Each Gherkin keyword line is preceded and followed by a blank
  line so that every step renders as its own Markdown paragraph
  under GitHub-Flavored Markdown. Fenced code blocks are not used
  to hold Gherkin steps.

  ## Scenario: <placeholder scenario name>

  Given a placeholder precondition

  When a placeholder action is taken

  Then a placeholder outcome is observed
  ```

The `livespec` template ships `livespec-nlspec-spec.md` at its
template root — the adapted NLSpec guidelines document. The
template's prompts (`prompts/seed.md`, `prompts/propose-change.md`,
`prompts/critique.md`, `prompts/revise.md`, and
`prompts/doctor-llm-subjective-checks.md`) Read it internally
(via `../livespec-nlspec-spec.md`) where NLSpec discipline is
needed. This is a template-internal convention; the skill is not
aware of the file.

`livespec-nlspec-spec.md` is the v1 instance of a distinct file
class shipped at template root: **template-bundled prompt-reference
materials**. Inclusion criteria: LLM-time read-only references the
template's prompts cite at runtime; no skill-side parsing or
behavioral contract; no doctor-static check operates on the file;
the skill's Python is unaware of it. This class is structurally
distinct from `template.json` (skill-side config), `prompts/`
(LLM-time interview/check prompts), and `specification-template/`
(seed-time starter content). Unlike those three classes,
prompt-reference materials are **not governed by the template's
sub-spec at `SPECIFICATION/templates/<name>/`** and are **not
agent-generated in Phase 7 of the bootstrap plan**: the sub-spec
scopes to template *behavior* (interview flow intents, contracts
the prompts produce, constraints the template imposes); rubric
content the prompts cite is upstream input to that behavior, not
output of it. Post-bootstrap evolution of prompt-reference materials
is via direct edit of the bundled file at the template path under
ordinary PR review, exempt from the Plan §3 cutover-principle ban
on hand-editing files under `.claude-plugin/specification-templates/
<name>/`. The carve-out is bounded: the cutover ban continues to
apply to `template.json`, anything under `prompts/`, and anything
under `specification-template/` post-Phase-6.

#### Built-in template: `minimal` (v014 N1)

The `minimal` template produces a **single-file** specification
at the repo root. Intended as:

1. A minimal-example reference for future custom-template
   authors (documenting the smallest set of files a template
   needs to provide).
2. The canonical shape for the v014 N9 end-to-end integration
   test (see §"Testing approach — End-to-end harness-level
   integration test"). Its prompts include hardcoded delimiter
   comments the mock harness parses to drive the workflow
   deterministically. Per v018 Q1, the delimiter-comment format
   is codified in the `minimal` template's sub-spec at
   `SPECIFICATION/templates/minimal/contracts.md` under a
   "Template↔mock delimiter-comment format" section (authored
   during Phase 7 of the bootstrap plan); Phase 9's
   `fake_claude.py` parses against that section, not against
   an implicit implementer convention. The real LLM treats the
   delimiter comments as inert markdown.

Template layout:

```
.claude-plugin/specification-templates/minimal/
├── template.json                       (template_format_version: 1; spec_root: "./")
├── prompts/
│   ├── seed.md                         (REQUIRED; minimal prompt; includes delimiter comments)
│   ├── propose-change.md               (REQUIRED; includes delimiter comments)
│   ├── revise.md                       (REQUIRED; includes delimiter comments)
│   └── critique.md                     (REQUIRED; includes delimiter comments)
└── specification-template/
    └── SPECIFICATION.md                (single starter file; lands at <repo-root>/SPECIFICATION.md)
```

Key characteristics:

- `template.json` declares `spec_root: "./"` (repo-root
  placement). Under this setting, `SPECIFICATION.md`,
  `proposed_changes/`, and `history/` all live directly at
  the repo root rather than under a `SPECIFICATION/`
  sub-directory. Every doctor-static check parameterizes
  against `<spec-root>/` per the v009 I7 discipline;
  `spec_root: "./"` collapses that to the repo root.
- `doctor_llm_objective_checks_prompt` and
  `doctor_llm_subjective_checks_prompt` are OPTIONAL and MAY
  be null (omitting them leaves the LLM-driven doctor phase
  running only the skill-baked checks).
- The `gherkin-blank-line-format` doctor-static check is
  **conditional on the `livespec` template** (see
  §"Static-phase checks"); it does NOT apply when the
  active template is `minimal`.
- `minimal` does not ship a `livespec-nlspec-spec.md`
  reference and does not require its prompts to Read one.
  Users who want NLSpec-style discipline in a single-file
  spec adopt the `livespec` template instead (or author a
  custom template).

Seed-time starter content: a single `SPECIFICATION.md` file
at the repo root, with top-level headings derived from the
seed intent by the template's `prompts/seed.md`, plus a
"Definition of Done" heading at the bottom (even if
initially empty).

---

## Versioning

- Versions are integer-numbered, zero-padded to three digits as
  `vNNN`. Version numbers MUST be monotonic and contiguous in
  the set of versions that exist on disk.
- Version numbers MUST always be parsed and compared numerically,
  never lexically. Doctor's contiguity check uses numeric
  parsing.
- Width starts at 3 digits. New versions are zero-padded to
  `max(3, width-of-previous-highest-on-disk)`. When `v999` is
  exceeded, the next version is `v1000` and all subsequent
  versions use ≥4-digit widths. Historic version directories and
  files keep their original widths forever (no retroactive
  renames). Mixed widths within `history/` are valid.
- The current working spec content lives at the paths produced
  by the template (for the `livespec` template: `SPECIFICATION/`
  plus partition files). Working files do NOT carry any
  version prefix.
- **v000 is the implicit empty pre-seed state.** It never exists
  on disk. `seed` models itself as the proposal that transforms
  v000 into v001.
- A new version is cut when, and only when, `revise` either
  accepts or modifies at least one proposal in
  `<spec-root>/proposed_changes/`. A `revise` invocation that finds no
  proposals MUST fail hard and direct the user to
  `propose-change`.
- A `revise` invocation that processes proposals but rejects all
  of them MUST still cut a new version. The version's
  specification files are byte-identical copies of the prior
  version's specification files; the version's
  `<spec-root>/history/vNNN/` directory contains the proposed-
  change files and rejection revisions. This preserves the audit
  trail for every proposal that ever reached `revise`.
- `seed` creates `v001` directly: it writes both the working
  specification files AND `<spec-root>/history/v001/` including
  the seed's auto-created proposed-change and revision (see
  `seed` below).

---

## Commit conventions and versioning (v034 D1)

livespec adopts **Conventional Commits 1.0** as the commit-
message format and **semantic-release-style** automatic
version derivation from commit history. The convention
applies to commits that land on the livespec repo itself
(authoring of the skill bundle and dev-tooling); it does NOT
apply to commits in user projects that consume livespec —
livespec-the-skill imposes no commit-format discipline on
its consumers.

**Format.** Subject line: `<type>[optional scope][!]:
<description>` (≤ 72 characters). Optional body separated
from subject by one blank line. Optional footer trailers in
`Token: value` form (one per line, separated from the body
by one blank line). Trailers parseable by `git
interpret-trailers --parse`. Recognized types: `feat`, `fix`,
`refactor`, `perf`, `test`, `chore`, `docs`, `build`, `ci`,
`style`, `revert`. Breaking changes are marked with `!` after
the type/scope and a `BREAKING CHANGE:` footer trailer.

**Type semantics for version derivation.**

| Type | Version impact | Notes |
|---|---|---|
| `feat:` | minor bump | new user-facing behavior |
| `fix:` | patch bump | bug correction |
| `BREAKING CHANGE:` (footer) or `<type>!:` | major bump | API or behavior break |
| `refactor:` | none | structure change, behavior-preserving |
| `perf:` | none | performance improvement, behavior-preserving |
| `test:` | none | test-only changes |
| `chore:` | none | maintenance, no source-code change |
| `docs:` | none | documentation only |
| `build:` | none | build-system / dependencies |
| `ci:` | none | CI configuration |
| `style:` | none | formatting only |
| `revert:` | mirrors reverted | revert of a prior commit |

**Type semantics for TDD enforcement.** The TDD-Red/Green
trailer schema (v034 D2) is required on `feat:` and `fix:`
commits and forbidden on `refactor:` and `perf:` commits.
The remaining types skip TDD enforcement entirely (no new
behavior introduced). See §"Testing approach — Activation"
for the full hook contract.

**Versioning derivation.** A semantic-release tool
(specific selection deferred to Phase 9) consumes the
post-v034 commit history to compute the next version. The
`v1.0.0` tag at Phase 10 exit is the first auto-derived
release. Pre-v1 commits drive future changelog generation
but trigger no automatic version bumps; v1 is the first
release where the deriver-tool runs as part of the release
workflow.

**Cutover boundary.** The v034 codification commit is the
first commit under this convention. Pre-v034 commits use the
prior `phase-N: cycle N — ...` prose format and are
grandfathered: commitlint configuration excludes any commit
whose ancestor SHA precedes the v034 codification commit
from format checking. Post-v034 commits are linted at
authoring time (pre-commit hook) and validated at CI time
(GitHub Actions on the PR branch).

**Operational cache via git notes.** See v034 D4 and
§"Developer tooling layout" §"Git notes as operational
cache" for the advisory layer that complements but never
replaces commit-message content.

---

## Pruning history

A dedicated `prune-history` sub-command removes older history
while preserving auditable continuity.

Operation:

1. Identify the current highest version `vN`.
2. If `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json` exists, read its
   `pruned_range[0]` value and retain it as `first` for the new
   marker (carrying the original-earliest version number forward).
   If no prior marker exists, `first` is the earliest v-directory
   version number currently in `<spec-root>/history/` (typically
   `1`).
3. Delete every `<spec-root>/history/vK/` directory where `K < N-1`.
4. Replace the contents of `<spec-root>/history/v(N-1)/` with a
   single file: `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json`,
   containing only
   `{"pruned_range": [first, N-1]}`.
5. Leave `<spec-root>/history/vN/` fully intact.

Invariants:

- Version numbers MUST NEVER be re-used. `prune-history` does
  not reset the counter.
- `PRUNED_HISTORY.json` MUST NOT contain timestamps, git SHAs,
  or identity fields. These are fragile under git rebase/merge,
  and git commit metadata already provides that audit context.
- Doctor's contiguity check (`version-contiguity`) reads the marker
  file and applies contiguity only to surviving versions (those
  with filename ≥ `N-1`). The pruned range is treated as
  intentional missing history.
- Running `prune-history` on a project with only `v001`
  (nothing to prune) is a no-op.
- Running `prune-history` on a project where the oldest
  surviving history entry is already a `PRUNED_HISTORY.json`
  marker (i.e., no full versions below `vN` remain to prune) is
  also a no-op. The existing marker is NOT re-written; no new
  commit-worthy diff is produced. The `prune-history` wrapper
  detects this precondition before reaching step 4 and
  short-circuits with an informational finding
  (`status: "skipped"`, `message: "nothing to prune; oldest
  surviving history is already PRUNED_HISTORY.json"`).

Users MAY run `prune-history` at any time to reduce repository
clutter. Because `prune-history` is destructive, its SKILL.md
frontmatter MUST set `disable-model-invocation: true` — the user
MUST invoke it explicitly via `/livespec:prune-history`.

---

## `livespec` skill sub-commands

Each sub-command lives at `.claude-plugin/skills/<sub-command>/
SKILL.md` and is invoked as `/livespec:<sub-command>`.

The wrapper-side ROP-chain orchestration of pre-step and post-step
doctor is described in §"Sub-command lifecycle orchestration"
above. The skill-prose-side post-step LLM-driven phase is described
in the same section.

### `help`

- `/livespec:help` shows usage and lists every sub-command's
  `description`.
- The user MAY ask for help on a specific sub-command in dialogue;
  the LLM consults that sub-command's SKILL.md.
- `help` MUST NOT run `doctor` (pre- or post-step).
- Frontmatter: read-only `allowed-tools`.

### `seed <intent>`

(The LLM consumes `<intent>` from dialogue in `seed/SKILL.md`
prose; the wrapper `bin/seed.py` itself takes `--seed-json
<path>` where the freeform `<intent>` is already embedded in
the JSON payload. The heading names the user-facing dialogue
interface; see §"Inputs" in the SKILL.md body structure for
the split between SKILL.md-prose and wrapper-CLI
responsibilities.)

- With no args, prompts the user for `<intent>` in dialogue.
- `<intent>` is freeform text and MAY include references to
  existing specifications, examples, projects, or other
  context. Path references and `@`-mentions in the intent are
  handled by the LLM's natural file-reading capability; the
  skill requires no special path-dereference logic.
- **Pre-seed template selection (v014 N1; pre-seed template
  resolution mechanism codified in v017 Q2; sub-spec-emission
  question added in v020 Q2).** When `.livespec.jsonc` is absent
  (the normal pre-seed state), seed's SKILL.md prose MUST
  prompt the user for template choice in dialogue BEFORE
  invoking the wrapper. Options presented: `livespec`
  (multi-file, recommended default), `minimal` (single-file
  `SPECIFICATION.md` at repo root), or a custom template path.
  The LLM then resolves the chosen template's directory by
  invoking `bin/resolve_template.py --project-root . --template
  <chosen>` via Bash (per the v017 Q2 addition to §"Template
  resolution contract"); the wrapper's stdout is the absolute
  template directory path. The LLM uses that path to Read
  `<path>/prompts/seed.md` and proceeds with the normal seed
  template-prompt dispatch. The chosen value is ALSO passed into
  the wrapper via the seed-input payload's required top-level
  `template` field (see payload schema below); the wrapper uses
  that value to bootstrap `.livespec.jsonc` (per v016 P2).

  **Sub-spec-emission dialogue question (v020 Q2).** After
  template selection AND only when the selected template's seed
  prompt declares sub-spec-emission capability (the `livespec`
  built-in is the v1 example; a custom template MAY opt in by
  authoring its `prompts/seed.md` to handle the answer), the
  pre-seed dialogue asks one additional question:

  > "Does this project ship its own livespec templates that
  > should be governed by sub-spec trees under
  > `SPECIFICATION/templates/<name>/`? (default: no)"

  On "yes" (the meta-project case — livespec-the-project itself
  and any user project that ships livespec templates of its
  own), the dialogue then asks for the list of template
  directory names under
  `.claude-plugin/specification-templates/` (or equivalent
  project-specific location); the seed prompt then emits one
  `sub_specs[]` entry per named template per the payload schema
  below. On "no" (the default and the typical end-user case),
  the seed prompt emits `sub_specs: []`. The shipped seed
  prompt's behavior is uniform across templates and does not
  assume any specific main-spec template name; sub-spec emission
  is driven by the user's answer, not by template-conditional
  hard-coding.

  When `.livespec.jsonc` IS present, the wrapper reuses its
  existing `template` value (no dialogue is needed; SKILL.md
  prose MAY skip the prompt entirely and proceed with the
  normal `bin/resolve_template.py --project-root .` resolution
  that walks upward for the existing config). The pre-seed
  dialogue is the only SKILL.md-prose special case for handling
  an absent `.livespec.jsonc`; every non-seed sub-command's
  SKILL.md invokes `bin/resolve_template.py` without
  `--template` and gets exit 3 on a missing config (which is
  the correct behavior because non-seed sub-commands cannot
  usefully run without a seeded project).
- **`.livespec.jsonc` is wrapper-owned (v016 P2; exit codes
  refined in v017 Q5/Q6).** The wrapper writes
  `.livespec.jsonc` as part of its deterministic file-shaping
  work, from a full commented schema skeleton with the
  `template` value taken from the seed-input payload's
  top-level `template` field. The wrapper writes
  `.livespec.jsonc` BEFORE post-step doctor-static runs, so
  post-step inspects a fully-bootstrapped project tree.
  `.livespec.jsonc` is NOT a template-declared target file.
  Three branches cover every state the wrapper can encounter:
    1. **Absent (the normal pre-seed case).** The wrapper writes
       the full commented schema skeleton using the payload's
       `template` value.
    2. **Present and valid.** The wrapper reuses it without
       modification (validating against the config schema
       first); the payload's `template` value MUST match the
       on-disk `template` value or the wrapper exits `3` with a
       `PreconditionError` describing the conflict (v017 Q6 —
       mismatch is an incompatible state between two validated
       inputs, not a CLI-argument error).
    3. **Present but invalid (malformed JSONC or
       schema-invalid).** The wrapper exits `3` with a
       `PreconditionError` citing the specific parse error or
       schema-violation path (v017 Q5). The user's corrective
       action is to fix or delete the broken `.livespec.jsonc`
       before re-running seed. Seed's idempotency refusal may
       also prevent re-running if template-declared target
       files already exist; the user fixes both conditions
       together. This preserves the non-doctor fail-fast rule
       (see §"Doctor → Bootstrap lenience") and never silently
       overwrites a user's manual edit.
- The LLM (per `seed/SKILL.md`) invokes the active template's
  `prompts/seed.md` with `<intent>` and the template's
  `specification-template/` starter content as input. The prompt
  MUST emit JSON conforming to
  `.claude-plugin/scripts/livespec/schemas/seed_input.schema.json`:
  ```json
  {
    "template": "<chosen-template-name-or-path>",
    "files": [
      {"path": "<template-declared spec file path>", "content": "..."}
    ],
    "intent": "<verbatim user intent>",
    "sub_specs": [
      {
        "template_name": "livespec",
        "files": [
          {"path": "SPECIFICATION/templates/livespec/spec.md", "content": "..."}
        ]
      }
    ]
  }
  ```
  The top-level `template` field is required and carries the
  user-chosen template value from the pre-seed SKILL.md-prose
  dialogue (one of `livespec`, `minimal`, or a custom template
  path). Under the built-in `livespec` template, a representative
  main-spec `files[].path` is `SPECIFICATION/spec.md`; under the
  built-in `minimal` template, the representative path is
  `SPECIFICATION.md`. The schema is template-agnostic at the
  main-spec layer; the `template` field controls the concrete
  main-spec path set.

  **Sub-specs payload (v018 Q1; v020 Q2 user-answer-driven).**
  The `sub_specs` field is a list (possibly empty) of
  `SubSpecPayload` entries. Sub-spec emission is driven by the
  user's answer to the pre-seed "ships own livespec templates"
  dialogue question (see §"`seed`" — pre-seed template
  selection above). On "yes", the seed prompt emits one
  `sub_specs[]` entry per template named in the follow-on
  dialogue. Each entry carries the sub-spec's `template_name`
  (matching the template's directory name under
  `.claude-plugin/specification-templates/<name>/` — `"livespec"`
  or `"minimal"` for v1 built-ins, or any user-shipped template
  name) AND a `files[]` array with the sub-spec's spec-file
  content at
  `SPECIFICATION/templates/<template_name>/<spec-file>` per
  §"Template sub-specifications" (uniformly multi-file:
  `README.md`, `spec.md`, `contracts.md`, `constraints.md`,
  `scenarios.md`). On "no" (the default), the seed prompt
  emits `sub_specs: []`. The shipped seed prompt's behavior is
  uniform across templates and does not assume any specific
  main-spec template name; the per-template hard-coded
  dispatch in v019 (where the `livespec` template emitted
  sub-specs unconditionally and the `minimal` template MAY-
  emitted empty) is superseded by the user-driven dialogue
  answer. Custom-template authors MAY choose whether their seed
  prompts implement sub-spec-emission capability per the
  user-provided-extensions minimal-requirements principle.
  The LLM writes this JSON to a temp file and invokes
  `bin/seed.py --seed-json <tempfile>`. The wrapper validates
  the payload against the schema internally; on validation
  failure, it exits 4 with structured findings on stderr. The
  skill SHOULD treat exit 4 as a retryable malformed-payload
  signal and SHOULD re-invoke the template prompt with error context
  per PROPOSAL.md §"Templates — Skill↔template communication
  layer." The exact retry count is intentionally unspecified in
  v1.
- `bin/seed.py --seed-json <path>` is the sole wrapper entry
  point. The wrapper performs its deterministic file-shaping work
  in the following order, all BEFORE post-step doctor-static
  runs:
  1. Write `.livespec.jsonc` at repo root with the full commented
     schema skeleton, using the payload's top-level `template`
     field value.
  2. Write each main-spec `files[]` entry to its specified path.
  3. **(v018 Q1)** For each entry in `sub_specs[]`, write every
     `files[]` entry in that sub-spec to its
     `SPECIFICATION/templates/<template_name>/<spec-file>` path.
     The sub-spec trees are written alongside the main tree,
     atomically with it; sub-spec trees that fail to write for
     any reason roll the entire seed back (partial-write
     refusal).
  4. Create `<spec-root>/history/v001/` for the main spec
     (including the initial versioned spec files, a
     `proposed_changes/` subdir, and, for templates whose
     versioned surface includes one, a per-version README copy).
     Under the built-in `minimal` template, no
     `<spec-root>/history/v001/README.md` is written because the
     template's versioned surface has no separate README file.
  5. **(v018 Q1; v020 Q1 uniform README)** For each sub-spec
     tree, create
     `SPECIFICATION/templates/<template_name>/history/v001/`
     alongside the main-spec history — including the sub-spec's
     own versioned spec files and `proposed_changes/` subdir.
     Every sub-spec tree uniformly captures a sub-spec-root
     `README.md` AND a per-version `README.md` snapshot.
     Sub-spec README presence is decoupled from the described
     template's end-user convention, per §"Template sub-
     specifications" — the sub-spec README serves as
     orientation for the sub-spec's livespec-managed content,
     not as an end-user-facing artifact. The skill-owned
     `proposed_changes/README.md` and `history/README.md`
     paragraphs are written per-tree (same content as the
     main tree's, only the `<spec-root>/` base differs).
  6. Auto-capture the seed itself as a proposed-change (see
     auto-generated-file details below). The auto-captured
     proposed-change lands in the MAIN spec's
     `<spec-root>/proposed_changes/` (sub-specs do not each get
     their own auto-captured seed proposal — the single
     main-spec seed artifact documents the whole multi-tree
     creation).

  Seed is exempt from pre-step doctor-static (see §"Sub-command
  lifecycle orchestration"); post-step runs normally after the
  wrapper's deterministic work completes, and it now validates a
  fully-bootstrapped project tree (including `.livespec.jsonc`
  itself, which is inspected by `livespec-jsonc-valid` and
  `template-exists`).
- **Auto-generated `<spec-root>/history/v001/proposed_changes/seed.md`
  content:** the wrapper writes a proposed-change file
  conforming to the format defined in §"Proposed-change file
  format" with the following canonical contents:
  - Front-matter: `topic: seed`, `author: livespec-seed`,
    `created_at: <UTC ISO-8601 seconds at invocation>`.
  - One `## Proposal: seed` section with:
    - `### Target specification files`: every path listed in the
      seed-input `files` array, one per line (repo-root-relative).
    - `### Summary`: the verbatim string `"Initial seed of the
      specification from user-provided intent."`
    - `### Motivation`: the verbatim `<intent>` from the
      seed-input payload.
    - `### Proposed Changes`: the verbatim `<intent>` from the
      seed-input payload.
- **Auto-generated
  `<spec-root>/history/v001/proposed_changes/seed-revision.md`**: front-matter
  `proposal: seed.md`, `decision: accept`, `revised_at` matching
  `created_at`, `author_llm: livespec-seed`, `author_human:
  <git user or "unknown">`, with `## Decision and Rationale`
  paragraph "auto-accepted during seed" and `## Resulting
  Changes` naming every seed-written file.
- Idempotency: if any template-declared target file already
  exists at its target path, `seed` MUST refuse and list the
  existing files. Partial state (some target files present,
  others absent) is also a refusal; the user is directed to
  `doctor` for diagnosis. The user's recovery is to either
  remove the offending files or run `propose-change` /
  `critique` to evolve the existing spec instead of re-seeding.
- **Post-step doctor-static failure recovery (v014 N7;
  narration contract clarified in v017 Q4).** If seed's
  post-step doctor-static emits fail Findings (exit 3), the
  specification and history files have already been written
  to disk (seed's sub-command logic completed before
  post-step). To correct the issues WITHOUT re-seeding
  (seed's idempotency refusal blocks re-seed), the user
  follows this recovery path:

  1. Review the fail Findings surfaced in stderr / skill-prose
     narration.
  2. Run `/livespec:propose-change --skip-pre-check <topic>
     "<fix description>"` to file a proposed-change that
     addresses the findings. `--skip-pre-check` bypasses the
     pre-step doctor-static that would otherwise trip the same
     findings (per §"Pre-step skip control" — the flag pair
     was designed for exactly this emergency-recovery case).
  3. **`git commit` the partial state** (the just-written
     proposed-change file plus any earlier seed-written files)
     so that the next invocation's `doctor-out-of-band-edits`
     check does not trip its pre-backfill guard. livespec does
     NOT write to git itself (per §"Git"); the commit is a user
     action. This step is load-bearing — without it,
     `doctor-out-of-band-edits` will refuse to proceed on the
     next invocation.
  4. Run `/livespec:revise --skip-pre-check` to process the
     proposed-change and cut `v002` with the corrections.
     (`v001` is the seed; `v002` is the first revision that
     makes the spec pass its own doctor-static.) Revise's
     post-step runs against the now-fixed state and passes.

  **Recovery-flow expectations (v017 Q4).** `--skip-pre-check`
  bypasses ONLY the pre-step, not the post-step. Propose-change
  in step 2 therefore runs its own post-step doctor-static
  against the still-broken project state (seed's fixes have
  not yet been applied at this point) and exits `3` with the
  SAME findings that tripped seed's post-step. This is the
  expected behavior in the sequential-lifecycle flow:
  propose-change's sub-command logic DID run (the
  proposed-change file IS on disk per §"Wrapper-side:
  deterministic lifecycle"), and the user proceeds to the
  commit-and-revise steps regardless of propose-change's
  exit code.

  `propose-change/SKILL.md` prose MUST narrate the exit-3
  path distinctly when the narrator can detect the
  seed-recovery-in-progress state (heuristic: no `vNNN`
  beyond `v001` exists AND pre-check was skipped); in that
  case the narration names step 3 (commit) + step 4 (revise)
  as the expected continuation. When that state cannot be
  detected, the generic exit-3 narration applies and the
  user is expected to recognize the recovery path from
  seed's earlier narration. The deferred entry
  `skill-md-prose-authoring` codifies the dual narration
  contract.

  Seed's idempotency refusal stays strict; there is no
  `--force-reseed` flag. Seed's SKILL.md prose MUST surface
  the recovery path in its post-step-failure narration,
  including the explicit git-commit step between
  propose-change and revise.

### `propose-change <topic> <intent>`

(The LLM consumes `<topic>` and `<intent>` from dialogue in
`propose-change/SKILL.md` prose; the wrapper
`bin/propose_change.py` itself takes `--findings-json <path>
<topic> [--author <id>]` where `<intent>` has already been
consumed into the JSON payload by the LLM invoking the
template's `prompts/propose-change.md`. The heading names the
user-facing dialogue interface; see §"Inputs" in the SKILL.md
body structure for the split.)

- Creates a new file
  `<spec-root>/proposed_changes/<canonical-topic>.md` containing
  one or more `## Proposal: <name>` sections (see
  "Proposed-change file format" below).
- **`bin/propose_change.py` accepts `--findings-json <path>`
  (required) and `--author <id>` (optional)**; it never invokes
  the template prompt or the LLM. The freeform `<intent>` path is
  driven by the LLM per `propose-change/SKILL.md`: the LLM invokes
  the active template's `prompts/propose-change.md`, captures the
  output, writes the JSON to a temp file, then invokes
  `bin/propose_change.py --findings-json <tempfile> <topic>
  [--author <id>]`. The wrapper validates the payload against the
  schema internally; on validation failure, it exits 4 with
  structured findings on stderr. The skill SHOULD interpret exit
  4 as a retryable malformed-payload signal and SHOULD re-invoke the
  template prompt with the error context; the exact retry count is
  intentionally unspecified in v1.
- **Topic canonicalization (v015 O3).** `bin/propose_change.py`
  treats the inbound `<topic>` as a user-facing topic hint, not
  yet the canonical artifact identifier. Before collision lookup,
  filename selection, or front-matter population, the wrapper
  canonicalizes the topic via: lowercase → replace every run of
  non-[a-z0-9] characters with a single hyphen → strip leading
  and trailing hyphens → truncate to 64 characters. If the result
  is empty, the wrapper exits 2 with `UsageError`. The
  canonicalized topic is used uniformly for the output filename,
  the proposed-change front-matter `topic` field, and the
  collision-disambiguation namespace. This applies to direct
  callers and to internal delegates such as `critique`.
- **Reserve-suffix canonicalization (v016 P3; PROPOSAL.md
  scope trimmed to invariants-only in v017 Q1).**
  `bin/propose_change.py` accepts an optional
  `--reserve-suffix <text>` flag (also exposed as a keyword-only
  parameter on the Python internal API path used by `critique`'s
  internal delegation). When supplied, canonicalization
  guarantees that the resulting topic is at most 64 characters
  AND that the caller-supplied suffix is preserved intact at
  the end of the result, even when the inbound hint already
  ends in that suffix (pre-attached case) or when truncation
  would otherwise clip the suffix. When `--reserve-suffix` is
  NOT supplied, canonicalization behaves exactly as v015 O3
  defined. The empty-after-canonicalization `UsageError` (exit
  2) continues to apply to the final composed result. The exact
  algorithm (pre-strip, truncate-and-hyphen-trim, re-append) is
  codified in `deferred-items.md`'s `static-check-semantics`
  entry; PROPOSAL.md deliberately does not duplicate the
  algorithm here (per the architecture-vs-mechanism discipline
  in `livespec-nlspec-spec.md` §"Architecture-Level
  Constraints").
- **Author identifier resolution.** The file-level `author` field
  in the resulting proposed-change front-matter is resolved by
  the unified precedence used across all three LLM-driven wrappers
  (`propose-change`, `critique`, `revise`):
  1. If `--author <id>` is passed on the CLI and non-empty, use
     its value.
  2. Otherwise, if the `LIVESPEC_AUTHOR_LLM` environment variable
     is set and non-empty, use its value.
  3. Otherwise, if the LLM self-declared an `author` field in the
     `proposal_findings.schema.json` payload (file-level, optional)
     and it is non-empty, use that value.
  4. Otherwise, use the literal `"unknown-llm"`.
  A warning is surfaced via LLM narration whenever fallback (4)
  is reached. The reserved `livespec-` prefix is a convention, not
  a mechanical reservation (see §"Proposed-change file format"):
  human authors and LLMs SHOULD NOT use the `livespec-` prefix,
  but no schema or wrapper rejects user-supplied `livespec-`
  values. The convention exists to preserve visual audit-trail
  disambiguation between skill-auto artifacts
  (`livespec-seed` / `livespec-doctor`) and user/LLM authorship.
- **Author identifier → filename slug transformation (v014 N5).**
  When the resolved `author` value is used as a filename
  component (the raw topic stem passed from `critique`, or any
  other author-derived filename use in the future),
  the wrapper transforms it via the following rule: lowercase
  → replace every run of non-[a-z0-9] characters with a single
  hyphen → strip leading and trailing hyphens → truncate to
  64 characters. The **slug form** is used as the filename
  component; the **original un-slugged value** is preserved in
  the YAML front-matter `author` / `author_human` / `author_llm`
  fields for audit-trail fidelity. The slug rule matches the
  GFM slug algorithm already used by the
  `anchor-reference-resolution` doctor-static check. This
  transformation applies whenever a resolved author value is used
  to derive a topic hint or filename component. Full semantics
  (edge cases, interaction with topic canonicalization, collision
  with already-slugged topic values) are codified in
  `deferred-items.md`'s `static-check-semantics` entry.
- The wrapper validates the JSON against
  `.claude-plugin/scripts/livespec/schemas/proposal_findings.schema.json` and
  maps each finding to one `## Proposal` section. The mapping is
  one-to-one field-copy:
  - finding `name` → `## Proposal: <name>` heading.
  - finding `target_spec_files` (array of strings) →
    `### Target specification files` (one path per line).
  - finding `summary` (string) → `### Summary` body.
  - finding `motivation` (string) → `### Motivation` body.
  - finding `proposed_changes` (string; prose or fenced diff) →
    `### Proposed Changes` body.
- **Note on two findings schemas.** `proposal_findings.schema.json`
  (this one) is distinct from `doctor_findings.schema.json` (the
  doctor static-phase output contract — see §"Static-phase output
  contract"). Doctor findings never route directly to
  `propose-change`; fixes surface via the LLM, which composes a
  proposal-findings payload as its input.
- External programmatic callers that already have structured
  findings JSON use the same `--findings-json <path>` flag
  directly without LLM mediation.
- Within-skill callers (e.g., `critique`) delegate to
  `propose_change`'s internal logic directly via Python imports,
  bypassing the LLM round-trip (see §"livespec skill sub-commands"
  on internal delegation).
- **Collision disambiguation (v014 N6).** If a file with topic
  `<canonical-topic>.md` already exists, the skill MUST auto-disambiguate
  by appending a hyphen-separated **monotonic integer suffix
  starting at `2`**: the first collision becomes
  `<canonical-topic>-2.md`, the second `<canonical-topic>-3.md`,
  and so on. No
  zero-padding is applied (so the tenth collision is
  `<canonical-topic>-10.md`; alphanumeric sort misordering past nine
  duplicates is accepted as an extreme edge case). No user
  prompt for collision. Starting the counter at `2` (not `1`)
  makes the "this is the second file named `<canonical-topic>`"
  relationship explicit; the first file is suffix-less by
  convention. Note: this convention applies to propose-change
  and critique filenames. The `out-of-band-edit-<UTC-seconds>.md`
  filename form used by the `doctor-out-of-band-edits` check
  is a separate always-appended UTC-timestamp convention (each
  backfill is a distinct timed event); the two conventions are
  not unified.
- The proposed-change file MUST conform to the format defined in
  "Proposed-change file format" below.
- A `## Proposal` MAY include an inline diff in its `### Proposed
  Changes` section. Diff format is unified diff (`---`/`+++`/
  `@@`). Paths in diff headers are relative to the repo root.

### `critique`

- The LLM (per `critique/SKILL.md`) invokes the active template's
  `prompts/critique.md`. The prompt MUST emit JSON conforming to
  the proposal-findings schema (skill-owned; under
  `.claude-plugin/scripts/livespec/schemas/proposal_findings.schema.json`).
- The LLM writes the JSON to a tempfile and invokes
  `bin/critique.py --findings-json <tempfile> [--author <id>]`.
  The wrapper validates the payload against the schema
  internally; on validation failure, it exits 4 with structured
  findings on stderr. The skill SHOULD interpret exit 4 as a
  retryable malformed-payload signal and SHOULD re-invoke the
  template prompt with error context; the exact retry count is
  intentionally unspecified in v1.
- **Author identifier resolution** uses the same unified
  precedence as §"propose-change → Author identifier resolution":
  1. CLI `--author <id>` if set and non-empty.
  2. Env var `LIVESPEC_AUTHOR_LLM` if set and non-empty.
  3. LLM self-declared `author` field in the
     `proposal_findings.schema.json` payload (file-level,
     optional) if present and non-empty.
  4. Literal `"unknown-llm"` fallback.
  The resolved author value is used both as the front-matter
  `author` field on the resulting proposed-change file and as
  the raw author stem supplied to `propose_change`'s internal
  canonicalization along with the reserve-suffix parameter
  `"-critique"` (v016 P3; see next bullet).
- `bin/critique.py` delegates internally to `propose_change`'s
  Python logic with topic hint `<resolved-author>` (the
  author stem only, without the `-critique` suffix) plus the
  reserve-suffix parameter set to `"-critique"` (v016 P3).
  `propose_change` then canonicalizes the composite via its
  reserve-suffix canonicalization (the invariants named
  above; the full algorithm is codified in
  `deferred-items.md`'s `static-check-semantics` entry per
  v017 Q1). Informally: a short author stem like
  `"Claude Opus 4.7"` combines to
  `"claude-opus-4-7-critique"`; a long stem is truncated on
  its non-suffix portion so the `-critique` suffix is
  preserved at the 64-char cap; a pre-attached `-critique`
  suffix in the hint does NOT double after canonicalization.
  The resulting canonicalized topic is used for filename,
  front-matter `topic`, and collision handling. Internal
  delegation skips the inner pre/post doctor cycle since the
  outer `critique` invocation's wrapper ROP chain already
  covers the whole operation.
- **Collision disambiguation (v014 N6).** If a file with topic
  equal to the resulting canonicalized critique topic already
  exists, the skill MUST auto-disambiguate using the same
  monotonic-counter-from-`2` convention documented in
  §"propose-change": e.g. `claude-opus-4-7-critique-2.md`,
  `claude-opus-4-7-critique-3.md`, and so on. No user prompt.
- Does not run `revise`; the user reviews and runs `revise` to
  process.

### `revise <revision-steering-intent>`

(The LLM consumes `<revision-steering-intent>` from dialogue
in `revise/SKILL.md` prose; the wrapper `bin/revise.py` itself
takes `--revise-json <path> [--author <id>]` where the steering
intent, if provided, has already been used by the LLM during
per-proposal decision-making and is not included in the JSON
payload at all. The heading names the user-facing dialogue
interface; see §"Inputs" in the SKILL.md body structure for
the split.)

- `<revision-steering-intent>` is OPTIONAL and, when provided,
  MUST only steer per-proposal decisions for the current revise
  invocation (e.g., "reject anything touching the auth section").
  It MUST NOT contain new spec content. If the user supplies
  content that expresses new intent rather than decision-steering,
  the skill MUST surface a warning and direct the user to run
  `propose-change` first. Detection is best-effort LLM judgment;
  on ambiguity, the skill proceeds with a visible warning.
- **`revise` MUST fail hard when `<spec-root>/proposed_changes/` contains no
  proposal files**, directing the user to run `propose-change`
  first. No auto-creation of ephemeral proposals.
- Files in `<spec-root>/proposed_changes/` are processed in **creation-time
  order** by YAML front-matter `created_at` (oldest first), with
  lexicographic filename as fallback on tie. Within each file,
  `## Proposal` sections are processed in document order (top to
  bottom).
- For each `## Proposal` in order, the LLM (invoked via the
  active template's `prompts/revise.md`) proposes an acceptance
  decision: `accept`, `modify`, or `reject`, with rationale.
- The user is presented with the per-proposal decision and MUST
  confirm or override before any history is written. At any
  point the user MAY toggle "delegate remaining proposals to
  the LLM"; once set, this toggle applies to **all remaining
  proposals across all remaining files** (whole-revise scope),
  and the skill auto-accepts/modifies/rejects them without
  further confirmation.
- On `modify`, the LLM drafts the modification; user iterates in
  dialogue to convergence, then confirms. Auto-handled when
  delegation is active.
- **`bin/revise.py` accepts `--revise-json <path>` (required) and
  `--author <id>` (optional)**; it never invokes the template
  prompt, the LLM, or the interactive confirmation dialogue. The
  LLM-driven per-proposal confirmation flow is entirely
  skill-prose-side (per `revise/SKILL.md`). Once every decision
  is confirmed, the LLM assembles a JSON payload conforming to
  `.claude-plugin/scripts/livespec/schemas/revise_input.schema.json`:
  ```json
  {
    "author": "<LLM self-declaration or 'unknown-llm'>",
    "decisions": [
      {
        "proposal_topic": "foo",
        "decision": "accept|modify|reject",
        "rationale": "...",
        "modifications": "...",
        "resulting_files": [
          {"path": "<template-declared spec file path>", "content": "..."}
        ]
      }
    ]
  }
  ```
  The optional file-level `author` field is the LLM's best-effort
  self-identification. The resolved author value (used for the
  revision-file front-matter `author_llm` field) follows the
  unified precedence: CLI `--author <id>` → env var
  `LIVESPEC_AUTHOR_LLM` → payload `author` field → `"unknown-llm"`
  fallback. The LLM writes the payload to a temp file and invokes
  `bin/revise.py --revise-json <tempfile> [--author <id>]`. The
  wrapper validates the payload against the schema internally;
  on validation failure, it exits 4 with structured findings on
  stderr. The skill SHOULD interpret exit 4 as a retryable
  malformed-payload signal and SHOULD re-assemble (or re-prompt)
  accordingly; the exact retry count is intentionally unspecified
  in v1.
- The wrapper reads the JSON and performs the deterministic
  file-shaping work:
  - If any decision is `accept` or `modify`, a new version `vN`
    is cut.
  - Working-spec files named in `resulting_files` are updated in
    place with the new content.
  - `<spec-root>/history/vN/` is created with copies of the active template's
    versioned spec files at this new version, including a
    per-version README only when the active template's versioned
    surface defines one.
  - A `<spec-root>/history/vN/proposed_changes/` subdirectory is created.
  - Each processed proposal file is moved
    **byte-identical** from `<spec-root>/proposed_changes/`
    into `<spec-root>/history/vN/proposed_changes/<stem>.md`,
    where `<stem>` is the proposed-change file's existing
    filename stem (which, under v014 N6 collision
    disambiguation, may include a `-N` suffix — e.g.,
    `foo.md`, `foo-2.md`, `foo-3.md`). Relative markdown
    links preserved.
  - Each processed proposal gets a paired revision at
    `<spec-root>/history/vN/proposed_changes/<stem>-revision.md`,
    using the SAME `<stem>` value as the proposed-change
    filename (`foo-2.md` → `foo-2-revision.md`). Conforms to
    the format defined in "Revision file format" below,
    populated from the decision's `rationale` and (for
    `modify`) `modifications` fields.
  - **Filename stem vs. front-matter `topic` distinction
    (v017 Q7).** Under collision disambiguation, the
    filename stem carries the `-N` suffix for disambiguation
    BUT the front-matter `topic` field (v015 O3 + v016 P4)
    carries the canonical topic WITHOUT the `-N` suffix.
    Every file sharing a canonical topic shares the same
    front-matter `topic` value; the filename-level `-N`
    suffix is how the filesystem distinguishes them.
    Revision-pairing (by doctor's
    `revision-to-proposed-change-pairing` check) walks
    filename stems, not front-matter `topic` values — for
    every `<stem>-revision.md`, the check verifies
    `<stem>.md` exists in the same directory.
- After successful completion, `<spec-root>/proposed_changes/`
  MUST be empty (of in-flight proposals; the skill-owned
  `proposed_changes/README.md` persists).

### `prune-history`

- Runs the pruning operation defined in the "Pruning history"
  section above.
- Accepts only the mutually-exclusive `--skip-pre-check` /
  `--run-pre-check` flag pair per §"Pre-step skip control"; no
  other arguments in v1. (v014 N8 corrects a prior wording that
  said "accepts no arguments", which contradicted the flag
  pair's applicability to every pre-step-having sub-command.)
- SKILL.md frontmatter MUST set `disable-model-invocation: true`
  (destructive operation; explicit invocation only).
- Post-step doctor static runs normally after pruning. No
  post-step LLM-driven phase.

### `doctor`

`doctor` runs in two phases:

- **Static phase** is implemented in Python. The orchestrator is
  at `.claude-plugin/scripts/livespec/doctor/run_static.py` and
  invoked via the shebang wrapper at `.claude-plugin/scripts/bin/doctor_static.py`.
  Each static check is a Python module at
  `.claude-plugin/scripts/livespec/doctor/static/<module>.py`.
- **LLM-driven phase** is skill behavior (prose in
  `doctor/SKILL.md`), not Python. It has no exit codes.

There is no `bin/doctor.py` wrapper; see §"Sub-command lifecycle
orchestration" → "Note on `bin/doctor.py`".

#### Static-phase structure

Each static check is a Python module at
`.claude-plugin/scripts/livespec/doctor/static/<module>.py`. Each check:

- Exports a `SLUG` constant (hyphenated string, e.g.,
  `"out-of-band-edits"`).
- Exports `run(ctx: DoctorContext) -> IOResult[Finding, E]` where
  `E` is any `LivespecError` subclass (a domain error). Bugs inside
  a check propagate as raised exceptions to the supervisor's
  bug-catcher (see `python-skill-script-style-requirements.md`
  §"Exit code contract" and `livespec-nlspec-spec.md` §"Error
  Handling Discipline").
- Has a corresponding `test_<module>.py` file under
  `tests/livespec/doctor/static/`.
- Runs on the Result / IOResult railway, short-circuiting on
  failure and producing a `fail` Finding for known-domain
  failures. The specific composition primitives (`flow`, `bind`,
  `.map`, `.lash`, etc.) are implementer choice under the
  architecture-level constraints (see `livespec-nlspec-spec.md`
  §"Architecture-Level Constraints").

The orchestrator `.claude-plugin/scripts/livespec/doctor/run_static.py`:

- Uses the **static registry** at
  `.claude-plugin/scripts/livespec/doctor/static/__init__.py`, which imports every
  check module by name and re-exports a tuple of `(SLUG, run)` pairs.
  Adding or removing a check is one explicit edit to the registry.
  No dynamic discovery; pyright strict can fully type-check the
  composition.
- **Iterates over every spec tree (v018 Q1; field-name
  finalized in v021 Q1)**. At startup the orchestrator
  enumerates `(spec_root, template_name)` pairs: the main spec
  tree first (template-name sentinel `"main"`), then each
  sub-spec tree under
  `<main-spec-root>/templates/<sub-name>/` discovered via
  directory listing. For each pair, the orchestrator builds a
  per-tree `DoctorContext` (with `spec_root` set to the tree's
  root and a new `template_name: str` field carrying the tree's
  template-name marker — `"main"` for the main spec tree, or
  the sub-spec directory name (e.g. `"livespec"`, `"minimal"`)
  for each sub-spec tree — used for per-tree applicability
  dispatch) and runs the applicable check subset.
- **Per-tree check applicability (v018 Q1).** Most checks run
  for every tree uniformly. The v1 exceptions:
  - `gherkin-blank-line-format` applies to the main spec tree
    when the main template is `livespec` (existing v014 N1
    rule), AND to the `livespec` sub-spec tree when one
    exists, BUT NOT to the `minimal` sub-spec tree (the
    `minimal` sub-spec's `scenarios.md` follows the minimal
    template's no-Gherkin convention).
  - `template-exists` and `template-files-present` are main-
    tree-only checks; they verify the currently-active
    main-spec template's own layout. Sub-spec trees do not
    re-run these (a sub-spec IS a spec tree, not a template
    payload).
  - Every other doctor-static check runs for every spec tree
    uniformly.
- Calls `module.run(ctx)` in-process for every registered
  check in every applicable tree.
- Composes all check results into one `IOResult[FindingsReport,
  E]` via the composition primitives from `dry-python/returns`.
  The specific primitive (e.g., `Fold.collect`, a reduce over
  `bind`, etc.) is implementer choice under the architecture-level
  constraints; what matters is that the composition is a single
  ROP chain and the final payload preserves both pass-and-fail
  findings plus domain-error short-circuits. Findings carry a
  `spec_root` field discriminating per-tree origin (main vs
  sub-spec path).
- `IOSuccess(finding)` (pass or fail finding) accumulates into
  the report; `IOFailure(err)` (internal bug) short-circuits.
- The supervisor in `main()` unwraps the final `IOResult`
  and emits `{"findings": [...]}` JSON to stdout. Each finding
  includes the `spec_root` field; the skill's LLM narration
  groups findings by `spec_root` so the user can tell which
  tree surfaced which issue.

The slug↔module-name mapping is recorded literally in the registry
(no hyphen-to-underscore conversion loop). User-facing `check_id`
values in JSON findings keep hyphens: `"doctor-out-of-band-edits"`.

#### Bootstrap lenience (v014 N3)

The orchestrator MUST construct `DoctorContext` with best-effort
defaults when `.livespec.jsonc` is absent, malformed, or
schema-invalid, so that the `livespec-jsonc-valid` check can
itself run and emit a fail Finding citing the specific failure.
Strict bootstrap (aborting before any check runs) would defeat
`livespec-jsonc-valid`'s purpose — the K10 fail-Finding
discipline (domain-meaningful failures → `IOSuccess(Finding
(status="fail", ...))`) applies UNIFORMLY, including to
bootstrap-critical inputs. The same discipline applies to
`template.json` → `template-exists`.

`DoctorContext` (see `python-skill-script-style-requirements.md`
§"Context dataclasses") gains the following fields:

- `config_load_status: Literal["ok", "absent", "malformed",
  "schema_invalid"]` (v014 N3)
- `template_load_status: Literal["ok", "absent", "malformed",
  "schema_invalid"]` (v014 N3)
- `template_name: str` (v018 Q1, field-name finalized in v021
  Q1) — `"main"` sentinel for the main spec tree, or the
  sub-spec directory name for each sub-spec tree; consumed by
  the orchestrator-owned applicability table for per-tree
  check dispatch (see preceding §"Static-phase orchestrator"
  prose).

The `config_load_status` / `template_load_status` fields
preserve the fallback reason for bootstrap-critical
checks to inspect. On `"ok"`, the check emits a pass Finding.
On `"absent"`, the check emits a skipped Finding ("no
`.livespec.jsonc` to validate"). On `"malformed"` or
`"schema_invalid"`, the check emits a fail Finding citing the
specific parse error or schema path. Full semantics (the
best-effort parse mechanism on malformed input; exact Finding
messages per status) are codified in `deferred-items.md`'s
`static-check-semantics` entry §"Orchestrator bootstrap
lenience".

Note: bootstrap lenience is a doctor-static-only discipline. The
non-doctor wrappers (`bin/seed.py`, `bin/propose_change.py`,
etc.) continue to fail-fast on malformed `.livespec.jsonc`
(exit 3 via `PreconditionError`); fixing the config is the
user's first step in non-doctor flows, while doctor-static
exists precisely to diagnose the broken state.

#### Static-phase output contract

The orchestrator writes structured JSON to stdout conforming to
`.claude-plugin/scripts/livespec/schemas/doctor_findings.schema.json` and returns
an exit code per the "Static-phase exit codes" table below. Output
shape:

```json
{
  "findings": [
    { "check_id": "doctor-version-contiguity", "status": "fail", "message": "...", "path": "<spec-root>/history", "line": null }
  ]
}
```

`check_id` takes the form `doctor-<slug>` where `<slug>` is the
hyphenated form matching the module filename's underscore form.
The `doctor-` prefix namespaces the ID so future check categories
don't collide.

Note: `doctor_findings.schema.json` is a DISTINCT schema from
`proposal_findings.schema.json` (the propose-change / critique
template-output schema). Doctor findings carry
`{check_id, status, message, path, line}`; proposal findings
carry `{name, target_spec_files, summary, motivation,
proposed_changes}`. Doctor findings never route directly to
`propose-change`; the LLM composes a proposal-findings payload
as its input when it wants to convert a doctor finding into a
proposal.

No human-readable output is produced on stdout; the skill's LLM
narrates the findings to the user from the JSON. Diagnostic text
MAY appear on stderr as structured JSON lines via `structlog`
(see `python-skill-script-style-requirements.md`).

#### Static-phase checks (exit `3` on any failure)

Each check below is implemented as one Python module at
`.claude-plugin/scripts/livespec/doctor/static/<module>.py`, registered statically
in `static/__init__.py`. The slug is the hyphenated form of the
module filename.

**Domain-failure-to-fail-Finding discipline.** Doctor-static checks
MUST map domain-meaningful failure modes (validation failure,
missing file, permission denied, etc.) to
`IOSuccess(Finding(status="fail", ...))` rather than
`IOFailure(err)`. The `IOFailure` track is reserved for unexpected
impure-boundary failures where the check itself cannot continue
(e.g., an I/O error reading `.livespec.jsonc` from disk, not a
validation error against its parsed content). Domain findings are
user-reportable via the Findings channel and map to exit `3` via
the "any fail finding" supervisor clause; `IOFailure` is short-
circuit-and-abort only. This preserves the invariant that
`bin/doctor_static.py` never emits exit `4` (which is reserved for
schema-validation failures on LLM-provided JSON payloads, a class
that cannot arise inside doctor-static). See
`deferred-items.md`'s `static-check-semantics` entry.

- **`livespec-jsonc-valid`** — `.livespec.jsonc`, if present,
  validates against its schema (`livespec_config.schema.json`) via
  `fastjsonschema` (factory-shape; `io/` reads the schema, `validate/`
  consumes the parsed dict).
- **`template-exists`** — The active template (built-in or at the
  configured path) exists and has the required layout
  (`template.json`, `prompts/`, `specification-template/`).
  `template.json`'s `template_format_version` matches
  `.livespec.jsonc`'s `template_format_version` and is supported
  by livespec. **v014 N4 widening:** the check ADDITIONALLY
  verifies that (a) all four REQUIRED prompt files exist as
  files inside `prompts/` (`seed.md`, `propose-change.md`,
  `revise.md`, `critique.md`); (b) when `template.json` declares
  `doctor_llm_objective_checks_prompt` or
  `doctor_llm_subjective_checks_prompt` as non-null, the
  declared path (resolved relative to the template root) exists
  as a file; (c) when `template.json` declares a non-empty
  `doctor_static_check_modules` list, each listed path exists as
  a file (deeper validity — module loads cleanly, exports
  `TEMPLATE_CHECKS` — is checked at doctor-static orchestrator
  load-time per C3 routing). On any failure, the finding MUST
  name the offending `template.json` field or missing-file
  path, its value, and the resolved template path.
- **`template-files-present`** — All template-required files
  (derived by walking the template's `specification-template/`
  directory) are present at their expected repo-root-relative
  paths.
- **`proposed-changes-and-history-dirs`** — `proposed_changes/` and
  `history/` directories exist under `<spec-root>/` (the template-
  declared spec root from `template.json`; default
  `"SPECIFICATION/"`) and contain their skill-owned `README.md`.
- **`version-directories-complete`** — Every `<spec-root>/history/vNNN/`
  directory that is not the pruned-marker directory contains the
  full set of template-required files, a `proposed_changes/`
  subdir, and — when the active template declares a versioned
  per-version `README.md` — a matching `README.md` (the built-in
  `livespec` template declares one; the built-in `minimal`
  template does not, per v014 N1 / v015 O2). The pruned-marker
  directory (the oldest surviving, when `PRUNED_HISTORY.json` is
  present) contains ONLY `PRUNED_HISTORY.json`.
- **`version-contiguity`** — Version numbers in
  `<spec-root>/history/` are contiguous from `pruned_range.end + 1`
  (if `PRUNED_HISTORY.json` exists at the oldest surviving `vN-1`
  directory) or from `v001` upward. Numeric parsing.
- **`revision-to-proposed-change-pairing`** — For every
  `<stem>-revision.md` in `<spec-root>/history/vNNN/proposed_changes/`,
  a corresponding `<stem>.md` exists in the same directory.
  Pairing walks filename stems (NOT front-matter `topic`
  values); under v014 N6 collision disambiguation, `<stem>`
  may include a `-N` suffix (e.g., `foo-2-revision.md` pairs
  with `foo-2.md`). See §"Proposed-change file format" →
  "Filename stem vs. front-matter `topic` distinction" for
  why stem-based pairing is the correct algorithm.
- **`proposed-change-topic-format`** — Every file in the working
  `<spec-root>/proposed_changes/` has a name conforming to
  `<topic>.md`.
- **`out-of-band-edits`** — Compares committed active spec state
  to committed history state at HEAD; backfills missing history
  when they diverge. Paths are all parameterized against
  `<spec-root>/` from `DoctorContext.spec_root`. Behavior:
  * **If the project is not a git repo:** skip this check with a
    JSON finding marked `status: "skipped"` (no committed state to
    compare).
  * **Pre-backfill guard — uncommitted prior backfill present.**
    Before running the comparison + backfill, the check inspects
    the working tree for either:
    1. A `<spec-root>/history/v(N+1)/` directory (whether
       committed at HEAD or only on disk), OR
    2. Any `<spec-root>/proposed_changes/out-of-band-edit-*.md`
       file.
    If either is present, the check emits a fail finding: "prior
    out-of-band-edit backfill is present but incomplete; commit
    the existing `history/v(N+1)/` and associated
    `out-of-band-edit-*.md` files, then re-run the original
    command." The check does NOT run the comparison or attempt
    another backfill. Under the workflow discipline of committing
    after every successful spec-writing operation, this state
    indicates the user skipped the commit step; refusing to
    proceed is the correct behavior.
  * **Comparison (both sides HEAD-committed).** Otherwise, the
    check diffs `git show HEAD:<spec-root>/<spec-file>` against
    `git show HEAD:<spec-root>/history/vN/<spec-file>` for each
    template-declared spec file. Both sides are HEAD-committed
    artifacts; working-tree WIP is ignored for the comparison.
  * **Backfill on drift.** If the diff is non-empty, the check
    auto-backfills. It creates
    `<spec-root>/proposed_changes/out-of-band-edit-<UTC-seconds>.md`
    containing one `## Proposal` with the diff as
    `### Proposed Changes`. It creates a paired revision in the
    corresponding location. It writes `<spec-root>/history/v(N+1)/`
    with the current HEAD-committed spec content. It then moves
    the proposed-change and revision into
    `<spec-root>/history/v(N+1)/proposed_changes/`. Author
    identifier: `livespec-doctor` (reserved skill-tool prefix).
    Check exits `3` with a finding instructing the user to commit
    the new `history/v(N+1)/` + backfill proposed-change files
    and re-run the original command.
- **`bcp14-keyword-wellformedness`** — Detects misspelled uppercase
  BCP 14 keywords and mixed-case BCP 14 keywords appearing as
  standalone words (`Must`, `Should`, `May`, etc.). Sentence-level
  context-dependent checks move to the LLM-driven phase (see
  below). The precise enumeration of detected misspellings is
  deferred to `deferred-items.md`'s `static-check-semantics`
  entry.
- **`gherkin-blank-line-format`** — **(Conditional: only when the
  active template is `livespec`.)** In `scenarios.md`, within any
  scenario block (from a `Scenario:` line through the next
  `Scenario:` or end-of-file), every line whose first
  non-whitespace token is a Gherkin keyword (`Scenario:`,
  `Given`, `When`, `Then`, `And`, `But`) MUST be preceded and
  followed by a blank line. Fenced code blocks containing Gherkin
  steps MUST NOT be present. Prose outside scenario blocks is
  unaffected. Fenced-block detection follows GFM conventions
  (triple-backtick or triple-tilde delimiters).
- **`anchor-reference-resolution`** — All Markdown links with
  anchor references resolve to existing headings in the
  referenced files. The walk set is the active template's
  declared spec file set, NOT an arbitrary `<spec-root>/`
  recursive glob. Specifically, the check inspects:
  - every template-declared spec file (resolved from the active
    template's `specification-template/` walk + the spec-root-
    relative paths),
  - the spec-root `README.md` when the template declares one
    (the built-in `livespec` template declares one; the built-in
    `minimal` template does not),
  - every file under `<spec-root>/proposed_changes/**`,
  - every file under `<spec-root>/history/**/proposed_changes/**`,
  - every per-version copy of each template-declared spec file
    under `<spec-root>/history/**/<spec-file>`.

  This scoping is deliberate: under the built-in `minimal`
  template's `spec_root: "./"`, the check does NOT walk the
  project's top-level `README.md`, `CONTRIBUTING.md`, source
  trees, `.github/`, or any other markdown that is not a
  template-declared spec artifact. The same walk-set semantic
  applies to any future doctor-static check that walks
  `<spec-root>/` recursively.

  Anchors are generated per GitHub-flavored Markdown (GFM)
  slug rules: the heading text is lowercased; internal
  whitespace is replaced with single hyphens; punctuation is
  stripped except `-` and `_`; multiple consecutive hyphens
  collapse to one. Headings inside fenced code blocks
  (`` ``` `` or `~~~`) are NOT considered headings. Explicit
  `{#custom-id}` syntax is NOT supported in v1. Edge-case
  details (case variations, non-ASCII headings, duplicate-
  heading disambiguation suffixes) and the exact walk
  algorithm are codified in `deferred-items.md`'s
  `static-check-semantics` entry.

#### Static-phase exit codes

- `0`: all checks pass; LLM-driven phase MAY proceed.
- `1`: script-internal failure (bug in `run_static` or any
  individual check); LLM-driven phase MUST NOT run; the invoking
  sub-command MUST abort.
- `3`: at least one check failed (input or precondition failed);
  LLM-driven phase MUST NOT run; the invoking sub-command MUST
  abort. NOT retryable via template re-prompt.
- `4`: schema-validation failure on an LLM-provided JSON payload
  (only emitted by non-doctor wrappers that validate input JSON;
  `bin/doctor_static.py` itself never emits `4` because it takes
  no JSON input). Retryable by re-prompting the template and
  re-assembling the JSON; see §"Per-sub-command SKILL.md body
  structure" → Retry-on-exit-4.

The supervisor derives the exit code as follows:

- On `IOFailure(HelpRequested(text))`: emit `text` to stdout; exit
  `0`. (`--help` is informational, not an error.)
- On `IOFailure(err)` where `err` is a `LivespecError` subclass:
  emit a structured-error JSON line on stderr via `structlog`,
  then exit `err.exit_code` (`2` for `UsageError`, `3` for
  `PreconditionError` / `GitUnavailableError`, `4` for
  `ValidationError`, `126` for `PermissionDeniedError`, `127` for
  `ToolMissingError`).
- On `IOSuccess(report)`: emit `{"findings": [...]}` to stdout,
  then exit `3` if any finding has `status: "fail"`, else exit
  `0`. `status: "skipped"` does NOT trigger a fail exit.

Exit-code semantics align with the companion
`python-skill-script-style-requirements.md` contract. Static
checks are pass-or-fail (or skipped) only. There is no warning
tier.

#### LLM-driven phase

The LLM-driven phase is skill behavior implemented in prose at
`doctor/SKILL.md`, not a script. It has no exit codes. The
doctor LLM-driven phase operates in two categories, both of which
are template-extensible via `template.json` declarations.

**LLM-driven objective checks.** Unambiguous pass/fail; non-
deterministic because the LLM is fallible (it may produce
inconsistent findings across runs, which is an LLM logic error
remediable by re-run or different model).

Skill-baked LLM-objective checks (always run unless skipped):

- Internal contradiction detection (section A says X, section B
  says not-X).
- Undefined term detection (a requirement references a term
  not defined anywhere).
- Dangling / unresolvable references that escaped the
  `anchor-reference-resolution` check (e.g., case-variant
  spellings).
- Spec↔history semantic drift (content moved between
  specification files without trace).
- BCP 14 case-inconsistency within a sentence (the deferred
  portion of the `bcp14-keyword-wellformedness` check).
- Gherkin step semantic validity (each step is actually a step,
  not prose).

Template-extension LLM-objective checks: if the active template's
`template.json` names a `doctor_llm_objective_checks_prompt`, the
skill reads that file (via `bin/resolve_template.py` and the Read
tool) and runs the template-defined checks immediately after the
skill-baked objective checks in the same LLM turn. Template owns
the check criteria entirely; any template-internal reference files
(e.g., `../livespec-nlspec-spec.md`) are read by the template's
prompt, not by the skill.

Skippability: `--skip-doctor-llm-objective-checks` and
`--run-doctor-llm-objective-checks` form a mutually exclusive
CLI flag pair (LLM-layer only — never passed to Python wrappers).
Precedence: CLI → config key
`post_step_skip_doctor_llm_objective_checks` → hardcoded default
`false`. Both flags present → argparse usage error (exit 2).

**LLM-driven subjective checks.** Ambiguous AND non-deterministic;
a "fail" finding may or may not be one the user wants to act on,
depending on intent and preference.

Skill-baked LLM-subjective checks (always run unless skipped):

- Spec↔implementation drift (comparing spec content to the
  surrounding repo's source code).
- Prose quality / structural suggestions.

Template-extension LLM-subjective checks: if the active template's
`template.json` names a `doctor_llm_subjective_checks_prompt`, the
skill reads that file and runs the template-defined checks. For
the built-in `livespec` template this prompt contains NLSpec-
conformance evaluation (economy, conceptual fidelity, spec
readability) and template-compliance semantic judgments (e.g.,
"contracts should go in contracts.md"); the prompt Reads
`../livespec-nlspec-spec.md` template-internally.

Skippability: `--skip-doctor-llm-subjective-checks` and
`--run-doctor-llm-subjective-checks` form a mutually exclusive
CLI flag pair (LLM-layer only). Precedence: CLI → config key
`post_step_skip_doctor_llm_subjective_checks` → hardcoded default
`false`. Both flags present → argparse usage error (exit 2).

For any finding surfaced in either LLM-driven category, the skill
prompts the user with a description and asks whether to address it
via a `critique` call. The user MAY accept (which invokes
`critique`), defer, or dismiss each finding individually. No cross-
invocation persistence of dismissals in v1.

**Narration rule** (applies to both flag pairs and mirrors the
pre-step narration discipline): the skill MUST surface a warning
via LLM narration whenever an LLM-driven phase is SILENTLY skipped
(config-driven, no CLI flag passed). When a `--skip-*` CLI flag
is passed explicitly, the skip is self-evident to the user and no
narration fires. When a `--run-*` CLI flag overrides a config
default of `true`, no narration fires — the explicit flag makes
the override self-evident.

---

## Proposed-change file format

A proposed-change file MUST contain, in order:

1. YAML front-matter (file-level):
   ```yaml
   ---
   topic: <kebab-case-topic>
   author: <author-id>                # LLM identifier, human handle, or reserved livespec-<tool>
   created_at: <UTC ISO-8601 seconds>
   ---
   ```

   The `topic` value is the wrapper-canonicalized kebab-case form
   of the inbound topic hint supplied to `propose-change`
   directly, delegated by `critique` (with reserve-suffix
   `"-critique"` per v016 P3), or assigned by a skill-auto-
   generated path (e.g., `seed` auto-capture uses `topic: seed`
   per §"seed"; `doctor-out-of-band-edits` backfill assigns a
   canonical value of its own choosing).

   **Single-canonicalization invariant (v016 P4).** The `topic`
   field's value MUST be derived via the same canonicalization
   rule across ALL creation paths — user-invoked
   `propose-change`, `critique`'s internal delegation (which
   adds the `-critique` reserve-suffix; see v016 P3), and
   skill-auto-generated artifacts (`seed` auto-capture,
   `doctor-out-of-band-edits` backfill). Implementations MUST
   route every `topic` derivation through a single shared
   canonicalization so two livespec implementations cannot
   diverge on the `topic` value for semantically-identical
   inputs. This is an architecture-level requirement on the
   interface; the exact code-path mechanism (single helper
   function vs. anything else) is an implementation choice.

   **Filename stem vs. front-matter `topic` distinction (v017
   Q7).** Under v014 N6 collision disambiguation, the
   proposed-change filename stem may include a `-N` suffix
   (`foo.md`, `foo-2.md`, `foo-3.md`). The front-matter
   `topic` field carries ONLY the canonical topic WITHOUT the
   `-N` suffix — every file sharing a canonical topic shares
   the same front-matter `topic` value. The `-N` suffix is
   filename-level disambiguation only. Revision-pairing (by
   `revision-to-proposed-change-pairing`) walks filename stems
   (not front-matter `topic` values); each
   `<stem>-revision.md` pairs with `<stem>.md` in the same
   directory.

   **Author-identifier namespace convention:** identifiers with
   the prefix `livespec-` (e.g., `livespec-seed`,
   `livespec-doctor`) are used by skill-auto-generated artifacts
   (seed auto-capture, doctor-`out-of-band-edits` backfill).
   Human authors and LLMs SHOULD NOT use this prefix for their
   own artifacts so that the audit trail can visually distinguish
   skill-auto artifacts from user/LLM-authored ones. This is a
   convention; no mechanical enforcement exists — no schema
   pattern rejects `livespec-`-prefixed values from user-supplied
   sources, and no wrapper rejects them on input. Users who
   deliberately type `livespec-`-prefixed identifiers create
   self-inflicted audit-trail confusion but nothing breaks.

   Front-matter is parsed by the restricted-YAML parser at
   `.claude-plugin/scripts/livespec/parse/front_matter.py` (deferred; see
   `deferred-items.md`). Format restrictions: values MUST be
   JSON-compatible scalars (strings, integers, booleans, `null`);
   no lists, no nested dicts, no anchors, no flow style. Unknown
   keys are a parse error. The parsed dict is validated against
   `proposed_change_front_matter.schema.json` via the factory-shape
   validator pattern. (A separate `revision_front_matter.schema.json`
   validates revision file front-matter — see "Revision file
   format" below; the two schemas have distinct shapes and are
   kept separate per the sum-type / conceptual-fidelity
   principle in `livespec-nlspec-spec.md`.)

2. One or more `## Proposal: <short-name>` sections, each with
   the following sub-headings in order:
   - `### Target specification files` — list of file paths
     (repo-root-relative) this proposal touches.
   - `### Summary` — one paragraph stating what changes and
     why.
   - `### Motivation` — the intent input that produced this
     proposal.
   - `### Proposed Changes` — prose describing the changes, or a
     unified diff in fenced ` ```diff ` blocks, or both.

Each `## Proposal` is independently evaluated by `revise`
(accept / modify / reject). A proposal MUST NOT contain nested
`## Proposal:` headings.

A proposal MUST be explicit about the intent it specifies. It
MUST NOT defer sub-decisions to `revise`; `revise`'s only
choice per proposal is accept / modify / reject. A
proposed-change file MUST NOT contain open questions,
alternatives, or "we should decide X later" content. If those
exist, resolve them before filing or file a separate `critique`.

---

## Revision file format

Each `<topic>-revision.md` in `<spec-root>/history/vNNN/proposed_changes/`
MUST contain, in order:

1. YAML front-matter:
   ```yaml
   ---
   proposal: <topic>.md
   decision: accept | modify | reject
   revised_at: <UTC ISO-8601 seconds>
   author_human: <git user.name and user.email from `git config`, or "unknown">
   author_llm: <resolved author id (CLI / env var / payload / "unknown-llm"), or the skill-auto convention value livespec-<tool>>
   ---
   ```

   `author_human` is populated by the `revise` / `seed` wrappers
   via `livespec.io.git.get_git_user()` (see §"Git"); the
   fallback is the literal `"unknown"` when git is available but
   either config value is unset.

   `author_llm` is populated by the unified precedence across
   all LLM-driven wrappers:
   (1) CLI `--author <id>` if passed and non-empty;
   (2) env var `LIVESPEC_AUTHOR_LLM` if set and non-empty;
   (3) the LLM's self-declared `author` field in the wrapper-input
   JSON payload if present and non-empty;
   (4) the literal `"unknown-llm"` fallback.
   For automated skill-tool-authored revisions (e.g., `seed` auto-
   capture, `out-of-band-edits` auto-backfill), `author_llm` takes
   the convention value `livespec-seed` / `livespec-doctor`,
   hardcoded by the wrapper and bypassing the precedence above.

   **Author-identifier namespace convention** applies here
   identically to §"Proposed-change file format": `livespec-`
   prefix is a SHOULD-NOT convention for user/LLM authorship (no
   mechanical enforcement; see §"Proposed-change file format").

   Same restricted-YAML parsing rules as proposed-change
   front-matter. The parsed dict is validated against
   `revision_front_matter.schema.json` via the factory-shape
   validator pattern.

2. `## Decision and Rationale` — one paragraph explaining the
   decision.
3. `## Modifications` (REQUIRED when `decision: modify`) — prose
   describing how the proposal was changed before incorporation.
   Unified diffs are NOT used here (line-number anchors are
   fragile across multi-proposal revises). Optional short fenced
   before/after excerpts are permitted for hyper-local clarity.
4. `## Resulting Changes` (REQUIRED when `decision: accept` or
   `modify`) — names the specification files modified and lists
   the sections changed.
5. `## Rejection Notes` (REQUIRED when `decision: reject`) —
   explains what would need to change about the proposal for it
   to be acceptable in a future revision.

Note: historical versions of this format used the term
`acknowledgement`. That term is retired in favor of `revision`,
which better captures the role of the file (the outcome of a
revise decision) and matches the command name.

---

## Test-Driven Development discipline

livespec is developed under strict Test-Driven Development per
Kent Beck's Red-Green-Refactor canon. The discipline applies
to every covered-code change from the first Python module
onward; what activates at the v033-codification commit is the
*mechanical enforcement gate* (lefthook + 100% per-file
coverage + mirror-pairing + commit-pair source-and-test +
`## Red output` block — all hard gates per v033 D1-D5),
NOT the discipline itself. Authoring rhythm is upstream of gate
activation: a module authored without a failing test driving
each behavior produces covered code, not designed code, and
the coverage gate cannot detect the difference. v032 closed
the prior temporal carve-out that read this section as
permitting pre-Phase-5-exit characterization-style authoring;
v033 then closes the residual gap discovered in v032's first
retroactive-redo attempt (cycles 1-56 reached "integration-
test-green" parity but produced zero unit tests under
`tests/livespec/**`). See Plan Phase 5 §"Retroactive TDD redo
of Phase 3 + Phase 4 work — second attempt (v033 D5b)" for
the one-time mechanism that brings the pre-v033 codebase
under the discipline plus the four mechanical guardrails
that prevent the first-redo failure mode from recurring.

### Authoring rhythm vs. commit boundaries

Red-Green-Refactor is the **authoring rhythm** — the order in
which an author works in their editor. It is NOT a commit
rhythm. Commits represent **cohesive units of user-facing
value delivered**, not phases of an internal authoring cycle.
Two distinct kinds of commit follow from this:

1. **Feature / bugfix commit** = the Red-Green pair, atomically.
   The test was Red during authoring (the author wrote it
   first, ran it, and observed it fail for the right reason);
   the implementation that follows turns it Green; the commit
   captures both together as one unit. At commit time
   everything is green and the per-commit gate passes.
   Committing a Red failing test by itself would (a) fail
   the per-commit gate (broken-tests / sub-100%-coverage
   rejects the commit), and (b) deliver no user-facing value;
   the project does not allow it.
2. **Refactor commit** = behavior-preserving restructuring,
   committed independently. A refactor does NOT involve
   writing a new failing test; the existing tests stay green
   throughout and prove the refactor preserves behavior. A
   refactor MAY backfill missing tests for code that is about
   to be restructured (characterization tests that pin down
   current behavior so the refactor is auditable); those
   tests pass against the pre-refactor implementation, then
   continue to pass against the restructured code. The
   refactor lands as its own commit because it is its own
   unit of value (improved structure with same behavior); it
   is reviewable on its own terms, separate from any feature
   work.

### The internal authoring cycle (Red → Green)

For every change to a covered code file (any `.py` file under
`.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, or `<repo-root>/dev-tooling/**`)
that introduces new behavior:

1. **Red.** Write the smallest failing test that names the
   behavior the change introduces or the bug the change fixes.
   The test MUST execute end-to-end and MUST fail for the
   *right reason* — the assertion fails because the desired
   behavior is missing, NOT because of a SyntaxError, an
   ImportError, a missing fixture, or a typo in the test
   itself. If the test fails for any other reason, fix the
   test until the failure mode is "the implementation does
   not yet do X" before proceeding. Run the test (`uv run
   pytest <test_file>::<test_name>`) and observe the failing
   output; the failure message is what justifies the
   implementation that follows. (Red lives in the editor.
   It does NOT get committed in isolation.)
2. **Green.** Write the *minimum* implementation that turns
   the failing test green. "Minimum" is taken seriously: do
   not add functionality the test does not exercise; do not
   anticipate the next test; do not pre-factor for shape that
   is not yet pressured by a failing assertion. Re-run the
   test and observe it pass. Run the full suite
   (`just check-tests`) to confirm no regression. Once the
   full suite is green and coverage is at 100%, the
   Red-Green pair commits together as the feature/bugfix
   unit of value.

   Per v034 D2-D3, the commit boundary uses the
   **amend-and-add-trailers** pattern. Concretely: the Red
   moment lands as an initial commit with `feat:` or `fix:`
   subject, the failing test in the staged tree, and the
   pre-commit hook (`check-red-green-replay`) verifying the
   test fails before letting the commit land. The Green
   amend re-stages the implementation alongside the test
   (test file content unchanged); `git commit --amend`
   triggers the same hook, which now verifies the test
   passes and adds the `TDD-Green-Verified-At:` and
   `TDD-Green-Parent-Reflog:` trailers. The post-amend
   single commit carries both Red and Green trailers,
   structurally proving the temporal order via reflog. See
   §"Testing approach — Activation" for the full trailer
   schema and hook contract.

### The independent refactor cycle

Refactor is a separate kind of work, not the third phase of
the Red-Green cycle. A refactor commit:

- Starts with the suite green (existing tests cover the
  pre-refactor behavior).
- MAY first backfill characterization tests if the existing
  coverage has gaps — write tests that pin down current
  behavior, run them against the pre-refactor code, observe
  them PASS (they are NOT Red — current code already does
  the thing the test asserts). The point of these tests is
  to safety-net the impending refactor, not to drive new
  behavior.
- Restructures the implementation (and possibly tests, if
  their shape benefits from cleanup) to remove duplication,
  clarify naming, align with the architectural rules in
  `python-skill-script-style-requirements.md`, or otherwise
  improve structure without changing behavior.
- Keeps tests green throughout; if a test goes red during
  the refactor, that is a signal that behavior changed
  (deliberately or accidentally) and the refactor has stopped
  being a refactor. Either back it out and reapply as a
  separate Red-Green-driven feature change, or scope the
  characterization-test backfill more carefully and try
  again.
- Commits as its own unit of value with a refactor-shaped
  commit message (e.g., `refactor: extract X helper from Y`;
  `refactor: rename Z to clarify intent`). Refactor commits
  are reviewable independently of any feature work.

### Failing for the right reason

A test that fails because the assertion expectation is wrong
is a useful Red. A test that fails because of a SyntaxError
in the test, an ImportError caused by a missing module, a
missing fixture, or a typo in the test name is NOT a useful
Red — it tells the author nothing about the behavior under
test. Before writing the implementation:

- Run the failing test in isolation. Read the failure message.
- Confirm the failure message names the *missing behavior*
  (e.g., `AssertionError: expected 7, got 0` because the
  function returns a stub `0`).
- If the failure message names something else (e.g.,
  `ModuleNotFoundError`, `NameError`, `TypeError: f() missing
  1 required positional argument`), the test is not yet at
  Red. Fix the test until its failure mode reflects the
  behavior gap, then proceed to Green.

This applies recursively: a fix to a Red test that exposes a
new failure mode is itself a tiny test-first cycle on the
test authoring (the test author iterates the test until its
failure mode is the behavior gap, then proceeds to Green).

### Legitimate exceptions to test-first

The test-first discipline applies to every change that
introduces new behavior in executable code. The following
narrow categories are exempt from the test-first requirement
(but NOT from the 100% coverage gate post-commit) because
they introduce no new behavior:

- **Pure refactors** that change structure without changing
  behavior. Refactors are not "exempt" from TDD per se —
  they are a separate kind of work entirely (see §"The
  independent refactor cycle" above). The existing tests
  prove the refactor is behavior-preserving; no new failing
  test is authored as part of a refactor. If a refactor
  surfaces new behavior, that behavior is no longer a
  refactor and falls back into the test-first Red-Green
  workflow.
- **Type-only changes** (adding/removing annotations,
  introducing or renaming a `NewType` alias, switching a
  field from `str` to a more specific NewType). Type
  declarations have no runtime behavior to test directly;
  type correctness is verified by `check-types` (Phase-7
  active). The covering tests for the existing runtime
  behavior continue to pass.
- **Documentation-only changes** to `CLAUDE.md`, docstrings,
  comments, prose-only sections of `SPECIFICATION/`, or
  spec markdown files. No executable code is changed.
- **Configuration-only changes** to `pyproject.toml`,
  `justfile`, `lefthook.yml`, `.mise.toml`, `.vendor.jsonc`,
  YAML/TOML/JSON config files where the change does not
  alter Python execution semantics. (A `pyproject.toml`
  change that, e.g., adds a new ruff rule whose violations
  surface in covered code IS a behavior change in the
  enforcement surface and reapplies test-first — the
  failing-rule output is the Red signal that drives the
  follow-up fix as Green.)
- **Mechanical migrations** (renames via grep, file moves
  preserving content, mass-import-rewrites). The existing
  tests follow the rename and continue to pass; no new
  behavior is introduced.

The exception list is exhaustive. Anything outside it that
introduces new behavior follows the test-first Red-Green
workflow. "I couldn't think of a failing test smaller than
the implementation" is NOT an exception — it usually
indicates the implementation is being written too large;
the remedy is to take a smaller step, not to skip Red.

### Why this discipline (not just the coverage gate)

The 100% line+branch coverage gate at every commit (per
§"Testing approach") catches the common failure mode where
a line is added without any test exercising it. It does NOT
catch:

- Tests written *after* the implementation, which tend to
  encode whatever the implementation happens to do rather
  than what the design called for ("change-detector tests").
- Implementations that overshoot the actual requirement
  because the author was not constrained by a specific
  failing test.
- Tests whose execution covers a line but whose assertions
  do not actually verify behavior (the line-coverage tracer
  registers execution; assertion strength is invisible to
  it).

The Red-Green authoring rhythm addresses all three by
construction: the Red test names the desired behavior in
the form of an executable assertion *before* the
implementation exists; the Green implementation is bounded
by what makes the Red turn green; the test stays green from
that moment on. Refactor — committed separately as its own
unit of value — preserves the green by construction (no new
failing tests; characterization tests if needed pass against
the pre-refactor code). Mutation testing (release-gate per
v013 M3, separate from this gate) is the deeper rigor that
catches assertion-strength gaps; v1's per-commit gate stays
at line+branch for speed, with the test-first discipline as
the upstream forcing function for assertion quality.

### Test pyramid

The 100% coverage gate is satisfied by the **bottom of the
test pyramid** — pure unit tests under `tests/livespec/`,
`tests/bin/`, and `tests/dev-tooling/checks/`. These tests
are fast, isolated, and exercise the implementation directly
(no LLM-in-the-loop, no real `git`, no Claude Agent SDK).
The integration and prompt-QA layers above the unit layer
(`tests/e2e/`, `tests/prompts/`) provide additional
confidence but do NOT contribute to the 100% gate — their
test execution paths overlap the unit-layer paths but are
slower, more setup-dependent, and less suitable as a
per-commit forcing function.

`pyproject.toml`'s `[tool.coverage.run].source` enumerates
exactly the three implementation trees (`livespec/`, `bin/`,
`dev-tooling/`) so coverage measurement is anchored at the
unit-test target, not at the integration or prompt-QA
layers.

---

## Testing approach

Tests for the `livespec` skill live at the skill-repo root under
`tests/` (a sibling of `.claude-plugin/`). Tests of a user's own
SPECIFICATION are out of scope for livespec.

Test runner and tooling:

- Test runner is **`pytest`**. Test files use the `.py`
  extension and the `test_` filename prefix.
- Required pytest plugins: `pytest-cov` (coverage integration)
  and `pytest-icdiff` (structured failure diffs that surface
  usefully in the LLM's context). No other plugins.
- Test-local filesystem state uses pytest's `tmp_path` fixture.
  Filesystem fixtures live under `tests/fixtures/` (tests MUST
  NOT mutate them).
- Stubbing impure wrappers uses pytest's `monkeypatch` fixture.
- Coverage is measured by **`coverage.py`** via `pytest-cov`.
  The 100% line+branch gate is the mechanical forcing
  function for §"Test-Driven Development discipline" — read
  that section first; the coverage rule below is the
  per-commit verification that the discipline was followed.
  Coverage MUST be 100% line + branch across all Python files
  under `.claude-plugin/scripts/livespec/**`,
  `.claude-plugin/scripts/bin/**` (per v010 J8 / v011 K3 —
  including `_bootstrap.py` and the wrapper bodies, with
  wrapper coverage achieved via dedicated
  `tests/bin/test_<cmd>.py` files per K3, NOT via pragma
  exclusions), and `<repo-root>/dev-tooling/**`. v033 D2
  tightens this: coverage is measured **per-file** at 100%
  (not just total) — the existing `[tool.coverage.report].
  fail_under = 100` total threshold is preserved as a
  belt-and-braces guard, but the authoritative gate is
  `dev-tooling/checks/per_file_coverage.py` which fails the
  first time any single file falls below 100% line OR 100%
  branch. Vendored third-party libraries under
  `.claude-plugin/scripts/_vendor/` are excluded from the
  coverage measurement (they are pinned and audited via the
  discipline in §"Dependencies — Runtime"; no automated audit
  script). See the companion
  `python-skill-script-style-requirements.md` for the full
  coverage contract (100% per-file line+branch; no line-level
  pragma escape hatch). Note: v012 L13 mutation testing is a
  SEPARATE release-gate measurement; the line+branch coverage
  rule above remains the per-commit gate. The rule is a HARD
  constraint per §"Test-Driven Development discipline": no
  `# pragma: no cover` annotation is permitted in covered
  code; the only structural exclusions are
  `if TYPE_CHECKING:`, `raise NotImplementedError`,
  `@overload`, and `case _:` blocks via
  `[tool.coverage.report].exclude_also`. The fourth pattern
  (`case _:`) reflects the universal
  `case _: assert_never(<subject>)` mandate at companion
  style-doc lines 1054-1066 plus the AST-level enforcement
  at `dev-tooling/checks/assert_never_exhaustiveness.py`:
  every `case _:` arm in the codebase is the
  structurally-unreachable assert-never sentinel, and
  coverage.py's compound-statement exclusion rule excludes
  the arm body (`assert_never(<subject>)`) in the same
  sweep as the `case _:` line.

**Activation.** The hard-constraint pre-commit gate
(`just check-coverage` at 100% line+branch **per-file** per
v033 D2, plus the rest of `just check`, plus the v034 D3
Red→Green replay verification) becomes binding at the
moment lefthook is installed into `.git/hooks/`. Per
v033 D5a this happens at the v033-codification-commit
boundary (one commit + the four guardrail-script commits
authoring D1-D4 + the `just bootstrap` promotion + the
`lefthook install` invocation). The earlier framing
("Phase-5-exit lefthook activation") is closed at v033;
moving the activation forward eliminates the discipline-
gap window during which v032's first redo authored 56
cycles of impl-first-style work without commit-time
mirror-pairing or per-file-coverage enforcement. Pre-v033-
codification-commit commits are grandfathered (they precede
the new guardrails). From the v033-codification commit
onward, no commit lands without passing the per-commit
gate; the Phase 6 first self-application seed is the first
working commit subject to the discipline at full
specification-driven strength.

**v034 D2-D3 Red→Green replay contract.** The v033 D4
honor-system rule (commit body must contain a `## Red
output` heading + fenced pytest block) is superseded at the
v034-codification boundary by a structured trailer schema +
mechanical replay verification. The `commit-msg` hook
(`dev-tooling/checks/red_green_replay.py`, replacing the
v033 `red_output_in_commit.py`) operates in two modes,
distinguished by inspecting `HEAD~0`'s commit message:

1. **Red mode (initial commit).** Triggered when the staged
   tree carries test files but no implementation files AND
   the subject line is `feat:` or `fix:`. Hook computes the
   test file's SHA-256, runs the listed test (extracted
   from a candidate `TDD-Red-Test:` trailer or from the
   commit body's `## Red output` block), expects non-zero
   exit code with the test's pytest node-id appearing in
   the failure summary. On success, hook writes the Red
   trailers into the commit message via `git
   interpret-trailers --in-place` and lets the commit land.

   **Per-file constraint (v035 D4).** Red mode is per-file:
   exactly one test file must be staged. If multiple test
   files are staged, the hook rejects with a structured
   `red-green-replay-multi-test-file` diagnostic and skips
   checksum computation. The constraint follows from the
   singular `TDD-Red-Test-File-Checksum:` trailer in
   §"Trailer schema" below; staging multiple test files in
   a single Red commit produces ambiguity the schema cannot
   represent.

2. **Green mode (amend).** Triggered when `HEAD~0`'s
   message carries Red trailers and the new staged tree
   adds implementation files. Hook recomputes the test
   file's SHA-256 from the staged tree; rejects if it
   differs from `TDD-Red-Test-File-Checksum`. Runs the
   listed test; expects exit zero. Adds
   `TDD-Green-Verified-At:` and `TDD-Green-Parent-Reflog:`
   trailers (the latter pinning the pre-amend HEAD SHA so
   the temporal order is reflog-verifiable). On any
   mismatch — wrong checksum, test still fails, missing
   parent in reflog — the amend is rejected.

**Trailer schema.** The full set, all required on `feat:`
and `fix:` commits at the Green amend boundary:

```
TDD-Red-Test: <pytest-node-id>
TDD-Red-Failure-Reason: <one-line failure summary>
TDD-Red-Test-File-Checksum: sha256:<hex>
TDD-Red-Output-Checksum: sha256:<hex>
TDD-Red-Captured-At: <UTC ISO 8601>
TDD-Green-Verified-At: <UTC ISO 8601>
TDD-Green-Parent-Reflog: <pre-amend SHA>
```

The captured pytest failure output continues to live in the
commit body as a fenced `## Red output` block (preserved for
human readability via `git log`); `TDD-Red-Output-Checksum`
is the SHA-256 of that block, allowing the hook to detect
tamper without parsing pytest's volatile formatting (which
includes timestamps, paths, and version-specific layout).
`TDD-Red-Test-File-Checksum` is the SHA-256 of the test
file's content as it was at the Red moment.

**Failure-mode quality (90% heuristic).** "Test failed for
the right reason" (assertion vs. ImportError/SyntaxError) is
hard to mechanize fully. The hook applies a 90% heuristic:
uses `pytest --collect-only` to detect collection-time
errors (rejected as "test not at Red — fix collection
first"); accepts any non-zero pytest exit code where the
test's node-id appears in the short summary. Edge cases
(test errors mid-body via `RuntimeError` rather than
`AssertionError`) are accepted; mutation testing
(`check-mutation`, release-gate) catches the residual
"tests are vacuous" case.

**Anti-cheat.** A bad actor could attempt to skip the Red
moment and produce a single commit with hand-faked
trailers. The hook rejects this via reflog inspection: if
`TDD-Green-Parent-Reflog` references a SHA that either
(a) does not appear in the local reflog, or (b) appears but
does not carry a Red marker + matching checksum, the
commit is rejected. Reflog is local-only and not pushed, so
server-side verification falls back to mutation testing as
a vacuity check; local enforcement is mechanically airtight
for any commit authored on a development machine running
the hook.

**v034 D3 implementation status (per v035 D3): reflog-
inspection deferred.** The reflog-inspection mechanism
described above is deferred to post-v1.0.0 hardening. The
`dev-tooling/checks/red_green_replay.py` hook captures the
parent SHA via `git rev-parse HEAD` and writes the
`TDD-Green-Parent-Reflog` trailer, but does NOT verify the
SHA's presence in the reflog or inspect its trailers for a
Red marker + matching checksum. The local Red→Green amend
pattern is mechanically airtight for honest workflows; bad-
actor protection via reflog inspection is not load-bearing
for the v034 D7 drain (which operates locally with the
developer following discipline) or for Phase 6+ self-
application work. Post-v1.0.0 hardening can revisit if
warranted (e.g., for hosted-CI verification of remote
contributor commits).

**Required-vs-skipped by commit type.**

| Type | Trailers required? |
|---|---|
| `feat`, `fix` | Yes (full schema mandatory) |
| `refactor`, `perf` | No (must NOT add new failing tests) |
| `chore`, `docs`, `build`, `ci`, `style`, `test` | No (config/meta) |
| `revert` | No (mirrors reverted commit's type) |

Directory structure (mirrors the implementation trees 1:1,
including subdirectories):

```
tests/
├── CLAUDE.md                                 (enforces test/spec consistency; see below)
├── heading-coverage.json                     (meta-test registry; see below)
├── fixtures/                                 (explicit test fixtures; MUST NOT be mutated by tests)
├── bin/                                      (mirrors scripts/bin/)
│   ├── test_bootstrap.py                     (covers bin/_bootstrap.py)
│   ├── test_wrappers.py                      (meta-test: all wrappers match the 6-statement shape)
│   ├── test_seed.py                          (per-wrapper coverage via pytest.raises(SystemExit) + monkeypatch of main)
│   ├── test_propose_change.py
│   ├── test_critique.py
│   ├── test_revise.py
│   ├── test_doctor_static.py
│   ├── test_resolve_template.py
│   └── test_prune_history.py
├── livespec/                                 (mirrors .claude-plugin/scripts/livespec/)
│   ├── commands/
│   │   ├── test_seed.py
│   │   ├── test_propose_change.py
│   │   └── ...
│   ├── doctor/
│   │   ├── test_run_static.py
│   │   └── static/                           (one test_*.py per static-check module)
│   │       ├── test_livespec_jsonc_valid.py
│   │       ├── test_template_exists.py
│   │       ├── ...
│   │       └── test_anchor_reference_resolution.py
│   ├── io/
│   │   └── test_fs.py
│   ├── parse/
│   │   ├── test_jsonc.py
│   │   └── test_front_matter.py
│   ├── validate/
│   │   └── ...
│   ├── schemas/
│   │   └── dataclasses/                    (per v011 K11 — Finding + pass_finding/fail_finding tests)
│   │       ├── test_finding.py
│   │       ├── test_doctor_findings.py
│   │       └── ...
│   └── ...
├── dev-tooling/                              (mirrors <repo-root>/dev-tooling/)
│   └── checks/                               (one test_*.py per enforcement script; note: no test_purity.py / test_import_graph.py — those were replaced by Import-Linter per v012 L15a)
│       ├── test_private_calls.py
│       ├── test_supervisor_discipline.py
│       └── ...
├── e2e/                                      (v014 N9 end-to-end integration test)
│   ├── CLAUDE.md                             (notes the E2E test's harness-mode env-var + delimiter-comment dependency)
│   ├── fake_claude.py                        (livespec-authored API-compatible pass-through mock of the Claude Agent SDK; drives wrappers deterministically via delimiter comments in the minimal template's prompts)
│   ├── fixtures/                             (tmp_path-template fixtures for happy path + 3 error paths; fresh-repo + pre-seeded variants)
│   └── test_*.py                             (common pytest suite for mock + real harness modes; env var LIVESPEC_E2E_HARNESS=mock|real selects executable; mock-only cases use pytest markers/skipifs)
├── prompts/                                  (v018 Q5 prompt-QA tier — per-prompt verification)
│   ├── CLAUDE.md                             (notes the prompt-QA harness conventions + assertion-type split; distinct from tests/e2e/fake_claude.py scope)
│   ├── livespec/                             (prompt-QA tests for the livespec built-in template's REQUIRED prompts)
│   │   ├── test_seed.py                      (≥ 1 case: schema-valid payload + semantic properties per seed-prompt intent)
│   │   ├── test_propose_change.py
│   │   ├── test_revise.py
│   │   └── test_critique.py
│   └── minimal/                              (prompt-QA tests for the minimal built-in template's REQUIRED prompts)
│       ├── test_seed.py
│       ├── test_propose_change.py
│       ├── test_revise.py
│       └── test_critique.py
└── test_*.py                                 (per-specification-file rule-coverage tests)
```

Test organization rules:

- `tests/livespec/` mirrors `.claude-plugin/scripts/livespec/`
  one-to-one, preserving subdirectory structure.
  `tests/dev-tooling/` mirrors `<repo-root>/dev-tooling/` the same
  way. `tests/bin/` mirrors `.claude-plugin/scripts/bin/`. Adding a module anywhere
  under those trees requires adding the corresponding test file at the
  mirrored path. The 1:1 mirror rule is mechanically enforced by
  `dev-tooling/checks/tests_mirror_pairing.py` per v033 D1 —
  every covered `.py` file under `livespec/`, `bin/`, and
  `dev-tooling/checks/` MUST have a paired `tests/<mirror>/test_<name>.py`
  containing at least one `def test_*` function. The check's
  closed exemption set: `_vendor/**`, `bin/_bootstrap.py`
  (covered by the preserved `tests/bin/test_bootstrap.py`),
  and `__init__.py` files containing only `from __future__ import
  annotations` + `__all__: list[str] = []` (with no executable
  logic). Empty paired files or paired files containing only
  fixtures/helpers fail the check.
- **Leading-underscore source modules.** Source modules whose
  filename begins with `_` (e.g., `_bootstrap.py`) use a test
  filename that strips the leading underscore:
  `_<name>.py` → `test_<name>.py` (NOT `test__<name>.py`).
  This matches pytest's idiomatic `test_`-prefix convention and
  avoids double-underscore visual noise.
- **Per-module tests** (under `tests/livespec/`,
  `tests/dev-tooling/`, `tests/bin/`) exercise a module's **contract**:
  function signatures, Result/IOResult shapes, input validation,
  error paths, individual helper functions.
- **Per-spec-file tests** (`tests/test_spec.py`,
  `tests/test_contracts.py`, `tests/test_constraints.py`,
  `tests/test_scenarios.py`) exercise **rules stated in a
  specification file** end-to-end, invoking whatever module(s)
  implement the rule. These are the tests referenced by
  `heading-coverage.json`; per-module tests are not required to
  appear in the registry.
- A `tests/CLAUDE.md` MUST exist to enforce consistency between
  tests and the actual specification (instructing the LLM that
  test coverage tracks specification files, not implementation
  files).
- A `CLAUDE.md` MUST exist at every directory level under `tests/`
  mirroring the `scripts/` tree's CLAUDE.md discipline (see
  `python-skill-script-style-requirements.md`).
- Each test MUST execute the skill against fixtures in a
  throwaway temporary directory (via `tmp_path`) and compare
  results to expected outputs. The test runner MUST NOT mutate
  the project's own `SPECIFICATION/`.
- A meta-test, `test_meta_section_drift_prevention.py`, MUST
  verify that every top-level (`##`) heading in each
  specification file has at least one corresponding per-spec-file
  test case in the coverage registry. The meta-test walks
  every spec tree (main `SPECIFICATION/` + every sub-spec under
  `SPECIFICATION/templates/<name>/` per v018 Q1); each
  `(spec_root, spec_file, heading)` triple must have a
  registry entry. The meta-test SKIPS any `##` heading whose
  text begins with the literal `Scenario:` prefix (scenario
  blocks are exercised end-to-end by the per-spec-file rule
  test for the scenario-carrying spec file; per-scenario
  registry entries are not required).
- **Coverage registry**: `tests/heading-coverage.json` maps
  `(spec_root, spec_file, heading)` triples to test
  identifiers (the `spec_root` field was added in v018 Q1 to
  disambiguate heading-text collisions across trees —
  main-spec headings vs per-sub-spec headings):
  ```json
  [
    { "spec_root": "SPECIFICATION", "spec_file": "spec.md", "heading": "Proposed-change file format", "test": "test_propose_change.py::test_multi_proposal_write" },
    { "spec_root": "SPECIFICATION/templates/livespec", "spec_file": "spec.md", "heading": "Seed-prompt interview flow", "test": "TODO", "reason": "sub-spec content authored via Phase-7 propose-change against SPECIFICATION/templates/livespec; test pending" },
    { "spec_root": "SPECIFICATION", "spec_file": "spec.md", "heading": "Foo rule", "test": "TODO", "reason": "rule added in v015; implementation and test pending" }
  ]
  ```
  The `spec_root` field is the repo-root-relative path to the
  root of the spec tree carrying the heading (main spec =
  `SPECIFICATION`; sub-spec =
  `SPECIFICATION/templates/<name>`). The `spec_file` field is
  the `spec_root`-relative path to the specification file
  containing the heading. The `heading` field is the exact `##`
  heading text without the `## ` prefix. The `test` field is a
  pytest node identifier (`<path>::<function>`), OR the literal
  `"TODO"` when the test is not yet authored — in which case
  the entry MUST also carry a non-empty `reason` field
  explaining why (e.g., `"rule added in v015; implementation
  and test pending"`).

  The meta-test fails in all of:
  - Uncovered headings (in spec, not in registry): "heading X
    has no test."
  - Orphaned registry entries (heading in registry, not in
    spec): "registry entry for heading 'OldName' is orphaned.
    Update the registry or the test."
  - `test: "TODO"` entries with empty or missing `reason`.

- **Registry lifecycle.** Entries in `tests/heading-coverage.json`
  MAY carry `test: "TODO"` when a real test for the referenced
  rule does not yet exist, provided the entry carries a
  non-empty `reason`. The `just check` aggregator (via the
  meta-test) accepts `"TODO"` entries with reason; it rejects
  them without reason.
  The release-gate target `just check-no-todo-registry` (grouped
  with `just check-mutation` on the release-tag CI workflow only;
  NOT included in `just check`; NOT run per-commit) rejects any
  `test: "TODO"` entry regardless of `reason`, ensuring every
  release ships with full rule-test coverage.
  Registry-update authority is livespec-repo-internal: whoever
  lands a spec change introducing a new `##` heading SHOULD add
  a corresponding registry entry in the same commit (with a
  real test if implemented; with `test: "TODO"` + `reason`
  otherwise). The meta-test catches drift at `just check`
  time; the release-gate forces eventual cleanup. This
  lifecycle applies ONLY to livespec's own dogfooded `tests/`
  tree at the repo root; it is NOT codified in shipped
  `SKILL.md` prose, shipped `doctor/static/` checks, or shipped
  wrappers — livespec-user projects inherit no such discipline
  from the plugin.

### Prompt-QA tier (per-prompt verification, v018 Q5)

Every built-in template's REQUIRED prompts
(`prompts/seed.md`, `prompts/propose-change.md`,
`prompts/revise.md`, `prompts/critique.md`) are exercised by
per-prompt tests under
`<repo-root>/tests/prompts/<template>/` before any end-to-end
harness test runs. The prompt-QA harness is a small
deterministic replay mechanism — scope-distinct from
`tests/e2e/fake_claude.py` (which drives wrappers end-to-end
via the Claude Agent SDK surface). Each prompt-QA test case
provides a prompt-response pair, runs the prompt against the
harness, and asserts on structured output at the corresponding
input-schema boundary (`seed_input.schema.json`,
`proposal_findings.schema.json`, `revise_input.schema.json`)
PLUS semantic properties (e.g., a seed prompt given
"build a web service" intent produces top-level headings
matching the domain, not arbitrary taxonomy; a revise prompt
given a `modify` decision produces `resulting_files[]` whose
paths match the template-declared spec file set).

Coverage:

- Every built-in template (`livespec`, `minimal`) MUST ship
  ≥ 1 prompt-QA test per REQUIRED prompt (4 prompts × 2
  templates = 8 minimum test cases).
- `just check-prompts` runs the tests (per-commit; included
  in `just check`).
- Custom templates MAY ship their own prompt-QA tests inside
  the template's own test directory; livespec imposes no
  requirement (consistent with the user-provided-extensions
  minimal-requirements principle — livespec's enforcement
  suite does NOT scope to user-template tests).

Harness scope (what prompt-QA verifies, what it does NOT):

- **Does verify**: prompt behavior at the skill↔template JSON
  contract boundary (LLM output conforms to schema AND
  satisfies declared semantic properties for the given
  input).
- **Does NOT verify**: wrapper integration (that's the E2E
  tier's job); doctor's static phase (that's unit tests);
  cross-prompt workflow sequencing (that's the E2E tier's
  job).

Under v018 Q1-Option-A, the prompt-QA tier validates every
built-in template's prompts BEFORE Phase 7 of the bootstrap
plan agent-generates their final content from their
sub-specs. Phase 7's propose-change cycle against each
sub-spec therefore targets a prompt set whose behavior is
already machine-verified; failing prompt-QA tests in Phase 7
surface before template content is generated, catching
regressions at the earliest possible point.

Implementation, fixture format, and the specific
schema-level-vs-semantic-level assertion mechanism per
prompt are tracked in `deferred-items.md`'s
`prompt-qa-harness` entry (joint-resolved with
`sub-spec-structural-formalization`, which supersedes the
closed `template-prompt-authoring` entry for prompt
authoring, AND `end-to-end-integration-test`).

### End-to-end harness-level integration test (v014 N9)

Livespec ships a REQUIRED end-to-end integration test that
exercises the full user workflow (Claude Code ↔ SKILL.md ↔
wrapper ↔ doctor) against a temporary git-repo fixture using
the `minimal` template. Two invocation tiers share a common
pytest suite, with harness-specific pytest markers / skipifs for
scenarios intentionally mock-only:

- **`just e2e-test-claude-code-mock`** (in `just check`;
  per-commit, local + CI): uses a livespec-authored Python
  API-compatible pass-through mock (at
  `<repo-root>/tests/e2e/fake_claude.py`) that implements the
  Claude Agent SDK's query-interface surface livespec uses.
  On each query, the mock reads the `minimal` template's
  prompt files, parses hardcoded delimiter comments
  identifying wrapper invocations, invokes the corresponding
  `bin/<cmd>.py` wrapper with a deterministically-generated
  JSON payload, and returns structured SDK-compatible
  messages to the test. Deterministic; instant; no LLM API
  cost.
- **`just e2e-test-claude-code-real`** (NOT in `just check`):
  uses the real `claude-agent-sdk` Python library against a
  live Anthropic API (`ANTHROPIC_API_KEY` env var required).
  CI triggers via three GitHub Actions events: (a) pre-merge
  check on PRs via GitHub merge queue (`on: merge_group`
  event; requires merge queue enabled in branch-protection
  settings); (b) every master-branch commit (`on: push` with
  `branches: [master]`, covering merged PRs and direct
  pushes); (c) manual invocation on any branch via
  `on: workflow_dispatch` (developers can trigger from the
  GitHub Actions UI). Locally invokable for developers
  validating before PR submission.

The env var `LIVESPEC_E2E_HARNESS=mock|real` selects the
executable. Shared tests run in both modes; mock-only scenarios
are annotated explicitly and skipped in real mode.

**Mock scope.** The mock replaces ONLY the Claude Agent SDK /
LLM layer. Every wrapper (`bin/seed.py`, `bin/doctor_static.py`,
`bin/propose_change.py`, `bin/critique.py`, `bin/revise.py`,
`bin/resolve_template.py`, `bin/prune_history.py`) runs for
real in BOTH tiers. The mock never stubs wrapper Python code.
Doctor-static's LLM-driven phase is handled by the mock
(LLM-driven by construction); doctor-static's Python phase
runs for real. This preserves the mock tier's ability to
catch wrapper-chain integration regressions (the hardest
class for per-module tests to cover).

**Coverage.** The happy path exercises the full user
workflow: `/livespec:seed` → `/livespec:propose-change` →
`/livespec:critique` → `/livespec:revise` → `/livespec:doctor`
→ `/livespec:prune-history` against the `minimal` template
in a `tmp_path`-scoped git-repo fixture. Plus three
user-visible error paths that can only be validated at the
harness level:

1. **Retry-on-exit-4**: an intentionally schema-invalid LLM
   payload triggers wrapper exit `4`. The mock tier then
   exercises exactly one retry cycle: first payload malformed,
   second payload well-formed. Assertion: the skill/prompt
   orchestration interprets return code `4` as a retry signal
   and the sub-command succeeds on the second attempt. This test
   is intentionally **mock-only** and is skipped in real mode;
   v1 does not require deterministic retry-path coverage in the
   real E2E tier.
2. **Doctor-static fail-then-fix**: pre-seed a state that
   trips a content-inspecting doctor-static check (e.g.,
   `bcp14-keyword-wellformedness` on a mixed-case `Must`);
   run `/livespec:doctor` to verify the fail Finding;
   apply the fix via `/livespec:propose-change --skip-pre-check`
   + `/livespec:revise --skip-pre-check` (per §"seed"
   post-step-failure recovery); verify post-revise
   doctor-static passes.
3. **Prune-history no-op**: run `/livespec:prune-history`
   on a project with only `v001` (nothing to prune); verify
   skipped Finding and filesystem unchanged.

**Delimiter-comment format.** The `minimal` template's
prompt files carry parseable delimiter comments identifying
the wrapper invocations the mock should perform. The real
LLM treats these as inert markdown comments (they do not
affect natural-language prompt interpretation). Per v018 Q1,
the exact format is codified in the `minimal` template's
sub-spec at
`SPECIFICATION/templates/minimal/contracts.md` under a
"Template↔mock delimiter-comment format" section (authored
during Phase 7 of the bootstrap plan via
`propose-change --spec-target SPECIFICATION/templates/minimal`
→ `revise --spec-target ...`); Phase 9's `fake_claude.py`
parses against that section. The v014 codification of the
format as a joint resolution between `template-prompt-
authoring` and `end-to-end-integration-test` is superseded
by v018 Q1's sub-spec codification. This remains an instance
of the architecture-vs-mechanism discipline (v009 I0): v014
codified the CONTRACT ("parseable directives identifying
wrapper invocations"), and v018 Q1 places the specific
format under the governed propose-change / revise loop.

**Implementation, fixtures, CI workflow files, and
environment-variable contracts** are tracked in
`deferred-items.md`'s `end-to-end-integration-test` entry.
A future option to replace the `ANTHROPIC_API_KEY` CI
dependency with a local/bundled model (preserving mock↔real
parity) is tracked in `deferred-items.md`'s
`local-bundled-model-e2e` entry (v2+ scope).

Full Python-specific constraints (complexity thresholds, purity
classification, enforcement-suite scripts under `dev-tooling/
checks/`, etc.) are in
`python-skill-script-style-requirements.md`, destined for
`SPECIFICATION/constraints.md`.

---

## Developer tooling layout

Developer-time artifacts live at the livespec repository root,
**outside the shipped skill bundle**. They are NOT installed into
user projects; they exist purely for livespec maintainers and CI.

```
<livespec-repo-root>/
├── .claude-plugin/                            (the shipped skill bundle; runtime-only)
├── dev-tooling/
│   └── checks/                                (enforcement-check Python scripts; purity + import_graph are NOT here — replaced by Import-Linter declarative contracts in pyproject.toml per v012 L15a. Import-surface portion of no_raise_outside_io was v012 L15a-delegated to Import-Linter but v017 Q3 retracted that delegation, so no_raise_outside_io.py is the sole enforcement point for the raise-discipline — raise-site only.)
│       ├── file_lloc.py
│       ├── private_calls.py
│       ├── global_writes.py
│       ├── supervisor_discipline.py
│       ├── rop_pipeline_shape.py              (v029 D1: single public method per @rop_pipeline-decorated class; encodes the Command / Use Case Interactor lineage at the class level)
│       ├── no_raise_outside_io.py             (raise-site portion only per v012 L15a; v017 Q3 confirmed raise-site is the SOLE enforcement point)
│       ├── no_except_outside_io.py
│       ├── public_api_result_typed.py         (rescoped per v012 L9 to use __all__ for public-API detection)
│       ├── main_guard.py
│       ├── wrapper_shape.py
│       ├── schema_dataclass_pairing.py
│       ├── keyword_only_args.py               (v011 K4 + v012 L4: also verifies frozen=True + kw_only=True + slots=True on @dataclass)
│       ├── match_keyword_only.py              (v011 K4)
│       ├── no_inheritance.py                  (v012 L5)
│       ├── assert_never_exhaustiveness.py     (v012 L7)
│       ├── newtype_domain_primitives.py       (v012 L8)
│       ├── all_declared.py                    (v012 L9)
│       ├── no_write_direct.py                 (v012 L10)
│       ├── pbt_coverage_pure_modules.py       (v012 L12)
│       ├── claude_md_coverage.py
│       ├── no_direct_tool_invocation.py
│       ├── no_todo_registry.py                 (v013 M8; release-gate only, not in `just check`)
│       ├── heading_coverage.py                (validates every `##` heading in every spec tree has a matching `tests/heading-coverage.json` entry whose `spec_root` field matches; tolerates empty array pre-Phase-6)
│       ├── vendor_manifest.py                 (validates `.vendor.jsonc` schema-conformance: every entry has a non-empty `upstream_url`, non-empty `upstream_ref`, parseable-ISO `vendored_at`; `shim: true` flag present on `jsoncomment` per v026 D1 and absent on every other entry)
│       ├── check_tools.py                     (meta check verifying every dev-tooling tool referenced in justfile is reachable on PATH or via uv-managed dependency)
│       ├── tests_mirror_pairing.py            (v033 D1: every covered .py under livespec/, bin/, dev-tooling/checks/ has a paired tests/<mirror>/test_<name>.py with at least one def test_*; closed exemption set is _vendor/**, _bootstrap.py, and empty-init __init__.py files)
│       ├── per_file_coverage.py               (v033 D2: parses .coverage data file, fails first time any single covered file is below 100% line OR 100% branch; authoritative gate, supersedes the totalize-only fail_under threshold)
│       ├── commit_pairs_source_and_test.py    (v033 D3: every feature/bugfix commit touching livespec/**, bin/**, or dev-tooling/checks/** must also touch tests/**; lefthook pre-commit only, NOT in `just check`)
│       ├── red_green_replay.py                (v034 D2-D3: replaces red_output_in_commit.py; mechanically verifies temporal Red→Green order via amend pattern + test-file-checksum + reflog inspection; runs the listed test in Red mode expecting fail and Green mode expecting pass; rejects amend if test-file checksum changed or if pre-amend HEAD lacks Red trailers; lefthook pre-commit only, NOT in `just check`)
│       └── check_mutation.py                  (v013 M3 release-gate; ratchet-with-ceiling against `.mutmut-baseline.json`, capped at 80%; not in `just check`)
├── tests/                                     (see "Testing approach")
├── justfile                                   (task runner — single source of truth for dev-tooling invocations)
├── lefthook.yml                               (pre-commit / pre-push hooks; delegates to just targets)
├── .github/
│   └── workflows/
│       └── ci.yml                             (CI config; delegates to just targets)
├── .mise.toml                                 (pins `uv`, `just`, `lefthook` — non-Python binaries only per v024; Python and Python deps are uv-managed via `pyproject.toml` `[dependency-groups.dev]`)
├── .python-version                             (uv-managed Python pin per v024; companion to `pyproject.toml` `[project.requires-python]`)
├── uv.lock                                     (UV lockfile recording exact resolved versions of every dev dep per v024; committed)
├── .vendor.jsonc                               (records exact upstream version pinned for each vendored library; includes typing_extensions per v013 M1)
├── .mutmut-baseline.json                       (initial mutation-kill-rate measurement; ratchet reference per v013 M3)
├── pyproject.toml                             (ruff + pyright + pytest + coverage + import-linter config; `[project.requires-python]` Python pin + `[dependency-groups.dev]` uv-managed dev tools per v024; no build system; Import-Linter minimum configuration per v013 M7, narrowed to two contracts per v017 Q3)
└── NOTICES.md                                 (lists every vendored library with its license and copyright; includes typing_extensions PSF-2.0 per v013 M1)
```

Key conventions:

- **The enforcement suite is invocation-surface-agnostic.** Every
  check is a `just` target. pre-commit (via lefthook), pre-push (via
  lefthook), CI (via GitHub Actions), and manual developer
  invocation all delegate to `just <target>`. No direct ruff /
  pyright / pytest invocations appear in `lefthook.yml` or
  `.github/workflows/*.yml`.
- **The `justfile` is the single source of truth** for dev-tooling
  invocations. `lefthook.yml` contains only `just <target>` in
  `run:` fields. `.github/workflows/*.yml` contains only
  `run: just <target>` steps. A
  `check-no-direct-tool-invocation` grep-level check enforces
  this discipline.
- **`just check` runs every target sequentially, continues on
  failure, and exits non-zero if any target failed,** listing which
  failed at the end. Matches CI's `fail-fast: false` matrix; one
  local run reproduces full CI feedback.
- **First-time bootstrap:** `mise install` then `uv sync
  --all-groups` then `just bootstrap` (per v024). `mise install`
  pulls non-Python binaries (`uv`, `just`, `lefthook`); `uv sync`
  resolves Python and the dev-deps from `pyproject.toml`
  `[dependency-groups.dev]` into a project-local `.venv`;
  `just bootstrap` runs `lefthook install` (registers git hooks)
  and any other one-time setup.
- **The enforcement suite runs on Linux + macOS.** No Windows
  native support. Python 3.10+ is the only interpreter.
- **Python is pinned to a specific 3.10+ release** via
  `pyproject.toml` `[project.requires-python]` and a committed
  `.python-version` (uv-managed per v024) so developers and CI
  run the same Python version. Accidental use of 3.11+ features
  fails at authoring time.
- **Vendored libraries are version-pinned, not hash-audited.**
  `.vendor.jsonc` records the exact upstream ref for each vendored
  lib so re-vendoring via `just vendor-update <lib>` is
  reproducible. There is no automated drift-detection check;
  `_vendor/` is treated as immutable third-party code, with code
  review and git diff visibility catching accidental edits.
- **Enforcement-suite check scripts under `dev-tooling/checks/`**
  are standalone Python modules with a top-level `main()` function
  and an `if __name__ == "__main__":` guard, invokable via `python3
  dev-tooling/checks/<name>.py` from a `just` recipe. They MUST
  themselves comply with every rule in
  `python-skill-script-style-requirements.md`.
- **CLAUDE.md coverage:** every directory under `dev-tooling/` MUST
  contain a `CLAUDE.md` describing directory-local constraints.
- Full enforcement-suite contract (canonical `just` target list,
  per-check rules, tool-dependency management via mise (binaries) + uv (Python and Python deps) per v024, coverage
  contract) is documented in the companion
  `python-skill-script-style-requirements.md`, destined for
  `SPECIFICATION/constraints.md`.

### Git notes as operational cache (v034 D4)

`refs/notes/commits` is the designated namespace for execution
metadata that does NOT belong in commit messages. Examples:
cached pytest output for fast replay, cached mutation-testing
scores, CI status snapshots, hook-run timestamps. Notes are
**never load-bearing** for invariant checks — the source of
truth for any TDD or coverage claim is the commit message
itself (subject + body + trailers). The pre-commit hooks read
trailers; if notes disappear, fork between machines, or
diverge, no invariant breaks.

**Replication.** Notes do not push/fetch by default. The
`just bootstrap` recipe runs `git config --add
remote.origin.fetch "+refs/notes/*:refs/notes/*"` to
configure the local repo to fetch notes alongside refs.
Pushing notes uses `git push origin "refs/notes/*"`
explicitly; the hook does NOT auto-push notes (push remains
manual or scheduled by future workflow).

**Allowed contents.** Notes MAY carry: full pytest --verbose
output (too verbose for commit body), multi-megabyte
mutation reports, CI run timestamps + status, replay-hook
local execution timestamps. Notes MUST NOT carry: TDD
trailer values (those live in commit messages), coverage
percentages claimed in checks (those derive from the live
`.coverage` data file), or anything else that hook decisions
read.

### Baseline-grandfathered violations (v034 D6) — DEFERRED per v035 D1

**Status as of v035: deferred indefinitely.** The
mechanism originally specified at v034 codification — a
TOML baseline file at
`<repo-root>/phase-5-deferred-violations.toml` loaded by
each check, with per-`(target, file, rule, location)` skip
semantics — is **not implemented**. The v034 step-3
activation commit (`chore!: activate v034 replay hook +
remove v033 hook (slim activation; v034 D6 deferred)`,
sha `495e5ce`) deliberately took the slim path per
`bootstrap/decisions.md` 2026-05-02T06:00:00Z. The
mechanism described above is preserved for historical
reference but is NOT load-bearing for the v034 D7 drain or
any post-Phase-5 work.

**Actual mechanism in use.** The v033 D5b thinned-
aggregate-grows-as-passing pattern was retained: the local
`just check` aggregate gates on a thinned list of
currently-passing canonical targets (defined inline at
`justfile:75-99`); each v034 D7 drain cycle that resolves a
currently-unbound canonical target rejoins it to the
aggregate's `targets=(...)` list in the same commit.

**Drain exit condition.** When all six previously-unbound
canonical targets (the four content-gap targets plus
`check-lint` and `check-format` config-tier cleanup) are
bound to the aggregate AND passing, the aggregate de facto
matches the full canonical-target list — no separate
"baseline empty" file-deletion event is involved.

**Why deferred.** Implementing v034 D6 as originally
written would have required ~22 check-script modifications
(each script loads the TOML, builds its violation set,
filters its own output against the baseline). The v034 D7
drain only resolves ~6 violations across ~11-15 cycles;
the per-check baseline-loading machinery is over-engineered
for that scope. The simpler thinned-aggregate-grows
pattern was already proven through cycles 1-172 of the
v033 D5b second redo. Per the v035 D1 codification, the
slim path is now the canonical mechanism; future
re-introduction of baseline-grandfathered violations (if
ever warranted) would route through a future propose-
change cycle rather than against this PROPOSAL.

**Historical-reference content.** The original v034 D6
schema, field semantics, lifecycle, and CI-semantics
prose follow below in case future hardening work wants to
revisit the mechanism. The `phase-5-deferred-violations.toml`
file does NOT exist in the repo.

**Schema (historical reference).**

```toml
[[violation]]
target = "check-complexity"
file = ".claude-plugin/scripts/livespec/commands/seed.py"
rule = "PLR2004"
location = "186:39"
note = "magic value 2; fix in seed.py refactor cycle"

[[violation]]
target = "check-newtype-domain-primitives"
file = ".claude-plugin/scripts/livespec/types.py"
rule = "module-missing"
location = ""
note = "create types.py with NewType definitions; replace 4 raw-str fields"
```

**Field semantics (historical reference).**

- `target` — canonical `just` target name whose check
  produces this violation.
- `file` — path to the offending file, repo-root-relative.
  Empty string permitted only for module-missing
  violations.
- `rule` — check-specific rule identifier (e.g.,
  `PLR2004` for ruff PLR violations; `module-missing` for
  required-module-absent; check-defined identifiers for
  custom checks).
- `location` — line:column or line range where the
  violation occurs. Empty string permitted for
  whole-file or whole-module violations.
- `note` — human-readable description / fix plan
  reference.

**Why mechanical-not-prose (historical reference).** The
original argument for the TOML baseline was that the v033
thinned aggregate encoded "what's deferred" in a justfile
comment — unstructured, drift-prone, opaque. The slim path
adopted at v035 accepts those tradeoffs because the drain
is short (~11-15 cycles), the targets are small in number
(~6), and the `bootstrap/STATUS.md` next-action prose +
this PROPOSAL section serve as the human-readable "what's
deferred" registry.

### CI workflow (v034 D8)

GitHub Actions runs the full canonical-target matrix on
both `pull_request` events and `push to master` events with
`fail-fast: false`. The matrix mirrors the canonical target
list (every `just check-*` target plus
`check-tests`, `check-coverage`, and the e2e + prompts
targets when active). Steps inside each matrix job:
checkout, install pinned binaries via `jdx/mise-action@v2`,
install Python dev deps via `uv sync --all-groups`,
delegate to `just <target>`. Direct tool invocations in CI
step `run:` lines are forbidden by
`check-no-direct-tool-invocation` (every CI step delegates
to `just`).

**Branch protection on master (deferred activation).**
A GitHub branch protection rule on `master` requires:

- All CI matrix jobs pass before merge.
- Linear history: PRs land via squash or rebase, not merge
  commits. Semantic-release derives version bumps from
  individual commit subjects, so squash-merge commits
  retain their conventional-commit type semantics.
- No direct pushes to master. All changes flow through PR.

The rule is configured via `gh api -X PUT
repos/:owner/:repo/branches/master/protection
--input branch-protection.json` where the request body
encodes the required-checks list, the linear-history
requirement, and the no-direct-push enforcement.

**Solo-dev + agent workflow.** Agent opens a PR with
auto-merge enabled (`gh pr create --fill && gh pr merge
--auto --squash`); GitHub merges automatically when CI
turns green. User retains manual override (`gh pr review`
or `gh pr merge` invoked by hand) for any PR they want to
inspect before merge.

**Activation boundary.** The `gh api` call to enable the
branch protection rule runs as the **final sub-step of
Phase 5**, AFTER the Phase 5 exit gates pass (5a drift-
review, 5b exit-criterion check, 5c advance-to-Phase-6
confirmation). Pre-Phase-5-exit cycles operate under
direct-push to master so the bootstrap workflow is not
artificially slowed by PR + CI round-trips during the
heavy authoring phase. Phase 6 onward operates under
protected master.

**CI cost.** PR-based workflow runs ~2× CI per cycle
versus direct-push (one PR-push CI run + one master-merge
CI run). At ~1.5 min per matrix run, ~3 min per cycle
wall-clock. For typical post-Phase-5 cycle counts this is
well under the GitHub Free tier 2000-min/month budget for
private repos and unlimited for public.

---

## Definition of Done (v1)

`livespec` v1 is complete when all of the following are true:

1. All sub-commands implemented and exposed as namespaced skills:
   `/livespec:help`, `/livespec:seed`, `/livespec:propose-change`,
   `/livespec:critique`, `/livespec:revise`, `/livespec:doctor`,
   `/livespec:prune-history`. Each lives at
   `.claude-plugin/skills/<sub-command>/SKILL.md` with appropriate
   `description`, `allowed-tools`, and (where applicable)
   `disable-model-invocation` frontmatter.
2. The plugin layout (`.claude-plugin/plugin.json` +
   `.claude-plugin/skills/<sub-command>/SKILL.md` per sub-command +
   shared `.claude-plugin/scripts/` containing `bin/`, `_vendor/`,
   and the `livespec/` Python package — including `commands/`,
   `doctor/run_static.py`, `doctor/static/__init__.py` (static
   registry), per-check modules under `doctor/static/`, `io/`
   (with vendored-lib facades and `io/git.py::get_git_user`),
   `parse/`, `validate/` (with 1:1 paired validators per v013 M6;
   including `validate/finding.py` per v014 N2),
   `schemas/` (with paired `schemas/dataclasses/` dataclasses
   enforced by the now-three-way `check-schema-dataclass-pairing`
   walking schema ↔ dataclass ↔ validator; `finding.schema.json`
   is a REQUIRED standalone schema per v014 N2, closing v010 J11's
   implementer-choice), `context.py` (with `DoctorContext.spec_root`
   AND v014 N3's `config_load_status` + `template_load_status`
   fields), `types.py` (canonical NewType
   aliases for domain primitives per v012 L8), `errors.py`
   (domain-error classes only), plus the `bin/*.py` shebang-
   wrapper executables and `bin/_bootstrap.py`, and the
   `_vendor/` tree with pinned versions of dry-python/returns
   + fastjsonschema + structlog + typing_extensions
   (upstream-sourced; typing_extensions reclassified from shim
   per v027 D1) and the `jsoncomment` shim (per v026 D1) — and
   the
   built-in `specification-templates/livespec/` and
   `specification-templates/minimal/` templates per v014 N1) is
   complete and self-consistent.
3. **Both built-in templates are fully implemented** (v014 N1):
   - `livespec` (default, multi-file): `template.json` declaring
     `template_format_version: 1`, prompts for seed/propose-change/
     revise/critique producing schema-valid JSON, full starter
     content under `specification-template/SPECIFICATION/`.
   - `minimal` (single-file): `template.json` declaring
     `template_format_version: 1` + `spec_root: "./"`, prompts
     for seed/propose-change/revise/critique producing
     schema-valid JSON AND containing the hardcoded delimiter
     comments the v014 N9 mock harness parses (format codified
     by the v018 Q1 `minimal`-sub-spec's `contracts.md`
     "Template↔mock delimiter-comment format" section), plus
     the starter `specification-template/SPECIFICATION.md`.
   Seed's SKILL.md prose prompts the user to select between
   these two (or a custom template path) when `.livespec.jsonc`
   is absent pre-seed. **Per v018 Q1, each built-in template
   additionally ships its own sub-specification tree seeded
   under `SPECIFICATION/templates/<name>/` at Phase 6 of the
   bootstrap plan.** Template content
   (`template.json`, `prompts/*.md`,
   `specification-template/**`) is generated by agents from
   each template's sub-spec in Phase 7 via propose-change →
   revise cycles with `--spec-target
   SPECIFICATION/templates/<name>`. The
   `template-prompt-authoring` deferred item is CLOSED by this
   mechanism (prompt content is specified at sub-spec level, not
   implementer-chosen).
4. `.livespec.jsonc` schema validation is implemented via
   `fastjsonschema` against
   `.claude-plugin/scripts/livespec/schemas/livespec_config.schema.json` using
   the factory-shape validator pattern.
5. Custom templates (template values pointing at a directory
   path) load successfully and pass all applicable doctor checks.
6. The full `doctor` static-check suite (every check listed in
   §"Static-phase checks") is implemented as per-check Python
   modules under `.claude-plugin/scripts/livespec/doctor/static/<module>.py`,
   registered statically in `static/__init__.py`, orchestrated by
   `.claude-plugin/scripts/livespec/doctor/run_static.py` via a single ROP chain
   (composition primitive is implementer choice under the
   architecture-level constraints), with documented exit-code
   semantics (0/1/3), the supervisor's findings-to-exit-code
   derivation, and the JSON output contract using `doctor-<slug>`
   check_ids. **Per v018 Q1, the orchestrator iterates over
   every spec tree (main + each sub-spec under
   `SPECIFICATION/templates/<name>/`)** per §"doctor →
   Static-phase structure"; findings carry a `spec_root` field
   discriminating per-tree origin; per-tree applicability
   dispatches according to the v018 Q1 rules
   (`gherkin-blank-line-format` conditional per template;
   `template-exists` and `template-files-present` main-tree
   only; all other checks per-tree uniformly).
7. The `doctor` LLM-driven phase's objective and subjective
   check categories are implemented at the skill layer
   (`doctor/SKILL.md`), with template-extension hooks declared
   via `template.json`'s `doctor_static_check_modules`,
   `doctor_llm_objective_checks_prompt`, and
   `doctor_llm_subjective_checks_prompt` fields; the two LLM-
   layer flag pairs (`--skip-doctor-llm-objective-checks` /
   `--run-doctor-llm-objective-checks`,
   `--skip-doctor-llm-subjective-checks` /
   `--run-doctor-llm-subjective-checks`) and corresponding
   `post_step_skip_doctor_llm_{objective,subjective}_checks`
   config keys provide bidirectional control with CLI → config →
   default precedence.
8. Every sub-command that does spec work invokes template prompts
   with schema-validated I/O. Template-internal discipline-doc
   injection (when the template ships one) is handled by the
   template's own prompts; the skill does not load or name any
   template-internal reference file.
9. The proposed-change and revision file formats are enforced
   by doctor's static phase (YAML front-matter validated via the
   restricted-YAML parser at `livespec/parse/front_matter.py`;
   required headings present per decision type).
10. The test suite covers every sub-command, both doctor phases,
    the `prune-history` flow, the wrapper-shape meta-test
    (`test_wrappers.py`), and the
    `test_meta_section_drift_prevention.py` meta-test. Test
    trees mirror the implementation trees one-to-one. 100% line
    + branch coverage across `.claude-plugin/scripts/livespec/**`,
    `.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/**`. Per v012 L12,
    every test module under `tests/livespec/parse/` and
    `tests/livespec/validate/` declares at least one
    `@given(...)`-decorated property-based test (enforced by
    `check-pbt-coverage-pure-modules`). Per v012 L13 + v013 M3,
    the release-tag CI workflow runs `just check-mutation`
    against `livespec/parse/` and `livespec/validate/` with a
    ratchet against `.mutmut-baseline.json` bounded by an
    absolute 80% mutation kill-rate ceiling (NOT in `just
    check`; NOT per-commit). Per v013 M8, the same release-tag
    CI workflow also runs `just check-no-todo-registry`
    rejecting any `test: "TODO"` entry in
    `tests/heading-coverage.json` — ensuring every release
    ships with full rule-test coverage. The
    `test_meta_section_drift_prevention.py` meta-test accepts
    `test: "TODO"` entries with a non-empty `reason` field
    during `just check` (per-commit tolerance); the release-
    gate forbids them outright.
    **Per v014 N9, the end-to-end harness-level integration test
    is implemented under `<repo-root>/tests/e2e/` with the
    `minimal` template as its canonical fixture.** Two just
    targets: `just e2e-test-claude-code-mock` (in `just check`;
    deterministic via livespec-authored API-compatible mock
    `fake_claude.py`) and `just e2e-test-claude-code-real` (NOT
    in `just check`; uses the real `claude-agent-sdk` against a
    live Anthropic API via `ANTHROPIC_API_KEY`). Env var
    `LIVESPEC_E2E_HARNESS=mock|real` selects the executable for
    the common pytest suite; mock-only scenarios such as the
    deterministic retry-on-exit-4 case are annotated with pytest
    markers / skipifs and are skipped in real mode. CI triggers
    for the real target
    are three GitHub Actions events: `merge_group` (pre-merge
    check via merge queue), `push` to `master` (every master
    commit), `workflow_dispatch` (manual invocation on any
    branch).
    **Per v018 Q5, a per-prompt verification tier at
    `<repo-root>/tests/prompts/<template>/` exercises every
    built-in template's REQUIRED prompts before the harness-
    level E2E tier runs.** `just check-prompts` runs the
    prompt-QA suite (included in `just check`; per-commit).
    Each built-in template ships ≥ 1 prompt-QA test per
    REQUIRED prompt. The prompt-QA harness is distinct from
    `tests/e2e/fake_claude.py`; it verifies prompt behavior
    at the skill↔template JSON-contract boundary (schema
    validity + declared semantic properties), not wrapper
    integration. See §"Prompt-QA tier (per-prompt
    verification)" for the full contract.
11. `python3 >= 3.10` presence check is implemented in
    `.claude-plugin/scripts/bin/_bootstrap.py`; the `bootstrap()` function exits
    127 with an actionable install instruction if older.
    `.claude-plugin/scripts/livespec/__init__.py` does NOT raise; it bootstraps
    structlog and binds `run_id`.
12. Developer tooling is in place under `<repo-root>/`:
    enforcement-check Python scripts under `dev-tooling/checks/`,
    `justfile` as single source of truth for invocations
    (including `just bootstrap` and `just check` aggregation
    behavior), `lefthook.yml` delegating to just targets,
    `.github/workflows/ci.yml` delegating to just targets
    (with a separate release-tag workflow invoking
    `just check-mutation` AND `just check-no-todo-registry`
    per v012 L13 + v013 M8),
    committed `.mise.toml` pinning non-Python binaries (`uv`,
    `just`, `lefthook`) per v024; Python and the v012-added dev
    packages (`hypothesis`, `hypothesis-jsonschema`, `mutmut`,
    `import-linter`) plus `pytest`, `pytest-cov`, `pytest-icdiff`,
    `ruff`, `pyright` declared in `pyproject.toml`
    `[dependency-groups.dev]` and resolved by `uv sync` into a
    committed `uv.lock` per v024; `typing_extensions` is vendored
    per v013 M1, NOT in either config,
    `.mutmut-baseline.json` at repo root recording initial
    mutation-kill-rate measurement per v013 M3,
    `.vendor.jsonc` recording vendored library upstream
    versions (extended to include `typing_extensions` per
    v013 M1),
    `pyproject.toml` configuring ruff + pyright + pytest +
    coverage + `[tool.importlinter]` (with `_vendor/` excluded
    from pyright strict; v012 strict-plus diagnostics enabled
    per L1+L2; v012 ruff selection at 27 categories per
    L3+L10+L11; TID banned-imports per L6+L11; Import-Linter
    contracts per L15a + v013 M7 minimum-configuration example,
    narrowed in v017 Q3 to two contracts — purity and layered
    architecture — with raise-discipline raise-site-enforced
    only via `check-no-raise-outside-io`; pyright is the
    chosen typechecker — closes `basedpyright-vs-pyright`;
    the `returns-pyright-plugin-disposition` deferred item
    was originally closed in v018 Q4 by vendoring a pyright
    plugin and was re-opened and re-closed in v025 with the
    revised disposition: no pyright plugin is vendored,
    because no such plugin exists upstream and pyright does
    not support plugins by design — see
    `history/v025/proposed_changes/critique-fix-v024-revision.md`
    decision D1),
    and `NOTICES.md` listing vendored libraries (extended with
    `typing_extensions` PSF-2.0 per v013 M1; mise-pinned binaries
    and uv-managed Python dev tools are NOT in NOTICES.md per
    v024).
13. Every directory under `.claude-plugin/scripts/` (with
    `_vendor/` and its entire subtree explicitly excluded), under
    `<repo-root>/tests/` (with any `fixtures/` subtree at any
    depth explicitly excluded — `tests/fixtures/` AND
    `tests/e2e/fixtures/` per v014 N9 both fall under this
    rule), and under `<repo-root>/dev-tooling/`
    contains a `CLAUDE.md` describing directory-local constraints,
    enforced by the `check-claude-md-coverage` target. One
    optional `tests/fixtures/CLAUDE.md` at the fixtures root
    (and similarly one optional
    `tests/e2e/fixtures/CLAUDE.md`) is permitted but not required.
14. `livespec` dogfoods itself: `<project-root>/SPECIFICATION/`
    (main spec) AND each built-in template's sub-spec tree
    under `<project-root>/SPECIFICATION/templates/<name>/` (per
    v018 Q1) exist, were generated by `livespec seed`, have
    each been revised at least once through `propose-change
    --spec-target <path>` + `revise --spec-target <path>`
    (the main tree's revision includes the post-seed initial
    pass; each sub-spec tree's revision is Phase 7's agent-
    generation of that template's shipped content), and all
    trees pass `livespec doctor` cleanly (doctor iterates over
    every tree per v018 Q1). Every item in `deferred-items.md`
    has been processed (paired revision exists in
    `<project-root>/SPECIFICATION/history/` for main-spec
    items, or the relevant sub-spec's history for
    sub-spec-targeted items). Closed deferred items
    (`template-prompt-authoring`,
    `returns-pyright-plugin-disposition`,
    `basedpyright-vs-pyright`, `companion-docs-mapping` —
    the latter rewritten as a pointer) land as
    bookkeeping revisions referencing the closure
    decisions in PROPOSAL.md.
15. The skill bundle includes its own `help` skill covering every
    sub-command.

---

## v1 non-goals (stated explicitly)

The following are intentionally out of scope for v1. The proposal
calls them out so their absence is recognized as a deliberate
boundary, not an accidental gap.

- **Subdomain ownership and cross-cutting routing.** As argued
  in `subdomains-and-unsolved-routing.md`, no public consensus
  exists. Templates and prompt conventions handle this; livespec
  does not.
- **Multi-specification per project (independent specs).**
  `.livespec.jsonc` has no `specification_dir` field; one
  PRIMARY specification per project. v018 Q1's sub-specification
  mechanism for built-in templates (`SPECIFICATION/templates/
  <name>/`) is a narrower, strictly smaller carve-out —
  hierarchical sub-specs of a single primary — and does NOT
  re-open this non-goal. Unrelated independent specs with
  distinct `.livespec.jsonc` files, independent versioning,
  and no primary/sub relationship remain out of v1 scope.
- **Writing to git.** `livespec` MUST NOT invoke `git commit`,
  `git push`, or any write operations. Read-only `git status` /
  `git show HEAD:` is the narrow exception for the
  `doctor-out-of-band-edits` check.
- **Claude Code plugin marketplace publishing.** Plugin is
  manually installable in v1; marketplace distribution is v2.
- **Alternate agent runtime packaging (`opencode`, `pi-mono`).**
  Plugin targets Claude Code only in v1.
- **Cross-invocation suppression / allow-listing of LLM-driven
  findings.** The subjective-checks skip flag is the only
  suppression mechanism in v1.
- **Scripted non-interactive revise.** `revise` is designed for
  interactive confirmation.
- **Additional built-in templates beyond `livespec` and
  `minimal`.** v014 N1 adds `minimal` as a second built-in
  (single-file spec at repo root; also serves as the canonical
  fixture for the v014 N9 E2E integration test). Further
  built-ins (`openspec`, domain-specific shapes, etc.) are not
  reserved; any alternate template is user-provided via a path.
- **Windows native support.** Linux and macOS are supported
  developer and end-user platforms; Windows is not.
- **Async / concurrency.** livespec's workload is synchronous and
  deterministic; no asyncio / threading / multiprocessing.
- **Automated vendored-lib drift detection.** Pinned versions in
  `.vendor.jsonc` + the no-edit discipline + code review are the
  controls; no `check-vendor-audit` script exists.

---

## Self-application

`livespec` MUST be developed by dogfooding itself. The bootstrap
order is:

1. Author this proposal, `PROPOSAL.md`, to a state that passes
   the recreatability test against `livespec-nlspec-spec.md`.
2. Implement the plugin skeleton: `plugin.json`, per-sub-command
   `SKILL.md` files, the Python package tree under
   `.claude-plugin/scripts/livespec/`, vendored libraries under `.claude-plugin/scripts/_vendor/`,
   `bin/*.py` shebang wrappers + `bin/_bootstrap.py`, doctor's
   static-check modules + the static registry at
   `doctor/static/__init__.py`, the minimum subset of the
   `livespec` template needed to consume PROPOSAL.md as seed
   input, AND minimum-viable implementations of
   `propose-change`, `critique`, and `revise` (wrappers +
   command modules + their schemas / dataclasses / validators)
   sufficient to file the first dogfooded change cycle against
   the seeded `SPECIFICATION/` (v019 Q1). "Minimum-viable" means
   correctness sufficient for the FIRST dogfooded cycle (parse a
   propose-change file, write a revision file, cut a new
   history version, route via `--spec-target`), not full-feature
   parity. Full-feature widening of these sub-commands lands in
   step 4 via propose-change/revise cycles against the seed.
   `prune-history` and doctor's LLM-driven phase at the skill
   layer stay out of step 2 — neither is required for the first
   dogfooded cycle.
3. Run `livespec seed` against this project, producing
   `<project-root>/SPECIFICATION/` (main spec) AND each
   built-in template's sub-specification tree under
   `<project-root>/SPECIFICATION/templates/<name>/` per v018
   Q1-Option-A. All trees are produced atomically by a single
   seed invocation; each tree's `history/v001/` is created in
   the same step.
4. **Widen** the minimum-viable sub-commands implemented in
   step 2 (`propose-change`, `critique`, `revise`) to
   full-feature parity (topic canonicalization, reserve-suffix
   discipline, collision disambiguation, single-canonicalization
   invariant routing, full critique-as-internal-delegation flow,
   full revise per-proposal LLM decision flow with delegation
   toggle and rejection audit trail), AND implement the
   remaining sub-commands not present in step 2 (`prune-history`,
   doctor's LLM-driven phase at the skill layer), all using
   `propose-change` / `revise` cycles against the seeded spec
   trees (v019 Q1). Each cycle targets a specific tree via
   `--spec-target <path>` (default: main spec root).
5. **Process every entry in `deferred-items.md`** by filing
   `propose-change`s for each, then revising. Items resolved this
   way include per-sub-command SKILL.md prose authoring
   (`skill-md-prose-authoring`), wrapper input schemas
   (`wrapper-input-schemas`), static-check semantics
   (`static-check-semantics`), the restricted-YAML parser
   (`front-matter-parser`), the companion-doc migrations
   (per the Companion documents and migration classes
   subsection below), the v014 N9
   `end-to-end-integration-test` entry (fixture + mock
   executable + pytest suite + CI workflows), the v018 Q5
   `prompt-qa-harness` entry (per-prompt verification tier),
   the v018 Q1 `sub-spec-structural-formalization` entry
   (doctor parameterization + `--spec-target` routing + seed
   multi-tree output + heading-coverage scoping), and the
   v014 N9-D1 future-scope `local-bundled-model-e2e` entry.
   The v018 Q1 `template-prompt-authoring` closure (prompt
   content generated from each built-in template's sub-spec
   rather than implementer-chosen), the v018 Q4
   `returns-pyright-plugin-disposition` closure (plugin
   vendored; see §"Dependencies — Vendored pure-Python
   libraries"), and the v018 Q4 `basedpyright-vs-pyright`
   closure (pyright is the chosen typechecker; see
   §"Dependencies — Developer-time dependencies") require
   only bookkeeping revisions pointing at the closure
   decisions in PROPOSAL.md.
6. Land the v1 Definition of Done items as the spec evolves.

**Bootstrap exception (v018 Q2; v019 Q1 clarification).** The
bootstrap ordering above (steps 1-4, ending with the first
`livespec seed` invocation in step 3) lands imperatively. The
governed propose-change → revise loop becomes operable starting
at step 4 — after seed has produced the working
`SPECIFICATION/` tree (main spec + every built-in template's
sub-spec under `SPECIFICATION/templates/<name>/` per the v018
Q1 addition). From the second change onward (every change to
livespec's skill bundle, developer tooling, built-in template
content, or any seeded spec tree), the loop is MANDATORY;
hand-editing any file under any spec tree or under
`.claude-plugin/specification-templates/<name>/` after the
first seed is a bug in execution, not a permitted fast-path.
The exception applies ONCE per livespec repo, at initial
bootstrap; it does NOT apply to v2+ releases of livespec
(those flow through the governed loop against the
then-existing SPECIFICATION).

The v019 Q1 widening of step 2 places minimum-viable
implementations of `propose-change`, `critique`, and `revise`
BEFORE the seed, inside the imperative window. The imperative
window's closing point (end of step 3, the first seed) is
unmoved by this widening; step 2 retains its imperative status,
and step 4 retains its governed-loop-mandatory status.
Widening of the minimum-viable sub-commands to full feature
parity in step 4 happens entirely through dogfooded cycles, so
step 4 has no imperative landings.

### Companion documents and migration classes (v018 Q6)

Companion documents in `brainstorming/approach-2-nlspec-based/`
are classified as exactly one of three migration classes:

- **MIGRATED-to-SPEC-file**: content moves verbatim (or
  restructured for BCP 14 + heading conventions) into a
  named `SPECIFICATION/` file.
- **SUPERSEDED-by-section**: content becomes a named section
  in an existing `SPECIFICATION/` file.
- **ARCHIVE-ONLY**: content lives in `brainstorming/` for
  historical context; not migrated to `SPECIFICATION/`.
  Explicit rationale required per doc.

Assignments (class, destination, target phase in the bootstrap
plan):

| Companion doc | Class | Destination | Phase |
|---|---|---|---|
| `goals-and-non-goals.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Goals" + "Non-goals" sections | 6 |
| `python-skill-script-style-requirements.md` | MIGRATED-to-SPEC-file | `SPECIFICATION/constraints.md` | 8 |
| `subdomains-and-unsolved-routing.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Non-goals" appendix (subordinate to `goals-and-non-goals.md`'s "Non-goals" section) | 8 |
| `prior-art.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Prior Art" appendix | 8 |
| `2026-04-19-nlspec-lifecycle-diagram.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Lifecycle" section | 8 |
| `2026-04-19-nlspec-lifecycle-diagram-detailed.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Lifecycle" section (subordinate to preceding entry) | 8 |
| `2026-04-19-nlspec-lifecycle-legend.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Lifecycle" section (subordinate) | 8 |
| `2026-04-19-nlspec-terminology-and-structure-summary.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Lifecycle" section (subordinate) | 8 |
| `livespec-nlspec-spec.md` | ARCHIVE-ONLY + TEMPLATE-BUNDLED-PROMPT-REFERENCE | Brainstorming copy archived in `brainstorming/`; initial bundled copy lands at `.claude-plugin/specification-templates/livespec/livespec-nlspec-spec.md` in Phase 2; post-bootstrap evolution is via direct edit of the bundled file under ordinary PR review, exempt from Plan §3's cutover hand-edit ban under the prompt-reference-metadata carve-out (see §"Built-in template: `livespec`"). Not sub-spec-governed and not agent-regenerated in Phase 7. | N/A (already shipped per §"Built-in template: `livespec`") |
| `deferred-items.md` | ARCHIVE-ONLY | Archived in `brainstorming/`; items processed as Phase 8 propose-changes per step 5 above | 8 (items) / N/A (doc itself) |
| `critique-interview-prompt.md` | ARCHIVE-ONLY | Archived in `brainstorming/`; brainstorming-process artifact, not part of shipped livespec | N/A |
| `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` | ARCHIVE-ONLY | Archived in `brainstorming/` after bootstrap completes; execution artifact, not spec content | N/A (bootstrap-only) |

The `companion-docs-mapping` deferred-items entry body points
at this subsection; per-doc resolution notes (what was migrated
where, when) accumulate in the corresponding Phase-8 revise
decisions.

The canonical list of items deferred from this proposal lives in
`brainstorming/approach-2-nlspec-based/deferred-items.md` (and
flows into the seeded `SPECIFICATION/` in step 3). Each entry has
a stable id, target spec file(s), and a how-to-resolve paragraph.
Future revisions of this proposal MUST keep that file authoritative;
removing a deferred item from the file requires explicit explanation
in the corresponding revision.
