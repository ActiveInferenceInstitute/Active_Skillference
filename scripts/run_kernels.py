#!/usr/bin/env python3
"""Run computational kernels, register claims, validate scholarship, render figures.

Thin orchestrator: kernels live in ``src.kernels``; figures in ``src.figures``.
Emits ``output/data/claims.json`` (the provenance ledger), a
``manuscript_variables.json`` for the manuscript, the scholarship audit,
the manuscript artifact audit, and deterministic figures.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.pipeline.generated_outputs import build_generated_outputs


def main() -> list[Path]:
    bundle = build_generated_outputs(_ROOT)
    print(f"registered {bundle.provenance_claims} provenance claims")
    print(f"validated scholarship coverage: {bundle.cited_sources} cited sources")
    print(
        "validated manuscript artifacts: "
        f"{bundle.registered_figures} registered figures"
    )
    print("validated cover asset: active_skillference_cover.png")
    print("validated page-two visual: active_skillference_skill_atlas.png")
    print("validated American English manuscript language")
    print(f"validated manuscript claim support: {bundle.claim_rows} claims")
    print(
        f"validated scholarship gap report: {bundle.frontier_sources} frontier sources"
    )
    print(f"validated course materials: {bundle.material_records} skills")
    for path in bundle.paths:
        print(str(path))
    return list(bundle.paths)


if __name__ == "__main__":
    main()
