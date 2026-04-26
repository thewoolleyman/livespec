"""template-files-present static check: required template files exist
(`template.json`, `prompts/*`, `specification-template/*`).

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/doctor/static/template_files_present: not yet implemented"),
    )
