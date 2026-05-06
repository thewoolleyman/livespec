"""commit_pairs_source_and_test — every source-touching commit also touches tests/ (v033 D3).

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-commit-pairs-source-and-test` row,
added at v033) and the v033 D3 revision file, every commit
modifying any `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, or `<repo-root>/dev-tooling/
checks/**` source file MUST also modify a `tests/**` file in
the same commit. Lefthook pre-commit gate; NOT in `just check`
aggregate (the aggregate runs once-per-`just check` invocation
on the working tree, while this gate is intrinsically
per-commit and inspects the staged state).

Pre-commit invocation context: lefthook runs the check before
the commit lands. The script reads `git diff --cached
--name-only` to enumerate staged files, applies the source-tree
filter, and verifies a `tests/**` co-staging.

**v034 D2-D3 amend-pattern coexistence.** When HEAD's
commit message carries `TDD-Red-Test-File-Checksum:` trailers
WITHOUT paired `TDD-Green-Verified-At:` trailers, the next
operation is structurally guaranteed by the v034 contract to
be `git commit --amend` adding the impl. During that amend,
`git diff --cached --name-only` shows only the impl files
(the Red commit's test is already in HEAD, unchanged), so the
naive staged-only enforcement would reject the amend. The
check skips itself in that case — the Red→Green replay contract
enforces pairing structurally (Red commit MUST stage a test;
Green amend MUST land impl and pass the test). The "every
feat/fix commit must also touch tests/**" contract is satisfied
by the post-amend commit (which contains BOTH the Red commit's
test and the Green amend's impl). Once the amend lands, HEAD carries both Red AND Green
trailers and the next commit's pre-commit sees the
"complete" state — the check resumes normal enforcement.

Cycle 1 implemented the bare rejection: any staged source-tree
file without a co-staged tests/-tree file fails the check.
Cycle 2.7 (this cycle) adds the v034 amend-mode skip described
above. Subsequent cycles will add the closed carve-out set
(refactor: prefix, ## Type: refactor / config / docs-only,
deletion-only commits, config-only filenames like
pyproject.toml / justfile / lefthook.yml / .mise.toml /
.vendor.jsonc / .gitignore).

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import
time.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_SOURCE_TREE_PREFIXES: tuple[str, ...] = (
    ".claude-plugin/scripts/livespec/",
    ".claude-plugin/scripts/bin/",
    "dev-tooling/checks/",
)
_TESTS_TREE_PREFIX: str = "tests/"
_RED_TRAILER_TOKEN: str = "TDD-Red-Test-File-Checksum:"
_GREEN_TRAILER_TOKEN: str = "TDD-Green-Verified-At:"


def _staged_files(*, cwd: Path) -> list[str]:
    # S603/S607: argv is a fixed list (literal git binary + literal flags);
    # bare `git` resolves via PATH; no untrusted shell input.
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _head_has_unpaired_red_trailers(*, cwd: Path) -> bool:
    """Detect HEAD = v034 D2-D3 Red commit pending Green amend.

    Returns True iff HEAD's commit message contains
    `TDD-Red-Test-File-Checksum:` AND does NOT contain
    `TDD-Green-Verified-At:` — the canonical "amend-pending"
    state. After the Green amend lands, HEAD's message
    carries both trailers and this function returns False.

    On a fresh repo with no commits, `git log -1` exits
    non-zero; the resulting `subprocess.CalledProcessError`
    is caught and treated as "no Red trailers" (returns
    False). The check then applies its normal enforcement.
    """
    # S603/S607: argv is a fixed list (literal git binary + literal flags);
    # bare `git` resolves via PATH; no untrusted shell input.
    result = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    message = result.stdout
    has_red = _RED_TRAILER_TOKEN in message
    has_green = _GREEN_TRAILER_TOKEN in message
    return has_red and not has_green


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("commit_pairs_source_and_test")
    cwd = Path.cwd()

    if _head_has_unpaired_red_trailers(cwd=cwd):
        log.info(
            "v034 D2-D3 Green amend in progress; commit-pairs check skipped",
            check_id="commit-pairs-source-and-test-amend-skip",
        )
        return 0

    staged = _staged_files(cwd=cwd)
    source_changes = [path for path in staged if path.startswith(_SOURCE_TREE_PREFIXES)]
    test_changes = [path for path in staged if path.startswith(_TESTS_TREE_PREFIX)]

    if source_changes and not test_changes:
        for source_path in source_changes:
            log.error(
                "source change staged without paired test change",
                source=source_path,
                staged_files=staged,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
