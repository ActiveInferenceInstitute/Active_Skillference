"""Tests for scholarship source coverage validation."""

from __future__ import annotations

import ssl
import threading
import urllib.error
from dataclasses import replace
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from src.kernels.examples import build_claim_registry
from src.manuscript.claim_support import validate_claim_support
from src.scholarship import source_health
from src.scholarship.coverage import (
    EXPECTED_LANES,
    ScholarshipError,
    audit_scholarship,
    parse_bib_keys,
    role_is_claim_specific,
    validate_scholarship,
    write_scholarship_audit,
)
from src.scholarship.gap_report import (
    FRONTIER_SOURCE_CONTRACTS,
    ScholarshipGapError,
    audit_scholarship_gaps,
    validate_scholarship_gaps,
    write_scholarship_gap_report,
)
from src.scholarship.source_health import (
    SourceHealthError,
    audit_source_health,
    validate_source_health,
    write_source_health_audit,
)
from src.scholarship.source_health_report import scholarship_source_health_network

REPO = Path(__file__).resolve().parents[1]

FRONTIER_UPGRADE_SOURCE_KEYS = {
    "leo2024workflow_run_rocrate",
    "bagaev2023reactive_message_passing",
    "bagaev2023rxinfer",
    "fu2025curriculum_aware_gncd",
    "nelson2025coupled_free_energy",
    "rao2024active_predictive_coding",
    "sennesh2024dcpc",
    "hugo2026teacher_development",
    "smith2016softwarecitation",
    "citationfileformat2026",
    "codemeta2026schema",
    "github2026citingcontent",
    "zenodo2026github",
    "reuse2024spec",
}


def _real_claim_support():
    return validate_claim_support(
        manuscript_dir=REPO / "manuscript",
        support_path=REPO / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=REPO / "data" / "scholarship_sources.yaml",
        bib_path=REPO / "manuscript" / "references.bib",
        registry_claim_ids=build_claim_registry().names(),
        project_root=REPO,
    )


def _write_fixture(
    root: Path,
    *,
    manuscript: str,
    bib: str,
    matrix: str,
) -> tuple[Path, Path, Path]:
    manuscript_dir = root / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_fixture.md").write_text(manuscript, encoding="utf-8")
    bib_path = manuscript_dir / "references.bib"
    bib_path.write_text(bib, encoding="utf-8")
    matrix_path = root / "scholarship_sources.yaml"
    matrix_path.write_text(matrix, encoding="utf-8")
    return manuscript_dir, matrix_path, bib_path


def test_parse_bib_keys_extracts_entries() -> None:
    assert parse_bib_keys("@article{a,\n}\n@book{b,\n}\n") == frozenset({"a", "b"})


def test_scholarship_rejects_cited_key_missing_from_matrix(tmp_path: Path) -> None:
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known; @missing].",
        bib="@article{known,\n}\n@article{missing,\n}\n",
        matrix="""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: doi:10.1/example
    role: Known source with a declared support role.
""",
    )

    with pytest.raises(ScholarshipError, match="missing from scholarship matrix"):
        validate_scholarship(manuscript_dir, matrix_path, bib_path)


def test_scholarship_rejects_unused_matrix_entry(tmp_path: Path) -> None:
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n@article{unused,\n}\n",
        matrix="""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: doi:10.1/example
    role: Known source with a declared support role.
  - key: unused
    lane: active_inference_core
    kind: review
    locator: doi:10.2/example
    role: Unused source row that should not certify coverage.
""",
    )

    with pytest.raises(ScholarshipError, match="matrix keys not cited"):
        validate_scholarship(manuscript_dir, matrix_path, bib_path)


def test_scholarship_rejects_uncited_bib_entry(tmp_path: Path) -> None:
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n@article{orphan,\n}\n",
        matrix="""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: doi:10.1/example
    role: Known source with a declared support role.
""",
    )

    with pytest.raises(ScholarshipError, match="references.bib keys not cited"):
        validate_scholarship(manuscript_dir, matrix_path, bib_path)


def test_scholarship_flags_bad_locator_and_terse_role(tmp_path: Path) -> None:
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix="""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: local-note
    role: Too terse.
""",
    )

    audit = audit_scholarship(manuscript_dir, matrix_path, bib_path)

    assert any("locator lacks" in issue for issue in audit.invalid_sources)
    assert any("claim-specific" in issue for issue in audit.invalid_sources)


