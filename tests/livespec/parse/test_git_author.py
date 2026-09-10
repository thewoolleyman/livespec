"""Tests for livespec.parse.git_author.

The module holds the effective-Git-author policy rule shared by
the doctor's publication-time verifier and the revision-metadata
author capture, per `SPECIFICATION/contracts.md` (the `git_author`
declaration) and `SPECIFICATION/non-functional-requirements.md`
(the operator Git authorship rule).

The load-bearing property under test is FAIL-CLOSED
classification: an identity that is neither the declared operator
pair, nor an exactly-declared mechanical pair, nor a self-declared
preserved third-party author, classifies as `conflict`. Everything
else here — identity parsing across both git ident shapes, trailer
reading — exists to feed that decision correctly.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.parse.git_author import (
    PRESERVED_AUTHOR_TRAILER,
    GitIdentity,
    classify_identity,
    format_identity,
    parse_author_ident,
    parse_preserved_author,
)
from returns.result import Failure, Success

__all__: list[str] = []


_OPERATOR = GitIdentity(name="Chad Woolley", email="thewoolleyman@gmail.com")
_BOT = GitIdentity(
    name="livespec-pr-bot[bot]",
    email="livespec-pr-bot[bot]@users.noreply.github.com",
)
_THIRD_PARTY = GitIdentity(name="Outside Contributor", email="outside@example.com")


def test_unknown_identity_classifies_as_conflict() -> None:
    """An identity the declaration does not cover fails closed.

    The sandbox-fallback identity that motivated the operator-author
    contract is exactly this shape: a plausible-looking author that
    no declaration names. It MUST NOT pass merely because it is
    unrecognized.
    """
    verdict = classify_identity(
        identity=GitIdentity(name="fabro", email="fabro@livespec.invalid"),
        operator=_OPERATOR,
        mechanical=(_BOT,),
        preserved=None,
    )
    assert verdict.classification == "conflict"


def test_operator_identity_classifies_as_operator() -> None:
    """The exact declared operator pair is the canonical passing case."""
    verdict = classify_identity(
        identity=_OPERATOR,
        operator=_OPERATOR,
        mechanical=(_BOT,),
        preserved=None,
    )
    assert verdict.classification == "operator"
    assert verdict.identity == _OPERATOR


def test_declared_mechanical_identity_classifies_as_mechanical() -> None:
    """A declared mechanical bot pair remains supported."""
    verdict = classify_identity(
        identity=_BOT,
        operator=_OPERATOR,
        mechanical=(_BOT,),
        preserved=None,
    )
    assert verdict.classification == "mechanical"


def test_undeclared_bot_identity_classifies_as_conflict() -> None:
    """A bot-shaped identity absent from the declaration still fails closed.

    Mechanical authorship is narrow by contract: the permission
    comes from the exact configured pair, never from the identity
    looking automated.
    """
    verdict = classify_identity(
        identity=GitIdentity(
            name="some-other-bot[bot]",
            email="some-other-bot[bot]@users.noreply.github.com",
        ),
        operator=_OPERATOR,
        mechanical=(_BOT,),
        preserved=None,
    )
    assert verdict.classification == "conflict"


def test_self_declared_preserved_third_party_classifies_as_third_party() -> None:
    """A genuine third-party import that declares itself is preserved."""
    verdict = classify_identity(
        identity=_THIRD_PARTY,
        operator=_OPERATOR,
        mechanical=(_BOT,),
        preserved=_THIRD_PARTY,
    )
    assert verdict.classification == "third_party"


def test_preserved_declaration_naming_another_author_does_not_excuse_this_one() -> None:
    """A preservation declaration only covers the identity it names.

    Otherwise one declared import would launder every other author
    on the same commit range.
    """
    verdict = classify_identity(
        identity=GitIdentity(name="Someone Else", email="else@example.com"),
        operator=_OPERATOR,
        mechanical=(_BOT,),
        preserved=_THIRD_PARTY,
    )
    assert verdict.classification == "conflict"


def test_matching_email_with_different_name_is_a_conflict() -> None:
    """The operator match is byte-for-byte on BOTH fields.

    The audited history's largest non-canonical population differed
    from the canonical pair only in the name, so a
    right-email/wrong-name commit must not read as canonical.
    """
    verdict = classify_identity(
        identity=GitIdentity(name="thewoolleyman", email="thewoolleyman@gmail.com"),
        operator=_OPERATOR,
        mechanical=(),
        preserved=None,
    )
    assert verdict.classification == "conflict"


def test_parse_author_ident_reads_the_git_var_ident_shape() -> None:
    """`git var GIT_AUTHOR_IDENT` appends a timestamp and timezone offset."""
    result = parse_author_ident(raw="Chad Woolley <thewoolleyman@gmail.com> 1789074913 +0000")
    assert result == Success(_OPERATOR)


def test_parse_author_ident_reads_the_bare_pair_shape() -> None:
    """`git log`'s `%an <%ae>` rendering carries no timestamp suffix."""
    result = parse_author_ident(raw="Chad Woolley <thewoolleyman@gmail.com>")
    assert result == Success(_OPERATOR)


