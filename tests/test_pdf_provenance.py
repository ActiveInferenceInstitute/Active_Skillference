"""Receipt/freshness contracts use disposable real files, never historical outputs."""

from __future__ import annotations

from copy import deepcopy

import pytest

from src.manuscript.pdf_receipt import (
    PdfReceiptError,
    add_pdf_assets,
    capture_pdf_inputs,
    latex_asset_paths,
    pdf_receipt_issues,
    validate_pdf_inputs,
    write_pdf_receipt,
)


def _receipt(project):
    return write_pdf_receipt(
        project["target"],
        root=project["root"],
        source_revision=project["revision"],
        inputs=project["inputs"],
    )


@pytest.mark.parametrize(
    "relative",
    [
        "manuscript/config.yaml",
        "manuscript/preamble.md",
        "manuscript/references.bib",
        "output/manuscript/01_fixture.md",
        "output/manuscript/assets/cover.pdf",
        "output/manuscript/assets/atlas.pdf",
        "output/manuscript/assets/body.pdf",
    ],
)
def test_changed_actual_input_invalidates_unchanged_pdf_and_cannot_refresh_receipt(
    pdf_project, relative: str
) -> None:
    receipt = _receipt(pdf_project)
    old_receipt, old_pdf = receipt.read_bytes(), pdf_project["target"].read_bytes()
    path = pdf_project["root"] / relative
    path.write_bytes(path.read_bytes() + b"\nchanged input\n")

    assert pdf_receipt_issues(pdf_project["root"])
    with pytest.raises(PdfReceiptError, match="changed"):
        _receipt(pdf_project)
    assert receipt.read_bytes() == old_receipt
    assert pdf_project["target"].read_bytes() == old_pdf


@pytest.mark.parametrize(
    "change",
    ["add-section", "delete-section", "delete-image", "replace-pdf", "delete-pdf"],
)
def test_changed_input_set_or_final_pdf_is_not_fresh(
    pdf_project, pdf_bytes, change: str
) -> None:
    receipt = _receipt(pdf_project)
    old_receipt = receipt.read_bytes()
    if change == "add-section":
        (pdf_project["section"].parent / "02_added.md").write_text("# Added section\n")
    elif change == "delete-section":
        pdf_project["section"].unlink()
    elif change == "delete-image":
        pdf_project["assets"][1].unlink()
    elif change == "replace-pdf":
        pdf_project["target"].write_bytes(pdf_bytes("Different finalized PDF"))
    else:
        pdf_project["target"].unlink()
    assert pdf_receipt_issues(pdf_project["root"])
    assert receipt.read_bytes() == old_receipt


@pytest.mark.parametrize(
    "raw",
    [
        b"not JSON",
        b"[]",
        b'{"schema":"active-skillference-pdf/v1"}',
        b'{"schema":"active-skillference-pdf/v2"}',
    ],
)
def test_legacy_or_incomplete_receipt_requires_real_rerender_without_relabeling(
    pdf_project, raw: bytes
) -> None:
    receipt = pdf_project["target"].with_suffix(".receipt.json")
    receipt.write_bytes(raw)
    assert pdf_receipt_issues(pdf_project["root"])
    assert receipt.read_bytes() == raw


def test_missing_receipt_is_not_created_by_read_only_freshness_audit(
    pdf_project,
) -> None:
    receipt = pdf_project["target"].with_suffix(".receipt.json")
    assert pdf_receipt_issues(pdf_project["root"])
    assert not receipt.exists()


@pytest.mark.parametrize(
    "damage",
    [
        "missing-primary",
        "missing-section",
        "missing-image",
        "duplicate-path",
        "unsafe-path",
        "bad-digest",
        "missing-assets-list",
    ],
)
def test_incomplete_or_unsafe_input_manifest_is_rejected(
    pdf_project, damage: str
) -> None:
    manifest = deepcopy(pdf_project["inputs"])
    rows = manifest["files"]
    if damage.startswith("missing-") and damage != "missing-assets-list":
        kind = {
            "missing-primary": "config",
            "missing-section": "section",
            "missing-image": "asset",
        }[damage]
        rows.remove(next(row for row in rows if row["kind"] == kind))
    elif damage == "duplicate-path":
        rows.append(dict(rows[0]))
    elif damage == "unsafe-path":
        rows[0]["path"] = "../outside"
    elif damage == "bad-digest":
        rows[0]["sha256"] = "not-a-content-digest"
    else:
        manifest.pop("assets")
    with pytest.raises(PdfReceiptError):
        validate_pdf_inputs(pdf_project["root"], manifest)


def test_actual_latex_image_inputs_are_deduplicated_and_comments_do_not_create_inputs(
    pdf_project,
) -> None:
    root = pdf_project["root"]
    tex = root / "build.tex"
    cover, _atlas, body = pdf_project["assets"]
    tex.write_text(
        "% \\includegraphics{missing-commented.pdf}\n"
        f"\\includegraphics*[width=.5\\linewidth]{{{cover.as_posix()}}}\n"
        f"\\includegraphics{{{cover.as_posix()}}}\n\\includegraphics{{{body.as_posix()}}}\n"
    )
    paths = latex_asset_paths(tex, build_directory=root, root=root)
    assert paths == sorted([cover.resolve(), body.resolve()])
    manifest = add_pdf_assets(
        root, capture_pdf_inputs(root, [pdf_project["section"]]), paths
    )
    assert set(manifest["assets"]) == {
        path.relative_to(root).as_posix() for path in (cover, body)
    }


def test_nonliteral_latex_image_input_cannot_create_incomplete_provenance(
    pdf_project,
) -> None:
    root = pdf_project["root"]
    tex = root / "build.tex"
    tex.write_text(r"\includegraphics{\chosenImage{}}")
    with pytest.raises(PdfReceiptError, match="non-literal"):
        latex_asset_paths(tex, build_directory=root, root=root)


def test_unrelated_repository_file_does_not_invalidate_actual_input_snapshot(
    pdf_project,
) -> None:
    _receipt(pdf_project)
    (pdf_project["root"] / "unrelated.txt").write_text("Not a PDF compiler input.")
    assert pdf_receipt_issues(pdf_project["root"]) == []
