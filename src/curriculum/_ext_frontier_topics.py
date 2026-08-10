"""Frontier-topic curriculum expansion.

These skills extend the validated graph into advanced mathematical, probabilistic,
information-theoretic, variational, FEP, active-inference, implementation, and
application topics. They are intentionally authored as ordinary catalog data:
no computed claims, no hand-typed result decimals, and REST-safe identifiers.
"""

from __future__ import annotations

from src.curriculum._ext_helpers import _AI, _APP, _C, _FEP, _IT, _M, _P, _VM, _q, _s

_FRONTIER_MATH = [
    _s(
        "front_math_measure_spaces",
        "Measure Spaces for Generative Models",
        _M,
        "Define measurable spaces as the domain on which probability models live.",
        "A measure space separates the set of possible states from the sigma-algebra of "
        "events that can be assigned probability. This is the precise substrate for "
        "continuous generative models and prevents informal densities from being treated "
        "as if they were always ordinary functions.",
        ("m_sets", "p_axioms"),
        _q(
            "Why introduce a sigma-algebra in a probabilistic model?",
            [
                "To specify which events are measurable",
                "To enumerate every possible outcome of the model",
                "To replace every likelihood with a matrix",
            ],
            0,
        ),
        tags=("frontier", "math"),
    ),
    _s(
        "front_math_disintegration",
        "Disintegration and Conditional Kernels",
        _M,
        "Read conditional probability as a kernel between measurable spaces.",
        "Disintegration gives a rigorous version of conditioning in continuous spaces: "
        "a joint law can be decomposed into a marginal law and a conditional kernel. "
        "This is the measure-theoretic backbone of hierarchical generative models.",
        ("front_math_measure_spaces", "p_joint_marginal"),
        _q(
            "Disintegration decomposes a joint law into which objects?",
            [
                "A marginal law and a conditional kernel",
                "A Hessian and an eigenvector",
                "A policy prior and a reward scalar",
            ],
            0,
        ),
        tags=("frontier", "math"),
    ),
    _s(
        "front_math_optimal_transport",
        "Optimal Transport and Distribution Geometry",
        _M,
        "Use transport distances to compare distributions by moving probability mass.",
        "Optimal transport compares distributions through the cost of moving mass "
        "between them. It complements KL-based geometry by remaining meaningful when "
        "supports barely overlap, which is useful for studying belief dynamics and "
        "mode movement.",
        ("front_math_disintegration", "geo_statistical_manifold"),
        _q(
            "Optimal transport compares distributions by asking for the cost of:",
            [
                "Moving probability mass",
                "Increasing policy precision",
                "Renaming hidden states",
            ],
            0,
        ),
        tags=("frontier", "math"),
    ),
    _s(
        "front_math_observability_control",
        "Observability, Controllability and Identifiability",
        _M,
        "Separate what can be inferred, influenced, and uniquely identified.",
        "A model can only support action when hidden causes are observable enough to infer "
        "and controllable enough to influence. Identifiability asks whether distinct "
        "parameters imply distinguishable observation laws. These concepts expose when "
        "free-energy minimisation lacks the information needed to succeed.",
        ("front_math_optimal_transport", "dyn_state_space"),
        _q(
            "Identifiability asks whether distinct parameters imply:",
            [
                "Distinguishable observation laws",
                "The same preferred policy",
                "Identical prior distributions",
            ],
            0,
        ),
        tags=("frontier", "math"),
    ),
    _s(
        "front_math_categorical_composition",
        "Compositional Models and Category-Theoretic Glue",
        _M,
        "Describe how model components compose without losing their interfaces.",
        "Category-theoretic language treats models as objects with explicit interfaces "
        "and transformations as structure-preserving maps. Used carefully, it clarifies "
        "how blankets, policies and messages can be composed across scales without "
        "silently changing what each component means.",
        ("front_math_observability_control", "geo_natural_inference"),
        _q(
            "The practical value of compositional model language is that it preserves:",
            [
                "Interfaces between components",
                "Only scalar objectives",
                "Only the runtime execution order of operations",
            ],
            0,
        ),
        tags=("frontier", "math"),
    ),
]

