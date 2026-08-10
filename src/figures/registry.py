"""Typed helpers for figure-registry chart contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.artifacts.json_io import JsonArtifactError, read_json_array

#: Where deterministic, regenerable figures are written.
DEFAULT_ASSET_ROOT = "output/figures"
#: Where captured browser evidence is tracked. It is version-controlled rather
#: than generated because a screenshot of a running system is a recording, not a
#: pure function of project data, so it cannot be rebuilt from a fresh checkout.
CAPTURED_ASSET_ROOT = "manuscript/assets/screenshots"
RENDERED_EVIDENCE = "rendered"
CAPTURED_EVIDENCE = "captured"

FIGURE_CONTRACT_FIELDS = (
    "question",
    "takeaway",
    "data_sources",
    "data_grain",
    "encoding",
    "palette_policy",
    "palette_roots",
    "non_color_encoding",
    "static_read",
    "mobile_read",
    "failure_mode",
)

GENERIC_VISUAL_GRAMMAR = (
    "neutral context is gray; primary evidence is blue; successful gates are green; "
    "caution states are amber; violations are vermillion; strata use the project "
    "colorblind-safe categorical palette with direct labels."
)

GENERIC_CONTRACT_FRAGMENTS: Mapping[str, tuple[str, ...]] = {
    "question": (
        "what evidence question does",
        "make auditable?",
    ),
    "data_grain": (
        "one generated figure-level evidence surface",
        "assembled from generated artifact records",
    ),
    "static_read": (
        "keeps the source, labels, and boundary visible",
        "describes generated artifact state",
    ),
    "mobile_read": (
        "open the larger preview when dense labels exceed",
        "open the full-size image when dense labels exceed",
        "dense labels remain available through the dashboard",
    ),
    "failure_mode": (
        "prevents polished visuals from certifying stale or unsupported surfaces",
        "prevents a polished visual from certifying a stale or unsupported manuscript surface",
    ),
}


class FigureRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class FigureContract:
    """Structured chart contract stored additively in figure_registry.json."""

    question: str
    takeaway: str
    data_sources: tuple[str, ...]
    data_grain: str
    encoding: str
    palette_policy: str
    palette_roots: tuple[str, ...]
    non_color_encoding: str
    static_read: str
    mobile_read: str
    failure_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_grain": self.data_grain,
            "data_sources": list(self.data_sources),
            "encoding": self.encoding,
            "failure_mode": self.failure_mode,
            "mobile_read": self.mobile_read,
            "non_color_encoding": self.non_color_encoding,
            "palette_policy": self.palette_policy,
            "palette_roots": list(self.palette_roots),
            "question": self.question,
            "static_read": self.static_read,
            "takeaway": self.takeaway,
        }


@dataclass(frozen=True)
class FigureRegistryEntry:
    label: str
    filename: str
    caption: str
    alt_text: str
    generated_by: str
    chart_family: str
    data_source: str
    data_sources: tuple[str, ...]
    data_grain: str
    encoding: str
    palette_policy: str
    palette_roots: tuple[str, ...]
    non_color_encoding: str
    question: str
    takeaway: str
    subtitle: str
    interpretation_boundary: str
    static_read: str
    false_certification_risk: str
    failure_mode: str
    accessibility_note: str
    mobile_note: str
    mobile_read: str
    qa_role: str
    visual_grammar: str
    claim_tokens: tuple[str, ...]
    table_companion_id: str = ""
    #: Repository-relative directory holding this image. Deterministic figures
    #: are written to the generated figure directory; captured evidence lives in
    #: a tracked directory because a browser recording cannot be regenerated.
    asset_root: str = DEFAULT_ASSET_ROOT
    #: ``rendered`` for a deterministic matplotlib figure, ``captured`` for a
    #: browser recording of the running application.
    evidence_kind: str = RENDERED_EVIDENCE

    @property
    def is_captured(self) -> bool:
        """Return whether this row is captured evidence rather than a render."""
        return self.evidence_kind == CAPTURED_EVIDENCE

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "accessibility_note": self.accessibility_note,
            "alt_text": self.alt_text,
            "asset_root": self.asset_root,
            "caption": self.caption,
            "chart_family": self.chart_family,
            "claim_tokens": list(self.claim_tokens),
            "data_grain": self.data_grain,
            "evidence_kind": self.evidence_kind,
            "data_source": self.data_source,
            "data_sources": list(self.data_sources),
            "encoding": self.encoding,
            "false_certification_risk": self.false_certification_risk,
            "failure_mode": self.failure_mode,
            "filename": self.filename,
            "generated_by": self.generated_by,
            "interpretation_boundary": self.interpretation_boundary,
            "label": self.label,
            "mobile_note": self.mobile_note,
            "mobile_read": self.mobile_read,
            "non_color_encoding": self.non_color_encoding,
            "palette_policy": self.palette_policy,
            "palette_roots": list(self.palette_roots),
            "qa_role": self.qa_role,
            "question": self.question,
            "static_read": self.static_read,
            "subtitle": self.subtitle,
            "takeaway": self.takeaway,
            "visual_grammar": self.visual_grammar,
        }
        if self.table_companion_id:
            payload["table_companion_id"] = self.table_companion_id
        return payload


def contract_from_registry_row(row: Mapping[str, Any]) -> FigureContract:
    """Build a chart contract from the canonical registry row fields."""
    filename = str(row.get("filename", "figure.png"))
    label = str(row.get("label", filename)).replace("fig:", "")
    chart_family = str(row.get("chart_family", "audit summary"))
    encoding = str(row.get("encoding", "Labeled marks encode the generated evidence."))
    takeaway = str(
        row.get("takeaway", "The figure makes a generated evidence surface reviewable.")
    )
    source = str(row.get("data_source", "Generated project artifact data."))
    boundary = str(
        row.get(
            "interpretation_boundary",
            "The figure describes generated artifact state, not learner outcomes.",
        )
    )
    mobile_note = str(
        row.get(
            "mobile_note",
            "Open the full-size image when dense labels exceed the dashboard card.",
        )
    )
    failure_mode = str(
        row.get(
            "false_certification_risk",
            "Prevents polished visuals from certifying stale or unsupported surfaces.",
        )
    )
    raw_sources = row.get("data_sources")
    if isinstance(raw_sources, list):
        data_sources = tuple(
            item.strip()
            for item in raw_sources
            if isinstance(item, str) and item.strip()
        )
    else:
        data_sources = ()
    raw_roots = row.get("palette_roots")
    if isinstance(raw_roots, list):
        palette_roots = tuple(
            item.strip() for item in raw_roots if isinstance(item, str) and item.strip()
        )
    else:
        palette_roots = ()
    return FigureContract(
        question=str(
            row.get("question", f"What evidence question does {label} make auditable?")
        ),
        takeaway=str(row.get("takeaway", takeaway)),
        data_sources=data_sources or (source,),
        data_grain=str(
            row.get(
                "data_grain",
                (
                    f"One rendered {chart_family} assembled from generated artifact "
                    f"records for {label}."
                ),
            )
        ),
        encoding=str(row.get("encoding", encoding)),
        palette_policy=str(
            row.get(
                "palette_policy",
                "single-root preferred with neutral context and explicit status accents",
            )
        ),
        palette_roots=palette_roots or ("blue", "gray"),
        non_color_encoding=str(
            row.get(
                "non_color_encoding",
                (
                    "Direct labels, ordered positions, axis text, and source notes "
                    "carry the reading without relying on hue alone."
                ),
            )
        ),
        static_read=str(
            row.get(
                "static_read",
                (
                    f"The static {chart_family} keeps the source, labels, and boundary "
                    f"visible: {boundary}"
                ),
            )
        ),
        mobile_read=str(row.get("mobile_read", mobile_note)),
        failure_mode=str(row.get("failure_mode", failure_mode)),
    )


def attach_chart_contract(row: dict[str, Any]) -> None:
    """Attach structured chart-contract metadata to a registry row."""
    contract = contract_from_registry_row(row)
    row.update(contract.to_dict())
    chart_family = str(row.get("chart_family", "audit summary"))
    row["visual_grammar"] = (
        f"{chart_family}: {contract.encoding} Data grain: {contract.data_grain} "
        f"Palette: {contract.palette_policy} using {', '.join(contract.palette_roots)}. "
        f"Non-color encoding: {contract.non_color_encoding} "
        f"Static read: {contract.static_read} Mobile read: {contract.mobile_read}"
    )


def figure_contract_errors(row: Mapping[str, Any], *, index: int) -> tuple[str, ...]:
    """Return structural chart-contract errors for a registry row."""
    errors: list[str] = []
    for field in FIGURE_CONTRACT_FIELDS:
        value = row.get(field)
        if field in {"data_sources", "palette_roots"}:
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                errors.append(
                    f"figure registry row {index}.{field} must be a list of strings"
                )
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"figure registry row {index}.{field} must be a string")
            continue
        normalized = " ".join(value.lower().split())
        for fragment in GENERIC_CONTRACT_FRAGMENTS.get(field, ()):
            if fragment in normalized:
                errors.append(
                    f"figure registry row {index}.{field} must be figure-specific"
                )
                break
    visual = row.get("visual_grammar")
    if isinstance(visual, str) and visual.strip().lower() == GENERIC_VISUAL_GRAMMAR:
        errors.append(
            f"figure registry row {index}.visual_grammar must be figure-specific"
        )
    return tuple(errors)


def load_figure_registry_rows(path: Path) -> tuple[FigureRegistryEntry, ...]:
    try:
        payload = read_json_array(Path(path))
    except JsonArtifactError as exc:
        raise FigureRegistryError("figure registry must be a JSON list") from exc
    entries: list[FigureRegistryEntry] = []
    seen_labels: set[str] = set()
    seen_files: set[str] = set()
    for index, row in enumerate(payload, start=1):
        if not isinstance(row, dict):
            raise FigureRegistryError(f"figure registry row {index} must be an object")
        contract_errors = figure_contract_errors(row, index=index)
        if contract_errors:
            raise FigureRegistryError("; ".join(contract_errors))
        entry = FigureRegistryEntry(
            label=_string_field(row, "label", index),
            filename=_string_field(row, "filename", index),
            caption=_string_field(row, "caption", index),
            alt_text=_string_field(row, "alt_text", index),
            generated_by=_string_field(row, "generated_by", index),
            chart_family=_string_field(row, "chart_family", index),
            data_source=_string_field(row, "data_source", index),
            data_sources=_string_tuple(row, "data_sources", index),
            data_grain=_string_field(row, "data_grain", index),
            encoding=_string_field(row, "encoding", index),
            palette_policy=_string_field(row, "palette_policy", index),
            palette_roots=_string_tuple(row, "palette_roots", index),
            non_color_encoding=_string_field(row, "non_color_encoding", index),
            question=_string_field(row, "question", index),
            takeaway=_string_field(row, "takeaway", index),
            subtitle=_string_field(row, "subtitle", index),
            interpretation_boundary=_string_field(
                row, "interpretation_boundary", index
            ),
            static_read=_string_field(row, "static_read", index),
            false_certification_risk=_string_field(
                row, "false_certification_risk", index
            ),
            failure_mode=_string_field(row, "failure_mode", index),
            accessibility_note=_string_field(row, "accessibility_note", index),
            mobile_note=_string_field(row, "mobile_note", index),
            mobile_read=_string_field(row, "mobile_read", index),
            qa_role=_string_field(row, "qa_role", index),
            visual_grammar=_string_field(row, "visual_grammar", index),
            claim_tokens=_string_tuple(row, "claim_tokens", index),
            table_companion_id=_optional_string_field(row, "table_companion_id", index),
            asset_root=_optional_string_field(row, "asset_root", index)
            or DEFAULT_ASSET_ROOT,
            evidence_kind=_optional_string_field(row, "evidence_kind", index)
            or RENDERED_EVIDENCE,
        )
        if entry.evidence_kind not in {RENDERED_EVIDENCE, CAPTURED_EVIDENCE}:
            raise FigureRegistryError(
                f"figure registry row {index} evidence_kind must be "
                f"{RENDERED_EVIDENCE!r} or {CAPTURED_EVIDENCE!r}"
            )
        expected_root = CAPTURED_ASSET_ROOT if entry.is_captured else DEFAULT_ASSET_ROOT
        if entry.asset_root != expected_root:
            raise FigureRegistryError(
                f"figure registry row {index} asset_root must be {expected_root!r} "
                f"for {entry.evidence_kind!r} evidence"
            )
        if not entry.label.startswith("fig:"):
            raise FigureRegistryError(
                f"figure registry row {index} label must start with fig:"
            )
        if (
            "/" in entry.filename
            or "\\" in entry.filename
            or not entry.filename.endswith(".png")
        ):
            raise FigureRegistryError(
                f"figure registry row {index} filename must be a local PNG filename"
            )
        if entry.label in seen_labels:
            raise FigureRegistryError(f"duplicate figure label {entry.label!r}")
        if entry.filename in seen_files:
            raise FigureRegistryError(f"duplicate figure filename {entry.filename!r}")
        seen_labels.add(entry.label)
        seen_files.add(entry.filename)
        entries.append(entry)
    return tuple(entries)


def _string_field(row: Mapping[str, Any], field: str, index: int) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise FigureRegistryError(
            f"figure registry row {index}.{field} must be a string"
        )
    return value.strip()


def _string_tuple(row: Mapping[str, Any], field: str, index: int) -> tuple[str, ...]:
    value = row.get(field)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise FigureRegistryError(
            f"figure registry row {index}.{field} must be a list of strings"
        )
    return tuple(item.strip() for item in value)


def _optional_string_field(row: Mapping[str, Any], field: str, index: int) -> str:
    value = row.get(field, "")
    if value == "":
        return ""
    if not isinstance(value, str) or not value.strip():
        raise FigureRegistryError(
            f"figure registry row {index}.{field} must be a string when present"
        )
    return value.strip()
