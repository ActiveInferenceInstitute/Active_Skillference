"""PDF provenance receipts use finalized bytes and a real source revision."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from scripts.render_manuscript import PDF_NAME, ROOT, _write_pdf_receipt


def test_pdf_receipt_records_finalized_output(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Receipt Test",
            "-c",
            "user.email=receipt@example.org",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "Source revision",
        ],
        cwd=tmp_path,
        check=True,
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    target = tmp_path / "output" / "pdf" / PDF_NAME
    target.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "output" / "pdf" / PDF_NAME, target)
    receipt = target.with_suffix(".receipt.json")
    receipt.write_text("outdated receipt", encoding="utf-8")

    assert _write_pdf_receipt(target, root=tmp_path) == receipt

    content = target.read_bytes()
    assert json.loads(receipt.read_text(encoding="utf-8")) == {
        "schema": "active-skillference-pdf/v1",
        "output_path": f"output/pdf/{PDF_NAME}",
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "source_revision": revision,
    }
