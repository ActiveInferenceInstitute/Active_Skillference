"""Tests for the protocol-only learner-pilot contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.pilot.contract import (
    PilotContractError,
    load_pilot_contract,
    validate_pilot_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def test_real_pilot_contract_is_valid_and_protocol_only() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")

    assert payload["status"] == "protocol-only"
    assert payload["participants"]["directIdentifiersAllowed"] is False
    assert "efficacy" in payload["claimsBoundary"]["prohibited"][0]

    # Required nested fields must be present so a dropped section fails loudly.
    assert payload["participants"]["requiredFields"]
    assert payload["events"]["allowedEventTypes"]
    assert payload["outcomes"]["primary"]["estimand"]
    assert payload["outcomes"]["primary"]["measure"]
    assert payload["analysis"]["preregistration"]
    assert payload["analysis"]["notebookContract"]
    assert payload["export"]["sourceBoundary"]
    assert payload["export"]["fields"]


def test_pilot_contract_rejects_allowed_efficacy_claims() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["claimsBoundary"]["allowed"].append("learner efficacy")

    with pytest.raises(PilotContractError, match="efficacy language"):
        validate_pilot_contract(payload)


def test_pilot_contract_rejects_direct_identifiers_and_duplicate_fields() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["participants"]["directIdentifiersAllowed"] = True
    with pytest.raises(PilotContractError, match="directIdentifiersAllowed"):
        validate_pilot_contract(payload)

    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["events"]["requiredFields"].append("event_type")
    with pytest.raises(PilotContractError, match="must not contain duplicates"):
        validate_pilot_contract(payload)


def test_pilot_contract_load_fails_closed_on_missing_or_non_object(
    tmp_path: Path,
) -> None:
    with pytest.raises(PilotContractError, match="could not read pilot contract"):
        load_pilot_contract(tmp_path / "missing.json")

    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(PilotContractError, match="must be a JSON object"):
        load_pilot_contract(bad)


def test_pilot_contract_rejects_wrong_version_and_status() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["contractVersion"] = 2
    with pytest.raises(PilotContractError, match="contractVersion must be 1"):
        validate_pilot_contract(payload)

    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["status"] = "live"
    with pytest.raises(PilotContractError, match="protocol-only"):
        validate_pilot_contract(payload)


def test_pilot_contract_rejects_empty_claims_boundary() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["claimsBoundary"]["allowed"] = []
    with pytest.raises(PilotContractError, match="needs both allowed and prohibited"):
        validate_pilot_contract(payload)


def test_pilot_contract_requires_efficacy_in_prohibited() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["claimsBoundary"]["prohibited"] = ["no strong claim"]
    with pytest.raises(PilotContractError, match="must explicitly include efficacy"):
        validate_pilot_contract(payload)


def test_pilot_contract_requires_primary_estimand_and_mapping_secondary() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    del payload["outcomes"]["primary"]["estimand"]
    with pytest.raises(PilotContractError, match="estimand"):
        validate_pilot_contract(payload)

    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["outcomes"]["secondary"] = [1]
    with pytest.raises(PilotContractError, match="must be an object"):
        validate_pilot_contract(payload)


def test_pilot_contract_requires_export_source_boundary() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    del payload["export"]["sourceBoundary"]
    with pytest.raises(PilotContractError, match="sourceBoundary"):
        validate_pilot_contract(payload)


def test_pilot_contract_rejects_wrong_mapping_and_list_shapes() -> None:
    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["participants"] = "not-a-mapping"
    with pytest.raises(PilotContractError, match="participants must be an object"):
        validate_pilot_contract(payload)

    payload = load_pilot_contract(ROOT / "data" / "learner_pilot_contract.json")
    payload["events"]["allowedEventTypes"] = "not-a-list"
    with pytest.raises(PilotContractError, match="allowedEventTypes must be a list"):
        validate_pilot_contract(payload)
