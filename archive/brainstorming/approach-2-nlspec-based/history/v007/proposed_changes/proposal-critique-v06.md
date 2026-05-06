---
topic: proposal-critique-v06
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-22T18:00:00Z
---

# Critique scope

This critique evaluates **v006 PROPOSAL.md** plus its companion
`python-skill-script-style-requirements.md` against the embedded
`livespec-nlspec-spec.md` guidelines, with primary focus on what
the v005→v006 language migration left underspecified or
self-contradictory.

The v006 revision (`history/v006/proposed_changes/proposal-critique-v05-revision.md`)
locked in 22 dispositions (P1-P22) covering Python floor, vendoring,
ROP, ruff/pyright/pytest, just/lefthook/CI, and CLAUDE.md coverage.
This critique does **not** reopen any of those decisions. It asks the
narrower question: **given those decisions, can a competent
implementer recreate the livespec plugin from PROPOSAL.md +
python-skill-script-style-requirements.md + livespec-nlspec-spec.md
alone?**

The recreatability test surfaces gaps in two clusters:

1. **Cross-document integration drift.** PROPOSAL.md and the Python
   style doc were authored in the same pass and agree on most
   load-bearing facts, but disagree on the scope of CLAUDE.md
   coverage, on how impure operations integrate with the "purity by
   directory" rule, and on who owns pre/post-step doctor invocation.
2. **Missing seams introduced by the language flip.** Bash had a
   single-process model where `dispatch` invoked `run-static`;
   Python introduces import semantics, sys.path setup, package
   discovery, and ROP supervisor boundaries that v006 partially
   addresses but does not tie together end-to-end.

Items are labelled `G1`–`G18` (the `G` prefix distinguishes "v006
gap" findings from prior critiques' `B`-prefixed style-doc items
and the older numbered series). Each item is labelled with one of
the four NLSpec failure modes:

- **ambiguity** — admits multiple incompatible interpretations.
- **malformation** — self-contradiction within or across documents.
- **incompleteness** — missing information needed to act.
- **incorrectness** — internally consistent but specifies behavior
  that cannot work as written.

Major gaps appear first (block recreatability outright), then
significant gaps (force the implementer to make load-bearing
guesses), then smaller cleanup items.

---

## Major gaps

These items would block a competent implementer from producing
a working v006 livespec without filing additional propose-changes.

---

## Proposal: G1-python-import-path-bootstrap

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (recreatability defect).

### Summary

How `from livespec.commands.seed import main` actually resolves at
the Python interpreter level is undocumented. The shebang-wrapper
contract forbids logic beyond a 5-line shape; `python3 bin/seed.py`
adds `bin/` to `sys.path`, not the parent `scripts/` directory. The
import will fail on a clean install.

### Motivation

PROPOSAL.md (lines 114-118) and the style doc (lines 502-516) jointly
mandate: each `bin/<cmd>.py` is ≤ 5 lines matching exactly:

```python
#!/usr/bin/env python3
"""Shebang wrapper for <description>. ..."""
from livespec.<module>.<submodule> import main

raise SystemExit(main())
```

The wrapper "MUST NOT" contain other content. But `python3 bin/seed.py`
puts `<bundle>/scripts/bin/` on `sys.path[0]` (Python's
"script-directory" rule). The `livespec` package lives at
`<bundle>/scripts/livespec/`, which is not on `sys.path`. Imports fail.

The style doc says "`scripts/livespec/__init__.py` MUST insert
`_vendor/` into `sys.path` at import time" (lines 122-124) — but
`__init__.py` runs only **after** `livespec` is successfully imported.
It can't bootstrap its own discoverability.

Three plausible recovery mechanisms exist; the proposal picks none of
them:

1. **`PYTHONPATH` set by SKILL.md.** SKILL.md tells the LLM to
   invoke wrappers with `PYTHONPATH=<bundle>/scripts python3
   <bundle>/scripts/bin/seed.py`. Pollutes every invocation; makes
   path manipulation a wire-contract.
2. **`-m` invocation.** Skill invokes `python3 -m livespec.bin.seed`
   from the bundle root. Requires `bin/` to be a Python package
   (with `__init__.py`); changes the wrapper layout.
3. **`sys.path` insert in the wrapper.** Wrapper opens with
   `import sys; sys.path.insert(0, str(Path(__file__).parent.parent))`
   before any `livespec` import. Adds 2-3 lines and explicitly
   violates the "no logic; ≤ 5 lines" wrapper-shape rule.

The orchestration is load-bearing (every wrapper invocation depends
on it) and missing.

### Proposed Changes

Pick one mechanism and document it in both PROPOSAL.md (under
"Skill layout inside the plugin") and the style doc (under
"Shebang-wrapper contract"). Likely the cleanest path:

- Allow the wrapper to exceed 5 lines for the explicit purpose of
  adding the bundle's `scripts/` directory to `sys.path` before
  importing `livespec`. Update the style doc's wrapper shape to:

  ```python
  #!/usr/bin/env python3
  """Shebang wrapper for <description>. No logic; see livespec.<module> for implementation."""
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
  from livespec.<module>.<submodule> import main

  raise SystemExit(main())
  ```

