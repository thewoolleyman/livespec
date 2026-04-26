"""livespec-jsonc-valid static check: parses `.livespec.jsonc` and validates against
its schema (with v014 N3 bootstrap-lenience for absent/malformed/schema-invalid).

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/doctor/static/livespec_jsonc_valid: not yet implemented"),
    )
