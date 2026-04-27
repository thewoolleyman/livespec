"""Immutable context dataclasses (railway payload).

Each sub-command's context is a frozen, keyword-only, slotted
dataclass. The triple `frozen=True, kw_only=True, slots=True` is the
canonical shape for every dataclass in `livespec/**` (enforced by
`check-keyword-only-args`):

- `frozen=True` — instances are immutable. Field reassignment raises
  `FrozenInstanceError` at runtime; pyright surfaces the same as a
  static error. Pure-function railway code cannot mutate context.
- `kw_only=True` — every field is keyword-only at construction.
  `DoctorContext(project_root=..., spec_root=...)` is the only valid
  form; positional args raise `TypeError`. Reduces site-mismatch bugs
  when fields are added.
- `slots=True` — `__slots__` is generated from field names so the
  instance has no `__dict__`. Catches typo-set assignments
  (`ctx.spec_rot = ...`) at runtime and saves memory.

Sub-command contexts EMBED `DoctorContext` as a field rather than
inheriting from it. Embedding lets the type checker narrow each
sub-command's payload independently and avoids deep inheritance
trees (`check-no-inheritance` only allows direct-parent bases from
a small allowlist; sub-command contexts have no parent).

Field annotations referencing dataclasses generated from the
JSON Schemas (LivespecConfig, SeedInput, ProposalFindings,
ReviseInput) use forward references via the `TYPE_CHECKING` block
so this module is authorable before
`livespec/schemas/dataclasses/*.py` lands. `from __future__ import
annotations` makes every annotation lazy at runtime so the
dataclass decorator reads them as strings without resolving the
referenced types — pyright still resolves them statically once the
target modules exist.

`template_name` is `str` (not the `TemplateName` NewType) per the
`check-newtype-domain-primitives` field-name keying: the canonical
NewType mapping uses field name `template`, NOT `template_name`.
The `template_name` field carries the orchestrator's per-tree
applicability marker — `"main"` for the main spec tree or the
sub-spec directory name (e.g. `"livespec"`, `"minimal"`) for each
sub-spec tree (PROPOSAL.md §"Static-phase orchestrator"; v018 Q1;
field name finalized in v021 Q1, replacing the prior binary
`template_scope: Literal["main", "sub-spec"]`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from livespec.types import Author, RunId, SpecRoot, TopicSlug

if TYPE_CHECKING:
    from livespec.schemas.dataclasses.livespec_config import LivespecConfig
    from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
    from livespec.schemas.dataclasses.revise_input import ReviseInput
    from livespec.schemas.dataclasses.seed_input import SeedInput


__all__: list[str] = [
    "CritiqueContext",
    "DoctorContext",
    "ProposeChangeContext",
    "PruneHistoryContext",
    "ReviseContext",
    "SeedContext",
]


@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorContext:
    project_root: Path
    spec_root: SpecRoot
    config: LivespecConfig
    config_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]
    template_root: Path
    template_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]
    template_name: str
    run_id: RunId
    git_head_available: bool


@dataclass(frozen=True, kw_only=True, slots=True)
class SeedContext:
    doctor: DoctorContext
    seed_input: SeedInput


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposeChangeContext:
    doctor: DoctorContext
    findings: ProposalFindings
    topic: TopicSlug


@dataclass(frozen=True, kw_only=True, slots=True)
class CritiqueContext:
    doctor: DoctorContext
    findings: ProposalFindings
    author: Author


@dataclass(frozen=True, kw_only=True, slots=True)
class ReviseContext:
    doctor: DoctorContext
    revise_input: ReviseInput
    steering_intent: str | None


@dataclass(frozen=True, kw_only=True, slots=True)
class PruneHistoryContext:
    doctor: DoctorContext
