# Release Readiness Inventory

Date: 2026-08-10

Scope: local `Active_Skillference` checkout only. This inventory records the current git-visible release state and remaining external release blockers; generation and validation do not create a public release, DOI, pull request, or destructive cleanup.

## Dirty Worktree Snapshot

`git status --short` currently reports 1 rows outside this inventory file. The detailed file lists below contain 1 modified tracked paths and 0 untracked paths requiring intentional add or exclusion before a release commit.

Tracked diff summary outside this inventory file from `git diff --stat -- . ':(exclude)docs/release_readiness_inventory.md'`: `1 file changed, 2 insertions(+), 1 deletion(-)`.

## Modified Tracked Files

- `manuscript/README.md`

## Untracked Files Requiring Intentional Add Later

These files are visible to `git ls-files -o --exclude-standard` and must be intentionally reviewed before any release commit:

- None.

## Generated Or Ignored Surfaces

The validator confirms these examples are ignored by git, so generated publication and local runtime outputs can be refreshed without becoming tracked release sources by accident:

- `output/pdf/_combined_manuscript.aux`
- `output/pdf/_combined_manuscript.log`
- `output/slides/00_abstract_slides.aux`
- `output/slides/00_abstract_slides.log`
- `.active_skillference_local/dashboard.log`
- `.active_skillference_local/skilltree_auth.json`

## Key Artifact Hashes

These SHA-256 rows are local reproducibility evidence for generated bundle artifacts present at validation time. They do not imply a public archive, DOI, clean release tag, or cross-machine bitwise guarantee.

