"""Visual-evidence contract curriculum slice."""

from __future__ import annotations

from src.curriculum._ext_helpers import _AI, _C, _q, _s
from src.curriculum.model import AssessmentQuestion, Skill, Stratum


def _contract_questions(stage: str, noun: str) -> tuple[AssessmentQuestion, ...]:
    return (
        _q(
            f"What makes the {stage} stage evidence-critical rather than decorative?",
            [
                f"It states the {noun}, the source surface, and the review gate before styling choices are accepted.",
                f"It makes the {noun} memorable by choosing a saturated palette before checking the data source.",
                f"It lets reviewers defer the {noun} decision until after the dashboard card is published.",
            ],
            0,
        ),
        _q(
            f"A reviewer is auditing a figure at the {stage} stage. Which action is safest?",
            [
                f"Accept the panel when the {noun} looks visually plausible in the manuscript preview.",
                f"Trace the {noun} to generated data, registry metadata, and the validator that would fail on drift.",
                f"Rewrite the caption so the {noun} sounds less uncertain without changing the artifact contract.",
            ],
            1,
        ),
    )


def _skill(
    skill_id: str,
    name: str,
    stratum: Stratum,
    objective: str,
    description: str,
    prerequisites: tuple[str, ...],
    stage: str,
    noun: str,
    tags: tuple[str, ...],
    related: tuple[str, ...],
) -> Skill:
    return _s(
        skill_id,
        name,
        stratum,
        objective,
        description,
        prerequisites,
        *_contract_questions(stage, noun),
        tags=tags,
        related=tuple(item for item in related if item not in prerequisites),
    )


_VISUAL_EVIDENCE_TAGS = (
    "visual-evidence",
    "chart-contract",
    "artifact-validation",
    "computation",
)
_ACTIVE_VISUAL_TAGS = (
    "visual-evidence",
    "active-inference",
    "explanation",
    "claim-boundary",
)


_VISUAL_EVIDENCE_CONTRACTS = [
    _skill(
        "vdiag_question_contract",
        "Question Contract Diagnostics",
        _C,
        "State the reader question a figure must answer before validating its design.",
        (
            "Learners practice turning a proposed visualization into an explicit question "
            "contract before any chart form is accepted. The skill links figure intent to "
            "generated artifacts, registry rows, and validator failure modes so an appealing "
            "graphic cannot substitute for a reviewable evidence surface."
        ),
        ("viz_computation_04", "pub_computation_04"),
        "question-contract",
        "reader question",
        _VISUAL_EVIDENCE_TAGS,
        ("viz_computation_04", "pub_computation_04"),
    ),
    _skill(
        "vdiag_data_grain_audit",
        "Data Grain Audit",
        _C,
        "Verify that a visualization uses the same grain as its authored claim.",
        (
            "Learners inspect whether rows, graph nodes, figure files, or registry entries "
            "are the real observation grain behind a visual claim. The exercise prevents a "
            "summary chart from silently mixing incompatible surfaces such as curriculum "
            "skills, subjects, manuscript labels, and dashboard artifacts."
        ),
        ("vdiag_question_contract", "os_computation_04"),
        "data-grain-audit",
        "observation grain",
        _VISUAL_EVIDENCE_TAGS,
        ("os_computation_04",),
    ),
    _skill(
        "vdiag_encoding_strength_audit",
        "Encoding Strength Audit",
        _C,
        "Match visual encodings to the strength and direction of the evidence claim.",
        (
            "Learners compare position, length, color, annotation, and grouping choices "
            "against the question contract and data grain. The skill emphasizes that strong "
            "perceptual encodings belong to load-bearing comparisons, while decorative "
            "channels must not imply quantitative certainty the data does not support."
        ),
        ("vdiag_data_grain_audit", "viz_math_01"),
        "encoding-strength-audit",
        "encoding strength",
        _VISUAL_EVIDENCE_TAGS,
        ("viz_math_01",),
    ),
    _skill(
        "vdiag_annotation_claim_boundary",
        "Annotation Claim Boundaries",
        _C,
        "Separate labels that summarize generated evidence from labels that overclaim it.",
        (
            "Learners audit titles, badges, subtitles, and callouts for evidence inflation. "
            "The skill trains a rule that annotations must name computed or generated "
            "surfaces and boundaries, not convert deterministic artifact checks into claims "
            "about learner effectiveness or external deployment performance."
        ),
        ("vdiag_encoding_strength_audit", "sci_computation_02"),
        "annotation-boundary",
        "annotation boundary",
        _VISUAL_EVIDENCE_TAGS,
        ("sci_computation_02",),
    ),
    _skill(
        "vdiag_static_mobile_survival",
        "Static and Mobile Survival",
        _C,
        "Check that a figure keeps its evidence readable in static and narrow views.",
        (
            "Learners test whether a manuscript PNG and a dashboard card still expose the "
            "question, data grain, encoding, boundary, and source without hover behavior. "
            "The review path treats mobile readability as part of evidence integrity rather "
            "than a cosmetic responsive-design pass."
        ),
        ("vdiag_annotation_claim_boundary", "front_comp_dashboard_observability"),
        "static-mobile-survival",
        "static and mobile reading path",
        _VISUAL_EVIDENCE_TAGS,
        ("front_comp_dashboard_observability",),
    ),
    _skill(
        "vdiag_visual_negative_control",
        "Visual Negative Controls",
        _C,
        "Design a stale-output or missing-contract case that the validator must reject.",
        (
            "Learners specify the negative control for a figure contract: a missing registry "
            "row, absent file, stale manifest, weak caption, or unsupported annotation that "
            "must fail closed. The skill makes visualization QA falsifiable instead of only "
            "checking that the final image looks complete."
        ),
        ("vdiag_static_mobile_survival", "audit_computation_03"),
        "visual-negative-control",
        "negative-control case",
        _VISUAL_EVIDENCE_TAGS,
        ("audit_computation_03",),
    ),
]


