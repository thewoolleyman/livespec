"""Outside-in test for `dev-tooling/checks/no_raise_outside_io.py` — domain-error raises confined to io/+errors.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-raise-outside-io` row), raising
of `LivespecError` subclasses (domain errors) at runtime is
restricted to `livespec/io/**` and `livespec/errors.py`.
Anywhere else under `livespec/**`, raising domain errors is
banned — pure layers return `Failure(LivespecError(...))` on
the ROP railway. Raising bug-class exceptions (TypeError,
NotImplementedError, AssertionError, etc.) is permitted
anywhere.

The known domain-error class names that count as
`LivespecError` subclasses: `LivespecError` itself,
`UsageError`, `PreconditionError`, `ValidationError`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_RAISE_OUTSIDE_IO = _REPO_ROOT / "dev-tooling" / "checks" / "no_raise_outside_io.py"


def test_no_raise_outside_io_rejects_domain_error_raise_in_pure_layer(*, tmp_path: Path) -> None:
    """A `raise ValidationError(...)` inside `livespec/parse/foo.py` fails the check.

    Fixture: a parse-layer module raises a domain error (banned
    — pure layers return Failure(...) on the railway). The
    check must walk livespec/, parse the file, detect the
    domain-error raise, exit non-zero, and surface the file
    path plus line number.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def parse_thing() -> None:\n"
        '    raise ValidationError("malformed")\n',
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_RAISE_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_raise_outside_io should reject ValidationError raise in parse/; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/parse/foo.py"
    assert expected_path in combined, (
        f"no_raise_outside_io diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_raise_outside_io_accepts_domain_error_raise_in_io_layer(*, tmp_path: Path) -> None:
    """A `raise PreconditionError(...)` inside `livespec/io/fs.py` passes (exit 0).

    Pass-case: the io/ layer is the side-effect boundary that
    legitimately raises domain errors (the impure_safe
    decorator lifts them onto the IOResult railway via
    @impure_safe(exceptions=(PreconditionError,)).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "io"
    package_dir.mkdir(parents=True)
    source = package_dir / "fs.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def read_text() -> None:\n"
        '    raise PreconditionError("missing")\n',
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_RAISE_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_raise_outside_io should accept domain-error raise in io/ with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_raise_outside_io_accepts_domain_error_raise_in_errors_module(*, tmp_path: Path) -> None:
    """A `raise LivespecError(...)` inside `livespec/errors.py` passes (exit 0).

    Pass-case: errors.py is the hierarchy definition module
    and is exempt by spec.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "errors.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def raise_test() -> None:\n"
        '    raise LivespecError("test")\n',
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_RAISE_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_raise_outside_io should accept domain-error raise in errors.py with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_raise_outside_io_accepts_bug_class_raise_in_pure_layer(*, tmp_path: Path) -> None:
    """A `raise TypeError(...)` (bug-class) in pure layer passes (exit 0).

    Pass-case: bug-class exceptions (TypeError, ValueError,
    NotImplementedError, AssertionError, etc.) are permitted
    anywhere — they propagate to the supervisor's bug-catcher.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def parse_thing() -> None:\n"
        '    raise NotImplementedError("not yet")\n'
        "\n"
        "\n"
        "def reraise() -> None:\n"
        "    try:\n"
        "        parse_thing()\n"
        "    except NotImplementedError:\n"
        "        raise\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_RAISE_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_raise_outside_io should accept bug-class raise with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_raise_outside_io_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_RAISE_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_raise_outside_io should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_raise_outside_io_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "no_raise_outside_io_for_import_test", str(_NO_RAISE_OUTSIDE_IO),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
