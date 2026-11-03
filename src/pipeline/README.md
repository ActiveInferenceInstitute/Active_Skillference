# `src/pipeline/` — importable artifact builders

`generated_outputs.py` builds the project's derived artifacts in one place:
the claim ledger, deterministic figures and table companions, dashboard
artifact payloads, course-material records, and the audit JSON that figures and
the dashboard consume. It calls the owning packages rather than reimplementing
their logic.

`scripts/run_kernels.py` is the thin CLI wrapper: it parses arguments, calls
this package, and maps the result to a process status.

Parent guide: [`../AGENTS.md`](../AGENTS.md). Output layout:
[`../../docs/output_conventions.md`](../../docs/output_conventions.md).
