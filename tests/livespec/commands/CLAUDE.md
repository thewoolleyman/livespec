# tests/livespec/commands/

Per-supervisor + per-railway tests for `livespec/commands/`.
Each `test_<cmd>.py` covers the matching `commands/<cmd>.py`:

- `run()` — the railway entry. Assert it returns the expected
  `IOResult[<value>, LivespecError]` for both the success path
  (covering each branch of the railway) and each
  `LivespecError` subtype the command can produce.
- `main()` — the supervisor. Assert it pattern-matches `run()`'s
  result correctly: success → exit 0 with the documented stdout
  shape; `HelpRequested` → exit 0 with the help text;
  `UsageError` → exit 2 with the usage diagnostic to stderr;
  every other `LivespecError` → exit 1 with the error message.
  Bug-path (raised exception) handling is covered as well.
- `_<cmd>_helpers.py` — pure helper-module tests cover the
  rendering / formatting helpers exercised by their consumers.

Tests use `tmp_path` to construct minimal repo-shape fixtures,
`monkeypatch` to stub `os.environ`, and `capsys` to capture
stdout/stderr.
