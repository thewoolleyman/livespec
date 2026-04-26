"""version-contiguity static check: the vNNN version sequence is contiguous
with no gaps.

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/doctor/static/version_contiguity: not yet implemented"),
    )
