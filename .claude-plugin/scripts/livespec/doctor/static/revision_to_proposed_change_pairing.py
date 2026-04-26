"""revision-to-proposed-change-pairing static check: each version snapshot has
matching `proposed_changes/` entries documenting how it was produced.

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError(
            "livespec/doctor/static/revision_to_proposed_change_pairing: not yet implemented",
        ),
    )
