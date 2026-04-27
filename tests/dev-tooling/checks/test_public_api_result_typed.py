"""Tests for dev-tooling/checks/public_api_result_typed.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import public_api_result_typed  # noqa: E402

__all__: list[str] = []


_RAILWAY_ANNOTATED_PASSES = '''"""docstring"""
from returns.result import Result

__all__: list[str] = ["my_func"]


def my_func(*, x: int) -> Result[int, ValueError]:
    return Result.from_value(x)
'''

_IORESULT_ANNOTATED_PASSES = '''"""docstring"""
from returns.io import IOResult

__all__: list[str] = ["my_func"]


def my_func(*, x: int) -> IOResult[int, ValueError]:
    raise NotImplementedError
'''

_BARE_RESULT_PASSES = '''"""docstring"""
__all__: list[str] = ["my_func"]


def my_func(*, x: int) -> Result:
    raise NotImplementedError
'''

_INT_RETURN_FAILS = '''"""docstring"""
__all__: list[str] = ["my_func"]


def my_func(*, x: int) -> int:
    return x + 1
'''

_MISSING_ANNOTATION_FAILS = '''"""docstring"""
__all__: list[str] = ["my_func"]


def my_func(*, x: int):
    return x
'''

_IMPURE_SAFE_DECORATED_PASSES = '''"""docstring"""
from returns.future import impure_safe

__all__: list[str] = ["read_thing"]


@impure_safe(exceptions=(OSError,))
def read_thing(*, path: str) -> str:
    raise NotImplementedError
'''

_BARE_IMPURE_SAFE_PASSES = '''"""docstring"""
__all__: list[str] = ["read_thing"]


@impure_safe
def read_thing(*, path: str) -> str:
    raise NotImplementedError
'''

_SAFE_DECORATED_PASSES = '''"""docstring"""
__all__: list[str] = ["maybe_parse"]


@safe(exceptions=(ValueError,))
def maybe_parse(*, text: str) -> int:
    return 0
'''

_PRIVATE_FUNCTION_NOT_CHECKED = '''"""docstring"""
__all__: list[str] = ["my_func"]


def my_func(*, x: int) -> Result:
    return _helper(x=x)


def _helper(*, x: int) -> int:
    return x + 1
'''

_NO_ALL_SKIPPED = '''"""docstring"""
def my_func(*, x: int) -> int:
    return x
'''


def _do_check(*, source: str, relative: Path) -> list[str]:
    """Run check_file against an in-memory `source` masquerading as `relative`."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        return public_api_result_typed.check_file(path=Path(f.name), relative=relative)


_LIVESPEC = Path(".claude-plugin/scripts/livespec/foo.py")
_COMMANDS = Path(".claude-plugin/scripts/livespec/commands/seed.py")
_DOCTOR_RUN_STATIC = Path(".claude-plugin/scripts/livespec/doctor/run_static.py")
_VALIDATE = Path(".claude-plugin/scripts/livespec/validate/seed_input.py")
_STRUCTLOG_FACADE = Path(".claude-plugin/scripts/livespec/io/structlog_facade.py")
_FASTJSON_FACADE = Path(".claude-plugin/scripts/livespec/io/fastjsonschema_facade.py")
_TYPES_MODULE = Path(".claude-plugin/scripts/livespec/types.py")


def test_result_annotated_passes() -> None:
    assert _do_check(source=_RAILWAY_ANNOTATED_PASSES, relative=_LIVESPEC) == []


def test_ioresult_annotated_passes() -> None:
    assert _do_check(source=_IORESULT_ANNOTATED_PASSES, relative=_LIVESPEC) == []


def test_bare_result_annotation_passes() -> None:
    assert _do_check(source=_BARE_RESULT_PASSES, relative=_LIVESPEC) == []


def test_int_return_fails() -> None:
    violations = _do_check(source=_INT_RETURN_FAILS, relative=_LIVESPEC)
    assert len(violations) == 1
    assert "returns `int`" in violations[0]


def test_missing_annotation_fails() -> None:
    violations = _do_check(source=_MISSING_ANNOTATION_FAILS, relative=_LIVESPEC)
    assert len(violations) == 1
    assert "lacks a return annotation" in violations[0]


