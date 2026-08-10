"""Stage tracked captured evidence into the generated figure directory.

The manuscript renderer resolves every referenced image from ``output/figures``,
so the captured screenshots have to appear there for a render to succeed. They
are not *authored* there: the tracked copies under the captured asset root stay
the source of truth, and this step copies them forward on every generation run
the same way the deterministic plots are written forward.

Copying rather than symlinking keeps the generated tree self-contained, which
matters because the renderer and the archive tooling both treat ``output/`` as a
standalone bundle.
"""

from __future__ import annotations

from pathlib import Path

from src.figures.registry import CAPTURED_ASSET_ROOT
from src.screenshots.manifest import screenshot_views


class CapturedEvidenceError(RuntimeError):
    """Raised when tracked captured evidence is missing from the checkout."""


def captured_source_dir(project_root: Path) -> Path:
    """Return the tracked directory holding captured browser evidence."""
    return Path(project_root) / CAPTURED_ASSET_ROOT


def stage_captured_evidence(
    *, project_root: Path, figure_dir: Path
) -> tuple[Path, ...]:
    """Copy every tracked captured image into ``figure_dir`` and return the paths.

    Fails closed on a missing image. These files cannot be regenerated from
    project data, so an absent one is a broken checkout rather than a step that
    can be recovered by rerunning the pipeline, and the message says so.
    """
    source_dir = captured_source_dir(project_root)
    figure_dir = Path(figure_dir)
    figure_dir.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    missing: list[str] = []
    for view in screenshot_views():
        source = source_dir / view.filename
        if not source.is_file():
            missing.append(view.filename)
            continue
        target = figure_dir / view.filename
        target.write_bytes(source.read_bytes())
        staged.append(target)
    if missing:
        raise CapturedEvidenceError(
            "tracked captured evidence is missing from the checkout: "
            + ", ".join(sorted(missing))
            + f" (expected under {CAPTURED_ASSET_ROOT}/). These images are browser "
            "recordings and cannot be regenerated from project data; restore them "
            "from version control, or recapture against a live stack with "
            "scripts/capture_dashboard_screenshots.py."
        )
    return tuple(staged)