def test_scholarship_rejects_generic_six_word_role_in_both_validate_paths(
    tmp_path: Path,
) -> None:
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix="""
sources:
  - key: known
    lane: delivery_and_reporting
    kind: primary
    locator: doi:10.1/example
    role: A useful source for this work.
""",
    )

    scholarship_audit = audit_scholarship(manuscript_dir, matrix_path, bib_path)
    assert any("claim-specific" in issue for issue in scholarship_audit.invalid_sources)
    # Red-without / green-with: the previous word-count floor would have let this
    # six-word filler role pass because it is long enough but still lane-generic.
    with pytest.raises(ScholarshipError, match="claim-specific"):
        validate_scholarship(manuscript_dir, matrix_path, bib_path)

    source_health_audit = audit_source_health(matrix_path, bib_path, online=False)
    assert any(
        issue.code == "terse_role" and "claim-specific" in issue.message
        for issue in source_health_audit.issue_list
    )
    with pytest.raises(SourceHealthError, match="terse_role"):
        validate_source_health(matrix_path, bib_path)


def test_scholarship_rejects_single_keyword_stuffing_in_both_validate_paths(
    tmp_path: Path,
) -> None:
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix="""
sources:
  - key: known
    lane: delivery_and_reporting
    kind: primary
    locator: doi:10.1/example
    role: A generic helpful note about reporting things here.
""",
    )

    assert not role_is_claim_specific(
        "delivery_and_reporting",
        "A generic helpful note about reporting things here.",
    )

    source_health_audit = audit_source_health(matrix_path, bib_path, online=False)
    assert any(
        issue.code == "terse_role" and "claim-specific" in issue.message
        for issue in source_health_audit.issue_list
    )

    scholarship_audit = audit_scholarship(manuscript_dir, matrix_path, bib_path)
    assert any("claim-specific" in issue for issue in scholarship_audit.invalid_sources)


def test_real_manuscript_passes_scholarship_coverage() -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    payload = audit.to_dict()

    assert payload["issues"] == []
    assert payload["summary"]["citedSources"] >= 40
    assert payload["summary"]["unusedMatrixEntries"] == 0
    assert payload["summary"]["uncitedBibEntries"] == 0
    assert set(payload["lanes"]) == set(EXPECTED_LANES)
    assert all(payload["lanes"][lane]["citedSources"] > 0 for lane in EXPECTED_LANES)


def test_active_inference_institute_open_education_sources_are_covered() -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    payload = audit.to_dict()
    required = {
        "activeinferenceinstitute2026home",
        "activeinferenceinstitute2026courses",
        "activeinferenceinstitute2026start",
    }

    assert required <= set(payload["sources"])
    assert required <= set(audit.bib_keys)
    cited = {key for section in payload["sections"] for key in section["citations"]}
    assert required <= cited
    assert all(
        payload["sources"][key]["locator"].startswith("url:") for key in required
    )


def test_current_review_and_critique_sources_are_covered() -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    payload = audit.to_dict()
    required = {
        "sprevak2023predictive",
        "zhang2024overview",
        "aguilera2022particular",
        "aguilera2023confederation",
        "hodson2024empirical",
        "isomura2023experimental",
        "gershman2019free",
    }
    cited = {key for section in payload["sections"] for key in section["citations"]}

    assert required <= set(payload["sources"])
    assert required <= set(audit.bib_keys)
    assert required <= cited
    assert all(
        payload["sources"][key]["locator"].startswith("doi:") for key in required
    )


def test_expected_free_energy_unification_source_is_covered() -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    payload = audit.to_dict()
    required = {"champion2026reframing"}
    cited = {key for section in payload["sections"] for key in section["citations"]}

    assert required <= set(payload["sources"])
    assert required <= set(audit.bib_keys)
    assert required <= cited
    assert payload["sources"]["champion2026reframing"]["locator"].startswith("doi:")
    assert "Expected-free-energy" in payload["sources"]["champion2026reframing"]["role"]


def test_accessibility_guidance_sources_are_covered() -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    payload = audit.to_dict()
    required = {"acm2023accessiblefigures", "section508alttext"}
    cited = {key for section in payload["sections"] for key in section["citations"]}

    assert required <= set(payload["sources"])
    assert required <= set(audit.bib_keys)
    assert required <= cited
    assert all(
        payload["sources"][key]["locator"].startswith("url:") for key in required
    )


def test_nsa_skilltree_and_security_posture_sources_are_covered() -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    payload = audit.to_dict()
    required = {
        "skilltree2020nsa",
        "skilltree2026github",
        "nsa2026opensource",
        "nist2020zerotrust",
        "slsa2026framework",
        "sigstore2026overview",
        "cisa2026sbom",
        "mitre2026attack",
    }
    cited = {key for section in payload["sections"] for key in section["citations"]}

    assert required <= set(payload["sources"])
    assert required <= set(audit.bib_keys)
    assert required <= cited
    assert "National Security Agency" in payload["sources"]["skilltree2020nsa"]["role"]
    assert (
        "National Security Agency" in payload["sources"]["skilltree2026github"]["role"]
    )
    assert payload["sources"]["nist2020zerotrust"]["locator"].startswith("url:")


