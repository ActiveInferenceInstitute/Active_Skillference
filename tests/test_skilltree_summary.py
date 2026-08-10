"""Tests for the SkillTree export-payload summary and validation surface.

These are negative/fail-closed tests for ``validate_export_payload``: the
relationships a count-only summary cannot see (duplicate ids, dangling quiz
references, malformed shapes, self-loops/cycles in dependencies). The happy
path is exercised by the real-export tests in ``test_skilltree_exporter.py``.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from src.skilltree.summary import (
    SkillTreeSummaryError,
    validate_export_payload,
)


def _base() -> dict[str, Any]:
    """A structurally valid export payload (two skills, one quiz, no deps)."""
    return {
        "projectId": "p",
        "name": "P",
        "subjects": [
            {
                "subjectId": "s1",
                "skills": [
                    {"skillId": "k1", "quizId": "q1"},
                    {"skillId": "k2", "quizId": "q1"},
                ],
            }
        ],
        "dependencies": [],
        "quizzes": [
            {
                "quizId": "q1",
                "questions": [
                    {
                        "question": "Q",
                        "answers": [
                            {"answer": "A", "isCorrect": True},
                            {"answer": "B", "isCorrect": False},
                        ],
                    }
                ],
            }
        ],
    }


def test_validate_export_payload_accepts_valid_payload() -> None:
    validate_export_payload(_base())  # must not raise


def test_validate_export_payload_requires_collections_and_text() -> None:
    payload = _base()
    del payload["subjects"]
    with pytest.raises(SkillTreeSummaryError, match="requires subjects collection"):
        validate_export_payload(payload)

    payload = _base()
    payload["projectId"] = ""
    with pytest.raises(SkillTreeSummaryError, match="projectId must be non-empty text"):
        validate_export_payload(payload)

    payload = _base()
    payload["subjects"] = "not-a-list"
    with pytest.raises(SkillTreeSummaryError, match="subjects must be a list"):
        validate_export_payload(payload)


def test_validate_export_payload_rejects_bad_subject_and_skill_shapes() -> None:
    payload = _base()
    payload["subjects"] = ["not-an-object"]
    with pytest.raises(SkillTreeSummaryError, match="subject 1 is not an object"):
        validate_export_payload(payload)

    payload = _base()
    payload["subjects"].append({"subjectId": "s1", "skills": []})
    with pytest.raises(SkillTreeSummaryError, match="duplicate subjectId 's1'"):
        validate_export_payload(payload)

    payload = _base()
    payload["subjects"][0]["skills"] = ["not-an-object"]
    with pytest.raises(SkillTreeSummaryError, match="skill 1 is not an object"):
        validate_export_payload(payload)

    payload = _base()
    payload["subjects"][0]["skills"].append({"skillId": "k1", "quizId": "q1"})
    with pytest.raises(SkillTreeSummaryError, match="duplicate skillId 'k1'"):
        validate_export_payload(payload)

    payload = _base()
    payload["subjects"][0]["skills"][0]["selfReportingType"] = 123
    with pytest.raises(SkillTreeSummaryError, match="selfReportingType must be text"):
        validate_export_payload(payload)

    payload = _base()
    payload["subjects"][0]["skills"][0]["quizId"] = 123
    with pytest.raises(SkillTreeSummaryError, match="quizId must be text"):
        validate_export_payload(payload)


def test_validate_export_payload_rejects_bad_quiz_shapes() -> None:
    payload = _base()
    payload["quizzes"] = ["not-an-object"]
    with pytest.raises(SkillTreeSummaryError, match="quiz 1 is not an object"):
        validate_export_payload(payload)

    payload = _base()
    payload["quizzes"].append({"quizId": "q1", "questions": []})
    with pytest.raises(SkillTreeSummaryError, match="duplicate quizId 'q1'"):
        validate_export_payload(payload)

    payload = _base()
    payload["quizzes"][0]["questions"] = ["not-an-object"]
    with pytest.raises(SkillTreeSummaryError, match="question 1 is not an object"):
        validate_export_payload(payload)

    payload = _base()
    payload["quizzes"][0]["questions"][0]["answers"] = "not-a-list"
    with pytest.raises(SkillTreeSummaryError, match="answers must be a list"):
        validate_export_payload(payload)

    payload = _base()
    payload["quizzes"][0]["questions"][0]["answers"] = []
    with pytest.raises(SkillTreeSummaryError, match="must contain at least one answer"):
        validate_export_payload(payload)

    payload = _base()
    payload["quizzes"][0]["questions"][0]["answers"] = ["not-an-object"]
    with pytest.raises(SkillTreeSummaryError, match="answer 1 is not an object"):
        validate_export_payload(payload)

    payload = _base()
    payload["quizzes"][0]["questions"][0]["answers"] = [
        {"answer": "A", "isCorrect": False}
    ]
    with pytest.raises(SkillTreeSummaryError, match="mark at least one answer correct"):
        validate_export_payload(payload)

    # A skill referencing a quiz that does not exist.
    payload = _base()
    payload["subjects"][0]["skills"][0]["quizId"] = "missing"
    with pytest.raises(
        SkillTreeSummaryError, match="references missing quiz 'missing'"
    ):
        validate_export_payload(payload)


def test_validate_export_payload_rejects_bad_dependencies() -> None:
    payload = _base()
    payload["dependencies"] = ["not-an-object"]
    with pytest.raises(SkillTreeSummaryError, match="dependency 1 is not an object"):
        validate_export_payload(payload)

    payload = _base()
    payload["dependencies"] = [{"skillId": "k1", "dependsOnSkillId": "k1"}]
    with pytest.raises(SkillTreeSummaryError, match="self-loop"):
        validate_export_payload(payload)

    payload = _base()
    payload["dependencies"] = [{"skillId": "k1", "dependsOnSkillId": "unknown"}]
    with pytest.raises(SkillTreeSummaryError, match="references an unknown skill"):
        validate_export_payload(payload)

    payload = _base()
    payload["dependencies"] = [
        {"skillId": "k1", "dependsOnSkillId": "k2"},
        {"skillId": "k1", "dependsOnSkillId": "k2"},
    ]
    with pytest.raises(SkillTreeSummaryError, match="duplicate dependency"):
        validate_export_payload(payload)


def test_validate_export_payload_rejects_dependency_cycle() -> None:
    payload = {
        "projectId": "p",
        "name": "P",
        "subjects": [
            {
                "subjectId": "s1",
                "skills": [
                    {"skillId": "a", "quizId": "q1"},
                    {"skillId": "b", "quizId": "q1"},
                ],
            }
        ],
        "dependencies": [
            {"skillId": "a", "dependsOnSkillId": "b"},
            {"skillId": "b", "dependsOnSkillId": "a"},
        ],
        "quizzes": deepcopy(_base()["quizzes"]),
    }
    with pytest.raises(SkillTreeSummaryError, match="contain a cycle"):
        validate_export_payload(payload)
