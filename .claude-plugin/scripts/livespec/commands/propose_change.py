"""livespec.commands.propose_change — supervisor for `bin/propose_change.py`.

v032 TDD redo cycle 11: smallest impl that makes the outside-in
integration test go Green. Per PROPOSAL.md §"`propose-change`"
lines 2134-2278 + Plan §"Phase 3" lines 1389-1407 (minimum-viable
shape after the v032 Case-B plan reconciliation at commit
a627003): parse `--findings-json <path> <topic> [--author <id>]`,
read+JSON-parse the findings payload, compose a proposed-change
markdown file (front-matter + one `## Proposal: <name>` section
per finding via the field-copy mapping at PROPOSAL.md lines
2232-2242), and write to
`<spec-root>/proposed_changes/<topic>.md` via
`livespec.io.fs.write_text`.

Smallest-thing-that-could-possibly-work scope per the briefing:

- `<spec-root>` is hardcoded to `"SPECIFICATION"` (the `livespec`
  template default per `template_config.schema.json`). `--spec-target
  <path>` flag for sub-spec routing is deferred to a later cycle
  when the test exercises it.
- Topic regex check `^[a-z][a-z0-9]*(-[a-z0-9]+)*$` per
  `proposed_change_front_matter.schema.json`; rejection with exit 4
  if the topic does not match (PROPOSAL.md lines 2839-2843 maps
  `ValidationError` to exit 4). Full topic canonicalization (v015 O3
  lowercase + non-alphanumeric → hyphen + truncate) is Phase 7 work
  per Plan lines 1399-1407.
- Author resolution at Phase 3 minimum-viable: simplest two-source
  rule per the briefing — `--author <id>` flag if non-empty, else
  fall back to `livespec.io.git.current_user_or_unknown()` (the
  helper authored at cycle 8 for seed-revision's `author_human`).
  The full 4-source precedence (CLI → env → payload → "unknown-llm"
  per PROPOSAL.md lines 2194-2213) is Phase 7 widening.
- Payload schema validation against `proposal_findings.schema.json`
  is deferred until a failure-path test (malformed-payload exit 4
  per PROPOSAL.md lines 2156-2161) forces it; same deferral pattern
  as seed cycle 12 (payload validation deferred).
- Collision disambiguation (`-2`, `-3` suffixes per PROPOSAL.md
  lines 2256-2273) and `--reserve-suffix` (PROPOSAL.md lines
  2174-2193) are also Phase 7 widening.
- ROP plumbing (`@impure_safe`, `IOResult`, factory-shape
  validators) is deferred until either a failure-path test forces
  it or the post-v032 ROP-lift cycle adds it uniformly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import structlog

from livespec.io.fs import write_text
from livespec.io.git import current_user_or_unknown

__all__: list[str] = ["main"]

_VALIDATION_EXIT_CODE = 4
_TOPIC_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="propose-change", exit_on_error=False)
    parser.add_argument("--findings-json", required=True, type=Path)
    parser.add_argument("--author", default=None)
    parser.add_argument("topic")
    return parser


def _resolve_author(*, cli_author: str | None) -> str:
    if cli_author is not None and cli_author != "":
        return cli_author
    return current_user_or_unknown()


def _render_proposed_change_md(
    *, topic: str, author: str, created_at: str, findings: list[dict[str, object]]
) -> str:
    front_matter = f"---\ntopic: {topic}\nauthor: {author}\ncreated_at: {created_at}\n---\n"
    sections = [_render_proposal_section(finding=finding) for finding in findings]
    return front_matter + "\n" + "\n".join(sections)


def _render_proposal_section(*, finding: dict[str, object]) -> str:
    name = cast("str", finding["name"])
    target_spec_files = cast("list[str]", finding["target_spec_files"])
    summary = cast("str", finding["summary"])
    motivation = cast("str", finding["motivation"])
    proposed_changes = cast("str", finding["proposed_changes"])
    target_block = "\n".join(f"- {p}" for p in target_spec_files)
    return (
        f"## Proposal: {name}\n"
        "\n"
        "### Target specification files\n"
        "\n"
        f"{target_block}\n"
        "\n"
        "### Summary\n"
        "\n"
        f"{summary}\n"
        "\n"
        "### Motivation\n"
        "\n"
        f"{motivation}\n"
        "\n"
        "### Proposed Changes\n"
        "\n"
        f"{proposed_changes}\n"
    )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:])
    topic: str = args.topic
    if not _TOPIC_PATTERN.match(topic):
        structlog.get_logger().error(
            "propose_change.topic_not_canonical",
            error="ValidationError",
            message="topic must match `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`",
            topic=topic,
        )
        return _VALIDATION_EXIT_CODE
    findings_path: Path = args.findings_json
    payload = json.loads(findings_path.read_text(encoding="utf-8"))
    findings = cast("list[dict[str, object]]", payload["findings"])
    author = _resolve_author(cli_author=args.author)
    created_at = (
        datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    rendered = _render_proposed_change_md(
        topic=topic, author=author, created_at=created_at, findings=findings
    )
    cwd = Path.cwd()
    spec_root = "SPECIFICATION"
    output_path = cwd / spec_root / "proposed_changes" / f"{topic}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path=output_path, content=rendered)
    return 0
