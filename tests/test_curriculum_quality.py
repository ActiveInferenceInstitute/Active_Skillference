"""Tests for curriculum learner-quality invariants beyond graph validity."""

from __future__ import annotations

import pytest

from src.curriculum.catalog import build_curriculum
from src.curriculum.diagnostics import curriculum_diagnostic_gap_map
from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import (
    AssessmentQuestion,
    CurriculumError,
    Skill,
    Stratum,
    Subject,
)
from src.curriculum.quality import audit_curriculum_quality, validate_curriculum_quality


def _q(prompt: str = "Q?", correct: int = 0) -> AssessmentQuestion:
    return AssessmentQuestion(prompt, ("a", "b", "c"), (correct,))


def _mc(prompt: str = "Transfer?") -> AssessmentQuestion:
    return AssessmentQuestion(
        prompt,
        ("good transfer", "bad transfer", "boundary check"),
        (0, 2),
        question_type="MultipleChoice",
    )


def _skill(
    sid: str,
    stratum: Stratum,
    prereqs: tuple[str, ...] = (),
    *,
    assessments: tuple[AssessmentQuestion, ...] = (
        _q(),
        _q("Q2?", 1),
        _q("Q3?", 2),
        _mc(),
    ),
    tags: tuple[str, ...] = ("math_foundations", "topic"),
    description: str = (
        "This description is long enough to explain the idea, its role, and how a "
        "learner will use it later."
    ),
) -> Skill:
    return Skill(
        sid,
        sid,
        stratum,
        "Use this concept in the curriculum.",
        description,
        prereqs,
        assessments,
        tags=tags,
    )


def _graph(*skills: Skill) -> CurriculumGraph:
    by_stratum: dict[Stratum, list[Skill]] = {}
    for skill in skills:
        by_stratum.setdefault(skill.stratum, []).append(skill)
    subjects = [
        Subject(
            f"sub_{stratum.value}",
            stratum.value,
            stratum,
            "A subject description long enough for learner orientation.",
            tuple(items),
        )
        for stratum, items in by_stratum.items()
    ]
    return CurriculumGraph(subjects)


def test_quality_rejects_backward_prerequisites() -> None:
    graph = _graph(
        _skill("later", Stratum.ACTIVE_INFERENCE, ("root",)),
        _skill("root", Stratum.MATH_FOUNDATIONS),
        _skill("early", Stratum.MATH_FOUNDATIONS, ("later",)),
    )

    issues = audit_curriculum_quality(graph)

    assert any(issue.code == "backward_prerequisite" for issue in issues)
    with pytest.raises(CurriculumError, match="backward_prerequisite"):
        validate_curriculum_quality(graph)


def test_curriculum_diagnostic_gap_map_tracks_maintenance_surfaces() -> None:
    payload = curriculum_diagnostic_gap_map(build_curriculum())

    assert payload["summary"]["skills"] > 0
    assert payload["summary"]["bottleneckCount"] > 0
    assert payload["summary"]["longPathCount"] > 0
    assert payload["remediationQueue"]
    assert payload["assessmentBalance"]
    assert all("skillId" in row for row in payload["bottlenecks"])


def test_quality_rejects_shallow_assessment_skills() -> None:
    graph = _graph(
        _skill(
            "one",
            Stratum.MATH_FOUNDATIONS,
            assessments=(_q(), _mc()),
        )
    )

    with pytest.raises(CurriculumError, match="assessment_depth"):
        validate_curriculum_quality(graph)


def test_quality_rejects_three_question_skills() -> None:
    graph = _graph(
        _skill(
            "three",
            Stratum.MATH_FOUNDATIONS,
            assessments=(_q(), _q("Q2?", 1), _mc()),
        )
    )

    with pytest.raises(CurriculumError, match="assessment_depth"):
        validate_curriculum_quality(graph)


def test_quality_rejects_missing_multiple_choice_transfer_item() -> None:
    graph = _graph(
        _skill(
            "thinquiz",
            Stratum.MATH_FOUNDATIONS,
            assessments=(_q("Q1?", 0), _q("Q2?", 1), _q("Q3?", 2), _q("Q4?", 1)),
        )
    )

    with pytest.raises(CurriculumError, match="assessment_variety"):
        validate_curriculum_quality(graph)


