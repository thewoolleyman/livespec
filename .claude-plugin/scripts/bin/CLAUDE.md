# bin/

Shebang-wrapper executables (`#!/usr/bin/env python3`). Each wrapper
is a 6-statement supervisor entry point that imports
`livespec.commands.<cmd>.main` (or `livespec.doctor.run_static.main`)
and calls `raise SystemExit(main())`. Shape is mechanically enforced
by `check-wrapper-shape`.

`_bootstrap.py` is the one exception to the wrapper shape: it carries
the pre-livespec sys.path setup + Python version check, and delegates
the plugin-currency gate to the sibling stdlib-only `_currency`
package (`.claude-plugin/scripts/_currency/`, a top-level sibling of
`bin/`, imported after `.claude-plugin/scripts` is on sys.path but
before the vendor path or any `livespec` import — so importing it
never drags in the `livespec` package's structlog-configuring
`__init__`). `_currency.verify_currency()` returns a `CurrencyVerdict`
(pure data); `_bootstrap.py` performs the `sys.stderr.write` + `raise
SystemExit` on the verdict, so the currency package itself stays clear
of `check-supervisor-discipline`. `_bootstrap.py` is thus the only
file outside supervisor scope where `sys.stderr.write` is permitted
(the version-check error message and the currency verdict message;
structlog has not yet been configured at that point).

`raise SystemExit(...)` is permitted in this directory. Everywhere
else, the supervisor pattern-matches an `IOResult` and returns the
exit code; bare `sys.exit` is banned.
