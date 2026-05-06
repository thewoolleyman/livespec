---
topic: proposal-critique-v10
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-23T00:00:00Z
---

# Critique scope

This critique evaluates **v010 PROPOSAL.md** against its companions
`python-skill-script-style-requirements.md`, `deferred-items.md`,
and the embedded `livespec-nlspec-spec.md` (including its v009
"Architecture-Level Constraints" + "Error Handling Discipline"
sections). Primary lens: the **recreatability test** against v010 —
given only PROPOSAL.md, the Python style doc, `livespec-nlspec-
spec.md`, `deferred-items.md`, and the companion brainstorming
docs, can a competent implementer produce a working v010 livespec
plugin?

The v010 revision (`history/v010/proposed_changes/
proposal-critique-v09-revision.md`) locked in 14 dispositions
(J1-J14): DoctorInternalError / Fold.collect residual cleanup,
io/git.get_git_user semantic unification, custom-template prompt-
path resolution via `bin/resolve_template.py`, new exit code `4`
for schema-validation retries, `build_parser` check-public-api
exemption, propose-change `--author` precedence, `HelpRequested`
non-LivespecError informational early-exit, coverage scope
extended to `scripts/bin/`, `.vendor.toml` → `.vendor.jsonc`
rename (reusing vendored `jsoncomment`), inverse `--run-pre-check`
flag, `Finding` relocation to `schemas/dataclasses/finding.py`,
dogfood symlink committed as tracked symlink, `template_format_
version: {1}` enumerated, `prune-history` repeat-no-op. This
critique does **not** reopen any of those decisions, nor any
earlier v001–v009 disposition.

The recreatability test over v010 surfaces gaps in three clusters:

1. **Layout malformations from J3 introducing `resolve_template.py`.**
   The new wrapper slots into `bin/` and `commands/`, but the
   style doc's bin/ tree wasn't updated, the CLI and stdout
   contract are under-specified, and the layout lists
   `commands/doctor.py` orphaned relative to the explicit "no
   `bin/doctor.py`" doctrine.
2. **Coverage × wrapper-shape interaction** from J8 (coverage
   scope now includes `scripts/bin/**`) colliding with the 6-line
   wrapper-shape rule (no extra lines, including no `# pragma`
   comment) and the per-file 3-pragma-line cap.