def test_quality_rejects_dominant_correct_answer_position() -> None:
    # A full 3-answer bucket whose correct answer is always index 0 must be flagged
    # (per answer-count bucket, so a dead index cannot hide behind a pooled average).
    biased = tuple(_q(f"Q{index}?", 0) for index in range(16))
    graph = _graph(
        _skill("biased", Stratum.MATH_FOUNDATIONS, assessments=biased + (_mc(),))
    )

    # Assert the exact code (not a substring match that would also match
    # "mc_answer_position_bias" from the fixture's multiple-choice item).
    codes = {issue.code for issue in audit_curriculum_quality(graph)}
    assert "answer_position_bias" in codes
    with pytest.raises(CurriculumError):
        validate_curriculum_quality(graph)


def test_quality_rejects_available_answer_slot_underuse() -> None:
    # 4-answer bucket where the correct index never lands on slot 3: index 3 is present
    # in every question but correct in none, which the per-bucket audit must reject.
    single_choice = tuple(
        AssessmentQuestion(f"Q{index}?", ("a", "b", "c", "d"), (index % 3,))
        for index in range(15)
    )
    graph = _graph(
        _skill(
            "underused",
            Stratum.MATH_FOUNDATIONS,
            assessments=single_choice
            + (
                AssessmentQuestion(
                    "Transfer?",
                    ("good transfer", "bad transfer", "boundary check", "overclaim"),
                    (0, 2),
                    question_type="MultipleChoice",
                ),
            ),
        )
    )

    with pytest.raises(CurriculumError, match="answer_position_underuse"):
        validate_curriculum_quality(graph)


def test_quality_rejects_longest_correct_answer_leak() -> None:
    # If the correct answer is the strictly longest option in too many questions, a
    # learner can pass by always picking the longest answer. The audit must catch it.
    leaky = tuple(
        AssessmentQuestion(
            f"Q{index}?",
            (
                "this is by far the longest and most complete correct answer option",
                "short wrong",
                "also short",
            ),
            (0,),
        )
        for index in range(16)
    )
    graph = _graph(
        _skill("lengthy", Stratum.MATH_FOUNDATIONS, assessments=leaky + (_mc(),))
    )

    with pytest.raises(CurriculumError, match="answer_length_bias"):
        validate_curriculum_quality(graph)


def test_quality_rejects_shortest_correct_answer_leak() -> None:
    # Two-sided: a correct answer that is consistently the SHORTEST is just as exploitable
    # (pick-shortest) as one that is longest. The one-sided longest-only check missed this.
    leaky = tuple(
        AssessmentQuestion(
            f"Q{index}?",
            (
                "yes",
                "a clearly longer and more elaborate distractor option here",
                "another clearly longer and more elaborate distractor option",
            ),
            (0,),
        )
        for index in range(16)
    )
    graph = _graph(
        _skill("shorty", Stratum.MATH_FOUNDATIONS, assessments=leaky + (_mc(),))
    )

    issues = audit_curriculum_quality(graph)
    length_issues = [i for i in issues if i.code == "answer_length_bias"]
    assert any("shortest" in i.message for i in length_issues)
    with pytest.raises(CurriculumError):
        validate_curriculum_quality(graph)


def test_quality_rejects_fixed_multiple_choice_positions() -> None:
    # Every multiple-choice item with the correct set fixed at (0, 2) lets a learner
    # pass with a constant two-index rule; the MC position audit must flag it.
    fixed_mc = tuple(
        AssessmentQuestion(
            f"MC{index}?",
            ("alpha", "beta", "gamma", "delta"),
            (0, 2),
            question_type="MultipleChoice",
        )
        for index in range(16)
    )
    graph = _graph(
        _skill(
            "fixedmc",
            Stratum.MATH_FOUNDATIONS,
            assessments=(_q("Q1?", 0), _q("Q2?", 1), _q("Q3?", 2)) + fixed_mc,
        )
    )

    with pytest.raises(CurriculumError, match="mc_answer_position_bias"):
        validate_curriculum_quality(graph)


def test_quality_rejects_duplicated_objectives() -> None:
    # Many skills sharing one verbatim objective string reads as templated filler.
    dupes = tuple(
        Skill(
            f"dup{index}",
            f"dup{index}",
            Stratum.MATH_FOUNDATIONS,
            "One shared objective reused verbatim across every skill.",
            (
                "This description is long enough to explain the idea, its role, and how "
                "a learner will use it later on."
            ),
            (),
            (_q(), _q("Q2?", 1), _q("Q3?", 2), _mc()),
            tags=("math_foundations", "topic"),
        )
        for index in range(6)
    )
    graph = _graph(*dupes)

    with pytest.raises(CurriculumError, match="duplicate_objective"):
        validate_curriculum_quality(graph)


