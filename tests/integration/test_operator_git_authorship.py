"""Integration-tier coverage for `SPECIFICATION/scenarios.md`.

Covers the H2 section "Operator-owned Git work retains the
declared author" end-to-end: a real git repository, a real
`.livespec.jsonc` validated by the shipped validator against the
committed schema, real commits produced through the real override
paths, and the shipped `git-author-policy` Verifier reading the
resulting objects.

One test per scenario in that section, plus the Red→Green replay
leg the scenario's first case names explicitly:

- Interactive, replay, and agent-produced work use the operator
  pair, with agent attribution confined to a trailer.
- The Red commit and the amended Green commit carry the SAME
  validated author.
- A conflicting environment value, an explicit author, and a
  malformed declaration each fail closed with a diagnostic that
  identifies the offending pair or the offending key.
- Mechanical authorship is narrow: an exactly-declared pair is
  allowed, a bot-shaped undeclared pair is not.
- A genuine third-party import that declares itself preserved
  keeps its original author.
- The publication scan reports the exact offending commit and
  author pair, and states its own scanned count so an empty
  range never reads as an unqualified endorsement.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import git_author_policy
from livespec.io import git as io_git
from livespec.schemas.dataclasses.finding import Finding
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []

pytestmark = pytest.mark.integration


_OPERATOR_NAME = "Chad Woolley"
_OPERATOR_EMAIL = "thewoolleyman@gmail.com"
_OPERATOR_PAIR = f"{_OPERATOR_NAME} <{_OPERATOR_EMAIL}>"
_BOT_NAME = "thewoolleyman-factory-bot[bot]"
_BOT_EMAIL = "thewoolleyman-factory-bot[bot]@users.noreply.github.com"
_AGENT_TRAILER = "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"


def _git(
    *,
    cwd: Path,
    args: list[str],
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one git command in `cwd`, failing the test on a non-zero exit."""
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def _author_env(*, name: str, email: str) -> dict[str, str]:
    """A child environment whose `GIT_AUTHOR_*` overrides the repo config."""
    env = dict(os.environ)
    env["GIT_AUTHOR_NAME"] = name
    env["GIT_AUTHOR_EMAIL"] = email
    return env


def _commit(
    *,
    root: Path,
    filename: str,
    message: str,
    author: str | None = None,
    env: dict[str, str] | None = None,
) -> None:
    """Write, stage, and commit one file, optionally overriding the author."""
    _ = (root / filename).write_text(f"{filename}\n", encoding="utf-8")
    _ = _git(cwd=root, args=["add", filename])
    args = ["commit", "--quiet", "-m", message]
    if author is not None:
        args.append(f"--author={author}")
    _ = _git(cwd=root, args=args, env=env)


def _head_author(*, root: Path) -> str:
    """Return HEAD's author as the conventional `Name <email>` pair."""
    return _git(cwd=root, args=["log", "-1", "--format=%an <%ae>"]).stdout.strip()


def _head_sha(*, root: Path) -> str:
    """Return HEAD's full object id."""
    return _git(cwd=root, args=["rev-parse", "HEAD"]).stdout.strip()


def _declaration() -> dict[str, object]:
    """The canonical fleet declaration plus this repo's release-bot pair."""
    return {
        "operator_name": _OPERATOR_NAME,
        "operator_email": _OPERATOR_EMAIL,
        "mechanical_authors": [{"name": _BOT_NAME, "email": _BOT_EMAIL}],
    }


def _governed_repo(*, root: Path, git_author: dict[str, object] | None) -> None:
    """Build an opted-in repository whose `origin/master` is pinned at its base commit.

    The base commit stands in for already-published history, so the
    scanned range holds exactly what a push would introduce — which
    is what makes the later assertions about "newly introduced"
    commits mean what they say.
    """
    _ = _git(cwd=root, args=["init", "--quiet"])
    _ = _git(cwd=root, args=["config", "--local", "user.name", _OPERATOR_NAME])
    _ = _git(cwd=root, args=["config", "--local", "user.email", _OPERATOR_EMAIL])
    _ = _git(cwd=root, args=["config", "--local", "user.useConfigOnly", "true"])
    config: dict[str, object] = {"template": "livespec", "spec_root": "SPECIFICATION"}
    if git_author is not None:
        config["git_author"] = git_author
    _ = (root / ".livespec.jsonc").write_text(json.dumps(config), encoding="utf-8")
    _commit(root=root, filename="base.txt", message="chore: base")
    _ = _git(cwd=root, args=["remote", "add", "origin", str(root)])
    _ = _git(cwd=root, args=["update-ref", "refs/remotes/origin/master", "HEAD"])
    _ = _git(
        cwd=root,
        args=["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"],
    )


