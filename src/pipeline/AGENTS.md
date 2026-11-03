# AGENTS.md — `src/pipeline/`

- Keep this package importable and argument-free. CLI parsing, stdout and exit
  codes belong in `scripts/`.
- Call the owning package for each artifact; do not duplicate kernel, figure,
  curriculum or scholarship logic here.
- Writes go through `src.artifacts.json_io` and stay deterministic. Do not add
  timestamps or machine paths to a payload.
- Rebuilding the full artifact set must remain safe to run repeatedly and must
  not require the live SkillTree stack.
- Parent rules: [../AGENTS.md](../AGENTS.md).
