---
proposal: expand-coverage-exclude-also-to-match-impl.md
decision: accept
revised_at: 2026-05-27T06:47:11Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Pure NFR catchup to the impl: the existing pyproject.toml [tool.coverage.report].exclude_also config carries 7 structural patterns but NFR §"Code coverage thresholds" enumerated only 4. The PC adds the 3 missing patterns (raise ImportError, if __name__ == .__main__.:, sys.path.insert) to bring NFR into agreement with pyproject.toml. No code change required. H2 set of NFR unchanged; no tests/heading-coverage.json update needed.

## Resulting Changes

- non-functional-requirements.md