def _verify(*, root: Path) -> Finding:
    """Run the shipped publication-time Verifier against `root`."""
    ctx = DoctorContext(project_root=root, spec_root=root / "SPECIFICATION")
    result = unsafe_perform_io(git_author_policy.run(ctx=ctx))
    match result:
        case Success(finding):
            return finding
        case _:
            raise AssertionError(f"expected IOSuccess(<Finding>), got {result!r}")


def test_interactive_replay_and_agent_work_all_carry_the_operator_pair(
    *,
    tmp_path: Path,
) -> None:
    """Every operator-owned commit ends with the declared pair as its author.

    Three shapes in one range — an ordinary edit, an amended
    commit, and an agent-produced commit carrying a
    `Co-Authored-By` trailer — because the contract's claim is that
    agent identity belongs in a trailer while the AUTHOR stays the
    operator, not that agent work is exempt.
    """
    _governed_repo(root=tmp_path, git_author=_declaration())
    _commit(root=tmp_path, filename="interactive.txt", message="feat: interactive edit")
    _commit(root=tmp_path, filename="amended.txt", message="feat: work to amend")
    _ = (tmp_path / "amended.txt").write_text("amended twice\n", encoding="utf-8")
    _ = _git(cwd=tmp_path, args=["add", "amended.txt"])
    _ = _git(cwd=tmp_path, args=["commit", "--quiet", "--amend", "--no-edit"])
    _commit(
        root=tmp_path,
        filename="agent.txt",
        message=f"feat: agent-produced work\n\n{_AGENT_TRAILER}\n",
    )

    assert _head_author(root=tmp_path) == _OPERATOR_PAIR
    body = _git(cwd=tmp_path, args=["log", "-1", "--format=%B"]).stdout
    assert _AGENT_TRAILER in body

    finding = _verify(root=tmp_path)
    assert finding.status == "pass"
    assert "3 commit(s)" in finding.message


def test_red_and_amended_green_commits_share_one_validated_author(
    *,
    tmp_path: Path,
) -> None:
    """The Red commit and the Green amend carry the SAME validated identity.

    The replay ritual creates the Red commit and then amends it to
    add the implementation. The amend preserves the Red author, so
    validating the range validates both halves as one identity —
    and the assertion pins the equality rather than checking each
    half against the declaration independently.
    """
    _governed_repo(root=tmp_path, git_author=_declaration())
    _commit(root=tmp_path, filename="test_thing.py", message="feat: red")
    red_author = _head_author(root=tmp_path)

    _ = (tmp_path / "thing.py").write_text("value = 1\n", encoding="utf-8")
    _ = _git(cwd=tmp_path, args=["add", "thing.py"])
    _ = _git(cwd=tmp_path, args=["commit", "--quiet", "--amend", "--no-edit"])
    green_author = _head_author(root=tmp_path)

    assert red_author == green_author == _OPERATOR_PAIR
    assert _verify(root=tmp_path).status == "pass"


def test_conflicting_author_environment_fails_before_publication(
    *,
    tmp_path: Path,
) -> None:
    """A stale `GIT_AUTHOR_*` override is refused, naming the offending pair.

    This is the exact defect the contract exists to close: a
    long-lived runtime or a sandbox fallback keeps writing an
    identity nobody configured, and `git config user.email` reads
    canonical the whole time.
    """
    _governed_repo(root=tmp_path, git_author=_declaration())
    _commit(
        root=tmp_path,
        filename="fabro.txt",
        message="feat: work from a stale runtime",
        env=_author_env(name="fabro", email="fabro@livespec.invalid"),
    )
    offending_sha = _head_sha(root=tmp_path)

    finding = _verify(root=tmp_path)
    assert finding.status == "fail"
    assert offending_sha in finding.message
    assert "fabro <fabro@livespec.invalid>" in finding.message
    assert _OPERATOR_PAIR in finding.message


