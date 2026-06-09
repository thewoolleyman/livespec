"""Tests for livespec.doctor.static._work_items_provider.

The shared work-item provider seam for the six cross-boundary doctor
checks. Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants", the checks acquire work-items by invoking the active
impl-plugin's `list-work-items` wrapper (resolved from
`LIVESPEC_IMPL_LIST_WORK_ITEMS` into `ctx.work_items_provider`)
rather than a direct JSONL read. This module exercises the
three-state outcome (`ProviderUnset` / `ProviderUnreachable` /
`WorkItemsIndex`), the env-var resolution, and the standardized
skip-message rendering.

The fake wrapper scripts written into `tmp_path` stand in for the
real impl-plugin wrapper: each is a tiny `python3` script that emits
a fixed payload (or exits nonzero) so the subprocess boundary is
exercised without a live work-item backend.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import _work_items_provider
from livespec.doctor.static._work_items_provider import (
    PROVIDER_ENV_VAR,
    ProviderUnreachable,
    ProviderUnset,
    WorkItemsIndex,
    load_work_items_index,
    resolve_provider_path,
    skip_message,
)
from livespec.errors import PreconditionError
from returns.io import IOFailure, IOSuccess

__all__: list[str] = []


def _write_wrapper(*, tmp_path: Path, body: str) -> Path:
    """Write a fake list-work-items wrapper script and return its path."""
    wrapper = tmp_path / "fake_wrapper.py"
    _ = wrapper.write_text(body, encoding="utf-8")
    return wrapper


def _emit_array_wrapper(*, tmp_path: Path, json_literal: str) -> Path:
    """Fake wrapper that prints a fixed JSON array literal and exits 0."""
    body = f"import sys\nsys.stdout.write({json_literal!r})\n"
    return _write_wrapper(tmp_path=tmp_path, body=body)


def _ctx(*, tmp_path: Path, provider: Path | None) -> DoctorContext:
    """Build a DoctorContext rooted at tmp_path with the given provider path."""
    project_root = tmp_path / "project"
    project_root.mkdir(exist_ok=True)
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir(exist_ok=True)
    return DoctorContext(
        project_root=project_root,
        spec_root=spec_root,
        work_items_provider=provider,
    )


def test_resolve_provider_path_returns_none_when_unset() -> None:
    """An empty env mapping yields None (no provider configured)."""
    assert resolve_provider_path(env={}) is None


def test_resolve_provider_path_returns_none_when_empty_value() -> None:
    """An explicitly empty env value yields None."""
    assert resolve_provider_path(env={PROVIDER_ENV_VAR: ""}) is None


def test_resolve_provider_path_returns_path_when_set() -> None:
    """A non-empty env value yields the corresponding Path."""
    result = resolve_provider_path(env={PROVIDER_ENV_VAR: "/abs/list_work_items.py"})
    assert result == Path("/abs/list_work_items.py")


def test_skip_message_for_unset() -> None:
    """ProviderUnset renders the 'no live work-item provider configured' narration."""
    message = skip_message(slug_prefix="demo-check", outcome=ProviderUnset())
    assert message == (
        "demo-check: no live work-item provider configured "
        f"(set {PROVIDER_ENV_VAR} to the active impl-plugin's "
        "list-work-items wrapper to enforce); check skipped"
    )


def test_skip_message_for_unreachable() -> None:
    """ProviderUnreachable renders the 'work-item store unreachable' narration."""
    message = skip_message(
        slug_prefix="demo-check",
        outcome=ProviderUnreachable(detail="wrapper exited 7"),
    )
    assert message == "demo-check: work-item store unreachable (wrapper exited 7); check skipped"


def test_load_returns_unset_when_provider_none(*, tmp_path: Path) -> None:
    """A None provider short-circuits to ProviderUnset without a subprocess."""
    ctx = _ctx(tmp_path=tmp_path, provider=None)
    assert load_work_items_index(ctx=ctx) == IOSuccess(ProviderUnset())


def test_load_returns_unreachable_when_wrapper_missing(*, tmp_path: Path) -> None:
    """A non-existent wrapper path makes `python3` exit nonzero → ProviderUnreachable."""
    ctx = _ctx(tmp_path=tmp_path, provider=tmp_path / "does_not_exist.py")
    result = load_work_items_index(ctx=ctx)
    assert result == IOSuccess(ProviderUnreachable(detail="wrapper exited 2"))


def test_load_returns_unreachable_on_subprocess_oserror(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An OSError at the subprocess boundary (e.g. python3 absent) lashes to unreachable.

    The real `python3 <missing-wrapper>` path exits nonzero rather
    than raising; this test drives the OSError-lash branch directly
    by stubbing `proc.run_subprocess` to fail on the IO track.
    """
    wrapper = _write_wrapper(tmp_path=tmp_path, body="import sys\nsys.exit(0)\n")
    ctx = _ctx(tmp_path=tmp_path, provider=wrapper)

    def _stub_run_subprocess(**_kwargs: object) -> object:
        return IOFailure(PreconditionError("proc.run_subprocess: python3 absent"))

    monkeypatch.setattr(_work_items_provider.proc, "run_subprocess", _stub_run_subprocess)
    result = load_work_items_index(ctx=ctx)
    assert result == IOSuccess(
        ProviderUnreachable(
            detail="wrapper invocation failed: proc.run_subprocess: python3 absent",
        ),
    )


