# Third-party notices

This project vendors the following third-party libraries into
`.claude-plugin/scripts/_vendor/`. Each library's verbatim
upstream `LICENSE` file is preserved alongside its source at
`.claude-plugin/scripts/_vendor/<name>/LICENSE` (per
python-skill-script-style-requirements.md §"Vendored third-party
libraries"). Phase 2's initial-vendoring procedure (per v018 Q3)
copies the libraries and their `LICENSE` files in place; until
then the per-library `LICENSE` paths referenced below do not
yet exist.

The library list and license metadata below are authoritative
per PROPOSAL.md §"Runtime dependencies — Vendored pure-Python
libraries" (six entries per v018 Q4).

---

## `returns`

- **Upstream:** dry-python/returns (https://github.com/dry-python/returns)
- **License:** BSD-2-Clause
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/returns/LICENSE`

ROP primitives: `Result`, `IOResult`, `bind`, `map`, `Success`,
`Failure`. See PROPOSAL.md §"Railway-Oriented Programming (ROP)".

---

## `returns_pyright_plugin`

- **Upstream:** dry-python/returns (https://github.com/dry-python/returns)
- **License:** BSD-2-Clause (same upstream project as `returns`)
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/returns_pyright_plugin/LICENSE`

The pyright plugin packaged alongside the `returns` library.
Loaded via `pyproject.toml`'s
`[tool.pyright]` `pluginPaths = ["_vendor/returns_pyright_plugin"]`
entry. Per v018 Q4.

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
- **License:** Dual-licensed BSD-2-Clause / MIT (consumer's choice)
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/structlog/LICENSE`
  (preserves both license texts as shipped upstream)

Structured JSON logging. See python-skill-script-style-requirements.md
§"Structured logging".

---

## `jsoncomment`

- **Upstream:** Dmitry-Me/JsonComment
  (https://github.com/Dmitry-Me/JsonComment)
- **License:** MIT
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/jsoncomment/LICENSE`

JSONC (JSON-with-comments) parser. Used for `.vendor.jsonc`
and other livespec config files that benefit from inline
comments.

---

## `typing_extensions` (shim)

- **Upstream:** python/typing_extensions
  (https://github.com/python/typing_extensions)
- **License:** Python Software Foundation License (PSF-2.0)
- **Verbatim license file:** `.claude-plugin/scripts/_vendor/typing_extensions/LICENSE`

Shim re-exporting `override` and `assert_never` from the
standard library equivalents available in Python 3.10+. Per
v013 M1: livespec uses `from typing_extensions import override,
assert_never` uniformly so pyright's `reportImplicitOverride`
diagnostic and `check-assert-never-exhaustiveness` recognize a
single canonical import path. The shim's `upstream_ref` (in
`.vendor.jsonc`) records the upstream `typing_extensions`
release whose `override` / `assert_never` semantics the shim
faithfully replicates.
