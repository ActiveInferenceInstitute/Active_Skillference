# Introduction: Why Active Inference Needs an Auditable Learning Path

## Problem: prerequisite opacity, numerical drift, and evidence-status confusion

### Historical lineage and model boundary

<!-- claim-support:intro_fep_lineage -->
The Free Energy Principle is often situated in a historically bounded perception-as-inference
context that includes Helmholtz's account of unconscious inference, Bayesian-brain accounts
of neural uncertainty, and tutorials that make prediction error and variational bounds
teachable [@helmholtz1867handbuch; @knill2004bayesian; @bogacz2017tutorial;
@sprevak2023predictive]. Its deeper background is selective rather than a single direct
descent: ancient accounts of demonstration and ordered instruction, medieval optical work,
early-modern method and probability, and eighteenth-century accounts of association and
education all expose related questions about evidence, perception, uncertainty, and sequence
[@aristotle_posterior_analytics; @alhazen1989optics_direct_vision;
@quintilian95institutio_oratoria; @bacon1620novum_organum;
@descartes1628rules_direction_mind; @huygens1657ratiociniis;
@newton1704opticks; @rousseau1762emile]. Bernoulli, de Moivre, Bayes, and Laplace then
anchor more specific histories of probability and inverse-probability reasoning, while
Berkeley, Hume, Condillac, Hartley, Locke, Comenius, and Kant provide distinct traditions
of perception, association, habit, experience, and structured cognition
[@bernoulli1713ars_conjectandi; @demoivre1718doctrine_chances;
@bayes1763doctrine_chances; @laplace1774inverse_probability;
@berkeley1709new_theory_vision; @hume1739treatise; @condillac1754sensations;
@hartley1749observations; @locke1690essay; @comenius1657great_didactic;
@kant1781critique_pure_reason]. These sources are historical context and design analogies,
not evidence that modern variational free energy, Bayesian brain models, or Active Inference
already existed in their period; the fuller selective history appears in
[@sec:related-work-aif-information-sources].

The modern FEP frames self-organizing systems in terms of variational free energy, with
review work clarifying both the principle's scope and the need to avoid oversimplified
readings [@friston2006free; @friston2010free; @friston2023simpler;
@zhang2024overview]. In the discrete formulations used here, Active Inference supplies
model-based rules for belief updating and policy evaluation: variational free energy is
used for current inference, while expected free energy evaluates policies under stated
preferences and observation models [@friston2017process; @dacosta2020synthesis;
@parr2022active; @pezzulo2024sentient_behavior]. The word *agent* therefore names a
modeled decision-making system; it does not by itself establish consciousness,
intelligence, autonomy, or empirical adequacy.

## Situation awareness: theory, model, software, and education are different objects

### Education and delivery boundary

<!-- claim-support:intro_situation_awareness -->
The field is easiest to misread when four layers are collapsed into one label. At the
theory layer, the FEP is a broad explanatory and mathematical framing whose scope,
generality, and distinctive empirical predictions remain matters of active debate
[@friston2023simpler; @aguilera2022particular; @gershman2019free; @hodson2024empirical]. At
the model layer, a discrete Active-Inference process theory specifies beliefs, likelihoods,
preferences, policies, and an inference or planning scheme; changing those assumptions
changes the model's behavior, even when authors use the same vocabulary
[@friston2017process; @dacosta2020synthesis; @parr2022active; @millidge2021whence]. A
software implementation then adds a third layer: libraries such as `pymdp` and this
project's kernels are executable realizations with different goals, tests, and coverage,
not interchangeable evidence for the theory or for biological adequacy
[@heins2022pymdp; @vanoostrum2025concise].

The education layer adds a fourth boundary. Active-learning and prepared-environment
proposals make the framework relevant to instruction, while knowledge-space and
curriculum-aware cognitive-diagnosis work describe stronger learner-model commitments
that require response data and an explicit account of learner state
[@dipaolo2024school; @doignon1985knowledge_spaces; @falmagne2011learning_spaces;
@fu2025curriculum_aware_gncd]. Learning analytics can support such future evaluation, but
its use also creates privacy, data-protection, validity, and human-oversight obligations
[@liu2023_learning_analytics_privacy; @sclater2015learning_analytics_code]. SkillTree is a delivery substrate with its own
runtime semantics; it does not convert a curriculum export into an intelligent tutor or
turn a model demonstration into learner-outcome evidence [@skilltree2026docs;
@skilltree2020nsa].

