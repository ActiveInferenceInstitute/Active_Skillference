"""Next-hardening and scientific-supplement extension subjects."""

from __future__ import annotations

from .._ext_next_hardening import (
    _NEXT_APPLIED_EVAL_DOSSIERS,
    _NEXT_CONTINUOUS_DYNAMICS,
    _NEXT_CONTINUOUS_VARIATIONAL,
    _NEXT_HIERARCHICAL_ACTIVE_INFERENCE,
    _NEXT_PREDICTIVE_CODING_PROCESS,
    _NEXT_RATE_DISTORTION_INFO,
    _NEXT_REPRO_SIM_LABS,
    _NEXT_STATE_SPACE_PROBABILITY,
)
from .._ext_scientific_supplement import (
    _SCI_ACTIVE_INFERENCE,
    _SCI_APPLICATIONS,
    _SCI_COMPUTATION,
    _SCI_FEP,
    _SCI_INFORMATION,
    _SCI_MATH,
    _SCI_PROBABILITY,
    _SCI_VARIATIONAL,
)
from ..authoring import (
    _AI,
    _APP,
    _C,
    _FEP,
    _IT,
    _M,
    _P,
    _VM,
)
from ..model import Subject


def hardening_extension_subjects() -> list[Subject]:
    return [
        Subject(
            "sub_continuous_dynamics",
            "Continuous Dynamics & Stability",
            _M,
            "Continuous state variables, flow fields, stability checks and trajectory boundary cases for dynamic modelling.",
            tuple(_NEXT_CONTINUOUS_DYNAMICS),
        ),
        Subject(
            "sub_state_space_probability",
            "State-Space Probability Models",
            _P,
            "Hidden states, emissions, transitions, filtering and stress tests for temporal probabilistic examples.",
            tuple(_NEXT_STATE_SPACE_PROBABILITY),
        ),
        Subject(
            "sub_rate_distortion_information",
            "Rate-Distortion & Decision Information",
            _IT,
            "Compression, bottlenecks, channel limits and value-of-information triage for task-relevant evidence.",
            tuple(_NEXT_RATE_DISTORTION_INFO),
        ),
        Subject(
            "sub_continuous_variational",
            "Continuous Variational Inference",
            _VM,
            "Continuous recognition densities, functional objectives, pathwise gradients and approximation audits.",
            tuple(_NEXT_CONTINUOUS_VARIATIONAL),
        ),
        Subject(
            "sub_predictive_coding_process",
            "Predictive-Coding Process Theory",
            _FEP,
            "Prediction-error units, precision weighting and action-mediated error resolution for process-level FEP explanations.",
            tuple(_NEXT_PREDICTIVE_CODING_PROCESS),
        ),
        Subject(
            "sub_hierarchical_active_inference",
            "Hierarchical Active-Inference Design",
            _AI,
            "Nested policies, empirical-prior handoffs and multi-level epistemic action for hierarchical agents.",
            tuple(_NEXT_HIERARCHICAL_ACTIVE_INFERENCE),
        ),
        Subject(
            "sub_reproducible_simulation_labs",
            "Reproducible Simulation Labs",
            _C,
            "Seeded simulations, trace schemas, sweep diagnostics and artifact manifests for replayable learning.",
            tuple(_NEXT_REPRO_SIM_LABS),
        ),
        Subject(
            "sub_applied_evaluation_dossiers",
            "Applied Evaluation & Source Dossiers",
            _APP,
            "Source dossiers, claim-evidence tables, misuse reviews and capstone evidence audits for responsible application.",
            tuple(_NEXT_APPLIED_EVAL_DOSSIERS),
        ),
        Subject(
            "sub_scientific_supplement_math",
            "Scientific Supplement: Variational Mathematics",
            _M,
            "Inequality, convexity, gradient and stability checks that make VFE/EFE supplement derivations inspectable.",
            tuple(_SCI_MATH),
        ),
        Subject(
            "sub_scientific_supplement_probability",
            "Scientific Supplement: Probabilistic Evidence",
            _P,
            "Likelihood audits, evidence checks, calibration and posterior-predictive reviews for worked examples.",
            tuple(_SCI_PROBABILITY),
        ),
        Subject(
            "sub_scientific_supplement_information",
            "Scientific Supplement: Information Geometry",
            _IT,
            "KL geometry, entropy attribution, bound-gap interpretation and epistemic-value warnings for scientific reading.",
            tuple(_SCI_INFORMATION),
        ),
        Subject(
            "sub_scientific_supplement_variational",
            "Scientific Supplement: Variational Bounds",
            _VM,
            "ELBO/VFE identities, bound tightness, approximation-family declarations and convergence trace reviews.",
            tuple(_SCI_VARIATIONAL),
        ),
        Subject(
            "sub_scientific_supplement_fep",
            "Scientific Supplement: FEP Scope Tests",
            _FEP,
            "Surprise-bound scope, blanket boundaries, process-theory caveats and falsification notes for FEP exposition.",
            tuple(_SCI_FEP),
        ),
        Subject(
            "sub_scientific_supplement_active_inference",
            "Scientific Supplement: Active-Inference Terms",
            _AI,
            "EFE term separation, policy precision, regime switching and preference-design checks for action examples.",
            tuple(_SCI_ACTIVE_INFERENCE),
        ),
        Subject(
            "sub_scientific_supplement_computation",
            "Scientific Supplement: Computational Traceability",
            _C,
            "Kernel traces, plot provenance, numerical stability and manifest audits for reproducible supplement artifacts.",
            tuple(_SCI_COMPUTATION),
        ),
        Subject(
            "sub_scientific_supplement_applications",
            "Scientific Supplement: Applied Critique",
            _APP,
            "Evidence dossiers, source-to-claim tables, overclaim detection and capstone critique for applied explanations.",
            tuple(_SCI_APPLICATIONS),
        ),
    ]
