"""Front-matter text edits for per-proposal spec-governance overrides."""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = ["write_proposal_override"]

_SPEC_ROOT = "SPECIFICATION"


def write_proposal_override(
    *,
    project_root: Path,
    proposal_stem: str,
    value: str | None,
    key: str = "ratification_review_policy",
) -> Path | str:
    """Set or clear one proposal front-matter policy override."""
    path = project_root / _SPEC_ROOT / "proposed_changes" / f"{proposal_stem}.md"
    if not path.is_file():
        return f"proposal not found: {path}"
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return "proposal front matter is missing"
    closing = text.find("\n---\n", 4)
    if closing < 0:
        return "proposal front matter is unterminated"
    front = text[4:closing]
    body = text[closing + 1 :]
    updated_front = _upsert_front_matter_value(
        front=front,
        key=key,
        value=value,
    )
    updated = f"---\n{updated_front}{body}"
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    _ = temp_path.write_text(updated, encoding="utf-8")
    _ = temp_path.replace(path)
    return path.relative_to(project_root)


def _upsert_front_matter_value(
    *,
    front: str,
    key: str,
    value: str | None,
) -> str:
    lines = front.splitlines()
    replacement = None if value is None else f"{key}: {value}"
    out: list[str] = []
    seen = False
    for line in lines:
        if line.startswith(f"{key}:"):
            seen = True
            if replacement is not None:
                out.append(replacement)
        else:
            out.append(line)
    if not seen and replacement is not None:
        out.append(replacement)
    return "\n".join(out) + "\n"
