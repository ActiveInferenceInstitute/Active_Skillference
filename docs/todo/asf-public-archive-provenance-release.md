# Public archive, DOI, and provenance release package

<!-- GENERATED FROM tasks.yaml. Do not edit by hand. -->

## Roadmap Link

- Task id: `asf-public-archive-provenance-release`
- Status: `todo`
- Scale: `major`
- Surface: `metadata`
- Owner: `manuscript/config.yaml`
- Top-level TODO: [`TODO.md`](../../TODO.md)

## Scope

Upstream dependency cleared on 2026-11-12: the public target carries main, 19 pull-request refs, and the annotated tags v1.0.0 (5f32086) and v1.0.1 (c4e34e7), and Zenodo record 21865644 holds version 1.0.0 (published 2026-08-10; concept DOI 10.5281/zenodo.21865643). The release chain can therefore be read from observed records; what remains is making it agree with itself. (1) Version drift: the only deposit is 1.0.0, while .zenodo.json (version 1.0.1, publication_date 2026-08-09), CITATION.cff (version 1.0.1, date-released 2026-08-09), codemeta.json (version 1.0.1, datePublished 2026-08-09) and manuscript/config.yaml (paper.version and book.edition 1.0.1) all claim a release Zenodo does not hold, the v1.0.1 tag has no deposit behind it, and manuscript/config.yaml keeps publication.version_doi and version_record blank. Either deposit v1.0.1 and record the version DOI it returns, or downgrade the claim to the observed 1.0.0. (2) docs/release_readiness_inventory.md is stale at HEAD: validate_release_readiness_inventory.py fails on the tracked-diff summary, on the listed manuscript/README.md modification, and on the recorded figure hashes, and src/release_readiness.py renders "Public DOI/repository remains blocked until git ls-remote succeeds" unconditionally, so a --write refresh would publish a sentence the current probe no longer supports. Fix the generator before refreshing the snapshot. (3) The third-party notice sweep and the counsel-review checklist are still outstanding. Every value must come from the observed records; nothing here may be fabricated.

## Deliverables

- After the public repository blocker clears, complete release tag, Zenodo DOI, CFF, CodeMeta, artifact hashes, notices, and inventory refresh.
- Preserve the no-fabricated-metadata boundary until upstream release proof exists.
- Update the `metadata` surface owned by `manuscript/config.yaml` only as needed for this task.
- Refresh generated artifacts or documentation surfaces named by the evidence commands.
- Keep `tasks.yaml` canonical and regenerate `TODO.md` rather than hand-editing it.

## Out of Scope

- Do not backfill public metadata before `asf-public-release-metadata` is unblocked.
- Do not stage, commit, push, publish, or mint a DOI as part of this task unless a later request explicitly asks for it.
- Do not weaken validators, coverage thresholds, provenance checks, or source-role requirements to make evidence pass.

## Dependencies and Blockers

- Depends on: `asf-public-release-metadata`
- Current blocker: upstream dependency must clear first: `asf-public-release-metadata`

## Evidence Commands

- `git ls-remote --tags https://github.com/ActiveInferenceInstitute/Active_Skillference.git (v1.0.0 = 5f32086, v1.0.1 = c4e34e7)`
- `curl -s https://zenodo.org/api/records/21865644/versions (a single version — 1.0.0)`
- `uv run python scripts/validate_release_readiness_inventory.py --write`
- `uv run python scripts/validate_release_readiness_inventory.py`
- `uv run python scripts/validate_manuscript_variables.py`
- `uv run python scripts/validate_rendered_freshness.py`

## Acceptance Criteria

- All evidence commands listed above pass, or the task remains blocked with exact blocker evidence.
- Generated roadmap surfaces validate with `uv run python scripts/validate_roadmap.py`.
- Live counts remain current with `uv run python scripts/validate_live_counts.py`.

## Scholarship and Evidence Plan

- Lanes: delivery_and_reporting, applications_and_scope
- Existing source keys: `smith2016softwarecitation`, `citationfileformat2026`, `codemeta2026schema`, `github2026citingcontent`, `zenodo2026github`, `wilkinson2016fair`, `nosek2015top`
- Planned source targets:
-   none
- Claim-support types: delivery, scope_limit, literature
- Boundaries:
-   Deposited version identifiers and dates must match the Zenodo record that actually exists (1.0.0, published 2026-08-10), not the locally claimed 1.0.1.
-   Metadata standards support release reproducibility, not scientific validity, legal advice, or learner outcomes.
- Phase exit:
-   A real public tag, archive deposit, DOI, CFF/CodeMeta metadata, hashes, notices, and inventory agree.
-   The final release record is regenerated from observed external metadata rather than placeholders.