_FRONTIER_PROBABILITY = [
    _s(
        "front_prob_exchangeability",
        "Exchangeability and De Finetti Structure",
        _P,
        "Distinguish independent samples from exchangeable observations.",
        "Exchangeability means the order of observations does not matter to their joint "
        "law. It is weaker than independence and supports latent-variable explanations "
        "where observations are conditionally independent given a hidden parameter.",
        ("p_independence", "p_dirichlet"),
        _q(
            "Exchangeability is weaker than which stronger assumption?",
            ["Independence", "Differentiability", "Convexity"],
            0,
        ),
        tags=("frontier", "probability"),
    ),
    _s(
        "front_prob_graphical_models",
        "Graphical Models beyond Chains",
        _P,
        "Use graph structure to encode conditional independence assumptions.",
        "Directed and undirected graphical models make independence assumptions visible. "
        "For active inference, this clarifies which hidden factors, outcomes and policies "
        "can be updated locally and which dependencies require coupled messages.",
        ("front_prob_exchangeability", "p_cond_independence"),
        _q(
            "A graphical model primarily makes which assumptions explicit?",
            [
                "Conditional independencies",
                "The exact marginal likelihood",
                "The choice of sampling algorithm",
            ],
            0,
        ),
        tags=("frontier", "probability"),
    ),
    _s(
        "front_prob_causal_graphs",
        "Causal Graphs and Interventions",
        _P,
        "Separate conditioning from intervention in generative models.",
        "Causal graphs distinguish seeing from doing. Conditioning updates beliefs after "
        "an observation; intervention changes the generative process itself. This matters "
        "for active inference because policies are interventions, not passive evidence.",
        ("front_prob_graphical_models", "ai_pomdp"),
        _q(
            "In a causal graph, an intervention differs from conditioning because it:",
            [
                "Changes the generative process",
                "Merely reweights existing observations",
                "Requires a Gaussian prior",
            ],
            0,
        ),
        tags=("frontier", "probability"),
    ),
    _s(
        "front_prob_filtering_smoothing",
        "Filtering, Smoothing and Prediction",
        _P,
        "Compare online filtering, retrospective smoothing, and forward prediction.",
        "Filtering estimates the current hidden state from past and present observations; "
        "smoothing revises past states using later observations; prediction projects "
        "future observations. Discrete active inference reuses all three operations inside "
        "policy evaluation.",
        ("front_prob_causal_graphs", "p_stochastic_process"),
        _q(
            "Smoothing differs from filtering because it uses:",
            [
                "Later observations to revise past states",
                "Only a prior",
                "Only preferences",
            ],
            0,
        ),
        tags=("frontier", "probability"),
    ),
    _s(
        "front_prob_nonparametric_models",
        "Nonparametric Priors and Growing State Spaces",
        _P,
        "Explain why some models let their effective complexity grow with data.",
        "Nonparametric Bayesian models place priors over flexible structures such as "
        "clusters, functions or state spaces. They are useful when the agent should be "
        "able to discover that its current catalogue of hidden causes is incomplete.",
        ("front_prob_filtering_smoothing", "learn_structure_learning"),
        _q(
            "A nonparametric prior is useful when the model must allow:",
            [
                "Complexity to grow with data",
                "Every policy to be deterministic",
                "No hidden states",
            ],
            0,
        ),
        tags=("frontier", "probability"),
    ),
]

