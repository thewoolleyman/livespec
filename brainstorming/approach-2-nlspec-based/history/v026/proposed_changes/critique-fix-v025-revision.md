# critique-fix v025 → v026 revision

## Origin

Bootstrap-skill consistency scan during Phase 2 sub-step 5
(vendoring) attempted to apply the v018 Q3 initial-vendoring
procedure to `jsoncomment`. The procedure mandates
`git clone <upstream>` + `git checkout <ref>` against the upstream
recorded in `.vendor.jsonc`. Verification:

1. **`.vendor.jsonc`'s recorded GitHub URL is wrong.** Phase 1
   authored `https://github.com/Dmitry-Me/JsonComment` as the
   upstream URL; that repo returns HTTP 404 (does not exist).

2. **PyPI's canonical homepage URL is dead.** PyPI metadata for
   `jsoncomment` (v0.4.2, the last release) lists
   `https://bitbucket.org/Dando_Real_ITA/json-comment` as the
   project homepage. The bitbucket repo also returns HTTP 404
   (Atlassian sunset Mercurial-based bitbucket repos circa 2020;
   this repo went away in that purge).

3. **No GitHub mirror exists.** GitHub repository search returns
   no active mirrors of the `jsoncomment` source.

4. **PyPI sdist is the only canonical surviving artifact.** The
   PyPI sdist (`jsoncomment-0.4.2.tar.gz`, released 2019-02-08) is
   the only surviving source-of-record: 3 files, ~240 LOC
   (`jsoncomment/__init__.py` 48 lines, `comments.py` 177 lines,
   `wrapper.py` 15 lines), MIT-licensed via a `COPYING` file
   attributed to "Gaspare Iengo (Dando Real ITA)". The package
   has had no releases since 2019; upstream maintenance is
   effectively dormant.

The v018 Q3 initial-vendoring procedure cannot be executed against
a non-existent upstream git repo. Three resolution paths were
evaluated: (a) extend the procedure to allow sdist-only upstreams,
(b) replace `jsoncomment` with an actively-maintained alternative
JSONC-parser library, (c) hand-author a livespec-internal shim per
the v013 M1 pattern. Option (c) was selected.

This is Case A (PROPOSAL.md drift) auto-blocking per the bootstrap
skill rule, requiring a v026 PROPOSAL.md snapshot.

## Decisions captured in v026

### D1 — Reclassify `jsoncomment` as a hand-authored shim per the v013 M1 pattern

**Decision.** The canonical vendored-libs list keeps five entries
total (per v025 D1), but the breakdown shifts: 3 upstream-sourced
(`returns`, `fastjsonschema`, `structlog`) + 2 hand-authored
shims (`typing_extensions` per v013 M1, `jsoncomment` per v026
D1). The `jsoncomment` shim retains the import name `jsoncomment`
(so any code that does `import jsoncomment` — including
`livespec.parse.jsonc` — works unchanged) and faithfully
replicates jsoncomment 0.4.2's `//` line-comment and `/* */`
block-comment stripping semantics. Multi-line strings and
trailing-commas support are OPTIONAL — the shim implements them
only if `livespec.parse.jsonc` actually requires them, matching
the v013 M1 minimalism principle. The shim's `LICENSE` file
carries verbatim MIT attribution to Gaspare Iengo (citing
jsoncomment 0.4.2's `COPYING` file as the derivative-work
source); livespec's shim is a derivative work under MIT.

Lib path stays `.claude-plugin/scripts/_vendor/jsoncomment/`. The
v018 Q3 initial-vendoring procedure's upstream-sourced-lib list
shrinks from four to three by dropping `jsoncomment`. The "shim
libraries" sentence in §"Vendoring discipline" generalizes from
"currently only `typing_extensions`" to enumerate both shims and
covers derivative-work attribution as well as verbatim-LICENSE
copy. The bootstrap-circularity rationale
(`livespec.parse.jsonc` imports `jsoncomment`; `just
vendor-update` invokes Python through `livespec.parse.jsonc`;
therefore `jsoncomment` must exist before vendor-update can run)
holds unchanged in spirit — only the mechanism for satisfying it
shifts from "git-clone-and-copy of an upstream lib" to
"hand-author the shim file at Phase 2 of the bootstrap plan."

**Rationale.** Three resolution paths were evaluated:

