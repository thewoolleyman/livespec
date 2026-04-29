"""livespec.doctor.static.proposed_change_topic_format — filename canonical-format check.

Verifies that every file in the working
`<spec-root>/proposed_changes/` directory has a filename
conforming to the canonical `<topic>.md` form. Per PROPOSAL.md
§"`doctor` → Static-phase checks" lines 2721-2723 and Plan
§"Phase 3" line 1481, this is the eighth (and final) Phase-3
minimum-subset check.

Per PROPOSAL.md §"Topic canonicalization (v015 O3)" lines 2162-
2173, the canonical topic format is:

- lowercase
- `[a-z0-9-]+` (every run of non-`[a-z0-9]` collapsed to a
  single hyphen by the producer)
- no leading or trailing hyphens
- max 64 characters
- non-empty

The topic regex `^[a-z0-9](-?[a-z0-9])*$` enforces all but the
length cap and non-emptiness (which the structural anchors
guarantee). The 64-char limit is structurally satisfied by the
canonicalization pipeline at the producer side; the
failure-path test that pins the length-limit branch lands when
a malformed-filename test forces it.

Under v014 N6 collision disambiguation, the filename stem MAY
include a `-N` suffix (e.g., `foo-2.md`). The `-N` suffix is
just digits + a single hyphen, both of which fit within
`[a-z0-9-]`, so the same regex matches both bare topics and
`-N`-suffixed variants — no special-case branch needed.

Per PROPOSAL.md line 2722, the check scope is the **working**
directory (`<spec-root>/proposed_changes/`), NOT history. After
a successful `revise`, the working directory is empty of
in-flight proposals (only the skill-owned `README.md` persists,
per PROPOSAL.md lines 2450-2452); the check has zero
proposed-change files to validate at that state, which
satisfies the check vacuously.

The skill-owned `README.md` (PROPOSAL.md lines 992-994) is the
one fixed-name entity that intentionally lives in the working
directory. It does NOT match the canonical topic format
(uppercase letters), but it is also NOT a proposed-change file.
The check excludes `README.md` literally — implementer-derived
correctness from PROPOSAL line 2452's "skill-owned ...
persists" clause and the check description's intent to validate
*proposed-change* filenames, not the skill-owned README.

v032 TDD redo cycle 28: minimal authoring under outside-in
consumer pressure. The cycle-28 test seeds a livespec-template
tree (which produces only the skill-owned `README.md` in the
working `<spec-root>/proposed_changes/`) and asserts a `pass`
Finding. With zero proposed-change files (after exclusion), the
check trivially passes. When a `propose-change` integration
test populates the working directory with `<topic>.md` files,
the regex meaningfully validates each filename.

Out of cycle-28 scope (deferred per outside-in walking direction,
each driven by a specific test):

- Failure-path Findings naming each non-conforming filename:
  the `fail` branch is structurally present but no
  failure-path test pins the message shape yet.
- Length-limit (64-char) failure branch: structurally satisfied
  by canonicalization on the producer side; lands when a test
  exercises a too-long filename.
- Sub-spec iteration: this check is uniform across spec trees
  per PROPOSAL.md §"Per-tree check applicability" — runs
  unconditionally, no main-tree-only restriction. Sub-spec
  coverage lands when orchestrator iteration drives it.
- Bootstrap lenience (v014 N3) for `template_load_status`.

`spec_root` is hardcoded to `"SPECIFICATION"` per the `livespec`
template's default; data-driven `spec_root` resolution lands
when a `minimal`-template test or sub-spec test forces it (same
transitional collapse as cycles 21-27).
"""

from __future__ import annotations

import re

from livespec.context import DoctorContext
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "proposed-change-topic-format"

_TOPIC_FILENAME_RE = re.compile(r"^[a-z0-9](-?[a-z0-9])*\.md$")
_SKILL_OWNED_README = "README.md"


def run(*, ctx: DoctorContext) -> Finding:
    proposed_changes_dir = (
        ctx.project_root / "SPECIFICATION" / "proposed_changes"
    )
    if not proposed_changes_dir.is_dir():
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message=(
                "no working <spec-root>/proposed_changes/ directory; "
                "topic-format vacuously satisfied"
            ),
            path=None,
            line=None,
            spec_root="SPECIFICATION",
        )
    nonconforming: list[str] = []
    validated_count = 0
    for path in sorted(proposed_changes_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name == _SKILL_OWNED_README:
            continue
        if _TOPIC_FILENAME_RE.match(path.name) is None:
            nonconforming.append(path.name)
        else:
            validated_count += 1
    if not nonconforming:
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message=(
                f"all {validated_count} proposed-change filename(s) under "
                f"<spec-root>/proposed_changes/ conform to <topic>.md"
            ),
            path=None,
            line=None,
            spec_root="SPECIFICATION",
        )
    return Finding(
        check_id=f"doctor-{SLUG}",
        status="fail",
        message=(
            f"{len(nonconforming)} non-conforming filename(s) under "
            f"<spec-root>/proposed_changes/: " + ", ".join(nonconforming)
        ),
        path=None,
        line=None,
        spec_root="SPECIFICATION",
    )
