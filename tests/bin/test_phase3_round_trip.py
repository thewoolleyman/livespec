"""Phase-3 exit-criterion round-trip integration test.

Per Plan §"Exit criterion (narrow Phase-3 gate)" lines 1592-1633
and PROPOSAL.md §"`seed`" / §"`propose-change`" / §"`revise`" /
§"`doctor`", this module exercises the full Phase-3 mechanically-
achievable round-trip: seed → propose-change main → revise main →
propose-change sub-spec → revise sub-spec → doctor static. Each
wrapper invocation runs as a real subprocess, exercising the
full wrapper-shape + bootstrap + supervisor plumbing end-to-end
exactly as Claude Code invokes it.

The v020 Q3 sub-spec routing smoke cycle is the load-bearing
ratchet: it pins that `--spec-target SPECIFICATION/templates/
livespec` actually routes propose-change/revise to the sub-spec
tree's `proposed_changes/` and `history/vNNN/proposed_changes/`
directories (NOT to the main tree's directories). Catches
sub-spec-routing bugs at the Phase 3 boundary where recovery is
imperative-landing (cheap), instead of Phase 7's dogfood
boundary where recovery would require the broken governed loop.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIN_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin"
_SEED_WRAPPER = _BIN_DIR / "seed.py"
_PROPOSE_CHANGE_WRAPPER = _BIN_DIR / "propose_change.py"
_REVISE_WRAPPER = _BIN_DIR / "revise.py"
_DOCTOR_STATIC_WRAPPER = _BIN_DIR / "doctor_static.py"


def _run_wrapper(*, argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Invoke a wrapper subprocess with a fixed argv list and capture stdout/stderr."""
    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper paths + literal flags + tmp_path-derived inputs); no
    # untrusted shell input.
    return subprocess.run(  # noqa: S603
        argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _seed_main_plus_two_sub_specs(*, tmp_path: Path) -> None:
    """Seed `tmp_path` with main + livespec sub-spec + minimal sub-spec.

    Mirrors Plan lines 1599-1610: the seed dialogue's "ships own
    livespec templates" answer is "yes" naming `livespec` and
    `minimal`, producing three trees materialized atomically by
    the single seed invocation (M5 + v018 Q1 + v020 Q1 uniform
    README).
    """
    main_files = [
        {"path": "SPECIFICATION/spec.md", "content": "main stub spec"},
        {"path": "SPECIFICATION/contracts.md", "content": "main stub contracts"},
        {
            "path": "SPECIFICATION/constraints.md",
            "content": "main stub constraints",
        },
        {"path": "SPECIFICATION/scenarios.md", "content": "main stub scenarios"},
        {"path": "SPECIFICATION/README.md", "content": "main stub readme"},
    ]
    livespec_sub_files = [
        {
            "path": "SPECIFICATION/templates/livespec/spec.md",
            "content": "livespec sub-spec stub",
        },
        {
            "path": "SPECIFICATION/templates/livespec/contracts.md",
            "content": "livespec sub-spec contracts stub",
        },
        {
            "path": "SPECIFICATION/templates/livespec/constraints.md",
            "content": "livespec sub-spec constraints stub",
        },
        {
            "path": "SPECIFICATION/templates/livespec/scenarios.md",
            "content": "livespec sub-spec scenarios stub",
        },
        {
            "path": "SPECIFICATION/templates/livespec/README.md",
            "content": "livespec sub-spec readme stub",
        },
    ]
    minimal_sub_files = [
        {
            "path": "SPECIFICATION/templates/minimal/spec.md",
            "content": "minimal sub-spec stub",
        },
        {
            "path": "SPECIFICATION/templates/minimal/contracts.md",
            "content": "minimal sub-spec contracts stub",
        },
        {
            "path": "SPECIFICATION/templates/minimal/constraints.md",
            "content": "minimal sub-spec constraints stub",
        },
        {
            "path": "SPECIFICATION/templates/minimal/scenarios.md",
            "content": "minimal sub-spec scenarios stub",
        },
        {
            "path": "SPECIFICATION/templates/minimal/README.md",
            "content": "minimal sub-spec readme stub",
        },
    ]
    payload: dict[str, object] = {
        "template": "livespec",
        "files": main_files,
        "intent": "phase 3 exit-criterion round-trip integration",
        "sub_specs": [
            {"template_name": "livespec", "files": livespec_sub_files},
            {"template_name": "minimal", "files": minimal_sub_files},
        ],
    }
    seed_input = tmp_path / "seed_input.json"
    seed_input.write_text(json.dumps(payload), encoding="utf-8")
    result = _run_wrapper(
        argv=[sys.executable, str(_SEED_WRAPPER), "--seed-json", str(seed_input)],
        cwd=tmp_path,
    )
    assert result.returncode == 0, (
        f"seed exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def _propose_change_in(*, tmp_path: Path, spec_target: str, topic: str) -> None:
    """File a propose-change against the named spec_target."""
    findings_payload: dict[str, object] = {
        "findings": [
            {
                "name": f"Round-trip proposal for {spec_target}",
                "target_spec_files": [f"{spec_target}/spec.md"],
                "summary": "Stub summary for the round-trip integration test.",
                "motivation": "Stub motivation paragraph.",
                "proposed_changes": "Stub prose describing the proposed changes.",
            },
        ],
    }
    findings_input = tmp_path / f"findings_{topic}.json"
    findings_input.write_text(json.dumps(findings_payload), encoding="utf-8")
    result = _run_wrapper(
        argv=[
            sys.executable,
            str(_PROPOSE_CHANGE_WRAPPER),
            "--findings-json",
            str(findings_input),
            "--spec-target",
            spec_target,
            topic,
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, (
        f"propose-change exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def _revise_in(*, tmp_path: Path, spec_target: str, topic: str) -> None:
    """Revise the named topic against the named spec_target with an accept decision."""
    revise_payload: dict[str, object] = {
        "decisions": [
            {
                "proposal_topic": topic,
                "decision": "accept",
                "rationale": "auto-accepted for round-trip integration",
                "modifications": "",
                "resulting_files": [
                    {
                        "path": f"{spec_target}/spec.md",
                        "content": f"post-revise content under {spec_target}",
                    },
                ],
            },
        ],
    }
    revise_input = tmp_path / f"revise_input_{topic}.json"
    revise_input.write_text(json.dumps(revise_payload), encoding="utf-8")
    result = _run_wrapper(
        argv=[
            sys.executable,
            str(_REVISE_WRAPPER),
            "--revise-json",
            str(revise_input),
            "--spec-target",
            spec_target,
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, (
        f"revise exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_phase_3_exit_criterion_round_trip_main_and_sub_spec(  # noqa: PLR0915
    *, tmp_path: Path
) -> None:
    """Full Phase-3 round-trip: seed → propose-change → revise (main and sub-spec) → doctor.

    Step 1: seed produces .livespec.jsonc + main + 2 sub-specs.
    Step 2: propose-change against MAIN tree → working proposal exists.
    Step 3: revise main → history/v002/ materializes with paired files.
    Step 4 (v020 Q3 sub-spec smoke): propose-change --spec-target
            SPECIFICATION/templates/livespec → working proposal exists
            in the sub-spec tree.
    Step 5: revise --spec-target SPECIFICATION/templates/livespec →
            sub-spec history/v002/ materializes with paired files.
    Step 6: doctor_static returns exit 0 with all findings status="pass".

    Per Plan lines 1592-1633.
    """
    # Step 1: seed.
    _seed_main_plus_two_sub_specs(tmp_path=tmp_path)

    livespec_jsonc = tmp_path / ".livespec.jsonc"
    main_root = tmp_path / "SPECIFICATION"
    livespec_sub_root = main_root / "templates" / "livespec"
    minimal_sub_root = main_root / "templates" / "minimal"

    assert livespec_jsonc.is_file(), "expected .livespec.jsonc at repo root"
    assert (main_root / "history" / "v001" / "spec.md").is_file(), (
        "expected main history/v001/ snapshot"
    )
    assert (livespec_sub_root / "history" / "v001" / "spec.md").is_file(), (
        "expected livespec sub-spec history/v001/ snapshot"
    )
    assert (minimal_sub_root / "history" / "v001" / "spec.md").is_file(), (
        "expected minimal sub-spec history/v001/ snapshot"
    )

    # Step 2: propose-change against MAIN.
    main_topic = "main-roundtrip-proposal"
    _propose_change_in(
        tmp_path=tmp_path, spec_target="SPECIFICATION", topic=main_topic
    )
    main_in_flight = main_root / "proposed_changes" / f"{main_topic}.md"
    assert main_in_flight.is_file(), (
        f"expected in-flight proposal {main_in_flight} after propose-change"
    )

    # Step 3: revise main.
    _revise_in(tmp_path=tmp_path, spec_target="SPECIFICATION", topic=main_topic)
    main_v002 = main_root / "history" / "v002"
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

    # Step 4 (v020 Q3 smoke): propose-change against LIVESPEC SUB-SPEC.
    sub_spec_target = "SPECIFICATION/templates/livespec"
    sub_topic = "sub-spec-roundtrip-proposal"
    _propose_change_in(
        tmp_path=tmp_path, spec_target=sub_spec_target, topic=sub_topic
    )
    sub_in_flight = livespec_sub_root / "proposed_changes" / f"{sub_topic}.md"
    assert sub_in_flight.is_file(), (
        f"expected sub-spec in-flight proposal {sub_in_flight} after propose-change "
        f"--spec-target {sub_spec_target}"
    )

    # Step 5: revise --spec-target SUB-SPEC.
    _revise_in(tmp_path=tmp_path, spec_target=sub_spec_target, topic=sub_topic)
    sub_v002 = livespec_sub_root / "history" / "v002"
    assert sub_v002.is_dir(), (
        f"expected sub-spec {sub_v002} (history/v002/) after revise "
        f"--spec-target {sub_spec_target}; this is the v020 Q3 sub-spec "
        f"routing smoke ratchet"
    )
    assert (sub_v002 / "proposed_changes" / f"{sub_topic}.md").is_file(), (
        "expected sub-spec revise to byte-move proposed_changes/<topic>.md into v002"
    )
    assert (
        sub_v002 / "proposed_changes" / f"{sub_topic}-revision.md"
    ).is_file(), (
        "expected sub-spec revise to write paired <topic>-revision.md into v002"
    )
    assert not sub_in_flight.exists(), (
        "expected sub-spec in-flight proposal moved out of working directory after revise"
    )

    # Step 6: doctor_static — exit 0 + every finding status="pass".
    result = _run_wrapper(
        argv=[sys.executable, str(_DOCTOR_STATIC_WRAPPER)], cwd=tmp_path
    )
    assert result.returncode == 0, (
        f"doctor_static exited {result.returncode} on final round-trip state; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    parsed: object = json.loads(result.stdout)
    assert isinstance(parsed, dict)
    findings_obj = parsed["findings"]
    assert isinstance(findings_obj, list)
    findings = [f for f in findings_obj if isinstance(f, dict)]
    fail_findings = [f for f in findings if f.get("status") == "fail"]
    assert not fail_findings, (
        f"expected zero fail findings on final round-trip state; "
        f"got {fail_findings!r}"
    )

    # Per-tree presence: at least one finding for each spec tree.
    spec_roots_seen = {f.get("spec_root") for f in findings}
    assert "SPECIFICATION" in spec_roots_seen, (
        f"expected main-tree findings; got spec_roots={spec_roots_seen!r}"
    )
    assert "SPECIFICATION/templates/livespec" in spec_roots_seen, (
        f"expected livespec sub-spec-tree findings; got spec_roots={spec_roots_seen!r}"
    )
    assert "SPECIFICATION/templates/minimal" in spec_roots_seen, (
        f"expected minimal sub-spec-tree findings; got spec_roots={spec_roots_seen!r}"
    )
