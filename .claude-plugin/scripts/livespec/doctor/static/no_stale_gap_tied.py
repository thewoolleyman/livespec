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
"""Static-phase doctor check: no_stale_gap_tied.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-stale-gap-tied`":

  A gap-tied open work item whose underlying gap no longer surfaces in a
  fresh impl-plugin gap-detection run MUST be closed via a non-fix
  disposition (`spec-revised`, `no-longer-applicable`,
  `resolved-out-of-band`, or equivalent administrative reason). The
  check fires `warn` (NOT `fail`) per the productivity-grade
  housekeeping classification.

Cross-boundary mechanism:

  The spec describes this check as "invoking the active impl-plugin's
  `detect-impl-gaps --json` thin-transport skill at check time".
  In v1 (this implementation), the check applies the same
  MUST / MUST NOT / SHOULD / SHOULD NOT enumeration + stable-hash
  gap-id derivation that `livespec-impl-plaintext`'s `detect-impl-gaps`
  applies, against the same live `<spec-root>/` content. The
  derivation MUST stay in lockstep with the impl-plugin's; a future
  refinement will replace the duplicated logic with a subprocess
  invocation of `<impl-plugin>:detect-impl-gaps --json` (or extract
  the shared detector into `livespec_runtime`).

  Only the `livespec-impl-plaintext` backend is supported in v1
  (JSONL store at the path declared by `<plugin>.work_items_path`).
"""

from __future__ import annotations

import hashlib
import re
from base64 import b32encode
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


SLUG: CheckId = CheckId("doctor-no-stale-gap-tied")
_SUPPORTED_PLUGINS: frozenset[str] = frozenset({"livespec-impl-plaintext"})
_DEFAULT_WORK_ITEMS_PATH: str = "work-items.jsonl"
_RULE_KEYWORD_PATTERN: re.Pattern[str] = re.compile(r"\b(MUST NOT|SHOULD NOT|MUST|SHOULD)\b")
_HEADING_PATTERN: re.Pattern[str] = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_CODE_FENCE_PATTERN: re.Pattern[str] = re.compile(r"^\s*```")
_GAP_ID_LENGTH: int = 8