def test_explicit_author_option_fails_before_publication(*, tmp_path: Path) -> None:
    """`git commit --author=...` is refused on the object it produced."""
    _governed_repo(root=tmp_path, git_author=_declaration())
    _commit(
        root=tmp_path,
        filename="explicit.txt",
        message="feat: explicit author",
        author="thewoolleyman <chad@thewoolleyman.com>",
    )

    finding = _verify(root=tmp_path)
    assert finding.status == "fail"
    assert "thewoolleyman <chad@thewoolleyman.com>" in finding.message


def test_malformed_declaration_fails_naming_the_key(*, tmp_path: Path) -> None:
    """A declaration that cannot be enforced fails, and says which key is wrong.

    Failing closed here is what keeps a half-migrated config from
    reading as an opt-out.
    """
    _governed_repo(
        root=tmp_path,
        git_author={"operator_name": _OPERATOR_NAME},
    )
    _commit(root=tmp_path, filename="work.txt", message="feat: work")

    finding = _verify(root=tmp_path)
    assert finding.status == "fail"
    assert "git_author" in finding.message
    assert "operator_email" in finding.message


def test_revision_metadata_refuses_to_record_a_disagreeing_author(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Metadata capture and the commit path resolve one identity or fail.

    With an override in place, a config-only capture would write the
    canonical pair into the revision file while the commit carrying
    it records the override — the two surfaces disagreeing silently.
    """
    _governed_repo(root=tmp_path, git_author=_declaration())
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "fabro")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "fabro@livespec.invalid")

    result = unsafe_perform_io(io_git.get_git_user())
    match result:
        case Failure(_):
            return
        case _:
            raise AssertionError(f"expected IOFailure(...), got {result!r}")


def test_mechanical_authorship_is_narrow(*, tmp_path: Path) -> None:
    """An exactly-declared bot pair passes; a bot-shaped undeclared pair does not."""
    _governed_repo(root=tmp_path, git_author=_declaration())
    _commit(
        root=tmp_path,
        filename="CHANGELOG.md",
        message="chore(master): release 1.2.3",
        env=_author_env(name=_BOT_NAME, email=_BOT_EMAIL),
    )
    assert _verify(root=tmp_path).status == "pass"

    _commit(
        root=tmp_path,
        filename="pin.txt",
        message="chore(deps): bump pin",
        env=_author_env(
            name="some-other-bot[bot]",
            email="some-other-bot[bot]@users.noreply.github.com",
        ),
    )
    undeclared = _verify(root=tmp_path)
    assert undeclared.status == "fail"
    assert "some-other-bot[bot]" in undeclared.message


def test_imported_third_party_authorship_is_preserved(*, tmp_path: Path) -> None:
    """A declared third-party import keeps its original author and passes."""
    _governed_repo(root=tmp_path, git_author=_declaration())
    _commit(
        root=tmp_path,
        filename="upstream.txt",
        message=(
            "fix: import upstream patch\n"
            "\n"
            "Livespec-Preserved-Author: Outside Contributor <outside@example.com>\n"
        ),
        env=_author_env(name="Outside Contributor", email="outside@example.com"),
    )

    assert _head_author(root=tmp_path) == "Outside Contributor <outside@example.com>"
    assert _verify(root=tmp_path).status == "pass"


def test_a_project_that_does_not_opt_in_is_never_given_the_operator_identity(
    *,
    tmp_path: Path,
) -> None:
    """An adopter without a declaration keeps its own authors, unjudged.

    The opt-in is what activates enforcement; core imposes the
    fleet operator's identity on nobody.
    """
    _governed_repo(root=tmp_path, git_author=None)
    _commit(
        root=tmp_path,
        filename="adopter.txt",
        message="feat: adopter work",
        env=_author_env(name="Some Adopter", email="adopter@example.com"),
    )

    finding = _verify(root=tmp_path)
    assert finding.status == "skipped"
    assert _OPERATOR_EMAIL not in finding.message


def test_the_scan_reports_its_own_count_rather_than_a_bare_pass(
    *,
    tmp_path: Path,
) -> None:
    """An empty newly-introduced range passes, and says it scanned nothing.

    A push that introduces no commit has nothing to refuse; the
    message states the count and the range so a reader can tell that
    outcome apart from a range that was actually inspected.
    """
    _governed_repo(root=tmp_path, git_author=_declaration())

    finding = _verify(root=tmp_path)
    assert finding.status == "pass"
    assert "0 commit(s)" in finding.message
    assert "origin/master..HEAD" in finding.message
