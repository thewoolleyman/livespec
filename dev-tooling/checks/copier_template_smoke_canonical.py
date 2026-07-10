"""Canonical-slug stamping checks for copier_template_smoke."""

from __future__ import annotations

import re
from pathlib import Path

import structlog

__all__: list[str] = ["_verify_canonical_slug_stamping"]

_TARGETS_LINE_RE = re.compile(r"^ {8}(check-[a-z0-9-]+)$", re.MULTILINE)


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
