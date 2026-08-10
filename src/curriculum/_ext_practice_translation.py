"""Practice and translation curriculum expansion.

These subjects add worked-practice skills that bridge the formal theory to the
learner behaviours a SkillTree course should train: checking assumptions, spotting
model failures, designing policies, testing implementations, and translating the
framework into applied settings.
"""

from __future__ import annotations

from src.curriculum._ext_helpers import _AI, _APP, _C, _FEP, _IT, _M, _P, _VM, _q, _s

_PRACTICE_MATH = [
    _s(
        "practice_math_dimension_check",
        "Dimension Checks for Generative Models",
        _M,
        "Verify that vectors, matrices and gradients have compatible shapes before using them.",
        "A shape mismatch is often the earliest visible sign that a generative model has "
        "confused states, observations, actions or parameters. Learners practice reading "
        "each symbol through its domain, codomain and role in the update equation before "
        "trusting any optimisation step.",
        ("m_matrix", "m_jacobian_hessian"),
        _q(
            "What should a learner check before multiplying a likelihood matrix by a belief vector?",
            [
                "That the matrix columns match the belief states it is meant to score",
                "That the matrix has more rows than columns",
                "That every entry was produced by gradient descent",
            ],
            0,
        ),
        _q(
            "A dimension check is most useful because it catches:",
            [
                "Role confusion between mathematical objects",
                "Numerical rounding error",
                "Slow execution speed",
            ],
            0,
        ),
        tags=("practice", "math"),
    ),
    _s(
        "practice_math_assumption_checklist",
        "Assumption Checklists for Derivations",
        _M,
        "State the differentiability, convexity and normalisation assumptions used in a derivation.",
        "Many active-inference derivations silently rely on smooth objectives, valid "
        "probability simplices, or convex approximations. This skill trains learners to "
        "write the assumptions beside the calculation so later failures are diagnosable "
        "instead of mysterious.",
        ("m_convexity", "m_lagrange", "m_simplex"),
        _q(
            "Why attach assumptions to a derivation?",
            [
                "So the learner knows when the result can legitimately be reused",
                "So the proof can ignore its prerequisites",
                "So every distribution becomes Gaussian",
            ],
            0,
        ),
        _q(
            "A normalisation assumption is especially relevant when optimising over:",
            [
                "A probability vector on the simplex",
                "An unconstrained real-valued vector",
                "A set of independent binary flags",
            ],
            0,
        ),
        tags=("practice", "math"),
    ),
    _s(
        "practice_math_sensitivity_probe",
        "Sensitivity Probes for Approximation Errors",
        _M,
        "Probe how local approximations change when curvature or step size changes.",
        "Taylor, Laplace and gradient-based approximations can look precise while hiding "
        "sensitivity to curvature and update size. Learners vary the local assumptions and "
        "explain whether the same qualitative inference still holds.",
        ("m_taylor", "m_gradient_descent", "m_jacobian_hessian"),
        _q(
            "A sensitivity probe asks whether a conclusion survives changes to:",
            [
                "Curvature, step size or local approximation assumptions",
                "Only how the final number is rounded",
                "Only the choice of variable names",
            ],
            0,
        ),
        _q(
            "Which mathematical object is most directly tied to local curvature?",
            ["The Hessian", "The gradient vector", "The Jacobian matrix"],
            0,
        ),
        tags=("practice", "math"),
    ),
]

