"""Static-phase doctor check: no_duplicate_gap_id.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-duplicate-gap-id`":

  No two open work items MAY claim the same gap-id label. The check
  fires `fail` when two or more open items share a gap-id. Closed
  items sharing a historical gap-id with an open item are exempt;
  this is the dual of `gap-tracking-one-to-one` viewed from the
  work-items-store side.

Cross-boundary mechanism: same v1 scope as `no_stalled_epic` and
`no_orphan_blocker` — direct JSONL read of the active impl-plugin's
work-items store. Only livespec-impl-plaintext is supported in v1;
other plugins receive a `skipped` Finding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Success

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-no-duplicate-gap-id")
_SUPPORTED_PLUGINS: frozenset[str] = frozenset({"livespec-impl-plaintext"})
_DEFAULT_WORK_ITEMS_PATH: str = "work-items.jsonl"
_OPEN_STATUSES: frozenset[str] = frozenset({"open", "in_progress", "blocked"})
_DUPLICATE_THRESHOLD: int = 2


def _pass(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a pass-status Finding."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _skipped(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a skipped-status Finding."""
    return Finding(
        check_id=SLUG,
        status="skipped",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _fail(*, ctx: DoctorContext, message: str, path: str | None) -> Finding:
    """Build a fail-status Finding."""
    return Finding(
        check_id=SLUG,
        status="fail",
        message=message,
        path=path,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _materialize_records(*, jsonl_text: str) -> dict[str, dict[str, Any]]:
    """Parse JSONL text and return latest-record-per-id index."""
    index: dict[str, dict[str, Any]] = {}
    for raw_line in jsonl_text.splitlines():
        stripped = raw_line.strip()
        if stripped == "":
            continue
        parsed_result = jsonc.loads(text=stripped)
        if not isinstance(parsed_result, Success):
            continue
        parsed = parsed_result.unwrap()
        if not isinstance(parsed, dict):
            continue
        item_id = parsed.get("id")
        if not isinstance(item_id, str):
            continue
        index[item_id] = parsed
    return index


def _find_duplicate_gap_ids(
    *,
    index: dict[str, dict[str, Any]],
) -> list[tuple[str, list[str]]]:
    """Return sorted (gap_id, [item_ids]) pairs where ≥2 open items share gap_id."""
    grouped: dict[str, list[str]] = {}
    for item_id, record in index.items():
        status = record.get("status")
        if status not in _OPEN_STATUSES:
            continue
        gap_id = record.get("gap_id")
        if not isinstance(gap_id, str):
            continue
        grouped.setdefault(gap_id, []).append(item_id)
    duplicates: list[tuple[str, list[str]]] = []
    for gap_id, item_ids in grouped.items():
        if len(item_ids) >= _DUPLICATE_THRESHOLD:
            duplicates.append((gap_id, sorted(item_ids)))
    return sorted(duplicates)


def _resolve_work_items_path(*, ctx: DoctorContext, config: dict[str, Any]) -> Path | None:
    """Return the resolved work-items.jsonl path, or None if active impl is unsupported."""
    impl_section = config.get("implementation")
    if not isinstance(impl_section, dict):
        return None
    plugin_name = impl_section.get("plugin")
    if not isinstance(plugin_name, str) or plugin_name not in _SUPPORTED_PLUGINS:
        return None
    plugin_section = config.get(plugin_name)
    raw_path: object = _DEFAULT_WORK_ITEMS_PATH
    if isinstance(plugin_section, dict):
        candidate = plugin_section.get("work_items_path", _DEFAULT_WORK_ITEMS_PATH)
        if isinstance(candidate, str):
            raw_path = candidate
    return ctx.project_root / str(raw_path)


def _evaluate(*, ctx: DoctorContext, parsed: Any) -> IOResult[Finding, LivespecError]:
    """Resolve the work-items path and evaluate the invariant."""
    if not isinstance(parsed, dict):
        return IOSuccess(
            _skipped(
                ctx=ctx,
                message="no-duplicate-gap-id: .livespec.jsonc root is not an object; check skipped",
            )
        )
    work_items_path = _resolve_work_items_path(ctx=ctx, config=parsed)
    if work_items_path is None:
        return IOSuccess(
            _skipped(
                ctx=ctx,
                message=(
                    "no-duplicate-gap-id: active impl-plugin is not in the v1 supported set "
                    "(livespec-impl-plaintext); check skipped"
                ),
            ),
        )
    if not work_items_path.exists():
        return IOSuccess(
            _pass(
                ctx=ctx,
                message=(
                    f"no-duplicate-gap-id: work-items store at {work_items_path} not present yet; "
                    "no gap-ids to check"
                ),
            ),
        )
    return fs.read_text(path=work_items_path).bind(
        lambda text: IOSuccess(
            _evaluate_text(ctx=ctx, jsonl_text=text, work_items_path=work_items_path)
        ),
    )


def _evaluate_text(*, ctx: DoctorContext, jsonl_text: str, work_items_path: Path) -> Finding:
    """Apply the invariant against the JSONL text content."""
    index = _materialize_records(jsonl_text=jsonl_text)
    duplicates = _find_duplicate_gap_ids(index=index)
    if not duplicates:
        return _pass(
            ctx=ctx,
            message=(
                f"no-duplicate-gap-id: every open work-item's gap-id is unique "
                f"({len(index)} work-items scanned)"
            ),
        )
    groups_joined = "; ".join(
        f"{gap_id}: [{', '.join(item_ids)}]" for gap_id, item_ids in duplicates
    )
    return _fail(
        ctx=ctx,
        message=(
            f"no-duplicate-gap-id: {len(duplicates)} gap-id(s) claimed by multiple "
            f"open work-items: {groups_joined}. Consolidate or close the duplicates."
        ),
        path=str(work_items_path),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-duplicate-gap-id against `ctx`."""
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
        .bind(lambda parsed: _evaluate(ctx=ctx, parsed=parsed))
        .lash(
            lambda err: IOSuccess(
                _skipped(
                    ctx=ctx,
                    message=(
                        f"no-duplicate-gap-id: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
