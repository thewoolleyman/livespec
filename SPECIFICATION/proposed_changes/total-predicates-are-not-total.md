---
topic: total-predicates-are-not-total
author: claude-opus-5
created_at: 2026-08-02T11:30:00Z
---

## Proposal: v184's governing example is factually wrong — the filesystem predicates are NOT total

### Target specification files

- non-functional-requirements.md

### Summary

§"ROP composition" §"What counts as an I/O boundary" (ratified as **v184**) states the correct CRITERION — an I/O boundary is a primitive at which a failure can ORIGINATE — and then names, as its **governing case**, an example that measurement refutes: *"the filesystem TOTAL PREDICATES (`Path.exists`, `Path.is_file`, `Path.is_dir`, and their siblings that catch `OSError` internally and answer `False`) ... are total by the standard library's own contract"*. **They are not.** They catch a fixed ERRNO ALLOWLIST, not `OSError`, and a `PermissionError` propagates out of every one of them. **Correct the example; leave the criterion untouched.**

### Motivation

**THE CRITERION IS RIGHT AND IS NOT AT ISSUE.** What is wrong is one factual claim inside it, and that claim is load-bearing: it is the only concrete case the rule names, it is what an implementer will reach for first, and it points the implementation in exactly the wrong direction.

**MEASURED against CPython 3.10.16 — the fleet's `requires-python` floor, not a newer interpreter — running as an ordinary user (uid 1000, NOT root).** Every probe is positive-controlled, so a negative result is credible rather than blind:

```
# a path under a chmod-000 directory (EACCES)
exists()      -> RAISES PermissionError
is_file()     -> RAISES PermissionError
is_dir()      -> RAISES PermissionError
is_symlink()  -> RAISES PermissionError
is_fifo()     -> RAISES PermissionError
is_socket()   -> RAISES PermissionError

# POSITIVE CONTROL — the same six verbs on an ordinary missing path (ENOENT)
exists() is_file() is_dir() is_symlink() is_fifo() is_socket()  -> all return False
```

**AND THE MECHANISM IS IN THE STANDARD LIBRARY'S OWN SOURCE, so this is not an interpreter quirk.** `pathlib` defines:

```python
_IGNORED_ERROS = (ENOENT, ENOTDIR, EBADF, ELOOP)

def _ignore_error(exception):
    return (getattr(exception, 'errno', None) in _IGNORED_ERROS or
            getattr(exception, 'winerror', None) in _IGNORED_WINERRORS)
```

and each predicate is `try: ... except OSError as e: if not _ignore_error(e): raise`. **`EACCES` is absent from that tuple.** So the predicates are not total — they are total *with respect to four errnos*, which is a different and much weaker property. A failure genuinely CAN originate at them.

**WHY IT SURVIVED REVIEW, and it generalizes.** Every probe run on this question — including the ones that produced the v184 proposal — drove the predicates with only two adverse inputs: a MISSING path (`ENOENT`) and a path whose parent is a FILE (`ENOTDIR`). **Both are in the ignore list.** The one input class that separates "swallows everything" from "swallows four errnos" is the PERMISSION case, and it was excluded by a standing rule that a `chmod 000` probe proves nothing because the suite runs as root — **a rule that was true of the environment it was written for and false of the one the measurement was finally taken in.** A probe that cannot reach the distinguishing input cannot decide the question, and reporting its result as a determination is the manufactured-confidence shape this section exists to remove.

**THE CONSEQUENCE IS THAT v184's RELAXING HALF HAS ZERO MEMBERS.** v184 was ratified as a correction moving in BOTH directions. Measured against every verb a conforming implementation currently carries, **no verb is total**, so nothing leaves scope and the correction is purely a TIGHTENING. That does not weaken v184 — the tightening half was always the half that made it a fidelity fix rather than a relief — but a rule whose stated relaxing half is empty MUST say so, or every implementer will keep looking for the members it promises.

**AND IT REVERSES A DISPOSITION IN THE GOVERNED FLEET.** Two `livespec-dev-tooling` functions (`reconcile_beads_dir_perms`, `reconcile_beads_metadata_present`) were held OFF conversion on the strength of the refuted premise — their only direct primitives are `is_dir()` / `is_file()`. Under the corrected facts they are ordinary I/O boundaries at which a `PermissionError` can originate, and they MUST convert. **A rule that mis-states its own governing example does not merely mislead; it produces wrong dispositions that look justified.**

**Deliberately NOT proposed:** any change to the criterion, to the both-directions requirement, to the refusal of an enumerated verb list, to the store-no-claim obligation, or to the doubt-tightens rule. All were correct as ratified. Indeed **v184's own doubt-tightens rule already reaches the right answer** — this proposal makes the text stop contradicting it.

This proposal adds no new `## ` heading — it replaces a sentence and adds a bolded paragraph inside the existing §"ROP composition" section — so it carries no `tests/heading-coverage.json` co-edit obligation.

### Proposed Changes

In `non-functional-requirements.md` §"ROP composition", inside the **What counts as an I/O boundary** block, REPLACE the sentence beginning *"A primitive cannot fail when, for every input, it either returns a value or the language guarantees it does not raise: the filesystem TOTAL PREDICATES..."* through *"...rather than by the caller's discipline."* with the following, and append the second paragraph to the end of that block:

**A primitive cannot fail when, for every input, it either returns a value or the language guarantees it does not raise.** That guarantee MUST be established against the language's ACTUAL behavior, driven with the adverse inputs that distinguish a total primitive from a nearly-total one, and never inferred from a docstring or from a partial catch. **A primitive that swallows SOME failures is FAILABLE, not total**, and the distinction is not academic: a catch scoped to an ERRNO ALLOWLIST leaves every other errno propagating.

⛔ **AND THE EXAMPLE THIS RULE ORIGINALLY GAVE WAS WRONG, WHICH IS RECORDED HERE RATHER THAN QUIETLY REPLACED.** This rule was ratified naming the filesystem predicates — `Path.exists`, `Path.is_file`, `Path.is_dir` and their siblings — as TOTAL "by the standard library's own contract", and as the rule's governing case. **MEASURED against CPython 3.10.16 as an ordinary user, with a positive control in both directions: they all RAISE `PermissionError` on a path under an unreadable directory, and return `False` only for a missing path.** `pathlib` catches a fixed allowlist — `(ENOENT, ENOTDIR, EBADF, ELOOP)` — and re-raises everything else, `EACCES` included. They are total with respect to four errnos, which is a WEAKER property than total and does not satisfy this rule. **They are therefore I/O boundaries and MUST NOT be removed from any implementation's set on the strength of the retracted example.** The error survived because every probe of the question drove those predicates with a MISSING path and a path under a FILE — both in the ignore list — while the PERMISSION input that separates the two properties was never run. **A determination reached without the input that could refute it is not a measurement**, and this rule's own requirement to record each determination WITH its evidence exists to make that visible. It follows that this rule's RELAXING half currently has NO known members and the correction is, in practice, purely a TIGHTENING; that is a statement about the measured world, not a narrowing of the criterion, and a later implementer MUST re-derive it rather than inherit it.
