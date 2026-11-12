# FIX-ME major: >=90% coverage aggregate masks 32% security-module coverage

<!-- GENERATED FROM tasks.yaml. Do not edit by hand. -->

## Roadmap Link

- Task id: `asf-review-coverage-floor-illusion`
- Status: `todo`
- Scale: `major`
- Surface: `validation`
- Owner: `tests`
- Top-level TODO: [`TODO.md`](../../TODO.md)

## Scope

Progress through 2026-08-01: aggregate src coverage is 92.03% (up from 90.30%) and the previously-thin logic/validation modules are now genuinely covered: summary.py 85% -> 99%, curriculum/alignment.py 66% -> 95%, pilot/contract.py 83% -> 95%, form_login_validation guard branches 32% -> 50%, github_sources retry paths (5xx/network/exhaustion), and recommendations ordering/cycle/remediation. The aggregate floor no longer greenwashes these core modules. Remaining sub-90 modules are all live/network/browser gated and need a Docker/browser-capable host (they are folded into the live-stack tasks): full_app_stack.py ~61% (Docker), form_login_validation.py ~50% (browser subprocess), source_health_network.py ~72% (live HTTP), dashboard/payload.py ~68% (live-auth block, httpserver). Add live/browser-capable coverage for those before claiming the floor is uniformly green. 2026-08-09 update: aggregate is 92.08% over 923 tests. The four named modules are still the sub-90 set (full_app_stack.py 63.77%, form_login_validation.py 49.76%, source_health_network.py 72.39%, dashboard/payload.py 70.37%), and this pass confirmed empirically why the exception matters rather than assuming it: the dashboard CSP bug that blanked the official SkillTree iframe was invisible to all 900+ offline tests and was caught only by the live browser console gate, and the reconciler's abort-on-slow-write bug was caught only by a real 1199-edge run. Offline unit coverage of these modules would not have found either. The regression tests added here are the mechanically checkable part (browser-session restart, post-timeout confirmation, retry bounds, CSP directives, deferred parity, gzip), and the live gates remain the proof for the rest. 2026-11-12 re-measurement of the current tree (`python -m pytest --cov=src`, no floor override): 989 passed, aggregate src coverage 90.92% (10348 statements, 738 missed, 3228 branches, 355 partial), i.e. 0.92 points above the 90% gate. The four modules this task names are unchanged (full_app_stack.py 63.77%, form_login_validation.py 49.76%, source_health_network.py 72.39%, dashboard/payload.py 70.37%), but they are not the whole sub-90 set: 23 src modules sit under 90%, and the extremes are src/publication/zenodo.py 0.00% (98 statements that no test touches, although scripts/publish_zenodo_deposit.py calls it), form_login_validation.py 49.76%, src/screenshots/capture.py 47.79%, full_app_stack.py 63.77%, and src/curriculum/materials/* between 75.48% and 84.38%. The same measurement found a second illusion: dropping the last blocked task from tasks.yaml moved the blocked-status branches of src/roadmap.py (94.23% -> 92.99%) and src/figures/plots/roadmap.py (92.62% -> 89.34%) out of coverage, because those paths were exercised only by the real roadmap data and have no fixture, so the next blocked task silently restores the appearance of coverage. A roadmap-state fixture is therefore part of closing this. Blocker for the live-gated share is a Docker/browser-capable host, and the maintainer who can provide it is the owner; the per-module coverage exception record this task keeps pointing at still does not exist in the repository.

## Deliverables

- Update the `validation` surface owned by `tests` only as needed for this task.
- Refresh generated artifacts or documentation surfaces named by the evidence commands.
- Keep `tasks.yaml` canonical and regenerate `TODO.md` rather than hand-editing it.

## Out of Scope

- Do not stage, commit, push, publish, or mint a DOI as part of this task unless a later request explicitly asks for it.
- Do not weaken validators, coverage thresholds, provenance checks, or source-role requirements to make evidence pass.

## Dependencies and Blockers

- Depends on: none declared in `tasks.yaml`.
- Current blocker: none; this item is open for implementation.

## Evidence Commands

- `uv run pytest --cov=src --cov-fail-under=90`

## Acceptance Criteria

- All evidence commands listed above pass, or the task remains blocked with exact blocker evidence.
- Generated roadmap surfaces validate with `uv run python scripts/validate_roadmap.py`.
- Live counts remain current with `uv run python scripts/validate_live_counts.py`.

## Scholarship and Evidence Plan

- Lanes: delivery_and_reporting, applications_and_scope
- Existing source keys: none
- Planned source targets:
-   none
- Claim-support types: delivery
- Boundaries:
-   Coverage measures exercised code paths, not correctness or safety.
- Phase exit:
-   Every sub-90 module meets the 90% floor or has a documented browser/Docker path exception.
