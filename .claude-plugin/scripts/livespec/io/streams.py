"""Standard stream write helpers."""

from __future__ import annotations

import sys
from typing import TextIO

__all__: list[str] = ["write_stderr", "write_stdout"]


def _write_stream(*, stream: TextIO, text: str) -> int:
    return stream.write(text)


def write_stdout(*, text: str) -> int:
    return _write_stream(stream=sys.stdout, text=text)


def write_stderr(*, text: str) -> int:
    return _write_stream(stream=sys.stderr, text=text)
