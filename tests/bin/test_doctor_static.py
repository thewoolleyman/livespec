"""Outside-in integration test for `bin/doctor_static.py` — Phase 3 doctor rail.

Per Phase 5 plan §"Phase 3" lines 1438-1500 and PROPOSAL.md §"`doctor` →
Static-phase structure" (lines 2483-2562) + §"Static-phase output
contract" (lines 2610-2643), invoking `doctor_static.py` against a
spec tree iterates every `(spec_root, template_name)` pair, runs the
applicable check subset, and writes `{"findings": [...]}` JSON to
stdout conforming to `doctor_findings.schema.json`. Exit code 0 when
every finding is `pass` or `skipped`; exit 3 on any `fail` finding.

Per PROPOSAL.md §"Note on `bin/doctor.py`" (lines 872-880), there is
NO `bin/doctor.py` wrapper. The Python entry for the static phase is
`bin/doctor_static.py`; the LLM-driven phase is skill-prose only with
no Python module. The wrapper imports `livespec.doctor.run_static.main`
(distinct from the `livespec.commands.<cmd>` shape used by the other
sub-commands per `livespec/commands/CLAUDE.md`).

This module holds the OUTERMOST integration test for the doctor-static
exit-criterion round-trip. Per the v032 D2 outside-in walking
direction, the failure point of this single test advances forward
across many TDD cycles: first the wrapper file does not exist
(FileNotFoundError); next, the supervisor stub exists and emits an
empty `{"findings": []}` document; then the orchestrator-iteration
behavior; then each Phase-3 minimum check (`livespec_jsonc_valid`,
`template_exists`, `template_files_present`,
`proposed_changes_and_history_dirs`, `version_directories_complete`,
`version_contiguity`, `revision_to_proposed_change_pairing`,
`proposed_change_topic_format`); etc. Lower-layer unit tests (under
`tests/livespec/doctor/...`) are pulled into existence when this rail's
failure is too coarse to drive design at a specific layer.

The wrapper is invoked as a subprocess so the wrapper-shape +
bootstrap + supervisor plumbing is exercised end-to-end exactly as
Claude Code invokes it; runtime version-check, `sys.path` setup, and
structlog configuration all run for real here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCTOR_STATIC_WRAPPER = (
    _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "doctor_static.py"
)
_SEED_WRAPPER = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "seed.py"


def _seed_minimal_tree(*, tmp_path: Path) -> None:
    """Seed `tmp_path` with the smallest valid livespec spec tree.

    Uses `bin/seed.py` end-to-end so the resulting tree is exactly
    what a real `seed` flow produces (auto-captured proposal, history
    v001 snapshot, `.livespec.jsonc`, etc.). The tree is then the
    input under test for `doctor_static`.
    """
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec"},
            {"path": "SPECIFICATION/contracts.md", "content": "stub contracts"},
            {"path": "SPECIFICATION/constraints.md", "content": "stub constraints"},
            {"path": "SPECIFICATION/scenarios.md", "content": "stub scenarios"},
            {"path": "SPECIFICATION/README.md", "content": "stub readme"},
        ],
        "intent": "doctor-static integration test fixture",
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    seed_result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert seed_result.returncode == 0, (
        f"seed fixture invocation failed; "
        f"stdout={seed_result.stdout!r} stderr={seed_result.stderr!r}"
    )


def test_doctor_static_emits_findings_json_against_freshly_seeded_tree(
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` exits 0 and emits findings JSON against a freshly-seeded tree.

    A freshly-seeded `livespec`-template tree (built via `bin/seed.py`
    in this same test) satisfies every Phase-3 minimum check
    (`livespec_jsonc_valid`, `template_exists`, `template_files_present`,
    `proposed_changes_and_history_dirs`, `version_directories_complete`,
    `version_contiguity`, `revision_to_proposed_change_pairing`,
    `proposed_change_topic_format`). With every check passing, the
    orchestrator returns exit 0 and writes `{"findings": [...]}` JSON
    to stdout per PROPOSAL.md §"Static-phase output contract" lines
    2610-2643. The findings array conforms to
    `.claude-plugin/scripts/livespec/schemas/doctor_findings.schema.json`:
    a JSON object with exactly one required key `findings` whose value
    is an array.

    This cycle pins only the wrapper-exists + stdout-shape contract;
    later cycles pin the per-check `pass` Findings (one cycle per
    check or per orchestrator behavior).
    """
    _seed_minimal_tree(tmp_path=tmp_path)

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_DOCTOR_STATIC_WRAPPER)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"doctor_static wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    # Stdout contract: a single JSON document conforming to
    # doctor_findings.schema.json — one required key `findings` whose
    # value is a list.
    stdout = result.stdout
    parsed: object = json.loads(stdout)
    assert isinstance(parsed, dict), (
        f"doctor_static stdout must be a JSON object; got {type(parsed).__name__}: {parsed!r}"
    )
    assert "findings" in parsed, (
        f"doctor_static stdout must have a `findings` key; got keys {list(parsed.keys())!r}"
    )
    findings = parsed["findings"]
    assert isinstance(findings, list), (
        f"`findings` must be a JSON array; got {type(findings).__name__}: {findings!r}"
    )


