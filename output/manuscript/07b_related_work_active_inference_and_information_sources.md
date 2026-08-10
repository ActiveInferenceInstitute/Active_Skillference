# Related Work: Historical Foundations, Active Inference Evidence Status, and Information Sources {#sec:related-work-aif-information-sources}

## Active Inference and FEP lineage: historical context and curriculum scope

### Formal lineage and model commitments

<!-- claim-support:related_fep_lineage -->
The FEP is commonly situated in a perception-as-inference lineage that includes Helmholtz,
Bayesian-brain accounts of uncertainty, and tutorial treatments that translate the
mathematics into worked learning sequences [@helmholtz1867handbuch; @knill2004bayesian;
@bogacz2017tutorial; @sprevak2023predictive]. Its modern variational formulation is
developed in Friston's early and review papers [@friston2006free; @friston2010free], and
recent overview work usefully maps the breadth of related research without removing the
need for local modeling commitments [@friston2023simpler; @zhang2024overview].
Mathematical reviews and textbooks situate the principle as a variational bound on
surprise and a process theory for perception, action, and learning [@buckley2017free;
@parr2022active; @smith2022tutorial; @pezzulo2024sentient_behavior]. Associative-learning
work makes attention, prediction-error, blocking, and surprise phenomena explicit inside
an Active Inference account, which is useful pedagogical context but not direct evidence
for this curriculum's outcomes [@anokhin2024associative_active_inference]. The discrete
POMDP formulation with $A$, $B$, $C$, and $D$ matrices is the direct basis for the kernels
here [@friston2017process; @dacosta2020synthesis], while epistemic value and curiosity are
treated by the expected-free-energy literature [@friston2015epistemic;
@friston2017curiosity; @millidge2021whence; @sajid2021demystified;
@champion2026reframing]. Recent variational-inference and
message-passing treatments make those formulation choices explicit by separating
epistemic-prior, entropy-correction, and planning-correction assumptions rather than
treating EFE as one unqualified objective [@nuijten2026what_type_inference;
@nuijten2026efe_planning_vi; @nuijten2025message_passing_efe].
The planning-frontier argument therefore leans on those EFE planning and message-passing
papers rather than on informal Lazy Dynamics talk material, because the manuscript needs
source-backed claims about objectives, factorization, and assumptions rather than a weak
conference-talk framing.

## Ancient, medieval, and early-modern foundations of inference, perception, and sequenced learning

<!-- claim-support:related_pre1800_foundations -->
This is a selective history of problems and design concerns, not a single-lineage account
of Active Inference. The sources below are used to motivate an inspectable prerequisite
order and to distinguish historical analogies from modern formal commitments. They do not
show that modern FEP, Bayesian inference, variational inference, adaptive tutoring, or
Active Inference existed before their later mathematical and computational formulations.
The historical source set spans demonstration, optics, method, probability, association,
education, and structured cognition [@aristotle_posterior_analytics;
@alhazen1989optics_direct_vision; @quintilian95institutio_oratoria;
@bacon1620novum_organum; @descartes1628rules_direction_mind;
@huygens1657ratiociniis; @bernoulli1713ars_conjectandi;
@demoivre1718doctrine_chances; @bayes1763doctrine_chances;
@laplace1774inverse_probability; @newton1704opticks;
@berkeley1709new_theory_vision; @locke1690essay; @hume1739treatise;
@hume1748enquiry; @hartley1749observations; @condillac1754sensations;
@comenius1657great_didactic; @locke1693education;
@rousseau1762emile; @kant1781critique_pure_reason].

### Demonstration, vision, and ordered instruction before modern probability

Ancient demonstration and explanation provide one early vocabulary for separating
reasons, evidence, and teachable order [@aristotle_posterior_analytics]. Quintilian's
*Institutio Oratoria* presents a staged rhetorical education involving elementary studies,
practice, revision, and progression through increasingly demanding forms of performance
[@quintilian95institutio_oratoria]. Its relevance here is historical: it shows that ordered
instruction and repeated practice were explicit design concerns, not that ancient rhetoric
implemented a learner model or adaptive tutor.

