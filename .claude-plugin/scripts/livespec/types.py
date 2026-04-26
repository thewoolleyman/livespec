"""Canonical NewType aliases for domain primitives (v012 L8).

Phase 2 placeholder. The full set of NewType aliases — `RunId`,
`SpecRoot`, `TopicSlug`, `CheckId`, `SchemaId`, `Author`,
`TemplateName`, `VersionTag`, plus any added during sub-command
authoring — lands when later phases need them at function-signature
boundaries. Until then this module exposes no public names; importers
that need a NewType must wait for the corresponding sub-command's
phase to land it.

The `livespec/types.py` location is reserved here so import paths
referenced by the style doc (e.g.,
`from livespec.types import Author, RunId, SpecRoot, TopicSlug`)
resolve as soon as the aliases are added.
"""

__all__: list[str] = []