def test_report_recommended_scholarship_frontier_sources_are_contracts() -> None:
    expected = {
        "groth2013prov_overview",
        "moreau2013prov_dm",
        "doignon1985knowledge_spaces",
        "falmagne2011learning_spaces",
        "biggs1996constructive_alignment",
        "black1998assessment",
        "shute2008formative_feedback",
        "designbasedresearchcollective2003",
        "barab2004design_based",
        "sandve2013reproducible",
        "wilson2014scientific_computing",
        "munafo2017reproducible_science",
        *FRONTIER_UPGRADE_SOURCE_KEYS,
    }

    assert expected <= {contract.source_key for contract in FRONTIER_SOURCE_CONTRACTS}


def test_frontier_scholarship_upgrade_sources_are_contract_bound() -> None:
    scholarship = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    claim_support = _real_claim_support()
    report = validate_scholarship_gaps(
        scholarship,
        claim_support,
        REPO / "manuscript" / "references.bib",
    )
    payload = scholarship.to_dict()
    cited = {key for section in payload["sections"] for key in section["citations"]}
    contract_keys = {contract.source_key for contract in FRONTIER_SOURCE_CONTRACTS}
    support_rows_by_key = {
        citation: row.claim_id
        for row in claim_support.rows
        for citation in row.citations
        if citation in FRONTIER_UPGRADE_SOURCE_KEYS
    }
    frontier_rows = {
        row["sourceKey"]: row for row in report.to_dict()["frontierSources"]
    }

    assert FRONTIER_UPGRADE_SOURCE_KEYS <= set(payload["sources"])
    assert FRONTIER_UPGRADE_SOURCE_KEYS <= set(scholarship.bib_keys)
    assert FRONTIER_UPGRADE_SOURCE_KEYS <= cited
    assert FRONTIER_UPGRADE_SOURCE_KEYS <= contract_keys
    assert FRONTIER_UPGRADE_SOURCE_KEYS <= set(support_rows_by_key)
    assert FRONTIER_UPGRADE_SOURCE_KEYS <= set(frontier_rows)
    assert all(
        frontier_rows[key]["boundarySupported"] for key in FRONTIER_UPGRADE_SOURCE_KEYS
    )
    assert all(
        frontier_rows[key]["supportRows"] for key in FRONTIER_UPGRADE_SOURCE_KEYS
    )


def test_scholarship_frontier_gap_report_passes_and_writes() -> None:
    scholarship = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    claim_support = _real_claim_support()

    report = validate_scholarship_gaps(
        scholarship,
        claim_support,
        REPO / "manuscript" / "references.bib",
    )
    payload = report.to_dict()

    assert payload["issues"] == []
    assert payload["summary"]["frontierSources"] == len(FRONTIER_SOURCE_CONTRACTS)
    assert {row["sourceKey"] for row in payload["frontierSources"]} == {
        contract.source_key for contract in FRONTIER_SOURCE_CONTRACTS
    }
    assert all(row["presentInMatrix"] for row in payload["frontierSources"])
    assert all(row["presentInBib"] for row in payload["frontierSources"])
    assert all(row["citedInManuscript"] for row in payload["frontierSources"])


def test_scholarship_frontier_gap_report_is_deterministic(tmp_path: Path) -> None:
    scholarship = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    report = validate_scholarship_gaps(
        scholarship,
        _real_claim_support(),
        REPO / "manuscript" / "references.bib",
    )

    out = write_scholarship_gap_report(report, tmp_path / "gap.json")
    payload = out.read_text(encoding="utf-8")

    assert '"frontierSources"' in payload
    assert '"blockingIssues": 0' in payload
    assert payload.endswith("\n")