_FRONTIER_INFORMATION = [
    _s(
        "front_info_mdl",
        "Minimum Description Length",
        _IT,
        "Connect model evidence with compression of data and model structure.",
        "Minimum description length treats learning as compression: a good model gives "
        "a short joint code for the model plus the data under that model. This reframes "
        "Occam factors in evidence and free energy as penalties for wasteful structure.",
        ("it_free_energy_link", "p_evidence"),
        _q(
            "Minimum description length evaluates a model by its ability to:",
            [
                "Compress model plus data",
                "Maximise the training-set likelihood alone",
                "Avoid all priors",
            ],
            0,
        ),
        tags=("frontier", "information"),
    ),
    _s(
        "front_info_predictive_efficiency",
        "Predictive Efficiency and Retained Information",
        _IT,
        "Measure how much past information is retained because it predicts the future.",
        "Predictive efficiency asks whether memory keeps information that helps predict "
        "future observations instead of merely memorising the past. It sharpens the "
        "distinction between epistemic value and indiscriminate data accumulation.",
        ("front_info_mdl", "im_predictive_information"),
        _q(
            "Predictive efficiency rewards memory that helps predict:",
            ["Future observations", "File names only", "Random labels"],
            0,
        ),
        tags=("frontier", "information"),
    ),
    _s(
        "front_info_partial_information",
        "Partial Information Decomposition",
        _IT,
        "Separate redundant, unique, and synergistic information in multiple sources.",
        "Partial information decomposition asks whether sources carry the same evidence, "
        "different evidence, or evidence that only appears when combined. It is a useful "
        "lens for multi-agent sensing, communication, and collective inference.",
        ("front_info_predictive_efficiency", "im_total_correlation"),
        _q(
            "Partial information decomposition separates information into redundant, unique, and:",
            ["Synergistic parts", "Executable bits", "Unobservable preferences"],
            0,
        ),
        tags=("frontier", "information"),
    ),
    _s(
        "front_info_active_sensing_channels",
        "Active Sensing as Channel Design",
        _IT,
        "Treat action as choosing the channel through which evidence will arrive.",
        "An active sensor does not merely receive a channel; it configures the channel by "
        "moving, probing or querying. Expected free energy can therefore be read as a "
        "criterion for selecting informative channels under preference constraints.",
        ("front_info_partial_information", "ai_epistemic_value"),
        _q(
            "In active sensing, action primarily changes:",
            [
                "The evidence channel",
                "The agent's fixed prior preferences",
                "The transition dynamics of the world",
            ],
            0,
        ),
        tags=("frontier", "information"),
    ),
    _s(
        "front_info_semantic_information",
        "Semantic Information and Action-Relevance",
        _IT,
        "Distinguish mere uncertainty reduction from information that matters for action.",
        "Semantic information is information that changes viable action, not just any "
        "posterior detail. In active inference this keeps epistemic value tied to the "
        "agent's generative model, preferences and policy repertoire.",
        ("front_info_active_sensing_channels", "ai_pragmatic_value"),
        _q(
            "Semantic information is information that changes:",
            ["Viable action", "Only text formatting", "Only the number of containers"],
            0,
        ),
        tags=("frontier", "information"),
    ),
]

