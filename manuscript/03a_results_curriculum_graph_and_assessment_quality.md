# Results: Curriculum Graph and Assessment Audits {#sec:results-curriculum-graph-assessment}

## Graph validity, prerequisite depth, and assessment-quality gates

<!-- claim-support:results_curriculum_graph -->
The assembled curriculum is a valid directed acyclic graph of **{{skill_count}} skills**
in **{{subject_count}} subjects** joined by **{{edge_count}} prerequisite edges**,
spanning all {{strata_count}} strata with a maximum prerequisite depth of {{max_depth}} and two
foundational roots (set theory and the probability axioms). Validation passes: no cycles,
no dangling prerequisites, and every applications skill is reachable from a foundational
root. [@fig:curriculum_dag] lays the graph out by stratum and depth, uses wrapped
stratum-count labels and root annotations, and reports the maximum-depth summary.

The learner-quality gate then checks whether that valid graph is also usable as a
micro-learning catalog. Each skill has at least {{failable_floor}} failable assessment items including
a transfer-oriented multiple-choice check. Answer position and answer length are then
audited per answer-count bucket, in every bucket carrying enough single-choice items to
read. Each option slot has to be correct at a rate inside a band around chance, between
$0.10$ and $0.45$ of the bucket, so no slot either dominates or sits unused. The length
check is two-sided: the rate at which the correct option is the strictly longest answer
and the rate at which it is the strictly shortest answer must both land between $0.12$
and $0.42$ of the bucket. Bounding only the long end would relocate the cue rather than
remove it, because an answer that is never the longest teaches a learner to pick the
shortest one. Multiple-choice correctness is kept from collapsing onto a template: no
option index sits in the correct set for more than $0.60$ of multiple-choice items, and
no single correct subset covers more than $0.30$ of them. Objective strings may repeat,
but only within a bound — at most four skills may share one objective before the gate
reports templated filler. No single name-normalized answer body is reused across more
than $0.12$ of skills, with the declared shared rubric exempted as described below.
Skill tags include both stratum and topic context, and backward cross-stratum references
are kept out of the exported prerequisite path.

The one deliberately shared instrument is disclosed rather than hidden. Each skill
carries bespoke domain assessment items; most skills additionally carry a shared
transfer-and-misuse rubric, a uniform metacognitive instrument applied across the
curriculum and marked as such. The answer-reuse gate exempts that declared rubric,
requires every skill to retain at least one bespoke item, and bounds every other
name-normalized answer body to at most $0.12$ of skills. The exemption is what makes
that bound readable rather than misleading: each per-family review rubric spans a whole
stratum-by-role family, a footprint above a tenth of the curriculum and therefore above
the bound the gate enforces on authored answers. We name the instrument and the
exemption instead of letting a shared rubric sit quietly under a threshold, and the
bespoke-item requirement keeps the rubric scaffolding rather than a substitute for
per-skill assessment.

These checks establish structural assessment discipline, not psychometric validity. They
show that quiz-gated completion is not thin, duplicated, or position-biased under the
local validators; they do not estimate item reliability, construct validity, learner
ability, retention, transfer, or differential item functioning.

The headline depth of {{max_depth}} is not a single conceptual chain. It is dominated by
the per-stratum mastery and open-science review ladders, which sequence skills for
completeness rather than by genuine conceptual prerequisite. Excluding only those
review and meta scaffold families and keeping every genuine concept family (mathematics
through applications, plus the dynamical, geometric, hierarchical, implementation and
cognitive-security families), the substantive concept chain a learner must climb is
{{core_max_depth}} deep; the difference is review and mastery sequencing, not conceptual
dependency. We report both so the headline number is not read as the depth of the
conceptual curriculum.