_PRACTICE_PROBABILITY = [
    _s(
        "practice_prob_story_to_factorisation",
        "From Story to Probabilistic Factorisation",
        _P,
        "Translate a verbal scenario into variables, dependencies and a joint factorisation.",
        "Before a learner can perform Bayesian inference, they must decide what the model "
        "claims exists and how those variables depend on one another. This skill turns a "
        "narrative into an explicit factorisation that can be checked and revised.",
        ("p_joint_marginal", "front_prob_graphical_models"),
        _q(
            "What is the main product of translating a modelling story?",
            [
                "An explicit variable set and joint factorisation",
                "A fixed reward table",
                "A single summary statistic",
            ],
            0,
        ),
        _q(
            "A probabilistic factorisation makes it easier to inspect:",
            [
                "Which dependencies the model assumes",
                "The exact posterior values",
                "The optimal policy to follow",
            ],
            0,
        ),
        tags=("practice", "probability"),
    ),
    _s(
        "practice_prob_missing_data",
        "Missing Data and Observation Masks",
        _P,
        "Represent absent observations without pretending they are observed outcomes.",
        "An unobserved value should not be treated as a surprising observed value. Learners "
        "practice separating missingness, censoring and noisy observation so inference "
        "updates only on evidence that actually exists.",
        ("p_cond_independence", "front_prob_filtering_smoothing"),
        _q(
            "Why should missing data not be encoded as an ordinary observation?",
            [
                "Because absence of evidence is not the same likelihood event",
                "Because it always proves the prior is wrong",
                "Because it removes the need for a generative model",
            ],
            0,
        ),
        _q(
            "An observation mask primarily indicates:",
            [
                "Which evidence was actually available",
                "Which action must be selected",
                "Which prior was assumed",
            ],
            0,
        ),
        tags=("practice", "probability"),
    ),
    _s(
        "practice_prob_prior_predictive_check",
        "Prior Predictive Checks",
        _P,
        "Use simulated observations from the prior to detect implausible model assumptions.",
        "Prior predictive checks ask what the model expects before seeing data. If simulated "
        "observations are impossible, trivial or wildly off-domain, the learner should repair "
        "the priors or likelihood before interpreting posterior beliefs.",
        ("p_monte_carlo", "p_evidence"),
        _q(
            "A prior predictive check examines:",
            [
                "Observations simulated before conditioning on new data",
                "Only posterior means after inference",
                "The order in which data arrived",
            ],
            0,
        ),
        _q(
            "Implausible prior predictive samples usually point to a problem in:",
            [
                "The prior or likelihood",
                "The data-preprocessing pipeline",
                "The number of posterior draws",
            ],
            0,
        ),
        tags=("practice", "probability"),
    ),
]

_PRACTICE_INFORMATION = [
    _s(
        "practice_info_surprise_decomposition",
        "Surprise Decomposition Practice",
        _IT,
        "Separate surprise due to model mismatch from surprise due to rare but expected events.",
        "A surprising observation can mean the model is wrong, or it can be a rare event the "
        "model already expected to happen sometimes. Learners practice using entropy, KL "
        "and model evidence language to avoid over-interpreting a single outcome.",
        ("it_surprise", "it_kl", "p_evidence"),
        _q(
            "Why distinguish rare expected events from model mismatch?",
            [
                "They imply different repairs to the generative model",
                "They always produce the same posterior",
                "They remove the need for entropy",
            ],
            0,
        ),
        _q(
            "Which quantity measures distributional mismatch?",
            ["KL divergence", "A subject count", "A route name"],
            0,
        ),
        tags=("practice", "information"),
    ),
    _s(
        "practice_info_information_budget",
        "Information Budgets for Learning Paths",
        _IT,
        "Estimate what information a learner gains from an observation, exercise or intervention.",
        "Information gain is not just a formula inside expected free energy; it is also a "
        "design lens for curriculum. Learners identify which uncertainty a practice item "
        "reduces and whether that reduction is worth its cognitive cost.",
        ("it_info_gain", "front_info_predictive_efficiency"),
        _q(
            "An information budget asks whether an activity reduces:",
            [
                "A relevant uncertainty at acceptable cost",
                "Only the number of subjects",
                "The need for prerequisites",
            ],
            0,
        ),
        _q(
            "A high-value diagnostic exercise should reveal:",
            [
                "Which misconception or uncertainty remains",
                "Only whether the export file exists",
                "The learner's terminal theme",
            ],
            0,
        ),
        tags=("practice", "information"),
    ),
    _s(
        "practice_info_channel_audit",
        "Channel Audits for Observations",
        _IT,
        "Evaluate whether an observation channel can actually carry the distinction a model needs.",
        "An active-inference model can ask for observations that the available channel cannot "
        "distinguish. Learners audit channels for noise, compression and confounding before "
        "trusting information gain or policy comparisons.",
        ("it_channel", "front_info_active_sensing_channels"),
        _q(
            "A channel audit asks whether observations can carry:",
            [
                "The distinction the model needs to infer",
                "Unlimited information regardless of noise",
                "A signal that is immune to compression loss",
            ],
            0,
        ),
        _q(
            "Noise and compression matter because they can reduce:",
            [
                "Usable information",
                "The source's intrinsic entropy",
                "The size of the symbol alphabet",
            ],
            0,
        ),
        tags=("practice", "information"),
    ),
]

