"""Tests for signals.py — pure pane parsing + marker certification.

Run: ``uv run pytest .claude/skills/overseer/ -q``. ``import signals`` resolves
via conftest.py. The two adversarial-critical behaviors are tested hard:
``parse_ctx_remaining`` anchoring (design blocker #5) and the
``ready_marker_valid`` certification (presence + freshness only — the marker's
contents are no longer inspected; markers live under ``<repo>/tmp/overseer/``).
"""

import os
from pathlib import Path

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
    design doc scrolled by) far ABOVE the bottom rows, while the bottom
    statusline carries no Ctx (a fresh session). The bounded last-rows scan must
    NOT reach the stray body match — result None, not a false 5%."""
    capture = (
        "The design doc says the statusline prints Ctx: 5% left near the end.\n"
        "filler A\nfiller B\nfiller C\nfiller D\n"
        + ("─" * 40)
        + "\n❯ \n"
        + ("─" * 40)
        + "\n  Opus 4.8 (1M context) | /x/repo\n"
        + "  ⏵⏵ bypass permissions on (shift+tab to cycle)\n"
    )
    assert signals.parse_ctx_remaining(capture) is None


def test_parse_ctx_reads_statusline_above_the_hint_line():
    """REGRESSION (live 2026-07-13): the statusline is the SECOND-to-last row —
    a footer hint renders BELOW it — so reading only the LAST row returns None.
    The bounded last-rows scan must still find the real 73%."""
    assert signals.parse_ctx_remaining(_IDLE_CAPTURE) == 73


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
    # The real active-generation spinner (verified live 2026-07-13): a spinner
    # line carrying a token counter / dot-delimited elapsed / hook phase.
    assert signals.is_busy("✻ Galloping… (running stop hooks… 1/3 · 24s · ↓ 1.4k tokens)") is True
    # The lingering completed-turn summary is deliberately NOT busy.
    assert signals.is_busy("✻ Brewed for 25s") is False
    # A plain idle capture is not busy.
    assert signals.is_busy(_IDLE_CAPTURE) is False


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

# The REAL live Claude TUI idle shape (verified 2026-07-13): an empty `❯` prompt
# between two horizontal rule lines, the statusline as the SECOND-to-last row,
# and a footer hint LAST (NOT a `╭─╮` box + `? for shortcuts`).
_IDLE_CAPTURE = (
    "● prior response\n"
    + ("─" * 40)
    + "\n❯ \n"
    + ("─" * 40)
    + "\n  Opus 4.8 (1M context) | /x/repo | Ctx: 73% left\n"
    + "  ⏵⏵ bypass permissions on (shift+tab to cycle) · ← for agents\n"
)


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


def _setup_track(tmp_path):
    """A watched track: a repo with the session's own ``plan/<topic>/`` dir.

    The overseer's markers live under ``<repo>/tmp/overseer/<topic>/`` (created by
    the marker-writing helpers), NEVER under ``plan/`` — the ``plan/`` dir here is
    only the session's own workflow tree, which the overseer never touches.
    """
    repo = tmp_path / "repo"
    topic = "mytopic"
    (repo / "plan" / topic).mkdir(parents=True)
    return repo, topic


def _write_marker(repo, topic, contents, *, mtime):
    """Write the ready marker at its TEMP path, creating the parent dir first.

    The marker now lives at ``<repo>/tmp/overseer/<topic>/.overseer-ready``, whose
    parent does not exist yet — so the helper mkdirs it. ``contents`` is arbitrary:
    ``ready_marker_valid`` inspects presence + mtime only, never the bytes.
    """
    marker = signals.ready_marker_path(str(repo), topic)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(contents, encoding="utf-8")
    os.utime(marker, (mtime, mtime))
    return marker


def test_marker_paths_are_under_tmp_overseer(tmp_path):
    """The markers resolve under ``<repo>/tmp/overseer/<topic>/`` and NOT plan/."""
    repo = str(tmp_path / "repo")
    topic = "mytopic"
    expected_dir = Path(repo) / "tmp" / "overseer" / topic
    assert signals.marker_dir(repo, topic) == expected_dir
    assert signals.ready_marker_path(repo, topic) == expected_dir / ".overseer-ready"
    assert signals.blocked_marker_path(repo, topic) == expected_dir / ".overseer-blocked"
    # The overseer never writes under a session's plan/ tree.
    assert "plan" not in signals.ready_marker_path(repo, topic).parts
    assert "plan" not in signals.blocked_marker_path(repo, topic).parts


def test_ready_marker_valid_true_when_stamp_marker_and_mtime_hold(tmp_path):
    # The three surviving conditions: injection_stamp present, marker exists, and
    # its mtime is strictly newer than the stamp. Content is irrelevant.
    repo, topic = _setup_track(tmp_path)
    _write_marker(repo, topic, "x", mtime=1001.0)  # newer than stamp
    assert signals.ready_marker_valid(str(repo), topic, injection_stamp=1000.0) is True


def test_ready_marker_valid_is_presence_and_freshness_only(tmp_path):
    """A marker with ARBITRARY content (not a hash of anything) validates purely on
    presence + freshness — the overseer never inspects the marker's bytes."""
    repo, topic = _setup_track(tmp_path)
    _write_marker(repo, topic, "totally arbitrary not-a-hash payload\n", mtime=1001.0)
    assert signals.ready_marker_valid(str(repo), topic, injection_stamp=1000.0) is True


