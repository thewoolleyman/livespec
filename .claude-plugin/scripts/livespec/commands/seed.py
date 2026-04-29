"""livespec.commands.seed — supervisor for `bin/seed.py`.

v032 TDD redo cycle 9: adds the idempotency-refusal pre-check
per PROPOSAL.md §"`seed`" lines 2065-2071 ("if any
template-declared target file already exists at its target path,
`seed` MUST refuse and list the existing files") and §"Sub-command
lifecycle orchestration" line 2128 ("Seed's idempotency refusal
stays strict; there is no `--force-reseed` flag"). Before any
writes, the supervisor collects the project-root-relative paths
in `payload["files"]` and `payload["sub_specs"][].files`
(template-declared target files per PROPOSAL.md line 1902 —
`.livespec.jsonc` is wrapper-owned and goes through its own
three-branch logic). If any candidate already exists at its
target path, the supervisor emits a structured-error event via
`structlog.get_logger().error(...)` (the canonical stderr seam
per python-skill-script-style-requirements.md §"Logging" /
§"Output channels" — `sys.stderr.write` is banned in supervisor
`main()` per the three-designated-surfaces rule, so structlog is
the only legitimate path) with `existing_files=[...]` kwarg, then
returns exit code `3` (`PreconditionError` per PROPOSAL.md lines
2839-2843).

The pre-check runs against fresh-cwd state; partial-write rollback
on mid-seed failure is a separate behavior covered by a future
cycle. The check enumerates only template-declared target files;
auto-captured seed.md + seed-revision.md and history snapshots
are wrapper-generated artifacts NOT in the strict idempotency
set per PROPOSAL.md line 1902 wording.

v032 TDD redo cycle 8: completes the auto-captured proposal +
revision pair at `<spec-root>/history/v001/proposed_changes/`. The
cycle-7 `seed.md` is now joined by `seed-revision.md` per
PROPOSAL.md §"`seed`" lines 2058-2064 and the canonical revision
format (PROPOSAL.md §"Revision file format" lines 3037-3097). The
revision file carries front-matter `proposal: seed.md`,
`decision: accept`, `revised_at: <UTC ISO-8601 seconds>` (matching
the paired seed.md `created_at` exactly — both files share the
single timestamp captured at invocation), `author_human: <git user
or "unknown">`, `author_llm: livespec-seed`, followed by
`## Decision and Rationale` ("auto-accepted during seed") and
`## Resulting Changes` (every payload-`files[]` path).

`author_human` is sourced via the new `livespec.io.git` module
(specifically `current_user_or_unknown() -> str`), pulled into
existence under consumer pressure for the architectural seam
(subprocess effects live exclusively in `livespec/io/**` per
PROPOSAL §"Skill layout" / `python-skill-script-style-requirements.md`).
The cycle-8 helper collapses PROPOSAL §"Git" lines 685-711's
three-branch `IOResult[str, GitUnavailableError]` semantics into a
plain `str` return — `"<name> <email>"` on full success, the
literal `"unknown"` on ANY non-success path. Refactor to the full
three-branch IOResult shape lands when a failure-path test (e.g.,
seed-aborts-when-git-unavailable per PROPOSAL.md line 705-708)
forces the discrimination.

The shared timestamp is captured once in
`_write_auto_captured_seed_pair` and threaded into both
`_render_seed_md` (as `created_at`) and `_render_seed_revision_md`
(as `revised_at`), so the two files agree byte-for-byte on the
moment the seed completed.

The main-spec and sub-spec write+history loops remain duplicated
per Kent Beck's "tolerate two duplicates; refactor on three" —
the auto-captured seed pair uses composed-string writes rather
than the file-copy loop pattern, so it does NOT trigger the
third-consumer refactor. That refactor lands when a genuine third
file-copy consumer appears.

`spec_root` is currently hardcoded to `"SPECIFICATION"` (the
`livespec` template default per `template_config.schema.json`).
This will refactor to data-driven resolution (read the template's
`template.json`) when the `minimal` template's `spec_root: "./"`
or a custom-template test forces it.

Smallest-thing-that-could-possibly-work — no validation, no ROP
plumbing, no per-version README copy (deferred until a content
assertion / payload-with-README forces it; PROPOSAL.md lines
2019-2020 mandate sub-spec README presence but the smallest
payload exercising the history-v001 path doesn't require one),
no skill-owned `proposed_changes/README.md` and `history/README.md`
paragraphs (lines 2025-2028; deferred until a content assertion
forces them), no idempotency-refusal (lines 2065-2071; deferred
to its own cycle), no payload schema validation (deferred), no
post-step doctor-static invocation (deferred), no typed
front-matter dataclass (deferred until a second consumer like
`propose_change.py` composing its own front-matter forces it).

Refactor toward `.livespec.jsonc` content materialization
(commented schema skeleton per PROPOSAL.md §"`seed`" lines
1894-1924), payload validation, per-version README snapshots,
skill-owned README paragraphs, idempotency-refusal, post-step
doctor-static, data-driven spec_root, full IOResult three-branch
git semantics, and ROP-on-the-railway composition will land in
subsequent cycles when content assertions, failure-path tests, or
new consumers force them.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import structlog

from livespec.io.fs import write_text
from livespec.io.git import current_user_or_unknown

_PRECONDITION_EXIT_CODE = 3

__all__: list[str] = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seed", exit_on_error=False)
    parser.add_argument("--seed-json", required=True, type=Path)
    return parser


def _existing_target_files(*, cwd: Path, payload: dict[str, object]) -> list[str]:
    candidates: list[str] = []
    files = cast("list[dict[str, str]]", payload["files"])
    candidates.extend(entry["path"] for entry in files)
    sub_specs = cast("list[dict[str, object]]", payload["sub_specs"])
    for sub_spec in sub_specs:
        sub_files = cast("list[dict[str, str]]", sub_spec["files"])
        candidates.extend(entry["path"] for entry in sub_files)
    return [path for path in candidates if (cwd / path).exists()]


def _write_sub_spec_tree(*, cwd: Path, spec_root: str, sub_spec: dict[str, object]) -> None:
    sub_spec_root_rel = f"{spec_root}/templates/{sub_spec['template_name']}"
    sub_history_v001 = cwd / sub_spec_root_rel / "history" / "v001"
    files = cast("list[dict[str, str]]", sub_spec["files"])
    for entry in files:
        rel_path = entry["path"]
        entry_path = cwd / rel_path
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path=entry_path, content=entry["content"])
        if rel_path.startswith(sub_spec_root_rel + "/"):
            rel_to_sub_root = rel_path[len(sub_spec_root_rel) + 1 :]
            history_path = sub_history_v001 / rel_to_sub_root
            history_path.parent.mkdir(parents=True, exist_ok=True)
            write_text(path=history_path, content=entry["content"])
    (sub_history_v001 / "proposed_changes").mkdir(parents=True, exist_ok=True)


def _write_auto_captured_seed_pair(*, payload: dict[str, object], history_v001: Path) -> None:
    created_at = (
        datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    files = cast("list[dict[str, str]]", payload["files"])
    intent = cast("str", payload["intent"])
    file_paths = [entry["path"] for entry in files]
    proposed_changes_dir = history_v001 / "proposed_changes"
    seed_md = _render_seed_md(file_paths=file_paths, intent=intent, created_at=created_at)
    write_text(path=proposed_changes_dir / "seed.md", content=seed_md)
    seed_revision_md = _render_seed_revision_md(
        file_paths=file_paths,
        revised_at=created_at,
        author_human=current_user_or_unknown(),
    )
    write_text(path=proposed_changes_dir / "seed-revision.md", content=seed_revision_md)


def _render_seed_md(*, file_paths: list[str], intent: str, created_at: str) -> str:
    target_files_block = "\n".join(f"- {p}" for p in file_paths)
    return (
        "---\n"
        "topic: seed\n"
        "author: livespec-seed\n"
        f"created_at: {created_at}\n"
        "---\n"
        "\n"
        "## Proposal: seed\n"
        "\n"
        "### Target specification files\n"
        "\n"
        f"{target_files_block}\n"
        "\n"
        "### Summary\n"
        "\n"
        "Initial seed of the specification from user-provided intent.\n"
        "\n"
        "### Motivation\n"
        "\n"
        f"{intent}\n"
        "\n"
        "### Proposed Changes\n"
        "\n"
        f"{intent}\n"
    )


def _render_seed_revision_md(*, file_paths: list[str], revised_at: str, author_human: str) -> str:
    resulting_files_block = "\n".join(f"- {p}" for p in file_paths)
    return (
        "---\n"
        "proposal: seed.md\n"
        "decision: accept\n"
        f"revised_at: {revised_at}\n"
        f"author_human: {author_human}\n"
        "author_llm: livespec-seed\n"
        "---\n"
        "\n"
        "## Decision and Rationale\n"
        "\n"
        "auto-accepted during seed\n"
        "\n"
        "## Resulting Changes\n"
        "\n"
        f"{resulting_files_block}\n"
    )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:])
    seed_json_path: Path = args.seed_json
    payload = json.loads(seed_json_path.read_text(encoding="utf-8"))
    cwd = Path.cwd()
    spec_root = "SPECIFICATION"
    existing = _existing_target_files(cwd=cwd, payload=payload)
    if existing:
        structlog.get_logger().error(
            "seed.idempotency_refusal",
            error="PreconditionError",
            message="seed refuses: template-declared target files already exist",
            existing_files=existing,
        )
        return _PRECONDITION_EXIT_CODE
    write_text(path=cwd / ".livespec.jsonc", content="{}\n")
    history_v001 = cwd / spec_root / "history" / "v001"
    for entry in payload["files"]:
        rel_path = entry["path"]
        entry_path = cwd / rel_path
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path=entry_path, content=entry["content"])
        if rel_path.startswith(spec_root + "/"):
            rel_to_spec_root = rel_path[len(spec_root) + 1 :]
            history_path = history_v001 / rel_to_spec_root
            history_path.parent.mkdir(parents=True, exist_ok=True)
            write_text(path=history_path, content=entry["content"])
    (history_v001 / "proposed_changes").mkdir(parents=True, exist_ok=True)
    for sub_spec in payload["sub_specs"]:
        _write_sub_spec_tree(cwd=cwd, spec_root=spec_root, sub_spec=sub_spec)
    _write_auto_captured_seed_pair(payload=payload, history_v001=history_v001)
    return 0
