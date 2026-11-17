"""Learner fields share canonical claim admission and retain original claim IDs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from src.curriculum.graph import CurriculumGraph
from src.curriculum.materials import (
    audit_course_material_index,
    build_course_material_index,
)
from src.curriculum.model import AssessmentQuestion, Skill, Stratum, Subject
from src.provenance.binding import (
    ProvenanceError,
    lint_graph,
    render_graph,
    validate_curriculum,
    validate_skill,
)
from src.provenance.claims import ClaimRegistry

TOKEN = "{{cl\u200baim:bo\u200bund}}"


def _registry() -> ClaimRegistry:
    registry = ClaimRegistry()
    registry.register("bound", "bound-value")
    return registry


def _skill() -> Skill:
    return Skill(
        "a",
        "A",
        Stratum.MATH_FOUNDATIONS,
        "Objective",
        "Description",
        (),
        (AssessmentQuestion("Question", ("one", "two"), (0,)),),
    )


def _field(skill: Skill, name: str, value: str) -> Skill:
    if name == "assessment_prompt":
        return replace(
            skill, assessments=(replace(skill.assessments[0], prompt=value),)
        )
    if name == "assessment_answer":
        return replace(
            skill, assessments=(replace(skill.assessments[0], answers=(value, "two")),)
        )
    return replace(skill, **{name: value})


@pytest.mark.parametrize(
    "field",
    ["name", "objective", "description", "assessment_prompt", "assessment_answer"],
)
@pytest.mark.parametrize(
    "token",
    [
        "{{claim:missing}}",
        "{{ claim:bound }}",
        "{{claim:bad-id}}",
        "{{cl\u200baim:missing}}",
    ],
)
def test_standalone_skill_and_curriculum_validation_reject_every_bad_field(
    field: str, token: str
) -> None:
    skill = _field(_skill(), field, token)
    with pytest.raises(ProvenanceError):
        validate_skill(skill, _registry())
    with pytest.raises(ProvenanceError):
        validate_curriculum([skill], _registry())


@pytest.mark.parametrize(
    "field",
    ["name", "objective", "description", "assessment_prompt", "assessment_answer"],
)
def test_format_character_normalization_preserves_original_claim_identity(
    field: str,
) -> None:
    skill = _field(_skill(), field, TOKEN)
    assert skill.claim_tokens() == {"bound"}
    validate_skill(skill, _registry())


def _graph() -> CurriculumGraph:
    first = replace(
        _skill(),
        name=f"A {TOKEN}",
        objective=f"Objective {TOKEN}",
        description=f"Description {TOKEN}",
    )
    second = replace(_skill(), skill_id="b", name=f"B {TOKEN}", prerequisites=("a",))
    return CurriculumGraph(
        [
            Subject(
                "sub_m",
                f"Subject {TOKEN}",
                Stratum.MATH_FOUNDATIONS,
                "Subject description",
                (first, second),
            )
        ]
    )


def _sources(*, claims: bool = True) -> dict:
    value = TOKEN if claims else "bound-value"
    pointer = {
        "source_id": "fixture",
        "path": "lessons/intro.md",
        "title": f"Pointer {value}",
        "role": f"Role {value}",
    }
    return {
        "version": 1,
        "sources": [
            {
                "source_id": "fixture",
                "repo_url": "https://github.com/fixture/materials",
                "commit": "a" * 40,
                "title": f"Source {value}",
                "license_status": f"License {value}",
                "status_note": f"Status {value}",
                "path_globs": ["lessons/*.md"],
            }
        ],
        "stratum_mappings": {stratum.value: [dict(pointer)] for stratum in Stratum},
        "topic_mappings": [],
    }


def test_material_names_references_context_and_source_labels_render_without_losing_claim_ids() -> (
    None
):
    graph = _graph()
    index = build_course_material_index(graph, _sources(), registry=_registry())
    first, second = index["skills"]["a"], index["skills"]["b"]

    assert (
        first["name"] == "A bound-value"
        and first["subjectName"] == "Subject bound-value"
    )
    assert second["prerequisites"][0]["name"] == "A bound-value"
    assert second["relatedSkills"][0]["subjectName"] == "Subject bound-value"
    assert first["downstreamSkills"][0]["name"] == "B bound-value"
    assert "A bound-value (a)" in "\n".join(
        section["body"] for section in second["sections"]
    )
    assert "B bound-value (b)" in "\n".join(
        section["body"] for section in first["sections"]
    )
    assert first["provenance"]["claimTokens"] == ["bound"]
    assert first["externalPointers"][0]["title"] == "Pointer bound-value"
    assert first["externalPointers"][0]["role"] == "Role bound-value"
    assert index["sources"][0]["title"] == "Source bound-value"
    assert index["sources"][0]["statusNote"] == "Status bound-value"
    assert audit_course_material_index(index, graph).issues == ()


def test_material_builder_without_registry_accepts_claim_free_input_but_refuses_raw_claims() -> (
    None
):
    graph = _graph()
    with pytest.raises(ProvenanceError):
        build_course_material_index(graph, _sources(claims=False))
    rendered = render_graph(graph, _registry())
    index = build_course_material_index(rendered, _sources(claims=False))
    assert index["skills"]["a"]["name"] == "A bound-value"


@pytest.mark.parametrize(
    "field", ["name", "subjectName", "prerequisite", "section", "source", "pointer"]
)
@pytest.mark.parametrize(
    "token", ["{{claim:missing}}", "{{ claim:bound }}", "{{cl\u200baim:missing}}"]
)
def test_material_audit_catches_unrendered_tokens_outside_section_bodies(
    field: str, token: str
) -> None:
    graph = _graph()
    index = deepcopy(
        build_course_material_index(graph, _sources(), registry=_registry())
    )
    record = index["skills"]["b"]
    if field in ("name", "subjectName"):
        record[field] = token
    elif field == "prerequisite":
        record["prerequisites"][0]["name"] = token
    elif field == "section":
        record["sections"][0]["body"] = token
    elif field == "source":
        index["sources"][0]["title"] = token
    else:
        record["externalPointers"][0]["title"] = token
    issues = audit_course_material_index(index, graph).issues
    assert any(issue.code == "unresolved-claim-token" for issue in issues)


def test_subject_name_is_rendered_and_is_part_of_numeric_lint() -> None:
    graph = _graph()
    assert render_graph(graph, _registry()).subjects[0].name == "Subject bound-value"
    malformed = CurriculumGraph([replace(graph.subjects[0], name="{{ claim:bound }}")])
    with pytest.raises(ProvenanceError):
        render_graph(malformed, _registry())
    unbacked = CurriculumGraph([replace(graph.subjects[0], name="Result 2.75 nats")])
    violations = lint_graph(unbacked)
    assert len(violations) == 1 and violations[0].value == "2.75"


def test_subject_names_that_collide_after_rendering_are_refused() -> None:
    from src.curriculum.model import CurriculumError

    registry = ClaimRegistry()
    registry.register("first", "same")
    registry.register("second", "same")
    first = _skill()
    second = replace(first, skill_id="b", name="B", prerequisites=("a",))
    graph = CurriculumGraph(
        [
            Subject("sub_a", "Course {{claim:first}}", first.stratum, "", (first,)),
            Subject("sub_b", "Course {{claim:second}}", second.stratum, "", (second,)),
        ]
    )
    graph.validate()
    with pytest.raises(CurriculumError, match="duplicate subject name"):
        render_graph(graph, registry)
