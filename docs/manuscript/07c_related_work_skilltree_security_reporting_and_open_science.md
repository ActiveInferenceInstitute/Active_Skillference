# Related Work: SkillTree Delivery, Security Posture, Reporting, and Open Science {#sec:related-work-skilltree-security-reporting-open-science}

## SkillTree delivery as prerequisite learning and gamified practice context

<!-- claim-support:related_skilltree_delivery -->
SkillTree supplies the delivery substrate: Project, Subject, Skill, learning-path
dependencies, quizzes, and report endpoints [@skilltree2020nsa; @skilltree2026docs;
@skilltree2026github]. Active Skillference uses those concepts directly rather than
inventing a new learning platform. The graph layer adds prerequisite validation and
connectivity checks because the learning object is the ordered dependency structure, not
only the text attached to each node [@bloom1956taxonomy; @bloom1968learning_for_mastery;
@liang2018prerequisite; @doignon1985knowledge_spaces; @falmagne2011learning_spaces].

Gamification is relevant but not itself the contribution; SkillTree provides the
gamified runtime, and the project contributes the verified content and graph
[@dicheva2015gamification]. Visual skill-tree and gamified microlearning sources provide
useful delivery precedent for making dependencies and progress inspectable, but they do not
constitute learner-outcome evidence for this export [@burau2022deciduous;
@septiani2021gamified_microlearning].
Constructive alignment and formative-assessment sources supply the education-facing
language for this design: objectives, activities, feedback, and quiz gates are treated as
aligned checkpoints, not as outcome evidence [@biggs1996constructive_alignment;
@bloom1968learning_for_mastery; @black1998assessment; @shute2008formative_feedback].

## SkillTree provenance, deployment security, and access-control boundaries

<!-- claim-support:related_skilltree_security_posture -->
SkillTree's origin matters for the delivery argument. NSA describes SkillTree as an
internally developed open-source training platform, and the public `skills-service`
repository and NSA open-source portal identify the service as public government-origin
software rather than a generic third-party widget [@skilltree2020nsa; @skilltree2026github;
@nsa2026opensource]. Active Skillference therefore treats SkillTree as a real delivery
substrate with explicit platform ownership boundaries: SkillTree owns learner progress,
quiz state, authentication, ranking and reporting semantics, while this project owns the
curriculum graph, provenance gates, manuscript evidence and exported SkillTree payload.

<!-- claim-support:related_national_security_boundary -->
That provenance raises the bar for deployment language. A national-security posture would
still require organization-specific threat modeling, zero-trust access decisions,
supply-chain provenance, software-development process, artifact signing, SBOM visibility,
and adversary-technique coverage beyond this educational repository [@nist2020zerotrust;
@nist2022ssdf; @slsa2026framework; @sigstore2026overview; @cisa2026sbom;
@mitre2026attack]. Active Skillference can support defensible training review because
claims, figures, source roles, dashboard artifacts and SkillTree handoff routes are
inspectable; it does not certify operator competence, harden a production deployment,
replace APT-aware threat modeling, or imply NSA approval of the curriculum.

## Reproducible reporting, accessible artifacts, and source-role auditing

<!-- claim-support:related_reproducible_reporting -->
The content-provenance binding is closest in spirit to literate programming and literate
statistical reporting: code and explanation are kept mutually inspectable, and R/knitr-
style workflows bind prose to executable analysis so reported numbers can be regenerated
[@knuth1984literate; @xie2015knitr]. Peng's reproducible-research argument is the
reporting boundary used here: when a claim is computational, readers should be able to
rerun the workflow that produced it [@peng2011reproducible; @sandve2013reproducible].
Scientific-computing practice adds the software-maintenance side of the same argument:
versioned code, automated checks, and tested workflows are part of the scholarly surface
when the artifact is executable [@wilson2014scientific_computing]. W3C PROV gives the
formal provenance vocabulary for entities, activities, agents, derivations, bundles, and
validity constraints, while reproducible-science sources keep the claim boundary tied to
transparent methods rather than trust language [@groth2013prov_overview;
@moreau2013prov_dm; @cheney2013prov_constraints; @munafo2017reproducible_science].
FAIR and transparency guidelines extend that boundary
from rerunnable computation to metadata and open-science claim discipline
[@wilkinson2016fair; @nosek2015top]. Active Skillference differs by keeping a central
claim registry, applying the same gate to curriculum content and manuscript prose, and
refusing export when any token is unbacked. The DAG engine uses standard graph algorithms
for cycle detection and topological ordering
[@cormen2022introduction]. Figures use an accessible categorical palette rather than a
single-hue theme [@wong2011color]. The figure-registry validator also treats alt text and
semantic caption metadata as reporting obligations, aligning the artifact layer with
ACM/SIGCHI, Section 508 and WCAG guidance that accessible figures and web content should
carry meaningful alternatives rather than empty labels [@acm2023accessiblefigures;
@section508alttext; @w3c2023wcag22].

<!-- claim-support:related_ip_license_boundary -->
Release metadata and license notices are treated as delivery evidence, not as scientific
or learner-efficacy support. Software citation principles, Citation File Format and
CodeMeta guide the citation and metadata surfaces [@smith2016softwarecitation;
@citationfileformat2026; @codemeta2026schema]. GitHub and Zenodo documentation bound the
repository and DOI workflow to an actual public target and deposit
[@github2026citingcontent; @zenodo2026github]. SPDX, OSI and REUSE license-notice
references support the MIT and third-party notice signposting
[@spdx2026mit; @opensourceinitiative2026mit; @reuse2024spec]. These references do not
provide legal advice, do not relicense third-party course materials or vendored browser
bundles, and do not turn a static review checkout into a production deployment.

<!-- claim-support:related_scholarship_audit -->
The scholarship audit extends that reproducible-reporting idea from numbers to source
coverage. Ordinary citation validators can show that `[@key]` resolves, but not that the
key has a stated role in the argument. The source matrix makes that role explicit and
keeps the bibliography aligned with the manuscript's actual lanes. The frontier gap
report adds a narrower check for newly emphasized source areas: a pedagogy, assessment,
formal provenance, workflow provenance, knowledge-space, cognitive-diagnosis,
message-passing, predictive-coding, design-based evaluation, open-science, security,
accessibility, reproducibility, or course-material source must be cited and tied to an
explicit claim-support class and, where needed, a boundary row before it can count as a
scholarship upgrade.

## Open-science education ecosystem, interoperability, and community handoff

<!-- claim-support:related_open_science_ecosystem -->
Active Skillference also sits inside a broader open-science educational ecosystem. The
Active Inference Institute publishes a public resource hub with community pathways,
verified public repositories, and a documented projection boundary; it also publishes
public course infrastructure, a START project for
tailored Active Inference research and training curricula, and an institute website that
frames education as part of an open-science mission [@activeinferenceinstitute2026courses;
@activeinferenceinstitute2026start; @activeinferenceinstitute2026home;
@activeinferenceinstitute2026website].

The cognitive
knowledge-base repository is treated as course-material provenance for generated Learn
pointers, not as copied prose or as an endorsement claim
[@activeinferenceinstitute2026cognitive]. This project does not replace those efforts; it
contributes a provenance-bound SkillTree export, quiz gate, and verifier suite that can
interoperate with public learning paths. Recent educational Active Inference scholarship
also motivates prepared learning environments and active exploration as topics for future
classroom evaluation, while this release limits itself to the inspectable curriculum and
delivery contract [@dipaolo2024school].
