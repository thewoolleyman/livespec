"""copier_template_smoke — smoke test for templates/orchestrator-plugin/.

Per livespec-core/SPECIFICATION/contracts.md, livespec-core publishes a copier template at
`templates/orchestrator-plugin/` and every `livespec-impl-*` repository
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

Per livespec-core/SPECIFICATION/contracts.md Template gate, the template's `justfile.jinja`
stamps the full canonical check-slug aggregate at copier-copy time
from the committed STATIC DATA file `canonical-slugs.yml` (a
release-time projection of
`livespec_dev_tooling.canonical_checks.canonical_check_slugs()`,
regenerated via `just stamp-canonical-slugs` and `{% include %}`'d by
`justfile.jinja`). This check verifies the generated `justfile`
contains every slug from
`livespec_dev_tooling.canonical_checks.canonical_check_slugs()` in
alphabetical order. The stamping is import-free — there is no copier
Jinja extension and no PYTHONPATH injection — so this check exercises
the same render path the consumer `copier update` flow uses (the
`canonical-slugs-projection` check separately gates that the committed
`canonical-slugs.yml` matches the source of truth).

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import json
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


_TEMPLATE_PATH_REL = Path("templates") / "orchestrator-plugin"
# Regex matching the bash array entry shape inside the `check:`
# recipe's `targets=(...)` block. Each canonical slug is rendered
# as 8-space-indented bareword on its own line by `justfile.jinja`'s
# include-then-line-parse loop over the committed canonical-slugs.yml
# data file. The check matches only `check-*` identifiers to avoid
# accidentally catching shell keywords or comment text in other recipes.
_TARGETS_LINE_RE = re.compile(r"^ {8}(check-[a-z0-9-]+)$", re.MULTILINE)

_STOCK_ANSWERS: tuple[tuple[str, str], ...] = (
    ("plugin_short_name", "smoketest"),
    ("plugin_full_name", "livespec-impl-smoketest"),
    ("plugin_description", "Smoke-test fixture plugin for the orchestrator-plugin template."),
    ("plugin_namespace", "livespec-impl-smoketest"),
    ("author_name", "Smoke Test"),
    ("author_email", "smoke@example.invalid"),
    ("github_owner", "thewoolleyman"),
    ("github_repo", "livespec-impl-smoketest"),
    ("python_version", "3.13"),
    ("livespec_release_tag", "v0.1.0"),
)

_EXPECTED_FILES: tuple[str, ...] = (
    # `.copier-answers.yml` is rendered from the template's answers-file
    # boilerplate (`{{ _copier_conf.answers_file }}.jinja`) on EVERY
    # copy, regardless of source kind — local-path copies merely omit
    # the `_commit` key (no VCS version to record). Pinning it here
    # makes the smoke gate fail loudly if the boilerplate is ever
    # dropped, which would re-introduce the stuck-`_commit` re-sync
    # defect (livespec-n9f0).
    ".copier-answers.yml",
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
    # `.ai/agent-disciplines.md` seeds the agent-instruction `.ai/`
    # convention in every generated adopter repo (per
    # livespec/SPECIFICATION/contracts.md, the fleet agent-instruction
    # core contract). Pinning it ensures the scaffold is never silently
    # dropped on a template update.
    ".ai/agent-disciplines.md",
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


def _run_copier_copy(*, template_path: Path, target: Path) -> subprocess.CompletedProcess[str]:
    """Run `copier copy` against the template with the stock answers.

    The subprocess inherits the ambient environment unchanged: the
    canonical `check:` aggregate is stamped from the committed
    `canonical-slugs.yml` data file via a `{% include %}` (no copier
    Jinja extension, no PYTHONPATH injection), so this render path is
    identical to the consumer `copier update` flow.
    """
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


def _verify_justfile_parses(*, target: Path, log: structlog.stdlib.BoundLogger) -> bool:
    """Verify the generated `justfile` parses under `just`.

    `just` is the generated repo's sole task runner and parses the WHOLE
    justfile before running any recipe, so an unparseable justfile breaks every
    `just` command (`bootstrap`, `check`, the worktree-* recipes). The
    text-grep assertions elsewhere never invoke `just`, so this is the only
    gate that exercises the parse: `just --summary` parses and lists recipe
    names without running anything. Returns True on a clean parse, False (after
    emitting a diagnostic) on a parse error. `just` is always on PATH where
    this check runs — it is invoked via `just check-copier-template-smoke`.
    """
    justfile = target / "justfile"
    result = subprocess.run(
        ["just", "--justfile", str(justfile), "--working-directory", str(target), "--summary"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        log.error(
            "generated justfile does not parse under `just`",
            check_id="copier-template-smoke-justfile-parse-failed",
            returncode=result.returncode,
            stderr_tail=result.stderr[-2000:],
            hint="A multi-line recipe must be a shebang recipe; see the bootstrap recipe.",
        )
        return False
    return True


def _verify_generated_justfile(
    *, target: Path, log: structlog.stdlib.BoundLogger, repo_root: Path
) -> int | None:
    """Verify the generated justfile: it parses under `just`, then stamps every
    canonical check slug.

    Returns the verified slug count on success, or None if EITHER the justfile
    fails to parse OR the canonical-slug array drifts (each emits its own
    diagnostic). Folding both gates behind one return keeps main() within the
    return-statement lint budget; the parse gate runs FIRST because an
    unparseable justfile is the more fundamental failure.
    """
    if not _verify_justfile_parses(target=target, log=log):
        return None
    return _verify_canonical_slug_stamping(log=log, target=target, repo_root=repo_root)


def main() -> int:
    log = _configure_logger()
    repo_root = Path.cwd()
    template_path = repo_root / _TEMPLATE_PATH_REL
    if not (template_path / "copier.yml").is_file():
        log.error(
            "templates/orchestrator-plugin/copier.yml not found",
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
                hint="Check templates/orchestrator-plugin/ for the corresponding .jinja sources.",
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
        # The generated `justfile` MUST parse under `just` AND stamp every
        # canonical check slug. `_verify_generated_justfile` runs the parse gate
        # first (the text-grep assertions never invoke `just`, so it is the only
        # gate that exercises the parse — it caught the non-shebang bootstrap
        # recipe `just` rejected with "extra leading whitespace"), then the
        # canonical-slug assertion; it returns the verified slug count, or None
        # if EITHER fails. Combining them keeps main()'s return-statement count
        # within the lint budget (PLR0911).
        slugs_verified = _verify_generated_justfile(target=target, log=log, repo_root=repo_root)
        if slugs_verified is None:
            return 1
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
            "Run `just stamp-canonical-slugs` to regenerate "
            "templates/orchestrator-plugin/canonical-slugs.yml from the source of "
            "truth, and verify justfile.jinja includes + line-parses it."
        ),
    )
    return None


if __name__ == "__main__":
    raise SystemExit(main())
