"""template-exists static check: the active template's resolved path exists on disk.

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/doctor/static/template_exists: not yet implemented"),
    )
