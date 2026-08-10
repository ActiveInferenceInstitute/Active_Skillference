"""Tests for the assembled Active Inference curriculum (the real catalog)."""

from __future__ import annotations

import pytest

import src.curriculum.catalog as catalog_module
from src.curriculum.catalog import build_curriculum
from src.curriculum.model import ALL_STRATA, CurriculumError, Stratum
from src.curriculum.vfe_efe_bridge import (
    VFE_EFE_BRIDGE_SUBJECT_IDS,
    build_vfe_efe_bridge_rows,
    vfe_efe_bridge_markdown_table,
)


def test_catalog_builds_and_validates() -> None:
    # build_curriculum() calls validate() internally; reaching here means it passed.
    graph = build_curriculum()
    assert graph.skills


def test_build_curriculum_raises_when_disconnected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fail-closed connectivity guard raises rather than returning a broken graph."""
    monkeypatch.setattr(
        catalog_module.CurriculumGraph,
        "is_connected_foundations_to_applications",
        lambda self: False,
    )
    with pytest.raises(CurriculumError, match="not connected"):
        build_curriculum()


def test_maximal_enumeration_at_least_600_skills() -> None:
    graph = build_curriculum()
    assert len(graph.skills) == 630
    assert len(graph.subjects) == 111
    assert len(graph.prerequisite_edges()) == 1199
    assert sum(len(skill.assessments) for skill in graph.skills) == 2520


def test_all_eight_strata_present() -> None:
    graph = build_curriculum()
    assert graph.strata_present() == set(ALL_STRATA)


def test_every_stratum_has_at_least_one_subject() -> None:
    graph = build_curriculum()
    strata_with_subjects = {s.stratum for s in graph.subjects}
    assert strata_with_subjects == set(ALL_STRATA)


def test_connected_foundations_to_applications() -> None:
    graph = build_curriculum()
    assert graph.is_connected_foundations_to_applications()
    assert graph.skills_without_foundation_path() == ()


def test_every_skill_has_objective_and_assessment() -> None:
    graph = build_curriculum()
    for skill in graph.skills:
        assert skill.objective.strip(), skill.skill_id
        assert len(skill.assessments) >= 4, skill.skill_id
        assert any(q.question_type == "MultipleChoice" for q in skill.assessments)


def test_non_foundational_skills_have_prerequisites() -> None:
    graph = build_curriculum()
    for skill in graph.skills:
        if not skill.stratum.is_foundational:
            assert skill.prerequisites, f"{skill.skill_id} is a non-foundational root"


def test_roots_only_in_foundational_strata() -> None:
    graph = build_curriculum()
    roots = [s for s in graph.skills if s.is_root]
    assert roots, "expected at least one root"
    assert all(s.stratum.is_foundational for s in roots)


def test_no_backward_stratum_prerequisites() -> None:
    graph = build_curriculum()
    skill_by_id = {skill.skill_id: skill for skill in graph.skills}

    for prereq_id, dependent_id in graph.prerequisite_edges():
        assert (
            skill_by_id[prereq_id].stratum.order
            <= skill_by_id[dependent_id].stratum.order
        ), (prereq_id, dependent_id)


def test_skill_ids_are_unique() -> None:
    graph = build_curriculum()
    ids = [s.skill_id for s in graph.skills]
    assert len(ids) == len(set(ids))


def test_applications_stratum_is_the_canopy() -> None:
    graph = build_curriculum()
    levels = graph.levels()
    app_levels = [
        levels[s.skill_id] for s in graph.skills if s.stratum is Stratum.APPLICATIONS
    ]
    # applications skills sit deep in the DAG (well past the roots)
    assert min(app_levels) >= 3


def test_frontier_topic_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    frontier = [s for s in graph.subjects if s.subject_id.startswith("sub_frontier_")]

    assert {s.subject_id for s in frontier} == {
        "sub_frontier_math",
        "sub_frontier_probability",
        "sub_frontier_information",
        "sub_frontier_variational",
        "sub_frontier_fep",
        "sub_frontier_ai",
        "sub_frontier_computation",
        "sub_frontier_applications",
    }
    assert {s.stratum for s in frontier} == set(ALL_STRATA)
    assert {len(s.skills) for s in frontier} == {5}


def test_practice_translation_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    practice = [s for s in graph.subjects if s.subject_id.startswith("sub_practice_")]

    assert {s.subject_id for s in practice} == {
        "sub_practice_math",
        "sub_practice_probability",
        "sub_practice_information",
        "sub_practice_variational",
        "sub_practice_fep",
        "sub_practice_active_inference",
        "sub_practice_computation",
        "sub_practice_applications",
    }
    assert {s.stratum for s in practice} == set(ALL_STRATA)
    assert {len(s.skills) for s in practice} == {3}
    assert all(
        len(skill.assessments) >= 3 for subject in practice for skill in subject.skills
    )


def test_open_science_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    open_science = [
        s for s in graph.subjects if s.subject_id.startswith("sub_open_science_")
    ]

    assert {s.subject_id for s in open_science} == {
        "sub_open_science_math",
        "sub_open_science_probability",
        "sub_open_science_information",
        "sub_open_science_variational",
        "sub_open_science_fep",
        "sub_open_science_active_inference",
        "sub_open_science_computation",
        "sub_open_science_applications",
    }
    assert {s.stratum for s in open_science} == set(ALL_STRATA)
    assert {len(s.skills) for s in open_science} == {8}


def test_next_hardening_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    subject_ids = {
        "sub_continuous_dynamics",
        "sub_state_space_probability",
        "sub_rate_distortion_information",
        "sub_continuous_variational",
        "sub_predictive_coding_process",
        "sub_hierarchical_active_inference",
        "sub_reproducible_simulation_labs",
        "sub_applied_evaluation_dossiers",
    }
    subjects = [
        subject for subject in graph.subjects if subject.subject_id in subject_ids
    ]

    assert {subject.subject_id for subject in subjects} == subject_ids
    assert {subject.stratum for subject in subjects} == set(ALL_STRATA)
    assert {len(subject.skills) for subject in subjects} == {6}


def test_scientific_supplement_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    subject_ids = {
        "sub_scientific_supplement_math",
        "sub_scientific_supplement_probability",
        "sub_scientific_supplement_information",
        "sub_scientific_supplement_variational",
        "sub_scientific_supplement_fep",
        "sub_scientific_supplement_active_inference",
        "sub_scientific_supplement_computation",
        "sub_scientific_supplement_applications",
    }
    subjects = [
        subject for subject in graph.subjects if subject.subject_id in subject_ids
    ]

    assert {subject.subject_id for subject in subjects} == subject_ids
    assert {subject.stratum for subject in subjects} == set(ALL_STRATA)
    assert {len(subject.skills) for subject in subjects} == {6}


def test_visual_reasoning_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    subject_ids = {
        "sub_visual_reasoning_math",
        "sub_visual_reasoning_probability",
        "sub_visual_reasoning_information",
        "sub_visual_reasoning_variational",
        "sub_visual_reasoning_fep",
        "sub_visual_reasoning_active_inference",
        "sub_visual_reasoning_computation",
        "sub_visual_reasoning_applications",
    }
    subjects = [
        subject for subject in graph.subjects if subject.subject_id in subject_ids
    ]

    assert {subject.subject_id for subject in subjects} == subject_ids
    assert {subject.stratum for subject in subjects} == set(ALL_STRATA)
    assert {len(subject.skills) for subject in subjects} == {4}


def test_visual_evidence_contract_subjects_and_edges_are_exact() -> None:
    graph = build_curriculum()
    subject_by_id = {subject.subject_id: subject for subject in graph.subjects}
    skill_by_id = {skill.skill_id: skill for skill in graph.skills}
    expected_prereqs = {
        "vdiag_question_contract": ("viz_computation_04", "pub_computation_04"),
        "vdiag_data_grain_audit": ("vdiag_question_contract", "os_computation_04"),
        "vdiag_encoding_strength_audit": (
            "vdiag_data_grain_audit",
            "viz_math_01",
        ),
        "vdiag_annotation_claim_boundary": (
            "vdiag_encoding_strength_audit",
            "sci_computation_02",
        ),
        "vdiag_static_mobile_survival": (
            "vdiag_annotation_claim_boundary",
            "front_comp_dashboard_observability",
        ),
        "vdiag_visual_negative_control": (
            "vdiag_static_mobile_survival",
            "audit_computation_03",
        ),
        "aiviz_policy_landscape_reading": (
            "viz_active_inference_04",
            "sci_active_inference_03",
        ),
        "aiviz_precision_regime_visuals": (
            "aiviz_policy_landscape_reading",
            "ai_expected_free_energy",
        ),
        "aiviz_efe_component_contrast": (
            "aiviz_precision_regime_visuals",
            "sci_active_inference_01",
        ),
        "aiviz_preference_surface_caveats": (
            "aiviz_efe_component_contrast",
            "pub_active_inference_03",
        ),
        "aiviz_action_failure_panel": (
            "aiviz_preference_surface_caveats",
            "audit_active_inference_04",
        ),
        "aiviz_stakeholder_handoff_caption": (
            "aiviz_action_failure_panel",
            "pub_active_inference_04",
        ),
    }

    computation = subject_by_id["sub_visual_evidence_contracts"]
    active = subject_by_id["sub_active_inference_visual_explanation"]

    assert computation.stratum is Stratum.COMPUTATION
    assert active.stratum is Stratum.ACTIVE_INFERENCE
    assert [skill.skill_id for skill in computation.skills] == [
        "vdiag_question_contract",
        "vdiag_data_grain_audit",
        "vdiag_encoding_strength_audit",
        "vdiag_annotation_claim_boundary",
        "vdiag_static_mobile_survival",
        "vdiag_visual_negative_control",
    ]
    assert [skill.skill_id for skill in active.skills] == [
        "aiviz_policy_landscape_reading",
        "aiviz_precision_regime_visuals",
        "aiviz_efe_component_contrast",
        "aiviz_preference_surface_caveats",
        "aiviz_action_failure_panel",
        "aiviz_stakeholder_handoff_caption",
    ]
    reachable = graph.reachable_from_foundations()
    for skill_id, prereqs in expected_prereqs.items():
        skill = skill_by_id[skill_id]
        assert skill.prerequisites == prereqs
        assert len(skill.assessments) == 4
        assert skill_id in reachable


def test_publication_synthesis_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    subject_ids = {
        "sub_publication_synthesis_math",
        "sub_publication_synthesis_probability",
        "sub_publication_synthesis_information",
        "sub_publication_synthesis_variational",
        "sub_publication_synthesis_fep",
        "sub_publication_synthesis_active_inference",
        "sub_publication_synthesis_computation",
        "sub_publication_synthesis_applications",
    }
    subjects = [
        subject for subject in graph.subjects if subject.subject_id in subject_ids
    ]

    assert {subject.subject_id for subject in subjects} == subject_ids
    assert {subject.stratum for subject in subjects} == set(ALL_STRATA)
    assert {len(subject.skills) for subject in subjects} == {4}


def test_scientific_audit_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    subject_ids = {
        "sub_scientific_audit_math",
        "sub_scientific_audit_probability",
        "sub_scientific_audit_information",
        "sub_scientific_audit_variational",
        "sub_scientific_audit_fep",
        "sub_scientific_audit_active_inference",
        "sub_scientific_audit_computation",
        "sub_scientific_audit_applications",
    }
    subjects = [
        subject for subject in graph.subjects if subject.subject_id in subject_ids
    ]

    assert {subject.subject_id for subject in subjects} == subject_ids
    assert {subject.stratum for subject in subjects} == set(ALL_STRATA)
    assert {len(subject.skills) for subject in subjects} == {4}


def test_national_security_context_subject_is_bounded_computation_training() -> None:
    graph = build_curriculum()
    subject = next(
        subject
        for subject in graph.subjects
        if subject.subject_id == "sub_national_security_computation"
    )

    assert subject.stratum is Stratum.COMPUTATION
    assert len(subject.skills) == 8
    assert all(
        "national-security" in skill.tags and "skilltree" in skill.tags
        for skill in subject.skills
    )
    assert all(
        "endorsement" in skill.description or "operator-owned" in skill.description
        for skill in subject.skills
    )


def test_skilltree_mastery_subjects_cover_every_stratum() -> None:
    graph = build_curriculum()
    subject_ids = {
        "sub_skilltree_mastery_math",
        "sub_skilltree_mastery_probability",
        "sub_skilltree_mastery_information",
        "sub_skilltree_mastery_variational",
        "sub_skilltree_mastery_fep",
        "sub_skilltree_mastery_active_inference",
        "sub_skilltree_mastery_computation",
        "sub_skilltree_mastery_applications",
    }
    subjects = [
        subject for subject in graph.subjects if subject.subject_id in subject_ids
    ]

    assert {subject.subject_id for subject in subjects} == subject_ids
    assert {subject.stratum for subject in subjects} == set(ALL_STRATA)
    assert {len(subject.skills) for subject in subjects} == {8}
    assert all(
        "skilltree-mastery" in skill.tags
        and len(skill.assessments) >= 4
        and any(q.question_type == "MultipleChoice" for q in skill.assessments)
        for subject in subjects
        for skill in subject.skills
    )


def test_vfe_efe_skilltree_bridge_uses_real_subjects_skills_edges_and_routes() -> None:
    graph = build_curriculum()
    rows = build_vfe_efe_bridge_rows(graph)
    table = vfe_efe_bridge_markdown_table(graph)
    subject_ids = {subject.subject_id for subject in graph.subjects}

    assert tuple(row.subject_id for row in rows) == VFE_EFE_BRIDGE_SUBJECT_IDS
    assert all(row.subject_id in subject_ids for row in rows)
    assert all(row.skill_count > 0 for row in rows)
    assert all(row.prerequisite_edges > 0 for row in rows)
    assert all(row.min_depth <= row.max_depth for row in rows)
    assert all(row.representative_skill_ids for row in rows)
    assert all(
        route.startswith("/subjects/") for route in (row.learn_route for row in rows)
    )
    assert all("/quizzes/" in row.quiz_route for row in rows)
    assert "Representative IDs" in table
    assert "Learn route | Quiz route" in table
    assert "/subjects/sub_free_energy" in table
    assert "Route fragment" not in table


def test_real_skilltree_export_has_four_question_quizzes() -> None:
    from src.kernels.examples import build_claim_registry
    from src.project_identity import SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME
    from src.provenance.binding import render_graph
    from src.skilltree.exporter import export_project

    rendered = render_graph(build_curriculum(), build_claim_registry())
    project = export_project(rendered, SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME)

    assert len(project.quizzes) >= 600
    assert all(len(quiz.questions) >= 4 for quiz in project.quizzes)


def test_subject_names_respect_live_skilltree_limit() -> None:
    graph = build_curriculum()

    assert all(len(subject.name) <= 50 for subject in graph.subjects)
