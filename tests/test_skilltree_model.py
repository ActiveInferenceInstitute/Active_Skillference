"""Tests for the SkillTree-native data model using pure data."""

from __future__ import annotations

import pytest

from src.skilltree.model import (
    Quiz,
    QuizQuestion,
    SkillDependency,
    SkillTreeModelError,
    SkillTreeProject,
    SkillTreeSkill,
    SkillTreeSubject,
)
from src.skilltree.summary import SkillTreeSummaryError, validate_export_payload


def test_skill_to_dict_emits_camelcase_field_names() -> None:
    skill = SkillTreeSkill(
        skill_id="bayes_rule",
        name="Bayes' Rule",
        point_increment=150,
        num_perform_to_completion=2,
        description="Apply **Bayes** to update beliefs.",
        help_url="https://example.org/bayes",
        self_reporting_type="Quiz",
    )
    payload = skill.to_dict()
    assert payload == {
        "skillId": "bayes_rule",
        "name": "Bayes' Rule",
        "type": "Skill",
        "pointIncrement": 150,
        "numPerformToCompletion": 2,
        "description": "Apply **Bayes** to update beliefs.",
        "helpUrl": "https://example.org/bayes",
        "selfReportingType": "Quiz",
    }
    # as_payload is the request-body alias.
    assert skill.as_payload() == payload


def test_quiz_skill_to_dict_includes_quiz_id_when_present() -> None:
    skill = SkillTreeSkill(
        skill_id="bayes_rule",
        name="Bayes' Rule",
        self_reporting_type="Quiz",
        quiz_id="bayes_rule_quiz",
    )
    payload = skill.to_dict()
    assert payload["quizId"] == "bayes_rule_quiz"


def test_skill_defaults() -> None:
    skill = SkillTreeSkill(skill_id="s1", name="Skill One")
    assert skill.point_increment == 100
    assert skill.num_perform_to_completion == 1
    assert skill.type == "Skill"
    assert skill.self_reporting_type == "HonorSystem"
    assert skill.quiz_id == ""


def test_skill_bad_self_reporting_type_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="selfReportingType"):
        SkillTreeSkill(skill_id="s1", name="Skill", self_reporting_type="Nonsense")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_increment", [0, -5])
def test_skill_nonpositive_point_increment_raises(bad_increment: int) -> None:
    with pytest.raises(SkillTreeModelError, match="pointIncrement"):
        SkillTreeSkill(skill_id="s1", name="Skill", point_increment=bad_increment)


def test_skill_nonpositive_perform_count_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="numPerformToCompletion"):
        SkillTreeSkill(skill_id="s1", name="Skill", num_perform_to_completion=0)


def test_skill_empty_id_and_name_raise() -> None:
    with pytest.raises(SkillTreeModelError, match="skillId"):
        SkillTreeSkill(skill_id="  ", name="x")
    with pytest.raises(SkillTreeModelError, match="must have a name"):
        SkillTreeSkill(skill_id="s1", name="   ")


def test_subject_to_dict_round_trips_nested_skills() -> None:
    subject = SkillTreeSubject(
        subject_id="probability",
        name="Probability",
        description="Foundations of probability.",
        skills=[SkillTreeSkill(skill_id="s1", name="Skill One")],
    )
    payload = subject.to_dict()
    assert payload["subjectId"] == "probability"
    assert payload["name"] == "Probability"
    assert payload["description"] == "Foundations of probability."
    assert len(payload["skills"]) == 1
    assert payload["skills"][0]["skillId"] == "s1"
    assert subject.as_payload() == payload


def test_subject_empty_id_and_name_raise() -> None:
    with pytest.raises(SkillTreeModelError, match="subjectId"):
        SkillTreeSubject(subject_id=" ", name="x")
    with pytest.raises(SkillTreeModelError, match="must have a name"):
        SkillTreeSubject(subject_id="s", name=" ")


