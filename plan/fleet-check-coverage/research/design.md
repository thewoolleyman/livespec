# Design — fleet-check-coverage

The permanent fix behind this thread. Read `root-cause.md` first for why the
current model rots; this file is the target design. The executable next step is
`../handoff.md`.

## Principle

Replace enumerated, per-repo coverage allowlists — which fail **open** (a wrong
list silently covers nothing and reports green) — with coverage **derived from
the filesystem** and checks that fail **closed** (a scan that covers nothing in
a repo that has code is an error, not a pass). Land it once in the shared
`livespec-dev-tooling` package; the existing release + `bump-pin` fan-out carries
it to every fleet repo with zero per-repo config to keep in sync.

## The file universe

The set of files every "applies to all first-party code" check inspects:

```
git ls-files '*.py'   MINUS   the exemptions below
```

`git ls-files` is "every Python file the repo tracks" — identical across every
fleet repo, needs no config, auto-covers any new file or new top-level directory
the moment it is committed, and inherits `.gitignore` for free (so `.venv/`,
`__pycache__/`, and build output never appear). Every fleet repo is a git
checkout, so the primitive is always available.

## Exemptions — the ONLY things not covered

Coverage is default-ON; you must loudly opt something OUT. Each exemption is
explicit, visible, and justified (maintainer-decided 2026-07-08):

1. **`_vendor/`** — third-party code livespec did not author. A
   naming-convention prefix (the same one every check already skips).
2. **Tests** — the repo's test tree (`tests_tree_prefix`, plus any `conftest.py`).
3. **Generated code** — files produced by a generator, identified by the **generic
   `@generated` sentinel** (RESOLVED 2026-07-08, OQ1): the `@generated` token
   recognized inside a file's NATIVE comment syntax via an extensible
   ext→comment-prefix registry (`#` for Python/shell/YAML/TOML; `//` and `/* */`
   for Rust/TS/JS/Go/C; `<!-- -->`; `--`; …), **not merely a directory name** and
   **not a per-repo glob list** (a glob list would recreate the fail-open
   allowlist). Only `.py` is wired today; the registry makes other ecosystems
   trivial, so keep all prose ecosystem-generic (never "the Python `#` comment").
   Zero `.py` carry the sentinel today — it is collision-free future-proofing (the
   one existing "DO NOT EDIT" hit, livespec-runtime `_fractional_indexing.py`, is
   a hand-maintained port that MUST stay checked).
4. **`templates/**` copier payload** (RESOLVED 2026-07-08, OQ2) — adopter-facing
   template/extension code livespec ships but does not govern; livespec imposes
   nothing on extension/template code. (Core's 2 real `.py` under
   `templates/orchestrator-plugin/.claude/hooks/` are the only instances today.)

Each repo's OWN hooks (`.claude/hooks/**`, `.claude-plugin/hooks/**`) ARE covered
(OQ2) — first-party livespec code, and the two Driver repos' entire codebase.
Anything not matching an exemption is covered. There is no catch-all bucket.

## Fail-closed guards

**Empty-walk guard.** If a check's resolved universe is empty in a repo that has
tracked first-party `.py`, that is a hard error — the exact
"walked-a-nonexistent-dir → green" bug can never recur. **Subtlety that must be
gotten right:** a repo with GENUINELY zero first-party `.py` legitimately produces
an empty universe and MUST pass — but in THIS fleet that is exactly ONE repo,
`livespec-console-beads-fabro` (0 tracked `.py`). **Correction (verified
2026-07-08):** the Driver repos are NOT codeless — `livespec-driver-claude` carries
2 first-party hook `.py` and `livespec-driver-codex` 3 (under `.claude/hooks/` /
`.claude-plugin/hooks/` / `livespec/hooks/`); their universes are NON-empty and
their hooks MUST be covered, not passed over. The guard distinguishes "no
first-party code exists here" (pass — the console) from "first-party code exists
but this check saw none of it" (fail). Getting this wrong in either direction
re-creates a silent hole (false pass) or a false alarm on the genuinely-empty
console repo.

**Partition-completeness meta-check.** The role-partition checks (io vs pure vs
commands, etc.) genuinely need semantic config — keep it. But add one guard:
every tracked first-party `.py` must be claimed by exactly one role OR a named,
visible, justified exclusion. An unclaimed file → hard error naming the file.
This makes the whole suite self-extending: drop a file into a new directory and
CI tells you to claim or exempt it — you cannot silently lose it.

