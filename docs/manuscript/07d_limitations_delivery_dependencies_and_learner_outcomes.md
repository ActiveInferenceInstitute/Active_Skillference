# Limitations and Planned Evaluation: Delivery Dependencies, Kernel Scope, and Learner Outcomes {#sec:limitations-delivery-dependencies-learner-outcomes}

## Delivery dependencies, fixed-kernel scope, and learner-outcome boundaries

### Delivery substrate and kernel scope

<!-- claim-support:limitations_delivery_and_scope -->
The local learner dashboard can be verified in artifact-only mode without Docker; live
progress, ranking, and quiz completion still require a SkillTree service. When that
service is available, the dashboard mounts the official learner display and separates
local lesson material from official subject and quiz handoffs, but it does not provide a
second source of learner truth. The REST contract is verified against a
`pytest-httpserver` mirror of SkillTree's endpoints, and the live seed is documented and
scripted.

The implemented kernels cover discrete pedagogical cases, reference
variational examples, and bounded predictive-coding or planning demonstrations; they do
not provide a continuous, scalable, robust, or deep predictive-coding inference engine.
Reactive message passing, RxInfer, coupled free energy, active predictive coding,
divide-and-conquer predictive coding, generalized filtering, generalized free energy,
hierarchical multi-step planning, and richer reinforcement-learning comparisons remain
cited roadmap context rather than hidden implementation claims
[@bagaev2023reactive_message_passing; @bagaev2023rxinfer;
@nelson2025coupled_free_energy; @rao2024active_predictive_coding; @sennesh2024dcpc;
@friston2008dem; @friston2010generalised; @parr2019generalised]. The RL comparison
matters because probabilistic-inference views of control overlap with, but are not
identical to, active-inference policy selection [@levine2018probabilistic].
Psychology-and-psychiatry Active Inference reviews likewise support cautious application
language rather than theory-level validation claims [@badcock2024psychology_psychiatry].
Finally, the platform's contribution is the verifiability and provenance of curriculum
content, not a measured claim about learning outcomes: it does not evaluate teaching
effectiveness, retention, or transfer, and no efficacy study is reported here.
Microlearning studies, epistemic-curiosity evidence, learning-analytics reviews, and
learning-analytics intervention meta-analyses motivate the proposed study design but do
not substitute for data from this curriculum, and learning analytics also introduces
privacy and data-protection obligations before progress exports can be treated as
evidence [@monib2024microlearning_boundaries; @rof2024microlearning_satisfaction;
@emin2026epistemic_curiosity_mind_wandering; @liu2025learning_analytics_intervention_meta;
@hernandezcampos2025_learning_analytics_outcomes; @liu2023_learning_analytics_privacy].
Whether this provenance discipline actually
improves how people learn the framework remains future work, outside the scope of what the
code, citations, and validators establish. The preregistered pilot design in
`experiment_plan.yaml` is therefore a setup artifact: it defines consent, privacy,
SkillTree progress-export, pre/post, delayed-retention, and analysis boundaries, and
follows design-based research framing for studying a curriculum artifact in context, but
it is not learner-outcome evidence until real data are collected and added to the
claim-support record [@designbasedresearchcollective2003; @barab2004design_based].
