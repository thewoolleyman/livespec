---
topic: proposal-critique-v07
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-22T20:00:00Z
---

# Critique scope

This critique evaluates **v007 PROPOSAL.md** plus its companion
`python-skill-script-style-requirements.md` against the embedded
`livespec-nlspec-spec.md` guidelines. Primary focus: the recreatability
test over v007 — given only PROPOSAL.md, the Python style doc,
`livespec-nlspec-spec.md`, and `deferred-items.md`, can a competent
implementer produce a working v007 livespec plugin?

The v007 revision (`history/v007/proposed_changes/proposal-critique-v06-revision.md`)
locked in 18 dispositions (G1-G18) covering per-sub-command skill
structure, the shared `_bootstrap.py` wrapper shape, the single ROP
chain wrapper-side orchestration, the factory-shape validator pattern,
the static check registry, vendoring discipline (pinned versions, no
audit script), and the `deferred-items.md` tracking mechanism. This
critique does **not** reopen any of those decisions.

The recreatability test surfaces gaps in four clusters:

1. **Bootstrap / import-path integration.** The shared `_bootstrap.py`
   inserts `scripts/` into sys.path so `livespec` resolves — but the
   vendored libs live under `scripts/_vendor/` and the spec claims
   they resolve as `returns.io`, `fastjsonschema`, `structlog`. They
   don't.
2. **Parsing seams that have no parser.** `.livespec.jsonc` is JSONC
   (JSON-with-comments). `livespec/parse/jsonc.py` is in the layout
   but no parser is specified, none of the vendored libs parse JSONC,
   and no `deferred-items.md` entry covers it. Same shape of gap as
   v007 G2 (YAML front-matter) — which was resolved — but for JSONC.
3. **LLM↔wrapper split finished for `propose-change` and `critique`
   only.** v007 G11 resolved the split for those two sub-commands.
   `revise` and `seed`'s wrapper input contracts still use hedged
   language ("or equivalent entry path"); the deterministic halves'
   inputs are undefined.
4. **Skill-prose body content is unspecified.** v007 restructured
   from a single skill to per-sub-command skills, each carrying its
   own `SKILL.md`. Every SKILL.md's frontmatter is specified; the
   prose body (which orchestrates the LLM's post-wrapper work,
   template-prompt invocation, and per-proposal dialogue) is not.
   Nothing in PROPOSAL.md, the style doc, or `deferred-items.md`
   covers it.

