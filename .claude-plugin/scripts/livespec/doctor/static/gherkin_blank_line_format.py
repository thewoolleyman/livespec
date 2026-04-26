"""gherkin-blank-line-format static check: gherkin-style scenario blocks follow
the blank-line discipline in the spec.

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError(
            "livespec/doctor/static/gherkin_blank_line_format: not yet implemented",
        ),
    )