A modeled Active-Inference agent is therefore a formal decision-making object with
specified states, observations, preferences, and policies; it is not by itself
an intelligent system. An intelligent system would require a separate capability and
evaluation argument, while an adaptive learner-facing tutor would additionally require
learner-state data, intervention logic, and prospective outcome evidence. Active Skillference
occupies the intersection of these layers as a provenance-bound curriculum artifact: it
makes a selected model family representable, teachable, and inspectable without claiming to
settle the theory, personalize instruction, or measure learning.

<!-- claim-support:intro_prerequisite_opacity -->
That compact summary hides a long prerequisite chain. To interpret expected free energy,
a learner needs KL divergence; to interpret KL divergence, entropy and expectation; and
to work with those quantities, probability, logarithms, optimization, and the geometry of
distributions. A learner can encounter apex terms such as "expected free energy" or
"epistemic value" before the mathematical foundations that make them derivable. The
pedagogical risk is conceptual miscalibration: a learner may know the words before being
able to compute the quantities or distinguish mathematical identities from process-theory
commitments, empirical hypotheses, and philosophical scope claims. Active Inference
tutorials and expected-free-energy derivation reviews show why the formal sequence cannot
be replaced by slogans, while education-oriented and associative-learning Active Inference
work frames learning as structured exploration of prepared material, attention, and
prediction-error reduction rather than passive term recognition
[@smith2022tutorial; @millidge2021whence; @champion2026reframing; @dipaolo2024school;
@anokhin2024associative_active_inference].

<!-- claim-support:intro_provenance_problem -->
A second problem is quantitative integrity. Hand-maintained numerical examples can drift
from the equations they illustrate. Without an executable source of truth, a reader cannot
tell whether a displayed value was computed, rounded, copied, or invented. This is a
design risk that the platform addresses; it is not a prevalence claim about every
tutorial or textbook.

<!-- claim-support:intro_scholarship_drift -->
A third problem is scholarship drift. A manuscript can accumulate citations that are
syntactically valid but weakly connected to the claims they are supposed to support, while
newer reviews or critiques change the evidential status of a phrase without changing its
syntax. That matters here because technical critiques of FEP generality and recent
empirical-status reviews, psychology-and-psychiatry progress reviews, and
distinctive-prediction critiques belong in the evidential context
[@aguilera2022particular; @aguilera2023confederation; @hodson2024empirical;
@badcock2024psychology_psychiatry; @gershman2019free]. This project treats the
bibliography as part of the build contract: every cited source is mapped to a support lane
and role, then checked before figures or learner artifacts are emitted.

## Approach: provenance-bound prerequisites delivered through SkillTree

<!-- claim-support:intro_graph_approach -->
Active Skillference addresses the three failure modes with one construction: a validated
directed acyclic graph whose nodes are atomic *skills* and whose edges are explicit
prerequisites. A skill is reachable only after the graph resolves the dependencies that
precede it. The graph spans {{strata_count}} strata from mathematical foundations to
applications and is checked to be acyclic, connected from foundations to applications,
and free of dangling prerequisites. This follows the basic premise of
prerequisite-sensitive curriculum design: ordering is part of the learning object
[@bloom1956taxonomy; @liang2018prerequisite]. The result is also interpretable through
knowledge-space and learning-space theory, but only as an authored closure condition over
course content; this release does not infer an individual's knowledge state or implement
an adaptive diagnostic learning-space engine [@doignon1985knowledge_spaces;
@falmagne2011learning_spaces].

<!-- claim-support:intro_evaluation_questions -->
The evaluation is correspondingly bounded by four questions. First, does the curriculum
graph satisfy its declared structural and assessment invariants? Second, can quantitative
examples be regenerated from tested kernels without unbacked or hand-entered result values?
Third, can citation roles, manuscript claims, figures, and generated artifacts be audited
as one evidence surface? Fourth, does the export preserve SkillTree's ownership of
learning paths, quizzes, progress, and scoring? These questions evaluate the artifact and
its delivery contract; they do not test whether the curriculum is optimal, whether an
Active-Inference model is empirically true, or whether learners improve.