def test_scholarship_source_health_network_separates_issue_classes() -> None:
    scholarship = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    source_health_audit = validate_source_health(
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    gap_report = validate_scholarship_gaps(
        scholarship,
        _real_claim_support(),
        REPO / "manuscript" / "references.bib",
    )

    payload = scholarship_source_health_network(
        scholarship=scholarship,
        source_health=source_health_audit,
        gap_report=gap_report,
    )

    assert payload["summary"]["sources"] >= 58
    assert payload["summary"]["deadLinks"] == 0
    assert payload["summary"]["botBlocks"] == 0
    assert payload["summary"]["roleGaps"] == 0
    assert payload["boundarySources"]
    assert set(payload["uncitedDrift"]) == {
        "singleSectionWithoutClaimSupport",
        "uncitedBibEntries",
        "underweightedLanes",
        "unusedMatrixEntries",
    }


def test_scholarship_gap_report_rejects_missing_frontier_source() -> None:
    scholarship = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    missing_key = FRONTIER_SOURCE_CONTRACTS[0].source_key
    corrupted = replace(
        scholarship,
        sources={
            key: source
            for key, source in scholarship.sources.items()
            if key != missing_key
        },
    )

    with pytest.raises(ScholarshipGapError, match="missing source matrix row"):
        validate_scholarship_gaps(
            corrupted,
            _real_claim_support(),
            REPO / "manuscript" / "references.bib",
        )


def test_scholarship_gap_report_rejects_unbound_frontier_claim() -> None:
    scholarship = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    missing_key = "w3c2023wcag22"
    claim_support = _real_claim_support()
    corrupted = replace(
        claim_support,
        rows=tuple(
            replace(
                row,
                citations=tuple(
                    citation for citation in row.citations if citation != missing_key
                ),
            )
            for row in claim_support.rows
        ),
    )
    report = audit_scholarship_gaps(
        scholarship,
        corrupted,
        REPO / "manuscript" / "references.bib",
    )

    assert any("required claim-support" in issue for issue in report.issues())
    with pytest.raises(ScholarshipGapError, match="required claim-support"):
        validate_scholarship_gaps(
            scholarship,
            corrupted,
            REPO / "manuscript" / "references.bib",
        )


def test_real_scholarship_sources_pass_offline_health_check() -> None:
    audit = validate_source_health(
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )

    assert audit.to_dict()["summary"]["issueCount"] == 0
    assert audit.source_count >= 58


def test_real_scholarship_roles_pass_stronger_claim_specificity_gate() -> None:
    source_health_audit = audit_source_health(
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
        online=False,
    )
    scholarship_audit = audit_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )

    role_issues = [
        issue for issue in source_health_audit.issue_list if issue.code == "terse_role"
    ]
    claim_specificity_failures = [
        issue
        for issue in scholarship_audit.invalid_sources
        if "claim-specific" in issue
    ]

    assert role_issues == []
    assert claim_specificity_failures == []


def test_source_health_rejects_weak_locator_and_terse_role(tmp_path: Path) -> None:
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix="""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: local-note
    role: Too terse.
""",
    )

    assert manuscript_dir.exists()
    with pytest.raises(SourceHealthError, match="weak_locator"):
        validate_source_health(matrix_path, bib_path)


def test_role_is_claim_specific_requires_a_lane_relevant_token() -> None:
    # Two lane-relevant tokens pass.
    assert role_is_claim_specific(
        "active_inference_core",
        "Tutorial on active-inference policy decomposition.",
    )
    # Generic filler with no lane token is flagged.
    assert not role_is_claim_specific(
        "delivery_and_reporting",
        "A generic helpful note about things here.",
    )
    # Off-topic roles with many distinct but lane-irrelevant words are still flagged.
    assert not role_is_claim_specific(
        "delivery_and_reporting",
        "Some random words completely unrelated to anything meaningful today.",
    )


def test_source_health_records_online_timeouts_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix="""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: url:https://example.invalid/source
    role: Perception source supporting Bayesian inference framing.
""",
    )

    def _raise_timeout(*_args: object, **_kwargs: object) -> None:
        raise TimeoutError("The read operation timed out")

    monkeypatch.setattr(source_health.urllib.request, "urlopen", _raise_timeout)
    audit = audit_source_health(matrix_path, bib_path, online=True, timeout=0.01)

    assert audit.online_results["known"] == "timeout:read"
    assert any("unreachable" in issue for issue in audit.issues())


def test_source_health_strict_online_rejects_404_but_tolerates_403(
    tmp_path: Path,
    httpserver,
) -> None:
    # Real local HTTP endpoints exercise the internal ``_check_url`` directly:
    # a HEAD 404 is a genuine dead link (strict-fatal "unreachable"); a HEAD 403 is
    # a publisher bot-block (tolerated "blocked"). ``allow_private=True`` lets the
    # audit reach the loopback test server, matching the sibling ``_check_url_*``
    # real-server tests.
    httpserver.expect_request("/dead", method="HEAD").respond_with_data("", status=404)
    httpserver.expect_request("/blocked", method="HEAD").respond_with_data(
        "", status=403
    )

    dead_root = tmp_path / "dead"
    dead_root.mkdir()
    _dead_dir, dead_matrix, dead_bib = _write_fixture(
        dead_root,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix(httpserver.url_for("/dead")),
    )
    dead_audit = audit_source_health(
        dead_matrix, dead_bib, online=True, timeout=5.0, allow_private=True
    )
    assert dead_audit.online_results["known"] == "http_error:404"
    assert any(issue.code == "unreachable" for issue in dead_audit.issue_list)
    with pytest.raises(SourceHealthError, match="unreachable"):
        validate_source_health(
            dead_matrix,
            dead_bib,
            online=True,
            strict_online=True,
            timeout=5.0,
            allow_private=True,
        )

    blocked_root = tmp_path / "blocked"
    blocked_root.mkdir()
    _blocked_dir, blocked_matrix, blocked_bib = _write_fixture(
        blocked_root,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix(httpserver.url_for("/blocked")),
    )
    audit = validate_source_health(
        blocked_matrix,
        blocked_bib,
        online=True,
        strict_online=True,
        timeout=5.0,
        allow_private=True,
    )

    assert audit.online_results["known"] == "http_error:403"
    assert any(issue.code == "blocked" for issue in audit.issue_list)


