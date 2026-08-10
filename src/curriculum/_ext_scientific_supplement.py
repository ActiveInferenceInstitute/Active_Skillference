"""Scientific supplement expansion for VFE/EFE interpretation practice."""

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


def _scientific_skill(
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
    skill_id = f"sci_{prefix}_{index:02d}"
    prior = f"sci_{prefix}_{index - 1:02d}" if index > 1 else ""
    description = (
        f"{focus} This supplement skill asks learners to identify the claim, the "
        "mathematical object being inspected, the evidence that could falsify the "
        "interpretation, and the exact place where the result should appear in the "
        "provenance-bound manuscript or dashboard."
    )
    return _s(
        skill_id,
        name,
        stratum,
        objective,
        description,
        _dedupe((anchor, prior)),
        _q(
            f"What is the scientific role of {name} in the supplement?",
            [
                "It makes a mathematical claim inspectable and falsifiable.",
                "It lets the learner replace the derivation with an authority cue.",
                "It removes the need to connect the example to prerequisites.",
            ],
            0,
        ),
        tags=("scientific-supplement", "vfe-efe", prefix),
        related=related,
    )


def _make(
    prefix: str,
    stratum: Stratum,
    anchor: str,
    rows: tuple[tuple[str, str, str, tuple[str, ...]], ...],
) -> list[Skill]:
    return [
        _scientific_skill(
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


_SCI_MATH = _make(
    "math",
    _M,
    "m_convexity",
    (
        (
            "Variational Inequality Reading",
            "Read inequalities as claims about approximation error and admissible beliefs.",
            "A variational inequality is not decoration; it states which quantity is bounded and when equality can occur.",
            ("vm_elbo",),
        ),
        (
            "Jensen Step Audits",
            "Identify where Jensen's inequality enters an evidence-bound derivation.",
            "The supplement should make the concavity or convexity assumption visible before using a bound.",
            ("m_lagrange", "vm_free_energy"),
        ),
        (
            "Convexity and Local Optima",
            "Separate global convex arguments from local free-energy descent claims.",
            "Learners need to know whether a plotted descent demonstrates a global guarantee or a local diagnostic.",
            ("m_gradient_descent",),
        ),
        (
            "Gradient Field Interpretation",
            "Connect free-energy slopes to belief updates without overclaiming dynamics.",
            "A plotted gradient field teaches only when axes, objective, and update rule are explicit.",
            ("dyn_gradient_flow",),
        ),
        (
            "Fixed-Point Evidence Checks",
            "Treat posterior optima as fixed points that still need model assumptions.",
            "A fixed point in the bound is meaningful only relative to the likelihood and prior that define it.",
            ("dyn_fixed_point",),
        ),
        (
            "Lyapunov Framing Boundaries",
            "Explain when free-energy descent can and cannot be read as stability evidence.",
            "Lyapunov language should name the state, objective and neighbourhood, rather than imply universal stability.",
            ("dyn_stability",),
        ),
    ),
)


_SCI_PROBABILITY = _make(
    "probability",
    _P,
    "p_evidence",
    (
        (
            "Likelihood Audit Tables",
            "Separate likelihood entries, priors and posterior beliefs in worked examples.",
            "A likelihood audit prevents the answer from being hidden inside the observation model.",
            ("ai_matrix_A",),
        ),
        (
            "Evidence Probability Checks",
            "Track the normalising evidence term before interpreting surprise.",
            "The evidence term is the bridge between Bayes' rule and the free-energy bound.",
            ("vm_bayes_worked",),
        ),
        (
            "Posterior Calibration Review",
            "Compare posterior magnitude against base rates and diagnostic reliability.",
            "Calibration review keeps the supplement from treating high likelihood as high posterior probability.",
            ("p_bayes_theorem",),
        ),
        (
            "Observation-Model Boundary Cases",
            "State which observations the generative model can actually explain.",
            "Boundary observations show when the model structure is doing less work than the prose implies.",
            ("practice_prob_missing_data",),
        ),
        (
            "Base-Rate Trap Diagnostics",
            "Detect explanations that ignore low prior probability in favour of vivid evidence.",
            "Base-rate traps are useful because they make posterior reasoning testable for learners.",
            ("p_bayes_theorem",),
        ),
        (
            "Posterior Predictive Checks",
            "Ask what the inferred model predicts before trusting the fitted posterior.",
            "A posterior predictive check turns a completed derivation into an empirical question.",
            ("practice_prob_prior_predictive_check",),
        ),
    ),
)


_SCI_INFORMATION = _make(
    "information",
    _IT,
    "it_kl",
    (
        (
            "KL Geometry for Learners",
            "Explain KL divergence as a directional mismatch between beliefs.",
            "The supplement should state which distribution is the reference and which is the approximation.",
            ("geo_kl_divergence_local",),
        ),
        (
            "Entropy-Term Attribution",
            "Identify which term in a bound rewards uncertainty and which term penalises mismatch.",
            "Entropy attribution prevents learners from reading every free-energy decrease as accuracy alone.",
            ("it_entropy",),
        ),
        (
            "Information-Gain Decomposition",
            "Separate expected uncertainty reduction from pragmatic preference satisfaction.",
            "Information gain is the part of the example that explains epistemic action.",
            ("ai_epistemic_value",),
        ),
        (
            "Bound-Gap Interpretation",
            "Read the gap between free energy and surprise as approximation error.",
            "A bound gap is a diagnostic of mismatch, not an arbitrary visual distance on a plot.",
            ("vm_free_energy_tight",),
        ),
        (
            "Compression Tradeoff Notes",
            "Connect representation cost to the information retained for action.",
            "Compression tradeoffs help the supplement avoid treating all information as equally valuable.",
            ("front_info_predictive_efficiency",),
        ),
        (
            "Epistemic-Value Warnings",
            "State when expected information gain stops being the action-selection driver.",
            "The same information measure can support curiosity or be dominated by precision and preferences.",
            ("ai_precision_gamma",),
        ),
    ),
)


_SCI_VARIATIONAL = _make(
    "variational",
    _VM,
    "vm_free_energy",
    (
        (
            "ELBO and VFE Identity Checks",
            "Show why minimising VFE corresponds to maximising the ELBO.",
            "The supplement should name both signs of the objective so learners do not treat them as unrelated.",
            ("vm_elbo",),
        ),
        (
            "Bound-Tightness Demonstrations",
            "Recognise that the bound is tight only at the exact posterior.",
            "A tightness demonstration must identify the posterior and the model evidence it matches.",
            ("vm_free_energy_tight",),
        ),
        (
            "Approximation-Family Declarations",
            "State which recognition density family is allowed before interpreting fit.",
            "Approximation families determine what the learner can infer from a successful descent.",
            ("vm_mean_field",),
        ),
        (
            "Posterior-Mismatch Diagnostics",
            "Identify when a recognition density fits the wrong aspect of the posterior.",
            "Mismatch diagnostics are the scientific reason to plot the whole belief sweep.",
            ("vm_forward_reverse_kl",),
        ),
        (
            "Convergence Trace Reviews",
            "Distinguish monotone optimisation traces from evidence of model truth.",
            "A convergence trace shows objective behaviour, not automatic validity of the generative model.",
            ("practice_var_elbo_failure_modes",),
        ),
        (
            "Supplement Reading Lab",
            "Read the VFE supplement as a provenance-bound worked example.",
            "The reading lab connects derivation, plot, claim tokens and SkillTree quiz prompts in one audit path.",
            ("comp_provenance_gate",),
        ),
    ),
)


_SCI_FEP = _make(
    "fep",
    _FEP,
    "fep_statement",
    (
        (
            "Surprise-Bound Scope",
            "State the model-relative scope of a surprise-bound claim.",
            "The FEP supplement should keep surprise, evidence and model assumptions in the same sentence.",
            ("vm_free_energy",),
        ),
        (
            "Markov-Blanket Claim Boundaries",
            "Check whether a blanket claim names internal, external, sensory and active states.",
            "A blanket explanation becomes testable when the boundary variables are explicit.",
            ("fep_markov_blanket",),
        ),
        (
            "Process-Theory Caveats",
            "Separate the mathematical objective from a proposed biological process.",
            "Process claims need mechanism and timescale, not only a free-energy equation.",
            ("fep_predictive_processing",),
        ),
        (
            "Free-Energy Explanation Tests",
            "Ask what observation would make a free-energy explanation fail.",
            "A scientific free-energy explanation should expose the evidence that would change the model.",
            ("practice_fep_claim_boundary",),
        ),
        (
            "Falsification Boundary Notes",
            "Name the conditions under which an FEP example is outside scope.",
            "Boundary notes prevent the principle from becoming an unfalsifiable gloss.",
            ("app_limitations",),
        ),
        (
            "Timescale-Claim Reviews",
            "Check whether the explanation concerns perception, action, learning or development.",
            "Timescale review keeps fast belief updates separate from slow model changes.",
            ("front_fep_scale_separation",),
        ),
    ),
)


_SCI_ACTIVE_INFERENCE = _make(
    "active_inference",
    _AI,
    "ai_expected_free_energy",
    (
        (
            "EFE Term Separation",
            "Separate epistemic and pragmatic terms before comparing policies.",
            "The EFE supplement should make each plotted term traceable to a model component.",
            ("ai_epistemic_value", "ai_pragmatic_value"),
        ),
        (
            "Epistemic-Pragmatic Arbitration",
            "Explain when information seeking wins and when preference satisfaction dominates.",
            "Policy comparison is scientific only when both motives and their weights are visible.",
            ("ai_policy_selection",),
        ),
        (
            "Policy-Precision Sensitivity",
            "Inspect how precision changes the posterior over policies.",
            "A policy-precision sweep keeps the learner from reading one regime as a universal law.",
            ("ai_precision_gamma",),
        ),
        (
            "Regime-Switch Narratives",
            "Describe why an action preference changes across sensor precision.",
            "A regime switch teaches a boundary, not a contradiction in the theory.",
            ("practice_ai_counterfactual_debugging",),
        ),
        (
            "Preference-Design Checks",
            "State which outcomes the agent prefers before judging pragmatic value.",
            "Preference design is part of the scientific model, not an afterthought.",
            ("ai_matrix_C",),
        ),
        (
            "Action-Selection Failure Modes",
            "Recognise when the policy set or likelihood makes EFE comparison misleading.",
            "Failure-mode review prevents the supplement from overgeneralising a two-action example.",
            ("practice_ai_policy_space_design",),
        ),
    ),
)


_SCI_COMPUTATION = _make(
    "computation",
    _C,
    "comp_provenance_gate",
    (
        (
            "Kernel Trace Reading",
            "Follow a claim from kernel output through manuscript and dashboard artifacts.",
            "Trace reading makes each numerical statement reproducible instead of ornamental.",
            ("practice_comp_trace_artifacts",),
        ),
        (
            "Plot-Provenance Review",
            "Verify that figure annotations come from claims or generated graph data.",
            "Plot provenance prevents captions from introducing unchecked numerical claims.",
            ("comp_skilltree_export",),
        ),
        (
            "Numerical-Stability Checks",
            "Inspect clipping, normalisation and finite-log behaviour before trusting a plot.",
            "Stability checks protect VFE and EFE examples from plausible but invalid floating-point output.",
            ("impl_logsumexp",),
        ),
        (
            "Sweep-Diagnostic Artifacts",
            "Use parameter sweeps to expose regimes, boundaries and failure cases.",
            "A sweep diagnostic turns one worked example into a falsifiable family of cases.",
            ("comp_efe_eval",),
        ),
        (
            "Artifact Manifest Audits",
            "Confirm that supplement figures are registered, rendered and dashboard-exposed.",
            "The manifest audit catches the false demo where a plot exists but the manuscript or dashboard omits it.",
            ("next_repro_sim_labs_05",),
        ),
        (
            "Reproducible Supplement Checks",
            "Rerun kernel, figure, export and render checks as one supplement contract.",
            "The supplement is complete only when the same commands regenerate its claims, figures and routes.",
            ("next_repro_sim_labs_06",),
        ),
    ),
)


_SCI_APPLICATIONS = _make(
    "applications",
    _APP,
    "practice_app_domain_fit",
    (
        (
            "Scientific Evidence Dossiers",
            "Bundle sources, model assumptions and validation evidence for applied claims.",
            "An evidence dossier keeps an application from borrowing confidence from the theory alone.",
            ("next_applied_eval_dossiers_01",),
        ),
        (
            "Source-to-Claim Tables",
            "Map each applied statement to a cited source, kernel claim or limitation.",
            "A source-to-claim table makes scholarly support inspectable at review time.",
            ("next_applied_eval_dossiers_02",),
        ),
        (
            "Overclaim Detection",
            "Find places where a domain story outruns the validated model.",
            "Overclaim detection is the applied counterpart of bound-gap interpretation.",
            ("app_limitations",),
        ),
        (
            "Misuse-Case Framing",
            "State how a concept could be misapplied in a real decision context.",
            "Misuse cases turn ethical boundaries into learner-assessable content.",
            ("practice_app_ethics_and_misuse",),
        ),
        (
            "Review-Rubric Construction",
            "Create a compact rubric for judging applied VFE/EFE explanations.",
            "A rubric makes expert review repeatable across capstone submissions.",
            ("next_applied_eval_dossiers_03",),
        ),
        (
            "Capstone Critique Studio",
            "Apply the supplement's scientific checks to a learner's final application.",
            "The capstone critique closes the loop from mathematical example to responsible applied use.",
            ("app_curriculum_capstone",),
        ),
    ),
)