_FRONTIER_VARIATIONAL = [
    _s(
        "front_var_black_box_vi",
        "Black-Box Variational Inference",
        _VM,
        "Use stochastic gradients when analytic updates are unavailable.",
        "Black-box variational inference estimates gradients of the variational objective "
        "without deriving bespoke coordinate updates. It expands active-inference-style "
        "modelling to generative models whose posteriors are too complex for closed-form "
        "message passing.",
        ("vm_amortised", "impl_vi_gradient"),
        _q(
            "Black-box variational inference is useful when analytic updates are:",
            ["Unavailable or impractical", "Always exact", "Unrelated to gradients"],
            0,
        ),
        tags=("frontier", "variational"),
    ),
    _s(
        "front_var_normalising_flows",
        "Normalising Flows as Recognition Densities",
        _VM,
        "Represent flexible posteriors through invertible transformations.",
        "A normalising flow transforms a simple base distribution into a flexible density "
        "while tracking the change in volume. As a recognition density, it can reduce "
        "the mismatch imposed by a rigid mean-field approximation.",
        ("front_var_black_box_vi", "vm_mean_field"),
        _q(
            "A normalising flow builds a flexible density using:",
            [
                "Invertible transformations",
                "Only a categorical table",
                "A fixed policy prior",
            ],
            0,
        ),
        tags=("frontier", "variational"),
    ),
    _s(
        "front_var_expectation_propagation",
        "Expectation Propagation and Local Projections",
        _VM,
        "Approximate each factor by projecting local beliefs back into a tractable family.",
        "Expectation propagation updates one factor at a time, then projects the result "
        "back into an approximating family. It highlights the design choice behind any "
        "message-passing scheme: what information is preserved when local beliefs are "
        "compressed.",
        ("front_var_normalising_flows", "vm_message_passing"),
        _q(
            "Expectation propagation repeatedly projects local beliefs back into:",
            [
                "A tractable approximating family",
                "The exact intractable posterior",
                "A single maximum-likelihood point estimate",
            ],
            0,
        ),
        tags=("frontier", "variational"),
    ),
    _s(
        "front_var_importance_weighted_bounds",
        "Importance-Weighted Bounds",
        _VM,
        "Tighten variational objectives by using multiple weighted samples.",
        "Importance-weighted bounds replace a single-sample estimate with a weighted set "
        "of samples. They can tighten the training objective, but they also expose the "
        "variance and degeneracy issues that appear when proposal and target diverge.",
        ("front_var_expectation_propagation", "impl_monte_carlo"),
        _q(
            "Importance-weighted bounds tighten an objective by using:",
            [
                "Multiple weighted samples",
                "Only deterministic actions",
                "No recognition density",
            ],
            0,
        ),
        tags=("frontier", "variational"),
    ),
    _s(
        "front_var_streaming_vi",
        "Streaming Variational Inference",
        _VM,
        "Update approximate posteriors online without revisiting all observations.",
        "Streaming variational inference maintains an approximate posterior as data arrive. "
        "It is the variational analogue of online perception and is essential when an "
        "agent must learn continually from a non-stationary stream.",
        ("front_var_importance_weighted_bounds", "learn_timescales"),
        _q(
            "Streaming variational inference is designed for data that arrive:",
            ["Online over time", "Only in a static PDF", "Without observations"],
            0,
        ),
        tags=("frontier", "variational"),
    ),
]

_FRONTIER_FEP = [
    _s(
        "front_fep_particular_blankets",
        "Particular Blankets and System Individuation",
        _FEP,
        "Use blankets to define which system is being modelled.",
        "A particular blanket is not just a boundary in space; it is a modelling claim "
        "about which internal, external, sensory and active states form a system. The "
        "same physical process can be individuated differently depending on the inferential "
        "question.",
        ("fep_markov_blanket", "dyn_ness"),
        _q(
            "A particular blanket primarily specifies:",
            [
                "The system being modelled",
                "Only the physical spatial boundary",
                "The total number of internal states",
            ],
            0,
        ),
        tags=("frontier", "fep"),
    ),
    _s(
        "front_fep_path_integrals",
        "Path Integrals and Trajectory Free Energy",
        _FEP,
        "Move from state-wise objectives to trajectory-wise objectives.",
        "Many organisms minimise surprise over trajectories, not isolated instants. A "
        "path-integral view treats histories as the objects of inference and makes the "
        "temporal structure of action, learning and self-maintenance explicit.",
        ("front_fep_particular_blankets", "dyn_gradient_flow"),
        _q(
            "A trajectory free-energy view treats the inferred object as:",
            [
                "A history or path",
                "Only a single scalar preference",
                "Only a single instantaneous state",
            ],
            0,
        ),
        tags=("frontier", "fep"),
    ),
    _s(
        "front_fep_generalised_synchrony",
        "Generalised Synchrony and Coupled Systems",
        _FEP,
        "Explain how coupled systems can synchronise without becoming identical.",
        "Generalised synchrony means one system's states become a lawful function of "
        "another's states. In FEP language, it clarifies how internal states can track "
        "external causes through a blanket while preserving their own dynamics.",
        ("front_fep_path_integrals", "col_generalised_synchrony"),
        _q(
            "Generalised synchrony allows coupled systems to track each other without:",
            ["Becoming identical", "Using observations", "Having internal dynamics"],
            0,
        ),
        tags=("frontier", "fep"),
    ),
    _s(
        "front_fep_operational_autonomy",
        "Operational Autonomy and Viability",
        _FEP,
        "Connect self-maintenance with the viable set of states an agent must preserve.",
        "Operational autonomy is the capacity of a system to keep itself within a viable "
        "set of states through action. The free-energy principle becomes concrete when "
        "viability constraints are stated as the outcomes the organism must keep sampling.",
        ("front_fep_generalised_synchrony", "fep_self_organisation"),
        _q(
            "Operational autonomy concerns keeping the system within:",
            [
                "A viable set of states",
                "A single fixed equilibrium point",
                "An ever-expanding state space",
            ],
            0,
        ),
        tags=("frontier", "fep"),
    ),
    _s(
        "front_fep_scale_separation",
        "Scale Separation across States, Parameters and Structure",
        _FEP,
        "Separate fast inference, slower learning, and slowest model revision.",
        "FEP models become clearer when fast hidden-state inference, slower parameter "
        "learning and slow structural revision are not conflated. Scale separation explains "
        "why perception, adaptation and development need different update rules.",
        ("front_fep_operational_autonomy", "learn_timescales"),
        _q(
            "Scale separation distinguishes fast state inference from slower:",
            [
                "Parameter and structure learning",
                "Per-step reward accumulation",
                "Immediate action selection",
            ],
            0,
        ),
        tags=("frontier", "fep"),
    ),
]

