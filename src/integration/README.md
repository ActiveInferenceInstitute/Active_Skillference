# `src/integration/` — live-stack orchestration

`full_app_stack.py` brings up and checks the live proof: Docker services,
SkillTree and the local learner dashboard. It owns orchestration only; the
dashboard payload, SkillTree client and curriculum logic stay in their packages.

`ensure_browser_session_responsive` probes the browser automation daemon and
restarts it once before a browser proof, so a stale session is reported as a
harness problem rather than an application failure.

Driver: `scripts/validate_full_app_stack.py`. Parent guide:
[`../AGENTS.md`](../AGENTS.md). This proof needs a Docker daemon and a browser;
CI does not run it.
