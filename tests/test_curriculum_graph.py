"""Tests for the prerequisite-DAG engine."""

from __future__ import annotations

import pytest

from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import (
    AssessmentQuestion,
    CurriculumError,
    Skill,
    Stratum,
    Subject,
)

_M = Stratum.MATH_FOUNDATIONS
_APP = Stratum.APPLICATIONS


def _q() -> AssessmentQuestion:
    return AssessmentQuestion("Q", ("a", "b"), (0,))


def _skill(sid: str, stratum: Stratum, prereqs: tuple[str, ...]) -> Skill:
    return Skill(sid, sid, stratum, "obj", "desc", prereqs, (_q(),))


def _graph(*skills: Skill) -> CurriculumGraph:
    by_stratum: dict[Stratum, list[Skill]] = {}
    for sk in skills:
        by_stratum.setdefault(sk.stratum, []).append(sk)
    subjects = [
        Subject(f"sub_{st.value}", st.value, st, "d", tuple(sks))
        for st, sks in by_stratum.items()
    ]
    return CurriculumGraph(subjects)


def test_valid_chain_passes() -> None:
    g = _graph(
        _skill("a", _M, ()),
        _skill("b", _M, ("a",)),
        _skill("c", _APP, ("b",)),
    )
    g.validate()
    assert g.is_connected_foundations_to_applications()
    assert g.skills_without_foundation_path() == ()


def test_duplicate_id_raises() -> None:
    g = _graph(_skill("a", _M, ()), _skill("a", _M, ()))
    with pytest.raises(CurriculumError, match="duplicate"):
        g.validate()


def test_duplicate_name_raises() -> None:
    """Distinct ids but a shared display name must fail validation.

    SkillTree requires project-wide unique skill names; a collision otherwise
    corrupts the live re-seed silently (the duplicate-named skill is never
    created, so its prerequisite edges later 404).
    """
    a = Skill("a", "Shared Title", _M, "obj", "desc", (), (_q(),))
    b = Skill("b", "Shared Title", _M, "obj", "desc", (), (_q(),))
    g = _graph(a, b)
    with pytest.raises(CurriculumError, match="duplicate skill name"):
        g.validate()


def test_duplicate_subject_name_raises() -> None:
    """Distinct subject ids but a shared subject name must fail validation.

    Subjects route through the same idempotent re-seed swallow path as skills, so
    a duplicate subject name would be silently dropped live (Forge HUNT 2).
    """
    s1 = Subject("sub_a", "Shared Subject", _M, "d", (_skill("a", _M, ()),))
    s2 = Subject("sub_b", "Shared Subject", _M, "d", (_skill("b", _M, ()),))
    g = CurriculumGraph([s1, s2])
    with pytest.raises(CurriculumError, match="duplicate subject name"):
        g.validate()


def test_duplicate_subject_id_raises() -> None:
    s1 = Subject("dup", "Subject One", _M, "d", (_skill("a", _M, ()),))
    s2 = Subject("dup", "Subject Two", _M, "d", (_skill("b", _M, ()),))
    g = CurriculumGraph([s1, s2])
    with pytest.raises(CurriculumError, match="duplicate subject_id"):
        g.validate()


def test_skill_subject_id_collision_raises() -> None:
    """A skill id equal to a subject id collides in SkillTree's shared namespace."""
    s = Subject("collide", "A Subject", _M, "d", (_skill("collide", _M, ()),))
    g = CurriculumGraph([s])
    with pytest.raises(CurriculumError, match="namespace collision"):
        g.validate()


def test_dangling_prerequisite_raises() -> None:
    g = _graph(_skill("a", _M, ("missing",)))
    with pytest.raises(CurriculumError, match="dangling"):
        g.validate()


def test_self_loop_raises() -> None:
    g = _graph(_skill("a", _M, ("a",)))
    with pytest.raises(CurriculumError, match="itself"):
        g.validate()


def test_cycle_raises_with_path() -> None:
    g = _graph(
        _skill("a", _M, ("c",)),
        _skill("b", _M, ("a",)),
        _skill("c", _M, ("b",)),
    )
    with pytest.raises(CurriculumError, match="cycle"):
        g.validate()


def test_non_foundational_root_raises() -> None:
    g = _graph(_skill("app1", _APP, ()))
    with pytest.raises(CurriculumError, match="no prerequisites"):
        g.validate()


def test_topological_order_respects_prerequisites() -> None:
    g = _graph(
        _skill("a", _M, ()),
        _skill("b", _M, ("a",)),
        _skill("c", _APP, ("a", "b")),
    )
    order = [s.skill_id for s in g.topological_order()]
    assert order.index("a") < order.index("b") < order.index("c")


def test_topological_order_is_deterministic() -> None:
    g = _graph(_skill("a", _M, ()), _skill("b", _M, ()), _skill("c", _APP, ("a", "b")))
    assert g.topological_order() == g.topological_order()


def test_levels_increase_along_chain() -> None:
    g = _graph(
        _skill("a", _M, ()),
        _skill("b", _M, ("a",)),
        _skill("c", _APP, ("b",)),
    )
    levels = g.levels()
    assert levels["a"] == 0 and levels["b"] == 1 and levels["c"] == 2


def test_connectivity_true_when_path_exists() -> None:
    g = _graph(
        _skill("a", _M, ()),
        _skill("p", Stratum.PROBABILITY, ()),
        _skill("app", _APP, ("p",)),
    )
    # 'app' is reachable from foundational root 'p'.
    assert g.is_connected_foundations_to_applications()


def test_connectivity_false_when_application_unreachable() -> None:
    # 'orphan' is a non-foundational root (COMPUTATION): structurally parseable but it
    # would fail validate(). 'app' depends only on it, so 'app' is NOT reachable from
    # any foundational root and connectivity is False (exercises the False branch).
    g = _graph(
        _skill("p", Stratum.PROBABILITY, ()),  # a real foundational root
        _skill("orphan", Stratum.COMPUTATION, ()),  # non-foundational root
        _skill("app", _APP, ("orphan",)),
    )
    assert not g.is_connected_foundations_to_applications()
    assert g.skills_without_foundation_path() == ("app", "orphan")


def test_get_skill_missing_raises() -> None:
    g = _graph(_skill("a", _M, ()))
    with pytest.raises(CurriculumError):
        g.get_skill("nope")


def test_stats_reports_counts() -> None:
    g = _graph(_skill("a", _M, ()), _skill("b", _M, ("a",)), _skill("c", _APP, ("b",)))
    stats = g.stats()
    assert stats["skills"] == 3
    assert stats["prerequisite_edges"] == 2
    assert stats["roots"] == 1
    assert stats["max_depth"] == 2


def test_connectivity_fails_closed_when_no_foundational_roots() -> None:
    # If the only root is non-foundational, BFS seeds from the empty set and reaches
    # nothing -> any application is unreachable -> False (fail-closed, not vacuous pass).
    g = _graph(
        _skill("orphan", Stratum.COMPUTATION, ()),
        _skill("app", _APP, ("orphan",)),
    )
    assert g.reachable_from_foundations() == set()
    assert not g.is_connected_foundations_to_applications()