_FRONTIER_ACTIVE_INFERENCE = [
    _s(
        "front_ai_affordance_fields",
        "Affordance Fields",
        _AI,
        "Represent action opportunities as structured predictions over possible engagement.",
        "An affordance field maps situations to action possibilities. In active inference, "
        "affordances are not merely perceived objects; they are predictions about which "
        "policies can reduce expected free energy from the current state.",
        ("ai_policy_selection", "app_robotics"),
        _q(
            "An affordance field represents:",
            ["Action opportunities", "Only raw pixels", "Only static object labels"],
            0,
        ),
        tags=("frontier", "active-inference"),
    ),
    _s(
        "front_ai_counterfactual_policies",
        "Counterfactual Policy Evaluation",
        _AI,
        "Evaluate policies by simulating what would be observed if each were enacted.",
        "Policy selection depends on counterfactual futures: what observations, beliefs "
        "and outcomes would follow if a policy were chosen. This makes planning a disciplined "
        "form of imagination constrained by the generative model.",
        ("front_ai_affordance_fields", "ai_sophisticated"),
        _q(
            "Counterfactual policy evaluation asks what would happen if:",
            [
                "A policy were enacted",
                "All evidence were ignored",
                "A past trajectory were replayed unchanged",
            ],
            0,
        ),
        tags=("frontier", "active-inference"),
    ),
    _s(
        "front_ai_multifactor_planning",
        "Multifactor Planning under Factorised State Spaces",
        _AI,
        "Plan over separable hidden-state factors without losing cross-factor constraints.",
        "Factorised state spaces make planning tractable by decomposing hidden causes, but "
        "good policies still respect dependencies between factors. Multifactor planning "
        "tracks which parts of the policy tree can be evaluated independently.",
        ("front_ai_counterfactual_policies", "ai_state_factorisation"),
        _q(
            "Factorised planning is useful because it can reduce:",
            [
                "Combinatorial policy complexity",
                "All epistemic value",
                "The need for validation",
            ],
            0,
        ),
        tags=("frontier", "active-inference"),
    ),
    _s(
        "front_ai_meta_precision_learning",
        "Meta-Precision Learning",
        _AI,
        "Learn how strongly to weight different prediction-error channels.",
        "Agents can learn not only beliefs, but also the precision policies that determine "
        "which errors deserve attention. Meta-precision learning connects attention, "
        "confidence, habits and psychopathology in a single control problem.",
        ("front_ai_multifactor_planning", "hier_attention_precision"),
        _q(
            "Meta-precision learning adjusts how strongly the agent weights:",
            [
                "Prediction-error channels",
                "Only the prior over actions",
                "Only the reward magnitude",
            ],
            0,
        ),
        tags=("frontier", "active-inference"),
    ),
    _s(
        "front_ai_open_ended_exploration",
        "Open-Ended Exploration and Model Expansion",
        _AI,
        "Explain when exploration should expand the model rather than fill in old variables.",
        "Some uncertainty cannot be resolved inside the current state space. Open-ended "
        "exploration recognises when the agent should add hypotheses, factors or actions "
        "rather than merely estimate existing variables more precisely.",
        ("front_ai_meta_precision_learning", "front_prob_nonparametric_models"),
        _q(
            "Open-ended exploration is needed when uncertainty suggests:",
            [
                "The model itself may be incomplete",
                "No further learning is possible",
                "The export should be skipped",
            ],
            0,
        ),
        tags=("frontier", "active-inference"),
    ),
]

