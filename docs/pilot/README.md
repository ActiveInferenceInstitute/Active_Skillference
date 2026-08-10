# Learner pilot package

This folder defines the minimum evidence contract for a future learner pilot. It is
deliberately protocol-only: the current repository contains no learner data and makes no
efficacy, retention, transfer, or population-level impact claim.

## Contract

[`../../data/learner_pilot_contract.json`](../../data/learner_pilot_contract.json) is the
machine-readable source of truth. Validate it with:

```bash
uv run python scripts/validate_learner_pilot_contract.py
```

The contract requires consent and data minimization, prohibits direct identifiers in the
analysis export, names the unit of analysis and missing-data policy, and keeps SkillTree as
the system of record for progress and quiz state.

## Protocol sequence

1. Pre-register recruitment, inclusion/exclusion, outcomes, observation windows, stopping
   rules, and the analysis notebook version before inspecting learner outcomes.
2. Obtain consent and record only the declared participant fields. Generate a study ID that
   cannot be used to recover a learner account.
3. Export read-only SkillTree events using the declared schema. Never add an app-owned
   progress store or silently merge dashboard state into the export.
4. Run completeness and missingness checks first. Report denominators and structural gaps;
   do not impute a missing completion or quiz result as success.
5. Publish only feasibility and measurement-readiness summaries until a separately reviewed
   study supports stronger claims.

## What this package does not prove

Curriculum size, prerequisite validity, quiz completion, and synthetic diagnostics are
engineering evidence about the artifact. They are not evidence that learners learn, retain,
transfer, or benefit from adaptive recommendations. Those claims require real participants,
predeclared outcomes, appropriate review, and a claim-support record tied to the observed
data.
