"""livespec.commands.seed — supervisor for `bin/seed.py`.

v032 TDD redo cycle 2: Green for the
`tests/bin/test_seed.py::test_seed_writes_livespec_jsonc_at_repo_root`
assertion that `.livespec.jsonc` exists at the project root after a
successful seed invocation. The smallest-thing-that-could-possibly-
work parses `--seed-json <path>`, reads the JSON payload (no
validation yet — that's a later cycle), and writes an empty
`.livespec.jsonc` at the current working directory via
`livespec.io.fs.write_text` (the only sanctioned filesystem write
seam outside `livespec/io/**`).

Refactor toward content materialization (commented schema skeleton
per PROPOSAL.md §"`seed`" lines 1894-1924), payload validation, and
ROP-on-the-railway composition will land in subsequent cycles when
content assertions, failure-path tests, or a second `io/fs.py`
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
    _payload = json.loads(seed_json_path.read_text(encoding="utf-8"))
    write_text(path=Path.cwd() / ".livespec.jsonc", content="")
    return 0
