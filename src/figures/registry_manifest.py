from __future__ import annotations

from typing import Any

from src.curriculum.quality import MIN_ASSESSMENTS_PER_SKILL
from src.figures.registry import attach_chart_contract


def figure_registry_payload(
    *,
    include_scholarship: bool = False,
    include_claim_support: bool = False,
    include_roadmap: bool = False,
) -> list[dict[str, Any]]:
    registry = [
        {
            "filename": "curriculum_dag.png",
            "label": "fig:curriculum_dag",
            "caption": (
                "Validator-checked prerequisite DAG generated from the current curriculum graph. "
                "Each point is a skill, horizontal position encodes the pedagogical "
                "stratum, vertical position encodes longest prerequisite depth, gray "
                "segments encode prerequisite edges, root annotations identify the two "
                "allowed foundations, and the inset reports the live graph counts. The "
                "figure is an overview and density check; it verifies connected structure "
                "and visible roots, but detailed learner-quality review still belongs in "
                "the bottleneck, assessment-depth, and neighborhood diagnostics."
            ),
            "alt_text": (
                "Scatter plot of curriculum skills arranged by pedagogical stratum and "
                "prerequisite depth, with gray prerequisite edges, color-coded strata, "
                "root labels for set theory and probability axioms, and an inset showing "
                "the current skill, subject, edge, and depth counts."
            ),
            "generated_by": "src.figures.plots.plot_curriculum_dag",
        },
        {
            "filename": "dependency_strata_flow.png",
            "label": "fig:dependency_strata_flow",
            "caption": (
                "Prerequisite-edge flow matrix generated from every exported learning-path "
                "edge. Rows are prerequisite strata, columns are dependent strata, cell "
                "labels count edges, row and column totals expose load, and the side "
                "bar reports the number of skills per stratum. The "
                "intended reading is directional: diagonal cells show same-stratum "
                "reinforcement, upper-triangular cells show forward movement through "
                "the curriculum, and the lower triangle is shaded and hatched as a "
                "backward-dependency zone that must stay empty. The title carries an "
                "explicit no-backward-edges check, and any populated lower-triangle cell "
                "is ringed in vermillion so a backward dependency the quality gate must "
                "reject is impossible to miss."
            ),
            "alt_text": (
                "Heatmap of prerequisite edge counts from source strata to dependent "
                "strata, paired with a horizontal skill-count bar, with the lower triangle "
                "shaded and hatched as a backward-dependency safety zone that reads as "
                "empty when the no-backward-edges invariant holds, so forward, same-level, "
                "and prohibited backward learning-path dependencies can be distinguished."
            ),
            "generated_by": "src.figures.plots.plot_dependency_strata_flow",
        },
        {
            "filename": "assessment_depth_matrix.png",
            "label": "fig:assessment_depth",
            "caption": (
                "Assessment-depth audit generated from the current Skill assessment tuples "
                "and the configured quality floor. The bar panel counts quiz-bearing skills "
                "by stratum, and the table reports the minimum questions per skill, "
                "below-floor counts, questions per skill, and PASS/REVIEW status. The "
                f"figure makes the {MIN_ASSESSMENTS_PER_SKILL}-question floor visible at "
                "a glance and prevents a structurally valid graph from concealing "
                "shallow completion checks."
            ),
            "alt_text": (
                "Bar and audit-table figure with strata as rows, skill counts, minimum "
                "quiz questions, below-floor counts, questions per skill, and PASS or "
                f"REVIEW status for the required {MIN_ASSESSMENTS_PER_SKILL} failable "
                "assessment questions."
            ),
            "generated_by": "src.figures.plots.plot_assessment_depth_matrix",
        },
        {
            "filename": "curriculum_stratum_balance.png",
            "label": "fig:stratum_balance",
            "caption": (
                "Stratum-balance figure generated from current graph statistics after "
                "expansion. The left panel compares skills and subjects by pedagogical "
                "stratum, the middle panel compares assessment questions with incoming "
                "prerequisite edges, and the right panel adds normalized companion "
                "measures: skills per subject, questions per skill, and incoming edges "
                "per skill. The visual encoding is deliberately parallel so a reader "
                "can separate raw curriculum growth from per-unit load."
            ),
            "alt_text": (
                "Three-panel balance figure: raw skills and subjects by stratum, raw "
                "assessment questions and incoming prerequisite edges, and normalized "
                "per-subject and per-skill measures to bound imbalance interpretation."
            ),
            "generated_by": "src.figures.plots.plot_curriculum_stratum_balance",
        },
        {
            "filename": "free_energy_descent.png",
            "label": "fig:free_energy",
            "caption": (
                "Supplemental noisy-sensor VFE belief sweep generated from the registered "
                "Bayesian and variational-free-energy kernels. The curve encodes "
                "variational free energy as the recognition belief varies, the dashed "
                "horizontal line encodes negative log-evidence, the dotted vertical line "
                "marks the exact posterior, and the labeled points compare uniform belief "
                "with the bound-tight posterior value. The figure teaches bound tightness "
                "for one discrete model and must not be read as evidence that the model "
                "itself is true."
            ),
            "alt_text": (
                "Line plot for the noisy-sensor model with recognition belief q present "
                "on the x-axis and variational free energy in nats on the y-axis, marking "
                "the exact posterior minimum, the negative log-evidence reference line, "
                "and the looser uniform-belief comparison point."
            ),
            "generated_by": "src.figures.plots.plot_free_energy_descent",
        },
        {
            "filename": "efe_decomposition.png",
            "label": "fig:efe",
            "caption": (
                "Supplemental expected-free-energy decomposition for the sample and commit "
                "task. The left panel uses grouped bars to compare total expected free "
                "energy and epistemic value at the reference sensor precision, while the "
                "right panel sweeps sensor precision and marks the precision-regime switch "
                "where the preferred policy changes. The figure supports a bounded teaching "
                "claim about this policy set and preference structure, not a universal "
                "statement that information seeking always wins."
            ),
            "alt_text": (
                "Two-panel figure for the sample and commit task: grouped bars compare "
                "total expected free energy and epistemic value at the reference sensor "
                "precision, and line curves sweep sensor precision to mark where the "
                "preferred policy switches."
            ),
            "generated_by": "src.figures.plots.plot_efe_decomposition",
        },
        {
            "filename": "planning_lookahead.png",
            "label": "fig:planning_lookahead",
            "caption": (
                "Supplemental multi-step planning look-ahead generated from the discrete "
                "active-inference planning kernel. The left panel contrasts the measured "
                "look-ahead gain (greedy G minus optimal G, per the figure's formula — "
                "positive when the optimal multi-step plan beats the myopic policy) for a "
                "decoupled sample/commit model, where the gain is zero, and a "
                "coupled investment model, where paying a worse first step to unlock the goal "
                "yields a positive gain. The right panel shows the cumulative expected free "
                "energy of every enumerated policy in the coupled model with the greedy and "
                "optimal policies marked. The figure supports a bounded claim that look-ahead "
                "value is model dependent, not a universal property of planning."
            ),
            "alt_text": (
                "Two-panel figure: a bar chart comparing the look-ahead gain in a decoupled "
                "model (zero) against a coupled investment model (positive), and a bar chart "
                "of cumulative expected free energy for every two-step policy in the coupled "
                "model with the greedy and optimal policies highlighted."
            ),
            "generated_by": "src.figures.plots.plot_planning_lookahead",
        },
        {
            "filename": "predictive_coding_descent.png",
            "label": "fig:predictive_coding",
            "caption": (
                "Supplemental continuous-state predictive-coding descent generated from "
                "the linear-Gaussian kernel. The left panel shows the latent estimate "
                "settling from the prior mean to the analytic precision-weighted posterior "
                "(dashed) as it balances the sensory and prior prediction errors; the right "
                "panel shows the free energy descending monotonically to its analytic "
                "minimum. The figure supports a bounded claim that prediction-error descent "
                "implements exact Gaussian inference for this one model, not a universal "
                "convergence guarantee for all generative models."
            ),
            "alt_text": (
                "Two-panel figure: a line of the latent estimate converging from the prior "
                "mean to a dashed analytic-posterior line over descent steps, and a "
                "monotonically decreasing free-energy curve reaching its minimum."
            ),
            "generated_by": "src.figures.plots.plot_predictive_coding",
        },
        {
            "filename": "graph_bottlenecks.png",
            "label": "fig:graph_bottlenecks",
            "caption": (
                "Graph-bottleneck ranking generated by counting downstream dependents for "
                "each prerequisite skill. Bars encode dependent fan-out, y-axis labels pair "
                "skill ids with readable names, hatch patterns and color encode the "
                "skill's stratum, and annotations report dependent count, graph depth, and "
                "stratum text. The figure turns an otherwise hidden maintenance risk into "
                "a review queue: weak explanations at high-fan-out nodes can affect many "
                "later skills even when the graph remains acyclic."
            ),
            "alt_text": (
                "Horizontal bar chart listing prerequisite skills with the most dependent "
                "skills, labeled by skill id and readable name, color-coded and hatched by "
                "stratum, and annotated with dependent counts, depth, and stratum text so "
                "high-impact review targets can be identified without relying on color."
            ),
            "generated_by": "src.figures.plots.plot_graph_bottlenecks",
        },
        {
            "filename": "skill_neighborhood_paths.png",
            "label": "fig:skill_neighborhood_paths",
            "caption": (
                "Skill-neighborhood path view generated from the current prerequisite "
                "graph after structural checks by selecting a representative longest path "
                "from foundation toward "
                "deep application. Position along the line encodes prerequisite depth, "
                "vertical placement and color encode stratum, and the checkpoint ledger "
                "names the start, each stratum transition, and the endpoint without "
                "requiring angled micro-labels. The figure is a diagnostic complement to "
                "the dense DAG: it sacrifices global completeness so a reader can inspect "
                "one concrete chain of dependencies without zooming the full network."
            ),
            "alt_text": (
                "Path-style diagram of a representative longest curriculum path, with "
                "skills ordered by prerequisite depth, color-coded by stratum, and paired "
                "with a checkpoint ledger so local dependency sequence can be reviewed "
                "without scanning the full DAG."
            ),
            "generated_by": "src.figures.plots.plot_skill_neighborhood_paths",
        },
        {
            "filename": "semantic_prerequisite_coverage.png",
            "label": "fig:semantic_prerequisite_coverage",
            "caption": (
                "Semantic-prerequisite coverage generated from the live graph and the "
                "quality gate's concept map. For each load-bearing concept (KL divergence, "
                "Markov chain, Laplace approximation, ELBO) the long bar "
                "counts skills that reach the concept's defining skill through their "
                "prerequisite closure, and the inner bar counts skills actually assessed on "
                "the concept. The subtitle reports the gate verdict: a passing curriculum "
                "has zero skills assessed on a concept they cannot have learned, so every "
                "inner bar is contained by the structure that makes it reachable."
            ),
            "alt_text": (
                "Horizontal bar chart with one row per load-bearing concept, showing the "
                "number of skills whose prerequisite closure reaches the concept's defining "
                "skill alongside the number of skills assessed on the concept, annotated "
                "with the semantic-prerequisite gate verdict of zero violations."
            ),
            "generated_by": "src.figures.plots.plot_semantic_prerequisite_coverage",
        },
        {
            "filename": "validation_intent_mismatch_matrix.png",
            "label": "fig:validation_intent_mismatch_matrix",
            "caption": (
                "Validation-intent mismatch matrix generated from the same render "
                "configuration that writes the figure registry. Rows enumerate concrete "
                "false-certification classes: a rendered PNG missing from the registry, "
                "a registry row without a readable file, a registered label missing from "
                "the manuscript, a registered figure missing from the dashboard, a missing "
                "roadmap metric, and a stale generated manifest. Columns identify whether "
                "the source-of-truth, manuscript gate, or dashboard gate is expected to "
                "catch that mismatch before release. One cell is deliberately open: the "
                "learner dashboard has no roadmap surface, so a missing roadmap metric is "
                "caught at source-of-truth and by the manuscript gate but cannot be caught "
                "by a learner-facing page. That open cell is a scope boundary rather than "
                "an unguarded class, and it is drawn rather than hidden."
            ),
            "alt_text": (
                "Matrix of validation mismatch classes with rows for missing registry "
                "entries, missing figure files, missing manuscript labels, missing "
                "dashboard artifacts, missing roadmap metrics, and stale manifests, plus "
                "columns showing the source-of-truth, manuscript, and dashboard gates "
                "that bind each class."
            ),
            "generated_by": "src.figures.plots.plot_validation_intent_mismatch_matrix",
        },
        {
            "filename": "visual_evidence_contract_ladder.png",
            "label": "fig:visual_evidence_contract_ladder",
            "caption": (
                "Visual-evidence contract ladder generated from the live curriculum graph "
                "after adding the focused visual-evidence curriculum slice. The six rungs "
                "move from question contract to data grain, encoding strength, annotation "
                "boundary, static and mobile survival, and negative-control validation. "
                "Each rung names the exact skill identifier that carries the review step, "
                "and the bottom labels report whether that skill is present in the graph "
                "and at what prerequisite depth. The figure is a validation and authoring "
                "workflow view; it does not claim that learners improve because the visual "
                "surface exists."
            ),
            "alt_text": (
                "Annotated horizontal ladder with six numbered rungs for question "
                "contract, data grain, encoding strength, annotation boundary, static "
                "and mobile survival, and negative-control validation, each labeled with "
                "the corresponding visual-evidence skill id and live graph registration "
                "status."
            ),
            "generated_by": "src.figures.plots.plot_visual_evidence_contract_ladder",
        },
        {
            "filename": "kernel_sensitivity_profiles.png",
            "label": "fig:kernel_sensitivity_profiles",
            "caption": (
                "Kernel-sensitivity profiles generated from the noisy-sensor posterior, "
                "variational-free-energy sweep, and expected-free-energy precision sweep. "
                "The left panel varies the base rate, the middle panel repeats the VFE "
                "bound-tightness profile, and the right panel shows the policy-regime "
                "boundary for sample versus commit. The figure states where the toy "
                "examples are sensitive or stable; it does not introduce empirical learner "
                "statistics or population-level inference."
            ),
            "alt_text": (
                "Three-panel sensitivity figure: posterior probability changes with the "
                "base rate, variational free energy reaches the evidence bound at the "
                "posterior, and expected-free-energy policy curves cross at the computed "
                "precision boundary."
            ),
            "generated_by": "src.figures.plots.plot_kernel_sensitivity_profiles",
        },
        {
            "filename": "vfe_efe_skilltree_bridge.png",
            "label": "fig:vfe_efe_skilltree_bridge",
            "caption": (
                "VFE/EFE SkillTree bridge generated from the current curriculum graph. "
                "Rows are the real SkillTree subjects that carry core VFE, core EFE, "
                "supplement interpretation, and mastery handoff material; columns show "
                "subject identifiers, skill counts, prerequisite-edge counts, graph-depth "
                "ranges, representative skill ids, and distinct learn-route and quiz-route "
                "fragments. "
                "The figure connects the supplement's mathematical plots to quiz-gated "
                "curriculum nodes without manually copying the SkillTree database."
            ),
            "alt_text": (
                "Table-style figure listing six VFE and EFE SkillTree subjects with "
                "subject ids, skill counts, prerequisite-edge counts, depth ranges, "
                "representative skill ids, plus separate learn-route and quiz-route fragments."
            ),
            "generated_by": "src.figures.plots.plot_vfe_efe_skilltree_bridge",
        },
    ]
    if include_scholarship:
        registry.append(
            {
                "filename": "scholarship_coverage.png",
                "label": "fig:scholarship_coverage",
                "caption": (
                    "Scholarship coverage generated from manuscript citations, BibTeX "
                    "entries, and source-matrix lanes. The bar panel compares cited "
                    "sources against the declared matrix for each lane, and the heatmap "
                    "panel shows which manuscript sections carry each scholarship lane. "
                    "The figure prevents bibliography size from being mistaken for "
                    "support quality by showing both coverage balance and section-level "
                    "placement. The gold overlay exposes the selected historical layer "
                    "from ancient and medieval sources through the eighteenth century."
                ),
                "alt_text": (
                    "Bar and heatmap figure showing cited scholarship sources by support "
                    "lane and the distribution of citation lanes across manuscript "
                    "sections, making missing or overconcentrated support visible."
                ),
                "generated_by": "src.figures.plots.plot_scholarship_coverage",
            }
        )
        registry.append(
            {
                "filename": "open_science_source_map.png",
                "label": "fig:open_science_sources",
                "caption": (
                    "Open-science learning-source ledger generated from scholarship "
                    "support rows and generated course-material pointers. Summary "
                    "cards expose local material records, external pointer count, "
                    "cognitive knowledge-base pointers, and topic-matched KB skills; "
                    "ledger rows keep the course repository, cognitive knowledge-base "
                    "source, Institute homepage, website repository, and START source "
                    "visible with their roles. The website row is distinct from course "
                    "and knowledge-base pointers. The figure records pinned links and "
                    "cited support surfaces; it does not copy or endorse external prose."
                ),
                "alt_text": (
                    "Ledger chart showing Active Inference Institute course-material "
                    "sources, KB pointers, topic-matched KB skills, and cited support "
                    "rows, including the community website repository, so open-science "
                    "learning sources are auditable without implying quality or endorsement."
                ),
                "generated_by": "src.figures.plots.plot_open_science_source_map",
            }
        )
        registry.append(
            {
                "filename": "validation_surface_matrix.png",
                "label": "fig:validation_surface_matrix",
                "caption": (
                    "Validation-surface matrix generated from the live graph, claim "
                    "registry, scholarship audit, and configured figure inventory. Matrix "
                    "cells show which gates bind generated JSON, negative controls, "
                    "manuscript text, dashboard artifacts, release documentation, and "
                    "SkillTree handoff, export integrity, and material-link safety; row and "
                    "column tick labels state bound-cell totals "
                    "so scope gaps remain visible "
                    "without reading the heatmap color. The side bars report the live evidence "
                    "counts emitted by the build. "
                    "The figure is a release-integrity view: it shows which surfaces are "
                    "actually certified by validators and which are outside a given gate."
                ),
                "alt_text": (
                    "Two-panel figure with a validation-gate matrix across generated JSON, "
                    "tests, manuscript, dashboard, release documentation, SkillTree handoff, "
                    "export integrity, and material-link safety surfaces, row and column bound "
                    "totals, plus live bar counts for "
                    "skills, subjects, "
                    "prerequisite edges, assessment questions, claims, cited sources, and "
                    "figures."
                ),
                "generated_by": "src.figures.plots.plot_validation_surface_matrix",
            }
        )
        registry.append(
            {
                "filename": "scholarship_source_health.png",
                "label": "fig:scholarship_source_health",
                "caption": (
                    "Scholarship source-health summary generated from locator syntax, "
                    "lane assignment, and support-role specificity checks. Bars separate "
                    "total matrixed sources, offline validation issues, and optionally "
                    "online-checked sources. The figure distinguishes citation coverage "
                    "from source metadata quality, so a source can be present in the "
                    "matrix while still requiring locator or role repair before release."
                ),
                "alt_text": (
                    "Bar chart showing scholarship source count, offline source-health "
                    "issues, and optionally online checked sources so citation metadata "
                    "quality can be audited separately from manuscript coverage."
                ),
                "generated_by": "src.figures.plots.plot_scholarship_source_health",
            }
        )
    if include_claim_support:
        registry.append(
            {
                "filename": "scientific_evidence_matrix.png",
                "label": "fig:scientific_evidence_matrix",
                "caption": (
                    "Scientific-evidence matrix generated from manuscript claim-support "
                    "anchors and data/manuscript_claim_support.yaml. Rows are claim "
                    "types, columns are evidence classes, cell labels count anchored "
                    "claims, and the side panel counts claims by type. The figure makes "
                    "the manuscript's epistemic status visible by separating computed "
                    "claims, descriptive counts, simulations, literature claims, scope "
                    "limits, delivery claims, and visual claims."
                ),
                "alt_text": (
                    "Heatmap of anchored manuscript claim types by evidence classes such "
                    "as claim tokens, manuscript variables, citations, figures, validators, "
                    "and limitation markers, with a side bar counting claims per type."
                ),
                "generated_by": "src.figures.plots.plot_scientific_evidence_matrix",
            }
        )
    if include_roadmap:
        registry.append(
            {
                "filename": "roadmap_risk.png",
                "label": "fig:roadmap_risk",
                "caption": (
                    "Roadmap-status summary generated from tasks.yaml and the live "
                    "metrics stored in the roadmap source data. The first panel counts "
                    "roadmap items by status, the middle panel groups remaining open or "
                    "blocked work by surface with direct release-class segment labels, "
                    "hatching, and surface totals, and the final panel shows live "
                    "curriculum, assessment, scholarship, and figure metrics. The figure "
                    "separates external blockers from the git-authorization release "
                    "hygiene task so release-readiness text must agree with the same "
                    "machine-readable source."
                ),
                "alt_text": (
                    "Three-panel figure with roadmap task status counts, remaining work "
                    "grouped by surface and release class with external-blocker and "
                    "git-authorization segment labels, plus live project metric bars for "
                    "curriculum, assessment, scholarship, and figure surfaces."
                ),
                "generated_by": "src.figures.plots.plot_roadmap_risk",
            }
        )
    _attach_figure_semantics(registry)
    # Imported lazily: src.screenshots.manifest reads the registry contract from
    # src.figures.registry, and importing that package here at module scope would
    # close a cycle through src/figures/__init__.py.
    from src.screenshots.manifest import captured_registry_payload

    # Captured browser evidence is appended after the deterministic rows so it
    # inherits the same registry contract, caption/alt-text floors, and dashboard
    # parity, while carrying evidence_kind="captured" for every consumer that has
    # to treat a recording differently from a render.
    registry.extend(captured_registry_payload())
    return registry


