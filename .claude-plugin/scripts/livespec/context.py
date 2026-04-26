"""Immutable context dataclasses (railway payload).

Phase 2 placeholder. The full set of context dataclasses —
`DoctorContext`, `SeedContext`, `ProposeChangeContext`,
`CritiqueContext`, `ReviseContext`, `PruneHistoryContext` — lands
when later phases need them as the `ctx` parameter on `run()` /
`main()` signatures. Each is
`@dataclass(frozen=True, kw_only=True, slots=True)` per the style
doc §"Context dataclasses".

The `livespec/context.py` location is reserved here so import paths
referenced by the style doc (e.g.,
`from livespec.context import DoctorContext`) resolve as soon as the
dataclasses are added.
"""

__all__: list[str] = []
