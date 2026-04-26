# Bootstrap status

**Current phase:** 3
**Current sub-step:** 12
**Last completed exit criterion:** phase 2
**Next action:** Phase 3 sub-step 12 — author `livespec/commands/resolve_template.py` per PROPOSAL §"Template resolution contract" (lines 1424-1500): full implementation of `--project-root <path>` (default `Path.cwd()`), `--template <value>` (v017 Q2 pre-seed flag), upward-walk on `.livespec.jsonc`, built-in-name-vs-path resolution, single-line stdout contract (resolved absolute POSIX path + `\n`), exit-code table. The wrapper supervisor calls `livespec.io.cli.parse_args` over a pure `build_parser()` factory, threads through the railway, pattern-matches the final IOResult to derive exit code. Sub-step 11 closed: ALL 10 validator triples authored (livespec_config, template_config, seed_input, sub_spec_payload, finding, doctor_findings, proposed_change_front_matter, revision_front_matter, proposal_findings, revise_input) — 30 files total (10 schemas + 10 dataclasses + 10 factory-shape validators). Each validator captures a pre-compiled fastjsonschema validator per the established pure-validate factory pattern. Phase 3 progress: errors.py + types.py + context.py + 6 io modules + 1 parse module + 30 schema/dataclass/validator files = 41 files committed; 5 commands + doctor (orchestrator + 8 check modules) + 6 SKILL.md prose + 4 livespec-template prompts + exit-criterion test remain.
**Last updated:** 2026-04-26T09:35:23Z
**Last commit:** 4d36589