<!-- claim-support:intro_claim_tokens -->
Every quantitative claim in a skill's content is produced by a tested computational kernel
and inserted through a `{{claim:NAME}}` token. The platform refuses to publish a skill
whose claims are not backed by code, and a linter flags any bare result number that slips
into prose outside a claim token or LaTeX math. Thus the worked example that teaches
entropy shows {{claim:entropy_fair_coin}} for a fair coin and {{claim:surprise_rare_event}}
for a one-in-a-hundred event because the kernel computed those values.

<!-- claim-support:intro_skilltree_delivery -->
Finally, the curriculum is built for delivery. It targets **SkillTree**, an open-source
training and gamification platform whose public documentation describes Project -> Subject
-> Skill composition, learning paths, and quiz-based knowledge checks
[@skilltree2020nsa; @skilltree2026docs; @skilltree2026github; @nsa2026opensource]. Active
Skillference maps subjects, skills, prerequisite learning paths, and quizzes onto that
data model so the exported artifact can be inspected and, when the service is available,
handed to a real progress-tracking environment. The citation is a platform-provenance
claim: it identifies the SkillTree substrate and its government open-source origin, not an
endorsement of this curriculum or a security assurance for any deployment.

The delivery layer also belongs to a wider community and open-science setting. The Active
Inference Institute's public website repository describes a static resource hub with
audience-specific pathways for newcomers, learners, researchers, developers, contributors,
partners, and supporters; public repositories and learning resources; and an explicit
boundary for sanitizing and verifying public projections [@activeinferenceinstitute2026website].
Active Skillference contributes one interoperable piece to that ecosystem: a
provenance-bound curriculum and SkillTree delivery contract that makes formal examples,
source roles, prerequisites, and release checks inspectable. This is a contribution to
community-facing educational infrastructure, not a claim that the project represents the
Institute, speaks for its contributors, or replaces its broader open-science programs.

These design choices turn the paper's contribution from a list of topics into a set of
auditable contracts. Each contribution below is either a checked structure, a provenance
gate, a source-role audit, or a delivery path into the existing SkillTree runtime.

The contribution map is therefore tied to six evidence classes. **Structural evidence**
covers graph, prerequisite, assessment, and artifact invariants. **Computed evidence**
covers values regenerated by tested kernels and resolved claim tokens. **Simulation
evidence** covers fixed-input demonstrations whose behavior is conditional on an explicit
model and parameter regime. **Literature evidence** covers historical lineage, formal
definitions, pedagogical rationale, platform provenance, and critiques, each assigned a
source role. **Delivery evidence** covers export, REST-contract, dashboard, and publication
surfaces. **Scope-limit evidence** records what the validators and sources cannot establish:
biological adequacy, learner-state inference, personalization, efficacy, retention, or
transfer. No evidence class is used as a substitute for another.

## Contributions: graph validation, provenance binding, scholarship audit, and delivery

1. **Structural evidence:** a typed, validated **prerequisite-DAG engine** for curriculum
   design, including cycle
   detection, topological ordering, depth levels, and connectivity checks.
2. **Computed evidence:** a **content-provenance binding** mechanism that ties every
   learner-facing number to a
   tested kernel and fails the build otherwise.
3. **Curriculum representation:** an implemented **Active Inference curriculum** --
   {{skill_count}} skills across all
   {{strata_count}} strata -- authored against that engine.
4. **Delivery evidence:** a **SkillTree exporter and seeder** that turns the curriculum into
   an importable,
   gamified training profile, with live availability treated as an external dependency.
5. **Literature evidence:** a **scholarship coverage audit** that maps manuscript citations
   to source roles and
   generates a reproducible coverage artifact.
6. **Scope-limit evidence:** an explicit boundary between formal model demonstrations,
   implementation checks, delivery checks, and future learner-outcome evaluation.
