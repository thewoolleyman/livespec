# critique-fix v026 → v027 revision

## Origin

Phase 2 sub-step 5 vendoring (post-v026) authored the v013 M1
hand-authored typing_extensions shim at
`.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`.
The v013 M1 spec mandated "exports exactly `override` and
`assert_never`" with an explicit allowance to widen one symbol at
a time. Initial widening at sub-step 5 added Never, ParamSpec,
Self, TypeVarTuple, TypedDict, and Unpack — six additions
discovered by greppting the actual `from typing_extensions import
...` calls inside the vendored returns + structlog + fastjsonschema
sources. On Python 3.13 (system) the smoke test passed: all 5 libs
import and the deep paths
(`returns.io.IOResult`, `returns.result.Result`,
`fastjsonschema.compile`, `structlog.get_logger`,
`jsoncomment.JsonComment`) all worked.

On Python 3.10.16 (the dev-env minimum pinned in `.python-version`),
the deep import `from returns.io import IOResult` failed at:

```python
# returns/primitives/hkt.py line 25
class KindN(Generic[_InstanceType_co, Unpack[_TypeVars]]):
```

where `_TypeVars = TypeVarTuple("_TypeVars")`. The shim's 3.10
fallback stubs (`Never = NoReturn`, `_TypeVarTupleStub`,
`_UnpackStub`) cover *type-hint-only* usage but cannot satisfy
`Generic[..., Unpack[_TypeVars]]` at class-definition time on 3.10:
making `Unpack[X]` subscriptable via `__class_getitem__` is
straightforward, but Python 3.10's `Generic.__class_getitem__`
calls `_collect_parameters` which rejects non-TypeVar /
non-ParamSpec arguments. There is no realistic shim path to make a
`TypeVarTuple` instance look like a TypeVar to 3.10's `Generic`
machinery — variadic-generics support requires the actual 3.11+
stdlib semantics or an upstream-typing_extensions backport.

The Phase 2 stub contract (PROPOSAL.md
§"Stub contract — Phase 2-3") requires
`IOFailure(<DomainError>(...))` return statements that
transitively load `returns.primitives.hkt`, so Phase 2 cannot
proceed on the pinned 3.10 dev env without resolving the import
failure. The v013 M1 minimal-shim assumption — which only
anticipated livespec's *own* usage of `override` + `assert_never`
— did not account for vendored libs depending on full
typing_extensions semantics (especially variadic generics) at
import time.

This is Case A (PROPOSAL.md drift) auto-blocking per the bootstrap
skill rule, requiring a v027 PROPOSAL.md snapshot. Two resolution
paths were evaluated; option (a) was selected.

## Decisions captured in v027

### D1 — Vendor full typing_extensions upstream; reclassify from shim to upstream-sourced lib

**Decision.** The v013 M1 minimal-shim approach is replaced by
verbatim upstream vendoring per PROPOSAL.md's pre-planned
"scope-widening decision" framing. `typing_extensions` moves from
the "shim" category to the "upstream-sourced" category. The
canonical vendored-libs list keeps five entries total; the
breakdown shifts to **4 upstream-sourced** (`returns`,
`fastjsonschema`, `structlog`, `typing_extensions`) + **1 shim**
(`jsoncomment`, the real derivative-work shim per v026 D1). The
`_vendor/typing_extensions/__init__.py` content is replaced with
the verbatim upstream `typing_extensions/src/typing_extensions.py`
content at tag `4.12.2`. The hand-authored shim's body
(override + assert_never + 6 widening symbols + 3.10 fallbacks)
becomes obsolete — upstream typing_extensions provides all of
these symbols natively with proper backports for 3.10 (variadic
generics included).

The v018 Q3 git-clone-and-copy initial-vendoring procedure now
applies to typing_extensions. The "shim" category narrows to one
entry (`jsoncomment` only), preserving v026 D1's framing of
shim = "livespec-authored module that replicates an upstream
library's algorithm with derivative-work attribution when the
upstream is dead/orphaned."

The user-facing Python minimum stays at 3.10+ — upstream
typing_extensions handles the 3.10 backports internally.

**Rationale.** Two resolution paths were evaluated:

- **(a) Vendor full typing_extensions upstream. (CHOSEN.)**
  Replaces the hand-authored shim with verbatim upstream content
  (~3641-line single .py file at v4.12.2, PSF-2.0 LICENSE).
  Eliminates the "what symbols does the shim need?" question
  permanently — upstream provides everything. Variadic generics
  work on 3.10 because upstream typing_extensions has the proper
  backports. The PSF-2.0 LICENSE we already wrote during the
  hand-authored shim work is verbatim correct and stays in place
  unchanged. PROPOSAL.md anticipated this exact path at v013 M1
  ("re-vendoring the full upstream is a future option tracked as
  a scope-widening decision, not a v013 default"). Aligns with
  the user-stated preference for standardized libraries over
  hand-rolled.

- **(b) Bump user-facing Python minimum from 3.10+ to 3.11+.**
  `_bootstrap.py:11` (`(3, 10)` → `(3, 11)`),
  `pyproject.toml [project.requires-python]`,
  `.python-version`, and the corresponding PROPOSAL.md / style
  doc references all bump. The widened shim's try-branches
  succeed on 3.11+ stdlib; the 3.10 fallbacks become dead code.
  Smaller change overall (no new vendored content), but bumps
  the user-facing Python requirement. Rejected because the
  user-facing minimum is a more visible commitment than the
  internal shim-vs-vendor choice; option (a) preserves it.

**Source-doc impact list (PROPOSAL.md).**

- Directory tree (vendored-libs section, around line 102-103) —
  typing_extensions comment changes from minimal-shim framing
  to upstream-sourced framing. Example: `# (PSF-2.0) — Python
  typing backports including variadic generics (vendored
  upstream per v027 D1)`.
- Vendored pure-Python libraries enumeration (around lines
  485-499, the `typing_extensions` bullet) — rewrite to mirror
  the upstream-sourced bullets (`returns`, `fastjsonschema`,
  `structlog`): describe upstream provenance, license, what
  livespec uses (`override` + `assert_never` plus the symbols
  vendored libs transitively need), and that v018 Q3 git-clone-
  and-copy procedure applies. Note that v013 M1's hand-authored
  shim approach was replaced in v027 because vendored-lib
  internal use of variadic generics requires upstream
  typing_extensions backports that a minimal shim cannot
  provide on Python 3.10.
- §"Vendoring discipline — Initial-vendoring exception" (around
  lines 506-512) — add `typing_extensions` to the upstream-
  sourced lib list. Now: `returns`, `fastjsonschema`,
  `structlog`, `typing_extensions`. Update the parenthetical
  clauses: "(`returns_pyright_plugin` was removed in v025 D1;
  `jsoncomment` was reclassified as a hand-authored shim in
  v026 D1 and is no longer subject to the git-based procedure
  below; `typing_extensions` was reclassified from hand-
  authored shim to upstream-sourced lib in v027 D1.)"
