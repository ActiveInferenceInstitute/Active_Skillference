# Adopt the v5.1.0 GNN upstream pin (currently v5.0.3)

<!-- GENERATED FROM tasks.yaml. Do not edit by hand. -->

## Roadmap Link

- Task id: `asf-gnn-upstream-5-1-adoption`
- Status: `todo`
- Scale: `minor`
- Surface: `validation`
- Owner: `gnn/upstream.json`
- Top-level TODO: [`TODO.md`](../../TODO.md)

## Scope

gnn/upstream.json pins Generalized_Notation_Notation at v5.0.3 (8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1), while the estate cutover moved the importer repositories to v5.1.0 (75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf); this repository was not part of that cutover, so its pin is accurate but behind. The tag is duplicated in five places that must move together: gnn/upstream.json, gnn/README.md, docs/gates.md, .github/GNN.md, and the pinned-record constant plus the scratch-checkout tag in tests/test_gnn_conformance.py, with README.md linking the v5.0.3 tag at three places. scripts/validate_gnn_spec.py extracts the pinned commit with git archive and parses the specification with that checkout's parser, so a metadata-only edit would be drift rather than proof: the bump counts only once ./gates.sh gnn passes against a v5.1.0 checkout. Blocker: the arm fails, never skips, without a prepared v5.1.0 checkout and interpreter (GNN_ROOT/GNN_PYTHON), and the hosted `gnn conformance (pinned)` job cannot stand in for it while Actions is billing-locked org-wide. A local Generalized_Notation_Notation checkout at v5.1.0 already exists on the working host (75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf), so the maintainer who runs it can close this.

## Deliverables

- Update the `validation` surface owned by `gnn/upstream.json` only as needed for this task.
- Refresh generated artifacts or documentation surfaces named by the evidence commands.
- Keep `tasks.yaml` canonical and regenerate `TODO.md` rather than hand-editing it.

## Out of Scope

- Do not stage, commit, push, publish, or mint a DOI as part of this task unless a later request explicitly asks for it.
- Do not weaken validators, coverage thresholds, provenance checks, or source-role requirements to make evidence pass.

## Dependencies and Blockers

- Depends on: none declared in `tasks.yaml`.
- Current blocker: none; this item is open for implementation.

## Evidence Commands

- `git ls-remote --tags https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation.git (v5.1.0 = 75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf)`
- `GNN_ROOT=<v5.1.0 checkout> GNN_PYTHON=<interpreter> ./gates.sh gnn`
- `uv run pytest tests/test_gnn_conformance.py -q`

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
-   A pin bump is specification-conformance maintenance, not scientific or learner-outcome evidence.
- Phase exit:
-   gnn/upstream.json records tag v5.1.0 and commit 75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf, the five duplicated pin references agree, and `./gates.sh gnn` reports clean against that checkout with no skips.
