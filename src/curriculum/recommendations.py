"""Deterministic, graph-only path recommendations for the learner dashboard.

This module deliberately does not infer a learner state.  It accepts an optional
snapshot of completion and unsuccessful-attempt signals owned by SkillTree and
returns explainable candidates from the exported prerequisite graph.  With no
snapshot it returns a clearly labelled foundation-start view, which is useful for
inspection but is not personalization or evidence of learning effectiveness.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
from typing import Any

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{3,}")
_STOP_WORDS = frozenset(
    {
        "about",
        "after",
        "before",
        "from",
        "into",
        "that",
        "their",
        "these",
        "this",
        "with",
        "your",
    }
)


def recommend_next_skills(
    project: Mapping[str, Any],
    *,
    completed_skill_ids: Iterable[str] = (),
    unsuccessful_skill_ids: Iterable[str] = (),
    limit: int = 8,
) -> dict[str, Any]:
    """Return explainable prerequisite-frontier recommendations.

    ``completed_skill_ids`` and ``unsuccessful_skill_ids`` are intentionally
    caller-provided.  A live integration may pass signals retrieved from
    SkillTree; the local dashboard currently passes none and therefore exposes
    only a foundation-start prototype.  The function is pure with respect to
    learner state: it never writes progress, ranks learners, or changes the
    exported project.
    """
    if limit <= 0:
        raise ValueError("limit must be positive")
    skills, subjects, prerequisites, quizzes = _index_project(project)
    if not skills:
        return {
            "available": False,
            "signalSource": "none",
            "personalized": False,
            "completedSkillCount": 0,
            "recommendations": [],
            "boundary": _BOUNDARY,
            "error": "SkillTree project export is unavailable or malformed",
        }

    known_ids = set(skills)
    completed = {str(skill_id) for skill_id in completed_skill_ids} & known_ids
    unsuccessful = {str(skill_id) for skill_id in unsuccessful_skill_ids} & known_ids
    depths = _depths(known_ids, prerequisites)
    frontier = {
        skill_id
        for skill_id in known_ids - completed
        if not prerequisites[skill_id] or prerequisites[skill_id] <= completed
    }
    # Failed skills remain actionable even when the learner has not completed a
    # prerequisite.  They are presented as official quiz retakes, never as an
    # app-owned remediation state.
    candidates = frontier | (unsuccessful - completed)
    if not completed and not unsuccessful:
        signal_source = "none"
        personalized = False
    else:
        signal_source = "skilltree"
        personalized = True

    failed_concepts = set().union(
        *(
            _concepts(skills[skill_id], quizzes.get(_quiz_id(skills[skill_id])))
            for skill_id in unsuccessful
        )
    )
    rows: list[dict[str, Any]] = []
    for skill_id in sorted(candidates):
        skill = skills[skill_id]
        is_unsuccessful = skill_id in unsuccessful
        directly_remediates = bool(prerequisites[skill_id] & unsuccessful)
        concepts = sorted(
            _concepts(skill, quizzes.get(_quiz_id(skill))),
            key=lambda value: value,
        )[:6]
        concept_overlap = len(set(concepts) & failed_concepts)
        if is_unsuccessful:
            reason = (
                "SkillTree reported an unsuccessful attempt; retake the official quiz."
            )
            category = 3
        elif directly_remediates:
            reason = "This skill is the next prerequisite frontier after an unsuccessful attempt."
            category = 2
        elif skill_id in frontier:
            reason = "All exported prerequisites are satisfied; this is an available next skill."
            category = 1
        else:
            reason = "This foundational skill is an available starting point in the exported graph."
            category = 0
        rows.append(
            {
                "skillId": skill_id,
                "name": str(skill.get("name", skill_id)),
                "subjectId": subjects[skill_id]["subjectId"],
                "subjectName": subjects[skill_id]["name"],
                "depth": depths.get(skill_id, 0),
                "assessmentQuestionCount": len(quizzes.get(_quiz_id(skill), ())),
                "concepts": concepts,
                # Ordering is dependency-forward: topological depth (readiness) is the
                # primary term, so a satisfied frontier skill always precedes a deeper
                # candidate; the reason category and a bounded concept-overlap term are
                # secondary and can never overturn the depth ordering (overlap is
                # clamped far below the per-depth step). Ascending score == shallowest
                # first, then highest-priority category, then id for determinism.
                "score": depths.get(skill_id, 0) * 10_000
                - category * 100
                - min(concept_overlap, 9),
                "reason": reason,
                "officialSkillTree": _routes(
                    subjects[skill_id]["subjectId"],
                    skill_id,
                    _quiz_id(skill),
                ),
            }
        )
    rows.sort(key=lambda row: (int(row["score"]), str(row["skillId"])))
    return {
        "available": True,
        "signalSource": signal_source,
        "personalized": personalized,
        "completedSkillCount": len(completed),
        "recommendations": rows[:limit],
        "boundary": _BOUNDARY,
        "error": None,
    }


_BOUNDARY = (
    "Graph candidates are an offline prototype. SkillTree owns completion and quiz "
    "state; no latent learner state, efficacy, ranking, or autonomous tutoring is inferred."
)


def _index_project(
    project: Mapping[str, Any],
) -> tuple[
    dict[str, Mapping[str, Any]],
    dict[str, dict[str, str]],
    dict[str, set[str]],
    dict[str, tuple[Mapping[str, Any], ...]],
]:
    raw_subjects = project.get("subjects")
    raw_dependencies = project.get("dependencies")
    raw_quizzes = project.get("quizzes")
    if (
        not isinstance(raw_subjects, list)
        or not isinstance(raw_dependencies, list)
        or not isinstance(raw_quizzes, list)
    ):
        return {}, {}, {}, {}
    skills: dict[str, Mapping[str, Any]] = {}
    subjects: dict[str, dict[str, str]] = {}
    for subject in raw_subjects:
        if not isinstance(subject, Mapping):
            continue
        subject_id = str(subject.get("subjectId", ""))
        if not subject_id:
            continue
        subject_name = str(subject.get("name", subject_id))
        raw_skills = subject.get("skills", [])
        if not isinstance(raw_skills, list):
            continue
        for skill in raw_skills:
            if not isinstance(skill, Mapping):
                continue
            skill_id = str(skill.get("skillId", ""))
            if skill_id and skill_id not in skills:
                skills[skill_id] = skill
                subjects[skill_id] = {"subjectId": subject_id, "name": subject_name}
    prerequisites: dict[str, set[str]] = {skill_id: set() for skill_id in skills}
    for dependency in raw_dependencies:
        if not isinstance(dependency, Mapping):
            continue
        skill_id = str(dependency.get("skillId", ""))
        prerequisite_id = str(dependency.get("dependsOnSkillId", ""))
        if (
            skill_id in skills
            and prerequisite_id in skills
            and skill_id != prerequisite_id
        ):
            prerequisites[skill_id].add(prerequisite_id)
    quizzes: dict[str, tuple[Mapping[str, Any], ...]] = {}
    for quiz in raw_quizzes:
        if not isinstance(quiz, Mapping):
            continue
        quiz_id = str(quiz.get("quizId", ""))
        questions = quiz.get("questions", [])
        if quiz_id and isinstance(questions, list):
            quizzes[quiz_id] = tuple(
                question for question in questions if isinstance(question, Mapping)
            )
    return skills, subjects, prerequisites, quizzes


def _quiz_id(skill: Mapping[str, Any]) -> str:
    return str(skill.get("quizId", ""))


def _concepts(
    skill: Mapping[str, Any], questions: tuple[Mapping[str, Any], ...] | None
) -> set[str]:
    text = " ".join(
        [
            str(skill.get("name", "")),
            str(skill.get("description", "")),
            *(str(question.get("question", "")) for question in (questions or ())),
        ]
    ).lower()
    return {token for token in _TOKEN_RE.findall(text) if token not in _STOP_WORDS}


def _depths(
    skill_ids: set[str], prerequisites: Mapping[str, set[str]]
) -> dict[str, int]:
    indegree = {skill_id: len(prerequisites[skill_id]) for skill_id in skill_ids}
    dependents: dict[str, list[str]] = defaultdict(list)
    for skill_id, prereqs in prerequisites.items():
        for prerequisite_id in prereqs:
            dependents[prerequisite_id].append(skill_id)
    queue = deque(
        sorted(skill_id for skill_id, count in indegree.items() if count == 0)
    )
    depths = {skill_id: 0 for skill_id in skill_ids}
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for dependent in sorted(dependents[current]):
            depths[dependent] = max(depths[dependent], depths[current] + 1)
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
    if visited != len(skill_ids):
        # The export validator normally prevents this.  Keeping the recommendation
        # helper fail-closed avoids inventing a path if it is called on raw data.
        return {skill_id: 0 for skill_id in skill_ids}
    return depths


def _routes(subject_id: str, skill_id: str, quiz_id: str) -> dict[str, str]:
    subject_route = f"/subjects/{subject_id}"
    quiz_route = (
        f"{subject_route}/skills/{skill_id}/quizzes/{quiz_id}" if quiz_id else ""
    )
    return {
        "subjectRoute": subject_route,
        "skillRoute": f"{subject_route}/skills/{skill_id}",
        "quizRoute": quiz_route,
    }