def test_ready_marker_valid_false_when_marker_missing(tmp_path):
    repo, topic = _setup_track(tmp_path)
    assert signals.ready_marker_valid(str(repo), topic, injection_stamp=1000.0) is False


def test_ready_marker_valid_false_when_mtime_not_newer_than_stamp(tmp_path):
    repo, topic = _setup_track(tmp_path)
    _write_marker(repo, topic, "x", mtime=999.0)  # OLDER than the stamp
    assert signals.ready_marker_valid(str(repo), topic, injection_stamp=1000.0) is False


def test_ready_marker_valid_false_when_injection_stamp_is_none(tmp_path):
    repo, topic = _setup_track(tmp_path)
    _write_marker(repo, topic, "x", mtime=1001.0)
    # No injection this round → any pre-existing marker is not certified.
    assert signals.ready_marker_valid(str(repo), topic, injection_stamp=None) is False


# --------------------------------------------------------------------------- #
# blocked_marker.
# --------------------------------------------------------------------------- #


def test_blocked_marker_returns_contents_or_none(tmp_path):
    repo, topic = _setup_track(tmp_path)
    assert signals.blocked_marker(str(repo), topic) is None  # absent
    marker = signals.blocked_marker_path(str(repo), topic)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("waiting on a human decision about schema\n", encoding="utf-8")
    assert signals.blocked_marker(str(repo), topic) == "waiting on a human decision about schema"


def test_blocked_marker_empty_file_is_present_not_none(tmp_path):
    repo, topic = _setup_track(tmp_path)
    marker = signals.blocked_marker_path(str(repo), topic)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("", encoding="utf-8")
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


def test_is_idle_input_accepts_renamed_titled_border():
    # B2: `claude -n <topic>` renders the session name INTO the top border
    # (`─── mytopic ──`), which is NOT a pure rule. is_idle_input must still detect
    # the idle box, else every daemon-renamed session becomes unmanageable.
    rule = "─" * 40
    titled = ("─" * 20) + " mytopic ──"
    renamed = f"● prior\n{titled}\n❯ \n{rule}\n  Opus | /r | Ctx: 40% left\n  ? for shortcuts\n"
    assert signals.is_idle_input(renamed) is True
    assert signals.input_box_ready(renamed) is True


def test_is_idle_input_rejects_prose_around_empty_prompt():
    # Guard: an empty `❯` between ordinary prose lines (no box borders) is NOT idle.
    prose = "● Read 1 file\n❯ \nSome narration line.\n"
    assert signals.is_idle_input(prose) is False
