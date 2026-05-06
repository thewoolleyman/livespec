# `livespec` Proposal

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
│   │   ├── returns/                     # dry-python/returns (BSD-2) — ROP primitives
│   │   ├── fastjsonschema/              # (MIT) — JSON Schema Draft-7 validator
│   │   ├── structlog/                   # (BSD-2 / MIT dual) — structured JSON logging
│   │   └── jsoncomment/                 # (MIT) — JSONC (JSON-with-comments) parser
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
│       ├── validate/                    # pure validators (Result-returning, factory shape)
│       ├── schemas/                     # JSON Schema Draft-7 files + paired dataclasses
│       │   ├── dataclasses/                       # paired hand-authored dataclasses (see I3)
│       │   │   ├── livespec_config.py
│       │   │   ├── seed_input.py
│       │   │   ├── revise_input.py
│       │   │   ├── proposal_findings.py
│       │   │   ├── doctor_findings.py
│       │   │   ├── finding.py                     # Finding + pass_finding/fail_finding constructors (moved from doctor/ per J11)
│       │   │   ├── proposed_change_front_matter.py
│       │   │   └── revision_front_matter.py
│       │   ├── doctor_findings.schema.json       # doctor static-phase output contract
│       │   ├── proposal_findings.schema.json     # propose-change / critique template output
│       │   ├── seed_input.schema.json            # seed wrapper input (deferred; see deferred-items.md)
│       │   ├── revise_input.schema.json          # revise wrapper input (deferred; see deferred-items.md)
│       │   ├── livespec_config.schema.json
│       │   ├── proposed_change_front_matter.schema.json  # (deferred; see deferred-items.md)
│       │   └── revision_front_matter.schema.json         # (deferred; see deferred-items.md)
│       ├── context.py                   # immutable context dataclasses (railway payload)
│       └── errors.py                    # LivespecError hierarchy (expected-failure classes only; per-subclass exit_code)
└── specification-templates/             # built-in templates (see "Templates" below)
    └── livespec/
        ├── template.json
        ├── livespec-nlspec-spec.md
        ├── prompts/
        │   ├── seed.md
        │   ├── propose-change.md
        │   ├── revise.md
        │   └── critique.md
        └── specification-template/
            └── SPECIFICATION/
                ├── README.md
                ├── spec.md
                ├── contracts.md
                ├── constraints.md
                └── scenarios.md
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
    `SPECIFICATION/proposed_changes/` and `SPECIFICATION/history/`
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
   under `scripts/livespec/schemas/` is named. The wrapper
   validates the payload internally; the SKILL.md prose does NOT
   invoke a separate validator.
