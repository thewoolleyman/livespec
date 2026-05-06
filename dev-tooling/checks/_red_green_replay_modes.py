"""Red-mode and Green-mode dispatch helpers for `red_green_replay`.

Extracted from `red_green_replay.py` at cycle 4c so the parent
file's LLOC stays under the 200-line ceiling enforced by
`check-complexity`. The split is purely organizational; the
behavior is identical to the inline original. The leading
underscore in the filename marks this as a private sibling
module — entry-point check scripts under `dev-tooling/checks/`
have no underscore prefix.
"""

from __future__ import annotations

import datetime
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    import structlog.stdlib

__all__: list[str] = []


def _head_has_red_trailers() -> bool:
    """Return True iff HEAD's commit message carries `TDD-Red-*` trailers."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        capture_output=True,
        text=True,
        check=False,
    )
    return "TDD-Red-Test-File-Checksum:" in result.stdout


def _head_trailer_value(*, key: str) -> str:
    """Return the value of HEAD~0's named trailer, or empty if absent."""
    result = subprocess.run(
        ["git", "log", "-1", f"--pretty=%(trailers:key={key},valueonly)"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _current_head_sha() -> str:
    """Return the current HEAD SHA via `git rev-parse HEAD`, or empty on failure."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _write_trailers(*, msg_path: Path, trailers: tuple[tuple[str, str], ...]) -> None:
    # Two-step write to handle the v034 D2-D3 Red re-amend case
    # (surfaced concretely 2026-05-04 during v039 D3 authoring):
    # three Red re-amends produced three sets of `TDD-Red-*`
    # trailers in the commit message, after which
    # `_head_trailer_value` returned a newline-joined string of
    # three identical paths and the Green-mode handler raised
    # FileNotFoundError on Path.read_bytes().
    #
    # Step 1: pre-strip any line in the existing message whose
    # leading token matches one of the keys we're about to write.
    # We CANNOT use `git interpret-trailers --if-exists=replace`
    # here because git's `replace` matching uses prefix-aliasing
    # (treats `TDD-Red-Test` and `TDD-Red-Test-File-Checksum` as
    # the same trailer when one is a prefix of the other) and
    # silently DROPS the longer-keyed trailer when a shorter
    # prefix is present. The Red trailer schema has exactly
    # this collision (`TDD-Red-Test` is a strict prefix of
    # `TDD-Red-Test-File-Checksum` and `TDD-Red-Output-Checksum`'s
    # base form), so prefix-matching corrupts the trailer set
    # rather than fixing the duplicate-append bug.
    #
    # Step 2: invoke `git interpret-trailers --in-place` to add
    # the new trailers. Git's trailer-block-formatting rules
    # (blank-line separator between body and trailer block,
    # `Key: value` formatting, etc.) are preserved.
    keys_to_replace = {key for key, _ in trailers}
    original_text = msg_path.read_text(encoding="utf-8")
    stripped_lines: list[str] = []
    for line in original_text.splitlines(keepends=True):
        head = line.split(":", 1)[0]
        if head in keys_to_replace:
            continue
        stripped_lines.append(line)
    msg_path.write_text("".join(stripped_lines), encoding="utf-8")

    args: list[str] = []
    for key, value in trailers:
        args.extend(["--trailer", f"{key}: {value}"])
    subprocess.run(
        ["git", "interpret-trailers", "--in-place", *args, str(msg_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def _handle_red_mode(
    *,
    msg_path: Path,
    log: structlog.stdlib.BoundLogger,
    tests_paths: list[str],
) -> int:
    if len(tests_paths) > 1:
        log.error(
            "multi-test-file: Red mode is per-file (one test file per commit)",
            check_id="red-green-replay-multi-test-file",
            tests_paths=tests_paths,
            hint=(
                "The v034 D2 trailer schema's "
                "`TDD-Red-Test-File-Checksum:` is a singular field; "
                "stage exactly one test file per Red commit."
            ),
        )
        return 1
    test_file_path = Path.cwd() / tests_paths[0]
    test_file_bytes = test_file_path.read_bytes()
    test_file_checksum = f"sha256:{hashlib.sha256(test_file_bytes).hexdigest()}"
    log.info(
        "red-mode-candidate: tests-only staged tree",
        check_id="red-green-replay-red-mode-candidate",
        tests_paths=tests_paths,
        test_file_checksum=test_file_checksum,
    )
    pytest_result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file_path), "--tb=no", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    if pytest_result.returncode == 0:
        log.error(
            "test-passed-at-red-moment: not a valid Red moment",
            check_id="red-green-replay-test-passed-at-red",
            tests_paths=tests_paths,
            test_file_checksum=test_file_checksum,
            pytest_returncode=pytest_result.returncode,
            hint=(
                "Red mode requires the staged test to fail; "
                "if the test already passes, this is not a Red "
                "moment (the subsequent Green amend has "
                "nothing to verify)."
            ),
        )
        return 1
    log.info(
        "red-pytest-result: test failed at Red moment as required",
        check_id="red-green-replay-red-pytest-result",
        tests_paths=tests_paths,
        test_file_checksum=test_file_checksum,
        pytest_returncode=pytest_result.returncode,
    )
    pytest_output = pytest_result.stdout + pytest_result.stderr
    output_checksum = f"sha256:{hashlib.sha256(pytest_output.encode('utf-8')).hexdigest()}"
    captured_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    failure_reason = " ".join(pytest_output.split())[:200]
    _write_trailers(
        msg_path=msg_path,
        trailers=(
            ("TDD-Red-Test", tests_paths[0]),
            ("TDD-Red-Failure-Reason", failure_reason),
            ("TDD-Red-Test-File-Checksum", test_file_checksum),
            ("TDD-Red-Output-Checksum", output_checksum),
            ("TDD-Red-Captured-At", captured_at),
        ),
    )
    return 0


def _handle_green_mode(
    *,
    msg_path: Path,
    log: structlog.stdlib.BoundLogger,
    impl_paths: list[str],
) -> int:
    log.info(
        "green-mode-candidate: HEAD~0 carries Red trailers + impl staged",
        check_id="red-green-replay-green-mode-candidate",
        impl_paths=impl_paths,
    )
    recorded_test = _head_trailer_value(key="TDD-Red-Test")
    recorded_checksum = _head_trailer_value(key="TDD-Red-Test-File-Checksum")
    green_test_path = Path.cwd() / recorded_test
    green_test_bytes = green_test_path.read_bytes()
    green_test_checksum = f"sha256:{hashlib.sha256(green_test_bytes).hexdigest()}"
    if green_test_checksum != recorded_checksum:
        log.error(
            "test-file-checksum-mismatch: test file changed between Red and Green",
            check_id="red-green-replay-checksum-mismatch",
            recorded=recorded_checksum,
            current=green_test_checksum,
            test_path=recorded_test,
            hint=(
                "The test file referenced by HEAD~0's "
                "TDD-Red-Test must be byte-identical at the "
                "Green amend; if you needed to change the test, "
                "author a new Red commit."
            ),
        )
        return 1
    green_pytest_result = subprocess.run(
        [sys.executable, "-m", "pytest", str(green_test_path), "--tb=no", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    if green_pytest_result.returncode != 0:
        log.error(
            "test-still-failing-at-green: not a valid Green moment",
            check_id="red-green-replay-test-still-failing",
            pytest_returncode=green_pytest_result.returncode,
            test_path=recorded_test,
            hint=(
                "Green mode requires the staged test to pass; "
                "the new impl has not yet made the Red test green."
            ),
        )
        return 1
    green_verified_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    green_parent_reflog = _current_head_sha()
    _write_trailers(
        msg_path=msg_path,
        trailers=(
            ("TDD-Green-Verified-At", green_verified_at),
            ("TDD-Green-Parent-Reflog", green_parent_reflog),
        ),
    )
    return 0
