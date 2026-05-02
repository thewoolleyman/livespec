"""Domain-primitive NewTypes for livespec.

Per PROPOSAL.md §"`livespec/types.py`" +
`python-skill-script-style-requirements.md` §"Skill layout":
the canonical-target check `check-newtype-domain-primitives`
(per `dev-tooling/checks/newtype_domain_primitives.py`)
requires specific field names in
`schemas/dataclasses/*.py` to use the corresponding NewType
declared here.

NewType is structural: at runtime each NewType is the
underlying `str`, so `isinstance(CheckId("x"), str)` is True
and existing code passing string literals where a NewType is
expected works unchanged. pyright (reactivated at Phase 7)
treats them as distinct nominal types; mistaking a `CheckId`
for a `SpecRoot` is caught at type-check time.
"""

from __future__ import annotations

from typing import NewType

__all__: list[str] = ["Author", "CheckId", "SpecRoot", "TemplateName", "TopicSlug"]


CheckId = NewType("CheckId", str)
SpecRoot = NewType("SpecRoot", str)
Author = NewType("Author", str)
TemplateName = NewType("TemplateName", str)
TopicSlug = NewType("TopicSlug", str)