The medieval Arabic optical tradition adds a distinct perception strand. Ibn al-Haytham's
*Book of Optics*, represented here through a critical edition and translation, treats vision
through geometrical analysis, observation, and experimentally constrained accounts of
seeing [@alhazen1989optics_direct_vision]. That tradition belongs in the history of
perception and evidence, but it is not a predictive-coding theory, a Bayesian brain model,
or evidence for the biological adequacy of the kernels in this release.

### Early-modern method, probability, and experimental perception

Early-modern method sources connect ordered reasoning to observation without collapsing
their differences. Bacon's induction and experimental program, and Descartes's rules for
moving through clear intuitions, deductions, and probable conjectures, make method and
sequence explicit [@bacon1620novum_organum; @descartes1628rules_direction_mind]. Huygens's
work on expectation in games of chance provides an early published probability treatment,
while Bernoulli, de Moivre, Bayes, and Laplace extend the mathematical history of repeated
observation and inverse-probability reasoning [@huygens1657ratiociniis;
@bernoulli1713ars_conjectandi; @demoivre1718doctrine_chances;
@bayes1763doctrine_chances; @laplace1774inverse_probability]. These sources support a
history of calculation and inference under uncertainty, not a claim that their concepts
were already variational or computational in the modern sense.

Newton's *Opticks* adds a controlled-experiment and sensory-observation strand: optical
phenomena are varied, separated, and analyzed through explicit apparatus and mathematical
argument [@newton1704opticks]. Berkeley's account of vision similarly treats visual
perception as involving learned relations among sensory cues, but neither source should
be translated directly into modern generative models or neural predictive coding
[@berkeley1709new_theory_vision].

### Eighteenth-century association, education, and structured cognition

Eighteenth-century sources then widen the educational and psychological context. Locke,
Hume, Hartley, and Condillac discuss experience, association, habit, sensation, and
reflection in different philosophical registers [@locke1690essay; @hume1739treatise;
@hume1748enquiry; @hartley1749observations; @condillac1754sensations]. Comenius, Locke's
education writings, and Rousseau's *Émile* make staged progression, practice, motivation,
and learner-sensitive ordering visible as historical pedagogical concerns
[@comenius1657great_didactic; @locke1693education; @rousseau1762emile]. Kant provides a
different account of structured cognition and recognition [@kant1781critique_pure_reason].
Together these sources justify treating sequence, representation, and evidence status as
design questions; they do not establish modern cognitive science, personalized learning,
or empirical efficacy.

## Evidence-status critiques and empirical boundaries

<!-- claim-support:related_fep_evidence_status -->
The same literature also warns against collapsing every layer of the project into a
single grand claim. A variational identity, a process theory, a simulation recipe, and an
empirical neuroscience hypothesis have different evidential burdens. Technical critiques
of the FEP's particular-physics assumptions and subsequent Bayesian-mechanics framing
therefore belong in the curriculum as boundary-setting material, not as adversarial
footnotes [@aguilera2022particular; @aguilera2023confederation]. Recent empirical reviews
similarly motivate the platform's wording discipline: the curriculum can teach predictive
coding and Active Inference as formal frameworks while still marking where direct
empirical support is incomplete or domain-specific [@hodson2024empirical].
Psychology-and-psychiatry reviews add the same caution at the behavioral-modeling level:
Active Inference is productive for model fitting and explanation, but its theory-level
empirical adequacy still requires direct comparison with alternatives
[@badcock2024psychology_psychiatry]. Gershman's critique is useful here because it asks
what distinctive predictions the FEP contributes, which is exactly the kind of scope
boundary this manuscript treats as a claim-support obligation [@gershman2019free].
The perception literature supplies a complementary, narrower evidence map: Bayesian
vision and predictive-processing accounts connect generative hypotheses to perceptual
inference, while cortical-microcircuit, efficient-coding, perceptual-decision, and
neurophysiological reviews expose model-specific assumptions and unresolved empirical
questions [@yuille2006vision_bayesian; @clark2013predictive_brain;
@hohwy2013predictive_mind; @kersten2004object_perception;
@bastos2012canonical_microcircuits; @spratling2017predictive_algorithms;
@summerfield2014perceptual_decision; @wei2015efficient_bayesian_perception;
@millidge2021predictive_coding_review; @smith2020predictive_neurophysiology;
@seth2020predictive_consciousness]. These sources sharpen the perception-as-inference
lane without turning predictive processing into a settled theory of the brain or this
curriculum into a neuroscience intervention.