- Update `check-wrapper-shape` to accept the augmented shape.
- Document the "add `<bundle>/scripts/` to `sys.path`" requirement
  separately from the "no business logic" requirement so they
  cannot be conflated.

Alternative: switch to `python3 -m livespec.bin.<cmd>` invocation
under SKILL.md, keep wrappers at 5 lines, and require an `__init__.py`
under `bin/` (turning `bin/` into a package). Either resolution
works; the proposal must commit to one and reflect it consistently.

---

## Proposal: G2-yaml-front-matter-parser-missing

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (recreatability defect).

### Summary

Both proposed-change files (lines 1015-1024) and revision files
(lines 1052-1063) carry YAML front-matter that doctor's static phase
must parse and validate. The vendored libraries are
`dry-python/returns`, `fastjsonschema`, and `structlog`. **None of
them parse YAML.** The runtime-deps section explicitly forbids any
other dependency. There is no path to validate front-matter as
specified.

### Motivation

PROPOSAL.md DoD #9 (lines 1334-1336): "The proposed-change and
revision file formats are enforced by doctor's static phase (YAML
front-matter validated; required headings present per decision
type)."

`fastjsonschema` validates **dicts** against JSON Schema Draft-7;
it does not parse YAML. Python's stdlib has no YAML parser
(`tomllib` is 3.11+ and is for TOML, which the proposal
explicitly forbids using).

