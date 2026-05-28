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

Per livespec-core/SPECIFICATION/contracts.md §"Shared code sync —
livespec-dev-tooling", the template's
`justfile.jinja` stamps the full canonical check-slug aggregate at
copier-copy time via the
`copier_extensions.canonical_checks:CanonicalChecksExtension` Jinja
extension. This check verifies (a) the extension resolves at copy
time by injecting `<repo-root>/dev-tooling` onto the subprocess
PYTHONPATH, and (b) the generated `justfile` contains every slug
from `livespec_dev_tooling.canonical_checks.canonical_check_slugs()`
in alphabetical order.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import json
import os
import re
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
_DEV_TOOLING_REL = Path("dev-tooling")
# Regex matching the bash array entry shape inside the `check:`
# recipe's `targets=(...)` block. Each canonical slug is rendered
# as 8-space-indented bareword on its own line by `justfile.jinja`'s
# `{%- for slug in canonical_check_slugs %}` loop. The check matches
# only `check-*` identifiers to avoid accidentally catching shell
# keywords or comment text that might appear in other recipes.
_TARGETS_LINE_RE = re.compile(r"^ {8}(check-[a-z0-9-]+)$", re.MULTILINE)

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
    ("livespec_release_tag", "v0.1.0"),
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
    ".claude/settings.json",
)

_JSON_FILES: tuple[str, ...] = (
    ".claude-plugin/marketplace.json",
    ".claude-plugin/plugin.json",
    ".claude/settings.json",
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


def _build_copier_env(*, repo_root: Path) -> dict[str, str]:
    """Build the env dict for the `copier copy` subprocess.

    Injects `<repo-root>/dev-tooling` onto `PYTHONPATH` so the
    `copier_extensions.canonical_checks:CanonicalChecksExtension`
    Jinja extension referenced by `templates/impl-plugin/copier.yml`
    resolves under `uv run copier copy`. Without this, copier's
    Jinja2 environment construction raises `ExtensionNotFoundError`
    because `uv run` does not auto-add the project root to
    `sys.path`.
    """
    env = dict(os.environ)
    dev_tooling_abs = str(repo_root / _DEV_TOOLING_REL)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{dev_tooling_abs}{os.pathsep}{existing}" if existing else dev_tooling_abs
    return env


def _run_copier_copy(
    *, template_path: Path, target: Path, repo_root: Path
) -> subprocess.CompletedProcess[str]:
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
        env=_build_copier_env(repo_root=repo_root),
    )


def _expected_canonical_slugs(*, repo_root: Path) -> tuple[str, ...] | None:
    """Resolve the canonical check-slug tuple by importing the source-of-truth.

    Returns `None` when `livespec_dev_tooling.canonical_checks` is not
    importable in the current environment — this signals that the pin
    has not yet been bumped to a release that ships the module, and
    the canonical-slug assertion below skips gracefully (the
    structural assertions are the load-bearing gate; the slug-set
    assertion is defense-in-depth for the wiring-completeness
    invariant). The skip is logged at warn level so green CI does
    not hide a missing canonical_checks module.

    The `repo_root` argument is reserved for a future tightening
    (e.g., reading a vendored fallback list) but is not used today.
    """
    # `repo_root` is currently unused; kept in the signature so the
    # callsite documents the dependency and future implementations
    # can introduce a vendored-fallback path without touching the
    # caller.
    _ = repo_root
    # Local import: defers the ImportError to the call site so the
    # surrounding check still runs its structural assertions even
    # when the canonical_checks module is absent. This is the
    # transitional shape — once livespec's pin reaches the release
    # that ships canonical_checks, the fallback branch becomes
    # dead code and can be removed.
    try:
        from livespec_dev_tooling.canonical_checks import canonical_check_slugs
    except ImportError:  # pragma: no cover — transitional pin-bump path; see docstring.
        return None
    return canonical_check_slugs()


def _extract_stamped_targets(*, justfile_text: str) -> tuple[str, ...]:
    """Return the bareword `check-*` slug list from the `targets=(...)` block.

    Matches every 8-space-indented `check-<kebab>` line, preserving
    file order. Comparison against the expected canonical tuple
    pins both set membership and alphabetical ordering.
    """
    return tuple(_TARGETS_LINE_RE.findall(justfile_text))


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
        result = _run_copier_copy(template_path=template_path, target=target, repo_root=repo_root)
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
        # Wiring-completeness invariant: the generated `justfile`
        # MUST stamp every canonical check slug, in alphabetical
        # order, inside the `check:` recipe's `targets=(...)` array.
        # Helper handles the skip-vs-assert branch + diagnostic
        # emission.
        canonical_outcome = _verify_canonical_slug_stamping(
            log=log, target=target, repo_root=repo_root
        )
        if canonical_outcome is None:
            return 1
        slugs_verified = canonical_outcome
    log.info(
        "copier template smoke check passed",
        check_id="copier-template-smoke-ok",
        files_verified=len(_EXPECTED_FILES),
        canonical_slugs_verified=slugs_verified,
    )
    return 0


def _verify_canonical_slug_stamping(
    *, log: structlog.stdlib.BoundLogger, target: Path, repo_root: Path
) -> int | None:
    """Verify the generated justfile stamps every canonical check slug.

    Returns:
        - `int` (count of expected slugs) on success.
        - `0` when the canonical_checks module is not importable and
          the assertion is skipped (transitional-pin path).
        - `None` when a drift is detected; the caller propagates the
          non-zero exit. The drift diagnostic has already been logged.
    """
    expected_slugs = _expected_canonical_slugs(repo_root=repo_root)
    # pragma: no cover — transitional pin-bump path; see
    # _expected_canonical_slugs docstring.
    if expected_slugs is None:  # pragma: no cover
        log.warning(
            (
                "livespec_dev_tooling.canonical_checks not importable; "
                "skipping canonical-aggregate stamping assertion"
            ),
            check_id="copier-template-smoke-canonical-slugs-skipped",
            hint=(
                "Bump the livespec-dev-tooling pin to a release that "
                "ships canonical_checks; this skip is transitional."
            ),
        )
        return 0
    justfile_path = target / "justfile"
    justfile_text = justfile_path.read_text(encoding="utf-8")
    stamped = _extract_stamped_targets(justfile_text=justfile_text)
    if stamped == expected_slugs:
        return len(expected_slugs)
    log.error(
        (
            "generated justfile's targets=(...) array does not "
            "match canonical check-slug aggregate"
        ),
        check_id="copier-template-smoke-canonical-slug-drift",
        expected_count=len(expected_slugs),
        stamped_count=len(stamped),
        missing=sorted(set(expected_slugs) - set(stamped)),
        extra=sorted(set(stamped) - set(expected_slugs)),
        out_of_order=stamped != tuple(sorted(stamped)),
        hint=(
            "Verify the copier Jinja extension at "
            "dev-tooling/copier_extensions/canonical_checks.py "
            "resolves and that justfile.jinja loops over "
            "canonical_check_slugs."
        ),
    )
    return None


if __name__ == "__main__":
    raise SystemExit(main())
