---
topic: proposal-critique-v05
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-22T18:00:00Z
---

# Conversion plan: bash → Python (v005 → v006)

## Scope and framing

This document is a **language-migration plan**, not a defect critique.
It proposes replacing bash with Python 3.x as the implementation
language for every script the livespec skill bundles (runtime
`scripts/*`) and every dev-tooling enforcement script at
`<repo-root>/dev-tooling/**`. The driving argument is summarized in
`python-conversion-prompt.md`:

* The v005 bash style doc grew to ~24 pages of rules that exist
  largely to compensate for features bash lacks (namespaces, import
  systems, data structures, an AST, test/coverage tooling,
  dependency management). Python supplies those out of the box.
* The v005 portability premise ("bash + jq is the minimum-dependency
  story") is already compromised by the bash 3.2.57 macOS floor and
  by `jq` as a hard runtime dep. Python 3.x is preinstalled on every
  supported Linux distro and one-command-installable on macOS (brew
  / Xcode CLT), so the dependency surface is comparable in practice.
* `ruff` alone replaces `shellcheck` + `shfmt` + `shellharden` +
  `shellmetrics`. `pytest` + `coverage.py` replaces `bats-core` +
  `bats-assert` + `bats-support` + `kcov`. `mypy` or `pyright` add
  type checking with no bash analogue. AST-level checks the v005
  revision reserved for `tree-sitter-bash` become `ast.walk()` calls.

Failure-mode labels from prior critiques (ambiguity, malformation,
incompleteness, incorrectness) do not apply here. Each proposal is
labelled by **axis** instead:

* **language-floor** — Python version target.
* **dependency-strategy** — runtime and dev-time deps.
* **tooling** — concrete tools substituting bash-era tools.
* **layout** — on-disk structure of scripts and the skill bundle.
* **rule-simplification** — style-doc rules that shrink or drop
  because Python supplies the missing abstraction natively.
* **enforcement-suite-shape** — Makefile targets that stay, drop, or
  morph.
* **backwards-compatibility** — fate of bash-era artifacts.
* **architecture-pattern** — Python-specific architectural mandates
  named in `python-conversion-prompt.md` (ROP + functional +
  type-safety patterns).

This pass does **not** reopen any decision from v001–v005 about
**what** livespec does. Sub-commands, template architecture,
lifecycle, history shape, proposed-change / revision file formats,
doctor's static-check slug-based contract, dev-time / runtime split,
mise-pinning discipline, enforcement-suite-is-invocation-agnostic
framing — all load-bearing and out of scope.

---

## Proposal: P1-python-version-floor

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new, replaces bash style doc)

### Axis

language-floor

### Summary

Pin the Python version the skill targets. Bash 3.2.57 was the v005
floor because macOS ships it; Python has no analogous "shipped, never
updated" floor, but the wider the support matrix, the smaller the
usable feature set.

### Motivation

Python version floor directly shapes:

* **Which typing features are available.** `X | Y` union syntax needs
  3.10; `match` statement needs 3.10; `ParamSpec` and `TypeAlias` are
  3.10+. Running on 3.8 means `Optional[Union[...]]` prose everywhere.
* **Which stdlib modules behave uniformly.** `tomllib` (replacement
  for `toml`) is stdlib-standard on 3.11; before that a vendor dep
  is needed if we read any TOML.
* **How far "preinstalled on Linux" extends.** Debian stable ships
  3.11 (bookworm) and will ship 3.12 (trixie, expected 2026);
  Ubuntu LTS 22.04 ships 3.10, 24.04 ships 3.12; RHEL 9 ships 3.9,
  RHEL 10 ships 3.12; macOS has no preinstalled `python3` — users
  install via `brew install python` (currently 3.12/3.13) or via
  Xcode CLT (3.9).

The parallel to the v005 bash-3.2 reasoning: pick the floor that
matches realistic end-user environments, not the freshest shiny
feature. But unlike bash, Python is reasonable to *require a specific
version via mise* because the runtime dep is "a reasonably current
Python 3," and mise can pin it precisely for livespec developers
without demanding users install mise.

### Proposed Changes

Pick one:

**(a) 3.10 floor (Recommended).** Union syntax (`X | Y`), `match`
statement, parameter-specifying typing, better error messages.
Preinstalled on Ubuntu 22.04 LTS (widely used dev baseline) and
ships in every Debian ≥ 12, Ubuntu ≥ 22.04, Fedora ≥ 36, RHEL 9
(via `python3.11` EPEL or equivalent). Homebrew Python is well
past it. The floor matches what "modern Python 3" means to most
readers without reaching for 3.12-only features.

**(b) 3.11 floor.** Adds `tomllib` in stdlib (useful if `.mise.toml`
or any future TOML file needs reading), `Self` type, nicer tracebacks,
ExceptionGroup. Cost: RHEL 9 base image ships 3.9, so RHEL-only
shops need EPEL or mise-installed Python. Ubuntu 22.04 LTS defaults
to 3.10; 3.11 requires deadsnakes PPA or mise.

**(c) 3.12 floor.** The most expressive option (`type` statement,
improved typing syntax, new PEP 695 generics). Cost: not yet in
most LTS-distro defaults. Macos default via Xcode is 3.9. Excludes
any dev environment that has not upgraded beyond LTS-default.

**(d) 3.8 or 3.9 floor.** Widest compatibility (matches ancient
macOS Xcode CLT, RHEL 8, Ubuntu 20.04). Cost: no union-pipe syntax,
no `match`, more verbose typing annotations, and the style doc
inherits a handful of "work around pre-3.10 typing" rules similar
in spirit to the bash-3.2 accommodations we just retired.

Recommend **(a) 3.10**: matches the most-common "modern Python"
expectation, retains expressive modern typing/match syntax, and
keeps the dev-tooling story honest against Ubuntu 22.04 LTS (still
the default dev-server base in 2026) without forcing mise on every
macOS contributor.

---

## Proposal: P2-runtime-dependency-set

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

dependency-strategy

### Summary

