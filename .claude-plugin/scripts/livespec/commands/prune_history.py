"""Prune-history sub-command supervisor.

Per v012 SPECIFICATION/spec.md §"Sub-command lifecycle"
prune-history paragraph: the wrapper resolves the spec root from
`--project-root` and `.livespec.jsonc` (the main spec tree only —
no `--spec-target` flag in v1) and performs deterministic
file-shaping per the 5-step prune mechanic. Two no-op short-
circuits MUST be detected before any deletion: (i) only `v001`
exists; (ii) the oldest surviving v-directory already contains a
`PRUNED_HISTORY.json` marker. On either no-op, the wrapper emits
a single-finding `prune-history-no-op` skipped JSON document to
stdout and exits 0.

`build_parser()` is the pure argparse factory; `main()` is the
supervisor that threads argv through the railway and pattern-
matches the final IOResult to derive the exit code. Cycle 6.c.3
landed the no-op short-circuit (i); subsequent cycles widen to
no-op (ii), the prune mechanic itself, and pre-step doctor
invocation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError
from livespec.io import cli, fs

__all__: list[str] = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Construct the prune-history argparse parser without parsing.

    Per v012 spec.md §"Pre-step skip control" rule: the wrapper
    declares an `add_mutually_exclusive_group` carrying the two
    flags `--skip-pre-check` / `--run-pre-check`; passing both
    together lifts to argparse usage error → exit 2 via
    `IOFailure(UsageError)`. The universal `--project-root <path>`
    flag is per the wrapper-CLI baseline (defaults to `Path.cwd()`).
    """
    parser = argparse.ArgumentParser(prog="prune-history", exit_on_error=False)
    pre_check_group = parser.add_mutually_exclusive_group()
    _ = pre_check_group.add_argument("--skip-pre-check", action="store_true")
    _ = pre_check_group.add_argument("--run-pre-check", action="store_true")
    _ = parser.add_argument("--project-root", default=None)
    return parser


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    Success(<value>) -> exit 0 per style doc §"Exit code
    contract". Failure(LivespecError) lifts via err.exit_code;
    assert_never closes the match.
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
    """Prune-history supervisor entry point. Returns the process exit code.

    Threads argv through `parse_argv` -> `_run_prune` (which
    resolves the spec root, enumerates history, and dispatches to
    the no-op short-circuit when applicable). Pattern-matches the
    final IOResult onto an exit code per style doc §"Exit code
    contract".
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    railway: IOResult[Any, LivespecError] = cli.parse_argv(
        parser=parser,
        argv=resolved_argv,
    ).bind(
        lambda namespace: _run_prune(namespace=namespace),
    )
    return _pattern_match_io_result(io_result=railway)


def _run_prune(*, namespace: argparse.Namespace) -> IOResult[None, LivespecError]:
    """Resolve the spec root and dispatch to the prune mechanic.

    Per v012 spec.md prune-history paragraph: spec-root resolution
    is `<project-root>/SPECIFICATION/` (no `--spec-target` in v1).
    Lists `<spec-root>/history/` and dispatches to the no-op
    detection path; subsequent cycles widen the dispatch to the
    full 5-step prune mechanic.
    """
    spec_root = _resolve_spec_root(namespace=namespace)
    return fs.list_dir(path=spec_root / "history").bind(
        lambda children: _maybe_no_op(children=children),
    )


def _resolve_spec_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve `<project-root>/SPECIFICATION/` from --project-root or cwd.

    Per v012 contracts.md §"Wrapper CLI surface" prune-history row
    + the universal `--project-root <path>` baseline. Defaults to
    `Path.cwd() / "SPECIFICATION"` when --project-root is omitted.
    """
    project_root = Path.cwd() if namespace.project_root is None else Path(namespace.project_root)
    return project_root / "SPECIFICATION"


def _maybe_no_op(*, children: list[Path]) -> IOResult[None, LivespecError]:
    """Emit the no-op skipped finding when only v001 exists; else continue.

    Per v012 spec.md prune-history no-op short-circuit (i): when
    `<spec-root>/history/` contains only `v001`, the wrapper emits
    a single-finding skipped JSON document to stdout and exits 0
    without any deletion. Subsequent cycles widen this to also
    detect short-circuit (ii) (oldest surviving is already
    `PRUNED_HISTORY.json`) and to perform the actual prune.
    """
    max_version = _find_max_version(children=children)
    if max_version == 1:
        _emit_no_op_finding()
    return IOResult.from_value(None)


def _find_max_version(*, children: list[Path]) -> int:
    """Compute the highest `vNNN` integer suffix among directory children.

    Walks `children` looking for `vNNN` directories; tracks the
    maximum N found; returns 0 when no `vNNN` children are present.
    Non-directory entries and non-`v\\d+` names are skipped.
    """
    max_version = 0
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        max_version = max(max_version, int(suffix))
    return max_version


def _emit_no_op_finding() -> None:
    """Write the canonical prune-history-no-op skipped finding to stdout.

    Per v012 spec.md prune-history paragraph: the wrapper emits a
    single-finding `{"findings": [{"check_id": "prune-history-
    no-op", "status": "skipped", "message": "..."}]}` JSON document
    to stdout. The commands/-tree exemption in the
    `check-no-write-direct` allowlist permits this stdout-write.
    """
    payload = {
        "findings": [
            {
                "check_id": "prune-history-no-op",
                "status": "skipped",
                "message": (
                    "nothing to prune; oldest surviving history is " "already PRUNED_HISTORY.json"
                ),
            },
        ],
    }
    _ = sys.stdout.write(json.dumps(payload) + "\n")
