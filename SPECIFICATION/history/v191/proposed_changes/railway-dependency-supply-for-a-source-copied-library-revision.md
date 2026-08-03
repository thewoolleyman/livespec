---
proposal: railway-dependency-supply-for-a-source-copied-library.md
decision: modify
revised_at: 2026-08-03T08:24:09Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

The proposal answers an open question in the clause it edits — how a repo whose own package is copied verbatim into other governed repos' `_vendor/` trees satisfies the railway's `dry-python/returns` requirement — with the pattern already in production in the same repo for the same reason. Re-verified independently at `livespec-runtime` `67bc22d`: `typing_extensions>=4.4.0` declared, bare imports at `cross_repo/types.py:23` and `cross_repo/resolve.py:38`, zero `_vendor/` files tracked, `returns` absent from `pyproject.toml`. The literal alternative reading forces `livespec_runtime/_vendor/returns/` — the only placement inside the wheel — which fans a nested `_vendor`-inside-`_vendor` into three consumers that each already vendor `returns` at their own root, putting two copies on one `sys.path` under two independent manifests. That is the drift hazard the vendoring discipline exists to prevent. The closure obligation is ratified with it rather than after it, because the source-copied shape is only sound if the consuming repo supplies the vendored library's declared dependencies; `livespec-orchestrator-git-jsonl` is the measured instance where that did not happen and nothing noticed — filed as `livespec-dev-tooling-0n2a`. Placement is `non-functional-requirements.md` per the §Boundary litmus: contributor-facing fleet infrastructure, the same shape as the red-green-replay clause in the same bullet list. No `scenarios.md` entry is owed — a governed-repo shape requirement enforced by consumer CI is not observable behavior of a livespec spec-side operation — and the change adds no heading, so no `tests/heading-coverage.json` entry is owed. Drift-swept before ratification: no other statement in the live spec tree asserts the flat rule; `constraints.md` §"Vendoring procedure" and `spec.md`'s vendored-dependency list describe core's own directly-consumed vendoring, which the new bullet preserves. Ratified as MODIFIED — see `## Modifications` for the two changes and the measurements behind them.

## Modifications

MODIFIED, not accepted as filed. TWO edits, both confined to the directly-consumed BRANCH — edit 1 within its sentence, edit 2 appending a sibling sentence after it. The source-copied branch and the closure obligation are ratified exactly as proposed.

The proposal's directly-consumed branch read (the bold below marks the removed span — it is this record's emphasis, not bytes present in the proposal): "MUST vendor `returns` under its own `_vendor/` root **per `constraints.md` §\"Vendoring procedure\"** and import it from there". The ratified text reads, in full: "A **directly-consumed repo** — a plugin, application, or tool whose Python is executed from its own checkout — MUST vendor `returns` under its own `_vendor/` root and import it from there; this is the default shape and the one the clause above has always described. The import is spelled BARE in BOTH shapes — they differ in where the vendored copy lives and in what puts it on the path, never in how the import is written."

EDIT 1 — THE PROCEDURAL CITATION IS REMOVED.

WHY. The replaced fragment ("`dry-python/returns` is vendored under `_vendor/`") carried PLACEMENT force only. §"Vendoring procedure" carries procedural force: its observable artifacts are the blessed `just vendor-update` path and a `.vendor.jsonc` recording `{upstream_url, upstream_ref, vendored_at}` per lib. Citing it normatively in a clause that binds "the `livespec-driver-*` Drivers" BY NAME was a tightening the proposal neither intended nor measured — its own Summary characterizes this branch as "vendors `returns` under its own `_vendor/` root AS TODAY".

WHAT IT WOULD HAVE COST, measured rather than asserted. `livespec-driver-claude` at origin/master `16dfe50` is fully livespec-governed (`.livespec.jsonc`, `SPECIFICATION/`), carries 117 tracked `_vendor/returns/` files, and has NO `.vendor.jsonc` anywhere in the tree. Letter-conformant under the old fragment; instantly non-conformant under the cited version, with no manifest for the blessed path to update and no recorded provenance. That state is already filed as `livespec-dev-tooling-y8o3` (P2, open), so ratifying the citation would have converted known, prioritized debt into a live spec violation in a repo this proposal never surveyed.

HOW IT WAS FOUND. The v190 mandatory independent adversarial ratification review raised it as BLOCKER B1 under dimension 5 (cross-repo consistency). The reviewer was not told `y8o3` existed and reached it by checking all seven governed repos against the proposed text, including both `livespec-driver-*` repos — which the proposal's own blast-radius survey never measured. The durable lesson is recorded on `y8o3`: a clause's blast radius is the set it NAMES, not the set that motivated it.

EDIT 2 — A BARE-SPELLING SENTENCE IS APPENDED, AND IT IS NOT IN THE PROPOSAL.

