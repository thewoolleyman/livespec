# Corrections to deferrals D3 and D4 — 2026-08-20

Two claims in `2026-08-20-measured-state.md` were wrong in ways that
change what the deferrals argue. Both were surfaced by the core
`livespec-foreman` seat after that note was committed, and both were
re-verified here before being recorded.

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

**That is true but is not the mechanism**, and the imprecision matters
because it implies the trigger is something about caching. It is not.
Read from the hook source at
`hooks/github_rate_limit_guard.py`:

```python
_LOOP_OR_SLEEP = re.compile(rf"\b(?:for|while|until)\b|{_SHELL_SELECT}|\bsleep\b", re.IGNORECASE)
```

`_deny_reason` denies when that pattern matches **anywhere in the whole
command string** and any non-mutating `gh` read is present. The `--cache`
flag is never inspected at all. So the trigger is bare token
co-occurrence: a `for`, `while`, `until`, or `sleep` token anywhere in
the command — inside a piped Python one-liner, a quoted string, a
filename, a commit message — plus any `gh api` / `gh run` / `gh pr` read.

**Empirically confirmed while gathering this plan's research.** A single
`gh pr list ... | python3 -c "for p in json.load(...)"` was denied: one
`gh` call, no shell loop, and the only matching token was the `for` in
the piped Python. Meanwhile a bare `gh api --cache 60m ...` issued alone
passed. The core seat independently hit the same thing with a
`gh api --cache 2m` call batched alongside other commands.

**Where the peer's proposed remedy is wrong, and R1 must not adopt it.**
The core seat concluded the working remedy is "one call per step, which
needs no skill-documented screen." That is right for an *incidental*
denial — a cached read that happens to sit next to a `for` token. It is
**wrong for the fleet-wide sweep R1 has to perform**. Issuing fourteen
per-repo reads as fourteen separate steps is still a looped GitHub read;
it merely spreads the loop across tool calls where the regex cannot see
it. `needs-attention-internal/SKILL.md` addresses this case directly and
denies it by name:

> **⛔ RUNNING THAT COMMAND ONCE PER MEMBER IS DENIED — use the ONE-CALL
> SCREEN below first.**

So D3 stands as written in its operative half: **R1's implementation
must use the one-call GraphQL screen**, generated from
`.livespec-fleet-manifest.jsonc` rather than hand-written, so the member
list cannot silently fork from the manifest. What changes is only the
*characterization* of the guard's defect, above.

**The second-order harm, worth stating because it is the reason this
correction is in the plan at all.** A guard whose denial message
prescribes a remedy it then denies trains operators toward evasion — as
it did here, in this plan's own research-gathering. That cost is larger
than the rate-limit budget the guard protects. It remains owned
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
`livespec-driver-claude-cezqks`) owns both halves. Nothing is owed by
this plan.
