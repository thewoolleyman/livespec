"""End-to-end integration test package.

Per SPECIFICATION/contracts.md §"E2E harness contract": this package
houses the mock harness (fake_claude.py) and the pytest test suite
(test_*.py) for the livespec E2E integration tier.

Mode selected by LIVESPEC_E2E_HARNESS env var (mock | real).
"""

__all__: list[str] = []
