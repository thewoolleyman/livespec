---
topic: expand-coverage-exclude-also-to-match-impl
author: claude-opus-4-7
created_at: 2026-05-27T06:41:57Z
---

## Proposal: Expand exclude_also enumeration in NFR "Code coverage thresholds" to match impl

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

`SPECIFICATION/non-functional-requirements.md` §"Code coverage thresholds" currently enumerates FOUR structural `exclude_also` patterns (`if TYPE_CHECKING:`, `raise NotImplementedError`, `@overload`, `case _:`), but `pyproject.toml`'s `[tool.coverage.report].exclude_also` actually carries SEVEN: those four PLUS `raise ImportError`, `if __name__ == .__main__.:`, and `sys.path.insert`. The spec must be brought into agreement with the impl by enumerating all seven patterns. No code change is needed; this is pure NFR catchup to the impl.

### Motivation

Cross-spec follow-up from livespec-dev-tooling PR #34 (`spec-amendments-from-doctor-followup-findings`, merged today). That PC's sub-proposal #5 (`add-sys-path-insert-to-coverage-exclude-also-exact-list`) added `sys.path.insert` to dev-tooling's NFR exact list and mandated a parallel propose-change against livespec-core if its list did not already carry that pattern. Verification of livespec/SPECIFICATION/non-functional-requirements.md §"Code coverage thresholds" against livespec/pyproject.toml revealed the drift is broader than just `sys.path.insert`: livespec-core's NFR is missing THREE patterns relative to its own pyproject.toml. Filing one PC that captures all three missing patterns is better diff economy than filing only the mandated single-pattern fix and leaving the other two drifts open, and resolves the full spec→impl alignment in one revise cycle. The `sys.version_info` gates in `bin/_bootstrap.py` already noted in the NFR remain accurate (covered by dedicated tests rather than excluded — not an exclude_also entry).

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Code coverage thresholds", the paragraph at line 638 currently reads:

> **No line-level pragma escape hatch.** `# pragma: no cover` comments are forbidden anywhere in covered trees. The ONLY coverage exclusions permitted are the four structural patterns in `[tool.coverage.report].exclude_also`: `if TYPE_CHECKING:`, `raise NotImplementedError`, `@overload`, and `case _:` (the assert_never exhaustiveness arm). These are block-level patterns recognized by coverage.py without per-instance annotation:

Replace with the seven-pattern enumeration that matches the actual `[tool.coverage.report].exclude_also` config:

> **No line-level pragma escape hatch.** `# pragma: no cover` comments are forbidden anywhere in covered trees. The ONLY coverage exclusions permitted are the seven structural patterns in `[tool.coverage.report].exclude_also`: `if TYPE_CHECKING:`, `raise NotImplementedError`, `raise ImportError`, `@overload`, `if __name__ == .__main__.:`, `sys.path.insert`, and `case _:` (the assert_never exhaustiveness arm). These are block-level patterns recognized by coverage.py without per-instance annotation:

The three added patterns:

- `raise ImportError` — guards in vendored-fallback paths where an upstream package's import may fail and a documented fallback is taken; the `raise` line itself is structurally unreachable in the happy-path test matrix.
- `if __name__ == .__main__.:` — main-guard blocks; never executed when modules are imported under pytest. The dotted form matches the literal token coverage.py emits in source.
- `sys.path.insert` — the vendored-path guard `if str(X) not in sys.path: sys.path.insert(...)`; already in `sys.path` when tests run via pyproject.toml's `pythonpath` config, so the insert branch is structurally dead in tests.

The three existing bullets immediately below the paragraph (the `if TYPE_CHECKING:` bullet, the `sys.version_info` bullet, and the `case _:` bullet) remain unchanged. The `sys.version_info` bullet's framing — "covered by dedicated `tests/bin/test_bootstrap.py` tests" rather than excluded — remains accurate (it is NOT an `exclude_also` entry); no change to that bullet.

No `tests/heading-coverage.json` change is needed (the H2 set of `non-functional-requirements.md` is untouched; this is body-text-only inside §"Code coverage thresholds").