def test_quality_rejects_missing_tags_and_terse_descriptions() -> None:
    graph = _graph(
        _skill(
            "thin",
            Stratum.MATH_FOUNDATIONS,
            tags=(),
            description="Too short.",
        )
    )

    issues = audit_curriculum_quality(graph)

    assert {issue.code for issue in issues} >= {
        "missing_tags",
        "terse_skill_description",
    }


def test_quality_rejects_dominant_mc_correct_set() -> None:
    # Green-by-construction guard: alternating (0,2)/(1,3) makes every index correct 50%
    # of the time (passing the per-index gate) while a constant {0,2} rule still clears
    # half the items. The per-correct-set gate must catch the joint-distribution leak.
    mc = tuple(
        AssessmentQuestion(
            f"MC{index}?",
            ("alpha", "beta", "gamma", "delta"),
            (0, 2) if index % 2 == 0 else (1, 3),
            question_type="MultipleChoice",
        )
        for index in range(20)
    )
    graph = _graph(
        _skill(
            "jointmc",
            Stratum.MATH_FOUNDATIONS,
            assessments=(_q("Q1?", 0), _q("Q2?", 1), _q("Q3?", 2)) + mc,
        )
    )

    issues = audit_curriculum_quality(graph)
    codes = {issue.code for issue in issues}
    # The per-index gate is satisfied (each index correct 50% < 60%) ...
    assert "mc_answer_position_bias" not in codes
    # ... but the per-set gate must fire on the dominant (0,2)/(1,3) split.
    assert "mc_answer_set_bias" in codes


def test_quality_rejects_answer_body_reused_across_skills() -> None:
    # Verbatim quiz boilerplate shared across many skills must be flagged.
    shared = AssessmentQuestion(
        "Shared?", ("the one reused boilerplate answer", "b", "c"), (0,)
    )
    skills = tuple(
        _skill(
            f"reuse{index}",
            Stratum.MATH_FOUNDATIONS,
            assessments=(shared, _q("Q2?", 1), _q("Q3?", 2), _mc()),
        )
        for index in range(20)
    )
    graph = _graph(*skills)

    with pytest.raises(CurriculumError, match="answer_reuse"):
        validate_curriculum_quality(graph)


def test_quality_rejects_banned_endorsement_phrase_in_skill() -> None:
    # An endorsement-overreach phrase in learner-facing curriculum text must fail the
    # gate, not just in manuscript prose.
    skill = Skill(
        "natsec",
        "NSA approved security skill",
        Stratum.APPLICATIONS,
        "Teach a defensive concept.",
        (
            "This description is long enough to explain the idea, its role, and how a "
            "learner will use it later in the path."
        ),
        (),
        (_q(), _q("Q2?", 1), _q("Q3?", 2), _mc()),
        tags=("applications", "topic"),
    )
    graph = _graph(skill)

    with pytest.raises(CurriculumError, match="banned_endorsement_phrase"):
        validate_curriculum_quality(graph)


def test_quality_rejects_off_domain_placeholder_distractor() -> None:
    """Negative control: a known placeholder used as a DISTRACTOR is flagged."""
    skill = _skill(
        "joke",
        Stratum.MATH_FOUNDATIONS,
        assessments=(
            AssessmentQuestion(
                "Bayes' rule updates a:", ("Prior", "Pixels", "c"), (0,)
            ),
            _q("Q2?", 1),
            _q("Q3?", 2),
            _mc(),
        ),
    )

    codes = {issue.code for issue in audit_curriculum_quality(_graph(skill))}
    assert "implausible_distractor" in codes
    with pytest.raises(CurriculumError, match="implausible_distractor"):
        validate_curriculum_quality(_graph(skill))


def test_quality_allows_placeholder_term_as_correct_answer() -> None:
    """Positive control: the same term as the CORRECT answer is not flagged.

    A learner question whose answer is legitimately e.g. "Pixels" (a vision-input skill)
    must not trip the distractor guard — the gate is scoped to incorrect answers only.
    """
    skill = _skill(
        "legit",
        Stratum.MATH_FOUNDATIONS,
        assessments=(
            AssessmentQuestion(
                "A raster image is an array of:", ("Pixels", "Theorems", "Priors"), (0,)
            ),
            _q("Q2?", 1),
            _q("Q3?", 2),
            _mc(),
        ),
    )

    codes = {issue.code for issue in audit_curriculum_quality(_graph(skill))}
    assert "implausible_distractor" not in codes


