"""Plugin-currency verdict orchestration and the stale/unknown message.

`verify_currency()` resolves the running and expected builds and returns a
`CurrencyVerdict` describing what the bin supervisor (`_bootstrap.py`)
should do. This package NEVER writes stderr or raises SystemExit — those
process-termination side effects belong to the bin supervisor, which keeps
`_currency` clear of `check-supervisor-discipline`.
"""

from typing import NamedTuple

from _currency.expected_build import _expected_build_id
from _currency.locate import (
    _MARKETPLACE_NAME,
    _PLUGIN_NAME,
    _is_codex_installed_plugin_cache_path,
    _is_installed_plugin_cache_path,
    _plugin_root,
)
from _currency.running_build import _running_build_id

__all__ = ["_CHECKOUT_MODE_MESSAGE", "CurrencyVerdict", "_currency_message", "verify_currency"]

_CHECKOUT_MODE_MESSAGE = "INFO: running from a repo checkout; plugin-currency gate not applicable\n"


class CurrencyVerdict(NamedTuple):
    """What the bin supervisor should do with a currency check result.

    - `message`: stderr text to emit, or None to stay silent.
    - `hard_fail`: a confirmed-stale CLAUDE install (both builds known and
      mismatched) — the supervisor always exits. A confirmed-stale CODEX
      install is fail-soft (Codex auto-upgrades natively at session start),
      so it sets `gate_sensitive` instead.
    - `gate_sensitive`: currency unknown OR a confirmed-stale Codex install —
      the supervisor exits only when `LIVESPEC_CURRENCY_GATE=fail`.
    """

    message: str | None
    hard_fail: bool
    gate_sensitive: bool


def verify_currency() -> CurrencyVerdict:
    plugin_root = _plugin_root()
    if not _is_installed_plugin_cache_path(plugin_root=plugin_root):
        return CurrencyVerdict(
            message=_CHECKOUT_MODE_MESSAGE, hard_fail=False, gate_sensitive=False
        )
    codex = _is_codex_installed_plugin_cache_path(plugin_root=plugin_root)
    running_build_id = _running_build_id(plugin_root=plugin_root)
    expected_build_id = _expected_build_id(plugin_root=plugin_root)
    message = _currency_message(
        running_build_id=running_build_id,
        expected_build_id=expected_build_id,
        codex=codex,
    )
    if message is None:
        return CurrencyVerdict(message=None, hard_fail=False, gate_sensitive=False)
    confirmed_stale = running_build_id is not None and expected_build_id is not None
    hard_fail = confirmed_stale and not codex
    return CurrencyVerdict(message=message, hard_fail=hard_fail, gate_sensitive=not hard_fail)


def _currency_message(
    *, running_build_id: str | None, expected_build_id: str | None, codex: bool
) -> str | None:
    if running_build_id is None or expected_build_id is None:
        return (
            "livespec plugin currency could not be verified; running build or pinned "
            "marketplace build is unknown. Set LIVESPEC_CURRENCY_GATE=fail to make "
            "this warning fatal in CI or dispatch.\n"
        )
    if running_build_id == expected_build_id:
        return None
    if codex:
        command = f"codex plugin marketplace upgrade {_MARKETPLACE_NAME}"
        restart = "restart the session"
    else:
        command = f"claude plugin update {_PLUGIN_NAME}@{_MARKETPLACE_NAME} --scope project"
        restart = "restart Claude Code (or run /reload-plugins)"
    return (
        f"livespec plugin '{_PLUGIN_NAME}' is stale: running build {running_build_id} does not "
        f"match pinned release build {expected_build_id}. Run `{command}` and {restart}.\n"
    )
