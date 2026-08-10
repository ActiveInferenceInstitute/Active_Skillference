"""Tests for the deterministic figures (headless Agg backend)."""

from __future__ import annotations

import inspect
import json
import re
from pathlib import Path
from types import SimpleNamespace

import matplotlib.image as mpimg
import pytest

from src.curriculum.catalog import build_curriculum
from src.curriculum.materials import (
    audit_course_material_index,
    build_course_material_index,
    load_material_sources,
)
from src.figures.plots import (
    FigureRegistryError,
    _skill_name_atlas_payload,
    planned_figure_count,
    plot_active_skillference_cover,
    plot_assessment_depth_matrix,
    plot_curriculum_dag,
    plot_curriculum_stratum_balance,
    plot_dependency_strata_flow,
    plot_efe_decomposition,
    plot_free_energy_descent,
    plot_graph_bottlenecks,
    plot_kernel_sensitivity_profiles,
    plot_open_science_source_map,
    plot_roadmap_risk,
    plot_scholarship_coverage,
    plot_scholarship_source_health,
    plot_scientific_evidence_matrix,
    plot_semantic_prerequisite_coverage,
    plot_skill_name_atlas,
    plot_skill_neighborhood_paths,
    plot_validation_intent_mismatch_matrix,
    plot_validation_surface_matrix,
    plot_vfe_efe_skilltree_bridge,
    plot_visual_evidence_contract_ladder,
    render_all,
    validation_surface_matrix,
)
from src.figures.plots.registry_helpers import (
    _coerce_int,
    _figure_registry_file_count,
    _int_from_mapping,
    _lane_label,
    _require_positive_int,
    _resolve_cover_figure_count,
    _section_label,
)
from src.figures.registry import (
    FigureRegistryError as RegistryFigureError,
)
from src.figures.registry import (
    figure_contract_errors,
    load_figure_registry_rows,
)
from src.figures.table_companions import (
    _source_health_companion,
    _subject_matches_vfe_efe,
    figure_table_companions,
    write_figure_table_companions,
)
from src.kernels.examples import build_claim_registry
from src.manuscript.claim_support import validate_claim_support
from src.roadmap import load_roadmap
from src.scholarship.coverage import validate_scholarship
from src.scholarship.gap_report import validate_scholarship_gaps
from src.scholarship.source_health import validate_source_health

REPO = Path(__file__).resolve().parents[1]
COURSE_SOURCE_PATH = REPO / "data" / "course_material_sources.yaml"


def test_registry_helper_labels_and_integer_coercion() -> None:
    assert _lane_label("short_lane") == "short lane"
    assert _lane_label("long_source_lane") == "long source\nlane"
    assert _section_label("03_results_section.md") == "results section"
    assert _section_label("appendix_notes.md") == "appendix notes"
    assert _int_from_mapping({"count": 4}, "count") == 4
    assert _int_from_mapping("not-a-mapping", "count") == 0
    assert [_coerce_int(value) for value in (True, 3, 2.9, "3")] == [1, 3, 2, 0]
    assert _require_positive_int(2, "count") == 2
    for invalid in (True, 0, -1, 2.0, "2"):
        with pytest.raises(FigureRegistryError, match="positive integer"):
            _require_positive_int(invalid, "count")


def test_figure_registry_file_count_validates_real_png_contract(tmp_path: Path) -> None:
    registry = tmp_path / "figure_registry.json"
    (tmp_path / "one.png").write_bytes(b"png-one")
    (tmp_path / "two.png").write_bytes(b"png-two")
    registry.write_text(
        json.dumps([{"filename": "one.png"}, {"filename": "two.png"}]),
        encoding="utf-8",
    )

    assert _figure_registry_file_count(registry) == 2
    assert (
        _resolve_cover_figure_count({}, figure_count=2, figure_registry_path=registry)
        == 2
    )
    with pytest.raises(FigureRegistryError, match="disagrees"):
        _resolve_cover_figure_count({}, figure_count=3, figure_registry_path=registry)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"filename": "one.png"}, "must be a JSON list"),
        (["row"], "row 1 must be an object"),
        ([{"filename": "one.jpg"}], "filename must be a PNG string"),
        (
            [{"filename": "one.png"}, {"filename": "one.png"}],
            "duplicate figure registry filename",
        ),
        ([{"filename": "missing.png"}], "references missing files"),
    ],
)
def test_figure_registry_file_count_rejects_invalid_contracts(
    tmp_path: Path, payload: object, message: str
) -> None:
    registry = tmp_path / "figure_registry.json"
    (tmp_path / "one.png").write_bytes(b"png")
    registry.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(FigureRegistryError, match=message):
        _figure_registry_file_count(registry)


