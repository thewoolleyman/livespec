"""Phase-3 exit-criterion round-trip integration test.

Per Plan §"Exit criterion (narrow Phase-3 gate)" lines 1592-1633
and PROPOSAL.md §"`seed`" / §"`propose-change`" / §"`critique`"
/ §"`revise`" / §"`prune-history`" / §"`doctor`": this module
exercises the full Phase-3 mechanically-achievable round-trip
in one pytest run by invoking each shebang wrapper as a real
subprocess (mirroring v032 cycle 30 commit 1b8e81a's pattern).

Steps pinned:

1. seed → `.livespec.jsonc` + main spec tree + auto-captured
   seed.md / seed-revision.md beneath history/v001/, plus
   skill-owned `<spec-root>/proposed_changes/README.md`. Seed's
   own post-step doctor (cycle 145) runs in-band and exits 0
   on the doctor-clean tree.
2. propose-change against MAIN tree → working
   `<spec-root>/proposed_changes/<topic>.md` exists.
3. critique → delegates to propose-change with `-critique`
   reserve-suffix appended, producing
   `<spec-root>/proposed_changes/<author>-critique.md`.
4. revise → cuts `history/v002/`, byte-moves both proposals
   from `<spec-root>/proposed_changes/` into
   `<spec-root>/history/v002/proposed_changes/`, and writes
   the paired revision files for each.
5. prune-history → Phase-3 stub, returns exit 0 (full prune
   mechanic is Phase-7 scope).
6. doctor_static → exit 0 with every finding `status: "pass"`
   on the final round-trip state.

Each wrapper invocation runs as a real subprocess, exercising
the full wrapper-shape + bootstrap + supervisor plumbing
end-to-end exactly as Claude Code invokes it. The integration
test verifies the COMPOSED behavior; the per-cycle unit tests
under `tests/livespec/commands/` already pin each constituent
behavior individually.
"""

from __future__ import annotations

import json
import subprocess  # documented integration-test usage
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIN_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin"
_SEED_WRAPPER = _BIN_DIR / "seed.py"
_PROPOSE_CHANGE_WRAPPER = _BIN_DIR / "propose_change.py"
_CRITIQUE_WRAPPER = _BIN_DIR / "critique.py"
_REVISE_WRAPPER = _BIN_DIR / "revise.py"
_PRUNE_HISTORY_WRAPPER = _BIN_DIR / "prune_history.py"
_DOCTOR_STATIC_WRAPPER = _BIN_DIR / "doctor_static.py"


