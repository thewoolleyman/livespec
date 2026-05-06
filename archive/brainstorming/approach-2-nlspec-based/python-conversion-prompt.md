# Python-Conversion Session Prompt

Paste the block below into a new Claude Code session (in the
livespec repo) to start the bash-to-Python conversion pass.
Produces the next version from the current working `PROPOSAL.md`
by **replacing** bash with Python as the implementation language
for every script the skill bundles and every enforcement-suite
script in `dev-tooling/`.

This prompt is a Python-specialization of the generic
`critique-interview-prompt.md`; the versioning mechanics,
multi-proposal file format, and interview discipline from that
prompt carry over unchanged.

Before pasting, fill in the three numbers at the top of the
prompt:

- `N`         — the current (latest completed) version number.
                This is the version recorded as the latest entry
                in `history/README.md`, and the working
                `PROPOSAL.md` is byte-identical to
                `history/vN/PROPOSAL.md`.
- `NEXT`      — `N + 1` — the version being produced by this
                session.
- `CRITIQUE`  — the critique-file sequence number for this pass.
                Convention: producing `v(NEXT)` uses
                `v(NEXT-1)` zero-padded to two digits (e.g.
                producing v006 → `CRITIQUE = 05`).

Everything below the `---` is the prompt body. The placeholders
`vNNN` / `v(NEXT)` / `critique-vCC` use the literal variables
`N`, `NEXT`, `CRITIQUE` — replace them verbatim before pasting,
or hand the whole prompt to Claude Code and let it substitute.

---

I want to convert the livespec skill's bundled scripts **and** the
dev-tooling enforcement suite from **bash** to **Python**, producing
v{NEXT} from the current v{N}. This is a deliberate language
migration; it is not a critique of the existing bash design. The
bash implementation in v{N} and the accompanying
`bash-skill-script-style-requirements.md` are the input; a
Python-based `PROPOSAL.md` plus a new
`python-skill-script-style-requirements.md` are the output.

## Motivation (load-bearing — read carefully)