_PRACTICE_VARIATIONAL = [
    _s(
        "practice_var_approximation_choice",
        "Choosing a Variational Approximation",
        _VM,
        "Select a recognition density family that matches the inference question and failure risks.",
        "A variational approximation is a modelling decision, not an implementation detail. "
        "Learners compare mean-field, Laplace, amortised and flow-based choices by the "
        "dependencies they keep, the dependencies they drop and the errors they invite.",
        ("vm_mean_field", "vm_laplace", "front_var_normalising_flows"),
        _q(
            "Why is the recognition density family a modelling decision?",
            [
                "It determines which posterior dependencies can be represented",
                "It only changes variable names",
                "It guarantees exact inference",
            ],
            0,
        ),
        _q(
            "Mean-field approximations are risky when the posterior has strong:",
            ["Dependencies between factors", "File permissions", "Subject labels"],
            0,
        ),
        tags=("practice", "variational"),
    ),
    _s(
        "practice_var_elbo_failure_modes",
        "ELBO Failure Mode Diagnosis",
        _VM,
        "Diagnose loose bounds, poor local optima and misleading convergence in variational inference.",
        "A stable free-energy trace can still reflect a poor approximation or a bad local "
        "optimum. Learners inspect initialisation, posterior checks and alternative "
        "approximations before treating convergence as correctness.",
        ("vm_elbo", "vm_free_energy_tight", "front_var_black_box_vi"),
        _q(
            "Why can a converged ELBO still be misleading?",
            [
                "It may reflect a poor approximation or local optimum",
                "It always proves exact posterior recovery",
                "It removes the need for posterior checks",
            ],
            0,
        ),
        _q(
            "A useful ELBO diagnosis compares convergence with:",
            [
                "Posterior checks and alternative starts or approximations",
                "Only generated file size",
                "The number of navigation links",
            ],
            0,
        ),
        tags=("practice", "variational"),
    ),
    _s(
        "practice_var_message_trace",
        "Message Trace Reviews",
        _VM,
        "Trace which variables send which messages during an approximate inference update.",
        "Message passing becomes teachable when each update names the factor it reads, the "
        "belief it changes and the assumption it uses. Learners build trace tables that "
        "make local inference steps auditable.",
        ("vm_message_passing", "front_var_expectation_propagation"),
        _q(
            "A message trace should record the factor read, the belief changed and:",
            [
                "The assumption used by the update",
                "Only the final free-energy value",
                "Only the order the factors were created",
            ],
            0,
        ),
        _q(
            "Message trace reviews are mainly valuable because they make inference:",
            ["Auditable step by step", "Independent of the model", "A pure UI concern"],
            0,
        ),
        tags=("practice", "variational"),
    ),
]

_PRACTICE_FEP = [
    _s(
        "practice_fep_blanket_critique",
        "Markov Blanket Critique",
        _FEP,
        "Critique whether a proposed blanket actually separates internal and external states.",
        "Blanket language can become decorative if the conditional independencies are not "
        "specified. Learners practice naming sensory, active, internal and external states, "
        "then testing whether the claimed separation is defensible.",
        ("fep_markov_blanket", "front_fep_particular_blankets"),
        _q(
            "A Markov blanket critique should test whether the blanket:",
            [
                "Supports the claimed conditional separation",
                "Has the most appealing diagram",
                "Eliminates all external states",
            ],
            0,
        ),
        _q(
            "Which roles should be named in a concrete blanket proposal?",
            [
                "Sensory, active, internal and external states",
                "Only priors and rewards",
                "Only subjects and quizzes",
            ],
            0,
        ),
        tags=("practice", "fep"),
    ),
    _s(
        "practice_fep_timescale_map",
        "Timescale Maps for Self-Organisation",
        _FEP,
        "Map fast perception, slower action and slower parameter learning into separate timescales.",
        "Free-energy arguments often mix belief updates, action updates and learning updates. "
        "Learners construct timescale maps so claims about stability, adaptation and identity "
        "do not collapse into a single undifferentiated process.",
        ("fep_self_organisation", "front_fep_scale_separation"),
        _q(
            "A timescale map prevents learners from confusing:",
            [
                "Belief updates, action updates and learning updates",
                "Only assessment order and answer order",
                "Only variables and constants",
            ],
            0,
        ),
        _q(
            "Scale separation is useful because it clarifies:",
            [
                "Which process is changing at which rate",
                "Which topic tag is longest",
                "Which export file is newest",
            ],
            0,
        ),
        tags=("practice", "fep"),
    ),
    _s(
        "practice_fep_claim_boundary",
        "FEP Claim Boundary Setting",
        _FEP,
        "Separate formal FEP claims from metaphors, applications and speculative extrapolations.",
        "A careful learner can state what the formal framework licenses and what still "
        "requires empirical, modelling or implementation evidence. This skill trains "
        "claim boundaries so the FEP remains explanatory without becoming unfalsifiable.",
        ("fep_statement", "app_limitations", "front_fep_operational_autonomy"),
        _q(
            "Why set boundaries around an FEP claim?",
            [
                "To distinguish formal support from metaphor or extrapolation",
                "To make every application automatically correct",
                "To avoid specifying a generative model",
            ],
            0,
        ),
        _q(
            "A speculative application should be labelled as speculative until it has:",
            [
                "Model, empirical or implementation support",
                "A longer skill name",
                "A lower quiz point value",
            ],
            0,
        ),
        tags=("practice", "fep"),
    ),
]

