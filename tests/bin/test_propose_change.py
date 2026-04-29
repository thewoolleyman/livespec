"""Outside-in integration test for `bin/propose_change.py` — Phase 3 exit-criterion rail.

Per Phase 5 plan §"Phase 3 — Minimum viable `livespec propose-change`"
and PROPOSAL.md §"`propose-change`" (lines 2134-2278), invoking
`propose_change.py --findings-json <path> <topic>` against an
already-seeded tmp_path materializes a new file at
`<spec-root>/proposed_changes/<canonical-topic>.md` containing one
`## Proposal: <name>` section per finding (one-to-one field-copy
per PROPOSAL.md lines 2232-2242).

This module holds the OUTERMOST integration test for the
propose-change exit-criterion round-trip. Per the v032 D2
outside-in walking direction, the failure point of this single
test advances forward across many TDD cycles: first the wrapper
file does not exist (FileNotFoundError); next, the supervisor
stub exists but writes nothing (`<topic>.md` missing assertion);
and so on until every Phase 3 propose-change exit-criterion
artifact is materialized.

The wrapper is invoked as a subprocess so the wrapper-shape +
bootstrap + supervisor plumbing is exercised end-to-end exactly
as Claude Code invokes it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SEED_WRAPPER = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "seed.py"
_PROPOSE_CHANGE_WRAPPER = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "propose_change.py"


def _seed_tmp_path(*, tmp_path: Path) -> None:
    """Pre-seed tmp_path with the minimum spec tree propose-change needs.

    Uses the seed wrapper itself rather than hand-creating files —
    the integration-rail discipline keeps every cycle's pre-condition
    grounded in real wrapper behavior. The smallest valid seed payload
    creates `.livespec.jsonc`, `SPECIFICATION/spec.md`, and the
    `<spec-root>/history/v001/proposed_changes/` directory plus the
    auto-captured seed pair.
    """
    seed_payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec"},
        ],
        "intent": "pre-seed for propose-change integration test",
        "sub_specs": [],
    }
    seed_input = tmp_path / "seed_input.json"
    seed_input.write_text(json.dumps(seed_payload), encoding="utf-8")
    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    seed_result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(seed_input)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        seed_result.returncode == 0
    ), f"pre-seed failed; stdout={seed_result.stdout!r} stderr={seed_result.stderr!r}"


def test_propose_change_writes_proposed_change_file_at_spec_target(*, tmp_path: Path) -> None:
    """propose_change.py --findings-json + <topic> writes `<spec-root>/proposed_changes/<topic>.md`.

    Per PROPOSAL.md §"`propose-change`" lines 2145-2148, the
    wrapper "creates a new file
    `<spec-root>/proposed_changes/<canonical-topic>.md` containing
    one or more `## Proposal: <name>` sections." Per lines
    2232-2242, the wrapper validates the JSON payload against
    `proposal_findings.schema.json` and maps each finding to one
    `## Proposal` section via field-copy.

    Output file location is the TOP-LEVEL
    `<spec-root>/proposed_changes/`, NOT
    `<spec-root>/history/v001/proposed_changes/` — the latter is
    where revise versions in-flight proposals after acceptance.
    """
    _seed_tmp_path(tmp_path=tmp_path)
    findings_payload: dict[str, object] = {
        "findings": [
            {
                "name": "First proposal",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": "Stub summary of what changes and why.",
                "motivation": "Stub motivation paragraph.",
                "proposed_changes": "Stub prose describing the proposed changes.",
            },
        ],
    }
    findings_input = tmp_path / "findings.json"
    findings_input.write_text(json.dumps(findings_payload), encoding="utf-8")
    topic = "stub-topic"

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload + literal topic); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(_PROPOSE_CHANGE_WRAPPER),
            "--findings-json",
            str(findings_input),
            topic,
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"propose-change wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    proposed_change_path = tmp_path / "SPECIFICATION" / "proposed_changes" / f"{topic}.md"
    assert proposed_change_path.exists(), (
        f"proposed-change file {proposed_change_path} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