def test_subject_name_length_matches_live_skilltree_limit() -> None:
    with pytest.raises(SkillTreeModelError, match="50 chars"):
        SkillTreeSubject(subject_id="s", name="x" * 51)


def test_dependency_to_dict() -> None:
    dep = SkillDependency(skill_id="advanced", depends_on_skill_id="basic")
    assert dep.to_dict() == {"skillId": "advanced", "dependsOnSkillId": "basic"}
    assert dep.as_payload() == dep.to_dict()


def test_dependency_self_loop_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="cannot depend on itself"):
        SkillDependency(skill_id="x", depends_on_skill_id="x")


def test_dependency_empty_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="non-empty"):
        SkillDependency(skill_id="", depends_on_skill_id="y")


def test_quiz_question_maps_correct_flags() -> None:
    q = QuizQuestion(
        question="What is 2 + 2?",
        answers=[
            {"answer": "3", "isCorrect": False},
            {"answer": "4", "isCorrect": True},
        ],
        question_type="SingleChoice",
    )
    payload = q.to_dict()
    assert payload["questionType"] == "SingleChoice"
    assert payload["answers"] == [
        {"answer": "3", "isCorrect": False},
        {"answer": "4", "isCorrect": True},
    ]
    assert q.as_payload() == payload


def test_quiz_question_bad_type_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="questionType"):
        QuizQuestion(
            question="q",
            answers=[{"answer": "a", "isCorrect": True}],
            question_type="Wrong",  # type: ignore[arg-type]
        )


def test_quiz_question_empty_question_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="non-empty"):
        QuizQuestion(question="  ", answers=[{"answer": "a", "isCorrect": True}])


def test_quiz_question_no_answers_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="≥1 answer"):
        QuizQuestion(question="q", answers=[])


def test_quiz_question_missing_keys_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="'answer' and 'isCorrect'"):
        QuizQuestion(question="q", answers=[{"answer": "a"}])


def test_quiz_question_no_correct_answer_raises() -> None:
    with pytest.raises(SkillTreeModelError, match="≥1 answer correct"):
        QuizQuestion(
            question="q",
            answers=[{"answer": "a", "isCorrect": False}],
        )


def test_quiz_to_dict() -> None:
    quiz = Quiz(
        quiz_id="q1",
        name="Quiz One",
        questions=[
            QuizQuestion(question="q?", answers=[{"answer": "a", "isCorrect": True}])
        ],
    )
    payload = quiz.to_dict()
    assert payload["quizId"] == "q1"
    assert payload["type"] == "Quiz"
    assert len(payload["questions"]) == 1
    assert quiz.as_payload() == payload


def test_quiz_question_admin_create_payload() -> None:
    question = QuizQuestion(
        question="q?",
        answers=[
            {"answer": "a", "isCorrect": True},
            {"answer": "b", "isCorrect": False},
        ],
    )
    assert question.to_admin_create_payload() == {
        "question": "q?",
        "answerHint": "",
        "questionType": "SingleChoice",
        "questionScale": 5,
        "answers": [
            {"answer": "a", "isCorrect": True},
            {"answer": "b", "isCorrect": False},
        ],
    }


def test_quiz_empty_id_and_name_raise() -> None:
    with pytest.raises(SkillTreeModelError, match="quizId"):
        Quiz(quiz_id=" ", name="x")
    with pytest.raises(SkillTreeModelError, match="must have a name"):
        Quiz(quiz_id="q", name=" ")