_FRONTIER_COMPUTATION = [
    _s(
        "front_comp_schema_validation",
        "Schema Validation for Learning Artifacts",
        _C,
        "Validate generated JSON before any downstream tool treats it as truth.",
        "A generated artifact should be treated as untrusted until it passes schema and "
        "semantic checks. For SkillTree exports this means validating required fields, "
        "identifier formats and dependency endpoints before the dashboard reports the data "
        "as available.",
        ("comp_skilltree_export_dep", "comp_provenance_gate"),
        _q(
            "Generated JSON should be treated as trusted only after:",
            [
                "Schema and semantic validation",
                "It parses as well-formed JSON without raising an error",
                "It was produced by our own export script",
            ],
            0,
        ),
        tags=("frontier", "computation"),
    ),
    _s(
        "front_comp_batch_seed",
        "Batch Seeding and Idempotent Repair",
        _C,
        "Seed large SkillTree graphs in dependency order while detecting silent shortfalls.",
        "A live seeder must be idempotent without becoming permissive. It should create "
        "subjects, skills, quizzes and dependencies in dependency-safe order, then query "
        "the server to verify that the live graph count equals the export.",
        ("front_comp_schema_validation", "comp_skilltree_export"),
        _q(
            "An idempotent seeder still has to detect:",
            [
                "Silent live shortfalls",
                "Partial writes from an interrupted run",
                "Duplicate skill display names",
            ],
            0,
        ),
        tags=("frontier", "computation"),
    ),
    _s(
        "front_comp_replay_harness",
        "Replay Harnesses for Agent Simulations",
        _C,
        "Make simulation traces deterministic enough to debug and compare.",
        "A replay harness records seeds, inputs, policies and observations so an agent "
        "trajectory can be rerun. This makes stochastic active-inference simulations "
        "auditable rather than anecdotal.",
        ("front_comp_batch_seed", "impl_reproducibility"),
        _q(
            "A replay harness records enough information to:",
            ["Rerun a trajectory", "Bypass provenance checks", "Invent missing claims"],
            0,
        ),
        tags=("frontier", "computation"),
    ),
    _s(
        "front_comp_dashboard_observability",
        "Dashboard Observability without Reimplementing SkillTree",
        _C,
        "Expose artifact and runtime health while leaving learner state to SkillTree.",
        "The local dashboard should report whether artifacts are current, whether SkillTree "
        "is reachable, and whether local token exchange is ready. It must not become a "
        "second learning-state authority.",
        ("front_comp_replay_harness", "comp_skilltree_export_dep"),
        _q(
            "The local dashboard must leave learner state owned by:",
            ["SkillTree", "A generated markdown table", "A figure registry"],
            0,
        ),
        tags=("frontier", "computation"),
    ),
    _s(
        "front_comp_runtime_secret_hygiene",
        "Runtime Secret Hygiene for Local Tooling",
        _C,
        "Keep trusted-client secrets server-side and fail closed on unsafe hosts.",
        "Local helper servers can improve ergonomics, but secret-bearing token exchange "
        "must remain server-side and loopback-only. Serving a trusted-client bridge on a "
        "non-loopback host turns a development convenience into an authentication risk.",
        ("front_comp_dashboard_observability", "front_ai_open_ended_exploration"),
        _q(
            "A local trusted-client bridge should fail closed when served on:",
            [
                "A non-loopback host",
                "A short-lived local port",
                "A privileged port below 1024",
            ],
            0,
        ),
        tags=("frontier", "computation"),
    ),
]