_PRACTICE_ACTIVE_INFERENCE = [
    _s(
        "practice_ai_policy_space_design",
        "Policy Space Design",
        _AI,
        "Design a policy space that includes meaningful actions without hiding the hard choices.",
        "Expected free energy can only compare policies that the modeller has made available. "
        "Learners practice defining actions, horizons and constraints so a policy set is "
        "tractable without excluding the choices that matter.",
        ("ai_policy_selection", "ai_planning_horizon", "front_ai_multifactor_planning"),
        _q(
            "Why does policy-space design matter?",
            [
                "The agent can only evaluate policies included in the model",
                "It guarantees every policy has the same value",
                "It replaces the need for preferences",
            ],
            0,
        ),
        _q(
            "A badly designed policy space can hide:",
            [
                "The choices that determine behaviour",
                "Genuinely distinct courses of action",
                "Trade-offs between competing preferences",
            ],
            0,
        ),
        tags=("practice", "active-inference"),
    ),
    _s(
        "practice_ai_preference_elicitation",
        "Preference Elicitation and C-Matrix Audits",
        _AI,
        "Translate desired outcomes into preference distributions and audit their side effects.",
        "Preference vectors are normative inputs, not facts about the world. Learners "
        "practice eliciting them, checking for unintended incentives and distinguishing "
        "preferred outcomes from observed outcomes.",
        ("ai_matrix_C", "ai_pragmatic_value", "front_ai_meta_precision_learning"),
        _q(
            "Why audit a preference distribution?",
            [
                "It can encode unintended incentives or normative assumptions",
                "It always equals the posterior belief",
                "It is generated automatically by the likelihood",
            ],
            0,
        ),
        _q(
            "Preferred outcomes should be kept distinct from:",
            ["Observed outcomes", "Subject descriptions", "Import paths"],
            0,
        ),
        tags=("practice", "active-inference"),
    ),
    _s(
        "practice_ai_counterfactual_debugging",
        "Counterfactual Policy Debugging",
        _AI,
        "Debug policy choice by comparing what each candidate policy expects to observe.",
        "When an active-inference agent behaves oddly, the learner should inspect predicted "
        "observations, expected ambiguity, expected risk and epistemic value for rejected as "
        "well as selected policies. Counterfactual inspection turns policy choice into an "
        "auditable comparison.",
        ("front_ai_counterfactual_policies", "ai_risk_ambiguity", "ai_epistemic_value"),
        _q(
            "Counterfactual policy debugging compares:",
            [
                "Expected observations and values under candidate policies",
                "Only the policy names",
                "Only the final selected action",
            ],
            0,
        ),
        _q(
            "Rejected policies are useful to inspect because they reveal:",
            [
                "What the agent believed it was giving up",
                "Why prerequisites can be ignored",
                "Which subject should render first",
            ],
            0,
        ),
        tags=("practice", "active-inference"),
    ),
]