def test_source_health_online_validation_tolerates_publisher_blocks(
    tmp_path: Path,
    httpserver,
) -> None:
    # Real HEAD 403 endpoint exercises non-strict online validation directly.
    # records the publisher block as a "blocked" issue but does not raise.
    httpserver.expect_request("/source", method="HEAD").respond_with_data(
        "", status=403
    )
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix(httpserver.url_for("/source")),
    )

    audit = validate_source_health(
        matrix_path, bib_path, online=True, timeout=5.0, allow_private=True
    )

    assert audit.online_results["known"] == "http_error:403"
    assert any(issue.code == "blocked" for issue in audit.issue_list)


def test_source_health_blocks_loopback_url_before_network_fetch(
    tmp_path: Path,
) -> None:
    hits: list[str] = []

    class ProbeHandler(BaseHTTPRequestHandler):
        def do_HEAD(self) -> None:
            hits.append(self.path)
            self.send_response(HTTPStatus.OK)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), ProbeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        _manuscript_dir, matrix_path, bib_path = _write_fixture(
            tmp_path,
            manuscript="Claim [@known].",
            bib="@article{known,\n}\n",
            matrix=f"""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: url:http://{host}:{port}/internal-probe
    role: Perception source supporting Bayesian inference framing.
""",
        )
        audit = audit_source_health(matrix_path, bib_path, online=True, timeout=0.1)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert hits == []
    assert audit.online_results["known"] == "blocked_url:private_address"
    assert any(issue.code == "forbidden_locator" for issue in audit.issue_list)
    with pytest.raises(SourceHealthError, match="forbidden_locator"):
        validate_source_health(
            matrix_path,
            bib_path,
            online=True,
            strict_online=True,
            timeout=0.1,
        )


def test_write_scholarship_audit_emits_deterministic_json(tmp_path: Path) -> None:
    audit = validate_scholarship(
        REPO / "manuscript",
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
    )
    path = write_scholarship_audit(audit, tmp_path / "audit.json")

    assert path.read_text(encoding="utf-8").endswith("\n")
    assert '"scholarship_coverage"' not in path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# coverage.py: malformed-matrix and invalid-source branches
# ---------------------------------------------------------------------------


def test_load_source_matrix_rejects_non_mapping_payload(tmp_path: Path) -> None:
    matrix_path = tmp_path / "scholarship_sources.yaml"
    matrix_path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(ScholarshipError, match="top-level sources list"):
        source_health.load_source_matrix(matrix_path)


def test_load_source_matrix_rejects_non_mapping_row(tmp_path: Path) -> None:
    matrix_path = tmp_path / "scholarship_sources.yaml"
    matrix_path.write_text(
        "sources:\n  - just-a-string\n",
        encoding="utf-8",
    )

    with pytest.raises(ScholarshipError, match=r"sources\[1\] must be a mapping"):
        source_health.load_source_matrix(matrix_path)


def test_load_source_matrix_rejects_blank_string_field(tmp_path: Path) -> None:
    matrix_path = tmp_path / "scholarship_sources.yaml"
    matrix_path.write_text(
        """
sources:
  - key: "   "
    lane: perception_as_inference
    kind: primary
    locator: doi:10.1/example
    role: Perception source supporting Bayesian inference framing.
""",
        encoding="utf-8",
    )

    with pytest.raises(ScholarshipError, match=r"sources\[1\].key must be a non-empty"):
        source_health.load_source_matrix(matrix_path)


def test_load_source_matrix_rejects_duplicate_keys(tmp_path: Path) -> None:
    matrix_path = tmp_path / "scholarship_sources.yaml"
    matrix_path.write_text(
        """
sources:
  - key: dup
    lane: perception_as_inference
    kind: primary
    locator: doi:10.1/example
    role: Perception source supporting Bayesian inference framing.
  - key: dup
    lane: active_inference_core
    kind: review
    locator: doi:10.2/example
    role: Active-inference policy review of free-energy methods.
""",
        encoding="utf-8",
    )

    with pytest.raises(
        ScholarshipError, match="duplicate scholarship matrix keys: dup"
    ):
        source_health.load_source_matrix(matrix_path)


