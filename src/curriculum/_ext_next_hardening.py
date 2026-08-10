"""Next hardening expansion: dynamics, diagnostics, and evaluation practice."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

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


def _hardening_skill(
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
    skill_id = f"next_{prefix}_{index:02d}"
    prior = f"next_{prefix}_{index - 1:02d}" if index > 1 else ""
    description = (
        f"{focus} This hardening skill asks the learner to make the modelling "
        "commitment explicit, name the evidence that would falsify it, and connect "
        "the move back to the prerequisite graph before applying it downstream."
    )
    return _s(
        skill_id,
        name,
        stratum,
        objective,
        description,
        _dedupe((anchor, prior)),
        _q(
            f"What does {name} add to the learning path?",
            [
                (
                    f"A checkable modelling commitment from {name} that a later skill can "
                    "reuse"
                ),
                f"A decorative topic label for {name} with no prerequisite meaning",
                f"A way for {name} to avoid stating the assumptions in its example",
            ],
            0,
        ),
        _q(
            f"Which failure mode should a learner watch for when using {name}?",
            [
                f"Treating {name} as valid outside the assumptions it actually requires",
                f"Documenting the prerequisites of {name} before applying the method",
                f"Testing the worked example in {name} against a boundary case",
            ],
            0,
        ),
        tags=("hardening", "diagnostics", prefix),
        related=related,
    )


def _make(
    prefix: str,
    stratum: Stratum,
    anchor: str,
    rows: tuple[tuple[str, str, str, tuple[str, ...]], ...],
) -> list[Skill]:
    return [
        _hardening_skill(
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


_NEXT_CONTINUOUS_DYNAMICS = _make(
    "continuous_dynamics",
    _M,
    "m_derivative",
    (
        (
            "Continuous-Time State Variables",
            "Represent evolving hidden states as trajectories rather than isolated values.",
            "Continuous-time examples begin by separating a state, its derivative, and the observation that samples it.",
            ("dyn_state_space",),
        ),
        (
            "Flow-Field Sketches",
            "Read vector-field diagrams as local commitments about state change.",
            "A flow-field sketch helps learners see whether an assumed direction of change is stable, unstable, or under-specified.",
            ("m_vectors",),
        ),
        (
            "Fixed-Point Stability Checks",
            "Classify local attractors before interpreting a dynamical example.",
            "Stability checks prevent a learner from treating any stationary point as an explanatory attractor.",
            ("m_jacobian_hessian",),
        ),
        (
            "Timescale Separation Heuristics",
            "State which variables are slow, fast, or held fixed in an argument.",
            "A timescale claim is meaningful only when the learner can identify what changes faster than what.",
            ("front_fep_scale_separation",),
        ),
        (
            "Noisy Flow Intuitions",
            "Distinguish deterministic drift from diffusion in a process model.",
            "Noisy dynamics require learners to separate the expected motion from the uncertainty around it.",
            ("dyn_fokker_planck",),
        ),
        (
            "Trajectory Boundary Cases",
            "Use boundary trajectories to find where a continuous model stops teaching.",
            "Boundary cases reveal whether the continuous story is robust or only a polished central example.",
            ("practice_math_sensitivity_probe",),
        ),
    ),
)


_NEXT_STATE_SPACE_PROBABILITY = _make(
    "state_space_probability",
    _P,
    "p_markov_chain",
    (
        (
            "State-Space Storyboards",
            "Turn a temporal scenario into hidden states, observations, and transitions.",
            "State-space storyboards keep learners from mixing the latent process with the measurement channel.",
            ("front_prob_graphical_models",),
        ),
        (
            "Transition-Matrix Audits",
            "Check that transition rows encode possible movement and remain normalized.",
            "A transition matrix is a behavioural claim, not just a table of probabilities.",
            ("ai_matrix_B",),
        ),
        (
            "Emission-Model Audits",
            "Separate sensory likelihoods from beliefs about the hidden state.",
            "Emission audits catch examples where the answer is smuggled into the observation model.",
            ("ai_matrix_A",),
        ),
        (
            "Filtering Recursion Walkthroughs",
            "Trace prediction and correction steps in a temporal inference loop.",
            "Filtering is teachable when each prior-to-posterior update is visible.",
            ("front_prob_filtering_smoothing",),
        ),
        (
            "Smoothing Versus Filtering",
            "Explain whether future evidence is allowed to revise a past state estimate.",
            "Learners need to know whether an estimate uses only past evidence or the whole trajectory.",
            ("p_stochastic_process",),
        ),
        (
            "State-Space Stress Tests",
            "Probe what happens when a state, observation, or transition is missing.",
            "Stress tests show whether the model degrades intelligibly when the scenario is incomplete.",
            ("practice_prob_missing_data",),
        ),
    ),
)


_NEXT_RATE_DISTORTION_INFO = _make(
    "rate_distortion_info",
    _IT,
    "it_mutual_information",
    (
        (
            "Rate-Distortion Tradeoffs",
            "Describe how much compression a task can tolerate before behaviour fails.",
            "Rate-distortion examples connect information budgets to the quality of a downstream decision.",
            ("front_info_predictive_efficiency",),
        ),
        (
            "Task-Relevant Compression",
            "Keep information that matters for action while discarding nuisance detail.",
            "Compression is not just smaller representation; it is a choice about which errors matter.",
            ("front_info_semantic_information",),
        ),
        (
            "Channel-Capacity Teaching Cases",
            "Compare what a learner can infer under narrow and wide observation channels.",
            "A channel-capacity case makes sensing limitations concrete before policy selection.",
            ("it_channel",),
        ),
        (
            "Information Bottleneck Diagrams",
            "Draw encoder, bottleneck, and target variables for a learning example.",
            "Bottleneck diagrams expose which variable a representation is meant to preserve.",
            ("front_info_predictive_efficiency",),
        ),
        (
            "Distortion-Loss Checklists",
            "Name the error function before comparing compressed representations.",
            "A distortion loss records which mistake the curriculum is willing to pay for.",
            ("it_cross_entropy",),
        ),
        (
            "Value-of-Information Triage",
            "Prioritize observations by expected decision value rather than raw novelty.",
            "Information value is a control question when sensing has a cost.",
            ("ai_epistemic_value",),
        ),
    ),
)


_NEXT_CONTINUOUS_VARIATIONAL = _make(
    "continuous_variational",
    _VM,
    "vm_free_energy",
    (
        (
            "Continuous Recognition Densities",
            "Use parametric densities to represent beliefs over continuous states.",
            "Continuous variational examples require the learner to track both support and parameterisation.",
            ("p_gaussian",),
        ),
        (
            "Functional Free-Energy Terms",
            "Distinguish energy and entropy terms in a continuous variational objective.",
            "The continuous objective is clearer when learners can point to expectation, entropy, and model terms separately.",
            ("m_functional",),
        ),
        (
            "Pathwise Gradient Intuitions",
            "Explain when gradients can move through sampled latent variables.",
            "Pathwise gradients make the approximation inspectable instead of a black-box optimizer.",
            ("impl_vi_gradient",),
        ),
        (
            "Laplace Approximation Checks",
            "State when a local Gaussian approximation is credible.",
            "A Laplace example must say what curvature and local-mode assumptions it is using.",
            ("vm_forward_reverse_kl",),
        ),
        (
            "Continuous Message Passing",
            "Map message-passing ideas onto continuous sufficient statistics.",
            "Continuous messages should preserve the meaning of uncertainty, not only the mean estimate.",
            ("vm_message_passing",),
        ),
        (
            "Approximation Boundary Audits",
            "Find cases where a continuous approximation hides multi-modality or tail risk.",
            "Approximation audits prevent learners from confusing smoothness with truth.",
            ("practice_var_elbo_failure_modes",),
        ),
    ),
)
# The Laplace-checks hardening skill builds directly on the Laplace approximation, so
# bind it as a real prerequisite (the ladder anchor alone does not reach vm_laplace).
_NEXT_CONTINUOUS_VARIATIONAL = [
    replace(skill, prerequisites=_dedupe(skill.prerequisites + ("vm_laplace",)))
    if skill.skill_id == "next_continuous_variational_04"
    else skill
    for skill in _NEXT_CONTINUOUS_VARIATIONAL
]


_NEXT_PREDICTIVE_CODING_PROCESS = _make(
    "predictive_coding_process",
    _FEP,
    "fep_predictive_processing",
    (
        (
            "Prediction-Error Units",
            "Identify where prediction error is computed in a hierarchical example.",
            "Predictive-coding process theory begins with the local comparison between expected and observed signals.",
            ("hier_prediction_error_passing",),
        ),
        (
            "Precision-Weighted Error",
            "Explain how precision changes the effect of an error signal.",
            "Precision weighting turns an error into a control-relevant message rather than a raw discrepancy.",
            ("fep_precision",),
        ),
        (
            "Top-Down Prediction Paths",
            "Trace how a higher-level expectation constrains lower-level inference.",
            "A top-down path is credible only when the learner can name what is predicted and where it is compared.",
            ("hier_empirical_priors",),
        ),
        (
            "Bottom-Up Error Paths",
            "Trace how unresolved error changes higher-level beliefs.",
            "Bottom-up messages should be read as pressure to revise a hypothesis, not as direct facts.",
            ("app_predictive_brain",),
        ),
        (
            "Action as Error Resolution",
            "Distinguish perceptual belief change from action that changes observations.",
            "Active error resolution asks whether the agent should update beliefs or sample the world differently.",
            ("fep_action",),
        ),
        (
            "Predictive-Coding Failure Cases",
            "Use precision, hierarchy, and action failures to bound predictive-coding claims.",
            "Failure cases keep predictive-coding explanations from becoming unfalsifiable stories.",
            ("practice_fep_claim_boundary",),
        ),
    ),
)


_NEXT_HIERARCHICAL_ACTIVE_INFERENCE = _make(
    "hierarchical_active_inference",
    _AI,
    "ai_hierarchical",
    (
        (
            "Hierarchical Policy Contexts",
            "Represent policies at nested temporal and spatial scales.",
            "Hierarchical policies make the planning level an explicit modelling choice.",
            ("hier_temporal_depth_policies",),
        ),
        (
            "Empirical-Prior Handoffs",
            "Explain how one level supplies priors for another level.",
            "Empirical-prior handoffs teach learners to inspect where a higher-level belief enters a lower-level update.",
            ("hier_empirical_priors",),
        ),
        (
            "Nested Preference Design",
            "Separate immediate preferences from slower contextual goals.",
            "Nested preferences prevent a model from hiding long-horizon commitments in a single reward-like term.",
            ("ai_matrix_C",),
        ),
        (
            "Multi-Level Epistemic Action",
            "Show when exploration reduces uncertainty at a local or contextual level.",
            "Exploration can target a sensory detail, a task structure, or a policy context.",
            ("ai_epistemic_value",),
        ),
        (
            "Hierarchical Habit Formation",
            "Distinguish repeated local actions from stable higher-level routines.",
            "Habit examples improve when learners can name the level at which repetition is being learned.",
            ("ai_habits",),
        ),
        (
            "Hierarchy Debugging Studios",
            "Find level-confusion bugs in active-inference examples.",
            "Hierarchy debugging asks whether each variable belongs to the level where it is used.",
            ("practice_ai_counterfactual_debugging",),
        ),
    ),
)


_NEXT_REPRO_SIM_LABS = _make(
    "repro_sim_labs",
    _C,
    "impl_reproducibility",
    (
        (
            "Seeded Simulation Contracts",
            "Pin random seeds and expected traces for educational simulations.",
            "A seeded simulation lets learners reproduce a claim before modifying the example.",
            ("comp_determinism",),
        ),
        (
            "Trace Schema Design",
            "Write machine-readable traces for beliefs, actions, and free-energy terms.",
            "Trace schemas turn a simulation into evidence that validators and dashboards can inspect.",
            ("front_comp_schema_validation",),
        ),
        (
            "Notebook-to-Test Promotion",
            "Move a successful notebook example into a repeatable test or script.",
            "Public notebooks become durable when the important checks survive outside the notebook UI.",
            ("os_computation_01",),
        ),
        (
            "Batch Simulation Sweeps",
            "Run parameter sweeps that expose regime changes instead of a single happy path.",
            "Sweeps help learners see where an agent switches behaviour or fails.",
            ("comp_efe_eval",),
        ),
        (
            "Artifact Manifest Reviews",
            "Check that every generated output has a producer, consumer, and validator.",
            "A manifest review prevents polished dashboards from hiding stale artifacts.",
            ("os_computation_04",),
        ),
        (
            "Reproducibility Incident Drills",
            "Practice diagnosing a changed output back to data, code, or environment.",
            "Incident drills teach maintainers how to respond when reproducibility fails.",
            ("front_comp_replay_harness",),
        ),
    ),
)


_NEXT_APPLIED_EVAL_DOSSIERS = _make(
    "applied_eval_dossiers",
    _APP,
    "app_curriculum_capstone",
    (
        (
            "Application Source Dossiers",
            "Collect sources, assumptions, and boundaries before an applied lesson.",
            "A source dossier gives learners the evidence envelope for an application claim.",
            ("os_applications_08",),
        ),
        (
            "Claim-to-Evidence Tables",
            "Map each applied claim to the source or generated artifact that supports it.",
            "Claim tables keep applications from outrunning their evidence.",
            ("practice_app_domain_fit",),
        ),
        (
            "Evaluation Metric Selection",
            "Choose metrics that match the applied learning objective and boundary.",
            "An evaluation metric should test the behaviour the lesson claims to teach.",
            ("practice_app_evaluation_design",),
        ),
        (
            "Misuse-Case Reviews",
            "State how an active-inference example could be overclaimed or misapplied.",
            "Misuse reviews make scope boundaries part of the learner's assessment.",
            ("app_limitations",),
        ),
        (
            "Community Feedback Loops",
            "Design review loops that let learners and maintainers improve applied material.",
            "Feedback loops turn public education into an inspectable process rather than a static release.",
            ("os_applications_02",),
        ),
        (
            "Capstone Evidence Audits",
            "Review a full applied capstone for source, model, metric, and visualization integrity.",
            "The capstone audit asks whether every applied move remains connected to the validated graph.",
            ("app_active_learning",),
        ),
    ),
)
