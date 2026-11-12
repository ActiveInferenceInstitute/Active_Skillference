"""Pytest configuration for Active Skillference tests."""

import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Keep the project root and src/ importable when pytest is invoked directly: the
# pyproject `pythonpath` already provides both, but a bare `pytest` started from a
# subdirectory would otherwise miss them. The project is self-contained — there is no
# outer repository whose root has to be added.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
for _path in (ROOT, SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)
