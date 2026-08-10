"""National-security context skills for SkillTree delivery posture."""

from __future__ import annotations

from collections.abc import Iterable

from src.curriculum._ext_helpers import _C, _q, _s
from src.curriculum.model import Skill


def _dedupe(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _security_skill(
    index: int,
    name: str,
    objective: str,
    focus: str,
    anchor: str,
    related: tuple[str, ...] = (),
) -> Skill:
    skill_id = f"natsec_computation_{index:02d}"
    prior = f"natsec_computation_{index - 1:02d}" if index > 1 else ""
    return _s(
        skill_id,
        name,
        _C,
        objective,
        (
            f"{focus} Learners practice separating platform provenance from endorsement, "
            "identifying which evidence belongs to this repository, and naming the "
            "operator-owned controls still required before a shared SkillTree deployment."
        ),
        _dedupe((anchor, prior)),
        _q(
            f"What is the safest interpretation of {name}?",
            [
                "It documents a boundary between educational evidence and operator-owned deployment controls.",
                "It proves the curriculum is endorsed by the platform's original author.",
                "It lets local Docker auth replace organization-owned identity policy.",
            ],
            0,
        ),
        tags=("national-security", "skilltree", "delivery-posture"),
        related=related,
    )


_NATSEC_COMPUTATION: list[Skill] = [
    _security_skill(
        1,
        "NSA SkillTree Provenance Review",
        "Explain why SkillTree's NSA-origin open-source provenance is attribution, not endorsement.",
        "SkillTree provenance review names the platform source while keeping curriculum authorship and assurance claims separate.",
        "comp_skilltree_export",
        ("os_computation_03",),
    ),
    _security_skill(
        2,
        "Trusted-Client Boundary Review",
        "Trace the dashboard token bridge without moving SkillTree secrets into browser assets.",
        "Trusted-client boundary review keeps local token exchange server-side and treats static artifacts as public inspection surfaces.",
        "os_computation_07",
        ("front_comp_runtime_secret_hygiene",),
    ),
    _security_skill(
        3,
        "Zero-Trust Deployment Framing",
        "List the identity, device, network and telemetry decisions left to an operator deployment.",
        "Zero-trust framing prevents a local no-login learner shell from being mistaken for enterprise access control.",
        "audit_computation_04",
        ("front_comp_dashboard_observability",),
    ),
    _security_skill(
        4,
        "Supply-Chain Evidence Packet",
        "Identify which generated artifacts would need SBOM, signature and provenance evidence in a release.",
        "Supply-chain packet review connects generated JSON, figures, PDF and Docker images to build attestations rather than prose confidence.",
        "audit_computation_01",
        ("front_comp_replay_harness",),
    ),
    _security_skill(
        5,
        "APT-Aware Misuse Boundary",
        "Describe how a training platform can be abused through credentials, dependencies or misleading completion claims.",
        "APT-aware misuse review treats learner-state, admin access and dependency ingestion as possible adversary paths.",
        "audit_computation_02",
        ("cog_precision_attack",),
    ),
    _security_skill(
        6,
        "Learner-Data Classification Review",
        "Classify which local and SkillTree-held records may become sensitive in shared deployments.",
        "Learner-data review separates public curriculum artifacts from SkillTree-owned progress, ranking, quiz and approval records.",
        "audit_computation_03",
        ("os_computation_04",),
    ),
    _security_skill(
        7,
        "Incident Evidence Readiness",
        "Name logs, generated artifacts and replay commands needed during a deployment investigation.",
        "Incident readiness review keeps rebuild commands, source-health status, dashboard access and SkillTree status inspectable during triage.",
        "front_comp_replay_harness",
        ("audit_applications_03",),
    ),
    _security_skill(
        8,
        "Security-Posture Capstone",
        "Assemble a bounded review packet for SkillTree deployment context without claiming certification.",
        "The capstone asks learners to audit provenance, trusted-client exchange, generated artifacts, source roles and deployment limits together.",
        "audit_computation_04",
        ("audit_applications_04",),
    ),
]
