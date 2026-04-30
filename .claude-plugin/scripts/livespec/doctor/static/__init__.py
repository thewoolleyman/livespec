"""Static-doctor check registry.

Per PROPOSAL.md §"`doctor` → Static-phase structure" lines
2507-2512, this package's `__init__.py` holds the registry of
implemented static-phase check modules. Each check is registered
explicitly (no dynamic discovery); adding or removing a check is
one explicit edit to this file.

v033 D5b second-redo cycle 103: stubbed down to the canonical
no-op preamble. The prior content (cycle 28's eight-check
registry) referenced check modules and the `livespec.context`
module that haven't been re-authored under TDD yet, so the file
couldn't be imported successfully — `from livespec.doctor import
static` raised ModuleNotFoundError on the first import statement.
The minimum-viable form here lets the namespace be discovered
while subsequent consumer-pressure cycles re-author each check
module + its registry entry as outside-in tests demand them.

The v033 D1 mirror-pairing-rule's `__init__.py` carve-out exempts
a file whose body is exactly `from __future__ import annotations`
+ `__all__: list[str] = []` from requiring a paired non-trivial
test, but the package itself still warrants an importability test
under `tests/livespec/doctor/static/test___init__.py` so the
namespace contract is pinned — this is what the cycle's Red
captured.
"""

from __future__ import annotations

__all__: list[str] = []
