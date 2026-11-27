# Methods: Evidence Roles, Curriculum Graph, and Stratum Design {#sec:methodology-scholarship-curriculum-strata}

## Source-role matrix for citation coverage and source health

<!-- claim-support:method_scholarship_matrix -->
The manuscript uses a second, non-numeric integrity gate for citations. The static
`data/scholarship_sources.yaml` file maps each cited BibTeX key to a scholarship lane,
source kind, locator, and support role. `src/scholarship/coverage.py` parses the authored
manuscript sections, validates those keys against `manuscript/references.bib`, and
rejects any cited key that lacks a matrix entry or authoritative locator. It also rejects
stale source-matrix rows and uncited BibTeX entries, because those orphans would otherwise
let the coverage artifact imply support that no manuscript sentence actually uses. The
resulting JSON and figure are generated artifacts, not hand-maintained summaries.
The source-health check adds a second layer over this matrix: DOI and URL locators must
be syntactically authoritative, documentation/software rows must point to URLs, and each
role must explain how the source supports the manuscript rather than merely naming the
source.

This gate does not decide whether a paper is true. It prevents weaker failure modes that
ordinary citation checks miss: an undefined BibTeX key, a citation with no stated role, a
new source absent from the coverage matrix, or a source lane that disappears from the
manuscript without anyone noticing. The scholarship figure is therefore an audit view over
the current manuscript, not a bibliography inventory.

The matrix is also a situation map for the paper's evidence boundary. Foundational and
historical sources explain vocabulary and lineage; Active-Inference sources define or
compare model formulations; critique and empirical-status sources calibrate generality
and application language; pedagogy and assessment sources motivate ordering and future
study design; platform and software sources establish delivery and implementation
context; and provenance, reproducibility, accessibility, and security sources describe
artifact obligations. A source can occupy more than one lane, but its role is declared at
the claim boundary rather than inferred from prestige, recency, or citation count.

## Curriculum graph model, DAG validation, and quality gates

### Pedagogical quality constraints

<!-- claim-support:method_curriculum_quality -->
`src/curriculum` defines typed `Stratum`, `Subject`, `Skill`, and `AssessmentQuestion`
records, with field names mirroring SkillTree so export is a thin map. The
`CurriculumGraph` validates structural invariants -- unique identifiers, no self-loops,
no dangling prerequisites, no cycles, and roots only in the two foundational strata --
and provides deterministic topological order, per-skill depth levels, and a reachability
check from foundations to applications. Cycle detection uses the standard three-color
depth-first-search pattern from graph algorithms [@cormen2022introduction].

Structural validity is necessary but not sufficient for learning quality, so the build
also runs `src/curriculum/quality.py`. That gate rejects shallow one-question skills,
missing tags, terse subject or skill descriptions, answer-position bias, and backward
prerequisites that would force later-stratum concepts into earlier learning paths. Such
cross-stratum references are retained as non-blocking related links rather than exported
as SkillTree dependencies. A semantic-prerequisite gate additionally rejects any skill
that is *assessed on* a load-bearing concept (KL divergence, Markov chains, the Laplace
approximation, the ELBO) without the concept's defining skill in its transitive
prerequisites, flagging pedagogical inversions while exempting forward references for
motivation; a non-empty-scan guard fails the build if any guarded concept stops appearing
in the live corpus, so the gate cannot silently become vacuous.

The newest hardening layer expands continuous dynamics,
state-space probability, rate-distortion information, continuous variational inference,
predictive-coding process theory, hierarchical active inference, reproducible simulation,
and applied evaluation dossiers. Those additions are grounded in filtering, information
bottleneck, Helmholtz-machine, and generalized-filtering references while remaining
pedagogical rather than production inference engines [@sarkka2013bayesian;
@tishby1999information; @dayan1995helmholtz; @friston2010generalised].

The same graph is educationally meaningful only in a narrower sense: it approximates a
knowledge-space style closure condition over authored skills, where later tasks should
not be treated as feasible before their prerequisites, but it does not infer an
individual learner's latent knowledge state [@doignon1985knowledge_spaces;
@falmagne2011learning_spaces].

## Stratum order as an inspectable historical and pedagogical design choice

<!-- claim-support:method_stratum_ordering -->
The eight-stratum ordering -- mathematics, probability, information theory, variational
methods, the Free Energy Principle, Active Inference, computation, and applications -- is
an authored design decision, not a unique decomposition of the domain. An
applications-first path or a thematic split between generative-model statics and
inference/action dynamics could serve different learners. This release chooses the
linear order because the graph can then enforce a simple local rule: concepts precede
the concepts that depend on them [@bloom1956taxonomy; @bloom1968learning_for_mastery;
@liang2018prerequisite]. Historical sources motivate the categories and expose older
problems of demonstration, perception, probability, and ordered instruction, but they do
not determine the graph edges or certify the selected order as historically inevitable
[@aristotle_posterior_analytics; @alhazen1989optics_direct_vision;
@quintilian95institutio_oratoria; @huygens1657ratiociniis].

Historical pedagogy sources support this as a bounded history of design concerns rather
than as an efficacy claim: Bacon emphasizes staged inquiry, Comenius ordered progression,
Locke habit and practice, and Rousseau developmental sequencing [@bacon1620novum_organum;
@comenius1657great_didactic; @locke1693education; @rousseau1762emile]. Knowledge-space and learning-space theory provide a formal
comparison for prerequisite-constrained mastery states, while curriculum-aware cognitive
diagnosis work shows that a stronger learner-model claim would require response data and
an explicit model of learner state [@doignon1985knowledge_spaces;
@falmagne2011learning_spaces; @fu2025curriculum_aware_gncd]. Hugo's Active Inference
account of teacher development, embodied cognition, and education-oriented Active
Inference work motivate keeping the order revisable and uncertainty-sensitive, but this
release does not evaluate teacher development, infer learner states, or implement an
adaptive diagnostic engine [@hugo2026teacher_development; @clark2016surfing;
@dipaolo2024school].

Microlearning and gamification sources motivate modular delivery while warning that
implementation context, satisfaction, and measured effectiveness can diverge
[@septiani2021gamified_microlearning; @monib2024microlearning_boundaries;
@rof2024microlearning_satisfaction]. Active-learning, epistemic-curiosity,
cognitive-engagement, retrieval-practice, and evidence-centered-assessment sources
therefore inform the design of interaction and quiz tasks; they do not substitute for
data from this curriculum or establish durable competence [@freeman2014activelearning;
@emin2026epistemic_curiosity_mind_wandering; @chi2014icap;
@roediger2006testenhanced; @mislevy2003ecd]. Constructive alignment, mastery learning,
formative assessment, and feedback provide the local rule that objectives, activities,
and quiz gates should be co-specified and used as revision checkpoints
[@biggs1996constructive_alignment; @bloom1968learning_for_mastery;
@black1998assessment; @shute2008formative_feedback]. The resulting ordering is a
parameter to inspect and revise, not a theoretical or empirically tested claim about how
the field must be structured.
