"""Tests for livespec.doctor.static.git_author_policy.

Per `SPECIFICATION/contracts.md` (the opt-in `git_author`
declaration) and `SPECIFICATION/non-functional-requirements.md`
(the operator Git authorship rule): the check classifies every
commit the branch would INTRODUCE against the declared policy and
refuses publication when one carries an undeclared author.

The fixtures create the offending commits through the real
override paths rather than through a stub, so each case proves the
check sees what git actually recorded:

(a) No `git_author` declaration `skipped` — an adopter that does
    not opt in is not made to carry the operator's identity.
(b) Malformed declaration `fail` — an unenforceable declaration
    MUST NOT silently disarm the check.
(c) Every introduced commit authored by the operator pair `pass`.
(d) A commit authored through a `GIT_AUTHOR_*` override `fail`
    naming the object id and the offending pair.
(e) A commit authored through an explicit `--author` `fail`.
(f) A declared mechanical bot pair `pass`.
(g) A third-party author declaring itself preserved `pass`.
(h) Not a git working tree, and an unresolvable default-branch
    remote tip `skipped`.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import git_author_policy
from livespec.schemas.dataclasses.finding import Finding
from returns.result import Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


_OPERATOR_NAME = "Chad Woolley"
_OPERATOR_EMAIL = "thewoolleyman@gmail.com"
_BOT_NAME = "livespec-pr-bot[bot]"
_BOT_EMAIL = "livespec-pr-bot[bot]@users.noreply.github.com"


def _git(*, cwd: Path, args: list[str], env: dict[str, str] | None = None) -> None:
    """Run one git command in `cwd`, failing the test on a non-zero exit."""
    _ = subprocess.run(["git", *args], cwd=cwd, check=True, env=env)


def _init_repo(*, root: Path) -> None:
    """Initialize a repo whose configured identity is the operator pair."""
    _git(cwd=root, args=["init", "--quiet"])
    _git(cwd=root, args=["config", "--local", "user.name", _OPERATOR_NAME])
    _git(cwd=root, args=["config", "--local", "user.email", _OPERATOR_EMAIL])


def _commit(
    *,
    root: Path,
    filename: str,
    message: str = "fixture commit",
    author: str | None = None,
    env: dict[str, str] | None = None,
) -> None:
    """Write, stage, and commit one file, optionally overriding the author."""
    _ = (root / filename).write_text(f"{filename}\n", encoding="utf-8")
    _git(cwd=root, args=["add", filename])
    commit_args = ["commit", "--quiet", "-m", message]
    if author is not None:
        commit_args.append(f"--author={author}")
    _git(cwd=root, args=commit_args, env=env)


def _pin_origin_master(*, root: Path) -> None:
    """Point `origin/master` at HEAD so the scanned range starts there."""
    _git(cwd=root, args=["remote", "add", "origin", str(root)])
    _git(cwd=root, args=["update-ref", "refs/remotes/origin/master", "HEAD"])
    _git(
        cwd=root,
        args=["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"],
    )


def _write_config(*, root: Path, git_author: dict[str, object] | None) -> None:
    """Write a `.livespec.jsonc` carrying (or omitting) a `git_author` block."""
    payload: dict[str, object] = {"template": "livespec", "spec_root": "SPECIFICATION"}
    if git_author is not None:
        payload["git_author"] = git_author
    _ = (root / ".livespec.jsonc").write_text(json.dumps(payload), encoding="utf-8")


def _opted_in_declaration() -> dict[str, object]:
    """The canonical fleet declaration plus one mechanical bot pair."""
    return {
        "operator_name": _OPERATOR_NAME,
        "operator_email": _OPERATOR_EMAIL,
        "mechanical_authors": [{"name": _BOT_NAME, "email": _BOT_EMAIL}],
    }


def _run(*, root: Path) -> Finding:
    """Invoke the check against `root` and unwrap its Finding."""
    ctx = DoctorContext(project_root=root, spec_root=root / "SPECIFICATION")
    result = git_author_policy.run(ctx=ctx)
    match unsafe_perform_io(result):
        case Success(finding):
            return finding
        case _:
            raise AssertionError(f"expected IOSuccess(<Finding>), got {result!r}")


def _env_with_author(*, name: str, email: str) -> dict[str, str]:
    """A child environment whose `GIT_AUTHOR_*` overrides the repo config."""
    env = dict(os.environ)
    env["GIT_AUTHOR_NAME"] = name
    env["GIT_AUTHOR_EMAIL"] = email
    return env


def test_project_without_a_declaration_is_skipped(*, tmp_path: Path) -> None:
    """An adopter that does not opt in keeps its own author identities.

    Core MUST NOT impose the fleet operator's identity on a project
    whose config declares no `git_author`.
    """
    _init_repo(root=tmp_path)
    _write_config(root=tmp_path, git_author=None)
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)

    finding = _run(root=tmp_path)
    assert finding.status == "skipped"
    assert "has not opted into" in finding.message


def test_malformed_declaration_fails(*, tmp_path: Path) -> None:
    """An unenforceable declaration fails rather than disarming the check.

    An unknown key inside `git_author` is a typo'd or half-migrated
    declaration; treating it as absent would turn a configuration
    mistake into a silent exemption.
    """
    _init_repo(root=tmp_path)
    _write_config(
        root=tmp_path,
        git_author={
            "operator_name": _OPERATOR_NAME,
            "operator_email": _OPERATOR_EMAIL,
            "operater_email": _OPERATOR_EMAIL,
        },
    )
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)

    finding = _run(root=tmp_path)
    assert finding.status == "fail"
    assert "git_author" in finding.message


def test_operator_authored_commits_pass(*, tmp_path: Path) -> None:
    """Every introduced commit carrying the declared operator pair passes."""
    _init_repo(root=tmp_path)
    _write_config(root=tmp_path, git_author=_opted_in_declaration())
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)
    _commit(root=tmp_path, filename="feature.txt")

    finding = _run(root=tmp_path)
    assert finding.status == "pass"
    assert "1 commit(s)" in finding.message


def test_author_environment_override_fails_naming_the_commit(*, tmp_path: Path) -> None:
    """A `GIT_AUTHOR_*` override is caught on the object it produced.

    This is the shape a stale long-lived runtime or a sandbox
    fallback produces, and it is invisible to any guard that reads
    `git config user.email`.
    """
    _init_repo(root=tmp_path)
    _write_config(root=tmp_path, git_author=_opted_in_declaration())
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)
    _commit(
        root=tmp_path,
        filename="feature.txt",
        env=_env_with_author(name="fabro", email="fabro@livespec.invalid"),
    )

    finding = _run(root=tmp_path)
    assert finding.status == "fail"
    assert "fabro <fabro@livespec.invalid>" in finding.message
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head in finding.message


def test_explicit_author_option_fails(*, tmp_path: Path) -> None:
    """`git commit --author=...` is a separate override path and is caught."""
    _init_repo(root=tmp_path)
    _write_config(root=tmp_path, git_author=_opted_in_declaration())
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)
    _commit(
        root=tmp_path,
        filename="feature.txt",
        author="Someone Else <else@example.com>",
    )

    finding = _run(root=tmp_path)
    assert finding.status == "fail"
    assert "Someone Else <else@example.com>" in finding.message


def test_declared_mechanical_author_passes(*, tmp_path: Path) -> None:
    """A release or pin-bump bot declared in `mechanical_authors` stays supported."""
    _init_repo(root=tmp_path)
    _write_config(root=tmp_path, git_author=_opted_in_declaration())
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)
    _commit(
        root=tmp_path,
        filename="CHANGELOG.md",
        message="chore(master): release 1.2.3",
        env=_env_with_author(name=_BOT_NAME, email=_BOT_EMAIL),
    )

    finding = _run(root=tmp_path)
    assert finding.status == "pass"


def test_preserved_third_party_author_passes(*, tmp_path: Path) -> None:
    """A genuine third-party import declaring itself preserved is allowed."""
    _init_repo(root=tmp_path)
    _write_config(root=tmp_path, git_author=_opted_in_declaration())
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)
    _commit(
        root=tmp_path,
        filename="vendored.txt",
        message=(
            "fix: import upstream patch\n"
            "\n"
            "Livespec-Preserved-Author: Outside Contributor <outside@example.com>\n"
        ),
        env=_env_with_author(name="Outside Contributor", email="outside@example.com"),
    )

    finding = _run(root=tmp_path)
    assert finding.status == "pass"


def test_undeclared_third_party_author_fails(*, tmp_path: Path) -> None:
    """Preservation must be declared; an unfamiliar author is not self-excusing."""
    _init_repo(root=tmp_path)
    _write_config(root=tmp_path, git_author=_opted_in_declaration())
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)
    _commit(
        root=tmp_path,
        filename="vendored.txt",
        env=_env_with_author(name="Outside Contributor", email="outside@example.com"),
    )

    finding = _run(root=tmp_path)
    assert finding.status == "fail"


def test_missing_config_is_skipped(*, tmp_path: Path) -> None:
    """A missing `.livespec.jsonc` is `livespec-jsonc-valid`'s failure to report."""
    _init_repo(root=tmp_path)
    _commit(root=tmp_path, filename="base.txt")
    _pin_origin_master(root=tmp_path)

    finding = _run(root=tmp_path)
    assert finding.status == "skipped"


