# scripts/_stubs/livespec_dev_tooling-stubs/

Type stubs for the installed `livespec_dev_tooling` package.

Upstream (livespec-dev-tooling) does not ship a `py.typed` marker
yet, so pyright treats every import as untyped (`Unknown`) under
strict-mode `reportMissingTypeStubs`. These stubs declare the
minimal public surface livespec consumes (today: the single
`canonical_check_slugs() -> tuple[str, ...]` function from
`livespec_dev_tooling.canonical_checks`) so the type checker has
a typed shape to flow against.

Scope rules (mirrors the sibling `fastjsonschema-stubs/` carve-out):

- Stubs cover ONLY the public surface livespec consumes. Other
  modules under `livespec_dev_tooling/` are consumed exclusively
  via `python -m` subprocess invocations and need no stubs.
- When upstream livespec-dev-tooling ships its own `py.typed`
  marker in a future release, this stub package should be removed
  and the import sites left untouched.

Consumers:

- `dev-tooling/copier_extensions/canonical_checks.py` (the copier
  Jinja extension that stamps the canonical aggregate at
  `copier copy` time).
- `dev-tooling/checks/copier_template_smoke.py` (the smoke check
  that verifies the stamped aggregate matches the source-of-truth
  list).
- `.claude-plugin/scripts/livespec/doctor/static/wiring_completeness_cross_repo.py`
  (the cross-repo backstop doctor invariant that walks every
  registered sibling's justfile aggregate and fires fail on any
  sibling missing any canonical slug).
