"""Static-phase doctor check: no_orphan_blocker.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-orphan-blocker`":

  Every work item's declared `blocked_by` reference MUST resolve to an
  existing work item in the same impl-plugin's store. The check fires
  `fail` when a `blocked_by` reference targets a non-existent
  work-item id. Closed blockers are NOT orphans (their blocked-by
  relationship is historically valid); only missing-from-store ids
  fire the check.

The livespec-impl-plaintext schema uses `depends_on` for the same
semantic edge ("X depends on Y" == "X is blocked by Y"). This check
reads `depends_on` — the spec's `blocked_by` terminology refers to
the same relationship.

Cross-boundary mechanism: same v1 scope as `no_stalled_epic` — direct
JSONL read of the active impl-plugin's work-items store. Only
livespec-impl-plaintext is supported in v1; other plugins receive a
`skipped` Finding.
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


SLUG: CheckId = CheckId("doctor-no-orphan-blocker")
_SUPPORTED_PLUGINS: frozenset[str] = frozenset({"livespec-impl-plaintext"})
_DEFAULT_WORK_ITEMS_PATH: str = "work-items.jsonl"


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


def _find_orphan_blockers(*, index: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    """Return sorted (item_id, missing_dep_id) pairs where dep doesn't resolve."""
    orphans: list[tuple[str, str]] = []
    for item_id, record in index.items():
        deps = record.get("depends_on")
        if not isinstance(deps, list):
            continue
        for dep_id in deps:
            if not isinstance(dep_id, str):
                continue
            if dep_id not in index:
                orphans.append((item_id, dep_id))
    return sorted(orphans)


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
                message="no-orphan-blocker: .livespec.jsonc root is not an object; check skipped",
            )
        )
    work_items_path = _resolve_work_items_path(ctx=ctx, config=parsed)
    if work_items_path is None:
        return IOSuccess(
            _skipped(
                ctx=ctx,
                message=(
                    "no-orphan-blocker: active impl-plugin is not in the v1 supported set "
                    "(livespec-impl-plaintext); check skipped"
                ),
            ),
        )
    if not work_items_path.exists():
        return IOSuccess(
            _pass(
                ctx=ctx,
                message=(
                    f"no-orphan-blocker: work-items store at {work_items_path} not present yet; "
                    "no blockers to check"
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
    orphans = _find_orphan_blockers(index=index)
    if not orphans:
        return _pass(
            ctx=ctx,
            message=(
                f"no-orphan-blocker: every depends_on reference resolves to an existing "
                f"work-item ({len(index)} work-items scanned)"
            ),
        )
    pairs_joined = ", ".join(f"{item_id}→{missing}" for item_id, missing in orphans)
    return _fail(
        ctx=ctx,
        message=(
            f"no-orphan-blocker: {len(orphans)} unresolved depends_on reference(s): "
            f"{pairs_joined}. Either add the missing work-item(s) or remove the stale "
            "depends_on entry."
        ),
        path=str(work_items_path),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-orphan-blocker against `ctx`."""
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
                        f"no-orphan-blocker: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
