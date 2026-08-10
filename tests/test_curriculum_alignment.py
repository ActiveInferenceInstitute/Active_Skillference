"""Negative/alignment-gap tests for course-material alignment.

These drive ``validate_course_material_alignment`` with malformed project, material
index, and audit payloads to exercise the fail-closed diagnostic branches (duplicate
ids, dangling references, bad shapes) that the real 630-skill pipeline's happy path
never hits. The valid base comes from the real data builders, not a hand-drawn stub.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from src.curriculum.alignment import (
    CourseAlignmentError,
    load_json_object,
    validate_course_material_alignment,
    validate_course_material_alignment_files,
)
from tests.test_course_materials import _exported_project_and_materials


@pytest.fixture(scope="module")
def valid_trio() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _exported_project_and_materials()


def _codes(project, material_index, material_audit) -> set[str]:
    report = validate_course_material_alignment(
        project=project,
        material_index=material_index,
        material_audit=material_audit,
    )
    return {issue.code for issue in report.issues}


@pytest.fixture
def trio(valid_trio):
    return deepcopy(valid_trio)


def test_alignment_rejects_subject_and_skill_shape_errors(trio) -> None:
    project = trio[0]
    project["subjects"] = "not-a-list"
    assert "project-subjects" in _codes(*trio)

    project["subjects"] = ["not-an-object"]
    assert "subject" in _codes(*trio)

    project["subjects"] = [{"subjectId": "", "skills": []}]
    assert "subject-id" in _codes(*trio)

    project["subjects"] = [{"subjectId": "s", "skills": "nope"}]
    assert "subject-skills" in _codes(*trio)

    project["subjects"] = [{"subjectId": "s", "skills": ["not-an-object"]}]
    assert "skill" in _codes(*trio)

    project["subjects"] = [{"subjectId": "s", "skills": [{"noId": True}]}]
    assert "skill-id" in _codes(*trio)

    project["subjects"] = [
        {
            "subjectId": "s",
            "skills": [{"skillId": "dup", "quizId": ""}],
        },
        {
            "subjectId": "s2",
            "skills": [{"skillId": "dup", "quizId": ""}],
        },
    ]
    assert "duplicate-skill" in _codes(*trio)


def test_alignment_rejects_dependency_shape_errors(trio) -> None:
    project = trio[0]
    project["subjects"] = [
        {"subjectId": "s", "skills": [{"skillId": "a", "quizId": ""}]}
    ]
    project["dependencies"] = "nope"
    assert "dependencies" in _codes(*trio)

    project["dependencies"] = ["not-an-object"]
    assert "dependency" in _codes(*trio)

    project["dependencies"] = [{"skillId": "nope", "dependsOnSkillId": "a"}]
    assert "dependency-skill" in _codes(*trio)

    project["dependencies"] = [{"skillId": "a", "dependsOnSkillId": "nope"}]
    assert "dependency-prerequisite" in _codes(*trio)

    project["dependencies"] = [{"skillId": "a", "dependsOnSkillId": "a"}]
    assert "dependency-self-loop" in _codes(*trio)


def test_alignment_rejects_quiz_shape_and_content_errors(trio) -> None:
    project = trio[0]
    project["quizzes"] = "nope"
    assert "quizzes" in _codes(*trio)

    project["quizzes"] = ["not-an-object"]
    assert "quiz" in _codes(*trio)

    project["quizzes"] = [{"noId": True}]
    assert "quiz-id" in _codes(*trio)

    project["quizzes"] = [
        {"quizId": "q", "questions": []},
        {"quizId": "q", "questions": []},
    ]
    assert "duplicate-quiz" in _codes(*trio)

    project["quizzes"] = [{"quizId": "q", "questions": []}]
    assert "quiz-questions" in _codes(*trio)

    project["quizzes"] = [
        {
            "quizId": "q",
            "numQuestions": 2,
            "questions": [
                {"question": "Q", "answers": [{"answer": "A", "isCorrect": True}]}
            ],
        }
    ]
    assert "quiz-question-count" in _codes(*trio)

    project["quizzes"] = [
        {
            "quizId": "q",
            "passingPercent": 0,
            "questions": [
                {"question": "Q", "answers": [{"answer": "A", "isCorrect": True}]}
            ],
        }
    ]
    assert "quiz-passing-percent" in _codes(*trio)

    project["quizzes"] = [{"quizId": "q", "questions": ["not-an-object"]}]
    assert "quiz-question" in _codes(*trio)

    project["quizzes"] = [
        {
            "quizId": "q",
            "questions": [{"answers": [{"answer": "A", "isCorrect": True}]}],
        }
    ]
    assert "quiz-question-text" in _codes(*trio)

    project["quizzes"] = [
        {"quizId": "q", "questions": [{"question": "Q", "answers": []}]}
    ]
    assert "quiz-answers" in _codes(*trio)

    project["quizzes"] = [
        {
            "quizId": "q",
            "questions": [
                {"question": "Q", "answers": [{"answer": "A", "isCorrect": False}]}
            ],
        }
    ]
    assert "quiz-correct-answer" in _codes(*trio)

    project["quizzes"] = [
        {"quizId": "q", "questions": [{"question": "Q", "answers": ["not-an-object"]}]}
    ]
    assert "quiz-answer" in _codes(*trio)

    project["quizzes"] = [
        {"quizId": "q", "questions": [{"question": "Q", "answers": [{"wrong": True}]}]}
    ]
    assert "quiz-answer-fields" in _codes(*trio)


def test_alignment_rejects_extra_and_missing_material_records(trio) -> None:
    project, material_index, _ = trio
    # A quiz defined but referenced by no exported skill.
    project["quizzes"].append(
        {
            "quizId": "orphan",
            "questions": [
                {"question": "Q", "answers": [{"answer": "A", "isCorrect": True}]}
            ],
        }
    )
    assert "extra-quiz" in _codes(*trio)

    material_index["skills"]["no-such-skill"] = {}
    assert "extra-material" in _codes(*trio)

    material_index["skills"] = "nope"
    assert "material-skills" in _codes(*trio)


def test_alignment_rejects_bad_audit_summary(trio) -> None:
    project, material_index, material_audit = trio
    bad = deepcopy(material_audit)
    bad["summary"] = "nope"
    assert "material-audit-summary" in _codes(project, material_index, bad)


def test_load_json_object_error_modes(tmp_path: Path) -> None:

    with pytest.raises(CourseAlignmentError, match="does not exist"):
        load_json_object(tmp_path / "missing.json")

    bad = tmp_path / "bad.json"
    bad.write_text("{ not json ", encoding="utf-8")
    with pytest.raises(CourseAlignmentError, match="is not valid JSON"):
        load_json_object(bad)

    arr = tmp_path / "arr.json"
    arr.write_text(json.dumps([1, 2]), encoding="utf-8")
    with pytest.raises(CourseAlignmentError, match="must contain a JSON object"):
        load_json_object(arr)


def test_validate_course_material_alignment_files_wraps_and_reports(
    tmp_path: Path, trio
) -> None:
    project, material_index, material_audit = trio
    p = tmp_path / "project.json"
    mi = tmp_path / "index.json"
    ma = tmp_path / "audit.json"
    p.write_text(json.dumps(project), encoding="utf-8")
    mi.write_text(json.dumps(material_index), encoding="utf-8")
    ma.write_text(json.dumps(material_audit), encoding="utf-8")

    report = validate_course_material_alignment_files(
        project_path=p, material_index_path=mi, material_audit_path=ma
    )
    assert report.ok is True
    total_skills = sum(len(subject["skills"]) for subject in project["subjects"])
    assert report.summary["skills"] == total_skills


def test_report_serializes_issues_to_dict(trio) -> None:
    project = trio[0]
    project["subjects"] = "nope"
    report = validate_course_material_alignment(
        project=trio[0], material_index=trio[1], material_audit=trio[2]
    )
    assert report.ok is False
    d = report.to_dict()
    assert isinstance(d["issues"], list)
    assert d["issues"]  # an issue exists and serializes with code/location/message


def test_alignment_rejects_dirty_audit_and_index_summary(trio) -> None:
    project, material_index, material_audit = trio

    dirty_audit = deepcopy(material_audit)
    dirty_audit["issues"] = [{"code": "x", "location": "y", "message": "z"}]
    assert "material-audit-issues" in _codes(project, material_index, dirty_audit)

    bad_index = deepcopy(material_index)
    bad_index["summary"] = "not-an-object"
    assert "material-index-summary" in _codes(project, bad_index, material_audit)


def test_alignment_rejects_non_object_material_record(trio) -> None:
    project, material_index, material_audit = trio
    any_skill_id = next(iter(material_index["skills"]))
    material_index["skills"][any_skill_id] = "not-an-object"
    assert "material-record" in _codes(project, material_index, material_audit)


def test_alignment_rejects_record_content_errors(trio) -> None:
    """Mutation-based coverage of _validate_material_record's sections/pointers."""
    project, material_index, material_audit = trio
    skill_id = next(iter(material_index["skills"]))

    cases = [
        (lambda m: m["skills"][skill_id].update(skillId="wrong"), "material-skill-id"),
        (
            lambda m: m["skills"][skill_id].update(subjectId="wrong"),
            "material-subject-id",
        ),
        (lambda m: m["skills"][skill_id].update(sections=[]), "material-sections"),
        (lambda m: m["skills"][skill_id].update(sections=["x"]), "material-section"),
        (
            lambda m: m["skills"][skill_id].update(
                sections=[{"heading": "", "body": "b"}]
            ),
            "material-section-heading",
        ),
        (
            lambda m: m["skills"][skill_id].update(
                sections=[{"heading": "h", "body": ""}]
            ),
            "material-section-body",
        ),
        (
            lambda m: m["skills"][skill_id].update(externalPointers=[]),
            "material-pointers",
        ),
        (
            lambda m: m["skills"][skill_id].update(externalPointers=["x"]),
            "material-pointer",
        ),
    ]
    for mutator, code in cases:
        mutated = deepcopy(material_index)
        mutator(mutated)
        codes = _codes(project, mutated, material_audit)
        assert code in codes, f"expected issue {code!r} not produced"


def test_alignment_rejects_low_external_pointer_summary(trio) -> None:
    project, material_index, material_audit = trio
    material_index["summary"]["externalPointers"] = 1  # below one-per-skill floor
    assert "material-pointer-count" in _codes(project, material_index, material_audit)