def _run_wrapper(
    *,
    argv: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Invoke a wrapper subprocess with a fixed argv list.

    Captures stdout/stderr as text. `check=False` keeps non-zero
    exits in the CompletedProcess return value so the test can
    assert on returncode + diagnostic streams.
    """
    return subprocess.run(  # argv is a fixed repo-controlled list
        argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def test_phase_3_exit_criterion_round_trip(*, tmp_path: Path) -> None:  # noqa: PLR0915
    """Full Phase-3 round-trip: seed -> propose-change -> critique -> revise -> prune-history -> doctor.

    Pins the composed behavior the cycles 65-145 ladder authored
    incrementally. Per Plan §"Exit criterion (narrow Phase-3
    gate)" lines 1592-1633: the gate fires when all five
    sub-commands compose into a clean round-trip exiting at
    each stage with the documented exit code, and the final
    doctor static check sees zero fail-status findings.

    Phase-3 minimum scope: single main-spec tree, no sub-spec
    trees (sub-spec routing was the v020 Q3 ratchet that v032
    cycle 30 carried; it lands in Phase 7 hardening for v033
    per the briefing's "Phase-3 minimum subset" framing). Seed's
    payload here exercises only the main `SPECIFICATION/` tree.

    PLR0915 noqa rationale (cycle 4d, 2026-05-02): integration
    tests of multi-step round-trips inherently exceed ruff's
    default 30-statement budget — this test has 49 statements
    across 6 sequential sub-command invocations + their
    assertions. Extracting each step into a helper function would
    obscure the round-trip's sequential reading order without
    materially improving testability (the steps share state via
    the shared `tmp_path` filesystem and are tested as a
    composed pipeline, not individually). The noqa is targeted
    to this single function rather than a tests/**.py-wide
    PLR0915 exemption (no other test exceeds the 30-statement
    threshold; widening would mask future test bloat).
    """
    project_root = tmp_path

    # Step 1: seed.
    seed_payload: dict[str, object] = {
        "template": "livespec",
        "intent": "phase 3 exit-criterion round-trip integration",
        "files": [
            {
                "path": "SPECIFICATION/spec.md",
                "content": "# Spec\n\nSeeded baseline content.\n",
            },
        ],
        "sub_specs": [],
    }
    seed_input = tmp_path / "seed_input.json"
    _ = seed_input.write_text(json.dumps(seed_payload), encoding="utf-8")
    seed_result = _run_wrapper(
        argv=[
            sys.executable,
            str(_SEED_WRAPPER),
            "--seed-json",
            str(seed_input),
            "--project-root",
            str(project_root),
        ],
        cwd=tmp_path,
    )
    assert seed_result.returncode == 0, (
        f"seed exited {seed_result.returncode}; "
        f"stdout={seed_result.stdout!r} stderr={seed_result.stderr!r}"
    )
    assert (project_root / ".livespec.jsonc").is_file()
    assert (project_root / "SPECIFICATION" / "spec.md").is_file()
    assert (project_root / "SPECIFICATION" / "history" / "v001" / "spec.md").is_file()
    assert (
        project_root
        / "SPECIFICATION"
        / "history"
        / "v001"
        / "proposed_changes"
        / "seed.md"
    ).is_file()
    assert (
        project_root
        / "SPECIFICATION"
        / "proposed_changes"
        / "README.md"
    ).is_file()

    # Step 2: propose-change against MAIN.
    main_topic = "main-roundtrip-proposal"
    findings_payload: dict[str, object] = {
        "findings": [
            {
                "name": "Round-trip proposal for SPECIFICATION",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": "Stub summary for the round-trip integration test.",
                "motivation": "Stub motivation paragraph.",
                "proposed_changes": "Stub prose describing the proposed changes.",
            },
        ],
    }
    findings_input = tmp_path / "findings_main.json"
    _ = findings_input.write_text(json.dumps(findings_payload), encoding="utf-8")
    propose_result = _run_wrapper(
        argv=[
            sys.executable,
            str(_PROPOSE_CHANGE_WRAPPER),
            "--findings-json",
            str(findings_input),
            "--project-root",
            str(project_root),
            main_topic,
        ],
        cwd=tmp_path,
    )
    assert propose_result.returncode == 0, (
        f"propose-change exited {propose_result.returncode}; "
        f"stdout={propose_result.stdout!r} stderr={propose_result.stderr!r}"
    )
    main_in_flight = (
        project_root / "SPECIFICATION" / "proposed_changes" / f"{main_topic}.md"
    )
    assert main_in_flight.is_file(), (
        f"expected in-flight proposal {main_in_flight} after propose-change"
    )

    # Step 3: critique (delegates to propose-change with `-critique` suffix).
    critique_findings: dict[str, object] = {
        "findings": [
            {
                "name": "Round-trip critique for SPECIFICATION",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": "Stub critique summary.",
                "motivation": "Stub critique motivation.",
                "proposed_changes": "Stub critique proposed changes.",
            },
        ],
    }
    critique_input = tmp_path / "findings_critique.json"
    _ = critique_input.write_text(json.dumps(critique_findings), encoding="utf-8")
    critique_result = _run_wrapper(
        argv=[
            sys.executable,
            str(_CRITIQUE_WRAPPER),
            "--findings-json",
            str(critique_input),
            "--author",
            "roundtrip-critic",
            "--project-root",
            str(project_root),
        ],
        cwd=tmp_path,
    )
    assert critique_result.returncode == 0, (
        f"critique exited {critique_result.returncode}; "
        f"stdout={critique_result.stdout!r} stderr={critique_result.stderr!r}"
    )
    critique_in_flight = (
        project_root
        / "SPECIFICATION"
        / "proposed_changes"
        / "roundtrip-critic-critique.md"
    )
    assert critique_in_flight.is_file(), (
        f"expected critique in-flight proposal {critique_in_flight} (delegated "
        f"to propose-change with `-critique` reserve-suffix)"
    )

    # Step 4: revise — cuts v002, byte-moves both proposals, writes paired revisions.
    revise_payload: dict[str, object] = {
        "decisions": [
            {
                "proposal_topic": main_topic,
                "decision": "accept",
                "rationale": "auto-accepted for round-trip integration",
                "modifications": "",
                "resulting_files": [
                    {
                        "path": "SPECIFICATION/spec.md",
                        "content": "# Spec\n\nRevised content after v002.\n",
                    },
                ],
            },
            {
                "proposal_topic": "roundtrip-critic-critique",
                "decision": "accept",
                "rationale": "auto-accepted critique for round-trip integration",
                "modifications": "",
                "resulting_files": [
                    {
                        "path": "SPECIFICATION/spec.md",
                        "content": "# Spec\n\nRevised content after v002.\n",
                    },
                ],
            },
        ],
    }
    revise_input = tmp_path / "revise_input.json"
    _ = revise_input.write_text(json.dumps(revise_payload), encoding="utf-8")
    revise_result = _run_wrapper(
        argv=[
            sys.executable,
            str(_REVISE_WRAPPER),
            "--revise-json",
            str(revise_input),
            "--project-root",
            str(project_root),
        ],
        cwd=tmp_path,
    )
    assert revise_result.returncode == 0, (
        f"revise exited {revise_result.returncode}; "
        f"stdout={revise_result.stdout!r} stderr={revise_result.stderr!r}"
    )
    main_v002 = project_root / "SPECIFICATION" / "history" / "v002"
    assert main_v002.is_dir(), "expected main history/v002/ after revise"
    assert (main_v002 / "proposed_changes" / f"{main_topic}.md").is_file(), (
        "expected revise to byte-move proposed_changes/<topic>.md into v002"
    )
    assert (
        main_v002 / "proposed_changes" / f"{main_topic}-revision.md"
    ).is_file(), "expected revise to write paired <topic>-revision.md into v002"
    assert not main_in_flight.exists(), (
        "expected in-flight proposal moved out of working directory after revise"
    )
    assert not critique_in_flight.exists(), (
        "expected critique in-flight proposal moved out of working directory "
        "after revise"
    )

    # Step 5: prune-history (Phase-3 stub, returns 0).
    prune_result = _run_wrapper(
        argv=[sys.executable, str(_PRUNE_HISTORY_WRAPPER)],
        cwd=tmp_path,
    )
    assert prune_result.returncode == 0, (
        f"prune-history exited {prune_result.returncode}; "
        f"stdout={prune_result.stdout!r} stderr={prune_result.stderr!r}"
    )

    # Step 6: doctor_static — exit 0 + every finding status="pass".
    doctor_result = _run_wrapper(
        argv=[
            sys.executable,
            str(_DOCTOR_STATIC_WRAPPER),
            "--project-root",
            str(project_root),
        ],
        cwd=tmp_path,
    )
    assert doctor_result.returncode == 0, (
        f"doctor_static exited {doctor_result.returncode} on final round-trip "
        f"state; stdout={doctor_result.stdout!r} stderr={doctor_result.stderr!r}"
    )
    parsed = json.loads(doctor_result.stdout)
    assert isinstance(parsed, dict)
    findings_obj = parsed["findings"]
    assert isinstance(findings_obj, list)
    findings = [f for f in findings_obj if isinstance(f, dict)]
    fail_findings = [f for f in findings if f.get("status") == "fail"]
    assert not fail_findings, (
        f"expected zero fail findings on final round-trip state; "
        f"got {fail_findings!r}"
    )
