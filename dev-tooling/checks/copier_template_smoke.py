"""copier_template_smoke — smoke test for templates/impl-plugin/.

Per livespec-core/SPECIFICATION/contracts.md §"Shared content sync
— copier template", livespec-core publishes a copier template at
`templates/impl-plugin/` and every `livespec-impl-*` repository
MUST be generated from it. This check is the acceptance gate that
the template is actually usable: it runs `copier copy` against a
tmpdir with a stock answers fixture, then verifies the generated
tree contains the expected file set and that JSON files parse.

The check does NOT exercise the generated repo's `just check` —
that would require installing the full toolchain (uv, just,
lefthook, mise) inside the tmpdir and is out of scope for a fast
per-commit smoke test. The structural assertions here are the
load-bearing acceptance gate for the C.6 sub-task of the Phase C
epic (li-jsl / li-vyj).

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_TEMPLATE_PATH_REL = Path("templates") / "impl-plugin"

_STOCK_ANSWERS: tuple[tuple[str, str], ...] = (
    ("plugin_short_name", "smoketest"),
    ("plugin_full_name", "livespec-impl-smoketest"),
    ("plugin_description", "Smoke-test fixture plugin for the impl-plugin template."),
    ("plugin_namespace", "livespec-impl-smoketest"),
    ("author_name", "Smoke Test"),
    ("author_email", "smoke@example.invalid"),
    ("github_owner", "thewoolleyman"),
    ("github_repo", "livespec-impl-smoketest"),
    ("python_version", "3.13"),
    ("livespec_core_release_tag", "v0.1.0"),
)

_EXPECTED_FILES: tuple[str, ...] = (
    # `.copier-answers.yml` is omitted from local-path copies (copier
    # writes it when generating from a git/remote source). The smoke
    # test invokes copier against a local path, so this file is not
    # expected in the generated tree.
    ".python-version",
    ".mise.toml",
    "pyproject.toml",
    "justfile",
    "lefthook.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/copier-update-drift.yml",
    ".claude-plugin/marketplace.json",
    ".claude-plugin/plugin.json",
    "SPECIFICATION/README.md",
    ".claude/skills/loop/SKILL.md",
)

_JSON_FILES: tuple[str, ...] = (
    ".claude-plugin/marketplace.json",
    ".claude-plugin/plugin.json",
)


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("copier_template_smoke")


def _run_copier_copy(*, template_path: Path, target: Path) -> subprocess.CompletedProcess[str]:
    data_args: list[str] = []
    for key, value in _STOCK_ANSWERS:
        data_args.extend(["--data", f"{key}={value}"])
    return subprocess.run(
        [
            "uv",
            "run",
            "copier",
            "copy",
            "--defaults",
            "--trust",
            "--vcs-ref=HEAD",
            *data_args,
            str(template_path),
            str(target),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    log = _configure_logger()
    repo_root = Path.cwd()
    template_path = repo_root / _TEMPLATE_PATH_REL
    if not (template_path / "copier.yml").is_file():
        log.error(
            "templates/impl-plugin/copier.yml not found",
            check_id="copier-template-smoke-missing-template",
            template_path=str(template_path),
            hint="Run from the livespec-core repo root.",
        )
        return 1
    with tempfile.TemporaryDirectory(prefix="livespec-copier-smoke-") as tmp_str:
        target = Path(tmp_str) / "generated"
        result = _run_copier_copy(template_path=template_path, target=target)
        if result.returncode != 0:
            log.error(
                "copier copy failed",
                check_id="copier-template-smoke-copy-failed",
                returncode=result.returncode,
                stdout_tail=result.stdout[-2000:],
                stderr_tail=result.stderr[-2000:],
            )
            return 1
        missing = [rel for rel in _EXPECTED_FILES if not (target / rel).is_file()]
        if missing:
            log.error(
                "generated tree missing expected files",
                check_id="copier-template-smoke-missing-output",
                missing=missing,
                hint="Check templates/impl-plugin/ for the corresponding .jinja sources.",
            )
            return 1
        json_failures: list[dict[str, str]] = []
        for rel in _JSON_FILES:
            path = target / rel
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                json_failures.append({"path": rel, "error": str(exc)})
        if json_failures:
            log.error(
                "generated JSON files do not parse",
                check_id="copier-template-smoke-invalid-json",
                failures=json_failures,
            )
            return 1
    log.info(
        "copier template smoke check passed",
        check_id="copier-template-smoke-ok",
        files_verified=len(_EXPECTED_FILES),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
