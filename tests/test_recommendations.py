"""Tests for the graph-only adaptive path prototype."""

from __future__ import annotations

import pytest

from src.curriculum.recommendations import recommend_next_skills


def _project() -> dict[str, object]:
    return {
        "subjects": [
            {
                "subjectId": "sub_foundations",
                "name": "Foundations",
                "skills": [
                    {
                        "skillId": "math_sets",
                        "name": "Set reasoning",
                        "description": "Use set reasoning to describe probability events.",
                        "quizId": "math_sets_quiz",
                    },
                    {
                        "skillId": "prob_events",
                        "name": "Probability events",
                        "description": "Connect probability events to set reasoning.",
                        "quizId": "prob_events_quiz",
                    },
                ],
            },
            {
                "subjectId": "sub_inference",
                "name": "Inference",
                "skills": [
                    {
                        "skillId": "bayes_update",
                        "name": "Bayesian update",
                        "description": "Update beliefs after observing evidence.",
                        "quizId": "bayes_update_quiz",
                    }
                ],
            },
        ],
        "dependencies": [
            {"skillId": "prob_events", "dependsOnSkillId": "math_sets"},
            {"skillId": "bayes_update", "dependsOnSkillId": "prob_events"},
        ],
        "quizzes": [
            {
                "quizId": "math_sets_quiz",
                "questions": [{"question": "What is a set?"}],
            },
            {
                "quizId": "prob_events_quiz",
                "questions": [{"question": "How do events relate to sets?"}],
            },
            {
                "quizId": "bayes_update_quiz",
                "questions": [{"question": "How does evidence update belief?"}],
            },
        ],
    }


def test_recommendations_are_deterministic_and_foundation_bounded() -> None:
    first = recommend_next_skills(_project(), limit=4)
    second = recommend_next_skills(_project(), limit=4)

    assert first == second
    assert first["signalSource"] == "none"
    assert first["personalized"] is False
    assert [row["skillId"] for row in first["recommendations"]] == ["math_sets"]
    assert first["recommendations"][0]["officialSkillTree"]["subjectRoute"] == (
        "/subjects/sub_foundations"
    )
    assert first["recommendations"][0]["officialSkillTree"]["quizRoute"].endswith(
        "/math_sets_quiz"
    )


def test_completed_progress_exposes_only_the_next_prerequisite_frontier() -> None:
    result = recommend_next_skills(_project(), completed_skill_ids=["math_sets"])

    assert result["signalSource"] == "skilltree"
    assert result["personalized"] is True
    assert [row["skillId"] for row in result["recommendations"]] == ["prob_events"]
    assert result["recommendations"][0]["depth"] == 1


def test_unsuccessful_attempt_is_prioritized_as_an_official_quiz_retake() -> None:
    result = recommend_next_skills(
        _project(),
        completed_skill_ids=["math_sets"],
        unsuccessful_skill_ids=["prob_events"],
    )

    assert [row["skillId"] for row in result["recommendations"]] == ["prob_events"]
    assert "retake" in result["recommendations"][0]["reason"]
    assert "latent learner state" in result["boundary"]


def test_malformed_export_fails_closed_and_limit_is_guarded() -> None:
    result = recommend_next_skills({"subjects": [], "dependencies": [], "quizzes": []})
    assert result["available"] is False
    assert result["recommendations"] == []

    with pytest.raises(ValueError, match="limit must be positive"):
        recommend_next_skills(_project(), limit=0)


def test_ordering_is_dependency_forward_not_retake_dominated() -> None:
    """A shallow available frontier skill precedes a deeper unsuccessful retake."""
    result = recommend_next_skills(
        _project(),
        unsuccessful_skill_ids=["bayes_update"],  # depth 2, retake
    )
    ids = [row["skillId"] for row in result["recommendations"]]
    assert ids[0] == "math_sets"  # depth 0, available frontier
    assert ids.index("math_sets") < ids.index("bayes_update")


def test_frontier_skill_whose_prerequisite_failed_is_remediation() -> None:
    """A satisfied-frontier skill directly remediating an unsuccessful prerequisite is
    categorized as a remediation (not a retake)."""
    result = recommend_next_skills(
        _project(),
        completed_skill_ids=["math_sets"],
        unsuccessful_skill_ids=["math_sets"],
    )
    rows = {row["skillId"]: row for row in result["recommendations"]}
    prob = rows["prob_events"]
    assert "next prerequisite frontier after an unsuccessful attempt" in prob["reason"]
    # It is a remediation, not flagged as the official quiz retake itself.
    assert "retake the official quiz" not in prob["reason"]


def test_cyclic_exports_fail_closed_to_zero_depths() -> None:
    """A dependency cycle in a malformed export makes _depths fail closed (depth 0)."""
    project = {
        "subjects": [
            {
                "subjectId": "s",
                "name": "S",
                "skills": [
                    {"skillId": "a", "name": "A", "description": "a"},
                    {"skillId": "b", "name": "B", "description": "b"},
                ],
            }
        ],
        "dependencies": [
            {"skillId": "a", "dependsOnSkillId": "b"},
            {"skillId": "b", "dependsOnSkillId": "a"},
        ],
        "quizzes": [],
    }
    result = recommend_next_skills(project)
    assert result["available"] is True
    assert all(row["depth"] == 0 for row in result["recommendations"])
