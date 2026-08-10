"""Validate manuscript figure and artifact surfaces against generated outputs."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.image as mpimg
import numpy as np
import yaml  # type: ignore[import-untyped]

from src.artifacts.json_io import (
    JsonArtifactError,
    read_json_object,
    write_json_artifact,
)
from src.figures.registry import (
    DEFAULT_ASSET_ROOT,
    FigureRegistryEntry,
    FigureRegistryError,
    load_figure_registry_rows,
)

_CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
_DECLARED_FIGURE_RE = re.compile(r"\{#(fig:[A-Za-z0-9_:-]+)(?:\s+[^}]*)?\}")
_REFERENCED_FIGURE_RE = re.compile(r"@fig:([A-Za-z0-9_:-]+)")
_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_MIN_FIGURE_WIDTH = 480
_MIN_FIGURE_HEIGHT = 360
_MIN_FIGURE_STDDEV = 0.01
_MIN_FIGURE_RANGE = 0.05
_MIN_CAPTION_WORDS = 24
_MIN_ALT_TEXT_WORDS = 20
_MIN_SEMANTIC_WORDS = 7
_NUMERIC_ANNOTATION_FIGURES = frozenset(
    {
        "free_energy_descent.png",
        "efe_decomposition.png",
        "kernel_sensitivity_profiles.png",
    }
)


class ManuscriptArtifactError(ValueError):
    """Raised when manuscript artifact wiring is incomplete or stale."""


@dataclass(frozen=True)
class CoverAssetAudit:
    """Validation result for the first-page generated cover asset."""

    configured_image: str
    resolved_path: str
    dashboard_category: str
    image_metrics: FigureImageMetrics | None
    missing_file: bool
    unreadable_file: str
    low_information_file: bool
    missing_dashboard_artifact: bool
    registered_as_figure: bool

    def issues(self) -> tuple[str, ...]:
        """Return human-readable cover-asset issues."""
        messages: list[str] = []
        if not self.configured_image:
            messages.append("book.cover.image is not configured")
        if self.missing_file:
            messages.append(f"cover image file is missing: {self.resolved_path}")
        if self.unreadable_file:
            messages.append(
                f"cover image file is not a readable PNG: {self.unreadable_file}"
            )
        if self.low_information_file:
            messages.append(
                f"cover image file is blank, tiny, or low-information: {self.resolved_path}"
            )
        if self.missing_dashboard_artifact:
            messages.append("cover image is missing from dashboard artifacts")
        if self.dashboard_category == "figures":
            messages.append(
                "cover dashboard artifact must not use the figures category"
            )
        if self.registered_as_figure:
            messages.append("cover image must not appear in figure_registry.json")
        return tuple(messages)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic cover-audit data for JSON output."""
        return {
            "configuredImage": self.configured_image,
            "dashboardCategory": self.dashboard_category,
            "imageMetrics": self.image_metrics.to_dict()
            if self.image_metrics is not None
            else None,
            "issues": list(self.issues()),
            "resolvedPath": self.resolved_path,
            "summary": {
                "issues": len(self.issues()),
                "missingDashboardArtifact": self.missing_dashboard_artifact,
                "registeredAsFigure": self.registered_as_figure,
            },
        }


