# tests/_currency/

Mirrors `.claude-plugin/scripts/_currency/` — the stdlib-only
pre-import plugin-currency gate package. One test module per source
module:

- `test_locate.py` — plugin-root / installed-cache detection / JSON read
- `test_codex_remote.py` — Codex `config.toml` parse + `ls-remote` tip
- `test_expected_build.py` — Claude clone HEAD / Codex remote-ref pin
- `test_running_build.py` — Claude installed-registry / Codex
  `last_revision` running-build detection
- `test_verify.py` — `verify_currency()` verdict orchestration and the
  stale/unknown message

The `bin/_bootstrap.py` supervisor's delegation to this package
(writing the verdict message, raising SystemExit on a hard-fail or a
gate-sensitive verdict under `LIVESPEC_CURRENCY_GATE=fail`) is covered
by `tests/bin/test_bootstrap.py`.
