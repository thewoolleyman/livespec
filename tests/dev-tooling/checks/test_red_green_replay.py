"""Outside-in test for `dev-tooling/checks/red_green_replay.py` — v034 D2-D3 replay-based TDD enforcement.

Per `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
§"Testing approach — Activation §v034 D2-D3 Red→Green replay
contract" and Plan §"Per-commit Red→Green replay discipline
(v034 D2-D3)", this hook gates `feat:`/`fix:` commits via the
amend pattern (Red-mode initial commit; Green-mode amend) and
exempts other Conventional Commit types (chore, docs, build,
ci, style, test, refactor, perf, revert).

Cycle 173 pins the first behavior: a `chore:` commit subject
is exempt from TDD enforcement; the hook reads the commit
message file (passed as argv[1] per the git commit-msg hook
contract) and exits 0 without running any test.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_RED_GREEN_REPLAY = _REPO_ROOT / "dev-tooling" / "checks" / "red_green_replay.py"


def test_chore_commit_subject_exits_zero(*, tmp_path: Path) -> None:
    """A `chore:` commit subject is exempt from TDD enforcement; hook exits 0.

    Fixture: a tmp_path COMMIT_EDITMSG file containing
    `chore: codify v034`. The hook is invoked as a `commit-msg`
    git hook (the v034 D2-D3 design): argv[1] is the path to
    the commit message file. For non-`feat:`/`fix:` types the
    hook MUST exit 0 without running any test or computing any
    checksum.
    """
    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("chore: codify v034\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_green_replay should exit 0 for chore: subject; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_docs_commit_subject_exits_zero(*, tmp_path: Path) -> None:
    """A `docs:` commit subject is exempt from TDD enforcement; hook exits 0.

    Fixture: a tmp_path COMMIT_EDITMSG file containing
    `docs: clarify proposal`. Per v034 D3, `docs:` is one of
    the nine exempt Conventional Commit types (chore, docs,
    build, ci, style, test, refactor, perf, revert). Subsequent
    cycles add the remaining six exempt types one per cycle.
    """
    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("docs: clarify proposal\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_green_replay should exit 0 for docs: subject; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


@pytest.mark.parametrize(
    "type_token",
    ["build", "ci", "style", "test", "refactor", "perf", "revert"],
)
def test_remaining_exempt_commit_subjects_exit_zero(
    *, type_token: str, tmp_path: Path,
) -> None:
    """Each remaining v034 D3 exempt Conventional Commit type exits 0.

    Cycle 176 batches the seven types not yet pinned by
    cycles 173-175 (chore: by 173, docs: by 175). Per v034
    D3, the full exempt set is {chore, docs, build, ci,
    style, test, refactor, perf, revert} — config/meta
    types that produce no test/impl pairing and therefore
    do not require Red→Green replay verification. The
    parameterized test pins all seven remaining types in
    one test function (one Red→Green pair: list-extension
    is parameter expansion of the cycle-174
    type-discrimination switch, not new behavior).
    """
    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text(f"{type_token}: minor change\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_green_replay should exit 0 for {type_token}: subject; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_feat_commit_subject_exits_nonzero(*, tmp_path: Path) -> None:
    """A `feat:` commit subject is NOT exempt; hook MUST exit non-zero.

    Fixture: a tmp_path COMMIT_EDITMSG file containing
    `feat: add new feature`. Per v034 D3, `feat:` and `fix:`
    types require Red→Green replay verification — Red mode
    (test staged + no impl + pytest fails) or Green mode
    (amend with impl + pytest passes). With nothing to verify
    (no git repo, no staged tree, no Red-trailer parent), the
    hook cannot complete verification and MUST reject the
    commit. This pins the type-discrimination contract:
    non-exempt subjects do not exit 0. Future cycles refine
    the rejection diagnostic + add the actual replay logic.
    """
    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"red_green_replay should exit non-zero for feat: subject; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_feat_in_git_repo_with_no_staged_files_diagnoses_no_mode(*, tmp_path: Path) -> None:
    """A feat: subject in a git repo with NO staged files cannot enter Red or Green mode.

    Cycle 177 drives the first staged-tree inspection in the hook.
    Per Plan §"Per-commit Red→Green replay discipline (v034 D2-D3)",
    Red mode requires staged test files + no staged impl; Green mode
    requires HEAD~0 Red trailers + staged impl files. With ZERO staged
    files, neither mode applies; the hook MUST reject with a diagnostic
    on stderr that mentions "staged" so the developer understands the
    rejection reason. Pins the True branch of the staged-emptiness
    check.
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"feat: with empty staged tree must reject; "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )
    assert "staged" in result.stderr.lower(), (
        f"expected 'staged' diagnostic in stderr for empty-staged feat:; "
        f"got stderr={result.stderr!r}"
    )


