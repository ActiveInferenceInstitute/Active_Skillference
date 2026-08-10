from __future__ import annotations

_VALIDATION_SURFACE_COLUMNS = (
    "generated\nJSON",
    "negative\ncontrols",
    "manuscript\nbinding",
    "dashboard\nbinding",
    "release\ndocs",
    "SkillTree\nhandoff",
)

# Each cell names the validator/test file(s) that bind that artifact surface. A cell is
# "bound" only if every named file exists; ``None`` means the binding is genuinely not
# applicable. The matrix is therefore falsifiable: delete a gate and its cell flips to
# "n/a" instead of silently reading "bound" (a hand-coded literal could not).
_VALIDATION_SURFACE_BINDINGS: tuple[
    tuple[str, tuple[tuple[str, ...] | None, ...]], ...
] = (
    (
        "Curriculum graph",
        (
            ("scripts/build_curriculum.py", "tests/test_curriculum_graph.py"),
            ("tests/test_curriculum_graph.py",),
            ("scripts/validate_manuscript_variables.py",),
            ("tests/test_dashboard.py",),
            None,
            ("tests/test_skilltree_exporter.py",),
        ),
    ),
    (
        "Quiz quality",
        (
            ("src/curriculum/quality.py", "tests/test_curriculum_quality.py"),
            ("tests/test_curriculum_quality.py",),
            ("scripts/validate_manuscript_variables.py",),
            ("tests/test_dashboard.py",),
            None,
            ("tests/test_skilltree_exporter.py",),
        ),
    ),
    (
        "Claim provenance",
        (
            ("scripts/run_kernels.py", "tests/test_claim_support.py"),
            ("tests/test_claim_support.py",),
            ("scripts/validate_claim_support.py",),
            ("tests/test_dashboard.py",),
            None,
            ("tests/test_skilltree_exporter.py",),
        ),
    ),
    (
        "Scholarship matrix",
        (
            ("scripts/analyze_scholarship.py", "tests/test_scholarship.py"),
            ("tests/test_scholarship.py",),
            # Manuscript binding for scholarship is the claim-support gate (manuscript
            # citations vs source matrix + bib), not the figure-artifact validator, which
            # contains no scholarship logic.
            ("scripts/validate_claim_support.py", "tests/test_claim_support.py"),
            ("tests/test_dashboard.py",),
            None,
            None,
        ),
    ),
    (
        "Figure artifacts",
        (
            ("scripts/run_kernels.py", "tests/test_figures.py"),
            ("tests/test_figures.py",),
            ("scripts/validate_manuscript_artifacts.py",),
            ("tests/test_dashboard.py",),
            None,
            None,
        ),
    ),
    (
        "Web math",
        (
            None,
            ("tests/test_web_math.py",),
            ("scripts/validate_web_math.py",),
            ("tests/test_dashboard.py",),
            None,
            None,
        ),
    ),
    (
        "Release inventory",
        (
            None,
            ("tests/test_release_readiness_inventory.py",),
            None,
            None,
            (
                "scripts/validate_release_readiness_inventory.py",
                "docs/release_readiness_inventory.md",
            ),
            None,
        ),
    ),
    (
        "SkillTree handoff",
        (
            ("scripts/export_skilltree.py", "tests/test_skilltree_exporter.py"),
            ("tests/test_skilltree_exporter.py",),
            None,
            ("tests/test_dashboard.py",),
            None,
            ("scripts/validate_live_skilltree_dashboard.py",),
        ),
    ),
    (
        "Export integrity",
        (
            ("src/skilltree/summary.py", "tests/test_skilltree_model.py"),
            ("tests/test_skilltree_model.py",),
            None,
            ("tests/test_dashboard.py",),
            None,
            ("scripts/validate_live_skilltree_dashboard.py",),
        ),
    ),
    (
        "Material link safety",
        (
            ("src/curriculum/alignment.py", "tests/test_course_materials.py"),
            ("tests/test_course_materials.py",),
            None,
            ("tests/test_dashboard.py",),
            None,
            None,
        ),
    ),
)
