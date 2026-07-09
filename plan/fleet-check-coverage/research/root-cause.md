# Root cause — fleet-check-coverage

Durable finding behind the `fleet-check-coverage` thread. Read this and
`design.md` before acting; the executable next step lives in `../handoff.md`.

## The trigger

A `dispatcher.py` of **2,616 physical lines** exists at
`livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/dispatcher.py`,
despite the fleet shipping a per-file logical-line ceiling — the shared
`file_lloc` check (soft-warn at 200 LLOC, hard-fail at 250). It is not alone:
`_dispatcher_plan.py` (1484), `_dispatcher_reflector_oob.py` (1245),
`_beads_client.py` (781), and `store.py` (775) are all far over the hard
ceiling. None ever tripped the gate.

## Why the gate is blind — two compounding faults

**Fault 1 — `file_lloc` hardcodes its coverage.** The check counts logical lines
correctly (it excludes blank lines, comment-only lines, and docstrings) and
enforces the 200/250 two-tier policy correctly. But its `_COVERED_TREES` is a
hardcoded tuple — `.claude-plugin/scripts/livespec`,
`.claude-plugin/scripts/bin`, `dev-tooling` — and it never calls `load_config`.
So it only ever walks a directory literally named `livespec`.

**Fault 2 — that tree does not exist in non-`livespec`-named repos.** The
orchestrator's product package is `livespec_orchestrator_beads_fabro/`, not
`livespec/`. The check hits `if not root.is_dir(): continue`, walks zero files,
and exits 0. `dispatcher.py` is never opened. **A scan that scanned nothing
reported green.**

## The bigger blast radius — not a `file_lloc`-only bug

Every OTHER structural check resolves its trees from the consumer's
`[tool.livespec_dev_tooling]` block via `load_config`.
`livespec-orchestrator-beads-fabro`'s block restates **core's** layout verbatim
(`source_trees = [".claude-plugin/scripts/livespec"]`, `covered_trees` = same,
etc.) to dodge the "empty-baseline flip" its own pyproject comment documents.
That `livespec/` directory does not exist there either. So keyword-only-args,
no-inheritance, no-write-direct, coverage pairings — the whole family — walk an
empty tree and pass vacuously. **The orchestrator's entire product codebase is
outside every structural check.** `livespec-console-beads-fabro` (also a
non-`livespec` package name) almost certainly shares the class; verify in
Phase 0.

## Why core stayed honest — only for `file_lloc`, NOT the whole suite

**For `file_lloc`:** in livespec CORE the product code genuinely lives in
`.claude-plugin/scripts/livespec/`, so the hardcoded `_COVERED_TREES` tree matches
and the check works as intended. That defect is invisible from core — it only
manifests in a repo whose package directory is not named `livespec`. That is why the
LLOC blindness went unnoticed: the dogfood hub is the one repo where THAT bug cannot
bite.

**Correction (2026-07-09) — core was NOT honest on the seven config-driven checks.**
The "core stayed honest" framing holds ONLY for `file_lloc`'s hardcoded tree. For the
SEVEN `config:source_trees` checks (`all_declared`, `assert_never_exhaustiveness`,
`global_writes`, `keyword_only_args`, `match_keyword_only`, `no_inheritance`,
`private_calls`), core's `[tool.livespec_dev_tooling]` block is PRESENT but OMITS
`source_trees`, so `load_config` returns effective `config.source_trees = ()` — a
present block with an omitted key defaults empty; it does NOT fall back to
`_livespec_core_config()`, which fires only when the block is ABSENT. So those 7
checks scanned ZERO first-party `.py` on core too — core was ALSO fail-open on them,
the SAME bug class as the orchestrator (proven by running v0.34.2 `no_inheritance`
against core → scanned nothing, exit 0). The "core stayed honest" story was true only
for the LLOC ceiling, not for the whole structural suite.

## The disease, named

Coverage is an **allowlist that fails open.** Whether hardcoded (`file_lloc`) or
per-repo config (everything else), the set of files a check inspects is an
enumerated list that must be hand-maintained per repo; when it is wrong — a
renamed package, a new top-level directory, a copy-pasted block — the check
silently inspects nothing and reports success. Correcting the lists is the
band-aid (it re-arms the same trap the next time a directory moves). The fix is
to invert the model so coverage is DERIVED from the filesystem and checks FAIL
CLOSED when they cover nothing. See `design.md`.

## Reproduce

```sh
# The over-ceiling file the gate never saw:
wc -l /data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/dispatcher.py

# The hardcoded covered trees (no load_config):
python3 - <<'PY'
import inspect, livespec_dev_tooling.checks.file_lloc as m
print([l for l in inspect.getsource(m).splitlines() if "_COVERED_TREES" in l or "scripts" in l][:6])
PY

# The tree the check walks does not exist in the orchestrator repo:
test -d /data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec \
  && echo EXISTS || echo "MISSING -> check no-ops green"

# Run the check in the orchestrator repo and watch it pass while dispatcher.py is huge:
( cd /data/projects/livespec-orchestrator-beads-fabro && just check-file-lloc; echo "exit=$?" )
```
