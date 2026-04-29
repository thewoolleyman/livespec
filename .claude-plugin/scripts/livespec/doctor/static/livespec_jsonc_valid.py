"""livespec.doctor.static.livespec_jsonc_valid — `.livespec.jsonc` validity check.

Verifies that `<project_root>/.livespec.jsonc` exists and parses
as valid JSON. Per PROPOSAL.md §"`doctor` → Static-phase checks"
and Plan §"Phase 3" line 1481, this is the first of the eight
Phase-3 minimum-subset checks.

v032 TDD redo cycle 21: minimal authoring under outside-in
consumer pressure. The cycle-21 test seeds a tree (which produces
a freshly-written `.livespec.jsonc`) and asserts a `pass` Finding
is emitted. Therefore this cycle only handles the happy path:
file exists + parses. Failure modes (absent file, malformed JSON,
schema-invalid content per `livespec_config.schema.json`) land
under future test pressure — each failure-path test pulls a
specific Finding-shape branch into existence and (eventually) the
v014 N3 bootstrap-lenience semantics that map
`config_load_status` to `pass`/`skipped`/`fail`.

Per the style doc §"Context dataclasses" the `run` signature is
keyword-only. Per PROPOSAL.md lines 2625-2628, the JSON `check_id`
is `doctor-<slug>` — composed once here at the Finding-construction
site rather than at orchestrator-serialization time. The prefix is
literal, no conversion loop.

JSON parsing uses the stdlib `json` module rather than the
vendored `jsoncomment` shim. The `.livespec.jsonc` written by
`bin/seed.py` (PROPOSAL.md §"`seed`" lines 1894-1924) is currently
plain JSON without comments; the JSONC parse path will land when
a test exercises a comment-bearing config (or the vendored shim
is consumed under broader pressure from `livespec/parse/jsonc.py`).
"""

from __future__ import annotations

import json

from livespec.context import DoctorContext
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "livespec-jsonc-valid"


def run(*, ctx: DoctorContext) -> Finding:
    config_path = ctx.project_root / ".livespec.jsonc"
    config_text = config_path.read_text(encoding="utf-8")
    json.loads(config_text)
    return Finding(
        check_id=f"doctor-{SLUG}",
        status="pass",
        message=".livespec.jsonc parsed successfully",
        path=None,
        line=None,
        spec_root="SPECIFICATION",
    )
