from __future__ import annotations

import json
import os
import stat
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LOCAL_STATE_DIR = ".active_skillference_local"
LOCAL_STATE_FILE = "skilltree_auth.json"
DEFAULT_LOCAL_ADMIN_USERNAME = "active-skillference-admin@localhost.invalid"
DEFAULT_LOCAL_ADMIN_PASSWORD = "active-skillference-local"
LOCAL_ADMIN_USERNAME_ENV = "ACTIVE_SKILLFERENCE_LOCAL_ADMIN_USERNAME"
LOCAL_ADMIN_PASSWORD_ENV = "ACTIVE_SKILLFERENCE_LOCAL_ADMIN_PASSWORD"
LOCAL_REQUEST_TIMEOUT_ENV = "ACTIVE_SKILLFERENCE_SKILLTREE_REQUEST_TIMEOUT"
DEFAULT_LOCAL_LEARNER_ID = "local-learner"
LOCAL_TOKEN_ENDPOINT = "/api/skilltree/token"
DEFAULT_LOCAL_REQUEST_TIMEOUT_SECONDS = 600.0
_DEFAULT_PORTS = {"http": 80, "https": 443}


class LocalSkillTreeAuthError(RuntimeError):
    """Raised when local SkillTree auth cannot be bootstrapped or used."""


def is_browser_login_compatible_username(username: str) -> bool:
    """Return whether ``username`` is usable in SkillTree's email login field."""
    value = username.strip()
    return "@" in value and " " not in value and "." in value.rsplit("@", 1)[-1]


@dataclass(frozen=True)
class LocalSkillTreeState:
    """Private local state for the SkillTree trusted-client bridge."""

    admin_username: str
    admin_password: str
    learner_id: str
    project_id: str
    skilltree_url: str
    client_secret: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_private_dict(self) -> dict[str, str]:
        """Serialize the state, including secrets, for the ignored state file."""
        return {
            "adminUsername": self.admin_username,
            "adminPassword": self.admin_password,
            "learnerId": self.learner_id,
            "projectId": self.project_id,
            "skilltreeUrl": self.skilltree_url,
            "clientSecret": self.client_secret,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_private_dict(cls, payload: dict[str, Any]) -> LocalSkillTreeState:
        """Build state from an on-disk JSON object."""
        required = ["adminUsername", "adminPassword", "learnerId", "projectId"]
        missing = [key for key in required if not str(payload.get(key, "")).strip()]
        if missing:
            raise LocalSkillTreeAuthError(
                f"local SkillTree auth state is missing required fields: {', '.join(missing)}"
            )
        return cls(
            admin_username=str(payload["adminUsername"]),
            admin_password=str(payload["adminPassword"]),
            learner_id=str(payload["learnerId"]),
            project_id=str(payload["projectId"]),
            skilltree_url=str(payload.get("skilltreeUrl", "")),
            client_secret=str(payload.get("clientSecret", "")),
            created_at=str(payload.get("createdAt", "")),
            updated_at=str(payload.get("updatedAt", "")),
        )


@dataclass(frozen=True)
class LocalAuthDescription:
    """Browser-safe local auth status."""

    enabled: bool
    ready: bool
    learner_id: str
    token_endpoint: str
    state_dir: str
    message: str
    browser_login_compatible: bool | None = None

    def to_public_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "ready": self.ready,
            "learnerId": self.learner_id,
            "tokenEndpoint": self.token_endpoint,
            "stateDir": self.state_dir,
            "message": self.message,
            "browserLoginCompatible": self.browser_login_compatible,
        }


@dataclass(frozen=True)
class BootstrapResult:
    """Result returned by the local SkillTree bootstrap orchestrator."""

    state: LocalSkillTreeState
    created_root: bool
    seeded: bool
    seed_summary: dict[str, int] | None
    token_verified: bool

    def to_public_dict(self) -> dict[str, object]:
        return {
            "createdRoot": self.created_root,
            "seeded": self.seeded,
            "seedSummary": self.seed_summary,
            "tokenVerified": self.token_verified,
            "learnerId": self.state.learner_id,
            "projectId": self.state.project_id,
            "skilltreeUrl": self.state.skilltree_url,
            "tokenEndpoint": LOCAL_TOKEN_ENDPOINT,
        }


