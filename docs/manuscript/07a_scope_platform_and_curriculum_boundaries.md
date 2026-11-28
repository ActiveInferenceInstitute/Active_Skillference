# Scope: Curriculum Platform, Runtime Ownership, and Non-Claims {#sec:scope-platform-curriculum-boundaries}

## Curriculum platform scope: not an inference engine or hosted LMS

<!-- claim-support:scope_platform_boundary -->
Active Skillference is curriculum-authoring and delivery infrastructure, not a new
inference engine. Its kernels are pedagogical, correctness-first reference
implementations chosen
for legibility and testability, not for the performance or breadth of production toolboxes
such as `pymdp` for discrete state spaces, concise discrete-time tutorial/code treatments
aligned with that ecosystem [@heins2022pymdp; @vanoostrum2025concise], or SPM/DEM for
continuous dynamic systems [@friston2007variational; @friston2008dem]. The contribution
described here is *how the curriculum is built and verified*: a validated prerequisite DAG
with content-provenance binding, exported into an existing micro-learning runtime. The
repository is not an intelligent tutor, a learner-state estimator, or a general-purpose
adaptive system.

<!-- claim-support:scope_curriculum_boundary -->
The curriculum is deliberately broad ({{skill_count}} skills across all eight strata) and
designed so that growth is a data operation: adding skills or worked examples extends the
catalog without changing the engine. Its new practice layer is still pedagogical rather
than clinical or operational advice: domain-fit, ethics, misuse, and evaluation skills
train learners to ask better modeling questions, not to deploy autonomous interventions
without local review. Out of scope for this release are hosting and authentication of a
production SkillTree deployment, learner analytics, and a textbook-length treatment of
every individual skill. The local dashboard narrows that boundary: it is enough to show
that the export can be inspected locally and, when a SkillTree runtime is available,
opened through subject and quiz routes; it is not a hosted LMS or analytics product.
