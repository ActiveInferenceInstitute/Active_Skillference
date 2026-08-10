# Live re-verify local SkillTree stack against skills-service 4.6.0

<!-- GENERATED FROM tasks.yaml. Do not edit by hand. -->

## Roadmap Link

- Task id: `asf-skilltree-460-live-reverify`
- Status: `todo`
- Scale: `minor`
- Surface: `skilltree`
- Owner: `docker-compose.yml`
- Top-level TODO: [`TODO.md`](../../TODO.md)

## Scope

Opened 2026-08-01 after bumping the pinned runtime from skills-service 4.5.2 to 4.6.0 (upstream release 2026-07-28). docker-compose.yml postgres:15 digest and the skills-service tag+digest were refreshed via the documented Docker Hub procedure (skills-service 4.6.0 = sha256:071220ce..., single-arch; postgres:15 = sha256:74e110c4..., multi-arch incl. arm64), and AuthMode was re-confirmed as FORM/PKI/SAML2 at the 4.6.0 tag (no PKI_OR_FORM). The digest pin and docs were updated, but no live full-app boot against 4.6.0 was recorded because Docker was not running on the reconciliation host. Per the provenance-over-assertion principle, the 4.5.2 live records (asf-skilltree-452-live-reverify) do NOT prove anything about 4.6.0; run the full-app proof (reset_local_skilltree.py --confirm-local-reset --timeout 1200) against 4.6.0 and record proof.ok here before reading this pin as live-verified. 2026-08-09 partial progress on a Docker-capable host, recorded without claiming the phase exit: validate_docker_digests.py passes against the running stack, and the strict full-parity proof (validate_full_app_stack.py --skip-regenerate, see asf-live-stack-ci-rehearsal) is green against skills-service 4.6.0 with 1199/1199 live dependencies, 630 live admin skills, raw FORM login, and the browser console gate. What is still NOT proven is the fresh-volume path this task actually asks for: whether the documented default root credentials bootstrap correctly on a newly created 4.6.0 volume. That requires the destructive reset (docker compose down -v), which would also discard the 1199/1199 parity that took roughly an hour of per-edge writes to reach on this Apple/ARM host, so it is deliberately left for an explicit maintainer run rather than folded in here.

## Deliverables

- Update the `skilltree` surface owned by `docker-compose.yml` only as needed for this task.
- Refresh generated artifacts or documentation surfaces named by the evidence commands.
- Keep `tasks.yaml` canonical and regenerate `TODO.md` rather than hand-editing it.

## Out of Scope

- Do not stage, commit, push, publish, or mint a DOI as part of this task unless a later request explicitly asks for it.
- Do not weaken validators, coverage thresholds, provenance checks, or source-role requirements to make evidence pass.

## Dependencies and Blockers

- Depends on: `asf-skilltree-452-live-reverify`
- Current blocker: upstream dependency must clear first: `asf-skilltree-452-live-reverify`

## Evidence Commands

- `uv run python scripts/reset_local_skilltree.py --confirm-local-reset --timeout 1200`
- `uv run python scripts/validate_docker_digests.py`

## Acceptance Criteria

- All evidence commands listed above pass, or the task remains blocked with exact blocker evidence.
- Generated roadmap surfaces validate with `uv run python scripts/validate_roadmap.py`.
- Live counts remain current with `uv run python scripts/validate_live_counts.py`.

## Scholarship and Evidence Plan

- Lanes: delivery_and_reporting
- Existing source keys: none
- Planned source targets:
-   none
- Claim-support types: scope_limit
- Boundaries:
-   Live full-app proof against skills-service 4.6.0 is operational verification, not a scientific or learner-outcome claim.
- Phase exit:
-   `uv run python scripts/reset_local_skilltree.py --confirm-local-reset --timeout 1200` reports proof.ok=true against 4.6.0 and the evidence is recorded in this task.
