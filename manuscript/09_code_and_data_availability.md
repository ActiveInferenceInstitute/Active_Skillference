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
with the v1.0.0 manuscript archived on Zenodo at
[doi.org/10.5281/zenodo.21865644](https://doi.org/10.5281/zenodo.21865644). The
identifier appears on the cover page, in the citation file, in the CodeMeta and Zenodo
records, and in the archived copy of this document, all naming the same deposit. That
agreement is enforced rather than assumed: a test cross-checks each surface against the
recorded deposit and fails on any divergence, which is what keeps a plausible but wrong
identifier out of a citation. Version-specific identifiers stay blank because no
versioned deposit beyond this one exists, and the same test holds them blank.

<!-- claim-support:availability_generated_artifacts -->
Generated outputs travel with the repository even though they are rebuildable, so a reader
can open the manuscript, the figures, the SkillTree export, and every audit record without
installing anything or running the pipeline. Committing them does not soften the
regenerability claim: running the kernels rebuilds the claim ledger, manuscript variables,
scholarship audits, figures, lesson records, and the export from source, and the freshness
validator fails if a committed artifact has drifted from what the current source produces.
Only build detritus is withheld, meaning renderer logs and intermediates that change on
every run and carry nothing a reader would read. The captured evidence described in
[@sec:results-skilltree-dashboard-front-matter] is different in kind rather than in
handling: a recording of a running system is not a function of project data and cannot be
rebuilt from a checkout at all, which is why it is stored beside a provenance record naming
the dashboard address, viewport, live counts, full-stack mode, capture timestamp, and a
digest per image. Every other image in this paper regenerates; those five are archived
precisely because they do not.
