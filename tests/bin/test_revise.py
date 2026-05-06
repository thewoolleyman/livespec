"""Per-wrapper coverage test for bin/revise.py.

Asserts the shebang wrapper threads its main()'s return value
into `raise SystemExit(<code>)`, per the canonical 6-statement
wrapper shape (SPECIFICATION/constraints.md §"Shebang-wrapper
contract").
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_revise_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/revise.py` calls livespec.commands.revise.main() and forwards exit."""
    wrapper_runner("revise.py", "livespec.commands.revise", 0)
