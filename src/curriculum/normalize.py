"""Deterministic learner-quality normalization for authored curriculum subjects."""

from __future__ import annotations

from dataclasses import replace

from src.curriculum.assessment_normalize import (
    diagnostic_question,
    misuse_question,
    rebalance_assessments,
    transfer_question,
)
from src.curriculum.model import Skill, Subject
from src.curriculum.quality import (
    MIN_SKILL_DESCRIPTION_WORDS,
    MIN_SUBJECT_DESCRIPTION_WORDS,
)

_SKILL_DESCRIPTION_SUFFIX = (
    " Learners should be able to state the concept, connect it to its prerequisites, "
    "and explain the downstream Active Inference move it makes possible."
)
_SUBJECT_DESCRIPTION_SUFFIX = (
    " It groups concepts that learners reuse directly in later strata and in the "
    "SkillTree learning path."
)


def _word_count(text: str) -> int:
    return len(text.split())


def _append_if_short(text: str, suffix: str, minimum_words: int) -> str:
    if _word_count(text) >= minimum_words:
        return text
    if suffix.strip() in text:
        return text
    return f"{text.rstrip()} {suffix.strip()}"


def _dedupe(items: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def normalize_graph(subjects: list[Subject]) -> list[Subject]:
    """Apply deterministic learner-quality normalization to authored catalog data."""
    by_id = {skill.skill_id: skill for subject in subjects for skill in subject.skills}
    hardened: list[Subject] = []
    single_choice_index: dict[int, int] = {}
    multi_choice_index: dict[tuple[int, int], int] = {}
    length_rank_index: dict[int, int] = {}

    for subject in subjects:
        topic_tag = subject.subject_id.removeprefix("sub_").replace("_", "-")
        skills: list[Skill] = []
        for skill in subject.skills:
            prerequisites: list[str] = []
            related = list(skill.related)
            for prereq_id in skill.prerequisites:
                prereq = by_id.get(prereq_id)
                if prereq is not None and prereq.stratum.order > skill.stratum.order:
                    related.append(prereq_id)
                else:
                    prerequisites.append(prereq_id)

            assessments = list(skill.assessments)
            if len(assessments) < 2:
                assessments.append(diagnostic_question(skill))
            if len(assessments) < 3:
                assessments.append(transfer_question(skill))
            if len(assessments) < 4:
                assessments.append(misuse_question(skill))
            if not any(q.question_type == "MultipleChoice" for q in assessments):
                assessments.append(transfer_question(skill))
            rebalanced = rebalance_assessments(
                assessments,
                single_choice_index=single_choice_index,
                multi_choice_index=multi_choice_index,
                length_rank_index=length_rank_index,
            )

            tags = _dedupe((skill.stratum.value, topic_tag, *skill.tags))
            skills.append(
                replace(
                    skill,
                    description=_append_if_short(
                        skill.description,
                        _SKILL_DESCRIPTION_SUFFIX,
                        MIN_SKILL_DESCRIPTION_WORDS,
                    ),
                    prerequisites=tuple(prerequisites),
                    related=_dedupe(tuple(related)),
                    assessments=tuple(rebalanced),
                    tags=tags,
                )
            )

        hardened.append(
            replace(
                subject,
                description=_append_if_short(
                    subject.description,
                    _SUBJECT_DESCRIPTION_SUFFIX,
                    MIN_SUBJECT_DESCRIPTION_WORDS,
                ),
                skills=tuple(skills),
            )
        )

    return hardened
