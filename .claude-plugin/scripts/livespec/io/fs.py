"""livespec.io.fs — filesystem write primitives.

Pulled into existence under consumer pressure from
`livespec.commands.seed.main` at v032 TDD redo cycle 2: the seed
supervisor needs to materialize `.livespec.jsonc` at the project
root, and `Path.write_text` plus bare `open(...)` are eventually
banned outside `livespec/io/**` by `check-no-write-direct`
(Phase 4). A single `write_text` primitive satisfies that
architectural boundary today.

ROP wrapping (`@impure_safe`, `IOResult`) is deferred until a
second consumer or a failure-path test forces it — per Kent-Beck
smallest-thing-that-could-possibly-work.
"""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = ["write_text"]


def write_text(*, path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
