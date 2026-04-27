"""anchor-reference-resolution static check: every markdown anchor reference
(e.g., `[link](#anchor)`) resolves to a real anchor target in the spec.

Phase 2 stub.
"""

from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError(
            "livespec/doctor/static/anchor_reference_resolution: not yet implemented",
        ),
    )
