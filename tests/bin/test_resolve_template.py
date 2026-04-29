"""Outside-in integration test for `bin/resolve_template.py` — Phase 3 utility wrapper rail.

Per PROPOSAL.md §"Template resolution contract (`bin/resolve_template.py`)"
lines 1424-1503, the `resolve_template` wrapper is invoked by
per-sub-command SKILL.md prose to learn the active template's
absolute directory path. Its CLI shape is frozen in v1: zero
positional args; two optional flags `--project-root <path>`
(default `Path.cwd()`) and `--template <value>`.

Stdout contract on success: exactly one line, absolute POSIX
path, trailing `\\n`. For built-in template names (`livespec`,
`minimal`), the wrapper emits
`<bundle-root>/specification-templates/<name>/`, where
`<bundle-root>` is `.claude-plugin/` (the parent of `scripts/`).

This module holds the OUTERMOST integration test for the
resolve-template exit-criterion round-trip. Per the v032 D2
outside-in walking direction, the failure point of this single
test advances forward across many TDD cycles: first the wrapper
file does not exist (FileNotFoundError); next, the supervisor
stub exists but emits empty stdout (the path-emit assertion);
then `--template` flag handling; then the bundle-root
computation; etc.

The wrapper is invoked as a subprocess so the wrapper-shape +
bootstrap + supervisor plumbing is exercised end-to-end exactly
as Claude Code invokes it via Bash.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_RESOLVE_TEMPLATE_WRAPPER = (
    _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "resolve_template.py"
)
_BUNDLE_ROOT = _REPO_ROOT / ".claude-plugin"


def test_resolve_template_emits_builtin_path_for_template_flag(*, tmp_path: Path) -> None:
    """`resolve_template.py --template livespec` emits the bundle's livespec template path.

    Per PROPOSAL.md §"Template resolution contract" lines
    1460-1476, supplying `--template livespec` (or `minimal`)
    bypasses `.livespec.jsonc` lookup and resolves directly to
    `<bundle-root>/specification-templates/<name>/`. The wrapper
    is invoked from an arbitrary cwd (here `tmp_path`); the
    `--project-root` flag is irrelevant for built-in resolution
    because `<bundle-root>` is derived inside
    `livespec/commands/resolve_template.py` via
    `Path(__file__).resolve().parents[3]`, which always lands at
    `.claude-plugin/` regardless of cwd.

    Stdout contract per PROPOSAL.md lines 1455-1459: exactly one
    line, absolute POSIX path, trailing `\\n`. The path
    corresponds to a real directory on disk (validated by this
    test's `Path.is_dir()` assertion).
    """
    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + literal flag and value); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RESOLVE_TEMPLATE_WRAPPER), "--template", "livespec"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"resolve_template wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    # Stdout contract: exactly one line, absolute POSIX path, trailing \n.
    lines = result.stdout.splitlines(keepends=True)
    assert len(lines) == 1, f"stdout must be exactly one line; got {len(lines)} lines: {lines!r}"
    assert lines[0].endswith("\n"), f"stdout line must end with `\\n`; got {lines[0]!r}"
    resolved_path = Path(lines[0].rstrip("\n"))
    assert resolved_path.is_absolute(), f"emitted path must be absolute; got {resolved_path}"
    expected_path = _BUNDLE_ROOT / "specification-templates" / "livespec"
    assert resolved_path == expected_path or resolved_path == expected_path.resolve(), (
        f"emitted path {resolved_path} does not match "
        f"expected {expected_path} or its resolved form {expected_path.resolve()}"
    )
    assert resolved_path.is_dir(), f"emitted path {resolved_path} is not an existing directory"
