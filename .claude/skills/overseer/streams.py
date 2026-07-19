"""Process-output sinks for the overseer.

Every line the overseer writes to a real terminal goes through here.

Two reasons this module exists rather than bare ``print``:

* The project reserves stdout for documented contracts and bans ``print``
  mechanically (ruff ``T20``) — see ``SPECIFICATION/constraints.md``. Routing
  output through a named sink is the same one-hop indirection the product side
  uses in ``livespec/io/streams.py``.
* A named sink is substitutable. A test can point these at a buffer and assert
  on what the daemon actually reported; a bare ``print`` makes that awkward.

The daemon's TABLE render does not come through here — it writes to the
``Supervisor.out`` stream, which is injectable for exactly the same reason and
predates this module.

Stdlib-only, like every module in this folder.
"""

from __future__ import annotations

import sys
from typing import TextIO

__all__ = ["write_stderr", "write_stdout"]


def _write(*, stream: TextIO, text: str) -> None:
    _ = stream.write(text)


def write_stdout(*, text: str) -> None:
    """Write ``text`` to stdout verbatim. The caller supplies any newline."""
    _write(stream=sys.stdout, text=text)


def write_stderr(*, text: str) -> None:
    """Write ``text`` to stderr verbatim. The caller supplies any newline."""
    _write(stream=sys.stderr, text=text)
