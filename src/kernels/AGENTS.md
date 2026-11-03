# AGENTS.md — `src/kernels/`

- Keep every function pure: inputs in, values out, no file, network or global
  state. Rendering and writes belong in `figures/` and `scripts/`.
- Units are nats. Keep the existing guards against negative, unnormalized and
  non-finite inputs; a new guard needs a test that rejects the bad input.
- No bare `kernels.` imports. Use `from src.kernels.<module> import ...`.
- Every learner-facing number comes from `examples.build_claim_registry()`,
  referenced as `{{claim:NAME}}`; never hardcode a result in a skill.
- Kernel changes land with a real-value test asserting an analytic identity,
  not a smoke call. Seed any RNG with `numpy.random.default_rng`.
- Parent rules: [../AGENTS.md](../AGENTS.md).