@dataclass(frozen=True)
class FrontMatterVisualAudit:
    """Validation result for the generated page-two publishing visual."""

    configured_image: str
    configured_title: str
    configured_caption: str
    resolved_path: str
    dashboard_category: str
    image_metrics: FigureImageMetrics | None
    missing_file: bool
    unreadable_file: str
    low_information_file: bool
    missing_dashboard_artifact: bool
    registered_as_figure: bool

    def issues(self) -> tuple[str, ...]:
        """Return human-readable front-matter visual issues."""
        messages: list[str] = []
        if not self.configured_image:
            messages.append("front_matter.page_two_visual.image is not configured")
        if not self.configured_title:
            messages.append("front_matter.page_two_visual.title is not configured")
        if not self.configured_caption:
            messages.append("front_matter.page_two_visual.caption is not configured")
        if self.missing_file:
            messages.append(f"page-two visual file is missing: {self.resolved_path}")
        if self.unreadable_file:
            messages.append(
                f"page-two visual file is not a readable PNG: {self.unreadable_file}"
            )
        if self.low_information_file:
            messages.append(
                f"page-two visual file is blank, tiny, or low-information: {self.resolved_path}"
            )
        if self.missing_dashboard_artifact:
            messages.append("page-two visual is missing from dashboard artifacts")
        if self.dashboard_category == "figures":
            messages.append(
                "page-two visual dashboard artifact must not use the figures category"
            )
        if self.registered_as_figure:
            messages.append("page-two visual must not appear in figure_registry.json")
        return tuple(messages)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic front-matter-visual audit data for JSON output."""
        return {
            "configuredCaption": self.configured_caption,
            "configuredImage": self.configured_image,
            "configuredTitle": self.configured_title,
            "dashboardCategory": self.dashboard_category,
            "imageMetrics": self.image_metrics.to_dict()
            if self.image_metrics is not None
            else None,
            "issues": list(self.issues()),
            "resolvedPath": self.resolved_path,
            "summary": {
                "issues": len(self.issues()),
                "missingDashboardArtifact": self.missing_dashboard_artifact,
                "registeredAsFigure": self.registered_as_figure,
            },
        }


@dataclass(frozen=True)
class FigureImageMetrics:
    """Information-content checks for one generated PNG."""

    filename: str
    width: int
    height: int
    channels: int
    min_value: float
    max_value: float
    stddev: float
    bytes: int

    def to_dict(self) -> dict[str, int | float | str]:
        """Return a deterministic JSON representation."""
        return {
            "bytes": self.bytes,
            "channels": self.channels,
            "filename": self.filename,
            "height": self.height,
            "maxValue": round(self.max_value, 6),
            "minValue": round(self.min_value, 6),
            "stddev": round(self.stddev, 6),
            "width": self.width,
        }


@dataclass(frozen=True)
class ManuscriptArtifactAudit:
    """Cross-surface audit for generated figures and dashboard artifacts."""

    registry_entries: tuple[FigureRegistryEntry, ...]
    image_metrics: tuple[FigureImageMetrics, ...]
    declared_figure_labels: tuple[str, ...]
    referenced_figure_labels: tuple[str, ...]
    dashboard_figure_paths: tuple[str, ...]
    missing_files: tuple[str, ...]
    unreadable_files: tuple[str, ...]
    low_information_files: tuple[str, ...]
    terse_captions: tuple[str, ...]
    terse_alt_texts: tuple[str, ...]
    missing_semantic_metadata: tuple[str, ...]
    missing_claim_tokens: tuple[str, ...]
    registry_labels_missing_from_manuscript: tuple[str, ...]
    manuscript_labels_missing_from_registry: tuple[str, ...]
    references_missing_declarations: tuple[str, ...]
    registry_files_missing_from_dashboard: tuple[str, ...]
    dashboard_files_missing_from_registry: tuple[str, ...]
    missing_table_companions: tuple[str, ...]
    malformed_table_companions: tuple[str, ...]

    def issues(self) -> tuple[str, ...]:
        """Return human-readable failure messages."""
        messages: list[str] = []
        if self.missing_files:
            messages.append(
                "registered figure files missing: " + ", ".join(self.missing_files)
            )
        if self.unreadable_files:
            messages.append(
                "registered figure files are not readable PNGs: "
                + ", ".join(self.unreadable_files)
            )
        if self.low_information_files:
            messages.append(
                "registered figure files are blank, tiny, or low-information: "
                + ", ".join(self.low_information_files)
            )
        if self.terse_captions:
            messages.append(
                "figure captions are too terse: " + ", ".join(self.terse_captions)
            )
        if self.terse_alt_texts:
            messages.append(
                "figure alt text is too terse: " + ", ".join(self.terse_alt_texts)
            )
        if self.missing_semantic_metadata:
            messages.append(
                "figure semantic metadata is missing or too terse: "
                + ", ".join(self.missing_semantic_metadata)
            )
        if self.missing_claim_tokens:
            messages.append(
                "numeric figures are missing claim tokens: "
                + ", ".join(self.missing_claim_tokens)
            )
        if self.registry_labels_missing_from_manuscript:
            messages.append(
                "registered figure labels not declared in manuscript: "
                + ", ".join(self.registry_labels_missing_from_manuscript)
            )
        if self.manuscript_labels_missing_from_registry:
            messages.append(
                "manuscript figure labels missing from registry: "
                + ", ".join(self.manuscript_labels_missing_from_registry)
            )
        if self.references_missing_declarations:
            messages.append(
                "figure cross-references missing declarations: "
                + ", ".join(self.references_missing_declarations)
            )
        if self.registry_files_missing_from_dashboard:
            messages.append(
                "registered figure files missing from dashboard artifacts: "
                + ", ".join(self.registry_files_missing_from_dashboard)
            )
        if self.dashboard_files_missing_from_registry:
            messages.append(
                "dashboard figure artifacts missing from registry: "
                + ", ".join(self.dashboard_files_missing_from_registry)
            )
        if self.missing_table_companions:
            messages.append(
                "figure table companions missing: "
                + ", ".join(self.missing_table_companions)
            )
        if self.malformed_table_companions:
            messages.append(
                "figure table companions malformed: "
                + "; ".join(self.malformed_table_companions)
            )
        return tuple(messages)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic audit data for JSON output."""
        return {
            "dashboardFigurePaths": list(self.dashboard_figure_paths),
            "declaredFigureLabels": list(self.declared_figure_labels),
            "imageMetrics": [metric.to_dict() for metric in self.image_metrics],
            "issues": list(self.issues()),
            "referencedFigureLabels": list(self.referenced_figure_labels),
            "registry": [entry.to_dict() for entry in self.registry_entries],
            "summary": {
                "dashboardFigureArtifacts": len(self.dashboard_figure_paths),
                "declaredFigureLabels": len(self.declared_figure_labels),
                "imageMetrics": len(self.image_metrics),
                "lowInformationFigureFiles": len(self.low_information_files),
                "issues": len(self.issues()),
                "referencedFigureLabels": len(self.referenced_figure_labels),
                "registeredFigures": len(self.registry_entries),
                "semanticMetadataIssues": len(self.missing_semantic_metadata),
                "missingClaimTokens": len(self.missing_claim_tokens),
                "missingTableCompanions": len(self.missing_table_companions),
                "malformedTableCompanions": len(self.malformed_table_companions),
                "terseAltTexts": len(self.terse_alt_texts),
                "terseCaptions": len(self.terse_captions),
                "unreadableFigureFiles": len(self.unreadable_files),
            },
        }