The proposal never contained it; it originates in this ratification pass. The independent review's pass-3 report identified a FALSE CONTRAST created by the proposal's own drafting: the source-copied branch spells out "BARE (no vendor-path prefix, no `sys.path` manipulation, no import-time fallback)" while the directly-consumed branch said only "import it from there", so a reader treating the two branches as exhaustive opposites could infer that a directly-consumed repo's import must be PREFIXED. It must not be. The appended sentence states the invariant directly.

MEASURED, NOT ASSERTED, AND THE MEASUREMENT IS WHAT MAKES IT SAFE. Every first-party `returns` import in the governed fleet is already spelled bare, verified per repo at origin/master: `livespec`, `livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`, `livespec-dev-tooling` (e.g. `canonical_checks.py:82`, reached by per-module `sys.path` insertion rather than a shared bootstrap), and `livespec-driver-claude`'s checkout-local guard hook. ZERO prefixed imports exist anywhere in the governed set, so the sentence flips no repo's conformance.

IT IS A REAL RULE CHOICE, NOT A NO-OP CLARIFICATION, AND IS RECORDED AS ONE. By fixing bare spelling for both shapes it forecloses a future pip-style prefixed vendoring that "import it from there" alone would have tolerated. Measured impact today is zero repos; the narrowing matches `constraints.md`'s ratified natural-name resolution contract and is what makes the source-copied resolution model coherent.

ONE WORDING REJECTED DELIBERATELY. The review suggested "(resolved via the repo's own bootstrap `sys.path` insertion)". That was declined and the reviewer concurred: the fleet uses at least four different mechanisms — `livespec` core's `bin/_bootstrap.py`, `livespec-dev-tooling`'s per-module insertion, `livespec-driver-claude`'s hand-rolled `_add_vendor_path()`, and site-packages on the installed path — so naming one would have been false in letter for the others. That is the same defect as EDIT 1's citation: binding repos on a dimension nobody measured. The ratified phrasing "what puts it on the path" abstains from every mechanism.

SCOPE OF BOTH MODIFICATIONS. They touch only the directly-consumed BRANCH. The source-copied branch (declared `pyproject.toml` dependency + BARE import + no nested `_vendor/`) and the closure obligation are ratified exactly as proposed — they are the substance `4ihw` asked for, and neither depends on the removed citation.

WHAT THIS RATIFICATION DELIBERATELY DOES NOT DECIDE, STATED SO IT IS NOT MISTAKEN FOR SILENCE. The source-copied / directly-consumed distinction does NOT adjudicate `livespec-driver-claude`'s missing `.vendor.jsonc`. That gap is real, it is measured above, and after this modification it remains OUTSIDE what this clause requires: the directly-consumed branch carries PLACEMENT and IMPORT force but no PROCEDURAL force, so a repo that vendors `returns` under its own `_vendor/` root and imports it from there satisfies this clause whether or not it records provenance. (Stated that way deliberately: an earlier draft of this record said the branch carries "placement force only", which understates its own letter — the import half is real, and is duplicative of §"ROP composition" rather than new.) `livespec-dev-tooling-y8o3` (P2, open) OWNS that gap and is the gate on it; this clause is not, and nothing here should be read as having closed it. Dropping the citation is a decision NOT to add a new tightening in this pass, not a judgment that the underlying state is acceptable. Any future proposal that binds the `livespec-driver-*` Drivers to `constraints.md` §"Vendoring procedure" is blocked on `y8o3` and should say so rather than rediscover it.

DISCLOSURE — THIS RECORD'S `content_digest` CONFORMS TO THE SHIPPED VALIDATOR AND NOT TO THE RATIFIED CONTRACT, AND THE TWO DISAGREE. `contracts.md` §"Ratification-review evidence" defines the canonical digest as covering `LP(P) || LP(path_1) || LP(content_1) || ...` — proposal bytes INCLUDED, `resulting_files[]` sorted by bytewise path comparison, and `LP(x)` an unsigned 64-bit big-endian length prefix. The shipped validator (`commands/_revise_ratification.py::_canonical_ratification_digest`) computes ascii-decimal `:`-separated length prefixes over `resulting_files[]` ONLY, in list order, and HARD-REFUSES any digest that does not match its own recompute. The two definitions disagree on all three axes, so no digest can satisfy both: a contract-conformant value would be rejected with "content_digest does not match final bytes". This evidence therefore binds the VALIDATOR's digest, which is the only value that can pass the gate — stated here rather than left implicit, because a record silently asserting a contract conformance it does not have is the same defect this ratification twice corrected in its own narrative. Neither scheme is unsound: ascii-decimal-plus-`:` is injective for the same reason the u64 prefix is, so reconciling them is a free choice between two sound encodings, not a correction of a broken one. `livespec-dev-tooling-k4km` (P1, open) OWNS the reconciliation and names both directions; it does not gate this cut, and nothing here should be read as having decided which side moves.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-03T08:22:35Z
verdict: NO BLOCKERS
proposal_stem: railway-dependency-supply-for-a-source-copied-library
content_digest: b744fa639dfd44f46dfcd17287623f0d6a48aba88d4c5db688a074b652f3526a
