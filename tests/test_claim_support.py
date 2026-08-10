"""Tests for manuscript claim-level scientific support validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.manuscript.claim_support import (
    ClaimSupportError,
    validate_claim_support,
    write_claim_support_audit,
)

REPO = Path(__file__).resolve().parents[1]


def _fixture(
    tmp_path: Path,
    *,
    manuscript: str,
    support: str,
    bib: str = "@article{source,\n}\n",
    matrix: str = """
sources:
  - key: source
    lane: applications_and_scope
    kind: review
    locator: doi:10.1/example
    role: Source row with enough words to explain support.
""",
) -> tuple[Path, Path, Path, Path]:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_fixture.md").write_text(manuscript, encoding="utf-8")
    bib_path = manuscript_dir / "references.bib"
    bib_path.write_text(bib, encoding="utf-8")
    matrix_path = tmp_path / "scholarship_sources.yaml"
    matrix_path.write_text(matrix, encoding="utf-8")
    support_path = tmp_path / "manuscript_claim_support.yaml"
    support_path.write_text(support, encoding="utf-8")
    return manuscript_dir, support_path, matrix_path, bib_path


def test_claim_support_rejects_anchor_missing_row(tmp_path: Path) -> None:
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:missing -->\nA supported-looking claim.",
        support="claims: []\n",
    )

    with pytest.raises(ClaimSupportError, match="missing rows"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_claim_support_rejects_unsupported_strong_language(tmp_path: Path) -> None:
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:delivery -->\n"
            "The artifact is validated for every possible use."
        ),
        support="""
claims:
  - id: delivery
    type: delivery
    summary: Delivery claim with no strong-word authorization.
    validators: [scripts/example.py]
""",
    )

    with pytest.raises(ClaimSupportError, match="unsupported strong word"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_claim_support_rejects_unsupported_security_language(tmp_path: Path) -> None:
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:security -->\n"
            "The dashboard is secure, government validated, and NSA-approved."
        ),
        support="""
claims:
  - id: security
    type: delivery
    summary: Security claim with no strong-word authorization.
    validators: [scripts/example.py]
""",
    )

    with pytest.raises(ClaimSupportError, match="unsupported strong"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_claim_support_rejects_missing_computed_token(tmp_path: Path) -> None:
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:computed -->\nThe result is produced by a kernel.",
        support="""
claims:
  - id: computed
    type: computed
    summary: Computed claim missing its token.
    claim_tokens: [entropy_fair_coin]
""",
    )

    with pytest.raises(ClaimSupportError, match="missing claim token"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_claim_support_rejects_claim_token_absent_from_registry(tmp_path: Path) -> None:
    """A declared claim token that is not a real kernel claim must fail.

    The token IS present in the manuscript text (so the per-type text check passes),
    isolating the registry cross-check: a YAML row that declares a token the kernels no
    longer emit is a silent provenance drift the text check alone cannot catch.
    """
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:computed -->\n"
            "The value {{claim:ghost_token}} is shown to the learner."
        ),
        support="""
claims:
  - id: computed
    type: computed
    summary: Computed claim whose token no longer exists in the kernels.
    claim_tokens: [ghost_token]
""",
    )

    with pytest.raises(
        ClaimSupportError, match="absent from the kernel claim registry"
    ):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
            registry_claim_ids={"entropy_fair_coin"},
        )


def test_claim_support_accepts_registered_token(tmp_path: Path) -> None:
    """Positive control: a declared token that IS in the registry passes the gate."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:computed -->\n"
            "The value {{claim:entropy_fair_coin}} is shown to the learner."
        ),
        support="""
claims:
  - id: computed
    type: computed
    summary: Computed claim whose token is registered by a kernel.
    claim_tokens: [entropy_fair_coin]
""",
    )

    audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=support_path,
        source_matrix_path=matrix_path,
        bib_path=bib_path,
        registry_claim_ids={"entropy_fair_coin"},
    )
    assert audit.issues() == ()


def test_claim_support_rejects_missing_validator_path(tmp_path: Path) -> None:
    """A path-shaped validator that does not exist on disk must fail."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:delivery -->\nThe delivery step runs in the build.",
        support="""
claims:
  - id: delivery
    type: delivery
    summary: Delivery claim naming a validator script that does not exist.
    validators: [scripts/does_not_exist.py]
