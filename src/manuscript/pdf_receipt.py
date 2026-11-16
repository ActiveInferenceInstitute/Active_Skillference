"""Content-bound PDF receipts for repository inputs, not release authorization.

Primary inputs are captured before assembly; actual LaTeX image inputs are added
before compilation. Every bound file and the section set must still match before
publication. Historical receipts are never rewritten by validation.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact

SECTION_EXCLUDE = frozenset(
    {"config.yaml", "preamble.md", "README.md", "AGENTS.md", "SYNTAX.md"}
)
PDF_NAME = "Active_Skillference_combined.pdf"
_PRIMARY_INPUTS = {
    "manuscript/config.yaml": "config",
    "manuscript/preamble.md": "preamble",
    "manuscript/references.bib": "bibliography",
}
_IMAGE_RE = re.compile(r"\\includegraphics\*?(?:\[[^\]]*\])?\{([^{}]+)\}")


class PdfReceiptError(ValueError):
    """A PDF or its actual repository inputs are missing, changed or unverifiable."""


def hydrated_section_files(directory: Path) -> list[Path]:
    return [
        path
        for path in sorted(directory.glob("*.md"))
        if path.name not in SECTION_EXCLUDE
    ]


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise PdfReceiptError(
            "PDF inputs/output must remain inside the project root"
        ) from exc


def _record(path: Path, root: Path, kind: str) -> dict[str, Any]:
    relative = _relative(path, root)
    try:
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        size = path.stat().st_size
    except OSError as exc:
        raise PdfReceiptError(f"PDF {kind} file is unreadable: {relative}") from exc
    return {"path": relative, "kind": kind, "size_bytes": size, "sha256": digest}


def capture_pdf_inputs(root: Path, sections: Sequence[Path]) -> dict[str, Any]:
    if not sections:
        raise PdfReceiptError("PDF input manifest needs hydrated sections")
    rows = [_record(root / name, root, kind) for name, kind in _PRIMARY_INPUTS.items()]
    rows.extend(_record(path, root, "section") for path in sections)
    return {
        "sections": [_relative(path, root) for path in sections],
        "assets": [],
        "files": sorted(rows, key=lambda row: row["path"]),
    }


def latex_asset_paths(tex: Path, *, build_directory: Path, root: Path) -> list[Path]:
    text = tex.read_text(encoding="utf-8")
    text = re.sub(r"(?<!\\)%[^\n]*", "", text)
    matches = list(_IMAGE_RE.finditer(text))
    if len(matches) != len(re.findall(r"\\includegraphics\b", text)):
        raise PdfReceiptError(
            "LaTeX contains an unsupported non-literal image input; cannot bind PDF provenance"
        )
    paths: set[Path] = set()
    for match in matches:
        path = Path(match.group(1).strip())
        if not path.is_absolute():
            path = build_directory / path
        _relative(path, root)
        if not path.is_file():
            raise PdfReceiptError(
                f"LaTeX image input is missing: {_relative(path, root)}"
            )
        paths.add(path.resolve())
    return sorted(paths)


def add_pdf_assets(
    root: Path,
    manifest: Mapping[str, Any],
    assets: Iterable[Path],
) -> dict[str, Any]:
    validate_pdf_inputs(root, manifest)
    rows = {row["path"]: dict(row) for row in manifest["files"]}
    for path in assets:
        row = _record(path, root, "asset")
        rows.setdefault(row["path"], row)
    result = {
        "sections": list(manifest["sections"]),
        "assets": sorted(name for name, row in rows.items() if row["kind"] == "asset"),
        "files": [rows[name] for name in sorted(rows)],
    }
    validate_pdf_inputs(root, result)
    return result


def validate_pdf_inputs(root: Path, manifest: Mapping[str, Any]) -> None:
    sections, rows = manifest.get("sections"), manifest.get("files")
    assets = manifest.get("assets")
    if (
        not isinstance(sections, list)
        or not sections
        or any(not isinstance(path, str) for path in sections)
        or len(set(sections)) != len(sections)
        or not isinstance(rows, list)
        or not rows
        or not isinstance(assets, list)
        or any(not isinstance(path, str) for path in assets)
        or len(set(assets)) != len(assets)
    ):
        raise PdfReceiptError(
            "PDF input manifest is missing its complete section/file set"
        )
    expected_sections = [
        _relative(path, root)
        for path in hydrated_section_files(root / "output" / "manuscript")
    ]
    if sections != expected_sections:
        raise PdfReceiptError("hydrated PDF section set/order changed")
    by_path: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("path"), str):
            raise PdfReceiptError("PDF input manifest contains a malformed file row")
        name = row["path"]
        path = Path(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or _relative(root / path, root) != name
            or name in by_path
        ):
            raise PdfReceiptError("PDF input manifest has an unsafe or duplicate path")
        if (
            not isinstance(row.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
            or type(row.get("size_bytes")) is not int
            or row["size_bytes"] < 0
            or row.get("kind")
            not in ("config", "preamble", "bibliography", "section", "asset")
        ):
            raise PdfReceiptError(f"PDF input digest row is malformed: {name}")
        current = _record(root / path, root, row["kind"])
        if (
            current["sha256"] != row["sha256"]
            or current["size_bytes"] != row["size_bytes"]
        ):
            raise PdfReceiptError(f"PDF input changed: {name}")
        by_path[name] = row
    if any(
        name not in by_path or by_path[name]["kind"] != kind
        for name, kind in _PRIMARY_INPUTS.items()
    ):
        raise PdfReceiptError(
            "PDF input manifest is missing configuration/preamble/bibliography"
        )
    if {name for name, row in by_path.items() if row["kind"] == "section"} != set(
        sections
    ):
        raise PdfReceiptError(
            "PDF input manifest does not cover the complete hydrated section set"
        )
    if {name for name, row in by_path.items() if row["kind"] == "asset"} != set(assets):
        raise PdfReceiptError(
            "PDF input manifest does not cover its complete image set"
        )


def write_pdf_receipt(
    target: Path,
    *,
    root: Path,
    source_revision: str,
    inputs: Mapping[str, Any],
) -> Path:
    validate_pdf_inputs(root, inputs)
    if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise PdfReceiptError(
            "PDF source revision must be the observed full Git commit"
        )
    output = _record(target, root, "pdf")
    if output["size_bytes"] <= 0:
        raise PdfReceiptError("finalized PDF is empty")
    receipt = target.with_suffix(".receipt.json")
    return write_json_artifact(
        receipt,
        {
            "schema": "active-skillference-pdf/v2",
            "output_path": output["path"],
            "size_bytes": output["size_bytes"],
            "sha256": output["sha256"],
            "source_revision": source_revision,
            "inputManifest": dict(inputs),
        },
    )


def pdf_receipt_issues(root: Path, target: Path | None = None) -> list[str]:
    target = target if target is not None else root / "output" / "pdf" / PDF_NAME
    receipt = target.with_suffix(".receipt.json")
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != "active-skillference-pdf/v2"
        ):
            raise PdfReceiptError(
                "missing/legacy PDF input provenance; a genuine re-render is required"
            )
        manifest = payload.get("inputManifest")
        if not isinstance(manifest, Mapping):
            raise PdfReceiptError("PDF receipt has no complete input manifest")
        validate_pdf_inputs(root, manifest)
        output = _record(target, root, "pdf")
        if (
            payload.get("output_path") != output["path"]
            or payload.get("sha256") != output["sha256"]
            or payload.get("size_bytes") != output["size_bytes"]
        ):
            raise PdfReceiptError(
                "finalized PDF bytes do not match the recorded render"
            )
        revision = payload.get("source_revision")
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise PdfReceiptError("PDF receipt has no observed source revision")
    except (OSError, ValueError) as exc:
        return [f"PDF freshness failed: {exc}; re-render before publishing"]
    return []