def extract_declared_figure_labels(manuscript_dir: Path) -> tuple[str, ...]:
    """Return figure labels declared with Pandoc-crossref image identifiers."""
    return _extract_labels(manuscript_dir, _DECLARED_FIGURE_RE, prefix="")


def extract_referenced_figure_labels(manuscript_dir: Path) -> tuple[str, ...]:
    """Return figure labels referenced with ``[@fig:...]`` cross-references."""
    return _extract_labels(manuscript_dir, _REFERENCED_FIGURE_RE, prefix="fig:")


def load_figure_registry(path: Path) -> tuple[FigureRegistryEntry, ...]:
    """Load and validate ``figure_registry.json``."""
    try:
        return load_figure_registry_rows(path)
    except FigureRegistryError as exc:
        raise ManuscriptArtifactError(str(exc)) from exc


def audit_manuscript_artifacts(
    *,
    manuscript_dir: Path,
    figure_registry_path: Path,
    figure_dir: Path,
    dashboard_figure_paths: Iterable[Path | str] = (),
    project_root: Path | None = None,
) -> ManuscriptArtifactAudit:
    """Compute figure/registry/dashboard drift without raising."""
    entries = load_figure_registry(figure_registry_path)
    declared = extract_declared_figure_labels(manuscript_dir)
    referenced = extract_referenced_figure_labels(manuscript_dir)
    registry_labels = {entry.label for entry in entries}
    declared_labels = set(declared)
    referenced_labels = set(referenced)
    registry_files = {entry.filename for entry in entries}
    dashboard_paths = tuple(
        sorted(_normalize_path(path) for path in dashboard_figure_paths)
    )
    dashboard_files = {Path(path).name for path in dashboard_paths}
    image_metrics, unreadable_files, low_information_files = _audit_figure_images(
        entries,
        figure_dir,
        project_root,
    )
    missing_companions, malformed_companions = _audit_table_companions(
        entries,
        _table_companion_path(figure_registry_path),
    )

    return ManuscriptArtifactAudit(
        registry_entries=entries,
        image_metrics=image_metrics,
        declared_figure_labels=declared,
        referenced_figure_labels=referenced,
        dashboard_figure_paths=dashboard_paths,
        missing_files=tuple(
            sorted(
                entry.filename
                for entry in entries
                if not _entry_image_path(entry, figure_dir, project_root).exists()
            )
        ),
        unreadable_files=unreadable_files,
        low_information_files=low_information_files,
        terse_captions=tuple(
            sorted(
                entry.label
                for entry in entries
                if _word_count(entry.caption) < _MIN_CAPTION_WORDS
            )
        ),
        terse_alt_texts=tuple(
            sorted(
                entry.label
                for entry in entries
                if _word_count(entry.alt_text) < _MIN_ALT_TEXT_WORDS
            )
        ),
        missing_semantic_metadata=tuple(
            sorted(
                entry.label for entry in entries if _has_terse_semantic_metadata(entry)
            )
        ),
        missing_claim_tokens=tuple(
            sorted(
                entry.label
                for entry in entries
                if entry.filename in _NUMERIC_ANNOTATION_FIGURES
                and not entry.claim_tokens
            )
        ),
        registry_labels_missing_from_manuscript=tuple(
            sorted(registry_labels - declared_labels)
        ),
        manuscript_labels_missing_from_registry=tuple(
            sorted(declared_labels - registry_labels)
        ),
        references_missing_declarations=tuple(
            sorted(referenced_labels - declared_labels)
        ),
        registry_files_missing_from_dashboard=tuple(
            sorted(registry_files - dashboard_files)
        ),
        dashboard_files_missing_from_registry=tuple(
            sorted(dashboard_files - registry_files)
        ),
        missing_table_companions=missing_companions,
        malformed_table_companions=malformed_companions,
    )


