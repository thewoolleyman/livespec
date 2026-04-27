"""bcp14-keyword-wellformedness static check: BCP-14 keywords (MUST, SHOULD, MAY,
etc.) appear only in the canonical positions defined by the spec.

Phase 2 stub.
"""

from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError(
            "livespec/doctor/static/bcp14_keyword_wellformedness: not yet implemented",
        ),
    )