- §"Vendoring discipline" shim sentence (around lines 532-536) —
  narrow to one entry: "Shim libraries (`jsoncomment` per v026
  D1) follow the separate 'widened manually via code review'
  rule — initial-vendoring of a shim is 'the author writes the
  shim file by hand and authors a derivative-work LICENSE with
  attribution to the upstream author (e.g., `jsoncomment` under
  MIT with attribution to Gaspare Iengo).'" The
  `typing_extensions`-as-shim language drops entirely.
- §"Runtime dependencies" section near the v013 M1 reference —
  add a paragraph noting v027 D1 reclassified typing_extensions
  from the v013 M1 hand-authored shim to upstream-sourced lib.

## Plan-level decisions paired with v027

The plan is unversioned per the v022 rule-refactor decision; plan
edits do not enter v027's overlay record but ride in the same
commit as the v027 snapshot. Paired plan edits:

- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` §"Version basis"**
  — bump version label to v027; add decision summary for v027 (D1:
  typing_extensions vendored full upstream, reclassified from shim
  to upstream-sourced).
- **Phase 0 step 1 byte-identity check** — bump from v026 to v027.
- **Phase 0 step 2 frozen-status header literal** — bump from
  "Frozen at v026" to "Frozen at v027".
- **Execution prompt block** — bump the "Treat PROPOSAL.md vNNN as
  authoritative" line from v026 to v027.
- **Phase 1 sub-step 9 (`.vendor.jsonc`)** — update typing_extensions
  entry: remove `"shim": true`. Now the breakdown is 4 upstream-
  sourced + 1 shim. Phase 2's placeholder-replacement note widens
  to cover the 4 upstream-sourced entries (returns, fastjsonschema,
  structlog, typing_extensions); the 1 shim (jsoncomment) carries
  its real `upstream_ref` from v026 D1 authoring time.
- **Phase 1 sub-step 11 (`NOTICES.md`)** — update the
  typing_extensions block to indicate upstream-sourced status (not
  shim). The `LICENSE` already in place at
  `.claude-plugin/scripts/_vendor/typing_extensions/LICENSE`
  (verbatim PSF-2.0) is correct as-is — no LICENSE-file change
  needed; only the descriptive prose changes.
- **Phase 2 sub-step 5 (`.claude-plugin/scripts/_vendor/`)** —
  move `typing_extensions/` from the shim sub-list to the upstream-
  sourced sub-list. Now upstream-sourced: 4 entries (returns,
  fastjsonschema, structlog, typing_extensions). Shim: 1 entry
  (jsoncomment).

## Companion-doc + repo-state changes paired with v027

These are downstream of PROPOSAL.md but already-authored at Phase
1 / Phase 2; they get edited in the same commit as the v027
snapshot:

- **`python-skill-script-style-requirements.md`** — update
  typing_extensions citations:
  - vendored-libs section enumeration — change typing_extensions
    from shim framing to upstream-sourced framing; mirror the
    other upstream-sourced bullets.
  - shim discipline section — narrow to jsoncomment as the only
    shim.
- **`NOTICES.md`** — update the `typing_extensions (shim)` block
  to `typing_extensions` (upstream-sourced); update prose to
  reflect that the LICENSE is a verbatim copy of upstream and
  the lib provides full typing_extensions semantics, not a
  minimal subset. Update the prologue's 3+2 framing to 4+1
  (4 upstream-sourced + 1 shim).
- **`.vendor.jsonc`** — change the `typing_extensions` entry:
  remove `"shim": true`. The header comment widens to reflect
  the new 4+1 breakdown.
- **`.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`**
  — replace the hand-authored shim content (95 lines) with the
  verbatim upstream `typing_extensions/src/typing_extensions.py`
  content at tag `4.12.2` (~3641 lines). The PSF-2.0 LICENSE
  next to it stays unchanged (was already verbatim from
  upstream during v013 M1 shim work).

## Why no formal critique-and-revise

This is a single substantive architectural decision (D1 — apply
the v013 M1-anticipated "scope-widening decision" to vendor full
typing_extensions upstream). Two resolution paths were evaluated;
the user reviewed the executor's analysis and selected option (a)
explicitly. No option-picker discussion remains for the revision
file to walk through. Direct overlay matches the v022/v023/v024/
v025/v026 precedent for narrow single-architectural-decision
fixes.
