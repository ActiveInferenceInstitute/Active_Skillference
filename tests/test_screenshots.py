"""Tests for the captured browser-evidence family.

Captured screenshots are held to the same registry contract as the deterministic
figures, so most of the coverage here is about the one thing that differs: a
recording must be marked as a recording, kept out of the render/registry parity
check, resolved from its tracked directory, and shipped with the provenance of
the run that produced it.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from src.dashboard.artifact_catalog import ARTIFACTS
from src.figures.plots.registry_io import planned_figure_registry_entries
from src.figures.registry import (
    CAPTURED_ASSET_ROOT,
    CAPTURED_EVIDENCE,
    DEFAULT_ASSET_ROOT,
    RENDERED_EVIDENCE,
    FigureRegistryError,
    figure_contract_errors,
    load_figure_registry_rows,
)
from src.figures.registry_manifest import figure_registry_payload
from src.screenshots.capture import CaptureSettings, ensure_browser_ready
from src.screenshots.manifest import (
    SCREENSHOT_PROVENANCE_FILENAME,
    captured_registry_payload,
    screenshot_views,
)
from src.screenshots.staging import (
    CapturedEvidenceError,
    stage_captured_evidence,
)

REPO = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = REPO / CAPTURED_ASSET_ROOT


def test_captured_rows_satisfy_the_same_chart_contract_as_figures() -> None:
    rows = captured_registry_payload()

    assert rows, "the captured-evidence manifest must not be empty"
    errors: list[str] = []
    for index, row in enumerate(rows):
        errors.extend(figure_contract_errors(row, index=index))
    assert errors == []


def test_captured_rows_declare_captured_evidence_and_tracked_asset_root() -> None:
    for row in captured_registry_payload():
        assert row["evidence_kind"] == CAPTURED_EVIDENCE
        assert row["asset_root"] == CAPTURED_ASSET_ROOT
        assert str(row["label"]).startswith("fig:")


def test_figure_registry_payload_includes_captured_rows() -> None:
    payload = figure_registry_payload(
        include_scholarship=True,
        include_claim_support=True,
        include_roadmap=True,
    )
    captured = [
        row
        for row in payload
        if row.get("evidence_kind", RENDERED_EVIDENCE) == CAPTURED_EVIDENCE
    ]

    assert len(captured) == len(screenshot_views())


def test_planned_render_entries_exclude_captured_evidence() -> None:
    """render_all must not be asked to produce a browser recording."""
    entries = planned_figure_registry_entries(
        include_scholarship=True,
        include_claim_support=True,
        include_roadmap=True,
    )

    assert entries
    assert all(
        entry.get("evidence_kind", RENDERED_EVIDENCE) == RENDERED_EVIDENCE
        for entry in entries
    )
    assert all(
        entry.get("asset_root", DEFAULT_ASSET_ROOT) == DEFAULT_ASSET_ROOT
        for entry in entries
    )


def test_registry_loader_rejects_a_captured_row_in_the_generated_figure_dir(
    tmp_path: Path,
) -> None:
    row = dict(captured_registry_payload()[0])
    row["asset_root"] = DEFAULT_ASSET_ROOT
    path = tmp_path / "figure_registry.json"
    path.write_text(json.dumps([row]), encoding="utf-8")

    try:
        load_figure_registry_rows(path)
    except FigureRegistryError as exc:
        assert "asset_root" in str(exc)
    else:
        raise AssertionError("mislocated captured row unexpectedly loaded")


def test_registry_loader_rejects_an_unknown_evidence_kind(tmp_path: Path) -> None:
    row = dict(captured_registry_payload()[0])
    row["evidence_kind"] = "screenshotish"
    path = tmp_path / "figure_registry.json"
    path.write_text(json.dumps([row]), encoding="utf-8")

    try:
        load_figure_registry_rows(path)
    except FigureRegistryError as exc:
        assert "evidence_kind" in str(exc)
    else:
        raise AssertionError("unknown evidence kind unexpectedly loaded")


def test_every_captured_view_is_declared_and_cross_referenced_in_the_manuscript() -> (
    None
):
    body = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((REPO / "manuscript").glob("[0-9][0-9]*_*.md"))
    )

    for view in screenshot_views():
        assert f"{{#{view.label}" in body, f"{view.label} is not declared"
        assert f"[@{view.label}]" in body, f"{view.label} is not cross-referenced"
        # The manuscript references the staged copy because the renderer resolves
        # every image from the generated figure directory; the tracked original
        # under the captured asset root stays the source of truth and must exist.
        assert f"../output/figures/{view.filename}" in body
        assert (SCREENSHOT_DIR / view.filename).is_file()


def test_every_captured_view_is_a_dashboard_figure_artifact() -> None:
    figure_files = {
        Path(artifact.relative_path).name
        for artifact in ARTIFACTS
        if artifact.category == "figures"
    }

    for view in screenshot_views():
        assert view.filename in figure_files


def test_captured_images_are_tracked_and_carry_provenance() -> None:
    """The images ship with the repository; a missing one is a real failure.

    They cannot be regenerated from project data, so unlike output/ artifacts
    there is no recovery command a reader can run.
    """
    provenance_path = SCREENSHOT_DIR / SCREENSHOT_PROVENANCE_FILENAME
    assert provenance_path.is_file()
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    recorded = {entry["filename"]: entry for entry in provenance["captures"]}
    context = provenance["context"]

    for key in ("dashboardUrl", "viewport", "exportedCounts", "liveDependencies"):
        assert context.get(key), f"capture provenance is missing {key}"
    assert context["fullAppStackProofMode"]
    assert "not a deterministic render" in context["evidenceKind"]

    for view in screenshot_views():
        image = SCREENSHOT_DIR / view.filename
        assert image.is_file(), f"{view.filename} is not tracked"
        assert image.stat().st_size > 0
        assert recorded[view.filename]["sha256"]


def test_captured_images_are_readable_and_not_blank() -> None:
    from src.manuscript.audit import _figure_image_metrics, _is_low_information

    for view in screenshot_views():
        metric = _figure_image_metrics(SCREENSHOT_DIR / view.filename, view.filename)
        assert not _is_low_information(metric)


def test_view_ids_and_labels_are_unique() -> None:
    views = screenshot_views()

    assert len({view.view_id for view in views}) == len(views)
    assert len({view.label for view in views}) == len(views)
    assert len({view.filename for view in views}) == len(views)


def test_capture_settings_default_to_the_tracked_asset_root() -> None:
    settings = CaptureSettings(
        dashboard_url="http://127.0.0.1:8765",
        output_dir=SCREENSHOT_DIR,
        project_root=REPO,
    )

    assert settings.output_dir == SCREENSHOT_DIR
    assert str(settings.staging_root) == "/tmp"


def _write_fake_browser(tmp_path: Path, *, recovers: bool) -> Path:
    state = tmp_path / "state"
    log = tmp_path / "calls.log"
    script = tmp_path / "fake-axi"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        f"state = pathlib.Path({str(state)!r})\n"
        f"log = pathlib.Path({str(log)!r})\n"
        f"recovers = {recovers!r}\n"
        "command = sys.argv[1] if len(sys.argv) > 1 else ''\n"
        "log.open('a', encoding='utf-8').write(command + '\\n')\n"
        "if command == 'start' and recovers:\n"
        "    state.write_text('ready', encoding='utf-8')\n"
        "if command == 'pages':\n"
        "    if state.exists():\n"
        "        print('pages: 1')\n"
        "        raise SystemExit(0)\n"
        "    print('code: TIMEOUT')\n"
        "    raise SystemExit(1)\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_capture_restarts_a_stale_browser_session(tmp_path: Path) -> None:
    script = _write_fake_browser(tmp_path, recovers=True)

    assert ensure_browser_ready(browser_command=str(script)) is True
    assert (tmp_path / "calls.log").read_text(encoding="utf-8").split() == [
        "pages",
        "stop",
        "start",
        "pages",
    ]


def test_capture_leaves_a_healthy_browser_session_alone(tmp_path: Path) -> None:
    script = _write_fake_browser(tmp_path, recovers=True)
    (tmp_path / "state").write_text("ready", encoding="utf-8")

    assert ensure_browser_ready(browser_command=str(script)) is False
    assert (tmp_path / "calls.log").read_text(encoding="utf-8").split() == ["pages"]


def test_capture_script_help_runs_without_a_browser() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/capture_dashboard_screenshots.py", "--help"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0
    assert "--dashboard-url" in result.stdout


def test_staging_copies_every_tracked_capture_into_the_figure_dir(
    tmp_path: Path,
) -> None:
    """The renderer resolves images from the generated figure directory."""
    figure_dir = tmp_path / "output" / "figures"

    staged = stage_captured_evidence(project_root=REPO, figure_dir=figure_dir)

    assert {path.name for path in staged} == {
        view.filename for view in screenshot_views()
    }
    for view in screenshot_views():
        copied = figure_dir / view.filename
        assert copied.is_file()
        assert copied.read_bytes() == (SCREENSHOT_DIR / view.filename).read_bytes()


def test_staging_fails_closed_when_a_tracked_capture_is_missing(
    tmp_path: Path,
) -> None:
    """A missing recording is a broken checkout, not a rerunnable step."""
    project_root = tmp_path / "checkout"
    (project_root / CAPTURED_ASSET_ROOT).mkdir(parents=True)

    try:
        stage_captured_evidence(
            project_root=project_root,
            figure_dir=tmp_path / "figures",
        )
    except CapturedEvidenceError as exc:
        message = str(exc)
        assert "cannot be regenerated" in message
        assert "capture_dashboard_screenshots.py" in message
        for view in screenshot_views():
            assert view.filename in message
    else:
        raise AssertionError("missing captured evidence unexpectedly passed")


def test_manuscript_caption_matches_the_manifest_caption_exactly() -> None:
    """One caption, two places, no drift.

    Each captured figure's caption is written in the manifest and again in the
    manuscript declaration. Nothing but this test stops the two from diverging,
    and a caption that describes the image differently in two places is the same
    false-certification risk the whole evidence family exists to avoid. The
    manifest is the source; the manuscript copy must match it word for word.
    """
    body = (
        (REPO / "manuscript")
        .joinpath("03d_results_skilltree_dashboard_and_front_matter_delivery.md")
        .read_text(encoding="utf-8")
    )

    for view in screenshot_views():
        # The caption class excludes ']' on purpose: a lazy '.*?' would span from
        # one declaration to the next filename and compare the wrong caption.
        pattern = re.compile(
            r"!\[([^\]]*)\]\(\.\./output/figures/" + re.escape(view.filename) + r"\)"
        )
        match = pattern.search(body)
        assert match is not None, f"{view.filename} has no manuscript declaration"
        assert " ".join(match.group(1).split()) == " ".join(view.caption.split()), (
            f"{view.view_id}: manuscript caption has drifted from the manifest"
        )