def _pass(*, ctx: DoctorContext, message: str) -> Finding:
    return Finding(
        check_id=SLUG,
        status="pass",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _skipped(*, ctx: DoctorContext, message: str) -> Finding:
    return Finding(
        check_id=SLUG,
        status="skipped",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _warn(*, ctx: DoctorContext, message: str, path: str | None) -> Finding:
    return Finding(
        check_id=SLUG,
        status="warn",
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


def _open_gap_tied_items(*, index: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    """Return (work_item_id, gap_id) pairs for open gap-tied work-items."""
    pairs: list[tuple[str, str]] = []
    for item_id, record in index.items():
        if record.get("origin") != "gap-tied":
            continue
        if record.get("status") not in ("open", "in_progress"):
            continue
        gap_id = record.get("gap_id")
        if not isinstance(gap_id, str):
            continue
        pairs.append((item_id, gap_id))
    pairs.sort()
    return pairs


def _push_heading(*, stack: list[str], level: int, title: str) -> None:
    while len(stack) >= level:
        _ = stack.pop()
    while len(stack) < level - 1:
        stack.append("")
    stack.append(title)


def _derive_gap_id(*, spec_file: str, heading_path: str, rule_text: str) -> str:
    payload = f"{spec_file}\x1f{heading_path}\x1f{rule_text}".encode()
    digest = hashlib.sha256(payload).digest()
    suffix = b32encode(digest).decode("ascii").rstrip("=").lower()[:_GAP_ID_LENGTH]
    return f"gap-{suffix}"


def _detect_gap_ids(*, spec_root: Path) -> set[str]:
    """Enumerate gap-ids by scanning the live spec tree.

    Mirrors `livespec_impl_plaintext.commands.detect_impl_gaps`'s
    detection logic byte-for-byte. v1 shortcut — see module docstring.
    """
    gap_ids: set[str] = set()
    for candidate in sorted(spec_root.rglob("*.md")):
        relative_parts = candidate.relative_to(spec_root).parts
        if any(part in ("history", "proposed_changes") for part in relative_parts):
            continue
        spec_file = str(candidate.relative_to(spec_root))
        content = candidate.read_text(encoding="utf-8")
        heading_stack: list[str] = []
        in_code_fence = False
        for raw_line in content.splitlines():
            if _CODE_FENCE_PATTERN.match(raw_line):
                in_code_fence = not in_code_fence
                continue
            if in_code_fence:
                continue
            heading_match = _HEADING_PATTERN.match(raw_line)
            if heading_match is not None:
                level = len(heading_match.group(1))
                title = heading_match.group(2)
                _push_heading(stack=heading_stack, level=level, title=title)
                continue
            if _RULE_KEYWORD_PATTERN.search(raw_line) is None:
                continue
            rule_text = raw_line.strip()
            heading_path = " > ".join(heading_stack) if heading_stack else "(top)"
            gap_ids.add(
                _derive_gap_id(spec_file=spec_file, heading_path=heading_path, rule_text=rule_text)
            )
    return gap_ids


def _resolve_work_items_path(*, ctx: DoctorContext, config: dict[str, Any]) -> Path | None:
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
    if not isinstance(parsed, dict):
        return IOSuccess(
            _skipped(
                ctx=ctx,
                message="no-stale-gap-tied: .livespec.jsonc root is not an object; check skipped",
            )
        )
    work_items_path = _resolve_work_items_path(ctx=ctx, config=parsed)
    if work_items_path is None:
        return IOSuccess(
            _skipped(
                ctx=ctx,
                message=(
                    "no-stale-gap-tied: active impl-plugin is not in the v1 supported set "
                    "(livespec-impl-plaintext); check skipped"
                ),
            ),
        )
    if not work_items_path.exists():
        return IOSuccess(
            _pass(
                ctx=ctx,
                message=(
                    f"no-stale-gap-tied: work-items store at {work_items_path} not present yet; "
                    "no gap-tied items to check"
                ),
            ),
        )
    return fs.read_text(path=work_items_path).bind(
        lambda text: IOSuccess(
            _evaluate_text(ctx=ctx, jsonl_text=text, work_items_path=work_items_path)
        ),
    )


def _evaluate_text(*, ctx: DoctorContext, jsonl_text: str, work_items_path: Path) -> Finding:
    index = _materialize_records(jsonl_text=jsonl_text)
    open_pairs = _open_gap_tied_items(index=index)
    if not open_pairs:
        return _pass(
            ctx=ctx,
            message=(
                f"no-stale-gap-tied: no open gap-tied work-items "
                f"({len(index)} work-items scanned)"
            ),
        )
    current_gap_ids = _detect_gap_ids(spec_root=ctx.spec_root)
    stale = [(item_id, gap_id) for item_id, gap_id in open_pairs if gap_id not in current_gap_ids]
    if not stale:
        return _pass(
            ctx=ctx,
            message=(
                f"no-stale-gap-tied: all {len(open_pairs)} open gap-tied work-item(s) "
                f"have gap-ids present in the current spec"
            ),
        )
    ids_joined = ", ".join(f"{item_id}({gap_id})" for item_id, gap_id in stale)
    return _warn(
        ctx=ctx,
        message=(
            f"no-stale-gap-tied: {len(stale)} open gap-tied work-item(s) whose gap-id "
            f"no longer surfaces in a fresh detection run: {ids_joined}. "
            "Close each via a non-fix disposition (spec-revised, no-longer-applicable, "
            "resolved-out-of-band, or equivalent administrative reason)."
        ),
        path=str(work_items_path),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-stale-gap-tied against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc`, resolves the active
    impl-plugin's work-items JSONL path, materializes the records,
    enumerates the live spec's current gap-id set, and warns when an
    open gap-tied work-item's gap_id is absent from that set.
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
                        f"no-stale-gap-tied: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