def test_figure_registry_file_count_rejects_missing_and_invalid_json(
    tmp_path: Path,
) -> None:
    registry = tmp_path / "figure_registry.json"
    with pytest.raises(FigureRegistryError, match="registry is missing"):
        _figure_registry_file_count(registry)
    registry.write_text("not json", encoding="utf-8")
    with pytest.raises(FigureRegistryError, match="not valid JSON"):
        _figure_registry_file_count(registry)


def test_resolve_cover_count_requires_a_governed_positive_source() -> None:
    assert (
        _resolve_cover_figure_count({}, figure_count=3, figure_registry_path=None) == 3
    )
    assert (
        _resolve_cover_figure_count(
            {"figures": 4}, figure_count=None, figure_registry_path=None
        )
        == 4
    )
    with pytest.raises(FigureRegistryError, match="requires project.live_metrics"):
        _resolve_cover_figure_count({}, figure_count=None, figure_registry_path=None)


def _valid_contract_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "data_grain": "One fixture row per rendered figure with explicit source grain.",
        "data_sources": ["Fixture generated inside tests/test_figures.py."],
        "encoding": "Direct labels and marker positions encode fixture completeness.",
        "failure_mode": "Fails if the fixture chart contract omits source-owned metadata.",
        "mobile_read": "On narrow screens the fixture remains readable because all labels are short.",
        "non_color_encoding": "Text labels and marker positions preserve the fixture reading without color.",
        "palette_policy": "single-root preferred with neutral context",
        "palette_roots": ["blue", "gray"],
        "question": "Does the fixture row carry a complete chart contract?",
        "static_read": "The static fixture preserves its labels and validation boundary.",
        "takeaway": "Complete fixture chart metadata passes structural validation.",
    }
    row.update(overrides)
    return row


def _valid_registry_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "label": "fig:fixture",
        "filename": "fixture.png",
        "caption": "Fixture registry caption with enough detail for direct loader validation.",
        "alt_text": "Fixture registry alternative text describing the direct loader validation.",
        "generated_by": "tests.test_figures._valid_registry_row",
        "chart_family": "direct registry fixture",
        "data_source": "Generated figure registry fixture.",
        "subtitle": "Source: direct registry loader fixture.",
        "interpretation_boundary": "Fixture validates registry structure, not learner outcomes.",
        "false_certification_risk": "Rejects malformed registry rows before dashboard use.",
        "accessibility_note": "Metadata carries the fixture reading through text fields.",
        "mobile_note": "The fixture remains readable on narrow screens.",
        "qa_role": "Direct registry loader regression fixture.",
        "visual_grammar": "Fixture labels, neutral context, and direct metadata encode validity.",
        "claim_tokens": [],
    }
    row.update(_valid_contract_row())
    row.update(overrides)
    return row


