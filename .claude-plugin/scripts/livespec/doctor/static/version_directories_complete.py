"""version-directories-complete static check: each `history/vNNN/` carries
the expected children (snapshot files + `proposed_changes/`).

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError(
            "livespec/doctor/static/version_directories_complete: not yet implemented",
        ),
    )
