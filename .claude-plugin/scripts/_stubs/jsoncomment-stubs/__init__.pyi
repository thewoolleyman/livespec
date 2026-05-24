"""Type stubs for the vendored jsoncomment package.

The vendored copy already types `loads(text: str) -> Any`, so pyright
resolves the public surface cleanly. These stubs exist to (a) document
the surface livespec consumes (just `loads`), and (b) keep parity with
the fastjsonschema-stubs sibling under the same stubPath root.
"""

from typing import Any

__all__ = ["loads"]

def loads(text: str) -> Any: ...
