"""Tests for manuscript language-variety contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.manuscript.american_english import (
    BRITISH_TO_AMERICAN,
    AmericanEnglishError,
    audit_american_english,
    validate_american_english,
)

REPO = Path(__file__).resolve().parents[1]


def _audit_prose(tmp_path: Path, prose: str) -> dict[str, str]:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(exist_ok=True)
    (manuscript / "00_abstract.md").write_text(prose, encoding="utf-8")
    return {
        issue.found: issue.suggestion for issue in audit_american_english(manuscript)
    }


def test_american_english_rejects_british_spelling_variants(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(
        "This modelling note uses colour to describe self-organisation.\n",
        encoding="utf-8",
    )

    issues = audit_american_english(manuscript)

    assert {issue.found for issue in issues} == {
        "modelling",
        "colour",
        "self-organisation",
    }
    with pytest.raises(AmericanEnglishError, match="British spelling"):
        validate_american_english(manuscript)


def test_american_english_ignores_code_spans_and_reference_section(
    tmp_path: Path,
) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(
        "Use `colour` only as a literal code token.\n",
        encoding="utf-8",
    )
    (manuscript / "99_references.md").write_text(
        "A cited title may preserve British modelling terminology.\n",
        encoding="utf-8",
    )

    validate_american_english(manuscript)


def test_american_english_detects_suffix_variants_without_false_positives(
    tmp_path: Path,
) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(
        "We minimise loss near the centre and honour the constraint.\n"
        "A travelling agent updates size, secure storage, and genre labels.\n"
        "Use `minimise` only in a code span.\n"
        "Cite @honour without linting the key token.\n",
        encoding="utf-8",
    )

    issues = audit_american_english(manuscript)
    suggestions = {issue.found: issue.suggestion for issue in issues}

    assert suggestions["minimise"] == "minimize"
    assert suggestions["honour"] == "honor"
    assert suggestions["travelling"] == "traveling"
    assert suggestions["centre"] == "center"
    assert "size" not in suggestions
    assert "secure" not in suggestions
    assert "genre" not in suggestions


def test_american_english_closed_list_avoids_false_positives_and_catches_british_words(
    tmp_path: Path,
) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    american_words = (
        "size",
        "prize",
        "surprise",
        "exercise",
        "comprise",
        "wise",
        "devise",
        "advertise",
        "enterprise",
        "secure",
        "pure",
        "genre",
        "acre",
        "sincere",
        "severe",
        "here",
        "core",
        "store",
        "more",
        "before",
        "nature",
        "future",
        "feature",
        "measure",
        "pressure",
        "figure",
        "advise",
        "supervise",
        "revise",
        "premise",
        "promise",
        "raise",
        "otherwise",
        "four",
        "tour",
        "pour",
        "contour",
        "detour",
        "sour",
        "scour",
        "ogre",
        "massacre",
        "mediocre",
    )
    british_words = (
        "colour",
        "behaviour",
        "honour",
        "defence",
        "licence",
        "programme",
        "grey",
        "organise",
        "analyse",
        "minimise",
        "optimise",
        "normalisation",
        "travelling",
        "modelling",
        "centre",
        "metre",
        "litre",
        "fibre",
        "aluminium",
        "catalogue",
        "generalised",
        "recognised",
        "specialised",
        "whilst",
        "towards",
    )
    (manuscript / "00_abstract.md").write_text(
        "American corpus: "
        + " ".join(american_words)
        + ".\nBritish corpus: "
        + " ".join(british_words)
        + ".\n",
        encoding="utf-8",
    )

    issues = audit_american_english(manuscript)
    flagged = {issue.found for issue in issues}

    assert flagged.isdisjoint(american_words)
    assert flagged == set(british_words)


def test_american_english_detects_neighbour(tmp_path: Path) -> None:
    suggestions = _audit_prose(
        tmp_path,
        "Each node updates the unobserved neighbour from its prior belief.\n",
    )

    assert suggestions["neighbour"] == "neighbor"


def test_american_english_detects_added_our_and_ce_variants(tmp_path: Path) -> None:
    suggestions = _audit_prose(
        tmp_path,
        "Neighbouring nodes in the neighbourhood favour a rigour we endeavour "
        "to keep.\nThe defences and offence sections describe behaviourally "
        "coloured labour.\n",
    )

    assert suggestions == {
        "Neighbouring": "Neighboring",
        "neighbourhood": "neighborhood",
        "favour": "favor",
        "rigour": "rigor",
        "endeavour": "endeavor",
        "defences": "defenses",
        "offence": "offense",
        "behaviourally": "behaviorally",
        "coloured": "colored",
        "labour": "labor",
    }


def test_american_english_detects_added_ise_families(tmp_path: Path) -> None:
    suggestions = _audit_prose(
        tmp_path,
        "We marginalise nuisance states, factorised the posterior, and "
        "discretising time.\nThe run visualises artefacts, randomised items, "
        "and a serialisation of the graph.\nWe maximise reward, recognise the "
        "bound, generalise the result, and specialise the path.\n",
    )

    assert suggestions == {
        "marginalise": "marginalize",
        "factorised": "factorized",
        "discretising": "discretizing",
        "visualises": "visualizes",
        "artefacts": "artifacts",
        "randomised": "randomized",
        "serialisation": "serialization",
        "maximise": "maximize",
        "recognise": "recognize",
        "generalise": "generalize",
        "specialise": "specialize",
    }


def test_american_english_detects_added_pedagogy_and_misc_variants(
    tmp_path: Path,
) -> None:
    suggestions = _audit_prose(
        tmp_path,
        "Enrolment rises amongst skilful learners who fulfil the enquiry "
        "criteria.\nA sceptical reviewer practising maths reads the greyscale "
        "figure and judgements.\nGoal-orientated levelling signalled the next "
        "unlocked skill.\n",
    )

    assert suggestions == {
        "Enrolment": "Enrollment",
        "amongst": "among",
        "skilful": "skillful",
        "fulfil": "fulfill",
        "enquiry": "inquiry",
        "sceptical": "skeptical",
        "practising": "practicing",
        "maths": "math",
        "greyscale": "grayscale",
        "judgements": "judgments",
        "Goal-orientated": "Goal-oriented",
        "levelling": "leveling",
        "signalled": "signaled",
    }


def test_american_english_catches_hyphenated_compounds(tmp_path: Path) -> None:
    suggestions = _audit_prose(
        tmp_path,
        "A colour-coded, self-organising, neighbour-aware legend.\n",
    )

    assert suggestions == {
        "colour-coded": "color-coded",
        "self-organising": "self-organizing",
        "neighbour-aware": "neighbor-aware",
    }


def test_american_english_added_entries_avoid_technical_false_positives(
    tmp_path: Path,
) -> None:
    legitimate = (
        "capitalise",
        "analyses",
        "dialogue",
        "acknowledgement",
        "premise",
        "expertise",
        "franchise",
        "noise",
        "poise",
        "rise",
        "arise",
        "labor",
        "neighbor",
        "among",
        "inquiry",
        "math",
        "grayscale",
    )
    suggestions = _audit_prose(tmp_path, " ".join(legitimate) + ".\n")

    assert suggestions == {}


def test_american_english_mapping_entries_are_normalized() -> None:
    for british, american in BRITISH_TO_AMERICAN.items():
        assert british == british.lower()
        assert american == american.lower()
        assert british != american


def test_real_manuscript_uses_american_english() -> None:
    validate_american_english(REPO / "manuscript")