_FRONTIER_APPLICATIONS = [
    _s(
        "front_app_digital_mental_health",
        "Digital Mental Health and Precision Support",
        _APP,
        "Frame adaptive interventions as precision-sensitive active-inference loops.",
        "Digital mental health systems can be evaluated as loops that sense context, infer "
        "latent need, choose interventions and update support policies. The hard part is "
        "calibrating precision and safety constraints, not merely increasing engagement.",
        ("app_computational_psychiatry", "front_ai_meta_precision_learning"),
        _q(
            "For digital mental health, increasing engagement is insufficient without calibrated:",
            [
                "Precision and safety constraints",
                "Calibrated estimates of clinical risk",
                "Limits on intervention intensity",
            ],
            0,
        ),
        tags=("frontier", "applications"),
    ),
    _s(
        "front_app_adaptive_tutoring",
        "Adaptive Tutoring as Active Inference",
        _APP,
        "Model teaching as selecting observations that improve a learner's hidden state.",
        "An adaptive tutor maintains beliefs about the learner's misconceptions and chooses "
        "questions, explanations and practice that are both epistemic for the tutor and "
        "useful for the learner.",
        ("front_app_digital_mental_health", "front_info_active_sensing_channels"),
        _q(
            "An adaptive tutor chooses activities partly to infer:",
            [
                "The learner's hidden misconceptions",
                "The learner's current uncertainty",
                "Only a fixed score",
            ],
            0,
        ),
        tags=("frontier", "applications"),
    ),
    _s(
        "front_app_human_robot_teaming",
        "Human-Robot Teaming and Shared Belief",
        _APP,
        "Coordinate agents by aligning beliefs, affordances and policy expectations.",
        "Human-robot teams require more than individual control. Each partner must infer "
        "what the other believes, can do and intends to do, then choose policies that keep "
        "the shared task legible and safe.",
        ("front_app_adaptive_tutoring", "app_robotics"),
        _q(
            "Human-robot teaming requires agents to infer each other's beliefs and:",
            ["Policy expectations", "Raw motor torques", "Fixed scripted routines"],
            0,
        ),
        tags=("frontier", "applications"),
    ),
    _s(
        "front_app_urban_sensing",
        "Urban Sensing and Collective Prediction",
        _APP,
        "Apply active sensing ideas to cities, infrastructure and public signals.",
        "An urban sensing system decides which signals to sample, where to place attention "
        "and how to aggregate local observations into a city-scale posterior. This is an "
        "active-inference problem whenever sensing choices change future uncertainty.",
        ("front_app_human_robot_teaming", "cog_sensemaking"),
        _q(
            "Urban sensing becomes active inference when sensing choices affect:",
            [
                "Future uncertainty",
                "Only the immediate measurement cost",
                "Only the sensor's power draw",
            ],
            0,
        ),
        tags=("frontier", "applications"),
    ),
    _s(
        "front_app_institutional_design",
        "Institutional Design as Epistemic Infrastructure",
        _APP,
        "Treat institutions as structures that shape collective inference and action.",
        "Institutions allocate attention, define trusted evidence channels and constrain "
        "policy repertoires. Designing them as epistemic infrastructure connects cognitive "
        "security, collective active inference and practical governance.",
        ("front_app_urban_sensing", "cog_commons"),
        _q(
            "Institutions shape collective inference by allocating attention and defining:",
            [
                "Trusted evidence channels",
                "Only image dimensions",
                "Only local file modes",
            ],
            0,
        ),
        tags=("frontier", "applications"),
    ),
]
