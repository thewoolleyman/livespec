"""Tests for signals.py — pure pane parsing + marker certification.

Run: ``uv run pytest .claude/skills/overseer/ -q``. ``import signals`` resolves
via conftest.py. The two adversarial-critical behaviors are tested hard:
``parse_ctx_remaining`` anchoring (design blocker #5) and the three-way
``ready_marker_valid`` certification (design blockers #1,#3,#4).
"""

import hashlib
import os

import pytest
import signals


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


# --------------------------------------------------------------------------- #
# strip_ansi.
# --------------------------------------------------------------------------- #


def test_strip_ansi_removes_csi_sequences():
    coloured = "\x1b[38;5;244mCtx: 73% left\x1b[0m"
    assert signals.strip_ansi(coloured) == "Ctx: 73% left"


# --------------------------------------------------------------------------- #
# parse_ctx_remaining — anchored + fail-closed (blocker #5).
# --------------------------------------------------------------------------- #


def test_parse_ctx_reads_last_status_row():
    capture = "some earlier output\n\n  Ctx: 73% left\n"
    assert signals.parse_ctx_remaining(capture) == 73


def test_parse_ctx_takes_last_match_on_the_row():
    # A row with two matches → the LAST wins.
    capture = "Ctx: 90% left   Ctx: 42% left\n"
    assert signals.parse_ctx_remaining(capture) == 42


def test_parse_ctx_ignores_body_when_last_line_is_a_normal_prompt():
    """ADVERSARIAL (blocker #5): the BODY contains 'Ctx: 5% left' (e.g. the
    design doc scrolled by), but the last non-empty line is a normal prompt —
    the result must be None, not a false 5%."""
    capture = "The design doc says the statusline prints Ctx: 5% left near the end.\n" "> \n"
    assert signals.parse_ctx_remaining(capture) is None


def test_parse_ctx_reads_status_row_not_body_ctx():
    """ADVERSARIAL: body carries 'Ctx: 5% left', but the actual statusline row
    (last non-empty) says 73% — must return 73, never 5."""
    capture = (
        "quoting the doc: Ctx: 5% left appears in page content\n"
        "\x1b[2m~/repo  main  Ctx: 73% left\x1b[0m\n"
    )
    assert signals.parse_ctx_remaining(capture) == 73


def test_parse_ctx_none_when_no_match_anywhere():
    assert signals.parse_ctx_remaining("just a normal prompt\n> \n") is None


def test_parse_ctx_none_on_empty_capture():
    assert signals.parse_ctx_remaining("") is None
    assert signals.parse_ctx_remaining("\n\n   \n") is None


def test_parse_ctx_skips_trailing_blank_lines_to_find_status_row():
    capture = "  Ctx: 12% left\n\n\n"  # blank lines after the status row
    assert signals.parse_ctx_remaining(capture) == 12


# --------------------------------------------------------------------------- #
# is_busy.
# --------------------------------------------------------------------------- #


def test_is_busy_markers():
    assert signals.is_busy("... esc to interrupt ...") is True
    assert signals.is_busy("Waiting for 3 background tasks") is True
    assert signals.is_busy("running: 2 shells") is True


def test_is_busy_false_when_idle():
    assert signals.is_busy("> \n  ? for shortcuts\n") is False
    # A prose 'background' with no count must not trip the waiting marker.
    assert signals.is_busy("thinking about background context") is False


# --------------------------------------------------------------------------- #
# is_structured_gate.
# --------------------------------------------------------------------------- #


def test_is_structured_gate_detects_permission_and_picker():
    permission = "Do you want to proceed?\n❯ 1. Yes\n  2. No\n"
    assert signals.is_structured_gate(permission) is True
    picker = "Choose an option\n❯ 1. Alpha\n  2. Beta\n"
    assert signals.is_structured_gate(picker) is True


def test_is_structured_gate_false_for_plain_numbered_list():
    # A numbered list in normal output (no cursor, no permission question)
    # must NOT read as a gate.
    plain = "Steps:\n1. do this\n2. do that\n> \n"
    assert signals.is_structured_gate(plain) is False


# --------------------------------------------------------------------------- #
# is_idle_input — verified idle (not "just not busy").
# --------------------------------------------------------------------------- #

_IDLE_CAPTURE = "╭──────────╮\n│ >        │\n╰──────────╯\n  ? for shortcuts\n  Ctx: 73% left\n"


def test_is_idle_input_true_for_verified_idle():
    assert signals.is_idle_input(_IDLE_CAPTURE) is True


def test_is_idle_input_false_when_busy():
    busy = "╭──────────╮\n│ > run    │\n╰──────────╯\n  esc to interrupt\n"
    assert signals.is_idle_input(busy) is False


def test_is_idle_input_false_when_gate():
    gated = "Do you want to proceed?\n❯ 1. Yes\n  2. No\n  ? for shortcuts\n"
    assert signals.is_idle_input(gated) is False


def test_is_idle_input_false_for_blank_pane():
    # 'Not busy' alone is NOT idle-input — a blank pane has no prompt box.
    assert signals.is_idle_input("") is False
    assert signals.is_idle_input("some stale scrollback with no box\n") is False


# --------------------------------------------------------------------------- #
# ready_marker_valid — the load-bearing three-way certification.
# --------------------------------------------------------------------------- #


def _setup_track(tmp_path, *, handoff_bytes=b"HANDOFF v1\ncontent\n"):
    repo = tmp_path / "repo"
    topic = "mytopic"
    plan_topic = repo / "plan" / topic
    plan_topic.mkdir(parents=True)
    handoff = plan_topic / "handoff.md"
    handoff.write_bytes(handoff_bytes)
    return repo, topic, handoff


