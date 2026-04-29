"""Outside-in test for `dev-tooling/checks/public_api_result_typed.py`.

Per `python-skill-script-style-requirements.md` line 2082:

    AST: every public function (per `__all__` declaration) returns
    `Result` or `IOResult` per annotation, OR carries a railway-
    lifting decorator that wraps the source-level annotation
    (`@impure_safe(...)` lifts to `IOResult`, `@safe(...)` lifts to
    `Result` — both recognized by name regardless of bare or
    parameterized form).

Cycle 47 pins ONE narrow violation pattern per v032 D1 one-
pattern-per-cycle: a public function (listed in `__all__`)
annotated `-> int` with no `@safe`/`@impure_safe` railway-lifting
decorator is rejected. Other failure-modes (broader return-type
shapes, the exemption list of supervisors / factories, the
`_*.py` package-private helper carve-out) are deferred to
subsequent cycles per v032 D1 — current cycle's responsibility
is the canonical primitive-int public-no-railway shape.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PUBLIC_API_RESULT_TYPED = _REPO_ROOT / "dev-tooling" / "checks" / "public_api_result_typed.py"


def test_public_api_result_typed_rejects_int_returning_public_without_railway(
    *,
    tmp_path: Path,
) -> None:
    """A public `-> int` function with no railway decorator is rejected.

    Fixture: `.claude-plugin/scripts/livespec/leaky.py` exports
    `compute` in `__all__`; `compute` is annotated `-> int` with
    no `@safe`/`@impure_safe` decorator. The check must walk the
    livespec tree, detect the bare-int public, exit non-zero,
    and surface the offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "leaky.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["compute"]\n'
        "\n"
        "\n"
        "def compute(*, x: int) -> int:\n"
        "    return x * 2\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"public_api_result_typed should reject int-returning public "
        f"with no railway decorator; got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/leaky.py"
    assert expected_path in combined, (
        f"public_api_result_typed diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_public_api_result_typed_accepts_safe_decorated_int_function(
    *,
    tmp_path: Path,
) -> None:
    """A public `-> int` function decorated with `@safe` is accepted.

    Fixture: a livespec module whose public `compute` is
    `-> int` but carries `@safe` (recognized by decorator name,
    bare or parameterized). The check must exit 0 — the railway
    lift is what the rule permits.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "lifted.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from returns.result import safe\n"
        "\n"
        '__all__: list[str] = ["compute"]\n'
        "\n"
        "\n"
        "@safe\n"
        "def compute(*, x: int) -> int:\n"
        "    return x * 2\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"public_api_result_typed should accept @safe-decorated int public; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
