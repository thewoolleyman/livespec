"""livespec.commands.seed — supervisor for `bin/seed.py`.

v032 TDD redo cycle 3: in addition to the cycle-2 `.livespec.jsonc`
materialization, the supervisor now iterates the payload's
`files[]` array and writes each entry's `content` to its declared
`path` under cwd, creating parent directories on demand
(`Path.mkdir(parents=True, exist_ok=True)`). Per PROPOSAL.md
§"`seed`" lines 1992-2042 (the deterministic file-shaping work
order, step 2: "Write each main-spec `files[]` entry to its
specified path").

Smallest-thing-that-could-possibly-work — no validation, no ROP
plumbing, parent-directory creation inlined here rather than
authored as a second `livespec.io.fs` primitive (consumer pressure
for an `io.fs.mkdir` seam will be decided when a second consumer
or a `check-no-write-direct` test forces it).

Refactor toward `.livespec.jsonc` content materialization
(commented schema skeleton per PROPOSAL.md §"`seed`" lines
1894-1924), payload validation, sub-spec `sub_specs[]` traversal,
and ROP-on-the-railway composition will land in subsequent cycles
when content assertions, failure-path tests, or a second `io/fs.py`
consumer force them.
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
    write_text(path=cwd / ".livespec.jsonc", content="")
    for entry in payload["files"]:
        entry_path = cwd / entry["path"]
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path=entry_path, content=entry["content"])
    return 0
