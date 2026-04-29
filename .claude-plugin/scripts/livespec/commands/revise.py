"""livespec.commands.revise — supervisor for `bin/revise.py`.

v032 TDD redo cycle 13: smallest impl that drives the cycle-12
outside-in integration test to Green. Per PROPOSAL.md §"`revise`"
lines 2411-2452 (the deterministic file-shaping work order) +
§"Revision file format" lines 3037-3097 + Plan §"Phase 3" lines
1417-1437 (post-Case-B reconciliation at commit 72db010), the
supervisor:

1. Parses `--revise-json <path> [--author <id>]` via argparse.
2. Reads + JSON-parses the revise payload (no schema validation
   yet — same deferral pattern as seed cycle 12 and propose-change
   cycle 11).
3. Determines the next version `vNNN` by scanning
   `<spec-root>/history/v???/` directories for the max
   integer NNN and incrementing. Zero-padded per PROPOSAL.md
   line 1017-1018.
4. Creates `<spec-root>/history/vNNN/` and
   `<spec-root>/history/vNNN/proposed_changes/` directories.
5. For each decision in `decisions[]`:
   - If `decision in {"accept", "modify"}`, writes each
     `resulting_files[]` entry to its declared path (working-spec
     update).
   - Byte-moves (read text, write to new path, unlink original)
     `<spec-root>/proposed_changes/<topic>.md` →
     `<spec-root>/history/vNNN/proposed_changes/<topic>.md`. Uses
     `<topic>` as the stem; full collision-disambiguation `-N`
     suffix handling per PROPOSAL.md lines 2437-2449 is Phase 7
     widening.
   - Composes + writes the paired
     `<spec-root>/history/vNNN/proposed_changes/<topic>-revision.md`
     per the canonical revision format (front-matter +
     `## Decision and Rationale` + `## Resulting Changes` for
     accept/modify or `## Rejection Notes` for reject).
6. Snapshots each working-spec file named in any decision's
   `resulting_files[]` to its history-vNNN/<rel-to-spec-root>
   counterpart so the version archive contains the post-revise
   spec contents.

Smallest-thing-that-could-possibly-work scope per the briefing:

- `<spec-root>` is hardcoded to `"SPECIFICATION"` (matches seed
  cycle 4 and propose-change cycle 11). `--spec-target <path>`
  for sub-spec routing is deferred until a test exercises it.
- Topic-stem-to-filename mapping is identity (no collision
  disambiguation `-N` suffix). PROPOSAL.md lines 2437-2449
  full collision handling is Phase 7 widening.
- Author resolution at Phase 3 minimum-viable: simplest
  two-source rule per the seed/propose-change precedent
  (cycle 8 + cycle 11) — `--author` flag if non-empty, else
  the cycle-8 `livespec.io.git.current_user_or_unknown()` for
  `author_human`. `author_llm` follows the simpler precedence:
  `--author` flag first, payload `author` field second,
  `"unknown-llm"` fallback. Full 4-source precedence
  (PROPOSAL.md lines 3058-3068) is Phase 7 widening.
- Payload schema validation against `revise_input.schema.json`
  is deferred until a failure-path test forces it.
- Byte-fidelity for the move uses utf-8 read+write round-trip
  via `io.fs.write_text`. A dedicated `io.fs.write_bytes`
  primitive is deferred until a non-ASCII / binary content
  test forces it.
- ROP plumbing (`@impure_safe`, `IOResult`, factory-shape
  validators) is deferred until a failure-path test forces it
  or the post-v032 ROP-lift cycle adds it uniformly.
- The "active template's versioned spec files" copied at step 6
  is currently scoped to whatever files appear in any decision's
  `resulting_files[]`. A multi-file or template-config-driven
  test will force broader coverage; for cycle 13 this matches
  the integration test's pre-condition.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from livespec.io.fs import write_text
from livespec.io.git import current_user_or_unknown

__all__: list[str] = ["main"]

_VERSION_DIR_PATTERN = re.compile(r"^v(\d{3})$")


@dataclass(frozen=True, kw_only=True, slots=True)
class _RevisionContext:
    """Per-invocation shared context threaded into per-decision processing."""

    cwd: Path
    spec_root: str
    next_version_dir: Path
    revised_at: str
    author_human: str
    author_llm: str


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="revise", exit_on_error=False)
    parser.add_argument("--revise-json", required=True, type=Path)
    parser.add_argument("--author", default=None)
    return parser


def _next_version(*, history_dir: Path) -> str:
    if not history_dir.is_dir():
        return "v001"
    max_seen = 0
    for child in history_dir.iterdir():
        match = _VERSION_DIR_PATTERN.match(child.name)
        if child.is_dir() and match is not None:
            max_seen = max(max_seen, int(match.group(1)))
    return f"v{max_seen + 1:03d}"


def _resolve_author_llm(*, cli_author: str | None, payload_author: str | None) -> str:
    if cli_author is not None and cli_author != "":
        return cli_author
    if payload_author is not None and payload_author != "":
        return payload_author
    return "unknown-llm"


def _byte_move(*, source: Path, destination: Path) -> None:
    content = source.read_text(encoding="utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_text(path=destination, content=content)
    source.unlink()


def _render_revision_md(*, decision: dict[str, object], context: _RevisionContext) -> str:
    topic = cast("str", decision["proposal_topic"])
    decision_kind = cast("str", decision["decision"])
    rationale = cast("str", decision["rationale"])
    modifications = cast("str", decision.get("modifications", ""))
    resulting_files = cast("list[dict[str, str]]", decision.get("resulting_files", []))
    front_matter = (
        f"---\nproposal: {topic}.md\ndecision: {decision_kind}\n"
        f"revised_at: {context.revised_at}\nauthor_human: {context.author_human}\n"
        f"author_llm: {context.author_llm}\n---\n"
    )
    body = f"\n## Decision and Rationale\n\n{rationale}\n"
    if decision_kind == "modify":
        body += f"\n## Modifications\n\n{modifications}\n"
    if decision_kind in {"accept", "modify"}:
        files_block = "\n".join(f"- {entry['path']}" for entry in resulting_files)
        body += f"\n## Resulting Changes\n\n{files_block}\n"
    if decision_kind == "reject":
        body += "\n## Rejection Notes\n\nrejected during revise\n"
    return front_matter + body


def _process_decision(*, decision: dict[str, object], context: _RevisionContext) -> None:
    topic = cast("str", decision["proposal_topic"])
    decision_kind = cast("str", decision["decision"])
    resulting_files = cast("list[dict[str, str]]", decision.get("resulting_files", []))
    if decision_kind in {"accept", "modify"}:
        for entry in resulting_files:
            working_path = context.cwd / entry["path"]
            working_path.parent.mkdir(parents=True, exist_ok=True)
            write_text(path=working_path, content=entry["content"])
    source_proposal = context.cwd / context.spec_root / "proposed_changes" / f"{topic}.md"
    moved_proposal = context.next_version_dir / "proposed_changes" / f"{topic}.md"
    _byte_move(source=source_proposal, destination=moved_proposal)
    revision_md = _render_revision_md(decision=decision, context=context)
    write_text(
        path=context.next_version_dir / "proposed_changes" / f"{topic}-revision.md",
        content=revision_md,
    )


def _snapshot_resulting_files_to_history(
    *, decisions: list[dict[str, object]], context: _RevisionContext
) -> None:
    seen: set[str] = set()
    for decision in decisions:
        resulting_files = cast("list[dict[str, str]]", decision.get("resulting_files", []))
        for entry in resulting_files:
            rel_path = entry["path"]
            if rel_path in seen:
                continue
            seen.add(rel_path)
            if not rel_path.startswith(context.spec_root + "/"):
                continue
            rel_to_spec_root = rel_path[len(context.spec_root) + 1 :]
            history_path = context.next_version_dir / rel_to_spec_root
            history_path.parent.mkdir(parents=True, exist_ok=True)
            write_text(path=history_path, content=entry["content"])


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:])
    revise_json_path: Path = args.revise_json
    payload = json.loads(revise_json_path.read_text(encoding="utf-8"))
    decisions = cast("list[dict[str, object]]", payload["decisions"])
    payload_author = cast("str | None", payload.get("author"))
    cwd = Path.cwd()
    spec_root = "SPECIFICATION"
    history_dir = cwd / spec_root / "history"
    next_version = _next_version(history_dir=history_dir)
    next_version_dir = history_dir / next_version
    (next_version_dir / "proposed_changes").mkdir(parents=True, exist_ok=True)
    revised_at = (
        datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    context = _RevisionContext(
        cwd=cwd,
        spec_root=spec_root,
        next_version_dir=next_version_dir,
        revised_at=revised_at,
        author_human=current_user_or_unknown(),
        author_llm=_resolve_author_llm(cli_author=args.author, payload_author=payload_author),
    )
    for decision in decisions:
        _process_decision(decision=decision, context=context)
    _snapshot_resulting_files_to_history(decisions=decisions, context=context)
    return 0
