# dev-tooling/

Standalone enforcement scripts that the `justfile` invokes from
the canonical `just check-*` targets. Each `dev-tooling/checks/
<name>.py` is a self-contained Python module that walks the repo
(or a designated subtree) and exits 0 on pass, non-zero on fail.

These scripts conform to the same style rules as the shipped
livespec code (`just check` includes `dev-tooling/**` in the
ruff/pyright scope per pyproject.toml). They do NOT import from
`livespec/` — they're upstream of the package and run standalone
under `python3 dev-tooling/checks/<name>.py`.

Per Phase 4 of the bootstrap plan, this directory hosts ~22
enforcement scripts paired one-to-one with `tests/dev-tooling/
checks/test_<name>.py`. Adding a new check is one explicit edit
to `justfile` (new `check-<slug>` target + entry in the `check`
aggregate's targets list) plus authoring the script and its
paired test.
