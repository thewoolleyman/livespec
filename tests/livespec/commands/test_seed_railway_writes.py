"""Direct railway tests for `commands/_seed_railway_writes.py`.

Covers the defensive malformed-shape branches of the idempotency
guard's target enumeration that the supervisor path cannot reach
(schema validation upstream rejects malformed `sub_specs[]` before
the railway's write stages). The guard itself — refusal on existing
targets through `seed.main()` — is covered end-to-end in
`test_seed.py`; this file exercises the private stage directly, the
same pattern `test_seed.py`'s direct `_write_sub_spec_*` tests use
for their sibling branches.
"""

from __future__ import annotations

from pathlib import Path

from livespec.commands._seed_railway_writes import _refuse_when_seed_targets_exist
from livespec.errors import PreconditionError
from livespec.schemas.dataclasses.seed_input import SeedInput
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io


def test_refuse_guard_skips_sub_spec_whose_files_is_not_a_list(
    *,
    tmp_path: Path,
) -> None:
    """A sub-spec whose `files` is not a list contributes no targets.

    The guard mirrors `_write_sub_spec_files`' defensive skip: a
    malformed `files` value is ignored rather than crashing, so the
    guard passes through Success when no well-formed target exists.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    seed_input = SeedInput(
        template="livespec",
        intent="x",
        files=[],
        sub_specs=[
            {
                "template_name": "livespec",
                "files": "not-a-list",
            },
        ],
    )
    result = _refuse_when_seed_targets_exist(
        seed_input=seed_input,
        project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success), f"expected Success, got {unwrapped}"


def test_refuse_guard_skips_non_dict_file_entry_but_refuses_on_existing_dict_entry(
    *,
    tmp_path: Path,
) -> None:
    """A non-dict `files[]` entry is skipped; a dict entry still guards.

    One loop pass covers both arms: the malformed entry contributes
    no target, while the well-formed entry pointing at an existing
    file trips the PreconditionError refusal.
    """
    project_root = tmp_path / "proj"
    existing = project_root / "SPECIFICATION" / "templates" / "livespec" / "spec.md"
    existing.parent.mkdir(parents=True)
    _ = existing.write_text("# Pre-existing sub-spec\n", encoding="utf-8")
    seed_input = SeedInput(
        template="livespec",
        intent="x",
        files=[],
        sub_specs=[
            {
                "template_name": "livespec",
                "files": [
                    "not-a-dict-entry",
                    {
                        "path": "SPECIFICATION/templates/livespec/spec.md",
                        "content": "# Overwrite attempt\n",
                    },
                ],
            },
        ],
    )
    result = _refuse_when_seed_targets_exist(
        seed_input=seed_input,
        project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Failure), f"expected Failure, got {unwrapped}"
    error = unwrapped.failure()
    assert isinstance(error, PreconditionError)
    assert "idempotency" in str(error)
    assert existing.read_text(encoding="utf-8") == "# Pre-existing sub-spec\n"