- **(a) Extend v018 Q3 procedure to allow sdist-tarball
  upstreams.** Adds a permanent procedure-extension for one
  stale, orphaned lib (last released 2019, upstream sunset).
  Adds an sdist-checksum + url-of-record convention to the
  `.vendor.jsonc` schema; adds an alternate code path to
  `just vendor-update`. The architectural cost is high relative
  to the single edge case it serves; future libs would not benefit
  unless they too lose their git upstream.

- **(b) Replace `jsoncomment` with an active alternative
  (e.g., `NickolaiBeloguzov/jsonc-parser`,
  `jfcarter2358/jsonc`).** Adds a new lib-selection criterion to
  PROPOSAL.md (we'd need to formalize "what makes an acceptable
  JSONC parser"); requires re-evaluation of license, API parity,
  and dependency-graph posture for whichever alternative is
  chosen. Larger PROPOSAL surface area than (c), and introduces
  a new maintenance-posture question that v013 M1's shim pattern
  already answered cleanly.

- **(c) Hand-author a livespec-internal shim. (CHOSEN.)** Applies
  the existing v013 M1 shim pattern (already used for
  `typing_extensions`) to one more lib. Eliminates upstream-
  dependency risk for a library whose only canonical source is
  dead. The lib is small (~240 LOC; comment-stripping core is
  ~50-70 LOC) so the hand-authoring cost is bounded. Livespec's
  enforcement suite (pyright strict-plus, ROP discipline,
  mutation testing per Phase 5) gates the shim implementation —
  the same guardrails that gate every other livespec-authored
  module. v013 M1's "shim" category was already general (a
  livespec-authored pure-Python module under `_vendor/<name>/`
  that faithfully replicates a designated subset of an upstream
  library's semantics, with the upstream cited in `upstream_ref`
  as the comparison target for reviewers); v026 D1 just adds one
  more lib to the category and broadens the LICENSE-handling
  language to include derivative-work attribution.

**Source-doc impact list (PROPOSAL.md).**

- Directory tree (vendored-libs section, around line 102) —
  update the `jsoncomment/` comment from
  `(MIT) — JSONC (JSON-with-comments) parser` to a shim
  marker, e.g., `(MIT, derivative) — JSONC parser shim per v013
  M1 pattern (v026 D1)`.
- Vendored pure-Python libraries enumeration (around lines
  480-484, the `jsoncomment` bullet) — rewrite to mirror the
  `typing_extensions` shim bullet (around lines 485-499):
  describe the shim as livespec-authored, faithfully replicating
  jsoncomment 0.4.2's comment-stripping semantics, with the
  shim's `LICENSE` carrying MIT attribution to Gaspare Iengo.
  Cite `upstream_ref = "0.4.2"` as the comparison target.
  Mark used-by `livespec/parse/jsonc.py`. Mention the v018 Q3
  procedure does not apply to this lib post-v026.
- §"Vendoring discipline — Initial-vendoring exception" (around
  lines 506-512) — drop `jsoncomment` from the upstream-sourced
  lib list (now: `returns`, `fastjsonschema`, `structlog`).
  Append a parenthetical clause parallel to the existing v025
  one: "(`jsoncomment` was reclassified as a shim in v026 — see
  decision D1 of
  `history/v026/proposed_changes/critique-fix-v025-revision.md`.)"
- §"Vendoring discipline" bootstrap-circularity rationale
  (around lines 527-542) — rephrase the "Once `jsoncomment` is
  initially vendored, ..." sentence to reflect the shim
  mechanism: "Once the `jsoncomment` shim is hand-authored at
  Phase 2 of the bootstrap plan, `just vendor-update <lib>`
  becomes the only permitted path for subsequent re-vendoring of
  upstream-sourced libs." The circularity argument itself stands
  (`livespec.parse.jsonc` imports `jsoncomment`; vendor-update
  uses `livespec.parse.jsonc`); only the satisfying mechanism
  changed.