""",
    )

    with pytest.raises(ClaimSupportError, match="validator path .* does not exist"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
            project_root=tmp_path,
        )


def test_claim_support_ignores_command_style_validators(tmp_path: Path) -> None:
    """A shell-command validator (e.g. ``uv run pytest``) is not a path and is skipped."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:delivery -->\nThe delivery step runs in the build.",
        support="""
claims:
  - id: delivery
    type: delivery
    summary: Delivery claim whose validator is a command, not a repo path.
    validators: [uv run pytest --cov=src --cov-fail-under=90]
""",
    )

    audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=support_path,
        source_matrix_path=matrix_path,
        bib_path=bib_path,
        project_root=tmp_path,
    )
    assert audit.issues() == ()


def test_real_manuscript_passes_strict_registry_and_validator_gates() -> None:
    """The real manuscript must pass with the production-strict registry + path checks."""
    from src.kernels.examples import build_claim_registry

    audit = validate_claim_support(
        manuscript_dir=REPO / "manuscript",
        support_path=REPO / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=REPO / "data" / "scholarship_sources.yaml",
        bib_path=REPO / "manuscript" / "references.bib",
        registry_claim_ids=build_claim_registry().names(),
        project_root=REPO,
    )
    assert audit.issues() == ()


def test_real_manuscript_claim_support_passes(tmp_path: Path) -> None:
    audit = validate_claim_support(
        manuscript_dir=REPO / "manuscript",
        support_path=REPO / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=REPO / "data" / "scholarship_sources.yaml",
        bib_path=REPO / "manuscript" / "references.bib",
    )
    path = write_claim_support_audit(audit, tmp_path / "claim_support.json")

    payload = audit.to_dict()
    assert audit.issues() == ()
    assert payload["summary"]["claimRows"] >= 50
    assert payload["summary"]["typeCounts"]["computed"] >= 3
    row_ids = {row["id"] for row in payload["rows"]}
    assert "related_skilltree_security_posture" in row_ids
    assert "related_national_security_boundary" in row_ids
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_banned_phrase_list_matches_manuscript() -> None:
    """The curriculum's endorsement blocklist must stay in sync with the manuscript's.

    They are defined separately to keep curriculum free of a manuscript import, so this
    test guards against drift between the two copies.
    """
    from src.curriculum.quality import BANNED_ENDORSEMENT_PHRASES
    from src.manuscript.claim_support import STRONG_PHRASES

    assert set(BANNED_ENDORSEMENT_PHRASES) == set(STRONG_PHRASES)


# --- find_banned_phrases (line 85) -----------------------------------------


def test_find_banned_phrases_detects_and_skips() -> None:
    """The reusable blocklist returns each overreach phrase and nothing for clean text."""
    from src.manuscript.claim_support import find_banned_phrases

    found = find_banned_phrases(
        "This module is NSA approved and government-validated for everyone."
    )
    assert [phrase.lower() for phrase in found] == [
        "nsa approved",
        "government-validated",
    ]
    assert find_banned_phrases("A neutral description with no endorsement words.") == []


def test_find_banned_phrases_resists_whitespace_evasion() -> None:
    """Irregular separators (double space, newline, NBSP) must not evade the blocklist."""
    from src.manuscript.claim_support import find_banned_phrases

    for evasion in ("nsa  approved", "nsa\napproved", "nsa approved"):
        assert find_banned_phrases(f"This is {evasion} for everyone."), evasion


def test_audit_manuscript_banned_phrases_scans_whole_files(tmp_path: Path) -> None:
    """Manuscript-wide scan: a hit anywhere in any .md file is caught; code spans skipped.

    This gives find_banned_phrases a production caller (run_kernels) and closes the
    gap where endorsement phrases outside claim-support anchors were never scanned.
    """
    from src.manuscript.claim_support import audit_manuscript_banned_phrases

    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    # Negative control: an unanchored endorsement phrase in plain prose is flagged.
    (manuscript / "07d_limitations.md").write_text(
        "The platform is NSA approved for all learners.", encoding="utf-8"
    )
    # Clean file plus the same phrase quoted as code (must be skipped).
    (manuscript / "00_abstract.md").write_text(
        "A neutral abstract. The blocklist rejects `nsa approved` strings.",
        encoding="utf-8",
    )
    findings = audit_manuscript_banned_phrases(manuscript)
    assert "07d_limitations.md" in findings
    assert "00_abstract.md" not in findings


# --- load_claim_support structural errors (lines 197, 202, 205, 209) -------