def test_feat_in_git_repo_with_staged_files_skips_no_staged_diagnostic(
    *, tmp_path: Path,
) -> None:
    """A feat: subject in a git repo WITH staged files skips the no-staged diagnostic.

    Cycle 177 paired test: pins the False branch of the staged-emptiness
    check. With at least one staged file, the no-staged-files diagnostic
    MUST NOT fire on stderr; the hook still exits non-zero (the actual
    Red/Green replay verification logic — pytest invocation + checksum
    + trailer authoring — is not yet implemented), but the empty-staged
    rejection path is inactive. This guarantees per-file 100% branch
    coverage on the new staged-emptiness conditional.
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "test_dummy.py"
    test_file.write_text(
        "def test_x() -> None:\n    assert True\n", encoding="utf-8",
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "tests/test_dummy.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"feat: with staged files still rejects (full replay logic not yet implemented); "
        f"got returncode={result.returncode}"
    )
    assert "no staged files" not in result.stderr.lower(), (
        f"no-staged-files diagnostic must NOT fire when files ARE staged; "
        f"got stderr={result.stderr!r}"
    )


def test_feat_with_tests_only_staged_emits_red_mode_candidate(
    *, tmp_path: Path,
) -> None:
    """A feat: subject with tests-only staged is a Red-mode candidate.

    Cycle 178 drives the test/impl classification step. Per Plan
    §"Per-commit Red→Green replay discipline (v034 D2-D3)", Red mode
    is triggered when the staged tree carries test files but no
    implementation files. This test pins the True branch of
    "tests_paths AND NOT impl_paths" — staging a single file under
    `tests/` qualifies the commit as a Red-mode candidate; the hook
    emits a structured `red-mode-candidate` structlog event identifying
    the discriminator. The hook still exits non-zero (pytest invocation
    + Red-trailer authoring come in subsequent cycles).
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "test_dummy.py"
    test_file.write_text(
        "def test_x() -> None:\n    assert True\n", encoding="utf-8",
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "tests/test_dummy.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"feat: with tests-only staged still rejects (full Red replay not yet implemented); "
        f"got returncode={result.returncode}"
    )
    assert "red-mode-candidate" in result.stderr.lower(), (
        f"expected 'red-mode-candidate' diagnostic in stderr for tests-only feat:; "
        f"got stderr={result.stderr!r}"
    )


