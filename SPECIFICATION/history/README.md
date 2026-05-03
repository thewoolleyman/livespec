# History

This directory holds the immutable per-revision snapshots of the
specification. Each `vNNN/` subdirectory contains a byte-identical
copy of every spec file as it stood when revision `vNNN` was
finalized. Versions are contiguous starting at `v001`. Each
`vNNN/proposed_changes/` subdirectory contains the proposed-change
files plus paired `-revision.md` records that drove that revision.
The directory is skill-owned: `livespec` writes new versions on
`/livespec:revise`, `/livespec:prune-history` removes the oldest
contiguous block down to a caller-specified retention horizon, and
the doctor static phase enforces version contiguity plus
revision-pairing invariants.
