"""Scientific-audit curriculum expansion for claim support and evidence discipline."""

from __future__ import annotations

from collections.abc import Iterable

from src.curriculum._ext_helpers import _AI, _APP, _C, _FEP, _IT, _M, _P, _VM, _q, _s
from src.curriculum.model import Skill, Stratum


def _dedupe(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _audit_skill(
    *,
    prefix: str,
    index: int,
    name: str,
    stratum: Stratum,
    anchor: str,
    objective: str,
    focus: str,
    related: tuple[str, ...] = (),
) -> Skill:
    skill_id = f"audit_{prefix}_{index:02d}"
    prior = f"audit_{prefix}_{index - 1:02d}" if index > 1 else ""
    description = (
        f"{focus} Learners practice assigning a scientific claim to its evidence class, "
        "checking whether its language outruns the available support, and recording the "
        "validator, citation, figure, limitation, or kernel token that should carry the "
        "claim in a reproducible release."
    )
    return _s(
        skill_id,
        name,
        stratum,
        objective,
        description,
        _dedupe((anchor, prior)),
        _q(
            f"What makes {name} a scientific-audit skill?",
            [
                "It matches the claim's strength to its evidence class and names the verification surface.",
                "It replaces evidence with confident wording so the release reads cleanly.",
                "It treats every plotted or cited statement as empirically established.",
            ],
            0,
        ),
        tags=("scientific-audit", "claim-support", prefix),
        related=related,
    )


def _make(
    prefix: str,
    stratum: Stratum,
    anchor: str,
    rows: tuple[tuple[str, str, str, tuple[str, ...]], ...],
) -> list[Skill]:
    return [
        _audit_skill(
            prefix=prefix,
            index=index,
            name=name,
            stratum=stratum,
            anchor=anchor,
            objective=objective,
            focus=focus,
            related=related,
        )
        for index, (name, objective, focus, related) in enumerate(rows, start=1)
    ]


_AUDIT_MATH = _make(
    "math",
    _M,
    "pub_math_04",
    (
        (
            "Proof Obligation Inventory",
            "Separate algebraic identities, algorithmic invariants and empirical claims before assigning evidence.",
            "A proof obligation inventory starts from mathematical form: what follows from definitions, what follows from code, and what remains outside both.",
            ("m_convexity", "sci_math_02"),
        ),
        (
            "Invariant-to-Validator Mapping",
            "Map each mathematical invariant to the smallest validator that can fail on a counterexample.",
            "A graph, bound or optimization invariant should have a negative control rather than a prose assertion.",
            ("viz_math_03",),
        ),
        (
            "Quantifier Boundary Checks",
            "Identify when a sentence shifts from one example to all models or all learners.",
            "Scientific integrity depends on noticing when local notation has become a universal statement.",
            ("sci_math_06",),
        ),
        (
            "Claim Strength Ledgering",
            "Record the mathematical status of each strong claim before it enters manuscript prose.",
            "The ledger prevents proof language from being reused for deterministic enumeration, simulation, or delivery checks.",
            ("pub_math_03",),
        ),
    ),
)


_AUDIT_PROBABILITY = _make(
    "probability",
    _P,
    "pub_probability_04",
    (
        (
            "Calibration Claim Sorting",
            "Distinguish calibrated probability statements from deterministic posterior calculations.",
            "A computed posterior is not an empirical calibration result unless frequencies or held-out predictions support it.",
            ("p_bayes_theorem", "viz_probability_01"),
        ),
        (
            "Base-Rate Audit Trails",
            "Trace base-rate assumptions through posterior claims and reader-facing examples.",
            "Base-rate sensitivity keeps a persuasive example from being mistaken for a stable domain conclusion.",
            ("sci_probability_05",),
        ),
        (
            "Posterior-Predictive Evidence Classes",
            "Assign posterior-predictive statements to simulation, empirical or scope-limit evidence.",
            "Predictive checks can criticize a model, but their evidential status depends on what data produced them.",
            ("pub_probability_03",),
        ),
        (
            "Uncertainty Language Gate",
            "Revise probability prose so confidence words match the source of uncertainty.",
            "The gate prevents precise mathematical output from becoming unsupported certainty about the world.",
            ("viz_probability_04",),
        ),
    ),
)


_AUDIT_INFORMATION = _make(
    "information",
    _IT,
    "pub_information_04",
    (
        (
            "Information-Diagnostic Roles",
            "Decide whether an information measure is a teaching diagnostic, objective, or empirical statistic.",
            "Entropy, KL and information gain support different claim types depending on the artifact surface.",
            ("it_mutual_information", "viz_information_01"),
        ),
        (
            "KL Directionality Review",
            "Check that every KL-based claim names its reference distribution and direction.",
            "A reversed KL statement can remain syntactically correct while changing the scientific interpretation.",
            ("viz_information_02",),
        ),
        (
            "Compression Claim Boundaries",
            "State what a compressed curriculum or figure preserves and what it discards.",
            "Compression is useful for reader handoff only when the lost detail is named and recoverable.",
            ("pub_information_01",),
        ),
        (
            "Epistemic-Value Evidence Labels",
            "Label whether information-gain claims are computed, simulated, or empirically observed.",
            "Epistemic value is a kernel quantity here, not evidence that learners or agents behave that way in general.",
            ("pub_information_03",),
        ),
    ),
)


_AUDIT_VARIATIONAL = _make(
    "variational",
    _VM,
    "pub_variational_04",
    (
        (
            "Bound-Sensitivity Review",
            "Audit which variables make a variational bound tight or loose in the plotted example.",
            "A sensitivity review keeps bound tightness tied to the posterior and model rather than to broad truth claims.",
            ("vm_free_energy", "viz_variational_01"),
        ),
        (
            "Approximation-Family Evidence Tags",
            "Tag approximation-family claims as mathematical, computational, or empirical before publication.",
            "A tractable family can justify a calculation without proving adequacy for a domain dataset.",
            ("sci_variational_03",),
        ),
        (
            "Convergence Claim Triage",
            "Separate objective descent, fixed-point arrival and model-quality claims in optimization traces.",
            "Descent plots require language that says what is optimized and what remains untested.",
            ("viz_variational_02",),
        ),
        (
            "Supplement Sensitivity Handoff",
            "Route detailed VFE and EFE sensitivity claims into supplemental sections with explicit boundaries.",
            "The handoff lets Results state platform evidence while the supplement carries model-specific mathematics.",
            ("pub_variational_01",),
        ),
    ),
)


_AUDIT_FEP = _make(
    "fep",
    _FEP,
    "pub_fep_04",
    (
        (
            "FEP Falsifiability Boundaries",
            "Name the modelling commitments needed before an FEP explanation becomes testable.",
            "A broad principle does not by itself define an empirical test without a process theory and measurement model.",
            ("fep_statement", "viz_fep_04"),
        ),
        (
            "Principle-Process-Empirical Split",
            "Classify each FEP sentence as formal principle, process theory, implementation or empirical claim.",
            "The split prevents a valid variational identity from being read as evidence for every biological story.",
            ("pub_fep_03",),
        ),
        (
            "Critique Integration Checks",
            "Attach FEP critique sources to the precise claim class they challenge.",
            "Critique integration turns disagreement into a boundary condition rather than a bibliography footnote.",
            ("sci_fep_05",),
        ),
        (
            "Timescale Evidence Review",
            "Check whether timescale claims are derived, simulated, observed or out of scope.",
            "A timescale review keeps inference, learning and self-organization from collapsing into one unsupported mechanism.",
            ("pub_fep_02",),
        ),
    ),
)


_AUDIT_ACTIVE_INFERENCE = _make(
    "active_inference",
    _AI,
    "pub_active_inference_04",
    (
        (
            "Policy-Regime Audit",
            "Identify the preferences, precision and policy set that bound an active-inference example.",
            "Policy conclusions are meaningful only inside the regime that generated their expected-free-energy scores.",
            ("ai_expected_free_energy", "viz_active_inference_02"),
        ),
        (
            "Preference-Design Source Checks",
            "Check whether preference claims come from a model specification, source citation or empirical target.",
            "Preference design is a value-bearing modelling choice and should not be hidden inside technical language.",
            ("pub_active_inference_03",),
        ),
        (
            "Epistemic-Pragmatic Transfer Tests",
            "Test whether learners preserve epistemic and pragmatic terms when transferring to a new policy story.",
            "Transfer tests catch cases where expected free energy collapses into a single uninspected score.",
            ("pub_active_inference_02",),
        ),
        (
            "Action-Selection Overclaim Review",
            "Revise action-selection prose so deterministic toy results do not imply general behavioral evidence.",
            "The review protects Active Inference examples from overclaiming outside their specified agent model.",
            ("sci_active_inference_06",),
        ),
    ),
)


_AUDIT_COMPUTATION = _make(
    "computation",
    _C,
    "pub_computation_04",
    (
        (
            "Reproducible Audit Ledgers",
            "Write generated ledgers that connect claims, figures, citations and validators.",
            "A ledger is the computational bridge from scientific wording to inspectable release evidence.",
            ("comp_provenance_gate", "pub_computation_02"),
        ),
        (
            "Online Source-Health Statuses",
            "Record source reachability failures as statuses rather than crashing release audits.",
            "Network currentness evidence is useful only when timeout, TLS and URL errors are preserved for review.",
            ("viz_computation_03",),
        ),
        (
            "Figure Semantic Metadata Gates",
            "Validate that figures declare data source, encoding, takeaway and interpretation boundary.",
            "Semantic metadata makes visualization quality auditable beyond nonblank image checks.",
            ("pub_computation_03",),
        ),
        (
            "Browser Evidence Boundaries",
            "Separate dashboard smoke evidence from proof that a live external SkillTree service is online.",
            "A browser check can prove rendered routes and fallback behavior without inventing live learner-state evidence.",
            ("viz_computation_04",),
        ),
    ),
)


_AUDIT_APPLICATIONS = _make(
    "applications",
    _APP,
    "pub_applications_04",
    (
        (
            "Applied Claim-Review Dossiers",
            "Assemble source, figure, validator and limitation evidence for applied Active Inference claims.",
            "A dossier turns an applied explanation into an auditable packet instead of a persuasive story.",
            ("practice_app_domain_fit",),
        ),
        (
            "Misuse-Case Evidence Boundaries",
            "Mark where an applied example could be misused by treating pedagogical output as advice.",
            "Misuse boundaries are part of scientific quality when readers may transfer a model into practice.",
            ("sci_applications_04",),
        ),
        (
            "Reviewer Rubric Alignment",
            "Align reviewer rubrics with claim-support types and artifact validators.",
            "Rubric alignment makes review reproducible because the reviewer checks the same evidence classes as the build.",
            ("sci_applications_05",),
        ),
        (
            "Capstone Scientific Integrity Review",
            "Critique a full release packet for unsupported strong language and missing evidence classes.",
            "The capstone asks learners to red-team the manuscript, dashboard and curriculum as one scientific artifact.",
            ("sci_applications_06",),
        ),
    ),
)
