"""Read the canonical slug projection carried by the plugin bundle."""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = ["canonical_slugs_from_projection"]


_PROJECTION_PATH = Path(__file__).with_name("canonical-slugs.yml")


def canonical_slugs_from_projection() -> tuple[str, ...] | None:
    """Return the bundled canonical set, or None when its bytes are unusable.

    The plugin must evaluate doctor under bare Python, where dev-tooling is not a
    dependency. This deliberately line-parses the committed projection instead of
    importing its release-time source of truth. Any malformed non-comment line,
    duplicate slug, or unreadable file is an unavailable source rather than an
    empty canonical set, so the caller can fail closed.
    """
    try:
        text = _PROJECTION_PATH.read_text(encoding="utf-8")
    except OSError:
        return None
    slugs: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line == "" or line.startswith("#"):
            continue
        if not line.startswith("- check-"):
            return None
        slug = line.removeprefix("- ").strip()
        if slug == "" or slug in slugs:
            return None
        slugs.append(slug)
    return tuple(slugs) if slugs else None
