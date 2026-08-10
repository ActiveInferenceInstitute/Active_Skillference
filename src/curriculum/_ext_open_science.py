"""Open-science and reproducible-learning curriculum expansion.

The skills in this module connect the mathematical curriculum to the public
education ecosystem around Active Inference. They are still prerequisite nodes,
not citations: scholarship support remains in ``references.bib`` and the source
matrix.
"""

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


_SECONDARY_ANCHORS = {
    "math": "practice_math_dimension_check",
    "probability": "practice_prob_prior_predictive_check",
    "information": "practice_info_information_budget",
    "variational": "practice_var_elbo_failure_modes",
    "fep": "practice_fep_claim_boundary",
    "active_inference": "practice_ai_counterfactual_debugging",
    "computation": "front_comp_schema_validation",
    "applications": "practice_app_evaluation_design",
}


def _open_skill(
    *,
    prefix: str,
    index: int,
    name: str,
    stratum: Stratum,
    objective: str,
    focus: str,
    anchor: str,
    related: tuple[str, ...] = (),
) -> Skill:
    skill_id = f"os_{prefix}_{index:02d}"
    prior = f"os_{prefix}_{index - 1:02d}" if index > 1 else ""
    description = (
        f"{focus} The learner treats open educational material as a modelled object: "
        "its assumptions, examples, prerequisites, and failure modes must be explicit "
        "enough that another learner or maintainer can reproduce the intended path."
    )
    return _s(
        skill_id,
        name,
        stratum,
        objective,
        description,
        _dedupe(
            (anchor, prior, _SECONDARY_ANCHORS.get(prefix, "") if index == 8 else "")
        ),
        _q(
            f"What is the main learner-facing product of {name}?",
            [
                (
                    f"A reusable, auditable learning move that {name} makes reproducible "
                    "for the next learner who follows the path"
                ),
                (
                    f"A decorative label that lets {name} skip stating the prerequisites "
                    "it actually depends on"
                ),
                (
                    f"A claim from {name} that no verifier is ever expected to inspect "
                    "or reproduce"
                ),
            ],
            0,
        ),
        _q(
            f"Which review question best stress-tests {name}?",
            [
                (
                    f"Can another learner trace the prerequisites of {name} and reproduce "
                    "its worked example unaided?"
                ),
                (
                    f"Can {name} be advertised as covered without showing any supporting "
                    "evidence to the learner?"
                ),
                (
                    f"Can the quiz for {name} pass while quietly avoiding every concrete "
                    "misconception?"
                ),
            ],
            0,
        ),
        tags=("open-science", "education", prefix),
        related=related,
    )


def _make(
    prefix: str,
    stratum: Stratum,
    anchor: str,
    rows: tuple[tuple[str, str, str, tuple[str, ...]], ...],
) -> list[Skill]:
    return [
        _open_skill(
            prefix=prefix,
            index=index,
            name=name,
            stratum=stratum,
            objective=objective,
            focus=focus,
            anchor=anchor,
            related=related,
        )
        for index, (name, objective, focus, related) in enumerate(rows, start=1)
    ]


_OPEN_MATH = _make(
    "math",
    _M,
    "m_sets",
    (
        (
            "Notation Contracts for Shared Courses",
            "Specify symbols so course modules can reuse them consistently.",
            "Open curricula fail when the same symbol silently changes type across lessons.",
            ("front_math_categorical_composition",),
        ),
        (
            "Dimensional Rubrics for Worked Examples",
            "Write shape checks as grading criteria for mathematical examples.",
            "A public worked example should expose domain, codomain, and dimension assumptions before any result is trusted.",
            ("practice_math_dimension_check",),
        ),
        (
            "Assumption Ledgers for Derivations",
            "Track smoothness, convexity, and normalization assumptions in lesson material.",
            "Reusable derivations need an assumption ledger that travels with the exercise.",
            ("practice_math_assumption_checklist",),
        ),
        (
            "Visual Proof Sketches",
            "Translate algebraic steps into diagrams without replacing the proof.",
            "Diagrams help learners orient, but they must preserve the mathematical dependency they illustrate.",
            ("m_matrix",),
        ),
        (
            "Parameter Naming Hygiene",
            "Separate constants, estimates, latent states, and observations in shared notation.",
            "Educational repositories need naming discipline so examples compose across files and cohorts.",
            ("m_vectors",),
        ),
        (
            "Edge-Case Example Selection",
            "Choose boundary cases that reveal where a mathematical claim stops applying.",
            "A good public example includes a normal case and a boundary case that prevents overgeneralisation.",
            ("practice_math_sensitivity_probe",),
        ),
        (
            "Reusable Exercise Templates",
            "Design exercise templates that preserve formal roles while changing surface story.",
            "Template reuse is safe only when the mathematical role of each slot is stable.",
            ("m_functions_real",),
        ),
        (
            "Mathematical Review Checklists",
            "Review open learning material for type, assumption, and dependency completeness.",
            "A checklist turns mathematical quality into something another maintainer can verify.",
            ("m_chain_rule",),
        ),
    ),
)