def test_audit_scholarship_flags_unknown_lane_and_kind(tmp_path: Path) -> None:
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix="""
sources:
  - key: known
    lane: not_a_real_lane
    kind: not_a_real_kind
    locator: doi:10.1/example
    role: Perception source supporting Bayesian inference framing.
""",
    )

    audit = audit_scholarship(manuscript_dir, matrix_path, bib_path)

    assert any("unknown lane 'not_a_real_lane'" in row for row in audit.invalid_sources)
    assert any("unknown kind 'not_a_real_kind'" in row for row in audit.invalid_sources)


def test_audit_issues_report_missing_and_matrix_missing_bib(tmp_path: Path) -> None:
    # 'missing' is cited + in matrix but absent from references.bib -> missing_bib_entries.
    # 'ghost' is in the matrix but absent from references.bib -> matrix_entries_missing_bib.
    manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known; @missing].",
        bib="@article{known,\n}\n",
        matrix="""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: doi:10.1/example
    role: Perception source supporting Bayesian inference framing.
  - key: missing
    lane: active_inference_core
    kind: review
    locator: doi:10.2/example
    role: Active-inference policy review of free-energy methods.
  - key: ghost
    lane: active_inference_core
    kind: review
    locator: doi:10.3/example
    role: Active-inference policy review of free-energy methods.
""",
    )

    audit = audit_scholarship(manuscript_dir, matrix_path, bib_path)
    messages = audit.issues()

    assert "missing" in audit.missing_bib_entries
    assert "ghost" in audit.matrix_entries_missing_bib
    assert any(
        "cited keys missing from references.bib" in message for message in messages
    )
    assert any(
        "matrix keys missing from references.bib" in message for message in messages
    )


# ---------------------------------------------------------------------------
# source_health.py: offline-issue branches
# ---------------------------------------------------------------------------


def test_audit_source_health_flags_missing_bib_key(tmp_path: Path) -> None:
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{other,\n}\n",
        matrix="""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: doi:10.1/example
    role: Perception source supporting Bayesian inference framing.
""",
    )

    audit = audit_source_health(matrix_path, bib_path, online=False)

    assert any(
        issue.code == "missing_bib" and issue.key == "known"
        for issue in audit.issue_list
    )


def test_audit_source_health_flags_documentation_without_url(tmp_path: Path) -> None:
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix="""
sources:
  - key: known
    lane: delivery_and_reporting
    kind: documentation
    locator: doi:10.1/example
    role: Documentation describing the reporting dashboard provenance metadata.
""",
    )

    audit = audit_source_health(matrix_path, bib_path, online=False)

    assert any(
        issue.code == "documentation_locator" and issue.key == "known"
        for issue in audit.issue_list
    )


def test_validate_source_health_strict_requires_online() -> None:
    with pytest.raises(ValueError, match="strict_online requires online=True"):
        validate_source_health(
            REPO / "data" / "scholarship_sources.yaml",
            REPO / "manuscript" / "references.bib",
            online=False,
            strict_online=True,
        )


def test_write_source_health_audit_emits_sorted_json(tmp_path: Path) -> None:
    audit = audit_source_health(
        REPO / "data" / "scholarship_sources.yaml",
        REPO / "manuscript" / "references.bib",
        online=False,
    )
    out = tmp_path / "nested" / "health.json"

    path = write_source_health_audit(audit, out)
    text = path.read_text(encoding="utf-8")

    assert path == out
    assert path.exists()
    assert text.endswith("\n")
    import json

    payload = json.loads(text)
    assert payload["checkedOnline"] is False
    assert payload["summary"]["sources"] == audit.source_count


# ---------------------------------------------------------------------------
# source_health.py: real local HTTP via pytest-httpserver
# ---------------------------------------------------------------------------


def _health_matrix(url: str) -> str:
    return f"""
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: url:{url}
    role: Perception source supporting Bayesian inference framing.
"""


def test_check_url_ok_via_real_head_server(tmp_path: Path, httpserver) -> None:
    httpserver.expect_request("/source", method="HEAD").respond_with_data(
        "", status=200
    )
    url = httpserver.url_for("/source")
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix(url),
    )

    audit = audit_source_health(
        matrix_path,
        bib_path,
        online=True,
        timeout=5.0,
        allow_private=True,
    )

    assert audit.online_results["known"] == "ok:200"
    # ok status produces no online issue (124->87 / 236 branch).
    assert not any(
        issue.key == "known" and issue.code == "ok" for issue in audit.issue_list
    )
    assert "known" not in {
        issue.key
        for issue in audit.issue_list
        if issue.code in {"unreachable", "blocked", "unreachable_timeout"}
    }


