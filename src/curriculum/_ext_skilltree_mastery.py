"""SkillTree mastery curriculum expansion.

These subjects train learners to treat each skill as a SkillTree-delivered
learning contract: prerequisites, explanations, quiz evidence, route handoff,
and misuse boundaries must all agree.
"""

from __future__ import annotations

from collections.abc import Iterable

from src.curriculum._ext_helpers import _AI, _APP, _C, _FEP, _IT, _M, _P, _VM, _q, _s
from src.curriculum.model import AssessmentQuestion, Skill, Stratum


def _dedupe(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _mc(
    prompt: str, answers: tuple[str, ...], correct: tuple[int, ...]
) -> AssessmentQuestion:
    return AssessmentQuestion(
        prompt=prompt,
        answers=answers,
        correct=correct,
        question_type="MultipleChoice",
    )


_ROLE_ROWS: tuple[tuple[str, str, str], ...] = (
    (
        "Prerequisite Map Lab",
        "Map the prerequisite concepts a learner must already control before opening the SkillTree skill.",
        "Prerequisite mapping turns a skill from an isolated card into an inspectable learning-path node.",
    ),
    (
        "Core Concept Discriminator",
        "Distinguish the skill's central claim from nearby concepts, slogans and implementation details.",
        "Concept discrimination keeps quiz answers aligned with the actual objective rather than with familiar vocabulary.",
    ),
    (
        "Worked-Example Translation",
        "Translate a worked example into learner-facing steps while preserving assumptions and notation.",
        "Worked-example translation tests whether a learner can move between formal content, prose and SkillTree quiz wording.",
    ),
    (
        "Counterexample and Misuse Review",
        "Identify a plausible misuse, overclaim or missing boundary condition for the skill.",
        "Misuse review prevents high-confidence wording from replacing evidence, prerequisites or model-specific limits.",
    ),
    (
        "Quiz-Authoring Review",
        "Write quiz material that separates recall, transfer, boundary recognition and misuse detection.",
        "Quiz-authoring review makes assessment quality visible before a skill is treated as completion-gated training.",
    ),
    (
        "Dependency Handoff Review",
        "Explain how the skill hands off to downstream skills without creating a backward prerequisite.",
        "Dependency handoff review keeps learning-path edges causal and uses related links for non-blocking context.",
    ),
    (
        "SkillTree Route Handoff",
        "Check how a learner moves from the dashboard into the official SkillTree learning or quiz route.",
        "Route handoff review keeps the local dashboard a shell around SkillTree rather than a second learner-state system.",
    ),
    (
        "Capstone Mastery Packet",
        "Assemble a compact mastery packet with prerequisites, explanation, quiz evidence and boundary notes.",
        "The capstone packet asks learners to prove they can connect content, assessment and delivery constraints.",
    ),
)


_STRATUM_ROWS = {
    "math": {
        "stratum": _M,
        "anchor": "pub_math_04",
        "audit": "audit_math_04",
        "context": "mathematical notation, invariants and proof obligations",
        "example": "a convexity or gradient argument",
        "boundary": "universal proof language without a stated theorem or counterexample check",
        "related": ("m_convexity", "viz_math_03", "sci_math_02"),
    },
    "probability": {
        "stratum": _P,
        "anchor": "pub_probability_04",
        "audit": "audit_probability_04",
        "previous": "mastery_math_08",
        "context": "priors, likelihoods, evidence and posterior calibration",
        "example": "a base-rate-sensitive Bayesian update",
        "boundary": "a computed posterior being described as empirical calibration evidence",
        "related": ("p_bayes_theorem", "sci_probability_05", "viz_probability_04"),
    },
    "information": {
        "stratum": _IT,
        "anchor": "pub_information_04",
        "audit": "audit_information_04",
        "previous": "mastery_probability_08",
        "context": "entropy, KL directionality and epistemic value",
        "example": "an information-gain or compression diagnostic",
        "boundary": "an information measure being treated as a behavioral result without data",
        "related": ("it_entropy", "it_kl", "it_mutual_information"),
    },
    "variational": {
        "stratum": _VM,
        "anchor": "pub_variational_04",
        "audit": "audit_variational_04",
        "previous": "mastery_information_08",
        "context": "ELBO, VFE, approximation families and convergence traces",
        "example": "a variational bound or posterior-mismatch example",
        "boundary": "an optimization trace being used as proof of model adequacy",
        "related": ("vm_elbo", "vm_free_energy", "sci_variational_06"),
    },
    "fep": {
        "stratum": _FEP,
        "anchor": "pub_fep_04",
        "audit": "audit_fep_04",
        "previous": "mastery_variational_08",
        "context": "Markov blankets, surprise bounds and process-theory scope",
        "example": "a blanket or timescale interpretation",
        "boundary": "principle-level wording being mistaken for process-level evidence",
        "related": ("fep_statement", "fep_markov_blanket", "audit_fep_01"),
    },
    "active_inference": {
        "stratum": _AI,
        "anchor": "pub_active_inference_04",
        "audit": "audit_active_inference_04",
        "previous": "mastery_fep_08",
        "context": "EFE terms, policy precision, preferences and regime switches",
        "example": "a policy-selection or epistemic-action scenario",
        "boundary": "preferences or precision being tuned until a desired action appears",
        "related": (
            "ai_expected_free_energy",
            "ai_precision_gamma",
            "ai_explore_exploit",
        ),
    },
    "computation": {
        "stratum": _C,
        "anchor": "pub_computation_04",
        "audit": "audit_computation_04",
        "previous": "mastery_active_inference_08",
        "context": "export schemas, dashboard routes, replay commands and live SkillTree handoff",
        "example": "a generated SkillTree JSON and dashboard quiz route",
        "boundary": "static artifact inspection being described as live learner-state proof",
        "related": (
            "comp_skilltree_export",
            "natsec_computation_02",
            "front_comp_replay_harness",
        ),
    },
    "applications": {
        "stratum": _APP,
        "anchor": "pub_applications_04",
        "audit": "audit_applications_04",
        "previous": "mastery_computation_08",
        "context": "stakeholder explanation, review packets and responsible applied boundaries",
        "example": "an applied source-to-claim review packet",
        "boundary": "completion data being interpreted as operator competence or deployment assurance",
        "related": ("app_limitations", "app_active_learning", "natsec_computation_08"),
    },
}


def _skill_name(prefix: str, role_name: str) -> str:
    readable = prefix.replace("_", " ").title()
    return f"{readable} {role_name}"


def _mastery_skill(prefix: str, index: int, role: tuple[str, str, str]) -> Skill:
    row = _STRATUM_ROWS[prefix]
    stratum = row["stratum"]
    assert isinstance(stratum, Stratum)
    anchor = str(row["anchor"])
    audit = str(row["audit"])
    previous = str(row.get("previous", ""))
    role_name, objective, role_focus = role
    context = str(row["context"])
    # Make each role's objective stratum-specific so the 8 role objectives do not
    # repeat verbatim across the 8 strata (otherwise 64 mastery skills share 8
    # objective strings). The per-strand clause names the concept being reviewed.
    objective = f"{objective.rstrip('.')}, working in the {context} strand."
    skill_id = f"mastery_{prefix}_{index:02d}"
    prior = f"mastery_{prefix}_{index - 1:02d}" if index > 1 else ""
    secondary = anchor if index % 2 == 0 else audit
    prerequisites = (anchor, audit, previous) if index == 1 else (prior, secondary)
    example = str(row["example"])
    boundary = str(row["boundary"])
    description = (
        f"{role_focus} In the {context} strand, learners use {example} to verify "
        "the prerequisite path, the learner-facing explanation, the quiz evidence and "
        "the official SkillTree route. The review must name one boundary condition, "
        f"especially {boundary}, before the skill is treated as mastered."
    )
    name = _skill_name(prefix, role_name)
    return _s(
        skill_id,
        name,
        stratum,
        objective,
        description,
        _dedupe(prerequisites),
        _q(
            f"What is the main learner contract in {name}?",
            [
                (
                    f"{name} links its prerequisites, explanation, assessment and delivery "
                    "route together into one auditable learning-path unit."
                ),
                (
                    f"{name} is treated as complete as soon as its title resembles a "
                    "familiar Active Inference topic the learner has seen before."
                ),
                (
                    f"{name} is allowed to ignore its prerequisites whenever the matching "
                    "quiz answer already looks obvious to the learner."
                ),
                (
                    f"{name} should move its learner-state and completion logic out of "
                    "SkillTree and into a separate dashboard-only store."
                ),
            ],
            0,
        ),
        _q(
            f"Which source should carry mastery evidence for {name}?",
            [
                (
                    f"The generated graph, quiz, validator output or official SkillTree route "
                    f"that {name} itself names as its evidence."
                ),
                (
                    f"A confident written summary of {name} that is never linked back to "
                    "the exported SkillTree project in any checkable way."
                ),
                (
                    f"A dashboard-only completion flag for {name} that is maintained entirely "
                    "outside SkillTree and the generated curriculum artifacts."
                ),
                (
                    f"An uncited assertion that the learner has probably understood {name} "
                    "well enough to move on to the next skill."
                ),
            ],
            0,
        ),
        _q(
            f"Which boundary must remain visible when teaching {name}?",
            [
                (
                    f"The review of {name} must not turn {boundary} into a stronger claim "
                    "than the available evidence for this skill can actually support."
                ),
                (
                    f"The review should quietly hide the limitations of {name} so that the "
                    "overall learning path feels simpler than it really is."
                ),
                (
                    f"The review should treat the related links of {name} as if they were "
                    "mandatory blocking prerequisites for every learner."
                ),
                (
                    f"The review should make every downstream skill depend directly on "
                    f"{name} being completed first."
                ),
            ],
            0,
        ),
        _mc(
            f"Which actions show sound transfer for {name}?",
            (
                f"Name the prerequisite concept a learner must bring into {name}.",
                (
                    f"Open or cite the official SkillTree route for {name} when delivery "
                    "evidence is needed."
                ),
                f"Claim learner competence in {name} from export counts alone.",
                f"Replace a failed validator for {name} with softer manuscript wording.",
            ),
            (0, 1),
        ),
        tags=("skilltree-mastery", "quiz-quality", prefix),
        related=tuple(row["related"]),  # type: ignore[arg-type]
    )


def _make(prefix: str) -> list[Skill]:
    return [
        _mastery_skill(prefix, index, role)
        for index, role in enumerate(_ROLE_ROWS, start=1)
    ]


_MASTERY_MATH = _make("math")
_MASTERY_PROBABILITY = _make("probability")
_MASTERY_INFORMATION = _make("information")
_MASTERY_VARIATIONAL = _make("variational")
_MASTERY_FEP = _make("fep")
_MASTERY_ACTIVE_INFERENCE = _make("active_inference")
_MASTERY_COMPUTATION = _make("computation")
_MASTERY_APPLICATIONS = _make("applications")
