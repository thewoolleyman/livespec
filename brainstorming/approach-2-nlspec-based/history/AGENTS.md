# history/ orientation

Per-version snapshots of `PROPOSAL.md` and the `proposed_changes/`
files that drove each revision. Each `vNNN/` directory is **frozen
forever** — never modified, even when new versions are added.

## Structure

```
history/
├── README.md                          (frozen at v021; historical
│                                       directory description)
├── vNNN/
│   ├── PROPOSAL.md                    (snapshot at vNNN)
│   └── proposed_changes/
│       └── *.md                       (revision authoring files for
│                                       this version)
└── ... (one vNNN/ directory per version)
```

## Latest version

`v022/PROPOSAL.md` is currently the latest snapshot. The bootstrap
skill reads it to verify Phase 0's byte-identity check against
`brainstorming/approach-2-nlspec-based/PROPOSAL.md`.

## How new versions are created

The bootstrap skill's halt-and-revise sub-flow handles version
bumping mechanically (per Plan §8). It computes the next vNNN, asks
for revision shape (direct overlay vs full critique-and-revise),
walks through authoring revision file(s), applies edits to
`PROPOSAL.md`, snapshots to `history/vNNN/`, and updates the plan's
Version basis section.

After Phase 0 freeze, no new versions are created. All further
evolution happens in `SPECIFICATION/` via the governed
propose-change/revise loop.

## After bootstrap completes

Stays in place as historical reference. The production app does not
reference this directory.
