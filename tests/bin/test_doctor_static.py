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


def test_doctor_static_emits_pass_finding_for_template_files_present_against_seeded_tree(
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` emits a `pass` Finding for the `template-files-present` check.

    Pins the third Phase-3 minimum check into existence: the
    `template_files_present` static check (PROPOSAL.md §"`doctor`
    → Static-phase checks" lines 2691-2694, Plan line 1481).
    Per PROPOSAL.md lines 2691-2694, the check walks the active
    template's `specification-template/` directory and asserts each
    walked file exists at its expected repo-root-relative path
    (under `<spec-root>/`).

    Per Plan §"Phase 2" lines 1211-1214 the Phase-2 bootstrap
    state of `<bundle-root>/specification-templates/livespec/
    specification-template/` is "an empty skeleton (directory tree
    only, no starter content files). Starter content is generated
    agentically in Phase 7 from the template's sub-spec." The
    repo's current state matches that: the only on-disk file is
    a `.gitkeep` placeholder. `.gitkeep` is git-housekeeping
    plumbing — not a "starter content file" per Plan line 1212 —
    so the walker excludes it. With zero template-required files,
    the check trivially passes.

    Phase 7 will populate `specification-template/` with real
    content (PROPOSAL.md §"Definition of Done (v1)" line 3902:
    "full starter content under `specification-template/
    SPECIFICATION/`"); from then on the check meaningfully
    validates that seed materialized those files. The Phase-3
    bootstrap-minimum behavior of trivially-passing on an empty
    skeleton is the correct stepping stone — it pins the check's
    plumbing (registry registration, walker, repo-root-resolution,
    Finding shape) without depending on Phase-7 content.

    Per PROPOSAL.md lines 2625-2628, JSON `check_id` is
    `doctor-<slug>`; module `template_files_present.py` → SLUG
    `"template-files-present"` → JSON `check_id`
    `"doctor-template-files-present"`. Bootstrap lenience and the
    orchestrator's main-tree-only applicability for this check
    (PROPOSAL.md lines 2534-2538 — `template-files-present` is a
    main-tree-only check) defer to subsequent cycles, same
    pattern as `template-exists`.
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
    template_files_findings = [
        f
        for f in findings
        if isinstance(f, dict) and f.get("check_id") == "doctor-template-files-present"
    ]
    assert len(template_files_findings) >= 1, (
        f"expected >=1 finding with check_id 'doctor-template-files-present'; "
        f"got findings={findings!r}"
    )
    pass_findings = [f for f in template_files_findings if f.get("status") == "pass"]
    assert len(pass_findings) >= 1, (
        f"expected at least one template-files-present finding with status='pass'; "
        f"got {template_files_findings!r}"
    )


def test_doctor_static_emits_pass_finding_for_proposed_changes_and_history_dirs_against_seeded_tree(
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` emits a `pass` Finding for `proposed-changes-and-history-dirs`.

    Pins the fourth Phase-3 minimum check into existence: the
    `proposed_changes_and_history_dirs` static check
    (PROPOSAL.md §"`doctor` → Static-phase checks" lines
    2695-2698, Plan line 1481). Per PROPOSAL.md lines 2695-2698,
    the check verifies that `<spec-root>/proposed_changes/` and
    `<spec-root>/history/` directories both exist and contain
    their skill-owned `README.md` files.

    The skill-owned README content is frozen verbatim per
    PROPOSAL.md lines 992-1024: `proposed_changes/README.md`
    explains that the directory holds in-flight proposed changes,
    and `history/README.md` explains that the directory holds
    versioned snapshots. Per PROPOSAL.md lines 992-994, the
    READMEs are skill-owned: hard-coded inside the skill (the
    livespec Python package), written by `seed` only, NOT
    regenerated on every `revise`. Per PROPOSAL.md lines
    1065-1068, the README content is template-agnostic
    (same content for `livespec` and `minimal` templates;
    only the `<spec-root>/` base differs).

    Cycle-24 scope: the check itself + seed evolves under
    consumer pressure to materialize `<spec-root>/proposed_changes/`
    + its README + `<spec-root>/history/README.md` (the directory
    `<spec-root>/history/` already exists implicitly via
    `mkdir(parents=True)` for `history/v001/`). Per PROPOSAL.md
    lines 2025-2028, sub-spec trees ALSO get skill-owned READMEs
    written per-tree. Cycle 24 covers main-tree only; sub-spec
    coverage lands in a later cycle that exercises sub-spec
    iteration.

    Per PROPOSAL.md lines 2625-2628, JSON `check_id` is
    `doctor-<slug>`; module
    `proposed_changes_and_history_dirs.py` → SLUG
    `"proposed-changes-and-history-dirs"` → JSON `check_id`
    `"doctor-proposed-changes-and-history-dirs"`.
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
    pc_history_findings = [
        f
        for f in findings
        if isinstance(f, dict)
        and f.get("check_id") == "doctor-proposed-changes-and-history-dirs"
    ]
    assert len(pc_history_findings) >= 1, (
        f"expected >=1 finding with check_id 'doctor-proposed-changes-and-history-dirs'; "
        f"got findings={findings!r}"
    )
    pass_findings = [f for f in pc_history_findings if f.get("status") == "pass"]
    assert len(pass_findings) >= 1, (
        f"expected at least one proposed-changes-and-history-dirs finding "
        f"with status='pass'; got {pc_history_findings!r}"
    )


def test_doctor_static_emits_pass_finding_for_version_directories_complete_against_seeded_tree(
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` emits a `pass` Finding for `version-directories-complete`.

    Pins the fifth Phase-3 minimum check into existence: the
    `version_directories_complete` static check (PROPOSAL.md
    §"`doctor` → Static-phase checks" lines 2699-2707, Plan
    line 1481). Per PROPOSAL.md, every
    `<spec-root>/history/vNNN/` directory that is not the
    pruned-marker directory must contain (a) the full set of
    template-required files, (b) a `proposed_changes/` subdir,
    and (c) a per-version `README.md` when the active template
    declares a versioned per-version README. The pruned-marker
    directory (when `PRUNED_HISTORY.json` is present) contains
    ONLY that file.

    Cycle-25 scope: walks every `<spec-root>/history/v???/`
    directory and validates each against the requirements above.
    Per PROPOSAL.md lines 1416-1422, the "template-required
    files" set is derived by walking the active template's
    `specification-template/` directory. Per Plan §"Phase 2"
    lines 1211-1214, that directory is currently an "empty
    skeleton (directory tree only, no starter content files)";
    only `.gitkeep` is on disk, which the walker excludes (same
    reasoning as cycle 23's `template-files-present`). The
    derived requirement set is therefore empty at Phase 3, and
    the check focuses on the unconditional requirement
    (`proposed_changes/` subdir exists per version directory)
    plus the conditional per-version README requirement (which
    is also derived from the empty `specification-template/`
    walk, hence vacuously satisfied at Phase 3). When Phase 7
    populates `specification-template/` with real content, the
    check meaningfully validates each version directory's
    snapshot completeness.

    Against a freshly-seeded tree, only `v001` exists and seed
    has materialized `<spec-root>/history/v001/proposed_changes/`
    (cycle 4). The check passes.

    Out of cycle-25 scope (deferred): pruned-marker handling
    (no `PRUNED_HISTORY.json` exists at Phase 3 — drives in when
    a `prune-history` integration test forces it); per-version
    README requirement (derived-from-walk vacuously satisfied
    today; meaningful at Phase 7); failure-path findings
    (missing-file paths in specific versions); bootstrap
    lenience; sub-spec iteration.

    Per PROPOSAL.md lines 2625-2628, JSON `check_id` is
    `doctor-<slug>`; module
    `version_directories_complete.py` → SLUG
    `"version-directories-complete"` → JSON `check_id`
    `"doctor-version-directories-complete"`.
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
    vdc_findings = [
        f
        for f in findings
        if isinstance(f, dict)
        and f.get("check_id") == "doctor-version-directories-complete"
    ]
    assert len(vdc_findings) >= 1, (
        f"expected >=1 finding with check_id 'doctor-version-directories-complete'; "
        f"got findings={findings!r}"
    )
    pass_findings = [f for f in vdc_findings if f.get("status") == "pass"]
    assert len(pass_findings) >= 1, (
        f"expected at least one version-directories-complete finding "
        f"with status='pass'; got {vdc_findings!r}"
    )


def test_doctor_static_emits_pass_finding_for_version_contiguity_against_seeded_tree(
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` emits a `pass` Finding for `version-contiguity`.

    Pins the sixth Phase-3 minimum check into existence: the
    `version_contiguity` static check (PROPOSAL.md §"`doctor`
    → Static-phase checks" lines 2708-2711, Plan line 1481).
    Per PROPOSAL.md, version numbers in `<spec-root>/history/`
    MUST be contiguous from `pruned_range.end + 1` (when
    `PRUNED_HISTORY.json` exists at the oldest surviving
    directory) or from `v001` upward. Numeric parsing applies —
    not lexical (PROPOSAL.md lines 1718-1720).

    Per PROPOSAL.md lines 1715-1726: version directories are
    `vNNN` zero-padded to ≥3 digits, mixed widths within
    `history/` are valid (the v1000+ widening), and version
    numbers must be parsed and compared numerically.

    Against a freshly-seeded tree, only `v001` exists. A
    single-version sequence is trivially contiguous; the check
    emits `status: "pass"`. Multi-version coverage (v001 +
    v002 after a `revise` invocation) lands when an
    integration test exercises the post-revise tree shape.

    Cycle-26 scope: directory walk + numeric parsing of `vNNN`
    suffixes + contiguity assertion against the parsed sequence.
    Pruned-marker handling (`PRUNED_HISTORY.json` at the
    oldest surviving directory; pruned range treated as
    intentional missing history per PROPOSAL.md lines 1781-
    1784) defers to a `prune-history`-test cycle. Bootstrap
    lenience defers, same pattern as cycles 21-25.

    Per PROPOSAL.md lines 2625-2628, JSON `check_id` is
    `doctor-<slug>`; module `version_contiguity.py` → SLUG
    `"version-contiguity"` → JSON `check_id`
    `"doctor-version-contiguity"`.

    Uniform across spec trees per PROPOSAL.md §"Per-tree
    check applicability" — runs unconditionally for every
    spec tree, no main-tree-only restriction.
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
    contiguity_findings = [
        f
        for f in findings
        if isinstance(f, dict)
        and f.get("check_id") == "doctor-version-contiguity"
    ]
    assert len(contiguity_findings) >= 1, (
        f"expected >=1 finding with check_id 'doctor-version-contiguity'; "
        f"got findings={findings!r}"
    )
    pass_findings = [f for f in contiguity_findings if f.get("status") == "pass"]
    assert len(pass_findings) >= 1, (
        f"expected at least one version-contiguity finding "
        f"with status='pass'; got {contiguity_findings!r}"
    )


def test_doctor_static_emits_pass_finding_for_revision_to_proposed_change_pairing_against_seeded_tree(  # noqa: E501
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` emits a `pass` Finding for `revision-to-proposed-change-pairing`.

    Pins the seventh Phase-3 minimum check into existence: the
    `revision_to_proposed_change_pairing` static check
    (PROPOSAL.md §"`doctor` → Static-phase checks" lines 2712-
    2720, Plan line 1481). Per PROPOSAL.md, for every
    `<stem>-revision.md` in `<spec-root>/history/vNNN/proposed_changes/`,
    a corresponding `<stem>.md` MUST exist in the same directory.
    Pairing walks filename stems (NOT front-matter `topic`
    values); under v014 N6 collision disambiguation, `<stem>` may
    include a `-N` suffix (e.g., `foo-2-revision.md` pairs with
    `foo-2.md`). See PROPOSAL.md §"Proposed-change file format"
    → "Filename stem vs. front-matter `topic` distinction"
    (lines 2974-2985) for why stem-based pairing is correct.

    Per PROPOSAL.md line 2712-2714, the check scope is the
    history subtree (`<spec-root>/history/vNNN/proposed_changes/`),
    NOT the working `<spec-root>/proposed_changes/`. After a
    successful `revise`, the working directory is empty of
    in-flight proposals (only the skill-owned README persists);
    paired `*-revision.md` files exist only in history per the
    revise lifecycle (PROPOSAL.md lines 2421-2431).

    Against a freshly-seeded tree, seed cycles 7-8 wrote an
    auto-captured pair at
    `<spec-root>/history/v001/proposed_changes/`:
    `seed.md` + `seed-revision.md`. The pair satisfies the
    check; the check emits `status: "pass"`. Multi-version
    coverage (additional pairs in v002 after a `revise`) lands
    when an integration test exercises the post-revise tree.

    Cycle-27 scope: walk every
    `<spec-root>/history/v???/proposed_changes/` directory and
    validate stem-based pairing for each `*-revision.md` file.
    Sub-spec iteration (sub-spec history subtrees), bootstrap
    lenience (v014 N3), and detailed failure-path Findings
    naming each orphan revision defer to subsequent cycles,
    same pattern as cycles 21-26.

    Per PROPOSAL.md lines 2625-2628, JSON `check_id` is
    `doctor-<slug>`; module
    `revision_to_proposed_change_pairing.py` → SLUG
    `"revision-to-proposed-change-pairing"` → JSON `check_id`
    `"doctor-revision-to-proposed-change-pairing"`.

    Uniform across spec trees per PROPOSAL.md §"Per-tree check
    applicability" — runs unconditionally, no main-tree-only
    restriction.
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
    pairing_findings = [
        f
        for f in findings
        if isinstance(f, dict)
        and f.get("check_id") == "doctor-revision-to-proposed-change-pairing"
    ]
    assert len(pairing_findings) >= 1, (
        f"expected >=1 finding with check_id 'doctor-revision-to-proposed-change-pairing'; "
        f"got findings={findings!r}"
    )
    pass_findings = [f for f in pairing_findings if f.get("status") == "pass"]
    assert len(pass_findings) >= 1, (
        f"expected at least one revision-to-proposed-change-pairing finding "
        f"with status='pass'; got {pairing_findings!r}"
    )


def test_doctor_static_emits_pass_finding_for_proposed_change_topic_format_against_seeded_tree(
    *, tmp_path: Path
) -> None:
    """`doctor_static.py` emits a `pass` Finding for `proposed-change-topic-format`.

    Pins the eighth (and final) Phase-3 minimum check into
    existence: the `proposed_change_topic_format` static check
    (PROPOSAL.md §"`doctor` → Static-phase checks" lines 2721-
    2723, Plan line 1481). Per PROPOSAL.md, every file in the
    working `<spec-root>/proposed_changes/` MUST have a name
    conforming to `<topic>.md` where `<topic>` is the
    canonicalized kebab-case form per PROPOSAL.md §"Topic
    canonicalization (v015 O3)" lines 2162-2173: lowercase →
    `[a-z0-9-]+` with no leading/trailing hyphens → max 64
    characters → non-empty.

    Per PROPOSAL.md line 2722, the check scope is the **working
    directory** (`<spec-root>/proposed_changes/`), NOT history.
    The skill-owned `README.md` (PROPOSAL.md lines 992-994 +
    line 2452: "the skill-owned `proposed_changes/README.md`
    persists" after `revise`) is the one fixed-name entity in
    that directory and is excluded from the topic-format check
    (the check is about validating *proposed-change* filenames,
    not the skill-owned readme).

    Against a freshly-seeded tree, the working
    `<spec-root>/proposed_changes/` contains only the
    skill-owned `README.md` (cycle 24). The check excludes it
    and finds zero proposed-change files to validate, so the
    check emits `status: "pass"` (vacuously). When a
    `propose-change` invocation populates the working directory
    with `<topic>.md` files, the check meaningfully validates
    each filename against the canonical kebab-case format.

    Cycle-28 scope: walk `<spec-root>/proposed_changes/`,
    exclude `README.md`, validate each remaining filename
    matches `^[a-z0-9](-?[a-z0-9])*\\.md$` (the canonical
    topic-format regex enforcing lowercase, hyphen-separator,
    no-leading-or-trailing-hyphens, non-empty). The 64-char
    limit is structurally satisfied by the canonicalization
    pipeline and does not need a separate length check at this
    cycle (the failure-path test that pins the length-limit
    branch lands later). Bootstrap lenience and detailed
    failure-path Findings naming each non-conforming filename
    defer, same pattern as cycles 21-27.

    Per PROPOSAL.md lines 2625-2628, JSON `check_id` is
    `doctor-<slug>`; module
    `proposed_change_topic_format.py` → SLUG
    `"proposed-change-topic-format"` → JSON `check_id`
    `"doctor-proposed-change-topic-format"`.

    Uniform across spec trees per PROPOSAL.md §"Per-tree check
    applicability" — runs unconditionally, no main-tree-only
    restriction.
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
    topic_findings = [
        f
        for f in findings
        if isinstance(f, dict)
        and f.get("check_id") == "doctor-proposed-change-topic-format"
    ]
    assert len(topic_findings) >= 1, (
        f"expected >=1 finding with check_id 'doctor-proposed-change-topic-format'; "
        f"got findings={findings!r}"
    )
    pass_findings = [f for f in topic_findings if f.get("status") == "pass"]
    assert len(pass_findings) >= 1, (
        f"expected at least one proposed-change-topic-format finding "
        f"with status='pass'; got {topic_findings!r}"
    )


def _seed_main_plus_livespec_sub_spec_tree(*, tmp_path: Path) -> None:
    """Seed `tmp_path` with a `livespec`-template main spec + one `livespec` sub-spec.

    Per Plan §"After seed" lines 2280-2311, the post-seed tree
    carries the main spec at `SPECIFICATION/` plus a sub-spec at
    `SPECIFICATION/templates/livespec/` with the same multi-file
    structure (uniform livespec-internal layout per v020 Q1). The
    sub-spec receives skill-owned READMEs (per PROPOSAL.md lines
    2025-2028, written per-tree) but does NOT receive an auto-
    captured seed proposal pair (per PROPOSAL.md lines 2032-2034
    / v018 Q1, sub-specs do not each get their own seed
    artifact — the main-spec seed.md documents the whole
    multi-tree creation).
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
    sub_files = [
        {
            "path": "SPECIFICATION/templates/livespec/spec.md",
            "content": "sub-spec stub spec",
        },
        {
            "path": "SPECIFICATION/templates/livespec/contracts.md",
            "content": "sub-spec stub contracts",
        },
        {
            "path": "SPECIFICATION/templates/livespec/constraints.md",
            "content": "sub-spec stub constraints",
        },
        {
            "path": "SPECIFICATION/templates/livespec/scenarios.md",
            "content": "sub-spec stub scenarios",
        },
        {
            "path": "SPECIFICATION/templates/livespec/README.md",
            "content": "sub-spec stub readme",
        },
    ]
    payload: dict[str, object] = {
        "template": "livespec",
        "files": main_files,
        "intent": "doctor-static sub-spec iteration test fixture",
        "sub_specs": [
            {"template_name": "livespec", "files": sub_files},
        ],
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


def test_doctor_static_iterates_main_and_each_sub_spec_tree(*, tmp_path: Path) -> None:
    """`doctor_static.py` runs the applicable check subset against every spec tree.

    Pins the orchestrator's `(spec_root, template_name)` pair
    iteration (PROPOSAL.md §"`doctor` → Static-phase structure"
    lines 2513-2542, Plan lines 1438-1466). At startup the
    orchestrator enumerates pairs: the main spec tree first
    (template_name sentinel `"main"`), then each sub-spec tree
    under `<main-spec-root>/templates/<sub-name>/` discovered
    via directory listing. Per PROPOSAL.md lines 2520-2525, each
    pair gets a fresh `DoctorContext` with `spec_root` set to
    that tree's root and `template_name` set to the marker.

    Per the orchestrator-owned applicability table (PROPOSAL.md
    lines 2526-2540 / v021 Q1):

    - `template-exists` and `template-files-present` are
      main-tree-only checks. Sub-spec trees do NOT re-run them.
    - Every other Phase-3 check runs uniformly per tree.

    Each Finding's `spec_root` field discriminates per-tree
    origin (PROPOSAL.md lines 2549-2551 + finding.schema.json's
    `spec_root` required field). For a freshly-seeded tree with
    one `livespec` sub-spec, findings carry either
    `spec_root == "SPECIFICATION"` (main tree) or
    `spec_root == "SPECIFICATION/templates/livespec"` (sub-spec
    tree).

    Cycle-29 scope: orchestrator iteration + applicability
    table + Finding `spec_root` discrimination + seed evolution
    to write skill-owned READMEs per sub-spec tree (consumer-
    pressure step: doctor's per-tree iteration now demands
    each sub-spec have its `<sub-spec>/proposed_changes/README.md`
    and `<sub-spec>/history/README.md`, per PROPOSAL.md lines
    2025-2028). The full PROPOSAL.md
    `gherkin-blank-line-format` sub-spec applicability rule
    (PROPOSAL.md lines 2528-2533) defers to Phase 7 when that
    check is authored. Bootstrap lenience defers, same pattern
    as cycles 21-28.
    """
    _seed_main_plus_livespec_sub_spec_tree(tmp_path=tmp_path)

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
    findings_obj = parsed["findings"]
    assert isinstance(findings_obj, list)
    findings = [f for f in findings_obj if isinstance(f, dict)]

    # Findings include both main-tree and sub-spec-tree entries.
    main_spec_roots = {
        f["spec_root"] for f in findings if f.get("spec_root") == "SPECIFICATION"
    }
    sub_spec_roots = {
        f["spec_root"]
        for f in findings
        if f.get("spec_root") == "SPECIFICATION/templates/livespec"
    }
    assert "SPECIFICATION" in main_spec_roots, (
        f"expected findings with spec_root='SPECIFICATION' (main tree); "
        f"got findings={findings!r}"
    )
    assert "SPECIFICATION/templates/livespec" in sub_spec_roots, (
        f"expected findings with spec_root='SPECIFICATION/templates/livespec' "
        f"(sub-spec tree); got findings={findings!r}"
    )

    # Applicability: `template-exists` and `template-files-present`
    # appear ONLY for the main tree (main-tree-only per
    # PROPOSAL.md lines 2534-2538).
    main_only_check_ids = {
        "doctor-template-exists",
        "doctor-template-files-present",
    }
    for check_id in main_only_check_ids:
        spec_roots_for_check = {
            f["spec_root"] for f in findings if f.get("check_id") == check_id
        }
        assert spec_roots_for_check == {"SPECIFICATION"}, (
            f"expected {check_id} to appear ONLY for main spec_root=='SPECIFICATION'; "
            f"got spec_roots={spec_roots_for_check!r}"
        )

    # Other Phase-3 checks run uniformly per tree — at least one
    # uniform check must appear in BOTH spec_roots.
    uniform_check_ids = {
        "doctor-livespec-jsonc-valid",
        "doctor-proposed-changes-and-history-dirs",
        "doctor-version-directories-complete",
        "doctor-version-contiguity",
        "doctor-revision-to-proposed-change-pairing",
        "doctor-proposed-change-topic-format",
    }
    for check_id in uniform_check_ids:
        spec_roots_for_check = {
            f["spec_root"] for f in findings if f.get("check_id") == check_id
        }
        assert "SPECIFICATION" in spec_roots_for_check, (
            f"expected {check_id} to appear for main tree; "
            f"got spec_roots={spec_roots_for_check!r}"
        )
        assert "SPECIFICATION/templates/livespec" in spec_roots_for_check, (
            f"expected {check_id} to appear for sub-spec tree; "
            f"got spec_roots={spec_roots_for_check!r}"
        )

    # All findings emitted are pass (the freshly-seeded tree
    # satisfies every applicable check).
    fail_findings = [f for f in findings if f.get("status") == "fail"]
    assert not fail_findings, (
        f"expected zero fail findings on freshly-seeded sub-spec tree; "
        f"got {fail_findings!r}"
    )
