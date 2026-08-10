#!/usr/bin/env python3
"""Export the curriculum into a SkillTree-native project JSON.

Fail-closed pipeline:
1. build + validate the curriculum DAG,
2. build the kernel-derived claim registry,
3. run the provenance gate (every claim token must resolve; no bare result numbers),
4. resolve claim tokens into skill descriptions,
5. export to a SkillTree project JSON.

If any claim token is unbacked, :func:`render_graph` raises and nothing is written.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.curriculum.catalog import build_curriculum
from src.kernels.examples import build_claim_registry
from src.project_identity import (
    SKILLTREE_PROJECT_ID,
    SKILLTREE_PROJECT_NAME,
)
from src.project_paths import project_output_dirs
from src.provenance.binding import (
    lint_graph,
    render_graph,
    validate_curriculum,
)
from src.skilltree import export_to_json

PROJECT_ID = SKILLTREE_PROJECT_ID
PROJECT_NAME = SKILLTREE_PROJECT_NAME


def main() -> Path:
    graph = build_curriculum()
    registry = build_claim_registry()

    # Provenance gate (fail-closed): every claim token must resolve, and no bare result
    # number may appear in any learner-facing free-text field (skill names/descriptions,
    # subject descriptions).
    validate_curriculum(graph.skills, registry)
    violations = lint_graph(graph)
    if violations:
        raise SystemExit(
            f"provenance linter found {len(violations)} unbacked numbers — export refused"
        )

    rendered = render_graph(graph, registry)  # raises on any unresolved token

    out_dir = project_output_dirs()["data"]
    out_path = out_dir / "skilltree_project.json"
    export_to_json(rendered, PROJECT_ID, PROJECT_NAME, out_path)

    print(
        f"exported SkillTree project '{PROJECT_NAME}' "
        f"({len(rendered.skills)} skills, {len(rendered.prerequisite_edges())} dependencies)"
    )
    print(str(out_path))
    return out_path


if __name__ == "__main__":
    main()