def test_quality_distractor_guard_ignores_appended_balance_clause() -> None:
    """A placeholder is still caught when a length-balancing clause is appended to it."""
    skill = _skill(
        "joke_balanced",
        Stratum.MATH_FOUNDATIONS,
        assessments=(
            AssessmentQuestion(
                "Bayes' rule updates a:",
                ("Prior", "Pixels — weigh this against the prerequisites.", "c"),
                (0,),
            ),
            _q("Q2?", 1),
            _q("Q3?", 2),
            _mc(),
        ),
    )

    codes = {issue.code for issue in audit_curriculum_quality(_graph(skill))}
    assert "implausible_distractor" in codes


def test_quality_rejects_off_domain_display_substring_distractor() -> None:
    """Class guard: a display/UI distractor (not in the verbatim list) is still flagged."""
    skill = _skill(
        "display_joke",
        Stratum.MATH_FOUNDATIONS,
        assessments=(
            AssessmentQuestion(
                "A graphical model makes explicit the:",
                ("Conditional independencies", "The font rendering", "c"),
                (0,),
            ),
            _q("Q2?", 1),
            _q("Q3?", 2),
            _mc(),
        ),
    )

    codes = {issue.code for issue in audit_curriculum_quality(_graph(skill))}
    assert "implausible_distractor" in codes


def test_quality_distractor_guard_does_not_false_positive_on_word_prefix() -> None:
    """A substantive distractor that merely begins with a banned word is NOT flagged.

    "Pixels in a raster image" begins with "pixels" but is a real phrase; the full-phrase
    guard matches only the exact phrase or an appended balance clause, never a bare space.
    """
    skill = _skill(
        "prefix_ok",
        Stratum.MATH_FOUNDATIONS,
        assessments=(
            AssessmentQuestion(
                "An affordance field is not:",
                ("Action opportunities", "Pixels in a raster image", "c"),
                (0,),
            ),
            _q("Q2?", 1),
            _q("Q3?", 2),
            _mc(),
        ),
    )

    codes = {issue.code for issue in audit_curriculum_quality(_graph(skill))}
    assert "implausible_distractor" not in codes


def test_real_catalog_passes_curriculum_quality_gate() -> None:
    graph = build_curriculum()

    validate_curriculum_quality(graph)
    assert audit_curriculum_quality(graph) == []
    assert len(graph.skills) >= 600
    assert len(graph.subjects) >= 105
    assert len(graph.prerequisite_edges()) >= 1136
    assert sum(len(skill.assessments) for skill in graph.skills) >= 2400


def test_answer_reuse_exempts_rubric_but_counts_authored() -> None:
    # A rubric-tagged shared answer is exempt (declared instrument); an authored shared
    # answer reused across skills still fails.
    rubric = AssessmentQuestion(
        "rp", ("RUBRIC SHARED BODY", "r1", "r2"), (0,), origin="rubric"
    )
    authored = AssessmentQuestion("ap", ("AUTHORED SHARED BODY", "a1", "a2"), (0,))
    skills = tuple(
        _skill(
            f"x{i}",
            Stratum.MATH_FOUNDATIONS,
            assessments=(
                rubric,
                authored,
                AssessmentQuestion(f"u{i}?", (f"c{i}", f"d{i}", f"e{i}"), (0,)),
                _mc(),
            ),
        )
        for i in range(20)
    )
    msgs = [
        i.message
        for i in audit_curriculum_quality(_graph(*skills))
        if i.code == "answer_reuse"
    ]
    assert any("AUTHORED SHARED BODY" in m for m in msgs)
    assert not any("RUBRIC SHARED BODY" in m for m in msgs)


def test_answer_reuse_flags_skill_with_only_rubric_items() -> None:
    # The shared rubric must not be a skill's entire assessment set.
    only_rubric = _skill(
        "allrub",
        Stratum.MATH_FOUNDATIONS,
        assessments=(
            AssessmentQuestion("p1", ("a", "b", "c"), (0,), origin="rubric"),
            AssessmentQuestion("p2", ("d", "e", "f"), (1,), origin="rubric"),
            AssessmentQuestion("p3", ("g", "h", "i"), (2,), origin="rubric"),
            AssessmentQuestion(
                "p4",
                ("j", "k", "l", "m"),
                (0, 2),
                question_type="MultipleChoice",
                origin="rubric",
            ),
        ),
    )
    codes = {i.code for i in audit_curriculum_quality(_graph(only_rubric))}
    assert "all_rubric_assessments" in codes


