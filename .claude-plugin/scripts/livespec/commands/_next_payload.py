# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
"""Next command private ranking payload helpers."""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._next_ranking import (
    PRUNE_HISTORY_THRESHOLD,
    _collect_proposal_ages,
    _enumerate_candidates,
    _output_payload,
    _paginate,
    _threshold_from_config_text,
)
from livespec.errors import LivespecError, PreconditionError, UsageError, ValidationError
from livespec.io import fs
from livespec.parse import front_matter, jsonc
from livespec.schemas.dataclasses.next_output import NextCandidate, NextOutput
from livespec.validate import next_output as validate_next_output_module

__all__: list[str] = ["_ranked_payload", "_validate_window_flags"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_NEXT_OUTPUT_SCHEMA_PATH = _SCHEMAS_DIR / "next_output.schema.json"
_PROPOSED_CHANGES_README = "README.md"


def _resolve_project_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve --project-root to a Path, defaulting to Path.cwd()."""
    if namespace.project_root is None:
        return Path.cwd()
    return Path(namespace.project_root)


def _resolve_spec_target(*, namespace: argparse.Namespace, project_root: Path) -> Path:
    """Resolve --spec-target to a Path; default <project-root>/SPECIFICATION/.

    The default applies when --spec-target is omitted per the
    `next` row of the wrapper CLI surface table.
    """
    if namespace.spec_target is None:
        return project_root / "SPECIFICATION"
    return Path(namespace.spec_target)


def _validate_window_flags(
    *,
    namespace: argparse.Namespace,
) -> IOResult[tuple[int, int], LivespecError]:
    """Gate --offset/--limit values per the wrapper CLI flags contract.

    Returns `IOSuccess((offset, limit))` when both are in range.
    A non-positive `--limit` or negative `--offset` lifts a
    UsageError (exit 2) naming the offending flag and value;
    non-integer values never reach here (argparse's int
    conversion fails at the parse_argv seam, also exit 2).
    """
    limit = int(namespace.limit)
    offset = int(namespace.offset)
    if limit < 1:
        return IOResult.from_failure(
            UsageError(f"next: --limit must be a positive integer, got {limit}"),
        )
    if offset < 0:
        return IOResult.from_failure(
            UsageError(f"next: --offset must be a non-negative integer, got {offset}"),
        )
    return IOSuccess((offset, limit))


def _proposal_paths(*, spec_target: Path) -> IOResult[list[Path], LivespecError]:
    """List `<spec-target>/proposed_changes/*.md` excluding the README.

    Sorted lexicographically (via `fs.list_dir`) for deterministic
    iteration order. The skill-owned `proposed_changes/README.md`
    is excluded per `SPECIFICATION/spec.md` — the README is not
    an in-flight proposal.
    """
    return fs.list_dir(path=spec_target / "proposed_changes").map(
        lambda entries: [
            entry
            for entry in entries
            if entry.is_file() and entry.suffix == ".md" and entry.name != _PROPOSED_CHANGES_README
        ],
    )


def _front_matter_to_io(
    *,
    text: str,
    path: Path,
) -> IOResult[dict[str, Any], LivespecError]:
    """Lift `parse_front_matter` from Result to IOResult and remap errors.

    The pure front_matter parser returns `ValidationError` (exit
    4 — wire-format violation). For the next ranker, a malformed
    proposal in the spec tree is a project-state precondition
    failure (the spec tree contains an unparseable file); the
    remap to `PreconditionError` lifts the exit code from 4 → 3
    per the lifecycle exit-code table semantics.
    """
    parse_result = front_matter.parse_front_matter(text=text)
    match parse_result:
        case Success(payload):
            return IOSuccess(payload)
        case Failure(ValidationError() as ve):
            return IOResult.from_failure(
                PreconditionError(f"next: malformed proposal front-matter at {path}: {ve}"),
            )
        case _:
            assert_never(parse_result)  # pyright: ignore[reportArgumentType]


def _proposal_entry(*, path: Path) -> IOResult[tuple[str, str], LivespecError]:
    """Read one proposal and return its `(target, created_at)` pair.

    `target` is the spec-target-relative proposal path
    (`proposed_changes/<name>.md`) per the output schema.
    Composes fs.read_text -> front_matter parse, then coerces
    the `created_at` field to `str` via `str(... or "")`. A
    missing key or `null` value becomes the empty string, which
    downstream `_parse_iso_age_days` rejects via its canonical-
    `Z`-suffix gate — yielding the same `PreconditionError`
    exit-3 channel that malformed YAML front-matter takes. The
    coercion folds the missing-key / wrong-type / unparseable-
    ISO failure modes into a single branch.
    """
    return (
        fs.read_text(path=path)
        .bind(lambda text: _front_matter_to_io(text=text, path=path))
        .map(lambda fm: (f"proposed_changes/{path.name}", str(fm.get("created_at") or "")))
    )


def _history_version_count(*, spec_target: Path) -> IOResult[int, LivespecError]:
    """Count `<spec-target>/history/v*/` directories.

    The ranker treats every `v*`-named child as a version
    directory; pruned-marker directories (containing
    `PRUNED_HISTORY.json`) still count toward the unpruned-
    against-threshold comparison — the marker is the previous
    floor and the surviving versions sit above it. The ranker
    uses raw count; a future widening MAY subtract the
    pruned-marker contribution.
    """
    return fs.list_dir(path=spec_target / "history").map(
        lambda entries: sum(
            1 for entry in entries if entry.is_dir() and entry.name.startswith("v")
        ),
    )


def _now_utc() -> datetime.datetime:
    """Return the current time in UTC with tzinfo set.

    Wrapped for monkeypatch-replacement in tests that want a
    deterministic clock.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def _validate_and_serialize(*, output: NextOutput) -> IOResult[str, LivespecError]:
    """Validate the NextOutput against the schema and serialize to JSON.

    Round-trips the dataclass through `next_output.schema.json`
    via the validator factory so a drift between the dataclass
    fields and the schema enum/required constraints surfaces as
    a `ValidationError` (exit 4) before the supervisor writes a
    malformed payload to stdout.
    """
    payload = _output_payload(output=output)
    return (
        fs.read_text(path=_NEXT_OUTPUT_SCHEMA_PATH)
        .bind(
            lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(
            lambda schema_dict: IOResult.from_result(  # pyright: ignore[reportArgumentType]
                validate_next_output_module.validate_next_output(
                    payload=payload,
                    schema=schema_dict,
                ),
            ),
        )
        .map(
            lambda _validated: json.dumps(payload, separators=(",", ":"), sort_keys=True),
        )
    )


def _collect_proposal_entries(
    *,
    paths: list[Path],
) -> IOResult[list[tuple[str, str]], LivespecError]:
    """Read each proposal file and return its `(target, created_at)` pair.

    Aggregates per-proposal IOResults via short-circuiting:
    the first failure halts iteration and propagates to the
    supervisor's pattern-match. Equivalent in spirit to
    `Fold.collect` but spelled out to keep the type annotations
    legible.
    """
    out: list[tuple[str, str]] = []
    for path in paths:
        result = _proposal_entry(path=path)
        unwrapped = unsafe_perform_io(result)  # pyright: ignore[reportArgumentType]
        match unwrapped:
            case Success(value):
                out.append(value)
            case Failure(LivespecError()):
                return result.map(lambda _value, _out=out: _out)
            case _:
                assert_never(unwrapped)
    return IOSuccess(out)


def _verify_spec_target(*, spec_target: Path) -> IOResult[Path, LivespecError]:
    """Confirm the spec target directory exists; lift to PreconditionError otherwise.

    Without this guard, `_proposal_paths` and
    `_history_version_count` would each surface an opaque
    `fs.list_dir` precondition error. Checking the spec-target
    root once up front emits a clearer diagnostic naming the
    missing target.
    """
    if not spec_target.is_dir():
        return IOResult.from_failure(
            PreconditionError(
                f"next: --spec-target does not exist or is not a directory: {spec_target}"
            ),
        )
    return IOSuccess(spec_target)


def _resolve_prune_history_threshold(
    *,
    project_root: Path,
) -> IOResult[int, LivespecError]:
    """Resolve the prune-history threshold per `SPECIFICATION/contracts.md`.

    Reads `<project-root>/.livespec.jsonc` on each invocation. A
    missing config file means the key is absent, so the default
    `PRUNE_HISTORY_THRESHOLD` (20) applies; a present file is
    read and the pure `_threshold_from_config_text` extraction
    yields either the configured positive integer or
    `Failure(PreconditionError)` naming the offending key and
    value (exit 3 at the supervisor) on a
    non-positive-integer value.
    """
    config_path = project_root / ".livespec.jsonc"
    if not config_path.is_file():
        return IOSuccess(PRUNE_HISTORY_THRESHOLD)
    return fs.read_text(path=config_path).bind(
        lambda text: IOResult.from_result(_threshold_from_config_text(text=text)),
    )


def _rank_pipeline(
    *,
    spec_target: Path,
    prune_history_threshold: int,
) -> IOResult[list[NextCandidate], LivespecError]:
    """Compose the file-state reads into the ranked candidate list.

    Sequence: verify spec target → list proposal paths → read
    each proposal's `(target, created_at)` → count history
    versions → compute per-proposal ages → pure candidate
    enumeration + sort. `prune_history_threshold` is the
    per-invocation value resolved from `.livespec.jsonc` by
    `_resolve_prune_history_threshold`.

    Per `SPECIFICATION/contracts.md`: the ranker is a pure function
    of spec-side file state — no impl-side store reads and no
    subprocess probes in the ranking path.
    """
    return (
        _verify_spec_target(spec_target=spec_target)
        .bind(lambda _path: _proposal_paths(spec_target=spec_target))
        .bind(
            lambda paths: _collect_proposal_entries(paths=paths).bind(
                lambda entries: _history_version_count(spec_target=spec_target).bind(
                    lambda history_count: IOResult.from_result(
                        _collect_proposal_ages(
                            entries=entries,
                            now=_now_utc(),
                        ).map(
                            lambda proposal_ages: _enumerate_candidates(
                                proposal_ages=proposal_ages,
                                history_version_count=history_count,
                                prune_history_threshold=prune_history_threshold,
                            ),
                        ),
                    ),
                ),
            ),
        )
    )


def _ranked_payload(
    *,
    namespace: argparse.Namespace,
    window: tuple[int, int],
) -> IOResult[str, LivespecError]:
    """Resolve config + spec target, then rank, paginate, and serialize."""
    project_root = _resolve_project_root(namespace=namespace)
    spec_target = _resolve_spec_target(namespace=namespace, project_root=project_root)
    return (
        _resolve_prune_history_threshold(project_root=project_root)
        .bind(
            lambda threshold: _rank_pipeline(
                spec_target=spec_target,
                prune_history_threshold=threshold,
            ),
        )
        .bind(
            lambda candidates: _validate_and_serialize(
                output=_paginate(candidates=candidates, offset=window[0], limit=window[1]),
            ),
        )
    )