def validate_manuscript_artifacts(
    *,
    manuscript_dir: Path,
    figure_registry_path: Path,
    figure_dir: Path,
    dashboard_figure_paths: Iterable[Path | str] = (),
    project_root: Path | None = None,
) -> ManuscriptArtifactAudit:
    """Validate figure/registry/dashboard wiring, raising on drift."""
    audit = audit_manuscript_artifacts(
        manuscript_dir=manuscript_dir,
        figure_registry_path=figure_registry_path,
        figure_dir=figure_dir,
        dashboard_figure_paths=dashboard_figure_paths,
        project_root=project_root,
    )
    issues = audit.issues()
    if issues:
        raise ManuscriptArtifactError("; ".join(issues))
    return audit


def audit_cover_asset(
    *,
    config_path: Path,
    project_root: Path,
    figure_registry_path: Path,
    dashboard_artifacts: Iterable[Any] = (),
) -> CoverAssetAudit:
    """Compute first-page cover image validation without raising."""
    project_root = Path(project_root)
    raw_image = _configured_cover_image(config_path)
    resolved = _resolve_cover_image_path(raw_image, project_root)
    relative_path = _project_relative_path(resolved, project_root)
    dashboard_category = ""
    for artifact in dashboard_artifacts:
        artifact_path = getattr(artifact, "relative_path", None)
        if (
            artifact_path is not None
            and Path(artifact_path).as_posix() == relative_path
        ):
            dashboard_category = str(getattr(artifact, "category", ""))
            break

    metric: FigureImageMetrics | None = None
    unreadable = ""
    low_information = False
    missing = not resolved.exists()
    if not missing:
        try:
            metric = _figure_image_metrics(resolved, resolved.name)
        except (OSError, ValueError, SyntaxError) as exc:
            unreadable = f"{resolved.name} ({exc})"
        else:
            low_information = _is_low_information(metric)

    registered_as_figure = False
    if figure_registry_path.exists():
        registered_as_figure = any(
            entry.filename == resolved.name
            for entry in load_figure_registry(figure_registry_path)
        )

    return CoverAssetAudit(
        configured_image=raw_image,
        resolved_path=relative_path,
        dashboard_category=dashboard_category,
        image_metrics=metric,
        missing_file=missing,
        unreadable_file=unreadable,
        low_information_file=low_information,
        missing_dashboard_artifact=not dashboard_category,
        registered_as_figure=registered_as_figure,
    )


