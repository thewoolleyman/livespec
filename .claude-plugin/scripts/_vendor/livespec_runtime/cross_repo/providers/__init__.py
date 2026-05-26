"""livespec_runtime.cross_repo.providers — external state provider modules.

Per livespec/SPECIFICATION/contracts.md v072 §"Cross-repo dependency
awareness": cross-repo state queries live behind provider modules so
the resolve-ref walker stays agnostic of the underlying transport.

At v0.2.0 the only provider is `github` (gh CLI subprocess dispatch).
Future providers (gitlab, gitea, etc.) land as sibling modules with
the same function-level surface.
"""

__all__: list[str] = []
