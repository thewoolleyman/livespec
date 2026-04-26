"""jsoncomment shim per v026 D1.

Faithfully replicates jsoncomment 0.4.2's `//` line-comment and `/* */`
block-comment stripping semantics, then delegates to stdlib `json.loads`
for actual JSON parsing. Multi-line strings and trailing-commas support
are NOT IMPLEMENTED (livespec doesn't need them; widen one-line at a time
if `livespec/parse/jsonc.py` grows that requirement).

Derivative work of jsoncomment 0.4.2 (Gaspare Iengo, MIT-licensed). The
canonical upstream (`bitbucket.org/Dando_Real_ITA/json-comment`) was
sunset by Atlassian and no live git mirror exists; the PyPI sdist
(`https://pypi.org/project/jsoncomment/`) is the only surviving
source-of-record. See LICENSE next to this file for the verbatim MIT
text with attribution.
"""
from __future__ import annotations

import json
from typing import Any

__all__ = ["JsonComment", "loads"]


def _strip_comments(text: str) -> str:
    """Strip `//` line comments and `/* */` block comments. Respect string
    literals (don't strip comment markers that appear inside quoted strings).
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            out.append(ch)
            i += 1
            while i < n:
                ch2 = text[i]
                out.append(ch2)
                i += 1
                if ch2 == "\\" and i < n:
                    out.append(text[i])
                    i += 1
                elif ch2 == '"':
                    break
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def loads(text: str) -> Any:
    """Parse a JSONC string. Strips `//` and `/* */` comments, then
    delegates to stdlib `json.loads`.
    """
    return json.loads(_strip_comments(text))


class JsonComment:
    """jsoncomment 0.4.2-compatible API surface (minimal subset).

    Only `loads()` is implemented. Multi-line strings and trailing-commas
    options from the upstream API are not supported in this shim.
    """

    def loads(self, text: str) -> Any:
        return loads(text)