def test_load_claim_support_rejects_non_claims_payload(tmp_path: Path) -> None:
    """A YAML file without a top-level ``claims`` list is rejected."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="A paragraph with no anchors.",
        support="not_claims: 3\n",
    )

    with pytest.raises(ClaimSupportError, match="must contain a claims list"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_load_claim_support_rejects_non_object_row(tmp_path: Path) -> None:
    """A claims entry that is a scalar (not a mapping) is rejected."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="A paragraph with no anchors.",
        support="claims:\n  - just_a_string\n",
    )

    with pytest.raises(ClaimSupportError, match="row 1 must be an object"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_load_claim_support_rejects_duplicate_id(tmp_path: Path) -> None:
    """Two rows sharing an ``id`` is a declaration error."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="A paragraph with no anchors.",
        support="""
claims:
  - id: dup
    type: delivery
    summary: First row.
    validators: [scripts/example.py]
  - id: dup
    type: delivery
    summary: Second row with the same id.
    validators: [scripts/example.py]
""",
    )

    with pytest.raises(ClaimSupportError, match="duplicate claim-support id: dup"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_load_claim_support_rejects_unknown_type(tmp_path: Path) -> None:
    """An unrecognized claim ``type`` is rejected against the valid set."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="A paragraph with no anchors.",
        support="""
claims:
  - id: weird
    type: telepathy
    summary: A claim of an invalid type.
""",
    )

    with pytest.raises(ClaimSupportError, match="type must be one of"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


# --- _string_field / _string_tuple validation (lines 514, 530) -------------


def test_load_claim_support_rejects_blank_summary(tmp_path: Path) -> None:
    """A blank required string field (here ``summary``) is rejected."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="A paragraph with no anchors.",
        support="""
claims:
  - id: blank
    type: delivery
    summary: "   "
    validators: [scripts/example.py]
""",
    )

    with pytest.raises(ClaimSupportError, match="summary must be a string"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_load_claim_support_rejects_non_list_string_tuple(tmp_path: Path) -> None:
    """A list-valued field whose items are not all non-empty strings is rejected."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="A paragraph with no anchors.",
        support="""
claims:
  - id: badtokens
    type: computed
    summary: Computed claim with a malformed claim_tokens field.
    claim_tokens: [1, 2, 3]
""",
    )

    with pytest.raises(
        ClaimSupportError, match="claim_tokens must be a list of strings"
    ):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


# --- audit cross-checks: duplicate anchors, unused rows, section mismatch ---


def test_claim_support_rejects_duplicate_anchors(tmp_path: Path) -> None:
    """The same anchor id appearing in two paragraphs is flagged (line 289)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:delivery -->\nThe delivery step runs in the build here.\n\n"
            "<!-- claim-support:delivery -->\nThe delivery step also runs again later.\n"
        ),
        support="""
claims:
  - id: delivery
    type: delivery
    summary: Delivery claim anchored twice.
    validators: [scripts/example.py]
""",
    )

    with pytest.raises(
        ClaimSupportError, match="duplicate claim-support anchors: delivery"
    ):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_claim_support_rejects_unused_row(tmp_path: Path) -> None:
    """A declared row never anchored in the manuscript is flagged (line 299)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="A paragraph with no anchors at all.",
        support="""
claims:
  - id: orphan
    type: delivery
    summary: Delivery claim that is never anchored anywhere.
    validators: [scripts/example.py]
""",
    )

    with pytest.raises(
        ClaimSupportError, match="rows not anchored in manuscript: orphan"
    ):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_claim_support_rejects_section_mismatch(tmp_path: Path) -> None:
    """A row whose declared section differs from the anchor's file is flagged (line 308)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:delivery -->\nThe delivery step runs in the build.",
        support="""
claims:
  - id: delivery
    type: delivery
    summary: Delivery claim whose declared section is wrong.
    section: 99_other.md
    validators: [scripts/example.py]
""",
    )

    with pytest.raises(ClaimSupportError, match="does not match anchor"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


# --- anchor body fallbacks (lines 368, 370) --------------------------------


def test_anchor_empty_body_uses_next_paragraph(tmp_path: Path) -> None:
    """An anchor with no inline text borrows the following paragraph (line 368).

    The next paragraph supplies the required claim token, so the computed row passes.
    """
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:computed -->\n\n"
            "The standalone follow-on paragraph shows {{claim:entropy_fair_coin}} clearly."
        ),
        support="""
