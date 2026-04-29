"""livespec.doctor.run_static — supervisor for `bin/doctor_static.py`.

Per PROPOSAL.md §"`doctor` → Static-phase output contract" lines
2610-2643, the orchestrator writes `{"findings": [...]}` JSON to
stdout conforming to `doctor_findings.schema.json`. Each finding
entry is a `Finding` dataclass instance per
`livespec/schemas/dataclasses/finding.py` (paired 1:1 with
`finding.schema.json`), serialized via `dataclasses.asdict`.

v032 TDD redo cycle 21: walks the cycle-21 registry (currently
just `livespec_jsonc_valid`) for a single hardcoded
`(spec_root, template_name)` pair (`SPECIFICATION` / `"main"`),
collects each check's Finding, and emits the JSON document. Exit
code 0 unconditionally for now: the cycle-21 test asserts only
the pass-Finding shape, and `livespec_jsonc_valid` against a
freshly-seeded tree returns `status="pass"`. The exit-3-on-any-
fail-Finding semantics (PROPOSAL.md §"Static-phase exit codes"
lines 2820-2829) land when a fail-path test forces them. Same
deferred shape applies to the per-tree `(spec_root, template_name)`
iteration (PROPOSAL.md lines 2513-2542 / Plan lines 1438-1466)
and the orchestrator-owned applicability table (v021 Q1) — both
generalize under future consumer pressure when a sub-spec or a
main-only check is exercised by a test.

Out of cycle-21 scope (deferred per the outside-in walking
direction, each driven by a specific test):

- The full Phase-3 minimum subset of 8 checks (only
  `livespec_jsonc_valid` registered this cycle).
- The `(spec_root, template_name)` orchestrator iteration over
  every spec tree (PROPOSAL.md lines 2513-2542 / v018 Q1 + v021 Q1).
- The applicability table (orchestrator-owned per v021 Q1) deciding
  which checks run for which `(spec_root, template_name)` pair.
- Bootstrap lenience (v014 N3) for `.livespec.jsonc` and
  `template.json` load-failure handling.
- Exit-code 3 path for `status: "fail"` findings per PROPOSAL.md
  §"Exit codes".
- Argparse usage error (exit 2) for `--skip-pre-check` /
  `--run-pre-check` per PROPOSAL.md lines 832-836.
- ROP plumbing (`@impure_safe`, `IOResult`, `Fold.collect_all`).

`sys.stdout.write` is the sanctioned seam at supervisor scope per
`livespec/doctor/CLAUDE.md` ("`run_static.py` is the supervisor:
... it is one of three places where `sys.stdout.write` is permitted")
and `python-skill-script-style-requirements.md` §"Output channels".
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import CHECKS

__all__: list[str] = ["main"]


def main() -> int:
    ctx = DoctorContext(project_root=Path.cwd())
    findings = [dataclasses.asdict(run_fn(ctx=ctx)) for _slug, run_fn in CHECKS]
    sys.stdout.write(json.dumps({"findings": findings}) + "\n")
    return 0
