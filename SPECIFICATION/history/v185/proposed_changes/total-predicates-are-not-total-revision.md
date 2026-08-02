---
proposal: total-predicates-are-not-total.md
decision: accept
revised_at: 2026-08-02T07:12:33Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. v184 states the correct CRITERION — an I/O boundary is a primitive at which a failure can ORIGINATE — and then names, as its governing case, an example that measurement refutes. The filesystem predicates are NOT total: measured on CPython 3.10.16, the fleet's requires-python floor rather than a newer interpreter, running as an ordinary user, exists, is_file, is_dir, is_symlink, is_fifo and is_socket ALL raise PermissionError on a path under an unreadable directory, while the same six return False for an ordinary missing path. The probe was positive-controlled in both directions before either result was trusted. The mechanism is in the standard library's own source rather than inferred from behavior: pathlib defines an ignored-errno tuple of ENOENT, ENOTDIR, EBADF and ELOOP, and every predicate re-raises any OSError outside it, EACCES included. They are total with respect to four errnos, which is a strictly weaker property than total and does not satisfy this rule. Accepted rather than modified because the correction is exactly scoped: it replaces the refuted sentence, records the retraction with its evidence rather than quietly swapping the text, and changes NOTHING about the criterion, the both-directions requirement, the refusal of an enumerated verb list, the store-no-claim obligation, or the doubt-tightens rule. v184's own doubt-tightens rule already reached the right answer; this makes the text stop contradicting it. Two consequences are recorded because they are load-bearing rather than incidental: the rule's relaxing half has no known members, so in practice the correction is purely a TIGHTENING, and a live disposition in the governed fleet reverses, since two functions held off conversion on the refuted premise are ordinary I/O boundaries at which a PermissionError can originate. A rule that mis-states its own governing example does not merely mislead — it produces wrong dispositions that look justified, and this pass exists to stop that one propagating.

## Resulting Changes

- non-functional-requirements.md