def root_account_payload(state: LocalSkillTreeState) -> dict[str, object]:
    """Return SkillTree's ``UserInfo`` JSON for the local root account."""
    email = (
        state.admin_username
        if "@" in state.admin_username
        else DEFAULT_LOCAL_ADMIN_USERNAME
    )
    return {
        "firstName": "Active",
        "lastName": "Skillference",
        "nickname": "Active Skillference Local Admin",
        "email": email,
        "username": state.admin_username,
        "usernameForDisplay": state.admin_username,
        "password": state.admin_password,
        "accountNonExpired": True,
        "accountNonLocked": True,
        "credentialsNonExpired": True,
        "enabled": True,
        "emailVerified": True,
    }


def default_local_admin_username() -> str:
    """Return the configured local-development SkillTree admin username."""
    return os.environ.get(
        LOCAL_ADMIN_USERNAME_ENV, DEFAULT_LOCAL_ADMIN_USERNAME
    ).strip()


def default_local_admin_password() -> str:
    """Return the configured local-development SkillTree admin password."""
    return os.environ.get(
        LOCAL_ADMIN_PASSWORD_ENV, DEFAULT_LOCAL_ADMIN_PASSWORD
    ).strip()


def default_local_request_timeout() -> float:
    """Return the local bootstrap request timeout in seconds."""
    raw = os.environ.get(LOCAL_REQUEST_TIMEOUT_ENV, "").strip()
    if not raw:
        return DEFAULT_LOCAL_REQUEST_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError as exc:
        raise LocalSkillTreeAuthError(
            f"{LOCAL_REQUEST_TIMEOUT_ENV} must be a positive number of seconds"
        ) from exc
    if value <= 0:
        raise LocalSkillTreeAuthError(
            f"{LOCAL_REQUEST_TIMEOUT_ENV} must be a positive number of seconds"
        )
    return value


def _skilltree_origin(url: str) -> tuple[str, str, int]:
    parsed = urllib.parse.urlparse(url.strip())
    scheme = parsed.scheme.lower()
    if scheme not in _DEFAULT_PORTS or not parsed.hostname:
        raise LocalSkillTreeAuthError("SkillTree URL must be an absolute http(s) URL")
    try:
        port = parsed.port or _DEFAULT_PORTS[scheme]
    except ValueError as exc:
        raise LocalSkillTreeAuthError("SkillTree URL port is invalid") from exc
    return scheme, parsed.hostname.lower(), port


def _require_same_skilltree_origin(*, base_url: str, state_url: str) -> None:
    if _skilltree_origin(base_url) != _skilltree_origin(state_url):
        raise LocalSkillTreeAuthError(
            "configured SkillTree URL does not match bootstrapped local auth state; "
            "re-bootstrap local auth for the new SkillTree URL before issuing tokens"
        )


def new_local_state(
    *,
    skilltree_url: str,
    project_id: str,
    learner_id: str = DEFAULT_LOCAL_LEARNER_ID,
    admin_username: str | None = None,
    admin_password: str | None = None,
) -> LocalSkillTreeState:
    """Generate a fresh local-only state object."""
    now = _utc_now()
    username = admin_username or default_local_admin_username()
    password = admin_password or default_local_admin_password()
    if not username:
        raise LocalSkillTreeAuthError(
            f"{LOCAL_ADMIN_USERNAME_ENV} cannot be empty for local SkillTree bootstrap"
        )
    if not password:
        raise LocalSkillTreeAuthError(
            f"{LOCAL_ADMIN_PASSWORD_ENV} cannot be empty for local SkillTree bootstrap"
        )
    return LocalSkillTreeState(
        admin_username=username,
        admin_password=password,
        learner_id=learner_id,
        project_id=project_id,
        skilltree_url=skilltree_url.rstrip("/"),
        created_at=now,
        updated_at=now,
    )


