"""copier_extensions — Jinja2 extensions exposed to copier at copy-time.

Per `SPECIFICATION/contracts.md` §"Shared code sync —
livespec-dev-tooling", `livespec/templates/impl-plugin/justfile.jinja`
MUST stamp the full canonical aggregate at `copier copy` time so every
newly-generated `livespec-impl-*` sibling inherits the
wiring-completeness state from inception. Derivation MUST come from
`livespec_dev_tooling.canonical_checks` at copy time, NOT from a
hand-maintained list in the template.

Modules in this package implement Jinja2 `Extension` subclasses that
copier loads via the `_jinja_extensions` key in
`templates/impl-plugin/copier.yml`. Each module's docstring documents
its purpose, the globals/filters it exposes, and the upstream source-
of-truth it derives values from.

This package lives under `dev-tooling/` rather than `.claude-plugin/
scripts/livespec/` because copier extensions are dev-tooling concerns
(they participate in `copier copy` orchestration, not in the
runtime plugin surface). The smoke test injects `dev-tooling/` onto
the subprocess's PYTHONPATH so the dotted-path `copier_extensions.
canonical_checks:CanonicalChecksExtension` resolves under
`uv run copier copy`.
"""

__all__: list[str] = []
