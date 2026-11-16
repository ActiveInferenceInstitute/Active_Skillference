"""A protocol needs linkable event schemas, not merely list-shaped fields."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pilot.contract import PilotContractError, validate_pilot_contract


@pytest.fixture
def pilot_payload() -> dict:
    path = Path(__file__).resolve().parents[1] / "data" / "learner_pilot_contract.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("section", "field"),
    [
        ("participants", "requiredFields"),
        ("events", "allowedEventTypes"),
        ("events", "requiredFields"),
        ("export", "fields"),
    ],
)
def test_schema_lists_cannot_be_empty(
    pilot_payload: dict, section: str, field: str
) -> None:
    pilot_payload[section][field] = []
    with pytest.raises(PilotContractError, match="must not be empty"):
        validate_pilot_contract(pilot_payload)


@pytest.mark.parametrize(
    ("section", "field", "missing"),
    [
        ("participants", "requiredFields", "participant_id_hash"),
        ("events", "requiredFields", "event_timestamp"),
        ("export", "fields", "participant_id_hash"),
        ("export", "fields", "event_type"),
    ],
)
def test_schema_must_retain_linking_fields(
    pilot_payload: dict, section: str, field: str, missing: str
) -> None:
    pilot_payload[section][field].remove(missing)
    with pytest.raises(PilotContractError, match=missing):
        validate_pilot_contract(pilot_payload)


def test_linkage_does_not_require_demographics_or_secondary_outcomes(
    pilot_payload: dict,
) -> None:
    pilot_payload["participants"]["requiredFields"] = ["participant_id_hash"]
    pilot_payload["outcomes"]["secondary"] = []
    validate_pilot_contract(pilot_payload)
