# scripts/_stubs/

Type stubs for vendored libraries that ship without type
annotations. Pyright resolves these in preference to the vendored
`.py` files when `[tool.pyright].stubPath` points here.

Each subdirectory follows the `<package>-stubs/` convention from
typeshed: `<package>-stubs/__init__.pyi` declares the package's
public API as Python type stubs (PEP 561). Internal modules
declare additional `<module>.pyi` files inside the same
`<package>-stubs/` tree.

Scope rules:

- Stubs cover ONLY the public surface livespec consumes. Unused
  vendored APIs are intentionally omitted; pyright reports
  attribute access on missing names as a diagnostic, which is
  the desired signal.
- Stubs are excluded from pyright's `include` tree to avoid
  recursive self-typing; they are picked up via `stubPath`.
- Vendored library files under `_vendor/` remain untouched
  (read-only). When upstream ships type annotations later, the
  corresponding stub directory under `_stubs/` is removed and
  the vendored copy is refreshed via the standard vendor-manifest
  path.
