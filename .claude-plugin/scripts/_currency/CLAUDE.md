# _currency/

The pre-import plugin-currency gate: a top-level, stdlib-only
package (a sibling of `bin/`, `livespec/`, `_vendor/`, `_stubs/`).
`bin/_bootstrap.py` inserts `.claude-plugin/scripts` onto `sys.path`
and imports this package BEFORE the vendor path or the `livespec`
package, so it MUST stay stdlib-only and MUST NOT import `livespec`
(whose package `__init__` configures structlog at import time).

`verify_currency()` returns a `CurrencyVerdict`; the bin supervisor
(`bin/_bootstrap.py`) performs the `sys.stderr.write` + `raise
SystemExit`, keeping this package clear of
`check-supervisor-discipline` (which bans process termination
outside `bin/`).

Modules:

- `locate.py` — plugin-root, installed-cache detection, JSON read (leaf)
- `expected_build.py` — pinned marketplace-clone build resolution
- `running_build.py` — installed-registry + Codex plugin-list build detection
- `verify.py` — verdict orchestration + the stale/unknown message
