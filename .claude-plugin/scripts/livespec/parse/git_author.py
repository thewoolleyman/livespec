"""Pure effective-Git-author policy rule.

Per `SPECIFICATION/contracts.md` (the optional `git_author`
declaration on `.livespec.jsonc`) and
`SPECIFICATION/non-functional-requirements.md` (the operator Git
authorship rule): an opted-in project declares exactly one operator
identity plus zero or more mechanical-job identities, and every
commit it introduces MUST carry the operator pair byte-for-byte
unless the commit is exclusively mechanical output authored by an
exact declared mechanical pair, or a genuine third-party import
that DECLARES itself preserved.

This module holds the rule and nothing else — no I/O, no git
invocation. It parses the `Name <email>` identity form, reads the
`Livespec-Preserved-Author` trailer that declares a preserved
third-party import, and classifies one identity against one
declared policy. Both enforcement surfaces classify through here:
the doctor check that inspects newly-introduced commits, and the
revision-metadata author capture. Sharing this one rule is what
makes the two unable to drift apart — the failure mode the
`git_author` declaration exists to close is precisely a metadata
surface recording the configured identity while git writes a
different one.

The identity Git will ACTUALLY write is supplied by the io/ layer
(`git var GIT_AUTHOR_IDENT`), which already folds in `GIT_AUTHOR_*`
environment overrides, repository and worktree configuration, and
`user.useConfigOnly`. Reading `git config user.email` alone cannot
see those overrides, which is why nothing here accepts a raw config
value as an effective identity.

The fail-closed direction is deliberate: an identity that matches
neither the operator pair, nor a declared mechanical pair, nor a
self-declared preserved author classifies as `conflict`. There is
no "unknown but probably fine" outcome, because the classification
of an unrecognized author is exactly the question the declaration
answers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from returns.result import Failure, Result, Success

from livespec.errors import ValidationError

__all__: list[str] = [
    "PRESERVED_AUTHOR_TRAILER",
    "AuthorVerdict",
    "GitIdentity",
    "classify_identity",
    "format_identity",
    "parse_author_ident",
    "parse_preserved_author",
]


@dataclass(frozen=True, kw_only=True, slots=True)
class GitIdentity:
    """One exact Git author pair.

    Equality is byte-for-byte on both fields, which is the
    comparison the contract specifies: a declared operator pair
    matches only an identical name AND an identical email, so a
    right-email/wrong-name commit is a conflict rather than a
    near-miss.
    """

    name: str
    email: str


AuthorClassification = Literal["operator", "mechanical", "third_party", "conflict"]


@dataclass(frozen=True, kw_only=True, slots=True)
class AuthorVerdict:
    """The classification of one identity against one declared policy."""

    identity: GitIdentity
    classification: AuthorClassification


# The commit trailer by which a genuine third-party import declares
# itself preserved. A trailer is the only per-commit declaration
# channel a verifier can read, and the contract requires the
# classification to be "available to the verification surface" —
# so preservation is stated ON the commit rather than inferred from
# the author being unfamiliar. The trailer's value MUST repeat the
# commit's own author pair, so declaring preservation is an explicit
# statement about a specific identity and never a blanket waiver.
PRESERVED_AUTHOR_TRAILER: str = "Livespec-Preserved-Author"

# `Name <email>` optionally followed by git's ` <unix-seconds> <tz>`
# suffix, which `git var GIT_AUTHOR_IDENT` appends and `git log`'s
# `%an`/`%ae` do not. Accepting both shapes lets the pending-identity
# reader and the committed-identity reader share one parser. The name
# group is non-greedy so an email-like fragment inside a display name
# cannot swallow the real address.
_IDENT_PATTERN = re.compile(
    r"^(?P<name>.*?) <(?P<email>[^<>]*)>(?: \d+ [+-]\d{4})?$",
)

_TRAILER_PATTERN = re.compile(
    rf"^{PRESERVED_AUTHOR_TRAILER}:[ \t]*(?P<value>\S.*?)[ \t]*$",
    re.MULTILINE,
)


def format_identity(*, identity: GitIdentity) -> str:
    """Render an identity in the conventional `Name <email>` form."""
    return f"{identity.name} <{identity.email}>"


def parse_author_ident(*, raw: str) -> Result[GitIdentity, ValidationError]:
    """Parse one `Name <email>` line into a GitIdentity.

    Accepts both the bare pair and git's ident form with a trailing
    timestamp and timezone offset. Returns Failure(ValidationError)
    on any other shape — including an empty string and a name with
    no angle-bracketed address — because a shape this reader cannot
    understand MUST NOT resolve to an identity it then compares.
    """
    match = _IDENT_PATTERN.match(raw.strip())
    if match is None:
        return Failure(
            ValidationError(f"git_author: unparseable author identity {raw!r}"),
        )
    return Success(GitIdentity(name=match["name"], email=match["email"]))


def parse_preserved_author(*, message: str) -> GitIdentity | None:
    """Read the preserved-third-party-author declaration from a commit message.

    Returns the declared identity, or None when the trailer is
    absent or its value is not a parseable identity. An unparseable
    value yields None rather than an error: the caller's next step
    is to compare the declaration against the commit's real author,
    and "no usable declaration" and "declaration that cannot be
    compared" both mean the commit is undeclared.
    """
    match = _TRAILER_PATTERN.search(message)
    if match is None:
        return None
    return parse_author_ident(raw=match["value"]).value_or(None)


def classify_identity(
    *,
    identity: GitIdentity,
    operator: GitIdentity,
    mechanical: tuple[GitIdentity, ...],
    preserved: GitIdentity | None,
) -> AuthorVerdict:
    """Classify `identity` against the declared policy.

    `operator` is the declared operator pair; `mechanical` is the
    declared set of exclusively-mechanical job pairs; `preserved`
    is the identity the commit itself declares as a preserved
    third-party author (None when it declares none).

    Order matters only for reporting: the operator pair is checked
    first so a policy that (incorrectly) also lists the operator as
    mechanical still reports operator-authored work as such.

    A preserved declaration counts ONLY when it names the very
    identity being classified — a commit cannot declare some OTHER
    author preserved and thereby excuse its own.
    """
    if identity == operator:
        return AuthorVerdict(identity=identity, classification="operator")
    if identity in mechanical:
        return AuthorVerdict(identity=identity, classification="mechanical")
    if preserved == identity:
        return AuthorVerdict(identity=identity, classification="third_party")
    return AuthorVerdict(identity=identity, classification="conflict")
