# Wave 0 - Generated JSON Ownership

> **Path note (2026-07-05):** `src/curriculum/materials.py` is now the `materials/` package.
> See [`../PATH_CORRECTIONS.md`](../PATH_CORRECTIONS.md).

Worker: `019ee6e6-35dc-7de1-8978-0b4b70ce80a2`

Key findings:
- `src.artifacts.json_io` is the canonical helper for file-backed generated JSON artifacts.
- Several generated writers still open-coded `json.dumps(..., indent=2, sort_keys=True) + "\n"`.
- Transport JSON, HTTP response JSON, release markdown, and local auth private state should remain bespoke.

Implemented from this wave:
- Adopted `write_json_artifact` in `src/manuscript/audit.py`, `src/manuscript/claim_support.py`, `src/scholarship/coverage.py`, `src/scholarship/source_health.py`, `src/scholarship/gap_report.py`, `src/curriculum/materials.py`, and `scripts/build_curriculum.py`.
- Adopted `read_json_object` in `scripts/validate_manuscript_variables.py` and added executable script path bootstrapping.

Intentional exclusions:
- `src/skilltree/local_auth.py` remains bespoke for local credential-state permissions and token parsing.
- SkillTree HTTP clients, dashboard HTTP response serialization, CLI stdout JSON, and release-readiness markdown remain outside the artifact helper contract.

EXPAND markers:
- LEAD: `scripts/build_curriculum.py` still open-codes JSON artifact writing.
- LEAD: `src/manuscript/audit.py` has three local JSON writers.
- LEAD: `src/manuscript/claim_support.py` still writes audit JSON directly.
- LEAD: `src/scholarship/coverage.py` still writes JSON directly.
- LEAD: `src/curriculum/materials.py` has a local `_write_json` helper.
- LEAD: `scripts/validate_manuscript_variables.py` reads generated JSON directly.
- LEAD: local auth and HTTP JSON are intentionally bespoke.
