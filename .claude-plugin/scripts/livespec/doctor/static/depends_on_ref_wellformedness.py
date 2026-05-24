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
"""Static-phase doctor check: depends_on_ref_wellformedness.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants"
→ §"`depends_on-ref-wellformedness`":

  For every OPEN work-item's `depends_on` array, the invariant
  enforces:

  1. Discriminator present. Every entry MUST have a `kind` field
     whose value is one of `local`, `sibling_work_item`,
     `pull_request`, `branch`. Missing or unknown `kind` fires
     `fail`.
  2. Per-kind required fields present. `local` requires
     `work_item_id`; `sibling_work_item` requires `repo` and
     `work_item_id`; `pull_request` requires `repo` and `number`;
     `branch` requires `repo` and `name`. Missing required fields
     fire `fail` with the entry's index in the array.
  3. `repo` resolves to a configured target. For every entry with
     a `repo` field, the value MUST be a key in `.livespec.jsonc`'s
     `cross_repo_targets` block. Unresolvable `repo` values fire
     `fail` with the value and a hint pointing to the manifest.

  Closed records are out of scope (legacy bare-string entries and
  historical typed entries are tolerated to keep audit trail
  readable). Bare-string entries on open records fire `fail` under
  (1) since they lack a `kind` field; this overlaps with
  `no-orphan-dependency`'s data-migration narration but the two
  signals are complementary (well-formedness vs resolvability).

Cross-boundary mechanism: direct JSONL read of the active impl-
plugin's work-items store. Only `livespec-impl-plaintext` is
supported in v1; other plugins receive a `skipped` Finding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from livespec_runtime.cross_repo.types import CrossRepoManifest
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


SLUG: CheckId = CheckId("doctor-depends_on-ref-wellformedness")
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
        status=status,
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


def _entry_repo(*, entry: object) -> str | None:
    """Return the `repo` attribute if present, else None (LocalDependency has no repo)."""
    repo = getattr(entry, "repo", None)
    if isinstance(repo, str):
        return repo
    return None


def _check_entry(
    *,
    item_id: str,
    index_position: int,
    raw: Any,
    manifest: CrossRepoManifest,
) -> str | None:
    """Validate a single depends_on entry; return a failure narration or None."""
    if not isinstance(raw, dict):
        return (
            f"{item_id}#{index_position}: entry is not a typed object "
            f"(got {type(raw).__name__}); v072 requires typed-dict form"
        )
    parsed_result = cross_repo_parse.parse_entry(parsed=raw)
    if not isinstance(parsed_result, Success):
        err = parsed_result.failure()
        return f"{item_id}#{index_position}: {err}"
    entry = parsed_result.unwrap()
    repo = _entry_repo(entry=entry)
    if repo is not None and repo not in manifest.targets:
        return (
            f"{item_id}#{index_position}: repo {repo!r} not in "
            f".livespec.jsonc's `cross_repo_targets` block"
        )
    return None


def _find_failures(
    *,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> list[str]:
    """Walk every OPEN record's depends_on; return sorted failure narrations."""
    failures: list[str] = []
    for item_id, record in index.items():
        status_value = record.get("status")
        if status_value != "open":
            continue
        deps = record.get("depends_on")
        if not isinstance(deps, list):
            continue
        for position, raw in enumerate(deps):
            failure = _check_entry(
                item_id=item_id,
                index_position=position,
                raw=raw,
                manifest=manifest,
            )
            if failure is not None:
                failures.append(failure)
    return sorted(failures)


def _evaluate(*, ctx: DoctorContext, parsed: Any) -> IOResult[Finding, LivespecError]:
    """Resolve the work-items path and evaluate the invariant."""
    if not isinstance(parsed, dict):
        return IOSuccess(
            _make_finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "depends_on-ref-wellformedness: .livespec.jsonc root is not an "
                    "object; check skipped"
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
                    "depends_on-ref-wellformedness: active impl-plugin is not in the v1 "
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
                    f"depends_on-ref-wellformedness: work-items store at "
                    f"{work_items_path} not present yet; no entries to check"
                ),
            )
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
        )
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
    failures = _find_failures(index=index, manifest=manifest)
    if not failures:
        return _make_finding(
            ctx=ctx,
            status="pass",
            message=(
                f"depends_on-ref-wellformedness: every open work-item's depends_on "
                f"entries are well-formed ({len(index)} work-items scanned)"
            ),
        )
    joined = "; ".join(failures)
    return _make_finding(
        ctx=ctx,
        status="fail",
        message=(
            f"depends_on-ref-wellformedness: {len(failures)} ill-formed depends_on "
            f"entry(ies): {joined}."
        ),
        path=str(work_items_path),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run depends_on-ref-wellformedness against `ctx`."""
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(
            lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(lambda parsed: _evaluate(ctx=ctx, parsed=parsed))
        .lash(
            lambda err: IOSuccess(
                _make_finding(
                    ctx=ctx,
                    status="skipped",
                    message=(
                        f"depends_on-ref-wellformedness: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                )
            )
        )
    )
