# shipped-hook-seam-hardening — READY TO EXECUTE. Two independent children, one ordering constraint.

**Read this whole file before acting.** Planning is done. Status is READ from the ledgers (`bd`),
never stored here. Epic: `livespec-hvtc` (livespec tenant).

Both children are residue of ONE event: the `livespec-driver-claude` shipped-hook packaging
defect fixed by PR #213 (v0.4.1). Neither was in scope for that PR; both were open at merge.

## ⛔ Guards

- **Do NOT re-fix PR #213.** It is merged, released as v0.4.1, and independently verified
  (28/28 against a simulated install cache; `just check` green; its own regression test confirmed
  to fail 19/21 against the pre-fix hooks, so it genuinely bites). Nothing here reopens it.
- **Do NOT touch `.claude-plugin/hooks/no_shadow_ledger.py`.** Its body ships BYTE-IDENTICALLY
  across both Drivers per livespec `contracts.md` §"Driver-shipped hooks". Neither child needs it.
- **Child 1 is BLOCKED on `livespec-driver-claude-ob3`** (see Ordering). Starting it early
  guarantees rework.
- Never run a bare `tmux kill-server`, `pkill … tmux`, or `killall tmux`. This whole thread exists
  because a guard against exactly that silently stopped working.

## Why these two are one thread

They are NOT the same work — two repos, two subsystems, two independent fixes. They are grouped
because they share one root event and one lesson: **a safety hook that fails silently, and the
commit gate that should have caught it and structurally could not.** Child 2 is the systemic half;
Child 1 is the residue. Close both or the lesson is half-learned.

## Background — the originating defect (FIXED; context only)

`livespec-driver-claude` `b73260e` vendored dry-python `returns` at REPO-ROOT `_vendor/`, outside
`.claude-plugin/` — the plugin bundle root. The installer copies only `.claude-plugin/`, so shipped
hooks ran under bare system `python3` with no `returns` importable. The import sat at MODULE SCOPE,
outside `main()`'s fail-open `try`, so it could not be caught.

The severity was not the visible traceback. `tmux_fleet_guard.py` scored **0/15** on a hazard
corpus in the installed cache. A PreToolUse guard that crashes emits no decision, and no decision
**ALLOWS** the command — the guard silently stopped guarding, which is implicated in the repeated
fleet-wide tmux kills of 2026-07-19. The Stop-hook traceback users actually saw was the mild half.

## Ordering (the one real constraint)

```
Child 2 (livespec-dev-tooling-kfp)  ──> independent, start ANY TIME. Do this FIRST.
Child 1 (livespec-driver-claude-c90) ──> BLOCKED until livespec-driver-claude-ob3 lands.
```

`ob3` (hooks ROP remediation, currently `acceptance`) deletes the `_read_stdin`/`_write_stdout`
wrappers and the inert `_ = read_io` ceremony, which removes MOST of Child 1's call sites. The
surviving `.value_or(None)` calls keep the divergence alive, so Child 1 shrinks but does not close.

Do Child 2 first for a second reason: it repairs the gate that should police Child 1's own commit.
Bump `livespec-driver-claude`'s `livespec-dev-tooling` pin after Child 2 releases, then do Child 1
and confirm its commit completes a real Red→Green amend. That turns Child 1 into the live proof
that Child 2 worked.

## Child 2 — `livespec-dev-tooling-kfp` (P1) — do first

`checks/red_green_replay.py:125` hardcodes `_IMPL_PREFIXES` instead of reading the consumer's
declared layout from `load_config`, contradicting the library's own stated convention that
layout-dependent paths come from `config.py`.

`livespec-driver-claude`'s only source tree is `.claude-plugin/hooks/`, which matches no entry, so
`_classify_staged` (:153) always returns empty `impl_paths` there. A `feat:`/`fix:` subject then
routes every invocation to Red mode, which rejects a passing test — the Red→Green amend can never
complete. Evidence: `b73260e` (which INTRODUCED the defect) and PR #213 (which fixed it) BOTH carry
`TDD-Red-*` trailers with no Green pair.

**Scope is narrower than it looks.** The tuple already carries `"livespec/"`, so sibling
`livespec-driver-codex` (hooks at `livespec/hooks/`) is gated BY ACCIDENT, not by declaration.
`livespec-driver-claude` is the only repo falling through today. The durable problem is the
hardcoding: the next consumer with a novel layout loses the gate the same silent way, while CI
reports green. A silently-disabled gate is worse than an absent one.

Fix: derive from `config.source_tree_prefixes`, keeping the historical tuple as the block-absent
fallback (and the legacy `livespec/` / `bin/` entries, which tmp_path fixtures synthesize).
`livespec-driver-claude` already declares the correct value, so no consumer-side change is needed
to start working. Also check whether `red_leg_scope.py` shares the assumption.

## Child 1 — `livespec-driver-claude-c90` (P2) — after `ob3`

`.claude-plugin/hooks/_result.py` declares `value_or` KEYWORD-ONLY (`*, default`); the dry-python
container it substitutes for takes it POSITIONALLY (`default_value`). Self-consistent today: shipped
hooks use the keyword form, the never-shipped `.claude/hooks/livespec_footgun_guard.py` uses the
positional form against real vendored `returns`. No live defect.

The hazard is the failure mode if they cross. Moving a helper between the two hook trees raises
`TypeError` on the `value_or` call, INSIDE `main()`'s boundary `try/except`, which swallows it and
returns 0. The hook exits clean, emits nothing, denies nothing — the same end state as the defect
just fixed, minus the traceback that made that one findable.

Fix: make the shim a true positional drop-in and update the three call sites, so one convention
holds across both trees and the shim can be swapped for real `returns` without silent failure.

## Definition of done for the epic

- Both children closed in their own repos.
- A `feat:`/`fix:` commit touching `.claude-plugin/hooks/*.py` in `livespec-driver-claude`
  completes a real Red→Green amend and lands with a paired Green trailer.
- A test proves the shipped shim and vendored `returns` are call-compatible across the surface the
  hooks use.
- A regression test proves a consumer whose declared source tree is ABSENT from the historical
  tuple is still gated.

## Provenance

Diagnosed and verified from session `4a0c37fe` (livespec-driver-claude), which independently
reproduced the PR #213 defect, verified the fix, and surfaced both children during review. Review
comment: https://github.com/thewoolleyman/livespec-driver-claude/pull/213#issuecomment-5014828926