Define the list of hard runtime dependencies the livespec skill
imposes on an end-user machine. v005's list is `bash >= 3.2` + `jq`.
Under Python, the obvious question is whether `jq` survives, whether
any PyPI deps (yaml, jsonschema, etc.) become required, and whether
the skill's bash tool invocation can itself go.

### Motivation

Every runtime dep is a support burden. The fewer deps, the smaller
the "install instructions" surface the skill has to emit on startup
and the more environments "just work."

End-user install-path matrix:

* **Python 3.x itself.** Preinstalled Linux; one-command install on
  macOS (`brew install python@3.10` or the Xcode CLT bundle). The
  skill asserts at startup and exits `127` with an OS-appropriate
  install message if absent/too old — equivalent to v005's bash
  version assertion.
* **jq.** In v005 the skill uses jq for JSON parsing from bash. In
  Python, `json` is stdlib. The only remaining reason to keep jq
  is if bundled LLM prompts invoke jq from the prompt body; that
  is stylistic and reroutable to Python helpers.
* **PyYAML.** Needed iff any file the skill reads/writes is YAML
  (proposed-change/revision front-matter is YAML; today we
  structural-check it with `jq`-over-JSON-ish conversion). PyYAML
  is pure-Python and cheap to vendor.
* **jsonschema.** Useful for validating template I/O JSON and
  `.livespec.jsonc`. Stdlib has no schema validator.
* **Nothing else.** No HTTP clients, no ORMs, no frameworks.

### Proposed Changes

Four candidate deps sets:

**(a) python3 only, pure stdlib, no PyPI, no jq (Recommended).**
Most economical. `json` handles JSON; a small hand-written YAML
parser (YAML front-matter is trivial: `---`, `key: value` lines,
`---`) handles the front-matter we actually use; jsonschema is
replaced by targeted structural checks in Python (the JSON contracts
are narrow enough that a bespoke validator reads cleaner than
pulling a dep). jq is dropped entirely; any prompt that referenced
it is rewritten to name a Python helper. **Downside:** a tiny
hand-rolled YAML parser is only acceptable because front-matter is
this restricted — a full-YAML spec would disqualify this.

**(b) python3 + vendored PyYAML + vendored jsonschema.** Dependencies
ship as `.py` files inside the bundle (no install-time `pip install`
needed). Adds real schema validation and full-YAML parsing.
**Downside:** vendoring adds ~5–10 kLoC to the bundle and a license
audit burden; vendored libs need periodic re-vendor passes.

