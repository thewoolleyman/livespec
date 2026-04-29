"""livespec.doctor.run_static — supervisor for `bin/doctor_static.py`.

v032 TDD redo cycle 20: smallest impl that flips the cycle-20
outside-in integration test forward from "wrapper not found" to a
specific findings-shape failure mode (or, in this cycle, all the way
to Green for the empty-findings shape — the test pins only that
stdout is `{"findings": [...]}` JSON, not that any specific check
ran).

Per PROPOSAL.md §"`doctor` → Static-phase output contract" lines
2610-2643: the orchestrator writes structured JSON to stdout
conforming to `doctor_findings.schema.json` — a JSON object with one
required key `findings` whose value is an array of Finding entries.
This stub emits an empty array — a valid (if degenerate) doctor_findings
document. Subsequent cycles drive each Phase-3 minimum check
(`livespec_jsonc_valid`, `template_exists`, `template_files_present`,
`proposed_changes_and_history_dirs`, `version_directories_complete`,
`version_contiguity`, `revision_to_proposed_change_pairing`,
`proposed_change_topic_format`) into existence one at a time, plus the
orchestrator's `(spec_root, template_name)` iteration, plus the
applicability table.

`sys.stdout.write` is the sanctioned seam at supervisor scope per
`livespec/doctor/CLAUDE.md` ("`run_static.py` is the supervisor:
... it is one of three places where `sys.stdout.write` is permitted")
and `python-skill-script-style-requirements.md` §"Output channels".

Out of cycle-20 scope (deferred to subsequent cycles per the
outside-in walking direction, each driven by a specific test):

- The `(spec_root, template_name)` orchestrator iteration per
  PROPOSAL.md lines 2513-2542 (v018 Q1 + v021 Q1).
- The static-check registry at `livespec/doctor/static/__init__.py`
  enumerating the 8 Phase-3 minimum checks.
- Each individual check module under `livespec/doctor/static/`.
- The applicability table (orchestrator-owned per v021 Q1) deciding
  which checks run for which `(spec_root, template_name)` pair.
- Bootstrap lenience (v014 N3) for `.livespec.jsonc` and
  `template.json` load-failure handling.
- Exit-code 3 path for `status: "fail"` findings per PROPOSAL.md
  §"Exit codes".
- Argparse usage error (exit 2) for `--skip-pre-check` /
  `--run-pre-check` per PROPOSAL.md lines 832-836.
- ROP plumbing (`@impure_safe`, `IOResult`, `Fold.collect_all`).
"""

from __future__ import annotations

import json
import sys

__all__: list[str] = ["main"]


def main() -> int:
    sys.stdout.write(json.dumps({"findings": []}) + "\n")
    return 0
