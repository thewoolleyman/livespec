"""Static-phase doctor check: template_exists.

Per Plan Phase 3 + + livespec_config.schema.json §"template":
this check asserts that the `.livespec.jsonc` `template` field
resolves to either a built-in template name (one of
`{livespec, minimal}`) or a path-as-string to a custom template
directory present on disk relative to the project root.

Cycle 134 lands the success arm for the built-in branch.
Subsequent cycles add the failure arm (unknown name, missing
custom-template directory) and the on-disk path-resolution
branch under outside-in pressure.
"""

from __future__ import annotations

from typing import Any

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-template-exists"
BUILTIN_TEMPLATES: frozenset[str] = frozenset({"livespec", "minimal"})


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="template resolves to a known builtin or existing path",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _fail_finding(*, ctx: DoctorContext, template_value: str) -> Finding:
    """Construct a fail-status Finding naming the offending template value."""
    return Finding(
        check_id=SLUG,
        status="fail",
        message=f"template '{template_value}' is neither a builtin nor an existing path",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _evaluate(*, ctx: DoctorContext, parsed: Any) -> IOResult[Finding, LivespecError]:
    """Evaluate the parsed config against the template-exists rule.

    Cycle 135 splits the evaluation into two arms: the
    `template` value is checked against BUILTIN_TEMPLATES and
    yields a pass-Finding on hit; otherwise (unknown name)
    yields a fail-Finding naming the offending value. The
    on-disk path-resolution branch lands in a subsequent cycle.
    """
    template_value = parsed.get("template")
    if template_value in BUILTIN_TEMPLATES:
        return IOSuccess(_pass_finding(ctx=ctx))
    return IOSuccess(_fail_finding(ctx=ctx, template_value=str(template_value)))


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the template-exists check against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc`, parses it, and
    evaluates the `template` field. The success arm yields
    IOSuccess(Finding(status='pass')); failure arms land in
    subsequent cycles.
    """
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
        .bind(lambda parsed: _evaluate(ctx=ctx, parsed=parsed))
    )