_PRACTICE_COMPUTATION = [
    _s(
        "practice_comp_invariant_tests",
        "Invariant Tests for Agent Implementations",
        _C,
        "Write implementation checks for normalisation, non-negativity and deterministic reproducibility.",
        "An active-inference implementation should fail loudly when beliefs stop summing to "
        "a valid distribution, probabilities go negative, or deterministic examples drift. "
        "Learners connect mathematical invariants to executable tests.",
        (
            "comp_normalize_softmax",
            "impl_reproducibility",
            "front_comp_schema_validation",
        ),
        _q(
            "Which invariant should a belief-state test usually enforce?",
            [
                "The belief remains a valid probability distribution",
                "The belief always equals its prior",
                "The belief collapses to a single point estimate",
            ],
            0,
        ),
        _q(
            "Executable invariants are valuable because they turn theory into:",
            [
                "Fail-closed implementation checks",
                "Unreviewed prose",
                "A deployment shortcut",
            ],
            0,
        ),
        tags=("practice", "computation"),
    ),
    _s(
        "practice_comp_trace_artifacts",
        "Trace Artifacts for Belief and Policy Updates",
        _C,
        "Record intermediate beliefs, free energies and policy scores for debugging and teaching.",
        "A single final action is rarely enough to debug an agent. Learners create trace "
        "artifacts that expose intermediate beliefs, prediction errors, policy scores and "
        "selected actions in a reproducible order.",
        ("comp_agent_loop", "comp_visualization", "front_comp_replay_harness"),
        _q(
            "Why store trace artifacts during a simulation?",
            [
                "They make intermediate inference and policy steps inspectable",
                "They replace all tests",
                "They hide numerical instability",
            ],
            0,
        ),
        _q(
            "A useful trace should include intermediate beliefs and:",
            [
                "Policy scores or selected actions",
                "Only the final converged belief",
                "Only the number of iterations run",
            ],
            0,
        ),
        tags=("practice", "computation"),
    ),
    _s(
        "practice_comp_export_contract_review",
        "SkillTree Export Contract Reviews",
        _C,
        "Review whether subjects, skills, quizzes and dependencies preserve the curriculum contract.",
        "Export is a semantic boundary: prerequisites become SkillTree dependencies, "
        "assessments become quizzes and descriptions become learner-facing content. "
        "Learners audit the export so platform mechanics do not distort the graph.",
        ("comp_skilltree_export", "comp_provenance_gate", "front_comp_batch_seed"),
        _q(
            "Why review the SkillTree export contract?",
            [
                "Platform objects must preserve the intended curriculum graph",
                "Exports should remove prerequisites",
                "Quizzes should be created after skills that depend on them",
            ],
            0,
        ),
        _q(
            "In this curriculum, prerequisites export as:",
            ["SkillTree dependencies", "Subject descriptions", "Dashboard filters"],
            0,
        ),
        tags=("practice", "computation"),
    ),
]

_PRACTICE_APPLICATIONS = [
    _s(
        "practice_app_domain_fit",
        "Domain Fit Reviews for Applications",
        _APP,
        "Assess whether an application domain genuinely fits an active-inference formulation.",
        "Not every adaptive system needs the full active-inference vocabulary. Learners "
        "review whether the domain has hidden states, observations, actions, preferences "
        "and uncertainty that justify the modelling overhead.",
        ("app_limitations", "front_app_institutional_design"),
        _q(
            "A domain fit review asks whether the setting has enough structure to justify:",
            [
                "An active-inference generative model",
                "A longer application title",
                "Ignoring uncertainty",
            ],
            0,
        ),
        _q(
            "Which ingredients usually support an active-inference formulation?",
            [
                "Hidden states, observations, actions, preferences and uncertainty",
                "Only a reward function and a policy table",
                "Only a collective metaphor",
            ],
            0,
        ),
        tags=("practice", "applications"),
    ),
    _s(
        "practice_app_ethics_and_misuse",
        "Ethics and Misuse Reviews",
        _APP,
        "Identify where active-inference systems can manipulate, overfit or misrepresent agency.",
        "Applications that infer preferences or shape information environments can create "
        "ethical risks. Learners review consent, transparency, manipulation, surveillance "
        "and misuse before treating a technical model as a deployable intervention.",
        (
            "cog_precision_attack",
            "cog_sensemaking",
            "practice_ai_preference_elicitation",
        ),
        _q(
            "Why include an ethics and misuse review?",
            [
                "Preference-shaping systems can create manipulation and surveillance risks",
                "Ethics makes model validation unnecessary",
                "Applications cannot fail once they use active inference",
            ],
            0,
        ),
        _q(
            "A deployment review should consider consent, transparency and:",
            ["Misuse risk", "Only file size", "Only quiz answer order"],
            0,
        ),
        tags=("practice", "applications"),
    ),
    _s(
        "practice_app_evaluation_design",
        "Evaluation Designs for Active-Inference Interventions",
        _APP,
        "Design evidence checks that distinguish useful intervention from attractive theory.",
        "Applied work needs outcomes, baselines, failure criteria and monitoring. Learners "
        "design evaluations that can show whether an active-inference intervention improves "
        "behaviour, learning, coordination or resilience in the domain it targets.",
        (
            "front_app_adaptive_tutoring",
            "front_app_human_robot_teaming",
            "practice_comp_trace_artifacts",
        ),
        _q(
            "An evaluation design should include outcomes, baselines and:",
            [
                "Failure criteria or monitoring",
                "Only a preferred diagram",
                "Only the final policy name",
            ],
            0,
        ),
        _q(
            "The purpose of evaluation is to distinguish useful intervention from:",
            [
                "Attractive but unsupported theory",
                "Effects explained by regression to the mean",
                "Improvements that fail to generalise",
            ],
            0,
        ),
        tags=("practice", "applications"),
    ),
]
