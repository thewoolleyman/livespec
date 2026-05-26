"""livespec-runtime — shared runtime library for livespec-governed projects.

This package hosts runtime code consumed by canonical livespec skills,
impl-plugin skills, doctor invariants, hooks, and CI workflows. The
initial subpackage is `livespec_runtime.cross_repo` (cross-repo
dependency resolution per livespec/SPECIFICATION/contracts.md
§"Cross-repo dependency awareness").

This is NOT enforcement-suite code — those live in livespec-dev-tooling.
"""

__all__: list[str] = []
