# Active Skillference TODO

<!-- GENERATED FROM tasks.yaml. Do not edit by hand. -->

## Current Proof

- 630 skills, 111 subjects, 1199 prerequisite edges, 2520 assessment questions.
- 79 claims, 26 figures, 188 cited sources, max depth 75.

## Active Roadmap

### External Blockers

- [!] **[asf-public-release-metadata](docs/todo/asf-public-release-metadata.md)** (metadata): Publication DOI and repository target decision
  - Scope: The public repository target is owner-confirmed as ActiveInferenceInstitute/Active_Skillference and is set in manuscript/config.yaml. The owner also confirmed MIT for authored code/content and generated artifacts, Daniel Ari Friedman as the copyright holder, and the need for a counsel-review checklist before formal release. The private docxology/Active_Skillference mirror is current and local offline validators are green. Probed on 2026-08-09, the public target now exists and is public, but git ls-remote returns zero refs and the GitHub API reports size 0, so the target is reachable and still unpublished. Existence is not publication, and no commit, no tag, no archive deposit, and no DOI exist for it yet. This task stays blocked rather than todo because the remaining step is an owner-executed push, release, and Zenodo deposit performed outside this repository, not repository work that can be implemented here. DOI, release-date, and repository-URL fields stay blank rather than carrying fabricated metadata.
  - Evidence: `uv run python scripts/validate_live_counts.py`; `uv run python scripts/validate_manuscript_variables.py`; `uv run python scripts/z_generate_manuscript_variables.py`; `uv run python scripts/validate_rendered_freshness.py`; `git ls-remote --heads https://github.com/ActiveInferenceInstitute/Active_Skillference.git HEAD`
  - Scholarship lanes: delivery_and_reporting, applications_and_scope

### Minor Improvements

- [ ] **[asf-skilltree-460-live-reverify](docs/todo/asf-skilltree-460-live-reverify.md)** (skilltree): Live re-verify local SkillTree stack against skills-service 4.6.0
  - Scope: Opened 2026-08-01 after bumping the pinned runtime from skills-service 4.5.2 to 4.6.0 (upstream release 2026-07-28). docker-compose.yml postgres:15 digest and the skills-service tag+digest were refreshed via the documented Docker Hub procedure (skills-service 4.6.0 = sha256:071220ce..., single-arch; postgres:15 = sha256:74e110c4..., multi-arch incl. arm64), and AuthMode was re-confirmed as FORM/PKI/SAML2 at the 4.6.0 tag (no PKI_OR_FORM). The digest pin and docs were updated, but no live full-app boot against 4.6.0 was recorded because Docker was not running on the reconciliation host. Per the provenance-over-assertion principle, the 4.5.2 live records (asf-skilltree-452-live-reverify) do NOT prove anything about 4.6.0; run the full-app proof (reset_local_skilltree.py --confirm-local-reset --timeout 1200) against 4.6.0 and record proof.ok here before reading this pin as live-verified. 2026-08-09 partial progress on a Docker-capable host, recorded without claiming the phase exit: validate_docker_digests.py passes against the running stack, and the strict full-parity proof (validate_full_app_stack.py --skip-regenerate, see asf-live-stack-ci-rehearsal) is green against skills-service 4.6.0 with 1199/1199 live dependencies, 630 live admin skills, raw FORM login, and the browser console gate. What is still NOT proven is the fresh-volume path this task actually asks for: whether the documented default root credentials bootstrap correctly on a newly created 4.6.0 volume. That requires the destructive reset (docker compose down -v), which would also discard the 1199/1199 parity that took roughly an hour of per-edge writes to reach on this Apple/ARM host, so it is deliberately left for an explicit maintainer run rather than folded in here.
  - Depends on: `asf-skilltree-452-live-reverify`
  - Evidence: `uv run python scripts/reset_local_skilltree.py --confirm-local-reset --timeout 1200`; `uv run python scripts/validate_docker_digests.py`
  - Scholarship lanes: delivery_and_reporting

### Major Improvements

- [ ] **[asf-public-archive-provenance-release](docs/todo/asf-public-archive-provenance-release.md)** (metadata): Public archive, DOI, and provenance release package
  - Scope: The public target exists and is public but currently holds zero refs, so reachability is no longer the gate; published content is. After the target carries a real published release, complete the publication metadata chain: release tag, Zenodo DOI, CFF/CodeMeta/manuscript URL fields, artifact hashes, third-party notices, counsel-review checklist, and release inventory refresh. This task must not fabricate DOI or repository metadata before the upstream blocker is cleared.
  - Depends on: `asf-public-release-metadata`
  - Evidence: `git ls-remote --heads https://github.com/ActiveInferenceInstitute/Active_Skillference.git HEAD`; `uv run python scripts/validate_release_readiness_inventory.py --write`; `uv run python scripts/validate_release_readiness_inventory.py`; `uv run python scripts/validate_manuscript_variables.py`; `uv run python scripts/validate_rendered_freshness.py`
  - Scholarship lanes: delivery_and_reporting, applications_and_scope
- [ ] **[asf-review-coverage-floor-illusion](docs/todo/asf-review-coverage-floor-illusion.md)** (validation): FIX-ME major: >=90% coverage aggregate masks 32% security-module coverage
  - Scope: Progress through 2026-08-01: aggregate src coverage is 92.03% (up from 90.30%) and the previously-thin logic/validation modules are now genuinely covered: summary.py 85% -> 99%, curriculum/alignment.py 66% -> 95%, pilot/contract.py 83% -> 95%, form_login_validation guard branches 32% -> 50%, github_sources retry paths (5xx/network/exhaustion), and recommendations ordering/cycle/remediation. The aggregate floor no longer greenwashes these core modules. Remaining sub-90 modules are all live/network/browser gated and need a Docker/browser-capable host (they are folded into the live-stack tasks): full_app_stack.py ~61% (Docker), form_login_validation.py ~50% (browser subprocess), source_health_network.py ~72% (live HTTP), dashboard/payload.py ~68% (live-auth block, httpserver). Add live/browser-capable coverage for those before claiming the floor is uniformly green. 2026-08-09 update: aggregate is 92.08% over 923 tests. The four named modules are still the sub-90 set (full_app_stack.py 63.77%, form_login_validation.py 49.76%, source_health_network.py 72.39%, dashboard/payload.py 70.37%), and this pass confirmed empirically why the exception matters rather than assuming it: the dashboard CSP bug that blanked the official SkillTree iframe was invisible to all 900+ offline tests and was caught only by the live browser console gate, and the reconciler's abort-on-slow-write bug was caught only by a real 1199-edge run. Offline unit coverage of these modules would not have found either. The regression tests added here are the mechanically checkable part (browser-session restart, post-timeout confirmation, retry bounds, CSP directives, deferred parity, gzip), and the live gates remain the proof for the rest.
  - Evidence: `uv run pytest --cov=src --cov-fail-under=90`
  - Scholarship lanes: delivery_and_reporting, applications_and_scope