Over the v{N} pass, the bash style doc grew to roughly 24 pages of
rules that exist primarily to compensate for features bash lacks
(namespaces, import systems, data structures, a type system, a
reliable AST, built-in test/coverage tooling, dependency
management beyond filesystem sourcing). The premise of choosing
bash was "maximum portability, minimal runtime dependencies." That
premise is already compromised by `jq` being a hard runtime dep
and by macOS shipping bash 3.2.57 at `/bin/bash` (the whole B12
discussion in v005's revision file is about accommodating that).

Python substitutes cleanly:

- On Linux (Debian, Ubuntu, Fedora, Arch), Python 3.x is preinstalled.
- On macOS, `python3` is not preinstalled but is a one-command
  install via homebrew or the Xcode command-line tools (which most
  users doing any development already have).
- Python's standard library covers nearly every dep the bash suite
  needed external tools for (json, pathlib, subprocess, argparse,
  re, ast). `pyyaml` or `jsonschema` can be vendored if needed.
- `ruff` (one tool) replaces shellcheck + shfmt + shellharden +
  shellmetrics. `pytest` + `coverage.py` replaces bats-core +
  bats-assert + bats-support + kcov. `mypy` or `pyright` add type
  checking, with no bash analogue.

Net effect: the style doc shrinks from ~24 pages to an estimated
~5–8 pages; the enforcement suite drops from 6 external tools to
3; AST-level checks (cross-library private-call, source-cycle,
global-write) stop being R&D projects and become `ast.walk()`
calls; the kcov DEBUG-trap artifact story disappears.

This pass does NOT re-open any decision that v{N} already settled
about WHAT the skill does (sub-commands, templates, lifecycle,
history, proposed-change / revision file formats, doctor's check
*contract*). It only changes HOW scripts are implemented
(language and the constellation of rules that attend that
language).

## Version knobs for this session

- Current version: **v{N}**
- Next version: **v{NEXT}**
- Critique sequence number for this pass: **v{CRITIQUE}** (so the
  critique / conversion-plan file basename is
  `proposal-critique-v{CRITIQUE}`, retaining the naming continuity
  with prior passes even though the content is a conversion plan
  rather than a defect critique).

## Required reading (please load all of these before starting)

Working proposal and its embedded grounding:

- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/nlspec-spec.md`
  (upstream source for `livespec-nlspec-spec.md`, for reference
  when evaluating fidelity / adaptation)

Companion documents in the brainstorming folder (load every file
directly under `brainstorming/approach-2-nlspec-based/` that isn't
`PROPOSAL.md` or the two spec files above — the current set
includes):

- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/goals-and-non-goals.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/subdomains-and-unsolved-routing.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/prior-art.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md`
  (this is the document being REPLACED by the Python-equivalent
  produced in this session; read it as the reference for which
  rules transfer, which drop, and which take new shape)
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-diagram.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-diagram-detailed.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-legend.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-terminology-and-structure-summary.md`

If new files have landed there since this prompt was last
updated, load those too.

History (for versioning/lifecycle context and the prior decision
records — load **every file** under
`/data/projects/livespec/brainstorming/approach-2-nlspec-based/history/`,
including:

- `history/README.md`
- every `history/vNNN/PROPOSAL.md` (frozen per-version snapshots)
- every `history/vNNN/proposed_changes/*.md` (critiques,
  revisions, and any additional reference artifacts)
- every `history/vNNN/conversation.json` that exists (previous
  sessions' full dialogue records — use these to understand what
  was already considered and why; do not re-ask decisions that
  were explicitly resolved unless I bring them up)

The v{N} entry is the most recent and the most important. Its
PROPOSAL, its critique / conversion-plan, its revision, and its
`conversation.json` (if present) are the direct input to this
pass.

## What to produce

1. **Produce a Python-conversion plan document** — the v{CRITIQUE}
   analogue of prior critique files — organized as one
   `## Proposal: <name>` section per discrete decision the
   conversion requires. Use the same multi-proposal file format
   that v003+ prior critiques used (file-level YAML front-matter
   with `topic` / `author` / `created_at`; flat `## Proposal:
   <name>` sections with `### Target specification files`, `###
   Summary`, `### Motivation`, `### Proposed Changes`
   sub-headings). The **failure-mode labels** from prior
   critiques (ambiguity / malformation / incompleteness /
   incorrectness) do NOT apply here; conversion-plan proposals
   label themselves by **axis** instead (e.g., *language-floor*,
   *dependency-strategy*, *tooling*, *layout*,
   *rule-simplification*, *enforcement-suite-shape*,
   *backwards-compatibility*).

2. **Save the conversion plan** to
   `brainstorming/approach-2-nlspec-based/proposed_changes/v{NEXT}-proposed-change-proposal-critique-v{CRITIQUE}.md`.

3. **Decisions the conversion plan MUST address.** The plan has
   at least these items; feel free to add more if the conversion
   surfaces additional choices:

   - **Python version floor.** What's the minimum Python 3.x the
     skill targets? (Suggest 3.10 or 3.11 for pattern matching,
     structural types, etc.; or 3.8 for widest macOS/Linux
     coverage.)
   - **Runtime dependency set.** Which deps besides `python3`
     itself? Drop `jq` (Python has `json`)? Keep `jq` for LLM
     prompt use? Any others (`pyyaml`, `jsonschema`, etc.)?
   - **Dependency-shipping mechanism.** Stdlib-only, vendored
     .py files in the bundle, or install-time dependency
     management via `uv` / `pip`? (Skill bundles have no network
     access at runtime, so runtime `pip install` is out.)
   - **Package layout inside the bundle.** Flat files under
     `scripts/`, a single Python package (e.g.,
     `scripts/livespec/`), or a namespace package? How is it
     invoked from `SKILL.md` and from the `dispatch` entry point
     (if `dispatch` even stays as a bash stub or becomes a
     Python entry too)?
   - **Linter and formatter.** `ruff` (one tool) is the obvious
     choice; confirm, configure, pin via mise.
   - **Type checker.** `mypy` vs `pyright`; strict level; whether
     enforcement gates on type errors.
   - **Test framework and fixtures.** Assume `pytest`; confirm;
     specify fixture discipline, parametrize patterns,
     `tmp_path` usage, mock strategy.
   - **Coverage tool and threshold.** `coverage.py`; thresholds
     (per-file vs overall); Python has no kcov DEBUG-trap
     artifact problem, so the `≥ 95% pure` compromise from B2
     can be reconsidered (go back to 100%, drop the pure/impure
     distinction, or keep both tiers).
   - **Complexity thresholds.** `ruff`'s `C901` (mccabe) has a
     default of 10; revisit the CCN ≤ 10 / args ≤ 6 / LLOC ≤ 50
     limits from the bash doc now that Python's expressiveness
     changes what "complex" looks like.
   - **Enforcement-suite shape.** Which Makefile targets stay
     (`make check-lint`, `make check-types`, `make check-tests`,
     `make check-coverage`), which drop (no more
     `check-shellcheck` / `check-shfmt` / `check-shellharden` /
     `check-sourceable-guards` / `check-library-headers` /
     `check-source-graph` / `check-private-calls` /
     `check-global-writes` — most collapse into ruff + mypy or
     become unnecessary), and which take new Python-specific
     shape?
   - **doctor-static decomposition.** v{N} decomposed
     `doctor-static` into per-check executables under
     `scripts/doctor/static/<slug>`. Does that decomposition
     carry over with Python files (`scripts/doctor/static/
     <slug>.py` importing from a shared package)? Or does Python
     let us simplify back to a single module with dispatch
     functions? Preserve the slug-based `check_id` contract
     either way.
   - **Sourceable-guard equivalent.** Python's
     `if __name__ == "__main__":` is the built-in idiom; confirm
     it replaces the bash sourceable-guard rule.
   - **Purity / I/O isolation.** Python's namespaces and
     dependency-injection patterns make the pure/impure directive
     less necessary. Decide: drop entirely, keep as a soft
     convention documented in prose, or keep as a mechanical
     rule enforced by a custom ruff plugin or static analyzer.
   - **Debug / verbose affordances.** Replace `LIVESPEC_XTRACE` /
     `LIVESPEC_VERBOSE` bash env switches with Python's `logging`
     module configured by a single env var or `-v`/`-vv` CLI
     flag.
   - **Exit code contract.** Keep the 0/1/2/3/126/127 contract
     from the bash doc? Python's convention is slightly
     different (raise exceptions, `sys.exit(N)`); decide how to
     preserve the contract semantically.
   - **File naming and invocation.** Python files carry `.py`;
     direct-execution requires either a shebang + chmod+x or
     `python3 script.py` invocation; decide the convention and
     whether `SKILL.md` references `scripts/dispatch.py` or
     `python3 scripts/dispatch.py` or `python3 -m
     livespec.dispatch`.
   - **Bridging bash stub for `dispatch`.** An option worth
     considering: keep `dispatch` as a ~10-line bash stub that
     `exec`s a Python entry point, so `SKILL.md`'s invocation
     doesn't need to know about Python. OR: go all-Python, with
     `scripts/dispatch.py` carrying a shebang.
   - **Fate of `bash-skill-script-style-requirements.md`.**
     Replaced by `python-skill-script-style-requirements.md` at
     the same location; the bash doc is removed (or moved to
     `history/` as a retired reference document). Decide.
   - **Fate of the `bash-boilerplate.sh` file.** Removed
     entirely; Python code doesn't need one. The `dev-tooling/
     bash-boilerplate.sh` symlink is also removed.
   - **Backwards compatibility.** Is any bash kept (e.g., the
     `dispatch` stub, a `mise.toml` install-script, a trivial
     entry shim)? If yes, the bash style doc might be kept in
     abbreviated form for just those files; if no, it's fully
     retired.

4. **Interview me through every item**, one question at a time.
   Strict rules:

   - Print each item's sub-options visibly before asking.
   - Every `AskUserQuestion` MUST lead with a recommended option
     labelled `(Recommended)` and state the rationale in the
     surrounding text.
   - Ask exactly ONE question per turn — never batch multiple
     sub-items into a single AskUserQuestion call.
   - Push back when I'm wrong or when something I'm proposing
     conflicts with decisions already in PROPOSAL.md or any prior
     revision file under `history/`.
   - Don't obsess over preserving v{N} compatibility during
     brainstorming — if a cleaner break is better, propose it.
     This conversion is itself a clean break from bash; further
     clean breaks from v{N} incidentals are fair game.
   - If I ask you to clarify, clarify before re-asking.
   - If mid-interview I rewrite one of the companion files (the
     goals, the nlspec spec, etc.), append new items for any
     gaps that rewrite opens up against the conversion plan
     before finishing.

5. **After the interview**, do the full dogfood lifecycle apply:

   - Write
     `history/v{NEXT}/proposed_changes/proposal-critique-v{CRITIQUE}-revision.md`
     capturing per-item decisions (accept / modify / reject +
     rationale).
   - Write the new
     `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
     from scratch, reflecting every interview decision. It
     SHOULD be substantially shorter than the bash doc it
     replaces (~5–8 pages if the decisions align with the
     motivation above).
   - Remove or archive
     `brainstorming/approach-2-nlspec-based/bash-skill-script-style-requirements.md`
     per the interview decision. If archived, move it to
     `history/v{NEXT}/retired-documents/` or similar with a
     READMe.md noting why it was retired.
   - Rewrite top-level `PROPOSAL.md` to v{NEXT} incorporating all
     decisions: language references change from bash to Python,
     the skill layout tree shows `.py` files, the Dependencies
     section lists `python3` instead of `bash >= 3.2` / `jq`,
     the Developer tooling layout reflects ruff/mypy/pytest
     instead of shellcheck/shfmt/shellharden/shellmetrics/kcov/
     bats, the Testing approach references pytest conventions,
     the doctor static-check contract keeps its slug-based
     `check_id` shape but refers to Python implementations, and
     every cross-reference to `bash-skill-script-style-requirements.md`
     is updated to `python-skill-script-style-requirements.md`.
   - Create `history/v{NEXT}/PROPOSAL.md` as a byte-identical
     copy of the new working `PROPOSAL.md`.
   - Move the conversion-plan file from `proposed_changes/` to
     `history/v{NEXT}/proposed_changes/proposal-critique-v{CRITIQUE}.md`.
   - If a pre-interview draft of the conversion plan exists,
     also move it to `history/v{NEXT}/proposed_changes/` with a
     descriptive suffix (e.g.,
     `…-original-questions-pre-interview.md`).
   - Update `history/README.md` to add a v{NEXT} entry
     summarizing the major structural changes (language
     migration from bash to Python, specific tool substitutions,
     style-doc rename, retired artifacts) and pointing at the
     revision file; update the final "Pointer" paragraph to
     reference v{NEXT}.
   - Capture the session's turns into
     `history/v{NEXT}/conversation.json` (user verbatim,
     assistant summaries) — same schema as prior
     `conversation.json` files.

## Known constraints to honor

- **Do NOT reopen any decision about WHAT livespec does** that is
  currently written into `PROPOSAL.md` or into any prior
  `history/vNNN/proposed_changes/*-revision.md`. The sub-command
  set, the template architecture, the lifecycle, the history
  directory shape, the proposed-change / revision file formats,
  the doctor static-check slugs, the interactive revise flow, and
  the dev-time vs runtime split from v005 are all load-bearing
  and out of scope for this pass. This pass is purely HOW scripts
  are implemented, not WHAT they do.
- The latest revision file
  (`history/v{N}/proposed_changes/…-revision.md`) is the
  authoritative record of what was most recently settled — read
  it first and treat its dispositions as load-bearing.
- The `mise`-managed tool-pinning discipline from v{N} remains;
  update the tool set, not the mechanism.
- The enforcement suite stays invocation-agnostic and
  Makefile-driven; update the Makefile targets, not the framing.
- The runtime / dev-time split from v{N} stays; Python files
  replace bash files within each tree, but the tree shapes (skill
  bundle under `.claude-plugin/`, dev-tooling at repo root) don't
  move.
- The slug-based `doctor-<slug>` check_id contract from v{N}
  stays; Python implementations emit the same JSON findings.

Start by reading all the required files, then produce the
conversion plan and save it. Then begin the interview.


# Python architecture patterns

## Railway Oriented Programming

Functional, Type Safety, and Railway Oriented Programming (ROP) patterns MUST be used.

See the following examples for how to do this:
- Concrete Python examples of ROP patterns: https://github.com/thewoolleyman/tab-groups-windows-list/blob/master/adws/adw_modules/engine/README.md - see associated code in this directory 


- https://gitlab.com/gitlab-org/gitlab/-/blob/master/ee/lib/remote_development/README.md#railway-oriented-programming-and-the-result-class (Ruby Example) - see associated code below that directory

- Original talks and examples on ROP: https://fsharpforfunandprofit.com/rop/


