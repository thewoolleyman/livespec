"""Canonical NewType aliases for domain primitives (v012 L8).

`NewType` creates a zero-runtime-cost type alias that pyright treats
as distinct from its underlying primitive: passing a `RunId` where a
`CheckId` is expected becomes a type error. This eliminates the
"right shape, wrong meaning" bug class for raw-string and raw-`Path`
domain identifiers across `livespec/**`.

Field-name → NewType mapping is canonical and enforced by
`check-newtype-domain-primitives` (AST walk over
`livespec/schemas/dataclasses/*.py` and `livespec/**.py` function
signatures). The mapping below mirrors the table in
python-skill-script-style-requirements.md §"Domain primitives via
`NewType`":

| Field name | NewType | Underlying |
|---|---|---|
| `check_id` | `CheckId` | `str` |
| `run_id` | `RunId` | `str` |
| `topic` | `TopicSlug` | `str` |
| `spec_root` | `SpecRoot` | `Path` |
| `schema_id` | `SchemaId` | `str` |
| `template` | `TemplateName` | `str` |
| `author` / `author_human` / `author_llm` | `Author` | `str` |
| `version_tag` | `VersionTag` | `str` |

The `template_root: Path` field in `DoctorContext` is the resolved
template directory and uses raw `Path`, NOT `TemplateName` — the
mapping is field-name keyed, and `template_root` does not match
`template`.

v013 C4: the module name `livespec.types` intentionally echoes the
stdlib `types` module name. Absolute-import discipline (TID rule
`ban-relative-imports = "all"`) precludes any import-resolution
conflict between `from livespec.types import Author` and `from types
import ModuleType`.
"""

from pathlib import Path
from typing import Any, NewType, Protocol, TypeVar

from returns.result import Result

from livespec.errors import ValidationError

__all__: list[str] = [
    "Author",
    "CheckId",
    "RunId",
    "SchemaId",
    "SpecRoot",
    "TemplateName",
    "TopicSlug",
    "TypedValidator",
    "VersionTag",
    "rop_pipeline",
]


def rop_pipeline(cls: type) -> type:
    """Marker decorator for Railway-Oriented-Programming pipeline classes.

    A class decorated with `@rop_pipeline` MUST carry exactly ONE
    public method (the entry point); every other method MUST be
    `_`-prefixed (private to the class). Dunder methods (`__init__`,
    `__call__`, etc.) are not counted toward the public-method
    quota — they are Python-mandated structural surfaces.

    The decorator is a runtime no-op (returns `cls` unchanged); AST
    enforcement lives in `dev-tooling/checks/rop_pipeline_shape.py`,
    which walks every `@rop_pipeline`-decorated `ClassDef` and
    asserts the one-public-method invariant.

    Helper classes and helper modules (anything NOT carrying this
    decorator) are exempt from the rule and may export multiple
    public names. The pattern follows the established Command /
    Use Case Interactor / Trailblazer Operation lineage:

    - Each pipeline encapsulates one cohesive railway chain.
    - The single public method is the entry point.
    - Internal steps are private methods, structurally bounded by
      the class body.

    Note on the `cls` parameter: class decorators in Python receive
    the decorated class positionally — Python's decorator protocol
    passes it as the first argument. Naming the parameter `cls`
    aligns with the `@classmethod` convention and is recognized by
    `check-keyword-only-args` (which skips a leading `self` or
    `cls` parameter without requiring a `*` separator).
    """
    return cls


_T_co = TypeVar("_T_co", covariant=True)


class TypedValidator(Protocol[_T_co]):
    """Generic Protocol for keyword-only validators.

    A `TypedValidator[T]` is a callable that takes a JSON object as
    `payload` (kw-only) and returns
    `Result[T, ValidationError]`. This Protocol expresses the
    keyword-only call shape that `Callable[[X], Y]` cannot — pyright
    in strict mode rejects assigning a kw-only function to a
    positional `Callable` annotation, so the validator factories in
    `livespec/io/fastjsonschema_facade.py` and
    `livespec/validate/<name>.py` use this Protocol as their return
    type and `fast_validator` parameter type.

    The kw-only call shape (`validator(payload=...)`) is required by
    the `keyword-only-args` enforcement: every livespec-defined
    `def` must place a `*` separator as its first parameter.
    Validator closures returned from `make_validator(...)` factories
    are not ROP-DSL callbacks, so they are NOT covered by the
    ROP-DSL exemption — they must be kw-only at def-site, which
    cascades into Protocol-typed annotations here.
    """

    def __call__(
        self,
        *,
        payload: dict[str, Any],
    ) -> Result[_T_co, ValidationError]: ...


CheckId = NewType("CheckId", str)
"""doctor-static check slug, e.g. `CheckId("doctor-out-of-band-edits")`."""

RunId = NewType("RunId", str)
"""Per-invocation UUID bound once at process start by `livespec/__init__.py`."""

TopicSlug = NewType("TopicSlug", str)
"""Proposed-change topic identifier (kebab-case slug). The field name is
`topic`; the NewType name uses the `Slug` suffix to disambiguate from
the literal word `topic`."""

SpecRoot = NewType("SpecRoot", Path)
"""Resolved spec-root directory path. The supervisor verifies the path
exists and is a directory before constructing this type."""

SchemaId = NewType("SchemaId", str)
"""JSON Schema `$id` value used as the cache key in
`livespec/io/fastjsonschema_facade.py`."""

TemplateName = NewType("TemplateName", str)
"""The user's `.livespec.jsonc` `template` field — either a built-in
template name (`livespec`, `minimal`) or a path-as-string. The NewType
name uses the `Name` suffix to disambiguate from the
`template_root: Path` field, which carries the resolved directory."""

Author = NewType("Author", str)
"""Author identifier (per K7 rename). The same NewType applies to
the `author`, `author_human`, and `author_llm` field names."""

VersionTag = NewType("VersionTag", str)
"""`vNNN` zero-padded version identifier, e.g. `VersionTag("v001")`."""