claims:
  - id: computed
    type: computed
    summary: Computed claim whose anchor paragraph is empty.
    claim_tokens: [entropy_fair_coin]
""",
    )

    audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=support_path,
        source_matrix_path=matrix_path,
        bib_path=bib_path,
    )
    assert audit.issues() == ()


def test_anchor_short_body_merges_next_paragraph(tmp_path: Path) -> None:
    """A short anchor body (<8 words) is joined with the next paragraph (line 370)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:computed --> Short lead in.\n\n"
            "Continuation paragraph references {{claim:entropy_fair_coin}} as evidence."
        ),
        support="""
claims:
  - id: computed
    type: computed
    summary: Computed claim whose anchor body is short and merges the next paragraph.
    claim_tokens: [entropy_fair_coin]
""",
    )

    audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=support_path,
        source_matrix_path=matrix_path,
        bib_path=bib_path,
    )
    assert audit.issues() == ()


# --- simulation / literature / scope_limit / delivery / visual branches ----


def test_simulation_row_needs_tokens_or_figures(tmp_path: Path) -> None:
    """A simulation row declaring neither claim_tokens nor figures is flagged (line 411)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:sim -->\nThe simulation produces a deterministic run.",
        support="""
claims:
  - id: sim
    type: simulation
    summary: Simulation row with no tokens and no figures declared.
""",
    )

    with pytest.raises(
        ClaimSupportError, match="simulation row needs claim_tokens or figures"
    ):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_literature_citation_missing_from_matrix_and_bib(tmp_path: Path) -> None:
    """A literature citation present in prose but absent from matrix/bib fails (428, 432)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:lit -->\n"
            "Prior work @ghostref establishes the baseline used throughout this study."
        ),
        support="""
claims:
  - id: lit
    type: literature
    summary: Literature claim citing a key that exists nowhere.
    citations: [ghostref]
""",
    )

    with pytest.raises(ClaimSupportError) as excinfo:
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )
    message = str(excinfo.value)
    assert "ghostref missing from source matrix" in message
    assert "ghostref missing from references.bib" in message


def test_scope_limit_lacks_limitation_marker(tmp_path: Path) -> None:
    """A scope_limit row whose paragraph has no limitation marker is flagged (line 439)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:scope -->\nThe system handles every case we encountered."
        ),
        support="""
claims:
  - id: scope
    type: scope_limit
    summary: Scope claim whose prose contains none of its custom markers.
    limitation_markers: [caveat, restriction]
""",
    )

    with pytest.raises(ClaimSupportError, match="scope_limit lacks limitation marker"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_delivery_row_needs_validators(tmp_path: Path) -> None:
    """A delivery row that declares no validators is flagged (line 444)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:del -->\nThe delivery step ships in the build.",
        support="""
claims:
  - id: del
    type: delivery
    summary: Delivery claim missing its validators list.
""",
    )

    with pytest.raises(ClaimSupportError, match="delivery row needs validators"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_visual_row_missing_figure(tmp_path: Path) -> None:
    """A visual row whose paragraph lacks the required figure reference fails (line 447)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:vis -->\nThe rendered chart appears in the output.",
        support="""
claims:
  - id: vis
    type: visual
    summary: Visual claim requiring a figure that the prose never references.
    figures: [dashboard]
""",
    )

    with pytest.raises(ClaimSupportError, match="missing figure fig:dashboard"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_visual_row_with_figure_passes(tmp_path: Path) -> None:
    """A visual row whose prose references the declared figure passes (branch 445->449)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:vis -->\n"
            "The rendered chart @fig:dashboard appears in the generated output."
        ),
        support="""
claims:
  - id: vis
    type: visual
    summary: Visual claim whose figure reference is present in the prose.
    figures: [dashboard]
""",
    )

    audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=support_path,
        source_matrix_path=matrix_path,
        bib_path=bib_path,
    )
    assert audit.issues() == ()


def test_declared_citation_is_required_for_any_claim_type(tmp_path: Path) -> None:
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:computed -->\n"
            "The value {{claim:entropy_fair_coin}} is shown to the learner."
        ),
        support="""
claims:
  - id: computed
    type: computed
    summary: Computed claim with a declared but absent citation.
    claim_tokens: [entropy_fair_coin]
    citations: [source]
""",
    )

    with pytest.raises(ClaimSupportError, match="missing citation source"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_declared_variable_can_live_in_governed_claim_block(tmp_path: Path) -> None:
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:vis -->\n"
            "The generated table and @fig:dashboard describe the same surface.\n\n"
            "{{dashboard_table}}\n"
        ),
        support="""
claims:
  - id: vis
    type: visual
    summary: Visual claim with a generated table placeholder.
    figures: [dashboard]
    variables: [dashboard_table]
""",
    )

    audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=support_path,
        source_matrix_path=matrix_path,
        bib_path=bib_path,
    )
    assert audit.issues() == ()


