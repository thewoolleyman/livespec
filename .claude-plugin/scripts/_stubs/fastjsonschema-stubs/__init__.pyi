"""Type stubs for the vendored fastjsonschema package.

The vendored copy under .claude-plugin/scripts/_vendor/fastjsonschema/
ships without type annotations, so pyright infers Unknown for the
`compile` return value and every downstream call site of the returned
validator. These stubs declare the minimal public surface livespec
actually consumes (compile + JsonSchemaValueException) with the
strongest precise types pyright can flow-check against.
"""

from collections.abc import Callable
from typing import Any

__all__ = ["JsonSchemaDefinitionException", "JsonSchemaValueException", "compile"]

def compile(
    definition: dict[str, Any],
    handlers: dict[str, Any] | None = ...,
    formats: dict[str, Any] | None = ...,
    use_default: bool = ...,
    use_formats: bool = ...,
    detailed_exceptions: bool = ...,
) -> Callable[[dict[str, Any]], dict[str, Any]]: ...

class JsonSchemaValueException(Exception):  # noqa: N818 — upstream library exception name; stubs MUST match.
    message: str
    value: Any
    name: str
    definition: dict[str, Any]
    rule: str

    def __init__(
        self,
        message: str,
        value: Any = ...,
        name: str = ...,
        definition: dict[str, Any] | None = ...,
        rule: str = ...,
    ) -> None: ...

class JsonSchemaDefinitionException(Exception):  # noqa: N818 — upstream library exception name; stubs MUST match.
    """Raised by `compile()` when the schema itself is invalid."""
