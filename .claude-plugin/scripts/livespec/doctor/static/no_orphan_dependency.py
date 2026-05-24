"""Static-phase doctor check: no_orphan_dependency.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-orphan-dependency`":

  Every work item's declared `depends_on` entries MUST resolve
  cleanly. The check fires `fail` when any `DependsOnEntry` with
  `kind == "local"` references a `work_item_id` that does not
  exist in the materialized work-items store. For `kind` values
  `sibling_work_item`, `pull_request`, and `branch`, the invariant
  defers to `livespec_runtime.cross_repo.resolve_ref` — full
  cross-repo resolution lands in a follow-up PR; v1 of this rename
  parses typed entries and validates the local-kind subset while
  the resolver wiring is finished.

Cross-boundary mechanism: direct JSONL read of the active impl-
plugin's work-items store. Only `livespec-impl-plaintext` is
supported in v1; other plugins receive a `skipped` Finding.

Legacy bare-string entries (pre-v072 format) are tolerated for
closed records (treated as implicit local lookups); open records
with bare-string entries fire `fail` because v072 requires the
typed-dict form. The impl-plugin's data-migration step is the
proper place to convert legacy entries; this tolerance exists to
keep historical records readable.

Cross-repo resolution scope: when an open record's typed
`depends_on` entry carries a non-`local` `kind`, the check fires
`fail` with a "cross-repo resolution not yet wired" narration.
Wiring `livespec_runtime.cross_repo.resolve_ref` into this check
is tracked as a follow-up.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from livespec_runtime.cross_repo.types import LocalDependency
from returns.io import IOResult, IOSuccess
from returns.result import Success

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import cross_repo as cross_repo_parse
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-no-orphan-dependency")
_SUPPORTED_PLUGINS: frozenset[str] = frozenset({"livespec-impl-plaintext"})
_DEFAULT_WORK_ITEMS_PATH: str = "work-items.jsonl"


def _make_finding(
    *,
    ctx: DoctorContext,
    status: str,
    message: str,
    path: str | None = None,
) -> Finding:
    """Build a Finding with the check's SLUG + spec_root."""
    return Finding(
        check_id=SLUG,
        status=status,  # type: ignore[arg-type]
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


def _orphan(*, item_id: str, dep_id: str, kind: str) -> tuple[str, str]:
    """Format the (item_id, dep_label) pair used in the fail narration."""
    return (item_id, f"{dep_id} (kind={kind})")


def _check_str_entry(
    *,
    item_id: str,
    record_status: str,
    raw: str,
    index: dict[str, dict[str, Any]],
) -> tuple[str, str] | None:
    """Handle a legacy bare-string entry — fail for open records, tolerate closed."""
    if record_status != "closed":
        return _orphan(item_id=item_id, dep_id=raw, kind="bare-string (data-migration pending)")
    if raw not in index:
        return _orphan(item_id=item_id, dep_id=raw, kind="local-legacy")
    return None


def _check_dict_entry(
    *,
    item_id: str,
    record_status: str,
    raw: dict[str, Any],
    index: dict[str, dict[str, Any]],
) -> tuple[str, str] | None:
    """Handle a typed-dict entry: parse, then dispatch on kind."""
    parsed_result = cross_repo_parse.parse_entry(parsed=raw)
    if not isinstance(parsed_result, Success):
        if record_status == "closed":
            return None
        return _orphan(item_id=item_id, dep_id=str(raw), kind="schema-error")
    entry = parsed_result.unwrap()
    if isinstance(entry, LocalDependency):
        if entry.work_item_id in index:
            return None
        return _orphan(item_id=item_id, dep_id=entry.work_item_id, kind="local")
    if record_status == "closed":
        return None
    return _orphan(
        item_id=item_id,
        dep_id=str(raw),
        kind=f"{entry.kind} (cross-repo resolver wiring deferred)",
    )


def _check_raw(
    *,
    item_id: str,
    record_status: str,
    raw: Any,
    index: dict[str, dict[str, Any]],
) -> tuple[str, str] | None:
    """Dispatch on raw entry shape (str / dict / other)."""
    if isinstance(raw, str):
        return _check_str_entry(item_id=item_id, record_status=record_status, raw=raw, index=index)
    if isinstance(raw, dict):
        return _check_dict_entry(item_id=item_id, record_status=record_status, raw=raw, index=index)
    if record_status == "closed":
        return None
    return _orphan(item_id=item_id, dep_id=str(raw), kind="malformed (non-dict)")


def _find_orphans(*, index: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    """Walk every record's depends_on; return sorted orphan pairs."""
    orphans: list[tuple[str, str]] = []
    for item_id, record in index.items():
        deps = record.get("depends_on")
        if not isinstance(deps, list):
            continue
        status_value = record.get("status")
        record_status = status_value if isinstance(status_value, str) else ""
        for raw in deps:
            orphan = _check_raw(item_id=item_id, record_status=record_status, raw=raw, index=index)
            if orphan is not None:
                orphans.append(orphan)
    return sorted(orphans)


def _resolve_work_items_path(*, ctx: DoctorContext, config: dict[str, Any]) -> Path | None:
    """Return the work-items.jsonl path when impl-plugin is in the supported set."""
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
            _make_finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "no-orphan-dependency: .livespec.jsonc root is not an " "object; check skipped"
                ),
            )
        )
    work_items_path = _resolve_work_items_path(ctx=ctx, config=parsed)
    if work_items_path is None:
        return IOSuccess(
            _make_finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "no-orphan-dependency: active impl-plugin is not in the v1 "
                    "supported set (livespec-impl-plaintext); check skipped"
                ),
            )
        )
    if not work_items_path.exists():
        return IOSuccess(
            _make_finding(
                ctx=ctx,
                status="pass",
                message=(
                    f"no-orphan-dependency: work-items store at "
                    f"{work_items_path} not present yet; no dependencies to check"
                ),
            )
        )
    return fs.read_text(path=work_items_path).bind(
        lambda text: IOSuccess(
            _evaluate_text(ctx=ctx, jsonl_text=text, work_items_path=work_items_path)
        )
    )


def _evaluate_text(*, ctx: DoctorContext, jsonl_text: str, work_items_path: Path) -> Finding:
    """Apply the invariant against the JSONL text content."""
    index = _materialize_records(jsonl_text=jsonl_text)
    orphans = _find_orphans(index=index)
    if not orphans:
        return _make_finding(
            ctx=ctx,
            status="pass",
            message=(
                f"no-orphan-dependency: every depends_on reference resolves "
                f"({len(index)} work-items scanned)"
            ),
        )
    pairs_joined = ", ".join(f"{item_id}→{missing}" for item_id, missing in orphans)
    return _make_finding(
        ctx=ctx,
        status="fail",
        message=(
            f"no-orphan-dependency: {len(orphans)} unresolved depends_on "
            f"reference(s): {pairs_joined}. Either add the missing work-item(s) "
            "or remove the stale depends_on entry."
        ),
        path=str(work_items_path),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-orphan-dependency against `ctx`."""
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
        .bind(lambda parsed: _evaluate(ctx=ctx, parsed=parsed))
        .lash(
            lambda err: IOSuccess(
                _make_finding(
                    ctx=ctx,
                    status="skipped",
                    message=(
                        f"no-orphan-dependency: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                )
            )
        )
    )
