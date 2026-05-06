# Retired documents (v006)

This directory holds documents that were load-bearing in a prior
version and are no longer active in the working brainstorming folder.
Retirement context is recorded here so the on-disk record preserves
not just the document but the reason it was retired.

## `bash-skill-script-style-requirements.md`

**Retired in:** v006 (language migration pass from bash to Python).

**Replaced by:** `brainstorming/approach-2-nlspec-based/python-skill-
script-style-requirements.md`.

**Reason for retirement.** v006 migrated livespec's skill-bundled
scripts and dev-tooling enforcement scripts from bash to Python. The
bash style doc's ~24 pages of rules existed largely to compensate for
bash's missing abstractions (namespaces, import system, data
structures, a type system, AST access, test/coverage tooling). Python
3.10+ supplies those natively, collapsing the style doc to a
substantially smaller Python-specific replacement.

**Load-bearing invariants preserved in the Python style doc** — the
Python doc inherits v006's versions of these directly:

- Exit code contract (0 / 1 / 2 / 3 / 126 / 127).
- Enforcement-suite invocation-agnostic framing (Makefile → justfile
  targets consumed by pre-commit / pre-push / CI / manual invocation).
- mise-based tool pinning discipline (now pins Python + just +
  lefthook + pyright + ruff + pytest rather than bash + shellcheck +
  shfmt + etc.).
- Runtime vs dev-time split: shipped bundle in `.claude-plugin/`
  contains only runtime; dev-tooling at `<repo-root>/dev-tooling/`
  stays outside.
- Doctor static-check decomposition (per-slug per-module; slug-based
  `check_id` wire contract).
- Structured-output stdout contract for doctor's static phase; stderr
  reserved for diagnostics.
- No interactivity; non-interactive execution mandated.

**Discarded accommodations that were bash-specific** (no longer
relevant):

- Bash 3.2.57 floor (for macOS `/bin/bash` compatibility).
- Sourceable-guard idiom `if [[ "${0}" == "${BASH_SOURCE[0]}" ]]; then
  main "$@"; fi`.
- Shared `bash-boilerplate.sh` (strict-mode flags, error traps,
  xtrace setup).
- Forbidden-bash-4.x-features list (namerefs, associative arrays,
  `mapfile`, `${var,,}`).
- `"${arr[@]-}"` empty-default expansion rule.
- AST-level architectural checks mandated via tree-sitter-bash; these
  become `ast.walk(...)` calls in Python.
- Library-header directive format (`# concern: ...`, `# prefix: ...`,
  `# purity: ...`, `# sources: ...`); replaced by docstrings and
  directory-based purity.
- Function-name prefixing rules (Python's module system supplies
  namespacing natively).
- `kcov` coverage thresholds (95% pure / 80% overall); Python's
  `coverage.py` has no DEBUG-trap artifact, so v006 uses 100% line +
  branch everywhere.

**Where to find the retired document's content.** The full retired
document is preserved alongside this README:
`bash-skill-script-style-requirements.md` in this directory. It is
the byte-identical copy of what lived at
`brainstorming/approach-2-nlspec-based/bash-skill-script-style-
requirements.md` at the end of v005.

**What to read instead when asking bash-related questions.**

- For **why** livespec migrated: see `proposal-critique-v05.md` and
  its `proposal-critique-v05-revision.md` in
  `history/v006/proposed_changes/`.
- For **what the current Python style is:** see
  `brainstorming/approach-2-nlspec-based/python-skill-script-style-
  requirements.md`.
- For **prior bash decisions:** see the `history/vNNN/proposed_
  changes/*-revision.md` files for v002 through v005, which carry
  every bash-era decision record.
