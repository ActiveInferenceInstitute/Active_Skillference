"""Configuration for the local Active Skillference learner dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

from src.net_guard import is_loopback_host as _is_loopback_host
from src.project_identity import SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME
from src.project_paths import resolve_project_root
from src.skilltree.local_auth import (
    DEFAULT_LOCAL_ADMIN_USERNAME,
    DEFAULT_LOCAL_LEARNER_ID,
    DEFAULT_LOCAL_STATE_DIR,
    LOCAL_TOKEN_ENDPOINT,
    describe_local_auth,
)


def _is_dashboard_local_asset_url(module_url: str, dashboard_url: str) -> bool:
    value = module_url.strip()
    if value.startswith("/assets/"):
        return True
    parsed = urlparse(value)
    if not parsed.scheme and not parsed.netloc and value.startswith("assets/"):
        return True
    dashboard = urlparse(dashboard_url)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.scheme == dashboard.scheme
        and parsed.netloc == dashboard.netloc
        and parsed.path.startswith("/assets/")
    )


PROJECT_ID = SKILLTREE_PROJECT_ID
PROJECT_NAME = SKILLTREE_PROJECT_NAME
DEFAULT_SKILLTREE_URL = "http://localhost:8080"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_AUTHENTICATOR = ""
SKILLS_CLIENT_MODULE_URL = "/assets/vendor/skills-client-js.esm.min.js"


@dataclass(frozen=True)
class DashboardConfig:
    """Runtime settings for the local dashboard shell."""

    project_root: Path
    skilltree_url: str = DEFAULT_SKILLTREE_URL
    project_id: str = PROJECT_ID
    project_name: str = PROJECT_NAME
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    authenticator: str = DEFAULT_AUTHENTICATOR
    skills_client_module_url: str = SKILLS_CLIENT_MODULE_URL
    local_auth_enabled: bool = False
    local_state_dir: Path | None = None
    learner_id: str = DEFAULT_LOCAL_LEARNER_ID

    def __post_init__(self) -> None:
        if not self.skilltree_url.strip():
            raise ValueError("skilltree_url must be non-empty")
        if not self.project_id.strip():
            raise ValueError("project_id must be non-empty")
        if not self.project_name.strip():
            raise ValueError("project_name must be non-empty")
        if not self.host.strip():
            raise ValueError("host must be non-empty")
        # Defense-in-depth: when the local token bridge is enabled it issues bearer
        # tokens, so it must never be reachable off-host. A non-loopback bind would
        # turn the token endpoint into a LAN credential dispenser, so we fail closed
        # here rather than relying only on the request-time Host/Origin gate.
        if self.local_auth_enabled and not _is_loopback_host(self.host):
            raise ValueError(
                "host must be a loopback address (localhost, 127.0.0.0/8, or ::1) "
                "when local_auth_enabled is True"
            )
        if self.local_auth_enabled and not _is_dashboard_local_asset_url(
            self.skills_client_module_url, f"http://{self.host}:{self.port}"
        ):
            raise ValueError(
                "local auth requires a same-origin dashboard asset for "
                "skills_client_module_url"
            )
        if self.port <= 0:
            raise ValueError("port must be positive")
        if not self.learner_id.strip():
            raise ValueError("learner_id must be non-empty")
        object.__setattr__(self, "project_root", self.project_root.resolve())
        object.__setattr__(self, "skilltree_url", self.skilltree_url.rstrip("/"))
        state_dir = self.local_state_dir or Path(DEFAULT_LOCAL_STATE_DIR)
        if not state_dir.is_absolute():
            state_dir = self.project_root / state_dir
        object.__setattr__(self, "local_state_dir", state_dir.resolve())

    @property
    def dashboard_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def skilltree_status_url(self) -> str:
        return f"{self.skilltree_url}/public/status"

    @property
    def local_auth(self) -> dict[str, object]:
        return describe_local_auth(
            enabled=self.local_auth_enabled,
            state_dir=self.local_state_dir
            or self.project_root / DEFAULT_LOCAL_STATE_DIR,
            learner_id=self.learner_id,
            project_id=self.project_id,
        ).to_public_dict()

    @property
    def effective_authenticator(self) -> str:
        if self.authenticator:
            return self.authenticator
        local_auth = self.local_auth
        if local_auth["enabled"] and local_auth["ready"]:
            return f"{self.dashboard_url}{LOCAL_TOKEN_ENDPOINT}"
        return ""

    def to_public_dict(self) -> dict[str, object]:
        """Return the browser-safe runtime configuration."""
        authenticator = self.effective_authenticator
        local_auth = self.local_auth
        return {
            "project": {
                "id": self.project_id,
                "name": self.project_name,
            },
            "dashboard": {
                "host": self.host,
                "port": self.port,
                "url": self.dashboard_url,
            },
            "skilltree": {
                "url": self.skilltree_url,
                "statusUrl": self.skilltree_status_url,
                "authenticator": authenticator,
                "authenticatorConfigured": bool(authenticator),
                "clientModuleUrl": self.skills_client_module_url,
                "localAuth": local_auth,
                "localDevelopment": {
                    "defaultUsername": DEFAULT_LOCAL_ADMIN_USERNAME,
                    "defaultPassword": "",
                    "defaultPasswordAvailable": False,
                    "resetCommand": (
                        "uv run python scripts/reset_local_skilltree.py "
                        "--confirm-local-reset"
                    ),
                    "showCredentialsCommand": (
                        "uv run python scripts/bootstrap_local_skilltree.py "
                        "--show-local-credentials"
                    ),
                    "warning": (
                        "Local-development credentials only. Shared or deployed "
                        "SkillTree instances must replace these defaults."
                    ),
                },
                "links": {
                    "learnerDashboard": self.dashboard_url,
                    "skilltreeLogin": (
                        f"{self.skilltree_url}/skills-login"
                        "?redirect=/progress-and-rankings"
                    ),
                    "dashboard": self.skilltree_url,
                    "admin": f"{self.skilltree_url}/administrator",
                    "training": f"{self.skilltree_url}/training",
                },
            },
        }


def make_dashboard_config(
    *,
    project_root: Path | None = None,
    skilltree_url: str = DEFAULT_SKILLTREE_URL,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    project_id: str = PROJECT_ID,
    project_name: str = PROJECT_NAME,
    authenticator: str = DEFAULT_AUTHENTICATOR,
    skills_client_module_url: str = SKILLS_CLIENT_MODULE_URL,
    local_auth_enabled: bool = False,
    local_state_dir: Path | None = None,
    learner_id: str = DEFAULT_LOCAL_LEARNER_ID,
) -> DashboardConfig:
    """Build the default dashboard config, resolving the project root once."""
    root = project_root or resolve_project_root("src")
    return DashboardConfig(
        project_root=root,
        skilltree_url=skilltree_url,
        project_id=project_id,
        project_name=project_name,
        host=host,
        port=port,
        authenticator=authenticator,
        skills_client_module_url=skills_client_module_url,
        local_auth_enabled=local_auth_enabled,
        local_state_dir=local_state_dir,
        learner_id=learner_id,
    )


class DashboardPayload(TypedDict):
    """Browser-safe combined payload from :func:`src.dashboard.payload.dashboard_payload`."""

    config: dict[str, object]
    skilltree: dict[str, object]
    skilltreeDeployment: dict[str, object]
    project: dict[str, object]
    liveSkilltree: dict[str, object]
    graphAnalysis: dict[str, object]
    claims: dict[str, object]
    courseMaterials: dict[str, object]
    curriculum: dict[str, object]
    curriculumDiagnostics: dict[str, object]
    scholarshipHealthNetwork: dict[str, object]
    figureCompanions: dict[str, object]
    artifacts: list[dict[str, object]]
