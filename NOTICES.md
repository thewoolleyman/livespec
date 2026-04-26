# Third-party notices

This project vendors the following third-party libraries into
`.claude-plugin/scripts/_vendor/`. Each library's `LICENSE` file
is preserved alongside its source at
`.claude-plugin/scripts/_vendor/<name>/LICENSE` (per
python-skill-script-style-requirements.md §"Vendored third-party
libraries"). For the 4 upstream-sourced libs (`returns`,
`fastjsonschema`, `structlog`, `typing_extensions`), the
`LICENSE` is a verbatim copy of the upstream `LICENSE`. For the
1 shim (`jsoncomment`), the `LICENSE` is a derivative-work
LICENSE with attribution to the upstream author (Gaspare Iengo,
MIT). Phase 2's initial-vendoring procedure (per v018 Q3)
copies the upstream-sourced libraries and their `LICENSE` files
in place; the 1 shim is hand-authored at Phase 2. Until Phase
2 lands, the per-library `LICENSE` paths referenced below do not
yet exist.

The library list and license metadata below are authoritative
per PROPOSAL.md §"Runtime dependencies — Vendored pure-Python
libraries" (five entries per v025; 4 upstream-sourced + 1 shim
per v027; the v018 Q4 sixth entry `returns_pyright_plugin` was
dropped in v025 D1 — pyright has no plugin system and no
upstream artifact existed, see
`brainstorming/approach-2-nlspec-based/history/v025/proposed_changes/critique-fix-v024-revision.md`;
`jsoncomment` was reclassified from upstream-sourced lib to
hand-authored shim in v026 D1 because its canonical upstream
(`bitbucket.org/Dando_Real_ITA/json-comment`) was sunset and no
live git mirror exists, see
`brainstorming/approach-2-nlspec-based/history/v026/proposed_changes/critique-fix-v025-revision.md`;
`typing_extensions` was reclassified from hand-authored shim to
upstream-sourced lib in v027 D1 because vendored libs'
transitive use of variadic generics required full upstream
typing_extensions backports that a minimal shim cannot
synthesize on Python 3.10, see
`brainstorming/approach-2-nlspec-based/history/v027/proposed_changes/critique-fix-v026-revision.md`).

---

## `returns`

- **Upstream:** dry-python/returns (https://github.com/dry-python/returns)
- **License:** BSD-3-Clause
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/returns/LICENSE`

ROP primitives: `Result`, `IOResult`, `bind`, `map`, `Success`,
`Failure`. See PROPOSAL.md §"Railway-Oriented Programming (ROP)".

---

## `fastjsonschema`

- **Upstream:** horejsek/python-fastjsonschema
  (https://github.com/horejsek/python-fastjsonschema)
- **License:** BSD-3-Clause
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/fastjsonschema/LICENSE`

JSON Schema validator. Compiles schemas to Python code for
fast validation. See PROPOSAL.md §"Schemas and dataclasses".

---

## `structlog`

- **Upstream:** hynek/structlog (https://github.com/hynek/structlog)
- **License:** Dual-licensed MIT OR Apache-2.0 (consumer's choice)
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/structlog/LICENSE`
  (preserves both license texts as shipped upstream, prefixed by the
  upstream `COPYRIGHT` notice)

Structured JSON logging. See python-skill-script-style-requirements.md
§"Structured logging".

---

## `jsoncomment` (shim)

- **Upstream source-of-record:** jsoncomment 0.4.2 on PyPI
  (https://pypi.org/project/jsoncomment/) — the project's
  canonical homepage at bitbucket.org/Dando_Real_ITA/json-comment
  was sunset by Atlassian and no live git mirror exists; the PyPI
  sdist (`jsoncomment-0.4.2.tar.gz`, released 2019-02-08) is the
  only surviving canonical artifact. Original author: Gaspare
  Iengo (Dando Real ITA).
- **License:** MIT (derivative work)
- **Derivative-work license file:**
  `.claude-plugin/scripts/_vendor/jsoncomment/LICENSE` — verbatim
  MIT text with attribution to Gaspare Iengo, citing
  jsoncomment 0.4.2's `COPYING` file as the derivative-work
  source. Livespec's shim is a derivative work under MIT.

JSONC (JSON-with-comments) parser shim per v026 D1, faithfully
replicating jsoncomment 0.4.2's `//` line-comment and `/* */`
block-comment stripping semantics (multi-line strings + trailing-
commas support optional, only if `livespec/parse/jsonc.py`
requires them). Module-named `jsoncomment` so existing
`import jsoncomment` statements work unchanged. The shim's
`upstream_ref` (in `.vendor.jsonc`) records `0.4.2` as the
upstream release whose comment-stripping semantics the shim
replicates. Used for `.vendor.jsonc` and other livespec config
files that benefit from inline comments.

---

## `typing_extensions`

- **Upstream:** python/typing_extensions
  (https://github.com/python/typing_extensions)
- **License:** Python Software Foundation License (PSF-2.0)
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/typing_extensions/LICENSE`

Python typing-system backports. Vendored full upstream verbatim
at tag `4.12.2` per v027 D1 (was the v013 M1 hand-authored
minimal shim pre-v027). Provides the variadic-generics + Self +
Never + TypedDict + ParamSpec + TypeVarTuple + Unpack symbols
that the vendored returns + structlog + fastjsonschema sources
transitively require at import time, plus livespec's own
canonical-import-path needs (`override` for pyright's
`reportImplicitOverride` per style-doc L2; `assert_never` for
the Never-narrowing exhaustiveness check per style-doc L7).
v027 D1 reclassified typing_extensions from shim to
upstream-sourced because the v013 M1 minimal-shim approach
cannot satisfy `Generic[..., Unpack[TypeVarTuple(...)]]`
variadic-generics usage on Python 3.10 (the dev-env minimum) —
PROPOSAL.md v013 M1 explicitly anticipated this scope-widening
path.
