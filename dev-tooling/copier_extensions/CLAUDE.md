# dev-tooling/copier_extensions/

Jinja2 extensions consumed by copier at `copier copy` / `copier update`
time. Each `<name>.py` module declares a single `Extension` subclass
that mutates the copier-managed Jinja2 environment (registering
globals, filters, or tags) so `templates/impl-plugin/*.jinja` can
reference values that change over time without hand-editing the
template.

Conventions:

- Each module's docstring documents (a) the upstream source-of-truth
  it pulls values from, (b) the Jinja-side surface it exposes
  (global / filter / tag name), and (c) the contract reference that
  authorizes the extension (livespec-core SPECIFICATION pointer).
- The package lives under `dev-tooling/` (NOT under
  `.claude-plugin/scripts/livespec/`) because copier extensions are
  dev-tooling concerns — they participate in `copier copy`
  orchestration, not in the runtime plugin surface. The
  `check-no-inheritance` direct-parent allowlist (scoped to
  `.claude-plugin/scripts/livespec/**`) does not apply here, so
  `class X(Extension):` is the standard Jinja-loaded extension shape.
- Wiring path: `templates/impl-plugin/copier.yml` references each
  extension via its `module:Class` dotted form under
  `_jinja_extensions:`; the smoke check at
  `dev-tooling/checks/copier_template_smoke.py` injects
  `<repo-root>/dev-tooling` on the subprocess `PYTHONPATH` so the
  dotted path resolves under `uv run copier copy`.

Modules:

- `canonical_checks.py` — exposes `canonical_check_slugs` as a Jinja
  global by importing `livespec_dev_tooling.canonical_checks.
  canonical_check_slugs()`. Consumed by
  `templates/impl-plugin/justfile.jinja`'s `check:` recipe to stamp
  the wiring-completeness aggregate at copy time. Authority:
  livespec-core `SPECIFICATION/contracts.md` §"Shared code sync —
  livespec-dev-tooling".
