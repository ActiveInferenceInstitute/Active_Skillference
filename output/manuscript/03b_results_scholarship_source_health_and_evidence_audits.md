# Results: Scholarship Coverage and Evidence-Status Audits {#sec:results-scholarship-source-health-evidence}

## Citation coverage, locator health, and evidence-class auditing

<!-- claim-support:results_scholarship_coverage -->
The manuscript's source coverage is also treated as a generated result. Every authored
citation is parsed from the section files, matched against `references.bib`, and mapped
through `data/scholarship_sources.yaml` into a source lane and support role before the
build writes figures. The current audit covers 188 cited sources; that
number is generated from the manuscript and source matrix, not maintained as a prose
claim. [@fig:scholarship_coverage] shows both sides of the contract: the left panel
compares cited sources with the matrixed source pool for each lane, while the right panel
shows which manuscript sections carry each lane. The audit is deliberately orthogonal to
the numeric claim registry: one gate protects computed quantities; the other protects the
scholarly support surface.

![Scholarship coverage audit generated from manuscript citations, BibTeX keys, and the
source-role matrix. The left panel compares cited versus matrixed sources by scholarship
lane; the right panel maps manuscript sections to citation lanes. This figure makes
support distribution inspectable: a large bibliography is not treated as sufficient unless
sources are cited in the sections and roles where they support specific claims.](../output/figures/scholarship_coverage.png){#fig:scholarship_coverage width=100%}

<!-- claim-support:results_open_science_sources -->
The open-science education layer is also explicit. Active Skillference cites the Active
Inference Institute's public education ecosystem, including the open-source course
infrastructure, the START curriculum-generation project, and the Institute website's
open-science educational mission [@activeinferenceinstitute2026courses;
@activeinferenceinstitute2026start; @activeinferenceinstitute2026home].
The generated local Learn material also links every exported skill to commit-pinned
external material pointers, including the Active Inference Institute cognitive knowledge
base [@activeinferenceinstitute2026cognitive]. [@fig:open_science_sources] shows both
surfaces together: cited public sources remain visible, and the course-material source
rows expose how the cognitive knowledge base enters the generated skill records.

![Active Inference Institute open-science learning sources across scholarship support
and generated course-material pointers. Summary cards report local material records,
external pointers, cognitive knowledge-base pointers, and topic-matched KB skills; ledger
rows distinguish the course repository, cognitive knowledge-base source, Institute
homepage, website repository, and START source with locator and role text. The website
repository is a community/resource-hub pointer rather than a course or knowledge-base
record. The figure records pinned links and cited support surfaces; it does not claim
endorsement, completeness, or copied ownership of the public education ecosystem.](../output/figures/open_science_source_map.png){#fig:open_science_sources width=88%}

<!-- claim-support:results_source_health -->
The source matrix is then checked a second way: source locators must be syntactically
specific, documentation entries must use URL locators, and each support role must be
substantive enough to explain why the source is present. [@fig:scholarship_source_health]
reports the resulting offline source-health audit and provides a place for optional
online DOI/URL reachability checks to surface when release review requires currentness
evidence.

![Scholarship source-health audit generated from locator syntax, lane assignment, and
support-role checks. Status cards separate matrixed source count, offline validation
issues, and online-check mode, while the ledger rows distinguish local metadata health
from optional network reachability. The figure separates two different claims: a source
can be present in the matrix and still require locator, role, or currentness repair before
release.](../output/figures/scholarship_source_health.png){#fig:scholarship_source_health width=88%}

<!-- claim-support:results_validation_surface -->
The validation surface is intentionally visible rather than left as a hidden CI detail.
[@fig:validation_surface_matrix] summarizes which gates bind generated JSON, negative
controls, manuscript text, dashboard artifacts, release documentation, and SkillTree
handoffs. Its count panel is rebuilt from the same graph, claim registry, scholarship
audit and roadmap state that produce the curriculum and manuscript variables. The result
is a falsifiable release claim: if a count, citation, figure, dashboard artifact, release
inventory row, or roadmap item drifts away from its generator, the validator fails before
the manuscript or SkillTree export can be presented as current.

![Validation-surface matrix for Active Skillference. Each cell is derived from the
on-disk presence of the validator or test file that binds that artifact surface: a cell
reads "bound" only when every file named in its binding exists, so deleting a gate flips
its cell to "n/a" rather than leaving a stale "bound" claim. Row and column labels state
bound-cell totals, and each cell carries text, so the figure remains readable without
heatmap color. The side panel reports live evidence counts for skills, subjects,
dependencies, assessment questions, claims, cited sources, and registered figures, read
directly from the graph, claim registry, scholarship audit, and figure inventory. The
interpretation boundary is important: a bound cell means a named validator file exists
for that artifact surface (not that the gate is guaranteed sound), while an unbound cell
marks a surface that is out of scope for that gate.](../output/figures/validation_surface_matrix.png){#fig:validation_surface_matrix width=100%}

[@fig:validation_intent_mismatch_matrix] makes the negative controls behind that release
view explicit. It separates missing registry rows, missing files, missing manuscript
labels, missing dashboard artifacts, missing roadmap metrics, and stale manifests so the
validation layer is judged by concrete false-certification classes rather than by the
presence of a polished figure alone.

![Validation-intent mismatch matrix for Active Skillference. Rows enumerate concrete
false-certification classes: a rendered PNG omitted from the registry, a registered
figure without a readable file, a registered label omitted from the manuscript, a
registered figure omitted from the dashboard artifact roster, a missing roadmap live
metric, and a stale generated manifest. Columns show whether the source-of-truth,
manuscript gate, or dashboard gate is expected to reject each mismatch before release.
The right panel records the planned registered-figure count and which optional audit
surfaces were enabled for the render.](../output/figures/validation_intent_mismatch_matrix.png){#fig:validation_intent_mismatch_matrix width=98%}

The same contract is now represented inside the curriculum rather than only enforced at
release time. The visual-evidence slice adds a prerequisite-gated authoring path for
question contracts, data grain, encoding strength, annotation boundaries, static/mobile
readability, and negative-control validation. [@fig:visual_evidence_contract_ladder]
shows that path as generated curriculum evidence: each rung names the live skill that
carries the review step, while the registry and dashboard expose the same structured
chart-contract fields. This is a deterministic artifact-integrity claim, not a claim
that the visual curriculum has been externally tested with learners.

![Visual-evidence contract ladder generated from the live curriculum graph and figure
registry metadata. Six numbered rungs move from question contract through data grain,
encoding strength, annotation boundary, static/mobile survival, and negative-control
validation. Each rung names the skill identifier that carries the review obligation and
reports whether the skill is registered in the graph. The figure documents the authoring
and validation lifecycle for visual evidence; it does not claim learner effectiveness or
external deployment performance.](../output/figures/visual_evidence_contract_ladder.png){#fig:visual_evidence_contract_ladder width=98%}

<!-- claim-support:results_scientific_evidence_matrix -->
The scientific-claim layer adds one more audit view. [@fig:scientific_evidence_matrix]
is generated from manuscript `claim-support` anchors and the support matrix in
`data/manuscript_claim_support.yaml`. Its rows separate computed, descriptive-count,
simulation, literature, scope-limit, delivery and visual claims; its columns show whether
each class is backed by claim tokens, manuscript variables, citations, figures,
validators or limitation markers. This is not a statistical result. It is a release
integrity check that prevents strong scientific wording from passing without a declared
evidence class.

![Scientific evidence matrix for manuscript claims generated from claim-support anchors
and data/manuscript_claim_support.yaml. Rows are claim-support types, columns are
evidence classes, cell counts show how many anchored claims use each evidence class, and
the side panel counts claims per type. The purpose is epistemic classification rather than
statistical inference: computed, descriptive, simulation, literature, scope-limit,
delivery, and visual claims are forced to declare the kind of support they actually
have.](../output/figures/scientific_evidence_matrix.png){#fig:scientific_evidence_matrix width=96%}

The platform evidence above is intentionally separated from the small mathematical
examples. Those examples are still central teaching artifacts, but their scientific
meaning depends on the supplement's model assumptions and regime boundaries.