def local_state_path(state_dir: Path) -> Path:
    return state_dir / LOCAL_STATE_FILE


def load_local_state(state_dir: Path) -> LocalSkillTreeState | None:
    """Load local auth state, returning ``None`` when it does not exist."""
    path = local_state_path(state_dir)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LocalSkillTreeAuthError(
            f"local SkillTree auth state at {path} is not valid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise LocalSkillTreeAuthError(
            f"local SkillTree auth state at {path} must be a JSON object"
        )
    return LocalSkillTreeState.from_private_dict(payload)


def save_local_state(state_dir: Path, state: LocalSkillTreeState) -> None:
    """Write local auth state with owner-only permissions where supported."""
    state_dir.mkdir(parents=True, exist_ok=True)
    try:
        state_dir.chmod(stat.S_IRWXU)
    except OSError as exc:
        raise LocalSkillTreeAuthError(
            f"unable to restrict local SkillTree state directory permissions: {state_dir}"
        ) from exc
    path = local_state_path(state_dir)
    path.write_text(
        json.dumps(state.to_private_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError as exc:
        raise LocalSkillTreeAuthError(
            f"unable to restrict local SkillTree auth state file permissions: {path}"
        ) from exc


def describe_local_auth(
    *,
    enabled: bool,
    state_dir: Path,
    learner_id: str,
    project_id: str,
) -> LocalAuthDescription:
    """Return browser-safe readiness for the local trusted-client bridge."""
    if not enabled:
        return LocalAuthDescription(
            enabled=False,
            ready=False,
            learner_id=learner_id,
            token_endpoint=LOCAL_TOKEN_ENDPOINT,
            state_dir=str(state_dir),
            message="Local SkillTree auth is disabled.",
        )
    try:
        state = load_local_state(state_dir)
    except LocalSkillTreeAuthError as exc:
        return LocalAuthDescription(
            enabled=True,
            ready=False,
            learner_id=learner_id,
            token_endpoint=LOCAL_TOKEN_ENDPOINT,
            state_dir=str(state_dir),
            message=str(exc),
        )
    if state is None:
        return LocalAuthDescription(
            enabled=True,
            ready=False,
            learner_id=learner_id,
            token_endpoint=LOCAL_TOKEN_ENDPOINT,
            state_dir=str(state_dir),
            message=(
                "Local SkillTree auth has not been bootstrapped. Run "
                "./scripts/run_learning_dashboard.sh or "
                "uv run python scripts/bootstrap_local_skilltree.py."
            ),
        )
    if state.project_id != project_id:
        return LocalAuthDescription(
            enabled=True,
            ready=False,
            learner_id=learner_id,
            token_endpoint=LOCAL_TOKEN_ENDPOINT,
            state_dir=str(state_dir),
            message=(
                f"Local auth state is for project {state.project_id!r}, "
                f"not {project_id!r}."
            ),
            browser_login_compatible=is_browser_login_compatible_username(
                state.admin_username
            ),
        )
    if not state.client_secret.strip():
        return LocalAuthDescription(
            enabled=True,
            ready=False,
            learner_id=learner_id,
            token_endpoint=LOCAL_TOKEN_ENDPOINT,
            state_dir=str(state_dir),
            message=(
                "Local auth state exists, but the SkillTree trusted-client secret "
                "has not been stored. Re-run the local SkillTree bootstrap."
            ),
            browser_login_compatible=is_browser_login_compatible_username(
                state.admin_username
            ),
        )
    return LocalAuthDescription(
        enabled=True,
        ready=True,
        learner_id=state.learner_id,
        token_endpoint=LOCAL_TOKEN_ENDPOINT,
        state_dir=str(state_dir),
        message="Local SkillTree trusted-client bridge is ready.",
        browser_login_compatible=is_browser_login_compatible_username(
            state.admin_username
        ),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
