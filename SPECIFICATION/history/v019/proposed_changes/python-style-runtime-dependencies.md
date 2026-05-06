---
topic: python-style-runtime-dependencies
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T04:50:00Z
---

## Proposal: Migrate style-doc §"Runtime dependencies" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 4 of Plan Phase 8 item 2 per-section migration. Migrates source-doc §"Runtime dependencies" (lines 114-298, with 3 source-doc `###` sub-sections: End-user install, Vendored third-party libraries, Vendoring discipline) into `SPECIFICATION/constraints.md` as TWO destination sections — each scope-focused: (a) NEW `## End-user runtime dependencies` (from ### End-user install, inserted after `## Python runtime constraint` and before `## Vendored-library discipline`); (b) EXPANDED `## Vendored-library discipline` (existing heading retained, body replaced with merged content from ### Vendored third-party libraries + ### Vendoring discipline using `###` sub-headings). BCP-14-restructured throughout. Cross-references cycle 1's deviation rationale.

### Motivation

Source-doc §"Runtime dependencies" is the largest single section addressed so far (~184 lines) and covers two architecturally-distinct concerns: (1) what runtime dependencies the skill imposes on end-user machines, and (2) what dependencies the bundle vendors and the procedure governing them. The existing constraints.md `## Vendored-library discipline` already covers (2) at a high level (1 paragraph); merging in the source-doc detail expands it without scope creep. (1) has no existing destination section, so it lands as a new section. Splitting into two destination sections (rather than one large `## Runtime dependencies` umbrella) keeps each section's heading accurate to its content scope and aids future maintainers searching for specific rules.

The destination is `SPECIFICATION/constraints.md` (not `spec.md`) per Plan Phase 8 item 2's "destination heading taxonomy fits better" heuristic: both end-user-install rules and vendored-library rules are architectural constraints on the skill bundle, parallel to existing `## Python runtime constraint` and `## Pure / IO boundary`.

### Proposed Changes

Two atomic edits to **SPECIFICATION/constraints.md**:

1. **Insert a new `## End-user runtime dependencies` section** after the closing line of `## Python runtime constraint` and before `## Vendored-library discipline`:

   > ## End-user runtime dependencies
   >
   > `python3` >= 3.10 MUST be the sole runtime dependency the skill imposes on end-user machines. Python 3.10+ is preinstalled on Debian ≥ 12, Ubuntu ≥ 22.04, Fedora, Arch, RHEL ≥ 9; one-command install on macOS via Homebrew or Xcode CLT.
   >
   > The skill MUST NOT require any PyPI install step from end users; runtime imports MUST be satisfiable from the stdlib plus the vendored tree under `.claude-plugin/scripts/_vendor/<lib>/`. `jq` is NOT a runtime dependency (stdlib `json` covers every use). Bash MUST NOT be invoked anywhere in the bundle — every executable path is `python3` (or shebang scripts that `exec` Python).

