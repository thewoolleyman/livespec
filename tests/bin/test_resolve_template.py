"""Per-wrapper coverage test for bin/resolve_template.py.

Asserts the shebang wrapper threads its main()'s return value
into `raise SystemExit(<code>)`, per the canonical 6-statement
wrapper shape (SPECIFICATION/constraints.md §"Shebang-wrapper
contract" — the wrapper has no room for path-computation logic;
the heavy lifting lives in `livespec.commands.resolve_template`).

`wrapper_runner` (in conftest.py) stubs `_bootstrap.bootstrap`
and `livespec.commands.resolve_template.main` so we exercise
only the wrapper plumbing — the real resolve_template command
lives one layer deeper and is driven by its own tests.
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_resolve_template_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/resolve_template.py` calls livespec.commands.resolve_template.main() and forwards exit."""
    wrapper_runner("resolve_template.py", "livespec.commands.resolve_template", 0)
