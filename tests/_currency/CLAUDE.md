# tests/_currency/

Mirrors `.claude-plugin/scripts/_currency/` — the stdlib-only
pre-import plugin-currency gate package. One test module per source
module:

- `test_locate.py` — plugin-root / installed-cache detection / JSON read
- `test_expected_build.py` — marketplace-clone pin resolution
- `test_running_build.py` — installed-registry + Codex plugin-list
  running-build detection
- `test_verify.py` — `verify_currency()` verdict orchestration and the
  stale/unknown message

The `bin/_bootstrap.py` supervisor's delegation to this package
(writing the verdict message, raising SystemExit on a hard-fail or a
gate-sensitive verdict under `LIVESPEC_CURRENCY_GATE=fail`) is covered
by `tests/bin/test_bootstrap.py`.