def validate_cover_asset(
    *,
    config_path: Path,
    project_root: Path,
    figure_registry_path: Path,
    dashboard_artifacts: Iterable[Any] = (),
) -> CoverAssetAudit:
    """Validate the first-page cover asset, raising on missing or stale wiring."""
    audit = audit_cover_asset(
        config_path=config_path,
        project_root=project_root,
        figure_registry_path=figure_registry_path,
        dashboard_artifacts=dashboard_artifacts,
    )
    issues = audit.issues()
    if issues:
        raise ManuscriptArtifactError("; ".join(issues))
    return audit


def audit_front_matter_visual(
    *,
    config_path: Path,
    project_root: Path,
    figure_registry_path: Path,
    dashboard_artifacts: Iterable[Any] = (),
) -> FrontMatterVisualAudit:
    """Compute page-two front-matter visual validation without raising."""
    project_root = Path(project_root)
    raw_image, title, caption = _configured_page_two_visual(config_path)
    resolved = _resolve_front_matter_visual_path(raw_image, project_root)
    relative_path = _project_relative_path(resolved, project_root)
    dashboard_category = ""
    for artifact in dashboard_artifacts:
        artifact_path = getattr(artifact, "relative_path", None)
        if (
            artifact_path is not None
            and Path(artifact_path).as_posix() == relative_path
        ):
            dashboard_category = str(getattr(artifact, "category", ""))
            break

    metric: FigureImageMetrics | None = None
    unreadable = ""
    low_information = False
    missing = not resolved.exists()
    if not missing:
        try:
            metric = _figure_image_metrics(resolved, resolved.name)
        except (OSError, ValueError, SyntaxError) as exc:
            unreadable = f"{resolved.name} ({exc})"
        else:
            low_information = _is_low_information(metric)

    registered_as_figure = False
    if figure_registry_path.exists():
        registered_as_figure = any(
            entry.filename == resolved.name
            for entry in load_figure_registry(figure_registry_path)
        )

    return FrontMatterVisualAudit(
        configured_caption=caption,
        configured_image=raw_image,
        configured_title=title,
        dashboard_category=dashboard_category,
        image_metrics=metric,
        low_information_file=low_information,
        missing_dashboard_artifact=not dashboard_category,
        missing_file=missing,
        registered_as_figure=registered_as_figure,
        resolved_path=relative_path,
        unreadable_file=unreadable,
    )


def validate_front_matter_visual(
    *,
    config_path: Path,
    project_root: Path,
    figure_registry_path: Path,
    dashboard_artifacts: Iterable[Any] = (),
) -> FrontMatterVisualAudit:
    """Validate the page-two visual asset, raising on missing or stale wiring."""
    audit = audit_front_matter_visual(
        config_path=config_path,
        project_root=project_root,
        figure_registry_path=figure_registry_path,
        dashboard_artifacts=dashboard_artifacts,
    )
    issues = audit.issues()
    if issues:
        raise ManuscriptArtifactError("; ".join(issues))
    return audit


def write_manuscript_artifact_audit(audit: ManuscriptArtifactAudit, path: Path) -> Path:
    """Write the deterministic manuscript artifact audit JSON."""
    return write_json_artifact(Path(path), audit.to_dict())


def write_cover_asset_audit(audit: CoverAssetAudit, path: Path) -> Path:
    """Write deterministic cover-asset audit JSON."""
    return write_json_artifact(Path(path), audit.to_dict())


def write_front_matter_visual_audit(audit: FrontMatterVisualAudit, path: Path) -> Path:
    """Write deterministic page-two visual audit JSON."""
    return write_json_artifact(Path(path), audit.to_dict())


def _extract_labels(
    manuscript_dir: Path, pattern: re.Pattern[str], *, prefix: str
) -> tuple[str, ...]:
    labels: set[str] = set()
    for path in sorted(Path(manuscript_dir).glob("[0-9][0-9]*_*.md")):
        body = _CODE_RE.sub(" ", path.read_text(encoding="utf-8"))
        labels.update(prefix + match for match in pattern.findall(body))
    return tuple(sorted(labels))