def test_non_git_project_root_is_skipped(*, tmp_path: Path) -> None:
    """With no git working tree there are no commit objects to classify."""
    _write_config(root=tmp_path, git_author=_opted_in_declaration())

    finding = _run(root=tmp_path)
    assert finding.status == "skipped"
    assert "not a git working tree" in finding.message


def test_unresolvable_default_branch_tip_is_skipped(*, tmp_path: Path) -> None:
    """Without `origin/HEAD` there is no newly-introduced range to scan.

    The skip names its reason rather than reporting a pass, so an
    unscanned checkout never reads as a verified one.
    """
    _init_repo(root=tmp_path)
    _write_config(root=tmp_path, git_author=_opted_in_declaration())
    _commit(root=tmp_path, filename="base.txt")

    finding = _run(root=tmp_path)
    assert finding.status == "skipped"
    assert "precondition not met" in finding.message


def test_check_is_registered_for_the_main_tree() -> None:
    """The check is wired into the explicit static-check registry."""
    from livespec.doctor.static import APPLICABILITY_BY_TREE_KIND, STATIC_CHECKS

    assert git_author_policy in STATIC_CHECKS
    assert git_author_policy in APPLICABILITY_BY_TREE_KIND["main"]


def test_check_is_not_applied_per_sub_spec_tree() -> None:
    """The declaration is a project-root concern, checked once per project."""
    from livespec.doctor.static import APPLICABILITY_BY_TREE_KIND

    assert git_author_policy not in APPLICABILITY_BY_TREE_KIND["sub_spec"]
