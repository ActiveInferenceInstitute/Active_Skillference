"""Static frontier-source contract for scholarship gap reporting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrontierSourceContract:
    """One expected high-value scholarship frontier source."""

    area: str
    source_key: str
    claim_class: str
    required_claim_support_types: tuple[str, ...]
    requires_boundary: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON data for the contract row."""
        return {
            "area": self.area,
            "claimClass": self.claim_class,
            "requiresBoundary": self.requires_boundary,
            "requiredClaimSupportTypes": list(self.required_claim_support_types),
            "sourceKey": self.source_key,
        }


FRONTIER_SOURCE_CONTRACTS: tuple[FrontierSourceContract, ...] = (
    FrontierSourceContract(
        "formal_provenance_overview",
        "groth2013prov_overview",
        "formal provenance standard",
        ("literature",),
    ),
    FrontierSourceContract(
        "formal_provenance_model",
        "moreau2013prov_dm",
        "formal provenance standard",
        ("literature",),
    ),
    FrontierSourceContract(
        "workflow_run_rocrate",
        "leo2024workflow_run_rocrate",
        "workflow provenance standard",
        ("literature",),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "knowledge_space_foundation",
        "doignon1985knowledge_spaces",
        "knowledge-space theory",
        ("literature",),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "learning_space_foundation",
        "falmagne2011learning_spaces",
        "learning-space theory",
        ("literature",),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "curriculum_aware_cognitive_diagnosis",
        "fu2025curriculum_aware_gncd",
        "curriculum-aware cognitive diagnosis",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "active_inference_teacher_development",
        "hugo2026teacher_development",
        "active-inference pedagogy",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "pedagogy_active_learning",
        "freeman2014activelearning",
        "pedagogy",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "pedagogy_cognitive_engagement",
        "chi2014icap",
        "pedagogy",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "pedagogy_retrieval_practice",
        "roediger2006testenhanced",
        "pedagogy",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "assessment_design",
        "mislevy2003ecd",
        "assessment design",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "pedagogy_constructive_alignment",
        "biggs1996constructive_alignment",
        "pedagogy",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "pedagogy_formative_assessment",
        "black1998assessment",
        "pedagogy",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "pedagogy_formative_feedback",
        "shute2008formative_feedback",
        "pedagogy",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "design_based_research_collective",
        "designbasedresearchcollective2003",
        "design-based evaluation",
        ("scope_limit",),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "design_based_research_context",
        "barab2004design_based",
        "design-based evaluation",
        ("scope_limit",),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "reproducible_computational_workflow",
        "sandve2013reproducible",
        "reproducibility/open science",
        ("delivery", "literature"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "scientific_computing_practice",
        "wilson2014scientific_computing",
        "reproducibility/open science",
        ("delivery", "literature"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "reproducible_science_boundary",
        "munafo2017reproducible_science",
        "reproducibility/open science",
        ("delivery", "literature"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "reproducible_open_data",
        "wilkinson2016fair",
        "reproducibility/open science",
        ("delivery", "literature"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "transparent_open_science",
        "nosek2015top",
        "reproducibility/open science",
        ("delivery", "literature"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "software_citation_principles",
        "smith2016softwarecitation",
        "software citation metadata",
        ("delivery", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "citation_file_metadata",
        "citationfileformat2026",
        "software citation metadata",
        ("delivery", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "codemeta_metadata_schema",
        "codemeta2026schema",
        "software metadata schema",
        ("delivery", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "repository_archive_workflow",
        "github2026citingcontent",
        "repository archive workflow",
        ("delivery", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "zenodo_doi_workflow",
        "zenodo2026github",
        "DOI release workflow",
        ("delivery", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "license_notice_boundary",
        "reuse2024spec",
        "license notice standard",
        ("delivery", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "reactive_message_passing_scalability",
        "bagaev2023reactive_message_passing",
        "scalable Bayesian message passing",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "rxinfer_reactive_software",
        "bagaev2023rxinfer",
        "reactive Bayesian inference software",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "coupled_free_energy_robustness",
        "nelson2025coupled_free_energy",
        "coupled variational free energy",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "active_predictive_coding_frontier",
        "rao2024active_predictive_coding",
        "active predictive coding",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "dcpc_predictive_coding_scaling",
        "sennesh2024dcpc",
        "predictive-coding scalability",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "secure_development_posture",
        "nist2022ssdf",
        "security/release posture",
        ("scope_limit",),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "accessibility_standard",
        "w3c2023wcag22",
        "visualization/accessibility",
        ("literature",),
    ),
    FrontierSourceContract(
        "course_material_provenance",
        "activeinferenceinstitute2026cognitive",
        "course-material provenance",
        ("literature",),
    ),
    FrontierSourceContract(
        "responsible_learning_analytics",
        "sclater2015learning_analytics_code",
        "responsible learning analytics",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "pilot_feasibility_reporting",
        "eldridge2016consort_pilot",
        "pilot and feasibility reporting",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "intervention_replication_reporting",
        "hoffmann2014tidier",
        "intervention replication reporting",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "knowledge_tracing_comparison",
        "piech2015deep_knowledge_tracing",
        "learner-state modelling comparison",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "q_matrix_diagnostic_boundary",
        "tao2024q_matrix_constraint",
        "cognitive diagnosis and Q-matrix boundary",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "application_scope_evidence_status",
        "hodson2024empirical",
        "application evidence status",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "active_inference_open_science_infrastructure",
        "activeinferenceinstitute2026website",
        "Active Inference open-science infrastructure",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "information_theory_foundation",
        "shannon1948mathematical",
        "information-theory foundation",
        ("literature",),
    ),
    FrontierSourceContract(
        "variational_bayes_foundation",
        "beal2003variational",
        "variational Bayesian foundation",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
    FrontierSourceContract(
        "helmholtz_inference_foundation",
        "dayan1995helmholtz",
        "recognition and generative-model inference",
        ("literature", "scope_limit"),
        requires_boundary=True,
    ),
)
