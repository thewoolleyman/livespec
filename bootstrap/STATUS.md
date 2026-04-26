# Bootstrap status

**Current phase:** 2
**Current sub-step:** 8
**Last completed exit criterion:** phase 1
**Next action:** Begin Phase 2 sub-step 8 — amend `just bootstrap` (authored in Phase 1 as a placeholder) to append the defensive symlink step `ln -sfn ../.claude-plugin/skills .claude/skills` per Phase 2 plan lines 999-1004. Safe to run now that `.claude-plugin/skills/` exists. (`lefthook install` is NOT yet part of `just bootstrap` — that step lands at Phase 5 per the Phase 1 `just bootstrap` note.) Sub-step 7 complete (this commit): `.claude-plugin/specification-templates/{livespec,minimal}/` authored at bootstrap-minimum scaffolding per v018 Q1-Option-A — 14 files total (livespec: template.json + livespec-nlspec-spec.md verbatim copy + 5 prompt stubs including the v020 Q2 pre-seed-dialogue scaffolding in seed.md + doctor-llm-subjective-checks.md stub + specification-template/.gitkeep; minimal: template.json with spec_root: "./" + 4 prompt stubs carrying placeholder `<!-- LIVESPEC-MOCK-DELIMITER:... -->` markers + specification-template/.gitkeep). Final delimiter format and full template content are Phase 7 work.
**Last updated:** 2026-04-26T08:04:48Z
**Last commit:** 90e79dc