def test_impure_safe_decorated_passes() -> None:
    assert _do_check(source=_IMPURE_SAFE_DECORATED_PASSES, relative=_LIVESPEC) == []


def test_bare_impure_safe_decorated_passes() -> None:
    assert _do_check(source=_BARE_IMPURE_SAFE_PASSES, relative=_LIVESPEC) == []


def test_safe_decorated_passes() -> None:
    assert _do_check(source=_SAFE_DECORATED_PASSES, relative=_LIVESPEC) == []


def test_private_function_not_checked() -> None:
    """Functions not in `__all__` are not subject to the rule."""
    assert _do_check(source=_PRIVATE_FUNCTION_NOT_CHECKED, relative=_LIVESPEC) == []


def test_module_without_all_silent() -> None:
    """Modules missing `__all__` are flagged by all_declared, not here."""
    assert _do_check(source=_NO_ALL_SKIPPED, relative=_LIVESPEC) == []


def test_main_in_commands_exempt() -> None:
    source = '''"""docstring"""
__all__: list[str] = ["main"]


def main(*, argv) -> int:
    return 0
'''
    assert _do_check(source=source, relative=_COMMANDS) == []


def test_main_in_doctor_run_static_exempt() -> None:
    source = '''"""docstring"""
__all__: list[str] = ["main"]


def main(*, argv) -> int:
    return 0
'''
    assert _do_check(source=source, relative=_DOCTOR_RUN_STATIC) == []


def test_main_in_other_module_not_exempt() -> None:
    """`main` is exempt only in supervisor scope; elsewhere it's a normal public function."""
    source = '''"""docstring"""
__all__: list[str] = ["main"]


def main(*, argv) -> int:
    return 0
'''
    other_module = Path(".claude-plugin/scripts/livespec/io/whatever.py")
    violations = _do_check(source=source, relative=other_module)
    assert len(violations) == 1


def test_build_parser_in_commands_exempt() -> None:
    source = '''"""docstring"""
import argparse
__all__: list[str] = ["build_parser"]


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser()
'''
    assert _do_check(source=source, relative=_COMMANDS) == []


def test_build_parser_in_doctor_run_static_exempt() -> None:
    source = '''"""docstring"""
import argparse
__all__: list[str] = ["build_parser"]


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser()
'''
    assert _do_check(source=source, relative=_DOCTOR_RUN_STATIC) == []


def test_make_validator_in_validate_exempt() -> None:
    source = '''"""docstring"""
__all__: list[str] = ["make_validator"]


def make_validator(*, fast_validator) -> "TypedValidator[str]":
    return fast_validator
'''
    assert _do_check(source=source, relative=_VALIDATE) == []


def test_get_logger_in_structlog_facade_exempt() -> None:
    source = '''"""docstring"""
__all__: list[str] = ["get_logger"]


def get_logger(*, name: str) -> "Logger":
    return None
'''
    assert _do_check(source=source, relative=_STRUCTLOG_FACADE) == []


def test_compile_schema_in_fastjson_facade_exempt() -> None:
    source = '''"""docstring"""
__all__: list[str] = ["compile_schema"]


def compile_schema(*, schema_id: str, schema) -> "Validator":
    return None
'''
    assert _do_check(source=source, relative=_FASTJSON_FACADE) == []


def test_rop_pipeline_in_types_module_exempt() -> None:
    source = '''"""docstring"""
__all__: list[str] = ["rop_pipeline"]


def rop_pipeline(cls: type) -> type:
    return cls
'''
    assert _do_check(source=source, relative=_TYPES_MODULE) == []


def test_class_in_all_not_function_skipped() -> None:
    """Names in `__all__` that resolve to classes/constants/imports are not subject."""
    source = '''"""docstring"""
__all__: list[str] = ["MyClass", "MY_CONST"]


class MyClass:
    pass


MY_CONST: int = 42
'''
    assert _do_check(source=source, relative=_LIVESPEC) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """The shipped livespec/ tree conforms to the rule with the documented exemptions."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert public_api_result_typed.main() == 0
