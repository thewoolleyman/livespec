"""template-files-present static check.

Verifies the active template's required prompt files exist under
its template-root: prompts/seed.md, prompts/propose-change.md,
prompts/revise.md, prompts/critique.md (per PROPOSAL §"Templates"
line 1409-1411).

Phase 3 minimum-viable: hardcoded list of the four required
prompts. Phase 7 widens to also verify the optional
doctor-llm-{objective,subjective}-checks prompts when
template.json's corresponding fields are non-null.

Main-spec-tree-only (orchestrator-owned applicability — same as
template_exists).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId

__all__: list[str] = [
    "SLUG",
    "run",
]


SLUG: CheckId = CheckId("doctor-template-files-present")


_REQUIRED_PROMPTS: Sequence[str] = (
    "prompts/seed.md",
    "prompts/propose-change.md",
    "prompts/revise.md",
    "prompts/critique.md",
)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    spec_root_str = str(ctx.spec_root)
    if ctx.template_load_status != "ok":
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="skipped",
                message=(f"skipped: template not loaded (status={ctx.template_load_status})"),
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    missing = _missing_prompts(template_root=ctx.template_root)
    if missing:
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="fail",
                message=f"required prompt files missing: {', '.join(missing)}",
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    return IOSuccess(
        Finding(
            check_id=SLUG,
            status="pass",
            message="all required template prompt files present",
            path=None,
            line=None,
            spec_root=spec_root_str,
        ),
    )


def _missing_prompts(*, template_root: Path) -> list[str]:
    """Return the relative paths of any missing required prompt files."""
    return [rel for rel in _REQUIRED_PROMPTS if not (template_root / rel).is_file()]
