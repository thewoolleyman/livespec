"""critique sub-command (Phase 3 minimum-viable per v019 Q1).

Delegates to `propose_change` with `-critique` appended to the
topic. The simplest delegation shape: critique parses its own CLI,
appends `-critique` to the topic verbatim, and re-invokes
`propose_change.run(argv=...)` with the modified argv.

Out of Phase-3 scope (per plan line 1185-1193):
- Full reserve-suffix canonicalization (v016 P3 / v017 Q1):
  truncation-aware insertion, pre-attached-suffix detection,
  algorithmic guarantees on length and uniqueness. Phase 3
  appends `-critique` verbatim and lets propose_change's Phase-3
  canonical-topic check decide whether the result is acceptable;
  Phase 7 widens to the full algorithm.
- LLM-driven critique prompt flow: the `prompts/critique.md`
  invocation lives entirely on the SKILL.md prose side; the
  Python wrapper here is purely the internal-delegation
  mechanic.

This wrapper is sufficient for the Phase 6 first dogfooded
cycle, where critique-via-propose-change-delegation is the
contract the SKILL.md prose layer can rely on.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands import propose_change
from livespec.errors import HelpRequested, LivespecError
from livespec.io.cli import parse_args
from livespec.io.structlog_facade import get_logger

__all__: list[str] = [
    "build_parser",
    "main",
    "run",
]


_RESERVE_SUFFIX = "-critique"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="livespec critique",
        description="File a critique as propose-change with `-critique` reserve-suffix.",
        exit_on_error=False,
    )
    parser.add_argument(
        "topic",
        type=str,
        help="Canonical kebab-case topic (the wrapper appends `-critique`).",
    )
    parser.add_argument(
        "--findings-json",
        dest="findings_json",
        type=Path,
        required=True,
        help="Path to the findings-JSON payload from prompts/critique.md.",
    )
    parser.add_argument(
        "--author",
        type=str,
        default=None,
        help="Author identifier (forwarded to propose_change verbatim).",
    )
    parser.add_argument(
        "--spec-target",
        dest="spec_target",
        type=Path,
        default=None,
        help="Target spec tree (forwarded to propose_change).",
    )
    parser.add_argument(
        "--project-root",
        dest="project_root",
        type=Path,
        default=None,
        help="Project root for .livespec.jsonc lookup (forwarded).",
    )
    return parser


def run(*, argv: Sequence[str]) -> IOResult[Path, LivespecError]:
    """Parse our CLI; append `-critique` to topic; delegate to propose_change."""
    parser = build_parser()
    return parse_args(parser=parser, argv=argv).bind(_delegate)


def _delegate(namespace: argparse.Namespace) -> IOResult[Path, LivespecError]:
    """Build a propose_change argv from our namespace and forward."""
    propose_change_argv: list[str] = [
        f"{namespace.topic}{_RESERVE_SUFFIX}",
        "--findings-json",
        str(namespace.findings_json),
    ]
    if namespace.author is not None:
        propose_change_argv.extend(("--author", namespace.author))
    if namespace.spec_target is not None:
        propose_change_argv.extend(("--spec-target", str(namespace.spec_target)))
    if namespace.project_root is not None:
        propose_change_argv.extend(("--project-root", str(namespace.project_root)))
    return propose_change.run(argv=propose_change_argv)


def main(*, argv: Sequence[str] | None = None) -> int:
    """Supervisor: bug-catcher + railway dispatch inline (sys.stdout.write
    exemption per style doc lines 1474-1481 is per-`main()`, NOT per-helper)."""
    log = get_logger(name=__name__)
    actual_argv: Sequence[str] = list(argv) if argv is not None else sys.argv[1:]
    try:
        result = run(argv=actual_argv)
        inner = unsafe_perform_io(result)
        match inner:
            case Success(_):
                return 0
            case Failure(HelpRequested(text=text)):
                sys.stdout.write(text)
                return 0
            case Failure(err):
                log.error(
                    "critique failed",
                    error_type=type(err).__name__,
                    error_message=str(err),
                )
                return type(err).exit_code
            case _ as unreachable:
                _unreachable(value=unreachable)
    except Exception as exc:
        log.exception(
            "critique internal error",
            exception_type=type(exc).__name__,
            exception_repr=repr(exc),
        )
        return 1


def _unreachable(*, value: object) -> NoReturn:
    assert_never(value)  # type: ignore[arg-type]
