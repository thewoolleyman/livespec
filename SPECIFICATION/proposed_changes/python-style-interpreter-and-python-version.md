---
topic: python-style-interpreter-and-python-version
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T04:46:00Z
---

## Proposal: Merge style-doc §"Interpreter and Python version" into existing `## Python runtime constraint`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 3 of Plan Phase 8 item 2 per-section migration. Merges the source doc's §"Interpreter and Python version" content (lines 91-110) into the existing `## Python runtime constraint` section in `SPECIFICATION/constraints.md` (rather than inserting a duplicate section), preserving the existing heading and replacing the prior 1-paragraph body with a 4-paragraph BCP-14-restructured body that incorporates every source-doc bullet plus the existing constraints.md content. Cross-references cycle 1's revise body for the deviation rationale from `deferred-items.md` "at seed time" guidance.

### Motivation

The existing `## Python runtime constraint` section in `SPECIFICATION/constraints.md` was seeded at Phase 6 with PROPOSAL.md-direct content only (1 paragraph: Python 3.10+ minimum, `_bootstrap.py` shebang preamble, `.python-version` + `pyproject.toml` pinning). Source-doc §"Interpreter and Python version" carries the same architectural rule plus four additional concrete obligations not yet in the spec: (a) Python 3.10's modern syntax features (`X | Y`, `match`, `ParamSpec`, `TypeAlias`) are expected idioms; (b) Python 3.11+ features (`Self`, `tomllib`, `ExceptionGroup`) MUST NOT be used; (c) the canonical shebang `#!/usr/bin/env python3` is required; (d) `.mise.toml` pins only non-Python binaries (`uv`, `just`, `lefthook`); developers run `mise install` then `uv sync --all-groups`.

A merge (rather than a sibling-insert) is preferred per Plan Phase 8 item 2's "destination heading taxonomy fits better" heuristic: both sections constrain the same architectural surface (Python interpreter version + bootstrap + tooling). A duplicate sibling section would create ambiguity for future maintainers reading constraints.md. Heading kept as `## Python runtime constraint` (the existing constraints.md genre name); source-doc heading "Interpreter and Python version" is descriptive; `Python runtime constraint` is constraint-asserting and matches the file's surrounding section style.

### Proposed Changes

One atomic edit to **SPECIFICATION/constraints.md**: replace the body paragraph of `## Python runtime constraint` (the 1-paragraph body currently at line 30) with a 4-paragraph merged body. The heading itself is unchanged.

New body:

> `livespec`'s Python wrappers and library code MUST run on Python 3.10 or newer. Python 3.10's `X | Y` union syntax, `match` statements, `ParamSpec`, `TypeAlias`, and improved typing syntax are expected idioms. Features introduced in Python 3.11+ (e.g., `Self`, `tomllib`, `ExceptionGroup`) MUST NOT be used.
>
> The shared `bin/_bootstrap.py:bootstrap()` function MUST assert `sys.version_info >= (3, 10)` and exit `127` with an actionable install-instruction message on older interpreters. `bin/_bootstrap.py` is the canonical location for the version check; `.claude-plugin/scripts/livespec/__init__.py` MUST NOT raise (the railway requires unconditional importability).
>
> Bundled executables MUST use the shebang `#!/usr/bin/env python3`. No other interpreter path is valid.
>
> `.python-version` at the repo root pins the developer and CI Python version to an exact 3.10.x release (managed by `uv python pin` per v024 D1). `pyproject.toml`'s `[project.requires-python]` declares the same constraint as the user-facing minimum. `.mise.toml` pins only the non-Python binaries (`uv`, `just`, `lefthook`); developers run `mise install` then `uv sync --all-groups` to materialize the matched environment.
