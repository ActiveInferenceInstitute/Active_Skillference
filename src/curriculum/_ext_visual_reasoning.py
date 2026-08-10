"""Visual reasoning and manuscript-review curriculum expansion."""

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


def _visual_skill(
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
    skill_id = f"viz_{prefix}_{index:02d}"
    prior = f"viz_{prefix}_{index - 1:02d}" if index > 1 else ""
    description = (
        f"{focus} Learners practice reading a visualization as a claim with a data "
        "source, visual encoding, caption boundary, and validation path. The goal is "
        "to make figures useful for manuscript review, dashboard inspection, and "
        "SkillTree learning rather than decorative confirmation."
    )
    return _s(
        skill_id,
        name,
        stratum,
        objective,
        description,
        _dedupe((anchor, prior)),
        _q(
            f"What makes {name} a rigorous visualization skill?",
            [
                "It names the data source, encoding, inference boundary, and validation check.",
                "It replaces a prerequisite with a more memorable image.",
                "It lets the author hide uncertainty in a caption.",
            ],
            0,
        ),
        tags=("visual-reasoning", "manuscript-review", prefix),
        related=related,
    )


def _make(
    prefix: str,
    stratum: Stratum,
    anchor: str,
    rows: tuple[tuple[str, str, str, tuple[str, ...]], ...],
) -> list[Skill]:
    return [
        _visual_skill(
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


_VIS_MATH = _make(
    "math",
    _M,
    "m_matrix",
    (
        (
            "Axis and Scale Contracts",
            "Audit axes, units and scale choices before interpreting a mathematical plot.",
            "A mathematical figure is only reviewable when axis variables, transformations and units are explicit.",
            ("m_functions_real", "m_convexity"),
        ),
        (
            "Matrix Heatmap Reading",
            "Read heatmaps as structured arrays rather than coloured decoration.",
            "Heatmap literacy connects rows, columns, colour scales and zero cells to the underlying matrix.",
            ("m_dotproduct",),
        ),
        (
            "Slope and Curvature Marks",
            "Use visual slope and curvature cues to interpret optimisation claims.",
            "Slope annotations help learners distinguish monotone descent from unsupported claims about global optima.",
            ("m_gradient_descent", "sci_math_03"),
        ),
        (
            "Dimensional Reduction Warnings",
            "State what is lost when a high-dimensional model is shown in two visual coordinates.",
            "Projection warnings keep compact figures from overclaiming what a viewer can infer.",
            ("geo_statistical_manifold",),
        ),
    ),
)


_VIS_PROBABILITY = _make(
    "probability",
    _P,
    "p_bayes_theorem",
    (
        (
            "Calibration Plot Reading",
            "Use calibration visuals to compare predicted probability with observed frequency.",
            "Calibration plots prevent a posterior or classifier score from being treated as automatically reliable.",
            ("practice_prob_prior_predictive_check",),
        ),
        (
            "Likelihood Diagram Audits",
            "Check whether a probability diagram separates prior, likelihood and posterior roles.",
            "Likelihood diagrams are useful when the observation model is visible instead of implied by prose.",
            ("sci_probability_01",),
        ),
        (
            "Posterior Predictive Visuals",
            "Read posterior predictive checks as model criticism rather than as a fitted-value celebration.",
            "Predictive visuals ask what the model would generate after inference and where that generation fails.",
            ("sci_probability_06",),
        ),
        (
            "Uncertainty Interval Captions",
            "Write captions that state what an uncertainty interval covers and what it excludes.",
            "Intervals communicate uncertainty only when their target, conditioning assumptions and exclusions are named.",
            ("p_gaussian",),
        ),
    ),
)


_VIS_INFORMATION = _make(
    "information",
    _IT,
    "it_mutual_information",
    (
        (
            "Entropy Surface Interpretation",
            "Connect entropy heatmaps to distributions and uncertainty changes.",
            "Entropy surfaces should reveal uncertainty structure without implying semantic value by themselves.",
            ("it_entropy",),
        ),
        (
            "KL Asymmetry Visuals",
            "Explain why reversing KL arguments changes the visual and scientific interpretation.",
            "A KL figure must name the reference distribution so directionality is not hidden.",
            ("sci_information_01",),
        ),
        (
            "Information-Gain Panel Design",
            "Design panels that separate epistemic value from pragmatic value.",
            "Information-gain figures prevent expected free energy from collapsing into one uninspected score.",
            ("sci_information_03", "ai_epistemic_value"),
        ),
        (
            "Channel Diagram Captions",
            "Caption source, channel and outcome variables in information-flow diagrams.",
            "Channel diagrams are interpretable only when the viewer can locate the random variables being related.",
            ("it_channel",),
        ),
    ),
)


_VIS_VARIATIONAL = _make(
    "variational",
    _VM,
    "vm_free_energy",
    (
        (
            "Bound-Gap Figure Reading",
            "Read a free-energy gap as approximation error under stated model assumptions.",
            "Bound-gap visuals need both the bound and the evidence reference line to be scientifically meaningful.",
            ("sci_variational_02",),
        ),
        (
            "Optimisation Trace Diagnostics",
            "Separate descent traces, convergence claims and model-validity claims.",
            "Trace diagnostics keep an improving objective from being mistaken for proof that the model is true.",
            ("sci_variational_05",),
        ),
        (
            "Approximation-Family Sketches",
            "Use simple sketches to show which recognition densities are admissible.",
            "Approximation-family sketches clarify what kind of posterior mismatch a learner should look for.",
            ("sci_variational_03",),
        ),
        (
            "Message-Passing Diagram Reviews",
            "Check that message-passing diagrams expose factor roles and update direction.",
            "A message-passing diagram should support algorithmic review rather than only naming variables.",
            ("vm_message_passing",),
        ),
    ),
)


_VIS_FEP = _make(
    "fep",
    _FEP,
    "fep_statement",
    (
        (
            "Markov Blanket Diagram Boundaries",
            "Caption blanket diagrams with the partition and conditional-independence claim they express.",
            "Blanket diagrams become misleading when sensory, active, internal and external states are not separated.",
            ("fep_markov_blanket",),
        ),
        (
            "Timescale Layer Figures",
            "Show which process unfolds at which timescale in an FEP explanation.",
            "Layered timescale figures prevent rapid inference and slow learning from being conflated.",
            ("learn_timescales",),
        ),
        (
            "Process-Theory Caveat Marks",
            "Attach visual caveats to predictive-processing or self-organisation explanations.",
            "Caveat marks force the figure to state when a process-theory reading is schematic rather than measured.",
            ("sci_fep_03",),
        ),
        (
            "Falsification Flow Charts",
            "Draw what observation or intervention would count against an FEP interpretation.",
            "A falsification chart turns a broad principle into a reviewable scientific claim.",
            ("sci_fep_05",),
        ),
    ),
)


_VIS_ACTIVE_INFERENCE = _make(
    "active_inference",
    _AI,
    "ai_expected_free_energy",
    (
        (
            "Policy Comparison Panels",
            "Compare policies with visible epistemic and pragmatic terms.",
            "Policy panels should show why one action wins rather than hiding the choice inside a scalar total.",
            ("sci_active_inference_01",),
        ),
        (
            "Precision Sweep Visuals",
            "Use sweeps to show when policy preference changes across precision regimes.",
            "Precision sweep visuals make regime dependence visible before learners generalise an action claim.",
            ("sci_active_inference_03",),
        ),
        (
            "Preference Surface Maps",
            "Map how preferences shape pragmatic value without treating them as observations.",
            "Preference surfaces help learners inspect normative inputs separately from evidence.",
            ("ai_matrix_C",),
        ),
        (
            "Failure-Mode Panels",
            "Visualise ambiguity, risk and misspecified policy spaces in active-inference examples.",
            "Failure-mode panels make misuse and boundary cases part of the learning object.",
            ("ai_risk_ambiguity", "practice_ai_counterfactual_debugging"),
        ),
    ),
)


_VIS_COMPUTATION = _make(
    "computation",
    _C,
    "comp_visualization",
    (
        (
            "Figure Registry Audits",
            "Check that generated figure metadata matches manuscript declarations and dashboard artifacts.",
            "Registry audits make labels, filenames, captions and alt text part of the executable contract.",
            ("comp_provenance_gate",),
        ),
        (
            "Nonblank Image Checks",
            "Validate that a rendered figure contains information rather than an empty placeholder.",
            "Nonblank checks catch silent rendering failures that structure-only tests would miss.",
            ("os_computation_07",),
        ),
        (
            "Dashboard Exploration Controls",
            "Design filters and tables that make graph diagnostics inspectable without changing learner state.",
            "Dashboard controls should expose data for review while leaving SkillTree as the system of record.",
            ("comp_skilltree_export",),
        ),
        (
            "Manifest-to-Caption Traceability",
            "Trace every figure caption back to the data artifact and generator that support it.",
            "Traceability keeps manuscript visuals synchronized with regenerated JSON and source code.",
            ("sci_computation_05",),
        ),
    ),
)


_VIS_APPLICATIONS = _make(
    "applications",
    _APP,
    "practice_app_domain_fit",
    (
        (
            "Evidence-Dossier Visuals",
            "Turn source-to-claim dossiers into figures that show what supports each applied claim.",
            "Dossier visuals prevent applied examples from looking stronger than their source matrix warrants.",
            ("sci_applications_01",),
        ),
        (
            "Review-Rubric Dashboards",
            "Build compact dashboards for scoring claim scope, evidence quality and misuse risk.",
            "Rubric dashboards make expert review criteria visible and repeatable.",
            ("sci_applications_05",),
        ),
        (
            "Misuse-Risk Visual Summaries",
            "Visualise where an application could manipulate preferences or hide uncertainty.",
            "Misuse summaries keep ethical risks attached to the same artifacts that teach the model.",
            ("practice_app_ethics_and_misuse",),
        ),
        (
            "Stakeholder Explanation Captions",
            "Write captions that communicate model limits to non-specialist stakeholders.",
            "Stakeholder captions translate technical visuals without dropping the assumptions or caveats.",
            ("app_curriculum_capstone",),
        ),
    ),
)
