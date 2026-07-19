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


def _declare(repo, topic, value, *, mtime):
    """The session writes its ONE state file, creating the parent TEMP dir first.

    The single indicator lives at ``<repo>/tmp/overseer/<topic>/.overseer-state``, whose
    parent does not exist yet — so the helper mkdirs it.
    """
    path = signals.state_path(str(repo), topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def test_state_path_is_under_tmp_overseer_never_plan(tmp_path):
    """The ONE indicator file resolves under ``<repo>/tmp/overseer/<topic>/``, not plan/."""
    repo = str(tmp_path / "repo")
    topic = "mytopic"
    expected_dir = Path(repo) / "tmp" / "overseer" / topic
    assert signals.marker_dir(repo, topic) == expected_dir
    assert signals.state_path(repo, topic) == expected_dir / ".overseer-state"
    # The overseer never writes under a session's plan/ tree.
    assert "plan" not in signals.state_path(repo, topic).parts


def test_read_state_parses_token_and_detail(tmp_path):
    """`<token>` or `<token>: <detail>` — the detail carries a blocked reason."""
    repo, topic = _setup_track(tmp_path)
    _declare(repo, topic, "ready\n", mtime=1001.0)
    st = signals.read_state(str(repo), topic)
    assert st is not None and st.token == "ready" and st.detail == ""

    _declare(repo, topic, "blocked: waiting on the schema call\n", mtime=1002.0)
    st = signals.read_state(str(repo), topic)
    assert st is not None and st.token == "blocked"
    assert st.detail == "waiting on the schema call"

    _declare(repo, topic, "  WINDING-DOWN  \n", mtime=1003.0)  # tolerant: case + whitespace
    st = signals.read_state(str(repo), topic)
    assert st is not None and st.token == "winding-down"


def test_read_state_none_when_absent_and_token_validity(tmp_path):
    repo, topic = _setup_track(tmp_path)
    assert signals.read_state(str(repo), topic) is None  # absent → None (fail-closed)
    for good in signals.STATE_TOKENS:
        assert signals.valid_token(good) is True
    assert signals.valid_token("redy") is False  # a typo is NOT a state
    # A malformed value is still RETURNED (so the daemon can surface it), just invalid.
    _declare(repo, topic, "redy\n", mtime=1001.0)
    st = signals.read_state(str(repo), topic)
    assert st is not None and st.token == "redy" and signals.valid_token(st.token) is False


def test_ready_valid_only_on_a_fresh_ready_declaration(tmp_path):
    """`ready` is the SOLE restart authorization, and only when it is THIS round's."""
    repo, topic = _setup_track(tmp_path)
    _declare(repo, topic, "ready\n", mtime=1001.0)  # newer than the stamp
    assert signals.ready_valid(str(repo), topic, injection_stamp=1000.0) is True


def test_ready_valid_false_when_absent_stale_unstamped_or_other_value(tmp_path):
    """Fail-closed on every path that is not an unambiguous, this-round `ready`."""
    repo, topic = _setup_track(tmp_path)
    # 1. Nothing declared at all — the severe-bug case: idleness is NEVER readiness.
    assert signals.ready_valid(str(repo), topic, injection_stamp=1000.0) is False
    # 2. Declared `ready`, but STALE (older than this round's injection stamp).
    _declare(repo, topic, "ready\n", mtime=999.0)
    assert signals.ready_valid(str(repo), topic, injection_stamp=1000.0) is False
    # 3. Fresh `ready`, but NO injection this round → nothing to certify.
    _declare(repo, topic, "ready\n", mtime=1001.0)
    assert signals.ready_valid(str(repo), topic, injection_stamp=None) is False
    # 4. The other two values are NOT readiness — one file, so they REPLACE `ready`.
    for other in ("blocked: needs a human", "winding-down"):
        _declare(repo, topic, other + "\n", mtime=1001.0)
        assert signals.ready_valid(str(repo), topic, injection_stamp=1000.0) is False
    # 5. A typo'd value is not readiness either.
    _declare(repo, topic, "redy\n", mtime=1001.0)
    assert signals.ready_valid(str(repo), topic, injection_stamp=1000.0) is False


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


def test_parse_ctx_reads_both_runtimes_own_statuslines():
    """Each runtime renders ITS OWN computed context-left; the daemon reads that number
    rather than recomputing occupancy.

    Codex says `Context N% left`, Claude says `Ctx: N% left`. An earlier cut computed
    Codex's ctx from its rollout's `token_count` events and was WRONG by 2-4 points
    against Codex's own display (62 vs 66, 36 vs 38 — verified live 2026-07-17), because
    that reimplements codex-rs's private occupancy formula (a ~12k baseline, reasoning
    tokens excluded). Reading the runtime's own number cannot drift that way.
    """
    claude_pane = "\n".join(["irrelevant", "", "Ctx: 42% left", "? for shortcuts"])
    codex_pane = "\n".join(
        [
            "irrelevant",
            "",
            "\u203a Find and fix a bug in @filename",
            "",
            "  gpt-5.5 high \u00b7 /data/projects/x \u00b7 Context 66% left \u00b7 some-topic",
        ]
    )
    assert signals.parse_ctx_remaining(claude_pane) == 42
    assert signals.parse_ctx_remaining(codex_pane) == 66


def test_pane_is_codex_is_loose_and_must_never_gate_alone():
    """`bun` is the codex pane's foreground process (the launcher; the codex binary is
    its child) — and it matches ANY bun app, so this predicate is deliberately loose and
    is only ever used PAIRED with an exact live-session-map lookup."""
    assert signals.pane_is_codex("bun") is True
    assert signals.pane_is_codex("codex") is True
    assert signals.pane_is_codex("node") is False  # a Claude pane is never codex
    assert signals.pane_is_codex("zsh") is False
    assert signals.pane_is_codex(None) is False


def test_codex_prompt_present_requires_the_codex_statusline_not_just_the_glyph():
    """STRUCTURAL, never glyph-only: a `›` line alone is not a Codex TUI. Claude's own
    statusline says `Ctx: N% left`, Codex's says `Context N% left` — without the Codex
    form this must be False, or a Claude pane that happens to render a `›` (quoted text,
    a prompt char) would be driven through the Codex restart path."""
    claude_pane = "\n".join(
        [
            "● the doc quotes a codex line:",
            "› Find and fix a bug in @filename",
            "  Opus 4.8 | /x/repo | Ctx: 73% left",
            "  ? for shortcuts",
        ]
    )
    assert signals.codex_prompt_present(claude_pane) is False
    assert signals.is_codex_idle_input(claude_pane) is False


def test_is_codex_idle_input_false_while_the_codex_pane_is_busy():
    """A generating Codex pane still shows its `›` prompt AND its statusline, so the
    prompt check alone would call it idle. Busy must dominate — otherwise the daemon
    pastes the wrap-up into a session mid-generation."""
    busy_codex = "\n".join(
        [
            "✻ Working… (running tests… · 24s · ↓ 1.4k tokens)",
            "› ",
            "  gpt-5.5 high · /data/projects/x · Context 66% left · some-topic",
        ]
    )
    assert signals.codex_prompt_present(busy_codex) is True  # the prompt IS present...
    assert signals.is_busy(busy_codex) is True
    assert signals.is_codex_idle_input(busy_codex) is False  # ...but busy wins


def test_read_state_is_none_when_the_state_file_is_unreadable(tmp_path, monkeypatch):
    """Fail-closed: a PRESENT but unreadable indicator reads as "no state", never raises —
    so an unreadable file can never authorize a restart (it is not a `ready`).

    Denial is injected at ``Path.read_text`` rather than via ``chmod``: CI runs its
    container steps as ROOT, where mode bits deny nothing, so a chmod-based version
    of this test passes locally and silently stops exercising the fail-closed branch
    in CI — which is worse than no test, because this branch is a SAFETY guard.
    """
    repo, topic = _setup_track(tmp_path)
    _declare(repo, topic, "ready\n", mtime=1001.0)

    def _deny(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(signals.Path, "read_text", _deny)
    assert signals.read_state(str(repo), topic) is None
    assert signals.ready_valid(str(repo), topic, injection_stamp=1000.0) is False


def test_only_a_shell_proves_a_pane_is_dead():
    """The rule `start`'s fail-closed guard relies on: proof of DEATH, not "not Claude".
    Enumerating the live runtimes did not scale to a second one — a live codex pane
    (`bun`) failed the Claude test and got respawn-killed."""
    assert signals.pane_is_shell("zsh") is True
    for live_or_unknown in ("node", "claude", "bun", "codex", "vim", None):
        assert signals.pane_is_shell(live_or_unknown) is False
