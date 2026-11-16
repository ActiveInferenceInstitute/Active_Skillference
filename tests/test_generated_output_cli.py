"""The CLI owns process exits while the importable pipeline raises package errors."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import run_kernels


def test_cli_reports_real_manuscript_rejection_without_replacing_the_builder(tmp_path: Path, monkeypatch) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_fixture.md").write_text("The platform is NSA approved for all learners.\n", encoding="utf-8")
    monkeypatch.setattr(run_kernels, "_ROOT", tmp_path)
    with pytest.raises(SystemExit) as error:
        run_kernels.main()
    assert isinstance(error.value.code, str)
    assert "endorsement-overreach" in error.value.code