_OPEN_PROBABILITY = _make(
    "probability",
    _P,
    "p_bayes_theorem",
    (
        (
            "Generative Story Templates",
            "Turn public examples into explicit variables and factorisations.",
            "Shared examples become teachable when the generative story names variables before computing beliefs.",
            ("practice_prob_story_to_factorisation",),
        ),
        (
            "Prior Elicitation Exercises",
            "Teach learners to state priors as commitments rather than defaults.",
            "Open courseware should make prior assumptions visible enough to debate and revise.",
            ("p_dirichlet",),
        ),
        (
            "Observation Quality Notes",
            "Document missingness, censoring, and noise in educational examples.",
            "Learners need to know whether an observation was absent, hidden, or noisy before updating beliefs.",
            ("practice_prob_missing_data",),
        ),
        (
            "Calibration Mini-Labs",
            "Use small repeated predictions to connect probability to calibration.",
            "Calibration labs make probability operational instead of only symbolic.",
            ("p_expectation",),
        ),
        (
            "Prior Predictive Rehearsal",
            "Simulate before conditioning to catch implausible public examples.",
            "A prior predictive rehearsal protects shared lessons from examples that only work after the answer is known.",
            ("practice_prob_prior_predictive_check",),
        ),
        (
            "Bayesian Misconception Catalogues",
            "Collect common Bayesian reasoning errors as reusable quiz distractors.",
            "Open education improves when distractors are mapped to real learner misconceptions.",
            ("p_cond_independence",),
        ),
        (
            "Uncertainty Communication",
            "Explain posterior uncertainty without collapsing it into a single score.",
            "Shared materials should preserve uncertainty rather than hiding it behind a point estimate.",
            ("p_evidence",),
        ),
        (
            "Probability Audit Trails",
            "Record each modelling judgement that changes a probability calculation.",
            "An audit trail lets another learner reconstruct why the posterior changed.",
            ("p_joint_marginal",),
        ),
    ),
)

_OPEN_INFORMATION = _make(
    "information",
    _IT,
    "it_entropy",
    (
        (
            "Information-Gain Lesson Goals",
            "Connect each lesson to the uncertainty it should reduce.",
            "A learning objective can be read as an information-gain target for the learner.",
            ("practice_info_information_budget",),
        ),
        (
            "Surprise Versus Error Notes",
            "Distinguish rare expected events from model defects in examples.",
            "Public explanations should not treat every surprising event as evidence of a broken model.",
            ("practice_info_surprise_decomposition",),
        ),
        (
            "Channel Diagrams for Tutorials",
            "Draw observation channels so learners see where evidence enters.",
            "A tutorial benefits when signals, noise, and hidden states are separated visually.",
            ("practice_info_channel_audit",),
        ),
        (
            "Compression-Oriented Summaries",
            "Use short summaries that preserve the relevant dependency structure.",
            "Good summaries reduce length without erasing prerequisite relations.",
            ("front_info_mdl",),
        ),
        (
            "Semantic Information Checks",
            "Ask whether information is useful for the learner's task, not just large.",
            "A high-information exercise can still be irrelevant if it reduces the wrong uncertainty.",
            ("front_info_semantic_information",),
        ),
        (
            "Epistemic-Value Examples",
            "Show how information value changes policy evaluation.",
            "Learners should see information gain as a policy term, not an isolated formula.",
            ("it_info_gain",),
        ),
        (
            "Misleading Signal Cases",
            "Teach when a channel appears informative but changes the wrong belief.",
            "Open examples should include failure cases where evidence is precise but misdirected.",
            ("it_data_processing",),
        ),
        (
            "Information-Literacy Rubrics",
            "Score explanations by what uncertainty they reduce and what they leave open.",
            "Rubrics make information-theoretic teaching quality inspectable.",
            ("im_information_bottleneck",),
        ),
    ),
)