_ACTIVE_INFERENCE_VISUAL_EXPLANATION = [
    _skill(
        "aiviz_policy_landscape_reading",
        "Policy Landscape Reading",
        _AI,
        "Read policy-comparison visuals as bounded active-inference explanations.",
        (
            "Learners interpret a policy landscape by naming the policies, preference "
            "structure, state evidence, and missing alternatives. The skill prevents a "
            "smooth visual field from being mistaken for proof that the displayed policy "
            "set is exhaustive or empirically validated."
        ),
        ("viz_active_inference_04", "sci_active_inference_03"),
        "policy-landscape-reading",
        "policy comparison",
        _ACTIVE_VISUAL_TAGS,
        ("viz_active_inference_04", "sci_active_inference_03"),
    ),
    _skill(
        "aiviz_precision_regime_visuals",
        "Precision Regime Visuals",
        _AI,
        "Explain precision-sensitive regimes without implying universal policy laws.",
        (
            "Learners audit line sweeps, crossing points, and regime labels in active "
            "inference examples. The skill keeps precision visuals tied to the stated "
            "model, preference structure, and action set so the reader sees a bounded "
            "teaching example rather than an unsupported general theorem."
        ),
        ("aiviz_policy_landscape_reading", "ai_expected_free_energy"),
        "precision-regime-visuals",
        "precision regime",
        _ACTIVE_VISUAL_TAGS,
        ("ai_expected_free_energy",),
    ),
    _skill(
        "aiviz_efe_component_contrast",
        "EFE Component Contrast",
        _AI,
        "Contrast expected-free-energy components with visible scope boundaries.",
        (
            "Learners inspect bars, stacked terms, and annotations that separate risk, "
            "ambiguity, and epistemic value. The review emphasizes component clarity: a "
            "visual should show which term changes the policy reading while preserving "
            "the assumptions that make the decomposition meaningful."
        ),
        ("aiviz_precision_regime_visuals", "sci_active_inference_01"),
        "efe-component-contrast",
        "expected-free-energy component",
        _ACTIVE_VISUAL_TAGS,
        ("sci_active_inference_01",),
    ),
    _skill(
        "aiviz_preference_surface_caveats",
        "Preference Surface Caveats",
        _AI,
        "Caption preference-surface visuals with their modeled scope and exclusions.",
        (
            "Learners read preference maps as authored model artifacts, not empirical "
            "maps of human value. The skill requires captions to name the preference "
            "encoding, excluded stakeholders, and scope caveats before a surface is used "
            "to explain action selection."
        ),
        ("aiviz_efe_component_contrast", "pub_active_inference_03"),
        "preference-surface-caveats",
        "preference surface",
        _ACTIVE_VISUAL_TAGS,
        ("pub_active_inference_03",),
    ),
    _skill(
        "aiviz_action_failure_panel",
        "Action Failure Panels",
        _AI,
        "Use visual panels to show when an active-inference explanation should fail.",
        (
            "Learners construct contrast panels where an action story breaks because a "
            "preference, observation model, policy set, or precision assumption is wrong. "
            "The skill keeps active-inference visualization accountable to falsifiable "
            "failure cases rather than only successful toy trajectories."
        ),
        ("aiviz_preference_surface_caveats", "audit_active_inference_04"),
        "action-failure-panel",
        "failure panel",
        _ACTIVE_VISUAL_TAGS,
        ("audit_active_inference_04",),
    ),
    _skill(
        "aiviz_stakeholder_handoff_caption",
        "Stakeholder Handoff Captions",
        _AI,
        "Write visual captions that hand active-inference evidence to non-authors safely.",
        (
            "Learners convert a technical active-inference figure into a caption that names "
            "the modeled mechanism, visual evidence, caveat, and next review action. The "
            "skill treats captioning as evidence handoff, not marketing polish or a claim "
            "that local deterministic validation proves external effectiveness."
        ),
        ("aiviz_action_failure_panel", "pub_active_inference_04"),
        "stakeholder-handoff-caption",
        "handoff caption",
        _ACTIVE_VISUAL_TAGS,
        ("pub_active_inference_04",),
    ),
]