def test_project_to_export_dict_is_complete_and_serialisable() -> None:
    import json

    project = SkillTreeProject(
        project_id="active_inference",
        name="Active Inference",
        subjects=[
            SkillTreeSubject(
                subject_id="prob",
                name="Probability",
                skills=[
                    SkillTreeSkill(
                        skill_id="s1",
                        name="Skill One",
                        self_reporting_type="Quiz",
                        quiz_id="q1",
                    )
                ],
            )
        ],
        dependencies=[SkillDependency(skill_id="s2", depends_on_skill_id="s1")],
        quizzes=[
            Quiz(
                quiz_id="q1",
                name="Quiz One",
                questions=[
                    QuizQuestion(
                        question="q?", answers=[{"answer": "a", "isCorrect": True}]
                    )
                ],
            )
        ],
    )
    payload = project.to_export_dict()
    assert payload["projectId"] == "active_inference"
    assert payload["name"] == "Active Inference"
    assert len(payload["subjects"]) == 1
    assert len(payload["dependencies"]) == 1
    assert len(payload["quizzes"]) == 1
    # Whole structure is JSON-serialisable.
    assert json.loads(json.dumps(payload)) == payload


def test_project_empty_id_and_name_raise() -> None:
    with pytest.raises(SkillTreeModelError, match="projectId"):
        SkillTreeProject(project_id=" ", name="x")
    with pytest.raises(SkillTreeModelError, match="must have a name"):
        SkillTreeProject(project_id="p", name=" ")


def test_skilltree_skill_rejects_slash_in_id() -> None:
    from src.skilltree.model import SkillTreeModelError, SkillTreeSkill

    with pytest.raises(SkillTreeModelError, match="identifier"):
        SkillTreeSkill(skill_id="bayes/rule", name="Bayes")


def test_skilltree_skill_rejects_leading_underscore_id() -> None:
    from src.skilltree.model import SkillTreeModelError, SkillTreeSkill

    with pytest.raises(SkillTreeModelError, match="identifier"):
        SkillTreeSkill(skill_id="_bayes", name="Bayes")


def test_skilltree_skill_accepts_valid_id() -> None:
    from src.skilltree.model import SkillTreeSkill

    assert SkillTreeSkill(skill_id="bayes_rule", name="Bayes").skill_id == "bayes_rule"


def test_skilltree_skill_rejects_adversarial_ids() -> None:
    from src.skilltree.model import SkillTreeModelError, SkillTreeSkill

    for bad in ("../etc", "a/b", "a b", "a.b", "аbc", "id\x00x", "1abc", "-x"):
        with pytest.raises(SkillTreeModelError):
            SkillTreeSkill(skill_id=bad, name="X")


def _quiz(qid: str = "q1") -> Quiz:
    return Quiz(
        quiz_id=qid,
        name="Quiz",
        questions=[
            QuizQuestion(question="q?", answers=[{"answer": "a", "isCorrect": True}])
        ],
    )


def test_project_rejects_quiz_skill_without_quiz_id() -> None:
    """Negative control (convergence #9 CRITICAL): a Quiz-typed skill with no quizId is a
    broken gate and must be refused at export."""
    with pytest.raises(SkillTreeModelError, match="has no quizId"):
        SkillTreeProject(
            project_id="p",
            name="P",
            subjects=[
                SkillTreeSubject(
                    subject_id="sub",
                    name="Sub",
                    skills=[
                        SkillTreeSkill(
                            skill_id="s1", name="S1", self_reporting_type="Quiz"
                        )
                    ],
                )
            ],
        )


def test_project_rejects_dangling_quiz_reference() -> None:
    """Negative control (#10): a skill referencing a quizId with no definition must fail."""
    with pytest.raises(SkillTreeModelError, match="no quiz definition"):
        SkillTreeProject(
            project_id="p",
            name="P",
            subjects=[
                SkillTreeSubject(
                    subject_id="sub",
                    name="Sub",
                    skills=[
                        SkillTreeSkill(
                            skill_id="s1",
                            name="S1",
                            self_reporting_type="Quiz",
                            quiz_id="ghost",
                        )
                    ],
                )
            ],
        )


