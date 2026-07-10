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
"""Resolve-template sub-command supervisor.


and emits the resolved template directory path on stdout.
Resolution (the built-in name set and the custom-template path
rule) is delegated to the shared
`livespec.templates.resolve_template_value` — the single source of
truth shared with the two doctor-static resolvers (`template_exists`,
`_template_manifest`) so the three cannot drift.

 minimum-viable scope: only the --template flow is
implemented (the pre-seed flow per the spec Q2). The default
`.livespec.jsonc`-walking flow is deferred to  — no
consumer in 's seed self-application; the seed/SKILL.md
prose uses --template livespec pre-seed. With --template
required at this phase, the seed unblocks for .

`build_parser()` is the pure argparse factory per the style doc;
`main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code. `main()` uses
`sys.stdout.write` for the documented one-line resolved-path
output (per `commands/CLAUDE.md` exception list:
`HelpRequested.text` and the resolved-path single-line output
of `resolve_template` are the two `commands/` stdout-write
exemptions).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec import templates
from livespec.errors import LivespecError, PreconditionError
from livespec.io import cli, streams

__all__: list[str] = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Construct the resolve-template argparse parser without parsing.

    Two args: `--project-root <path>` (default `Path.cwd()`) and
    `--template <value>` (required at this minimum-viable stage;
    the default `.livespec.jsonc`-walking flow is a future widening).

    `exit_on_error=False` lets argparse signal errors via
    `argparse.ArgumentError` rather than `SystemExit`, per the
    style doc.
    """
    parser = argparse.ArgumentParser(prog="resolve-template", exit_on_error=False)
    _ = parser.add_argument("--project-root", default=None)
    _ = parser.add_argument("--template", required=True)
    return parser


def _resolve_project_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve --project-root to a Path, defaulting to Path.cwd()."""
    if namespace.project_root is None:
        return Path.cwd()
    return Path(namespace.project_root)


def _resolve_template_value(
    *,
    value: str,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    """Resolve a --template value to an absolute directory path.

    Delegates to the shared `livespec.templates.resolve_template_value`
    (the single built-in-set + custom-path source of truth shared with
    the two doctor-static resolvers), then lifts the pure `Result` onto
    the IO railway: a `TemplateResolutionFailure` maps to a
    `PreconditionError` (exit 3) via `_precondition_for_failure`.
    """
    resolution = templates.resolve_template_value(value=value, project_root=project_root)
    return IOResult.from_result(
        resolution.alt(lambda failure: _precondition_for_failure(failure=failure)),
    )


def _precondition_for_failure(
    *,
    failure: templates.TemplateResolutionFailure,
) -> LivespecError:
    """Map a shared-resolver failure onto the exit-3 PreconditionError.

    The two arms keep the messages resolve_template emitted before the
    resolution logic was extracted: `missing_dir` → the path is absent
    or not a directory; `missing_manifest` → the directory exists but
    carries no `template.json`.
    """
    if failure.reason == "missing_dir":
        return PreconditionError(
            f"resolve_template: --template path does not exist or "
            f"is not a directory: {failure.candidate}",
        )
    return PreconditionError(
        f"resolve_template: --template path lacks template.json: {failure.candidate}",
    )


def _emit_resolved_path(*, path: Path) -> IOResult[Path, LivespecError]:
    """Emit the resolved path on stdout per the v1-frozen contract.:
    exactly one line, absolute POSIX path, trailing `\\n`.
    """
    _ = streams.write_stdout(text=f"{path}\n")
    return IOSuccess(path)


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    Success(<value>) → exit 0 per the style doc exit code contract.
    Failure(LivespecError) lifts via err.exit_code; assert_never
    closes the match.
    """
    unwrapped = unsafe_perform_io(io_result)  # pyright: ignore[reportArgumentType]
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)


def main(*, argv: list[str] | None = None) -> int:
    """Resolve-template supervisor entry point. Returns the exit code.

    Threads argv through the railway:
      parse_argv -> _resolve_template_value -> _emit_resolved_path

    UsageError (parse, missing required) -> exit 2;
    PreconditionError (template path missing or invalid) -> exit
    3; success -> exit 0 with one-line stdout per
    SPECIFICATION/contracts.md.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: _resolve_template_value(  # pyright: ignore[reportArgumentType]
            value=namespace.template,
            project_root=_resolve_project_root(namespace=namespace),
        ).bind(lambda path: _emit_resolved_path(path=path)),
    )
    return _pattern_match_io_result(io_result=railway)
