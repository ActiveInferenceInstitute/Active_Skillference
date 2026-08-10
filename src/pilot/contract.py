"""Fail-closed validation for the learner-pilot protocol contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class PilotContractError(ValueError):
    """Raised when the protocol contract is incomplete or overclaims."""


def load_pilot_contract(path: Path) -> dict[str, Any]:
    """Load and validate a JSON pilot contract."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotContractError(
            f"could not read pilot contract {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise PilotContractError("pilot contract must be a JSON object")
    validate_pilot_contract(payload)
    return payload


def validate_pilot_contract(payload: Mapping[str, Any]) -> None:
    """Validate that a protocol is measurable, privacy-bounded, and non-causal."""
    if payload.get("contractVersion") != 1:
        raise PilotContractError("contractVersion must be 1")
    _require_text(payload, "status", expected="protocol-only")
    _require_text(payload, "purpose")
    _require_mapping(payload, "claimsBoundary")
    boundary = payload["claimsBoundary"]
    _require_list(boundary, "allowed")
    _require_list(boundary, "prohibited")
    if not boundary["allowed"] or not boundary["prohibited"]:
        raise PilotContractError(
            "claimsBoundary needs both allowed and prohibited claims"
        )
    if any("efficacy" in str(item).lower() for item in boundary["allowed"]):
        raise PilotContractError("allowed claims cannot contain efficacy language")
    if not any("efficacy" in str(item).lower() for item in boundary["prohibited"]):
        raise PilotContractError("prohibited claims must explicitly include efficacy")

    participants = _require_mapping(payload, "participants")
    _require_text(participants, "identifier")
    if participants.get("directIdentifiersAllowed") is not False:
        raise PilotContractError("directIdentifiersAllowed must be false")
    fields = _require_list(participants, "requiredFields")
    _unique_texts(fields, "participants.requiredFields")

    events = _require_mapping(payload, "events")
    event_types = _require_list(events, "allowedEventTypes")
    _unique_texts(event_types, "events.allowedEventTypes")
    event_fields = _require_list(events, "requiredFields")
    _unique_texts(event_fields, "events.requiredFields")

    outcomes = _require_mapping(payload, "outcomes")
    primary = _require_mapping(outcomes, "primary")
    for field in ("id", "estimand", "measure", "feasibilityBoundary"):
        _require_text(primary, field)
    secondary = _require_list(outcomes, "secondary")
    for index, item in enumerate(secondary, start=1):
        if not isinstance(item, Mapping):
            raise PilotContractError(f"outcomes.secondary[{index}] must be an object")
        for field in ("id", "measure", "interpretationBoundary"):
            _require_text(item, field)

    privacy = _require_mapping(payload, "privacy")
    for field in ("consent", "retention", "access", "minimization"):
        _require_text(privacy, field)
    missing_data = _require_mapping(payload, "missingData")
    for field in ("classification", "primaryAnalysis", "sensitivityAnalysis"):
        _require_text(missing_data, field)

    analysis = _require_mapping(payload, "analysis")
    for field in (
        "unitOfAnalysis",
        "preregistration",
        "stoppingRule",
        "notebookContract",
    ):
        _require_text(analysis, field)
    export = _require_mapping(payload, "export")
    _require_text(export, "sourceBoundary")
    export_fields = _require_list(export, "fields")
    _unique_texts(export_fields, "export.fields")


def _require_mapping(payload: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise PilotContractError(f"{key} must be an object")
    return value


def _require_list(payload: Mapping[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise PilotContractError(f"{key} must be a list")
    return value


def _require_text(
    payload: Mapping[str, Any], key: str, *, expected: str | None = None
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PilotContractError(f"{key} must be non-empty text")
    if expected is not None and value != expected:
        raise PilotContractError(f"{key} must equal {expected!r}")
    return value


def _unique_texts(values: list[Any], location: str) -> None:
    texts = []
    for index, value in enumerate(values, start=1):
        if not isinstance(value, str) or not value.strip():
            raise PilotContractError(f"{location}[{index}] must be non-empty text")
        texts.append(value)
    if len(texts) != len(set(texts)):
        raise PilotContractError(f"{location} must not contain duplicates")