def test_load_returns_unreachable_on_nonzero_exit(*, tmp_path: Path) -> None:
    """A wrapper that exits nonzero is a connection failure, not a check failure."""
    wrapper = _write_wrapper(tmp_path=tmp_path, body="import sys\nsys.exit(1)\n")
    ctx = _ctx(tmp_path=tmp_path, provider=wrapper)
    assert load_work_items_index(ctx=ctx) == IOSuccess(
        ProviderUnreachable(detail="wrapper exited 1"),
    )


def test_load_returns_unreachable_on_non_json_stdout(*, tmp_path: Path) -> None:
    """Zero-exit but non-JSON stdout is treated as unreachable."""
    wrapper = _write_wrapper(tmp_path=tmp_path, body="import sys\nsys.stdout.write('not json')\n")
    ctx = _ctx(tmp_path=tmp_path, provider=wrapper)
    assert load_work_items_index(ctx=ctx) == IOSuccess(
        ProviderUnreachable(detail="wrapper stdout is not valid JSON"),
    )


def test_load_returns_unreachable_on_non_array_json(*, tmp_path: Path) -> None:
    """Zero-exit valid JSON that is not a top-level array is treated as unreachable."""
    wrapper = _emit_array_wrapper(tmp_path=tmp_path, json_literal="{}")
    ctx = _ctx(tmp_path=tmp_path, provider=wrapper)
    assert load_work_items_index(ctx=ctx) == IOSuccess(
        ProviderUnreachable(detail="wrapper stdout is not a top-level JSON array"),
    )


def test_load_materializes_index_from_array(*, tmp_path: Path) -> None:
    """A valid JSON array materializes into a WorkItemsIndex keyed by id."""
    wrapper = _emit_array_wrapper(
        tmp_path=tmp_path,
        json_literal='[{"id": "a", "status": "open"}, {"id": "b", "status": "closed"}]',
    )
    ctx = _ctx(tmp_path=tmp_path, provider=wrapper)
    assert load_work_items_index(ctx=ctx) == IOSuccess(
        WorkItemsIndex(
            index={
                "a": {"id": "a", "status": "open"},
                "b": {"id": "b", "status": "closed"},
            },
        ),
    )


def test_load_skips_non_dict_and_idless_entries(*, tmp_path: Path) -> None:
    """Array entries that are not dicts, or lack a string id, contribute nothing."""
    wrapper = _emit_array_wrapper(
        tmp_path=tmp_path,
        json_literal='[42, {"status": "open"}, {"id": 7}, {"id": "ok"}]',
    )
    ctx = _ctx(tmp_path=tmp_path, provider=wrapper)
    assert load_work_items_index(ctx=ctx) == IOSuccess(
        WorkItemsIndex(index={"ok": {"id": "ok"}}),
    )


def test_load_last_record_per_id_wins(*, tmp_path: Path) -> None:
    """When the array carries duplicate ids, the last entry wins."""
    wrapper = _emit_array_wrapper(
        tmp_path=tmp_path,
        json_literal='[{"id": "a", "status": "open"}, {"id": "a", "status": "closed"}]',
    )
    ctx = _ctx(tmp_path=tmp_path, provider=wrapper)
    assert load_work_items_index(ctx=ctx) == IOSuccess(
        WorkItemsIndex(index={"a": {"id": "a", "status": "closed"}}),
    )


def test_provider_invocation_uses_sys_executable_compatible_python(*, tmp_path: Path) -> None:
    """The fake wrapper runs under the same interpreter family as the suite.

    Guards against the subprocess silently using a stale `python3` —
    the wrapper echoes the running executable's major version and the
    index materializes only when the subprocess actually executed.
    """
    wrapper = _write_wrapper(
        tmp_path=tmp_path,
        body=(
            "import json, sys\n"
            'sys.stdout.write(json.dumps([{"id": "v" + str(sys.version_info[0])}]))\n'
        ),
    )
    ctx = _ctx(tmp_path=tmp_path, provider=wrapper)
    expected_id = f"v{sys.version_info[0]}"
    assert load_work_items_index(ctx=ctx) == IOSuccess(
        WorkItemsIndex(index={expected_id: {"id": expected_id}}),
    )
