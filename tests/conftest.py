"""Pytest configuration for Active Skillference tests."""

import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ AND the monorepo root to path so the documented per-project pytest command
# works from a clean environment. The project pyproject's `pythonpath` is
# project-relative and omits the monorepo root, so without this any test that exercises
# a script importing `infrastructure` (e.g. the render preflight) would collect-error.
# The project lives at projects/<lifecycle>/<name>/ inside the template monorepo, so the
# monorepo root is three levels above ROOT (reached via the template-tracked path).
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
for _path in (REPO_ROOT, SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)
