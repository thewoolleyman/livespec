# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Static-phase doctor check: no_stalled_epic.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-stalled-epic`":

  A work-item with `type == "epic"` AND `status` in `{open, in_progress}`
  whose `depends_on` is non-empty AND every entry resolves to a closed
  work-item / PR / branch is "stalled" — the work it represents is
  logically complete but the epic record has not been transitioned to
  `closed`. The check fires `fail` (not `warn`) per the structural-not-
  staleness classification: an epic semantically aggregates its sub-
  tasks, so all blockers closed + epic open is a data-model
  contradiction.

  Empty `depends_on` is EXEMPT (vacuous-truth guard) — a freshly filed
  epic with no declared sub-tasks is not yet stalled.

  Unresolvable `depends_on` entries (referenced ids missing from the
  store, schema-malformed entries, or cross-repo entries resolving to
  `unknown`) MUST NOT fire `no-stalled-epic` — that drift class is
  `no-orphan-dependency`'s domain.

  When the epic's `depends_on` carries non-local typed entries
  (sibling_work_item / pull_request / branch), the check walks them
  via `livespec_runtime.cross_repo.resolve_ref` and treats any `open`
  external dependency as a legitimate stall reason (suppressing the
  fail). Resolved `closed` counts toward all-closed.

Cross-boundary mechanism:

  The spec describes this check as "querying the active impl-plugin's
  machine surface (the `list-work-items --json` thin-transport skill)".
  In v1 (this implementation), the check reads the impl-plugin's
  configured work-items store directly via the path declared in
  `.livespec.jsonc`.

  Only the `livespec-impl-plaintext` backend is supported in v1
  (JSONL store at the path declared by `<plugin>.work_items_path`).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from livespec_runtime.cross_repo.resolve import resolve_ref
from livespec_runtime.cross_repo.types import CrossRepoManifest, RefStatus
from returns.io import IOResult, IOSuccess
from returns.result import Success

from livespec.context import DoctorContext
from livespec.doctor.static._no_orphan_dependency_helpers import extract_manifest
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import cross_repo as cross_repo_parse
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


def _local_status(*, work_item_id: str, index: dict[str, dict[str, Any]]) -> RefStatus:
    """Return RefStatus for a same-repo id by scanning the materialized index."""
    record = index.get(work_item_id)
    if record is None:
        return RefStatus.UNKNOWN
    if record.get("status") == "closed":
        return RefStatus.CLOSED
    return RefStatus.OPEN


def _make_local_lookup(*, index: dict[str, dict[str, Any]]) -> Callable[[str], RefStatus]:
    """Build the local_status_lookup callable resolve_ref expects."""
    return lambda work_item_id: _local_status(work_item_id=work_item_id, index=index)


def _resolve_typed_dep(
    *,
    raw: dict[str, Any],
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> RefStatus:
    """Parse a typed-dict entry and dispatch through resolve_ref."""
    parsed_result = cross_repo_parse.parse_entry(parsed=raw)
    if not isinstance(parsed_result, Success):
        return RefStatus.UNKNOWN
    return resolve_ref(
        entry=parsed_result.unwrap(),
        manifest=manifest,
        local_status_lookup=_make_local_lookup(index=index),
    )


def _resolve_dep(
    *,
    raw: Any,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> RefStatus:
    """Return RefStatus for a single depends_on entry (bare-string or typed-dict)."""
    if isinstance(raw, str):
        return _local_status(work_item_id=raw, index=index)
    if isinstance(raw, dict):
        return _resolve_typed_dep(raw=raw, index=index, manifest=manifest)
    return RefStatus.UNKNOWN


def _find_stalled_epics(
    *,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> list[str]:
    """Return sorted ids of epics whose every depends_on entry resolves to CLOSED."""
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
        for raw in deps:
            if _resolve_dep(raw=raw, index=index, manifest=manifest) != RefStatus.CLOSED:
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
    manifest = extract_manifest(config=parsed)
    return fs.read_text(path=work_items_path).bind(
        lambda text: IOSuccess(
            _evaluate_text(
                ctx=ctx,
                jsonl_text=text,
                work_items_path=work_items_path,
                manifest=manifest,
            )
        ),
    )


def _evaluate_text(
    *,
    ctx: DoctorContext,
    jsonl_text: str,
    work_items_path: Path,
    manifest: CrossRepoManifest,
) -> Finding:
    """Apply the invariant against the JSONL text content."""
    index = _materialize_records(jsonl_text=jsonl_text)
    stalled = _find_stalled_epics(index=index, manifest=manifest)
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
        .bind(
            lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
        )
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