- `output/data/claims.json` | sha256: `68bcc9ec67b536dbfececa6dc2257bb12e9edabed1cfd728dad436287618ada6` | bytes: 12606
- `output/data/manuscript_variables.json` | sha256: `a7f0527bece47cf1ae985fc394dbdd1d3a40cc07fbdcfec9c8d24c17ea9b7587` | bytes: 5890
- `output/data/skilltree_project.json` | sha256: `9e905563876a45c960f1f081aa3f62b6be844058fd199b5c34e7f39b97265cce` | bytes: 3702245
- `output/figures/figure_registry.json` | sha256: `0e2fb28e68cc7ac59c80619ffecc25187ad3d1aa95e96d042af92bd8520c7ef2` | bytes: 112558
- `output/figures/curriculum_dag.png` | sha256: `32a48b3a20cb8d96c2f654c46f2c08a8f8e2045601aa6e8e3dc4a46b531ed599` | bytes: 477712
- `output/figures/dependency_strata_flow.png` | sha256: `b9f62fa2c746994e28278544a2f26992f73d37e875985727fe5c0536ebc45a04` | bytes: 232679
- `output/figures/assessment_depth_matrix.png` | sha256: `7a270ff6241e64b37aa9b7cb32cd4bcecf1aece89d2a424ccfb6617e487edb0c` | bytes: 164454
- `output/figures/curriculum_stratum_balance.png` | sha256: `0fb5eaa7b8ddb4f0d84a9a6300c8fee86a76489cce7630302a91e4ea2444090c` | bytes: 182536
- `output/figures/free_energy_descent.png` | sha256: `91706352c1b2d4168427afccf200b0e857e42751c57c25624df2ff47d11f4312` | bytes: 112930
- `output/figures/efe_decomposition.png` | sha256: `4266c883d7766007b699a3a455f4e799a1519bef1fccd6b389a2e1bcbdf43d72` | bytes: 143474
- `output/figures/planning_lookahead.png` | sha256: `2e84da490774ec8d27ccb38de699d4d038980461c87e7e9a11dfa1fbbebe55f3` | bytes: 120960
- `output/figures/predictive_coding_descent.png` | sha256: `7bda79a15ad26865ba4422dc651ae4f89695f9807832914467c5c5aea2dcb162` | bytes: 109825
- `output/figures/graph_bottlenecks.png` | sha256: `3f3b1053ad40d1989e6aea66e94dadf4c53ffcc8b03190f74b100548b72e73d9` | bytes: 195302
- `output/figures/skill_neighborhood_paths.png` | sha256: `f3be31e819a7801fd6d3f9b74d1a56912010aae9c88c7fcacb9ec92a53b1f450` | bytes: 252427
- `output/figures/semantic_prerequisite_coverage.png` | sha256: `4b0ea7d0e6b4694d950c1162954c739adb25f735ab9b6219f4f3426b78933f5a` | bytes: 121457
- `output/figures/validation_intent_mismatch_matrix.png` | sha256: `d4f17501ae017c2cf78afe83d6d3c00b7a6803ae812eeb43552ade342ced8e04` | bytes: 162117
- `output/figures/visual_evidence_contract_ladder.png` | sha256: `6f29cf8a06cc3d487baf13a0584d3586a38bef52c4771fb451e394b15db6c394` | bytes: 150049
- `output/figures/kernel_sensitivity_profiles.png` | sha256: `5ce0a4674cc6766da707589b7ecbf672ba7f469c93b224aaae945c39fa55646c` | bytes: 185805
- `output/figures/vfe_efe_skilltree_bridge.png` | sha256: `5d79e94120fa2476d71f631c67e19da0ca4f9cdf0c62efda7058c80277e7faee` | bytes: 444700
- `output/figures/scholarship_coverage.png` | sha256: `087d2476cfb2ddecd266b88c7bae934fb90798e550af553e9e19b823bc37599d` | bytes: 349999
- `output/figures/open_science_source_map.png` | sha256: `6ad68bb1ec53db990567e545a6c3cf8f188c54903d91482c3692ea9b02cb38d3` | bytes: 187702
- `output/figures/validation_surface_matrix.png` | sha256: `8c88e178a4dfad9eb75e877800736a51ebc4630bdbefb0c164de45f334383c92` | bytes: 218746
- `output/figures/scholarship_source_health.png` | sha256: `f976948d7ea67f88a81922f9af0158ca26cc14a65c9b2f407e51e40f5382d5eb` | bytes: 145649
- `output/figures/scientific_evidence_matrix.png` | sha256: `ef937feffe745741ebf6cd4348af704bb526b5c3bfe20a184b5ff582c53825b8` | bytes: 104136
- `output/figures/roadmap_risk.png` | sha256: `232a178581b839adb635bacca09f98576f0a1f2b8c1ae9eb4a9ed4ad958454ea` | bytes: 119364
- `output/figures/app_operational_snapshot.png` | sha256: `f19bd9d53485e948aab051c1e9c6b0719405cdd0f9dbaacdc30c8cae6ec2d3c4` | bytes: 184697
- `output/figures/app_official_learner_view.png` | sha256: `f95999a62f644b6c238177d1a30d200cd9480479f3ed756de7f68606c8144a2b` | bytes: 116303
- `output/figures/app_curriculum_learn_material.png` | sha256: `57f4de880810c6d8467b92e80363b0028256b9ca4ce0096a7f568f01ba119f3b` | bytes: 246197
- `output/figures/app_dependency_graph.png` | sha256: `4534faa1d92f540d5b2c95b086096c394eef6611adf3a9bab2870c697efc352b` | bytes: 279253
- `output/figures/app_runtime_deployment_matrix.png` | sha256: `aa5b8540e98a8446da6101bac0f065b4e35adbd10d48ead7ebcde9cadac56317` | bytes: 170462

## Evidence Commands

- `git status --short (excluding docs/release_readiness_inventory.md)`
- `git ls-files -o --exclude-standard`
- `git diff --check`
- `git diff --stat -- . ':(exclude)docs/release_readiness_inventory.md'`
- `uv run python scripts/validate_release_readiness_inventory.py`

## Remaining Release Blockers

- Public DOI/repository remains blocked until `git ls-remote https://github.com/ActiveInferenceInstitute/Active_Skillference.git` succeeds. Current probe: reachable but empty (no refs; not a published release).
- Live full-stack rehearsal is unblocked because `docker info` reaches the Docker/Colima daemon. Current proof status is tracked in tasks.yaml; rerun the app-ready and full-parity commands below before a public release handoff.
- Cross-vendor security audit evidence is closed as a point-in-time static Forge/GPT-5.4 review in tasks.yaml. That does not create operational security assurance, dependency/supply-chain coverage, secrets-in-git-history coverage, or dynamic runtime penetration testing.
- Branch hygiene remains open until the visible tracked and untracked project paths are intentionally staged, committed, excluded, or deferred.

Once Docker is reachable, run the app-ready proof first, then full dependency parity:

- `uv run python scripts/validate_full_app_stack.py --app-ready --skip-regenerate`
- `uv run python scripts/validate_full_app_stack.py --skip-regenerate`