def test_parse_author_ident_rejects_an_unparseable_line() -> None:
    """A shape the reader cannot understand MUST NOT resolve to an identity.

    Pure-layer parsers do not raise; the rejection flows as
    `Failure(ValidationError)` on the railway.
    """
    result = parse_author_ident(raw="no angle brackets here")
    match result:
        case Failure(ValidationError()):
            pass
        case _:
            raise AssertionError(f"expected Failure(ValidationError), got {result!r}")


def test_parse_preserved_author_reads_the_trailer() -> None:
    """The trailer declares which author a third-party import preserves."""
    message = (
        "fix: upstream patch\n"
        "\n"
        f"{PRESERVED_AUTHOR_TRAILER}: Outside Contributor <outside@example.com>\n"
    )
    assert parse_preserved_author(message=message) == _THIRD_PARTY


def test_parse_preserved_author_returns_none_without_the_trailer() -> None:
    """An ordinary commit message declares nothing."""
    assert parse_preserved_author(message="feat: ordinary work\n") is None


def test_parse_preserved_author_returns_none_for_an_unparseable_value() -> None:
    """An unusable declaration is no declaration.

    The caller's next step compares the declaration against the
    commit's real author, and a value it cannot parse can never
    match one — collapsing it to None keeps that path single.
    """
    message = f"fix: thing\n\n{PRESERVED_AUTHOR_TRAILER}: not an identity\n"
    assert parse_preserved_author(message=message) is None


def test_format_identity_renders_the_conventional_pair() -> None:
    """Rendering is the inverse of the bare-pair parse."""
    assert format_identity(identity=_OPERATOR) == "Chad Woolley <thewoolleyman@gmail.com>"


@settings(deadline=None)  # type: ignore[misc]
@given(
    name=st.text(
        alphabet=st.characters(blacklist_characters="<>\n\r"),
        min_size=1,
        max_size=20,
    ).filter(lambda value: value == value.strip()),
    email=st.text(
        alphabet=st.characters(blacklist_characters="<>\n\r"),
        min_size=1,
        max_size=20,
    ),
)
def test_format_then_parse_round_trips_any_identity(*, name: str, email: str) -> None:
    """For any bracket-free pair, rendering then parsing returns the original.

    The two directions are used on opposite sides of the guard —
    identities are parsed out of git and rendered back into
    diagnostics and revision metadata — so a shape that survives one
    direction but not the other would make a correct commit report
    as a conflict. Hypothesis explores display names containing
    spaces, punctuation, and non-ASCII text, which real author names
    do carry.
    """
    identity = GitIdentity(name=name, email=email)
    assert parse_author_ident(raw=format_identity(identity=identity)) == Success(identity)
