"""proposed-changes-and-history-dirs static check: spec_root carries
the expected `proposed_changes/` and `history/` directories.

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError(
            "livespec/doctor/static/proposed_changes_and_history_dirs: not yet implemented",
        ),
    )
