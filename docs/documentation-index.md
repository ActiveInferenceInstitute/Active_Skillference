# Documentation index

Flat index of the long-lived documentation in `docs/`. [`README.md`](README.md) is the
hub (grouped by the question you arrived with); this page is the complete list, with the
one fact each document is authoritative for. Generated pages are marked as such and are
refreshed by their producer, never edited by hand.

Contributing or reviewing? Start with [`agent_instructions.md`](agent_instructions.md)
(invariants) and [`gates.md`](gates.md) (the gate entry point).

There is no mkdocs or markdown-link-check configuration in this repository. Documentation
is gated by two things instead: [`../scripts/check_docs_links.py`](../scripts/check_docs_links.py)
(the `docs` arm) fails on any relative Markdown link or image that does not resolve, and
[`../tests/test_docs_inventory.py`](../tests/test_docs_inventory.py) fails when this folder's
inventory tables, the `scripts/` inventory, or the generated roadmap pages drift from the
files on disk.

## Entry points

| Document | Authoritative for |
| --- | --- |
| [`README.md`](README.md) | Documentation hub, what "high-integrity" means here, cold start |
| [`AGENTS.md`](AGENTS.md) | Technical index of this folder, conventions, verification commands |
| [`documentation-index.md`](documentation-index.md) | This flat index |
| [`quickstart.md`](quickstart.md) | First run: build → kernels → export → test |
| [`faq.md`](faq.md) | Recurring questions about provenance, the DAG, and SkillTree |
| [`troubleshooting.md`](troubleshooting.md) | Symptom → cause → fix recipes |
| [`agent_instructions.md`](agent_instructions.md) | Hard rules for agents and the verification checklist |

## Gates, testing, and delivery

| Document | Authoritative for |
| --- | --- |
| [`gates.md`](gates.md) | `./gates.sh` arms, what each one runs, and how CI maps to them |
| [`gate_metrics.md`](gate_metrics.md) | Generated per-arm wall times and test/coverage counts |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock policy, test-file inventory, coverage mechanics |
| [`style_guide.md`](style_guide.md) | Source rules: thin orchestrator, `src.*` imports, typing, error text |
| [`output_conventions.md`](output_conventions.md) | `output/` layout, what is disposable, regeneration rules |
| [`output_inventory.md`](output_inventory.md) | Producer/consumer graph for every pipeline artifact |
| [`release_readiness_inventory.md`](release_readiness_inventory.md) | Generated release-isolation inventory and artifact hashes |
| [`publication_readiness.md`](publication_readiness.md) | Static publication readiness and remaining release blockers |
| [`ip_license_status.md`](ip_license_status.md) | MIT declaration, third-party boundaries, DOI status, review caveats |

## Architecture and authoring

| Document | Authoritative for |
| --- | --- |
| [`architecture.md`](architecture.md) | The `src/` layers, dependency direction, adding a skill or kernel |
| [`syntax_guide.md`](syntax_guide.md) | Markdown/LaTeX in skill and manuscript content, `{{claim:NAME}}` tokens, figure references |
| [`scholarship_coverage.md`](scholarship_coverage.md) | Citation source-role matrix, validator, edit protocol |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Manuscript → PDF/web flow, preflight, hydration, render toolchain |
| [`curriculum_expert_audit.md`](curriculum_expert_audit.md) | Deterministic expert-review sample over the curriculum surfaces |
| [`forking_guide.md`](forking_guide.md) | Adapting the platform to another curriculum domain |

## Runtime and study surfaces

| Document | Authoritative for |
| --- | --- |
| [`learner_dashboard.md`](learner_dashboard.md) | Local dashboard routes, SkillTree ownership boundary, offline behavior |
| [`pilot/`](pilot/) | Protocol-only learner-pilot contract, privacy boundary, export schema |
| [`todo/`](todo/) | Generated per-task handoff pages for the active roadmap |

## Repository-level documents (outside this folder)

| Document | Authoritative for |
| --- | --- |
| [`../README.md`](../README.md) | Overview, quick start, the GNN model specification, required local GNN check |
| [`../AGENTS.md`](../AGENTS.md) | Project-level agent guidance and the auditable provenance chain |
| [`../ISA.md`](../ISA.md) | Ideal State Artifact: problem, principles, criteria, verification |
| [`../TODO.md`](../TODO.md) | Generated forward-only roadmap surface (`tasks.yaml` is the source) |
| [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) | Manuscript directory rules and the claim-token protocol |
| [`../vendor/README.md`](../vendor/README.md) | Running a live SkillTree instance |
| [`../.github/README.md`](../.github/README.md) | GitHub automation: workflows, Dependabot |
| [`../.github/GNN.md`](../.github/GNN.md) | What the GNN conformance job parses and which pin it reads |