def test_project_reports_orphan_quiz_without_hard_failing() -> None:
    """Orphan quizzes are a query, not a hard model error (an unused quiz pool is a valid
    authoring pattern). The generic model surfaces them via orphan_quiz_ids(); the project
    export seam decides the policy."""
    project = SkillTreeProject(
        project_id="p",
        name="P",
        subjects=[
            SkillTreeSubject(
                subject_id="sub",
                name="Sub",
                skills=[SkillTreeSkill(skill_id="s1", name="S1")],
            )
        ],
        quizzes=[_quiz("q1")],
    )
    assert project.orphan_quiz_ids() == ("q1",)
    # A project whose quizzes are all referenced reports no orphans.
    referenced = SkillTreeProject(
        project_id="p2",
        name="P2",
        subjects=[
            SkillTreeSubject(
                subject_id="sub",
                name="Sub",
                skills=[
                    SkillTreeSkill(
                        skill_id="s1",
                        name="S1",
                        self_reporting_type="Quiz",
                        quiz_id="q1",
                    )
                ],
            )
        ],
        quizzes=[_quiz("q1")],
    )
    assert referenced.orphan_quiz_ids() == ()


def test_validate_export_payload_rejects_dangling_dependency() -> None:
    payload = {
        "projectId": "p",
        "name": "Project",
        "subjects": [{"subjectId": "s", "skills": [{"skillId": "root"}]}],
        "dependencies": [{"skillId": "root", "dependsOnSkillId": "missing"}],
        "quizzes": [],
    }

    with pytest.raises(SkillTreeSummaryError, match="unknown skill"):
        validate_export_payload(payload)


def test_validate_export_payload_rejects_dependency_cycle() -> None:
    payload = {
        "projectId": "p",
        "name": "Project",
        "subjects": [
            {"subjectId": "s", "skills": [{"skillId": "a"}, {"skillId": "b"}]}
        ],
        "dependencies": [
            {"skillId": "a", "dependsOnSkillId": "b"},
            {"skillId": "b", "dependsOnSkillId": "a"},
        ],
        "quizzes": [],
    }

    with pytest.raises(SkillTreeSummaryError, match="contain a cycle"):
        validate_export_payload(payload)


def test_validate_export_payload_rejects_missing_quiz_gate() -> None:
    payload = {
        "projectId": "p",
        "name": "Project",
        "subjects": [
            {
                "subjectId": "s",
                "skills": [{"skillId": "quiz_skill", "selfReportingType": "Quiz"}],
            }
        ],
        "dependencies": [],
        "quizzes": [],
    }

    with pytest.raises(SkillTreeSummaryError, match="missing quizId"):
        validate_export_payload(payload)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("projectId", None, "projectId must be non-empty text"),
        ("name", 7, "name must be non-empty text"),
        ("subjects", None, "subjects must be a list"),
        ("dependencies", None, "dependencies must be a list"),
        ("quizzes", None, "quizzes must be a list"),
    ],
)
def test_validate_export_payload_rejects_type_confusion_and_missing_collections(
    field: str, value: object, message: str
) -> None:
    payload: dict[str, object] = {
        "projectId": "p",
        "name": "Project",
        "subjects": [],
        "dependencies": [],
        "quizzes": [],
    }
    payload.pop(field, None)
    if field in {"projectId", "name"}:
        payload[field] = value
    else:
        payload[field] = value
    with pytest.raises(SkillTreeSummaryError, match=message):
        validate_export_payload(payload)


def test_validate_export_payload_rejects_malformed_quiz_answers() -> None:
    payload = {
        "projectId": "p",
        "name": "Project",
        "subjects": [],
        "dependencies": [],
        "quizzes": [
            {
                "quizId": "q1",
                "questions": [
                    {
                        "question": "q?",
                        "answers": [{"answer": "a", "isCorrect": "yes"}],
                    }
                ],
            }
        ],
    }
    with pytest.raises(SkillTreeSummaryError, match="isCorrect must be boolean"):
        validate_export_payload(payload)
