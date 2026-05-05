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

from livespec.commands._prune_history_railway import (
    _emit_no_op_finding,
    _emit_pre_step_skipped_finding,  # re-exported for the paired test surface
    _emit_pruned_finding,
    _resolve_skip,  # re-exported for the paired test surface
)
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

    Per v012 spec.md §"Pre-step skip control": the supervisor
    threads `_resolve_skip` through the railway to derive the
    effective skip value from the 4-rule matrix (skip-flag,
    run-flag, `.livespec.jsonc` config key, default False).
    When the resolved value is True, the wrapper emits a single-
    finding `pre-step-skipped` JSON document to stdout BEFORE
    running the body. The body still runs and emits its own
    `prune-history-no-op` / `prune-history-pruned` finding, so
    stdout carries TWO JSON lines on the skip path. The pre-step
    doctor invocation (the rule that follows) lands at 6.c.10.
    """
    project_root = _resolve_project_root(namespace=namespace)
    history_root = project_root / "SPECIFICATION" / "history"
    return (
        _resolve_skip(namespace=namespace, project_root=project_root)
        .bind(
            lambda skip: _maybe_emit_skipped(skip=skip),
        )
        .bind(
            lambda _none: fs.list_dir(path=history_root),
        )
        .bind(
            lambda children: _maybe_no_op_or_resolve(
                children=children,
                history_root=history_root,
            ),
        )
    )


def _maybe_emit_skipped(*, skip: bool) -> IOResult[None, LivespecError]:
    """Emit the `pre-step-skipped` finding when `skip` is True; otherwise no-op.

    Threads the `_resolve_skip` boolean back through the railway
    as a side-effect-only step. Returns IOSuccess(None) in both
    branches so subsequent `.bind(...)` stages always run.
    """
    if skip:
        _emit_pre_step_skipped_finding()
    return IOResult.from_value(None)


def _resolve_project_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve `<project-root>` from `--project-root` or cwd.

    Per v012 contracts.md §"Wrapper CLI surface" prune-history row
    + the universal `--project-root <path>` baseline. Defaults to
    `Path.cwd()` when `--project-root` is omitted. The spec root
    `<project-root>/SPECIFICATION` is derived at the call site;
    `_resolve_skip` also needs `project_root` directly to read
    `<project-root>/.livespec.jsonc`, so the helper returns the
    project root rather than the spec root.
    """
    if namespace.project_root is None:
        return Path.cwd()
    return Path(namespace.project_root)


def _maybe_no_op_or_resolve(
    *,
    children: list[Path],
    history_root: Path,
) -> IOResult[None, LivespecError]:
    """Detect either no-op short-circuit; else resolve the carry-forward `first` field.

    Per v012 spec.md prune-history no-op short-circuits: (i) only
    `v001` exists; (ii) the oldest surviving v-directory already
    contains a `PRUNED_HISTORY.json` marker. On either, the
    wrapper emits a single-finding skipped JSON document to
    stdout and exits 0 without any deletion. When NEITHER no-op
    fires, this dispatches to the carry-forward `first`
    resolution per spec.md step (b), threading the
    `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json` marker
    (when present) through `_resolve_first`. Cycle 6.c.5 only
    EXERCISES the resolver — it does not yet act on the
    resolved `first`. Subsequent cycles widen the dispatch to
    the full 5-step prune mechanic.
    """
    max_version = _find_max_version(children=children)
    if max_version == 1:
        _emit_no_op_finding()
        return IOResult.from_value(None)
    if _oldest_below_has_pruned_marker(children=children, max_version=max_version):
        _emit_no_op_finding()
        return IOResult.from_value(None)
    return _resolve_first_via_marker_or_children(
        children=children,
        max_version=max_version,
        history_root=history_root,
    ).bind(
        lambda first: _delete_old_v_dirs(
            children=children,
            max_version=max_version,
        )
        .bind(
            lambda _none: _replace_v_n_minus_one_with_marker(
                history_root=history_root,
                max_version=max_version,
                first=first,
            ),
        )
        .map(lambda _none: _emit_pruned_finding(first=first, last=max_version - 1)),
    )


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


def _oldest_below_has_pruned_marker(*, children: list[Path], max_version: int) -> bool:
    """Whether the smallest-K v-directory (K < max_version) holds a PRUNED_HISTORY.json.

    Per v012 spec.md no-op short-circuit (ii): when the oldest
    surviving v-directory below the current max already carries a
    `PRUNED_HISTORY.json` marker, no full versions remain to prune
    below the prior marker. `children` is pre-sorted by
    `fs.list_dir`, so the FIRST eligible v-directory encountered
    IS the smallest-K; we return its marker presence directly.
    Returns False when no eligible v-directory exists below
    `max_version`.
    """
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        version = int(suffix)
        if version >= max_version:
            continue
        return (child / "PRUNED_HISTORY.json").is_file()
    return False