def _has_terse_semantic_metadata(entry: FigureRegistryEntry) -> bool:
    fields = (
        entry.data_source,
        " ".join(entry.data_sources),
        entry.data_grain,
        entry.encoding,
        entry.palette_policy,
        entry.non_color_encoding,
        entry.question,
        entry.takeaway,
        entry.subtitle,
        entry.interpretation_boundary,
        entry.static_read,
        entry.false_certification_risk,
        entry.failure_mode,
        entry.accessibility_note,
        entry.mobile_note,
        entry.mobile_read,
        entry.qa_role,
        entry.visual_grammar,
    )
    return any(_word_count(field) < _MIN_SEMANTIC_WORDS for field in fields)


def _audit_table_companions(
    entries: tuple[FigureRegistryEntry, ...],
    path: Path,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    requested = {
        entry.table_companion_id: entry.label
        for entry in entries
        if entry.table_companion_id
    }
    if not requested:
        return (), ()
    if not path.exists():
        return tuple(sorted(f"{label}:{cid}" for cid, label in requested.items())), ()
    try:
        payload = read_json_object(path)
    except (OSError, ValueError, JsonArtifactError) as exc:
        return (), (f"{path.name}: {exc}",)
    figures = payload.get("figures")
    if not isinstance(figures, dict):
        return (), ("figure_table_companions.json: figures must be an object",)
    companion_by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    malformed: list[str] = []
    for label, companion in figures.items():
        if not isinstance(label, str) or not isinstance(companion, dict):
            malformed.append("figures entries must map labels to objects")
            continue
        companion_id = companion.get("companionId")
        if isinstance(companion_id, str) and companion_id.strip():
            companion_by_id[companion_id.strip()] = (label, companion)
    missing: list[str] = []
    for companion_id, registry_label in sorted(requested.items()):
        companion_pair = companion_by_id.get(companion_id)
        if companion_pair is None:
            missing.append(f"{registry_label}:{companion_id}")
            continue
        keyed_label, companion = companion_pair
        issue = _table_companion_issue(
            keyed_label=keyed_label,
            registry_label=registry_label,
            companion_id=companion_id,
            companion=companion,
        )
        if issue:
            malformed.append(issue)
    return tuple(sorted(missing)), tuple(sorted(set(malformed)))


def _table_companion_path(figure_registry_path: Path) -> Path:
    registry_parent = Path(figure_registry_path).parent
    if registry_parent.name == "figures":
        return registry_parent.parent / "data" / "figure_table_companions.json"
    return registry_parent / "data" / "figure_table_companions.json"


def _table_companion_issue(
    *,
    keyed_label: str,
    registry_label: str,
    companion_id: str,
    companion: dict[str, Any],
) -> str:
    figure_label = companion.get("figureLabel")
    title = companion.get("title")
    columns = companion.get("columns")
    rows = companion.get("rows")
    if keyed_label != registry_label or figure_label != registry_label:
        return f"{registry_label}:{companion_id} has missing or mismatched figure label"
    if not isinstance(title, str) or not title.strip():
        return f"{registry_label}:{companion_id} title is empty"
    if not isinstance(columns, list) or not all(
        isinstance(column, str) and column.strip() for column in columns
    ):
        return f"{registry_label}:{companion_id} columns are empty or unlabeled"
    if not isinstance(rows, list) or not rows:
        return f"{registry_label}:{companion_id} rows are empty"
    if not all(isinstance(row, dict) and row for row in rows):
        return f"{registry_label}:{companion_id} rows must be non-empty objects"
    return ""


def _entry_image_path(
    entry: FigureRegistryEntry,
    figure_dir: Path,
    project_root: Path | None,
) -> Path:
    """Resolve one registry row's image, honoring its declared asset root.

    Deterministic figures resolve against the generated figure directory.
    Captured browser evidence declares a tracked asset root instead, because a
    recording of a running system cannot be rebuilt from a fresh checkout and so
    is version-controlled rather than generated.
    """
    if entry.asset_root == DEFAULT_ASSET_ROOT:
        return Path(figure_dir) / entry.filename
    root = (
        Path(project_root) if project_root is not None else Path(figure_dir).parents[1]
    )
    return root / entry.asset_root / entry.filename


def _audit_figure_images(
    entries: tuple[FigureRegistryEntry, ...],
    figure_dir: Path,
    project_root: Path | None = None,
) -> tuple[tuple[FigureImageMetrics, ...], tuple[str, ...], tuple[str, ...]]:
    metrics: list[FigureImageMetrics] = []
    unreadable: list[str] = []
    low_information: list[str] = []
    for entry in entries:
        path = _entry_image_path(entry, figure_dir, project_root)
        if not path.exists():
            continue
        try:
            metric = _figure_image_metrics(path, entry.filename)
        except (OSError, ValueError, SyntaxError) as exc:
            unreadable.append(f"{entry.filename} ({exc})")
            continue
        metrics.append(metric)
        if _is_low_information(metric):
            low_information.append(entry.filename)
    return tuple(metrics), tuple(sorted(unreadable)), tuple(sorted(low_information))


def _is_low_information(metric: FigureImageMetrics) -> bool:
    """Return whether a figure image is too small, too flat, or too low-contrast.

    Single source of truth for the cover-asset and figure-image audits (previously this
    predicate was duplicated). An image is rejected when it is below the minimum pixel
    dimensions, has standard deviation below ``_MIN_FIGURE_STDDEV`` (a near-uniform,
    near-blank frame), or spans a value range below ``_MIN_FIGURE_RANGE`` (no contrast).
    """
    return (
        metric.width < _MIN_FIGURE_WIDTH
        or metric.height < _MIN_FIGURE_HEIGHT
        or metric.stddev < _MIN_FIGURE_STDDEV
        or metric.max_value - metric.min_value < _MIN_FIGURE_RANGE
    )


def _figure_image_metrics(path: Path, filename: str) -> FigureImageMetrics:
    image = np.asarray(mpimg.imread(path))
    if image.size == 0 or image.ndim < 2:
        raise ValueError("empty image")
    data = image.astype(float)
    if data.ndim == 2:
        height, width = data.shape
        channels = 1
    elif data.ndim == 3:
        height, width, channels = data.shape
        if channels >= 3:
            data = data[..., :3]
    else:
        raise ValueError(f"unsupported image rank {data.ndim}")
    return FigureImageMetrics(
        filename=filename,
        width=int(width),
        height=int(height),
        channels=int(channels),
        min_value=float(np.nanmin(data)),
        max_value=float(np.nanmax(data)),
        stddev=float(np.nanstd(data)),
        bytes=path.stat().st_size,
    )


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _normalize_path(path: Path | str) -> str:
    return Path(path).as_posix()


def _configured_cover_image(config_path: Path) -> str:
    if not Path(config_path).is_file():
        return ""
    payload = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ""
    book = payload.get("book")
    if not isinstance(book, dict):
        return ""
    cover = book.get("cover")
    if not isinstance(cover, dict):
        return ""
    image = cover.get("image")
    return str(image).strip() if image else ""


def _configured_page_two_visual(config_path: Path) -> tuple[str, str, str]:
    if not Path(config_path).is_file():
        return "", "", ""
    payload = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return "", "", ""
    front_matter = payload.get("front_matter")
    if not isinstance(front_matter, dict):
        return "", "", ""
    visual = front_matter.get("page_two_visual")
    if not isinstance(visual, dict):
        return "", "", ""
    image = visual.get("image")
    title = visual.get("title")
    caption = visual.get("caption")
    return (
        str(image).strip() if image else "",
        str(title).strip() if title else "",
        str(caption).strip() if caption else "",
    )


def _resolve_cover_image_path(raw_image: str, project_root: Path) -> Path:
    if not raw_image:
        return project_root / "output" / "figures" / "active_skillference_cover.png"
    image_path = Path(raw_image)
    if image_path.is_absolute():
        return image_path
    return (project_root / "output" / "manuscript" / image_path).resolve()


def _resolve_front_matter_visual_path(raw_image: str, project_root: Path) -> Path:
    if not raw_image:
        return (
            project_root / "output" / "figures" / "active_skillference_skill_atlas.png"
        )
    image_path = Path(raw_image)
    if image_path.is_absolute():
        return image_path
    return (project_root / "output" / "manuscript" / image_path).resolve()


def _project_relative_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