Items are labelled `H1`–`H16` (the `H` prefix distinguishes
"v007 gap" findings from prior critiques' `G`-prefixed items). Each
item is labelled with one of the four NLSpec failure modes:

- **ambiguity** — admits multiple incompatible interpretations.
- **malformation** — self-contradiction within or across documents.
- **incompleteness** — missing information needed to act.
- **incorrectness** — internally consistent but specifies behavior
  that cannot work as written.

Major gaps appear first (block recreatability outright), then
significant gaps (force load-bearing guesses), then smaller cleanup.

---

## Major gaps

These items would block a competent implementer from producing a
working v007 livespec without filing additional propose-changes.

---

## Proposal: H1-bootstrap-syspath-vs-vendored-imports

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (self-contradiction across the style doc's bootstrap
body and the vendored-lib import shape).

### Summary

The style doc claims that inserting `scripts/` into `sys.path` is
sufficient to make `from returns.io import IOResult`,
`from fastjsonschema import compile`, and `import structlog` resolve.
It isn't: the vendored libraries live under `scripts/_vendor/<lib>/`,
so with only `scripts/` on `sys.path`, Python sees no top-level
`returns`, `fastjsonschema`, or `structlog` package. Every import in
`livespec/__init__.py` (structlog configuration) and throughout the
codebase fails on first invocation.

### Motivation

Style doc lines 127-130:

> The shared `bin/_bootstrap.py:bootstrap()` function inserts the
> bundle's `scripts/` directory into `sys.path` so `livespec` and
> `_vendor/<lib>` both resolve under their natural names
> (`from returns.io import IOResult`, `from livespec.commands.seed
> import main`).

Style doc lines 683-694 show the `_bootstrap.py` body: one
`sys.path.insert(0, str(bundle_scripts))`, where `bundle_scripts =
Path(__file__).resolve().parent.parent` (= `.claude-plugin/scripts/`).

With sys.path = `[scripts/, ...]`:

- `import livespec` → looks for `scripts/livespec/__init__.py` ✓
- `import returns` → looks for `scripts/returns.py` or
  `scripts/returns/__init__.py`. Neither exists.
  `scripts/_vendor/returns/__init__.py` is NOT discovered because
  `_vendor/` is not on `sys.path`.
- `import structlog`, `import fastjsonschema` → same failure.

Further, `livespec/__init__.py` itself tries to `import structlog`
(to call `structlog.configure(...)` and
`structlog.contextvars.bind_contextvars(...)`). This import runs at
package import time, which means every `from livespec.commands.seed
import main` triggers the broken structlog import.

The contradiction is load-bearing: nothing in the codebase works
without a fix.

### Proposed Changes

Amend `bin/_bootstrap.py:bootstrap()` to insert both `scripts/` and
`scripts/_vendor/` into `sys.path`:

```python
def bootstrap() -> None:
    if sys.version_info < (3, 10):
        sys.stderr.write(
            "livespec requires Python 3.10+; install via your package manager.\n"
        )
        raise SystemExit(127)
    bundle_scripts = Path(__file__).resolve().parent.parent
    bundle_vendor = bundle_scripts / "_vendor"
    for path in (bundle_scripts, bundle_vendor):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
```

Update the style doc's prose to reflect "inserts `scripts/` AND
`scripts/_vendor/` into sys.path" everywhere that phrasing appears
(lines 127-130 in the vendored-libraries subsection, and in the
`_bootstrap.py` body shape). `check-wrapper-shape` does not need to
change (it applies to `bin/*.py` except `_bootstrap.py`).

Alternative A: move vendored libs to `scripts/returns/`,
`scripts/fastjsonschema/`, `scripts/structlog/` (drop the `_vendor/`
prefix). Cleaner naming but loses the visual quarantine that
`_vendor/` provides and complicates the exclusion rules
(`check-claude-md-coverage`, pyright `exclude`, coverage exclusion
all reference `_vendor/**`).

Alternative B: rename every `from returns.io import IOResult` to
`from _vendor.returns.io import IOResult` (and similarly for
structlog/fastjsonschema). Makes the vendored-ness visible at every
call site; breaks upstream-mirroring and forces different test-import
shapes. Worse trade-off.

Recommend the two-path insert.

---

## Proposal: H2-jsonc-parser-unspecified

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (recreatability defect with no tracking entry).

### Summary

`.livespec.jsonc` is JSONC (JSON with comments). The layout lists
`scripts/livespec/parse/jsonc.py` (PROPOSAL.md line 120; style doc
line 186). Nothing in PROPOSAL.md, the style doc, or
`deferred-items.md` specifies what `parse/jsonc.py` contains or how
it's implemented. Python's stdlib `json` does not parse comments;
the three vendored libraries (`returns`, `fastjsonschema`,
`structlog`) do not parse JSON or JSONC either (fastjsonschema
validates *dicts*, it is not a parser).

This is the same shape of gap that v007 G2 resolved for YAML
front-matter (hand-rolled restricted parser at
`parse/front_matter.py`, tracked in `deferred-items.md`'s
`front-matter-parser`). JSONC got lost.

### Motivation

PROPOSAL.md references `.livespec.jsonc` parsing throughout:

- §"Configuration: `.livespec.jsonc`" § "Validation" (lines 554-561):
  "validation uses the vendored `fastjsonschema` library via the
  factory-shape validator pattern: `io/` reads the schema from disk,
  `validate/` is pure and accepts the parsed schema dict as a
  parameter."
- Doctor static check `livespec-jsonc-valid` depends on parsing.

"Reads the schema from disk" implies JSON deserialization; but the
USER CONFIG is also JSONC and needs comment-aware parsing before
`fastjsonschema.compile(...)` can validate it. Someone has to parse
JSONC-with-comments into a dict. That someone is `parse/jsonc.py`.
What does it do?

Three plausible implementations:

1. **Hand-roll a restricted JSONC parser.** Strip `//` line comments
   and `/* ... */` block comments before calling `json.loads`.
   ~30 LLOC pure module returning `Result[dict, ParseError]`.
   Handles the documented `.livespec.jsonc` shape exactly.
2. **Vendor a pure-Python JSONC library.** `json5`, `jsonc-parser`,
   or similar. Adds a fourth vendored lib; the vendoring precedent
   exists.
3. **Drop JSONC; switch to `.livespec.json` (no comments).** The
   self-documenting inline-schema-with-comments property of
   `.livespec.jsonc` (PROPOSAL.md line 548: "including comments and
   defaults, so the configuration is self-documenting on disk")
   is lost.

### Proposed Changes

Recommend option (1), mirroring the G2 resolution: hand-roll at
`scripts/livespec/parse/jsonc.py`, codify the format restriction in
PROPOSAL.md's `.livespec.jsonc` section so the parser stays narrow
forever.

Concretely:

- Add to PROPOSAL.md § "Configuration: `.livespec.jsonc`" § "Schema":
  - `.livespec.jsonc` uses the JSONC dialect: JSON plus `//` line
    comments and `/* ... */` block comments. No trailing commas, no
    single-quoted strings, no unquoted keys (i.e., not JSON5).
- Add a `jsonc-parser` entry to `deferred-items.md` (source: v008;
  target: `<bundle>/scripts/livespec/parse/jsonc.py`; how-to-resolve:
  hand-roll the restricted parser returning `Result[dict, ParseError]`,
  with tests covering line comments, block comments, comment-in-
  string, unterminated-block-comment, and JSON-parse fallthrough).

Alternative (3) is a v1-scope reduction. If preferred, drop the
`.jsonc` extension in favor of `.json`, remove the inline-comment
rationale, and accept that `seed` writes pure JSON with no inline
commentary.

---

## Proposal: H3-argparse-in-commands-main-violates-supervisor-discipline

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (self-contradiction between the wrapper shape, the
supervisor-discipline rule, and the argparse affordance).

### Summary

The 6-line wrapper contract (PROPOSAL.md lines 199-207; style doc
lines 652-660) allows no logic in `bin/<cmd>.py`:

```python
#!/usr/bin/env python3
"""..."""
from _bootstrap import bootstrap
bootstrap()
from livespec.<module>.<submodule> import main

raise SystemExit(main())
```

So argparse lives in `livespec.commands.<cmd>.main()`. But Python's
`argparse.ArgumentParser.parse_args()` raises `SystemExit(2)` on
usage errors (unknown flag, missing required arg, `-h` for help).
Style doc § "Non-interactive execution" (line 61) mandates argparse;
style doc § "Exit code contract" (line 611) says
`sys.exit(err.exit_code)` appears only in `bin/*.py`;
`check-supervisor-discipline` (line 763) AST-rejects `sys.exit` /
`raise SystemExit` anywhere outside `bin/*.py`.

`argparse.ArgumentParser.parse_args()` inside `livespec.commands.seed.main()`
raises `SystemExit(2)` on malformed args. That is a `raise SystemExit`
outside `bin/*.py`. AST gate rejects it.

### Motivation

argparse is a boundary I/O concern (reads argv; writes usage text to
stderr; decides exit codes). The G5/G11 resolutions established that
deterministic I/O lives in `io/`, pure composition lives in
`commands/`. But the style doc's argparse mandate is orthogonal to
that layering and not localized.

Three plausible implementations a reader could adopt:

1. **argparse in `livespec.commands.<cmd>.main()` directly.** Violates
   `check-supervisor-discipline` (argparse raises `SystemExit`).
   Cannot pass the gate.
2. **argparse in `livespec/io/cli.py`.** A thin `@impure_safe` wrapper
   around `ArgumentParser` with `exit_on_error=False`; returns
   `IOResult[Namespace, UsageError]`. `commands/<cmd>.main()` calls
   it via the railway. Fits ROP-all-the-way-down; requires spec
   acknowledgment.
3. **argparse in `bin/<cmd>.py`.** The wrapper parses argv before
   calling `main(parsed_args)`. Violates the 6-line wrapper shape and
   `check-wrapper-shape`.

Option 2 is the only ROP-consistent answer. It requires:

- A documented `livespec/io/cli.py` module with `@impure_safe` wrapped
  `parse_args(argv, parser_config) -> IOResult[Namespace, UsageError]`
  using `exit_on_error=False` (Python 3.9+).
- Each `livespec.commands.<cmd>.main()` threads argv through the
  railway: `flow(sys.argv[1:], parse_args_for_cmd, bind(run), ...)`.
- The supervisor maps `IOFailure(UsageError)` → exit `2`.
- Help (`-h`, `--help`): `exit_on_error=False` doesn't silence
  `--help`'s automatic exit. Extra handling needed — e.g., detect
  `-h` ahead of `parse_args` or catch `SystemExit` inside the
  `@impure_safe` wrapper and convert to an IOResult.

None of this is documented.

### Proposed Changes

Add a new subsection to the style doc under "Package layout" and to
PROPOSAL.md's DoD #11 neighborhood, titled "CLI argument parsing
seam":

- All argparse usage lives in `livespec/io/cli.py`, wrapped with
  `@impure_safe` and `exit_on_error=False`.
- Each sub-command exposes a `build_parser() -> ArgumentParser`
  factory under `livespec/commands/<cmd>.py` (pure construction;
  no parse).
- `io.cli.parse_args(argv: list[str], parser: ArgumentParser) ->
  IOResult[Namespace, UsageError]` is the only parse entry point.
  It detects `--help`/`-h` explicitly and returns
  `IOFailure(UsageError("..."))` with usage text routed through
  structlog or returned via the railway.
- `check-supervisor-discipline` scope clarified: applies to all
  `.py` files in `livespec/**`; `bin/*.py` (including
  `_bootstrap.py`) is the only carve-out.
- The `ast-check-semantics` deferred item expands to cover
  argparse's `SystemExit` path (if any) and the `-h`/`--help`
  convention.

Alternative: extend the 6-line wrapper shape to include an
`ArgumentParser` call before `main(parsed)`. This was explicitly
rejected by v007 G18's resolution (deterministic 6-line shape). Not
recommended.

---

## Proposal: H4-skill-md-prose-body-undefined

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (recreatability-blocking; no deferred-items
coverage).

### Summary

v007 G13 restructured the plugin to one SKILL.md per sub-command
(`skills/seed/SKILL.md`, `skills/propose-change/SKILL.md`, etc.).
Each SKILL.md's **frontmatter** is specified (`name`, `description`,
`allowed-tools`, optional `disable-model-invocation`). Each
SKILL.md's **prose body**, which orchestrates every LLM-driven
behavior after the wrapper exits, is entirely undefined.

PROPOSAL.md references the prose throughout:

- §"Sub-command lifecycle orchestration" → "Skill-prose-side:
  LLM-driven post-step" (lines 351-371): "SKILL.md prose MUST follow
  this pattern after the wrapper exits with code 0: 1. Run the
  LLM-driven phase per `commands/doctor.md` (skill prose)..."
- §"critique <author>" (lines 883-886): "The LLM (per
  `critique/SKILL.md`) invokes the active template's
  `prompts/critique.md`."
