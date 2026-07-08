"""Pre-import plugin-currency gate (stdlib-only; never imports `livespec`).

`bin/_bootstrap.py` inserts `.claude-plugin/scripts` onto `sys.path` and
imports this package BEFORE the vendor path and any `livespec` package
load, so it must stay stdlib-only. `verify_currency()` returns a
`CurrencyVerdict` the supervisor acts on (writes the message + raises
SystemExit); keeping those side effects in the bin supervisor keeps this
package clear of `check-supervisor-discipline`.
"""

from _currency.verify import CurrencyVerdict, verify_currency

__all__ = ["CurrencyVerdict", "verify_currency"]
