"""Interpret a resolved sibling aggregate source without I/O."""

from __future__ import annotations

from livespec.doctor.static._wiring_completeness_cross_repo_helpers import (
    compute_missing_slugs,
    interpret_justfile_text,
)

__all__: list[str] = ["interpret_check_source"]


def _inventory_slugs(*, inventory_text: str) -> tuple[str, ...]:
    """Apply the producer's `check-targets.txt` token rules exactly."""
    collected: list[str] = []
    for raw in inventory_text.splitlines():
        token = raw.split("#", 1)[0].strip()
        if token.startswith("check-"):
            collected.append(token)
    return tuple(collected)


def interpret_check_source(
    *,
    sibling_slug: str,
    source_kind: str,
    source_text: str | None,
    canonical_slugs: tuple[str, ...],
) -> list[tuple[str, str]]:
    """Map a resolved inventory or justfile to missing-slug pairs."""
    if source_kind != "inventory" or source_text is None:
        return interpret_justfile_text(
            sibling_slug=sibling_slug,
            justfile_text=source_text,
            canonical_slugs=canonical_slugs,
        )
    missing = compute_missing_slugs(
        canonical_slugs=canonical_slugs,
        wired_slugs=_inventory_slugs(inventory_text=source_text),
    )
    return [(sibling_slug, slug) for slug in missing]
