from __future__ import annotations

from typing import Any

from src.dashboard.artifacts import (
    artifact_inventory,
    load_claims_summary,
    load_course_materials_summary,
    load_curriculum_diagnostics,
    load_curriculum_stats,
    load_figure_table_companions,
    load_scholarship_health_network,
    load_skilltree_project,
)
from src.dashboard.config import DashboardConfig, DashboardPayload
from src.dashboard.graph_analysis import analyze_project_graph
from src.dashboard.status import check_skilltree_status
from src.skilltree.deployment_matrix import skilltree_deployment_matrix
from src.skilltree.local_auth import (
    DEFAULT_LOCAL_STATE_DIR,
    LocalSkillTreeAuthError,
    SkillTreeSessionClient,
    load_local_state,
)

DEFERRED_LIVE_PARITY_REASON = (
    "live dependency parity was deferred for first paint; "
    "request /api/status without defer_live to check it"
)


def dashboard_payload(
    config: DashboardConfig,
    *,
    defer_live: bool = False,
) -> DashboardPayload:
    """Build the combined runtime payload the browser consumes.

    ``defer_live`` skips only the live SkillTree parity call, which logs in as
    the local admin and pulls the whole live dependency graph — seconds of work
    that otherwise blocks every panel on first paint. The default is unchanged,
    so validators and proof artifacts still get a real parity check.
    """
    project = load_skilltree_project(config.project_root)
    public_config = config.to_public_dict()
    skilltree_status = check_skilltree_status(config.skilltree_url)
    public_skilltree = public_config.get("skilltree", {})
    local_auth = (
        public_skilltree.get("localAuth", {})
        if isinstance(public_skilltree, dict)
        else {}
    )
    authenticator_configured = (
        public_skilltree.get("authenticatorConfigured") is True
        if isinstance(public_skilltree, dict)
        else False
    )
    return {
        "config": public_config,
        "skilltree": skilltree_status,
        "skilltreeDeployment": skilltree_deployment_matrix(
            local_auth=local_auth if isinstance(local_auth, dict) else {},
            service_available=skilltree_status.get("available") is True,
            authenticator_configured=authenticator_configured,
        ),
        "project": project,
        "liveSkilltree": deferred_live_skilltree_summary(project)
        if defer_live
        else live_skilltree_summary(config, project),
        "graphAnalysis": analyze_project_graph(project),
        "claims": load_claims_summary(config.project_root),
        "courseMaterials": load_course_materials_summary(config.project_root),
        "curriculum": load_curriculum_stats(config.project_root),
        "curriculumDiagnostics": load_curriculum_diagnostics(config.project_root),
        "scholarshipHealthNetwork": load_scholarship_health_network(
            config.project_root
        ),
        "figureCompanions": load_figure_table_companions(config.project_root),
        "artifacts": artifact_inventory(config.project_root),
    }


def deferred_live_skilltree_summary(project: dict[str, Any]) -> dict[str, object]:
    """Return the explicit not-checked shape used when parity is deferred."""
    counts = project.get("counts", {})
    return {
        "checked": False,
        "deferred": True,
        "reason": DEFERRED_LIVE_PARITY_REASON,
        "expectedDependencies": counts.get("dependencies", 0)
        if isinstance(counts, dict)
        else 0,
    }


def live_skilltree_summary(
    config: DashboardConfig,
    project: dict[str, Any],
) -> dict[str, object]:
    """Return browser-safe live SkillTree admin/count parity when local auth is ready."""
    from src.skilltree.client import SkillTreeClientError
    from src.skilltree.dependency_reconciler import (
        dependency_pairs_from_payload,
        summarize_dependency_parity,
    )

    counts = project.get("counts", {})
    dependencies = project.get("dependencies", [])
    expected_dependencies = (
        counts.get("dependencies", 0) if isinstance(counts, dict) else 0
    )
    if not project.get("available"):
        return {
            "checked": False,
            "reason": "exported SkillTree project is unavailable",
            "expectedDependencies": expected_dependencies,
        }
    if not isinstance(dependencies, list):
        return {
            "checked": False,
            "reason": "exported SkillTree dependencies payload is not a list",
            "expectedDependencies": expected_dependencies,
        }
    local_auth = config.local_auth
    if not (local_auth.get("enabled") and local_auth.get("ready")):
        return {
            "checked": False,
            "reason": str(local_auth.get("message") or "local auth is not ready"),
            "expectedDependencies": expected_dependencies,
        }
    state_dir = config.local_state_dir or config.project_root / DEFAULT_LOCAL_STATE_DIR
    try:
        state = load_local_state(state_dir)
        if state is None:
            raise LocalSkillTreeAuthError("local SkillTree auth state is missing")
        expected_pairs = dependency_pairs_from_payload(dependencies, strict=False)
        client = SkillTreeSessionClient(
            config.skilltree_url,
            config.project_id,
            timeout=15.0,
        )
        client.login(state.admin_username, state.admin_password)
        live_pairs = client.live_dependency_pairs()
        parity = summarize_dependency_parity(
            expected_pairs=expected_pairs,
            live_pairs=live_pairs,
        )
        return {
            **parity,
            "skills": client.live_skill_count(),
            "subjects": client.live_subject_count(),
        }
    except (LocalSkillTreeAuthError, SkillTreeClientError) as exc:
        return {
            "checked": False,
            "reason": str(exc),
            "expectedDependencies": expected_dependencies,
        }