3. **Small integration gaps left from J4 / J6 / J7 landings.**
   `HelpRequested(text)` match-destructuring needs a Python
   protocol hook; `critique` has no CLI `--author` while
   `propose-change` just got one; the reserved `livespec-` prefix
   enforcement is described at two conflicting layers;
   doctor-static's validation findings (e.g., `livespec-jsonc-
   valid`) don't state whether they map to exit `3` (Finding) or
   exit `4` (IOFailure(ValidationError)); skill-prose injection
   of `livespec-nlspec-spec.md` as template-prompt context has no
   documented mechanism anywhere.

Items are labelled `K1`–`K11` (the `K` prefix distinguishes "v010
gap" findings from prior critiques' `G`- (v007), `H`- (v008),
`I`- (v009), and `J`- (v010) items). Each item carries one of the
four NLSpec failure modes:

- **ambiguity** — admits multiple incompatible interpretations.
- **malformation** — self-contradiction within or across
  documents.
- **incompleteness** — missing information needed to act.
- **incorrectness** — internally consistent but specifies
  behavior that cannot work as written or contradicts an
  established external convention.

Major gaps appear first (block recreatability outright), then
significant gaps (force load-bearing guesses or produce wrong
behavior), then smaller cleanup.

---

## Major gaps

These items would block a competent implementer from producing a
working v010 livespec without filing additional propose-changes,
because a downstream document still references a concept the
layout contradicts, a new wrapper's contract is under-specified,
or a mandated cross-rule has no self-consistent resolution.

---

## Proposal: K1-commands-doctor-orphan-vs-no-bin-doctor

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**malformation** (the v010 skill-layout tree lists
`livespec/commands/doctor.py`, but PROPOSAL.md §"Note on
`bin/doctor.py`" explicitly forbids a `bin/doctor.py` wrapper, and
`doctor_static.py` imports from `livespec.doctor.run_static`, not
from `livespec.commands.doctor` — so `commands/doctor.py` is an
unreferenced orphan with no entry path into it).

### Summary

PROPOSAL.md's §"Skill layout inside the plugin" tree (lines 97–107)
enumerates `commands/doctor.py` alongside `commands/{seed,
propose_change, critique, revise, resolve_template, prune_history}
.py`. But (a) there is no `bin/doctor.py` wrapper (explicitly
forbidden — §"Note on `bin/doctor.py`", PROPOSAL.md lines 574–580);
(b) `bin/doctor_static.py` imports from `livespec.doctor.run_static`
per the 6-line wrapper-shape contract; (c) no other wrapper or
sub-command entry point calls into `commands/doctor.py`. The file
is layout-named but mechanically unreachable. A recreator will
either create an empty/unused module to satisfy the layout, or
silently drop the module, breaking cross-document consistency
with the tests/ mirror rule and with `check-public-api-result-
typed`'s `main` exemption (which names "`main` in `commands/**.py`"
inclusive of `commands/doctor.py`).

### Motivation

**PROPOSAL.md lines 101–107** (skill-layout tree):

> │       ├── commands/                    # one module per sub-command: run() + main()
> │       │   ├── seed.py
> │       │   ├── propose_change.py
> │       │   ├── critique.py
> │       │   ├── revise.py
> │       │   ├── doctor.py
> │       │   ├── resolve_template.py      # resolves active template path (J3)
> │       │   └── prune_history.py

**PROPOSAL.md lines 574–580** (note on bin/doctor.py):

> There is no `bin/doctor.py` wrapper. The user invokes
> `/livespec:doctor` (or expresses intent in dialogue); the LLM
> follows `doctor/SKILL.md`, which calls `bin/doctor_static.py` for
> the static phase, then runs the LLM-driven phase from prose. The
> asymmetry is intentional: the LLM-driven phase has no Python entry
> because Python doesn't invoke the LLM.

**PROPOSAL.md line 1363** (doctor static phase):

> The orchestrator is at `.claude-plugin/scripts/livespec/doctor/run_static.py`
> and invoked via the shebang wrapper at `scripts/bin/doctor_static.py`.

**Style doc line 195–197** (commands/ convention):

> **`commands/<cmd>.py`** — one module per sub-command. Exports `run()`
> (ROP-returning) and `main()` (supervisor that unwraps to exit code).

But for `doctor`, the supervisor lives at
`livespec/doctor/run_static.py::main()`, not
`livespec/commands/doctor.py::main()`. The style doc's
`check-public-api-result-typed` exemption (style doc line 600–605,
and `static-check-semantics` deferred-item `supervisor public-API
exemption (v009 I4)`) names "functions named `main` in
`commands/**.py` and `doctor/run_static.py`" — already excluding
`commands/doctor.py` from its "commands/" supervisor enumeration in
the main-exemption path, since the doctor supervisor lives under
`doctor/`, not `commands/`. The layout's listing of
`commands/doctor.py` cannot be reconciled with this exemption
list.

Recreatability failure: the test-tree mirror rule
(PROPOSAL.md lines 1859–1867; style doc §"Testing") requires
`tests/livespec/commands/test_doctor.py` because
`commands/doctor.py` is in the tree. But there is no content to
test — the module has no purpose. The 100% coverage mandate then
forces the implementer to write contentless tests for an
unreachable module.

### Proposed Changes

Pick one disposition and update PROPOSAL.md's layout:

- **A. Remove `commands/doctor.py` from the layout tree.** It is
  not imported and has no purpose. PROPOSAL.md line 105 is edited
  to drop `│       │   ├── doctor.py`. The `commands/` comment "one
  module per sub-command" is softened to "one module per sub-command
  *with a Python wrapper*; `doctor` has no wrapper — see §'Note on
  `bin/doctor.py`'. The `doctor` sub-command's entry point is at
  `livespec/doctor/run_static.py`." The tests-tree mirror rule
  already excludes it (no module, no mirror).

- **B. Keep `commands/doctor.py` as a thin re-export shim** that
  does `from livespec.doctor.run_static import main, run` so the
  "commands/ mirrors sub-commands" invariant is preserved. Adds
  a 2-line module with no behavioral content; mirror tests assert
  the re-export; `check-public-api-result-typed` exempts `main`
  by name per I4. Risk: introduces an import cycle risk
  (`commands/` importing from `doctor/`, while nothing else does);
  adds a module whose only function is to be re-export plumbing.

- **C. Rename `doctor/run_static.py` → `commands/doctor.py`** so
  the convention "one supervisor per commands/" holds uniformly.
  PROPOSAL.md and the style doc replace every
  `livespec.doctor.run_static` reference with
  `livespec.commands.doctor`. `doctor/static/` stays in place as
  the check directory; only the orchestrator moves. Risk: larger
  textual change; the "doctor orchestrator is a runnable module"
  framing is lost; `static-check-semantics` deferred-item
  references need updating.

Recommended: **A**. This was most likely an implementer-pass
oversight during v010 — the J3 disposition added
`commands/resolve_template.py` to the layout and the adjacent
`doctor.py` line is a stale holdover from earlier iterations (when
`commands/doctor.py` was briefly the LLM-driven phase's Python
shadow in v007 before the "no `bin/doctor.py`" discipline landed).
The one-line deletion and a two-sentence comment update resolve
the malformation with the smallest blast radius; the "no Python
entry for doctor's LLM phase" invariant from v007/v008 is
preserved. Option B is acceptable but produces a purposeless
module; Option C reframes a load-bearing name without benefit.

---

## Proposal: K2-resolve-template-wrapper-contract

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (the v010 J3 disposition adds
`bin/resolve_template.py` and `commands/resolve_template.py` but
documents only the coarsest output contract — "exit 0 with
resolved path on stdout; exit 3 on invalid template config." The
CLI invocation shape, how the wrapper locates the project's
`.livespec.jsonc`, how it resolves built-in names vs user-provided
paths, the exact stdout form (absolute vs relative; trailing
newline; is multi-line output ever valid), and the pre/post-step
doctor-static treatment are all unspecified).

### Summary

Per-sub-command SKILL.md prose (PROPOSAL.md lines 218–227) invokes
`bin/resolve_template.py` via Bash as step (a) of the two-step
dispatch, then uses the Read tool to fetch `<resolved-path>/
prompts/<name>.md` as step (b). For the Bash invocation to be
reproducible by an LLM and by the wrapper itself, the interface
needs to be nailed: what is the exact argv the SKILL.md prose uses?
Zero positional args (implicit cwd-rooted `.livespec.jsonc`)? An
explicit `--project-root <path>`? What does the stdout line look
like — is it an absolute path, a repo-root-relative path, or
`file://` URI? Does the Read step reliably find
`<resolved-path>/prompts/<name>.md` given the stdout verbatim?
These are all load-bearing for the SKILL.md body structure
authoring (deferred `skill-md-prose-authoring`) and for
`user-hosted-custom-templates` (J3 deferred-items entry, which
depends on stdout-contract stability as its "v1 → v2 migration
shield").

### Motivation

**PROPOSAL.md lines 218–227** (SKILL.md body structure step 4):

> - **Resolve + invoke a template prompt.** Two-step dispatch:
>     (a) invoke `bin/resolve_template.py` via Bash and capture
>     the active template's path from stdout (the wrapper reads
>     `.livespec.jsonc`'s `template` field and resolves built-in
>     names or user-provided paths uniformly); (b) use the Read
>     tool to read `<resolved-path>/prompts/<name>.md` and use its
>     contents as the template prompt. …

**PROPOSAL.md lines 904–920** (custom templates in v1 scope):

> - `.livespec.jsonc`'s `template` field accepts either a built-in
>   name or a path to a template directory.
> …
> - **Deferred future feature: user-hosted custom templates at
>   arbitrary non-plugin locations.** The `bin/resolve_template.py`
>   wrapper is the seam through which v2+ template-discovery
>   extensions … will land without breaking the wrapper's output
>   contract.

**v010 revision file lines 165–179** (J3 disposition):

> - New wrapper `bin/resolve_template.py` + Python module
>   `livespec/commands/resolve_template.py` (pure `run()` + `main()`
>   supervisor; returns exit 0 on success with the resolved template
>   path on stdout, exit 3 with structured error on invalid template
>   config).

PROPOSAL.md does not answer:

1. **CLI shape.** What does the SKILL.md prose actually type? Is
   it `python3 .claude-plugin/scripts/bin/resolve_template.py`
   (no args) invoked from the project root? Or
   `resolve_template.py --project-root <abs-path>`? An LLM
   reproducing the command cannot guess.
2. **Project-root resolution.** If no arg, does the wrapper use
   `Path.cwd()`? Walk up looking for `.livespec.jsonc`? Read an
   env var?
3. **Stdout shape.** Is it an absolute POSIX path? A `pathlib`-
   repr? A repo-root-relative path? With or without trailing
   newline? If the resolved path contains spaces, is it quoted?
   (Read expects a literal path and does not de-quote.)
4. **Lifecycle applicability.** PROPOSAL.md §"Sub-command
   lifecycle orchestration" enumerates which sub-commands have
   pre-step and post-step doctor static. `resolve_template` is not
   in that list. Does it have neither (like `help`)? Should it —
   since it reads `.livespec.jsonc` which `livespec-jsonc-valid`
   would want to check first? Silence here forces a guess that
   ripples into whether `resolve_template.py` accepts
   `--skip-pre-check` / `--run-pre-check` flags.
5. **Built-in name resolution path.** When `.livespec.jsonc` says
   `"template": "livespec"`, what absolute path does the wrapper
   emit? `.claude-plugin/specification-templates/livespec/`
   relative to which root — the project's cwd, or the bundle's
   install location? (Bundle install can be any path when the
   plugin is loaded by Claude Code.)
6. **Failure cases.** Missing `.livespec.jsonc` — exit 0 with
   built-in default, or exit 3? User-provided path doesn't exist
   — exit 3 with what structured stderr? Path exists but lacks
   `template.json` — exit 3 again? (That's also what
   `template-exists` doctor check emits, so the error surface
   may double up.)

Without these, the SKILL.md prose authoring (skill-md-prose-
authoring deferred item) is blocked from producing deterministic
per-sub-command bodies — every sub-command's "Resolve + invoke a
template prompt" step has to guess the same six points identically.

### Proposed Changes

Nail down the wrapper contract in PROPOSAL.md §"Templates —
Skill↔template communication layer" (new subsection) or in a new
§"Template resolution contract" sub-heading:

- **A. Codify the contract in PROPOSAL.md now; keep
  `skill-md-prose-authoring` narrower.** Add a concrete spec:
  - **Invocation:** `python3 .claude-plugin/scripts/bin/resolve_template.py`
    with zero positional args and an optional `--project-root
    <path>` flag (default: `Path.cwd()`; wrapper walks up from
    `--project-root` looking for `.livespec.jsonc`; fails exit 3 if
    not found under the walked tree AND no built-in default
    applies).
  - **Stdout:** exactly one line: the resolved template directory
    as an absolute POSIX path, followed by `\n`. Paths with
    spaces are emitted literally (callers MUST NOT pipe the
    output through shells that would re-split on whitespace;
    Claude Code's Read tool takes literal paths).
  - **Built-in resolution:** `"template": "livespec"` resolves to
    `<bundle-root>/specification-templates/livespec/` where
    `<bundle-root>` is the ancestor of `bin/resolve_template.py`
    (computed via `Path(__file__).resolve().parent.parent`).
  - **User-path resolution:** any other string is interpreted as a
    path relative to `--project-root` and resolved absolute; the
    wrapper validates the directory exists and contains
    `template.json` (minimal validation mirroring the
    `template-exists` doctor check, but narrower — just the two
    invariants needed to fetch `prompts/<name>.md`).
  - **Lifecycle:** `resolve_template` has **no pre-step and no
    post-step** doctor static (like `help` and `doctor`). It is a
    utility wrapper, not a spec-writing sub-command; running
    doctor-static before a template resolution would recurse
    (`livespec-jsonc-valid` check itself needs the resolved
    template for some checks). Add `resolve_template` to the
    §"Sub-command lifecycle orchestration" applicability list
    alongside `help` and `doctor`.
  - **Exit codes:** 0 on success; 3 on any of {.livespec.jsonc not
    found above --project-root, .livespec.jsonc malformed/schema-
    invalid, resolved path missing, resolved path lacks
    template.json}; 2 on usage errors (bad `--project-root` flag);
    127 via bootstrap on too-old Python.
  - **Reserved v2+ extensibility note:** the wrapper's output
    contract is frozen at "one line, absolute POSIX path" in v1;
    v2+ extensions (`user-hosted-custom-templates`) MUST preserve
    that exact shape.

- **B. Defer the full contract to `skill-md-prose-authoring` and
  `user-hosted-custom-templates`.** Leave PROPOSAL.md as is;
  accept that recreatability of the two-step dispatch is
  implementer-guessed in v1 and tightened later. Risk: every
  sub-command's SKILL.md body (7 of them) has to coordinate its
  own guess at the invocation shape; one body diverging from the
  others breaks the "stability shield" framing of the v2
  extensibility argument.

- **C. Make `resolve_template.py` internal-only; ship a
  higher-level wrapper that both resolves and reads.** Replace the
  two-step dispatch with a single-step one: `bin/
  get_template_prompt.py <prompt-name>` outputs the resolved
  prompt file's contents to stdout. Benefits: no second Read step;
  SKILL.md prose is trivially simple. Costs: Python reads markdown
  from disk and emits to stdout (boundary expansion — currently
  the LLM reads markdown itself via the Read tool, preserving the
  "Python doesn't see prompts" discipline). Risk: re-litigates a
  J3 disposition that kept Python out of prompt content.

Recommended: **A**. The contract is small (six invariants) and the
v2 extensibility argument in J3 hinges on its stability — locking
it now is exactly the move that delivers on that promise. Option
B pushes the work to skill-md-prose-authoring, but every
sub-command's body needs to agree on the same invocation shape
anyway; codifying it once in PROPOSAL.md prevents per-sub-command
drift. Option C reopens the J3 two-step-vs-single-step choice.

---

## Proposal: K3-wrapper-shape-vs-coverage-pragma-cap-conflict

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (the v010 J8 disposition extended coverage scope
to `scripts/bin/**`, and the wrapper-body coverage escape hatch
relies on `# pragma: no cover`, but the shebang-wrapper 6-line
contract forbids "other lines, no other statements" — ruling out
the pragma comment itself. The per-file 3-pragma-line cap further
forbids a line-by-line pragma on each of the 6 lines even if
comments were allowed. The rules are individually reasonable but
jointly unsatisfiable).

### Summary

Three v010 rules collide:

- PROPOSAL.md §"Shebang-wrapper contract" (lines 316–327) and
  style doc §"Shebang-wrapper contract" (lines 983–1000): "Each
  file under `bin/*.py` (except `_bootstrap.py`) MUST consist of
  exactly the following 6-line shape (no other lines, no other
  statements)."
- Style doc §"Code coverage" (lines 738–759) after J8: "100% line
  + branch coverage is mandatory across … `scripts/bin/**` …
  `scripts/bin/` is included because `_bootstrap.py` carries real
  logic that warrants enforcement; the 6-line wrapper bodies are
  pragma-excluded per the rules below (trivial pass-throughs
  covered by the wrapper-shape meta-test)."
- Style doc §"Code coverage" escape hatch: "`# pragma: no cover —
  <reason>` on a single line or a bounded block; cap ≤ 3
  pragma-lines per file. Bare `# pragma: no cover` without a
  reason is rejected."

To pragma-exclude a wrapper body, the file needs at least one
`# pragma: no cover — <reason>` comment line — which violates the
6-line shape's "no other lines" clause. Alternatively, trailing
comments on each of the 6 lines (e.g., `bootstrap()  # pragma: no
cover — …`) violate the "no other statements" clause if strictly
read and definitely violate the "≤ 3 pragma-lines per file" cap
once there are more than 3.

A recreator following the wrapper-shape rule writes a bare 6-line
file; coverage then reports the wrapper as uncovered, fails the
100% gate. A recreator following the coverage rule adds a pragma,
the wrapper-shape meta-test (`test_wrappers.py`) rejects the
7-line file. No implementation satisfies both.

### Motivation

**PROPOSAL.md lines 316–327** (shebang-wrapper contract):

> Each `bin/<cmd>.py` MUST consist of exactly the following 6-line
> shape (no other lines, no other statements):
>
> ```python
> #!/usr/bin/env python3
> """Shebang wrapper for <description>. No logic; see livespec.<module> for implementation."""
> from _bootstrap import bootstrap
> bootstrap()
> from livespec.<module>.<submodule> import main
>
> raise SystemExit(main())
> ```

**Style doc lines 746–759** (code coverage escape hatch):

> - **100% line + branch coverage** is mandatory across the whole
>   Python surface in `scripts/livespec/**`, `scripts/bin/**`, and
>   `<repo-root>/dev-tooling/**`. … `scripts/bin/` is included
>   because `_bootstrap.py` carries real logic … the 6-line
>   wrapper bodies are pragma-excluded per the rules below
>   (trivial pass-throughs covered by the wrapper-shape meta-test).
> …
> - **Escape hatch:** `# pragma: no cover — <reason>` on a single
>   line or a bounded block; cap ≤ 3 pragma-lines per file.

**Style doc lines 997–999** (wrapper shape meta-coverage note):

> `# pragma: no cover` is applied to each wrapper file's body to
> acknowledge these are trivial pass-throughs (the shape is verified
> by the `test_wrappers.py` meta-test). Enforced by
> `check-wrapper-shape` (AST-lite).

The sentence "`# pragma: no cover` is applied to each wrapper
file's body" is inconsistent with the 6-line "no other lines"
rule — a body with a pragma line is 7 lines, not 6; per-line
pragmas on all six statements exceed the 3-pragma-line cap.

### Proposed Changes

Pick one disposition and harmonize every affected document:

- **A. Exclude `bin/*.py` wrapper files from coverage
  measurement via `[tool.coverage.run] omit` glob, scoped to
  everything in `bin/` except `_bootstrap.py`.** Wrappers stay at
  the 6-line shape with no pragmas; `_bootstrap.py` stays covered
  via `test_bootstrap.py`; the wrapper-shape meta-test
  (`test_wrappers.py`) is the verification surface for the
  wrappers' correctness. Update: style doc §"Code coverage"
  drops the "wrapper bodies pragma-excluded" sentence; replaces
  with "wrapper bodies are omit-excluded at the coverage-config
  layer (`omit = ['scripts/bin/*.py', '!scripts/bin/_bootstrap.py']`
  or equivalent); the wrapper-shape meta-test verifies the 6-line
  shape." The "100% line + branch coverage across `scripts/bin/**`"
  sentence is narrowed to "across `scripts/bin/_bootstrap.py`"
  (only covered file in that tree).

- **B. Relax the 6-line shape to permit one optional trailing
  `# pragma: no cover — trivial pass-through; covered by
  test_wrappers.py` comment line (making it a 6-or-7-line shape).**
  Style doc's wrapper-shape contract is updated; `check-wrapper-
  shape` adds a rule permitting the exact pragma comment as an
  optional final line. The pragma-line cap is interpreted as "≤ 3
  pragma `comment` lines"; one per wrapper is under cap. Risk:
  softens an invariant that was explicitly sharpened over multiple
  revisions; introduces a special case for wrappers.

- **C. Keep everything as written; accept that wrapper files
  contribute zero-line statements only (raise SystemExit,
  import, etc.) and rely on `coverage.py`'s default handling of
  `raise SystemExit` as uncovered to report wrappers as "covered"
  because the statements never complete via normal fall-through.**
  Risk: `coverage.py` does not in fact treat `raise SystemExit`
  as a "no-cover needed" pattern unless the raise is at module-
  level and the test harness imports without running; every
  `test_wrappers.py` case that imports the wrapper triggers the
  raise and is caught by pytest as SystemExit (normal), producing
  a covered line. That would accidentally work — but only if every
  wrapper is imported by a test, not subprocess-invoked. Fragile.

Recommended: **A**. The coverage-omit glob is the cleanest
resolution: `_bootstrap.py` is the only bin/ file carrying real
logic (per the J8 disposition's own rationale), so it's the only
bin/ file that needs coverage. Wrappers are verified by the
shape meta-test; their line-by-line execution adds no signal.
Option B weakens an invariant the wrapper-shape discipline has
hardened over multiple revisions (v007 G9, v008 H12). Option C
relies on pytest-internals behavior that is not the right
coverage discipline. Accepting A preserves the 6-line rule, the
wrapper-shape check, and the 100%-or-explicitly-excluded coverage
gate simultaneously.

---

## Significant gaps

These items do not outright block recreatability, but force load-
bearing guesses or surface cross-document friction that recreators
would hit mid-implementation.

---

## Proposal: K4-helprequested-match-destructure-protocol

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (the v010 J7 supervisor pattern-match snippet
`IOFailure(HelpRequested(text))` destructures the wrapped
exception's first positional attribute into `text`, but
`HelpRequested` is defined as a plain `Exception` subclass in
`errors.py` without `__match_args__` or dataclass decoration.
Python's `match` statement will not bind `text` positionally
without one of those; the supervisor code as described will fail
at pattern-match time with a `TypeError` or match-miss).

### Summary

Style doc §"Exit code contract" (around line 909–918) defines:

```python
class HelpRequested(Exception):
    """User requested help (`-h` or `--help`); NOT a LivespecError.
    …
    """
    exit_code: ClassVar[int] = 0
```

PROPOSAL.md line 1588 describes the supervisor's pattern-match:

> - On `IOFailure(HelpRequested(text))`: emit `text` to stdout; exit
>   `0`.

Style doc §"CLI argument parsing seam" (around line 396–398)
mirrors it:

> - `IOFailure(HelpRequested(text))`: emit `text` to stdout; exit 0.

Python's structural pattern matching requires either (a) explicit
`__match_args__` on the class, (b) `@dataclass` decoration which
synthesizes `__match_args__`, or (c) keyword binding like
`HelpRequested(args=(text,))`. A bare `Exception` subclass without
any of these does NOT support positional match binding — pattern
`HelpRequested(text)` raises `TypeError("HelpRequested() accepts 0
positional sub-patterns (1 given)")` at match time.

A recreator writing the supervisor verbatim from PROPOSAL.md
would get a runtime TypeError. Resolution is an implementer guess
— add `__match_args__ = ("text",)`? Decorate with `@dataclass`
(but then it's not a plain Exception)? Use `HelpRequested.args[0]`
via attribute access? Each choice has different ergonomic /
testing consequences.

### Motivation

**Style doc lines 909–918** (HelpRequested definition):

```python
class HelpRequested(Exception):
    """User requested help (`-h` or `--help`); NOT a LivespecError.
    …
    """
    exit_code: ClassVar[int] = 0
```

No `__match_args__`, no `@dataclass`, no `__init__` accepting
`text` explicitly.

**PROPOSAL.md line 1588** (supervisor derivation):

> - On `IOFailure(HelpRequested(text))`: emit `text` to stdout; exit `0`.

**Python language reference** (PEP 634 §4):

> If no keyword patterns are present, the positional arguments are
> matched against the attributes named by `__match_args__`.

Without `__match_args__`, positional patterns bind nothing.

The same issue lurks with `IOFailure(err)` where `err` is a
`LivespecError` subclass: that pattern binds the whole instance
to `err` (no positional sub-pattern), so it works. But the
moment any class destructures a positional sub-pattern like
`HelpRequested(text)` or `UsageError(message)`, the class needs
the match-protocol hook.

### Proposed Changes

Pick one disposition and update the style doc's `errors.py`
code listing:

- **A. Declare `__match_args__ = ("text",)` on `HelpRequested`,
  and add a pass-through `__init__(self, text: str)` that stores
  `self.text`.** Style doc line 909–918 becomes:

  ```python
  class HelpRequested(Exception):
      """User requested help (`-h` or `--help`); NOT a LivespecError.
      …
      """
      exit_code: ClassVar[int] = 0
      __match_args__ = ("text",)
      def __init__(self, text: str) -> None:
          super().__init__(text)
          self.text = text
  ```

  Same pattern applies to any other `LivespecError` subclass the
  supervisor positionally destructures (e.g., if `UsageError` is
  ever matched as `UsageError(message)`). Document the rule:
  "Exception classes whose positional attributes are destructured
  by pattern-match callers MUST declare `__match_args__` and
  provide a matching `__init__`."

- **B. Replace positional destructure with attribute access in
  every supervisor pattern-match.** PROPOSAL.md and style doc
  rewrite to: `case IOFailure(err) if isinstance(err,
  HelpRequested): emit err.text; exit 0`. No match-protocol hooks
  required. Risk: uglier code; `match` statement becomes a thin
  isinstance-dispatch; loses pattern-match-as-type-narrowing
  benefit.

- **C. Convert `HelpRequested` (and any similarly-destructured
  `LivespecError` subclass) to `@dataclass(frozen=True)`
  subclassing `Exception`.** `@dataclass` synthesizes
  `__match_args__` from the field order. Risk: mixing `Exception`
  with `@dataclass` is a minor Python gotcha (the dataclass-
  generated `__init__` replaces `Exception.__init__`; must call
  `super().__init__(msg)` explicitly for args-tuple
  compatibility).

Recommended: **A**. Minimal, explicit, and preserves the
style-doc's intent that supervisors use `match` for clean
three-way dispatch (HelpRequested / UsageError / other
LivespecError). Option B is mechanically simpler but contradicts
the style doc's explicit "pattern-match derive exit code"
wording at lines 929–935. Option C works but introduces dataclass-
meets-Exception subtleties without clear benefit.

---

## Proposal: K5-nlspec-spec-injection-mechanism-unspecified

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness** (PROPOSAL.md §"NLSpec conformance" mandates
that the skill concatenate `livespec-nlspec-spec.md` as reference
context before invoking any template prompt, but no document names
the layer — Python wrapper, SKILL.md prose instruction, template-
prompt authoring — that performs the concatenation, nor the form
of the concatenation (prepended to the prompt? as a separate
attachment? as a Read step the LLM performs first?). Given the
architectural invariant "Python MUST NOT invoke the LLM," the
mechanism MUST be skill-prose-side, but no SKILL.md body structure
step names the injection, and `skill-md-prose-authoring` deferred-
items entry doesn't enumerate it either).

### Summary

PROPOSAL.md §"NLSpec conformance" (lines 1779–1790):

> - The active template MAY ship a `livespec-nlspec-spec.md` (or
>   equivalent discipline doc) at its root. When present, the
>   skill MUST concatenate its contents as reference context
>   before invoking ANY template prompt (seed, propose-change,
>   revise, critique).

And PROPOSAL.md §"Templates — Skill↔template communication layer"
(lines 923–937) describes the skill sending variables to the
template and validating output, but not how `livespec-nlspec-
spec.md` rides along.

Because Python wrappers don't invoke the LLM (PROPOSAL.md line
282–288; reinforced in v007 G1, v008 H4, v009 I8), the
concatenation has to happen at the skill-prose layer — i.e., the
per-sub-command SKILL.md body says, in prose, "before invoking
the template prompt, Read `<template-root>/livespec-nlspec-spec.md`
(if present) and include its contents as reference context." But
no SKILL.md body structure step currently enumerates this, and
the `skill-md-prose-authoring` deferred-items entry (listing the
canonical body sections) does not name the injection step among
its bullet list.

A recreator authoring SKILL.md bodies will either (a) forget the
injection entirely (NLSpec discipline loses effect); (b) fabricate
a mechanism (inconsistent across sub-commands); or (c) push the
concatenation into the Python wrapper (violating "Python MUST NOT
invoke the LLM").

### Motivation

**PROPOSAL.md lines 192–271** (Per-sub-command SKILL.md body
structure canonical sections): enumerates `Opening statement`,
`When to invoke`, `Inputs`, `Steps`, `Post-wrapper`, `Failure
handling`. Step 4 has sub-items: invoke `bin/<cmd>.py`,
"Resolve + invoke a template prompt" (two-step dispatch), write
JSON to temp file, prompt user, narrate warning,
"Retry-on-exit-4." None of these says: "Include
`<template-root>/livespec-nlspec-spec.md` as reference context."

**deferred-items.md `skill-md-prose-authoring`** (lines 325–367):

> **How to resolve:** Author each SKILL.md body per the canonical
> body shape codified in PROPOSAL.md §"Per-sub-command SKILL.md
> body structure" …

Does NOT list `livespec-nlspec-spec.md` injection. The entry
inherits whatever PROPOSAL.md's body-structure section says; since
the section is silent on NLSpec injection, the deferred entry is
also silent.

**PROPOSAL.md lines 977–980** (NLSpec injection, second mention):

> The template's `livespec-nlspec-spec.md` at its root is the
> adapted NLSpec guidelines document; the skill injects it as
> reference context with every command invocation.

"the skill injects it" — but which part of the skill? The SKILL.md
prose? The wrapper? Implementation-unspecified.

### Proposed Changes

- **A. Add a new canonical step to the per-sub-command SKILL.md
  body structure: "Include discipline doc if present."** Between
  step 3 (Inputs) and step 4 (Steps), or as step 4-prefix. The
  prose instruction: "If `<resolved-template>/livespec-nlspec-
  spec.md` exists, use the Read tool to fetch its contents and
  include them as reference context in the same LLM turn as any
  template-prompt invocation in step 4. Resolve the template path
  via `bin/resolve_template.py` per step 4(a)." Deferred
  `skill-md-prose-authoring` entry widens to name this step's
  authoring per sub-command. `resolve_template.py` invocation
  already required in step 4; this reuses the resolved path.

- **B. Relocate the injection instruction to the shared
  `NLSpec conformance` section as an explicit LLM-prose
  operating rule.** Add: "The per-sub-command SKILL.md bodies
  MUST name this injection as an operating invariant; it is not
  a Python-wrapper behavior. Specifically, each SKILL.md prose
  body MUST, before invoking a template prompt, Read
  `<resolved-template>/livespec-nlspec-spec.md` (if present) and
  include its contents as the LLM's reference context."
  `skill-md-prose-authoring` deferred-items entry references
  this rule. Risk: the discipline is stated once but not
  reflected in the canonical body structure, so a recreator
  reading the body-structure section top-down could miss it.

- **C. Move the concatenation into the Python wrapper by
  extending `resolve_template.py` to emit both the resolved path
  AND a small JSON manifest of "files to include as context."
  The LLM then reads each.** Risk: re-litigates the v009/v010
  discipline that keeps Python out of prompt-content assembly;
  widens the resolve_template.py contract.

Recommended: **A**. Makes the injection explicit in exactly the
section (body structure) where a recreator will look when
authoring SKILL.md bodies; wires it through the already-required
`resolve_template.py` invocation so no new machinery is needed;
preserves the "Python MUST NOT invoke the LLM" architectural
invariant. Option B is acceptable but easier to miss. Option C
reopens architectural discipline.

---

## Proposal: K6-run-pre-check-narration-symmetry

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**ambiguity** (the v010 J10 disposition added `--run-pre-check` as
inverse of `--skip-pre-check`, but PROPOSAL.md's narration rule
fires only "whenever pre-step is skipped" — silent on when
`--run-pre-check` forces pre-step to run *against* a config
default of `pre_step_skip_static_checks: true`. No narration rule
exists for the inverse override case; the user loses visibility
into the fact that a config-level default was overridden by CLI).

### Summary

PROPOSAL.md §"Sub-command lifecycle orchestration — Pre-step skip
control" (lines 520–540) and PROPOSAL.md §"Configuration:
`.livespec.jsonc` — Per-invocation CLI overrides" (lines 813–829)
both describe the three-valued resolution: `--skip-pre-check` →
skip=true; `--run-pre-check` → skip=false; neither → config;
both → argparse usage error. Both sections also say the skill MUST
surface a warning whenever **pre-step is skipped** (via
`--skip-pre-check` or via config with default=true). Neither
addresses whether the skill narrates when `--run-pre-check` forces
pre-step to run despite a config default of `true`.

Why it matters: a team using `pre_step_skip_static_checks: true`
as a sticky config (e.g., during an emergency recovery that left
the project in a broken state) would never be warned, in any
invocation that passes `--run-pre-check`, that they just ran the
checks they'd globally decided to skip. That is an information gap
for the user and for the LLM narrating the result. And symmetrically:
a team using the default `pre_step_skip_static_checks: false` who
passes `--skip-pre-check` gets a warning (as specified); a team with
the config `true` who passes `--run-pre-check` gets silence (not
specified).

### Motivation

**PROPOSAL.md lines 527–534** (pre-step skip resolution):

>   The skill MUST surface a warning via LLM narration whenever
>   pre-step is skipped (cases 1 and 3-with-config-true). The raw
>   record at the skill's structural layer is a JSON finding
>   (`status: "skipped"`, `message: "pre-step checks skipped by
>   user config or --skip-pre-check"`). …

Only "skipped" cases trigger narration. No mirror rule for
overridden-to-run.

**PROPOSAL.md lines 813–824** (per-invocation CLI overrides):

> - `--skip-pre-check` is a wrapper-parsed flag … The skill MUST
>   surface a warning to the user via LLM narration whenever
>   pre-step is skipped. …

Same asymmetry.

**deferred-items.md `skill-md-prose-authoring`** (lines 354–367)
lists narration requirements: "narration for both flags (skip
warning when `--skip-pre-check` is set or config default is
skip=true; **neutral when `--run-pre-check` overrides config
default skip=true**)." — so deferred-items explicitly says the
override case is "neutral" (no warning). But the user visibility
argument cuts the other way: overriding a config default is a
user-meaningful action worth narrating, even if not as an urgent
warning.

The documents agree the override case is not warned. The question
is whether that's the right disposition.

### Proposed Changes

- **A. Add an explicit narration rule for the override case.**
  PROPOSAL.md §"Pre-step skip control" and §"Per-invocation CLI
  overrides" add: "When `--run-pre-check` is passed and the
  config's `pre_step_skip_static_checks` is `true`, the skill
  MUST surface an informational narration (not a warning): 'Pre-
  step checks running despite config `pre_step_skip_static_checks:
  true` (--run-pre-check flag).' The raw structural record is a
  JSON finding (`status: "pass"` if checks pass, `message: "pre-
  step checks run by --run-pre-check override; config default
  would have skipped"`)." `skill-md-prose-authoring` widens to
  cover the override narration.

- **B. Accept the documented asymmetry; no change.** Users who
  pass `--run-pre-check` get normal exit-0 output if checks pass
  or exit-3 narration if they fail. The fact that config would
  have skipped is inferable from the user having typed the flag
  intentionally.

- **C. Narrow the flag semantics: drop `--run-pre-check` in favor
  of `--no-skip-pre-check`** (argparse-generated inverse). Risk:
  reopens J10.

Recommended: **B**. The user-visibility argument is worth
considering, but: (a) the asymmetric silence is already codified
in deferred-items as intentional ("neutral when `--run-pre-check`
overrides config default skip=true"); (b) passing `--run-pre-
check` is an explicit user action at CLI time, making the
override self-evident to the person who typed it; (c) adding a
narration rule for every config-override case scales poorly (what
about `--skip-subjective-checks` overriding config
`post_step_skip_subjective_checks: false`? etc.). Keeping the
existing asymmetric rule (warn when something is silently
skipped; neutral when an explicit flag is exercised) is
defensible. If a user wants visibility into overrides, they can
rely on the structlog record. Option A is a viable alternative
if the user wants the narration; Option C re-litigates J10.

---

## Proposal: K7-critique-wrapper-author-flag-asymmetry

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**ambiguity** (the v010 J6 disposition added a CLI `--author <id>`
flag to `bin/propose_change.py` with precedence env-var → CLI →
payload → fallback, but `bin/critique.py` and `bin/revise.py` use
the same env-var / payload / fallback precedence chain without a
matching CLI flag. The three wrappers have inconsistent CLI
surfaces for the same conceptual identifier, and no rationale is
documented for the asymmetry).

### Summary

v010 J6 disposition text (revision file lines 243–264):

> PROPOSAL.md §"propose-change" adds an Author-resolution paragraph
> mirroring I13: precedence (1) CLI `--author <id>` if set;
> (2) `LIVESPEC_REVISER_LLM` env var if set and non-empty; (3) LLM
> self-declared `author` field in the proposal-findings JSON payload
> if present and non-empty; (4) literal `"unknown-llm"` fallback.

So `propose_change.py` has CLI `--author`. But critique and
revise — both of which populate the same `reviser_llm` concept
— use only the env var + payload fallback chain. If the
propose-change chain is worth CLI exposure, why not critique and
revise? The symmetric CLI flag seems to have been added to
propose-change alone without a rationale for why the other two
differ.

This is a minor ambiguity rather than a malformation — the
precedence rules are internally consistent within each sub-
command, and critique's `<author>` argument is already a
positional CLI arg (it's used for topic disambiguation
`<author>-critique`). But the three-wrapper consistency is
invisible from PROPOSAL.md; a recreator might (a) add `--author`
to critique by inference from J6's precedence rule, diverging;
or (b) omit `--author` from critique to match J6's scope exactly,
diverging from the consistency-signal J6 seems to establish.

### Motivation

**PROPOSAL.md §"propose-change" lines 1178–1195** (J6 resolution):

> **Author identifier resolution.** The file-level `author` field
> in the resulting proposed-change front-matter is resolved by
> the following precedence …:
>   1. If `--author <id>` is passed on the CLI and non-empty, use
>      its value.
>   2. Otherwise, if the `LIVESPEC_REVISER_LLM` environment variable
>      is set and non-empty, use its value.
>   3. Otherwise, if the LLM self-declared an `author` field in the
>      `proposal_findings.schema.json` payload (file-level, optional)
>      and it is non-empty, use that value.
>   4. Otherwise, use the literal `"unknown-llm"`.

**PROPOSAL.md §"critique" lines 1232–1241** (author precedence,
no CLI):

> - `<author>` defaults to a string identifying the current LLM
>   context, resolved by the following precedence:
>   1. If the `LIVESPEC_REVISER_LLM` environment variable is set
>      and non-empty, use its value.
>   2. Otherwise, the LLM self-declares its model identifier in
>      the `reviser_llm` field of the JSON payload passed to
>      `bin/critique.py` …
>   3. Otherwise, use the literal `"unknown-llm"`.

Note: critique's `<author>` is a positional CLI arg (PROPOSAL.md
line 1247 shows `bin/critique.py --findings-json <tempfile>
<author>`). But the precedence rule explicitly lists env →
payload → fallback; the positional `<author>` is passed only
when the LLM has already resolved it (it's the output of the
precedence chain, not an input to it). So critique's CLI has
`<author>` by coincidence, not by the same "user can override"
shape as propose-change's `--author`.

**PROPOSAL.md §"revise"** has no explicit precedence block
showing the user-override path — it's mentioned in §"Revision
file format" lines 1736–1744 as env → payload → fallback.

The three wrappers populate the same identifier via slightly
different CLI surfaces:

| Wrapper | CLI override | Env var | Payload | Fallback |
|---|---|---|---|---|
| propose-change | `--author <id>` (J6) | `LIVESPEC_REVISER_LLM` | `author` field | `"unknown-llm"` |
| critique | positional `<author>` (pre-resolved) | `LIVESPEC_REVISER_LLM` | `reviser_llm` field | `"unknown-llm"` |
| revise | — (no CLI override) | `LIVESPEC_REVISER_LLM` | `reviser_llm` field | `"unknown-llm"` |

### Proposed Changes

- **A. Document the intentional asymmetry in PROPOSAL.md and
  deferred-items.** Add a note to §"propose-change" (and
  mirror in §"critique" / §"revise"): "The `--author` CLI flag
  is exposed on `propose_change.py` because external
  programmatic callers (e.g., CI hooks filing proposals) want
  to supply a non-LLM author identifier. `critique` and `revise`
  are LLM-driven workflows where `author`/`reviser_llm` is
  always an LLM or skill-tool identifier; env-var override
  suffices. No CLI flag is added to those wrappers in v1."

- **B. Add `--reviser-llm <id>` flag to `bin/critique.py` and
  `bin/revise.py` for symmetry.** Same precedence as J6.
  `wrapper-input-schemas` deferred item widens to include the
  new flags. Risk: expands wrapper surface beyond what I13 and
  J6 motivated.

- **C. Remove `--author` from `bin/propose_change.py`**; rely
  only on env-var override and payload field across all three
  wrappers. Reopens J6 — not recommended.

Recommended: **A**. The asymmetry is justifiable (propose-change
has programmatic non-LLM callers; critique and revise don't),
but that justification is currently invisible. A short rationale
note in PROPOSAL.md eliminates the "is this an oversight?"
question for recreators. Option B is clean but expands surface
area without demonstrated need; Option C reopens a settled
decision.

---

## Smaller cleanup

These items are self-contained text errors, cross-document
inconsistencies from v010 implementer-pass oversights, or minor
ambiguities that a recreator can work around but that drift over
time if not fixed.

---

## Proposal: K8-style-doc-bin-tree-missing-resolve-template

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (cross-document inconsistency — PROPOSAL.md's
skill-layout tree lists `bin/resolve_template.py` under J3, but
the style doc's §"Package layout" bin/ sub-tree does not mention
`resolve_template.py`; an implementer following the style doc's
layout verbatim would skip creating the wrapper).

### Summary

PROPOSAL.md lines 85–97 (bin/ sub-tree):

```
│   ├── bin/                             # Python shebang-wrapper executables
│   │   ├── _bootstrap.py                # shared: sys.path setup + Python version check
│   │   ├── seed.py
│   │   ├── propose_change.py
│   │   ├── critique.py
│   │   ├── revise.py
│   │   ├── doctor_static.py             # static-phase only (LLM-driven phase is skill-layer)
│   │   ├── resolve_template.py          # resolves active template path; echoes to stdout (see J3 / §"Per-sub-command SKILL.md body structure")
│   │   └── prune_history.py
```

Style doc lines 180–193 (same sub-tree):

```
.claude-plugin/scripts/
├── bin/                                   # shebang-wrapper executables
│   ├── _bootstrap.py                      # SHARED: sys.path setup + Python version check
│   ├── seed.py
│   ├── propose_change.py
│   ├── critique.py
│   ├── revise.py
│   ├── doctor_static.py
│   └── prune_history.py
```

The style doc's tree was not updated during the v010 J3 implementer
pass. `resolve_template.py` is missing. A recreator using the
style doc's package layout as their skeleton would create six
wrappers (matching the style doc's six items) and miss the
seventh. `check-wrapper-shape` would still pass (all existing
wrappers match). The missing wrapper would only be noticed when
the first sub-command SKILL.md attempts step 4(a) and the file
doesn't exist — a runtime "file not found" instead of a static
layout failure.

### Motivation

See the two trees above. Same bin/ directory, different contents.
This is purely an implementer-pass oversight from v010; no
disposition debate is needed.

### Proposed Changes

- **A. Add `resolve_template.py` to the style doc's bin/
  sub-tree.** Update style doc line 186 (after `doctor_static.py`)
  to add:

  ```
  │   ├── doctor_static.py
  │   ├── resolve_template.py             # resolves active template path; echoes to stdout
  │   └── prune_history.py
  ```

  No other style-doc changes needed.

- **B. Rewrite the style doc to stop duplicating the layout
  tree.** Delete the bin/ tree from the style doc; reference
  PROPOSAL.md §"Skill layout inside the plugin" as the single
  source of truth. Eliminates the drift source permanently.
  Risk: the style doc currently replicates the tree for
  directory-oriented package-layout readability; removing it
  makes the style doc harder to read standalone.

Recommended: **A**. Trivial one-line fix, matching the PROPOSAL.md
tree. Option B is a bigger restructure that can happen later if
cross-doc layout drift becomes a pattern.

---

## Proposal: K9-livespec-prefix-enforcement-layer-dual-wording

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**ambiguity** (the reserved `livespec-` author-prefix namespace
convention is described at two layers in PROPOSAL.md: "pattern-
validated by the front-matter schema" AND "validation failure at
the proposed-change format layer (not the schema layer)." A
recreator cannot tell whether the schema enforces the
reservation, or the parse-time format validation does, or both).

### Summary

PROPOSAL.md §"Proposed-change file format" (lines 1669–1676):

> **Author-identifier namespace convention:** identifiers with
> the prefix `livespec-` … are **reserved** for automated
> skill-tool authorship. Human authors and LLMs MUST NOT use
> this prefix … The reservation is **pattern-validated by the
> front-matter schema** (see `front-matter-parser` in
> `deferred-items.md`).

PROPOSAL.md §"propose-change" (lines 1191–1195):

> The reserved `livespec-` prefix namespace convention (see
> §"Proposed-change file format") still applies: user-
> supplied authors MUST NOT use `livespec-`-prefixed values;
> attempts to do so produce a **validation failure at the
> proposed-change format layer (not the schema layer)**.

The first passage says the schema enforces. The second says the
proposed-change format layer enforces ("not the schema layer").
Both mention the `livespec-` prefix and the same user-supplied-
forbidden rule.

The actual distinction seems to be:
- **Schema layer:** allows values like `livespec-seed` (valid
  string matching the reservation pattern) because the skill
  itself writes them (seed auto-capture, doctor auto-backfill).
- **Format/parse layer:** rejects user-supplied `livespec-`-
  prefixed values, distinguishing user-input from skill-internal
  writes via provenance tracking.

But this distinction is not stated. "Pattern-validated by the
schema" and "not the schema layer" directly contradict if read
naively. `deferred-items.md` `front-matter-parser` entry (lines
304–323) lands on: "Each schema pattern-validates the reserved
`livespec-` prefix namespace convention from I9 … fields
accepting human-or-LLM identifiers MUST NOT accept user-supplied
`livespec-`-prefixed values from non-skill callers (enforced at
parse time on the proposed-change / revision file format, not at
the front-matter schema layer)." — which re-states the same
two-layer mechanism without explaining why the schema pattern
matters at all if the format layer handles the whole user-vs-
skill decision.

### Motivation

See the three passages above. They are not reconcilable without
adding the "allow-list" interpretation: the schema pattern
**permits** (doesn't reject) `livespec-`-prefixed values as
syntactically valid; the format-layer validator **rejects**
`livespec-`-prefixed values when provenance is user-supplied
(CLI arg, env var, LLM-supplied payload) vs skill-supplied
(wrapper-hardcoded for seed auto-capture, doctor auto-backfill).

But the concrete mechanism for distinguishing provenance is
unstated. The wrapper could (a) accept only non-`livespec-`
values from CLI/env/payload and never accept a user-supplied
`livespec-` identifier; (b) take a skill-provenance flag that
wrappers pass internally when calling the format validator.

### Proposed Changes

- **A. Rewrite PROPOSAL.md's two passages to state the two-layer
  mechanism explicitly.** Replace both paragraphs with:

  > **Author-identifier namespace convention:** identifiers with
  > the prefix `livespec-` (e.g., `livespec-seed`, `livespec-
  > doctor`) are reserved for automated skill-tool authorship.
  > Enforcement is two-layered:
  >
  > 1. **Schema layer:** the front-matter schemas
  >    (`proposed_change_front_matter.schema.json`,
  >    `revision_front_matter.schema.json`) pattern-match the
  >    `^livespec-[a-z-]+$` reservation shape so skill-tool
  >    writes (seed auto-capture, doctor auto-backfill) pass
  >    validation. The schema does NOT reject `livespec-`-
  >    prefixed values on input — it recognizes them.
  > 2. **Format/wrapper layer:** wrappers accepting
  >    user-supplied author identifiers (propose_change.py's
  >    `--author`, env var `LIVESPEC_REVISER_LLM`, LLM-supplied
  >    payload `author`/`reviser_llm` fields) reject values
  >    matching `^livespec-`. Skill-tool-owned wrappers (seed,
  >    doctor) hardcode `livespec-seed` / `livespec-doctor` and
  >    bypass this rejection.

  And update `front-matter-parser` deferred-items entry to match.

- **B. Collapse to one layer: the format/wrapper layer alone.**
  Schemas carry no `livespec-` pattern; the validation happens
  only at the wrapper-supplied-author-check layer. Risk:
  schema-produced error messages no longer distinguish
  reservation violations from other format errors.

- **C. Collapse to one layer: the schema alone.** Schemas
  reject all `livespec-`-prefixed values except when the caller
  passes a skill-internal provenance flag. Risk: threading the
  provenance flag through schema validation is awkward; the
  schema becomes context-sensitive.

Recommended: **A**. The two-layer mechanism is likely the
authorial intent (one layer recognizes, the other layer
gatekeeps); stating it explicitly eliminates the apparent
contradiction. Option B and C both collapse the layering in
different directions; both require more machinery changes than
A's prose fix.

---

## Proposal: K10-doctor-static-validation-finding-vs-iofailure

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**ambiguity** (the doctor-static `livespec-jsonc-valid` check
performs fastjsonschema validation on `.livespec.jsonc`; v010's
new exit code `4` for schema-validation failures does NOT apply
to this check per "doctor_static never emits 4 because it takes
no JSON input," but the check's own semantics — whether a schema-
validation failure produces a fail-Finding (exit 3 via IOSuccess
path) or an IOFailure(ValidationError) (would be exit 4 if not
caught) — are unstated. The supervisor's exit-code derivation
logic handles both, but the check's own API choice is a load-
bearing recreatability decision that silently splits exit-code
behavior based on check-author style).

### Summary

PROPOSAL.md §"Static-phase checks — livespec-jsonc-valid" (lines
1461–1464):

> - **`livespec-jsonc-valid`** — `.livespec.jsonc`, if present,
>   validates against its schema (`livespec_config.schema.json`)
>   via `fastjsonschema` (factory-shape; `io/` reads the schema,
>   `validate/` consumes the parsed dict).

PROPOSAL.md §"Static-phase exit codes" (lines 1579–1584):

> - `4`: schema-validation failure on an LLM-provided JSON payload
>   (only emitted by non-doctor wrappers that validate input JSON;
>   `bin/doctor_static.py` itself never emits `4` because it takes
>   no JSON input).

PROPOSAL.md §"Static-phase exit codes — supervisor derivation"
(lines 1585–1598):

> The supervisor derives the exit code as follows:
> …
> - On `IOFailure(err)` where `err` is a `LivespecError` subclass:
>   emit a structured-error JSON line on stderr via `structlog`,
>   then exit `err.exit_code` (`2` for `UsageError`, `3` for
>   `PreconditionError` / `GitUnavailableError`, `4` for
>   `ValidationError`, `126` for `PermissionDeniedError`, `127` for
>   `ToolMissingError`).
> - On `IOSuccess(report)`: emit `{"findings": [...]}` to stdout,
>   then exit `3` if any finding has `status: "fail"`, else exit
>   `0`. …

So if `livespec-jsonc-valid` returns `IOFailure(ValidationError(...))`
on a `.livespec.jsonc` schema-violation, the supervisor maps to
exit 4 — contradicting the "doctor_static never emits 4" rule.
If it returns `IOSuccess(Finding(status=fail, ...))`, the
supervisor maps to exit 3 — consistent with the doctor-static
rule.

So the implementer decision is: which does
`livespec-jsonc-valid::run(ctx)` emit on schema violation?

- **Finding path (IOSuccess + fail):** schema violation of
  `.livespec.jsonc` is a doctor-finding like any other, reported
  to the user with `check_id: "doctor-livespec-jsonc-valid",
  status: "fail", message: <validation error>`. Exit 3.
- **IOFailure path:** schema violation is an expected failure
  mode warranting the full-blown ValidationError class, exit 4.
  But exit 4 is retryable by the SKILL.md layer; the user
  doesn't "retry" a bad `.livespec.jsonc` through the LLM — they
  fix the file and re-run. Exit 4 semantics are wrong for this
  case.

The correct answer is Finding + exit 3 (validation of static
project config ≠ validation of LLM-generated payload). But
nothing in PROPOSAL.md or the style doc says so. A recreator
implementing from pattern (`io/` reads schema, `validate/` takes
dict, returns `Result[T, ValidationError]` — per factory shape at
style doc lines 269–277) will naturally thread `ValidationError`
on failure, creating an `IOFailure(ValidationError)` payload
from the check, producing exit 4, contradicting the doctor-static
exit-code rule.

### Motivation

See the three PROPOSAL.md passages above.

**Style doc lines 269–277** (factory-shape validators):

> **`validate/`** — pure validators using the **factory shape**:
> each validator takes `(payload: dict, schema: dict)` and returns
> `Result[T, ValidationError]`. …

So `validate/livespec_config.py::validate_livespec_config` returns
`Result[LivespecConfig, ValidationError]`. When
`livespec-jsonc-valid::run(ctx)` invokes this validator and
receives a `Result.Failure(ValidationError)`, what does it return
to the orchestrator?

If it re-lifts: `IOFailure(ValidationError)` → supervisor exit 4.
If it maps to Finding: `IOSuccess(Finding(status=fail, ...))` →
supervisor exit 3 via the "any finding fail" clause.

Implementer choice, unspecified.

### Proposed Changes

- **A. State the discipline explicitly in PROPOSAL.md §"Static-
  phase checks" opening paragraph.** Add: "Doctor-static checks
  MUST map domain-meaningful failure modes (validation failure,
  missing file, permission denied, etc.) to `IOSuccess(Finding(
  status='fail', ...))` rather than `IOFailure(err)`. The
  `IOFailure` track is reserved for unexpected impure-boundary
  failures (the check itself cannot continue — e.g., the
  `.livespec.jsonc` path couldn't be read at all due to I/O
  error). Domain findings are user-reportable via the Findings
  channel; `IOFailure` is short-circuit-and-abort only. This
  preserves the exit-code discipline that `bin/doctor_static.py`
  never emits exit 4 and that all check-driven failures exit 3
  via the `status: "fail"` Findings path." Update
  `static-check-semantics` deferred-items entry to reference
  this discipline.

- **B. Permit either path; clarify supervisor priority.** Add a
  supervisor rule: "If an `IOFailure(ValidationError)` is raised
  from within a doctor-static check, the supervisor maps it to
  exit 3 (via `err.exit_code` override for doctor_static context)
  rather than exit 4." Risk: context-sensitive exit_code
  overrides per entry-point are complex and fragile; violates
  the "exit_code is a stable class attribute" discipline.

- **C. Tag each doctor-static check at the registry layer with
  its expected error payload shape.** Requires introducing a
  check-meta type like `CheckKind = Literal["pure-validation",
  "impure-boundary", ...]`. Adds an orthogonal taxonomy; more
  machinery than the problem warrants.

Recommended: **A**. The architectural discipline ("IOFailure is
short-circuit-and-abort; findings are user-reportable via status:
fail") already implicit in the style doc's Error Handling
Discipline section — state it once for doctor-static-specific
validators and the ambiguity disappears. Option B introduces
per-entry-point exit_code overrides (complex); Option C adds
taxonomy for a two-value distinction.

---

## Proposal: K11-test-tree-mirror-silent-on-schemas-dataclasses

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (the v010 J11 disposition moved
`Finding`/`pass_finding`/`fail_finding` to
`schemas/dataclasses/finding.py`, but the test-tree example
trees in PROPOSAL.md §"Testing approach" and in the style doc
§"Testing" neither list `tests/livespec/schemas/dataclasses/
test_finding.py` nor otherwise reflect the move. The mirror rule
"tests/livespec/ mirrors `.claude-plugin/scripts/livespec/`
one-to-one" implies the file exists; the example tree omits it).

### Summary

PROPOSAL.md §"Testing approach" (lines 1825–1858) shows:

```
tests/
…
├── livespec/                                 (mirrors .claude-plugin/scripts/livespec/)
│   ├── commands/
│   │   ├── test_seed.py
│   │   ├── test_propose_change.py
│   │   └── ...
│   ├── doctor/
│   │   ├── test_run_static.py
│   │   └── static/                           (one test_*.py per static-check module)
…
│   ├── io/
│   │   └── test_fs.py
│   ├── parse/
│   │   ├── test_jsonc.py
│   │   └── test_front_matter.py
│   ├── validate/
│   └── ...
```

No `tests/livespec/schemas/` listed, even as `...`-capped. Style
doc §"Testing" (lines 682–703) is similarly silent on
`tests/livespec/schemas/`.

The mirror rule says tests mirror `scripts/livespec/` subtree-by-
subtree. `scripts/livespec/schemas/dataclasses/` exists (houses
`Finding`, `DoctorFindings`, `LivespecConfig`, etc.), with
constructor helpers (`pass_finding`, `fail_finding`) that have
behavioral content. Tests MUST exist per the mirror rule. But
nothing in either doc's example tree reflects this.

The 100% coverage mandate reinforces: `pass_finding`/`fail_finding`
constructors have logic (probably assembling a `Finding` with
defaulted `path=None, line=None` fields for pass, or taking a
message string and the path/line for fail). Coverage needs tests.

### Motivation

**PROPOSAL.md lines 1863–1867** (test organization rules):

> - `tests/livespec/` mirrors `.claude-plugin/scripts/livespec/`
>   one-to-one, preserving subdirectory structure.
>   `tests/dev-tooling/` mirrors `<repo-root>/dev-tooling/` the same
>   way. `tests/bin/` mirrors `scripts/bin/`. Adding a module anywhere
>   under those trees requires adding the corresponding test file at the
>   mirrored path.

**Style doc lines 682–703** (testing layout):

No `tests/livespec/schemas/` entry.

**v010 J11 revision** (revision lines 368–385): places `Finding`
under `schemas/dataclasses/finding.py` with constructor helpers;
cites `check-schema-dataclass-pairing` as the enforcement
walker, but does not mention test-mirror implications.

### Proposed Changes

- **A. Add `schemas/dataclasses/` test sub-tree to both example
  layouts.** PROPOSAL.md line 1853 area inserts:

  ```
  │   ├── schemas/
  │   │   └── dataclasses/
  │   │       ├── test_finding.py
  │   │       ├── test_doctor_findings.py
  │   │       └── ...
  ```

  Style doc same addition. Behavioral content tested: constructor
  helper contracts (`pass_finding(check_id) -> Finding(status='pass',
  ...)`, `fail_finding(check_id, message, path, line) -> Finding(
  status='fail', ...)`). The mirror rule is already normative;
  the example tree just becomes consistent with it.

- **B. Amend the mirror rule to exempt pure-data modules.**
  Add: "Modules under `schemas/dataclasses/*.py` containing only
  `@dataclass(frozen=True)` definitions with no behavioral
  methods MAY omit test-mirror files; their coverage is
  structural (`check-schema-dataclass-pairing` verifies shape).
  Modules with constructor helper functions (`pass_finding`,
  `fail_finding` in `finding.py`) MUST still have tests." Risk:
  introduces a carve-out in a rule that's otherwise uniform.

Recommended: **A**. The mirror rule is already universal; adding
the example tree rows makes the applicability to
`schemas/dataclasses/` visible to recreators. The tests are
small (constructor-contract checks) and fit the style doc's
existing "per-module test" discipline. Option B carves out a
rule boundary that doesn't cleanly apply (`finding.py` has logic;
`livespec_config.py` is pure-data; the boundary is per-file, not
per-directory).

---

## Summary of items

| Item | Failure mode | Cluster |
|---|---|---|
| K1 | malformation | Major — `commands/doctor.py` orphan vs "no bin/doctor.py" |
| K2 | incompleteness | Major — `resolve_template.py` wrapper contract under-specified |
| K3 | malformation | Major — wrapper-shape × coverage-pragma conflict |
| K4 | ambiguity | Significant — `HelpRequested(text)` match-destructure requires `__match_args__` |
| K5 | incompleteness | Significant — `livespec-nlspec-spec.md` injection mechanism unspecified |
| K6 | ambiguity | Significant — `--run-pre-check` narration symmetry |
| K7 | ambiguity | Significant — `critique`/`revise` wrappers' CLI author-flag asymmetry vs `propose-change` |
| K8 | malformation | Cleanup — style doc bin/ tree missing `resolve_template.py` |
| K9 | ambiguity | Cleanup — `livespec-` prefix enforcement: schema-layer vs format-layer dual wording |
| K10 | ambiguity | Cleanup — doctor-static validation findings: Finding vs IOFailure choice |
| K11 | incompleteness | Cleanup — test-tree example trees silent on `schemas/dataclasses/` |

No item reopens a v005–v010 disposition about what livespec does.
Each item either surfaces an implementer-pass oversight from
v010's J1–J14 landings, or an integration gap a downstream
recreator would hit but that was not flagged during v010's
critique pass.
