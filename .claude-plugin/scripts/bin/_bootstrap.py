"""Pre-livespec-import bootstrap: sys.path setup + Python version check.

Imported by every bin/*.py wrapper before any livespec import. Lives under
bin/ so raise SystemExit is permitted by check-supervisor-discipline.
"""

import sys
from pathlib import Path


def bootstrap() -> None:
    if sys.version_info < (3, 10):
        sys.stderr.write("livespec requires Python 3.10+; install via your package manager.\n")
        raise SystemExit(127)
    bundle_scripts = Path(__file__).resolve().parent.parent
    bundle_vendor = bundle_scripts / "_vendor"
    for path in (bundle_scripts, bundle_vendor):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
