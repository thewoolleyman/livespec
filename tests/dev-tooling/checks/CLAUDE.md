# tests/dev-tooling/checks/

Per-check tests. Each `test_<name>.py` covers both pass and fail
cases for the corresponding `dev-tooling/checks/<name>.py`
enforcement script. Tests use pytest's `tmp_path` fixture to
construct minimal repo-shape fixtures, then invoke the check
script (typically by importing its `main()` and calling it with
the `tmp_path` as cwd, or by `subprocess.run` with the script's
absolute path and `cwd=tmp_path`).

Common patterns (Phase 4 minimum-viable):

- **Pass case:** construct a fixture matching the rule the check
  enforces; assert exit 0 and empty/clean stdout-stderr.
- **Fail case:** construct a fixture violating the rule; assert
  non-zero exit and verify the diagnostic message names the
  offending file/line.
