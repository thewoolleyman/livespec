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
2. **Tests** — the repo's test tree.
3. **Generated code** — files produced by a generator, identified by a REAL,
   checkable marker (a committed generated-file header sentinel or an explicit
   committed glob), **not merely a directory name**. A bare `generated/` dir
   would become a dumping ground; a marker keeps the exemption honest. The exact
   marker is an open question for Phase 0 (see below).

Anything not matching an exemption is covered. There is no catch-all bucket.

## Fail-closed guards

**Empty-walk guard.** If a check's resolved universe is empty in a repo that has
tracked first-party `.py`, that is a hard error — the exact
"walked-a-nonexistent-dir → green" bug can never recur. **Subtlety that must be
gotten right:** a repo with GENUINELY zero first-party `.py` — a pure-prose
Driver like `livespec-driver-claude`/`livespec-driver-codex`, or an all-tests
repo — legitimately produces an empty universe and MUST pass. The guard
distinguishes "no first-party code exists here" (pass) from "first-party code
exists but this check saw none of it" (fail). Getting this wrong in either
direction re-creates a silent hole (false pass) or a false alarm on driver repos.

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

## Open questions — resolve in Phase 0; do NOT block plan creation

1. **The exact "generated code" marker** — committed header sentinel vs committed
   glob. Must be a real signal, not a directory name.
2. **Tests: full exemption vs higher ceiling.** Maintainer chose full exemption
   2026-07-08; revisit only if a real test file's length turns out to be
   load-bearing for a check other than LLOC.
3. **The precise per-repo flip mechanism** — a per-repo env lever set in every CI
   job, vs a committed per-repo `gate=hard` marker the check reads. Whichever is
   chosen must be set in ALL of a repo's CI jobs (a lever set in one job and not
   another is a silent hole).
4. **Applies-to-all vs role-scoped classification** of the current dev-tooling
   check set (the Phase-0 enumeration above).
5. **Definition of "first-party `.py`"** for the empty-walk guard — the predicate
   that separates a legitimately-codeless driver repo from a mis-configured one.
