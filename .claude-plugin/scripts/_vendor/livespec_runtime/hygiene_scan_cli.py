"""CLI adapter for hygiene scanning."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import TextIO

from livespec_runtime.hygiene_scan_context import DEFAULT_STALE_DAYS, run_command
from livespec_runtime.hygiene_scan_types import CommandRunner

__all__: list[str] = [
    "main",
    "run",
]


def main(
    *,
    argv: list[str],
    environ: Mapping[str, str],
    stdout: TextIO,
    stderr: TextIO,
    runner: CommandRunner | None = None,
) -> int:
    from livespec_runtime.hygiene_scan import scan_hygiene

    _ = environ
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.stale_days < 0:
        _ = stderr.write("hygiene-scan: --stale-days must be non-negative\n")
        return 2
    items = scan_hygiene(
        repo_path=args.repo,
        repo_name=args.repo_name,
        stale_days=args.stale_days,
        include_prs=not args.no_prs,
        runner=runner or run_command,
    )
    _ = stdout.write(json.dumps([asdict(item) for item in items], sort_keys=True))
    _ = stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="livespec-hygiene-scan")
    _ = parser.add_argument("--repo", type=Path, default=Path.cwd())
    _ = parser.add_argument("--repo-name", type=str, default=None)
    _ = parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    _ = parser.add_argument("--no-prs", action="store_true", default=False)
    return parser


def run() -> int:  # pragma: no cover
    """Process entry: wire real process inputs and outputs."""
    return main(
        argv=sys.argv[1:],
        environ=os.environ,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
