"""Per-wrapper coverage test for bin/critique.py.

Asserts the shebang wrapper threads its main()'s return value
into `raise SystemExit(<code>)`, per the canonical 6-statement
wrapper shape.

`wrapper_runner` (in conftest.py) stubs `_bootstrap.bootstrap`
and `livespec.commands.critique.main` so we exercise only the
wrapper plumbing — the real critique command lives one layer
deeper and is driven by its own tests.
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_critique_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/critique.py` calls livespec.commands.critique.main() and forwards exit."""
    wrapper_runner("critique.py", "livespec.commands.critique", 0)
