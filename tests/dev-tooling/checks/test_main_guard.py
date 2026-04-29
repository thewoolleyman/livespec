"""Outside-in test for `dev-tooling/checks/main_guard.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2084 the
`check-main-guard` rule reads:

    AST: no `if __name__ == "__main__":` in
    `.claude-plugin/scripts/livespec/**`.

Rationale (spec lines 149-150 of the briefing's hard
constraints): livespec runtime modules are imported by the
shebang-wrapper layer (`bin/*.py`); they MUST NOT carry a
self-execution guard because that pattern conflates library and
script roles. Wrappers in `bin/` use the canonical 6-statement
shape `raise SystemExit(main())` — no `if __name__ ==
"__main__":` anywhere.

Scope is the `livespec` package only. `bin/*.py` is exempt
(though wrappers don't use `__main__` either, by separate
contract). `dev-tooling/checks/*.py` and `tests/**` are NOT in
scope here — those legitimately use `if __name__ == "__main__":`
to invoke their `main()` from the CLI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_MAIN_GUARD = _REPO_ROOT / "dev-tooling" / "checks" / "main_guard.py"


def test_main_guard_rejects_main_guard_in_livespec_module(*, tmp_path: Path) -> None:
    """`if __name__ == "__main__":` inside `.claude-plugin/scripts/livespec/**` is rejected.

    Fixture: a synthetic project root with a single
    `.claude-plugin/scripts/livespec/has_guard.py` that declares
    a `main()` function and ends with the canonical
    `if __name__ == "__main__":` guard. The check, invoked with
    `cwd=tmp_path`, must walk the livespec tree, detect the
    guard pattern via AST inspection, exit non-zero, and surface
    the offending module path
    (`.claude-plugin/scripts/livespec/has_guard.py`) so the
    developer can locate the file.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "has_guard.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = ['main']\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return 0\n"
        "\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MAIN_GUARD)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"main_guard should reject `if __name__ == '__main__':` in livespec module; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/has_guard.py"
    assert expected_path in combined, (
        f"main_guard diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_main_guard_accepts_livespec_module_without_guard(*, tmp_path: Path) -> None:
    """A `livespec/**` module without any `__main__` guard is accepted.

    Fixture: a single `.claude-plugin/scripts/livespec/clean.py`
    that declares `main()` but does NOT have a guard at the
    bottom (the canonical livespec library-module shape; the
    `bin/*.py` shebang wrapper is the entry point that calls
    `main()`). The check must walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "clean.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = ['main']\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MAIN_GUARD)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"main_guard should accept livespec module without `__main__` guard; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_main_guard_accepts_main_guard_in_dev_tooling(*, tmp_path: Path) -> None:
    """`if __name__ == "__main__":` is permitted in `dev-tooling/**` (out of scope).

    Per spec line 2084 the rule scopes to
    `.claude-plugin/scripts/livespec/**` only. `dev-tooling/
    checks/*.py` scripts legitimately use the canonical
    `if __name__ == "__main__":` + `raise SystemExit(main())`
    pattern (every check authored from cycle 31 onwards has
    one). The check must walk only the in-scope tree and exit 0
    even when an out-of-scope file carries the guard.
    """
    dev_dir = tmp_path / "dev-tooling" / "checks"
    dev_dir.mkdir(parents=True)
    (dev_dir / "some_check.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return 0\n"
        "\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MAIN_GUARD)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"main_guard should accept `__main__` guard outside livespec scope; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