def _attach_figure_semantics(registry: list[dict[str, Any]]) -> None:
    """Attach semantic metadata required by the manuscript artifact validator."""
    generic = {
        "accessibility_note": "Uses direct labels, high-contrast text and a colorblind-safe palette so the key comparison is not encoded by hue alone.",
        "chart_family": "audit summary",
        "claim_tokens": [],
        "data_grain": "One generated figure-level evidence surface rendered from project artifact records.",
        "data_source": "Generated artifact data emitted by the project build pipeline.",
        "encoding": "Quantities are encoded with labeled axes, direct annotations and categorical color only where grouping is meaningful.",
        "false_certification_risk": "Prevents a polished visual from certifying a stale or unsupported manuscript surface.",
        "interpretation_boundary": "The figure describes the generated artifact state and should not be read as learner-study evidence.",
        "mobile_note": "Dense labels remain available through the dashboard full-size image link.",
        "non_color_encoding": "Direct labels, ordered placement, axis labels and source notes carry the reading without relying on hue alone.",
        "palette_policy": "single-root preferred with neutral context and explicit status accents",
        "palette_roots": ["blue", "gray"],
        "qa_role": "Gives reviewers a visual checksum for one generated manuscript surface.",
        "subtitle": "Source: generated project artifacts; units and boundaries are declared per figure.",
        "takeaway": "The plotted structure makes a specific validation or interpretation boundary inspectable.",
        "visual_grammar": (
            "Neutral context is gray; primary evidence is blue; successful gates are "
            "green; caution states are amber; violations are vermillion; strata use "
            "the project colorblind-safe categorical palette with direct labels."
        ),
    }
    overrides: dict[str, dict[str, Any]] = {
        "curriculum_dag.png": {
            "data_source": "CurriculumGraph levels, strata and prerequisite edges from build_curriculum().",
            "encoding": "Node position encodes stratum and prerequisite depth; direct stratum labels replace detached legend reliance; quiet gray lines encode prerequisite dependencies.",
            "takeaway": "The curriculum is connected from foundations to applications without hidden cycles.",
            "false_certification_risk": "Catches graph growth that looks complete while hiding roots, cycles or disconnected canopy skills.",
        },
        "dependency_strata_flow.png": {
            "data_source": "CurriculumGraph prerequisite_edges aggregated by prerequisite and dependent stratum.",
            "encoding": "Sequential heatmap cells encode edge counts; row and column totals expose load; a side bar encodes skill counts by stratum; the lower triangle is the backward-dependency zone that must stay empty.",
            "takeaway": "Forward and same-stratum dependencies dominate the exported learning path, and the hatched lower-triangle safety zone is empty so no backward prerequisite edge survived the gate.",
            "false_certification_risk": "Prevents backward prerequisite drift from being missed: a populated lower-triangle cell is ringed in vermillion against the empty backward zone instead of blending into the dense node-link graph.",
        },
        "assessment_depth_matrix.png": {
            "data_source": "Current curriculum assessment tuples after quality checks.",
            "encoding": "A floor-pass audit table/bar hybrid encodes quiz-bearing skill counts, minimum questions, below-floor counts, questions per skill and PASS/REVIEW status.",
            "takeaway": (
                f"Every stratum satisfies the {MIN_ASSESSMENTS_PER_SKILL}-question "
                "floor after quality hardening."
            ),
            "false_certification_risk": "Prevents shallow quizzes from passing because the graph structure alone is valid.",
        },
        "curriculum_stratum_balance.png": {
            "data_source": "Current curriculum graph statistics grouped by pedagogical stratum after structural checks.",
            "encoding": "Horizontal bars encode raw skills, subjects, assessment questions and incoming edges; normalized companion dots encode skills per subject, questions per skill and incoming edges per skill.",
            "takeaway": "Expansion is visible across all layers rather than concentrated in one stratum.",
            "false_certification_risk": "Prevents skill-count growth from hiding uneven subject or edge distribution.",
        },
        "free_energy_descent.png": {
            "claim_tokens": [
                "bayes_posterior_present_given_positive",
                "neg_log_evidence_positive",
                "vfe_descent_start",
                "vfe_descent_end",
            ],
            "data_source": "Noisy-sensor inference claims and vfe_belief_sweep() kernel outputs.",
            "encoding": "A line encodes VFE over beliefs, with reference marks for posterior and evidence.",
            "takeaway": "The variational bound is tight at the exact posterior for this model.",
            "interpretation_boundary": "The sweep is a one-dimensional discrete diagnostic, not proof of model truth.",
            "false_certification_risk": "Prevents hand-typed free-energy annotations or overgeneralized bound claims.",
        },
        "efe_decomposition.png": {
            "claim_tokens": [
                "agent_g_sample",
                "agent_g_commit",
                "agent_epistemic_sample",
                "agent_epistemic_commit",
                "agent_regime_switch_precision",
            ],
            "data_source": "Expected-free-energy claims and efe_precision_sweep() kernel outputs.",
            "encoding": "Grouped bars encode policy terms and lines encode policy scores across precision.",
            "takeaway": "Information seeking is preferred only inside the plotted sensor-precision regime.",
            "interpretation_boundary": "The conclusion is tied to the specified preferences, policy set and toy model.",
            "false_certification_risk": "Prevents one EFE example from being certified as a universal policy law.",
        },
        "planning_lookahead.png": {
            "claim_tokens": [
                "plan_greedy_policy_g",
                "plan_optimal_policy_g",
                "plan_lookahead_gain_coupled",
                "plan_lookahead_gain_decoupled",
            ],
            "question": "When does multi-step look-ahead actually beat a greedy myopic active-inference policy?",
            "data_source": "Multi-step planning kernel outputs for the decoupled sample/commit and coupled investment models.",
            "data_grain": "One look-ahead-gain bar per planning regime plus one cumulative-expected-free-energy bar per enumerated two-step policy in the coupled model.",
            "encoding": "Left bars encode the optimal-minus-greedy look-ahead gain per regime; right bars encode cumulative expected free energy per policy with greedy amber and optimal green.",
            "non_color_encoding": "Direct value labels, regime axis text, policy axis labels and a greedy/optimal/other legend carry the reading without relying on hue.",
            "static_read": "The static panels keep both regimes, every policy value and the greedy/optimal marks visible so the measured gain is auditable without interaction.",
            "mobile_read": "On narrow screens read the left panel as two regime bars and the right panel as four labelled policy bars.",
            "takeaway": "Look-ahead pays only in the coupled model, where immediate and long-run value diverge; the decoupled gain is exactly zero.",
            "interpretation_boundary": "The gain is a deterministic kernel measurement on two toy models, not a universal claim that planning always helps.",
            "failure_mode": "Prevents the planning example from implying look-ahead is universally beneficial by showing the honest zero-gain regime beside the positive one.",
            "false_certification_risk": "Prevents the planning example from implying look-ahead is universally beneficial by showing the honest zero-gain regime beside the positive one.",
        },
        "predictive_coding_descent.png": {
            "claim_tokens": [
                "pc_posterior_estimate",
                "pc_sensory_prediction_error",
                "pc_prior_prediction_error",
            ],
            "question": "Does continuous prediction-error descent actually reach exact Gaussian inference?",
            "data_source": "Linear-Gaussian predictive-coding descent kernel (predictive_coding_data()).",
            "data_grain": "One latent-estimate value and one free-energy value per gradient-descent step on a single linear-Gaussian model.",
            "encoding": "Left line traces the estimate to the dashed analytic-posterior reference; right line traces the monotonically descending free energy.",
            "non_color_encoding": "Direct value labels, a converged-at-step marker, observation/prior reference lines and axis text carry the reading without relying on hue.",
            "static_read": "The static panels keep the full descent trajectory, the analytic-posterior reference, and the free-energy minimum visible without interaction.",
            "mobile_read": "On narrow screens read the left panel as the estimate approaching the dashed posterior line and the right panel as the falling free energy.",
            "takeaway": "Prediction-error descent settles at the exact analytic posterior mean and minimizes free energy for this linear-Gaussian model.",
            "interpretation_boundary": "Exactness is specific to the linear-Gaussian case; nonlinear or hierarchical models are not covered by this one descent.",
            "failure_mode": "Prevents predictive coding from being presented as exact inference in general by tying the claim to a single linear-Gaussian model with a known fixed point.",
            "false_certification_risk": "Prevents predictive coding from being presented as exact inference in general by tying the claim to a single linear-Gaussian model with a known fixed point.",
        },
        "kernel_sensitivity_profiles.png": {
            "claim_tokens": [
                "bayes_posterior_present_given_positive",
                "agent_regime_switch_precision",
            ],
            "data_source": "Noisy-sensor posterior, VFE sweep and EFE precision sweep kernel outputs.",
            "encoding": "Three line panels encode posterior, VFE and policy-score sensitivity curves.",
            "takeaway": "Kernel examples have explicit base-rate, bound-tightness and policy-regime boundaries.",
            "interpretation_boundary": "Sensitivity curves describe deterministic toy kernels, not population effects.",
            "false_certification_risk": "Prevents scientific language from implying untested statistical generality.",
        },
        "vfe_efe_skilltree_bridge.png": {
            "data_source": "Current CurriculumGraph subjects, skills, prerequisite edges, depth levels, learn-route ids and quiz-route ids after structural checks.",
            "encoding": "Rows encode real SkillTree subjects; columns encode skill counts, prerequisite-edge counts, depth ranges, representative skill ids, learn routes and quiz routes.",
            "table_companion_id": "companion:vfe_efe_skilltree_bridge",
            "takeaway": "The VFE/EFE supplement is connected to concrete quiz-gated SkillTree subjects rather than floating as an isolated derivation.",
            "interpretation_boundary": "The bridge verifies curriculum/export wiring for the supplement and does not measure learner outcomes or biological validity.",
            "false_certification_risk": "Prevents supplemental mathematical figures from being treated as connected to SkillTree without real subject, skill, edge and quiz-route evidence.",
        },
        "graph_bottlenecks.png": {
            "data_source": "CurriculumGraph prerequisite edges counted by downstream dependent skills.",
            "data_grain": "One skill id/name row per high-fanout prerequisite, ranked by downstream dependent count from the live graph.",
            "encoding": "Horizontal bars encode dependent fan-out; y labels pair skill ids with readable names, small chips state stratum, and annotations report dependent count plus depth.",
            "non_color_encoding": "Rank order and direct labels carry the bottleneck reading; stratum chips and depth annotations preserve meaning when hue is unavailable.",
            "palette_policy": "relaxed multi-category for stratum identity plus neutral annotation text",
            "palette_roots": ["blue", "gold", "orange", "olive", "pink"],
            "table_companion_id": "companion:graph_bottlenecks",
            "takeaway": "High-fan-out skills are visible as priority review targets.",
            "false_certification_risk": "Prevents broad downstream learner risk from hiding inside a valid DAG.",
        },
        "skill_neighborhood_paths.png": {
            "data_source": "Longest-path and prerequisite-neighborhood data from the current graph after structural checks.",
            "encoding": "A path line encodes depth order; stratum bands and node positions encode the local route, while a checkpoint ledger names the start, each stratum transition and endpoint.",
            "non_color_encoding": "Depth order, checkpoint ledger text, y-axis stratum names, callout boxes and the endpoint note preserve the path reading without relying on node color.",
            "takeaway": "A local path view plus checkpoint ledger makes representative dependency context inspectable without angled micro-labels.",
            "false_certification_risk": "Prevents the dense overview graph from being the only diagnostic surface.",
        },
        "scholarship_coverage.png": {
            "data_source": "Scholarship audit over manuscript citations, BibTeX and source-matrix lanes.",
            "encoding": "Bars encode lane coverage and a heatmap encodes citation lanes by section.",
            "takeaway": "Every cited source has a declared lane and manuscript support role.",
            "false_certification_risk": "Prevents bibliography size from masquerading as claim-level support.",
        },
        "open_science_source_map.png": {
            "data_source": "Scholarship source matrix rows plus generated course_material_index/course_material_audit source coverage.",
            "data_grain": "One course-material source row per pinned external source plus cited support rows for non-course Institute surfaces; summary cards aggregate all generated skill material records.",
            "encoding": "Summary cards encode material records, external pointers, KB pointers and KB topic-skill coverage; ledger rows encode source type, source locator, role text and course/scholarship boundary.",
            "non_color_encoding": "Direct source labels, count cards, source-type badges, hatching, locator text and role summaries carry the ledger reading without relying on stripe color.",
            "takeaway": "The cognitive knowledge-base linkage is visible as generated course-material evidence, not hidden behind scholarship-only rows.",
            "false_certification_risk": "Prevents pinned course-material links, especially cognitive knowledge-base topic pointers, from being omitted while open-science support still appears certified.",
        },
        "validation_surface_matrix.png": {
            "data_source": "Live graph, claim registry, scholarship audit, configured figure counts and release-readiness inventory bindings.",
            "data_grain": "One validator-test binding row per artifact or release-documentation surface, one column per release gate family, plus live generated count bars.",
            "encoding": "Binary matrix cells encode bound versus n/a gate status with row and column totals in the tick labels; bars encode generated evidence counts.",
            "non_color_encoding": "Cell text, row totals, column totals, grid lines and direct bar labels identify bound versus n/a without relying on the heatmap color.",
            "palette_policy": "single-root preferred with neutral n/a cells and blue bound cells",
            "palette_roots": ["blue", "gray"],
            "takeaway": "Release claims are tied to explicit artifact validators, release inventory checks and live counts.",
            "false_certification_risk": "Prevents stale prose, metadata or release-inventory text from passing without generated evidence.",
        },
        "scholarship_source_health.png": {
            "data_source": "Scholarship source-health audit over locators, roles and optional online checks.",
            "encoding": "Status cards encode source count, offline issue count and online-check mode; a ledger below separates local metadata pass state from optional network reachability.",
            "non_color_encoding": "Card labels, PASS/NOT RUN/LOCAL status text and the release-boundary row preserve the source-health reading without hue.",
            "table_companion_id": "companion:scholarship_source_health",
            "takeaway": "Locator health is separated from citation coverage and manuscript use.",
            "false_certification_risk": "Prevents syntactically valid citations from hiding weak locator metadata.",
        },
        "scientific_evidence_matrix.png": {
            "data_source": "Manuscript claim-support anchors and data/manuscript_claim_support.yaml rows.",
            "encoding": "Heatmap cells encode evidence classes by claim type with side counts.",
            "takeaway": "Scientific claims are divided by computed, descriptive, literature and scope support.",
            "false_certification_risk": "Prevents strong scientific language from passing without an evidence class.",
        },
        "roadmap_risk.png": {
            "data_source": "tasks.yaml live metrics, status fields and generated roadmap state.",
            "data_grain": "tasks.yaml task records aggregated by status and active surface, plus the generated live_metrics block.",
            "encoding": "Bars encode roadmap status counts, stacked bars encode remaining work by surface and release class with direct total labels, and live project metrics appear as labeled horizontal bars.",
            "non_color_encoding": "Panel order, axis labels, hatching, EXT/GIT segment codes, stacked-bar totals, metric labels and status text preserve the release-state reading without color.",
            "palette_policy": "hard two-root cap for active risk states plus neutral live metrics and green done status",
            "palette_roots": ["green", "orange", "gray"],
            "takeaway": "Release-state claims are tied to machine-readable roadmap state while external blockers and git-authorization hygiene stay visibly distinct.",
            "false_certification_risk": "Prevents completed-status drift or git-authorization work from being mistaken for external release readiness.",
        },
        "semantic_prerequisite_coverage.png": {
            "chart_family": "concept-reach lollipop audit",
            "data_source": "Live curriculum graph prerequisite closure and the quality gate's concept map.",
            "encoding": "Wide lollipop stems encode skills reaching each concept definer, filled dots encode assessed subsets, and direct ratio labels state assessed skills inside each reachable set.",
            "non_color_encoding": "Open versus filled markers, direct assessed/reachable labels, concept/definer row labels and the verdict badge preserve the gate reading without hue.",
            "takeaway": "Every skill assessed on a load-bearing concept reaches its defining skill through prerequisites.",
            "false_certification_risk": "Prevents a skill from being tested on a concept a learner could not yet have learned.",
            "subtitle": "Source: prerequisite closure and the semantic-prerequisite concept map; counts are skills.",
            "qa_role": "Confirms the semantic-prerequisite gate passes with zero inversions on the live graph.",
        },
        "validation_intent_mismatch_matrix.png": {
            "chart_family": "mismatch-class coverage matrix",
            "data_source": "Canonical figure registry render configuration, validation gate inventory and enabled optional audit surfaces.",
            "encoding": "Rows encode false-certification classes; columns encode the source-of-truth, manuscript and dashboard gates expected to catch each class.",
            "takeaway": "Release validation is specified in terms of concrete mismatch classes, not only green script exits.",
            "false_certification_risk": "Prevents a validator from claiming coverage without stating which stale registry, file, manuscript, dashboard, roadmap or manifest drift it catches.",
            "subtitle": "Source: render configuration and validation-gate intent; cells are bound/gap classes.",
            "qa_role": "Documents the negative-control classes the artifact validators must continue to cover.",
        },
        "visual_evidence_contract_ladder.png": {
            "chart_family": "annotated contract ladder",
            "data_source": "Live CurriculumGraph skills, prerequisite depths and additive figure-registry chart-contract fields.",
            "data_sources": [
                "src.curriculum.catalog.build_curriculum",
                "src.figures.plots.render_all",
                "output/figures/figure_registry.json",
            ],
            "data_grain": "One ordered ladder rung per visual-evidence review skill and contract stage.",
            "encoding": "Six ordered ladder rungs encode the visual-evidence contract lifecycle; node color encodes the skill stratum and compact chips encode the review obligation for each rung.",
            "palette_policy": "relaxed multi-category for stratum identity with neutral connector lines",
            "palette_roots": ["blue", "gold", "orange", "olive", "pink"],
            "non_color_encoding": "Numbered rung order, skill ids, chips, and fail-closed endpoint labels carry the contract even without color.",
            "question": "How does Active Skillference teach visual evidence from chart question to negative-control validation?",
            "takeaway": "The new visual-evidence skills turn figure design into a prerequisite-gated audit path instead of a decorative reporting layer.",
            "static_read": "The static ladder preserves all six stages, the exact skill identifiers, and the fail-closed QA endpoint without hover interaction.",
            "mobile_read": "On narrow screens the figure can be read as six numbered contract stages from question to negative control.",
            "failure_mode": "Prevents a polished figure from passing review without a question, data-grain, encoding, annotation, static/mobile, or negative-control contract.",
            "false_certification_risk": "Prevents a polished figure from passing review without a question, data-grain, encoding, annotation, static/mobile, or negative-control contract.",
            "subtitle": "Source: live curriculum graph and generated figure-registry contract metadata.",
            "interpretation_boundary": "The ladder validates deterministic authoring and artifact wiring; it does not measure learner outcomes.",
            "mobile_note": "Read the six numbered rungs sequentially; the dashboard detail card exposes the same contract fields.",
            "qa_role": "Confirms that visual-evidence curriculum skills, registry metadata, manuscript references and dashboard exposure share one contract.",
        },
    }
    chart_families = {
        "assessment_depth_matrix.png": "floor-pass audit table",
        "curriculum_dag.png": "lane node-link DAG",
        "curriculum_stratum_balance.png": "bar and normalized-dot audit",
        "dependency_strata_flow.png": "matrix heatmap with totals",
        "efe_decomposition.png": "bar plus regime-sweep line chart",
        "free_energy_descent.png": "line chart with reference marks",
        "graph_bottlenecks.png": "top-N horizontal bar chart with stratum chips",
        "kernel_sensitivity_profiles.png": "small-multiple sensitivity lines",
        "open_science_source_map.png": "learning-source ledger",
        "roadmap_risk.png": "roadmap status and blocker-surface bars",
        "scholarship_coverage.png": "bar plus citation-lane heatmap",
        "scholarship_source_health.png": "source-health status ledger",
        "scientific_evidence_matrix.png": "claim-evidence heatmap",
        "skill_neighborhood_paths.png": "representative path trace with checkpoint ledger",
        "validation_intent_mismatch_matrix.png": "mismatch-class coverage matrix",
        "validation_surface_matrix.png": "binary validation matrix",
        "visual_evidence_contract_ladder.png": "annotated contract ladder",
        "vfe_efe_skilltree_bridge.png": "table-card bridge",
    }
    subtitles = {
        "assessment_depth_matrix.png": (
            "Source: exported assessment tuples; floor is "
            f"{MIN_ASSESSMENTS_PER_SKILL} questions per skill."
        ),
        "curriculum_dag.png": "Source: current CurriculumGraph after structural checks; x=stratum, y=longest prerequisite chain depth.",
        "curriculum_stratum_balance.png": "Source: graph stats grouped by stratum; raw counts and per-unit ratios share the same build.",
        "dependency_strata_flow.png": "Source: prerequisite-edge aggregation; counts are exported dependency links.",
        "efe_decomposition.png": "Source: EFE toy-agent kernel; units are nats across the stated policy set.",
        "free_energy_descent.png": "Source: deterministic noisy-sensor kernel; units are nats.",
        "graph_bottlenecks.png": "Source: prerequisite fan-out counts; units are dependent skills.",
        "kernel_sensitivity_profiles.png": "Source: deterministic posterior, VFE and EFE sweeps; units are probabilities and nats.",
        "open_science_source_map.png": "Source: scholarship rows plus generated course-material index/audit pointer coverage.",
        "planning_lookahead.png": "Source: discrete active-inference planning kernel; units are nats of expected free energy across the enumerated two-step policy set.",
        "predictive_coding_descent.png": "Source: linear-Gaussian predictive-coding kernel; units are latent-state units and nats of free energy.",
        "roadmap_risk.png": "Source: tasks.yaml roadmap, active task surfaces and generated live project metrics.",
        "scholarship_coverage.png": "Source: bibliography and scholarship source-role matrix.",
        "scholarship_source_health.png": "Source: scholarship source-health validator outputs over locators, roles and checks.",
        "scientific_evidence_matrix.png": "Source: manuscript claim-support anchors and YAML support rows.",
        "skill_neighborhood_paths.png": "Source: longest-path diagnostics; x marks depth checkpoints.",
        "validation_intent_mismatch_matrix.png": "Source: render configuration and validation-gate intent; cells are bound/gap classes.",
        "validation_surface_matrix.png": "Source: validator/test-file presence, release-inventory bindings and live generated counts.",
        "visual_evidence_contract_ladder.png": "Source: live curriculum graph and generated figure-registry contract metadata.",
        "vfe_efe_skilltree_bridge.png": "Source: graph rows, learn routes and quiz routes for VFE/EFE-adjacent SkillTree subjects.",
    }
    mobile_notes = {
        "assessment_depth_matrix.png": "Open the full-size image to read the PASS/REVIEW audit columns.",
        "curriculum_dag.png": "Use the full-size image for direct stratum labels; local path figures carry zoomed diagnostics.",
        "curriculum_stratum_balance.png": "Open the full preview when raw-count bars dominate the card thumbnail.",
        "dependency_strata_flow.png": "Horizontal scrolling preserves row/column totals and the lower-triangle note.",
        "validation_intent_mismatch_matrix.png": "Open the full preview to read the mismatch-class notes on the right panel.",
        "visual_evidence_contract_ladder.png": "Read the six numbered rungs sequentially; the dashboard detail card exposes the same contract fields.",
        "vfe_efe_skilltree_bridge.png": "This dense bridge should be read through the full-size image or PDF page.",
    }
    qa_roles = {
        "assessment_depth_matrix.png": "Checks that every exported stratum satisfies the quiz question floor.",
        "curriculum_dag.png": "Verifies that the exported DAG remains acyclic, connected and ordered by stratum/depth.",
        "curriculum_stratum_balance.png": "Separates expansion volume from per-unit imbalance signals.",
        "dependency_strata_flow.png": "Surfaces same-stratum, forward and forbidden backward dependency flow in one audit view.",
        "efe_decomposition.png": "Bounds the sample/commit preference claim to the plotted precision regime.",
        "free_energy_descent.png": "Confirms that the plotted VFE values come from registered kernel claims.",
        "kernel_sensitivity_profiles.png": "Shows kernel parameter boundaries before claims appear in prose.",
        "validation_intent_mismatch_matrix.png": "Documents which stale-output classes release validation is designed to reject.",
        "validation_surface_matrix.png": "Makes validator coverage auditable across manuscript, dashboard and release-inventory surfaces.",
        "visual_evidence_contract_ladder.png": "Confirms visual-evidence skills, registry metadata, manuscript references and dashboard exposure share one contract.",
        "vfe_efe_skilltree_bridge.png": "Confirms supplement subjects have concrete route and quiz handoffs.",
    }
    questions = {
        "assessment_depth_matrix.png": "Do all exported skills carry enough failable assessment questions for quiz-gated completion?",
        "curriculum_dag.png": "Does the generated curriculum remain connected, acyclic, rooted in foundations and ordered by prerequisite depth?",
        "curriculum_stratum_balance.png": "Is curriculum expansion distributed across strata without hiding per-subject or per-skill load?",
        "dependency_strata_flow.png": "Do prerequisite edges move within or forward through strata while the backward-dependency zone stays empty?",
        "efe_decomposition.png": "Which policy wins in the sample/commit toy task, and where does that preference switch with sensor precision?",
        "free_energy_descent.png": "Where does the variational free-energy bound become tight for the noisy-sensor example?",
        "graph_bottlenecks.png": "Which high-fan-out prerequisite skills would affect the most downstream material if their explanations drift?",
        "kernel_sensitivity_profiles.png": "Which toy-kernel conclusions are stable, and which depend on base rate, belief or precision settings?",
        "open_science_source_map.png": "Which open-science learning sources are cited, linked into course material, and bounded as pinned external pointers?",
        "roadmap_risk.png": "Which roadmap work remains open, and is it externally blocked or waiting on git authorization?",
        "scholarship_coverage.png": "Do cited sources cover the manuscript lanes and sections they are supposed to support?",
        "scholarship_source_health.png": "Are scholarship source locators and roles locally healthy, and was online reachability actually checked?",
        "scientific_evidence_matrix.png": "Which evidence classes support each manuscript claim type?",
        "semantic_prerequisite_coverage.png": "Are skills assessed on load-bearing concepts only after those concepts are reachable through prerequisites?",
        "skill_neighborhood_paths.png": "Can a reader inspect one representative long dependency path without decoding the full dense DAG?",
        "validation_intent_mismatch_matrix.png": "Which concrete stale-artifact mismatch classes are validators designed to catch?",
        "validation_surface_matrix.png": "Which generated, manuscript, dashboard, release and SkillTree surfaces are bound by real gates?",
        "visual_evidence_contract_ladder.png": "How does Active Skillference teach visual evidence from chart question to negative-control validation?",
        "vfe_efe_skilltree_bridge.png": "Do the VFE/EFE supplement figures connect to real SkillTree subjects, learn routes and quiz routes?",
    }
    data_grains = {
        "assessment_depth_matrix.png": "One stratum row per assessment audit group, with skill counts, minimum question counts, floor violations and question density.",
        "curriculum_dag.png": "One node per authored Skill and one edge per prerequisite relation from the live CurriculumGraph.",
        "curriculum_stratum_balance.png": "One pedagogical stratum row across raw skill, subject, assessment and prerequisite-edge counts plus normalized ratios.",
        "dependency_strata_flow.png": "One matrix cell per prerequisite-stratum to dependent-stratum pair, with row and column totals from exported edges.",
        "efe_decomposition.png": "One policy-term bar per sample/commit policy plus one precision-sweep line per policy from the toy EFE kernel.",
        "free_energy_descent.png": "One belief-grid point per noisy-sensor VFE value, with registered posterior and evidence reference claims.",
        "graph_bottlenecks.png": "One skill id/name row per top-8 high-fanout prerequisite, ranked by downstream dependent count from the live graph.",
        "kernel_sensitivity_profiles.png": "One deterministic sweep row per base-rate, belief or sensor-precision setting in the registered kernel examples.",
        "open_science_source_map.png": "One course-material source row per pinned external source plus cited non-course Institute support rows, with generated pointer and skill counts.",
        "roadmap_risk.png": "tasks.yaml task records aggregated by status, surface and release class, plus live metric bars.",
        "scholarship_coverage.png": "One scholarship source row per source-matrix key and one citation-lane count per manuscript section.",
        "scholarship_source_health.png": "One source-health audit summary over all source-matrix rows, issue classes and optional online-check mode.",
        "scientific_evidence_matrix.png": "One manuscript claim-support row per claim anchor, grouped by claim type and evidence class.",
        "semantic_prerequisite_coverage.png": "One concept row per semantic-prerequisite gate concept, with reachable-skill and assessed-skill counts.",
        "skill_neighborhood_paths.png": "One selected longest-path sequence of skill ids, with route callouts and a checkpoint ledger for endpoints and stratum transitions.",
        "validation_intent_mismatch_matrix.png": "One false-certification class row per stale-output scenario and one gate-family column per catching surface.",
        "validation_surface_matrix.png": "One validator-test binding row per artifact or release-documentation surface, one column per release gate family, plus live generated count bars.",
        "visual_evidence_contract_ladder.png": "One ordered ladder rung per visual-evidence review skill and contract stage.",
        "vfe_efe_skilltree_bridge.png": "One VFE/EFE-adjacent SkillTree subject row, including skill counts, edge counts, depth range and route fragments.",
    }
    static_reads = {
        "assessment_depth_matrix.png": "The static table/bar view keeps floor status, minimum question counts and below-floor counts visible on the PDF page.",
        "curriculum_dag.png": "The static DAG supports a structural overview read; local path and bottleneck figures carry detailed diagnosis.",
        "curriculum_stratum_balance.png": "The static three-panel layout separates raw scale from normalized load so imbalance claims can be checked without interaction.",
        "dependency_strata_flow.png": "The static matrix preserves same-stratum, forward and forbidden backward zones with totals and cell labels.",
        "efe_decomposition.png": "The static two-panel view preserves both the reference decomposition and the precision-switch boundary.",
        "free_energy_descent.png": "The static curve keeps the posterior, uniform belief and evidence-bound annotations visible with nats units.",
        "graph_bottlenecks.png": "The static top-8 ranking keeps skill ids, names, fan-out counts, depth and stratum chips visible.",
        "kernel_sensitivity_profiles.png": "The static small multiples keep the base-rate, VFE and EFE sensitivity boundaries side by side.",
        "open_science_source_map.png": "The static ledger keeps source names, source-type badges, KB pointer counts, locators and role snippets visible without hover.",
        "roadmap_risk.png": "The static panels keep task status, blocker class, surface totals and live metrics visible together.",
        "scholarship_coverage.png": "The static bar-plus-heatmap view keeps lane counts and section placement visible in one release snapshot.",
        "scholarship_source_health.png": "The static status ledger keeps local issue state and online-check mode visibly separate.",
        "scientific_evidence_matrix.png": "The static heatmap keeps claim types, evidence classes and side totals visible for support review.",
        "semantic_prerequisite_coverage.png": "The static lollipop view keeps assessed/reachable ratios and the zero-violation verdict visible per concept.",
        "skill_neighborhood_paths.png": "The static path view keeps start, stratum-transition and endpoint checkpoints readable through the ledger rather than angled micro-labels.",
        "validation_intent_mismatch_matrix.png": "The static matrix preserves mismatch-class names and catching gate families without relying on tooltips.",
        "validation_surface_matrix.png": "The static matrix keeps bound/n/a cell text, row totals, column totals and evidence-count bars visible.",
        "visual_evidence_contract_ladder.png": "The static ladder preserves all six stages, exact skill identifiers and the fail-closed QA endpoint.",
        "vfe_efe_skilltree_bridge.png": "The static table-card bridge keeps subject ids, counts, depth ranges, learn routes and quiz routes visible.",
    }
    mobile_reads = {
        "assessment_depth_matrix.png": "On narrow screens, use the full-size image to read audit columns while the card summary still exposes the floor-pass question.",
        "curriculum_dag.png": "On narrow screens, treat the card as an overview and use path/bottleneck figures for readable local structure.",
        "curriculum_stratum_balance.png": "On narrow screens, the three panels read left-to-right in the full-size image with direct stratum labels.",
        "dependency_strata_flow.png": "On narrow screens, row and column totals remain the primary read in the full-size image.",
        "efe_decomposition.png": "On narrow screens, the grouped bars and switch line should be read as two adjacent panels in the full-size image.",
        "free_energy_descent.png": "On narrow screens, the posterior and evidence reference annotations remain visible in the full-size image.",
        "graph_bottlenecks.png": "On narrow screens, the ranked row labels and stratum chips are preserved in the dashboard full-size image.",
        "kernel_sensitivity_profiles.png": "On narrow screens, read the three sensitivity panels sequentially in the full-size image.",
        "open_science_source_map.png": "On narrow screens, read the count cards first, then the ledger rows; source names and source-type badges remain visible before role snippets.",
        "roadmap_risk.png": "On narrow screens, read the status, blocker-surface and live-metric panels sequentially in the full-size image.",
        "scholarship_coverage.png": "On narrow screens, use the full-size image to inspect lane labels before section heatmap cells.",
        "scholarship_source_health.png": "On narrow screens, the status cards read before the local/online/release-boundary ledger rows.",
        "scientific_evidence_matrix.png": "On narrow screens, claim-type totals remain visible while detailed cells require the full-size image.",
        "semantic_prerequisite_coverage.png": "On narrow screens, direct assessed/reachable labels preserve the concept-gate read in the full-size image.",
        "skill_neighborhood_paths.png": "On narrow screens, read the checkpoint ledger first and use the line only for ordering context.",
        "validation_intent_mismatch_matrix.png": "On narrow screens, mismatch classes remain readable in the full-size image with gate columns as context.",
        "validation_surface_matrix.png": "On narrow screens, row totals and cell text preserve gate coverage in the full-size image.",
        "visual_evidence_contract_ladder.png": "On narrow screens, read the six numbered contract stages from question to negative control.",
        "vfe_efe_skilltree_bridge.png": "On narrow screens, use the full-size image because the route columns are intentionally dense.",
    }
    failure_modes = {
        "assessment_depth_matrix.png": "Fails to certify quiz depth if any stratum hides below-floor assessment counts.",
        "curriculum_dag.png": "Fails to certify curriculum structure if roots, cycles, disconnections or depth order drift are hidden by density.",
        "curriculum_stratum_balance.png": "Fails to certify expansion quality if raw growth hides subject, assessment or edge-load imbalance.",
        "dependency_strata_flow.png": "Fails to certify learning-path order if backward dependencies appear outside the empty safety zone.",
        "efe_decomposition.png": "Fails to certify policy claims if the precision regime or preference set is omitted.",
        "free_energy_descent.png": "Fails to certify VFE claims if plotted annotations drift from registered kernel values.",
        "graph_bottlenecks.png": "Fails to certify maintenance risk if high-fanout prerequisites are not ranked and directly labeled.",
        "kernel_sensitivity_profiles.png": "Fails to certify kernel interpretation if sensitivity boundaries are mistaken for empirical statistics.",
        "open_science_source_map.png": "Fails to certify open-science learning support if cognitive KB pointers or pinned course-material links disappear from the generated material index.",
        "roadmap_risk.png": "Fails to certify release readiness if blocked work and git-authorization hygiene collapse into one status.",
        "scholarship_coverage.png": "Fails to certify scholarship balance if bibliography size hides lane or section placement gaps.",
        "scholarship_source_health.png": "Fails to certify source health if offline metadata and online reachability are conflated.",
        "scientific_evidence_matrix.png": "Fails to certify manuscript evidence if claim types lack explicit support classes.",
        "semantic_prerequisite_coverage.png": "Fails to certify assessment ordering if any assessed concept is unreachable through prerequisites.",
        "skill_neighborhood_paths.png": "Fails to certify local dependency readability if the dense DAG is the only navigable dependency view.",
        "validation_intent_mismatch_matrix.png": "Fails to certify validator intent if stale-output classes are not named.",
        "validation_surface_matrix.png": "Fails to certify artifact validation if bound/n/a surfaces are not backed by real gate files.",
        "visual_evidence_contract_ladder.png": "Fails to certify visual-evidence teaching if any contract stage lacks a live curriculum skill.",
        "vfe_efe_skilltree_bridge.png": "Fails to certify supplement integration if math figures lack concrete SkillTree subject and route handoffs.",
    }
    for filename, chart_family in chart_families.items():
        overrides.setdefault(filename, {})["chart_family"] = chart_family
    for filename, subtitle in subtitles.items():
        overrides.setdefault(filename, {})["subtitle"] = subtitle
    for filename, mobile_note in mobile_notes.items():
        overrides.setdefault(filename, {})["mobile_note"] = mobile_note
    for filename, qa_role in qa_roles.items():
        overrides.setdefault(filename, {})["qa_role"] = qa_role
    for filename, question in questions.items():
        overrides.setdefault(filename, {})["question"] = question
    for filename, data_grain in data_grains.items():
        overrides.setdefault(filename, {})["data_grain"] = data_grain
    for filename, static_read in static_reads.items():
        overrides.setdefault(filename, {})["static_read"] = static_read
    for filename, mobile_read in mobile_reads.items():
        overrides.setdefault(filename, {})["mobile_read"] = mobile_read
    for filename, failure_mode in failure_modes.items():
        overrides.setdefault(filename, {})["failure_mode"] = failure_mode
    for entry in registry:
        semantic = dict(generic)
        semantic.update(overrides.get(str(entry.get("filename", "")), {}))
        entry.update(semantic)
        attach_chart_contract(entry)
