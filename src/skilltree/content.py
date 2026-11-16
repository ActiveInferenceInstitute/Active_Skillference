"""Semantic, multiplicity-aware comparison of exported and live admin content.

This module never updates or deletes live resources. Missing resources can be
created by the existing seeder; changed or unverifiable resources fail closed.
Only identifiers, counts and a digest leave the admin boundary, never answer keys.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from src.skilltree.admin_ops import (
    project_create_path,
    quiz_definition_path,
    quiz_questions_path,
    skill_create_path,
    subject_create_path,
)
from src.skilltree.local_auth_state import _skilltree_origin
from src.skilltree.model import QuizQuestion
from src.skilltree.summary import validate_export_payload
from src.skilltree.transport import SkillTreeClientError


class SkillTreeContentError(SkillTreeClientError):
    """Live content cannot safely be identified with an exported resource."""


def export_content_digest(project: Mapping[str, Any]) -> str:
    """Bind a receipt to the complete private export, including answer correctness."""
    validate_export_payload(project)
    raw = json.dumps(project, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _object(payload: Any, resource: str) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        data = payload.get("data")
        if isinstance(data, Mapping):
            return data
        return payload
    raise SkillTreeContentError(f"{resource} returned no verifiable content object")


def _rows(payload: Any, key: str, resource: str) -> list[Mapping[str, Any]]:
    if isinstance(payload, Mapping):
        if key in payload:
            payload = payload[key]
        elif "data" in payload:
            return _rows(payload["data"], key, resource)
    if not isinstance(payload, list) or any(not isinstance(row, Mapping) for row in payload):
        raise SkillTreeContentError(f"{resource} returned no verifiable {key} list")
    return payload


def _question_key(question: Mapping[str, Any]) -> str:
    text = question.get("question")
    question_type = question.get("questionType")
    answers = question.get("answers")
    if (
        not isinstance(text, str) or not text.strip()
        or not isinstance(question_type, str)
        or question_type not in {"SingleChoice", "MultipleChoice", "TextInput"}
        or not isinstance(answers, list) or not answers
    ):
        raise SkillTreeContentError("quiz question response lacks verifiable semantic content")
    normalized_answers = []
    for answer in answers:
        if (
            not isinstance(answer, Mapping)
            or not isinstance(answer.get("answer"), str)
            or not isinstance(answer.get("isCorrect"), bool)
        ):
            raise SkillTreeContentError("quiz answer response lacks verifiable correctness")
        normalized_answers.append((answer["answer"], answer["isCorrect"]))
    return json.dumps(
        [text, question_type, sorted(normalized_answers)],
        ensure_ascii=False, separators=(",", ":"),
    )


def missing_quiz_questions(
    payload: Any, expected: Sequence[QuizQuestion],
) -> list[QuizQuestion]:
    """Return missing question occurrences; refuse extras or changed answer keys."""
    current = Counter(_question_key(row) for row in _rows(payload, "questions", "quiz"))
    wanted = Counter(_question_key(question.to_dict()) for question in expected)
    if current - wanted:
        raise SkillTreeContentError(
            "live quiz contains extra or changed questions; existing content was not overwritten"
        )
    missing = []
    for question in expected:
        key = _question_key(question.to_dict())
        if current[key]:
            current[key] -= 1
        else:
            missing.append(question)
    return missing


def _index(rows: list[Mapping[str, Any]], field: str, resource: str) -> dict[str, Mapping[str, Any]]:
    result = {}
    for row in rows:
        identifier = row.get(field)
        if not isinstance(identifier, str) or not identifier or identifier in result:
            raise SkillTreeContentError(f"{resource} has missing or duplicate {field}")
        result[identifier] = row
    return result


def _quiz_completion_contract(payload: Any, question_count: int) -> tuple[int, int]:
    """Resolve native 4.6.0 length/pass-count settings, never an export-only percent."""
    rows = _index(_rows(payload, "settings", "quiz"), "setting", "quiz settings")

    def integer(name: str) -> int:
        if name not in rows:
            return -1
        value = rows[name].get("value")
        if not isinstance(value, str):
            raise SkillTreeContentError(f"quiz setting {name} is not a string integer")
        try:
            return int(value)
        except ValueError as exc:
            raise SkillTreeContentError(f"quiz setting {name} is not an integer") from exc

    length = integer("quizLength")
    passing = integer("quizPassingReq")
    if length == -1:
        length = question_count
    if length <= 0 or length > question_count or passing < -1 or passing > question_count:
        raise SkillTreeContentError("quiz length/pass-count settings are unverifiable")
    return length, passing if passing > 0 else length


def compare_live_content(
    *, get: Callable[[str], Any], base_url: str, project: Mapping[str, Any],
) -> dict[str, Any]:
    """Read actual admin content and return a browser-safe comparison receipt.

    A count-only response is not evidence of content parity. Server-generated
    identifiers and quiz ordering are ignored; duplicate question/answer
    occurrences and correctness flags are not. Global unrelated quiz definitions
    are outside the project boundary; every exported quiz is checked explicitly.
    """
    digest = export_content_digest(project)
    project_id = str(project["projectId"])
    root = project_create_path(project_id)
    live_project = _object(get(root), "project")
    if live_project.get("projectId") != project_id or not isinstance(live_project.get("name"), str):
        raise SkillTreeContentError("live project identity/name is unverifiable")
    missing: list[str] = []
    extra: list[str] = []
    changed: list[str] = []
    if live_project["name"] != project["name"]:
        changed.append(f"project:{project_id}")
    live_subjects = _index(_rows(get(f"{root}/subjects"), "subjects", "project"), "subjectId", "project")
    expected_subjects = {subject["subjectId"]: subject for subject in project["subjects"]}
    missing.extend(f"subject:{identifier}" for identifier in expected_subjects.keys() - live_subjects.keys())
    extra.extend(f"subject:{identifier}" for identifier in live_subjects.keys() - expected_subjects.keys())
    live_skill_count = 0
    for subject_id, subject in expected_subjects.items():
        if subject_id not in live_subjects:
            continue
        subject_path = subject_create_path(project_id, subject_id)
        live_subject = _object(get(subject_path), "subject")
        fields = ("subjectId", "name", "description")
        if any(field not in live_subject for field in fields):
            raise SkillTreeContentError(f"subject:{subject_id} content is unverifiable")
        if any(live_subject[field] != subject.get(field, "") for field in fields):
            changed.append(f"subject:{subject_id}")
        live_skills = _index(_rows(get(f"{subject_path}/skills"), "skills", "subject"), "skillId", "subject")
        wanted_skills = {skill["skillId"]: skill for skill in subject["skills"]}
        live_skill_count += len(live_skills)
        missing.extend(f"skill:{identifier}" for identifier in wanted_skills.keys() - live_skills.keys())
        extra.extend(f"skill:{identifier}" for identifier in live_skills.keys() - wanted_skills.keys())
        for skill_id, skill in wanted_skills.items():
            if skill_id not in live_skills:
                continue
            live_skill = _object(get(skill_create_path(project_id, subject_id, skill_id)), "skill")
            fields = ("skillId", "name", "description", "pointIncrement", "numPerformToCompletion", "helpUrl", "selfReportingType")
            if any(field not in live_skill for field in fields):
                raise SkillTreeContentError(f"skill:{skill_id} content is unverifiable")
            if (
                any(live_skill[field] != skill.get(field) for field in fields)
                or live_skill.get("quizId", "") != skill.get("quizId", "")
            ):
                changed.append(f"skill:{skill_id}")
    for quiz in project["quizzes"]:
        quiz_id = quiz["quizId"]
        try:
            live_quiz = _object(get(quiz_definition_path(quiz_id)), "quiz")
        except SkillTreeClientError as exc:
            if exc.status != 404:
                raise
            missing.append(f"quiz:{quiz_id}")
            continue
        fields = ("quizId", "name", "type")
        if any(field not in live_quiz for field in fields):
            raise SkillTreeContentError(f"quiz:{quiz_id} definition is unverifiable")
        if any(live_quiz[field] != quiz.get(field) for field in fields):
            changed.append(f"quiz:{quiz_id}")
        question_count = len(quiz["questions"])
        percent = quiz.get("passingPercent")
        if type(percent) is not int or not 1 <= percent <= 100:
            raise SkillTreeContentError(f"quiz:{quiz_id} export pass percentage is invalid")
        # Normalize defaults for the intended completed quiz. Missing questions
        # still make the receipt incomplete below and can be seeded without
        # misclassifying native default settings as an existing-content change.
        length, required = _quiz_completion_contract(
            get(f"{quiz_definition_path(quiz_id)}/settings"), question_count,
        )
        if (length, required) != (
            question_count, (question_count * percent + 99) // 100,
        ):
            changed.append(f"quiz:{quiz_id}")
        current = Counter(_question_key(row) for row in _rows(get(quiz_questions_path(quiz_id)), "questions", "quiz"))
        wanted = Counter(_question_key(row) for row in quiz["questions"])
        if current - wanted:
            changed.append(f"quiz-questions:{quiz_id}")
        if wanted - current:
            missing.append(f"quiz-questions:{quiz_id}")
    scheme, host, port = _skilltree_origin(base_url)
    return {
        "checked": True,
        "complete": not (missing or extra or changed),
        "targetOrigin": {"scheme": scheme, "host": host, "port": port},
        "projectId": project_id,
        "exportContentDigest": digest,
        "subjects": len(live_subjects),
        "skills": live_skill_count,
        "missingResources": sorted(missing),
        "extraResources": sorted(extra),
        "changedResources": sorted(set(changed)),
    }
