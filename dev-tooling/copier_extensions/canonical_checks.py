"""canonical_checks — copier Jinja extension exposing the canonical check-slug set.

Per `SPECIFICATION/contracts.md` §"Shared code sync —
livespec-dev-tooling", `livespec/templates/impl-plugin/justfile.jinja`
MUST stamp the full canonical aggregate at `copier copy` time so every
newly-generated `livespec-impl-*` sibling inherits the wiring-
completeness state from inception. The slug list MUST come from
`livespec_dev_tooling.canonical_checks` (the single source of truth
populated by `livespec_dev_tooling/checks/*.py`), NOT a hand-maintained
template list.

This Jinja2 `Extension` subclass calls
`livespec_dev_tooling.canonical_checks.canonical_check_slugs()` once
at copier-environment-construction time and exposes the resulting
tuple as the `canonical_check_slugs` Jinja global. Templates can
iterate it directly:

    targets=(
    {% for slug in canonical_check_slugs %}
        {{ slug }}
    {% endfor %}
    )

The slug tuple is alphabetically sorted at the source (per
`livespec_dev_tooling.canonical_checks._discover_slugs`), so consumers
get deterministic ordering without re-sorting in the template.

Output discipline: this module emits nothing to stdout or stderr —
copier consumes the Jinja global directly. Import-time failures
(e.g., `livespec_dev_tooling.canonical_checks` not installed) raise
`ImportError` at copier-environment-construction time, surfacing
through copier's `ExtensionNotFoundError` path.

Class inheritance: `jinja2.ext.Extension` is the documented Jinja2
extension base class; `class X(Extension):` is the only supported
shape for Jinja-loaded extensions. This module lives under
`dev-tooling/` (NOT under `.claude-plugin/scripts/livespec/`) so the
`check-no-inheritance` direct-parent allowlist (which scopes only
`.claude-plugin/scripts/livespec/**`) does not apply here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from jinja2.ext import Extension
from livespec_dev_tooling.canonical_checks import canonical_check_slugs

if TYPE_CHECKING:
    from jinja2 import Environment

__all__: list[str] = ["CanonicalChecksExtension"]


class CanonicalChecksExtension(Extension):
    """Expose `canonical_check_slugs` as a Jinja global for copier templates.

    Copier's `_jinja_extensions:` key references this class by dotted
    path. At copier-environment construction, Jinja2 instantiates
    `CanonicalChecksExtension(environment)`, which mutates
    `environment.globals` to add the `canonical_check_slugs` key
    bound to the alphabetically-sorted slug tuple discovered by
    `livespec_dev_tooling.canonical_checks.canonical_check_slugs()`.
    """

    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        # Jinja2's bundled stubs over-constrain the `globals` mapping
        # value type to a callable/class union; the runtime accepts
        # any value and surfaces it as a template global. The `tuple`
        # we assign here is the canonical-slug aggregate that
        # `justfile.jinja` iterates via `{% for slug in
        # canonical_check_slugs %}`. The narrow ignore is the
        # documented pragma for this kind of upstream-stub mismatch.
        environment.globals["canonical_check_slugs"] = canonical_check_slugs()  # pyright: ignore[reportArgumentType]