![The Active Inference curriculum as a prerequisite DAG generated from the current
curriculum graph after structural checks. Each point is one skill, color encodes the pedagogical stratum,
horizontal position follows the stratum order, vertical position follows longest
prerequisite depth, and gray segments encode exported learning-path dependencies. Wrapped
stratum chips report live skill totals, the two foundational roots are labeled, and the
inset reports the live skill, subject, edge, and maximum-depth counts. This figure is an
overview for structure and reachability; it does not by itself certify prose quality,
assessment quality, or scholarship support.](../output/figures/curriculum_dag.png){#fig:curriculum_dag width=100%}

<!-- claim-support:results_dependency_flow -->
The full DAG is the most faithful view, but it is intentionally dense: learners need to
see both the individual prerequisite chains and the curriculum's aggregate traffic
pattern. [@fig:dependency_strata_flow] adds that second view. Rows are prerequisite
strata, columns are dependent strata, and the right-hand bar gives the node count in each
stratum. Diagonal cells show within-stratum reinforcement; upper-triangular cells show
forward conceptual transitions. A populated lower-triangular cell would mean a backward
learning-path dependency, which the quality gate rejects before export.

![Prerequisite-edge flow across strata generated from every exported learning-path edge.
Rows are prerequisite strata, columns are dependent strata, cell labels count edges, and
the side bar reports how many skills live in each stratum. Diagonal cells show
within-stratum reinforcement, upper-triangular cells show forward conceptual transitions,
and a populated lower-triangular cell would expose a backward prerequisite that should be
rejected before export.](../output/figures/dependency_strata_flow.png){#fig:dependency_strata_flow width=95%}

<!-- claim-support:results_graph_diagnostics -->
The same graph also needs diagnostic views for authors. [@fig:graph_bottlenecks]
orders high-outdegree skills by how much downstream curriculum they unlock, so review can
focus on nodes where a weak explanation would create wide learner risk.
[@fig:skill_neighborhood_paths] complements that global view with a representative long
dependency path. The figure keeps the route line readable while a checkpoint ledger names
the start, stratum transitions, and endpoint, so a reader can inspect one concrete route
without zooming the full DAG or relying on angled micro-labels.

![Graph bottlenecks in the exported prerequisite network generated from downstream
dependent counts. Bars rank the top fan-out skills, y-axis labels pair skill ids with
readable names, hatching and stratum chips identify pedagogical layer, and annotations
report dependent count and prerequisite depth for each high-impact node. The figure is a
review-priority surface: it identifies where a weak explanation, stale citation, or thin
quiz would propagate to many later skills even though the graph remains valid.](../output/figures/graph_bottlenecks.png){#fig:graph_bottlenecks width=92%}

![Representative skill-neighborhood path generated from the longest-path diagnostic in
the current graph. The line orders skills by prerequisite depth, stratum bands and
vertical position encode pedagogical layer, and a checkpoint ledger names the start,
every stratum transition, and the endpoint. This view deliberately trades global
completeness for readability: it lets authors audit one concrete
foundation-to-application pathway without relying on the dense full-DAG overview or tiny
rotated labels.](../output/figures/skill_neighborhood_paths.png){#fig:skill_neighborhood_paths width=100%}

[@fig:semantic_prerequisite_coverage] audits the semantic-prerequisite gate, which checks
that no skill is assessed on one of the gate's tracked load-bearing concepts unless a
skill defining that concept sits in its transitive prerequisite closure. The gate reads
assessment text only, and it considers only definers at or before the using skill's own
stratum, so a forward reference to a later concept is not counted as a missing
prerequisite. For each concept the figure reports how many skills reach the defining skill through their
prerequisite closure and how many are assessed on the concept, so an inversion in which a
learner met a concept before they could have learned it would be visible rather than buried
in the dense graph.

![Semantic-prerequisite coverage generated from the live graph and the quality gate's
concept map. For each load-bearing concept the open marker and stem report skills whose
prerequisite closure reaches the concept's defining skill, while the filled marker and
direct label report the assessed subset inside that reachable set. The subtitle and badge
report the gate verdict so a passing curriculum shows zero skills tested on a concept they
could not yet have learned.](../output/figures/semantic_prerequisite_coverage.png){#fig:semantic_prerequisite_coverage width=92%}

<!-- claim-support:results_assessment_depth -->
The quiz surface is itself part of the curriculum result rather than a decorative add-on.
[@fig:assessment_depth] summarizes the assessment-depth invariant by stratum. Every skill
now carries the same {{failable_floor}}-question floor, so completion is not certified by a single
recognition item or by a thin two-question check.

![Quiz assessment depth by stratum generated from the skill assessment tuples. The bar panel counts
quiz-bearing skills per pedagogical stratum, and the accompanying audit table reports, per stratum,
the minimum questions per skill, below-floor counts, questions per skill, and a PASS/REVIEW verdict
against the configured {{failable_floor}}-question failable floor. The intended check is not average
quiz length but minimum learner friction: any below-floor mass would show that a skill can be
completed without the configured {{failable_floor}}-question floor.](../output/figures/assessment_depth_matrix.png){#fig:assessment_depth width=90%}

<!-- claim-support:results_stratum_balance -->
The latest expansion also needs a balance check. [@fig:stratum_balance] summarizes skills,
subjects, assessment questions and incoming prerequisite edges by stratum. This makes a
different false-certification path visible: the graph can be larger while still
overloading one pedagogical layer or leaving another underdeveloped.

![Curriculum stratum-balance audit generated from current graph statistics after structural checks. Three panels report the same underlying build:
the left panel shows skills and subjects per pedagogical stratum, the middle panel shows assessment-question
volume and incoming prerequisite edges, and the right panel shows companion per-unit (per-skill and
per-subject) normalized measures. Reading the panels together shows whether expansion is distributed across
the learning path or whether one layer is absorbing disproportionate topic, quiz, or dependency load. The
figure bounds the claim to catalog structure; it does not measure learner outcomes.](../output/figures/curriculum_stratum_balance.png){#fig:stratum_balance width=100%}

Having established the graph surface, the next result is source support. These audits ask
whether the manuscript's scholarly claims are connected to the roles its citations are
supposed to play.
