"""Static-phase doctor check: no_stalled_epic.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-stalled-epic`" (v069):

  A work-item with `type == "epic"` AND `status` in `{open, in_progress}`
  whose `depends_on` is non-empty AND every entry resolves to a closed
  work-item is "stalled" — the work it represents is logically complete
  but the epic record has not been transitioned to `closed`. The check
  fires `fail` (not `warn`) per the structural-not-staleness
  classification: an epic semantically aggregates its sub-tasks, so all
  blockers closed + epic open is a data-model contradiction.

  Empty `depends_on` is EXEMPT (vacuous-truth guard) — a freshly filed
  epic with no declared sub-tasks is not yet stalled.

  Unresolvable `depends_on` entries (referenced ids missing from the
  store) MUST NOT fire `no-stalled-epic` — that drift class is
  `no-orphan-dependency`'s domain.

Cross-boundary mechanism:

  The spec describes this check as "querying the active impl-plugin's
  machine surface (the `list-work-items --json` thin-transport skill)".
  In v1 (this implementation), the check reads the impl-plugin's
  configured work-items store directly via the path declared in
  `.livespec.jsonc`. This is mechanically equivalent to the thin-
  transport skill (the skill is itself a pass-through to a JSONL
  read) but skips the cross-process invocation. A future refinement
  MAY add subprocess-based skill invocation when the cross-plugin
  abstraction layer lands; the invariant's semantics are stable
  regardless.

  Only the `livespec-impl-plaintext` backend is supported in v1
  (JSONL store at the path declared by `<plugin>.work_items_path`).
  Other impl-plugin backends (e.g., `livespec-impl-beads`) would need
  their own work-items-shape adapter; the check skips when the
  active plugin isn't recognized.
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


SLUG: CheckId = CheckId("doctor-no-stalled-epic")
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
    """Build a skipped-status Finding (preferred over fail when the active impl is unrecognized)."""
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
    """Parse JSONL text and return latest-record-per-id index.

    Matches `livespec_impl_plaintext.store.materialize_work_items` semantics:
    last record per `id` wins (append-only store invariant). Lines that
    fail to parse or lack an `id` field are skipped silently — schema
    integrity is the impl-plugin's concern, not this check's. The pure
    `livespec.parse.jsonc.loads` carries the `@safe`-decorated JSON
    parse, so this function takes no `try/except` (per the io-only
    raise-site rule).
    """
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


def _find_stalled_epics(*, index: dict[str, dict[str, Any]]) -> list[str]:
    """Return the sorted ids of epics that satisfy the stalled-epic predicate."""
    stalled: list[str] = []
    for item_id, record in index.items():
        if record.get("type") != "epic":
            continue
        status = record.get("status")
        if status not in ("open", "in_progress"):
            continue
        deps = record.get("depends_on")
        if not isinstance(deps, list) or len(deps) == 0:
            continue
        all_closed = True
        for dep_id in deps:
            if not isinstance(dep_id, str):
                all_closed = False
                break
            dep_record = index.get(dep_id)
            if dep_record is None:
                all_closed = False
                break
            if dep_record.get("status") != "closed":
                all_closed = False
                break
        if all_closed:
            stalled.append(item_id)
    return sorted(stalled)


def _resolve_work_items_path(*, ctx: DoctorContext, config: dict[str, Any]) -> Path | None:
    """Return the resolved work-items.jsonl path, or None if the active impl is unsupported.

    The `implementation.plugin` key names the active impl-plugin. When the
    plugin is in `_SUPPORTED_PLUGINS`, the per-plugin section's
    `work_items_path` (relative to project_root) names the JSONL store.
    Missing key falls back to the default `work-items.jsonl` at project root.
    """
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
                message="no-stalled-epic: .livespec.jsonc root is not an object; check skipped",
            )
        )
    work_items_path = _resolve_work_items_path(ctx=ctx, config=parsed)
    if work_items_path is None:
        return IOSuccess(
            _skipped(
                ctx=ctx,
                message=(
                    "no-stalled-epic: active impl-plugin is not in the v1 supported set "
                    "(livespec-impl-plaintext); check skipped"
                ),
            ),
        )
    if not work_items_path.exists():
        return IOSuccess(
            _pass(
                ctx=ctx,
                message=(
                    f"no-stalled-epic: work-items store at {work_items_path} not present yet; "
                    "no epics to check"
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
    stalled = _find_stalled_epics(index=index)
    if not stalled:
        return _pass(
            ctx=ctx,
            message=(
                f"no-stalled-epic: no epics with all-closed depends_on detected "
                f"({len(index)} work-items scanned)"
            ),
        )
    ids_joined = ", ".join(stalled)
    return _fail(
        ctx=ctx,
        message=(
            f"no-stalled-epic: {len(stalled)} epic(s) with all depends_on entries closed "
            f"but epic still open/in_progress: {ids_joined}. "
            "Close the epic with an appropriate resolution OR add fresh depends_on entries."
        ),
        path=str(work_items_path),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-stalled-epic against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc`, resolves the active
    impl-plugin's work-items JSONL path, materializes the records, and
    applies the no-stalled-epic predicate. Returns IOSuccess(Finding)
    on success (pass / fail / skipped). On config-read or JSONC-parse
    failure, the IOFailure track is lashed back into IOSuccess with a
    skipped-status Finding so the orchestrator's stdout contract stays
    uniform.
    """
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
                        f"no-stalled-epic: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
