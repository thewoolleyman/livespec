---
topic: doctor-spec-target-drift
author: claude-opus-5-spec-side-autonomy
created_at: 2026-08-12T12:30:59Z
---

## Proposal: Record doctor's --spec-target flag in the wrapper CLI surface

### Target specification files

- SPECIFICATION/contracts.md
- .claude-plugin/prose/doctor.md (co-edit; see Edit 3)

### Summary

`contracts.md` states in two places that the `doctor` static wrapper takes only `--project-root`, but `.claude-plugin/scripts/bin/doctor_static.py` has accepted and honoured `--spec-target <path>` since 2026-07-01. This is implementation-ahead-of-contract drift, not a typo: the flag is exercised by a test that asserts doctor MUST expose the same targeting surface as its sibling wrappers. This proposal brings the contract into line with the shipped behaviour and, in doing so, makes doctor consistent with `propose-change`, `revise`, `critique` and `next`, all of which already declare `--spec-target`.

### Motivation

Found by exercising the shipped CLI rather than reading it. Running `doctor_static.py --spec-target SPECIFICATION` surfaced two path-resolution crashes (fixed in PRs #2222 and #2225) — which meant two fixes were landed for the behaviour of a flag the contract says does not exist. That is the sharpest possible signal that the contract and the implementation had diverged. Drift dated by `git log -S`: the flag entered in `8486f955` ("fix: add doctor static spec target coverage", 2026-07-01), a commit touching only `run_static.py` and its test, with no `SPECIFICATION/` change in the same changeset.

### Proposed Changes

THREE EDITS: two to `SPECIFICATION/contracts.md` and one co-edit to `.claude-plugin/prose/doctor.md`, each replacing text that exists verbatim in the live files today.

**Edit 1 — the Wrapper CLI surface table row.** Replace this line exactly:

```
| `doctor` (static) | (none) | `--project-root <path>` |
```

with:

```
| `doctor` (static) | (none) | `--spec-target <path>`, `--project-root <path>` |
```

**Edit 2 — the targeting paragraph.** Replace this sentence, which is the trailing sentence of the paragraph beginning "The `propose-change`, `revise`, and `critique` sub-commands accept `--spec-target <path>`":

```
The `doctor` sub-command takes only `--project-root`; its multi-tree enumeration is internal (see §"Per-sub-spec doctor parameterization").
```

with:

```
The `doctor` sub-command ALSO accepts `--spec-target <path>`, which selects the tree doctor treats as the MAIN spec root; its sub-spec enumeration remains internal, walking `<spec-target>/templates/<name>/` from whichever root is selected (see §"Per-sub-spec doctor parameterization"). A relative `--spec-target` or `--project-root` is anchored to the working directory, matching `revise` and `propose-change`; both resolve to absolute paths so that per-tree containment computations are well defined.
```

**Edit 3 — the operation prose (co-edit).** `.claude-plugin/prose/doctor.md` is the harness-neutral artifact BOTH Drivers read to drive the operation, and it enumerates doctor's accepted flags exhaustively without `--spec-target`. Left unamended, ratifying this proposal would leave core's own prose contradicting its own contract — and the prose, not the contract, is what an agent consults at invocation time. This co-edit was added in response to the independent adversarial review, which raised the contradiction as a ratification blocker.

(a) Under `## Inputs`, replace:

```
The doctor CLI accepts:

- `--project-root <path>` (optional; defaults to cwd).
```

with:

```
The doctor CLI accepts:

- `--spec-target <path>` (optional; selects the tree doctor
  treats as the main spec root; defaults to
  `<project-root>/SPECIFICATION/`).
- `--project-root <path>` (optional; defaults to cwd).

Both are anchored to the working directory when relative and
resolve to absolute paths.
```

(b) In the static-phase invocation step, replace:

```
   config with `[--project-root <path>]`. Capture stdout (the
   findings JSON) and the exit code.
```

with:

```
   config with `[--spec-target <path>] [--project-root <path>]`.
   Capture stdout (the findings JSON) and the exit code.
```

**Why this direction rather than the other.** The drift can be closed either by documenting the flag or by deleting it from the implementation. Documenting is recommended, for three reasons:

1. The flag is not incidental — `tests/livespec/doctor/test_run_static.py::test_run_static_main_accepts_spec_target` asserts doctor "must expose the same targeting surface" as its siblings, so removal would delete an asserted capability rather than an accident.
2. Every other spec-tree-scoped wrapper (`propose-change`, `revise`, `critique`, `next`) already declares `--spec-target`. Doctor being the sole exception is the anomaly.
3. The sentence's substantive claim survives intact: enumeration IS still internal. `--spec-target` selects the ROOT to enumerate from; it does not ask the caller to enumerate sub-specs. The replacement preserves that distinction explicitly.

**The alternative is recorded, not hidden.** A ratifier who judges that doctor should be un-targetable — that pointing it at one tree defeats the whole-project sweep the operation exists for — should REJECT this proposal and instead file an implementation-side work-item to remove `--spec-target` from `run_static.py` and delete the asserting test. That is a coherent position and this proposal does not foreclose it; it merely declines to make that call unilaterally, because it is a design question rather than a documentation gap.

**Scope note.** No sub-spec trees exist in this repository today, so the two directions are behaviourally indistinguishable for the main spec. The choice is about the contract's intent, which is why it belongs in a revise decision rather than in a silent code edit.
