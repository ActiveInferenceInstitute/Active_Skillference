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

The public target exists and is public but currently holds zero refs, so reachability is no longer the gate; published content is. After the target carries a real published release, complete the publication metadata chain: release tag, Zenodo DOI, CFF/CodeMeta/manuscript URL fields, artifact hashes, third-party notices, counsel-review checklist, and release inventory refresh. This task must not fabricate DOI or repository metadata before the upstream blocker is cleared.

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

- `git ls-remote --heads https://github.com/ActiveInferenceInstitute/Active_Skillference.git HEAD`
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
-   DOI, public URLs, and release timestamps are blank until the repository and archive events occur.
-   Metadata standards support release reproducibility, not scientific validity, legal advice, or learner outcomes.
- Phase exit:
-   A real public tag, archive deposit, DOI, CFF/CodeMeta metadata, hashes, notices, and inventory agree.
-   The final release record is regenerated from observed external metadata rather than placeholders.
