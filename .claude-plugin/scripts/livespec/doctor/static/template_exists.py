"""template-exists static check.

Verifies the resolved template directory exists and contains
template.json (the contract from PROPOSAL §"Template resolution
contract" lines 1467-1474, deferred-deeper-validation rule).

Inspects DoctorContext.template_load_status (set by the
orchestrator's pre-check resolution per v014 N3 bootstrap
lenience):

- "ok"             → pass
- "absent"         → fail (template path doesn't exist)
- "malformed"      → fail (template path exists but isn't a
                     directory, or template.json is malformed)
- "schema_invalid" → fail (template.json fails schema validation)

Main-spec-tree-only (orchestrator-owned applicability table per
PROPOSAL line 2534-2538). Sub-spec trees skip this check.
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


SLUG: CheckId = CheckId("doctor-template-exists")


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    spec_root_str = str(ctx.spec_root)
    match ctx.template_load_status:
        case "ok":
            return IOSuccess(
                Finding(
                    check_id=SLUG,
                    status="pass",
                    message=f"template directory exists: {ctx.template_root}",
                    path=None,
                    line=None,
                    spec_root=spec_root_str,
                ),
            )
        case "absent":
            return IOSuccess(
                Finding(
                    check_id=SLUG,
                    status="fail",
                    message=f"template path missing: {ctx.template_root}",
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
                    message=f"template.json malformed under {ctx.template_root}",
                    path="template.json",
                    line=None,
                    spec_root=spec_root_str,
                ),
            )
        case "schema_invalid":
            return IOSuccess(
                Finding(
                    check_id=SLUG,
                    status="fail",
                    message=f"template.json fails schema validation under {ctx.template_root}",
                    path="template.json",
                    line=None,
                    spec_root=spec_root_str,
                ),
            )
