# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Static-phase doctor check: template_exists.

Per livespec_config.schema.json §"template": this check asserts
that the `.livespec.jsonc` `template` field resolves to either a
built-in template name (one of `{livespec, livespec-with-diagrams,
minimal}`) or a path-as-string to a custom template directory
present on disk relative to the project root and carrying a
`template.json`.

Resolution is delegated to `livespec.templates.resolve_template_value`
— the single source of truth shared with `commands/resolve_template.py`
and `doctor/static/_template_manifest.py` — so the built-in set and the
custom-path rule cannot drift between the three resolvers (livespec-kfjd).
A resolvable value yields a pass-Finding; an unknown name or a missing
custom-template directory / `template.json` yields a fail-Finding naming
the offending value.
"""

from __future__ import annotations

from typing import Any

from returns.io import IOResult, IOSuccess
from returns.pipeline import is_successful

from livespec import templates
from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-template-exists")


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="template resolves to a known builtin or existing path",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _fail_finding(*, ctx: DoctorContext, template_value: str) -> Finding:
    """Construct a fail-status Finding naming the offending template value."""
    return Finding(
        check_id=SLUG,
        status="fail",
        message=f"template '{template_value}' is neither a builtin nor an existing path",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _evaluate(*, ctx: DoctorContext, parsed: Any) -> IOResult[Finding, LivespecError]:
    """Evaluate the parsed config against the template-exists rule.

    Delegates to `livespec.templates.resolve_template_value`: a
    built-in name or a project-relative directory carrying
    `template.json` resolves and yields a pass-Finding; an unknown
    name or a missing custom-template directory / `template.json`
    fails resolution and yields a fail-Finding naming the offending
    value.
    """
    template_value = parsed.get("template")
    resolution = templates.resolve_template_value(
        value=str(template_value),
        project_root=ctx.project_root,
    )
    if is_successful(resolution):
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
        .bind(
            lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(lambda parsed: _evaluate(ctx=ctx, parsed=parsed))
    )
