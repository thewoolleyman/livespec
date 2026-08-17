---
topic: out-of-band-edit-2026-08-17t16-20-50z
author: livespec-doctor
created_at: 2026-08-17T16:20:50Z
---

## Proposal: out-of-band-edit-2026-08-17t16-20-50z

doctor detected drift between HEAD-active spec content and the
HEAD-history-vN snapshot; this auto-backfill records the active
state as the new canonical version.

### Proposed Changes

```diff
--- history/vN/non-functional-requirements.md
+++ active/non-functional-requirements.md
@@ -449,7 +449,7 @@
 
 Each pi Driver binding MUST be thin: it reads the named core prose file completely, follows that prose for behavior and failure handling, invokes the named wrapper when wrapper-backed, and does not copy operation-specific prose sections. The pi Driver carries all eight operations; the mutating subset is gated on the pi footgun-guard extension per `contracts.md` §"Driver-shipped hooks". The detailed pi mapping for orchestrator-plugin commands is owned by each orchestrator plugin's own spec, consistent with §"pi dogfooding compatibility".
 
-pi compatibility verification is performed with separate pi processes against the installed distributed Driver. The acceptance bar is: the committed `.pi/settings.json` carries both package entries (core and the pi Driver), the packages are present in the project's `.pi/git/` install locations (or the user-scope equivalents), AND a non-interactive `pi -p` invocation with trust established drives a `/livespec:*` operation through the pi Driver and core prose WITHOUT relying on any repo-local adapter directory or an `AGENTS.md` mapping. The expected result is that pi names the bound core prose file (`.claude-plugin/prose/<name>.md`) and, for wrapper-backed operations, the matching `.claude-plugin/scripts/bin/...` wrapper it invokes. A separate human-discoverability claim MUST drive pi's interactive skill surface (the `/skill:` command completion or the startup skills listing) and verify the `livespec-<operation>` skills appear. Temporary pi package registrations used for testing MUST be removed after the test unless the user explicitly asks to keep them.
+pi compatibility verification is performed with separate pi processes against the installed distributed Driver. The acceptance bar is: the committed `.pi/settings.json` carries the core, pi Driver, and orchestrator package entries, the packages are present in the project's `.pi/git/` install locations (or the user-scope equivalents), AND a non-interactive `pi -p` invocation with trust established drives a `/livespec:*` operation through the pi Driver and core prose WITHOUT relying on any repo-local adapter directory or an `AGENTS.md` mapping. The expected result is that pi names the bound core prose file (`.claude-plugin/prose/<name>.md`) and, for wrapper-backed operations, the matching `.claude-plugin/scripts/bin/...` wrapper it invokes. A separate human-discoverability claim MUST drive pi's interactive skill surface (the `/skill:` command completion or the startup skills listing) and verify the `livespec-<operation>` skills appear. Temporary pi package registrations used for testing MUST be removed after the test unless the user explicitly asks to keep them.
 
 ### Cross-repo coordination — pin-and-bump
 
@@ -1441,7 +1441,7 @@
 
 ### Scenario: pi drives a spec-side operation through the installed packages
 
-Given a livespec-governed project whose committed `.pi/settings.json` declares the core package and the pi Driver package at the release branch ref
+Given a livespec-governed project whose committed `.pi/settings.json` declares the core package, the pi Driver package, and the orchestrator package at the release branch ref
 
 And a pi project-trust decision is established for the project
 
@@ -1453,7 +1453,7 @@
 
 ### Scenario: an untrusted non-interactive pi invocation resolves no project packages
 
-Given a livespec-governed project whose committed `.pi/settings.json` declares the core and pi Driver packages
+Given a livespec-governed project whose committed `.pi/settings.json` declares the core, pi Driver, and orchestrator packages
 
 And no pi project-trust decision exists for the project and the global default is not always-trust
 
```