Net effect: the failure mode flips from "forget a repo → silent green" to
"cover everything by default → you must loudly opt something out."

## Scope — the whole check family, on every repo

Dials to 11 (maintainer 2026-07-08). Every structural check meant to apply to
all first-party Python derives its universe from the filesystem through the
shared `iter_py_files` choke point — not just `file_lloc`. `file_lloc` stops
hardcoding `_COVERED_TREES` and routes through the same path. Role-partition
checks keep their semantic config but gain the partition guard. First deliverable
of Phase 0 is to enumerate the current dev-tooling check set and classify each as
"applies-to-all" (derive universe) or "genuinely role-scoped" (semantic config +
partition guard).

## Staged rollout — warn → burndown → fail

Landing this as a hard gate would red-out the fleet at once (dispatcher.py and
its siblings, the console repo, plus whatever drift the other checks catch).
Instead, three phases — extending the two-tier soft/hard pattern `file_lloc`
already ships (`LIVESPEC_FAIL_IF_LLOC_SOFT_WARNINGS_EXIST` already models
warn-vs-fail, flipped by CI):

- **Phase 0 — mechanism, WARN severity only.** Land derived-coverage +
  fail-closed guards + partition check in `livespec-dev-tooling`, all emitting at
  `warning` (exit 0). Release + fan-out so every repo SEES its true coverage with
  nothing going red.
- **Phase 1 — burndown, in parallel across all repos.** Each repo's warnings are
  its worklist: refactor over-ceiling files, resolve every check's findings,
  claim/exempt unclaimed files. Driven by a parallel overseer through the factory
  (`../handoff.md`), not repo-by-repo.
- **Phase 2 — flip WARN→FAIL, per-repo as each reaches clean.** A repo locks in
  its hard gate the moment it is warning-clean, so it cannot regress while slower
  repos finish. No fleet-wide big-bang flip. Critically: **no new escape hatch is
  added to achieve the flip** (per `.ai/ci-gate-discipline.md`) — the flip is
  severity, never a bypass.

## Propagation

Land once in `livespec-dev-tooling`; cut a release; the `bump-pin` fan-out
rewrites every consumer's pin AND reconciles each consumer's `check:` canonical
block so the new/changed checks are actually wired into every repo's
`just check` + lefthook + CI (precedent: `livespec-dev-tooling-adqmnm`, "the
fan-out writes the wiring"). `needs-attention-internal` / fleet-conformance
confirms adoption. A check available as a module but not wired into the aggregate
is not enforced — verify wiring, not availability.

## Open questions — Phase-0 resolutions + what remains for Phase 2

1. **The "generated code" marker — RESOLVED 2026-07-08 (OQ1):** the generic
   `@generated` sentinel recognized in each file's native comment syntax via an
   extensible ext→comment-prefix registry (see Exemptions above). Not a directory
   name; not a per-repo glob list (which would recreate the fail-open allowlist).
   Zero current hits — collision-free future-proofing.
2. **Tests: full exemption vs higher ceiling.** Maintainer chose full exemption
   2026-07-08; revisit only if a real test file's length turns out to be
   load-bearing for a check other than LLOC.
3. **The precise per-repo flip mechanism (STILL OPEN — Phase 2)** — a per-repo env
   lever set in every CI job, vs a committed per-repo `gate=hard` marker the check
   reads. Whichever is chosen must be set in ALL of a repo's CI jobs (a lever set
   in one job and not another is a silent hole).
4. **Applies-to-all vs role-scoped classification — RESOLVED 2026-07-08 (OQ4):**
   see `check-inventory.md` §2 — 13 applies-to-all checks derive their universe
   from the git-index choke point; ~11 stay role-scoped (semantic config +
   partition guard); `no_write_direct` is hybrid. Six checks currently hardcode
   their trees with raw `rglob` (same fail-open class as `file_lloc`).
5. **Definition of "first-party `.py`" — RESOLVED 2026-07-08 (OQ5):**
   `git ls-files '*.py'` minus any `_vendor` segment, minus the configured test
   tree (+`conftest.py`), minus `@generated`-marked, minus `templates/**`. The
   empty-walk guard fails closed iff that set is non-empty but a check saw zero;
   passes iff genuinely empty (the console). The Driver repos are NON-empty (hooks)
   and must be covered — see the Fail-closed guards correction above.
