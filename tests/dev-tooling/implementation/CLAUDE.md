# tests/dev-tooling/implementation/

Tests for the repo-local implementation-workflow scripts under
`dev-tooling/implementation/`. Each `test_<name>.py` covers both
pass and fail cases for the corresponding
`dev-tooling/implementation/<name>.py` script. Tests use pytest's
`tmp_path` fixture to construct minimal repo-shape fixtures, then
invoke the script (typically by `subprocess.run` with the
script's absolute path and `cwd=tmp_path`).

The mirroring discipline that the `tests_mirror_pairing` check
enforces for `dev-tooling/checks/` is currently scoped to that
tree only; this directory's tests are voluntary mirror coverage
until the check's `_SOURCE_TREES_TO_TESTS` map is widened to
include `dev-tooling/implementation/` (tracked separately as a
gap-0004 follow-on).
