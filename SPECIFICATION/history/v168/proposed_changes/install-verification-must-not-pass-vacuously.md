---
topic: install-verification-must-not-pass-vacuously
author: claude-opus-4-8
created_at: 2026-07-19T07:10:19Z
---

## Proposal: Install verification must not pass vacuously on an empty enablement set

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The install-verification invariant added at history/v166 enumerates `enabledPlugins` without requiring that set to be non-empty, so a conforming check reports success for a project with nothing enabled and nothing installed. `claude plugin uninstall -s project` reaches that state by rewriting the committed settings file and emptying `enabledPlugins`. Require verification to fail on it, and require the settings file to be restored from version control before re-verifying.

### Motivation

Found by dogfooding the livespec-s2de remedy against the `homelab` adopter:
uninstall the three project-scope plugins, then re-run the newly documented
install path as a first-time adopter would.

Two defects surfaced, and they compose.

DEFECT A. `claude plugin uninstall <plugin> -s project` mutates the project's
COMMITTED `.claude/settings.json`. Observed: uninstalling the three plugins
rewrote the tracked file and emptied `enabledPlugins` to `{}`. (`claude plugin
install` also rewrites the file, though only cosmetically.) The contract and the
docs both treat that file as hand-authored, committed, governed config.

DEFECT B. The install-verification check landed by livespec-s2de PASSES
VACUOUSLY on an empty `enabledPlugins`, because it enumerates that dict and
succeeds on zero iterations. Observed directly: immediately after the uninstall
in Defect A, the documented snippet printed "OK: all enabled plugins installed
for /data/projects/homelab" and exited 0 for a project that had just been
stripped of all three plugins. It reported the true state (MISSING x3, exit 1)
only once `.claude/settings.json` was restored from git.

Composed, they reconstitute precisely the failure class livespec-s2de existed to
eliminate: uninstall silently empties the enablement declaration, and the check
whose entire purpose is to catch silent breakage then certifies the project
healthy. A remedy that reintroduces its own false negative is worse than no
remedy, because it converts an unknown gap into a trusted one.

The fixed predicate is verified by execution against three states: healthy
(OK, exit 0), uninstall-aftermath (DEFECT, exit 1), and enabled-but-not-
installed (MISSING, exit 1).

### Proposed Changes

One replacement in `SPECIFICATION/contracts.md` §"Plugin distribution", in the
install-verification paragraph. The REPLACE-TARGET exists verbatim and uniquely
in the live file.

REPLACE-TARGET:

    Enabled-without-installed, and installed-against-a-different-`projectPath`, are both defective states that any provisioning or currency tooling MUST detect and report loudly; neither may be inferred from a command's exit status.

REPLACEMENT:

    Enabled-without-installed, and installed-against-a-different-`projectPath`, are both defective states that any provisioning or currency tooling MUST detect and report loudly; neither may be inferred from a command's exit status. Verification MUST NOT pass vacuously: because the check above enumerates `enabledPlugins`, it succeeds on zero iterations when that set is empty, so a project declaring `extraKnownMarketplaces` while carrying an empty or absent `enabledPlugins` is ITSELF a defective state and MUST fail verification rather than report success. That state is reachable in normal operation — `claude plugin uninstall <plugin> -s project` rewrites the project's COMMITTED `.claude/settings.json` and empties `enabledPlugins` rather than merely dropping the install record — so an uninstall both dirties governed config and disarms a naive verification in one step; the settings file MUST be restored from version control before re-verifying.
