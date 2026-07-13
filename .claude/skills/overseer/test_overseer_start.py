"""Tests for overseer-start — the /overseer skill's two-pane bootstrap guard.

Run: ``uv run pytest .claude/skills/overseer/ -q``. The bootstrap is a hyphen-named
executable (Python source under a `uv` shebang), so it is loaded via importlib; its
`if __name__ == "__main__"` guard keeps the import side-effect-free. Only the
Claude-Code precondition (the guard added 2026-07-13) is exercised here — the
proceed path performs real tmux splits and is covered by live exercise, not a
fake, since `main()` constructs its own `TmuxIO`.
"""

import importlib.machinery
import importlib.util
from pathlib import Path


def _load():
    # `overseer-start` has no `.py` extension, so spec_from_file_location can't infer
    # a loader — supply an explicit SourceFileLoader (loads any file as source).
    path = Path(__file__).resolve().parent / "overseer-start"
    loader = importlib.machinery.SourceFileLoader("overseer_start", str(path))
    spec = importlib.util.spec_from_loader("overseer_start", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def test_refuses_outside_claude_code(monkeypatch, capsys):
    # Run by hand in a plain shell ($CLAUDECODE unset): refuse BEFORE any tmux op,
    # so no half-set-up daemon pane / bare-shell bottom pane is ever created.
    mod = _load()
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setenv("TMUX_PANE", "%9")  # in tmux, but not a Claude session
    # main([]) — pass an explicit empty argv so argparse does not read pytest's own
    # sys.argv (main now parses `--warn-percent`); no flags → the guards still run.
    assert mod.main([]) == 1
    err = capsys.readouterr().err
    assert "/overseer" in err
    assert "$CLAUDECODE" in err


def test_claude_code_guard_precedes_tmux_check(monkeypatch, capsys):
    # The Claude-Code precondition is checked FIRST: with neither var set, the
    # message is the standalone-refusal, not the "$TMUX_PANE unset" one.
    mod = _load()
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("TMUX_PANE", raising=False)
    assert mod.main([]) == 1
    err = capsys.readouterr().err
    assert "Refusing to run outside Claude Code" in err
    assert "TMUX_PANE" not in err


def test_allows_when_claude_code_marker_present(monkeypatch, capsys):
    # With $CLAUDECODE set but $TMUX_PANE unset, the Claude-Code guard PASSES and
    # execution falls through to the tmux-pane check — proving the guard does not
    # block a genuine Claude Code session (it stops later, for the tmux reason).
    mod = _load()
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.delenv("TMUX_PANE", raising=False)
    assert mod.main([]) == 1
    err = capsys.readouterr().err
    assert "$TMUX_PANE unset" in err  # reached the tmux check
    assert "Refusing to run outside Claude Code" not in err  # NOT the guard


def test_daemon_command_threads_warn_percent():
    # Part 1: --warn-percent N is appended to the overseerd launch command; without
    # it the command is unchanged (default threshold applies inside overseerd).
    mod = _load()
    assert mod._daemon_command(None) == (
        ".claude/skills/overseer/overseerd 2> tmp/overseer/daemon.log"
    )
    assert mod._daemon_command(30) == (
        ".claude/skills/overseer/overseerd --warn-percent 30 2> tmp/overseer/daemon.log"
    )


def test_warn_percent_arg_parses(monkeypatch):
    # main([--warn-percent, N]) parses the flag; with $CLAUDECODE unset the guard
    # still short-circuits (return 1), proving the flag doesn't break arg parsing.
    mod = _load()
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("TMUX_PANE", raising=False)
    assert mod.main(["--warn-percent", "25"]) == 1
