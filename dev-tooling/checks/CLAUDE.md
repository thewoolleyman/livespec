# dev-tooling/checks/

Per-check enforcement scripts. Each `<name>.py`:

- Is a standalone Python module (no `livespec/` import; ruff/
  pyright scope includes this tree per pyproject.toml).
- Walks the repo (or a designated subtree) deterministically.
- Prints structured diagnostics for failures (one per line, with
  file path + line number + check_id).
- Exits 0 on pass, non-zero on fail.
- Is invokable as `python3 dev-tooling/checks/<name>.py`
  (no CLI flags; the script reads the repo at cwd).

Each script has a paired `tests/dev-tooling/checks/test_<name>.py`
that covers BOTH pass and fail cases (per plan line 1452-1453).

Slug ↔ filename mapping is direct (kebab-case slug ↔
snake_case filename ↔ `just check-<slug>` target).
