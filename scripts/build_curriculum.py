#!/usr/bin/env python3
"""Build and validate the Active Inference curriculum DAG; print and persist stats.

Thin orchestrator: all logic lives in ``src.curriculum``. Validation raises on any
cycle, dangling prerequisite, or non-foundational root.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.artifacts.json_io import write_json_artifact
from src.curriculum.catalog import build_curriculum
from src.curriculum.diagnostics import write_curriculum_diagnostic_gap_map
from src.curriculum.model import ALL_STRATA
from src.project_paths import project_output_dirs


def main() -> Path:
    graph = build_curriculum()  # validates internally
    stats = graph.stats()
    out_dir = project_output_dirs()["data"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "curriculum_stats.json"
    write_json_artifact(out_path, stats)
    diagnostic_path = write_curriculum_diagnostic_gap_map(
        graph,
        out_dir / "curriculum_diagnostic_gap_map.json",
    )

    print(
        f"curriculum valid: {stats['skills']} skills / {stats['subjects']} subjects "
        f"/ {stats['prerequisite_edges']} prerequisite edges"
    )
    print(
        f"strata present: {stats['strata_count']}/{len(ALL_STRATA)} "
        f"(all={stats['all_strata_present']}), "
        f"max depth {stats['max_depth']}, "
        f"connected foundations→applications={graph.is_connected_foundations_to_applications()}"
    )
    print(str(out_path))
    print(str(diagnostic_path))
    return diagnostic_path


if __name__ == "__main__":
    main()
