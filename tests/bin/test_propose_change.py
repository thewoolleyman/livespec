"""Per-wrapper coverage test for bin/propose_change.py.

Asserts the shebang wrapper threads its main()'s return value
into `raise SystemExit(<code>)`, per the canonical 6-statement
wrapper shape (style doc §"Wrapper shape" / PROPOSAL.md
§"`propose-change`").

`wrapper_runner` (in conftest.py) stubs `_bootstrap.bootstrap`
and `livespec.commands.propose_change.main` so we exercise only
the wrapper plumbing — the real propose-change command lives one
layer deeper and is driven by its own tests.
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_propose_change_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/propose_change.py` calls livespec.commands.propose_change.main() and forwards exit."""
    wrapper_runner("propose_change.py", "livespec.commands.propose_change", 0)
