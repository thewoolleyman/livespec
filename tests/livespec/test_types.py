"""Tests for livespec.types — domain-primitive NewTypes.

Per `python-skill-script-style-requirements.md` §"Skill layout"
+ PROPOSAL.md §"`livespec/types.py`": the module exposes a
small set of `typing.NewType`-defined domain primitives that
the canonical-target `check-newtype-domain-primitives`
(per `dev-tooling/checks/newtype_domain_primitives.py`)
requires for specific field names in
`schemas/dataclasses/*.py`. NewType is structural — at
runtime each NewType is the underlying `str`, so isinstance
checks pass; pyright treats them as distinct types so
mistaking a `CheckId` for a `SpecRoot` is caught at type-
check time.
"""

from __future__ import annotations

from livespec.types import Author, CheckId, SpecRoot, TemplateName, TopicSlug

__all__: list[str] = []


def test_check_id_newtype_wraps_str() -> None:
    """`CheckId(s)` returns `s` and is a `str` instance at runtime."""
    cid = CheckId("doctor-frontmatter-spec-version")
    assert cid == "doctor-frontmatter-spec-version"
    assert isinstance(cid, str)


def test_spec_root_newtype_wraps_str() -> None:
    """`SpecRoot(s)` returns `s` and is a `str` instance at runtime."""
    sr = SpecRoot("SPECIFICATION")
    assert sr == "SPECIFICATION"
    assert isinstance(sr, str)


def test_author_newtype_wraps_str() -> None:
    """`Author(s)` returns `s` and is a `str` instance at runtime."""
    a = Author("claude-opus-4-7")
    assert a == "claude-opus-4-7"
    assert isinstance(a, str)


def test_template_name_newtype_wraps_str() -> None:
    """`TemplateName(s)` returns `s` and is a `str` instance at runtime."""
    tn = TemplateName("livespec")
    assert tn == "livespec"
    assert isinstance(tn, str)


def test_topic_slug_newtype_wraps_str() -> None:
    """`TopicSlug(s)` returns `s` and is a `str` instance at runtime."""
    ts = TopicSlug("switch-auth-middleware")
    assert ts == "switch-auth-middleware"
    assert isinstance(ts, str)
