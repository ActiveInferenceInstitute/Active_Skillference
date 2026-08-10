"""Tests for the manuscript variable-map builder (rendered-output value path)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from src.curriculum.catalog import build_curriculum
from src.kernels.examples import build_claim_registry
from src.manuscript.variables import build_manuscript_variables
from src.scholarship.coverage import EXPECTED_LANES

REPO = Path(__file__).resolve().parents[1]


def test_build_manuscript_variables_reports_live_counts() -> None:
    graph = build_curriculum()
    registry = build_claim_registry()

    variables = build_manuscript_variables(registry=registry, graph=graph)

    stats = graph.stats()
    assert variables["skill_count"] == str(stats["skills"])
    assert variables["subject_count"] == str(stats["subjects"])
    assert variables["max_depth"] == str(stats["max_depth"])
    # The disclosed core-concept depth is real and strictly below the headline depth.
    assert variables["core_max_depth"] == str(stats["core_max_depth"])
    assert int(variables["core_max_depth"]) < int(variables["max_depth"])
    # Every registered claim token is rendered into the variable map.
    for name in registry.names():
        assert name in variables


def test_build_manuscript_variables_exports_strata_and_failable_floor() -> None:
    """strata_count and failable_floor are bound from live state, not hand-typed prose."""
    from src.curriculum.quality import MIN_ASSESSMENTS_PER_SKILL

    graph = build_curriculum()
    registry = build_claim_registry()
    variables = build_manuscript_variables(registry=registry, graph=graph)
    assert variables["strata_count"] == str(graph.stats()["strata_count"])
    # The enforced assessment floor is 4, NOT the "three" the manuscript used to claim.
    assert variables["failable_floor"] == str(MIN_ASSESSMENTS_PER_SKILL)
    assert int(variables["failable_floor"]) >= 4


def test_hardcode_linter_is_non_vacuous_on_subsection_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative control: a hand-typed live count in a lettered subsection file (the
    surface the old `[0-9][0-9]_*.md` glob missed) MUST be caught, and the same
    literal beside its token MUST be allowed (positive control)."""
    import scripts.validate_manuscript_variables as vmv

    fixture_manuscript = tmp_path / "manuscript"
    fixture_manuscript.mkdir()
    subsection = fixture_manuscript / "03a_results_curriculum.md"
    monkeypatch.setattr(vmv, "ROOT", tmp_path)
    monkeypatch.setattr(vmv, "MANUSCRIPT", fixture_manuscript)
    variables = {"skill_count": "630"}

    # Negative control: a bare hard-coded count in a subsection file is flagged.
    subsection.write_text("The curriculum has 630 skills today.", encoding="utf-8")
    issues = vmv._issues(variables)
    assert any("03a_results_curriculum.md" in issue for issue in issues), issues

    # Positive control: the same literal adjacent to its token is allowed.
    subsection.write_text(
        "The curriculum has {{skill_count}} (630) skills today.", encoding="utf-8"
    )
    assert vmv._issues(variables) == []


def test_build_manuscript_variables_rejects_inflated_floor(tmp_path: Path) -> None:
    """A config min_skill_count above the real skill count must fail closed (M1)."""
    graph = build_curriculum()
    registry = build_claim_registry()
    inflated = len(graph.skills) + 1
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"experiment": {"min_skill_count": inflated}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="exceeds actual skill count"):
        build_manuscript_variables(
            registry=registry, graph=graph, config_path=config_path
        )


def test_build_manuscript_variables_accepts_consistent_floor(tmp_path: Path) -> None:
    graph = build_curriculum()
    registry = build_claim_registry()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"experiment": {"min_skill_count": len(graph.skills)}}),
        encoding="utf-8",
    )

    variables = build_manuscript_variables(
        registry=registry, graph=graph, config_path=config_path
    )
    assert variables["min_skill_count"] == str(len(graph.skills))


def test_missing_config_file_yields_empty_floor(tmp_path: Path) -> None:
    """A config_path that does not exist is treated as no config (empty floor)."""
    graph = build_curriculum()
    registry = build_claim_registry()
    missing = tmp_path / "does_not_exist.yaml"

    variables = build_manuscript_variables(
        registry=registry, graph=graph, config_path=missing
    )
    # No floor configured -> the rendered min_skill_count is the empty string.
    assert variables["min_skill_count"] == ""


def test_non_mapping_config_payload_is_ignored(tmp_path: Path) -> None:
    """A YAML file whose top-level payload is not a mapping is discarded."""
    graph = build_curriculum()
    registry = build_claim_registry()
    config_path = tmp_path / "config.yaml"
    # A bare list is valid YAML but not a dict -> _load_config returns {}.
    config_path.write_text(yaml.safe_dump(["a", "b"]), encoding="utf-8")

    variables = build_manuscript_variables(
        registry=registry, graph=graph, config_path=config_path
    )
    assert variables["min_skill_count"] == ""


