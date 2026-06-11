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
"""Config/manifest loading for the revise render lifecycle.

Extracted from `_revise_render.py` so that file stays under the
250-LLOC hard ceiling enforced by
`livespec_dev_tooling.checks.file_lloc`. Holds the
`.livespec.jsonc` + active-template `spec_files` manifest loaders
the render stage composes against:

- `_load_spec_files` — resolve the active template and surface its
  `spec_files` manifest, degrading to `None` on every resolution
  failure (mirrors `doctor/static/_template_manifest.py`'s loader;
  duplicated because the layered-architecture import-linter
  contract treats `commands` and `doctor` as independent siblings
  that cannot import each other).
- `_load_render_argv` — surface the project-declared
  `render_commands.diagram_source` argv, failing with
  `PreconditionError` (exit 3) when a diagram_source write has no
  render command to run (per `contracts.md` §".livespec.jsonc
  render-commands shape").
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.io import IOResult

from livespec.errors import LivespecError, PreconditionError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.template_config import SpecFileDecl
from livespec.validate.livespec_config import validate_livespec_config
from livespec.validate.template_config import validate_template_config

__all__: list[str] = ["_load_render_argv", "_load_spec_files"]


_SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"
_TEMPLATE_CONFIG_SCHEMA_PATH = _SCHEMAS_DIR / "template_config.schema.json"
_LIVESPEC_CONFIG_SCHEMA_PATH = _SCHEMAS_DIR / "livespec_config.schema.json"
# parents[0]=commands/, [1]=livespec/, [2]=scripts/, [3]=.claude-plugin/
_BUNDLE_ROOT = Path(__file__).resolve().parents[3]
_BUILTIN_TEMPLATES_DIR = _BUNDLE_ROOT / "specification-templates"
_BUILTIN_TEMPLATE_NAMES = frozenset({"livespec", "livespec-with-diagrams", "minimal"})


def _load_json_file(*, path: Path) -> IOResult[Any, LivespecError]:
    """Read + JSONC-parse one file on the IO track."""
    return fs.read_text(path=path).bind(
        lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
    )


def _resolve_template_dir(*, template_value: str, project_root: Path) -> Path | None:
    """Resolve a `.livespec.jsonc` `template` value to a directory, or None."""
    if template_value in _BUILTIN_TEMPLATE_NAMES:
        return _BUILTIN_TEMPLATES_DIR / template_value
    candidate = (project_root / template_value).resolve()
    if candidate.is_dir() and (candidate / "template.json").is_file():
        return candidate
    return None


def _load_spec_files(
    *,
    project_root: Path,
) -> IOResult[dict[str, SpecFileDecl] | None, LivespecError]:
    """Load the active template's spec_files manifest, degrading to None."""
    return (
        _load_json_file(path=project_root / ".livespec.jsonc")
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
    return _load_json_file(path=template_dir / "template.json").bind(
        lambda payload: _load_json_file(path=_TEMPLATE_CONFIG_SCHEMA_PATH).bind(
            lambda schema: IOResult.from_result(  # pyright: ignore[reportArgumentType]
                validate_template_config(payload=payload, schema=schema),
            ).map(lambda cfg: cfg.spec_files),
        ),
    )


def _load_render_argv(*, project_root: Path) -> IOResult[list[str], LivespecError]:
    """Load `.livespec.jsonc` `render_commands.diagram_source` or fail.

    Per `contracts.md` §".livespec.jsonc render-commands shape":
    projects whose active template declares any `diagram_source`
    entry MUST declare the render command; a revise pass writing
    diagram source without one is a precondition failure (exit 3),
    BEFORE any tree mutation.
    """
    return (
        _load_json_file(path=project_root / ".livespec.jsonc")
        .bind(
            lambda payload: _load_json_file(path=_LIVESPEC_CONFIG_SCHEMA_PATH).bind(
                lambda schema: IOResult.from_result(  # pyright: ignore[reportArgumentType]
                    validate_livespec_config(payload=payload, schema=schema),
                ),
            ),
        )
        .bind(lambda config: _require_diagram_source_argv(config=config))
    )


def _require_diagram_source_argv(*, config: Any) -> IOResult[list[str], LivespecError]:
    """Surface `render_commands.diagram_source` or PreconditionError."""
    render_argv = config.render_commands.diagram_source
    if render_argv is None:
        return IOResult.from_failure(
            PreconditionError(
                "revise: the payload writes diagram_source content but "
                ".livespec.jsonc declares no render_commands.diagram_source "
                "(required per contracts.md §'.livespec.jsonc "
                "render-commands shape')",
            ),
        )
    return IOResult.from_value(render_argv)
