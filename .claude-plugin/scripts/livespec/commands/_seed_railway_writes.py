"""File-writing railway stages for the `seed` sub-command.

Extracted from `seed.py` at cycle 4e so the parent file's LLOC
stays under the 200-line ceiling enforced by `check-complexity`.
The split is purely organizational; the behavior is identical
to the inline original. The leading underscore in the filename
marks this as a private sibling module — the supervisor entry
point is `seed.py` (no underscore) which imports from here.

Stages: main-spec files, main-spec history/v001/, sub-spec
files, sub-spec history/v001/.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.seed_input import SeedInput

__all__: list[str] = [
    "_write_main_spec_files",
    "_write_main_spec_history_v001",
    "_write_sub_spec_files",
    "_write_sub_spec_history_v001",
]


# Path-shape minima — duplicated here from seed.py so this helper
# module is self-contained (no circular import). Same documented
# meaning: main-spec path is `<spec_root>/<file>` (≥ 2 parts);
# sub-spec path is `<spec_root>/templates/<template_name>/<file>`
# (≥ 4 parts).
_MIN_PARTS_MAIN_SPEC: int = 2
_MIN_PARTS_SUB_SPEC: int = 4


def _write_main_spec_files(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write each main-spec `files[]` entry to its project-root-relative path."""
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for entry in seed_input.files:
        target = project_root / entry["path"]
        text = entry["content"]
        accumulator = accumulator.bind(
            lambda _value, target=target, text=text: fs.write_text(
                path=target, text=text,
            ).map(lambda _: seed_input),
        )
    return accumulator


def _write_main_spec_history_v001(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Materialize `<spec-root>/history/v001/<spec-file>` for each main-spec entry."""
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for entry in seed_input.files:
        original_path = Path(entry["path"])
        if len(original_path.parts) < _MIN_PARTS_MAIN_SPEC:
            continue
        spec_root_name = original_path.parts[0]
        relative = Path(*original_path.parts[1:])
        target = project_root / spec_root_name / "history" / "v001" / relative
        text = entry["content"]
        accumulator = accumulator.bind(
            lambda _value, target=target, text=text: fs.write_text(
                path=target, text=text,
            ).map(lambda _: seed_input),
        )
    return accumulator


def _write_sub_spec_files(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write each sub-spec entry's `files[]` to project-root-relative paths."""
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for sub_spec in seed_input.sub_specs:
        files_list = sub_spec["files"]
        if not isinstance(files_list, list):
            continue
        for entry in files_list:
            if not isinstance(entry, dict):
                continue
            target = project_root / str(entry["path"])
            text = str(entry["content"])
            accumulator = accumulator.bind(
                lambda _value, target=target, text=text: fs.write_text(
                    path=target, text=text,
                ).map(lambda _: seed_input),
            )
    return accumulator


def _write_sub_spec_history_v001(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Materialize history/v001/ for each sub-spec tree."""
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for sub_spec in seed_input.sub_specs:
        files_list = sub_spec["files"]
        if not isinstance(files_list, list):
            continue
        for entry in files_list:
            if not isinstance(entry, dict):
                continue
            original_path = Path(str(entry["path"]))
            if len(original_path.parts) < _MIN_PARTS_SUB_SPEC:
                continue
            spec_root_parts = original_path.parts[:3]
            relative = Path(*original_path.parts[3:])
            target = (
                project_root.joinpath(*spec_root_parts)
                / "history"
                / "v001"
                / relative
            )
            text = str(entry["content"])
            accumulator = accumulator.bind(
                lambda _value, target=target, text=text: fs.write_text(
                    path=target, text=text,
                ).map(lambda _: seed_input),
            )
    return accumulator
