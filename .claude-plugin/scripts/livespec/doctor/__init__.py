"""livespec.doctor: static-phase doctor orchestrator + per-check modules.

Static phase runs as a single ROP chain in `run_static.main()`.
Per-check modules under `static/` each export a `run()` returning
`IOResult[Finding, E]` where E is a `LivespecError` subclass. The
LLM-driven doctor phase is skill-layer (no Python module here).
"""

__all__: list[str] = []
