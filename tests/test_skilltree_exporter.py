"""Tests for the curriculum → SkillTree exporter using concrete graph fixtures."""

from __future__ import annotations

import json

import pytest

from src.curriculum.model import AssessmentQuestion, Skill, Stratum, Subject
from src.skilltree.exporter import (
    CurriculumGraphLike,
    ExportError,
    export_project,
    export_to_json,
)
from src.skilltree.summary import (
    ExportSummary,
    SkillTreeSummaryError,
    summarize_export_payload,
    summarize_project,
)


class CurriculumGraphFixture:
    """A small concrete CurriculumGraphLike used by exporter tests.

    Exposes the three members the exporter consumes: ``subjects``, ``skills``
    (all skills across subjects), and ``prerequisite_edges()``.
    """

    def __init__(self, subjects: list[Subject], edges: list[tuple[str, str]]) -> None:
        self._subjects = subjects
        self._edges = edges

    @property
    def subjects(self) -> list[Subject]:
        return self._subjects

    @property
    def skills(self) -> list[Skill]:
        return [s for subj in self._subjects for s in subj.skills]

    def prerequisite_edges(self) -> list[tuple[str, str]]:
        return self._edges


def _build_graph() -> CurriculumGraphFixture:
    """2 subjects, 3 skills, 2 edges, 1 quiz-bearing skill."""
    s1 = Skill(
        skill_id="counting",
        name="Counting",
        stratum=Stratum.MATH_FOUNDATIONS,
        objective="Count things.",
        description="Counting basics.",
        self_reporting_type="HonorSystem",
    )
    s2 = Skill(
        skill_id="addition",
        name="Addition",
        stratum=Stratum.MATH_FOUNDATIONS,
        objective="Add numbers.",
        description="Addition basics.",
        prerequisites=("counting",),
        self_reporting_type="HonorSystem",
    )
    # Quiz-bearing skill with a SingleChoice and a MultipleChoice assessment.
    s3 = Skill(
        skill_id="bayes",
        name="Bayes & Rule",
        stratum=Stratum.PROBABILITY,
        objective="Update beliefs.",
        description="Posterior ∝ likelihood × prior.",
        prerequisites=("addition",),
        self_reporting_type="Quiz",
        assessments=(
            AssessmentQuestion(
                prompt="Bayes updates the ___?",
                answers=("prior", "posterior", "constant"),
                correct=(1,),
                question_type="SingleChoice",
            ),
            AssessmentQuestion(
                prompt="Which are probability axioms?",
                answers=("non-negativity", "normalisation", "linearity"),
                correct=(0, 1),
                question_type="MultipleChoice",
            ),
        ),
    )
    math_subject = Subject(
        subject_id="math",
        name="Math Foundations",
        stratum=Stratum.MATH_FOUNDATIONS,
        description="Foundations.",
        skills=(s1, s2),
    )
    prob_subject = Subject(
        subject_id="prob",
        name="Probability",
        stratum=Stratum.PROBABILITY,
        description="Probability.",
        skills=(s3,),
    )
    edges = [("counting", "addition"), ("addition", "bayes")]
    return CurriculumGraphFixture([math_subject, prob_subject], edges)


def test_graph_fixture_satisfies_protocol() -> None:
    # The fixture is structurally a CurriculumGraphLike (runtime_checkable).
    assert isinstance(_build_graph(), CurriculumGraphLike)


def test_export_counts_subjects_skills_dependencies() -> None:
    graph = _build_graph()
    project = export_project(graph, "ai", "Active Inference")

    assert project.project_id == "ai"
    assert project.name == "Active Inference"
    assert len(project.subjects) == 2
    total_skills = sum(len(s.skills) for s in project.subjects)
    assert total_skills == 3
    assert len(project.dependencies) == 2


def test_export_summary_matches_project_and_payload_counts() -> None:
    graph = _build_graph()
    project = export_project(graph, "ai", "Active Inference")

    project_summary = summarize_project(project)
    payload_summary = summarize_export_payload(project.to_export_dict())

    assert payload_summary == project_summary
    assert project_summary.project_counts() == {
        "subjects": 2,
        "skills": 3,
        "dependencies": 2,
        "quizzes": 1,
    }
    assert project_summary.assessments == 2


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"subjects": {}}, "SkillTree project subjects must be a list"),
        ({"subjects": [None]}, "SkillTree project subject 1 is not an object"),
        (
            {"subjects": [{"skills": {}}]},
            "SkillTree project subject 1 skills must be a list",
        ),
        ({"quizzes": [None]}, "SkillTree project quiz 1 is not an object"),
        (
            {"quizzes": [{"questions": {}}]},
            "SkillTree project quiz 1 questions must be a list",
        ),
    ],
)
def test_export_summary_rejects_malformed_payload_collections(
    payload: dict[str, object], message: str
) -> None:
    with pytest.raises(SkillTreeSummaryError, match=message):
        summarize_export_payload(payload)


def test_export_summary_non_strict_discards_malformed_nested_counts() -> None:
    summary = summarize_export_payload(
        {
            "subjects": [None, {"skills": {}}],
            "dependencies": {},
            "quizzes": [None, {"questions": {}}],
        },
        strict=False,
    )

    assert summary == ExportSummary(
        subjects=2,
        skills=0,
        dependencies=0,
        quizzes=2,
        assessments=0,
    )


