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
- `codex_remote.py` — Codex `config.toml` parse + remote-ref-tip `ls-remote`
- `expected_build.py` — Claude marketplace-clone HEAD / Codex remote-ref tip
- `running_build.py` — Claude installed-registry / Codex config `last_revision`
- `verify.py` — verdict orchestration + the stale/unknown message

The Codex currency axis is LOCAL provenance (the config `last_revision`
Codex last upgraded the clone to) versus the REMOTE tip of the tracked
`ref` — NOT the marketplace clone HEAD, which is tautologically equal to
the running build. A confirmed-stale Codex install is fail-soft (Codex
auto-upgrades natively at session start), so it warns and proceeds unless
`LIVESPEC_CURRENCY_GATE=fail`; a confirmed-stale Claude install hard-fails.