def _resolve_first_via_marker_or_children(
    *,
    children: list[Path],
    max_version: int,
    history_root: Path,
) -> IOResult[int, LivespecError]:
    """Read the v(N-1) marker (when present) and call `_resolve_first` to compute `first`.

    Per v012 spec.md prune-history paragraph step (b): if
    `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json` exists, the
    wrapper reads its `pruned_range[0]` and uses it as `first`;
    otherwise `first` is the smallest-numbered v-directory
    currently under `<spec-root>/history/`. This impure layer
    decides whether to invoke `fs.read_text` based on
    `Path.is_file()`, then threads the result through the pure
    resolver. The marker-absent path skips the read entirely and
    calls the resolver with `prior_marker_text=None`.
    """
    marker_path = history_root / f"v{max_version - 1:03d}" / "PRUNED_HISTORY.json"
    if not marker_path.is_file():
        return IOResult.from_value(
            _resolve_first(
                children=children,
                max_version=max_version,
                prior_marker_text=None,
            ),
        )
    return fs.read_text(path=marker_path).map(
        lambda text: _resolve_first(
            children=children,
            max_version=max_version,
            prior_marker_text=text,
        ),
    )


def _resolve_first(
    *,
    children: list[Path],
    max_version: int,  # noqa: ARG001
    prior_marker_text: str | None,
) -> int:
    """Resolve the carry-forward `first` field per v012 spec.md step (b).

    When `prior_marker_text` is provided (the v(N-1)
    `PRUNED_HISTORY.json` contents), parse it as JSON and return
    `pruned_range[0]`. Otherwise return the smallest-numbered v-
    directory in `children`. `max_version` is accepted to keep
    the call-site contract symmetric with
    `_oldest_below_has_pruned_marker` even though the resolver
    does not currently filter by it (the smallest-numbered v-
    dir is by definition <= max_version when callers respect the
    pre-no-op-check invariant).
    """
    if prior_marker_text is not None:
        payload = json.loads(prior_marker_text)
        pruned_range = payload["pruned_range"]
        first_int: int = pruned_range[0]
        return first_int
    smallest = 0
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        version = int(suffix)
        if smallest == 0 or version < smallest:
            smallest = version
    return smallest


def _v_dirs_below_threshold(*, children: list[Path], max_version: int) -> list[Path]:
    """Return the list of `vK/` paths in `children` where K < max_version - 1.

    Per v012 SPECIFICATION/spec.md §"Sub-command lifecycle"
    prune-history paragraph step (c): the wrapper deletes every
    `<spec-root>/history/vK/` where K < N-1. With N=4, that
    means K ∈ {1, 2} (v003 = v(N-1) is preserved at this cycle;
    its replacement-with-marker happens at 6.c.7). Pure helper
    so unit tests cover each filter branch without filesystem
    I/O. Mirrors `_find_max_version` and `_resolve_first`'s
    defensive guards (non-directory entries, non-`v`-prefixed
    names, `v<non-digits>` suffixes are all skipped).
    """
    threshold = max_version - 1
    paths: list[Path] = []
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        version = int(suffix)
        if version >= threshold:
            continue
        paths.append(child)
    return paths


def _delete_old_v_dirs(
    *,
    children: list[Path],
    max_version: int,
) -> IOResult[None, LivespecError]:
    """Delete every `<spec-root>/history/vK/` where K < max_version - 1.

    Per v012 spec.md prune-history paragraph step (c): the
    wrapper recursively removes each old v-directory below the
    K < N-1 threshold via the `fs.rmtree` boundary primitive.
    Threads the per-path deletions sequentially through the
    railway so a mid-iteration OSError lifts to
    `IOFailure(PreconditionError)` and short-circuits the
    remaining deletions.
    """
    paths = _v_dirs_below_threshold(children=children, max_version=max_version)
    railway: IOResult[None, LivespecError] = IOResult.from_value(None)
    for path in paths:
        railway = railway.bind(lambda _none, p=path: fs.rmtree(path=p))
    return railway


def _build_pruned_history_marker(*, first: int, last: int) -> str:
    """Build the canonical `PRUNED_HISTORY.json` body per v012 spec.md step (d).

    The marker is exactly `{"pruned_range": [first, N-1]}` — no
    timestamps, git SHAs, or identity fields (no-metadata
    invariant; git commit metadata already provides that audit
    context). Pure helper so unit tests cover the JSON shape
    without filesystem I/O.
    """
    return json.dumps({"pruned_range": [first, last]})


def _replace_v_n_minus_one_with_marker(
    *,
    history_root: Path,
    max_version: int,
    first: int,
) -> IOResult[None, LivespecError]:
    """Replace v(N-1)/ contents with a single PRUNED_HISTORY.json marker.

    Per v012 spec.md prune-history paragraph step (d): rmtree
    `<spec-root>/history/v(N-1)/` (clearing any leftover content
    including a stale prior marker), then write the fresh marker
    at `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json`. The
    `fs.write_text` boundary auto-creates the parent directory
    via `mkdir(parents=True, exist_ok=True)` so no separate
    mkdir stage is needed. Threaded through the railway so an
    rmtree OSError lifts to `IOFailure(PreconditionError)` and
    short-circuits the marker write.
    """
    v_n_minus_one = history_root / f"v{max_version - 1:03d}"
    marker_path = v_n_minus_one / "PRUNED_HISTORY.json"
    text = _build_pruned_history_marker(first=first, last=max_version - 1)
    return fs.rmtree(path=v_n_minus_one).bind(
        lambda _none: fs.write_text(path=marker_path, text=text),
    )
