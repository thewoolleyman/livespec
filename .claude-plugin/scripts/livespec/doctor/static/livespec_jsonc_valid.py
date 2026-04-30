"""Static-phase doctor check: livespec_jsonc_valid.

Per Plan Phase 3 line 1596-1602 + PROPOSAL.md §"`doctor` →
Static-phase checks": this check asserts that the project's
`.livespec.jsonc` config file exists and parses as valid JSONC.
First-of-eight in the Phase-3 minimum-subset registry.

The check composes the `fs.read_text` -> `jsonc.loads` railway
against `<project_root>/.livespec.jsonc`; on success it yields
`IOSuccess(Finding(status='pass', ...))`. On expected-domain
failures (file missing, unreadable, or malformed JSONC) the
railway's IOFailure track is folded back into IOSuccess
carrying a fail-status Finding so the orchestrator's stdout
contract is uniform across pass and fail outcomes (the
"check ran and detected a violation" semantics in
finding.schema.json's status enum).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-livespec-jsonc-valid"


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="livespec config parses as valid JSONC",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _missing_finding(*, ctx: DoctorContext, config_path: Path) -> Finding:
    """Construct the canonical fail-status Finding for a missing/unreadable config.

    Maps fs.read_text's PreconditionError (FileNotFoundError /
    other OSError) into a fail-status Finding with the config
    path embedded so the orchestrator's stdout output names the
    exact file the user must create.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message="livespec config file is missing or unreadable",
        path=str(config_path),
        line=None,
        spec_root=str(ctx.spec_root),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the livespec-jsonc-valid check against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc` and parses it as
    JSONC. On success yields `IOSuccess(Finding(status='pass'))`;
    on missing/unreadable config the IOFailure track is recovered
    via `.lash(...)` into `IOSuccess(Finding(status='fail'))` so
    every outcome the check produces is a Finding rather than a
    railway-level error. Future cycles add the malformed-JSONC
    failure arm by extending the recovery to discriminate
    PreconditionError vs ValidationError.
    """
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
        .bind(lambda _parsed: IOSuccess(_pass_finding(ctx=ctx)))
        .lash(lambda _err: IOSuccess(_missing_finding(ctx=ctx, config_path=config_path)))
    )
