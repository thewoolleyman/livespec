# critique-fix v028 → v029 revision

## Origin

Phase 4 sub-step 13 implementation work surfaced two literal-text
gaps in PROPOSAL.md's `dev-tooling/checks/` directory listing
(lines 3496-3520):

1. **Five check filenames are missing from the listing.** The
   justfile (and Phase 4 plan §"Phase 4 — Developer tooling
   enforcement scripts" lines 1411-1446) reference checks that
   are not enumerated in PROPOSAL.md:
   - `heading_coverage.py` (planned + present in justfile)
   - `vendor_manifest.py` (planned + present in justfile)
   - `check_tools.py` (meta check; present in justfile)
   - `check_mutation.py` (release-gate; present in justfile)
   - `rop_pipeline_shape.py` (newly authored at Phase 4
     sub-step 13 to enforce the new ROP pipeline shape rule)

2. **The `keyword_only_args.py` annotation is incomplete.** The
   parenthetical reads "v011 K4 + v012 L4: also verifies
   frozen=True + slots=True on @dataclass" but omits
   `kw_only=True` — which is the third member of the strict-
   dataclass triple per style doc lines 1311-1320 + the
   implementation in `dev-tooling/checks/keyword_only_args.py`
   (which enforces the full triple `frozen=True, kw_only=True,
   slots=True`). The triple is named in the plan
   (`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` line 1426) and
   in style doc; the PROPOSAL annotation drifted to a two-of-
   three subset.

Phase 4 sub-step 13 also added a new rule §"ROP pipeline shape"
to the style doc (single public method per `@rop_pipeline`-
decorated class). PROPOSAL.md does not duplicate style-doc rule
text — the directory listing's `rop_pipeline_shape.py` entry IS
the PROPOSAL-level acknowledgement; the style doc carries the
rule text.

This is Case A (PROPOSAL.md drift) auto-blocking per the
bootstrap skill rule, requiring a v029 PROPOSAL.md snapshot.

## Decisions captured in v029

### D1 — Add five missing check filenames to PROPOSAL.md `dev-tooling/checks/` directory listing

**Decision.** Insert the five missing filenames at the
appropriate alphabetical / topical positions in the listing,
each with a brief annotation matching the established convention
(check name + short rationale or version reference).

**Old text (PROPOSAL.md lines 3496-3520, the
`dev-tooling/checks/` directory listing block).**

```
├── dev-tooling/
│   └── checks/                                (...)
│       ├── file_lloc.py
│       ├── private_calls.py
│       ├── global_writes.py
│       ├── supervisor_discipline.py
│       ├── no_raise_outside_io.py             (...)
│       ├── no_except_outside_io.py
│       ├── public_api_result_typed.py         (...)
│       ├── main_guard.py
│       ├── wrapper_shape.py
│       ├── schema_dataclass_pairing.py
│       ├── keyword_only_args.py               (v011 K4 + v012 L4: also verifies frozen=True + slots=True on @dataclass)
│       ├── match_keyword_only.py              (v011 K4)
│       ├── no_inheritance.py                  (v012 L5)
│       ├── assert_never_exhaustiveness.py     (v012 L7)
│       ├── newtype_domain_primitives.py       (v012 L8)
│       ├── all_declared.py                    (v012 L9)
│       ├── no_write_direct.py                 (v012 L10)
│       ├── pbt_coverage_pure_modules.py       (v012 L12)
│       ├── claude_md_coverage.py
│       ├── no_direct_tool_invocation.py
│       └── no_todo_registry.py                 (v013 M8; release-gate only, not in `just check`)
```

**New text:**

```
├── dev-tooling/
│   └── checks/                                (...)
│       ├── file_lloc.py
│       ├── private_calls.py
│       ├── global_writes.py
│       ├── supervisor_discipline.py
│       ├── rop_pipeline_shape.py              (v029 D1: single public method per @rop_pipeline-decorated class; encodes the Command / Use Case Interactor lineage at the class level)
│       ├── no_raise_outside_io.py             (...)
│       ├── no_except_outside_io.py
│       ├── public_api_result_typed.py         (...)
│       ├── main_guard.py
│       ├── wrapper_shape.py
│       ├── schema_dataclass_pairing.py
│       ├── keyword_only_args.py               (v011 K4 + v012 L4: also verifies frozen=True + kw_only=True + slots=True on @dataclass)
│       ├── match_keyword_only.py              (v011 K4)
│       ├── no_inheritance.py                  (v012 L5)
│       ├── assert_never_exhaustiveness.py     (v012 L7)
│       ├── newtype_domain_primitives.py       (v012 L8)
│       ├── all_declared.py                    (v012 L9)
│       ├── no_write_direct.py                 (v012 L10)
│       ├── pbt_coverage_pure_modules.py       (v012 L12)
│       ├── claude_md_coverage.py
│       ├── no_direct_tool_invocation.py
│       ├── no_todo_registry.py                 (v013 M8; release-gate only, not in `just check`)
│       ├── heading_coverage.py                (validates every `##` heading in every spec tree has a matching `tests/heading-coverage.json` entry whose `spec_root` field matches; tolerates empty array pre-Phase-6)
│       ├── vendor_manifest.py                 (validates `.vendor.jsonc` schema-conformance: every entry has a non-empty `upstream_url`, non-empty `upstream_ref`, parseable-ISO `vendored_at`; `shim: true` flag present on `jsoncomment` per v026 D1 and absent on every other entry)
│       ├── check_tools.py                     (meta check verifying every dev-tooling tool referenced in justfile is reachable on PATH or via uv-managed dependency)
│       └── check_mutation.py                  (v013 M3 release-gate; ratchet-with-ceiling against `.mutmut-baseline.json`, capped at 80%; not in `just check`)
```

**Rationale.** The directory listing serves as PROPOSAL-level
inventory of the enforcement-suite surface. Drift between the
listing and the actual `dev-tooling/checks/` contents (or the
justfile's `check-*` targets) breaks PROPOSAL.md's role as the
authoritative spec — agents reading PROPOSAL.md to understand
the enforcement surface would miss five checks. The listing is
re-aligned to enumerate every authored or planned check, with
the same parenthetical-annotation convention used for existing
entries. `rop_pipeline_shape.py` is placed adjacent to
`supervisor_discipline.py` because both are class-level
discipline checks (one for the supervisor pattern, one for the
ROP pipeline pattern). `heading_coverage.py`, `vendor_manifest.py`,
`check_tools.py`, and `check_mutation.py` are placed at the end
of the listing because they post-date the original v011/v012
ordering and are naturally trailing entries.

**Source-doc impact list.**

- PROPOSAL.md lines 3496-3520 — single Edit replacing the
  directory-listing block with the corrected enumeration.
- No companion-doc impact: the style doc, plan, and justfile
  ALREADY enumerate these checks; PROPOSAL was the lone laggard.
- No deferred-items impact: the missing entries are purely
  enumeration drift; no v1 contract or v2+ extensibility shield
  is affected.

### D2 — Codify the `keyword_only_args.py` annotation's full triple

**Decision.** Update the parenthetical annotation to enumerate
all three triple members (`frozen=True + kw_only=True +
slots=True`), matching the style doc text + the actual check
implementation. Folded into D1's directory-listing replacement
above.

**Rationale.** The two-of-three subset annotation drifted from
the canonical full triple at style doc lines 1311-1320 and from
the implementation in `dev-tooling/checks/keyword_only_args.py`
(which enforces all three keyword args). The fix is purely
literal-text alignment — the rule and its implementation already
agree; only the PROPOSAL annotation was out of step.

**Source-doc impact list.** Same as D1 (folded into the same
replacement block).

## Plan-level decisions paired with v029

The plan is unversioned per the v022 rule-refactor decision; plan
edits do not enter v029's overlay record but ride in the same
commit as the v029 snapshot. Paired plan edits:

- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` §"Version basis"**
  — bump version label to v029; add decision summary for v029
  (D1 + D2: directory-listing enumeration + keyword_only_args
  triple annotation).
- **Phase 0 step 1 byte-identity check** — bump from v028 to v029.
- **Phase 0 step 2 frozen-status header literal** — bump from
  "Frozen at v028" to "Frozen at v029".
- **Execution prompt block** — bump the "Treat PROPOSAL.md vNNN as
  authoritative" line from v028 to v029.

No other plan-text edits required. The plan's Phase 4 enforcement-
script enumeration (lines 1411-1446) already lists every check
including `rop_pipeline_shape` would-have-been (the plan was
authored before the ROP pipeline shape rule landed at sub-step
13, but the listing format is open-ended and the addition rides
along with the existing prose). The plan does NOT need a Phase 4
sub-step renumbering — the new check counted as sub-step 13 in
practice; the plan's prose enumeration of "~22 enforcement
scripts" remains accurate.

Actually: the plan's Phase 4 list at line 1418-1446 enumerates
checks but does NOT list `rop_pipeline_shape.py`. Adding it to
the plan's enumeration ride alongs in the same commit:

- **Phase 4 enforcement-script enumeration (plan line 1419)** —
  insert `rop_pipeline_shape.py` adjacent to
  `supervisor_discipline.py` to match the new PROPOSAL ordering.

## Companion-doc + repo-state changes paired with v029

- `.claude-plugin/scripts/livespec/types.py` ALREADY carries the
  `rop_pipeline` decorator (added at sub-step 13).
- `dev-tooling/checks/rop_pipeline_shape.py` ALREADY exists.
- `tests/dev-tooling/checks/test_rop_pipeline_shape.py` ALREADY
  exists.
- `justfile` ALREADY carries the `check-rop-pipeline-shape`
  target + aggregate entry.
- `python-skill-script-style-requirements.md` ALREADY carries the
  new §"ROP pipeline shape" section + canonical-target-list
  entry (style doc edits ride freely with the implementation —
  not gated by halt-and-revise per the established style-doc-
  drift convention).

The PROPOSAL.md edit is therefore catch-up-only: the new rule's
existence (decorator + check + test + justfile target + style-
doc rule) precedes its PROPOSAL acknowledgement by one commit,
which is the natural order when the rule is added during Phase 4
implementation work and then captured in the snapshot record.
