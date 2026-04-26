"""Static-phase doctor supervisor.

Phase 2 stub. The real supervisor runs every registered check, derives
the exit code per the doctor static-phase output contract (style doc
§"Doctor static-phase exit-code derivation"), and writes
`{"findings": [...]}` to stdout. Implementation lands in Phase 3+.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["main", "run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/doctor/run_static: not yet implemented"),
    )


def main() -> int:
    return PreconditionError.exit_code
