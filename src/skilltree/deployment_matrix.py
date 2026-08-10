from __future__ import annotations

from collections.abc import Mapping


def skilltree_deployment_matrix(
    *,
    local_auth: Mapping[str, object],
    service_available: bool,
    authenticator_configured: bool,
) -> dict[str, object]:
    local_auth_enabled = local_auth.get("enabled") is True
    local_auth_ready = local_auth.get("ready") is True
    browser_login_compatible = local_auth.get("browserLoginCompatible") is True
    local_message = str(local_auth.get("message") or "")
    modes = [
        {
            "browserExposure": "login URL and local-development defaults only",
            "evidence": (
                "ready"
                if service_available and browser_login_compatible
                else local_message
                or "SkillTree service or browser-compatible local credentials unavailable"
            ),
            "id": "local_form_bootstrap",
            "label": "Local FORM bootstrap",
            "secretBoundary": "Password is shown only as a development default; no bearer token is embedded in JS.",
            "status": (
                "ready" if service_available and browser_login_compatible else "blocked"
            ),
        },
        {
            "browserExposure": "sanitized local-auth readiness and reset command",
            "evidence": (
                "ignored local state present"
                if local_auth_enabled and not local_auth_ready
                else "no stale ignored-state blocker reported"
            ),
            "id": "ignored_local_state",
            "label": "Ignored local state",
            "secretBoundary": "Local state directory, client secret and admin password stay server-side.",
            "status": "blocked"
            if local_auth_enabled and not local_auth_ready
            else "ready",
        },
        {
            "browserExposure": "same-origin token endpoint URL, never the token value",
            "evidence": (
                "trusted-client bridge configured"
                if local_auth_ready and authenticator_configured
                else local_message or "trusted-client bridge not configured"
            ),
            "id": "token_backed_admin_seeding",
            "label": "Token-backed admin seeding",
            "secretBoundary": "Client secret and admin credentials are exchanged server-side only.",
            "status": (
                "ready" if local_auth_ready and authenticator_configured else "blocked"
            ),
        },
        {
            "browserExposure": "external SkillTree URL and authenticator route only",
            "evidence": (
                "external SkillTree service reachable"
                if service_available
                else "SkillTree status endpoint unavailable from dashboard host"
            ),
            "id": "externally_operated_skilltree",
            "label": "Externally operated SkillTree",
            "secretBoundary": "Deployment-owned identity provider remains outside the dashboard payload.",
            "status": "ready" if service_available else "blocked",
        },
    ]
    ready_modes = sum(1 for mode in modes if mode["status"] == "ready")
    return {
        "modes": modes,
        "summary": {
            "browserSafe": True,
            "configuredAuthenticator": authenticator_configured,
            "modes": len(modes),
            "readyModes": ready_modes,
            "serviceAvailable": service_available,
        },
    }
