---
topic: live-known-empty-probe
created_at: 2026-08-11T00:00:00Z
---

# KNOWN-EMPTY live probe — DO NOT MERGE

This file exists only to drive the KNOWN-EMPTY leg of the
`livespec-jvdvx4.13` acceptance. It is shaped like a plain
`propose-change` FILING: it lands under
`SPECIFICATION/proposed_changes/`, which means it touches the configured
spec root but RATIFIES NOTHING, so the derived stem set is legitimately
empty.

That is the exact shape that crashed the shipped workflow. The step's
runner shell is `/usr/bin/bash -e {0}`, a no-match `grep` exits 1, and
`pipefail` propagated that into the assignment, killing the step before
it produced any output. The KNOWN-EMPTY branch was therefore unreachable
in production rather than merely untested, and the 2026-05-26 cadence
fix was broken for every plain filing.

The required observation is that the run CONCLUDES SUCCESS, that the
policy step EMITS ITS OWN KNOWN-EMPTY line, and only then that
auto-merge is registered. A silent exit 1 is indistinguishable from a
pass if the only check is that auto-merge is off, which is why all three
are checked in that order.

This pull request is closed and its branch deleted as soon as the
observation is recorded. It must never merge.
