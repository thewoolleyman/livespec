"""livespec.commands.seed — supervisor for `bin/seed.py`.

v032 TDD redo cycle 7: adds the auto-captured `seed.md`
proposed-change at `<spec-root>/history/v001/proposed_changes/seed.md`
per PROPOSAL.md §"`seed`" lines 2043-2057 and the canonical
proposed-change format (PROPOSAL.md §"Proposed-change file format"
lines 2939-3033). The wrapper composes a YAML-front-matter
markdown file with `topic: seed`, `author: livespec-seed`,
`created_at: <UTC ISO-8601 seconds>` (Z-suffixed), followed by
one `## Proposal: seed` section with `### Target specification
files` (every `payload["files"][i].path`, one per line),
`### Summary` (verbatim canonical text), `### Motivation`
(verbatim payload `intent`), and `### Proposed Changes`
(verbatim payload `intent` again). Sub-specs do NOT receive
their own auto-captured seed.md (PROPOSAL.md lines 2031-2035:
"the single main-spec seed artifact documents the whole
multi-tree creation").

The seed.md body is composed by the private `_render_seed_md`
helper — extracted under linter pressure (`PLR0915 Too many
statements` in `main`) and conceptually justified (a single
"build seed.md from payload + timestamp" responsibility). The
paired `seed-revision.md` (lines 2058-2064) is deferred to
cycle 8.

The main-spec and sub-spec write+history loops remain duplicated
per Kent Beck's "tolerate two duplicates; refactor on three" —
the auto-captured seed.md uses a separate composed-string write
path rather than the file-copy loop pattern, so it does NOT
trigger the third-consumer refactor. That refactor lands when a
genuine third file-copy consumer appears.

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
forces them), no paired seed-revision.md (cycle 8), no typed
front-matter dataclass (deferred until a second consumer like
`propose_change.py` composing its own front-matter forces it).

Refactor toward `.livespec.jsonc` content materialization
(commented schema skeleton per PROPOSAL.md §"`seed`" lines
1894-1924), payload validation, paired seed-revision.md,
per-version README snapshots, skill-owned README paragraphs,
data-driven spec_root, and ROP-on-the-railway composition will
land in subsequent cycles when content assertions, failure-path
tests, or a second `io/fs.py` consumer force them.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from livespec.io.fs import write_text

__all__: list[str] = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seed", exit_on_error=False)
    parser.add_argument("--seed-json", required=True, type=Path)
    return parser


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


def _write_auto_captured_seed_md(*, payload: dict[str, object], history_v001: Path) -> None:
    created_at = (
        datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    files = cast("list[dict[str, str]]", payload["files"])
    intent = cast("str", payload["intent"])
    file_paths = [entry["path"] for entry in files]
    seed_md = _render_seed_md(file_paths=file_paths, intent=intent, created_at=created_at)
    write_text(path=history_v001 / "proposed_changes" / "seed.md", content=seed_md)


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


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:])
    seed_json_path: Path = args.seed_json
    payload = json.loads(seed_json_path.read_text(encoding="utf-8"))
    cwd = Path.cwd()
    spec_root = "SPECIFICATION"
    write_text(path=cwd / ".livespec.jsonc", content="")
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
    _write_auto_captured_seed_md(payload=payload, history_v001=history_v001)
    return 0
