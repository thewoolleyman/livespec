---
topic: fix-bcp14-in-e2e-contract
author: unknown-llm
created_at: 2026-05-06T14:16:33Z
---

## Proposal: Fix BCP14 mixed-case keyword in E2E harness contract section

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The E2E harness contract section contains a standalone 'Must' word that trips the doctor-bcp14-keyword-wellformedness check. Rephrase to avoid the mixed-case keyword.

### Motivation

doctor-bcp14-keyword-wellformedness fails on contracts.md:170. The text describes a test that seeds a spec with a non-standard BCP14 normative-keyword capitalization, but the description itself uses 'Must' which trips the check.

### Proposed Changes

Rephrase line 170 from 'with a mixed-case Must trips' to 'containing a normative keyword in non-standard capitalization trips' to avoid the standalone mixed-case keyword.