def _write_marker(repo, topic, contents, *, mtime):
    marker = signals.ready_marker_path(str(repo), topic)
    marker.write_text(contents, encoding="utf-8")
    os.utime(marker, (mtime, mtime))
    return marker


def test_ready_marker_valid_true_only_when_all_three_hold(tmp_path):
    repo, topic, handoff = _setup_track(tmp_path)
    digest = hashlib.sha256(handoff.read_bytes()).hexdigest()
    _write_marker(repo, topic, digest + "\n", mtime=1001.0)  # newer than stamp
    assert (
        signals.ready_marker_valid(str(repo), topic, str(handoff), injection_stamp=1000.0) is True
    )


def test_ready_marker_valid_false_when_marker_missing(tmp_path):
    repo, topic, handoff = _setup_track(tmp_path)
    assert (
        signals.ready_marker_valid(str(repo), topic, str(handoff), injection_stamp=1000.0) is False
    )


def test_ready_marker_valid_false_when_mtime_not_newer_than_stamp(tmp_path):
    repo, topic, handoff = _setup_track(tmp_path)
    digest = hashlib.sha256(handoff.read_bytes()).hexdigest()
    _write_marker(repo, topic, digest + "\n", mtime=999.0)  # OLDER than the stamp
    assert (
        signals.ready_marker_valid(str(repo), topic, str(handoff), injection_stamp=1000.0) is False
    )


def test_ready_marker_valid_false_when_contents_mismatch_handoff_hash(tmp_path):
    repo, topic, handoff = _setup_track(tmp_path)
    _write_marker(repo, topic, "deadbeef" * 8 + "\n", mtime=1001.0)  # wrong hash
    assert (
        signals.ready_marker_valid(str(repo), topic, str(handoff), injection_stamp=1000.0) is False
    )


def test_ready_marker_valid_false_when_injection_stamp_is_none(tmp_path):
    repo, topic, handoff = _setup_track(tmp_path)
    digest = hashlib.sha256(handoff.read_bytes()).hexdigest()
    _write_marker(repo, topic, digest + "\n", mtime=1001.0)
    # No injection this round → any pre-existing marker is not certified.
    assert signals.ready_marker_valid(str(repo), topic, str(handoff), injection_stamp=None) is False


def test_ready_marker_invalidated_when_handoff_changes_after_marker(tmp_path):
    """The hash binds to the CURRENT on-disk handoff: a valid marker goes
    invalid if the handoff is subsequently edited without re-writing it."""
    repo, topic, handoff = _setup_track(tmp_path)
    digest = hashlib.sha256(handoff.read_bytes()).hexdigest()
    _write_marker(repo, topic, digest + "\n", mtime=1001.0)
    assert (
        signals.ready_marker_valid(str(repo), topic, str(handoff), injection_stamp=1000.0) is True
    )
    handoff.write_bytes(b"HANDOFF v2 - edited after the marker\n")  # hash now differs
    assert (
        signals.ready_marker_valid(str(repo), topic, str(handoff), injection_stamp=1000.0) is False
    )


def test_ready_marker_valid_false_when_handoff_unreadable(tmp_path):
    repo, topic, handoff = _setup_track(tmp_path)
    digest = hashlib.sha256(handoff.read_bytes()).hexdigest()
    _write_marker(repo, topic, digest + "\n", mtime=1001.0)
    missing_handoff = tmp_path / "repo" / "plan" / topic / "does-not-exist.md"
    assert (
        signals.ready_marker_valid(str(repo), topic, str(missing_handoff), injection_stamp=1000.0)
        is False
    )


# --------------------------------------------------------------------------- #
# blocked_marker.
# --------------------------------------------------------------------------- #


def test_blocked_marker_returns_contents_or_none(tmp_path):
    repo, topic, _handoff = _setup_track(tmp_path)
    assert signals.blocked_marker(str(repo), topic) is None  # absent
    marker = signals.blocked_marker_path(str(repo), topic)
    marker.write_text("waiting on a human decision about schema\n", encoding="utf-8")
    assert signals.blocked_marker(str(repo), topic) == "waiting on a human decision about schema"


def test_blocked_marker_empty_file_is_present_not_none(tmp_path):
    repo, topic, _handoff = _setup_track(tmp_path)
    signals.blocked_marker_path(str(repo), topic).write_text("", encoding="utf-8")
    # Presence (not content) is the signal → empty string, never None.
    assert signals.blocked_marker(str(repo), topic) == ""


# --------------------------------------------------------------------------- #
# Process-identity helpers.
# --------------------------------------------------------------------------- #


def test_pane_is_claude_and_shell():
    assert signals.pane_is_claude("node") is True
    assert signals.pane_is_claude("claude") is True
    assert signals.pane_is_claude("zsh") is False
    assert signals.pane_is_claude(None) is False
    assert signals.pane_is_shell("zsh") is True
    assert signals.pane_is_shell("bash") is True
    assert signals.pane_is_shell("node") is False


def test_path_in_repo():
    repo = "/data/projects/livespec"
    assert signals.path_in_repo("/data/projects/livespec", repo) is True  # equal
    assert signals.path_in_repo("/data/projects/livespec/plan/x", repo) is True  # inside
    # Sibling-prefix trap: '/data/projects/livespec-other' is NOT inside.
    assert signals.path_in_repo("/data/projects/livespec-other", repo) is False
    assert signals.path_in_repo("/somewhere/else", repo) is False
    assert signals.path_in_repo(None, repo) is False