def _write_registry_payload(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "figure_registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _course_material_payload() -> tuple[dict[str, object], dict[str, object]]:
    graph = build_curriculum()
    registry = build_claim_registry()
    source_payload = load_material_sources(COURSE_SOURCE_PATH)
    index = build_course_material_index(graph, source_payload, registry=registry)
    audit = audit_course_material_index(index, graph).to_dict()
    return index, audit


def _assert_nonblank_png(path) -> None:
    image = mpimg.imread(path)
    assert image.ndim in (2, 3)
    assert image.shape[0] >= 480
    assert image.shape[1] >= 720
    assert float(image.std()) > 0.01


def test_figure_contract_rejects_generic_fallback_text() -> None:
    generic_rows = [
        _valid_contract_row(
            question="What evidence question does fixture make auditable?"
        ),
        _valid_contract_row(
            data_grain="One generated figure-level evidence surface rendered from project artifact records."
        ),
        _valid_contract_row(
            static_read="The static audit summary keeps the source, labels, and boundary visible."
        ),
        _valid_contract_row(
            mobile_read="Open the full-size image when dense labels exceed the dashboard card."
        ),
        _valid_contract_row(
            failure_mode="Prevents polished visuals from certifying stale or unsupported surfaces."
        ),
    ]

    for row in generic_rows:
        assert figure_contract_errors(row, index=1)


def test_load_figure_registry_rows_accepts_valid_rows(tmp_path: Path) -> None:
    path = _write_registry_payload(
        tmp_path,
        [_valid_registry_row(table_companion_id="companion:fixture")],
    )

    rows = load_figure_registry_rows(path)

    assert len(rows) == 1
    assert rows[0].label == "fig:fixture"
    assert rows[0].filename == "fixture.png"
    assert rows[0].palette_roots == ("blue", "gray")
    assert rows[0].table_companion_id == "companion:fixture"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"not": "a list"}, "figure registry must be a JSON list"),
        ([1], "figure registry row 1 must be an object"),
        ([_valid_registry_row(label="fixture")], "label must start with fig:"),
        (
            [_valid_registry_row(filename="nested/fixture.png")],
            "filename must be a local PNG filename",
        ),
        (
            [_valid_registry_row(filename="fixture.svg")],
            "filename must be a local PNG filename",
        ),
        (
            [
                _valid_registry_row(label="fig:duplicate", filename="one.png"),
                _valid_registry_row(label="fig:duplicate", filename="two.png"),
            ],
            "duplicate figure label",
        ),
        (
            [
                _valid_registry_row(label="fig:one", filename="duplicate.png"),
                _valid_registry_row(label="fig:two", filename="duplicate.png"),
            ],
            "duplicate figure filename",
        ),
    ],
)
def test_load_figure_registry_rows_rejects_malformed_rows(
    tmp_path: Path, payload: object, message: str
) -> None:
    path = _write_registry_payload(tmp_path, payload)

    with pytest.raises(RegistryFigureError, match=message):
        load_figure_registry_rows(path)


