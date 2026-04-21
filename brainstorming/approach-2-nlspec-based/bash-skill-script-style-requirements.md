# Bash skill script style requirements

This section constrains how bash scripts bundled with a Claude Code
skill governed by this specification are authored, tested, and
enforced. It applies to executable scripts and to sourced libraries
written in bash; it does not apply to scripts written in other
languages (Python, Node, etc.), which are out of scope for this
section.

Scripts governed by this section are invoked by Claude as tools via
the bash tool. They execute **non-interactively**: no TTY is attached
to any standard stream, no user prompt is possible, and stdin is not
a terminal. Interactive-shell affordances are therefore forbidden
throughout this section, not merely discouraged.

The normative source of truth for bash practice in this section is
Greg Wooledge's wiki at
[mywiki.wooledge.org](http://mywiki.wooledge.org/) — in particular
the `BashFAQ`, `BashPitfalls`, `BashGuide`, `Quotes`, `NoClobber`,
and `ProcessManagement` pages. Where a rule below cites a specific
Wooledge page, that citation is authoritative; where a rule below is
silent on a question Wooledge covers, the Wooledge default applies.
No other bash style guide is normative for this section.

This section uses BCP 14 / RFC 2119 / RFC 8174 keywords (`MUST`,
`MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`,
`OPTIONAL`) for normative requirements.

---

## Scope

* These requirements apply to every bash script bundled with the
  skill, including but not limited to scripts referenced from
  `SKILL.md`, scripts invoked by the skill's sub-commands, and the
  shared `bash-boilerplate.sh` library itself.
* The `doctor` sub-command's static phase, when implemented in bash,
  MUST comply with this section in full. When implemented in another
  language, this section does not apply; a parallel section for that
  language is out of scope for v1.
* Scripts that are examples, fixtures, or test inputs under `tests/`
  MUST comply unless the test explicitly exercises a non-conforming
  input, in which case the non-conformance MUST be declared in a
  comment at the top of the fixture file.

---

## Non-interactive execution

Skill scripts run under the Claude bash tool in a code execution
environment. The following invariants hold, and the following
affordances are forbidden because they cannot function in that
context:

* Scripts MUST NOT read from a terminal. `read` without redirected
  input, `read -p`, and any prompt-and-wait construct are forbidden.
* Scripts MUST NOT call `stty` or otherwise manipulate terminal
  modes.
* Scripts MUST NOT open `/dev/tty`. A script that needs a
  human-confirmation step MUST instead fail with an actionable
  message and exit code `3` (precondition failed), leaving the
  decision to the caller.
* Scripts MUST NOT branch on interactivity checks (`[[ -t 0 ]]`,
  `[[ -t 1 ]]`, `[[ -p /dev/stdin ]]`, `tty -s`). These checks
  always resolve to the non-interactive branch in the skill runtime,
  so the opposite branch is unreachable dead code.
* Scripts MUST NOT rely on job control or on signal semantics that
  apply only to interactive shells (e.g., `SIGTSTP` beyond the
  default handler).
* All configuration and input MUST arrive through one of: positional
  arguments, optional flags, environment variables, or files named
  by the above. No other input channel is valid.

---

## Interpreter and shebang

* Every bash script MUST begin with `#!/usr/bin/env bash`. The
  `/usr/bin/env` form is required because it locates `bash` via
  `PATH`, accommodating systems where bash is installed outside
  `/bin` (e.g., Homebrew on macOS installs a modern bash at
  `/opt/homebrew/bin/bash` or `/usr/local/bin/bash`).
* Scripts MUST NOT use `#!/bin/sh`, `#!/bin/bash`, or any other
  interpreter path.
* Scripts MUST NOT be written to be POSIX-sh-compatible. Bashisms
  are permitted and expected.
* Scripts MUST target bash 4.4 or newer. Bash 4.4 (released 2016) is
  the baseline because it fixed several `nounset` pitfalls with
  empty arrays and `"$@"`
  ([BashFAQ/112](http://mywiki.wooledge.org/BashFAQ/112)). Skill
  runtime environments ship bash 5.x; targeting 4.4 is a safety
  floor.

---

## Required strict mode

Every runnable bash script MUST source the shared
`bash-boilerplate.sh` (see "Boilerplate requirement" below). The
boilerplate MUST set the following options unconditionally, in this
order:

* `set -o errexit` — exit immediately on non-zero exit of any simple
  command not otherwise tested. Authors MUST treat `errexit` as a
  safety net, not an error-handling strategy:
  [BashFAQ/105](http://mywiki.wooledge.org/BashFAQ/105) enumerates
  the cases where `errexit` does not fire as expected (inside
  functions called from `if`/`&&`/`||`, within pipelines without
  `pipefail`, and others). Every command whose non-zero exit is
  meaningful MUST be explicitly tested, regardless of `errexit`.
* `set -o errtrace` — ERR traps MUST be inherited by subshells and
  functions.
* `set -o noclobber` — `>` MUST NOT overwrite an existing file
  silently ([NoClobber](http://mywiki.wooledge.org/NoClobber)).
  Authors who need overwrite semantics MUST use `>|` explicitly.
* `set -o pipefail` — a pipeline's exit status MUST be the rightmost
  non-zero exit of any of its commands.
* `set -o nounset` — unbound variable references MUST cause
  immediate exit. The option is enabled **unconditionally** because
  skill scripts execute non-interactively. Before enabling
  `nounset`, the boilerplate MUST pre-define any environment-owned
  variables the surrounding shell might rely on but leave unset —
  specifically `: "${PROMPT_COMMAND:=}"` — so that `nounset` does
  not trip on variables the shell itself references.

The script MUST set `set -e` on its own first line, before sourcing
the boilerplate, so that a failure during sourcing itself still
aborts the script.

Commands whose non-zero exit is expected and meaningful MUST be
handled explicitly, via `|| true`, a captured exit code (`rc=$?`),
or an `if`/`&&`/`||` construct. Relying on `errexit` to silently
skip such commands is forbidden.

---

## Exit traps and error handling

* The boilerplate MUST install `trap onexit HUP INT QUIT TERM ERR`.
  Consumers MUST NOT replace this trap; they MAY extend it by
  defining an `onexit_hook` function, which the boilerplate-provided
  `onexit` function MUST invoke when present.
* On any non-zero exit, `onexit` MUST emit a diagnostic line that
  names the script (`$0`), the failing source file
  (`${BASH_SOURCE[0]}`), the line number (`${LINENO}`), and the
  numeric exit status. The exit status MUST be preserved and
  re-raised.
* Scripts that need to temporarily suspend error-checking MUST do so
  only via the boilerplate's `disable_error_checking` and
  `enable_error_checking` helpers, paired within the same function.
  Bare `set +e` or `trap - ERR` outside these helpers is forbidden
  because it loses the matching re-enable.
* Temp-file cleanup traps MUST use `EXIT`
  (`trap 'cleanup' EXIT`) and MUST compose with `onexit` rather
  than replace it. `EXIT` fires after signal traps; the two traps
  coexist without interference.
* `eval` is forbidden
  ([BashFAQ/048](http://mywiki.wooledge.org/BashFAQ/048)). Scripts
  that appear to need `eval` almost always need an array, a
  function, or a different data model instead.

---

## Functions and `main`

* All executable logic MUST live inside functions. The only code at
  the top level of a runnable script is: the shebang, the initial
  `set -e`, the sourcing of the boilerplate, function definitions,
  optional `readonly` constant declarations, and the `main`
  invocation.
* Every runnable script MUST define a `main` function and invoke it
  as `main "$@"` on the final line. The `set +o nounset` /
  `main "$@"` / `set -o nounset` wrap that appears in some older
  bash idioms is forbidden; it was a workaround for pre-4.4
  empty-`"$@"` behavior that no longer applies.
* Function definitions MUST use the `name() { ... }` form. The
  `function` keyword (both `function name { }` and
  `function name() { }`) is forbidden. The keyword form is
  bash-specific, provides no functional benefit in a bash-only
  codebase, and is what `shfmt -fn=0` (the default) normalizes
  away.
* Functions longer than two lines MUST declare their positional
  arguments by name at the top of the function body:
  ```
  my_func() {
    local arg1="${1}" arg2="${2}"
    ...
  }
  ```
  Variadic functions are exempt; they MUST use `shift` with
  descriptive local-variable assignments.
* Functions MUST use `local` for any variable they set, unless the
  function is deliberately setting an outer-scope variable, in
  which case a comment MUST state that intent.
* Variable names MUST be lowercase with underscores, except for
  variables exported to the process environment, which MUST be
  uppercase with underscores.
* Constants MUST be declared with `readonly` after assignment, or
  with `declare -r`, so that accidental reassignment fails loudly.

---

## Quoting

* Every parameter expansion and command substitution MUST be
  double-quoted
  ([Quotes](http://mywiki.wooledge.org/Quotes),
  [BashPitfalls #2](http://mywiki.wooledge.org/BashPitfalls#cp_.24file_.24target)),
  with the following narrow exceptions:
  * Inside `[[ ... ]]` on the right-hand side of `=~`, quotes
    change the semantics and SHOULD be omitted.
  * Inside arithmetic contexts (`(( ... ))`, `$(( ... ))`), quoting
    is unnecessary and SHOULD be omitted.
  * Explicit word-splitting of a known-safe value MAY be unquoted,
    but the author MUST add a
    `# shellcheck disable=SC2086` comment with a one-line
    justification on the same line or the line above.
* `"$@"` MUST be used when forwarding all positional arguments.
  Unquoted `$@` and `"$*"` are forbidden for forwarding
  ([BashPitfalls #1](http://mywiki.wooledge.org/BashPitfalls#for_f_in_.24.28ls_.2A.mp3.29)).
* `${array[@]}` MUST be quoted as `"${array[@]}"` when expanded.
  Scripts MUST NOT use `${array}` or `$array` when referring to an
  array; both expand to the first element only and are almost
  always a bug
  ([BashFAQ/005](http://mywiki.wooledge.org/BashFAQ/005)).
* `${BASH_SOURCE}` MUST be written as `${BASH_SOURCE[0]}`. The
  un-indexed form expands to the first element but looks like a
  scalar, which shellcheck flags as SC2128 and which confuses
  readers. The same applies to any other array variable treated
  as a scalar.
* Backticks are forbidden. Command substitution MUST use
  `$( ... )`.
* Scripts MUST use `printf` for any output that is not a
  fixed-literal string, because `echo`'s handling of backslashes
  and leading `-` flags varies across bash versions. Fixed-literal
  strings MAY use `echo`.
* Format strings passed to `printf` MUST be literals, not variables
  (shellcheck SC2059). Dynamic content belongs in `printf`'s
  arguments, not its format.

---

## Arrays and list handling

* Lists of items MUST be represented as bash arrays, never as
  whitespace- or newline-separated scalar strings
  ([BashFAQ/050](http://mywiki.wooledge.org/BashFAQ/050)).
* Scripts MUST NOT parse the output of `ls`
  ([BashPitfalls #1](http://mywiki.wooledge.org/BashPitfalls#for_f_in_.24.28ls_.2A.mp3.29),
  [ParsingLs](http://mywiki.wooledge.org/ParsingLs)). File
  enumeration MUST use globs (`for f in *.md`) or
  `find ... -print0` piped to `while IFS= read -r -d '' f`.
* Scripts MUST NOT build command strings as scalar variables and
  pass them through word-splitting. They MUST use arrays:
  `cmd=(foo --bar "$baz"); "${cmd[@]}"`.
* Scripts MUST handle filenames containing spaces, newlines, and
  leading dashes. Filenames with leading dashes MUST be passed with
  `--` separators or with a `./` prefix where the tool does not
  support `--`.

---

## Reading input

* All `read` invocations MUST use `-r` to preserve backslashes
  ([BashPitfalls #14](http://mywiki.wooledge.org/BashPitfalls#while_read_LINE_do_.....)).
  `read` without `-r` is forbidden.
* Reading a file line-by-line MUST use
  `while IFS= read -r line; do ... done < "$file"`, not
  `for line in $(cat "$file")`.
* Reading from command output MUST use process substitution
  (`while ...; do ...; done < <(cmd)`) when variable mutations
  inside the loop need to persist outside it; a pipeline forms a
  subshell and the mutations are lost
  ([BashFAQ/024](http://mywiki.wooledge.org/BashFAQ/024)).

---

## Tests and conditionals

* Conditional tests MUST use `[[ ... ]]`. The `[` and `test`
  built-ins are forbidden
  ([BashFAQ/031](http://mywiki.wooledge.org/BashFAQ/031)).
* Arithmetic MUST use `(( ... ))` or `$(( ... ))`. The `$[ ... ]`
  form is forbidden.
* Scripts SHOULD prefer exit-code testing (`if cmd; then`) over
  output-substring testing where the command provides a reliable
  exit code.

---

## I/O streams

* Errors, warnings, and diagnostics MUST go to stderr:
  `printf '...' >&2`. Emitting diagnostic output on stdout is
  forbidden.
* Anything the caller might parse (structured data, lists, file
  paths) MUST go to stdout.
* Status and progress messages MUST go to stderr so they do not
  contaminate stdout capture.

---

## Script interface

Because skill scripts are invoked by Claude (not humans) through a
contract documented in `SKILL.md`, the interface MUST be minimal
and predictable. This is a deliberate departure from the flag-heavy
patterns common in human-facing scripts.

* Scripts MUST accept their primary inputs as positional arguments,
  environment variables, or both. Positional arguments SHOULD be
  used for required inputs; environment variables SHOULD be used
  for optional configuration.
* Flag parsing is OPTIONAL. Scripts that accept flags MUST
  implement parsing inside a dedicated function (e.g.,
  `parse_options`) using an explicit `case` over `"${1}"`, with a
  separate `print_usage_and_exit` function that writes usage to
  stdout and a `print_error_and_exit` function that writes errors
  to stderr. Ad-hoc flag parsing scattered through `main` is
  forbidden.
* If a script accepts flags, it SHOULD support `-h`/`--help` that
  prints the usage text. `-V`/`--version` is OPTIONAL.
* A `--debug` flag is NOT required. Debug mode MUST be controlled
  exclusively by the `BASH_XTRACE` and `BASH_VERBOSE` environment
  variables (see "Debug and verbose affordances"). Scripts MAY add
  a `--debug` flag as a human-ergonomics convenience, but it MUST
  act by setting `BASH_XTRACE=true` internally and invoking the
  boilerplate's `handle_bash_xtrace` function; it MUST NOT
  introduce a parallel mechanism.
* Scripts MUST NOT prompt the user for any input. Missing required
  input MUST produce an error message, a hint at the correct
  invocation, and exit code `2`.

---

## Diagnostic output for AI agent consumption

Because bash-script output is the only channel through which the
script's behavior reaches Claude's context, diagnostic quality is a
first-class concern, not an afterthought.

* On any failure, the script MUST emit a message that names the
  failing operation, the inputs that triggered it, and the
  remediation the caller is expected to take. A generic `errexit`
  abort with no message is forbidden; the `onexit` trap's
  line-and-status output is a floor, not a ceiling.
* When a script validates input and an expected field, file, or
  value is missing, the error message MUST enumerate what WAS
  present. Example: "Field `signature_date` not found. Available
  fields: `customer_name`, `order_total`, `signature_date_signed`."
  A message of the form "validation failed" without enumeration is
  forbidden.
* Every configuration constant (timeout, retry count, path default,
  threshold) MUST be accompanied by a comment stating why that
  specific value was chosen. "Voodoo constants" — values without
  justification — are forbidden. If the author does not know the
  right value, the script MUST NOT hardcode one; it MUST accept
  the value as a flag or environment variable with a documented
  default.
* Success output SHOULD be terse. Failure output SHOULD be verbose
  and structured. The asymmetry is intentional: successful
  invocations consume Claude's context window; failing ones need
  enough information for Claude to repair the input or escalate.
* Scripts MUST NOT log progress on every iteration of a long loop
  by default. Verbose progress MUST be gated on
  `BASH_VERBOSE=true`.

---

## Temporary files and cleanup

* Temporary files and directories MUST be created with `mktemp`
  ([BashFAQ/062](http://mywiki.wooledge.org/BashFAQ/062)).
  Hardcoded paths under `/tmp/` are forbidden.
* Every script that creates a temporary file or directory MUST
  register a cleanup trap on `EXIT` that removes it:
  `trap 'rm -rf "${tmp}"' EXIT`. This trap composes with `onexit`
  without conflict.
* Temporary files containing sensitive data SHOULD be created
  inside a fresh `mktemp -d` so that the containing directory's
  default mode restricts access.

---

## Debug and verbose affordances

The boilerplate exposes two environment-variable switches and no
other debug-activation mechanism:

* `BASH_XTRACE=true` MUST enable `set -o xtrace` and install a
  `PS4` that expands `${BASH_SOURCE[0]}`, `${LINENO}`, and
  `${FUNCNAME[0]}` at **trace-emission time**, so that each traced
  command reports its own source, line, and function. `PS4` MUST
  therefore be set with single quotes (or with escaped `\$`) to
  defer expansion; setting `PS4` with double quotes that expand
  these variables once at assignment time is a latent bug and is
  forbidden.
* `BASH_VERBOSE=true` MUST enable `set -o verbose`.
* Alternative debug-variable names (`DEBUG`, `TRACE`, `XDEBUG`, or
  bespoke per-script variables) MUST NOT be introduced. Uniformity
  across scripts matters more than individual naming preference,
  because Claude and humans alike benefit from a single memorized
  switch.

---

## File naming and invocation

* Executable scripts MUST NOT carry a `.sh` or `.bash` file
  extension. The extension is reserved for files intended to be
  sourced.
* Sourced libraries MUST carry a `.sh` or `.bash` extension.
* Executable scripts MUST have the executable bit set on every file
  committed to the repository. Git hooks MUST verify this (see
  "Enforcement" below).
* Script filenames MUST use kebab-case (`validate-spec`,
  `generate-readme`), not snake_case or camelCase.
* Scripts MUST be invoked from `SKILL.md` by relative path from the
  skill root (`scripts/validate-spec`), with forward slashes only.
  Windows-style path separators are forbidden in any bundled path.

---

## Boilerplate requirement

Every skill that bundles bash scripts MUST also bundle a single
shared boilerplate file at `scripts/bash-boilerplate.sh`. The
boilerplate is an internal artifact of the skill; no external
source is normative for its contents. The boilerplate MUST, as a
self-contained specification:

* Enable `errexit`, `errtrace`, `noclobber`, `pipefail`, and
  `nounset` as described under "Required strict mode".
* Pre-define `PROMPT_COMMAND` via `: "${PROMPT_COMMAND:=}"` before
  enabling `nounset`, so that surrounding shell fixtures do not
  trip the option.
* Define a `_log_prefix` variable set to `"${BASH_SOURCE[0]}:"`
  for use by the trap diagnostic.
* Define an `onexit` function that emits the diagnostic described
  under "Exit traps and error handling", invokes an optional
  caller-defined `onexit_hook` function when present, and
  preserves the original exit status.
* Install `trap onexit HUP INT QUIT TERM ERR`.
* Define `disable_error_checking` and `enable_error_checking`
  helpers that toggle `errexit` and the ERR trap together.
* Define a `handle_bash_xtrace` function that, when
  `BASH_XTRACE=true`, sets `PS4` with single-quoted delimiters so
  that `${BASH_SOURCE[0]}`, `${LINENO}`, and `${FUNCNAME[0]}`
  expand at trace-emission time, then enables `set -o xtrace`.
* Honor `BASH_VERBOSE=true` by enabling `set -o verbose`.
* Define every function using the `name() { ... }` form; the
  `function` keyword is forbidden in the boilerplate as in all
  other scripts.

The boilerplate MUST be vendored into the skill, not fetched at
runtime. The Anthropic API execution environment does not provide
network access at runtime; any `curl` or `wget` of the boilerplate
would fail.

Runnable scripts MUST source the boilerplate via:
```
source "$(dirname "${BASH_SOURCE[0]}")/bash-boilerplate.sh"
```
or, when the boilerplate lives at a non-sibling path,
```
source "$(realpath "$(dirname "${BASH_SOURCE[0]}")/../scripts/bash-boilerplate.sh")"
```

---

## Static analysis

### shellcheck

* Every committed bash script MUST pass `shellcheck` at severity
  `style` (the strictest default level) with zero findings.
* `shellcheck` MUST be invoked with `--external-sources`
  (equivalently `-x`) so that sourced files are analyzed.
* Per-line disables (`# shellcheck disable=SCNNNN`) are permitted
  but MUST be accompanied by an inline comment stating why the
  disable is safe. Disables without justification are forbidden.
* Project-wide disables via `.shellcheckrc` are discouraged. When
  used, the `.shellcheckrc` MUST be committed and each `disable=`
  entry MUST include a comment explaining the rationale.
* The `shellcheck` version used in CI MUST be pinned (e.g., via a
  container digest or package version). Floating `latest` is
  forbidden because new releases can introduce new checks that
  break the build without a corresponding code change.

### shfmt

* Every committed bash script MUST be formatted with `shfmt` using
  the flags `-i 2 -ci -bn -sr`, meaning: 2-space indent, indent
  switch cases, binary ops at start of next line, redirect
  operators followed by a space.
* CI MUST invoke `shfmt -d` and MUST fail the build when the
  command produces any diff.
* Authors SHOULD configure their editors or a pre-commit hook to
  run `shfmt -w` on save.
* The `shfmt` version MUST be pinned in CI for the same reason as
  `shellcheck`.

### Additional static analysis

* `shellharden --check` MUST be run in CI against every committed
  bash script and MUST exit zero. `shellharden` catches unquoted
  expansions more aggressively than `shellcheck` and its check
  mode is non-destructive.
* Skills MAY additionally run `bashate` or `bash-language-server`;
  neither is required.
* Binaries used for static analysis MUST be installed via a
  reproducible mechanism (package manager with pinned version,
  container image with pinned digest, or `asdf`/`mise` with pinned
  versions). Downloading tools from unversioned URLs at CI time is
  forbidden.

---

## Testing

* Every bash script bundled with the skill MUST have at least one
  corresponding test under `tests/`. This requirement composes
  with the top-level testing requirements in
  [PROPOSAL.md — Testing approach](PROPOSAL.md#testing-approach);
  this section adds the bash-specific concretions.
* Tests for bash scripts MUST use `bats-core`
  ([github.com/bats-core/bats-core](https://github.com/bats-core/bats-core)).
  The `bats` version MUST be pinned in CI.
* Test files MUST mirror script names: `scripts/validate-spec` is
  tested by `tests/scripts/validate-spec.bats`.
* Each script MUST have, at minimum:
  * One happy-path test that exercises the script's primary
    contract.
  * One test per documented failure mode (missing required arg,
    missing input file, missing required tool, malformed input).
  * One test that verifies the script's exit code on an invalid
    flag or missing required arg is the "usage error" code
    defined in "Exit code contract" below.
* Tests MUST NOT depend on network access, on files outside the
  repo, or on global state mutations. Tests that require a
  filesystem fixture MUST create it in a `bats`-provided temporary
  directory and MUST NOT mutate the repo.

---

## Enforcement via git hooks and CI

### Pre-commit hooks

* The project MUST ship a pre-commit configuration
  (`.pre-commit-config.yaml` for the `pre-commit` framework, or an
  equivalent committed `.githooks/pre-commit` script) that runs
  against staged files.
* The pre-commit configuration MUST, at minimum, run:
  * `shellcheck -x` on every staged bash script and the
    boilerplate.
  * `shfmt -d -i 2 -ci -bn -sr` on every staged bash script.
  * `shellharden --check` on every staged bash script.
  * A check that every staged executable bash script has the
    executable bit set.
  * A check that no staged bash script carries a `.sh` or `.bash`
    extension unless it is a sourced library.
* Commits MUST be blocked when any of these checks fail. Bypassing
  via `git commit --no-verify` is permitted for local experimental
  commits but MUST NOT appear on any pushed branch; CI catches
  these.
* The pre-commit configuration MUST be installable by a single
  documented command (e.g., `pre-commit install` or `make hooks`).

### Continuous integration

* CI MUST run the full static-analysis suite (`shellcheck`,
  `shfmt`, `shellharden`) against every bash file in the
  repository on every pull request and every push to the default
  branch. "Changed files only" is forbidden at CI level; the
  pre-commit hook covers the changed-files-fast-feedback case,
  but CI MUST verify the whole tree because rename/move operations
  and non-bash-language edits can still affect the bash surface.
* CI MUST run the full `bats` test suite on every pull request and
  every push to the default branch.
* CI MUST fail the build on any static-analysis finding, any test
  failure, or any non-zero exit from any of the commands above.
* CI MUST cache tool installation (to avoid redundant downloads)
  but MUST NOT cache test results or analysis results across runs.
* CI MUST run on the same major OS families the skill supports
  (minimally Linux; optionally macOS). The CI matrix MUST pin the
  bash version(s) under test.
* CI jobs MUST run their shell steps with `set -euo pipefail` at
  the shell level, so that a failed step in the CI script itself
  does not silently pass.

---

## Exit code contract

Bash scripts bundled with the skill MUST use the following exit
codes, which combine POSIX exit-code conventions, bash's own
builtin-return convention for invocation errors, and one
project-specific code for input and precondition failures:

| Code  | Meaning |
| ----- | ------- |
| `0`   | Success. |
| `1`   | Script-internal failure (unexpected runtime error; likely a bug). Error message on stderr is required. |
| `2`   | Usage error: bad flag, wrong number of arguments, malformed CLI invocation. Emits `--help` hint on stderr. |
| `3`   | Input or precondition failed: a referenced file/path/value does not exist, cannot be parsed, or is in an incompatible state. Invalid configuration files (e.g., a malformed `.livespec.jsonc`) fall under this code; the specificity of the failure MUST appear in the stderr message, not in the exit code. |
| `126` | Permission denied: a required file exists but is not executable/readable/writable as needed. Matches the shell's own `126`. |
| `127` | Required external tool not on `PATH` (`jq`, `pandoc`, etc.). Matches the shell's own "command not found" code. |

Provenance: `0` and `1` are universal Unix convention. `2` matches
bash's own convention for builtin invocation errors and is followed
by `getopt`, GNU coreutils, and `grep`. `126` and `127` are the
POSIX shell's codes for "file exists but not executable" and
"command not found" respectively; reusing them for the analogous
script-level preconditions means the exit code is meaningful whether
the script probed ahead or the underlying tool surfaced the
condition itself. `3` has no universal meaning; it is defined here
as the dedicated "your inputs or environment are wrong" signal, so
callers can route it differently from `2` ("your invocation is
wrong").

Scripts MUST NOT use exit codes outside this set without a comment
in the script header documenting the additional code and its
meaning. Scripts MUST NOT use exit codes in the reserved ranges
`128-165` (signal-triggered exits) or `255` (out-of-range sentinel)
for deliberate signalling; those are reserved for the shell.

The boilerplate's `onexit` function MUST preserve and re-raise the
original exit code. Wrapping or remapping exit codes inside
`onexit` is forbidden.

---

## Non-goals

The following are intentionally out of scope for this section. They
are listed so their absence is a deliberate boundary, not a gap.

* **Interactive execution.** Skill scripts are non-interactive by
  design. Scripts intended for human use at a terminal are not
  governed by this section.
* **Portability to POSIX sh.** Bashisms are permitted throughout.
  Scripts that need sh-compatibility live outside the skill and
  are governed by a different section (not in v1).
* **Portability to zsh, ash, dash, ksh, or Windows shells.**
* **Non-bash script languages.** Python, Node, and Deno scripts
  bundled with the skill are governed by their own (future)
  sections; nothing in this section applies to them.
* **Performance tuning.** Bash is not the right tool for hot
  paths; scripts that need performance delegate to compiled tools
  via pipelines.
* **Runtime dependency resolution.** Missing external tools are
  reported with exit `127`; installing them is the caller's
  problem, not the script's. The Anthropic API runtime environment
  has no network access for runtime installs.
