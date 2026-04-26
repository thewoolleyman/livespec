"""livespec.parse: pure parsers (Result-returning).

Each parser is a Phase-`@safe` (or hand-authored `Result`-returning)
function over an in-memory string; no I/O. Errors flow as
`Failure(<LivespecError>)` payloads on the railway.
"""

__all__: list[str] = []
