---
name: feedback-be-more-autonomous
description: Stop asking confirmation questions for choices the user has already implicitly answered through their directives. Default to executing the obvious next step rather than pausing.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d2e1550c-8a13-4b97-bd9c-90858a6bdab2
---

When the user gives a clear directive (especially one expressed with frustration at being asked an obvious question), the implicit answer to any pending sub-question that flows from that directive is also given. Do not re-ask. Just execute.

**Why:** Twice in one session the user pushed back on me asking too many questions:
- First: I asked "should I commit and push?" after the user had separately asked me to land changes "on master". Their response: "Why is this even a question. Why would I want you to leave a dirty, unresolved state?"
- Second: When I started executing on the implicit answer, they asked "What are you doing? Weren't you in the middle of asking me some questions and we still had one left? Why didn't you just start doing stuff?"

The pattern is: I treat every degree of freedom as something to confirm, when in fact the user expects me to deduce the obvious answer from context and proceed. Asking the second question after they already answered the first one with a directive that obviously covers both feels to them like I'm not paying attention.

**How to apply:**

- If the user's response to question N+1 also implies the answer to question N+2 that I was about to ask, just answer it myself and execute.
- If the user expresses frustration with a question (e.g., "Why is this even a question"), do NOT respond by re-asking; respond by executing the obvious-from-context answer and proceeding.
- If I'm working autonomously on a clear directive and an unanswered AskUserQuestion item from a prior batch is still hanging, decide whether the user's subsequent directive resolved it (almost always yes — that's why they didn't answer it explicitly) and proceed. Do NOT re-prompt.
- Confirmation gates I should KEEP: (a) scope choices that genuinely could go multiple ways, (b) destructive / high-blast-radius actions that the user hasn't pre-authorized in this session.
- Confirmation gates I should DROP: "should I commit?", "should I push?", "should I land this on master?" — these all follow automatically from the [[feedback-worktree-discipline]] rule once the user has set up a worktree-bound task.

The autonomy expectation pairs with [[feedback-worktree-discipline]]: the user expects me to drive the full worktree → PR → merge → cleanup cycle on clear directives, without per-stage confirmation.
