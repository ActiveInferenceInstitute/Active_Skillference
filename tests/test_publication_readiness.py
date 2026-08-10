"""Tests for publication-readiness guidance."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
RELEASE_DOI = "10.5281/zenodo.21865644"
RELEASE_REPO_URL = "https://github.com/ActiveInferenceInstitute/Active_Skillference"
RELEASE_REPO_SLUG = "ActiveInferenceInstitute/Active_Skillference"


def test_publication_readiness_doc_preserves_release_boundaries() -> None:
    text = (REPO / "docs" / "publication_readiness.md").read_text(encoding="utf-8")

    assert "initial static public-review publication" in text
    assert "not ready to claim a live SkillTree deployment" in text
    assert "Do not claim empirical learner effectiveness" in text
    assert "Do not claim national-security-grade security" in text
    assert "Do not publish DOI" in text
    assert "docs/ip_license_status.md" in text
    assert "THIRD_PARTY_NOTICES.md" in text
    assert "owner has confirmed MIT" in text
    assert "counsel-review checklist" in text
    assert "validate_american_english.py" in text


def test_publication_metadata_matches_the_published_release() -> None:
    """Every identifier surface must name the same deposit and the same target.

    Before release this gate asked whether a DOI was absent. That question stops
    being useful once a real deposit exists, and the useful one takes its place:
    is the DOI *the right one*, everywhere. Divergence between these four files
    is how a plausible but wrong identifier reaches a citation.
    """
    citation = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    codemeta = json.loads((REPO / "codemeta.json").read_text(encoding="utf-8"))
    zenodo = json.loads((REPO / ".zenodo.json").read_text(encoding="utf-8"))
    config = yaml.safe_load((REPO / "manuscript" / "config.yaml").read_text())
    publication = config["publication"]

    assert RELEASE_DOI in citation
    assert f"repository-code: {RELEASE_REPO_URL}" in citation
    assert "date-released:" in citation
    assert codemeta["identifier"] == f"https://doi.org/{RELEASE_DOI}"
    assert codemeta["codeRepository"] == RELEASE_REPO_URL
    assert zenodo["doi"] == RELEASE_DOI
    assert publication["doi"] == RELEASE_DOI
    assert publication["repository_url"] == RELEASE_REPO_URL
    assert publication["github_repository"] == RELEASE_REPO_SLUG
    # Version-specific identifiers stay blank until a versioned deposit exists.
    assert publication["version_doi"] == ""
    assert publication["version_record"] == ""


def test_cover_doi_matches_the_recorded_zenodo_deposit() -> None:
    """The cover DOI must be the published deposit, not a hand-typed string.

    ``data/zenodo_reservation.json`` records the deposit this release is archived
    as. Cross-checking the rendered identifier against that record is what keeps
    a plausible-looking but wrong DOI off the cover page, and it also catches a
    stale reserved-state placeholder left behind after publication.
    """
    config = yaml.safe_load((REPO / "manuscript" / "config.yaml").read_text())
    publication = config["publication"]
    record = json.loads(
        (REPO / "data" / "zenodo_reservation.json").read_text(encoding="utf-8")
    )

    assert publication["doi"] == record["doi"] == RELEASE_DOI
    assert "doi_status" not in publication, (
        "a reserved-state placeholder must not survive alongside a populated doi"
    )
    # The record tracks whether the deposit is published; the gate does not force
    # a particular state, it forces the record and the rendered surfaces to agree.
    # `resolves` and `submitted` move together, and a published deposit is the
    # only state in which a doi.org link on the cover actually resolves.
    assert record["resolves"] is record["submitted"]
    if not record["submitted"]:
        assert record["state"] == "unsubmitted"
