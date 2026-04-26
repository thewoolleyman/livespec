# livespec/doctor/static/

Per-check modules. Each file exports `run(ctx) -> IOResult[Finding,
E]` where `E` is any `LivespecError` subclass. Bugs in a check
propagate as raised exceptions to the supervisor's bug-catcher and
result in exit 1.

The slug ↔ module-filename ↔ `check_id` mapping is recorded
literally in `__init__.py`. JSON slug `out-of-band-edits` ↔ module
filename `out_of_band_edits.py` ↔ check_id `doctor-out-of-band-edits`.
There is no slug-to-filename conversion loop; the registry's import
statements name both forms.

Checks under this directory are pure with respect to side effects
EXCEPT `out_of_band_edits.run`, which has a narrow auto-backfill
write path to `<spec-root>/proposed_changes/` and
`<spec-root>/history/` per PROPOSAL.md §"Static-phase checks".
