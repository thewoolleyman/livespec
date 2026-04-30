"""Static-phase doctor check: livespec_jsonc_valid.

Per Plan Phase 3 line 1596-1602 + PROPOSAL.md §"`doctor` →
Static-phase checks": this check asserts that the project's
`.livespec.jsonc` config file exists and parses as valid JSONC.
First-of-eight in the Phase-3 minimum-subset registry.

The check composes the `fs.read_text` -> `jsonc.loads` railway
against `<project_root>/.livespec.jsonc`; on success it yields
`IOSuccess(Finding(status='pass', ...))`. Failure arms are
added by subsequent cycles under outside-in pressure
(missing-file -> status='fail', malformed -> status='fail').
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-livespec-jsonc-valid"


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check.

    Held out as a helper so future cycles can add the matching
    fail-status helpers (missing-file, malformed-JSONC) under
    one Finding-construction surface per failure mode.
    """
    return Finding(
        check_id=SLUG,
        status="pass",
        message="livespec config parses as valid JSONC",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the livespec-jsonc-valid check against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc` and parses it as
    JSONC. On success yields `IOSuccess(Finding(status='pass'))`;
    cycle 131 lands the success arm only — the failure arms
    (missing config, malformed JSONC) land under outside-in
    consumer pressure as subsequent cycles add their tests.
    """
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
        .bind(lambda _parsed: IOSuccess(_pass_finding(ctx=ctx)))
    )
