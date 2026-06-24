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
"""Shared active-template manifest loader for manifest-driven checks.

Per `SPECIFICATION/spec.md` §"Template manifest" → "Heading-coverage
and doctor-static rewiring": the manifest-aware static check
`template_files_present` consults the active template's `spec_files`
manifest. This private sibling module holds the one shared
resolution railway:

1. read `<project_root>/.livespec.jsonc` and take its `template`
   value (defaulting to the built-in `livespec` name);
2. resolve the value to a template directory via the shared
   `livespec.templates.resolve_template_value` — built-in names map
   into the bundled `specification-templates/` tree, other strings
   resolve as project-root-relative paths that must contain
   `template.json`;
3. read + schema-validate `template.json` and surface
   `TemplateConfig.spec_files`.

The loader DEGRADES TO `IOSuccess(None)` ("no manifest available")
on every resolution failure — missing/unparseable `.livespec.jsonc`,
unknown template value, missing/invalid `template.json`, or a v1
template (which legitimately has no manifest). Config-validity
failure modes are owned by their dedicated checks
(`livespec_jsonc_valid`, `template_exists`); manifest consumers
only need the binary "is a v2 manifest available" answer so they
can fall back to their v1 behavior.

`is_main_spec_root` mirrors the orchestrator's tree enumeration in
`doctor/run_static.py`: the main tree is `<project_root>/SPECIFICATION`;
everything else (sub-spec trees at `<main>/templates/<name>/`) carries
no template manifest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.io import IOResult

from livespec import templates
from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.template_config import SpecFileDecl
from livespec.validate.template_config import validate_template_config

__all__: list[str] = ["is_main_spec_root", "load_active_template_spec_files"]


_SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"
_TEMPLATE_CONFIG_SCHEMA_PATH = _SCHEMAS_DIR / "template_config.schema.json"


def is_main_spec_root(*, ctx: DoctorContext) -> bool:
    """Whether `ctx` targets the main spec tree (vs a sub-spec tree).

    Mirrors `run_static._orchestrate`'s main-tree construction
    (`<project_root>/SPECIFICATION`). Sub-spec trees live under
    `<main>/templates/<name>/` and carry no template manifest.
    """
    return ctx.spec_root.resolve() == (ctx.project_root / "SPECIFICATION").resolve()


def _resolve_template_dir(*, template_value: str, project_root: Path) -> Path | None:
    """Resolve a `.livespec.jsonc` `template` value to a directory, or None.

    Delegates to the shared `livespec.templates.resolve_template_value`
    (the single built-in-set + custom-path source of truth shared with
    `commands/resolve_template.py` and `doctor/static/template_exists.py`).
    An unresolvable value yields `None` so the caller degrades to
    "no manifest" rather than surfacing a railway failure.
    """
    return templates.resolve_template_value(
        value=template_value,
        project_root=project_root,
    ).value_or(None)


def load_active_template_spec_files(
    *,
    project_root: Path,
) -> IOResult[dict[str, SpecFileDecl] | None, LivespecError]:
    """Load the active template's `spec_files` manifest, or None.

    `IOSuccess(<manifest dict>)` for a resolvable, schema-valid v2
    template; `IOSuccess(None)` for v1 templates and for EVERY
    resolution failure (the trailing `lash` folds the whole railway's
    failure track to the no-manifest answer — see the module
    docstring for why).
    """
    return (
        fs.read_text(path=project_root / ".livespec.jsonc")
        .bind(
            lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(
            lambda parsed: _spec_files_for_config(
                parsed=parsed,
                project_root=project_root,
            ),
        )
        .lash(lambda _err: IOResult.from_value(None))  # pyright: ignore[reportArgumentType]
    )


def _spec_files_for_config(
    *,
    parsed: Any,
    project_root: Path,
) -> IOResult[dict[str, SpecFileDecl] | None, LivespecError]:
    """Resolve the parsed config's template and read its manifest."""
    template_value = "livespec"
    if isinstance(parsed, dict):
        raw_template = parsed.get("template", "livespec")
        if isinstance(raw_template, str):
            template_value = raw_template
    template_dir = _resolve_template_dir(
        template_value=template_value,
        project_root=project_root,
    )
    if template_dir is None:
        return IOResult.from_value(None)
    return (
        fs.read_text(path=template_dir / "template.json")
        .bind(
            lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(lambda payload: _validated_spec_files(payload=payload))
    )


def _validated_spec_files(
    *,
    payload: Any,
) -> IOResult[dict[str, SpecFileDecl] | None, LivespecError]:
    """Schema-validate a template.json payload and surface `spec_files`."""
    return (
        fs.read_text(path=_TEMPLATE_CONFIG_SCHEMA_PATH)
        .bind(
            lambda schema_text: IOResult.from_result(jsonc.loads(text=schema_text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(
            lambda schema: IOResult.from_result(  # pyright: ignore[reportArgumentType]
                validate_template_config(payload=payload, schema=schema),
            ).map(lambda cfg: cfg.spec_files),
        )
    )
