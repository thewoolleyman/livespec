"""livespec.io: impure boundary wrappers + vendored-lib facades.

Every operation that touches the filesystem, the git working tree, or
the CLI surface lives here under `@impure_safe` so the railway can
flow through `IOResult`. Vendored libraries (`returns`,
`fastjsonschema`, `structlog`) reach the rest of the codebase only
through the typed facades below; `Any` is confined to this package
boundary.

Phase 2 placeholder. Concrete operations are added by later phases
as the supervisor and command modules need them.
"""

__all__: list[str] = []
