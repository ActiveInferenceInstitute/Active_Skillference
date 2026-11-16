"""PDF provenance receipts use finalized bytes and a real source revision."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess

import pytest

from scripts import render_manuscript as renderer
from src.manuscript.pdf_receipt import capture_pdf_inputs, pdf_receipt_issues


def test_pdf_receipt_records_finalized_output_and_actual_inputs(pdf_project) -> None:
    target, root = pdf_project["target"], pdf_project["root"]
    receipt = target.with_suffix(".receipt.json")
    receipt.write_text("outdated receipt", encoding="utf-8")

    assert renderer._write_pdf_receipt(target, root=root, inputs=pdf_project["inputs"]) == receipt

    content = target.read_bytes()
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["schema"] == "active-skillference-pdf/v2"
    assert payload["output_path"] == f"output/pdf/{renderer.PDF_NAME}"
    assert payload["size_bytes"] == len(content)
    assert payload["sha256"] == hashlib.sha256(content).hexdigest()
    assert payload["source_revision"] == pdf_project["revision"]
    expected = {
        "manuscript/config.yaml", "manuscript/preamble.md", "manuscript/references.bib",
        "output/manuscript/01_fixture.md", "output/manuscript/assets/cover.pdf",
        "output/manuscript/assets/atlas.pdf", "output/manuscript/assets/body.pdf",
    }
    rows = payload["inputManifest"]["files"]
    assert {row["path"] for row in rows} == expected
    for row in rows:
        actual = (root / row["path"]).read_bytes()
        assert row["size_bytes"] == len(actual)
        assert row["sha256"] == hashlib.sha256(actual).hexdigest()
    assert pdf_receipt_issues(root) == []


@pytest.mark.slow
def test_real_render_places_configured_atlas_on_physical_page_two(pdf_project, monkeypatch) -> None:
    required = ("pandoc", "pandoc-crossref", "xelatex", "bibtex", "pdftotext")
    missing = [tool for tool in required if shutil.which(tool) is None]
    if missing:
        pytest.skip("existing render tools unavailable: " + ", ".join(missing))
    root = pdf_project["root"]
    monkeypatch.setattr(renderer, "ROOT", root)
    monkeypatch.setattr(renderer, "MANUSCRIPT", root / "manuscript")
    monkeypatch.setattr(renderer, "OUTPUT_MANUSCRIPT", root / "output" / "manuscript")
    monkeypatch.setattr(renderer, "OUTPUT_PDF", root / "output" / "pdf")
    scratch = root / "build"
    scratch.mkdir()
    inputs = capture_pdf_inputs(root, [pdf_project["section"]])

    target = renderer._render_pdf(scratch, renderer._config(), inputs=inputs)

    extracted = subprocess.run(
        ["pdftotext", "-layout", str(target), "-"],
        check=True, capture_output=True, text=True,
    ).stdout.split("\f")
    assert "FixtureTitlePage" in extracted[0]
    assert "FixtureAtlasPage" in extracted[1]
    assert "FixtureAtlasCaption" in extracted[1]
    assert "AtlasGraphic" in extracted[1]
    assert "FixtureBodySection" not in extracted[1]
    assert "FixtureBodySection" in "\f".join(extracted[2:])
    receipt = json.loads(target.with_suffix(".receipt.json").read_text(encoding="utf-8"))
    assert set(receipt["inputManifest"]["assets"]) == {
        path.relative_to(root).as_posix() for path in pdf_project["assets"]
    }
    assert pdf_receipt_issues(root) == []
