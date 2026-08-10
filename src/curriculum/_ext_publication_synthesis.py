"""Publication-synthesis and reader-handoff curriculum expansion."""

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


def _publication_skill(
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
    skill_id = f"pub_{prefix}_{index:02d}"
    prior = f"pub_{prefix}_{index - 1:02d}" if index > 1 else ""
    description = (
        f"{focus} Learners connect a technical idea to a publication surface: "
        "cover image, abstract, figure caption, dashboard panel, or review packet. "
        "The emphasis is on preserving prerequisite meaning while making the "
        "artifact legible to readers who inspect claims through generated evidence."
    )
    return _s(
        skill_id,
        name,
        stratum,
        objective,
        description,
        _dedupe((anchor, prior)),
        _q(
            f"What makes {name} a valid publication-synthesis skill?",
            [
                "It preserves the technical claim, names the evidence surface, and states the reader-facing boundary.",
                "It turns the concept into a decorative summary without prerequisites.",
                "It hides unresolved assumptions so the artifact reads more smoothly.",
            ],
            0,
        ),
        tags=("publication-synthesis", "reader-handoff", prefix),
        related=related,
    )


def _make(
    prefix: str,
    stratum: Stratum,
    anchor: str,
    rows: tuple[tuple[str, str, str, tuple[str, ...]], ...],
) -> list[Skill]:
    return [
        _publication_skill(
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


_PUB_MATH = _make(
    "math",
    _M,
    "viz_math_01",
    (
        (
            "Publication Scale Checks",
            "Align visual scale, units and axes with the mathematical claim a reader must verify.",
            "A cover or figure can only summarize a mathematical object when its scale choices remain auditable.",
            ("m_functions_real", "viz_math_02"),
        ),
        (
            "Graph Layout Contracts",
            "Choose graph layouts that preserve dependency direction and level structure.",
            "Graph layouts become publication claims when placement implies ordering, grouping or bottleneck importance.",
            ("viz_math_02",),
        ),
        (
            "Notation Consistency Passes",
            "Check that symbols in the cover, captions and manuscript prose refer to the same objects.",
            "Notation mismatches break reader trust because visual shorthand no longer maps to the derivation.",
            ("sci_math_04",),
        ),
        (
            "Quantitative Density Triage",
            "Decide which counts belong on a public surface and which belong in the audit artifact.",
            "Dense quantitative summaries need a policy for including live counts without overwhelming the first reading path.",
            ("viz_math_04",),
        ),
    ),
)


_PUB_PROBABILITY = _make(
    "probability",
    _P,
    "viz_probability_01",
    (
        (
            "Calibration Summary Writing",
            "Write reader-facing summaries that distinguish calibrated probability from confident prose.",
            "Calibration language keeps probability claims tied to observed frequencies or validation checks.",
            ("p_bayes_theorem",),
        ),
        (
            "Uncertainty Wording Boundaries",
            "Phrase uncertainty without implying unsupported posterior precision.",
            "Publication prose should state what the interval or posterior conditions on and what remains outside scope.",
            ("viz_probability_04",),
        ),
        (
            "Posterior-Predictive Storyboards",
            "Turn posterior-predictive checks into a concise evidence story for readers.",
            "A storyboard shows what the model would generate and where those generated cases would be challenged.",
            ("viz_probability_03",),
        ),
        (
            "Risk Label Calibration",
            "Attach risk labels to probabilistic summaries without changing the underlying probability claim.",
            "Risk labels help readers triage artifacts while preserving the distinction between likelihood and value judgment.",
            ("practice_prob_prior_predictive_check",),
        ),
    ),
)


_PUB_INFORMATION = _make(
    "information",
    _IT,
    "viz_information_01",
    (
        (
            "Curriculum Map Compression",
            "Compress a large prerequisite graph into a publication-scale map without losing its learning contract.",
            "Information-theoretic compression is useful only when the discarded detail is named and recoverable elsewhere.",
            ("it_entropy",),
        ),
        (
            "Pathway Entropy Summaries",
            "Use entropy language to describe branching learning paths without implying learner cognition was measured.",
            "Pathway summaries can describe artifact structure while avoiding unsupported psychological claims.",
            ("it_joint_entropy",),
        ),
        (
            "Information Bottleneck Framing",
            "Frame cover and dashboard summaries as bottlenecks between full graph evidence and reader attention.",
            "A bottleneck framing helps decide which variables should survive into a first-page synthesis.",
            ("next_rate_distortion_info_04",),
        ),
        (
            "Rate-Distortion Reading Tradeoffs",
            "Explain how concise visuals trade fidelity for accessibility in a reproducible manuscript.",
            "Rate-distortion language clarifies why a simplified artifact is useful and where readers should inspect detail.",
            ("next_rate_distortion_info_01",),
        ),
    ),
)


_PUB_VARIATIONAL = _make(
    "variational",
    _VM,
    "viz_variational_01",
    (
        (
            "Bound Narrative Editing",
            "Edit VFE and ELBO explanations so bound, evidence and approximation gap remain separate.",
            "A bound narrative should help readers see what is optimized and what is merely bounded.",
            ("vm_free_energy",),
        ),
        (
            "Optimization Trace Narratives",
            "Translate optimization traces into publication prose without overclaiming convergence.",
            "Trace narratives distinguish numerical descent from posterior adequacy or scientific truth.",
            ("viz_variational_02",),
        ),
        (
            "Approximation Caveat Placement",
            "Place approximation-family caveats where readers encounter the relevant visual claim.",
            "Caveats protect the manuscript from implying that a tractable family equals the true posterior.",
            ("sci_variational_03",),
        ),
        (
            "Diagnostic Panel Sequencing",
            "Sequence diagnostic panels so assumptions, objective values and interpretation boundaries are inspectable.",
            "Panel order controls whether readers audit the method or merely consume the final curve.",
            ("viz_variational_04",),
        ),
    ),
)


_PUB_FEP = _make(
    "fep",
    _FEP,
    "viz_fep_01",
    (
        (
            "Blanket Boundary Captions",
            "Write captions that identify the Markov blanket partition and its conditional-independence claim.",
            "Blanket diagrams are publication claims, not ornaments, and need a stated partition.",
            ("fep_markov_blanket",),
        ),
        (
            "Publication Timescale Separation Notes",
            "Add timescale notes that separate inference, learning and evolutionary framing.",
            "Timescale notes prevent broad FEP exposition from collapsing distinct processes into one mechanism.",
            ("viz_fep_02",),
        ),
        (
            "Principle-versus-Process Labels",
            "Label whether a sentence invokes the formal principle, a process theory or an implementation metaphor.",
            "Reader handoff improves when explanatory levels are marked before critique.",
            ("sci_fep_03",),
        ),
        (
            "Falsification Frame Summaries",
            "Summarize what a reader should inspect to challenge an FEP interpretation.",
            "A falsification frame turns broad explanatory language into a reviewable scientific boundary.",
            ("viz_fep_04",),
        ),
    ),
)


_PUB_ACTIVE_INFERENCE = _make(
    "active_inference",
    _AI,
    "viz_active_inference_01",
    (
        (
            "EFE Storyboard Editing",
            "Turn an EFE decomposition into a reader-facing action-selection storyboard.",
            "Storyboards should preserve epistemic and pragmatic terms rather than flattening them into a slogan.",
            ("ai_expected_free_energy",),
        ),
        (
            "Epistemic-Pragmatic Captioning",
            "Caption policy comparisons so information-seeking and preference satisfaction remain distinct.",
            "Caption discipline prevents expected free energy from becoming an opaque total score.",
            ("ai_epistemic_value",),
        ),
        (
            "Preference Map Warnings",
            "State how preference maps encode objectives and where value assumptions enter.",
            "Preference maps need explicit warning labels because they encode aims, not only probabilities.",
            ("viz_active_inference_03",),
        ),
        (
            "Policy Failure-Mode Handoffs",
            "Route policy failure modes from manuscript prose into dashboard and quiz review surfaces.",
            "Failure-mode handoffs help learners test whether a policy example transfers beyond the toy case.",
            ("viz_active_inference_04",),
        ),
    ),
)


_PUB_COMPUTATION = _make(
    "computation",
    _C,
    "viz_computation_01",
    (
        (
            "Deterministic Cover Generation",
            "Generate cover artwork from live project data instead of static decorative files.",
            "A deterministic cover makes the first page part of the reproducible artifact chain.",
            ("comp_visualization",),
        ),
        (
            "Asset Provenance Ledgers",
            "Record which generated assets are figures, cover images, data files or rendered manuscripts.",
            "Asset ledgers keep dashboards and manuscript validators from certifying the wrong surface.",
            ("comp_provenance_gate",),
        ),
        (
            "Artifact Contract Tests",
            "Write tests that prove publication assets exist, are nonblank and are exposed in the intended surface.",
            "Contract tests make generated artwork auditable without turning it into a numbered scientific figure.",
            ("viz_computation_02",),
        ),
        (
            "PDF-Web Parity Reviews",
            "Check that cover, equations and artifact links render coherently across PDF and web outputs.",
            "Parity reviews catch cases where a manuscript render is correct but the learner-facing web handoff drifts.",
            ("viz_computation_03",),
        ),
    ),
)


_PUB_APPLICATIONS = _make(
    "applications",
    _APP,
    "viz_applications_01",
    (
        (
            "Abstract-Cover Alignment",
            "Align the abstract's claim stack with the visual story on the first page.",
            "The cover should prime readers for the validated curriculum, scholarship and dashboard artifacts they will inspect.",
            ("practice_app_domain_fit",),
        ),
        (
            "Stakeholder Reading Paths",
            "Design reading paths for learners, reviewers and implementers without changing the evidence contract.",
            "Different audiences need different entry points, but all paths should terminate in the same generated artifacts.",
            ("viz_applications_02",),
        ),
        (
            "Capstone Synthesis Briefs",
            "Write capstone briefs that connect curriculum skills, figures, claims and roadmap risks.",
            "A synthesis brief shows whether the learner can audit the whole project rather than repeat isolated terms.",
            ("sci_applications_06",),
        ),
        (
            "Review Packet Assembly",
            "Assemble manuscript, dashboard, SkillTree export and validation outputs into a reviewable release packet.",
            "Review packets make external inspection possible by showing the artifact, its source, and its validation evidence together.",
            ("viz_applications_04",),
        ),
    ),
)