**(c) python3 + mandatory `pip install pyyaml jsonschema` at the
user's project.** Smallest bundle, cleanest deps. **Downside:**
Anthropic's runtime has no network access at runtime, but the skill
is invoked by Claude Code on the end user's machine where `pip
install` does work — so this is viable but forces every user to run
pip. Contradicts the "single-copy runtime" premise that makes
shipping an installable plugin pleasant.

**(d) python3 + keep jq + stdlib-only Python.** Hybrid: jq remains
for JSON structural checks (back-compat with bash-era prompts) but
Python handles the rest. Most conservative migration but carries two
parsing technologies, which is exactly the duplication the migration
is supposed to eliminate.

Recommend **(a) stdlib-only, drop jq entirely**. Our YAML usage is
restricted enough to hand-parse; our JSON validation is narrow
enough to encode directly. One runtime dep (python3 >= 3.10) is the
cleanest story and matches the migration's motivating thesis.

---

## Proposal: P3-dependency-shipping-mechanism

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

dependency-strategy

### Summary

If any PyPI deps survive P2, decide how they reach the skill at
runtime. Claude Code plugin bundles have no runtime network access
for `pip install`, so vendoring or install-time-only options apply.

### Motivation

Three deployment-time modes:

1. **Stdlib-only.** Nothing to ship. Follows from P2(a).
2. **Vendored.** Ship dep `.py` files inside the skill bundle under
   (e.g.) `scripts/_vendor/`. The package's `__init__.py` prepends
   `_vendor/` to `sys.path`. Works offline, obeys the "runtime has
   no network" constraint, but inflates bundle size.
3. **User-installed.** Require users to install deps via `pip` /
   `uv` / `pipx`. Smallest bundle, smallest runtime footprint,
   biggest friction at install time.

### Proposed Changes

**(a) Stdlib-only; no mechanism needed (Recommended, conditional
on P2(a)).** If P2 picks (a), this proposal is moot — there is no
shipping mechanism because there's no external dep.

**(b) Vendored under `scripts/_vendor/`.** Required iff P2 picks (b).
Specify: leading-underscore directory name (private), single-point
`sys.path` insertion in the dispatch entry point, explicit
`vendor-audit` dev-tooling target that diffs vendored sources
against their upstream version and fails the enforcement suite on
drift. Prefer pure-Python deps; compiled wheels cannot be vendored
portably.

**(c) User-installed via `uv` + `pyproject.toml` at the skill root.**
Required iff P2 picks (c). Specify a committed `pyproject.toml` the
user can `uv pip install` or `pip install` against. The skill adds
a startup import check that emits an install-instructions message
and exits `127` on ImportError.

Recommend **(a)**, contingent on P2(a). If P2 picks (b) or (c), the
corresponding option here is forced.

---

## Proposal: P4-bundle-package-layout

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

layout

### Summary

Decide how Python source files organize under
`.claude-plugin/skills/livespec/scripts/`: flat `.py` files, a
single package, or a namespace/src layout. The v005 layout is
flat-bash-files (`dispatch`, `doctor/run-static`, `doctor/static/
<slug>`). Python's preferred organization is a package with
explicit imports.

### Motivation

Relevant considerations:

* **Bundle ergonomics.** Claude Code loads the skill by file;
  nothing in the plugin format forces a particular Python-import
  shape. The directory tree is readable either way.
* **Import clarity.** A flat pile of `.py` files either re-discovers
  sibling imports via `sys.path` manipulation (ugly) or forces
  `from .foo import bar` with a package `__init__.py` (standard).
* **Doctor-static decomposition.** Each check stays an independent
  unit of failure. Whether they live as package-rooted modules
  (`livespec.doctor.static.out_of_band_edits`) or as loose files
  under `scripts/doctor/static/*.py` changes how the orchestrator
  discovers and invokes them (import vs. subprocess).

### Proposed Changes

**(a) Single package `livespec/` at `scripts/livespec/` with
sub-packages (Recommended).** Layout:

```
.claude-plugin/skills/livespec/scripts/
└── livespec/
    ├── __init__.py
    ├── __main__.py                 # `python3 -m livespec` entry
    ├── dispatch.py                 # parses args, routes to sub-command
    ├── errors.py                   # exception hierarchy (see P21)
    ├── result.py                   # Result / ROP helpers (see P21)
    ├── config.py                   # .livespec.jsonc parsing
    ├── fs.py                       # impure FS wrappers (see P13)
    ├── git.py                      # impure git wrappers (narrow)
    ├── doctor/
    │   ├── __init__.py
    │   ├── run_static.py           # orchestrator
    │   └── static/
    │       ├── __init__.py
    │       ├── livespec_jsonc_valid.py
    │       ├── template_exists.py
    │       ├── ...
    │       └── anchor_reference_resolution.py
    └── commands/
        ├── __init__.py
        ├── seed.py
        ├── propose_change.py
        ├── critique.py
        ├── revise.py
        ├── prune_history.py
        └── doctor.py
```

**`SKILL.md` invokes** `python3 -m livespec <subcommand> [args]`,
which `scripts/livespec/__main__.py` dispatches. Orchestrator
imports each check module and calls its `run(...)` entry; `check_id`
slugs remain stable strings.

**(b) Flat `.py` files under `scripts/`.** No package; each file
`sys.path`-adds its directory. Simpler to show in the layout tree,
but forces either `__file__`-relative `sys.path.insert` or copy-paste
helpers — exactly the kind of module-boundary friction the migration
is meant to retire.

**(c) `src/` layout with editable install.** Cleanest Python library
practice, but overkill for a skill that is never `pip install`ed
as a user library.

Recommend **(a) single-package with sub-packages**. Matches Python
idioms, lets the orchestrator import-load checks instead of
fork+subprocess for each (faster, simpler error surfacing), and
leaves the slug-based check_id contract unchanged at the presentation
layer.

---

## Proposal: P5-linter-formatter-ruff

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

tooling

### Summary

Adopt `ruff` as the single linter + formatter + import-sorter,
replacing `shellcheck` + `shfmt` + `shellharden` + `shellmetrics`.

### Motivation

`ruff` (ruff.rs, by astral.sh) is a Rust-written drop-in for
`flake8` + `black` + `isort` + `pyupgrade` + `mccabe` complexity
checks. One tool, one config file (`pyproject.toml`'s `[tool.ruff]`
section), microseconds-per-file runtime. Already idiomatic in the
2025–2026 Python ecosystem.

This is the dominant choice; there is no serious competitor in
today's Python tooling landscape.

### Proposed Changes

**(a) `ruff` single-tool (Recommended).** Pin `ruff` via mise;
configure rulesets in `pyproject.toml` under `[tool.ruff]`. Adopt
broad rule selection (`E`, `F`, `I`, `B`, `UP`, `SIM`, `C90`, `N`,
`RUF`) with targeted opt-outs. `ruff format` replaces `shfmt`.
`C901` provides mccabe complexity checks (see P9). `RUF` and
subset-of-`PLR` catch additional footguns.

**(b) `ruff` + `black`.** Duplicate formatting surface; no reason
to run both — ruff's formatter is equivalent and coordinated.

**(c) `flake8` + `black` + `isort` legacy stack.** Strictly worse
dev UX; rejected.

Recommend **(a)**. There is no interview question here except to
confirm the recommendation and pick the initial rule selection
scope (which can be a post-seed refinement).

---

## Proposal: P6-type-checker

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

tooling

### Summary

Type checking has no bash analogue. Decide between `mypy` and
`pyright`, the strictness level, and whether the enforcement suite
gates on type errors.

### Motivation

Bash enforcement gaps that a type checker closes:

* Function-signature mismatches (wrong number / kind of args).
* Optional-vs-required fields in JSON dicts.
* Exhaustiveness on `match` statements / union types.
* Return-type inconsistencies.

In bash, these surface as "value of type string cannot be used as
array", at runtime, in production. Python typing makes them static.

Tools:

* **mypy** — Python Software Foundation's reference checker,
  mature, slower, plugin ecosystem, conservative default strictness.
* **pyright** — Microsoft-developed, Rust-fast, stricter defaults,
  better control-flow narrowing, newer PEP support. Ships as part
  of Pylance and `pyright` CLI.
* **ty** — astral's newer checker, not yet stable (late-2025); not
  recommended for v1 but worth monitoring.

### Proposed Changes

**(a) pyright in strict mode (Recommended).** Configure
`[tool.pyright]` in `pyproject.toml` with `strict` level; pin
`pyright` via mise. Enforcement: `make check-types` fails on any
pyright diagnostic. Strict mode yields the strongest static
guarantees and is the choice that pays back the ROP/type-safety
architectural mandate (P21) best.

**(b) mypy in strict mode.** Equivalent rigor with a slower
feedback loop. Broader plugin ecosystem (useful if we ever need
custom plugins for the Result-type idiom from P21, though pyright
handles such patterns via TypeGuard/PEP 695 generics without
plugins).

**(c) Type checker present but non-blocking.** Run mypy/pyright in
advisory mode; let developers see warnings without failing CI.
Discouraged — the entire premise of P6 is that static checking is
worth something only if it gates.

Recommend **(a) pyright strict**. Faster, stricter defaults, better
narrowing; the existing ROP-patterns reference projects generally
use pyright.

---

## Proposal: P7-test-framework

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

tooling

### Summary

Adopt `pytest` as the test framework, replacing `bats-core` +
`bats-assert` + `bats-support`. Specify fixture discipline,
parametrization patterns, and the `tmp_path` idiom that replaces
bats's `BATS_TEST_TMPDIR`.

### Motivation

`pytest` is the dominant Python test framework; the stdlib
`unittest` module is strictly less ergonomic and has no realistic
case in a fresh 2026 project.

Bash-era bats idioms and their pytest analogues:

| bash / bats | Python / pytest |
|---|---|
| `@test "name"` | `def test_name(...):` |
| `run cmd` + `[ "$status" -eq 0 ]` | `subprocess.run(..., check=True)` or in-process import |
| `BATS_TEST_TMPDIR` | pytest `tmp_path` fixture |
| `tests/fixtures/` read-only | same, unchanged |
| `bats-assert` structured diffs | pytest's default assertion introspection (with `pytest-diff` or `pytest-icdiff` if richer diffs wanted) |
| `setup` / `teardown` | pytest fixtures with `yield` |
| Stubbing impure wrappers by re-defining them in the test | pytest `monkeypatch` fixture (per-test patching) |

### Proposed Changes

**(a) pytest with tmp_path + monkeypatch + parametrize (Recommended).**
Standard Python testing practice. Tests at `tests/livespec/` mirror
`scripts/livespec/` 1:1 (see P11 for the full tree). Per-spec-file
tests (`test_spec.py`, `test_contracts.py`, etc.) stay at
`tests/` root, as in v005, with the same heading-coverage.json
meta-test.

**(b) pytest + pytest-mock + pytest-benchmark + pytest-xdist
plugin soup.** Heavier dep tail; most of these are unnecessary for
the project's size.

**(c) stdlib `unittest`.** Rejected; worse ergonomics, no parametrize,
no fixtures worth the name.

Recommend **(a)**. Interview question is whether any additional
plugins are needed from the start (e.g., `pytest-asyncio` is a
no-op unless we adopt async, which livespec doesn't need).

---

## Proposal: P8-coverage

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

tooling

### Summary

Adopt `coverage.py` (via `pytest-cov`), replacing `kcov`. Reset the
coverage thresholds because kcov's DEBUG-trap artifacts no longer
apply.

### Motivation

The v005 "pure libraries ≥ 95% / overall ≥ 80%" split arose because
kcov under-reports on bash by a few percentage points on
short-circuit chains and multi-line tests. `coverage.py` has no
such artifact; branches, lines, and partial-line executions are
measured accurately.

kcov was also Linux-only. `coverage.py` is pure Python and runs
everywhere Python runs — the "Linux-only for coverage" carve-out
disappears. Docker wrapper for coverage is retired.

### Proposed Changes

**(a) `coverage.py` via `pytest-cov`; 100% line + branch for pure
code, ≥ 90% overall (Recommended).** The purity discipline
(P13) still exists, but the tooling artifact that forced 95% is
gone; we can return to 100% for pure code (what the v005 proposal
originally wanted) and raise the overall bar. Coverage enforced via
`make check-coverage`. `pyproject.toml`'s `[tool.coverage.run]`
section configures source and branch settings.

**(b) Keep the 95%/80% tiers as-is.** Safe but wastes the
tooling-upgrade opportunity. No reason in Python to accept less
than the semantic truth.

**(c) 100% line + branch for the whole skill, no tiers.**
Aspirational; requires that genuinely hard-to-cover code paths
(e.g., filesystem error branches) have explicit test fixtures.
Harder but cleaner.

**(d) No coverage gate.** Rejected; regresses v005's discipline.

Recommend **(a)**: 100% pure / ≥ 90% overall. Restores the v005
intent with the tooling artifact removed; keeps the pure/impure
distinction load-bearing. If the interview on P13 drops the
pure/impure discipline, this proposal collapses to the single-tier
option under **(c)**.

---

## Proposal: P9-complexity-thresholds

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

rule-simplification

### Summary

Revisit the v005 complexity thresholds (CCN ≤ 10, args ≤ 6, function
LLOC ≤ 50, file LLOC ≤ 300) now that Python's expressiveness changes
what "complex" looks like.

### Motivation

Python's built-ins collapse many bash patterns. A 15-LLOC bash
function that hand-rolls a `{k=v}` parser is a 2-line Python dict
comprehension. The raw LLOC thresholds therefore want tightening —
not loosening.

`ruff`'s `C901` mccabe check defaults to 10 (matching v005). Per
idiomatic Python practice, project-level complexity limits are often
tighter than the default. Args-limit is an idiosyncratic rule that
isn't common in Python style guides — dataclasses and keyword-only
args handle the "many parameters" case naturally.

### Proposed Changes

**(a) CCN ≤ 10 (ruff C901 default), function body ≤ 30 logical
lines, file ≤ 200 logical lines, positional-args rule dropped
(Recommended).** LLOC targets tightened because Python is denser
than bash per semantically equivalent unit. Args limit retired
because it doesn't match Python idioms (keyword-only args and
dataclasses decompose large parameter sets naturally).

**(b) Keep v005's thresholds unchanged (CCN 10, LLOC 50, args 6,
file 300).** Safe and boring; ignores Python density.

**(c) Per-function waivers permitted via a pragma comment.**
Rejected in v005 (B11); no new reason to relax.

**(d) Drop all complexity gating.** Too permissive; undermines the
discipline that survived v005.

Recommend **(a)**. The Python migration is the moment to rebaseline
the thresholds; keeping the bash-era numbers embeds a tool-specific
accommodation (bash-dense 50-line functions) that Python doesn't
warrant.

---

## Proposal: P10-enforcement-suite

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

enforcement-suite-shape

### Summary

Rewrite the Makefile target list for the Python toolchain. The
invocation-agnostic framing (pre-commit / pre-push / CI / manual are
consumers of Makefile targets) stays; the target names change.

### Motivation

The v005 enforcement suite had 15+ Make targets, many of which were
bash-specific or compensated for bash's missing features. Most
collapse.

| v005 target | Python replacement |
|---|---|
| `check-shellcheck` | **dropped** — subsumed by `check-lint` (ruff) |
| `check-shfmt` | **dropped** — subsumed by `check-format` (ruff format) |
| `check-shellharden` | **dropped** — subsumed by ruff's strictness |
| `check-complexity` | **kept** — ruff C901 + file/function LLOC helper |
| `check-executable-bit` | **replaced** — `check-entry-points`: only `__main__.py` / scripts with shebangs require executable bit |
| `check-filename-blacklist` | **dropped** — Python idioms handle names; ruff `N`-rules flag weird naming |
| `check-library-headers` | **dropped** — Python modules have docstrings; no structured header directive needed |
| `check-sourceable-guards` | **replaced** — `check-main-guard`: verifies `if __name__ == "__main__":` in executable modules |
| `check-private-calls` | **replaced** — `check-private-calls`: `ast.walk` over all modules, reject cross-package imports of `_name` |
| `check-source-graph` | **replaced** — `check-import-graph`: cycle detection using `ast` import parse |
| `check-global-writes` | **replaced** — `check-global-writes`: `ast`-walk for module-level mutable state writes |
| `check-arg-count` | **dropped** — args count not enforced |
| `check-tests` | **kept** — runs pytest |
| `check-coverage` | **kept** — pytest-cov; Linux/macOS/Windows all work |
| `check-tools` | **kept** — verifies mise-pinned tool versions |
| `check` | **kept** — runs the full suite |
| (new) `check-types` | **new** — pyright/mypy; gates on any error |
| (new) `check-format` | **new** — `ruff format --check` |
| (new) `check-lint` | **new** — `ruff check` |

### Proposed Changes

**(a) Target list per table above (Recommended).** The net is 6
dropped targets, 5 renamed/replaced, 3 new, 4 kept — a ~40%
shrinkage, in line with the migration's stated goal. All AST
checks move from `tree-sitter-bash` (external dep) to `ast` (stdlib).

**(b) Keep every v005 target name; only change implementation
language.** Rejected — preserves bash-era taxonomy where the
underlying concern has dissolved.

**(c) Drop every check except lint/format/types/tests/coverage.**
Too aggressive; the AST-level architectural checks (private-calls,
import-graph, global-writes) earn their keep.

Recommend **(a)**.

---

## Proposal: P11-doctor-static-layout

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

layout

### Summary

v005 decomposed `doctor-static` into per-check executables under
`scripts/doctor/static/<slug>`. Decide whether that decomposition
carries over with `.py` modules, and preserve the slug-based
`check_id` contract.

### Motivation

Python's import story makes the decomposition cheaper than bash's
was:

* In bash, every per-check file was a separate fork+exec invocation
  by the orchestrator.
* In Python, the orchestrator can `importlib.import_module` each
  check module and call its `run()` function in-process. One
  `python3` interpreter per doctor invocation, not N.

But the decomposition still has per-check testing and insert/delete
benefits v005 valued. The question is only about file layout and
invocation, not about contract (which is slug-based and stable).

### Proposed Changes

**(a) One module per check, imported by the orchestrator in-process;
slug-based `check_id` and per-module `run(context) → Result[Findings,
Error]` contract (Recommended).** Mirrors v005's per-check
executable decomposition. Tests at
`tests/livespec/doctor/static/<slug>.py`. Slug ↔ filename mapping:
slug `out-of-band-edits` ↔ module `out_of_band_edits.py` — Python
can't use hyphens in module names, so the style doc SHOULD codify
the underscore/hyphen mapping. Orchestrator emits `check_id`
values as `doctor-<slug>` with hyphens (user-facing contract
unchanged). The mapping is one-line in `scripts/livespec/doctor/
static/__init__.py`.

**(b) Single `doctor/static.py` module with dispatch functions.**
Collapses per-check isolation, loses per-file testing; not
recommended. The v005 argument against the monolithic design (B20)
still applies.

**(c) Per-check subprocess executables at `scripts/doctor/static/
<slug>` (extensionless files with `#!/usr/bin/env python3`
shebangs).** Preserves 1:1 bash-era invocation shape but loses
in-process import benefits and fights Python packaging idioms.

Recommend **(a)**: module-per-check, slug↔module-name mapping
codified, orchestrator imports in-process.

---

## Proposal: P12-main-guard-idiom

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

rule-simplification

### Summary

v005 mandates the sourceable-guard idiom at the end of every
executable bash script:

```bash
if [[ "${0}" == "${BASH_SOURCE[0]}" ]]; then
  main "$@"
fi
```

Python has the built-in `if __name__ == "__main__":` idiom. Confirm
adoption.

### Motivation

This is the most trivial direct substitution in the migration.
`__name__` is set to `"__main__"` only when the file is executed
directly (including via `python -m pkg.module`). Tests import the
module and inspect / call named functions; the guard prevents
unwanted execution on import.

### Proposed Changes

**(a) Use `if __name__ == "__main__": main()` in every executable
Python entry point; style-doc rule is one paragraph (Recommended).**
Enforced by the `check-main-guard` ruff-equivalent or by an AST
custom check.

**(b) Skip the guard; structure the codebase so no executable
module is ever imported elsewhere.** Rejected — breaks testing.

Recommend **(a)**. This is table-stakes Python.

---

## Proposal: P13-purity-rule-fate

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

rule-simplification

### Summary

The v005 pure/impure library directive compensates for bash's lack
of dependency injection. Python's namespaces, classes, and
pytest's `monkeypatch` provide DI directly. Decide whether to drop
the directive, keep it as a soft convention, or keep it as a
mechanical AST-enforced rule.

### Motivation

Arguments for keeping:

* The rule enforces a testability discipline that's valuable beyond
  bash. Pure functions remain easier to reason about in any
  language.
* The enforcement check (no I/O in pure modules, no env writes)
  is cheap in Python (`ast.walk` over a small allow-list of
  side-effecting calls).
* Ties cleanly to the ROP mandate (P21) — pure functions return
  `Result[Success, Failure]`; impure functions wrap side-effecting
  I/O.

Arguments for dropping:

* The main motivation (compensate for bash's missing module
  boundaries) evaporates.
* pytest's `monkeypatch` and Python's first-class function
  references make stubbing trivial without a pure/impure directive.
* Less machinery to explain in the style doc.

### Proposed Changes

**(a) Keep pure/impure as a mechanical AST-enforced rule, simpler
formulation than v005 (Recommended).** Each module declares
`__purity__ = "pure"` or `"impure"` at module top (simple Python
constant, no comment-directive parsing). Custom AST check verifies
pure modules contain no `open()`, `os.*` file ops, `subprocess.*`,
`requests.*`, or module-level mutation. Pure modules MAY call
impure ones only via injected dependencies. Stronger rule than v005
because Python's DI story lets us actually enforce it with no
workarounds.

**(b) Keep pure/impure as prose guidance only, no enforcement.**
Weakens the rule to a suggestion; discipline survives review but
not CI.

**(c) Drop the pure/impure directive entirely.** Retains ordinary
Python testability patterns (fixtures, monkeypatch) without adding
a concept.

Recommend **(a)**. The discipline earned its place in v005; it
remains useful in Python and costs less to enforce than it did in
bash (one `ast.walk`, no tree-sitter).

---

## Proposal: P14-debug-logging

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

rule-simplification

### Summary

Replace `LIVESPEC_XTRACE` / `LIVESPEC_VERBOSE` bash env switches
with Python's stdlib `logging` module, configured by a single env
var or `-v` / `-vv` CLI flag.

### Motivation

`logging` is a stdlib module that delivers leveled logs (DEBUG,
INFO, WARNING, ERROR, CRITICAL), per-module loggers, structured
formatting, and handler routing out of the box. It's the idiomatic
Python mechanism.

Bash-era env vars map to log levels:

* `LIVESPEC_XTRACE=true` ≈ `DEBUG` (every logged call with line
  info).
* `LIVESPEC_VERBOSE=true` ≈ `INFO`.
* Default ≈ `WARNING` (quiet unless something's wrong).

CLI flags give a faster loop for developers: `-v` → INFO,
`-vv` → DEBUG.

### Proposed Changes

**(a) stdlib `logging`, configured by `LIVESPEC_LOG_LEVEL` env var
(accepting DEBUG / INFO / WARNING / ERROR / CRITICAL) and `-v` /
`-vv` CLI flags on every sub-command (Recommended).** CLI flag
wins when both are set. Default level WARNING. Log format includes
module name + level so per-module filtering is possible via
`LIVESPEC_LOG_MODULES` optional env var.

**(b) Keep separate `LIVESPEC_XTRACE` and `LIVESPEC_VERBOSE` env
vars for parity with v005.** Rejected — conflates two distinct
concerns (trace emission, verbose progress) that `logging`'s level
system models better.

**(c) `rich` / `loguru` / `structlog` third-party.** Rejected —
stdlib is enough; adding a dep loses more than the ergonomic gain.

Recommend **(a)**.

---

## Proposal: P15-exit-codes

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

rule-simplification

### Summary

v005's exit-code contract is 0 (success), 1 (internal failure),
2 (usage error), 3 (precondition failed), 126 (permission denied),
127 (required tool missing). Python's convention is to raise
exceptions and let uncaught ones produce exit 1 (and a traceback).
Decide how to preserve the contract semantically.

### Motivation

The contract has real users — sub-commands' doctor pre-step checks
the static-phase orchestrator's exit code and branches on `3` vs
`1` vs `0`. Breaking the contract breaks the invocation surface.
Preserving it means wrapping Python's native exception story in a
deliberate exit-code translation at the entry point.

### Proposed Changes

**(a) Explicit `sys.exit(n)` at every `__main__.py` with an error
hierarchy that maps to exit codes (Recommended).** Define a small
exception hierarchy in `scripts/livespec/errors.py`:

```python
class LivespecError(Exception): exit_code = 1
class UsageError(LivespecError): exit_code = 2
class PreconditionError(LivespecError): exit_code = 3
class PermissionError_(LivespecError): exit_code = 126
class ToolMissingError(LivespecError): exit_code = 127
```

Entry point in `__main__.py` catches `LivespecError`, prints the
message to stderr, and calls `sys.exit(err.exit_code)`. Anything
else bubbles as an uncaught exception → traceback to stderr, exit
1. Preserves the v005 contract without forcing Python code to
`sys.exit(n)` throughout.

**(b) `sys.exit(n)` calls scattered wherever exit code matters.**
Works but less Pythonic; harder to test (exit calls need
special-case handling in tests) and harder to enforce consistency.

**(c) Reduce to 0 / 1 / non-zero.** Breaks the v005 contract; callers
(the orchestrator, pre-step checks) break.

Recommend **(a)**.

---

## Proposal: P16-file-naming-invocation

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

layout

### Summary

Python files carry `.py`. Direct execution needs either a shebang
+ chmod+x or `python3 script.py` invocation. Decide the convention
and whether `SKILL.md` references `scripts/dispatch.py`,
`python3 scripts/dispatch.py`, `python3 -m livespec.dispatch`, or
a bash stub.

### Motivation

The v005 bash-era mandate was "no `.sh` extension on executables."
Python carries `.py` always; stripping extensions from Python files
is counterproductive (breaks imports, breaks tooling).

Invocation options for the skill entry:

* **`scripts/dispatch.py`** with shebang + chmod+x, invoked by
  relative path.
* **`python3 scripts/dispatch.py`** invoked explicitly.
* **`python3 -m livespec`** leveraging P4(a)'s package with
  `__main__.py`.
* **`scripts/dispatch` (bash stub)** that `exec`s `python3 -m
  livespec "$@"` — see P17.

### Proposed Changes

**(a) `python3 -m livespec` via package `__main__.py`; no shebangs
needed on library modules; `SKILL.md` references it directly
(Recommended, contingent on P4(a) and P17(b)).** Python's
recommended way to run a package. No executable bit needed; relies
on `python3` on PATH.

**(b) `scripts/dispatch.py` with shebang + chmod+x.** Works but
demands every doctor-static module also carry a shebang, or else
the orchestrator can't subprocess them — which we've already decided
against via P11(a).

**(c) Bash stub `scripts/dispatch` that exec's `python3 -m
livespec`.** See P17 for the full shape — this is the
backwards-compatible option.

Recommend **(a)** in combination with P17(b) (no bash stub). The
`SKILL.md` invocation `python3 -m livespec <subcommand> <args>`
is canonical and terse.

---

## Proposal: P17-dispatch-bash-stub

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

backwards-compatibility

### Summary

Decide whether `scripts/dispatch` survives as a ~10-line bash stub
that `exec`s `python3 -m livespec`, or whether the skill goes
all-Python with direct `python3 -m` invocation.

### Motivation

Arguments for the bash stub:

* `SKILL.md`'s invocation syntax stays the same; only the stub's
  internals change.
* If the skill ever gains additional language scripts, the stub can
  be the switchboard.

Arguments against:

* Adds a second language to the runtime surface that the migration
  explicitly aims to eliminate.
* Requires the user's bash to be present and on PATH — historically
  true on macOS and Linux, but less portable than "python3 is
  enough."
* Keeps the bash style doc alive in a reduced form for one file,
  which contradicts P18's drop-the-bash-doc intent.

### Proposed Changes

**(a) Keep a minimal bash stub at `scripts/dispatch`.** SKILL.md
references `scripts/dispatch "$@"`; stub runs `exec python3 -m
livespec "$@"`. Preserves a stable invocation path. Requires
keeping a minimal bash style doc (maybe 1 page) for this one file.

**(b) No bash stub; SKILL.md invokes `python3 -m livespec`
directly (Recommended).** Matches the stated migration intent
(fully retire bash). The stub's only value is abstract
insulation, not worth the cost of maintaining two language
toolchains.

Recommend **(b)**.

---

## Proposal: P18-bash-style-doc-fate

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

backwards-compatibility

### Summary

`bash-skill-script-style-requirements.md` is replaced by a new
`python-skill-script-style-requirements.md`. Decide what happens to
the retired bash doc: delete, or archive under
`history/v006/retired-documents/`.

### Motivation

The v001–v005 history already archives per-version copies of the
style doc inside `history/vNNN/` (as part of the whole PROPOSAL.md
snapshot references). The doc itself is not "lost" if we delete
the top-level copy — v005's version lives forever at
`history/v005/...` (implicitly, since the brainstorming folder's
history/vNNN/ doesn't itself snapshot companion docs, per v005
practice; the bash style doc was a brainstorming-folder companion,
not a snapshotted artifact).

Actually, because the bash style doc was a companion (not something
v001–v005 snapshotted into history/), the archive decision is
load-bearing: if we delete it outright, the bash-era rules are
readable only via `git show <old-commit>:...`; if we archive it
under history/v006/retired-documents/, it stays findable on disk.

### Proposed Changes

**(a) Archive under `history/v006/retired-documents/
bash-skill-script-style-requirements.md` with a one-paragraph
`README.md` noting why it was retired (Recommended).** Keeps the
reference discoverable without cluttering the working brainstorming
folder. Consistent with the v005 framing that history is the
on-disk long-term record.

**(b) Delete the file outright.** Cleaner working tree; `git log` /
`git show` preserves the historical content. But the retirement
context — why bash was swapped for Python — disappears from the
on-disk record.

**(c) Keep the bash doc at its original location alongside the new
Python doc.** Rejected — documents two conflicting languages
without a reason; readers have to infer which applies.

Recommend **(a)**.

---

## Proposal: P19-bash-boilerplate-fate

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Axis

backwards-compatibility

### Summary

Delete `.claude-plugin/skills/livespec/scripts/bash-boilerplate.sh`
and its symlink at `dev-tooling/bash-boilerplate.sh`. Python has no
shared-boilerplate analogue (strict mode, error traps, version
check are all either default Python behavior, or handled by a small
module that's imported, not sourced).

### Motivation

Every reason for bash-boilerplate.sh evaporates in Python:

* **Strict mode (`errexit`, `errtrace`, `pipefail`, `nounset`).**
  Python's exceptions are strict by default; unhandled errors
  propagate.
* **Version assertion.** One `if sys.version_info < (3, 10)` at
  `scripts/livespec/__main__.py` handles it.
* **Exit traps / onexit diagnostics.** `try/finally` / context
  managers / `atexit` handle this cleanly when needed.
* **xtrace / verbose affordances.** `logging` module (P14).
* **Error-check toggle helpers.** Not applicable.

The symlink at `dev-tooling/bash-boilerplate.sh` disappears with
the file.

### Proposed Changes

**(a) Delete both the bundled boilerplate and the dev-tooling
symlink (Recommended).** Nothing to replace it with; Python
doesn't need it.

**(b) Introduce a replacement `scripts/livespec/_boilerplate.py`
that consolidates version-check + logging setup.** Workable but
overkill — the version check is one line; logging setup is a few
more. They live cleanly in `__main__.py` without a new shared
module.

Recommend **(a)**.

---

## Proposal: P20-bash-retention

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

backwards-compatibility

### Summary

Broader question: is ANY bash retained in v006? Candidates include
a mise install hook, a CI setup shim, or a pre-commit-config
bootstrap script.

### Motivation

Even with P17(b) (no dispatch stub) and P19(a) (no boilerplate),
the repo may grow small bash touchpoints: `.pre-commit-config.yaml`
isn't bash but it can invoke bash commands; mise hooks use bash by
convention.

Deciding the question up front prevents the "just this one bash
script" drift that would keep the bash style doc on life support.

### Proposed Changes

**(a) No bash in the skill bundle; small bash in dev-tooling
wrappers is OK but covered by a two-paragraph style note, not a
full style doc (Recommended).** Realistic: the pre-commit hook's
shell invocations, a `make bootstrap` target, or a mise hook may
contain a line or two of bash. That's not enough to warrant a
full style doc. A two-paragraph "if you write bash glue, use
`set -euo pipefail` and quote everything" note in the Python style
doc is enough.

**(b) Zero bash anywhere in the repo.** Aspirational but may force
Python for trivial glue where bash is genuinely simpler
(`#!/usr/bin/env bash` for a 3-line CI setup step). Hardens the
migration at the cost of occasional awkwardness.

**(c) Bash is allowed for any dev-tooling script as long as it
conforms to the retained bash style doc.** Rejected — inverts P18.

Recommend **(a)**.

---

## Proposal: P21-rop-pattern

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md (new)

### Axis

architecture-pattern

### Summary

`python-conversion-prompt.md` mandates:

> Functional, Type Safety, and Railway Oriented Programming (ROP)
> patterns MUST be used.

Decide the concrete shape of this mandate in the Python style doc:
a `Result` type, `bind`/`map` helpers, and rules about when
functions return `Result` vs raise exceptions.

### Motivation

ROP (from F# by Scott Wlaschin) models function composition over
success/failure tracks. Each function returns `Result[Success,
Failure]`; composition via `bind` / `map` short-circuits on the
failure track. Integrates with Python type-safety via generics —
`pyright strict` can verify the tracks are correctly threaded.

Reference projects cited in the prompt:

* `https://github.com/thewoolleyman/tab-groups-windows-list/blob/master/adws/adw_modules/engine/README.md` (Python ROP examples).
* `https://gitlab.com/gitlab-org/gitlab/-/blob/master/ee/lib/remote_development/README.md#railway-oriented-programming-and-the-result-class` (Ruby ROP; see module structure).
* `https://fsharpforfunandprofit.com/rop/` (F# originals).

Two questions for the style doc:

1. **Which `Result` implementation?** Hand-rolled `Result` type in
   `scripts/livespec/result.py`, or a third-party library
   (`returns`, `result`, `expression`)?
2. **When does ROP apply?** Everywhere the codebase has a
   fallible-value boundary (I/O, parsing, validation), or only
   at named architectural seams?

### Proposed Changes

**(a) Hand-rolled `Result[T, E]` in `scripts/livespec/result.py` +
ROP-at-every-fallible-boundary rule; exceptions reserved for truly
exceptional cases (Recommended).** Pattern:

```python
from dataclasses import dataclass
from typing import Generic, TypeVar
T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)

@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

Result = Ok[T] | Err[E]
```

Helpers for `map`, `bind`, `unwrap`, `unwrap_or`. Module-level rule:
functions that parse, validate, or touch the filesystem return
`Result[_, LivespecError]`; the `__main__.py` entry point unwraps
at the top and translates `Err` → `sys.exit(err.error.exit_code)`
(integrates with P15).

Exceptions reserved for: (1) "programmer error" cases (assertion
failures, impossible states); (2) integration-with-third-party
code that raises (wrap at the boundary into `Result`).

**(b) Third-party library (`returns` / `result` / `expression`).**
Well-maintained options exist. `returns` is the most idiomatic for
Python, includes `@safe` decorator to auto-wrap exception-raising
code, and has pyright support. Cost: vendoring or user-install.
If P2/P3 settle on stdlib-only, we can't use this option; the
library is incompatible with that constraint.

**(c) No ROP. Functional style without Result; raise exceptions
conventionally.** Rejected — contradicts the python-conversion-
prompt.md mandate.

**(d) Optional ROP (documented as a SHOULD, not a MUST).**
Rejected for the same reason.

Recommend **(a)** in combination with P2/P3(a) (stdlib-only). The
Result type is small; writing it ourselves keeps the stdlib-only
promise, produces a style doc readers can grok in 10 minutes, and
doesn't depend on external-library maintenance.

---

## Summary and open sequencing

Proposal dependency graph (not a full ordering, just load-bearing
edges):

* P1 (Python version floor) ← precedes every subsequent typing decision (P6, P21(a)'s generics syntax).
* P2 (runtime deps) ↔ P3 (shipping mechanism) ↔ P21 (Result implementation).
* P4 (package layout) ← P11 (doctor-static layout) and P16 (file naming).
* P17 (dispatch stub) ↔ P16 (invocation) ↔ P18 (bash-doc fate) ↔ P20 (bash retention).

Interview will proceed in that rough order, one question per turn.

| Proposal | Axis | Recommendation |
|---|---|---|
| P1 Python version floor | language-floor | 3.10 |
| P2 Runtime deps | dependency-strategy | stdlib-only, drop jq |
| P3 Dep shipping | dependency-strategy | none needed (stdlib) |
| P4 Package layout | layout | single `livespec` package |
| P5 Linter/formatter | tooling | ruff single-tool |
| P6 Type checker | tooling | pyright strict |
| P7 Test framework | tooling | pytest + tmp_path + monkeypatch |
| P8 Coverage | tooling | coverage.py; 100% pure / ≥ 90% overall |
| P9 Complexity | rule-simplification | CCN 10 / func 30 / file 200; drop args limit |
| P10 Enforcement suite | enforcement-suite-shape | per target table above |
| P11 Doctor-static | layout | module-per-check, in-process import |
| P12 Main guard | rule-simplification | `if __name__ == "__main__"` |
| P13 Purity rule | rule-simplification | keep, AST-enforce |
| P14 Debug/logging | rule-simplification | stdlib `logging` + `LIVESPEC_LOG_LEVEL` |
| P15 Exit codes | rule-simplification | exception hierarchy → `sys.exit` |
| P16 File naming | layout | `python3 -m livespec` |
| P17 Dispatch stub | backwards-compatibility | no stub |
| P18 Bash doc fate | backwards-compatibility | archive under history/v006/retired-documents/ |
| P19 Bash boilerplate | backwards-compatibility | delete both |
| P20 Bash retention | backwards-compatibility | no skill bash; two-paragraph note covers dev glue |
| P21 ROP pattern | architecture-pattern | hand-rolled Result + ROP at every fallible boundary |

Open to additions mid-interview if discussion surfaces gaps the
initial plan missed (e.g., concurrency story, packaging metadata
for plugin-marketplace preparation, platform matrix for pytest).
