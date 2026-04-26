# Bootstrap status

**Current phase:** 3
**Current sub-step:** 2
**Last completed exit criterion:** phase 2
**Next action:** Phase 3 sub-step 2 — expand `livespec/types.py` from its Phase 2 placeholder to author all 8 canonical NewType aliases enumerated in style doc §"Domain primitives via `NewType`": `CheckId` (str), `RunId` (str), `TopicSlug` (str), `SpecRoot` (Path), `SchemaId` (str), `TemplateName` (str), `Author` (str), `VersionTag` (str). Sub-step 1 (errors.py verification) closed: traced every Phase-3 implementation surface (resolve_template, seed, propose_change/critique/revise, doctor static, validate/, parse/, io/) against the Phase 2 errors.py — every failure path maps to an existing class (collisions/idempotency/missing-template → PreconditionError; non-canonical topic / malformed payload / schema validation → ValidationError; argparse failures → UsageError; -h → HelpRequested; git absence → GitUnavailableError). No widening required; errors.py stays as authored at Phase 2.
**Last updated:** 2026-04-26T08:56:26Z
**Last commit:** 268ae05
