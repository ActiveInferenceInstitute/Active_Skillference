"""Negative control for the rendered-manuscript freshness gate (C1)."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import validate_rendered_freshness as freshness
import z_generate_manuscript_variables as zg

# Rehydrates the manuscript and rebuilds the live graph; `./gates.sh fast` deselects it.
pytestmark = pytest.mark.slow


def _setup(tmp_path: Path, monkeypatch) -> Path:
    manuscript = tmp_path / "manuscript"
    output = tmp_path / "output" / "manuscript"
    manuscript.mkdir(parents=True)
    output.mkdir(parents=True)
    (manuscript / "00_counts.md").write_text(
        "The curriculum has {{skill_count}} skills.", encoding="utf-8"
    )
    monkeypatch.setattr(zg, "MANUSCRIPT", manuscript)
    monkeypatch.setattr(zg, "OUTPUT_MANUSCRIPT", output)
    monkeypatch.setattr(zg, "_variables", lambda: {"skill_count": "600"})
    return output


def test_freshness_passes_when_render_matches(tmp_path, monkeypatch) -> None:
    output = _setup(tmp_path, monkeypatch)
    (output / "00_counts.md").write_text(
        "The curriculum has 600 skills.", encoding="utf-8"
    )
    assert freshness.check_rendered_freshness() == []


def test_freshness_detects_stale_render(tmp_path, monkeypatch) -> None:
    output = _setup(tmp_path, monkeypatch)
    # A stale rendered copy with the old count must be flagged.
    (output / "00_counts.md").write_text(
        "The curriculum has 536 skills.", encoding="utf-8"
    )
    stale = freshness.check_rendered_freshness()
    assert stale and "00_counts.md" in stale[0]


def test_freshness_detects_missing_render(tmp_path, monkeypatch) -> None:
    _setup(tmp_path, monkeypatch)  # no rendered file written
    stale = freshness.check_rendered_freshness()
    assert stale and "no rendered output" in stale[0]


def test_artifact_count_drift_against_live_graph_is_detected(monkeypatch) -> None:
    # Critical: a stale manuscript_variables.json must not pass as fresh. The check
    # re-derives counts from the live curriculum graph, so a wrong committed count fails.
    from src.curriculum.catalog import build_curriculum

    graph = build_curriculum()
    stats = graph.stats()
    good = {
        "skill_count": str(stats["skills"]),
        "subject_count": str(stats["subjects"]),
        "edge_count": str(stats["prerequisite_edges"]),
        "max_depth": str(stats["max_depth"]),
        "core_max_depth": str(stats["core_max_depth"]),
        "quiz_count": str(
            sum(1 for s in graph.skills if s.self_reporting_type == "Quiz")
        ),
        "assessment_count": str(sum(len(s.assessments) for s in graph.skills)),
    }
    monkeypatch.setattr(freshness.zg, "_variables", lambda: good)
    assert freshness.check_artifact_counts_match_graph() == []

    drifted = dict(good)
    drifted["skill_count"] = str(int(good["skill_count"]) - 1)
    monkeypatch.setattr(freshness.zg, "_variables", lambda: drifted)
    drift = freshness.check_artifact_counts_match_graph()
    assert drift and "skill_count" in drift[0]


def test_publication_bundle_freshness_detects_stale_roadmap_text(
    tmp_path: Path,
) -> None:
    conclusion = tmp_path / "output" / "manuscript" / "04_conclusion.md"
    stale_page = tmp_path / "output" / "web" / "index.html"
    conclusion.parent.mkdir(parents=True)
    stale_page.parent.mkdir(parents=True)
    conclusion.write_text(
        "The current roadmap has 9 open items across metadata, skilltree, validation.",
        encoding="utf-8",
    )
    stale_page.write_text(
        "<p>The current roadmap has 1 open items across metadata.</p>",
        encoding="utf-8",
    )

    issues = freshness.check_publication_bundle_roadmap_freshness(tmp_path)

    assert issues
    assert "output/web/index.html" in issues[0]
    assert "expected 9 open items" in issues[0]


def test_publication_bundle_freshness_accepts_docx_zip_text(
    tmp_path: Path,
) -> None:
    conclusion = tmp_path / "output" / "manuscript" / "04_conclusion.md"
    docx = tmp_path / "output" / "docx" / "paper.docx"
    conclusion.parent.mkdir(parents=True)
    docx.parent.mkdir(parents=True)
    conclusion.write_text(
        "The current roadmap has 4 open items across metadata, skilltree, validation.",
        encoding="utf-8",
    )
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<w:document><w:t>4 open items across metadata, skilltree, "
            "validation.</w:t></w:document>",
        )

    assert freshness.check_publication_bundle_roadmap_freshness(tmp_path) == []
