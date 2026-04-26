"""Git read-only operations (`@impure_safe`).

Phase 2 placeholder. Real wrappers over `git rev-parse`,
`git status --porcelain`, `git log`, etc. land at later phases as
the doctor checks need them. All are read-only; livespec never
mutates the git working tree directly.
"""

__all__: list[str] = []
