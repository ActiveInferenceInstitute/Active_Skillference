# AGENTS.md — `src/skilltree/`

- No mocks. Test the REST client and seeder against a real local server
  (`pytest-httpserver`), asserting path, method, headers and body.
- Seed in dependency-safe order: quizzes before quiz-gated skills, dependencies
  after skills. Do not reorder for convenience.
- Judge a reconciliation by `missingAfter`/`extraAfter`, not by retry counters.
  A late write confirmed by a re-read is `confirmedAfterTimeout`, not a failure.
- Read tokens from the caller or environment; never write a credential, cookie
  or session token into an artifact or test fixture.
- Keep browser automation out of the pure FORM helpers.
- Parent rules: [../AGENTS.md](../AGENTS.md).
