"""Outside-in integration test for `bin/revise.py` — Phase 3 exit-criterion rail.

Per PROPOSAL.md §"`revise`" lines 2335-2452 + Plan §"Phase 3"
lines 1417-1437 (post-Case-B reconciliation at commit 72db010),
invoking `revise.py --revise-json <path>` against a tmp_path
that already carries one or more in-flight proposed-change files
materializes a new `<spec-target>/history/vNNN/` version including
the byte-identical move of each processed proposal into
`history/vNNN/proposed_changes/<stem>.md` plus a paired
`<stem>-revision.md`, leaving the working
`<spec-root>/proposed_changes/` empty of in-flight files.

This module holds the OUTERMOST integration test for the revise
exit-criterion round-trip. Per the v032 D2 outside-in walking
direction, the failure point of this single test advances forward
across many TDD cycles: first the wrapper file does not exist
(FileNotFoundError); next, the supervisor stub exists but writes
nothing (history/v002/ missing assertion); and so on until every
Phase 3 revise exit-criterion artifact is materialized.

The wrapper is invoked as a subprocess so the wrapper-shape +
bootstrap + supervisor plumbing is exercised end-to-end exactly
as Claude Code invokes it. Pre-condition (seed + propose-change)
is built up via the real seed and propose_change wrappers rather
than hand-created files, keeping the integration rail grounded
in real wrapper behavior end-to-end.
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
_REVISE_WRAPPER = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "revise.py"


def _seed_tmp_path(*, tmp_path: Path) -> None:
    """Pre-seed tmp_path with the minimum spec tree revise needs."""
    seed_payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec"},
        ],
        "intent": "pre-seed for revise integration test",
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


def _file_in_flight_proposal(*, tmp_path: Path, topic: str) -> None:
    """File a proposed-change at SPECIFICATION/proposed_changes/<topic>.md via the wrapper."""
    findings_payload: dict[str, object] = {
        "findings": [
            {
                "name": "Stub revise-test proposal",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": "Proposal under test for revise integration.",
                "motivation": "Pre-condition for revise integration test.",
                "proposed_changes": "Replace stub spec with revised content.",
            },
        ],
    }
    findings_input = tmp_path / "findings.json"
    findings_input.write_text(json.dumps(findings_payload), encoding="utf-8")
    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload + literal topic); no untrusted shell input.
    pc_result = subprocess.run(  # noqa: S603
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
    assert pc_result.returncode == 0, (
        f"propose-change pre-condition failed; "
        f"stdout={pc_result.stdout!r} stderr={pc_result.stderr!r}"
    )


def test_revise_processes_proposed_change_into_history_v002(*, tmp_path: Path) -> None:
    """`revise.py --revise-json <path>` cuts vNNN, byte-moves proposal, writes paired revision.

    Per PROPOSAL.md §"`revise`" lines 2411-2452, on any
    `accept`/`modify` decision the wrapper:
    1. Cuts a new `<spec-root>/history/vNNN/` (here v002, since
       v001 was the seed).
    2. Updates working-spec files named in `resulting_files`
       in place (here `SPECIFICATION/spec.md`).
    3. Creates `<spec-root>/history/vNNN/proposed_changes/`.
    4. Byte-moves each processed proposal from
       `<spec-root>/proposed_changes/<stem>.md` into
       `<spec-root>/history/vNNN/proposed_changes/<stem>.md`.
    5. Writes a paired `<stem>-revision.md` per decision.
    6. Leaves `<spec-root>/proposed_changes/` empty of in-flight
       files (skill-owned README.md persists per line 2451-2452;
       not pinned by this test).

    Plan lines 1417-1437 confirm Phase-3 minimum-viable scope:
    `--revise-json <path>` payload validated against
    `revise_input.schema.json`, no LLM-driven decision dialogue
    (skill-prose-side responsibility).
    """
    topic = "stub-topic"
    _seed_tmp_path(tmp_path=tmp_path)
    _file_in_flight_proposal(tmp_path=tmp_path, topic=topic)

    in_flight_proposal = tmp_path / "SPECIFICATION" / "proposed_changes" / f"{topic}.md"
    assert (
        in_flight_proposal.exists()
    ), f"pre-condition: in-flight proposal {in_flight_proposal} not present"

    revise_payload: dict[str, object] = {
        "decisions": [
            {
                "proposal_topic": topic,
                "decision": "accept",
                "rationale": "auto-accepted for test",
                "modifications": "",
                "resulting_files": [
                    {
                        "path": "SPECIFICATION/spec.md",
                        "content": "post-revise content",
                    },
                ],
            },
        ],
    }
    revise_input = tmp_path / "revise_input.json"
    revise_input.write_text(json.dumps(revise_payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_REVISE_WRAPPER), "--revise-json", str(revise_input)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"revise wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    history_v002 = tmp_path / "SPECIFICATION" / "history" / "v002"
    moved_proposal = history_v002 / "proposed_changes" / f"{topic}.md"
    paired_revision = history_v002 / "proposed_changes" / f"{topic}-revision.md"
    assert history_v002.is_dir(), (
        f"history/v002/ {history_v002} not materialized; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert moved_proposal.exists(), (
        f"byte-moved proposal {moved_proposal} not at history/v002/proposed_changes/; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert paired_revision.exists(), (
        f"paired revision {paired_revision} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert not in_flight_proposal.exists(), (
        f"in-flight proposal {in_flight_proposal} still present after revise; "
        f"PROPOSAL.md lines 2450-2452 require <spec-root>/proposed_changes/ to be empty "
        f"of in-flight files. stdout={result.stdout!r} stderr={result.stderr!r}"
    )
