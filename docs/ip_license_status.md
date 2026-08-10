# IP And License Status

This page records the repository's current intellectual-property and license posture for
static public review. It is not legal advice and should be reviewed by qualified counsel
before any formal public release, institutional deployment, commercial use, or archival
deposit.

## Current Repository Declaration

The project owner has confirmed the following release-governance decisions for this
static public-review posture:

- MIT is the intended license for all authored repository code, manuscript/documentation,
  and generated artifacts.
- The current copyright holder line should remain `Daniel Ari Friedman`.
- The intended public repository target remains
  `ActiveInferenceInstitute/Active_Skillference`. Probed on 2026-08-09, that target now
  exists and is public but holds zero refs. It is reachable and unpublished: nothing from
  this project has been pushed, tagged, or deposited there, and no release date or DOI
  attaches to it. Existence of the repository is not publication of the code.
- A counsel-review checklist is required before any formal public release, DOI deposit,
  institutional deployment, commercial use, or production launch.

Active Skillference declares MIT for repository code and authored content in:

- `LICENSE`
- `CITATION.cff`
- `.zenodo.json`
- `codemeta.json`
- `manuscript/config.yaml`

The SPDX and OSI MIT texts are the reference boundary for this declaration. DOI, public
archive fields, renderer-facing repository links, and release-date metadata remain
intentionally blank or omitted until the confirmed public repository target holds published
content and a real release tag and deposit exist. The target's existence does not release
any of those fields.

## Third-Party Boundaries

- Vendored dashboard browser code is inventoried in `THIRD_PARTY_NOTICES.md`.
- SkillTree is attributed as an NSA-origin open-source runtime dependency, without
  endorsement or security certification.
- External Active Inference Institute course and knowledge-base materials are cited or
  linked through pinned source records. They are not copied into this repository and are
  not relicensed by this project.
- Scholarship citations support claims and scope boundaries; they do not transfer IP
  rights into this repository.

## Publication Boundary

The repository is suitable only for a static public-review posture after the dirty
worktree is intentionally committed or explicitly deferred and
`docs/release_readiness_inventory.md` is regenerated from the current checkout.

It is not ready for:

- DOI or Zenodo release claims.
- A public-repository claim for `ActiveInferenceInstitute/Active_Skillference`. The empty
  target may be named as the intended destination and nothing more.
- Learner-outcome or efficacy claims.
- Production deployment claims.
- Operational security, privacy, trademark, or access-control assurance.

## Counsel-Review Checklist

Before promoting beyond static public review, a qualified reviewer should confirm:

1. Confirm the intended public repository holds the published release and matches the
   metadata target; existence of an empty repository does not satisfy this item.
2. Confirm all license and notice files are included in the release tag.
3. Confirm third-party vendored assets and linked materials have acceptable license and
   attribution treatment.
4. Confirm DOI, citation metadata, and archival metadata are filled only after a real
   deposit is created.
5. Complete separate security, privacy, trademark, and access-control review for any
   production deployment.
6. Confirm whether institutional affiliation, funder, trademark, export-control,
   accessibility, data-protection, or contributor-license language is required.
7. Confirm generated artifacts can be distributed under the same MIT declaration as the
   authored sources that produce them.