def test_literature_row_requires_declared_citations(tmp_path: Path) -> None:
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:lit -->\nThe literature context is asserted.",
        support="""
claims:
  - id: lit
    type: literature
    summary: Literature claim with no citation declaration.
""",
    )

    with pytest.raises(ClaimSupportError, match="literature row needs citations"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_scope_limit_with_citation_missing_from_matrix_and_bib(tmp_path: Path) -> None:
    """A scope_limit row that also cites unknown sources fails on both checks (455, 459)."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:scope -->\n"
            "This boundary is not addressed here; future work @ghostref may extend it."
        ),
        support="""
claims:
  - id: scope
    type: scope_limit
    summary: Scope claim that also cites a key absent from matrix and bib.
    citations: [ghostref]
""",
    )

    with pytest.raises(ClaimSupportError) as excinfo:
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )
    message = str(excinfo.value)
    assert "ghostref missing from source matrix" in message
    assert "ghostref missing from references.bib" in message


def test_descriptive_count_missing_variable(tmp_path: Path) -> None:
    """A descriptive_count row whose declared variable is absent from prose fails."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:count -->\nThe curriculum currently spans many subjects."
        ),
        support="""
claims:
  - id: count
    type: descriptive_count
    summary: Descriptive count whose variable token is missing from prose.
    variables: [skill_total]
""",
    )

    with pytest.raises(
        ClaimSupportError, match="missing manuscript variable skill_total"
    ):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


# --- strong-phrase allow path (branch 476->474) ----------------------------


def test_allowed_strong_phrase_passes(tmp_path: Path) -> None:
    """An authorized strong phrase in ``allow_strong_words`` is permitted (branch 476->474).

    The matrix/bib carry the cited source so the literature checks pass, isolating the
    strong-phrase allow path: the phrase is found but explicitly authorized, so the loop
    continues without raising.
    """
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:lit -->\n"
            "We discuss why a national-security grade label, per @source, is unwarranted."
        ),
        support="""
claims:
  - id: lit
    type: literature
    summary: Literature claim explicitly authorizing one strong phrase.
    citations: [source]
    allow_strong_words: ["national-security grade"]
""",
    )

    audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=support_path,
        source_matrix_path=matrix_path,
        bib_path=bib_path,
    )
    assert audit.issues() == ()


def test_claim_support_rejects_computed_with_empty_token_list(tmp_path: Path) -> None:
    """Negative control (ISC-124): a computed claim with NO declared claim_tokens was
    vacuously consistent (empty - prose == empty), so a bare result could pass unbacked.
    The gate must now fire on the empty declaration itself."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript="<!-- claim-support:computed -->\nThe entropy is 1.6094 nats.",
        support="""
claims:
  - id: computed
    type: computed
    summary: Computed claim with no declared token.
    claim_tokens: []
""",
    )
    with pytest.raises(ClaimSupportError, match="needs ≥1 claim_token"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )


def test_claim_support_rejects_bare_result_number_in_computed_prose(
    tmp_path: Path,
) -> None:
    """Negative control (ISC-125): even with a valid backing token present, a SECOND
    hand-typed result number in the same computed claim's prose must be rejected — a
    declared binding proves one exists, not that none bypassed it."""
    manuscript_dir, support_path, matrix_path, bib_path = _fixture(
        tmp_path,
        manuscript=(
            "<!-- claim-support:computed -->\n"
            "The value {{claim:entropy_fair_coin}} matches, and separately 1.6094 nats."
        ),
        support="""
claims:
  - id: computed
    type: computed
    summary: Computed claim that smuggles a bare result alongside its token.
    claim_tokens: [entropy_fair_coin]
""",
    )
    with pytest.raises(ClaimSupportError, match="hand-typed result"):
        validate_claim_support(
            manuscript_dir=manuscript_dir,
            support_path=support_path,
            source_matrix_path=matrix_path,
            bib_path=bib_path,
        )
