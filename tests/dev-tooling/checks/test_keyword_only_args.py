"""Outside-in test for `dev-tooling/checks/keyword_only_args.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2086:

    AST: every `def` in livespec scope uses `*` as first
    separator (all params keyword-only); every `@dataclass`
    declares the strict-dataclass triple `frozen=True,
    kw_only=True, slots=True`. Exempts Python-mandated dunder
    signatures and `__init__` of Exception subclasses that
    forward to `super().__init__(msg)`.

The check has two responsibilities. Cycle 37 pins the first:
a `def` without a `*` separator (i.e., one or more positional
parameters) inside `.claude-plugin/scripts/livespec/**` is
rejected. The dataclass-triple check is deferred to a later
cycle per v032 D1 one-pattern-per-cycle.

Dunder methods (`__init__`, `__eq__`, `__hash__`, etc.) are
exempt because Python's call protocol fixes their signatures
positionally. The check skips function names matching the
`__<name>__` shape.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_KEYWORD_ONLY_ARGS = _REPO_ROOT / "dev-tooling" / "checks" / "keyword_only_args.py"


def test_keyword_only_args_rejects_def_with_positional_arg(*, tmp_path: Path) -> None:
    """A `def` with a positional parameter (no `*` separator) is rejected.

    Fixture: `.claude-plugin/scripts/livespec/positional.py`
    declares `def f(x: int) -> int: return x` — `x` is
    positional-or-keyword (no leading `*`). The check, invoked
    with `cwd=tmp_path`, must walk the livespec tree, detect
    the missing `*` separator via AST inspection, exit
    non-zero, and surface the offending module path so the
    developer can locate the file.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "positional.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["f"]\n'
        "\n"
        "\n"
        "def f(x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"keyword_only_args should reject `def f(x: int)` (no `*` separator); "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/positional.py"
    assert expected_path in combined, (
        f"keyword_only_args diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_keyword_only_args_accepts_def_with_kw_only_separator(*, tmp_path: Path) -> None:
    """A `def` with leading `*` (all params keyword-only) is accepted.

    Fixture: `.claude-plugin/scripts/livespec/kw_only.py`
    declares `def f(*, x: int) -> int: return x`. The leading
    `*` makes `x` keyword-only, satisfying the rule. The check
    must walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "kw_only.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["f"]\n'
        "\n"
        "\n"
        "def f(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"keyword_only_args should accept `def f(*, x: int)`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_keyword_only_args_accepts_dunder_with_positional_args(*, tmp_path: Path) -> None:
    """Dunder methods are exempt from the `*` separator rule.

    Python's call protocol fixes dunder signatures positionally
    (`__init__(self, ...)`, `__eq__(self, other)`, etc.). The
    rule explicitly exempts these per spec line 2086 ("Exempts
    Python-mandated dunder signatures").

    Fixture: a livespec module with `def __init__(self) -> None`
    inside a class body (or as a free function — the AST shape
    is the same `__name__` predicate). The check must accept
    these patterns.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "dunder_ok.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["Foo"]\n'
        "\n"
        "\n"
        "class Foo:\n"
        "    def __init__(self) -> None:\n"
        "        self.x = 0\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"keyword_only_args should accept dunder methods with positional args; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
