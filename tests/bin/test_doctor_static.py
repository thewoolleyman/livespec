"""Per-wrapper coverage test for bin/doctor_static.py.

Asserts the shebang wrapper threads its main()'s return value
into `raise SystemExit(<code>)`, per the canonical 6-statement
wrapper shape (SPECIFICATION/constraints.md §"Shebang-wrapper
contract").

Doctor's supervisor lives at `livespec/doctor/run_static.py`
(not `livespec/commands/doctor.py`) — doctor is the only
sub-command whose Python lives outside `commands/`.
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_doctor_static_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/doctor_static.py` calls livespec.doctor.run_static.main() and forwards exit."""
    wrapper_runner("doctor_static.py", "livespec.doctor.run_static", 0)
