# Methods Overview: From Mathematical Kernels to a Validated Learning Artifact

The platform is layered so that each concern is testable in isolation and composes
through fixed interfaces. The method therefore moves from numerical sources of truth, to
claim and citation gates, to the curriculum graph, and finally to the exported SkillTree
and publication surfaces that consume those artifacts.

The subsections below separate numerical provenance, scholarship coverage, curriculum
structure, and delivery integration so each evidential claim can be checked against its
own validator rather than blended into a single platform assertion.

## Evidence classes and construction boundary

<!-- claim-support:method_evidence_classes -->
The construction uses a deliberately plural evidence contract. Structural validators
check graph and artifact invariants; computational validators regenerate numerical claims;
fixed-input simulations illustrate model-specific behavior; scholarship validators check
citation resolution, source roles, and locator health; delivery checks inspect SkillTree
export and dashboard handoff surfaces; and scope-limit statements prevent any of those
checks from being read as learner-outcome or theory-validation evidence. This separation
is consistent with reproducible-science and FAIR reporting principles, but the local
implementation remains a repository-level artifact chain rather than a general scientific
provenance service [@munafo2017reproducible_science; @wilkinson2016fair].
