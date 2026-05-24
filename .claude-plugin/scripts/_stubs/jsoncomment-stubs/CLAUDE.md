# scripts/_stubs/jsoncomment-stubs/

Type stubs for the vendored `jsoncomment` package.

Public surface covered:

- `loads(text: str) -> Any`

Consumer: `livespec/parse/jsonc.py` calls `jsoncomment.loads(text)`
once. The vendored package's own `__init__.py` already types
`loads(text: str) -> Any`, but a sibling stubs directory is kept
here for consistency with the `fastjsonschema-stubs` neighbor and
to document the consumed surface in one place.