2. **Replace the body of `## Vendored-library discipline`** (the existing 2-paragraph body) with the merged content. Heading retained:

   > ## Vendored-library discipline
   >
   > The bundle MUST ship a curated set of pure-Python third-party libraries under `.claude-plugin/scripts/_vendor/<lib>/`. The vendored tree is the only runtime-import root for non-stdlib code, apart from the dev-time tooling layer at `pyproject.toml`'s `[dependency-groups.dev]`. `livespec` MUST NOT install runtime dependencies via pip or any other package manager at user invocation time.
   >
   > ### Lib admission policy
   >
   > Every vendored lib MUST be:
   >
   > - Pure Python — no compiled wheels, no C/Rust extensions.
   > - Permissively licensed — MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, or PSF-2.0. PSF-2.0 was admitted in v013 M1 to vendor `typing_extensions`; the narrow extension is deliberate and MUST NOT generalize to other licenses without an explicit PROPOSAL revision.
   > - Actively maintained by a reputable upstream.
   > - Either zero-transitive-dep, or all transitive deps also vendored.
   >
   > Each vendored lib's `LICENSE` file MUST be preserved at `_vendor/<lib>/LICENSE`. A `NOTICES.md` at the repo root MUST list every vendored lib with its license and copyright.
   >
   > ### Locked vendored libs
   >
   > Each lib is pinned to an exact upstream ref recorded in `<repo-root>/.vendor.jsonc`:
   >
   > - **`returns`** (dry-python/returns, BSD-3-Clause) — ROP primitives: `Result`, `IOResult`, `@safe`, `@impure_safe`, `flow`, `bind`, `Fold.collect`, `lash`. NO pyright plugin is vendored: pyright has no plugin system by design (microsoft/pyright#607) and dry-python/returns explicitly does not support pyright (dry-python/returns#1513). The seven strict-plus diagnostics in `[tool.pyright]` (especially `reportUnusedCallResult = "error"`) are the load-bearing guardrails against silent `Result` / `IOResult` discards. See PROPOSAL.md §"Runtime dependencies" v025 D1 for the full disposition.
   > - **`fastjsonschema`** (horejsek/python-fastjsonschema, MIT) — JSON Schema Draft-7 validator.
   > - **`structlog`** (hynek/structlog, BSD-2 / MIT dual) — structured JSON logging.
   > - **`jsoncomment`** (MIT, derivative work) — vendored as a minimal hand-authored shim per v026 D1. The shim at `.claude-plugin/scripts/_vendor/jsoncomment/__init__.py` faithfully replicates jsoncomment 0.4.2's `//` line-comment and `/* */` block-comment stripping semantics. The canonical upstream (`bitbucket.org/Dando_Real_ITA/json-comment`) was sunset by Atlassian and no live git mirror exists; the shim's `LICENSE` carries verbatim MIT attribution to Gaspare Iengo (citing jsoncomment 0.4.2's `COPYING` file). Used by `livespec/parse/jsonc.py` as a comment-stripping pre-pass over stdlib `json.loads`.
   > - **`typing_extensions`** (python/typing_extensions, PSF-2.0) — vendored full upstream verbatim at tag `4.12.2` per v027 D1. Provides `override`, `assert_never`, `Self`, `Never`, `TypedDict`, `ParamSpec`, `TypeVarTuple`, `Unpack` plus the variadic-generics symbols transitively required at import time by `returns`, `structlog`, `fastjsonschema` on Python 3.10. The verbatim PSF-2.0 `LICENSE` is shipped at `_vendor/typing_extensions/LICENSE`.
   >
   > The shared `bin/_bootstrap.py:bootstrap()` function MUST insert BOTH the bundle's `scripts/` directory AND the bundle's `scripts/_vendor/` directory into `sys.path`. Adding `scripts/` makes the `livespec` package resolvable (`from livespec.commands.seed import main`); adding `scripts/_vendor/` makes each vendored top-level package resolvable under its natural name (`from returns.io import IOResult`, `import structlog`, etc.).
   >
   > ### Vendoring procedure
   >
   > Source-tree population is governed by two paths:
   >
   > - **Re-vendoring** of upstream-sourced libs (`returns`, `fastjsonschema`, `structlog`, `typing_extensions`) MUST go through `just vendor-update <lib>` — the only blessed mutation path. The recipe fetches the upstream ref, copies it under `_vendor/<lib>/`, preserves `LICENSE`, and updates `.vendor.jsonc`'s recorded ref.
   > - **Initial vendoring** is a one-time MANUAL procedure (the v018 Q3 exception, executed once per livespec repo at Phase 2 of the bootstrap plan): `git clone` the upstream repo at a working ref into a throwaway directory, `git checkout <ref>` matching `.vendor.jsonc`'s `upstream_ref`, copy the library's source tree under `_vendor/<lib>/`, copy the upstream `LICENSE` verbatim to `_vendor/<lib>/LICENSE`, record the lib's provenance (`upstream_url`, `upstream_ref`, `vendored_at` ISO-8601 UTC), delete the throwaway clone, and smoke-test that the wrapper bootstrap imports the vendored lib successfully. The exception resolves the circularity that `just vendor-update` invokes Python through `livespec.parse.jsonc` (which imports `jsoncomment`); the recipe cannot run before `jsoncomment` exists.
   > - **Shim libs** are livespec-authored and DO NOT go through `just vendor-update`. The `jsoncomment` shim is the sole shim post-v027; it is widened (one-line edit per added feature) or replaced with a full upstream vendoring via a new propose-change cycle. `.vendor.jsonc` records the shim's upstream attribution ref (for provenance) and a `shim: true` flag.
   >
   > Direct edits to `_vendor/` files are forbidden for upstream-sourced libs — any such edit is treated as drift and caught at code review. The "never edit `_vendor/`" rule applies only to upstream-sourced libs; shim updates go through normal code-review.
   >
   > `.vendor.jsonc` records `{upstream_url, upstream_ref, vendored_at}` per lib; for shims, additionally `shim: true` and the provenance ref from which the shim's `LICENSE` was derived.
   >
   > `_vendor/` is EXEMPT from livespec's own style rules, type-checking strictness, coverage measurement, and CLAUDE.md coverage enforcement per `## Constraint scope` above.