_OPEN_VARIATIONAL = _make(
    "variational",
    _VM,
    "vm_elbo",
    (
        (
            "Approximation Choice Records",
            "Document why a lesson uses a particular variational approximation.",
            "Approximation choices should be part of the teaching artifact, not hidden implementation detail.",
            ("practice_var_approximation_choice",),
        ),
        (
            "ELBO Failure Walkthroughs",
            "Teach learners to diagnose loose bounds and bad optima.",
            "A public lesson should show how an approximation can fail, not only when it succeeds.",
            ("practice_var_elbo_failure_modes",),
        ),
        (
            "Message-Passing Trace Reviews",
            "Represent updates as inspectable traces across factors.",
            "Trace views help learners connect local messages to global inference.",
            ("practice_var_message_trace",),
        ),
        (
            "Gradient Estimator Warnings",
            "Explain estimator variance and bias in advanced examples.",
            "Open code examples should expose why an estimator is chosen and what risk it carries.",
            ("front_var_black_box_vi",),
        ),
        (
            "Bound-Tightness Exercises",
            "Ask learners to compare an exact quantity with its variational bound.",
            "Bound comparisons prevent learners from treating the approximation as the target.",
            ("vm_free_energy_tight",),
        ),
        (
            "Reusable Variational Notebooks",
            "Structure notebooks so each inference step can be rerun independently.",
            "Notebook lessons are more reusable when cells mirror the mathematical dependency order.",
            ("vm_message_passing",),
        ),
        (
            "Amortisation Caveat Cards",
            "State what is gained and lost when inference is amortised.",
            "Learners need a compact way to remember that speed can trade off with local fit.",
            ("vm_amortised",),
        ),
        (
            "Variational Peer Review",
            "Review public examples for objective, family, optimizer, and diagnostic completeness.",
            "A peer review checklist closes the gap between running code and teaching inference.",
            ("vm_mean_field",),
        ),
    ),
)

_OPEN_FEP = _make(
    "fep",
    _FEP,
    "fep_statement",
    (
        (
            "FEP Claim Boundary Cards",
            "State what a Free Energy Principle claim does and does not assert.",
            "Open education needs explicit boundaries so broad principles do not become unfalsifiable slogans.",
            ("practice_fep_claim_boundary",),
        ),
        (
            "Blanket Diagram Critiques",
            "Review Markov blanket diagrams for hidden variables and edge meaning.",
            "A blanket diagram is useful only if learners can recover the implied independencies.",
            ("practice_fep_blanket_critique",),
        ),
        (
            "Timescale Separation Notes",
            "Teach which processes are being modelled at each timescale.",
            "FEP explanations often fail when biological, behavioural, and learning timescales are collapsed.",
            ("practice_fep_timescale_map",),
        ),
        (
            "Particular-Systems Examples",
            "Connect abstract FEP language to bounded systems with measurable states.",
            "A public example should name the system whose persistence is being explained.",
            ("front_fep_particular_blankets",),
        ),
        (
            "Precision-Framing Exercises",
            "Show how precision changes interpretation without becoming mere confidence.",
            "Learners need examples where precision controls influence rather than just certainty.",
            ("fep_precision",),
        ),
        (
            "Self-Organisation Caveats",
            "Teach when self-organisation language adds structure and when it obscures.",
            "Open materials should separate mechanistic explanation from broad metaphor.",
            ("fep_self_organisation",),
        ),
        (
            "Predictive-Processing Bridges",
            "Map predictive-processing examples into FEP terminology carefully.",
            "Bridge lessons should preserve what changes when moving from prediction error to free-energy language.",
            ("fep_predictive_processing",),
        ),
        (
            "FEP Review Rubrics",
            "Evaluate public FEP explanations for scope, variables, boundary, and evidence.",
            "Rubrics protect learners from overgeneral claims while preserving conceptual ambition.",
            ("front_fep_operational_autonomy",),
        ),
    ),
)

_OPEN_ACTIVE_INFERENCE = _make(
    "active_inference",
    _AI,
    "ai_expected_free_energy",
    (
        (
            "Policy-Space Learning Paths",
            "Teach how candidate policies are enumerated and constrained.",
            "Open lessons should show the policy set before comparing expected free energy.",
            ("practice_ai_policy_space_design",),
        ),
        (
            "Preference-Elicitation Labs",
            "Turn learner goals into explicit preference distributions.",
            "Preference design is teachable when learners can inspect what each preference encodes.",
            ("practice_ai_preference_elicitation",),
        ),
        (
            "Epistemic Action Walkthroughs",
            "Show when information-seeking is selected and when it is not.",
            "A public curriculum should include regime changes, not only a single exploratory success case.",
            ("ai_epistemic_value",),
        ),
        (
            "Counterfactual Debugging Exercises",
            "Ask what would change if a policy, prior, or likelihood changed.",
            "Counterfactual questions train learners to debug models rather than memorize outcomes.",
            ("practice_ai_counterfactual_debugging",),
        ),
        (
            "Habit Versus Planning Cases",
            "Separate habitual policy priors from active planning objectives.",
            "Learners need cases where habits help and cases where they block useful exploration.",
            ("ai_habits",),
        ),
        (
            "Hierarchical Course Maps",
            "Use nested policies to organize beginner, intermediate, and advanced paths.",
            "Open curricula can mirror hierarchical active inference when paths are explicit.",
            ("ai_hierarchical",),
        ),
        (
            "Open-Ended Exploration Prompts",
            "Design prompts that make model uncertainty visible and revisable.",
            "Exploration prompts should reveal which uncertainty the learner or agent is reducing.",
            ("front_ai_open_ended_exploration",),
        ),
        (
            "Active-Inference Studio Critiques",
            "Review applied examples for states, observations, actions, preferences, and policies.",
            "A studio critique makes each modelling commitment inspectable before application.",
            ("ai_pomdp",),
        ),
    ),
)