def test_check_url_405_head_falls_back_to_get(tmp_path: Path, httpserver) -> None:
    httpserver.expect_request("/source", method="HEAD").respond_with_data(
        "", status=405
    )
    httpserver.expect_request("/source", method="GET").respond_with_data(
        "body", status=200
    )
    url = httpserver.url_for("/source")
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix(url),
    )

    audit = audit_source_health(
        matrix_path,
        bib_path,
        online=True,
        timeout=5.0,
        allow_private=True,
    )

    assert audit.online_results["known"] == "ok:200"


def test_check_url_405_then_get_404_reports_http_error(
    tmp_path: Path, httpserver
) -> None:
    httpserver.expect_request("/source", method="HEAD").respond_with_data(
        "", status=405
    )
    httpserver.expect_request("/source", method="GET").respond_with_data(
        "missing", status=404
    )
    url = httpserver.url_for("/source")
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix(url),
    )

    audit = audit_source_health(
        matrix_path,
        bib_path,
        online=True,
        timeout=5.0,
        allow_private=True,
    )

    assert audit.online_results["known"] == "http_error:404"
    assert any(issue.code == "unreachable" for issue in audit.issue_list)


def test_check_url_http_500_reports_unreachable(tmp_path: Path, httpserver) -> None:
    httpserver.expect_request("/source", method="HEAD").respond_with_data(
        "", status=500
    )
    url = httpserver.url_for("/source")
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix(url),
    )

    audit = audit_source_health(
        matrix_path,
        bib_path,
        online=True,
        timeout=5.0,
        allow_private=True,
    )

    assert audit.online_results["known"] == "http_error:500"
    assert any(issue.code == "unreachable" for issue in audit.issue_list)


def test_check_url_403_reports_blocked(tmp_path: Path, httpserver) -> None:
    httpserver.expect_request("/source", method="HEAD").respond_with_data(
        "", status=403
    )
    url = httpserver.url_for("/source")
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix(url),
    )

    audit = audit_source_health(
        matrix_path,
        bib_path,
        online=True,
        timeout=5.0,
        allow_private=True,
    )

    assert audit.online_results["known"] == "http_error:403"
    assert any(issue.code == "blocked" for issue in audit.issue_list)


def test_check_url_connection_refused_reports_url_error(tmp_path: Path) -> None:
    # Port 1 is reserved/closed: a real connection attempt raises URLError.
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=_health_matrix("http://127.0.0.1:1/source"),
    )

    audit = audit_source_health(
        matrix_path,
        bib_path,
        online=True,
        timeout=2.0,
        allow_private=True,
    )

    assert audit.online_results["known"].startswith("url_error:")
    assert any(issue.code == "unreachable" for issue in audit.issue_list)


def test_locator_url_construction_for_doi_and_url() -> None:
    # doi: locators expand to the canonical doi.org resolver URL (line 182 branch).
    assert (
        source_health._locator_url("doi:10.5555/example")
        == "https://doi.org/10.5555/example"
    )
    # url: locators strip the scheme prefix and pass the raw URL through.
    assert (
        source_health._locator_url("url:https://example.org/page")
        == "https://example.org/page"
    )


def test_audit_source_health_checks_doi_locator_online(
    tmp_path: Path, httpserver
) -> None:
    # A doi: locator drives audit_source_health through _locator_url's doi.org branch.
    # We monkeypatch only the pure URL builder to redirect doi.org to a real local
    # server (matching the existing tests' monkeypatch-of-real-callables pattern),
    # so the actual HTTP round-trip still happens against a live socket.
    httpserver.expect_request("/resolved", method="HEAD").respond_with_data(
        "", status=200
    )
    local_url = httpserver.url_for("/resolved")
    matrix = """
sources:
  - key: known
    lane: perception_as_inference
    kind: primary
    locator: doi:10.5555/example
    role: Perception source supporting Bayesian inference framing.
"""
    _manuscript_dir, matrix_path, bib_path = _write_fixture(
        tmp_path,
        manuscript="Claim [@known].",
        bib="@article{known,\n}\n",
        matrix=matrix,
    )

    import pytest as _pytest

    real_builder = source_health._locator_url

    def _redirect_doi(locator: str) -> str:
        assert real_builder(locator) == "https://doi.org/10.5555/example"
        return local_url

    monkeypatch = _pytest.MonkeyPatch()
    monkeypatch.setattr(source_health, "_locator_url", _redirect_doi)
    try:
        audit = audit_source_health(
            matrix_path,
            bib_path,
            online=True,
            timeout=5.0,
            allow_private=True,
        )
    finally:
        monkeypatch.undo()

    assert audit.online_results["known"] == "ok:200"


