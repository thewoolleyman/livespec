---
topic: proposal-critique-v04
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-22T00:00:00Z
---

# Critique scope

This critique focuses **specifically** on
`bash-skill-script-style-requirements.md` (henceforth "the style doc")
and the downstream consequences of its rules on `PROPOSAL.md` and on
any realistic implementation of the `livespec` skill. The driving
question is whether every mandated rule is:

1. **Possible** to satisfy (tools exist, constructs are expressible).
2. **Pragmatic** for day-to-day authoring (the rule's cost is
   proportional to its benefit; authors will actually follow it).
3. **Maintainable** for real-life usage (CI gates are stable;
   tooling upgrades don't cause surprise regressions).
4. **Internally consistent** (no self-contradictions within the
   style doc or between it and PROPOSAL.md).

Other aspects of the style doc (e.g., BCP 14 discipline, general
Wooledge citations) are assumed sound and are not re-critiqued here.

Items are labelled `B1`–`B20+` to distinguish them from the general
PROPOSAL.md critique numbering in prior rounds.

---

## Proposal: B1-final-line-rule-contradicts-sourceable-guard

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **malformation** (self-contradiction within the style
doc). Two sections prescribe different final lines for an executable
script, and both are phrased as `MUST`.

### Motivation

§"Functions and `main`" states:

> Every runnable script MUST define a `main` function and invoke it
> as `main "$@"` on the final line.

§"Testability requirements — Sourceable guard for executable scripts"
states:

> The script's final statement MUST therefore be:
>
> ```
> if [[ "${0}" == "${BASH_SOURCE[0]}" ]]; then
>   main "$@"
> fi
> ```
>
> not a bare `main "$@"`.

These two rules cannot both be satisfied. Either the script's final
line is bare `main "$@"` (first rule) or it is the `fi` of the guard
block (second rule). Two implementers writing scripts "to spec" will
produce scripts with different sourceability semantics: bare `main
"$@"` runs `main` on every `source`, defeating every bats test.

An implementer resolving the conflict by guesswork produces non-
uniform scripts; a pre-commit hook that checks for the guard idiom
rejects scripts that satisfy the first rule.

### Proposed Changes

Pick one rule and delete the other. The sourceable guard is
load-bearing for the testing strategy (bats sources scripts to reach
their internal functions), so keep it. Rewrite §"Functions and
`main`" to match:

> Every runnable script MUST define a `main` function and invoke it
> through the sourceable guard idiom specified in §"Testability
> requirements — Sourceable guard for executable scripts". A bare
> `main "$@"` on the final line is forbidden.

Remove the "the `set +o nounset` / `main "$@"` / `set -o nounset`
wrap that appears in some older bash idioms" parenthetical, which is
now about an idiom the doc no longer permits.

---

## Proposal: B2-kcov-100-percent-pure-coverage-infeasible

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incorrectness** (mandates a threshold the chosen
tool cannot reliably produce). `kcov`'s bash coverage uses bash's
DEBUG trap, which instruments at simple-command granularity. Several
common constructs don't register as separate lines even when every
"executable line" is exercised:

- Short-circuit expressions (`a && b || c`) emit a single DEBUG event
  for the whole chain, so one untested branch may not drop coverage
  below 100%, but one *tested* branch may also fail to register as
  hit.
- Multi-line `[[ ... ]]` tests split across continuation lines often
  register only the first line.
- `case` arms that only contain a variable assignment sometimes
  register as the pattern line, not the body.

The result: on real bash projects, `kcov` commonly reports 95–98%
line coverage even when every statement has a test. A 100% MUST gate
therefore blocks CI on tool artifacts, not on missing tests.

### Motivation

§"Code coverage" mandates:

> Pure libraries MUST achieve 100% line coverage.

and the only documented waiver is "kcov is known to be flaky on
Alpine/musl and unavailable on macOS." That carve-out is
platform-based, not threshold-based — the 100% Linux gate remains.

Secondary concerns:

- `kcov` pins matter enormously: the doc says "small differences in
  how `kcov` handles bash's DEBUG trap can shift reported coverage by
  several percentage points" — yet a 100% threshold has zero tolerance
  for that shift.
- `bashcov` (permitted alternative) has the same DEBUG-trap
  limitations plus a Ruby dependency.

### Proposed Changes

Either:

(a) **Lower the pure-library threshold** to a realistic value (≥ 95%)
    that survives normal DEBUG-trap artifacts while still catching
    untested functions.

(b) **Permit `# kcov-ignore-line` / `# kcov-ignore-branch`
    annotations** for DEBUG-trap artifacts, with a CI sub-check
    capping the annotation count (e.g., ≤ 5 per library) so the
    escape hatch is bounded.

(c) **Accept the current mandate** and document that any
    `kcov`-artifact coverage gap MUST be worked around by refactoring
    the offending function into a more granular shape — and that this
    may be required even when semantic coverage is genuinely 100%.

Recommend (a) or (b). (c) is workable but wastes engineering effort
on tool artifacts.

---

## Proposal: B3-ast-level-enforcement-checks-hard-to-implement

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incompleteness** (mandates checks whose
implementability is unresolved). Three enforcement checks require
understanding bash semantics that no off-the-shelf bash-in-bash tool
provides, and the doc explicitly declines to specify an
implementation.

### Motivation

The enforcement suite (exposed through Makefile entry points,
invocable from pre-commit, pre-push, CI, or manually) mandates:

1. **Cross-library private-function-call check**: "rejects any call
   from file A to a `_`-prefixed function defined in file B." This
   requires resolving, for every function-call site, which file
   defined the current binding. Bash has no reflection API that yields
   "file of origin"; a grep must parse all sources, build a
   function→file map, and re-parse all callers — while distinguishing
   a call from a variable assignment that happens to contain a
   matching string.

2. **Source-dependency-graph check**: "rejects any circular import."
   Bash `source` calls can be dynamic (`source "$lib"`), conditional
   (`[[ "$x" ]] && source y`), or nested inside functions. Static
   analysis of `source` statements misses the dynamic cases and
   over-reports conditional cases as unconditional.

3. **Global-variable-write check**: "rejects any function-body
   assignment not preceded by `local`, `declare`, or `readonly`."
   This must distinguish legitimate cases from forbidden ones:
   - `array[i]=x` (subscript write; variable is outer-scope but this
     is array indexing)
   - `declare -a arr; arr[0]=x` (declared, then subscript)
   - `local -n ref=outer; ref=x` (nameref write; the function IS
     writing an outer scope, but the rule's "explicit, documented
     outer-scope-write patterns" exception may or may not cover it)
   - `x=y` inside `"${x:=y}"` (parameter expansion default)

The doc says "exact implementation is left to the skill, but the
behavior is mandatory." That's a hard hand-off: the behavior is
mandated for an implementation approach that no existing bash tool
reliably provides.

### Proposed Changes

For each of the three checks, choose one:

(a) **Specify the implementation approach.** Name a concrete tool
    (`tree-sitter-bash` via a wrapper, `shfmt`'s parse-tree mode,
    or a bespoke bash-parser script) and commit to its limitations.
    Makes the Makefile target implementable with a named dependency.

(b) **Scope the check to a conservative grep-level heuristic** that
    catches obvious cases and is documented as best-effort. Pair
    with a review-level expectation for the rest.

(c) **Drop the check from MUST to SHOULD** and document the
    limitation.

(d) **Drop all three checks for v1.** Rely on `shellcheck` + review.
    Revisit post-v1 when code size justifies parser tooling.

Without one of these, a faithful implementer cannot build the
mandated enforcement. The R&D cost of writing a reliable bash AST
walker in bash (so it itself conforms to the style doc) is
substantial and out of scope for livespec v1.

---

## Proposal: B4-complexity-thresholds-in-combination-too-strict

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incorrectness** (pragmatic over-constraint). The
three function-level thresholds — CCN ≤ 7, LLOC ≤ 50, positional
args ≤ 4 — are each defensible alone but combine to force
over-decomposition of idiomatic bash patterns.

### Motivation

Concrete cases where the combined thresholds bite without improving
clarity:

- **`parse_options`** with a `case` over 5–6 flags: CCN ≥ 6 before
  any validation branches. Add `-h`, `-V`, missing-arg handling,
  unknown-flag handling → CCN 8–10 easily. Decomposition into a
  one-function-per-flag shape produces 6 tiny functions plus
  bookkeeping, which is LESS readable.
- **`validate_X`** functions with 5 independent field checks (missing
  field, wrong type, wrong range, wrong enum, cross-field
  consistency): CCN 6 for the checks plus 1 for the result aggregation
  = 7–8.
- **`main`** with > 4 phases (arg parse, precondition check, primary
  work, post-step, cleanup): easily > 4 positional args to each
  phase's helper, requiring namerefs-to-assoc-arrays that bash makes
  awkward.

The doc's escape ("Functions that need more MUST accept a
configuration variable (an associative array, a nameref to one, or a
file path)") produces a pattern that is idiomatically *worse* than 5
positional args in bash. Associative arrays are:

- Only referentially passable via nameref (bash 4.3+), and namerefs
  have known sharp edges with `unset` and read-only semantics.
- Not structurally validatable by `shellcheck`.
- Verbose to populate: `declare -A cfg; cfg[a]=1; cfg[b]=2; ...`.

### Proposed Changes

Three directions, pick one:

(a) **Raise the thresholds**: CCN ≤ 10 (McCabe's own bound), args ≤
    6. LLOC ≤ 50 retained. Keeps the gate meaningful without forcing
    over-decomposition.

(b) **Permit per-function waivers** via a `# shellmetrics: ccn-
    waiver-until=<date> justification=<reason>` comment, rejected by
    CI unless the comment is present, and rejected in review if the
    justification is weak. The doc currently says "Per-function
    waivers are NOT permitted" — invert that.

(c) **Keep the thresholds** but document explicitly that `parse_options`
    and `main`-orchestration are exempt, naming the names (the bash
    doc could just list allowed exemptions).

Recommend (a) as the closest to established practice; (b) as the
flexibility-preserving alternative.

---

## Proposal: B5-noclobber-always-on-is-disruptive

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incorrectness** (pragmatic over-constraint).
`set -o noclobber` as a global, unconditional strict-mode flag
inverts ergonomics for normal file-generation patterns without
proportionate benefit.

### Motivation

Skill scripts' normal output flows include:

- Regenerating a JSON findings file: `doctor-static > findings.json`.
- Overwriting a derived-state cache: `jq '...' input > output.json`.
- Emitting a temp-file that may exist from a prior aborted run
  (belt-and-suspenders before a final `mv`).

Under `noclobber`, every one of these requires `>|` instead of `>`.
That's fine in isolation, but it reverses the default: the "common
case" (regeneration) takes the unusual syntax, and the "unusual
case" (fail-if-exists) takes the plain syntax.

The Wooledge `NoClobber` page cited as provenance explicitly
discusses `set -C` as a **defense for scripts that want it**, not
as a universal mandate. Bash style guides from Google, Mozilla, and
GitHub's internal guide do not enable `noclobber` by default.

Combined with the "every redirect decision is an intentional choice"
framing the doc uses elsewhere, the rule pushes authors toward
noisy syntax (`>|` everywhere) that provides safety only when the
author also remembered to NOT use `>|` for the files where overwrite
should fail. The safety story is only as good as the author's
attention — which is no stronger than it was without the rule.

### Proposed Changes

Two directions:

(a) **Drop `noclobber` from the mandatory strict-mode flags.**
    Retain `errexit`, `errtrace`, `pipefail`, `nounset`. Authors who
    want noclobber enable it at the start of the specific function
    or script section where it's warranted. The cost of the opt-in
    is smaller than the cost of `>|`-everywhere.

(b) **Keep `noclobber` but relax the `>|` requirement** by providing
    an `overwrite` helper in the boilerplate:
    ```
    overwrite() {
      local dest="${1}"
      local tmp
      tmp="$(mktemp "${dest}.XXXXXX")"
      cat > "${tmp}" && mv -f "${tmp}" "${dest}"
    }
    ```
    and mandating its use for intentional overwrites. The helper
    gives atomic-replace semantics while preserving `noclobber` for
    accidental-overwrite detection.

Recommend (a). (b) is workable but adds boilerplate surface for a
safety benefit that's available via `>|` already.

---

## Proposal: B6-bash-prefix-env-var-namespace-collision

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incorrectness** (namespace collision risk). The
environment variable names `BASH_XTRACE` and `BASH_VERBOSE` reside
in bash's own reserved `BASH_*` prefix, which is used exclusively
for bash's built-in variables (`BASH_VERSION`, `BASH_SOURCE`,
`BASH_LINENO`, `BASH_COMMAND`, `BASH_ENV`, `BASH_ARGV`, etc.).

### Motivation

Two concrete risks:

1. **Forward-compatibility collision.** If bash adds a built-in
   variable named `BASH_XTRACE` or `BASH_VERBOSE` in a future
   release, the skill's scripts would silently conflict with it —
   either the shell's value leaks into the skill's option-handling
   logic, or the skill's assignment of the variable disrupts the
   shell's own state.

2. **Reader confusion.** An author or reviewer sees `BASH_XTRACE`
   and assumes it's a built-in. The boilerplate's `handle_bash_xtrace`
   function does not disabuse them — it reads like a wrapper around
   a bash builtin.

The doc's stated reason for these names is "Uniformity across scripts
matters more than individual naming preference." That's a valid case
for *some* shared prefix, not for *this specific* prefix.

### Proposed Changes

Rename to a project-specific prefix that signals ownership:

- `BASH_XTRACE` → `LIVESPEC_XTRACE` (or `SKILL_XTRACE` if the
  requirements are meant to apply beyond livespec).
- `BASH_VERBOSE` → `LIVESPEC_VERBOSE`.

Update the boilerplate helper name from `handle_bash_xtrace` to
`handle_xtrace` and the corresponding section's prose. The rule
about "Alternative debug-variable names MUST NOT be introduced"
remains — it just applies to a non-colliding name.

The `LIVESPEC_` prefix fails gracefully if the style doc migrates to
serve other skills (those skills would rename to their own prefix;
no reuse issue).

---

## Proposal: B7-realpath-portability-in-boilerplate-source-pattern

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incorrectness** (portability assumption unstated).
The non-sibling `source` pattern:

```
source "$(realpath "$(dirname "${BASH_SOURCE[0]}")/../scripts/bash-boilerplate.sh")"
```

depends on `realpath`, which is not POSIX and not universally
available.

### Motivation

Availability of `realpath`:

- **Modern Linux** (glibc coreutils ≥ 8.15, ~2012): present.
- **Alpine / musl**: `realpath` is in `busybox`, present.
- **macOS ≤ Big Sur (11.x)**: NOT present in the base system. Users
  install via `brew install coreutils`, which provides `grealpath`,
  not `realpath`. A well-set-up dev environment aliases or symlinks,
  but this is not guaranteed.
- **macOS ≥ Monterey (12.x, 2021)**: `/usr/bin/realpath` is present.
- **FreeBSD / OpenBSD**: `realpath(1)` is present but has different
  flag semantics.

The style doc's own rule says "Required external tool not on `PATH`"
exits `127`. A script that fails to locate its boilerplate exits with
a sourcing error, not `127`, and crashes before the boilerplate's
error-handling is in effect. The failure mode is harsh and the root
cause is obscure.

### Motivation (cont.)

There are portable alternatives that do the same work in pure bash:

```
lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)"
source "${lib_dir}/bash-boilerplate.sh"
```

This uses only bash built-ins (`cd`, `pwd`) and is robust to any
`PATH`.

### Proposed Changes

Replace the `realpath`-based example with the `cd && pwd` pattern,
or add `realpath` to the "MUST be available at runtime" tool list
alongside `jq` (with a presence check in the boilerplate itself).

Recommend the `cd && pwd` replacement: it removes a dependency, and
the boilerplate must be source-able before any tool presence check
can run.

---

## Proposal: B8-pure-library-env-var-ban-over-restricts

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incorrectness** (pragmatic over-constraint). A
"pure" library's functions "MUST NOT read or write environment
variables except those passed explicitly as function arguments."
Common legitimate reads are collateral damage.

### Motivation

Reading environment values that have no side effects and are not
practically injectable into a function signature:

- `IFS` — the function may need to save, modify, restore it for
  read-loops. Reading the current value is part of saving it.
- `LC_ALL`, `LANG` — relevant for `sort`, `grep -i`, etc., which
  the rule already permits as deterministic stdin-to-stdout tools.
- `PATH` — rarely read, but `command -v` internally consults it;
  the rule would ban any `command -v foo` use in a "pure" library.
- Constants exported by the calling script (`readonly DEFAULT_TTL=30`
  shared across sourced libraries) — the rule forces every such
  constant through every function's arg list.

The rule's motivation (testability: pure functions should be
callable without context setup) is sound. But it conflates
"environment-modifying" with "environment-reading." A function that
only reads `$IFS` can be tested by setting `IFS` once in the test's
`setup` block — no harder than passing it as an argument.

### Proposed Changes

Refine the rule:

> A *pure* library's functions:
>
> - MUST NOT **write** to environment variables or unset them.
> - MUST NOT **read** environment variables that are not either (a)
>   passed to the function as an argument, or (b) whose name appears
>   in a short allow-list of read-only framework values: `IFS`,
>   `LC_ALL`, `LANG`, `PATH`, `HOME`, `TMPDIR`. Reads of any other
>   variable are impure.
> - Rest of the rules unchanged.

The allow-list is small, stable, and named; authors can reason about
it; CI can enforce it with a grep over `${NAME}` / `"$NAME"` / `$NAME`
forms.

---

## Proposal: B9-coverage-gate-not-runnable-on-macos

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incompleteness** (developer-ergonomics gap).
`kcov` is Linux-only, so macOS developers cannot verify the
coverage gate locally. The pre-commit configuration cannot include
the coverage check without failing on macOS. The only escape path
is a Linux container, which adds friction.

### Motivation

§"Code coverage" says:

> CI matrices that include non-Linux OSes MAY skip the coverage gate
> on those OSes but MUST run it on at least one Linux configuration
> per pull request.

That's the CI story. For a macOS developer:

- Coverage runs server-side only. First feedback is after push.
- Running `kcov` locally isn't possible (no macOS build).
- `bashcov` (permitted alternative) is Ruby-only and has its own
  maintenance burden.
- Docker-based local runs work but require infrastructure the
  pre-commit framework doesn't provide natively.

The absence of a local-dev path means the tightest feedback loop
for a coverage-sensitive change is a round-trip through CI. For a
project that dogfoods itself, this is a friction-day-one issue.

### Proposed Changes

Either:

(a) **Endorse `bashcov` as a first-class macOS alternative** with the
    same coverage thresholds. The Ruby dependency is a one-time
    install; the payoff is parity across Linux/macOS.

(b) **Ship a `scripts/coverage-in-docker` wrapper** that runs `kcov`
    inside a pinned Linux image, detect-and-use on non-Linux hosts.
    Document that the coverage gate is "run locally via the wrapper
    or via CI; both paths produce comparable numbers."

(c) **Explicitly document** that coverage is a CI-only gate for v1,
    and that macOS developers must rely on the CI run. Accept the
    friction and revisit post-v1.

Recommend (a) or (b); (c) is the status quo and is the worst
developer experience.

---

## Proposal: B10-category-error-dev-time-checks-inside-runtime-bundle

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **malformation** (category error). Scripts under
`.claude-plugin/skills/livespec/scripts/checks/` are described as
"architectural-check scripts invoked by both git pre-commit hooks
and CI" — i.e., they police livespec's OWN bash source code against
the style doc's bespoke rules. They are developer-time artifacts of
the livespec repo. They are NOT runtime behavior for users.

Placing them inside `.claude-plugin/skills/livespec/` ships dev-only
enforcement to every user install for no user benefit and conflates
"runtime assets" with "development assets." It also collides with
the word "checks," which `doctor-static` already uses for its 12
static validations against user SPECIFICATIONs.

### Motivation

Two distinct concerns are being conflated under the word "checks":

| Dimension | `doctor-static`'s internal validations | Scripts formerly under `scripts/checks/` |
|---|---|---|
| **Validates** | User's `SPECIFICATION/`, `.livespec.jsonc`, `history/` state | livespec's own bash source code |
| **Runs when** | Pre/post-step of sub-commands in the user's repo | livespec dev on pre-commit / pre-push / Makefile / CI |
| **Subject** | End user's living spec | livespec maintainer's code |
| **Output** | JSON findings narrated to the user by the LLM | Raw diagnostics to terminal / CI logs |
| **Needed at runtime** | Yes; ships with every install | No; livespec-dev-only |

Current placement ships (b) inside the user-facing bundle.
PROPOSAL.md's skill-layout diagram therefore includes code the user
never touches; the bundle is larger than it needs to be; the
naming collision ("checks" means two different things in two
directories of the same tree) obscures the split.

### Proposed Changes

Split by consumer and relocate.

**Runtime (inside the shipped skill bundle):**

```
.claude-plugin/skills/livespec/scripts/
├── bash-boilerplate.sh
├── dispatch
└── doctor/
    ├── run-static                          # orchestrator executable
    └── static/                             # per-check executables (see B20)
        ├── livespec-jsonc-valid
        ├── template-exists
        └── ...
```

No `checks/` subdirectory in the bundle. The bundle ships only what
a user needs at livespec runtime.

**Dev-time (at the livespec-repo root, outside the bundle):**

```
<livespec-repo-root>/
├── dev-tooling/
│   ├── bash-boilerplate.sh                 # symlink to the bundled one
│   └── enforcement/
│       ├── check-library-headers
│       ├── check-source-graph
│       ├── check-private-calls
│       ├── check-global-writes
│       ├── check-file-length
│       ├── check-sourceable-guards
│       ├── check-filename-blacklist
│       └── check-arg-count
├── Makefile
├── .mise.toml
└── .pre-commit-config.yaml
```

Naming decisions:

- Parent directory: **`dev-tooling/`** (explicitly signals "for
  development, not runtime"; distinct from any `tools/` tree a
  consumer project might have).
- Line-4 subdirectory: **`enforcement/`** (matches the style doc's
  §"Enforcement" framing; avoids the overloaded word "checks"
  entirely; clear intent).
- Each enforcement script: standalone executable (no `.sh`,
  executable bit, sourceable guard), per file `tests/dev-tooling/
  enforcement/check-<name>.bats`.
- `dev-tooling/bash-boilerplate.sh` is a **symlink** to
  `.claude-plugin/skills/livespec/scripts/bash-boilerplate.sh`
  (enforcement is Linux-only; symlinks work everywhere
  enforcement runs).

Updates to PROPOSAL.md:

- §"Skill layout inside the plugin" no longer lists `checks/`.
- New §"Developer tooling layout" (or appendix) documents
  `dev-tooling/` at the repo root, including `Makefile`,
  `.mise.toml`, and `.pre-commit-config.yaml`.
- §"Dependencies" distinguishes runtime dependencies (`jq` + bash)
  from dev-time dependencies (mise-managed tools, per B19).

Updates to the style doc:

- §"Boilerplate requirement" notes that the boilerplate also serves
  `dev-tooling/` scripts via symlink.
- §"Enforcement" section reframed per B18 to describe
  `dev-tooling/enforcement/` as the canonical location; Makefile
  targets named by check.

---

## Proposal: B20-decompose-doctor-static-into-per-check-executables

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incompleteness** / **incorrectness**. PROPOSAL.md's
skill layout shows `doctor-static` as a single executable
implementing all 12 static checks. A single script of that scope
will easily exceed the style doc's complexity and length thresholds
(B4), will be hard to test at per-check granularity, and will be
the largest source of bash code in the skill by far.

Additionally, the current `check_id` naming (`"doctor-06"`) uses
positional numbers that are fragile under insert/delete of checks
and convey nothing about the check's subject.

### Motivation

Decomposing the static phase into one executable per check gives:

- Per-check unit tests (one `.bats` file per check file).
- Natural fit to the style doc's complexity limits: each check fits
  well under any reasonable CCN/LLOC threshold.
- Independent failure isolation; an internal error in one check
  doesn't corrupt another's output.
- Makefile targets per check are available (invoked from pre-commit
  hooks or manually) even though the primary invocation path is
  through the orchestrator called by livespec sub-commands.

Slug-only `check_id` values (e.g., `doctor-out-of-band-edits`)
replace positional numbers:

- Insert/delete of checks is a non-event; no number-stability
  invariant needed.
- Filenames and IDs are self-documenting.
- Deprecated checks disappear cleanly; no gaps in numbering to
  explain.

### Proposed Changes

Restructure doctor's static phase inside the bundle:

```
.claude-plugin/skills/livespec/scripts/
└── doctor/
    ├── run-static                          # orchestrator executable
    └── static/                             # one executable per check
        ├── livespec-jsonc-valid
        ├── template-exists
        ├── template-files-present
        ├── proposed-changes-and-history-dirs
        ├── version-directories-complete
        ├── version-contiguity
        ├── revision-to-proposed-change-pairing
        ├── proposed-change-topic-format
        ├── out-of-band-edits
        ├── bcp14-keyword-wellformedness
        ├── gherkin-blank-line-format
        └── anchor-reference-resolution
```

Per-check contract (PROPOSAL.md and style doc):

- Each check is a standalone executable (no extension, executable
  bit, sourceable guard) sourcing `../../bash-boilerplate.sh`.
- Emits a JSON findings array on stdout (empty if pass; one or more
  findings if fail).
- Exit `0` pass / `3` fail / `1` internal.
- Tested at `tests/scripts/doctor/static/<slug>.bats`.

Orchestrator `run-static`:

- Iterates `scripts/doctor/static/` by glob.
- Runs each check as a subprocess.
- Aggregates per-check JSON findings into one
  `{"findings": [...]}` array on stdout.
- Exit `0` if every child exited `0`; `3` if any exited `3`; `1` if
  any exited `1`.
- Called by livespec sub-commands (pre-step, post-step) and by the
  `doctor` sub-command itself.

JSON finding `check_id` format:

```diff
-{ "check_id": "doctor-06", "status": "fail", "message": "...", "path": "SPECIFICATION/history", "line": null }
+{ "check_id": "doctor-version-contiguity", "status": "fail", "message": "...", "path": "SPECIFICATION/history", "line": null }
```

`check_id` form: `doctor-<slug>` where `<slug>` matches the per-
check script's filename. The `doctor-` prefix namespaces the ID so
future check categories (e.g., from enforcement/, if any ever
surface end-user findings) don't collide.

Rewrite PROPOSAL.md §"Static-phase checks":

- Replace the numbered list with a bulleted list keyed by slug, each
  item naming the slug and describing the check. E.g.:
  - `out-of-band-edits`: diff between committed spec state and
    latest `history/vN/` copies is empty; otherwise auto-backfill
    flow per prior resolution.
- Replace prose references like "doctor check #9" and "check #12"
  with the corresponding slug, e.g., "the `out-of-band-edits`
  check" and "the `anchor-reference-resolution` check".
- Drop the "12 checks" count from DoD item 6; replace with "the full
  doctor static-check suite (listed in §'Static-phase checks')".

---

## Proposal: B11-shellmetrics-reliability-vs-no-waiver-rule

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incorrectness** (tool-dependence risk). The style
doc mandates `shellmetrics` as the single source of truth for CCN
and LLOC with "per-function waivers NOT permitted", while
`shellmetrics` is a niche tool with small maintainer velocity.

### Motivation

`shellmetrics` risks:

- **Reporting variance.** Its CCN algorithm may not match
  intuitive readings for some bash constructs (`&&`/`||` chains in
  conditions, nested `case` arms, brace-group fall-through). A
  function whose perceived CCN is 6 may measure as 8.
- **Upgrade regressions.** Any change to `shellmetrics`'s measurement
  code can silently re-categorize functions from "passing" to
  "failing" with no code change in the skill. The only remedy (no
  waivers permitted) is to refactor.
- **Limited active maintenance.** Single-maintainer bash tool; if it
  goes stale, the skill's entire CCN gate is stranded.

The doc pins the `shellmetrics` version in CI, which helps. But
pinning forever creates its own debt: eventually the pinned version
doesn't install on newer OS images, or `shellcheck`/`shfmt` updates
conflict.

### Proposed Changes

Add a limited escape hatch:

(a) **Permit a `# shellmetrics-disable-next-function: reason="..."`
    comment** that suppresses the CCN/LLOC gate for one function,
    with CI rejecting any such comment that does not include a
    non-empty `reason`. Cap total disables per file at 2; cap total
    across the skill at N (e.g., 5). This gives authors an escape for
    tool-misreport cases without opening a blanket waiver.

(b) **Or**: pin `shellmetrics` AND accept CCN/LLOC manually via a
    pre-committed `complexity-thresholds.csv` committed alongside
    the code. CI checks against the CSV; upgrading `shellmetrics`
    requires re-baselining the CSV. This makes tool drift visible
    and auditable.

Recommend (a). (b) is a richer machinery but heavier.

---

## Proposal: B12-bash-version-floor-breaks-portability-premise

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incorrectness** (core premise violation). The style
doc targets bash 4.4+ under the assumption that "Skill runtime
environments ship bash 5.x" — but the skill's bash scripts execute
on the **end user's** machine (Claude Code's bash tool runs locally,
not in Anthropic's sandbox). On macOS, `/usr/bin/env bash` resolves
to `/bin/bash` version 3.2.57 (Apple ships bash 3.2 for GPLv3
reasons and has done so since 2007 across every macOS release
through Sequoia).

This silently breaks the entire stated premise of choosing bash —
maximum POSIX portability with minimal runtime dependencies — for
every macOS end user who hasn't independently installed bash 4.x+.

### Motivation

Bash 4.x features used or recommended by the current style doc:

- Namerefs (`declare -n` / `local -n`, 4.3+), named as the escape
  for >4-arg functions.
- Associative arrays (`declare -A`, 4.0+), named as the
  configuration-variable escape.
- The `nounset` + empty-array interaction fix (4.4+), cited as the
  reason for the 4.4 floor specifically.

Each of these has a 3.2-compatible alternative:

- Namerefs → return via stdout (already the mandated primary pattern).
- Associative arrays → key=value lines in a temp file or heredoc;
  positional args; record-per-line scalar strings.
- `nounset` empty-array interaction → `"${arr[@]-}"` (empty-default
  expansion) works on bash 3.2.

Maintaining two bash standards (runtime 3.2 + dev-tooling 4.4) is
rejected as a maintenance tax. A single standard targeting 3.2 is
uniform and preserves the portability premise; it costs authors
nothing essential because no feature dropped is load-bearing.

Execution environment (pinned via `mise`, per B19) is set to
**bash 3.2.57 exactly**. Developers and CI run the same bash version
macOS end users run, catching any accidental 4.x leakage at
authoring time.

### Proposed Changes

1. Drop the 4.4 floor entirely. Change the style doc §"Interpreter
   and shebang" floor statement to:

   > Scripts MUST target bash 3.2.57 or newer. Bash 3.2 is the
   > baseline because macOS ships bash 3.2.57 at `/bin/bash` on
   > every supported release; the skill's scripts execute on the
   > end user's machine, and portability to stock macOS is a core
   > premise of choosing bash.

   Delete the sentence *"Skill runtime environments ship bash 5.x;
   targeting 4.4 is a safety floor"* — the premise is wrong.

2. Remove recommendations and escapes that rely on 4.x features:
   - Delete "nameref parameter declared with `declare -n`" from
     §"No global variable writes from functions".
   - Delete "associative array, a nameref to one" from the §"Function
     argument count" escape language.
   - Delete the §"Required strict mode" line citing
     [BashFAQ/112](http://mywiki.wooledge.org/BashFAQ/112) as the
     4.4-floor justification.

3. Mandate the `"${arr[@]-}"` (empty-default) expansion pattern for
   possibly-empty array expansions under `nounset`:

   > When expanding a possibly-empty array under `nounset`, scripts
   > MUST use `"${arr[@]-}"` (empty-default) rather than
   > `"${arr[@]}"`. Bash 3.2 errors on the latter when the array is
   > empty; the empty-default form is portable from 3.2 onward.

4. Add a bash-version check to `bash-boilerplate.sh`:

   ```
   if (( BASH_VERSINFO[0] < 3 )) || { (( BASH_VERSINFO[0] == 3 )) && (( BASH_VERSINFO[1] < 2 )); }; then
     printf 'livespec requires bash >= 3.2. Current: %s\n' "${BASH_VERSION}" >&2
     printf 'Install via your distro'\''s package manager, `brew install bash`, or `mise install`.\n' >&2
     exit 127
   fi
   ```

   Placed after `set -e` and before any bash-3.2-incompatible
   construct. Exit `127` matches the "missing required tool" code.

5. Add an optional bash-3.2 smoke-test target to the enforcement
   suite (not blocking in v1): a dockerized bash 3.2.57 runs the
   bundle's runtime scripts against a fixture, to catch accidental
   4.x-isms. Captured as a post-v1 follow-up if not in scope for v1.

Single, uniform bash standard. No two-tier rules. No silent user
breakage.

---

## Proposal: B13-test-file-naming-duality-unclear

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **ambiguity**. Tests for the skill follow two naming
conventions without a clear boundary rule: per-script at
`tests/scripts/<name>.bats` (style doc) and per-specification-file
at `tests/test_<spec-file>.bats` (PROPOSAL.md). When a test
concerns both (script's implementation of a spec rule), placement is
unclear.

### Motivation

- Style doc: "Test files MUST mirror script names:
  `scripts/validate-spec` is tested by
  `tests/scripts/validate-spec.bats`."
- PROPOSAL.md: "Tests MUST be split into separate files per
  specification file: `test_spec.bats`, `test_contracts.bats`,
  `test_constraints.bats`, `test_scenarios.bats`."

Consider a test that verifies `scripts/doctor-static` enforces the
Gherkin blank-line rule from `scenarios.md`. Does the test go in
`tests/scripts/doctor-static.bats` (per-script) or
`tests/test_scenarios.bats` (per-spec)?

The `tests/heading-coverage.json` meta-registry adds another wrinkle:
it maps spec headings to test identifiers. If the same test is
referenced from both "doctor-static" and "scenarios", which ID gets
the reference?

### Proposed Changes

State the boundary in both documents:

> Per-script test files at `tests/scripts/<name>.bats` exercise the
> **script's contract** (exit codes, output schema, error handling,
> input validation). Per-spec-file tests at `tests/test_<spec-
> file>.bats` exercise **rules stated in that specification file**,
> invoking whatever script(s) implement the rule. A rule-level test
> that calls `doctor-static` internally is per-spec-file, not
> per-script.
>
> The `heading-coverage.json` registry references per-spec-file
> tests by heading; per-script tests are not required to appear in
> the registry.

Adjust the `tests/scripts/` tree in PROPOSAL.md §"Testing approach"
to mirror any nested script directories (see B14).

---

## Proposal: B14-tests-scripts-does-not-mirror-scripts-checks

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness**. PROPOSAL.md's `tests/` skeleton
tree shows a flat `tests/scripts/` containing only `dispatch.bats`
and `doctor-static.bats`. The skill's `scripts/` has a `checks/`
subdirectory; the test tree does not show its mirror.

### Motivation

The "mirror script names" rule combined with the `scripts/checks/`
subdir implies tests at `tests/scripts/checks/check-library-
headers.bats`, etc. An implementer scanning PROPOSAL.md's testing
tree sees no such structure and may place the tests flat
(`tests/scripts/check-library-headers.bats`) or in a different
location entirely.

### Proposed Changes

Update the `tests/` skeleton in PROPOSAL.md §"Testing approach" to
show the mirroring:

```
tests/
├── CLAUDE.md
├── heading-coverage.json
├── fixtures/
├── scripts/
│   ├── dispatch.bats
│   ├── doctor-static.bats
│   └── checks/                        # mirrors scripts/checks/
│       └── <check-name>.bats
└── test_*.bats
```

Or explicitly state "the `tests/scripts/` tree mirrors the skill's
`scripts/` tree one-to-one, including subdirectories" to avoid
tree churn on later additions.

---

## Proposal: B15-variadic-function-mechanical-definition-missing

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **ambiguity**. §"Function argument count" requires
variadic functions to be annotated with `# variadic` and exempts
them from the 4-arg limit, but does not define what "variadic"
means.

### Motivation

Candidate definitions:

1. A function whose body uses `"$@"`, `$@`, `"$*"`, or `$*` at all.
2. A function that uses `shift` to consume N named args and treats
   the rest as a variable-count tail.
3. A function that has no `local arg1="${1}" ... local argN="${N}"`
   declarations.
4. A function that the author declares variadic via the annotation,
   with CI checking nothing beyond the annotation's presence.

Each produces a different set of exempt functions. A `main "$@"`
body uses `"$@"` (matches 1) but should not be annotated variadic.

The doc says CI "counts the highest positional index used" — but
variadic functions may use no positional index at all, relying on
`"$@"`. How does CI detect the "highest index" exempt-from-limit
violation for a variadic function?

### Proposed Changes

Define mechanically:

> A function is **variadic** if it reads `"$@"`, `"${*}"`, or
> iterates `"$@"` at any point in its body. Variadic functions MUST
> be annotated with a `# variadic` comment immediately preceding the
> function definition. CI verifies:
>
> - Any function with a `# variadic` annotation reads `"$@"` or
>   `"${*}"` in its body; absence is a style violation.
> - Any function that reads `"$@"` or `"${*}"` in its body has the
>   annotation; absence is a style violation.
> - `main` is exempt from the annotation requirement.

Or: drop the variadic exemption entirely and require variadic
functions to use the associative-array/nameref escape, aligning with
the ≤ 4 positional-arg rule.

---

## Proposal: B16-library-header-format-not-parseable

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **ambiguity**. Library headers carry three required
pieces of information and a fourth (the `# purity:` directive), all
in prose form. CI is required to verify these headers, but the
parseable form is not specified.

### Motivation

§"Single responsibility per library":

> Every library MUST begin with a header comment block stating
> (a) its single concern in one sentence, (b) the prefix used by
> its exported functions, and (c) the other libraries it sources.

§"The pure / impure distinction":

> The classification MUST appear as a `# purity: pure` or
> `# purity: impure` directive in the library's header comment block.

§"No kitchen-sink imports":

> CI MUST verify that every `source` statement in a library
> corresponds to an entry in that list, and that every listed
> library is actually sourced.

An implementer cannot write a compliance script against "its single
concern in one sentence" — there is no grammar. CI implementations
will diverge: some require a specific comment prefix, others match
free-form patterns, others give up and only check the `# purity:`
directive.

### Proposed Changes

Specify a structured header format:

```
#!/bin/... or (libraries have no shebang; start at the header)
# concern: validate BCP 14 keyword usage in prose.
# prefix: bcp14
# purity: pure
# sources:
#   - ./parse-markdown.sh
#   - ./keyword-registry.sh
```

Rules:

- The header MUST appear in the first 20 lines of the file, before
  any function definition.
- Every directive (`concern`, `prefix`, `purity`, `sources`) is a
  line starting with `# <key>:`.
- `sources` takes a multi-line list; each source is a `#   - <path>`
  line, path relative to the library file.
- CI reads the four directives, cross-checks `sources` against
  `source` statements in the file body, and enforces presence.

The format is grep-friendly, trivially parseable, and self-
documenting. It makes the CI check tractable and consistent.

---

## Proposal: B17-interactivity-check-absolute-ban-over-strict

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **incorrectness** (pragmatic over-constraint). §"Non-
interactive execution" forbids ALL interactivity checks (`[[ -t 0 ]]`,
`[[ -t 1 ]]`, `[[ -p /dev/stdin ]]`, `tty -s`). That's broader than
the motivation warrants.

### Motivation

The rule's motivation: "These checks always resolve to the non-
interactive branch in the skill runtime, so the opposite branch is
unreachable dead code." That's true if the checks are used to gate
into an interactive-prompt path. But `[[ -t 0 ]]` and `[[ -p
/dev/stdin ]]` also differentiate:

- **stdin-pipe**: data is being piped in (`cat file | my-check`).
- **stdin-file**: `my-check` was invoked without piped data, perhaps
  taking a path argument instead.

Both are non-interactive. A script that accepts `my-check input.json`
OR `cat input.json | my-check` legitimately uses `[[ -t 0 ]]` to
pick between the path-arg path and the stdin-read path. No
interactivity is involved.

The current rule blocks this pattern. The escape — reading only
from positional args — forces callers to write the file first even
when they have the content as an in-memory string in their shell.

### Proposed Changes

Refine the ban to its motivating case:

> Scripts MUST NOT branch on interactivity checks **to reach an
> interactive-prompt path**. The checks `[[ -t 0 ]]` and `[[ -p
> /dev/stdin ]]` MAY be used to differentiate stdin-pipe from
> stdin-redirect, so long as neither branch reads from a terminal
> and neither branch prompts the user. `[[ -t 1 ]]` and `tty -s`
> remain forbidden (no legitimate use in the skill runtime).

This preserves the invariant that skill scripts never prompt the
user without blocking a real stdin-routing pattern.

---

## Proposal: B18-enforcement-section-framed-as-ci-specific

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md

### Summary

Failure mode: **malformation** (framing mismatch). The style doc's
enforcement architecture is titled and framed as
§"Enforcement via git hooks and CI", treating CI as a co-equal
invocation surface alongside git hooks. In practice the checks are
invocation-surface-agnostic — a single enforcement suite that any
caller (pre-commit, pre-push, CI, developer at the shell) invokes
through a common handle.

### Motivation

Current doc structure splits enforcement responsibilities along
invocation surfaces:

- §"Pre-commit hooks" lists the checks the hook runs.
- §"Continuous integration" restates many of the same checks with
  "CI MUST run X" phrasing plus a few CI-only duties (coverage gate,
  full-tree instead of staged-files).

This split produces two problems:

1. **Duplicate mandates.** The same check (e.g., `shellcheck -x`)
   appears under both subsections. If one list drifts, the checks
   disagree across invocation surfaces.
2. **False CI-centrism.** A reader concludes the checks are "CI
   things," when in fact they are enforcement rules the suite
   carries around. Running the checks manually at the shell has no
   first-class documentation path.

The actual contract: each check is a Makefile target (or
equivalent). Pre-commit, pre-push, CI, and manual invocation are
*consumers* of the same target set, not primary owners of the
check. The platform constraint is "Linux"; within that, invocation
surface is arbitrary.

### Proposed Changes

Restructure §"Enforcement via git hooks and CI" into:

1. **§"Enforcement suite"** — the canonical list of checks
   (static analysis, complexity, coverage, architectural,
   sourceable-guard). Each check is expressed as a Makefile target
   (e.g., `make check-shellcheck`, `make check-complexity`,
   `make check-coverage`). The check list is stated once.

2. **§"Invocation surfaces"** — a short subsection per surface
   stating which Makefile targets that surface runs, not restating
   the checks:

   - **Pre-commit** (local, staged files): fast checks (`make
     check-staged-fast` or a named target) to give quick feedback.
   - **Pre-push** (local, whole tree): the full suite or a near-full
     subset.
   - **CI** (remote, whole tree on every PR/merge): full suite
     including coverage.
   - **Manual** (developer at the shell): `make check`, `make
     check-<name>`; same targets used by the hooks.

3. **Platform statement**: "The enforcement suite is Linux-only.
   Developers on macOS or other non-Linux hosts run the suite via
   Linux container, via CI, or via pre-push on a Linux CI runner.
   No cross-platform parity is attempted."

This reframing:

- Eliminates duplicate mandates (each check is stated once).
- Makes manual invocation a first-class concern.
- Lets pre-commit/pre-push invocations evolve without touching the
  check definitions.
- Simplifies documentation of new checks (add the Makefile target;
  hooks pick it up).

The Linux-only statement replaces the current doc's per-check
handling of macOS/non-Linux gaps (currently scattered across the
coverage section). Developers on non-Linux hosts have one clear
answer: use the Linux runner.

---

## Proposal: B19-mise-for-tool-dependency-and-version-management

### Target specification files

- brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Summary

Failure mode: **incompleteness** (tool-management mechanism not
named). The style doc requires several external tools (shellcheck,
shfmt, shellharden, shellmetrics, kcov, bats-core, bats-assert,
bats-support, jq) and — pending B3's resolution — may add
tree-sitter-bash or similar. Each tool's pinning is mandated in
prose ("MUST be pinned in CI"), but no single pinning mechanism is
named. The result is scattered per-tool pin language and no unified
install surface.

### Motivation

Problems with the current scatter-pinned approach:

- Each tool's pin is described in its own subsection ("The
  `shellmetrics` version MUST be pinned in CI", "The `kcov` version
  MUST be pinned", etc.), producing duplication.
- Pre-commit / pre-push / CI / manual invocation each need the
  tools installed. Without a unified manager, each invocation
  surface grows a bespoke install story.
- Developer-parity with CI is hard to verify: a developer may run
  a locally-available shellcheck version that differs from CI,
  producing green-locally / red-on-CI surprises.
- Upgrading a tool touches multiple docs and CI configs.

`mise` (jdx/mise, formerly rtx) is a polyglot tool-dependency
manager that solves these problems with one committed `.mise.toml`:

```toml
[tools]
bash = "3.2.57"              # pinned to the floor (per B12) so dev/CI match macOS end users
shellcheck = "0.10.0"
shfmt = "3.8.0"
shellharden = "4.3.1"
shellmetrics = "0.5.1"
kcov = "43"
bats = "1.11.0"
jq = "1.7.1"
tree-sitter = "0.22.6"       # per B3's (a) resolution
```

A developer runs `mise install` once; thereafter `mise`-shimmed
tools are on `PATH` at the pinned versions. Developers and CI use
identical versions, including bash itself pinned to the minimum
supported floor so accidental 4.x-only constructs fail at dev time,
not silently on end-user macOS.

### Proposed Changes

Add a new subsection to the style doc titled
§"Tool dependency management":

> External tools required by the enforcement suite (shellcheck,
> shfmt, shellharden, shellmetrics, kcov, bats-core, bats-assert,
> bats-support, jq, and any additional tool named in this document)
> MUST be pinned via `mise` in a committed `.mise.toml` at the
> livespec repository root. `mise install` MUST produce a
> ready-to-run environment for the full enforcement suite on Linux.
>
> Scatter-pinned per-tool language elsewhere in this document
> collapses into this mandate: where a section formerly said "the
> <tool> version MUST be pinned in CI," the mandate is that the tool
> is pinned via `mise`.
>
> Tools `mise` does not package natively (plugin- or helper-managed)
> are installed through `mise`'s plugin mechanism or through a small
> Makefile target invoked by the boilerplate; in either case the
> pinned version lives in `.mise.toml` or adjacent config.
>
> The enforcement suite's Makefile targets assume `mise`-managed
> tools are on `PATH`. A `make check-tools` target (or similar)
> verifies every required tool is present at the pinned version.

Update PROPOSAL.md:

- Add `.mise.toml` to the skill-repo root's documented files.
- Update §"Dependencies" to note that runtime tools (jq) plus every
  enforcement-suite tool are `mise`-pinned in the livespec repo;
  user projects consuming the skill have their own tool stories.
  livespec skill scripts invoked in a user's project depend only on
  `jq` + bash at runtime (per the existing rule); `mise` is a
  developer/CI concern for livespec itself, not a user runtime
  requirement.

Delete per-tool "MUST be pinned in CI" language from the style
doc's scattered sections (§"Cyclomatic complexity", §"Code
coverage", etc.), replacing each with a cross-reference to
§"Tool dependency management".

---

## Summary / metadata

| Severity | Count |
|---|---|
| Major | 5 |
| Significant | 8 |
| Smaller | 7 |

The focus throughout is pragmatism: does the rule survive real-
world authoring, real-world tool limitations, and real-world
dev-environment diversity? Items where the rule conflicts with
PROPOSAL.md directly (B1 partial, B10, B14) are surfaced alongside
the intra-doc concerns because the two documents ship together and
bind the same implementer.
