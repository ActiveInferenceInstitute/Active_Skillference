# Curriculum Expert Audit Sample

Date: 2026-06-18

Scope: deterministic expert-review sample over the current live curriculum graph.
This is a bounded content-quality audit, not learner-outcome evidence.

## Graph Snapshot

`build_curriculum()` reports 111 subjects, 630 skills, 1199 prerequisite edges, all 8
strata present, two foundational roots, max depth 75, and a core path depth of
thirty-three.

## Sampled High-Depth Path

The deepest chain is the SkillTree mastery/application handoff path:

| Depth | Skill | Subject |
|---:|---|---|
| 75 | `mastery_applications_08` Applications Capstone Mastery Packet | SkillTree Mastery: Applied Contracts |
| 74 | `mastery_applications_07` Applications SkillTree Route Handoff | SkillTree Mastery: Applied Contracts |
| 73 | `mastery_applications_06` Applications Dependency Handoff Review | SkillTree Mastery: Applied Contracts |
| 72 | `mastery_applications_05` Applications Quiz-Authoring Review | SkillTree Mastery: Applied Contracts |
| 71 | `mastery_applications_04` Applications Counterexample and Misuse Review | SkillTree Mastery: Applied Contracts |
| 70 | `mastery_applications_03` Applications Worked-Example Translation | SkillTree Mastery: Applied Contracts |
| 69 | `mastery_applications_02` Applications Core Concept Discriminator | SkillTree Mastery: Applied Contracts |
| 68 | `mastery_applications_01` Applications Prerequisite Map Lab | SkillTree Mastery: Applied Contracts |

Review result: the sampled path is intentionally cumulative. Each row has two or three
prerequisites, multiple assessment questions, and a handoff/review objective rather than a
new unsupported mathematical claim. No repeated issue was found that warrants a new
quality gate beyond the existing DAG, semantic-prerequisite, quiz-gating, and
course-material alignment gates.

## Sampled High-Fanout Nodes

| Dependents | Skill | Review focus |
|---:|---|---|
| 29 | `ai_expected_free_energy` Expected Free Energy (EFE) | Central policy-selection prerequisite; fanout is expected and conceptually coherent. |
| 26 | `vm_free_energy` Variational Free Energy | Bridges variational methods to FEP and active-inference subjects; no orphaned use found. |
| 23 | `p_bayes_theorem` Bayes' Theorem | Foundational probability hub; downstream use is broad but legitimate. |
| 22 | `fep_statement` The Free Energy Principle | Core FEP hub; downstream fanout matches curriculum architecture. |
| 18 | `it_mutual_information` Mutual Information | Information-theory bridge; downstream references stay inside information/EFE topics. |
| 18 | `practice_app_domain_fit` Domain Fit Reviews for Applications | Application-review hub; wording is evaluative, not operational advice. |

Review result: high fanout is concentrated in expected conceptual hubs. The pattern is
not a duplicated-template defect, so no new gate was added.

## Sampled Templated Extension Subjects

The review sampled full families rather than isolated leaves:

| Subject family | Subjects reviewed | Skill count pattern | Depth pattern |
|---|---:|---:|---|
| Visual reasoning by stratum | 8 | 4 each | 3-38 |
| Publication synthesis by stratum | 8 | 4 each | 4-39 |
| Visual evidence contracts | 1 | 6 | 30-35 |
| Active-inference visual explanation | 1 | 6 | 23-29 |
| National security computation context | 1 | 8 | 29-39 |

Review result: the repeated extension subjects are template-like by design, but the
sample did not show a repeated vacuity pattern: each family is checked by existing
semantic-prerequisite, quiz-quality, material-source, and artifact validators. Any future
audit finding should be promoted to a non-vacuous gate only if it repeats across more
than one subject or evades an existing validator.

## Boundary

This audit records expert sampling and gate coverage only. It does not claim learner
efficacy, retention, transfer, classroom validity, or live deployment readiness.