4. **Steps.** An ordered list of LLM-driven steps. Each step is
   one of:
   - Invoke `bin/<cmd>.py` via the Bash tool, with explicit argv.
   - **Resolve + invoke a template prompt.** Two-step dispatch:
     (a) invoke `bin/resolve_template.py` via Bash and capture
     the active template's path from stdout (the wrapper reads
     `.livespec.jsonc`'s `template` field and resolves built-in
     names or user-provided paths uniformly); (b) use the Read
     tool to read `<resolved-path>/prompts/<name>.md` and use its
     contents as the template prompt. This replaces the literal
     `@`-reference approach from v009 (which only worked for the
     built-in `livespec` template); the two-step dispatch works
     uniformly for built-in and custom templates. See J3 in
     `history/v010/proposed_changes/proposal-critique-v09-revision.md`.
   - Write LLM-produced JSON to a temp file in preparation for
     a wrapper invocation.
   - Prompt the user for confirmation (only for `revise`'s
     per-proposal dialogue; the frontmatter's
     `disable-model-invocation` and `allowed-tools` settings gate
     tooling access).
   - Narrate a warning (e.g., when pre-step checks are skipped).
   - **Retry-on-exit-4:** on wrapper exit code `4` (schema
     validation failed; LLM-provided JSON payload did not conform
     to the wrapper's input schema), re-invoke the relevant
     template prompt with the structured error context from stderr
     and re-assemble the JSON payload. Up to 3 retries per
     PROPOSAL.md §"Templates — Skill↔template communication layer";
     abort on repeated failure with a visible user message. Exit
     code `3` (precondition/doctor-static failure) is NOT
     retryable — it surfaces the findings to the user and aborts.
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
     payload; **retryable**. Re-invoke the template prompt with
     the error context from stderr and re-assemble the JSON, up
     to 3 retries (see step 4 "Retry-on-exit-4" above).
   - Exit `127` → too-old Python or missing tool; surface the
     install instruction and abort.

Concrete per-sub-command SKILL.md bodies are deferred to
`deferred-items.md`'s `skill-md-prose-authoring` entry.

#### Sub-command dispatch and invocation chain

- Each sub-command's SKILL.md prose names the relevant
  `scripts/bin/<cmd>.py` wrapper by path; the LLM invokes it
  directly via the bash tool. No top-level dispatcher script.
- The wrapper is a thin shebang pass-through to
  `livespec.commands.<cmd>.main()` via the shared
  `bin/_bootstrap.py` module.
- **Command files use `@`-reference syntax** to force deterministic
  reading of critical files (e.g., `@../../scripts/livespec/...`).
- **Deterministic logic MUST be implemented in Python** under
  `scripts/livespec/**`. LLM-driven behavior MUST NOT replace Python
  where a deterministic check is possible.
- **Python MUST NOT invoke the LLM.** LLM-driven work (template
  prompt invocation, LLM-driven doctor phase, interactive
  per-proposal confirmation) lives in skill prose; Python wrappers
  only handle deterministic work.
- **CLI argument parsing MUST happen in `livespec/io/cli.py`**, not
  in `livespec/commands/<cmd>/main()`. `argparse.ArgumentParser.parse_args`
  raises `SystemExit` on usage errors and `--help`; the wrapper's
  6-line shape leaves no room for argparse; and
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

#### Shebang-wrapper contract

Each `bin/<cmd>.py` MUST consist of exactly the following 6-line
shape (no other lines, no other statements):

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
  fields. Consumed by `just vendor-update <lib>` (a shell recipe
  that invokes Python through `livespec.parse.jsonc` to read/write
  the file) and by human reviewers:
  - `dry-python/returns` (BSD-2) — ROP primitives (`Result`,
    `IOResult`, `@safe`, `@impure_safe`, `flow`, `bind`,
    `Fold.collect`).
  - `fastjsonschema` (MIT) — JSON Schema Draft-7 validator.
  - `structlog` (BSD-2 / MIT dual) — structured JSON logging.
  - `jsoncomment` (MIT) — JSONC (JSON-with-comments) parser; used
    by `livespec/parse/jsonc.py` to parse `.livespec.jsonc` and any
    other JSONC input.
  - Each preserves its upstream `LICENSE`; a `NOTICES.md` at the
    livespec repo root lists every vendored library.
- **Vendoring discipline:** `_vendor/` files are NEVER edited
  directly. Re-vendoring goes through `just vendor-update <lib>`,
  which is the only blessed mutation path. Code review and git
  diff visibility catch accidental edits.
- LLM-bundled prompts MAY reference Python helpers from
  `scripts/livespec/**` (e.g., for JSON structural checks); they MUST
  NOT assume any non-vendored dependency.

#### Developer-time dependencies (livespec repo only)

Every tool the enforcement suite requires — `python3` (pinned 3.10+
exact), `just`, `lefthook`, `ruff`, `pyright`, `pytest`, `pytest-cov`,
`pytest-icdiff` — is managed via `mise`
([github.com/jdx/mise](https://github.com/jdx/mise)) in a committed
`.mise.toml` at the livespec repository root. Running `mise install`
followed by `just bootstrap` (which executes `lefthook install` and
any other one-time setup) produces a ready-to-run environment.
Developer tooling is NOT installed into user projects; it is purely
livespec-maintainer-facing.

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
- All file I/O in `SPECIFICATION/`, `proposed_changes/`, `history/`.
- Versioning, history directory creation, version-number contiguity.
- Doctor's static phase invocation and result handling (composed
  via the wrapper's ROP chain — see "Sub-command lifecycle
  orchestration" below).
- File-format validation (proposed-change format, revision format,
  YAML front-matter schemas).
- JSON Schemas that template-emitted JSON must conform to; LLM
  re-prompting on malformed output; abort after N retries.
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

---

## Configuration: `.livespec.jsonc`

`.livespec.jsonc` lives at the project root. It is OPTIONAL; when
absent, all documented defaults apply.

### JSONC dialect

`.livespec.jsonc` uses the JSONC dialect: JSON plus `//` line
comments and `/* ... */` block comments. Trailing commas,
single-quoted strings, and unquoted keys (features that would
qualify as JSON5) are NOT supported. Parsing is implemented at
`scripts/livespec/parse/jsonc.py` as a thin pure wrapper over the
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
Draft-7 file at `scripts/livespec/schemas/livespec_config.schema.json`
on every read. Validation uses the vendored `fastjsonschema` library
from `scripts/_vendor/fastjsonschema/` via the factory-shape
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
  unconditionally (and for the `author_llm` field on revision-file
  front-matter, where applicable), overriding any LLM self-
  declaration in the JSON payload and the `"unknown-llm"`
  fallback. See the unified precedence rules in §"propose-change
  → Author identifier resolution", §"critique", §"revise", and
  §"Revision file format".

### Multi-specification per project

Out of scope for v1. The schema intentionally has no
`specification_dir` field — the template controls placement.

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

- **Invocation shape.** Zero positional arguments. One optional
  flag: `--project-root <path>` (default: `Path.cwd()`; the
  wrapper walks upward from `--project-root` looking for
  `.livespec.jsonc`).
- **Stdout contract.** On success, exactly one line: the resolved
  template directory as an absolute POSIX path, followed by `\n`.
  Paths containing spaces are emitted literally (the Read tool
  accepts literal paths; callers MUST NOT pipe through shells
  that re-split on whitespace).
- **Built-in resolution.** When the resolved `.livespec.jsonc`
  names a built-in template (e.g., `"template": "livespec"`), the
  wrapper emits
  `<bundle-root>/specification-templates/<name>/` as its stdout,
  where `<bundle-root>` is derived via
  `Path(__file__).resolve().parent.parent` on the wrapper itself.
- **User-provided path resolution.** When the resolved
  `.livespec.jsonc` names anything other than a built-in name,
  the value is treated as a path relative to `--project-root`.
  The wrapper resolves the path to absolute and validates that
  (a) the directory exists and (b) it contains `template.json`.
  (Deeper validation — e.g., `template_format_version`, prompt-
  file presence — is left to the `template-exists` doctor
  static-check.)
- **Lifecycle applicability.** `resolve_template` has neither
  pre-step nor post-step doctor static (see §"Sub-command
  lifecycle orchestration — Pre-step/post-step applicability").
- **Exit codes.** `0` on success; `3` on any of {.livespec.jsonc
  not found above `--project-root`, malformed, schema-invalid,
  resolved path missing, resolved path lacks `template.json`};
  `2` on bad `--project-root` usage; `127` on too-old Python
  (via `_bootstrap.py`).
- **v2+ extensibility shield.** The stdout contract (one line,
  absolute POSIX path, trailing `\n`) is frozen in v1. Future
  template-discovery extensions (remote URLs, registries,
  plugin-path hints, per-environment overrides; see
  `user-hosted-custom-templates` in `deferred-items.md`) MUST
  preserve the exact shape so existing SKILL.md prose continues
  to work unchanged.

### Custom templates are in v1 scope

- `.livespec.jsonc`'s `template` field accepts either a built-in
  name or a path to a template directory.
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
  `user-hosted-custom-templates` entry.

### Skill↔template communication layer

All communication between the skill and template prompts is JSON
with schemas. Each template prompt has a documented input schema
(variables the skill provides) and output schema (what the prompt
emits). The skill validates output against the schema using the
vendored `fastjsonschema` library and re-invokes on malformed output
with error context. After a configured number of retries (3), the
skill aborts the sub-command with an error and preserves partial
state for investigation.

Schemas for the JSON contracts ship as part of the skill in
`.claude-plugin/scripts/livespec/schemas/`.
Authoring the full schemas and prompt input/output details is an
implementation task tracked in `deferred-items.md`
(`template-prompt-authoring`).

### Built-in template: `livespec`

The `livespec` template is the only built-in for v1. It produces
the SPECIFICATION directory structure shown above. Its starter
content for each specification file is described below.

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
  `proposed_changes/`. A `revise` invocation that finds no
  proposals MUST fail hard and direct the user to
  `propose-change`.
- A `revise` invocation that processes proposals but rejects all
  of them MUST still cut a new version. The version's
  specification files are byte-identical copies of the prior
  version's specification files; the version's `history/vNNN/`
  directory contains the proposed-change files and rejection
  revisions. This preserves the audit trail for every proposal
  that ever reached `revise`.
- `seed` creates `v001` directly: it writes both the working
  specification files AND `history/v001/` including the seed's
  auto-created proposed-change and revision (see `seed` below).

---

## Pruning history

A dedicated `prune-history` sub-command removes older history
while preserving auditable continuity.

Operation:

1. Identify the current highest version `vN`.
2. If `history/v(N-1)/PRUNED_HISTORY.json` exists, read its
   `pruned_range[0]` value and retain it as `first` for the new
   marker (carrying the original-earliest version number forward).
   If no prior marker exists, `first` is the earliest v-directory
   version number currently in `history/` (typically `1`).
3. Delete every `history/vK/` directory where `K < N-1`.
4. Replace the contents of `history/v(N-1)/` with a single file:
   `history/v(N-1)/PRUNED_HISTORY.json`, containing only
   `{"pruned_range": [first, N-1]}`.
5. Leave `history/vN/` fully intact.

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

- With no args, prompts the user for `<intent>` in dialogue.
- `<intent>` is freeform text and MAY include references to
  existing specifications, examples, projects, or other
  context. Path references and `@`-mentions in the intent are
  handled by the LLM's natural file-reading capability; the
  skill requires no special path-dereference logic.
- Creates `.livespec.jsonc` with full commented defaults if
  absent. `.livespec.jsonc` is NOT a template-declared target
  file; if present and valid, `seed` reuses it without
  modification (validating against the schema first).
- The LLM (per `seed/SKILL.md`) invokes the active template's
  `prompts/seed.md` with `<intent>` and the template's
  `specification-template/` starter content as input. The prompt
  MUST emit JSON conforming to
  `scripts/livespec/schemas/seed_input.schema.json`:
  ```json
  {
    "files": [
      {"path": "SPECIFICATION/spec.md", "content": "..."}
    ],
    "intent": "<verbatim user intent>"
  }
  ```
  The LLM writes this JSON to a temp file and invokes
  `bin/seed.py --seed-json <tempfile>`. The wrapper validates
  the payload against the schema internally; on validation
  failure, it exits 4 with structured findings on stderr and the
  LLM MUST re-invoke the template prompt with the error context,
  up to 3 retries per PROPOSAL.md §"Templates — Skill↔template
  communication layer."
- `bin/seed.py --seed-json <path>` is the sole wrapper entry
  point. The wrapper reads the JSON, writes each file to its
  specified path, creates `history/v001/` (including a `README.md`
  copy, the initial spec files, and a `proposed_changes/` subdir),
  and auto-captures the seed itself as a proposed-change. Seed
  is exempt from pre-step doctor static (see §"Sub-command
  lifecycle orchestration"); post-step runs normally after
  file creation.
- **Auto-generated `history/v001/proposed_changes/seed.md`
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
  `history/v001/proposed_changes/seed-revision.md`**: front-matter
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

### `propose-change <topic> <intent>`

- Creates a new file
  `SPECIFICATION/proposed_changes/<topic>.md` containing one or
  more `## Proposal: <name>` sections (see "Proposed-change
  file format" below).
- **`bin/propose_change.py` accepts `--findings-json <path>`
  (required) and `--author <id>` (optional)**; it never invokes
  the template prompt or the LLM. The freeform `<intent>` path is
  driven by the LLM per `propose-change/SKILL.md`: the LLM invokes
  the active template's `prompts/propose-change.md`, captures the
  output, writes the JSON to a temp file, then invokes
  `bin/propose_change.py --findings-json <tempfile> <topic>
  [--author <id>]`. The wrapper validates the payload against the
  schema internally; on validation failure, it exits 4 with
  structured findings on stderr, and the LLM MUST re-invoke the
  template prompt with the error context, up to 3 retries.
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
- The wrapper validates the JSON against
  `scripts/livespec/schemas/proposal_findings.schema.json` and
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
- If a file with topic `<topic>` already exists, the skill MUST
  auto-disambiguate by appending a short suffix. No user prompt
  for collision.
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
  findings on stderr, and the LLM MUST re-invoke the template
  prompt with the error context, up to 3 retries.
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
  the topic suffix.
- `bin/critique.py` delegates internally to `propose_change`'s
  Python logic with topic `<resolved-author>-critique` and the
  structured findings as input. Internal delegation skips the
  inner pre/post doctor cycle since the outer `critique`
  invocation's wrapper ROP chain already covers the whole
  operation.
- If a file with topic `<resolved-author>-critique` already
  exists, the skill MUST auto-disambiguate by appending a short
  suffix. No user prompt.
- Does not run `revise`; the user reviews and runs `revise` to
  process.

### `revise <revision-steering-intent>`

- `<revision-steering-intent>` is OPTIONAL and, when provided,
  MUST only steer per-proposal decisions for the current revise
  invocation (e.g., "reject anything touching the auth section").
  It MUST NOT contain new spec content. If the user supplies
  content that expresses new intent rather than decision-steering,
  the skill MUST surface a warning and direct the user to run
  `propose-change` first. Detection is best-effort LLM judgment;
  on ambiguity, the skill proceeds with a visible warning.
- **`revise` MUST fail hard when `proposed_changes/` contains no
  proposal files**, directing the user to run `propose-change`
  first. No auto-creation of ephemeral proposals.
- Files in `proposed_changes/` are processed in **creation-time
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
  `scripts/livespec/schemas/revise_input.schema.json`:
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
          {"path": "SPECIFICATION/spec.md", "content": "..."}
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
  stderr, and the LLM MUST re-assemble (or re-prompt) and retry,
  up to 3 retries.
- The wrapper reads the JSON and performs the deterministic
  file-shaping work:
  - If any decision is `accept` or `modify`, a new version `vN`
    is cut.
  - Working-spec files named in `resulting_files` are updated in
    place with the new content.
  - `history/vN/` is created with copies of the README and spec
    files at this new version.
  - A `history/vN/proposed_changes/` subdirectory is created.
  - Each processed proposal file is moved
    **byte-identical** from `SPECIFICATION/proposed_changes/`
    into `history/vN/proposed_changes/<topic>.md`. Relative
    markdown links preserved.
  - Each processed proposal gets a paired revision at
    `history/vN/proposed_changes/<topic>-revision.md`,
    conforming to the format defined in "Revision file format"
    below, populated from the decision's `rationale` and (for
    `modify`) `modifications` fields.
- After successful completion, `SPECIFICATION/proposed_changes/`
  MUST be empty.

### `prune-history`

- Runs the pruning operation defined in the "Pruning history"
  section above.
- Accepts no arguments in v1.
- SKILL.md frontmatter MUST set `disable-model-invocation: true`
  (destructive operation; explicit invocation only).
- Post-step doctor static runs normally after pruning. No
  post-step LLM-driven phase.

### `doctor`

`doctor` runs in two phases:

- **Static phase** is implemented in Python. The orchestrator is
  at `.claude-plugin/scripts/livespec/doctor/run_static.py` and
  invoked via the shebang wrapper at `scripts/bin/doctor_static.py`.
  Each static check is a Python module at
  `scripts/livespec/doctor/static/<module>.py`.
- **LLM-driven phase** is skill behavior (prose in
  `doctor/SKILL.md`), not Python. It has no exit codes.

There is no `bin/doctor.py` wrapper; see §"Sub-command lifecycle
orchestration" → "Note on `bin/doctor.py`".

#### Static-phase structure

Each static check is a Python module at
`scripts/livespec/doctor/static/<module>.py`. Each check:

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

The orchestrator `scripts/livespec/doctor/run_static.py`:

- Uses the **static registry** at
  `scripts/livespec/doctor/static/__init__.py`, which imports every
  check module by name and re-exports a tuple of `(SLUG, run)` pairs.
  Adding or removing a check is one explicit edit to the registry.
  No dynamic discovery; pyright strict can fully type-check the
  composition.
- Calls `module.run(ctx)` in-process for every registered check.
- Composes all check results into one `IOResult[FindingsReport,
  E]` via the composition primitives from `dry-python/returns`.
  The specific primitive (e.g., `Fold.collect`, a reduce over
  `bind`, etc.) is implementer choice under the architecture-level
  constraints; what matters is that the composition is a single
  ROP chain and the final payload preserves both pass-and-fail
  findings plus domain-error short-circuits.
- `IOSuccess(finding)` (pass or fail finding) accumulates into
  the report; `IOFailure(err)` (internal bug) short-circuits.
- The supervisor in `main()` unwraps the final `IOResult`
  and emits `{"findings": [...]}` JSON to stdout.

The slug↔module-name mapping is recorded literally in the registry
(no hyphen-to-underscore conversion loop). User-facing `check_id`
values in JSON findings keep hyphens: `"doctor-out-of-band-edits"`.

#### Static-phase output contract

The orchestrator writes structured JSON to stdout conforming to
`scripts/livespec/schemas/doctor_findings.schema.json` and returns
an exit code per the "Static-phase exit codes" table below. Output
shape:

```json
{
  "findings": [
    { "check_id": "doctor-version-contiguity", "status": "fail", "message": "...", "path": "SPECIFICATION/history", "line": null }
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
`scripts/livespec/doctor/static/<module>.py`, registered statically
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
  by livespec. On any failure, the finding MUST name the
  offending field, its value, and the path to `.livespec.jsonc`.
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
  full set of template-required files, a `README.md`, and a
  `proposed_changes/` subdir. The pruned-marker directory (the
  oldest surviving, when `PRUNED_HISTORY.json` is present)
  contains ONLY `PRUNED_HISTORY.json`.
- **`version-contiguity`** — Version numbers in
  `<spec-root>/history/` are contiguous from `pruned_range.end + 1`
  (if `PRUNED_HISTORY.json` exists at the oldest surviving `vN-1`
  directory) or from `v001` upward. Numeric parsing.
- **`revision-to-proposed-change-pairing`** — Every revision file
  in `<spec-root>/history/vNNN/proposed_changes/` has a
  corresponding proposed-change file with the same topic in the
  same directory.
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
- **`anchor-reference-resolution`** — All Markdown links in all
  files under `<spec-root>/` (spec files, READMEs,
  proposed-change files, revision files) with anchor references
  resolve to existing headings in the referenced files. Anchors
  are generated per GitHub-flavored Markdown (GFM) slug rules:
  the heading text is lowercased; internal whitespace is replaced
  with single hyphens; punctuation is stripped except `-` and
  `_`; multiple consecutive hyphens collapse to one. Headings
  inside fenced code blocks (`` ``` `` or `~~~`) are NOT
  considered headings. Explicit `{#custom-id}` syntax is NOT
  supported in v1. Edge-case details (case variations, non-ASCII
  headings, duplicate-heading disambiguation suffixes) are
  deferred to `deferred-items.md`'s `static-check-semantics`
  entry.

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
   `scripts/livespec/parse/front_matter.py` (deferred; see
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

Each `<topic>-revision.md` in `history/vNNN/proposed_changes/`
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
  Coverage MUST be 100% line + branch across all Python files
  under `.claude-plugin/scripts/livespec/**` and
  `<repo-root>/dev-tooling/**`. Vendored third-party libraries
  under `scripts/_vendor/` are excluded from the coverage
  measurement (they are pinned and audited via the discipline
  in §"Dependencies — Runtime"; no automated audit script).
  See the companion
  `python-skill-script-style-requirements.md` for the full
  coverage contract (100% line+branch; pragma escape hatch
  capped per file; no tier split).

Directory structure (mirrors the implementation trees 1:1,
including subdirectories):

```
tests/
├── CLAUDE.md                                 (enforces test/spec consistency; see below)
├── heading-coverage.json                     (meta-test registry; see below)
├── fixtures/                                 (explicit test fixtures; MUST NOT be mutated by tests)
├── bin/                                      (mirrors scripts/bin/)
│   ├── test_bootstrap.py                     (covers bin/_bootstrap.py)
│   ├── test_wrappers.py                      (meta-test: all wrappers match the 6-line shape)
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
│   └── checks/                               (one test_*.py per enforcement script)
│       ├── test_purity.py
│       ├── test_private_calls.py
│       └── ...
└── test_*.py                                 (per-specification-file rule-coverage tests)
```

Test organization rules:

- `tests/livespec/` mirrors `.claude-plugin/scripts/livespec/`
  one-to-one, preserving subdirectory structure.
  `tests/dev-tooling/` mirrors `<repo-root>/dev-tooling/` the same
  way. `tests/bin/` mirrors `scripts/bin/`. Adding a module anywhere
  under those trees requires adding the corresponding test file at the
  mirrored path.
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
  test case in the coverage registry.
- **Coverage registry**: `tests/heading-coverage.json` maps
  headings to test identifiers:
  ```json
  [
    { "heading": "Proposed-change file format", "test": "test_propose_change.py::test_multi_proposal_write" }
  ]
  ```
  The meta-test fails in both directions:
  - Uncovered headings (in spec, not in registry): "heading X
    has no test."
  - Orphaned registry entries (heading in registry, not in
    spec): "registry entry for heading 'OldName' is orphaned.
    Update the registry or the test."

The workflow for creating/updating tests and the registry is an
implementation concern, not specified here. Full Python-specific
constraints (complexity thresholds, purity classification,
enforcement-suite scripts under `dev-tooling/checks/`, etc.) are
in `python-skill-script-style-requirements.md`, destined for
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
│   └── checks/                                (enforcement-check Python scripts)
│       ├── file_lloc.py
│       ├── purity.py
│       ├── private_calls.py
│       ├── import_graph.py
│       ├── global_writes.py
│       ├── supervisor_discipline.py
│       ├── no_raise_outside_io.py
│       ├── no_except_outside_io.py
│       ├── public_api_result_typed.py
│       ├── main_guard.py
│       ├── wrapper_shape.py
│       ├── schema_dataclass_pairing.py
│       ├── claude_md_coverage.py
│       └── no_direct_tool_invocation.py
├── tests/                                     (see "Testing approach")
├── justfile                                   (task runner — single source of truth for dev-tooling invocations)
├── lefthook.yml                               (pre-commit / pre-push hooks; delegates to just targets)
├── .github/
│   └── workflows/
│       └── ci.yml                             (CI config; delegates to just targets)
├── .mise.toml                                 (pins python3 >=3.10, just, lefthook, pyright, ruff, pytest, pytest-cov, pytest-icdiff)
├── .vendor.jsonc                               (records exact upstream version pinned for each vendored library)
├── pyproject.toml                             (ruff + pyright + pytest + coverage config; no build system)
└── NOTICES.md                                 (lists every vendored library with its license and copyright)
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
- **First-time bootstrap:** `mise install` then `just bootstrap`.
  `just bootstrap` runs `lefthook install` (registers git hooks)
  and any other one-time setup.
- **The enforcement suite runs on Linux + macOS.** No Windows
  native support. Python 3.10+ is the only interpreter.
- **Python is pinned to a specific 3.10+ release** in `.mise.toml`
  so developers and CI run the same Python version. Accidental
  use of 3.11+ features fails at authoring time.
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
  per-check rules, tool-dependency management via mise, coverage
  contract) is documented in the companion
  `python-skill-script-style-requirements.md`, destined for
  `SPECIFICATION/constraints.md`.

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
   `parse/`, `validate/`, `schemas/` (with paired
   `schemas/dataclasses/` dataclasses enforced by
   `check-schema-dataclass-pairing`), `context.py` (with
   `DoctorContext.spec_root`), `errors.py` (domain-error classes
   only), plus the `bin/*.py` shebang-wrapper executables and
   `bin/_bootstrap.py`, and the `_vendor/` tree with pinned
   versions of dry-python/returns + fastjsonschema + structlog +
   jsoncomment — and the built-in `specification-templates/livespec/`
   template) is complete and self-consistent.
3. The `livespec` built-in template is fully implemented
   (`template.json` declaring `template_format_version: 1`,
   prompts for seed/propose-change/revise/critique producing
   schema-valid JSON, full starter content under
   `specification-template/`).
4. `.livespec.jsonc` schema validation is implemented via
   `fastjsonschema` against
   `scripts/livespec/schemas/livespec_config.schema.json` using
   the factory-shape validator pattern.
5. Custom templates (template values pointing at a directory
   path) load successfully and pass all applicable doctor checks.
6. The full `doctor` static-check suite (every check listed in
   §"Static-phase checks") is implemented as per-check Python
   modules under `scripts/livespec/doctor/static/<module>.py`,
   registered statically in `static/__init__.py`, orchestrated by
   `scripts/livespec/doctor/run_static.py` via a single ROP chain
   (composition primitive is implementer choice under the
   architecture-level constraints), with documented exit-code
   semantics (0/1/3), the supervisor's findings-to-exit-code
   derivation, and the JSON output contract using `doctor-<slug>`
   check_ids.
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
    + branch coverage across `scripts/livespec/**` and
    `dev-tooling/**`.
11. `python3 >= 3.10` presence check is implemented in
    `scripts/bin/_bootstrap.py`; the `bootstrap()` function exits
    127 with an actionable install instruction if older.
    `scripts/livespec/__init__.py` does NOT raise; it bootstraps
    structlog and binds `run_id`.
12. Developer tooling is in place under `<repo-root>/`:
    enforcement-check Python scripts under `dev-tooling/checks/`,
    `justfile` as single source of truth for invocations
    (including `just bootstrap` and `just check` aggregation
    behavior), `lefthook.yml` delegating to just targets,
    `.github/workflows/ci.yml` delegating to just targets,
    committed `.mise.toml` pinning every dev tool, `.vendor.jsonc`
    recording vendored library upstream versions,
    `pyproject.toml` configuring ruff + pyright + pytest +
    coverage (with `_vendor/` excluded from pyright strict),
    and `NOTICES.md` listing vendored libraries.
13. Every directory under `.claude-plugin/scripts/` (with
    `_vendor/` and its entire subtree explicitly excluded), under
    `<repo-root>/tests/` (with `fixtures/` and its entire subtree
    explicitly excluded), and under `<repo-root>/dev-tooling/`
    contains a `CLAUDE.md` describing directory-local constraints,
    enforced by the `check-claude-md-coverage` target. One
    optional `tests/fixtures/CLAUDE.md` at the fixtures root is
    permitted but not required.
14. `livespec` dogfoods itself: `<project-root>/SPECIFICATION/`
    exists, was generated by `livespec seed`, has been revised
    at least once through `propose-change` + `revise`, and
    passes `livespec doctor` cleanly. Every item in
    `deferred-items.md` has been processed (paired revision
    exists in `<project-root>/SPECIFICATION/history/`).
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
- **Multi-specification per project.** `.livespec.jsonc` has no
  `specification_dir` field; one specification per project.
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
- **Additional built-in templates beyond `livespec`.** `openspec`
  is not reserved; any alternate template is user-provided via a
  path.
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
   `scripts/livespec/`, vendored libraries under `scripts/_vendor/`,
   `bin/*.py` shebang wrappers + `bin/_bootstrap.py`, doctor's
   static-check modules + the static registry at
   `doctor/static/__init__.py`, and the minimum subset of the
   `livespec` template needed to consume PROPOSAL.md as seed
   input.
3. Run `livespec seed` against this project, producing
   `<project-root>/SPECIFICATION/` and `history/v001/`.
4. Implement remaining sub-commands (`propose-change`,
   `critique`, `revise`, `prune-history`, doctor's LLM-driven
   phase at the skill layer), using `propose-change` / `revise`
   cycles against the seeded spec.
5. **Process every entry in `deferred-items.md`** by filing
   `propose-change`s for each, then revising. Items resolved this
   way include template prompt authoring
   (`template-prompt-authoring`), per-sub-command SKILL.md prose
   authoring (`skill-md-prose-authoring`), wrapper input schemas
   (`wrapper-input-schemas`), static-check semantics
   (`static-check-semantics`), the returns pyright-plugin
   disposition (`returns-pyright-plugin-disposition`), the
   restricted-YAML parser (`front-matter-parser`), and the
   companion-doc migrations.
6. Land the v1 Definition of Done items as the spec evolves.

The canonical list of items deferred from this proposal lives in
`brainstorming/approach-2-nlspec-based/deferred-items.md` (and
flows into the seeded `SPECIFICATION/` in step 3). Each entry has
a stable id, target spec file(s), and a how-to-resolve paragraph.
Future revisions of this proposal MUST keep that file authoritative;
removing a deferred item from the file requires explicit explanation
in the corresponding revision.