The v005 PROPOSAL.md (line 379-381) implicitly relied on `jq` for
front-matter "structural" checks (treating front-matter as
JSON-ish). v006 dropped `jq` (line 146-148: "No `jq`. No PyPI
install step.") and replaced it with fastjsonschema — but fastjsonschema
is not a parser.

Three options the proposal should pick from:

1. **Hand-roll a restricted-YAML parser.** Front-matter is restricted
   enough (`---`, scalar `key: value` lines, no nested structures)
   that ~50 LLOC handles every documented field. Codify the format
   restriction so it cannot regress (e.g., "front-matter values
   MUST be scalars; no lists, no nested dicts").
2. **Vendor a pure-Python YAML library.** `strictyaml` (MIT,
   pure Python) or a stripped subset of PyYAML. Adds a fourth
   vendored lib; the user already authorized vendoring as a precedent
   for permissive pure-Python libs.
3. **Re-shape front-matter as JSON.** Replace `---\n…\n---` with
   inline JSON in a fenced code block at the top of each file.
   stdlib `json` parses it. Breaks compatibility with prior
   versions' front-matter shape.

### Proposed Changes

Recommend option (1): hand-roll the restricted parser at
`scripts/livespec/parse/front_matter.py` (pure module, returns
`Result[FrontMatter, ParseError]`). Document the format restrictions
in PROPOSAL.md's "Proposed-change file format" and "Revision file
format" sections so the parser surface stays narrow forever:

- Front-matter values MUST be JSON-compatible scalars: strings (no
  multi-line, no quote-escape ambiguity), integers, booleans
  (`true`/`false`), or `null`.
- No lists, no nested dicts, no anchors, no tags, no flow style.
- Keys MUST be the documented set (`topic`, `author`, `created_at`
  for proposed-change files; `proposal`, `decision`, `revised_at`,
  `reviser_human`, `reviser_llm` for revision files); unknown
  keys are a parse error.

The schema validator (fastjsonschema) then validates the parsed
dict against `front_matter.schema.json` for type and presence.

If the user prefers vendoring (option 2), name the library
explicitly in the style doc's vendored-libs list and add it to
`NOTICES.md`.

---

## Proposal: G3-init-version-check-violates-no-raise-rule

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (self-contradiction).

### Summary

Two rules conflict:

1. Style doc lines 72-75: "The package `livespec/__init__.py` MUST
   assert `sys.version_info >= (3, 10)` at import time and raise
   `ToolMissingError` (exit 127) if older."
2. Style doc lines 211-214 (ROP) + check `check-no-raise-outside-io`:
   "**No `raise` statements** outside `io/**` and `errors.py`."

`livespec/__init__.py` is in `livespec/` (not `livespec/io/` or
`livespec/errors.py`). The mandated `raise ToolMissingError(...)`
is exactly the construct the AST check rejects. Any attempt to
implement (1) fails the gate at (2).

### Motivation

PROPOSAL.md DoD #11 (lines 1342-1344) restates the same: "python3
>= 3.10 presence check is implemented at import time in
`scripts/livespec/__init__.py`; the skill exits 127 with an
actionable install instruction if older."

`check-supervisor-discipline` (style doc line 217-218) also rejects
`sys.exit` outside `bin/*.py`. Every available exit mechanism is
forbidden in `__init__.py`.

A subtler ordering issue compounds the contradiction: `__init__.py`
must perform the version check **before** importing anything from
the vendored `_vendor/` libs (which themselves may use 3.10+
syntax). It must also bootstrap `sys.path` for `_vendor/` (lines
122-124). And it must import `errors.py` to construct
`ToolMissingError`. That is a precise execution order which the
proposal does not document, and which the no-raise-outside-io rule
forbids regardless.

### Proposed Changes

Move the version assertion **out** of `__init__.py` and into each
`bin/*.py` wrapper, before the `from livespec... import main` line:

```python
#!/usr/bin/env python3
"""..."""
import sys
if sys.version_info < (3, 10):
    sys.stderr.write("livespec requires Python 3.10+; install via your package manager.\n")
    raise SystemExit(127)
# (sys.path bootstrap from G1)
from livespec.commands.seed import main

raise SystemExit(main())
```

This:
- Keeps `raise SystemExit` (allowed in `bin/*.py` per
  `check-supervisor-discipline`).
- Avoids importing `livespec.errors` before the version check.
- Avoids `__init__.py` raising at all.

Update style doc § "Interpreter and Python version" to specify the
wrapper-level check, and remove the `__init__.py` assertion language.
Update `check-wrapper-shape` to accept the version-check stanza
alongside the (G1) `sys.path` stanza.

Alternative: define `__init__.py` as exempt from
`check-no-raise-outside-io` (a one-line carve-out). This is
weaker — it prefers a special case over a clean placement.

---

## Proposal: G4-pure-validators-load-schemas-from-disk

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (self-contradiction).

### Summary

Two rules conflict:

1. Style doc § "Purity and I/O isolation" (lines 246-267):
   "`livespec/parse/**` and `livespec/validate/**` are PURE.
   Modules here MUST NOT import from … filesystem APIs (`open`,
   `pathlib.Path.read_text`, `.read_bytes`, `.write_text`,
   `.write_bytes`, any `os.*` I/O function)."
2. Style doc line 186-187: "`validate/` — pure validators. Uses
   `fastjsonschema` loaded from `../schemas/*.schema.json`. Returns
   `Result[T, ValidationError]`."

`*.schema.json` is on disk. `fastjsonschema.compile(schema)` takes
a parsed dict, but **someone** has to read the file from disk first.
If `validate/` does the read, it violates rule (1). If `io/` does the
read, then `validate/` must accept the schema dict as a parameter
(or via a registry initialized elsewhere) — the style doc does not
say which.

### Motivation

The contradiction has a cascade effect: the style doc invariably
references "validate/livespec_config.py validates against
livespec_config.schema.json" without specifying the call shape.
A reader cannot determine whether:

- Validators are factories: `validate_livespec_config(config: dict,
  schema: dict) -> Result[Config, ValidationError]` (pure; schema
  injected by caller).
- Validators are module-loaded: a one-time `_VALIDATOR =
  fastjsonschema.compile(_SCHEMA)` at module top, where `_SCHEMA`
  was loaded by some other code at import time and stuffed in.
- Validators are eager: each call reads the schema file fresh
  (impure; violates the rule).

Each has different testing implications and different ROP shape.

### Motivation continued — fastjsonschema specifics

`fastjsonschema.compile(schema_dict)` returns a callable that
validates dicts against the compiled schema. Compilation is non-
trivial work the implementer would naturally cache. Where? A
module-level constant in `validate/` is the easiest answer, but it
embeds the schema as a Python literal (drift risk: schema file and
literal can diverge). Loading at import time keeps a single source
of truth but introduces filesystem I/O at import.

### Proposed Changes

Resolve by mandating the **factory** shape:

- Style doc's `validate/` description: "Each validator module
  exposes a single function `validate_<name>(payload: dict,
  schema: dict) -> Result[T, ValidationError]`. Callers read the
  schema JSON via `io/` wrappers and pass the parsed dict in.
  `fastjsonschema.compile` MAY be cached at module level using
  `functools.lru_cache` keyed on the schema's `$id` field."
- PROPOSAL.md's references to `fastjsonschema` validation under
  `validate/` and to `.livespec.jsonc` schema validation are
  rewritten to call out the load step (`io.fs.read_jsonc`) plus
  the validation step (`validate.livespec_config.validate`).

This keeps `validate/` strictly pure, makes the railway compose
cleanly, and tests can hand a schema dict directly to validators
without touching the filesystem.

---

## Proposal: G5-pre-and-post-step-doctor-orchestration-undefined

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (admits multiple incompatible implementations).

### Summary

PROPOSAL.md (lines 627-642) mandates pre-step doctor static (every
sub-command except `help` and `doctor`), and post-step doctor
(static + LLM-driven phase, after `seed` / `propose-change` /
`critique` / `revise`). v006's Python-only architecture removes
the v005 bash dispatcher that made this orchestration concrete.
Who runs pre-step and post-step now is undocumented. Three
incompatible implementations are all consistent with the prose:

1. **Each `bin/<cmd>.py` invokes `bin/doctor_static.py` as a
   subprocess** before and after its main work. Forces every
   wrapper to exceed the 5-line shape; introduces process
   forking; can't run the post-step LLM-driven phase (Python
   doesn't invoke the LLM, per turn 23 of the v006 conversation).
2. **`livespec.commands.<cmd>.main()` invokes
   `livespec.doctor.run_static.run_static` in-process** (single
   ROP chain), then runs its own logic, then re-runs the static
   phase. Same can't-invoke-LLM issue for post-step LLM-driven
   phase. Static-only post-step is partial coverage of the
   documented requirement.
3. **The LLM (per `commands/<cmd>.md` skill prose) orchestrates
   all three steps**: invoke `bin/doctor_static.py`, then
   `bin/<cmd>.py`, then `bin/doctor_static.py`, then drive the
   LLM-driven phase from `commands/doctor.md` prose. This is the
   only option compatible with both ROP-all-the-way-down (Python
   never calls the LLM) and the LLM-driven-phase requirement.

Option (3) is almost certainly intended, but PROPOSAL.md's
imperative voice ("Every sub-command MUST run doctor's static
phase as its first step") reads as if the sub-command code itself
runs it. The mismatch matters: if a downstream agent reads
PROPOSAL.md and implements option (1) or (2), the LLM-driven
post-step never runs.

### Motivation

The v006 conversation (turn 23) explicitly resolved that "Python
scripts handle only deterministic work; LLM-driven logic lives at
the skill-markdown layer." The CLI flag `--skip-pre-check` is
described as going to "any sub-command" — but if the LLM drives
pre-step, the flag must be parsed by the LLM-prose orchestrator,
not by the wrapper. The flag's home is currently undefined.

`--skip-subjective-checks` has the same ambiguity: it gates the
LLM-driven phase, so it can't be parsed by `bin/doctor_static.py`
(which only runs the static phase). It must be a SKILL-prose flag
the LLM honors when invoking commands/doctor.md prose.

### Proposed Changes

Add a new top-level section to PROPOSAL.md, "Sub-command lifecycle
orchestration", that explicitly assigns ownership:

- The **LLM** (per `commands/<cmd>.md` prose) is responsible for
  invoking pre-step doctor, the sub-command wrapper, and post-step
  doctor in sequence. Each `commands/<cmd>.md` MUST document this
  sequence.
- Pre-step: LLM reads `.livespec.jsonc` + CLI flags; if
  `pre_step_skip_static_checks` (or `--skip-pre-check`) is set,
  emits a warning narration and skips the static-phase invocation.
  Otherwise invokes `bin/doctor_static.py`; aborts if exit ≠ 0.
- Sub-command: LLM invokes `bin/<cmd>.py` with the user's args
  (forwarding `--skip-subjective-checks` if present, since the
  Python wrapper passes it back to the LLM via... actually this
  flag never reaches Python; it's purely an LLM-layer flag).
- Post-step: LLM invokes `bin/doctor_static.py` again, then drives
  the LLM-driven phase per `commands/doctor.md` prose, honoring
  `--skip-subjective-checks` / `post_step_skip_subjective_checks`.

Update PROPOSAL.md's `### Per-invocation CLI overrides` section to
clarify: `--skip-pre-check` and `--skip-subjective-checks` are
**LLM-layer flags** the user passes in their dialogue; they do not
reach the Python wrappers.

Update `commands/doctor.md` and each `commands/<cmd>.md` (skill
prose, written at implementation time) to encode this orchestration.

---

## Significant gaps

Items that force the implementer to make load-bearing guesses but
do not block recreatability outright.

---

## Proposal: G6-ast-checks-for-deferred-purity-and-import-hygiene

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (cascade of small undefined behaviors).

### Summary

The style doc names a number of AST-level enforcement checks
(`check-purity`, `check-private-calls`, `check-import-graph`,
`check-global-writes`, `check-supervisor-discipline`,
`check-no-raise-outside-io`, `check-public-api-result-typed`,
`check-main-guard`, `check-wrapper-shape`) but does not specify the
behavioral edge cases that determine pass/fail. Implementers will
reach reasonable but mutually incompatible decisions on each.

### Motivation

Examples of unaddressed edge cases:

- **`check-purity`:** can `parse/` and `validate/` import from
  `pathlib` for *path manipulation* (joining paths, parsing parts)
  but not for I/O? `Path.read_text()` is I/O; `Path.parts` is not.
  An import-level ban on `pathlib` is too coarse; a function-call
  AST inspection is finer-grained.
- **`check-private-calls`:** the rule is "no cross-module calls to
  `_`-prefixed functions defined elsewhere." Does this apply
  intra-package (`livespec.parse._helper` from
  `livespec.validate.config`) or cross-package only? Module-level
  re-export via `__all__` should presumably bypass; not stated.
- **`check-import-graph`:** Python supports deferred imports inside
  function bodies for breaking cycles. Does the check inspect
  module-level imports only, or all imports including in-function
  ones?
- **`check-no-raise-outside-io`:** does it apply to `raise Foo()
  from None` re-raises? to `assert` statements (which raise
  `AssertionError`)? to `raise StopIteration` inside generators?
- **`check-public-api-result-typed`:** the rule says every public
  function returns `Result` or `IOResult`. What is "public"? The
  rest of the doc says "single-leading-underscore" denotes private,
  but a module-level function with no leading underscore in
  `livespec.commands.seed` is "public" within the package even if
  not part of any external API.
- **`check-main-guard`:** the rule "no `if __name__ ==
  "__main__":` in `livespec/`" is well-defined; but the rule's
  rationale (P12) says executable-ness is externalized to
  `bin/`. Tests at `tests/livespec/...` may legitimately want a
  bottom-of-file `if __name__ == "__main__":` to support
  `python tests/livespec/.../test_x.py` debugging. The check
  scope (`livespec/` only) excludes `tests/`, but the doc doesn't
  say so.

### Proposed Changes

Add a new sub-section "AST check semantics" under "Enforcement
suite" listing each AST check's:

- Exact AST node types it inspects (`ast.Import`, `ast.ImportFrom`,
  `ast.Call`, `ast.Raise`, `ast.FunctionDef`, etc.).
- Scope (file globs the check applies to / excludes).
- Edge-case dispositions (deferred imports, `__all__` re-exports,
  `assert`, generator `raise StopIteration`, etc.).

Or, alternatively, defer all AST-check behavior specifications to
"first-batch post-seed propose-change" and remove the implication
from PROPOSAL.md that the checks are recreatable from v006 alone.

---

## Proposal: G7-claude-md-coverage-rule-disagreement

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (cross-document inconsistency).

### Summary

Three documents disagree on the scope of CLAUDE.md coverage:

| Source | Scope |
|---|---|
| PROPOSAL.md line 130-131 ("Skill layout inside the plugin") | every directory under `scripts/` |
| PROPOSAL.md line 1284 ("Developer tooling layout") | every directory under `dev-tooling/` |
| PROPOSAL.md DoD #13 (line 1356) | `scripts/`, `tests/`, `dev-tooling/` |
| Style doc § "Agent-oriented documentation" lines 599-612 | `scripts/` and `tests/` only |
| Style doc § "Enforcement suite" line 570 (`check-claude-md-coverage`) | `scripts/` and `tests/` only |
| v006 revision P22 (file list) | 11 dirs under `scripts/`; "analogous tree under `tests/`" — `dev-tooling/` not enumerated |

A second contradiction: the rule "every directory under `scripts/`"
is recursive. `scripts/_vendor/returns/` and its subpackages are
"directories under `scripts/`". Adding CLAUDE.md inside vendored
trees triggers `check-vendor-audit` failures (because vendored
content drifted from upstream). Style doc § "Scope" line 36-39
exempts `_vendor/` from livespec's rules generally — but
`check-claude-md-coverage` is not carved out.

### Proposed Changes

Pick one canonical scope and propagate it everywhere:

- Recommend: every directory under `<bundle>/scripts/` (with
  `_vendor/` and its subtree explicitly excluded), every directory
  under `<repo-root>/tests/`, and every directory under
  `<repo-root>/dev-tooling/`.
- Update PROPOSAL.md line 130-131 to reference the same scope as
  DoD #13.
- Update style doc § "Agent-oriented documentation" lines 599-600
  to add `dev-tooling/` and explicitly exclude `_vendor/` and its
  subtree.
- Update `check-claude-md-coverage` description (style doc line
  570) to match.
- Update v006 revision P22 file list to enumerate the dev-tooling
  directories.

This is a one-pass cleanup; it does not change any architectural
decision, only ties the prose together.

---

## Proposal: G8-orchestrator-discovery-and-typing

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (admits incompatible implementations).

### Summary

PROPOSAL.md lines 826-829: "The orchestrator
`scripts/livespec/doctor/run_static.py`: Discovers check modules by
glob over `scripts/livespec/doctor/static/` (lexicographic order).
Imports each module and calls `module.run(ctx)` in-process."

This is dynamic discovery via filesystem glob + `importlib`. Pyright
strict cannot type-check dynamically discovered modules; their
`run()` return types are `Unknown` to the type checker. The
orchestrator's `Fold.collect(results, IOSuccess(()))` therefore
cannot be statically validated — yet `check-types` is gating.

Three plausible implementations:

1. **Truly dynamic.** `pathlib.Path.glob` + `importlib.import_module`.
   Type checker sees the orchestrator as untyped; some `# type:
   ignore` comments are required. Conflicts with the style-doc
   rule (line 285) that `# type: ignore` requires a narrow
   justification — but here the justification is structural, not
   narrow.
2. **Static registry.** A separate `livespec/doctor/static/__init__.py`
   imports every check module by name and re-exports a tuple of
   `(SLUG, run_callable)` pairs. Adding a check requires editing
   the registry, which contradicts the v005-preserved invariant
   "check insert/delete is a non-event" (PROPOSAL.md line 866-868).
3. **Hybrid.** Glob discovery is wrapped in a single `@impure_safe`
   I/O function returning `IOResult[list[CheckModule], DoctorInternalError]`;
   the imported callables conform to a `Protocol[CheckRun]` that
   pyright validates structurally. Most pleasant; least documented.

The orchestrator is the spine of doctor's static phase; the gap
matters.

### Motivation

There is also no rule for what happens when discovery loads a module
that doesn't export `SLUG` or `run`. ROP says known-domain failures
become `IOSuccess(fail_finding(...))`; here the failure is
discovery-time and there's no `SLUG` to attach. Should the
orchestrator emit an `IOFailure(DoctorInternalError(...))`? Crash
the supervisor? Skip silently? Not specified.

### Proposed Changes

Pick option (3): document a `CheckModule` `Protocol` in
`livespec/doctor/__init__.py`:

```python
from typing import Protocol
class CheckModule(Protocol):
    SLUG: str
    def run(self, ctx: DoctorContext) -> IOResult[Finding, DoctorInternalError]: ...
```

The orchestrator wraps glob+import in an `@impure_safe`
`io.discover.list_check_modules() -> IOResult[list[CheckModule],
DoctorInternalError]`. Modules failing the protocol cause an
`IOFailure(DoctorInternalError("check {filename} missing SLUG or
run"))` which short-circuits the orchestrator → exit `1`.

Document this in PROPOSAL.md's "Static-phase structure" subsection
and in the style doc's `doctor/run_static.py` description.

---

## Proposal: G9-supervisor-exit-code-derivation-from-findings

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness**.

### Summary

PROPOSAL.md lines 950-958 ("Static-phase exit codes"):

- `0`: all checks pass.
- `1`: script-internal failure.
- `3`: at least one check failed.

The orchestrator returns `IOResult[FindingsReport,
DoctorInternalError]`. `IOFailure(err)` → supervisor reads
`err.exit_code` (= 1 by default). `IOSuccess(report)` → supervisor
must inspect the report's findings and emit `0` or `3` based on
whether any finding has `status: "fail"`. The mapping logic is
load-bearing but undefined.

### Motivation

The supervisor in `bin/doctor_static.py` is the final ROP unwrap.
The wrapper shape (≤ 5 lines, no logic) means the unwrap is in
`livespec.doctor.run_static.main()`. That function must:

1. Construct a `DoctorContext` (from CLI args, cwd, environment).
2. Call `run_static(ctx)` (returns `IOResult[FindingsReport,
   DoctorInternalError]`).
3. Emit `{"findings": [...]}` JSON to stdout (always, regardless
   of pass/fail).
4. Inspect the findings to decide `0` vs `3`.
5. Pattern-match `IOFailure` → `err.exit_code`.

Step 4 is the gap: nothing in PROPOSAL.md or the style doc tells
the implementer that "any `status: "fail"` finding ⇒ exit 3."
Reasonable readers may instead interpret "status: "skipped"" as
fail (it isn't — see `out-of-band-edits` check `status:
"skipped"` on non-git repos, line 916-917) or treat the absence of
fail-findings as ambiguous.

### Proposed Changes

Add to PROPOSAL.md § "Static-phase exit codes":

> The supervisor derives the exit code as follows:
> - On `IOFailure(err)`: exit `err.exit_code` (typically `1`).
> - On `IOSuccess(report)`: emit `{"findings": [...]}` to stdout,
>   then exit `3` if any finding has `status: "fail"`, else exit
>   `0`. `status: "skipped"` does not trigger a fail exit.

Document the same in the style doc's exit-code-contract section.

---

## Proposal: G10-pyright-strict-with-vendored-libs

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness**.

### Summary

Pyright strict + vendored `dry-python/returns`, `fastjsonschema`,
and `structlog` is mandated, but the integration concerns are
unaddressed:

- `dry-python/returns` ships its own pyright plugin
  (`returns.contrib.mypy.returns_plugin`) and a "higher kinded
  types" hack via `KindN`. Without the plugin, pyright cannot
  narrow generic `Result[T, E]` chains through `bind`/`map`, and
  every chained call surfaces as `Result[Unknown, Unknown]`.
- `fastjsonschema` exposes generated validator callables typed as
  `Callable[[Any], Any]`. Pyright strict rejects `Any` in the
  livespec codebase (style doc line 282-283) — but vendored types
  are exempt only if the import is type-stub-clean.
- `structlog`'s logger objects are dynamically typed; calls like
  `log.info("msg", key=val)` are typed as `Callable[..., Any]`
  unless type stubs are present.

The proposal does not say:

- Whether `pyrightconfig.json` carves out `_vendor/` from strict
  mode (`exclude` or `useLibraryCodeForTypes`).
- Whether type stubs are written/sourced for any of the vendored
  libs.
- Whether thin `livespec.io.<lib>_wrapper` modules expose typed
  facades over the vendored libs to confine `Any` to a controlled
  boundary.

### Proposed Changes

Document the integration explicitly in the style doc:

- `pyrightconfig.json` (or `[tool.pyright]` in `pyproject.toml`)
  excludes `_vendor/**` from strict mode but enables
  `useLibraryCodeForTypes = true` so vendored libs' inferable types
  reach the type checker.
- For each vendored lib, the codebase touches it only via a thin
  wrapper module under `livespec/io/` (or `livespec/_returns_facade.py`,
  etc.) that exposes a fully-typed surface. The wrapper is the
  only place `Any` appears, and a single `# type:
  ignore[no-untyped-call] — vendored fastjsonschema returns Any`
  pragma is allowed there.
- For `dry-python/returns` specifically: add a sentence noting
  whether the vendored copy includes the pyright plugin, and if
  so how it is configured.

---

## Proposal: G11-propose-change-orchestration

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity**.

### Summary

PROPOSAL.md lines 690-705 describe `propose-change <topic> <intent>`:

- For freeform `<intent>`: "the skill invokes the active template's
  `prompts/propose-change.md` to reshape it into a JSON findings
  array, then maps each finding to one `## Proposal` section."
- For `--findings-json <path>`: validates JSON against
  `critique_findings.schema.json` and maps directly.

"The skill" here is ambiguous in v006's split architecture. The
template prompt invocation is LLM behavior; the file mapping is
deterministic. Three implementations are consistent:

1. `bin/propose_change.py` accepts both `<intent>` and
   `--findings-json`. For `<intent>`, it shells out to the LLM —
   forbidden (Python doesn't invoke LLMs).
2. `bin/propose_change.py` accepts only `--findings-json`. For
   freeform `<intent>`, the LLM (per `commands/propose-change.md`)
   invokes the template prompt itself, then calls
   `bin/propose_change.py --findings-json <generated.json>`.
3. There are two separate flows: LLM-driven freeform mode
   entirely in skill prose; programmatic mode via the wrapper.

Option (2) is consistent with the conversation turn 23 resolution.
PROPOSAL.md does not say so.

### Proposed Changes

Rewrite PROPOSAL.md `### propose-change <topic> <intent>` to make
explicit:

> `bin/propose_change.py` only accepts `--findings-json <path>`;
> it never invokes the template prompt or the LLM. The freeform
> `<intent>` path is driven by the LLM per
> `commands/propose-change.md`: the LLM invokes the active
> template's `prompts/propose-change.md`, captures the output,
> validates it against `critique_findings.schema.json` (using
> the python helper `livespec.validate.findings.validate`),
> writes the validated JSON to a temp file, then invokes
> `bin/propose_change.py --findings-json <tempfile> <topic>`.

Apply the same rewrite to `### critique <author>` (lines 718-741):
the template-prompt invocation is LLM behavior; only the
deterministic file shaping reaches `bin/critique.py`.

---

## Proposal: G12-vendor-audit-detail

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness**.

### Summary

`check-vendor-audit` is described abstractly: "diffs each vendored
lib's source tree against its upstream pinned version recorded in
`<repo-root>/.vendor.toml` (or equivalent manifest). Any drift
fails the gate." (style doc line 126-130, also DoD #12.)

Recreatability requires knowing:

- `.vendor.toml` schema (what fields name a vendored lib's
  upstream identity? `git_url`, `git_ref`, `path_within_repo`,
  `sha256`?).
- How the diff is computed (re-clone upstream at the pinned ref?
  compare to a stored snapshot? compare file hashes?).
- What "drift" means (any byte change? excluding test files?
  excluding LICENSE updates? excluding line-ending normalization?).
- Where vendoring scripts live (`dev-tooling/scripts/vendor.py`?
  inline in `justfile`?).
- How `just vendor-update <lib>` performs the re-vendor (fetches
  upstream, copies, updates `.vendor.toml`, but specifics?).

### Proposed Changes

Add a sub-section "Vendoring mechanics" to the style doc with at
least:

- `.vendor.toml` example with all required fields:
  ```toml
  [returns]
  upstream_url = "https://github.com/dry-python/returns"
  upstream_ref = "0.22.0"  # tag, branch, or commit
  vendored_at  = "scripts/_vendor/returns"
  source_subpath = "returns"  # path within upstream repo to vendor
  sha256 = "abc123..."  # of the vendored tree
  ```
- Diff algorithm: "`check-vendor-audit` re-fetches each upstream
  ref into a temp directory, copies `source_subpath` into a
  staging area, computes a recursive sha256 of the staging tree,
  and compares to the recorded `sha256`. Any mismatch fails the
  gate."
- Defer the actual implementation script to a first-batch post-
  seed `propose-change` (consistent with deferring other
  enforcement scripts).

Alternatively: explicitly state that `.vendor.toml` schema and
the audit script are deferred to first-batch propose-change, and
remove the implication that v006 is sufficient to recreate the
audit.

---

## Smaller items / cleanup

These are wording and reference fixes; none affect architecture.

---

## Proposal: G13-bin-doctor-wrapper-naming-consistency

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity**.

### Summary

The wrapper for the static phase is `bin/doctor_static.py`. There
is no `bin/doctor.py` — the LLM-driven phase has no Python entry.
But PROPOSAL.md repeatedly refers to "the `doctor` sub-command" and
"`livespec doctor`" as if there is a single command-line entry.
The user's mental model of "running `livespec doctor`" is in fact
"the LLM follows `commands/doctor.md`, which calls
`bin/doctor_static.py` and then drives the LLM-phase prose." This
is consistent with the architecture but not visible in the doc.

### Proposed Changes

Add a single sentence to PROPOSAL.md `### doctor`:

> Note: there is no `bin/doctor.py` wrapper. The user invokes
> `livespec doctor` via the LLM (per `commands/doctor.md`); the
> LLM calls `bin/doctor_static.py` for the static phase and then
> runs the LLM-driven phase from prose.

---

## Proposal: G14-structlog-bootstrap-location

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity**.

### Summary

Style doc lines 432-434: "Bootstrap: `scripts/livespec/__init__.py`
configures structlog's processors pipeline to emit JSON via
`structlog.processors.JSONRenderer()`."

But the same section says `run_id` is "bound at executable startup
via `structlog.contextvars.bind_contextvars`." `__init__.py` runs
on import (once per process); a fresh UUID generated there is
already per-invocation, since each wrapper is its own process.
Either location works, but the doc says both without saying which
is canonical.

Bigger question: structlog's processor configuration via
`structlog.configure(...)` is a global-mutable-state mutation. The
`check-global-writes` AST check (style doc line 564) forbids
"module-level mutable state writes." Whether `structlog.configure`
counts is undefined.

### Proposed Changes

Specify:

- `scripts/livespec/__init__.py` calls `structlog.configure(...)`
  exactly once. This is exempt from `check-global-writes` because
  it is third-party-library setup, not livespec module-level
  state.
- The `run_id` UUID is generated and bound in the same
  `__init__.py` block (right after `configure`). One bind per
  process; the wrapper inherits.
- Document the exempt `structlog.configure` call shape in the
  style doc and the AST check's exception list.

---

## Proposal: G15-just-check-failure-aggregation

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity**.

### Summary

`just check` runs every check (style doc line 556). Whether it
stops on first failure or runs all and aggregates is not specified.
The CI matrix uses `fail-fast: false` (revision P10) so CI runs all
in parallel. Pre-commit and pre-push run `just check` (style doc
lines 587-588) — sequential. Should `just check` mirror CI's
fail-fast: false behavior, or stop on first failure for fast
developer feedback?

### Proposed Changes

State explicitly: "`just check` runs every target sequentially and
continues on failure, exiting non-zero if any target failed,
listing which targets failed at the end." This matches CI's
intent and gives developers full failure context per run.

---

## Proposal: G16-lefthook-install-step

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness**.

### Summary

`lefthook.yml` configures hooks but lefthook requires `lefthook
install` (or equivalent) to register them with git. The bootstrap
sequence (`mise install` → ?) doesn't include this step. A new
contributor follows the dev-tooling instructions, has `lefthook`
on PATH, but no hooks fire on commit.

### Proposed Changes

Add to the style doc § "Dev tooling and task runner":

> First-time setup: after `mise install`, run `just bootstrap`
> (or equivalent), which runs `lefthook install` to register the
> pre-commit and pre-push hooks with git.

Add `bootstrap` to the canonical `just` target list.

---

## Proposal: G17-commands-namespace-overload

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity**.

### Summary

`commands/<cmd>.md` (skill prose, under
`.claude-plugin/skills/livespec/commands/`) and
`livespec/commands/<cmd>.py` (Python module under
`scripts/livespec/commands/`) share the directory name. The
proposal references "commands/" in places without disambiguating.
A first-time reader reasonably wonders whether they are the same
thing, alternates of each other, or paired. (They are paired but
distinct: one drives the LLM, the other implements deterministic
work.)

### Proposed Changes

Either:

- Rename one. E.g., `livespec/commands/` → `livespec/sub_commands/`
  to break the namespace overload. (Cost: rename in DoD #2,
  multiple proposal references, the style doc package layout.)
- Add a one-paragraph note under "Skill-level vs template-level
  responsibilities" explicitly distinguishing the two `commands/`
  trees.

Recommend the note: less churn, makes the intent visible.

---

## Proposal: G18-bin-wrapper-shape-line-count

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity**.

### Summary

Style doc lines 502-512 show a 4-line wrapper template (shebang +
docstring + import + `raise SystemExit(main())`) and say "≤ 5
lines." Whether the 5th line is a blank line, a shebang variant,
or anything else is undefined. With the G1 (`sys.path` insert) and
G3 (version check) additions, the wrapper grows naturally to 7-9
lines. The "≤ 5" rule and the "no logic" rule conflict with the
recovery proposed under G1/G3.

### Proposed Changes

Replace "≤ 5 lines" with a structural rule: "The wrapper MUST
consist only of the following stanzas in order, with no other
statements: (a) shebang, (b) module docstring, (c) optional
`sys.path` bootstrap (3-4 lines), (d) optional Python-version
check (3-4 lines), (e) `from livespec... import main`, (f)
`raise SystemExit(main())`." Update `check-wrapper-shape` to
match.

This dissolves the ≤ 5 line rule, which was bash-era thinking
about "minimal stub" not Python's reality.

---

## Recreatability summary

After applying every fix above, can a competent implementer
recreate v006 livespec from PROPOSAL.md +
python-skill-script-style-requirements.md + livespec-nlspec-spec.md
alone? Yes. Today, no — G1 (sys.path), G2 (YAML), G3 (init
raise), G4 (validate purity), and G5 (orchestration) each
individually break recreatability.

The remaining items (G6-G18) force the implementer to choose
between mutually incompatible plausible interpretations or to
file follow-up propose-changes for unspecified mechanics. They
do not block, but they do erode the spec-as-contract guarantee.

---

## Sequencing for the interview

The major gaps cluster:

- **G1-G4 are foundational python-architecture choices.** They
  should be settled first, in order, because each constrains the
  next (G3's resolution depends on G1's `sys.path` mechanism;
  G4's resolution depends on accepting that schemas come in via
  `io/`).
- **G5 settles the lifecycle orchestration** that several
  significant items (G11, G13, G17) depend on.
- **G6-G12 are independent significant gaps** and can be
  interviewed in any order; G7 and G10 are self-contained
  cleanups that don't depend on architectural choices.
- **G13-G18 are wording fixes** and can be batched at the end of
  the interview.

I will proceed in that order, one question per turn, reading
each item's options aloud before asking.
