# Corrections to deferrals D3 and D4 — 2026-08-20

Two claims in `2026-08-20-measured-state.md` were wrong in ways that
change what the deferrals argue. Both were surfaced by the core
`livespec-foreman` seat after that note was committed, and both were
re-verified here before being recorded.

Correction 2 then had to be corrected in turn, and that second round is
the more instructive of the two — see "A correction to this correction"
below.

## Correction 1 — D4's instance was CLOSED BY A FIX, not expired

**What the original note said.** That the peer's claim about commit
`52b5c30` being "on master and in no release" did not survive
re-measurement, and that *"the peer's measurement expired between
writing and reading, which is itself an instance of the plan's subject
matter."*

**What actually happened.** The measurement did not drift. The same seat
that diagnosed the defect also remediated it, and the remediation is
what moved the ref. Verified here:

| PR | Repo | Merged | Title |
|---|---|---|---|
| #549 | `livespec-driver-claude` | 2026-08-20T11:14:48Z | `fix(skill): carry --only-topic in the revise invocation forms` |
| #55 | `livespec-driver-pi` | 2026-08-20T11:16:21Z | same |
| #506 | `livespec-driver-codex` | 2026-08-20T11:23:14Z | same |

All three are MERGED, all hours before this plan's measurement. The
causal chain: the original fixes were `docs(...)`-typed and cut no
release; the `fix:`-typed follow-ups did cut one; that release swept up
the earlier `docs(...)` commits including `52b5c30`, which is why
`livespec-driver-claude`'s `release` ref moved `ac4c58b` → `263cd4f`.
This is exactly the seam `CLAUDE.md` already documents under dogfooding
pins — a behavior-changing commit reaches siblings only on the next
`feat:`/`fix:` release.

**Why the distinction changes D4's argument, which is the whole point of
recording it.** "The instance expired" and "the instance was closed by
the fix" argue in opposite directions:

- *Expired* would suggest the defect is self-limiting — state drifts,
  releases happen, undelivered commits get swept up eventually. That
  argues for leaving D4 deferred.
- *Closed by a fix* shows the opposite. Delivery was restored only
  because a human noticed the shipped bytes were stale and hand-authored
  three `fix:`-typed commits across three repos **for the sole purpose of
  triggering a release**. Nothing mechanical detected the condition and
  nothing mechanical would have resolved it. That is precisely this
  plan's disease, and it argues **for admitting D4 as a carrier**, not
  against.

The recommendation to the maintainer is accordingly to admit D4. The
decision remains theirs.

## Correction 2 — D3 mis-states the guard defect, in a way that would send R1 down the wrong path

**What the original note said.** That `github_rate_limit_guard` "denies
`gh api --cache`, the exact remedy its own denial message prescribes."

**That is true but is not the mechanism.** The original note implied the
trigger is something about caching; it is not. The cache flag is never
inspected on any path — `_GH_API` captures a call's arguments only to
test them for a mutating `-X`/`--method` value. So the denial message
prescribes a remedy the code has no way to recognise.

### A correction to this correction — I read the wrong build

The first version of this section characterised the matcher as firing on
a loop token **anywhere in the command string**. That was drawn from a
real file that was not the running one. A `find` over
`~/.claude/plugins/` returns **fifteen** cached driver-claude builds of
this hook, and taking the first result picked `53a7d5b097d4`, a stale one
carrying a superseded pattern that matched the bare word with no
positional anchor at all.

The build this session actually loads is `ac4c58bf5086` — named in the
session's own startup output — and it anchors the keyword to command
position, matching only at the start of a line, after a `;`/`&`/`|`
separator, or after `do`/`then`, with `MULTILINE` enabled. The hook's own
comment says the anchor was added deliberately, because matching the bare
word *"denied any `gh` command whose text merely contained 'for',
'while', 'until' or 'sleep' — ordinary English that turns up constantly
in PR titles, paths and jq filters."*

**This is a fresh instance for `.ai/verifying-against-the-right-source.md`,
and a nastier one than most it already records**, because nothing looked
wrong: the file was real, the path was plausible, the code parsed, and
every observation in this plan stayed consistent with it. Fifteen builds
of the same file sit side by side and taking the first chooses
arbitrarily among them. The right source was named in this session's own
startup output the whole time.

**What the anchor actually buys, measured rather than argued.** Running
the live pattern against each observed case and attributing which
sub-clause fired:

| Case | Denied? | Fired via |
|---|---|---|
| Prose describing the regex's own alternation | yes | separator clause |
| A `gh` read piped into a multi-line `python3 -c` | yes | line-start |
| Heredoc containing a real shell loop | yes | line-start |
| A bare cached `gh api` call, no loop token | **no** | — |
| Prose with a loop word only mid-line | **no** | — |

The last row **disconfirms the "anywhere in the string" claim directly**,
which is why it is retracted rather than softened.

**Where the peer's account also needs one refinement.** The core seat
attributed the anchor's weakness entirely to `MULTILINE` making the
start-of-string anchor match at every line start. That explains rows 2
and 3. It does not explain row 1: this plan's own pull-request body fired
via the **separator** clause, because prose describing regex alternation
puts a loop keyword directly after a pipe character. The anchor buys even
less than "almost nothing" — a separator inside quoted prose is enough.

**The root cause both accounts converge on, and it is the right one.**
The matcher has no lexical awareness: it cannot distinguish shell syntax
from text, so a loop keyword at a command-like position inside a quoted
`-c` string, a heredoc, or ordinary English is indistinguishable from a
real shell loop. Every `gh pr` subcommand is likewise classified a read,
mutations included, because the read pattern matches the subcommand
family rather than the verb.

**Empirically confirmed while gathering this plan's research.** A single
`gh` read piped into a multi-line Python one-liner was denied: one call,
no shell loop, the only trigger a loop keyword at the start of a line
inside the quoted Python. Meanwhile a bare cached read issued alone
passed. The core seat independently hit the same thing with a cached read
sitting beside other commands, and its disconfirming pair is the
discriminating evidence neither of us gathered first: a batch containing
**two** shell loops and **no** `gh` call passed, which proves the `gh`
read is the discriminator rather than the batching.

**Where the peer's proposed remedy is wrong, and R1 must not adopt it.**
The core seat initially concluded the working remedy is "one call per
step, which needs no skill-documented screen", and has since withdrawn
it. It is right for an *incidental* denial — a cached read that happens
to sit near a loop keyword. It is **wrong for the fleet-wide sweep R1 has
to perform**. Issuing fourteen per-repo reads as fourteen separate steps
is still a looped GitHub read; it merely spreads the loop across tool
calls where the regex cannot see it. `needs-attention-internal/SKILL.md`
addresses this case directly and denies it by name:

> **⛔ RUNNING THAT COMMAND ONCE PER MEMBER IS DENIED — use the ONE-CALL
> SCREEN below first.**

So D3 stands as written in its operative half: **R1's implementation
must use the one-call GraphQL screen**, generated from
`.livespec-fleet-manifest.jsonc` rather than hand-written, so the member
list cannot silently fork from the manifest. What changes is only the
*characterization* of the guard's defect, above.

**Three live reproductions, all from authoring this plan.** The
pull request carrying these corrections was denied on its first attempt,
because its body text — describing the guard — contained what the guard
matches on. The rewrite of this very section was denied for the same
reason. In both, no `gh` read was looped; the prose was. That is the most
legible statement of the defect available: the guard read *prose about
loops* as loops.

**The second-order harm, worth stating because it is the reason this
correction is in the plan at all.** A guard whose denial message
prescribes a remedy it cannot detect, whose true remedy for fleet work it
also cannot detect, and whose one *detectable* remedy — splitting the
loop across invocations — is evasion, teaches the wrong lesson. Both
operators who hit it on 2026-08-20 reached for a workaround before
reaching for the correct screen. That is the shape
`.ai/ci-gate-discipline.md` cares about, and it is separable from whether
the rate-limit protection itself is worth keeping. It remains owned
elsewhere (`livespec-driver-claude-mu5`) and is not admitted as a carrier
here, but if it ever is, this is the argument.

## One item needs no action — recorded so nobody re-opens it

The `resolve_core_root.py` predicate defect, which arrived here on a
misrouted message and which the previous handoff said should be
re-routed to the `resolve-core-root-predicate` seat, needs **no filing
and no routing**. Per the core seat it is already on file six times in
the `livespec-driver-claude` tenant — anchor `livespec-driver-claude-d7d`,
duplicates `-zgqrta` / `-4xc` / `-zeh4ft`, guard half `-tun`, and `-6o4`
(P1, ready) which already names `livespec-orchestrator-beads-fabro` as
the second false positive. Plan `resolve-core-root-predicate` (epic
`livespec-driver-claude-cezqks`) owns both halves. Core has since relayed
its clause-lockstep observation to that seat directly. Nothing is owed by
this plan.
