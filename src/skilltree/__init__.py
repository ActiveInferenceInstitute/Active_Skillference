"""SkillTree integration layer for the Active Inference micro-learning platform.

Public API:

* model    — SkillTree-native dataclasses (Project → Subject → Skill, quizzes, deps)
* exporter — curriculum graph → SkillTree project (+ deterministic JSON export)
* client   — minimal REST client for the SkillTree admin + report API
* seeder   — drives a client to create an exported project in the right order
"""

from __future__ import annotations

from src.skilltree.client import SkillTreeClient, SkillTreeClientError
from src.skilltree.exporter import (
    CurriculumGraphLike,
    ExportError,
    export_project,
    export_to_json,
)
from src.skilltree.local_auth import (
    DEFAULT_LOCAL_LEARNER_ID,
    DEFAULT_LOCAL_STATE_DIR,
    LOCAL_TOKEN_ENDPOINT,
    BootstrapResult,
    LocalAuthDescription,
    LocalSkillTreeAuthError,
    LocalSkillTreeState,
    SkillTreeSessionClient,
    describe_local_auth,
    ensure_local_skilltree_auth,
    fetch_local_skilltree_token,
)
from src.skilltree.model import (
    Quiz,
    QuizQuestion,
    SkillDependency,
    SkillTreeModelError,
    SkillTreeProject,
    SkillTreeSkill,
    SkillTreeSubject,
)
from src.skilltree.seeder import seed
from src.skilltree.summary import (
    ExportSummary,
    SkillTreeSummaryError,
    summarize_export_payload,
    summarize_project,
)

__all__ = [
    "DEFAULT_LOCAL_LEARNER_ID",
    "DEFAULT_LOCAL_STATE_DIR",
    "LOCAL_TOKEN_ENDPOINT",
    "BootstrapResult",
    # exporter
    "CurriculumGraphLike",
    "ExportError",
    "ExportSummary",
    "LocalAuthDescription",
    "LocalSkillTreeAuthError",
    "LocalSkillTreeState",
    "Quiz",
    "QuizQuestion",
    "SkillDependency",
    # client
    "SkillTreeClient",
    "SkillTreeClientError",
    "SkillTreeModelError",
    "SkillTreeProject",
    "SkillTreeSessionClient",
    # model
    "SkillTreeSkill",
    "SkillTreeSubject",
    "SkillTreeSummaryError",
    "describe_local_auth",
    "ensure_local_skilltree_auth",
    "export_project",
    "export_to_json",
    "fetch_local_skilltree_token",
    # seeder
    "seed",
    "summarize_export_payload",
    "summarize_project",
]
