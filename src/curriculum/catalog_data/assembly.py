"""Subject assembly for the Active Inference curriculum DAG."""

from __future__ import annotations

from ..model import Subject
from ..normalize import normalize_graph
from .subjects_canopy import canopy_subjects
from .subjects_extensions import extension_subjects


def build_subject_list() -> list[Subject]:
    return normalize_graph(canopy_subjects() + extension_subjects())
