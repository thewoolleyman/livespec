# tests/livespec/io/

Tests for the impure layer at `livespec/io/`. Each module's
test exercises the actual side-effecting operation against a
real fixture (filesystem via `tmp_path`, real git via
`subprocess.run` on a fresh `git init`'d directory, real CLI
parser invocation), wrapping the call in the
`@impure_safe`-emitted `IOResult` and asserting both the
success carrier value and the failure carriers for each
documented error path.

Coverage gates:

- `cli.py` — argparse setup with `exit_on_error=False`;
  `UsageError` propagation; help/version short-circuits.
- `fs.py`, `git.py` — exercise both success and known-failure
  modes; `LivespecError` subtype on each failure path.
- `fastjsonschema_facade.py`, `structlog_facade.py`,
  `returns_facade.py` — typed facade tests; assert the facade
  surface returns typed values (no `Any` leaking through).

Tests in this tree may import `livespec.io.*`; tests for pure
layers (`parse/`, `validate/`) MUST NOT import from `io/`.
