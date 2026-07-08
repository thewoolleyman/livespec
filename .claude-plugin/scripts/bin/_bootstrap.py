"""Pre-livespec-import bootstrap: Python version check + sys.path setup.

Imported by every bin/*.py wrapper before any livespec import. Lives under
bin/ so `raise SystemExit` is permitted by check-supervisor-discipline. The
plugin-currency gate itself lives in the sibling stdlib-only `_currency`
package: this supervisor inserts `.claude-plugin/scripts` onto sys.path,
imports `_currency` (which never touches the vendor path or the livespec
package), then writes the verdict message and raises SystemExit — before
the vendor path, the livespec package, or any command code is loaded.
"""

import os
import sys
from pathlib import Path

_EXIT_CODE_VERSION_MISMATCH = 127
_EXIT_CODE_STALE_PLUGIN = 78
_CURRENCY_GATE_FAIL = "fail"


def bootstrap() -> None:
    if sys.version_info < (3, 10):
        _ = sys.stderr.write("livespec requires Python 3.10+; install via your package manager.\n")
        raise SystemExit(_EXIT_CODE_VERSION_MISMATCH)
    bundle_scripts = Path(__file__).resolve().parent.parent
    _insert_sys_path(entry=bundle_scripts)
    from _currency import verify_currency

    verdict = verify_currency()
    if verdict.message is not None:
        _ = sys.stderr.write(verdict.message)
    gate_fail = os.environ.get("LIVESPEC_CURRENCY_GATE") == _CURRENCY_GATE_FAIL
    if verdict.hard_fail or (verdict.gate_sensitive and gate_fail):
        raise SystemExit(_EXIT_CODE_STALE_PLUGIN)
    _insert_sys_path(entry=bundle_scripts / "_vendor")


def _insert_sys_path(*, entry: Path) -> None:
    entry_str = str(entry)
    if entry_str not in sys.path:
        sys.path.insert(0, entry_str)