def test_dependency_edge_direction() -> None:
    graph = _build_graph()
    project = export_project(graph, "ai", "Active Inference")
    # Edge (prerequisite, dependent) => dependent depends on prerequisite.
    deps = {(d.skill_id, d.depends_on_skill_id) for d in project.dependencies}
    assert ("addition", "counting") in deps
    assert ("bayes", "addition") in deps


def test_quiz_built_only_for_quiz_skill_with_assessments() -> None:
    graph = _build_graph()
    project = export_project(graph, "ai", "Active Inference")
    # Only the 'bayes' skill is Quiz-typed with assessments.
    assert len(project.quizzes) == 1
    quiz = project.quizzes[0]
    assert quiz.quiz_id == "bayes_quiz"
    assert quiz.name == "Bayes and Rule Quiz"
    assert len(quiz.questions) == 2
    bayes = next(
        s for subj in project.subjects for s in subj.skills if s.skill_id == "bayes"
    )
    assert bayes.quiz_id == "bayes_quiz"
    assert bayes.to_dict()["quizId"] == "bayes_quiz"


def test_quiz_exports_explicit_passing_contract() -> None:
    # M4: every exported quiz must carry an explicit passing threshold and question count
    # so completion gating is a stated contract, not a SkillTree server default.
    graph = _build_graph()
    project = export_project(graph, "ai", "Active Inference")
    assert project.quizzes
    for quiz in project.quizzes:
        payload = quiz.to_dict()
        assert payload["numQuestions"] == len(quiz.questions)
        assert payload["numQuestions"] >= 1
        assert 1 <= payload["passingPercent"] <= 100
        # The high-integrity default requires every question correct to pass.
        assert payload["passingPercent"] == 100


def test_quiz_correct_flags_mapped_from_indices() -> None:
    graph = _build_graph()
    project = export_project(graph, "ai", "Active Inference")
    quiz = project.quizzes[0]

    single = quiz.questions[0].to_dict()
    assert single["questionType"] == "SingleChoice"
    assert [a["isCorrect"] for a in single["answers"]] == [False, True, False]

    multi = quiz.questions[1].to_dict()
    assert multi["questionType"] == "MultipleChoice"
    assert [a["isCorrect"] for a in multi["answers"]] == [True, True, False]


def test_description_carried_verbatim() -> None:
    graph = _build_graph()
    project = export_project(graph, "ai", "Active Inference")
    bayes = next(
        s for subj in project.subjects for s in subj.skills if s.skill_id == "bayes"
    )
    assert bayes.description == "Posterior ∝ likelihood × prior."


def test_duplicate_skill_id_raises() -> None:
    # Plant a duplicate skillId across two subjects.
    dup_a = Skill(
        skill_id="dup",
        name="Dup A",
        stratum=Stratum.MATH_FOUNDATIONS,
        objective="o",
        description="d",
        self_reporting_type="HonorSystem",
    )
    dup_b = Skill(
        skill_id="dup",
        name="Dup B",
        stratum=Stratum.PROBABILITY,
        objective="o",
        description="d",
        self_reporting_type="HonorSystem",
    )
    subj_a = Subject(
        subject_id="a",
        name="A",
        stratum=Stratum.MATH_FOUNDATIONS,
        description="d",
        skills=(dup_a,),
    )
    subj_b = Subject(
        subject_id="b",
        name="B",
        stratum=Stratum.PROBABILITY,
        description="d",
        skills=(dup_b,),
    )
    graph = CurriculumGraphFixture([subj_a, subj_b], [])
    with pytest.raises(ExportError, match="duplicate skillId"):
        export_project(graph, "ai", "Active Inference")


def test_export_to_json_writes_deterministic_sorted_json(tmp_path) -> None:
    graph = _build_graph()
    out = tmp_path / "nested" / "project.json"
    returned = export_to_json(graph, "ai", "Active Inference", out)
    assert returned == out
    assert out.exists()

    text = out.read_text(encoding="utf-8")
    # Deterministic: re-export produces byte-identical output.
    out2 = tmp_path / "nested" / "project2.json"
    export_to_json(graph, "ai", "Active Inference", out2)
    assert out2.read_text(encoding="utf-8") == text

    payload = json.loads(text)
    assert payload["projectId"] == "ai"
    # sort_keys => top-level keys are alphabetically ordered.
    assert list(payload.keys()) == sorted(payload.keys())


def test_export_to_json_rejects_dangling_dependency_at_serialization_boundary(
    tmp_path,
) -> None:
    # The in-memory model can represent a dependency before the live graph is
    # reconciled. The serialized handoff must not allow that dangling reference
    # to reach the dashboard or seeder.
    graph = CurriculumGraphFixture(_build_graph().subjects, [("counting", "missing")])
    with pytest.raises(SkillTreeSummaryError, match="unknown skill"):
        export_to_json(graph, "ai", "Active Inference", tmp_path / "project.json")


def test_real_curriculum_export_quizzes_carry_passing_contract() -> None:
    # M4 on the production curriculum (not just a fixture): every exported quiz in the
    # full build carries an explicit passing contract.
    from src.curriculum.catalog import build_curriculum

    project = export_project(
        build_curriculum(), "activeInference", "Active Skillference"
    )
    assert project.quizzes
    for quiz in project.quizzes:
        payload = quiz.to_dict()
        assert payload["numQuestions"] == len(quiz.questions) >= 1
        assert 1 <= payload["passingPercent"] <= 100
