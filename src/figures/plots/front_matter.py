"""Front-matter figure entry points (re-export split modules)."""

from .front_matter_atlas import (
    _longest_path_skills,
    _sample_skill_names,
    _skill_name_atlas_payload,
    _skill_name_tokens,
    _spine_label_indices,
    plot_skill_name_atlas,
)
from .front_matter_cover import plot_active_skillference_cover

__all__ = [
    "_longest_path_skills",
    "_sample_skill_names",
    "_skill_name_atlas_payload",
    "_skill_name_tokens",
    "_spine_label_indices",
    "plot_active_skillference_cover",
    "plot_skill_name_atlas",
]
