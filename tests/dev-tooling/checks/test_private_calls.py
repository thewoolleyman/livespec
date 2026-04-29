"""Outside-in test for `dev-tooling/checks/private_calls.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2076 the
`check-private-calls` rule reads:

    AST: no cross-module calls to `_`-prefixed functions defined
    elsewhere.

The convention is that a single-leading-underscore prefix on a
function name marks it private to the defining module; any
cross-module reference to such a name is a violation. The rule
pairs with ruff `SLF` (which catches `_`-prefixed *attribute*
access on instances) — the AST check covers the function-call
import surface that `SLF` does not.

This module holds the OUTERMOST behavioral test for that
contract. Each cycle pins one specific violation pattern;
cycle 33 pins the canonical pattern: module B imports `_helper`
from module A by name (`from a import _helper`) and calls it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PRIVATE_CALLS = _REPO_ROOT / "dev-tooling" / "checks" / "private_calls.py"


def test_private_calls_rejects_cross_module_import_of_private_name(*, tmp_path: Path) -> None:
    """Importing a `_`-prefixed name from another module is rejected.

    Fixture: a synthetic project root with two modules under
    `.claude-plugin/scripts/livespec/`:

        producer.py  — defines `def _helper() -> int: return 1`.
        consumer.py  — `from livespec.producer import _helper`
                       and calls it inside `public_main()`.

    The check, invoked with `cwd=tmp_path`, must walk the
    in-scope trees, detect the cross-module `_helper` import
    (a violation of the
    no-cross-module-`_`-prefixed-call rule), exit non-zero,
    and surface the offending module path
    (`.claude-plugin/scripts/livespec/consumer.py`) in its
    diagnostic so the developer can locate the file.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "producer.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def _helper() -> int:\n"
        "    return 1\n",
        encoding="utf-8",
    )
    (package_dir / "consumer.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec.producer import _helper\n"
        "\n"
        "__all__: list[str] = ['public_main']\n"
        "\n"
        "\n"
        "def public_main() -> int:\n"
        "    return _helper()\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PRIVATE_CALLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"private_calls should reject cross-module `_helper` import with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/consumer.py"
    assert expected_path in combined, (
        f"private_calls diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_private_calls_accepts_intra_module_use_of_private_name(*, tmp_path: Path) -> None:
    """A `_`-prefixed function called within its OWN module is accepted.

    The intra-module case is the legitimate `_`-prefix pattern:
    private helpers belong inside the defining module and may be
    freely called from any function in that same module. The
    fixture has `producer.py` defining `_helper` and a public
    `entry()` that calls it directly — no cross-module reference.
    The check must walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "producer.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = ['entry']\n"
        "\n"
        "\n"
        "def _helper() -> int:\n"
        "    return 1\n"
        "\n"
        "\n"
        "def entry() -> int:\n"
        "    return _helper()\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PRIVATE_CALLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"private_calls should accept intra-module `_helper` use with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