def test_length_fillers_carry_no_correctness_signal() -> None:
    # Regression guard for the suffix cue: the length-equalization fillers are drawn from
    # one shared pool, so no filler text may predict correctness above near-chance.
    from collections import Counter

    from src.curriculum.assessment_normalize import _LENGTH_FILLERS
    from src.curriculum.catalog import build_curriculum

    graph = build_curriculum()
    correct_with, total_with = Counter(), Counter()
    for skill in graph.skills:
        for q in skill.assessments:
            if q.question_type == "SingleChoice" and len(q.correct) == 1:
                for idx, opt in enumerate(q.answers):
                    for f in _LENGTH_FILLERS:
                        if opt.rstrip().endswith(f.rstrip()):
                            total_with[f] += 1
                            if idx == q.correct[0]:
                                correct_with[f] += 1
    for f, n in total_with.items():
        if n >= 20:
            assert correct_with[f] / n <= 0.45, (
                f"filler signals correctness: {correct_with[f] / n:.0%}"
            )


def test_quality_flags_extended_off_domain_distractor() -> None:
    """Negative control (ISC-126): a fresh off-domain distractor from an extended class
    (compute-infra/web/finance) that was never in the original list must still fire."""
    bad = AssessmentQuestion(
        "What does entropy measure?",
        ("The average surprise of a distribution", "A blockchain transaction fee"),
        (0,),
    )
    skill = _skill(
        "offdomain",
        Stratum.MATH_FOUNDATIONS,
        assessments=(bad, _q("Q2?", 1), _q("Q3?", 2), _mc()),
    )
    kinds = {issue.code for issue in audit_curriculum_quality(_graph(skill))}
    assert "implausible_distractor" in kinds


def test_quality_flags_missing_semantic_prerequisite() -> None:
    """Negative control (ISC-132): a skill assessed on KL divergence without it_kl in its
    transitive prerequisites must fire — pedagogical inversion the structural DAG misses."""
    definer = _skill("it_kl", Stratum.INFORMATION_THEORY)
    user = Skill(
        "it_uses_kl",
        "it_uses_kl",
        Stratum.INFORMATION_THEORY,
        "Use the divergence in scoring.",
        "A description with plenty of words so the description-length floor is cleared here.",
        ("it_kl_unrelated",),  # a prerequisite that is NOT the KL definer
        (
            AssessmentQuestion(
                "Which term is the KL divergence in the decomposition?",
                ("The directed divergence", "The variance", "The mean"),
                (0,),
            ),
            _q("Q2?", 1),
            _q("Q3?", 2),
            _mc(),
        ),
    )
    unrelated = _skill("it_kl_unrelated", Stratum.INFORMATION_THEORY)
    codes = {i.code for i in audit_curriculum_quality(_graph(definer, user, unrelated))}
    assert "semantic_prerequisite_missing" in codes

    # And it does NOT fire once it_kl is a real prerequisite.
    fixed = Skill(
        user.skill_id,
        user.name,
        user.stratum,
        user.objective,
        user.description,
        ("it_kl",),
        user.assessments,
    )
    codes2 = {i.code for i in audit_curriculum_quality(_graph(definer, fixed))}
    assert "semantic_prerequisite_missing" not in codes2


def test_semantic_prereq_concept_map_is_non_vacuous() -> None:
    """Advisor guard (anti-vacuity): every concept in the gate's map must be ACTUALLY
    assessed by at least one real skill. A concept matching zero assessments makes the
    gate silently vacuous for it (an empty scan can never fire), which an injection test
    cannot detect. This fails the build if the live corpus drifts away from a guarded
    concept (and is how the dead 'Taylor expansion' entry was caught and removed)."""
    import re as _re

    from src.curriculum.catalog import build_curriculum
    from src.curriculum.quality import _CONCEPT_PREREQUISITES

    graph = build_curriculum()
    for concept, patterns, definers in _CONCEPT_PREREQUISITES:
        compiled = [_re.compile(pat, _re.IGNORECASE) for pat in patterns]
        assessed = 0
        for skill in graph.skills:
            if skill.skill_id in definers:
                continue
            atext = " ".join(
                [q.prompt for q in skill.assessments]
                + [a for q in skill.assessments for a in q.answers]
            )
            if any(rx.search(atext) for rx in compiled):
                assessed += 1
        assert assessed > 0, (
            f"concept {concept!r} guards nothing — gate is vacuous for it"
        )