- §"propose-change" (lines 853-859): "The freeform `<intent>` path
  is driven by the LLM per `propose-change/SKILL.md`..."
- §"revise" (lines 906-953): entirely LLM-driven; no wrapper details.
- §"doctor" (lines 972-979): "LLM-driven phase is skill behavior
  (prose in `doctor/SKILL.md`)."

Every reference points to prose content that does not exist and is
not queued anywhere.

The `deferred-items.md` entries cover adjacent work but not this:

- `template-prompt-authoring` — template prompts
  (`specification-templates/livespec/prompts/{seed,propose-change,
  revise,critique}.md`), NOT SKILL.md bodies.
- `ast-check-semantics` — enforcement-check AST semantics.
- `front-matter-parser` — restricted YAML parser.
- `returns-pyright-plugin-disposition` — pyright plugin.

None of them instructs the implementer what `skills/doctor/SKILL.md`'s
body must say. The implementer would invent it, and the recreatability
claim ("a competent implementer can generate... from v007 PROPOSAL.md
+ livespec-nlspec-spec.md + python-skill-script-style-requirements.md
alone") fails.

### Motivation

Claude Code SKILL.md prose has structural conventions: step-by-step
instructions to the LLM, `@`-references to critical files, explicit
tool invocations, error-handling branches. None of that is specified.
Two implementers would produce wildly different `skills/seed/SKILL.md`
bodies — one terse, one verbose; one with explicit path references,
one with implicit ones; one that reads `@deferred-items.md` for seed
input, one that doesn't.

The v006 proposal had `commands/<cmd>.md` files which presumably
carried prose body content; v007's G13 restructure moved them to
SKILL.md but never stated what was moved.

### Proposed Changes

Two complementary actions:

1. Add a subsection to PROPOSAL.md under "Plugin delivery" titled
   "Per-sub-command SKILL.md body structure" stating the canonical
   body shape:

   - Opening sentence stating when this sub-command applies (mirrors
     `description`).
   - "When to invoke" paragraph (user-facing trigger phrases).
   - "Inputs" section (what the user provides; CLI flags and their
     meanings).
   - "Steps" section: an ordered list of LLM-driven steps, each
     either:
     - Invoking `bin/<cmd>.py` via the Bash tool with explicit argv.
     - Invoking a template prompt at
       `@../../specification-templates/<template>/prompts/<name>.md`
       and capturing output.
     - Validating output against a schema via
       `livespec.validate.<name>.validate`.
     - Prompting the user for confirmation (for `revise`) or narrating
       warnings (for skipped pre-check).
   - "Post-wrapper" section describing LLM-driven post-step
     behavior (for seed/propose-change/critique/revise) or its
     absence (prune-history, help, doctor's skip-on-static-fail).
   - "Failure handling" section explaining how to surface wrapper
     exit codes (0 → proceed; non-zero → abort with narration).

2. Add a `skill-md-prose-authoring` entry to `deferred-items.md`:
   - **Source:** v008 (NEW, H4)
   - **Target spec file(s):**
     `<bundle>/.claude-plugin/skills/<sub-command>/SKILL.md`
     (one per sub-command).
   - **How to resolve:** Author each SKILL.md body per the canonical
     body shape codified in PROPOSAL.md (above). Covers: sub-command
     trigger phrases, Bash invocations of `bin/<cmd>.py`, template
     prompt references with `@`-paths, schema validation routing,
     per-proposal confirmation dialogue (`revise` only),
     `--skip-pre-check` and `--skip-subjective-checks` handling.

This matches the v007 pattern of codifying the shape in PROPOSAL.md
and deferring the content to first-batch propose-change.

---

## Significant gaps

Items that force load-bearing implementation guesses but do not
block recreatability outright.

---

## Proposal: H5-ruff-max-args-vs-no-positional-arg-limit

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (self-contradiction within the style doc).

### Summary

The style doc contradicts itself on the positional-argument limit:

- Line 411: `[tool.ruff.lint.pylint]` sets `max-args = 6`,
  `max-branches = 10`, `max-statements = 30`.
- Line 515 (§ "Complexity thresholds"): "**No positional-arg limit**
  — Python's keyword-only args and dataclasses decompose large
  parameter sets naturally."

`max-args = 6` is a hard gate (ruff `PLR0913`); it rejects any
function with more than 6 arguments. "No positional-arg limit"
directly contradicts this. The v006 revision P9 explicitly *dropped*
the v005 args ≤ 6 rule; v007 G10 didn't reopen it. The `max-args = 6`
entry appears to be residue that was never removed from the ruff
config guidance.

### Motivation

An implementer copy-pasting the documented ruff config into
`pyproject.toml` would rediscover the v005 rule, reject any function
with more than 6 args, and force keyword-only decomposition — but the
reason for "no positional-arg limit" per P9 was that Python already
encourages keyword-only with `*,` and dataclasses; the limit adds
noise, not value.

### Proposed Changes

Drop `max-args = 6` from the style doc's ruff config. Keep
`max-branches = 10` (maps to `PLR0912`) and `max-statements = 30`
(maps to `PLR0915` — same as the function-body ≤ 30 LLOC rule).
Add a one-line note: "No `max-args` gate; Python's keyword-only args
and dataclasses decompose parameter sets naturally (v006 P9)."

Alternative: re-introduce the arg limit at a higher number (e.g., 8)
as a safety net. Not recommended; defeats the v006 P9 intent.

---

## Proposal: H6-revise-and-seed-wrapper-input-contracts

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (wrapper input shapes undefined; consequence of
incomplete G11 carry-through).

### Summary

v007 G11 resolved the LLM↔wrapper split for `propose-change` and
`critique`: the wrapper takes `--findings-json <path>`, the LLM
drives prompt invocation and schema validation. `seed` and `revise`
have the same structural need but their wrappers' inputs are
underspecified.

**`seed`** (PROPOSAL.md line 819-824):

> The LLM (per `seed/SKILL.md`) invokes the active template's
> `prompts/seed.md` with `<intent>` and the template's
> `specification-template/` starter content as input. The LLM
> validates the prompt's JSON output against the schema, then
> invokes `bin/seed.py --findings-json <tempfile>` (**or equivalent
> entry path**; the freeform-intent path is LLM-driven, the
> deterministic file-shaping is wrapper-driven).

"or equivalent entry path" is non-normative. What is the actual flag?
`--findings-json`? `--template-output`? `--seed-plan`? Seed's output
shape is the set of spec files to write (one per file from the
template's `specification-template/`), plus the `<intent>` for the
auto-captured proposed-change. That's not a findings list.

**`revise`** (PROPOSAL.md lines 906-953): describes the entire
interactive per-proposal confirmation loop as if it all happens in
one place — but `bin/revise.py` can't prompt the user (Python doesn't
invoke the LLM or dialogue). So `bin/revise.py` must take a
pre-confirmed decision set as input. The input flag is undocumented.

### Motivation

Without explicit wrapper input contracts:

- `check-public-api-result-typed` has no signature to validate
  against.
- `tests/bin/test_wrappers.py` cannot assert any argparse shape.
- The LLM-driven SKILL.md prose (H4) cannot be authored because the
  invocation target is unknown.

### Proposed Changes

Extend the G11 pattern to `seed` and `revise`:

- **`seed`**: `bin/seed.py --seed-plan <path>` (or `--files-json`,
  name TBD but committed). The LLM produces a `{"files": [{"path":
  "...", "content": "..."}, ...], "intent": "..."}` JSON object from
  `prompts/seed.md`'s output, validates it against a new
  `seed_plan.schema.json`, and invokes the wrapper. The wrapper
  writes files, creates `history/v001/`, and auto-captures the
  intent as `history/v001/proposed_changes/seed.md`.

- **`revise`**: `bin/revise.py --revise-plan <path>`. The LLM drives
  the per-proposal confirmation dialogue; once every decision is
  confirmed, the LLM assembles a `{"decisions": [{"proposal_file":
  "...", "topic": "...", "decision": "accept|modify|reject",
  "modifications": "...", "rationale": "..."}, ...]}` JSON object,
  validates it against a new `revise_plan.schema.json`, and invokes
  the wrapper. The wrapper cuts the new version, writes history,
  writes revision files, and updates working spec files.

Add the two new schema names to the `template-prompt-authoring`
deferred item in `deferred-items.md` (or split into a new
`wrapper-input-schemas` entry if authoring surface warrants it).

Update PROPOSAL.md's §"seed" and §"revise" to state the flag names
explicitly and drop "or equivalent entry path."

Alternative: `seed` writes directly from the template's output to
disk without a JSON schema intermediate — matches the current
hedged prose. Loses the schema-validated LLM↔wrapper boundary that
G11 established for propose-change and critique. Not recommended;
inconsistent.

---

## Proposal: H7-context-dataclass-fields-undefined

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness**.

### Summary

`scripts/livespec/context.py` is named as the home of "immutable
context dataclasses (`DoctorContext`, `SeedContext`, etc.) — the
railway payload" (style doc lines 231-232). Code examples reference
`ctx.project_root / ".livespec.jsonc"` (style doc line 268) and
`ctx` as the `run(ctx)` parameter in every static check. No explicit
field list for any context dataclass appears anywhere.

### Motivation

Context dataclasses are the carrier type on the railway — they hold
every piece of state that flows through the ROP chain. An implementer
needs to know:

- What fields `DoctorContext` carries (`project_root: Path`?
  `config: LivespecConfig`? `template_root: Path`? `cli_flags:
  Namespace`? `run_id: UUID`? `git_head_available: bool`?).
- Which contexts exist (`DoctorContext`, `SeedContext`,
  `ProposeChangeContext`, `ReviseContext`, `PruneHistoryContext`,
  `CritiqueContext`?).
- How they compose when a sub-command's main() needs to call
  `run_static` (does `SeedContext` subclass `DoctorContext`? contain
  one? share fields?).
- Whether any field is optional (e.g., `git_head_available` is False
  when the project isn't a git repo — used by the `out-of-band-edits`
  check to return `status: "skipped"`).

Different choices produce incompatible Python packages.

### Proposed Changes

Add an explicit subsection to the style doc (under "Package layout"
or near `livespec/context.py`) listing each context dataclass's
fields, at least for v1:

```python
@dataclass(frozen=True)
class DoctorContext:
    project_root: Path
    config: LivespecConfig
    template_root: Path
    run_id: str
    git_head_available: bool
```

Plus per-sub-command context dataclasses that either extend
`DoctorContext` or hold one plus their own fields (e.g.,
`SeedContext` holds the parsed seed plan; `ReviseContext` holds the
parsed revise plan).

Add a `context-dataclasses` entry to `deferred-items.md` if the
authoring task warrants one; otherwise codify the minimum fields in
the style doc now.

---

## Proposal: H8-doctor-allowed-tools-vs-out-of-band-edits-writes

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**malformation** (per-skill `allowed-tools` declaration contradicts
the auto-backfill behavior of one of its own static checks).

### Summary

PROPOSAL.md § "Per-sub-command skill frontmatter" (lines 155-160):

> `doctor`: Bash + Read (read-only validation; fixes route through
> `propose-change`).

`doctor` is declared read-only. But the `out-of-band-edits` static
check (PROPOSAL.md lines 1080-1099) writes files:

> it creates
> `SPECIFICATION/proposed_changes/out-of-band-edit-<UTC-seconds>.md`
> containing one `## Proposal` with the diff as `### Proposed
> Changes`. It creates a paired revision... It writes
> `history/v(N+1)/` with the current committed spec content. It
> then moves the proposed-change and revision into
> `history/v(N+1)/proposed_changes/`.

Two resolutions exist at the "allowed-tools" layer:

1. The writes happen *inside* `bin/doctor_static.py`, invoked by
   `doctor/SKILL.md` via the Bash tool. Bash has arbitrary process
   authority; nothing stops a Bash-executed Python script from
   calling `open("w")`. The skill's `allowed-tools: Bash + Read`
   means "the LLM at this skill uses only Bash and Read directly";
   it does NOT constrain what the Python process Bash spawns does.
2. The writes are part of a fix pipeline that routes through
   `propose-change`. The current PROPOSAL text suggests the Python
   *itself* writes the proposed-change + revision + history files.

If interpretation (1) is intended, the "read-only validation; fixes
route through `propose-change`" comment is misleading. If
interpretation (2) is intended, `doctor` needs `Write` in its
`allowed-tools`, OR the fix must be routed via dialogue ("LLM
observes doctor's finding, the LLM invokes `propose-change`") not
via Python auto-backfill.

### Motivation

The Claude Code `allowed-tools` mechanism is user-facing: tightly-
scoped tool lists communicate intent to the user ("this skill
won't write to my disk"). Having `doctor` silently write via a
Python subprocess contradicts that intent.

### Proposed Changes

Pick one and propagate:

- **Option A (recommended): honest Write on `doctor`.** Change
  `doctor`'s `allowed-tools` to `Bash + Read + Write` and drop
  "read-only" wording. Acknowledge that the `out-of-band-edits`
  check writes files. Update §"Per-sub-command skill frontmatter"
  and §"doctor".

- **Option B: dialogue-routed fix.** The `out-of-band-edits` check
  only *reports* drift (as a failing finding); the LLM in
  `doctor/SKILL.md` responds by invoking
  `/livespec:propose-change` via the standard dialogue flow. No
  Python auto-backfill. This is philosophically cleaner but loses
  the v004 commitment to auto-backfill drift into a spec version
  (see v004 revision).

- **Option C: explicit carve-out.** Keep `doctor`'s
  `allowed-tools: Bash + Read + Write`, but document the Write as
  "scoped to `SPECIFICATION/proposed_changes/` and
  `SPECIFICATION/history/` only; enforced by the Python wrapper,
  not by `allowed-tools`." Weaker guarantee; still honest.

Recommend A: simplest, honors Claude Code's `allowed-tools` intent
while preserving the v004 auto-backfill commitment.

---

## Proposal: H9-factory-validator-caching-mechanism

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (documented caching mechanism cannot be implemented
as-stated).

### Summary

Style doc line 226-227:

> `fastjsonschema.compile` MAY be cached at module level via
> `functools.lru_cache` keyed on the schema's `$id` field.

`functools.lru_cache` caches on the function's argument tuple. If
the caching function takes `schema: dict` (to pass to
`fastjsonschema.compile`), `dict` is unhashable and `lru_cache`
raises `TypeError: unhashable type: 'dict'`. You cannot "key an
`lru_cache` on `$id`" — the cache keys ARE the arguments.

Two workarounds exist, neither stated:

1. **Separate the cache key from the payload.** A factory
   `compile_by_id(schema_id: str, schema: dict) -> Callable` with
   `lru_cache` would dedupe on the string id only, ignoring the
   schema content. Risks stale cache if the same id is used for
   different schemas (unlikely but possible).
2. **Module-level dict.** A private `_CACHE: dict[str, Callable] =
   {}` that callers populate manually on miss. This is module-level
   mutable state and trips `check-global-writes`.
3. **`@cache` instead of `lru_cache` with frozen args.** Accept a
   `frozenset` / `tuple` schema representation. Expensive conversion
   per call.

### Motivation

The caching mechanism is called out by name in the style doc as a
performance optimization. Implementers left to invent it will
choose different paths — option 1 is the simplest but the style
doc's phrasing suggests option 2. Option 2 conflicts with
`check-global-writes`.

### Proposed Changes

Replace the style doc's phrasing with a concrete, implementable
mechanism. Recommended form:

```python
# In livespec/validate/<name>.py:
from functools import lru_cache

@lru_cache(maxsize=None)
def _compile(schema_id: str, schema_items: tuple[tuple[str, object], ...]) -> Callable[[dict], None]:
    return fastjsonschema.compile(dict(schema_items))

def validate_<name>(payload: dict, schema: dict) -> Result[T, ValidationError]:
    compiled = _compile(schema["$id"], tuple(sorted(schema.items())))
    ...
```

Or, mirroring the G4 factory shape:

- `validate/<name>.py` holds the pure `validate_<name>(payload,
  schema)` function.
- The *compile* step lives in `livespec/io/fastjsonschema_facade.py`
  (impure boundary; effect is compute-heavy but stateless) and uses
  a module-level `dict[str, Callable]` keyed on `$id`. The facade
  gets the `check-global-writes` exemption (single documented
  exemption in the ast-check-semantics deferred item).

Pick one and codify. Recommend the facade+dict approach: keeps
`validate/` pure, gets the cache out of the pure path, and extends
the existing exemption pattern established for `structlog.configure`.

---

## Proposal: H10-findings-to-proposal-section-mapping

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity**.

### Summary

PROPOSAL.md § "propose-change" line 861-863:

> The wrapper validates the JSON against
> `scripts/livespec/schemas/critique_findings.schema.json` and maps
> each finding to one `## Proposal` section.

The mapping is deterministic wrapper logic. What mapping?

A finding's shape (per the doctor static-phase output contract):

```json
{ "check_id": "...", "status": "fail", "message": "...", "path": "...", "line": null }
```

A `## Proposal` section's required sub-headings (§"Proposed-change
file format"):

- `### Target specification files`
- `### Summary`
- `### Motivation`
- `### Proposed Changes`

No deterministic mapping exists between finding fields and proposal
sub-headings. Possibilities:

- `check_id` → proposal name?
- `path` → Target specification files?
- `message` → Summary?
- The raw finding JSON → Proposed Changes (as fenced code block)?

The `critique` template prompt's output schema is more likely to
carry explicit proposal-section content (given it produces
proposals, not findings); the `critique_findings.schema.json` name
and the propose-change wrapper's findings-to-proposal mapping
suggest the findings themselves are richer than the doctor-static
contract. But this is speculation; the schemas are deferred via
`template-prompt-authoring`.

### Motivation

v007's G11 resolution committed to "`bin/propose_change.py` only
accepts `--findings-json <path>`." The wrapper must then
deterministically produce a proposed-change file from that JSON.
Without a documented mapping, the wrapper is undefined.

The `template-prompt-authoring` deferred item covers the *schema*,
but the mapping from schema-valid findings to proposal sections is
wrapper behavior, not template behavior.

### Proposed Changes

Two complementary actions:

1. Codify in PROPOSAL.md § "propose-change" that the
   `critique_findings.schema.json` schema is NOT the doctor static
   finding shape. It is a richer "proposal-findings" schema whose
   each item has exactly the fields needed to produce a `##
   Proposal` section:

   ```json
   {
     "findings": [
       {
         "name": "fix-retry-policy",
         "target_spec_files": ["SPECIFICATION/spec.md"],
         "summary": "...",
         "motivation": "...",
         "proposed_changes": "..."
       }
     ]
   }
   ```

   Rename the schema to `proposal_findings.schema.json` to reduce
   confusion with doctor findings. (Doctor findings are
   `{check_id, status, message, path, line}`; they are only used
   within doctor and not passed to `propose-change`.)

2. Expand the `template-prompt-authoring` deferred item to name both
   schemas separately: `proposal_findings.schema.json` (propose-
   change/critique template output) and the implicit doctor finding
   shape (already documented in PROPOSAL.md § "Static-phase output
   contract").

Alternative: leave the mapping ambiguous and let the deferred
`template-prompt-authoring` item pick the schema shape. Weakens
recreatability; the wrapper is a load-bearing contract point.

---

## Proposal: H11-out-of-band-edits-comparison-semantics

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity**.

### Summary

PROPOSAL.md § `out-of-band-edits` (lines 1080-1099):

> The diff between committed spec state (`git show HEAD:<path>` for
> each spec file) and the latest `history/vN/` copies is empty.

What does "the latest `history/vN/` copies" resolve to? Two
interpretations:

- **(a) Committed `history/vN/`**: `git show HEAD:history/vN/spec.md`.
  Compare two committed artifacts: the active spec file at HEAD and
  the latest history version at HEAD. This detects the case where
  a user edited `SPECIFICATION/spec.md` without running `revise`
  — the file at HEAD differs from the archived history at HEAD.
- **(b) Working-tree `history/vN/`**: the file on disk at
  `history/vN/spec.md` (whatever its commit state). Compare
  committed active spec to working-tree history archive. This
  introduces bidirectional drift detection (WIP history edits also
  fail the check).

(a) aligns with the v004 revision's move from working-tree to
committed-state comparison (intended to make the check stable
across WIP). (b) treats history as always-authoritative regardless
of WIP state.

### Motivation

This is subtly important because the `out-of-band-edits` auto-
backfill behavior writes to the working tree: it creates a new
`history/v(N+1)/` with the current HEAD spec content. On the next
run, should the check consider the just-written (uncommitted)
`history/v(N+1)/` as "the latest"? Under (a), no — uncommitted files
aren't in HEAD, and the check compares against the last committed
vN. Under (b), yes — it's on disk, and the check sees it.

The v004 revision seems to favor (a), but PROPOSAL.md's phrasing is
ambiguous.

### Proposed Changes

Clarify PROPOSAL.md to read:

> The `out-of-band-edits` check compares `git show HEAD:<path>`
> for each active spec file to `git show HEAD:history/vN/<path>`
> at the committed HEAD state. Both sides are HEAD-committed
> artifacts; working-tree WIP (including the just-written
> auto-backfill `history/v(N+1)/`) is ignored by the check.

Add: "After auto-backfill, the check expects the user to commit the
new `history/v(N+1)/` files; re-running `livespec doctor` before
commit will still fail the check (because HEAD still has only vN)
with the same backfill instruction, making the cycle non-destructive."

Alternative: switch to (b) (working-tree history), with the
motivation that WIP history is the user's intent. Changes the v004
invariant; not recommended.

---

## Proposal: H12-skill-owned-directory-readme-content

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness**.

### Summary

PROPOSAL.md § "SPECIFICATION directory structure (livespec
template)" (lines 491-495):

> The directory-README files in top-level `proposed_changes/` and
> `history/` are **skill-owned**: hard-coded inside the skill,
> written by `seed` only, not regenerated on every `revise`. Their
> content is a one-paragraph description of the directory's purpose
> and the filename convention used there.

The *content* of these one-paragraph descriptions is undefined.
`seed` writes both files; both are hard-coded inside the skill.
Different implementers will write different paragraphs. That's not
a severe gap (neither file is load-bearing in the sense of doctor
reading them) but it IS recreatability-relevant.

### Motivation

Hard-coded strings in the skill are exactly the kind of artifact
the recreatability test asks about: an implementer with no prior
spec history has to produce the exact strings. They can't.

### Proposed Changes

Add the two paragraphs verbatim to PROPOSAL.md, e.g.:

**`SPECIFICATION/proposed_changes/README.md`**:

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

**`SPECIFICATION/history/README.md`**:

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

Paragraphs above are suggestions; the user may rephrase. The
commitment is: the text is frozen in PROPOSAL.md.

---

## Smaller items / cleanup

These are wording and reference fixes; none affect architecture.

---

## Proposal: H13-bcp14-typo-list-enumeration

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness**.

### Summary

PROPOSAL.md § `bcp14-keyword-wellformedness` (lines 1100-1104):

> Misspelled uppercase BCP 14 keywords from a finite list
> (`MUSNT`, `SHOLD`, `SHAL`, etc.), and mixed-case BCP 14 keywords
> appearing as standalone words (`Must`, `Should`, `May`).

The "finite list" is not enumerated. `MUSNT`, `SHOLD`, `SHAL`, and
"etc." communicate intent but not the exact set. Two implementers
would pick different lists.

### Proposed Changes

Enumerate the list in PROPOSAL.md:

Misspellings detected (case-sensitive, uppercase context):
- `MUSNT`, `MUSTNOT` (missing space/punctuation), `MUSTN'T`
- `SHOLD`, `SHULD`, `SHOUDL`
- `SHAL`, `SHLL`
- `MAYBE` (when adjacent to "SHALL", "MUST", "SHOULD" phrasing)

Mixed-case standalone-word detection: any of `Must`, `Should`,
`May`, `Shall`, `Optional`, `Required`, `Recommended` appearing as
a standalone word (token-boundary match) inside a sentence where
the nearest sentence-level verb-of-requirement is also present.
Sentence-level context is deferred to the LLM-driven phase (per
the existing proposal).

Alternative: defer the exact list to `ast-check-semantics` (already
covers AST enforcement checks; extend to markdown-parsing checks).

---

## Proposal: H14-anchor-reference-resolution-algorithm

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity**.

### Summary

PROPOSAL.md § `anchor-reference-resolution` (lines 1114-1117):

> All Markdown links in all files under `SPECIFICATION/` (spec
> files, READMEs, proposed-change files, revision files) with
> anchor references resolve to existing headings in the referenced
> files.

Undefined:

- Which anchor-generation algorithm? GitHub-flavored (lower, space
  → hyphen, strip punctuation)? CommonMark (no standard anchor)?
  Custom?
- Are headings inside fenced code blocks counted? GitHub doesn't
  render them as headings.
- Case sensitivity on the anchor? GitHub lowercases.
- Anchors that use explicit `{#custom-id}` syntax? Some Markdown
  flavors support it.

### Proposed Changes

Specify GitHub-flavored anchor generation:

> Anchor references use GitHub-flavored slug generation: lowercase
> the heading text, replace internal spaces with hyphens, strip
> punctuation except hyphens and underscores, collapse multiple
> hyphens into one. Headings inside fenced code blocks are not
> considered headings. Explicit `{#custom-id}` syntax is not
> supported in v1 (the slug generator alone suffices).

Add to the `ast-check-semantics` deferred item: extend scope to
markdown-parsing checks (anchor-reference-resolution,
gherkin-blank-line-format, bcp14-keyword-wellformedness), OR split
into a new `markdown-check-semantics` entry in `deferred-items.md`.

---

## Proposal: H15-tests-fixtures-claude-md-carve-out

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity**.

### Summary

v007 G7 canonicalized CLAUDE.md coverage as: "every directory under
`scripts/` (with `_vendor/` and its entire subtree explicitly
excluded), every directory under `tests/`, and every directory under
`dev-tooling/`."

`tests/fixtures/` is a directory under `tests/`. Its subdirectories
(fixtures for each test subject) are also directories under `tests/`.
Does each require a CLAUDE.md?

Fixture directories typically hold static test inputs (sample
`.livespec.jsonc` files, sample proposed-changes, etc.). A CLAUDE.md
inside a fixture directory arguably conflicts with the rule that
"tests MUST NOT mutate fixtures" — a CLAUDE.md is part of the fixture
tree and could be read by tests as fixture content.

### Proposed Changes

Add a carve-out to both PROPOSAL.md DoD #13 and the style doc's
CLAUDE.md coverage rule:

> `tests/fixtures/` and its entire subtree are excluded from
> `check-claude-md-coverage`.

One `tests/fixtures/CLAUDE.md` at the fixtures root (not
recursively) is optional; if present, it states "this tree is
read-only test input — fixtures must not be mutated."

Alternative: require CLAUDE.md recursively in fixtures/. Weakest
option; pollutes the fixture tree.

---

## Proposal: H16-seed-autogenerated-proposed-change-content

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness**.

### Summary

PROPOSAL.md § "seed" (lines 833-837):

> Captures the seed itself as a proposed-change in
> `history/v001/proposed_changes/seed.md` (one `## Proposal` with
> `<intent>` as its `### Proposed Changes` section) plus a paired
> auto-created `history/v001/proposed_changes/seed-revision.md`
> with `decision: accept`, `reviser_llm: livespec-seed`, and
> rationale "auto-accepted during seed."

The proposed-change file format requires all four sub-headings:
`### Target specification files`, `### Summary`, `### Motivation`,
`### Proposed Changes`. The seed auto-captures only `Proposed
Changes`. What fills the other three?

- `Target specification files`: every file the template's
  `specification-template/` produced? Every file under
  `SPECIFICATION/`?
- `Summary`: a canonical one-liner?
- `Motivation`: another copy of `<intent>`?

### Proposed Changes

Specify in PROPOSAL.md § "seed":

> The auto-generated `seed.md` contains:
> - `### Target specification files`: the list of every file path
>   (repo-root-relative) written at seed time by the template, one
>   per line.
> - `### Summary`: "Initial seed of the specification from
>   user-provided intent."
> - `### Motivation`: the verbatim `<intent>` provided by the user.
> - `### Proposed Changes`: the verbatim `<intent>` provided by
>   the user (or, optionally, a summary of the template's output
>   when `<intent>` was minimal).

Alternative: relax the proposed-change file format to make
`Summary` and `Motivation` optional when `decision: accept` is
auto-generated. Breaks the uniform-format invariant; not
recommended.

---

## Recreatability summary

After applying every fix above, can a competent implementer recreate
v007 livespec from PROPOSAL.md + python-skill-script-style-
requirements.md + livespec-nlspec-spec.md + deferred-items.md alone?
Yes.

Today, without the fixes: **no**. H1 (bootstrap sys.path) is a
load-bearing import failure; H2 (JSONC parser) blocks
`.livespec.jsonc` parsing; H3 (argparse seam) trips the
supervisor-discipline AST gate on first use; H4 (SKILL.md prose
content) leaves every sub-command's LLM-driven behavior undefined.

The remaining items (H5-H16) force implementers to make load-bearing
guesses or to file follow-up propose-changes for mechanics that
should be codified. They do not block, but they erode the
spec-as-contract guarantee.

---

## Sequencing for the interview

- **H1-H4 are foundational integration gaps.** Settle them first,
  in order. H1 (bootstrap) and H2 (JSONC) are independent. H3
  (argparse) depends on the `io/` layer discipline; H4 (SKILL.md
  prose) depends on H6's wrapper contracts being nailed down.
- **H5-H12 are significant gaps** and can mostly be interviewed
  independently; H6 (seed/revise wrapper contracts) and H10
  (findings-to-proposal mapping) interact.
- **H13-H16 are cleanup** and can be batched at the end.

Every `deferred-items.md` entry carried forward from v007 remains
in scope; items H2 (`jsonc-parser`), H4 (`skill-md-prose-authoring`),
and potentially H6 (if schemas are added) introduce new deferred
entries.

I will proceed in that order, one question per turn, reading each
item's options aloud before asking.
