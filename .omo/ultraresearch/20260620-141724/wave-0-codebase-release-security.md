# Wave 0 - Release And Security Seams

Worker: `019ee6e6-3b54-7030-8d93-469df5ebec10`

Key findings:
- `src/skilltree/local_auth.py` persisted the trusted-client secret before token verification; a failed token exchange could leave a newly obtained secret in ignored local state.
- Release-readiness inventory wording and blocker probes are intentionally volatile; keep them factual and avoid treating roadmap text as release proof.
- Public redaction tests were strong for dashboard/public JSON, but the secret persistence order deserved a direct regression test.

Implemented from this wave:
- Changed local-auth bootstrap to build the updated secret-bearing state in memory, verify the trusted-client token first when requested, and only then save the state.
- Added `test_ensure_local_skilltree_auth_does_not_store_unverified_secret`.

EXPAND markers:
- LEAD: persisted trusted-client secret is written before token verification in local auth.
- LEAD: release inventory wording carries volatile blocker prose and old readiness framing.
- LEAD: public redaction coverage does not fully span every serialization path.
- LEAD: live-dashboard refactor contract is broader than the strongest tests prove.