def test_scholarship_summary_counts_propagate() -> None:
    """A scholarship audit carrying a summary mapping feeds the citation counts."""
    graph = build_curriculum()
    registry = build_claim_registry()
    audit = {
        "summary": {
            "citedSources": 7,
            "matrixSources": 11,
            "expectedLanes": 4,
            "sectionsWithCitations": 5,
        }
    }

    variables = build_manuscript_variables(
        registry=registry, graph=graph, scholarship_audit=audit
    )

    assert variables["citation_count"] == "7"
    assert variables["scholarship_source_count"] == "11"
    assert variables["scholarship_lane_count"] == "4"
    assert variables["sections_with_citations"] == "5"


def test_scholarship_audit_without_summary_uses_defaults() -> None:
    """An audit whose 'summary' is not a mapping falls back to default counts."""
    graph = build_curriculum()
    registry = build_claim_registry()
    # summary present but not a Mapping -> the isinstance guard skips it.
    audit = {"summary": ["not", "a", "mapping"]}

    variables = build_manuscript_variables(
        registry=registry, graph=graph, scholarship_audit=audit
    )

    assert variables["citation_count"] == "0"
    assert variables["scholarship_source_count"] == "0"
    # The expected-lane count defaults to the live EXPECTED_LANES length.
    assert variables["scholarship_lane_count"] == str(len(EXPECTED_LANES))
    assert variables["sections_with_citations"] == "0"


def test_summary_int_handles_bool_and_float() -> None:
    """_summary_int coerces bool and float summary values via the public builder."""
    graph = build_curriculum()
    registry = build_claim_registry()
    # bool is a subtype of int; the dedicated bool branch must run first so that
    # True renders as "1" (int(True)) rather than being swallowed by the int path.
    audit = {
        "summary": {
            "citedSources": True,  # bool branch -> 1
            "matrixSources": 3.9,  # float branch -> 3 (truncated)
            # 'expectedLanes' omitted -> default branch returns provided default.
            "sectionsWithCitations": "not-a-number",  # unhandled type -> default 0
        }
    }

    variables = build_manuscript_variables(
        registry=registry, graph=graph, scholarship_audit=audit
    )

    assert variables["citation_count"] == "1"
    assert variables["scholarship_source_count"] == "3"
    assert variables["scholarship_lane_count"] == str(len(EXPECTED_LANES))
    assert variables["sections_with_citations"] == "0"


def test_roadmap_summary_classifies_tasks_and_surfaces() -> None:
    """A populated roadmap is summarised into completed/open/total counts."""
    graph = build_curriculum()
    registry = build_claim_registry()
    roadmap = {
        "project": {"updated": "2026-06-15"},
        "tasks": [
            {"status": "done", "surface": "api"},
            {"status": "todo", "surface": "ui"},
            {"status": "in_progress", "surface": "api"},
            {"status": "blocked", "surface": "docs"},
            {"status": "done"},  # done, no surface
            "not-a-mapping",  # filtered out by the isinstance guard
        ],
    }

    variables = build_manuscript_variables(
        registry=registry, graph=graph, roadmap=roadmap
    )

    assert variables["roadmap_completed_count"] == "2"
    assert variables["roadmap_open_count"] == "3"
    # Five mappings survive the isinstance filter; the bare string is dropped.
    assert variables["roadmap_task_count"] == "5"
    assert variables["roadmap_updated"] == "2026-06-15"
    # Surfaces are de-duplicated and sorted across open tasks only.
    assert variables["roadmap_next_surfaces"] == "api, docs, ui"


def test_roadmap_summary_handles_missing_optional_fields() -> None:
    """Roadmap with no project mapping and non-list tasks degrades gracefully."""
    graph = build_curriculum()
    registry = build_claim_registry()
    # 'tasks' is not a list -> task_rows is empty; 'project' is not a Mapping ->
    # updated stays "". The truthy roadmap still bypasses the empty-default branch.
    roadmap = {"project": "ignored-scalar", "tasks": "not-a-list"}

    variables = build_manuscript_variables(
        registry=registry, graph=graph, roadmap=roadmap
    )

    assert variables["roadmap_completed_count"] == "0"
    assert variables["roadmap_open_count"] == "0"
    assert variables["roadmap_task_count"] == "0"
    assert variables["roadmap_updated"] == ""
    assert variables["roadmap_next_surfaces"] == ""


def test_roadmap_none_yields_zeroed_defaults() -> None:
    """The default (no roadmap) path emits the zeroed roadmap variables."""
    graph = build_curriculum()
    registry = build_claim_registry()

    variables = build_manuscript_variables(registry=registry, graph=graph)

    assert variables["roadmap_completed_count"] == "0"
    assert variables["roadmap_open_count"] == "0"
    assert variables["roadmap_task_count"] == "0"
    assert variables["roadmap_updated"] == ""
    assert variables["roadmap_next_surfaces"] == ""
