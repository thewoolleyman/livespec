"""red_green_replay — v034 D2-D3 replay-based TDD enforcement.

Per `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
§"Testing approach — Activation §v034 D2-D3 Red→Green replay
contract" and Plan §"Per-commit Red→Green replay discipline
(v034 D2-D3)", this hook is invoked as a `commit-msg` git
hook with the path to `.git/COMMIT_EDITMSG` as argv[1]. It
reads the commit subject; for `feat:` or `fix:` types it
runs the v034 D3 Red-or-Green-mode logic (test-file SHA-256
checksum, pytest invocation, trailer authoring); for other
Conventional Commit types (chore, docs, build, ci, style,
test, refactor, perf, revert) it exits 0 immediately.

Cycles 173-174 implement minimum-viable type discrimination:
`chore:` subjects exit 0; non-exempt subjects (feat:, fix:,
and any unknown type) exit 1. Future cycles extend the
exempt list with the remaining config/meta types and drive
the type-classification + Red/Green-mode dispatch +
checksum + replay logic via additional failing tests.

This file is authored under the v033 discipline still in
force (the replay hook itself is not yet gating; the v033
`red_output_in_commit.py` is still active). The v034 D5
replay-hook activation commit replaces the v033 hook with
this one and authors the initial
`phase-5-deferred-violations.toml`.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__: list[str] = []


def main() -> int:
    msg_path = Path(sys.argv[1])
    subject = msg_path.read_text(encoding="utf-8").split("\n", 1)[0]
    if subject.startswith("chore:"):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
