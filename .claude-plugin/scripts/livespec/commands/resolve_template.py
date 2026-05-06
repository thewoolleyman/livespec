"""Resolve-template sub-command supervisor.

Per PROPOSAL.md §"Template resolution contract"
and v028 D1: emits the resolved template directory path on
stdout. The path-computation formula
`Path(__file__).resolve().parents[3]` derives the bundle root
from this file's location: parents[0]=commands/,
parents[1]=livespec/, parents[2]=scripts/,
parents[3]=.claude-plugin/.

Phase 3 minimum-viable scope: only the --template flow is
implemented (the pre-seed flow per v017 Q2). The default
`.livespec.jsonc`-walking flow is deferred to Phase 7 — no
consumer in Phase 6's seed self-application; the seed/SKILL.md
prose uses --template livespec pre-seed. With --template
required at this phase, the seed unblocks for Phase 6.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
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

from livespec.errors import LivespecError, PreconditionError
from livespec.io import cli

__all__: list[str] = ["build_parser", "main"]


_BUNDLE_ROOT = Path(__file__).resolve().parents[3]
_BUILTIN_TEMPLATES_DIR = _BUNDLE_ROOT / "specification-templates"
_BUILTIN_TEMPLATE_NAMES = frozenset({"livespec", "minimal"})


def build_parser() -> argparse.ArgumentParser:
    """Construct the resolve-template argparse parser without parsing.

    Per PROPOSAL §"Template resolution contract":
    `--project-root <path>` (default `Path.cwd()`) and
    `--template <value>`. PROPOSAL marks --template OPTIONAL; this
    Phase-3-minimum makes it required (the default
    `.livespec.jsonc` walking flow is Phase 7 work).

    `exit_on_error=False` lets argparse signal errors via
    `argparse.ArgumentError` rather than `SystemExit`, per style
    doc §"CLI argument parsing seam".
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

    Built-in names (`livespec`, `minimal`) resolve to
    `<bundle-root>/specification-templates/<name>` via
    `_BUILTIN_TEMPLATES_DIR`. Other strings are treated as paths
    relative to --project-root and validated to (a) exist as a
    directory and (b) contain `template.json`. Failures map to
    `PreconditionError` (exit 3 per PROPOSAL).
    """
    if value in _BUILTIN_TEMPLATE_NAMES:
        return IOSuccess(_BUILTIN_TEMPLATES_DIR / value)
    candidate = (project_root / value).resolve()
    if not candidate.is_dir():
        return IOResult.from_failure(
            PreconditionError(
                f"resolve_template: --template path does not exist or "
                f"is not a directory: {candidate}",
            ),
        )
    if not (candidate / "template.json").is_file():
        return IOResult.from_failure(
            PreconditionError(
                f"resolve_template: --template path lacks template.json: " f"{candidate}",
            ),
        )
    return IOSuccess(candidate)


def _emit_resolved_path(*, path: Path) -> IOResult[Path, LivespecError]:
    """Emit the resolved path on stdout per the v1-frozen contract.

    PROPOSAL §"Template resolution contract":
    exactly one line, absolute POSIX path, trailing `\\n`.
    """
    sys.stdout.write(f"{path}\n")
    return IOSuccess(path)


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    Success(<value>) → exit 0 per style doc §"Exit code contract".
    Failure(LivespecError) lifts via err.exit_code; assert_never
    closes the match.
    """
    unwrapped = unsafe_perform_io(io_result)
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
    3; success -> exit 0 with one-line stdout per PROPOSAL
    §"Template resolution contract".
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: _resolve_template_value(
            value=namespace.template,
            project_root=_resolve_project_root(namespace=namespace),
        ).bind(lambda path: _emit_resolved_path(path=path)),
    )
    return _pattern_match_io_result(io_result=railway)
