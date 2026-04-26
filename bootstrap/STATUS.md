# Bootstrap status

**Current phase:** 2
**Current sub-step:** 5 (BLOCKED — one PROPOSAL drift)
**Last completed exit criterion:** phase 1
**Next action:** Resolve the blocking PROPOSAL.md drift logged at `bootstrap/open-issues.md` 2026-04-26T07:05:00Z: PROPOSAL.md / plan / NOTICES.md / .vendor.jsonc / pyproject.toml all reference vendoring `returns_pyright_plugin` from dry-python/returns, but the upstream repo (verified at v0.25.0) ships no pyright plugin (only mypy / pytest / hypothesis plugins under `returns/contrib/`). Before deciding the resolution path, do a thorough upstream search: other dry-python repos, recent main branch, GitHub-wide search for "returns pyright plugin" / "dry-python pyright". A scratch clone of dry-python/returns at v0.25.0 is at `tmp/bootstrap/vendoring/returns/` (gitignored). Once the search confirms the artifact's status, open the v025 halt-and-revise walkthrough — the v025 revision will also sweep the cosmetic BSD-2 → BSD-3-Clause license label fix (per the superseded entry at 2026-04-26T07:05:01Z; not its own blocker per the new one-finding-per-gate skill rule).
**Last updated:** 2026-04-26T07:26:00Z
**Last commit:** c0e7d61
