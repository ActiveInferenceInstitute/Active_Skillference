"""Extension and hardening subjects beyond the core canopy."""

from __future__ import annotations

from ..model import Subject
from .subjects_extensions_hardening import hardening_extension_subjects
from .subjects_extensions_pass5 import pass5_extension_subjects
from .subjects_extensions_review import review_extension_subjects
from .subjects_extensions_tracks import track_extension_subjects


def extension_subjects() -> list[Subject]:
    return (
        pass5_extension_subjects()
        + track_extension_subjects()
        + hardening_extension_subjects()
        + review_extension_subjects()
    )
