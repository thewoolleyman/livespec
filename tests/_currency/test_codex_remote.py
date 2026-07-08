"""Focused coverage for _currency.codex_remote config parse + ls-remote tip."""

# ruff: noqa: SLF001

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from _currency import codex_remote

__all__: list[str] = []

_LIVESPEC_CONFIG = (
    "[marketplaces.livespec-driver-codex]\n"
    'last_revision = "1111111111112222"\n'
    'ref = "release"\n'
    "\n"
    "[marketplaces.livespec]\n"
    'last_updated = "2026-07-08T00:11:07Z"\n'
    'last_revision = "abcdef1234567890abcdef1234567890abcdef12"\n'
    'source_type = "git"\n'
    'source = "https://github.com/thewoolleyman/livespec.git"\n'
    'ref = "release"\n'
    "\n"
    "[marketplaces.other]\n"
    'ref = "main"\n'
)


def _write_config(*, home: Path, body: str) -> None:
    config_path = home / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(body, encoding="utf-8")


def _make_marketplace_clone(*, home: Path) -> Path:
    clone = home / ".codex" / ".tmp" / "marketplaces" / "livespec"
    clone.mkdir(parents=True, exist_ok=True)
    return clone


def test_config_section_reads_only_the_target_marketplace_block(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The line parse collects the target section's keys and stops at the next header."""
    home = tmp_path / "home"
    _write_config(home=home, body=_LIVESPEC_CONFIG)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(tmp_path)
    section = codex_remote._codex_config_marketplace_section(marketplace="livespec")
    assert section == {
        "last_updated": "2026-07-08T00:11:07Z",
        "last_revision": "abcdef1234567890abcdef1234567890abcdef12",
        "source_type": "git",
        "source": "https://github.com/thewoolleyman/livespec.git",
        "ref": "release",
    }


def test_config_section_none_when_config_file_missing(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing ~/.codex/config.toml leaves the section unknown."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "absent-home")
    monkeypatch.chdir(tmp_path)
    assert codex_remote._codex_config_marketplace_section(marketplace="livespec") is None


def test_config_section_none_when_target_section_absent(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A config without the target marketplace section is unknown, not empty."""
    home = tmp_path / "home"
    _write_config(home=home, body='[marketplaces.other]\nref = "main"\n')
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(tmp_path)
    assert codex_remote._codex_config_marketplace_section(marketplace="livespec") is None


def test_last_revision_build_id_normalizes_to_twelve_hex(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A 40-hex last_revision is truncated to the 12-hex build id."""
    home = tmp_path / "home"
    _write_config(home=home, body=_LIVESPEC_CONFIG)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(tmp_path)
    assert codex_remote._codex_last_revision_build_id() == "abcdef123456"


def test_last_revision_build_id_none_when_absent_or_invalid(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A section missing last_revision, or with a non-SHA value, is unknown."""
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(tmp_path)
    _write_config(home=home, body='[marketplaces.livespec]\nref = "release"\n')
    assert codex_remote._codex_last_revision_build_id() is None
    _write_config(home=home, body='[marketplaces.livespec]\nlast_revision = "not-a-sha"\n')
    assert codex_remote._codex_last_revision_build_id() is None


def test_last_revision_build_id_none_when_config_missing(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No config file means no running build."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "absent")
    monkeypatch.chdir(tmp_path)
    assert codex_remote._codex_last_revision_build_id() is None


def test_remote_ref_build_id_resolves_branch_tip(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A branch `ref` resolves to the ls-remote tip, normalized to 12-hex."""
    home = tmp_path / "home"
    _write_config(home=home, body=_LIVESPEC_CONFIG)
    clone = _make_marketplace_clone(home=home)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(tmp_path)

    def fake_run(
        args: list[str], *, capture_output: bool, check: bool, text: bool, timeout: int
    ) -> SimpleNamespace:
        assert args == ["/usr/bin/git", "-C", str(clone), "ls-remote", "origin", "release"]
        assert capture_output is True
        assert check is False
        assert text is True
        assert timeout == codex_remote._LS_REMOTE_TIMEOUT_SECONDS
        return SimpleNamespace(
            returncode=0, stdout="cafebabecafe1234deadbeef\trefs/heads/release\n"
        )

    monkeypatch.setattr(codex_remote.subprocess, "run", fake_run)
    assert codex_remote._codex_remote_ref_build_id() == "cafebabecafe"


def test_remote_ref_build_id_prefers_peeled_annotated_tag(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An annotated-tag `ref` resolves to the peeled `^{}` commit, not the tag object."""
    home = tmp_path / "home"
    _write_config(home=home, body='[marketplaces.livespec]\nref = "v1.2.3"\n')
    _make_marketplace_clone(home=home)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(tmp_path)
    stdout = "aaaaaaaaaaaa0000\trefs/tags/v1.2.3\nbbbbbbbbbbbb1111\trefs/tags/v1.2.3^{}\n"
    monkeypatch.setattr(
        codex_remote.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=stdout),
    )
    assert codex_remote._codex_remote_ref_build_id() == "bbbbbbbbbbbb"


def test_remote_ref_build_id_none_when_clone_absent(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ls-remote is not attempted when the marketplace clone directory is absent."""
    home = tmp_path / "home"
    _write_config(home=home, body=_LIVESPEC_CONFIG)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(tmp_path)
    # A resolvable sentinel: if ls-remote ran despite the clone being absent,
    # this tip would surface instead of None and fail the assertion.
    monkeypatch.setattr(
        codex_remote.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout="deadbeefdead\trefs/heads/x\n"
        ),
    )
    assert codex_remote._codex_remote_ref_build_id() is None


def test_remote_ref_build_id_none_when_ref_absent(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A section without a `ref` cannot resolve a remote tip."""
    home = tmp_path / "home"
    _write_config(home=home, body='[marketplaces.livespec]\nlast_revision = "abcdef1234567890"\n')
    _make_marketplace_clone(home=home)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(tmp_path)
    assert codex_remote._codex_remote_ref_build_id() is None


def test_remote_ref_build_id_none_when_config_missing(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No config section means no expected build."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "absent")
    monkeypatch.chdir(tmp_path)
    assert codex_remote._codex_remote_ref_build_id() is None


def test_git_ls_remote_tip_handles_process_failures(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A non-zero exit, a timeout, or an OSError all leave the tip unknown."""
    clone = tmp_path / "clone"
    clone.mkdir()
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        codex_remote.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout=""),
    )
    assert codex_remote._git_ls_remote_tip(repository=clone, ref="release") is None

    def raise_timeout(*_args: object, **_kwargs: object) -> SimpleNamespace:
        raise codex_remote.subprocess.TimeoutExpired(cmd="git", timeout=5)

    monkeypatch.setattr(codex_remote.subprocess, "run", raise_timeout)
    assert codex_remote._git_ls_remote_tip(repository=clone, ref="release") is None

    def raise_os(*_args: object, **_kwargs: object) -> SimpleNamespace:
        raise OSError("git unavailable")

    monkeypatch.setattr(codex_remote.subprocess, "run", raise_os)
    assert codex_remote._git_ls_remote_tip(repository=clone, ref="release") is None


def test_git_ls_remote_tip_none_for_missing_repository(*, tmp_path: Path) -> None:
    """A non-existent clone leaves the tip unknown without shelling out."""
    assert codex_remote._git_ls_remote_tip(repository=tmp_path / "absent", ref="release") is None


def test_first_ls_remote_sha_skips_short_lines_and_validates() -> None:
    """The parser skips fieldless lines, rejects non-SHA output, and returns the first SHA."""
    assert codex_remote._first_ls_remote_sha(output="") is None
    assert codex_remote._first_ls_remote_sha(output="justonefield\n") is None
    assert codex_remote._first_ls_remote_sha(output="not-a-sha\trefs/heads/release\n") is None
    assert (
        codex_remote._first_ls_remote_sha(output="abcdef123456aaaa\trefs/heads/release\n")
        == "abcdef123456"
    )
    # Two non-peeled lines: the second keeps the first as the fallback.
    assert (
        codex_remote._first_ls_remote_sha(
            output="abcdef123456aaaa\trefs/heads/release\n999999999999bbbb\trefs/heads/other\n"
        )
        == "abcdef123456"
    )
