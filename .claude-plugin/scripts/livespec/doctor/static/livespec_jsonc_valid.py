"""Static-phase doctor check: livespec_jsonc_valid.

Per Plan Phase 3 line 1596-1602 + PROPOSAL.md §"`doctor` →
Static-phase checks": this check asserts that the project's
`.livespec.jsonc` config file exists and parses as valid JSONC.
First-of-eight in the Phase-3 minimum-subset registry.

The check composes the `fs.read_text` -> `jsonc.loads` railway
against `<project_root>/.livespec.jsonc`; on success it yields
`IOSuccess(Finding(status='pass', ...))`. On expected-domain
failures the railway's IOFailure track is folded back into
IOSuccess carrying a fail-status Finding so the orchestrator's
stdout contract is uniform across pass and fail outcomes (the
"check ran and detected a violation" semantics in
finding.schema.json's status enum). Two distinct fail messages
discriminate the two failure modes:
  - PreconditionError (file missing / unreadable) ->
    "livespec config file is missing or unreadable"
  - ValidationError (malformed JSONC) ->
    "livespec config is not valid JSONC"
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError, ValidationError
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


def _fail_finding(*, ctx: DoctorContext, config_path: Path, message: str) -> Finding:
    """Construct a fail-status Finding for `livespec_jsonc_valid` with `message`.

    Embeds the config path so the orchestrator's stdout output
    names the exact file the user must create or fix.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=message,
        path=str(config_path),
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _recover(
    *,
    error: LivespecError,
    ctx: DoctorContext,
    config_path: Path,
) -> IOResult[Finding, LivespecError]:
    """Map an expected-domain error into IOSuccess(fail-Finding).

    Discriminates ValidationError (jsonc.loads failure) from
    every other LivespecError (PreconditionError from
    fs.read_text). The two-message split lets the user see at
    a glance whether the file is missing or merely malformed.
    """
    if isinstance(error, ValidationError):
        return IOSuccess(
            _fail_finding(
                ctx=ctx,
                config_path=config_path,
                message="livespec config is not valid JSONC",
            ),
        )
    return IOSuccess(
        _fail_finding(
            ctx=ctx,
            config_path=config_path,
            message="livespec config file is missing or unreadable",
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the livespec-jsonc-valid check against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc` and parses it as
    JSONC. On success yields `IOSuccess(Finding(status='pass'))`;
    on PreconditionError (missing/unreadable) or ValidationError
    (malformed) the IOFailure track is recovered via `.lash(...)`
    into `IOSuccess(Finding(status='fail'))` with a message
    discriminating which mode tripped.
    """
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
        .bind(lambda _parsed: IOSuccess(_pass_finding(ctx=ctx)))
        .lash(lambda err: _recover(error=err, ctx=ctx, config_path=config_path))
    )
