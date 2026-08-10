# Code and Data Availability {#sec:code-and-data-availability}

<!-- claim-support:availability_artifact_scope -->
The artifact described here is a single repository containing the kernels, the curriculum
catalog, the SkillTree exporter, the learner dashboard, the manuscript sources, and every
validator named in [@sec:reproducibility]. Authored code and content are MIT licensed with
Daniel Ari Friedman as the copyright holder, recorded in `LICENSE` and mirrored in the
citation, CodeMeta, and Zenodo metadata files. Vendored runtime dependencies and their
separate notices are listed in `THIRD_PARTY_NOTICES.md`. External Active Inference
Institute course and knowledge-base material is referenced by repository, path, and commit
rather than copied, so upstream licensing stays with upstream.

<!-- claim-support:availability_public_target -->
The code is public at
[github.com/ActiveInferenceInstitute/Active_Skillference](https://github.com/ActiveInferenceInstitute/Active_Skillference),
released as v1.0.0 and archived on Zenodo at
[doi.org/10.5281/zenodo.21865644](https://doi.org/10.5281/zenodo.21865644). The
identifier appears on the cover page, in the citation file, in the CodeMeta and Zenodo
records, and in the archived copy of this document, all naming the same deposit. That
agreement is enforced rather than assumed: a test cross-checks each surface against the
recorded deposit and fails on any divergence, which is what keeps a plausible but wrong
identifier out of a citation. Version-specific identifiers stay blank because no
versioned deposit beyond this one exists, and the same test holds them blank.

<!-- claim-support:availability_generated_artifacts -->
Generated outputs are not committed, because they are rebuildable: running the kernels
regenerates the claim ledger, manuscript variables, scholarship audits, figures, lesson
records, and the SkillTree export from source. The one exception, described in
[@sec:results-skilltree-dashboard-front-matter], is the captured evidence. A recording of a
running system is not a function of project data and cannot be rebuilt from a checkout, so
those images are kept in the version-controlled tree rather than the generated one, alongside a provenance record that
names the dashboard address, viewport, live counts, full-stack mode, capture timestamp,
and a digest per image for the session that produced them. That record travels with the
repository, so it becomes checkable at the same moment the code does. Every other image in
this paper regenerates; those five are archived precisely because they do not.