_OPEN_COMPUTATION = _make(
    "computation",
    _C,
    "comp_provenance_gate",
    (
        (
            "Executable Course Notebooks",
            "Structure notebooks so claims, figures, and quizzes can be regenerated.",
            "Reproducible education requires the path from code to learner-facing claim to be runnable.",
            ("impl_reproducibility",),
        ),
        (
            "Schema-Checked Skill Exports",
            "Validate learning objects before seeding a runtime.",
            "Schema checks prevent a course from looking polished while exporting malformed skills.",
            ("front_comp_schema_validation",),
        ),
        (
            "Traceable Quiz Builds",
            "Connect each quiz item to its source skill and misconception target.",
            "Quiz generation should be inspectable because quizzes gate completion.",
            ("comp_skilltree_export",),
        ),
        (
            "Dashboard Artifact Contracts",
            "Expose generated artifacts without duplicating learner-state ownership.",
            "A dashboard can improve inspection while leaving progress and ranking to SkillTree.",
            ("front_comp_dashboard_observability",),
        ),
        (
            "Batch Seed Rehearsals",
            "Seed local runtimes in dependency-safe order before claiming deployment readiness.",
            "Rehearsal seeding catches order and authentication defects earlier than manual clicking.",
            ("front_comp_batch_seed",),
        ),
        (
            "Replayable Validation Runs",
            "Record command sequences that rebuild claims, figures, exports, and manuscript outputs.",
            "Replay turns package quality into evidence rather than memory.",
            ("front_comp_replay_harness",),
        ),
        (
            "Secret-Hygiene Teaching Examples",
            "Teach local auth without leaking credentials into generated artifacts.",
            "Educational tooling still needs boundaries around trusted-client state and tokens.",
            ("front_comp_runtime_secret_hygiene",),
        ),
        (
            "Visualization QA Scripts",
            "Check that charts are nonblank, labelled, and consistent with their data.",
            "A visualization is an artifact with its own verifier, not decoration.",
            ("comp_visualization",),
        ),
    ),
)

_OPEN_APPLICATIONS = _make(
    "applications",
    _APP,
    "practice_app_domain_fit",
    (
        (
            "Open-Science Course Ecosystem",
            "Situate Active Skillference among public Active Inference education efforts.",
            "Learners benefit when this curriculum points to neighboring open resources and explains its distinct role.",
            ("front_app_adaptive_tutoring",),
        ),
        (
            "Community Review Loops",
            "Design feedback paths for learners, maintainers, and domain reviewers.",
            "Open education improves when review is a repeatable loop rather than a one-time release.",
            ("cog_epistemic_communities",),
        ),
        (
            "Responsible Application Boundaries",
            "State when a learning exercise is not operational advice.",
            "Application lessons should separate conceptual practice from clinical, legal, or organizational deployment.",
            ("practice_app_ethics_and_misuse",),
        ),
        (
            "Evaluation Design Templates",
            "Define what evidence would show an applied learning path worked.",
            "A public course needs evaluation criteria beyond completion counts.",
            ("practice_app_evaluation_design",),
        ),
        (
            "Institutional Learning Maps",
            "Map concepts to roles, incentives, and shared generative models in institutions.",
            "Institutional examples help learners see active inference beyond individual agents.",
            ("front_app_institutional_design",),
        ),
        (
            "Cognitive Security Studios",
            "Teach information-ecosystem examples with misuse and resilience checks.",
            "Applied cognition examples need adversarial review because precision and trust can be attacked.",
            ("cog_adversarial_inference",),
        ),
        (
            "Adaptive Tutoring Comparisons",
            "Compare static course paths with tailored learning paths.",
            "Public educational efforts can complement each other when their adaptation assumptions are explicit.",
            ("front_app_adaptive_tutoring",),
        ),
        (
            "Capstone Source Dossiers",
            "Require capstones to cite sources, variables, claims, and validation commands.",
            "A capstone should demonstrate both conceptual modelling and reproducible evidence handling.",
            ("app_curriculum_capstone",),
        ),
    ),
)
