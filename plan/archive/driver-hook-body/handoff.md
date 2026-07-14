# Handoff — driver-hook-body ✅ COMPLETE (2026-07-13)

The **driver-hook-body** thread is **DONE**. Epic `livespec-9z8h` is CLOSED
(completed). Both Driver plugins now ship importable `main() -> int` hooks with
real per-file coverage, co-designed with byte-identity single-sourcing of the
neutral `no_shadow_ledger.py` and full aggregate/coverage/types CI parity across
both Drivers. Status is authoritative in the ledger — `bd -C /data/projects/livespec
show livespec-9z8h` (via `/usr/local/bin/with-livespec-env.sh -- bd …`).

## What shipped (all 9 slices merged + live-exercised — master CI green on each)

| Slice | Repo | Landing | Release |
|---|---|---|---|
| S1 `livespec-pxj9` | `livespec` | core `contracts.md` §"Driver-shipped hooks" amended (permit `.py`, importable-`main()` SHOULD, byte-identity narrowed to the neutral body) — revise v164, PR #1181 | — |
| S2 `livespec-8zxu` | `livespec-dev-tooling` | `CANONICAL_NO_SHADOW_LEDGER_BODY` + Verifier + installer + `neutral_hook_body_path` role key — PR #367/#369 | v0.44.0 |
| S3+S5 `livespec-nj7d`+`livespec-2ua9` | `livespec-driver-claude` | hooks `.sh`→`.py` importable+fail-open, `no_shadow_ledger.py` canonical byte-identical, own-spec ratified (Fable NO-BLOCKERS, history/v005), 100% hook coverage, full CI parity — combined PR #161 | 0.2.3 |
| S4 `livespec-8wea` | `livespec-driver-codex` | Codex hooks importable — PR #136 | — |
| S6 `livespec-vuy3` | `livespec-driver-codex` | Codex full CI parity — PR #141 | — |
| S7 `livespec-9z8h.1` | `livespec` | core adopt dev-tooling v0.45.0 (+CI job, orchestrator pin) — PR #1197 | 0.10.3 |
| S8 `livespec-9z8h.2` | `livespec-orchestrator-git-jsonl` | adopt v0.45.0 (cross-repo backstop) — PR #271 | — |
| S9 `livespec-9z8h.3` | `livespec-dev-tooling` | `check-skill-invocation-paths` Driver-aware (auto-detect `$LIVESPEC_CORE_ROOT` model) — PR #377 | v0.46.1 |

**Scope grew from the planned 4 repos to 6** as two things surfaced during
execution (both maintainer-approved):

- **S7 + S8**: adopting the S2 canonical check in core activated core's
  `doctor-wiring-completeness-cross-repo` backstop, which required core's one
  lagging `cross_repo_targets` sibling (`livespec-orchestrator-git-jsonl`) to
  adopt v0.45.0 too. Blast radius was verified BOUNDED (git-jsonl has no
  `cross_repo_targets` → no cascade).
- **S9**: freshness bumps wired canonical checks into `livespec-driver-claude`'s
  justfile ahead of the work, leaving its LOCAL `just check` red (masked CI-green
  by a narrower matrix). One, `check-skill-invocation-paths`, was structurally
  incompatible with the Driver's `$LIVESPEC_CORE_ROOT` SKILL.md invocation model.
  Maintainer chose "fix the gate" (option A) → dev-tooling made the check
  Driver-aware. S3+S5 then landed as ONE combined PR (neither could push green
  alone).

## Follow-ups filed (NOT part of this epic — separate items)

- `livespec-dev-tooling-u0x` — bump-pin/`justfile-canonical-reconcile` can wire a
  canonical check the consumer's PINNED dev-tooling lacks (pin-skew), AND
  canonical-check adoption needs HOST-SIDE CI-job + backstop-ordered merges the
  freshness bot can't do → recurring red freshness PRs.
- `livespec-dev-tooling-30g` — `red_green_replay._IMPL_PREFIXES` omits
  `.claude-plugin/hooks/`, so Driver hook `.py` can't use the Red→Green pair shape
  (falls back to the first-class `TDD-Suite-Green-*` shape; enhancement, not a bug).

## Open, UNOWNED, separate concern (surfaced, deliberately not absorbed)

dev-tooling **v0.46.0** (from parallel work) added a NEW canonical check
`local_memory_drift_audit`, repeating the same fleet-wide adoption obligation:
red freshness PRs `livespec#1199` and `livespec-orchestrator-git-jsonl#273` need
the same "cherry-pick bump + add CI job + ordered merge" treatment S7/S8 gave
v0.45.0. Separate, likely parallel-owned — see `livespec-dev-tooling-u0x` for the
systemic root cause.

## Golden rules (retained for reference)

- Status is READ live from the ledger, never stored here.
- Independent Fable review before every spec ratification (S1, S3 own-spec: both
  NO-BLOCKERS).
- HOST-SIDE workflow edits use maintainer creds; the fleet auto-merges on green
  (`app/livespec-pr-bot` re-enables auto-merge even after `--disable-auto`) →
  review-the-merged-commit + fix-forward is the operative model.

**No resume action — thread complete.** Any further work rides the separate
follow-up items above, not this thread.
