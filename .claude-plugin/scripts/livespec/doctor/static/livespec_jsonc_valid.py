"""livespec-jsonc-valid static check.

Verifies `.livespec.jsonc`'s parse + schema-validation status as
recorded by the orchestrator under v014 N3 bootstrap lenience.
The orchestrator builds DoctorContext with best-effort defaults
even when the config is absent/malformed/schema-invalid; this
check inspects the recorded status and emits the appropriate
Finding.

Per PROPOSAL §"Bootstrap lenience (v014 N3)" lines 2554-2592:
- "ok"             → pass
- "absent"         → skipped ("no .livespec.jsonc to validate")
- "malformed"      → fail (parse error; user fixes manually)
- "schema_invalid" → fail (schema violation; user fixes)
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId

__all__: list[str] = [
    "SLUG",
    "run",
]


SLUG: CheckId = CheckId("doctor-livespec-jsonc-valid")


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    spec_root_str = str(ctx.spec_root)
    match ctx.config_load_status:
        case "ok":
            return IOSuccess(
                Finding(
                    check_id=SLUG,
                    status="pass",
                    message=".livespec.jsonc parses and validates against schema",
                    path=".livespec.jsonc",
                    line=None,
                    spec_root=spec_root_str,
                ),
            )
        case "absent":
            return IOSuccess(
                Finding(
                    check_id=SLUG,
                    status="skipped",
                    message="no .livespec.jsonc to validate (defaults apply)",
                    path=None,
                    line=None,
                    spec_root=spec_root_str,
                ),
            )
        case "malformed":
            return IOSuccess(
                Finding(
                    check_id=SLUG,
                    status="fail",
                    message=".livespec.jsonc is malformed JSONC; fix or delete",
                    path=".livespec.jsonc",
                    line=None,
                    spec_root=spec_root_str,
                ),
            )
        case "schema_invalid":
            return IOSuccess(
                Finding(
                    check_id=SLUG,
                    status="fail",
                    message=".livespec.jsonc fails schema validation; fix or delete",
                    path=".livespec.jsonc",
                    line=None,
                    spec_root=spec_root_str,
                ),
            )
