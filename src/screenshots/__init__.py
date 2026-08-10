"""Captured runtime evidence from the running learner dashboard.

These images are registered in the same figure registry as the deterministic
plots, so they carry the same caption, alt-text, and chart-contract floors and
the same manuscript and dashboard parity checks. They differ in one recorded
way: ``evidence_kind`` is ``captured`` rather than ``rendered``.

That distinction is the point. A matplotlib figure is a pure function of
validated project data and rebuilds byte-for-byte from a fresh checkout; a
browser screenshot is a recording of a live system and cannot. Captured rows are
therefore version-controlled under ``manuscript/assets/screenshots/`` instead of
being generated into ``output/``, are excluded from the deterministic
render/registry parity check, and are stamped with the provenance of the run
that produced them — dashboard URL, viewport, live SkillTree counts, and the
full-app proof mode — so a reader can tell which system state they evidence.
"""

from __future__ import annotations

from src.screenshots.capture import (
    CaptureSettings,
    ScreenshotCaptureError,
    capture_screenshots,
)
from src.screenshots.manifest import (
    SCREENSHOT_DIR_NAME,
    SCREENSHOT_PROVENANCE_FILENAME,
    ScreenshotView,
    captured_registry_payload,
    screenshot_views,
)
from src.screenshots.staging import (
    CapturedEvidenceError,
    captured_source_dir,
    stage_captured_evidence,
)

__all__ = [
    "SCREENSHOT_DIR_NAME",
    "SCREENSHOT_PROVENANCE_FILENAME",
    "CaptureSettings",
    "CapturedEvidenceError",
    "ScreenshotCaptureError",
    "ScreenshotView",
    "capture_screenshots",
    "captured_registry_payload",
    "captured_source_dir",
    "screenshot_views",
    "stage_captured_evidence",
]