def test_curriculum_dag_figure_written(tmp_path) -> None:
    graph = build_curriculum()
    path = plot_curriculum_dag(graph, tmp_path / "dag.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_figure_table_companions_cover_dense_figure_labels() -> None:
    graph = build_curriculum()
    scholarship = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    claim_support = validate_claim_support(
        manuscript_dir=REPO / "manuscript",
        support_path=REPO / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=REPO / "data" / "scholarship_sources.yaml",
        bib_path=REPO / "manuscript" / "references.bib",
        registry_claim_ids=build_claim_registry().names(),
        project_root=REPO,
    )
    source_health = validate_source_health(
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    gap_report = validate_scholarship_gaps(
        scholarship,
        claim_support,
        REPO / "manuscript" / "references.bib",
    )

    payload = figure_table_companions(
        graph=graph,
        source_health=source_health,
        gap_report=gap_report,
    )

    assert set(payload["figures"]) == {
        "fig:graph_bottlenecks",
        "fig:vfe_efe_skilltree_bridge",
        "fig:scholarship_source_health",
    }
    assert payload["summary"]["rows"] > 0
    for companion in payload["figures"].values():
        assert companion["companionId"].startswith("companion:")
        assert companion["columns"]
        assert companion["rows"]


def test_figure_table_companion_helpers_cover_fallbacks(tmp_path: Path) -> None:
    assert _subject_matches_vfe_efe("Expected-free-energy bridge", "")
    assert _subject_matches_vfe_efe("route handoff", "variational free energy")
    assert not _subject_matches_vfe_efe("plain route handoff", "dashboard shell")

    issue = SimpleNamespace(
        code="missing_locator",
        key="fixture_source",
        message="fixture source missing locator",
    )
    issue_payload = _source_health_companion(
        SimpleNamespace(issue_list=[issue], source_count=1, checked_online=True),
        SimpleNamespace(to_dict=lambda: {"summary": {"frontierSources": 2}}),
    )
    assert issue_payload["rows"] == [
        {
            "code": "missing_locator",
            "key": "fixture_source",
            "message": "fixture source missing locator",
            "status": "review",
        }
    ]

    pass_payload = _source_health_companion(
        SimpleNamespace(issue_list=[], source_count=121, checked_online=False),
        SimpleNamespace(to_dict=lambda: {"summary": "not a mapping"}),
    )
    assert pass_payload["rows"][0]["status"] == "pass"
    assert "frontier sources=0" in pass_payload["rows"][0]["message"]

    out = write_figure_table_companions(
        {"figures": {}, "summary": {"rows": 0}},
        tmp_path / "figure_table_companions.json",
    )
    assert json.loads(out.read_text(encoding="utf-8"))["summary"]["rows"] == 0


def test_free_energy_figure_written(tmp_path) -> None:
    reg = build_claim_registry()
    path = plot_free_energy_descent(reg, tmp_path / "fe.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_dependency_strata_flow_figure_written(tmp_path) -> None:
    graph = build_curriculum()
    path = plot_dependency_strata_flow(graph, tmp_path / "flow.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_assessment_depth_matrix_figure_written(tmp_path) -> None:
    graph = build_curriculum()
    path = plot_assessment_depth_matrix(graph, tmp_path / "assessment.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_curriculum_stratum_balance_figure_written(tmp_path) -> None:
    graph = build_curriculum()
    path = plot_curriculum_stratum_balance(graph, tmp_path / "balance.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_active_skillference_cover_written_without_registry_entry(tmp_path) -> None:
    graph = build_curriculum()
    reg = build_claim_registry()
    roadmap = load_roadmap(REPO / "tasks.yaml")
    cover = plot_active_skillference_cover(
        graph,
        reg,
        roadmap,
        tmp_path / "active_skillference_cover.png",
    )
    _assert_nonblank_png(cover)
    image = mpimg.imread(cover)
    aspect_ratio = image.shape[1] / image.shape[0]
    assert 0.95 <= aspect_ratio <= 1.05
    assert image.shape[0] >= 2800
    assert image.shape[1] >= 2800

    render_all(
        graph,
        reg,
        tmp_path,
        scholarship_audit=validate_scholarship(
            REPO / "manuscript",
            REPO / "data" / "scholarship_sources.yaml",
            REPO / "manuscript" / "references.bib",
        ).to_dict(),
        source_health_audit=validate_source_health(
            REPO / "data" / "scholarship_sources.yaml",
            REPO / "manuscript" / "references.bib",
        ).to_dict(),
        roadmap=roadmap,
    )
    registry = json.loads((tmp_path / "figure_registry.json").read_text())
    assert "active_skillference_cover.png" not in {
        entry["filename"] for entry in registry
    }


def test_active_skillference_cover_rejects_missing_figure_count(tmp_path) -> None:
    graph = build_curriculum()
    reg = build_claim_registry()
    with pytest.raises(FigureRegistryError, match="live_metrics.figures"):
        plot_active_skillference_cover(
            graph,
            reg,
            {"project": {"live_metrics": {}}},
            tmp_path / "active_skillference_cover.png",
        )


def test_skill_name_atlas_written_without_registry_entry(tmp_path) -> None:
    graph = build_curriculum()
    atlas = plot_skill_name_atlas(
        graph,
        tmp_path / "active_skillference_skill_atlas.png",
    )
    _assert_nonblank_png(atlas)
    image = mpimg.imread(atlas)
    aspect_ratio = image.shape[1] / image.shape[0]
    assert 1.85 <= aspect_ratio <= 2.05

    payload = _skill_name_atlas_payload(graph)
    assert payload["skillCount"] == len(graph.skills)
    assert payload["subjectCount"] == len(graph.subjects)
    assert payload["stratumCount"] == 8
    assert payload["tokenCount"] > 100
    assert payload["topTerms"]

    reg = build_claim_registry()
    roadmap = load_roadmap(REPO / "tasks.yaml")
    render_all(
        graph,
        reg,
        tmp_path,
        scholarship_audit=validate_scholarship(
            REPO / "manuscript",
            REPO / "data" / "scholarship_sources.yaml",
            REPO / "manuscript" / "references.bib",
        ).to_dict(),
        source_health_audit=validate_source_health(
            REPO / "data" / "scholarship_sources.yaml",
            REPO / "manuscript" / "references.bib",
        ).to_dict(),
        roadmap=roadmap,
    )
    registry = json.loads((tmp_path / "figure_registry.json").read_text())
    assert "active_skillference_skill_atlas.png" not in {
        entry["filename"] for entry in registry
    }


def test_efe_figure_written(tmp_path) -> None:
    reg = build_claim_registry()
    path = plot_efe_decomposition(reg, tmp_path / "efe.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_kernel_sensitivity_profiles_figure_written(tmp_path) -> None:
    reg = build_claim_registry()
    path = plot_kernel_sensitivity_profiles(reg, tmp_path / "sensitivity.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_vfe_efe_skilltree_bridge_figure_written(tmp_path) -> None:
    graph = build_curriculum()
    path = plot_vfe_efe_skilltree_bridge(graph, tmp_path / "bridge.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_scholarship_coverage_figure_written(tmp_path) -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    path = plot_scholarship_coverage(audit.to_dict(), tmp_path / "scholarship.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_open_science_source_map_figure_written(tmp_path) -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    material_index, material_audit = _course_material_payload()
    path = plot_open_science_source_map(
        audit.to_dict(),
        tmp_path / "open-science.png",
        course_material_index=material_index,
        course_material_audit=material_audit,
    )
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)
    assert material_index["coverage"]["sourcePointerCounts"]["aii_cognitive_kb"] > 0


def test_graph_diagnostic_figures_written(tmp_path) -> None:
    graph = build_curriculum()
    bottlenecks = plot_graph_bottlenecks(graph, tmp_path / "bottlenecks.png")
    paths = plot_skill_neighborhood_paths(graph, tmp_path / "paths.png")

    _assert_nonblank_png(bottlenecks)
    _assert_nonblank_png(paths)


def test_scholarship_source_health_figure_written(tmp_path) -> None:
    audit = validate_source_health(
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    path = plot_scholarship_source_health(audit.to_dict(), tmp_path / "health.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_roadmap_risk_figure_written(tmp_path) -> None:
    roadmap = load_roadmap(REPO / "tasks.yaml")
    path = plot_roadmap_risk(roadmap, tmp_path / "roadmap.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_validation_surface_matrix_figure_written(tmp_path) -> None:
    graph = build_curriculum()
    reg = build_claim_registry()
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    path = plot_validation_surface_matrix(
        graph,
        reg,
        audit.to_dict(),
        tmp_path / "validation.png",
        figure_count=8,
    )
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_validation_intent_mismatch_matrix_figure_written(tmp_path) -> None:
    path = plot_validation_intent_mismatch_matrix(
        tmp_path / "validation-intent.png",
        figure_count=planned_figure_count(
            include_scholarship=True,
            include_claim_support=True,
            include_roadmap=True,
        ),
        include_scholarship=True,
        include_claim_support=True,
        include_roadmap=True,
    )
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_visual_evidence_contract_ladder_written(tmp_path) -> None:
    graph = build_curriculum()
    path = plot_visual_evidence_contract_ladder(graph, tmp_path / "contract.png")
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_semantic_prerequisite_figure_uses_public_quality_api() -> None:
    source = inspect.getsource(plot_semantic_prerequisite_coverage)
    assert "_CONCEPT_PREREQUISITES" not in source
    assert "_audit_semantic_prerequisites" not in source
    assert "_transitive_prerequisites" not in source


def _plots_package_source() -> str:
    plots_dir = REPO / "src" / "figures" / "plots"
    parts = [
        path.read_text(encoding="utf-8") for path in sorted(plots_dir.glob("*.py"))
    ]
    return "\n".join(parts)


def test_figure_typography_rejects_subminimum_hard_coded_font_sizes() -> None:
    source = _plots_package_source()
    # Scan BOTH fontsize= and labelsize=/set_size= numeric literals: a sub-floor tick
    # labelsize is just as illegible as a sub-floor fontsize, and the gate must see it.
    sizes = [
        float(match)
        for match in re.findall(
            r"(?:fontsize|labelsize)\s*=\s*([0-9]+(?:\.[0-9]+)?)", source
        )
    ]

    assert sizes
    assert min(sizes) >= 9.5
    assert "_FONT_SMALL = 9.5" in source
    assert "_FONT_NOTE = 8.5" in source
    assert "_MIN_FIGURE_FONT_SIZE = 9.5" in source
    assert source.count("fontsize=_FONT_NOTE") == 1


def test_figure_text_does_not_hardcode_a_stale_assessment_floor() -> None:
    """The figure caption/panel layer must bind to the enforced assessment floor.

    The manuscript-variable linter only scans manuscript/*.md, so a stale floor in a
    Python figure string (e.g. "three-question floor" while the enforced floor is 4)
    would bypass every other gate and contradict the manuscript. Bind the figure layer
    to MIN_ASSESSMENTS_PER_SKILL and reject the old hard-coded floor phrases.
    """
    from src.curriculum.quality import MIN_ASSESSMENTS_PER_SKILL

    source = _plots_package_source()
    stale_phrases = [
        "three-question floor",
        "three failable",
        "three questions per skill",
        "at least three questions",
    ]
    for phrase in stale_phrases:
        assert phrase not in source, (
            f"stale assessment-floor phrase in plots package: {phrase!r}"
        )
    # The figure layer references the enforced constant rather than a literal count.
    assert "MIN_ASSESSMENTS_PER_SKILL" in source
    assert MIN_ASSESSMENTS_PER_SKILL >= 4


def test_scientific_evidence_matrix_figure_written(tmp_path) -> None:
    audit = validate_claim_support(
        manuscript_dir=REPO / "manuscript",
        support_path=REPO / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=REPO / "data" / "scholarship_sources.yaml",
        bib_path=REPO / "manuscript" / "references.bib",
    )
    path = plot_scientific_evidence_matrix(
        audit.to_dict(),
        tmp_path / "evidence.png",
    )
    assert path.exists() and path.stat().st_size > 0
    _assert_nonblank_png(path)


def test_render_all_emits_registered_figures(tmp_path) -> None:
    graph = build_curriculum()
    reg = build_claim_registry()
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    health = validate_source_health(
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    claim_support = validate_claim_support(
        manuscript_dir=REPO / "manuscript",
        support_path=REPO / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=REPO / "data" / "scholarship_sources.yaml",
        bib_path=REPO / "manuscript" / "references.bib",
    )
    roadmap = load_roadmap(REPO / "tasks.yaml")
    material_index, material_audit = _course_material_payload()
    paths = render_all(
        graph,
        reg,
        tmp_path,
        scholarship_audit=audit.to_dict(),
        source_health_audit=health.to_dict(),
        claim_support_audit=claim_support.to_dict(),
        course_material_index=material_index,
        course_material_audit=material_audit,
        roadmap=roadmap,
    )
    assert len(paths) == 21
    assert all(p.exists() and p.stat().st_size > 0 for p in paths)
    aspect_ranges = {
        "planning_lookahead.png": (2.3, 2.5),
        "predictive_coding_descent.png": (2.4, 2.6),
        "assessment_depth_matrix.png": (1.6, 1.78),
        "curriculum_dag.png": (1.45, 1.65),
        "curriculum_stratum_balance.png": (1.9, 2.08),
        "dependency_strata_flow.png": (1.5, 1.7),
        "efe_decomposition.png": (2.15, 2.45),
        "free_energy_descent.png": (1.5, 1.7),
        "graph_bottlenecks.png": (1.4, 1.6),
        "kernel_sensitivity_profiles.png": (2.75, 3.05),
        "open_science_source_map.png": (1.75, 2.0),
        "roadmap_risk.png": (1.95, 2.2),
        "scholarship_coverage.png": (1.9, 2.15),
        "scholarship_source_health.png": (1.45, 1.7),
        "scientific_evidence_matrix.png": (1.75, 1.95),
        "semantic_prerequisite_coverage.png": (1.75, 1.95),
        "skill_neighborhood_paths.png": (2.05, 2.3),
        "validation_intent_mismatch_matrix.png": (1.85, 2.1),
        "validation_surface_matrix.png": (1.8, 2.05),
        "visual_evidence_contract_ladder.png": (2.1, 2.35),
        "vfe_efe_skilltree_bridge.png": (1.75, 2.0),
    }
    for figure_path in paths:
        image = mpimg.imread(figure_path)
        aspect = image.shape[1] / image.shape[0]
        low, high = aspect_ranges[figure_path.name]
        assert low <= aspect <= high, figure_path.name
    registry = json.loads((tmp_path / "figure_registry.json").read_text())
    # The written registry also carries captured browser evidence, which
    # render_all does not produce; compare against the rendered subset.
    rendered = [
        entry
        for entry in registry
        if entry.get("evidence_kind", "rendered") != "captured"
    ]
    assert {entry["label"] for entry in rendered} == {
        "fig:curriculum_dag",
        "fig:dependency_strata_flow",
        "fig:assessment_depth",
        "fig:stratum_balance",
        "fig:free_energy",
        "fig:efe",
        "fig:planning_lookahead",
        "fig:predictive_coding",
        "fig:kernel_sensitivity_profiles",
        "fig:vfe_efe_skilltree_bridge",
        "fig:graph_bottlenecks",
        "fig:skill_neighborhood_paths",
        "fig:semantic_prerequisite_coverage",
        "fig:validation_intent_mismatch_matrix",
        "fig:scholarship_coverage",
        "fig:open_science_sources",
        "fig:scholarship_source_health",
        "fig:validation_surface_matrix",
        "fig:visual_evidence_contract_ladder",
        "fig:scientific_evidence_matrix",
        "fig:roadmap_risk",
    }
    assert all(entry["alt_text"] for entry in registry)
    assert all(entry["chart_family"] for entry in registry)
    assert all(entry["data_grain"] for entry in registry)
    assert all(entry["data_source"] for entry in registry)
    assert all(entry["data_sources"] for entry in registry)
    assert all(entry["encoding"] for entry in registry)
    assert all(entry["failure_mode"] for entry in registry)
    assert all(entry["interpretation_boundary"] for entry in registry)
    assert all(entry["mobile_note"] for entry in registry)
    assert all(entry["mobile_read"] for entry in registry)
    assert all(entry["non_color_encoding"] for entry in registry)
    assert all(entry["palette_policy"] for entry in registry)
    assert all(entry["palette_roots"] for entry in registry)
    assert all(entry["question"] for entry in registry)
    assert all(entry["qa_role"] for entry in registry)
    assert all(entry["static_read"] for entry in registry)
    assert all(entry["subtitle"] for entry in registry)
    assert all(entry["visual_grammar"] for entry in registry)
    assert len({entry["visual_grammar"] for entry in registry}) == len(registry)
    by_label = {entry["label"]: entry for entry in registry}
    assert (
        by_label["fig:stratum_balance"]["filename"] == "curriculum_stratum_balance.png"
    )
    assert "Stratum-balance" in by_label["fig:stratum_balance"]["caption"]
    assert "assessment questions" in by_label["fig:stratum_balance"]["alt_text"]
    assert by_label["fig:free_energy"]["filename"] == "free_energy_descent.png"
    assert "Supplemental noisy-sensor" in by_label["fig:free_energy"]["caption"]
    assert "negative log-evidence" in by_label["fig:free_energy"]["alt_text"]
    assert by_label["fig:efe"]["filename"] == "efe_decomposition.png"
    assert "precision-regime switch" in by_label["fig:efe"]["caption"]
    assert "sample and commit task" in by_label["fig:efe"]["alt_text"]
    assert by_label["fig:free_energy"]["claim_tokens"]
    assert by_label["fig:efe"]["claim_tokens"]
    assert by_label["fig:kernel_sensitivity_profiles"]["claim_tokens"]
    assert (
        by_label["fig:vfe_efe_skilltree_bridge"]["filename"]
        == "vfe_efe_skilltree_bridge.png"
    )
    assert "SkillTree bridge" in by_label["fig:vfe_efe_skilltree_bridge"]["caption"]
    dag = by_label["fig:curriculum_dag"]
    assert "direct stratum labels" in dag["encoding"]
    assert dag["chart_family"] == "lane node-link DAG"
    flow = by_label["fig:dependency_strata_flow"]
    assert flow["filename"] == "dependency_strata_flow.png"
    # The lower-triangle backward-dependency safety marking must be described in
    # caption, alt-text, and the validator-facing encoding metadata so the
    # no-backward-edges invariant is documented, not just drawn.
    assert "lower triangle" in flow["caption"]
    assert "backward-dependency" in flow["caption"]
    assert "backward-dependency safety zone" in flow["alt_text"]
    assert "must stay empty" in flow["encoding"]
    assert "row and column totals" in flow["encoding"]
    assert flow["chart_family"] == "matrix heatmap with totals"
    assessment = by_label["fig:assessment_depth"]
    # The caption must report the ENFORCED floor (MIN_ASSESSMENTS_PER_SKILL=4), not the
    # old hand-typed "three" — the figure layer is bound to the constant.
    from src.curriculum.quality import MIN_ASSESSMENTS_PER_SKILL

    assert f"{MIN_ASSESSMENTS_PER_SKILL}-question floor" in assessment["caption"]
    assert "floor-pass audit table/bar hybrid" in assessment["encoding"]
    efe = by_label["fig:efe"]
    assert "precision-regime switch" in efe["caption"]
    assert "regime" in efe["qa_role"]
    balance = by_label["fig:stratum_balance"]
    assert "normalized companion dots" in balance["encoding"]
    validation = by_label["fig:validation_surface_matrix"]
    assert "bound versus n/a" in validation["encoding"]
    assert "validator-test binding row" in validation["data_grain"]
    assert "Cell text" in validation["non_color_encoding"]
    roadmap = by_label["fig:roadmap_risk"]
    assert "remaining work grouped by surface" in roadmap["alt_text"]
    assert (
        "stacked bars encode remaining work by surface and release class"
        in roadmap["encoding"]
    )
    assert "EXT/GIT segment codes" in roadmap["non_color_encoding"]
    assert roadmap["chart_family"] == "roadmap status and blocker-surface bars"
    assert "tasks.yaml task records" in roadmap["data_grain"]
    bottlenecks = by_label["fig:graph_bottlenecks"]
    assert "skill id/name row" in bottlenecks["data_grain"]
    assert "Rank order and direct labels" in bottlenecks["non_color_encoding"]
    open_science = by_label["fig:open_science_sources"]
    assert "course-material pointers" in open_science["caption"]
    assert "cognitive knowledge-base" in open_science["caption"]
    assert "KB pointers" in open_science["alt_text"]
    assert "course-material source row" in open_science["data_grain"]
    assert "pinned course-material links" in open_science["failure_mode"]
    intent = by_label["fig:validation_intent_mismatch_matrix"]
    assert intent["filename"] == "validation_intent_mismatch_matrix.png"
    assert "false-certification classes" in intent["caption"]
    assert intent["chart_family"] == "mismatch-class coverage matrix"
    ladder = by_label["fig:visual_evidence_contract_ladder"]
    assert ladder["filename"] == "visual_evidence_contract_ladder.png"
    assert ladder["chart_family"] == "annotated contract ladder"
    assert "question to negative-control" in ladder["question"]
    assert "six stages" in ladder["static_read"]
    assert "decorative reporting layer" in ladder["takeaway"]
    bridge = by_label["fig:vfe_efe_skilltree_bridge"]
    assert "learn routes and quiz routes" in bridge["encoding"]


def test_validation_surface_matrix_is_derived_from_validator_files(
    tmp_path: Path,
) -> None:
    """The matrix must reflect real validator/test files, not a hand-coded literal.

    A bound cell must flip to n/a when its backing file is absent, so the figure cannot
    certify a gate that does not exist.
    """
    rows, columns, matrix = validation_surface_matrix()
    assert matrix.shape == (len(rows), len(columns))
    assert "Export integrity" in rows
    assert "Material link safety" in rows
    # With the real repo root every backing file exists, so some cells are bound.
    assert matrix.sum() > 0

    # Against an empty root no validator files exist -> every cell is n/a (0).
    _, _, empty = validation_surface_matrix(tmp_path)
    assert empty.sum() == 0
