"""Scholarship figure entry points (re-export split modules)."""

from .scholarship_coverage import plot_scholarship_coverage
from .scholarship_source_health import plot_scholarship_source_health
from .scholarship_source_map import plot_open_science_source_map

__all__ = [
    "plot_open_science_source_map",
    "plot_scholarship_coverage",
    "plot_scholarship_source_health",
]
