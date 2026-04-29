"""livespec.commands.seed — supervisor for `bin/seed.py`.

v032 TDD redo cycle 4: extends cycle-3 `files[]` materialization
with the `<spec-root>/history/v001/` snapshot per PROPOSAL.md
§"`seed`" lines 1992-2042 step 4 ("Create `<spec-root>/history/v001/`
for the main spec (including the initial versioned spec files,
a `proposed_changes/` subdir, and, for templates whose versioned
surface includes one, a per-version README copy)"). For every
payload-`files[]` entry under the active template's spec_root,
the supervisor copies the file to
`<spec_root>/history/v001/<rel-to-spec-root>` (basename per
PROPOSAL.md lines 981-986: "Historic files under `history/vNNN/`
use plain filenames"). The empty `<spec_root>/history/v001/proposed_changes/`
subdir is created alongside.

`spec_root` is currently hardcoded to `"SPECIFICATION"` (the
`livespec` template default per
`template_config.schema.json`). This will refactor to data-driven
resolution (read the template's `template.json`) when the
`minimal` template's `spec_root: "./"` or a custom-template test
forces it.

Smallest-thing-that-could-possibly-work — no validation, no ROP
plumbing, no per-version README copy (deferred until a content
assertion forces it), no auto-captured seed proposed-change
(deferred until that test cycle), parent-directory creation
inlined here rather than authored as a second `livespec.io.fs`
primitive (consumer pressure for an `io.fs.mkdir` seam will be
decided when a second consumer or a `check-no-write-direct` test
forces it).

Refactor toward `.livespec.jsonc` content materialization
(commented schema skeleton per PROPOSAL.md §"`seed`" lines
1894-1924), payload validation, sub-spec `sub_specs[]` traversal,
auto-captured seed proposed-change/revision (lines 2043-2064), and
ROP-on-the-railway composition will land in subsequent cycles
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
    return 0