def test_online_issue_for_status_classifies_each_status() -> None:
    issue_for = source_health._online_issue_for_status

    assert issue_for("k", "ok:200") is None
    assert issue_for("k", "http_error:403").code == "blocked"
    assert issue_for("k", "timeout:read").code == "unreachable_timeout"
    assert issue_for("k", "timeout:socket").code == "unreachable_timeout"
    assert issue_for("k", "http_error:404").code == "unreachable"
    assert issue_for("k", "http_error:500").code == "unreachable"
    assert issue_for("k", "url_error:boom").code == "unreachable"
    assert issue_for("k", "os_error:OSError:boom").code == "unreachable"
    assert issue_for("k", "tls_error:boom").code == "unreachable"
    # Unrecognized status (e.g. a 3xx http_error) hits the final fallback (line 257).
    fallback = issue_for("k", "http_error:301")
    assert fallback is not None
    assert fallback.code == "unreachable"
    assert fallback.message == "http_error:301"


def _expect_status(
    monkeypatch: pytest.MonkeyPatch, exc: BaseException, *, method: str = "HEAD"
) -> str:
    """Drive _check_url with urlopen raising a real exception, return the status."""

    def _raise(*_args: object, **_kwargs: object) -> None:
        raise exc

    monkeypatch.setattr(source_health.urllib.request, "urlopen", _raise)
    return source_health._check_url("https://example.invalid/x", timeout=0.01)


def test_check_url_head_url_error(monkeypatch: pytest.MonkeyPatch) -> None:
    status = _expect_status(monkeypatch, urllib.error.URLError("no route"))
    assert status.startswith("url_error:")


def _ssl_error_with_reason() -> ssl.SSLError:
    """A real ssl.SSLError carries a .reason; bare instances do not, so set it."""
    exc = ssl.SSLError("bad cert")
    exc.reason = "CERTIFICATE_VERIFY_FAILED"
    return exc


def test_check_url_head_ssl_error(monkeypatch: pytest.MonkeyPatch) -> None:
    status = _expect_status(monkeypatch, _ssl_error_with_reason())
    assert status == "tls_error:CERTIFICATE_VERIFY_FAILED"


def test_check_url_head_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    status = _expect_status(monkeypatch, ConnectionResetError("reset by peer"))
    assert status.startswith("os_error:ConnectionResetError:")


def test_check_url_get_exception_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    # _check_url_get is reached when HEAD returns 405; once there, every socket-level
    # exception maps to the same status vocabulary as the HEAD path.
    def _make(exc: BaseException):
        def _raise(*_args: object, **_kwargs: object) -> None:
            raise exc

        return _raise

    monkeypatch.setattr(
        source_health.urllib.request,
        "urlopen",
        _make(TimeoutError("read timed out")),
    )
    assert (
        source_health._check_url_get("https://x.invalid/y", timeout=0.01)
        == "timeout:read"
    )

    monkeypatch.setattr(
        source_health.urllib.request,
        "urlopen",
        _make(urllib.error.URLError("down")),
    )
    assert source_health._check_url_get("https://x.invalid/y", timeout=0.01).startswith(
        "url_error:"
    )

    tls = ssl.SSLError("tls")
    tls.reason = "HANDSHAKE_FAILURE"
    monkeypatch.setattr(source_health.urllib.request, "urlopen", _make(tls))
    assert (
        source_health._check_url_get("https://x.invalid/y", timeout=0.01)
        == "tls_error:HANDSHAKE_FAILURE"
    )

    monkeypatch.setattr(
        source_health.urllib.request,
        "urlopen",
        _make(ConnectionAbortedError("aborted")),
    )
    assert source_health._check_url_get("https://x.invalid/y", timeout=0.01).startswith(
        "os_error:ConnectionAbortedError:"
    )


def test_check_url_get_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args: object, **_kwargs: object) -> None:
        raise urllib.error.HTTPError(
            "https://x.invalid/y", 404, "Not Found", hdrs=None, fp=None
        )

    monkeypatch.setattr(source_health.urllib.request, "urlopen", _raise)
    assert source_health._check_url_get("https://x.invalid/y", timeout=0.01) == (
        "http_error:404"
    )


def test_role_gate_rejects_lane_name_padding() -> None:
    """Negative control (ISC-128): a role echoing only the lane id's words (no curated
    content keywords) was vacuously accepted when lane-name tokens padded the count."""
    from src.scholarship.coverage import role_is_claim_specific

    assert (
        role_is_claim_specific(
            "mathematical_foundations", "Mathematical foundations here."
        )
        is False
    )
    # A role naming real curated content still passes.
    assert (
        role_is_claim_specific(
            "mathematical_foundations",
            "Probability and entropy foundations for the curriculum.",
        )
        is True
    )