- §"Vendoring discipline" shim sentence (around lines 532-536) —
  generalize from "Shim libraries (currently only
  `typing_extensions`, per v013 M1) ... initial-vendoring of a
  shim is 'the author writes the shim file by hand and copies
  the upstream LICENSE.'" to: "Shim libraries (`typing_extensions`
  per v013 M1; `jsoncomment` per v026 D1) follow the separate
  'widened manually via code review' rule — initial-vendoring of
  a shim is 'the author writes the shim file by hand and either
  copies the upstream LICENSE verbatim (if the shim is a faithful
  re-implementation of upstream APIs at upstream's license terms,
  e.g., `typing_extensions` under PSF-2.0) or authors a
  derivative-work LICENSE with attribution to the upstream author
  (if the shim is a derivative work, e.g., `jsoncomment` under
  MIT with attribution to Gaspare Iengo).'"

## Plan-level decisions paired with v026

The plan is unversioned per the v022 rule-refactor decision; plan
edits do not enter v026's overlay record but ride in the same
commit as the v026 snapshot. Paired plan edits:

- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` §"Version basis"**
  — bump version label to v026; add decision summary for v026
  (D1: jsoncomment reclassified as shim per v013 M1 pattern).
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 0 step 1
  byte-identity check** — bump reference from v025 to v026.
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 0 step 2
  frozen-status header literal** — bump from "Frozen at v025" to
  "Frozen at v026".
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` execution prompt
  block** — bump the "Treat PROPOSAL.md vNNN as authoritative"
  line from v025 to v026.
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 1
  sub-step 9 (`.vendor.jsonc`)** — update the `.vendor.jsonc`
  bullet's enumeration: jsoncomment moves from upstream-sourced
  to shim category. Note the jsoncomment shim entry carries
  `"shim": true`, `"upstream_ref": "0.4.2"` (the upstream
  release whose comment-stripping semantics the shim replicates),
  and `"upstream_url": "https://pypi.org/project/jsoncomment/"`
  (the canonical surviving source-of-record on PyPI; the
  bitbucket homepage URL is dead).
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 1
  sub-step 11 (`NOTICES.md`)** — update the jsoncomment NOTICES
  entry to indicate shim status with derivative-work attribution
  to Gaspare Iengo / jsoncomment 0.4.2.
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 2
  sub-step 5 (`.claude-plugin/scripts/_vendor/`)** — move
  `jsoncomment/` from the upstream-sourced sub-list to the shim
  sub-list. Upstream-sourced list now 3 entries (`returns`,
  `fastjsonschema`, `structlog`); shim list now 2 entries
  (`typing_extensions` per v013 M1, `jsoncomment` per v026 D1).
  Note the initial-vendoring exception's domain narrows
  accordingly. Update the surrounding language describing the
  v018 Q3 procedure scope.

## Companion-doc + repo-state changes paired with v026

These are downstream of PROPOSAL.md but already-authored at Phase
1; they get edited in the same commit as the v026 snapshot:

- **`python-skill-script-style-requirements.md`** — update any
  jsoncomment citations to mark shim status. Specifically:
  - vendored-libs section enumeration — change jsoncomment from
    upstream-sourced to shim, mirror the typing_extensions shim
    framing.
  - any text describing the upstream-sourced-libs initial-
    vendoring procedure — drop jsoncomment from those lists.
  - any LICENSE-handling commentary — broaden to cover
    derivative-work attribution alongside verbatim-copy.
- **`NOTICES.md`** — update the jsoncomment block: shim status
  with derivative-work MIT attribution to Gaspare Iengo (citing
  jsoncomment 0.4.2 as the source-of-record). Update any
  prologue framing to mention 3 upstream-sourced + 2 shim libs
  (still 5 total, unchanged from v025).
- **`.vendor.jsonc`** — change the `jsoncomment` entry: add
  `"shim": true`; set `"upstream_ref": "0.4.2"`; set
  `"upstream_url": "https://pypi.org/project/jsoncomment/"`
  (canonical source-of-record on PyPI). Update the file's header
  comment from "(six entries per v018 Q4)" — which was already
  stale post-v025 — to "(five entries per v025; jsoncomment
  reclassified as shim per v026 D1)". This sweeps a v025
  cascade leftover as a ride-along with the v026 substantive
  jsoncomment change.

## Why no formal critique-and-revise

This is a single substantive architectural decision (D1 — apply
the v013 M1 shim pattern to jsoncomment). Three resolution paths
were evaluated; the user reviewed the executor's analysis and
selected option (c) explicitly. No option-picker discussion
remains for the revision file to walk through. Direct overlay
matches the v022/v023/v024/v025 precedent for narrow single-
architectural-decision fixes.