def test_feat_with_impl_only_staged_skips_red_mode_candidate(
    *, tmp_path: Path,
) -> None:
    """A feat: subject with impl-only staged is NOT a Red-mode candidate.

    Cycle 178 paired test: pins the False branch of the
    "tests_paths AND NOT impl_paths" check. With one file staged under
    `livespec/` (impl bucket) and zero files under `tests/`, the
    Red-mode-candidate diagnostic MUST NOT fire. The commit might still
    qualify for Green mode in a future cycle (HEAD~0 carrying Red
    trailers), but Red mode is by-construction unreachable without
    staged tests. Together with the True-branch test above, this
    guarantees per-file 100% branch coverage on the new conditional.
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    impl_dir = tmp_path / "livespec"
    impl_dir.mkdir()
    impl_file = impl_dir / "foo.py"
    impl_file.write_text("VALUE: int = 1\n", encoding="utf-8")
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "livespec/foo.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"feat: with impl-only staged still rejects (Green-mode replay not yet implemented); "
        f"got returncode={result.returncode}"
    )
    assert "red-mode-candidate" not in result.stderr.lower(), (
        f"red-mode-candidate diagnostic must NOT fire when impl is staged; "
        f"got stderr={result.stderr!r}"
    )


def test_feat_with_single_test_file_staged_emits_sha256_checksum(
    *, tmp_path: Path,
) -> None:
    """A feat: subject with one staged test file surfaces a SHA-256 checksum.

    Cycle 179 wires SHA-256 computation of the staged test file. Per
    PROPOSAL.md §"Testing approach — Activation §v034 D2-D3 Red→Green
    replay contract" and the trailer schema (`TDD-Red-Test-File-Checksum:
    sha256:<hex>`), the Red-mode hook computes the test file's SHA-256
    so the Green-mode amend can verify the test file is unchanged. This
    test pins: a tests-only-staged commit with exactly one path under
    `tests/` carries a `test_file_checksum` field on the
    red-mode-candidate event whose value is the literal `sha256:` prefix
    followed by the 64-character lowercase hex digest of the staged
    file's bytes. The exact hex digest is asserted against
    `hashlib.sha256(file_bytes).hexdigest()` to make the contract
    mechanical.
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "test_dummy.py"
    test_bytes = b"def test_x() -> None:\n    assert True\n"
    test_file.write_bytes(test_bytes)
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "tests/test_dummy.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    expected_digest = hashlib.sha256(test_bytes).hexdigest()
    expected_checksum_token = f"sha256:{expected_digest}"

    assert result.returncode != 0, (
        f"feat: with single test file staged still rejects "
        f"(full Red replay not yet implemented); "
        f"got returncode={result.returncode}"
    )
    assert "test_file_checksum" in result.stderr, (
        f"expected 'test_file_checksum' field in red-mode-candidate event; "
        f"got stderr={result.stderr!r}"
    )
    assert expected_checksum_token in result.stderr, (
        f"expected sha256:<hex> token {expected_checksum_token!r} in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_feat_with_multiple_test_files_staged_rejects_with_multi_test_file_diagnostic(
    *, tmp_path: Path,
) -> None:
    """A feat: subject with multiple staged test files is not a valid Red moment.

    Cycle 179 paired test: pins the False branch of the
    "len(tests_paths) > 1" rejection. Per the v034 D2 trailer schema,
    `TDD-Red-Test:` and `TDD-Red-Test-File-Checksum:` are singular
    fields — Red mode is per-file (one staged test file per Red commit),
    so multi-test-file staged trees must be rejected with a clear
    `multi-test-file` diagnostic. The hook returns non-zero without
    emitting a checksum (no single canonical test file to checksum).
    Together with the True-branch test above, this guarantees per-file
    100% branch coverage on the new conditional.
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        "def test_a() -> None:\n    assert True\n", encoding="utf-8",
    )
    (tmp_path / "tests" / "test_b.py").write_text(
        "def test_b() -> None:\n    assert True\n", encoding="utf-8",
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "tests/test_a.py", "tests/test_b.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"feat: with multiple test files staged must reject; "
        f"got returncode={result.returncode}"
    )
    assert "multi-test-file" in result.stderr.lower(), (
        f"expected 'multi-test-file' diagnostic in stderr; "
        f"got stderr={result.stderr!r}"
    )
    assert "test_file_checksum" not in result.stderr, (
        f"checksum field must NOT fire when multiple test files are staged; "
        f"got stderr={result.stderr!r}"
    )


def test_feat_with_failing_test_staged_emits_red_pytest_result(
    *, tmp_path: Path,
) -> None:
    """A feat: subject with a single failing staged test file pins a valid Red moment.

    Cycle 180 invokes pytest on the staged test file. Per Plan
    §"Per-commit Red→Green replay discipline (v034 D2-D3)", a Red
    moment requires the staged test to fail (non-zero pytest exit
    code). This test stages a `tests/test_failing.py` whose body
    asserts a falsy expression, then invokes the hook; the hook
    runs pytest, observes a non-zero returncode, and emits a
    structured `red-green-replay-red-pytest-result` info event
    carrying `pytest_returncode=<non-zero-int>`. Pins the False
    branch of `pytest_result.returncode == 0`.
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "test_failing.py"
    test_file.write_text(
        "def test_failing() -> None:\n"
        "    assert False, 'staged red test fails as required'\n",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "tests/test_failing.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"after cycle 181, Red-moment-confirmed exits 0 (commit proceeds); "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )
    assert "red-pytest-result" in result.stderr, (
        f"expected 'red-pytest-result' event in stderr for failing test; "
        f"got stderr={result.stderr!r}"
    )
    assert "pytest_returncode" in result.stderr, (
        f"expected 'pytest_returncode' field in red-pytest-result event; "
        f"got stderr={result.stderr!r}"
    )
    assert "test-passed-at-red" not in result.stderr, (
        f"test-passed-at-red rejection MUST NOT fire when pytest fails; "
        f"got stderr={result.stderr!r}"
    )


def test_feat_with_passing_test_staged_rejects_with_test_passed_at_red(
    *, tmp_path: Path,
) -> None:
    """A feat: subject with a single passing staged test file is NOT a Red moment.

    Cycle 180 paired test: pins the True branch of
    `pytest_result.returncode == 0`. If the staged test PASSES when
    run, the commit is not a valid Red moment (Red mode requires
    the test to fail so that the subsequent Green amend has
    something to make pass). The hook MUST reject with a
    structured `red-green-replay-test-passed-at-red` error and
    surface a `pytest_returncode=0` field. The
    `red-green-replay-red-pytest-result` info event MUST NOT
    fire on this path.
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "test_passing.py"
    test_file.write_text(
        "def test_passing() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "tests/test_passing.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"hook must reject when staged test passes; "
        f"got returncode={result.returncode}"
    )
    assert "test-passed-at-red" in result.stderr, (
        f"expected 'test-passed-at-red' rejection in stderr for passing test; "
        f"got stderr={result.stderr!r}"
    )
    assert "red-pytest-result" not in result.stderr, (
        f"red-pytest-result event MUST NOT fire when pytest passes; "
        f"got stderr={result.stderr!r}"
    )


def test_feat_with_failing_test_writes_full_red_trailer_schema(
    *, tmp_path: Path,
) -> None:
    """Red-moment confirmed → COMMIT_EDITMSG gains the v034 D2 trailer schema.

    Cycle 181 wires Red trailer authoring via `git interpret-trailers
    --in-place`. Per PROPOSAL.md §"Trailer schema", the full set of
    Red trailers required at the Red commit boundary is:

      TDD-Red-Test: <pytest-node-id>
      TDD-Red-Failure-Reason: <one-line failure summary>
      TDD-Red-Test-File-Checksum: sha256:<hex>
      TDD-Red-Output-Checksum: sha256:<hex>
      TDD-Red-Captured-At: <UTC ISO 8601>

    This test stages a single failing test, runs the hook, then
    re-reads the COMMIT_EDITMSG file and asserts each trailer key is
    present. The hook returns 0 (the new happy-path exit — Red moment
    fully verified, commit proceeds).
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "test_red.py"
    test_file.write_text(
        "def test_red() -> None:\n"
        "    assert False, 'red-trailer-test'\n",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "tests/test_red.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"Red-moment-confirmed must exit 0 (commit proceeds); "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )

    final_msg = msg_path.read_text(encoding="utf-8")
    for trailer_key in (
        "TDD-Red-Test:",
        "TDD-Red-Failure-Reason:",
        "TDD-Red-Test-File-Checksum:",
        "TDD-Red-Output-Checksum:",
        "TDD-Red-Captured-At:",
    ):
        assert trailer_key in final_msg, (
            f"expected trailer {trailer_key!r} in COMMIT_EDITMSG; "
            f"got final_msg={final_msg!r}"
        )
    assert "sha256:" in final_msg, (
        f"expected sha256: prefix in trailers (Test-File-Checksum + Output-Checksum); "
        f"got final_msg={final_msg!r}"
    )


def test_feat_with_impl_staged_and_head_has_red_trailers_emits_green_mode_candidate(
    *, tmp_path: Path,
) -> None:
    """Green-mode-candidate detection: HEAD~0 has Red trailers + impl staged.

    Cycle 182 wires the Green-mode dispatch counterpart to Red mode.
    Per PROPOSAL.md §"Green mode (amend)" lines 3533-3543, Green mode
    is triggered when the HEAD~0 commit message carries Red trailers
    AND the new staged tree adds implementation files. This test
    fixtures a Red commit by manually authoring a commit body with
    the v034 D2 trailer schema, then stages an impl file under
    `livespec/`, then invokes the hook. The hook MUST detect the
    Green-mode-candidate condition and emit a structured
    `red-green-replay-green-mode-candidate` info event. Returns 1
    (full Green replay logic — checksum re-verification, pytest
    invocation, Green trailer authoring — lands in subsequent
    cycles).
    """
    subprocess.run(  # noqa: S603, S607
        ["git", "init", "-q"], cwd=str(tmp_path), check=True,
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "config", "user.email", "test@test.test"],
        cwd=str(tmp_path),
        check=True,
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "config", "user.name", "Test User"],
        cwd=str(tmp_path),
        check=True,
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_red.py").write_text(
        "def test_red() -> None:\n    assert False\n",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "tests/test_red.py"],
        cwd=str(tmp_path),
        check=True,
    )
    red_commit_msg = (
        "feat: add new feature\n"
        "\n"
        "TDD-Red-Test: tests/test_red.py\n"
        "TDD-Red-Failure-Reason: AssertionError\n"
        "TDD-Red-Test-File-Checksum: sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
        "TDD-Red-Output-Checksum: sha256:1111111111111111111111111111111111111111111111111111111111111111\n"
        "TDD-Red-Captured-At: 2026-05-02T05:00:00Z\n"
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "commit", "-m", red_commit_msg],
        cwd=str(tmp_path),
        check=True,
    )

    (tmp_path / "livespec").mkdir()
    (tmp_path / "livespec" / "foo.py").write_text(
        "VALUE: int = 1\n", encoding="utf-8",
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "livespec/foo.py"],
        cwd=str(tmp_path),
        check=True,
    )

    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add green impl\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"Green-mode-candidate detection still rejects until full Green replay lands; "
        f"got returncode={result.returncode}"
    )
    assert "green-mode-candidate" in result.stderr.lower(), (
        f"expected 'green-mode-candidate' diagnostic in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_red_green_replay_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Structural test mirroring the project convention (see e.g.
    `test_check_tools.py::test_check_tools_module_importable_without_running_main`):
    importing the module exercises the `if __name__ == "__main__":`
    False branch so per-file coverage hits 100% line+branch.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "red_green_replay_for_import_test", str(_RED_GREEN_REPLAY),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
