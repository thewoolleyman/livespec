"""Per-wrapper coverage test for bin/next.py.

Asserts the shebang wrapper threads its main()'s return value
into `raise SystemExit(<code>)`, per the canonical 6-statement
wrapper shape.

`wrapper_runner` (in conftest.py) stubs `_bootstrap.bootstrap`
and `livespec.commands.next.main` so we exercise only the
wrapper plumbing — the real next command lives one layer
deeper and is driven by its own tests under
`tests/livespec/commands/test_next.py`.
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_next_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/next.py` calls livespec.commands.next.main() and forwards exit."""
    wrapper_runner("next.py", "livespec.commands.next", 0)
