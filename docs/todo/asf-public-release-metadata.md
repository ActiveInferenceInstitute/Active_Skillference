# Publication DOI and repository target decision

<!-- GENERATED FROM tasks.yaml. Do not edit by hand. -->

## Roadmap Link

- Task id: `asf-public-release-metadata`
- Status: `blocked`
- Scale: `external`
- Surface: `metadata`
- Owner: `manuscript/config.yaml`
- Top-level TODO: [`TODO.md`](../../TODO.md)

## Scope

The public repository target is owner-confirmed as ActiveInferenceInstitute/Active_Skillference and is set in manuscript/config.yaml. The owner also confirmed MIT for authored code/content and generated artifacts, Daniel Ari Friedman as the copyright holder, and the need for a counsel-review checklist before formal release. The private docxology/Active_Skillference mirror is current and local offline validators are green. Probed on 2026-08-09, the public target now exists and is public, but git ls-remote returns zero refs and the GitHub API reports size 0, so the target is reachable and still unpublished. Existence is not publication, and no commit, no tag, no archive deposit, and no DOI exist for it yet. This task stays blocked rather than todo because the remaining step is an owner-executed push, release, and Zenodo deposit performed outside this repository, not repository work that can be implemented here. DOI, release-date, and repository-URL fields stay blank rather than carrying fabricated metadata.

## Deliverables

- Confirm the public repository target is reachable before adding public DOI or repository metadata.
- Keep blocked DOI, CFF, CodeMeta, and manuscript URL fields blank until release proof exists.
- Update the `metadata` surface owned by `manuscript/config.yaml` only as needed for this task.
- Refresh generated artifacts or documentation surfaces named by the evidence commands.
- Keep `tasks.yaml` canonical and regenerate `TODO.md` rather than hand-editing it.

## Out of Scope

- Do not invent a public repository, DOI, release URL, or publication timestamp.
- Do not stage, commit, push, publish, or mint a DOI as part of this task unless a later request explicitly asks for it.
- Do not weaken validators, coverage thresholds, provenance checks, or source-role requirements to make evidence pass.

## Dependencies and Blockers

- Depends on: none declared in `tasks.yaml`.
- Current blocker: blocked by the external condition described in the Scope section.

## Evidence Commands

- `uv run python scripts/validate_live_counts.py`
- `uv run python scripts/validate_manuscript_variables.py`
- `uv run python scripts/z_generate_manuscript_variables.py`
- `uv run python scripts/validate_rendered_freshness.py`
- `git ls-remote --heads https://github.com/ActiveInferenceInstitute/Active_Skillference.git HEAD`

## Acceptance Criteria

- The blocker is cleared and rerun evidence replaces the current blocked status.
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
-   The empty public repository remains an external blocker, not a failed scholarly claim.
-   DOI and repository metadata remain blank until real GitHub and Zenodo events are observed.
- Phase exit:
-   The public target carries published content and a real release, and the publication environment can complete the actual release path.
-   Any release metadata is copied from observed repository and archive records.