def test_doctor_static_emits_pass_finding_for_livespec_jsonc_valid_against_seeded_tree(
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` emits a `pass` Finding for the `livespec-jsonc-valid` check.

    Pins the first Phase-3 minimum check into existence: the
    `livespec_jsonc_valid` static check (PROPOSAL.md §"`doctor` →
    Static-phase checks", Plan line 1481). Against a freshly-seeded
    tree, `.livespec.jsonc` is wrapper-owned (PROPOSAL.md §"`seed`"
    lines 1894-1924) and parses cleanly — the check therefore emits
    `status: "pass"`. The schema-required `check_id` field carries
    the `doctor-`-prefixed slug per PROPOSAL.md lines 2625-2628:
    module filename `livespec_jsonc_valid.py` → SLUG
    `"livespec-jsonc-valid"` → JSON `check_id`
    `"doctor-livespec-jsonc-valid"`.

    Cycle-21 scope: just this one check + the registry skeleton +
    the orchestrator-walks-the-registry behavior + the minimal
    Finding dataclass + the minimal DoctorContext (with only the
    field this check consumes). The full eight-check Phase-3 subset,
    the `(spec_root, template_name)` per-tree iteration, the
    applicability table, the bootstrap-lenience semantics, and the
    full `IOResult[Finding, LivespecError]` ROP plumbing all land
    in subsequent cycles, each driven by a specific test under
    consumer pressure (same pattern as cycle 8's plain-`str`
    `current_user_or_unknown` collapse of the IOResult shape).
    """
    _seed_minimal_tree(tmp_path=tmp_path)

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_DOCTOR_STATIC_WRAPPER)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"doctor_static wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    parsed: object = json.loads(result.stdout)
    assert isinstance(parsed, dict)
    findings = parsed["findings"]
    assert isinstance(findings, list)
    livespec_jsonc_findings = [
        f
        for f in findings
        if isinstance(f, dict) and f.get("check_id") == "doctor-livespec-jsonc-valid"
    ]
    assert len(livespec_jsonc_findings) >= 1, (
        f"expected >=1 finding with check_id 'doctor-livespec-jsonc-valid'; "
        f"got findings={findings!r}"
    )
    pass_findings = [f for f in livespec_jsonc_findings if f.get("status") == "pass"]
    assert len(pass_findings) >= 1, (
        f"expected at least one livespec-jsonc-valid finding with status='pass'; "
        f"got {livespec_jsonc_findings!r}"
    )


def test_doctor_static_emits_pass_finding_for_template_exists_against_seeded_tree(
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` emits a `pass` Finding for the `template-exists` check.

    Pins the second Phase-3 minimum check into existence: the
    `template_exists` static check (PROPOSAL.md §"`doctor` →
    Static-phase checks" lines 2672-2690, Plan line 1481). Against
    a freshly-seeded tree built with `template=livespec`, the
    bundle's `<bundle-root>/specification-templates/livespec/`
    directory exists on disk (Phase 2 scaffolding artifact), so
    the check emits `status: "pass"` after resolving the
    `template` field from `.livespec.jsonc`. Per PROPOSAL.md lines
    2625-2628, JSON `check_id` is `doctor-<slug>`; module
    `template_exists.py` → SLUG `"template-exists"` → JSON
    `check_id` `"doctor-template-exists"`.

    Cycle-22 scope: just this one check + its registration in
    `static/__init__.py` + the seed's `template` field flowing
    into `.livespec.jsonc` (consumer pressure: the check needs to
    KNOW which template was selected, not hide it behind the
    schema's default-when-absent fallback). The full
    `template-exists` semantics from PROPOSAL.md lines 2672-2690
    (template.json layout, `template_format_version` matching, the
    four required prompt files, doctor-llm prompt fields,
    `doctor_static_check_modules` list) all land in subsequent
    cycles, each driven by a specific failure-path test under
    consumer pressure. Same applies to bootstrap lenience (v014 N3
    `template_load_status`) and the orchestrator's applicability
    table that restricts `template_exists` to `template_name ==
    "main"` (PROPOSAL.md lines 2534-2538) — generalizes when
    sub-spec iteration is exercised.
    """
    _seed_minimal_tree(tmp_path=tmp_path)

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_DOCTOR_STATIC_WRAPPER)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"doctor_static wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    parsed: object = json.loads(result.stdout)
    assert isinstance(parsed, dict)
    findings = parsed["findings"]
    assert isinstance(findings, list)
    template_exists_findings = [
        f
        for f in findings
        if isinstance(f, dict) and f.get("check_id") == "doctor-template-exists"
    ]
    assert len(template_exists_findings) >= 1, (
        f"expected >=1 finding with check_id 'doctor-template-exists'; "
        f"got findings={findings!r}"
    )
    pass_findings = [f for f in template_exists_findings if f.get("status") == "pass"]
    assert len(pass_findings) >= 1, (
        f"expected at least one template-exists finding with status='pass'; "
        f"got {template_exists_findings!r}"
    )
