# AGENTS.md — `src/provenance/`

- Fail closed. An unbacked, empty or malformed `{{claim:NAME}}` token is an
  error, never a blank substitution.
- Re-registering a claim with a different value or provenance must keep raising.
  String claims must not contain digits.
- Scan every learner-facing field, not only the description. Add the new field
  to `Skill.claim_tokens()` and to the render tests.
- Never hand-type a computed result into content; add the worked example in
  `../kernels/examples.py` and reference the claim.
- Parent rules: [../AGENTS.md](../AGENTS.md).
