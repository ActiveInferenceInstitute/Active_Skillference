# `src/artifacts/` — deterministic JSON artifacts

`json_io.py` provides read/write helpers for JSON objects and arrays, including
`write_json_artifact`. `contracts.py` declares the `TypedDict` payload shapes
shared by figure and dashboard consumers.

Artifacts are the boundary between producers (validators, figure renderers) and
readers (figures, dashboard, manuscript variables). Writers sort keys and omit
timestamps by default so rebuilds are byte-identical.

Parent guide: [`../AGENTS.md`](../AGENTS.md).
