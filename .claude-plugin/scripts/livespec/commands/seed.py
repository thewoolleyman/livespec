"""livespec.commands.seed — supervisor for `bin/seed.py`.

v032 TDD redo cycle 6: extends the cycle-5 sub-spec working-tree
materialization with the `<sub-spec-root>/history/v001/` snapshot
per PROPOSAL.md §"`seed`" lines 2014-2028 step 5 ("**(v018 Q1;
v020 Q1 uniform README)** For each sub-spec tree, create
`SPECIFICATION/templates/<template_name>/history/v001/` alongside
the main-spec history — including the sub-spec's own versioned
spec files and `proposed_changes/` subdir"). For every
`sub_specs[].files[]` entry whose path is under the sub-spec-root
(`SPECIFICATION/templates/<template_name>/`), the supervisor
copies the file to
`<sub-spec-root>/history/v001/<rel-to-sub-spec-root>` (basename
per PROPOSAL.md lines 981-986). The empty
`<sub-spec-root>/history/v001/proposed_changes/` subdir is created
alongside.

The main-spec and sub-spec write+history loops are intentionally
duplicated rather than extracted to a helper — Kent Beck's
"tolerate two duplicates; refactor on three" rule defers the
abstraction. The next likely third consumer is the auto-captured
seed proposed-change (PROPOSAL.md lines 2043-2064), which will
also write a markdown file to `<spec-root>/history/v001/proposed_changes/`
and so will reuse the same write pattern.

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
forces them), no auto-captured seed proposed-change (deferred
until that test cycle), parent-directory creation inlined here
rather than authored as a second `livespec.io.fs` primitive
(consumer pressure for an `io.fs.mkdir` seam will be decided when
a `check-no-write-direct` test forces it).

Refactor toward `.livespec.jsonc` content materialization
(commented schema skeleton per PROPOSAL.md §"`seed`" lines
1894-1924), payload validation, auto-captured seed
proposed-change/revision (lines 2043-2064), per-version README
snapshots, skill-owned README paragraphs, and ROP-on-the-railway
composition will land in subsequent cycles when content
assertions, failure-path tests, or a second `io/fs.py` consumer
force them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from livespec.io.fs import write_text

__all__: list[str] = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seed", exit_on_error=False)
    parser.add_argument("--seed-json", required=True, type=Path)
    return parser


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
        sub_spec_root_rel = f"{spec_root}/templates/{sub_spec['template_name']}"
        sub_history_v001 = cwd / sub_spec_root_rel / "history" / "v001"
        for entry in sub_spec["files"]:
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
    return 0
