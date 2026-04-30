"""Per-wrapper coverage test for bin/prune_history.py.

Asserts the shebang wrapper threads its main()'s return value
into `raise SystemExit(<code>)`, per the canonical 6-statement
wrapper shape (style doc §"Wrapper shape" / PROPOSAL.md
§"`prune-history`").
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_prune_history_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/prune_history.py` calls livespec.commands.prune_history.main() and forwards exit."""
    wrapper_runner("prune_history.py", "livespec.commands.prune_history", 0)
