---
topic: github-app-request-budget
author: claude-opus-5
created_at: 2026-07-28T00:07:19Z
---

## Proposal: The fleet App's request budget is a finite shared resource that MUST be observable

### Target specification files

- non-functional-requirements.md

### Summary

§"Constraints" specifies the fleet GitHub App's identity, permission set and installation scope, but is silent on its **request budget**. That budget is a single 5000/hour primary `core` bucket shared by every repo the App is installed on, it has been observed fully exhausted in production, and while it is empty every credentialed GitHub operation across the whole fleet fails identically. Add a **GitHub App request budget** rule making the budget a named finite shared resource whose consumption MUST be observable over time, and requiring that automation distinguish exhaustion from failures it resembles rather than treating a 403 as a generic error.

### Motivation

On 2026-07-26 the fleet App installation's `core` bucket was measured at `x-ratelimit-used: 5000`, `x-ratelimit-remaining: 0`, and a factory dispatch died in sandbox setup as a result. Three properties make this worth specifying rather than fixing locally.

**It is fleet-scoped by construction, so no consumer can own it.** §"Canonical source" already establishes "one canonical App private key shared by all fleet members", and the installation was verified on 2026-07-28 (`GET /installation/repositories`) to cover exactly the nine fleet members named in `.livespec-fleet-manifest.jsonc`. Every member draws on one bucket; no member can see the other eight's consumption. A rule that lives in any one repo's spec cannot bind the resource.

**The failure is silent and self-erasing, which is the class this specification already legislates against.** The bucket refills hourly, so an exhaustion leaves no standing evidence: measured 5000/5000 used at 20:27:16Z and 10 used 68 seconds later. A dispatch dies, a work-item strands, and by the time anyone investigates every manual reproduction succeeds and the bucket reads healthy. Post-hoc sampling is structurally incapable of diagnosing it; only a recorded signal can.

**It is misdiagnosed by default, and the natural reading is backwards.** Exhaustion returns `403`, which reads as a permissions failure — but an installation token is not denied these requests; it is being *billed* for them. The counter-intuitive shape: a credentialed request for a public resource FAILS while the anonymous request for the identical resource SUCCEEDS in the same second from the same egress IP, because anonymous requests draw on a different bucket. Adding a credential can strictly reduce the set of requests that succeed. Two separate investigations reached the wrong conclusion in this same direction before measurement settled it.

Deliberately **not** proposed here: any specific mitigation (back-off policy, per-tenant installations, decoupling further consumers). Nothing in the fleet can currently answer "what spent the budget", GitHub does not attribute primary-limit consumption per endpoint or caller, and the plausible causes imply incompatible remedies. Specifying observability first is what makes a later mitigation choosable on evidence rather than guessed. Tracked as `livespec-j49m`.

This proposal adds no new `## ` heading — it inserts a bolded rule block inside the existing §"Constraints" section — so it carries no `tests/heading-coverage.json` co-edit obligation.

### Proposed Changes

In `non-functional-requirements.md` §"Constraints", insert a new bolded rule block **GitHub App request budget** immediately after the existing **GitHub App permission set** block:

**GitHub App request budget.** A conforming automation App's request budget is a FINITE SHARED RESOURCE, not an ambient capability: GitHub meters an App installation's REST (`core`) and GraphQL (`graphql`) primary rate limits as separate hourly buckets scoped to the INSTALLATION, so every repo an App is installed on draws on the same buckets and any one consumer can starve all the others. The fleet's own installation is therefore a shared fleet resource across all members listed in `.livespec-fleet-manifest.jsonc`, and an adopter's App is a shared resource across that adopter's repos. Consumption of that budget MUST be observable over time: a conforming tenant MUST record installation rate-limit state (at minimum `used`, `remaining` and `reset`, per bucket) on a recurring basis to a durable local signal, so that a later exhaustion is diagnosable from the recorded burn curve rather than from live sampling that arrives after the hourly window has rolled and the evidence has refilled away. The sampling endpoint (`GET /rate_limit`) does not itself consume budget, so this observability obligation costs nothing against the resource it measures. Automated GitHub paths MUST distinguish budget exhaustion — a `403` carrying `x-ratelimit-remaining: 0` and naming the exhausted bucket in `x-ratelimit-resource` — from the two failures it resembles and MUST NOT report it as either: a permissions failure (a conforming installation token is not denied these requests; a malformed or expired credential returns `401`) or a secondary rate limit (which returns `403` without zeroing `x-ratelimit-remaining`). A path that surfaces exhaustion as a generic credential error is non-conforming, because it sends every future investigation toward the credential rather than toward the budget. Consumers that do NOT require the App identity — notably third-party public-resource fetches such as toolchain release-metadata lookups — SHOULD run unauthenticated rather than spend installation budget, since an anonymous request for a public resource draws on a different bucket and adding the credential can strictly reduce the set of requests that succeed.
