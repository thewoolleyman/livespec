"""Shared template-value resolution — single source of truth.

The built-in template name set and the custom-template on-disk
path-resolution rule shared by `commands/resolve_template.py`,
`doctor/static/template_exists.py`, and
`doctor/static/_template_manifest.py`. Keeping all three resolvers
behind this one helper is what stops them drifting: historically
`template_exists` carried its own `{livespec, minimal}` frozenset
and omitted both the `livespec-with-diagrams` built-in and the
custom-path branch, so it rejected configs the authoritative
resolver accepted (livespec-kfjd).

Resolution is a pure classification over filesystem state — the
`.is_dir()` / `.is_file()` probes mirror the inline checks the three
former copies each performed. A built-in name or a project-relative
directory carrying `template.json` yields `Success(<dir>)`; anything
else yields `Failure(TemplateResolutionFailure)` naming the probed
path and which arm failed. Callers map that onto their own shape:
`resolve_template` to a `PreconditionError` (exit 3), the manifest
loader to `None` (degrade), the doctor check to a pass/fail
`Finding`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from returns.result import Failure, Result, Success

__all__: list[str] = [
    "BUILTIN_TEMPLATES_DIR",
    "BUILTIN_TEMPLATE_NAMES",
    "TemplateResolutionFailure",
    "resolve_template_value",
]


# parents[0]=livespec/, [1]=scripts/, [2]=.claude-plugin/ — the bundle
# root carrying the built-in `specification-templates/` tree (the same
# root commands/resolve_template.py and doctor/static/_template_manifest.py
# each derive at their own nesting depth).
_BUNDLE_ROOT = Path(__file__).resolve().parents[2]
BUILTIN_TEMPLATES_DIR: Path = _BUNDLE_ROOT / "specification-templates"
BUILTIN_TEMPLATE_NAMES: frozenset[str] = frozenset(
    {"livespec", "livespec-with-diagrams", "minimal"},
)


@dataclass(frozen=True, kw_only=True, slots=True)
class TemplateResolutionFailure:
    """Why a non-built-in `template` value failed to resolve to a dir.

    `candidate` is the absolute project-relative path that was probed;
    `reason` discriminates the two failure arms so callers that care
    (e.g. `resolve_template`'s two distinct exit-3 messages) can
    branch, while callers that only need the binary "resolved?" answer
    ignore it.
    """

    candidate: Path
    reason: Literal["missing_dir", "missing_manifest"]


def resolve_template_value(
    *,
    value: str,
    project_root: Path,
) -> Result[Path, TemplateResolutionFailure]:
    """Resolve a `template` value to a template directory.

    A built-in name (`BUILTIN_TEMPLATE_NAMES`) resolves to
    `<bundle>/specification-templates/<name>` unconditionally. Any
    other string is treated as a path relative to `project_root` and
    must (a) be a directory and (b) contain `template.json`; the two
    failure arms surface as `TemplateResolutionFailure` with
    `reason="missing_dir"` / `reason="missing_manifest"`.
    """
    if value in BUILTIN_TEMPLATE_NAMES:
        return Success(BUILTIN_TEMPLATES_DIR / value)
    candidate = (project_root / value).resolve()
    if not candidate.is_dir():
        return Failure(
            TemplateResolutionFailure(candidate=candidate, reason="missing_dir"),
        )
    if not (candidate / "template.json").is_file():
        return Failure(
            TemplateResolutionFailure(candidate=candidate, reason="missing_manifest"),
        )
    return Success(candidate)
