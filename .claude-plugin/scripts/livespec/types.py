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
from typing import NewType

__all__: list[str] = [
    "Author",
    "CheckId",
    "RunId",
    "SchemaId",
    "SpecRoot",
    "TemplateName",
    "TopicSlug",
    "VersionTag",
]


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
