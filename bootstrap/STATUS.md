# Bootstrap status

**Current phase:** 2
**Current sub-step:** 10 (phase-exit gates: re-run 5b exit-criterion check post-fix → 5c advance to Phase 3)
**Last completed exit criterion:** phase 1
**Next action:** Re-run Phase 2 exit-criterion check (`ruff check .` + manual file-existence verification block) post sub-step 9 fix to pyproject.toml; then route to 5c advance gate. Sub-step 9 complete (this commit): pyproject.toml `[tool.ruff]` gained `extend-exclude = ["**/_vendor/**", "**/__pycache__/**"]` per style doc line 294-296, and a new `[tool.ruff.lint.per-file-ignores]` block exempts `.claude-plugin/scripts/bin/*.py` from `["I001", "E402", "E501"]` (per the wrapper-shape contract at style doc 1664-1668) and exempts `.claude-plugin/scripts/bin/_bootstrap.py` from `["UP036"]` (per the bootstrap-mechanism rule at style doc 1697-1700). Post-fix `uv run ruff check .` returns "All checks passed!" (was 1151 errors: 1132 in `_vendor/`, 19 in `bin/*.py`). Pure implementation bug fix in pyproject.toml — no PROPOSAL/plan changes; the spec already mandated both behaviors. Side observation captured to decisions.md for later sweep: style doc line 1820 has stale `check-vendor-manifest` shim-flag attribution to typing_extensions instead of jsoncomment (post-v026/v027 reclassification); cosmetic only, rides along with next substantive PROPOSAL revision.
**Last updated:** 2026-04-26T08:33:35Z
**Last commit:** 38db5fb
