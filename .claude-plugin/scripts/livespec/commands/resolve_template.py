"""resolve-template helper: echoes the active template's resolved path to stdout.

Per PROPOSAL.md §"Template resolution contract" (lines 1424-1494,
v028 D1 corrected). Resolves the active template's absolute
directory and writes it as one line of stdout (POSIX path + `\n`).

Two flag-driven flows:

- **Default flow** (no `--template`): walk upward from
  `--project-root` for `.livespec.jsonc`; parse it; validate
  against `livespec_config.schema.json`; resolve the parsed
  `template` field. Used by every non-seed sub-command.
- **Pre-seed flow** (`--template <value>` supplied; v017 Q2):
  bypass `.livespec.jsonc` lookup; resolve `<value>` directly.
  Built-in names (`livespec`, `minimal`) resolve to bundle-internal
  `.claude-plugin/specification-templates/<name>/`; other strings
  are paths relative to `--project-root`. Used by `seed/SKILL.md`
  prose to find the seed prompt before the first `.livespec.jsonc`
  exists on disk.

Validation surface (per PROPOSAL.md line 1471-1474):
- Resolved path exists.
- Resolved path is a directory.
- Resolved path contains `template.json`.

Deeper validation (`template_format_version` match, prompt-file
presence, etc.) is the `template-exists` doctor static check's
responsibility, not this wrapper's.

Bundle-root derivation (v028 D1): `Path(__file__).resolve().parents[3]`
— from `.claude-plugin/scripts/livespec/commands/resolve_template.py`,
`parents[3]` is `.claude-plugin/`. The shebang wrapper at
`bin/resolve_template.py` has no room for path-computation logic
per the wrapper-shape contract; the path derivation happens here
in the implementation.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, NoReturn

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import (
    HelpRequested,
    LivespecError,
    PreconditionError,
)
from livespec.io.cli import parse_args
from livespec.io.fastjsonschema_facade import compile_schema
from livespec.io.fs import find_upward, path_exists, read_text
from livespec.io.structlog_facade import get_logger
from livespec.parse.jsonc import parse as parse_jsonc
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.validate import livespec_config as validate_livespec_config

__all__: list[str] = [
    "build_parser",
    "main",
    "run",
]


_LIVESPEC_JSONC = ".livespec.jsonc"
_TEMPLATE_JSON = "template.json"
_BUILT_IN_TEMPLATES = frozenset({"livespec", "minimal"})


def build_parser() -> argparse.ArgumentParser:
    """Pure factory for the resolve-template argparse parser.

    Constructs the parser with `exit_on_error=False` so the
    `livespec.io.cli.parse_args` boundary catches usage errors as
    `UsageError` instead of letting argparse `sys.exit`.
    """
    parser = argparse.ArgumentParser(
        prog="livespec resolve-template",
        description="Resolve the active template's absolute directory path; echo to stdout.",
        exit_on_error=False,
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root for `.livespec.jsonc` lookup (default: cwd).",
    )
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Pre-seed override (built-in name or path); skips `.livespec.jsonc` lookup.",
    )
    return parser


def _bundle_root() -> Path:
    """Return the `.claude-plugin/` directory of the installed plugin.

    Per PROPOSAL.md §"Template resolution contract" line 1465-1476
    (v028 D1): from this file's location at
    `.claude-plugin/scripts/livespec/commands/resolve_template.py`,
    `parents[0]` is `commands/`, `parents[1]` is `livespec/`,
    `parents[2]` is `scripts/`, `parents[3]` is `.claude-plugin/`.
    """
    return Path(__file__).resolve().parents[3]


def _schema_path() -> Path:
    """Return the path to `livespec_config.schema.json` inside the bundle."""
    return Path(__file__).resolve().parent.parent / "schemas" / "livespec_config.schema.json"


def run(*, argv: Sequence[str]) -> IOResult[Path, LivespecError]:
    """Railway entry: parse argv → resolve template → return path.

    Composition (left-to-right reading):

    1. `parse_args(parser=..., argv=...)` ships `Namespace` on
       success or `IOFailure(UsageError | HelpRequested)` on
       failure.
    2. `_resolve_from_namespace(ns)` either uses the explicit
       `--template` value or walks upward for `.livespec.jsonc`,
       parses + validates, and resolves the config's template.
    3. `_validate_resolved_path(candidate)` confirms the resolved
       path exists, is a directory, and contains `template.json`.
    """
    parser = build_parser()
    parsed = parse_args(parser=parser, argv=argv)
    return parsed.bind(_resolve_from_namespace)


def _resolve_from_namespace(
    namespace: argparse.Namespace,
) -> IOResult[Path, LivespecError]:
    """Branch on `--template`; resolve to candidate; validate."""
    project_root: Path = (
        namespace.project_root
        if namespace.project_root is not None
        else Path.cwd()
    )
    template_override: str | None = namespace.template

    if template_override is not None:
        return _resolve_value(
            template=template_override,
            project_root=project_root,
        )

    return _resolve_via_jsonc(project_root=project_root)


def _resolve_via_jsonc(*, project_root: Path) -> IOResult[Path, LivespecError]:
    """Walk upward, read `.livespec.jsonc`, validate, resolve template."""
    return (
        find_upward(start=project_root, name=_LIVESPEC_JSONC)
        .bind(lambda jsonc_path: read_text(path=jsonc_path))
        .bind(_parse_and_validate_config)
        .bind(
            lambda config: _resolve_value(
                template=config.template,
                project_root=project_root,
            ),
        )
    )


def _parse_and_validate_config(
    text: str,
) -> IOResult[LivespecConfig, LivespecError]:
    """Parse JSONC text, schema-validate, construct LivespecConfig.

    The schema dict is loaded and compiled inside this function (not
    module-level) so the impure I/O happens on the railway. The
    fastjsonschema cache (keyed on `$id`) ensures the actual compile
    runs at most once per process across repeated invocations.
    """
    parsed = parse_jsonc(text=text)
    match parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(config_dict):
            return _load_schema_and_validate(payload=config_dict)
        case _:
            assert_never(parsed)


def _load_schema_and_validate(
    *,
    payload: dict[str, Any],
) -> IOResult[LivespecConfig, LivespecError]:
    """Read livespec_config.schema.json from the bundle, compile, validate payload."""
    return (
        read_text(path=_schema_path())
        .bind(lambda schema_text: _compile_and_validate(
            schema_text=schema_text,
            payload=payload,
        ))
    )


def _compile_and_validate(
    *,
    schema_text: str,
    payload: dict[str, Any],
) -> IOResult[LivespecConfig, LivespecError]:
    """Parse schema JSONC, compile validator, run against payload."""
    schema_parsed = parse_jsonc(text=schema_text)
    match schema_parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(schema_dict):
            fast_validator = compile_schema(
                schema_id="livespec_config.schema.json",
                schema=schema_dict,
            )
            validator = validate_livespec_config.make_validator(
                fast_validator=fast_validator,
            )
            validated = validator(payload)
            match validated:
                case Failure(err):
                    return IOFailure(err)
                case Success(config):
                    return IOSuccess(config)
                case _:
                    assert_never(validated)
        case _:
            assert_never(schema_parsed)


def _resolve_value(
    *,
    template: str,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    """Map a template value (built-in name or path) to a validated absolute Path."""
    if template in _BUILT_IN_TEMPLATES:
        candidate = _bundle_root() / "specification-templates" / template
    else:
        candidate = (project_root / template).resolve()
    return _validate_resolved_path(candidate=candidate)


def _validate_resolved_path(*, candidate: Path) -> IOResult[Path, LivespecError]:
    """Confirm the candidate path exists and contains template.json."""
    return path_exists(path=candidate).bind(
        lambda exists: _confirm_dir_and_template_json(
            candidate=candidate,
            exists=exists,
        ),
    )


def _confirm_dir_and_template_json(
    *,
    candidate: Path,
    exists: bool,
) -> IOResult[Path, LivespecError]:
    """If candidate exists, also verify template.json is present."""
    if not exists:
        return IOFailure(
            PreconditionError(f"resolved template path missing: {candidate}"),
        )
    return path_exists(path=candidate / _TEMPLATE_JSON).bind(
        lambda has_template_json: _final_check(
            candidate=candidate,
            has_template_json=has_template_json,
        ),
    )


def _final_check(
    *,
    candidate: Path,
    has_template_json: bool,
) -> IOResult[Path, LivespecError]:
    if not has_template_json:
        return IOFailure(
            PreconditionError(
                f"resolved template path lacks template.json: {candidate}",
            ),
        )
    return IOSuccess(candidate)


def main(*, argv: Sequence[str] | None = None) -> int:
    """Supervisor: run the railway, pattern-match, derive exit code.

    The bug-catcher (one `try/except Exception`) is the only
    catch-all in this module per `check-supervisor-discipline`. Any
    raised exception (TypeError, AssertionError, RuntimeError on
    unreachable branches, etc.) lands here, gets logged with
    traceback, and exits 1.

    The dispatch logic (railway invocation + pattern match +
    sys.stdout.write) is inline in `main()` rather than a helper —
    the `sys.stdout.write` exemption per style doc lines 1474-1481
    is per-supervisor "the function named `main` at module
    top-level", NOT per-helper.
    """
    log = get_logger(__name__)
    actual_argv: Sequence[str] = list(argv) if argv is not None else sys.argv[1:]
    try:
        result = run(argv=actual_argv)
        inner = unsafe_perform_io(result)
        match inner:
            case Success(value):
                sys.stdout.write(f"{value.as_posix()}\n")
                return 0
            case Failure(HelpRequested(text=text)):
                sys.stdout.write(text)
                return 0
            case Failure(err):
                log.error(
                    "resolve_template failed",
                    error_type=type(err).__name__,
                    error_message=str(err),
                )
                return _exit_code_of(err)
            case _ as unreachable:
                _unreachable(unreachable)
    except Exception as exc:
        log.exception(
            "resolve_template internal error",
            exception_type=type(exc).__name__,
            exception_repr=repr(exc),
        )
        return 1


def _exit_code_of(err: LivespecError) -> int:
    """Pull the per-class exit_code from a LivespecError instance."""
    return type(err).exit_code


def _unreachable(value: object) -> NoReturn:
    """Raise on supposedly-unreachable values; bug-catcher converts to exit 1.

    `assert_never` from typing_extensions narrows pyright's type
    knowledge but raises `AssertionError` at runtime if reached.
    Wrapped here so the supervisor's bug-catcher gets a NoReturn
    function rather than an inline assert_never call.
    """
    assert_never(value)  # type: ignore[arg-type]