## Information, variational, filtering, and application sources

### Information and filtering sources

<!-- claim-support:related_variational_information_sources -->
The information-theoretic and variational strata follow standard treatments of entropy,
KL divergence, variational inference, graphical-model message passing, the ELBO/free
energy relationship, and rate-distortion or bottleneck views of task-relevant compression
[@shannon1948mathematical; @beal2003variational; @cover2006elements; @tishby1999information; @bishop2006pattern;
@jordan1999variational; @winn2005variational; @blei2017variational].
State-space filtering, continuous-time predictive coding, and neural message passing are
represented in the curriculum, with deeper executable worked examples left for later
releases; the relevant literature includes Bayesian filtering, Helmholtz machines,
hierarchical predictive coding, the graphical-brain account, DEM, generalized filtering,
and generalized free energy [@sarkka2013bayesian; @dayan1995helmholtz;
@rao1999predictive; @friston2008hierarchical; @friston2017graphical;
@friston2008dem; @friston2010generalised; @parr2019generalised;
@kataoka2026extended_predictive_coding; @tschantz2023hybrid_predictive_coding].
Probability, information, and Bayesian-analysis textbooks provide adjacent mathematical
foundations for these implementations and help distinguish a reusable inference method
from any one Active-Inference formulation [@mackay2003information_inference;
@jaynes2003probability_logic; @murphy2012probabilistic_ml;
@gelman2013bayesian_analysis; @murphy2022probabilistic_ml].

Broader applications to embodied cognition, biological self-organization, collective
behavior, action-oriented model learning, and institutional sensemaking motivate the
applications and practice strata [@clark2016surfing; @friston2013life;
@tschantz2020learning; @ramstead2018answering; @friston2019particular].
Application-facing work spans cognitive control, hierarchical motivation, computational
consciousness, clinical neuroscience, control-as-inference comparisons, robotics, and
model-based cognitive flexibility [@pezzulo2012cognitive_control;
@pezzulo2018hierarchical_active_inference; @vilas2022active_consciousness;
@smith2021clinical_predictive_coding; @pezzulo2023generating_meaning;
@watson2020active_control_inference; @millidge2020active_control_relationship;
@schwartenbeck2015addiction_active_bayes; @lanillos2021active_robotics_survey;
@catal2021robot_navigation_active_inference; @queisser2021robot_active_inference;
@sales2019cognitive_flexibility_active_inference]. These are application and comparison
surfaces, not evidence that the present discrete kernels scale to robotics, clinical
decision support, or human cognitive change.
Predictive-learning neuroimaging evidence strengthens the plausibility of predictive
learning as a representational mechanism, but it remains neural-task evidence rather than
evidence that this microlearning curriculum changes learner representations
[@greco2024predictive_learning_geometry].
Current frontier sources sharpen the roadmap boundary. Reactive message passing and
RxInfer show a software and algorithmic path for scalable Bayesian message passing;
coupled free energy points toward robust variational geometry; active predictive coding
and divide-and-conquer predictive coding extend the neural-inference and scalability
context. Those sources are cited as scope-extending scholarship, not as implemented
kernels, production-scale evidence, or learner-outcome evidence in this release
[@bagaev2023reactive_message_passing; @bagaev2023rxinfer;
@nelson2025coupled_free_energy; @rao2024active_predictive_coding; @sennesh2024dcpc].
Recent experimental work also grounds the FEP outside purely theoretical exposition
[@isomura2023experimental].
