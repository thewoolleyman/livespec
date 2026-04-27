# tests/livespec/parse/

Tests for the pure parsing layer at `livespec/parse/`. Both
`front_matter.py` and `jsonc.py` are pure modules — their tests
must include property-based tests (via Hypothesis) per
`check-pbt-coverage-pure-modules`.

Coverage requirements:

- `front_matter.py` — round-trip: `parse(serialize(x)) == x`
  for any well-formed front-matter dataclass; malformed-input
  paths each produce the documented `Failure(<LivespecError>)`.
- `jsonc.py` — round-trip via the vendored shim; comments are
  stripped; trailing commas tolerated; explicit JSON-spec
  violations produce typed failures.

Imports from `livespec.io` are forbidden (enforced by the
import-linter pure-layer contract).
