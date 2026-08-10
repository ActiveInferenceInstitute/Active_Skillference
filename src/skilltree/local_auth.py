"""Local-only SkillTree FORM auth bootstrap and trusted-client token bridge.

This module intentionally keeps credentials server-side. It creates or reuses a
single local root/admin account, stores local-only secrets in an ignored state
directory, and exchanges the SkillTree project trusted-client secret for learner
tokens. Browser code only ever sees the dashboard token endpoint path.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import replace
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

from src.net_guard import is_loopback_host
from src.skilltree.admin_ops import (
    dependency_assign_path,
    dependency_payload,
    project_create_body,
    project_create_path,
    skill_create_path,
    skill_payload,
    subject_create_path,
    subject_payload,
)
from src.skilltree.local_auth_state import (
    DEFAULT_LOCAL_ADMIN_PASSWORD,
    DEFAULT_LOCAL_ADMIN_USERNAME,
    DEFAULT_LOCAL_LEARNER_ID,
    DEFAULT_LOCAL_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_LOCAL_STATE_DIR,
    LOCAL_ADMIN_PASSWORD_ENV,
    LOCAL_ADMIN_USERNAME_ENV,
    LOCAL_REQUEST_TIMEOUT_ENV,
    LOCAL_STATE_FILE,
    LOCAL_TOKEN_ENDPOINT,
    BootstrapResult,
    LocalAuthDescription,
    LocalSkillTreeAuthError,
    LocalSkillTreeState,
    _require_same_skilltree_origin,
    _skilltree_origin,
    _utc_now,
    default_local_admin_password,
    default_local_admin_username,
    default_local_request_timeout,
    describe_local_auth,
    is_browser_login_compatible_username,
    load_local_state,
    local_state_path,
    new_local_state,
    root_account_payload,
    save_local_state,
)
from src.skilltree.model import (
    Quiz,
    QuizQuestion,
    SkillDependency,
    SkillTreeProject,
    SkillTreeSkill,
    SkillTreeSubject,
)
from src.skilltree.seeder import seed
from src.skilltree.transport import SkillTreeClientError, quiz_question_count

# Backwards-compatible re-export surface pulled from local_auth_state so downstream
# callers can import these names from src.skilltree.local_auth. Declared explicitly
# so the linter treats them as public API rather than unused imports.
__all__ = [
    "DEFAULT_LOCAL_ADMIN_USERNAME",
    "DEFAULT_LOCAL_REQUEST_TIMEOUT_SECONDS",
    "DEFAULT_LOCAL_STATE_DIR",
    "LOCAL_ADMIN_USERNAME_ENV",
    "LOCAL_REQUEST_TIMEOUT_ENV",
    "LOCAL_STATE_FILE",
    "LOCAL_TOKEN_ENDPOINT",
    "LocalAuthDescription",
    "_skilltree_origin",
    "default_local_admin_password",
    "default_local_admin_username",
    "describe_local_auth",
]


class SkillTreeSessionClient:
    """Cookie/XSRF-aware SkillTree client for FORM-mode admin sessions."""

    def __init__(
        self,
        base_url: str,
        project_id: str,
        *,
        timeout: float = 120.0,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url must be non-empty")
        if not project_id.strip():
            raise ValueError("project_id must be non-empty")
        self.base_url = base_url.rstrip("/")
        self.project_id = project_id
        self.timeout = timeout
        self.cookie_jar = CookieJar()
        self._dependency_pairs: set[tuple[str, str]] | None = None
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    # ------------------------------------------------------------------ #
    # transport
    # ------------------------------------------------------------------ #
    def request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        form_body: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Issue a request and parse JSON objects or strings."""
        _, _, raw = self.request_raw(
            method,
            path,
            json_body=json_body,
            form_body=form_body,
            headers=headers,
        )
        return json.loads(raw) if raw.strip() else {}

    def request_text(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        form_body: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Issue a request and return the decoded response body."""
        _, _, raw = self.request_raw(
            method,
            path,
            json_body=json_body,
            form_body=form_body,
            headers=headers,
        )
        return raw

    def request_raw(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        form_body: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], str]:
        """Issue a request and return ``(status, headers, body)``."""
        if json_body is not None and form_body is not None:
            raise ValueError("json_body and form_body are mutually exclusive")
        url = f"{self.base_url}{path}"
        body: bytes | None = None
        request_headers = {"Accept": "application/json", **(headers or {})}
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        elif form_body is not None:
            body = urllib.parse.urlencode(form_body).encode("utf-8")
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"
        if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            token = self.xsrf_token
            if token:
                request_headers.setdefault("X-XSRF-TOKEN", token)
        request = urllib.request.Request(
            url,
            data=body,
            headers=request_headers,
            method=method.upper(),
        )
        try:
            if os.environ.get("ACTIVE_SKILLFERENCE_HTTP_TRACE") == "1":
                print(f"SkillTree HTTP --> {method.upper()} {path}", file=sys.stderr)
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
                status = response.status
                response_headers = dict(response.headers.items())
            if os.environ.get("ACTIVE_SKILLFERENCE_HTTP_TRACE") == "1":
                print(
                    f"SkillTree HTTP <-- {status} {method.upper()} {path}",
                    file=sys.stderr,
                )
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            if os.environ.get("ACTIVE_SKILLFERENCE_HTTP_TRACE") == "1":
                print(
                    f"SkillTree HTTP <-- {exc.code} {method.upper()} {path}",
                    file=sys.stderr,
                )
            raise SkillTreeClientError(
                f"{method.upper()} {path} failed with status {exc.code}",
                status=exc.code,
                body=raw,
            ) from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network dependent
            raise SkillTreeClientError(
                f"{method.upper()} {path} transport error: {exc.reason}"
            ) from exc
        except TimeoutError as exc:  # pragma: no cover - timing dependent
            raise SkillTreeClientError(
                f"{method.upper()} {path} timed out after {self.timeout:.0f}s"
            ) from exc
        return status, response_headers, raw

    @property
    def xsrf_token(self) -> str:
        """Return the current Spring XSRF cookie value, if available."""
        for cookie in self.cookie_jar:
            if cookie.name == "XSRF-TOKEN" and cookie.value is not None:
                return urllib.parse.unquote(cookie.value)
        return ""

    def prime_session(self) -> None:
        """Fetch the SPA root to collect initial cookies, including XSRF."""
        try:
            self.request_text(
                "GET", "/", headers={"Accept": "text/html,application/json"}
            )
        except SkillTreeClientError:
            # Some test servers do not provide the SPA route; public config is
            # enough to prove connectivity and may set cookies in live service.
            self.request_json("GET", "/public/config")

    # ------------------------------------------------------------------ #
    # auth/bootstrap endpoints
    # ------------------------------------------------------------------ #
    def public_config(self) -> dict[str, Any]:
        payload = self.request_json("GET", "/public/config")
        if not isinstance(payload, dict):
            raise LocalSkillTreeAuthError(
                "SkillTree /public/config returned non-object JSON"
            )
        return payload

    def create_root_account(self, state: LocalSkillTreeState) -> None:
        self.prime_session()
        self.request_json(
            "PUT", "/createRootAccount", json_body=root_account_payload(state)
        )

    def login(self, username: str, password: str) -> None:
        self.prime_session()
        self.request_json(
            "POST",
            "/performLogin",
            form_body={"username": username, "password": password},
        )

    def _live_project_count(self, field: str) -> int:
        """Return an integer count ``field`` from the live admin project response.

        SkillTree wraps some admin responses in ``{"data": {...}}`` and returns others
        flat, so accept both.
        """
        payload = self.request_json("GET", f"/admin/projects/{self.project_id}")
        if isinstance(payload, dict):
            data = payload.get("data")
            source = data if isinstance(data, dict) else payload
            value = source.get(field)
            if isinstance(value, int):
                return value
        raise LocalSkillTreeAuthError(
            f"SkillTree admin project response for {self.project_id!r} carried no "
            f"integer {field}"
        )

    def live_skill_count(self) -> int:
        """Return the live ``numSkills`` SkillTree reports for this project."""
        return self._live_project_count("numSkills")

    def live_subject_count(self) -> int:
        """Return the live ``numSubjects`` SkillTree reports for this project."""
        return self._live_project_count("numSubjects")

    def get_project_client_secret(self) -> str:
        raw = self.request_text(
            "GET", f"/admin/projects/{self.project_id}/clientSecret"
        )
        return _parse_secret_response(raw)

    def reset_project_client_secret(self) -> str:
        payload = self.request_json(
            "POST", f"/admin/projects/{self.project_id}/resetClientSecret"
        )
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, dict) and str(data.get("clientSecret", "")).strip():
                return str(data["clientSecret"])
            if str(payload.get("clientSecret", "")).strip():
                return str(payload["clientSecret"])
        return self.get_project_client_secret()

    def request_json_allowing_existing(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Request JSON, treating SkillTree duplicate-create errors as idempotent.

        The local bootstrap command is intentionally re-runnable. SkillTree returns
        400/409 responses for already-created projects, skills, quizzes, and
        learning paths; those are acceptable when the requested object already has
        the desired identity.
        """
        try:
            return self.request_json(method, path, json_body=json_body)
        except SkillTreeClientError as exc:
            if _is_existing_resource_error(exc):
                return {"success": True, "alreadyExisted": True}
            raise

    # ------------------------------------------------------------------ #
    # seed-compatible admin methods
    # ------------------------------------------------------------------ #
    def create_project(self, name: str) -> Any:
        return self.request_json_allowing_existing(
            "POST",
            project_create_path(self.project_id),
            json_body=project_create_body(self.project_id, name),
        )

    def create_subject(self, subject: SkillTreeSubject) -> Any:
        return self.request_json_allowing_existing(
            "POST",
            subject_create_path(self.project_id, subject.subject_id),
            json_body=subject_payload(subject),
        )

    def create_skill(self, subject_id: str, skill: SkillTreeSkill) -> Any:
        return self.request_json_allowing_existing(
            "POST",
            skill_create_path(self.project_id, subject_id, skill.skill_id),
            json_body=skill_payload(skill),
        )

    def assign_dependency(self, dep: SkillDependency) -> Any:
        existing = self.live_dependency_pairs()
        pair = (dep.skill_id, dep.depends_on_skill_id)
        if pair in existing:
            return {"success": True, "alreadyExisted": True}
        reverse_pair = (dep.depends_on_skill_id, dep.skill_id)
        reverse_was_deleted = False
        if reverse_pair in existing:
            self.delete_dependency(
                SkillDependency(
                    skill_id=dep.depends_on_skill_id,
                    depends_on_skill_id=dep.skill_id,
                )
            )
            reverse_was_deleted = True
            existing.discard(reverse_pair)
        try:
            result = self.request_json_allowing_existing(
                "POST",
                dependency_assign_path(self.project_id, dep),
                json_body=dependency_payload(dep),
            )
        except SkillTreeClientError as exc:
            # A delete-then-reseed may have only half-landed (the stale reverse edge
            # removed but the replacement POST rejected). Drop the cached graph so a
            # later read re-fetches the authoritative live state, and refresh now on
            # the partial-failure path so the caller never acts on a stale in-memory
            # belief about which edges exist. This keeps reseeds self-healing on retry.
            self._dependency_pairs = None
            if _is_dependency_confirmation_error(exc):
                if pair in self.live_dependency_pairs():
                    return {
                        "success": True,
                        "alreadyExisted": True,
                        "confirmedAfterError": True,
                    }
            elif reverse_was_deleted:
                self.live_dependency_pairs()
            raise
        existing.add(pair)
        return result

    def delete_dependency(self, dep: SkillDependency) -> Any:
        """Remove a stale live prerequisite edge before reseeding its replacement."""
        try:
            return self.request_json(
                "DELETE",
                f"/admin/projects/{self.project_id}/{dep.skill_id}"
                f"/prerequisite/{self.project_id}/{dep.depends_on_skill_id}",
            )
        except SkillTreeClientError as exc:
            raise LocalSkillTreeAuthError(
                "live SkillTree has stale reverse prerequisite "
                f"{dep.skill_id!r} -> {dep.depends_on_skill_id!r}, but it could not "
                "be removed before reseeding the current export"
            ) from exc

    def live_dependency_pairs(self) -> set[tuple[str, str]]:
        """Return live ``(dependent_skill_id, prerequisite_skill_id)`` pairs.

        SkillTree's duplicate dependency response can be slow or connection-sticky
        on large local reseeds. Reading the graph first keeps the bootstrap
        idempotent without deleting the user's Docker volume.
        """
        if self._dependency_pairs is not None:
            return self._dependency_pairs
        payload = self.request_json(
            "GET", f"/admin/projects/{self.project_id}/dependency/graph"
        )
        self._dependency_pairs = _parse_dependency_graph(payload)
        return self._dependency_pairs

    def create_quiz(self, quiz: Quiz) -> Any:
        result = self.request_json_allowing_existing(
            "POST", f"/admin/quiz-definitions/{quiz.quiz_id}", json_body=quiz.to_dict()
        )
        self._ensure_quiz_questions(quiz)
        return result

    def _ensure_quiz_questions(self, quiz: Quiz) -> None:
        """Create any exported quiz questions missing from the live quiz."""
        if not quiz.questions:
            return
        existing = self.request_json(
            "GET", f"/admin/quiz-definitions/{quiz.quiz_id}/questions"
        )
        existing_count = min(quiz_question_count(existing), len(quiz.questions))
        if existing_count >= len(quiz.questions):
            return
        for question in quiz.questions[existing_count:]:
            self.create_quiz_question(quiz.quiz_id, question)

    def create_quiz_question(self, quiz_id: str, question: QuizQuestion) -> Any:
        return self.request_json(
            "POST",
            f"/admin/quiz-definitions/{quiz_id}/create-question",
            json_body=question.to_admin_create_payload(),
        )


def _is_existing_resource_error(exc: SkillTreeClientError) -> bool:
    """Return true for SkillTree duplicate-create responses during local reseed."""
    if exc.status not in {400, 409} or not exc.body:
        return False
    text = exc.body.lower()
    return any(
        marker in text
        for marker in (
            "already exists",
            "already exist",
            "already been used",
            "duplicate",
        )
    )


def _is_dependency_confirmation_error(exc: SkillTreeClientError) -> bool:
    """Return true when a dependency POST may have succeeded despite the client error."""
    text = str(exc).lower()
    return exc.status is None and (
        "timed out" in text or "transport error" in text or "connection reset" in text
    )


def _parse_dependency_graph(payload: Any) -> set[tuple[str, str]]:
    """Parse SkillTree dependency graph JSON into skill-id dependency pairs."""
    if not isinstance(payload, dict):
        raise LocalSkillTreeAuthError(
            "SkillTree dependency graph response returned non-object JSON"
        )
    nodes_payload = payload.get("nodes")
    edges_payload = payload.get("edges")
    if nodes_payload is None and edges_payload is None:
        data = payload.get("data")
        if isinstance(data, dict):
            nodes_payload = data.get("nodes")
            edges_payload = data.get("edges")
    if not isinstance(nodes_payload, list) or not isinstance(edges_payload, list):
        raise LocalSkillTreeAuthError(
            "SkillTree dependency graph response is missing nodes/edges lists"
        )

    node_by_id: dict[int, str] = {}
    for node in nodes_payload:
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        skill_id = str(node.get("skillId", "")).strip()
        if isinstance(node_id, int) and skill_id:
            node_by_id[node_id] = skill_id

    pairs: set[tuple[str, str]] = set()
    for edge in edges_payload:
        if not isinstance(edge, dict):
            continue
        from_id = edge.get("fromId")
        to_id = edge.get("toId")
        if not isinstance(from_id, int) or not isinstance(to_id, int):
            continue
        dependent = node_by_id.get(from_id)
        prerequisite = node_by_id.get(to_id)
        if dependent and prerequisite:
            pairs.add((dependent, prerequisite))
    return pairs


def verify_seed_landed(
    client: SkillTreeSessionClient, project: SkillTreeProject
) -> None:
    """Fail loud if the live skill count is below what the project should have seeded.

    The idempotent re-seed swallows SkillTree's duplicate-resource 400s so the bootstrap
    is re-runnable — but that same swallow can mask a *genuine* creation failure (a skill
    rejected for a name collision, a name-length cap, or any future server constraint the
    local model does not mirror), leaving a partial graph with dangling prerequisite edges.
    A validator only guards constraints we already know about; this post-seed check is the
    belt-and-suspenders that turns ANY silently-dropped create into a loud error, by
    comparing live state to what we asked the server to create.
    """
    expected_skills = sum(len(subject.skills) for subject in project.subjects)
    expected_subjects = len(project.subjects)
    live_skills = client.live_skill_count()
    live_subjects = client.live_subject_count()
    # Check BOTH skills and subjects: counting only skills lets a dropped *subject* hide
    # (its skills are still summed into `expected_skills`), so a missing subject with all
    # its skills rejected would pass a skill-only check while leaving a partial graph.
    shortfalls = []
    if live_skills < expected_skills:
        shortfalls.append(f"{live_skills} skills vs {expected_skills} expected")
    if live_subjects < expected_subjects:
        shortfalls.append(f"{live_subjects} subjects vs {expected_subjects} expected")
    if shortfalls:
        raise LocalSkillTreeAuthError(
            f"seed verification failed for project {project.project_id!r}: SkillTree "
            f"reports {'; '.join(shortfalls)} — a create was silently dropped (likely a "
            "server-side rejection swallowed as idempotent). Inspect for duplicate "
            "names / invalid ids before trusting the live instance."
        )


def live_project_counts_match(
    client: SkillTreeSessionClient, project: SkillTreeProject
) -> bool:
    """Return whether live SkillTree already has this export's core resources."""
    expected_skills = sum(len(subject.skills) for subject in project.subjects)
    expected_subjects = len(project.subjects)
    return (
        client.live_skill_count() == expected_skills
        and client.live_subject_count() == expected_subjects
    )


def _refuse_default_password_off_loopback(base_url: str, password: str) -> None:
    """Refuse to bootstrap the well-known local-dev admin password off loopback.

    ``DEFAULT_LOCAL_ADMIN_PASSWORD`` is a source-controlled, publicly-readable
    string. Bootstrapping a fresh SkillTree root account with it is fine against
    a private local Docker instance, but if ``base_url`` ever points at a shared
    or staging target (an operator error, not an attack), anyone who reads this
    file could log in as root. Overriding ``LOCAL_ADMIN_PASSWORD_ENV`` bypasses
    this check, since the resulting password is then no longer the known default.
    """
    if password != DEFAULT_LOCAL_ADMIN_PASSWORD:
        return
    if is_loopback_host(urllib.parse.urlparse(base_url).hostname or ""):
        return
    raise LocalSkillTreeAuthError(
        "refusing to bootstrap the well-known local-development admin password "
        f"(source-controlled default, {LOCAL_ADMIN_PASSWORD_ENV} not overridden) "
        f"against non-loopback SkillTree target {base_url!r}. Set "
        f"{LOCAL_ADMIN_PASSWORD_ENV} explicitly before bootstrapping a shared, "
        "staging, or otherwise non-local instance."
    )


def _load_or_create_root_state(
    *,
    client: SkillTreeSessionClient,
    base_url: str,
    project_id: str,
    state_dir: Path,
    learner_id: str,
) -> tuple[LocalSkillTreeState, bool]:
    config = client.public_config()
    needs_bootstrap = bool(config.get("needToBootstrap"))
    state = load_local_state(state_dir)
    if state is not None:
        if state.skilltree_url:
            _require_same_skilltree_origin(
                base_url=base_url,
                state_url=state.skilltree_url,
            )
        if state.project_id != project_id:
            raise LocalSkillTreeAuthError(
                f"local SkillTree auth state is for project {state.project_id!r}, "
                f"not {project_id!r}"
            )
        return state, False
    if not needs_bootstrap:
        raise LocalSkillTreeAuthError(
            "SkillTree already has a root account, but no local credentials exist "
            f"at {local_state_path(state_dir)}. Remove the local Docker volume to "
            "restart bootstrap, restore the state file, or seed with SKILLTREE_TOKEN."
        )
    state = new_local_state(
        skilltree_url=base_url,
        project_id=project_id,
        learner_id=learner_id,
    )
    _refuse_default_password_off_loopback(base_url, state.admin_password)
    save_local_state(state_dir, state)
    client.create_root_account(state)
    return state, True


def _login_local_admin(
    client: SkillTreeSessionClient,
    state: LocalSkillTreeState,
) -> None:
    try:
        client.login(state.admin_username, state.admin_password)
    except SkillTreeClientError as exc:
        if not is_browser_login_compatible_username(state.admin_username):
            raise LocalSkillTreeAuthError(
                "stored local SkillTree credentials use a non-email username. "
                "SkillTree's browser login requires an email-style username; run "
                "`uv run python scripts/reset_local_skilltree.py --confirm-local-reset` "
                "to recreate the local Docker volume with the documented default "
                "login, or restore a matching local state file."
            ) from exc
        raise


def _seed_project_if_requested(
    *,
    client: SkillTreeSessionClient,
    project: SkillTreeProject | None,
    seed_project: bool,
    seed_dependencies: bool,
    skip_seed_if_live_counts_ready: bool,
    verify_seed: bool,
) -> tuple[bool, dict[str, int] | None]:
    if not seed_project or project is None:
        return False, None
    should_seed = True
    if skip_seed_if_live_counts_ready:
        try:
            should_seed = not live_project_counts_match(client, project)
        except (LocalSkillTreeAuthError, SkillTreeClientError):
            should_seed = True
    if not should_seed:
        return False, None
    seed_summary = seed(client, project, include_dependencies=seed_dependencies)
    if verify_seed:
        verify_seed_landed(client, project)
    return True, seed_summary


def _project_client_secret_state(
    *,
    client: SkillTreeSessionClient,
    base_url: str,
    project_id: str,
    state: LocalSkillTreeState,
    learner_id: str,
) -> LocalSkillTreeState:
    client_secret = client.get_project_client_secret()
    if not client_secret:
        client_secret = client.reset_project_client_secret()
    if not client_secret:
        raise LocalSkillTreeAuthError(
            f"SkillTree did not return a trusted-client secret for project {project_id!r}."
        )
    updated = replace(
        state,
        client_secret=client_secret,
        learner_id=learner_id,
        project_id=project_id,
        skilltree_url=base_url.rstrip("/"),
        updated_at=_utc_now(),
    )
    return updated


def _verify_local_trusted_client_token(
    *,
    base_url: str,
    project_id: str,
    state: LocalSkillTreeState,
    verify_token: bool,
) -> bool:
    if not verify_token:
        return False
    exchange_trusted_client_token(
        base_url=base_url,
        project_id=project_id,
        client_secret=state.client_secret,
        learner_id=state.learner_id,
    )
    return True


def ensure_local_skilltree_auth(
    *,
    base_url: str,
    project_id: str,
    state_dir: Path,
    learner_id: str = DEFAULT_LOCAL_LEARNER_ID,
    project: SkillTreeProject | None = None,
    seed_project: bool = True,
    seed_dependencies: bool = True,
    skip_seed_if_live_counts_ready: bool = False,
    verify_seed: bool = True,
    verify_token: bool = True,
) -> BootstrapResult:
    """Bootstrap local root auth, seed the project, and store client credentials."""
    client = SkillTreeSessionClient(
        base_url, project_id, timeout=default_local_request_timeout()
    )
    state, created_root = _load_or_create_root_state(
        client=client,
        base_url=base_url,
        project_id=project_id,
        state_dir=state_dir,
        learner_id=learner_id,
    )
    _login_local_admin(client, state)
    seeded, seed_summary = _seed_project_if_requested(
        client=client,
        project=project,
        seed_project=seed_project,
        seed_dependencies=seed_dependencies,
        skip_seed_if_live_counts_ready=skip_seed_if_live_counts_ready,
        verify_seed=verify_seed,
    )
    state = _project_client_secret_state(
        client=client,
        base_url=base_url,
        project_id=project_id,
        state=state,
        learner_id=learner_id,
    )
    token_verified = _verify_local_trusted_client_token(
        base_url=base_url,
        project_id=project_id,
        state=state,
        verify_token=verify_token,
    )
    save_local_state(state_dir, state)

    return BootstrapResult(
        state=state,
        created_root=created_root,
        seeded=seeded,
        seed_summary=seed_summary,
        token_verified=token_verified,
    )


def fetch_local_skilltree_token(
    *,
    base_url: str,
    state_dir: Path,
    project_id: str,
    learner_id: str,
) -> dict[str, Any]:
    """Load private local state and return a SkillTree OAuth token response."""
    state = load_local_state(state_dir)
    if state is None:
        raise LocalSkillTreeAuthError("local SkillTree auth has not been bootstrapped")
    if state.project_id != project_id:
        raise LocalSkillTreeAuthError(
            f"local auth state is for project {state.project_id!r}, not {project_id!r}"
        )
    if not state.client_secret.strip():
        raise LocalSkillTreeAuthError(
            "local SkillTree trusted-client secret is missing"
        )
    _require_same_skilltree_origin(base_url=base_url, state_url=state.skilltree_url)
    return exchange_trusted_client_token(
        base_url=base_url,
        project_id=project_id,
        client_secret=state.client_secret,
        learner_id=learner_id or state.learner_id,
    )


class _NoTokenRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def exchange_trusted_client_token(
    *,
    base_url: str,
    project_id: str,
    client_secret: str,
    learner_id: str,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Exchange SkillTree trusted-client credentials for a proxy-user token."""
    if not client_secret.strip():
        raise LocalSkillTreeAuthError("client_secret must be non-empty")
    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "proxy_user": learner_id,
        }
    ).encode("utf-8")
    credentials = base64.b64encode(f"{project_id}:{client_secret}".encode())
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/oauth/token",
        data=body,
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {credentials.decode('ascii')}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        opener = urllib.request.build_opener(_NoTokenRedirectHandler)
        with opener.open(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise SkillTreeClientError(
            f"POST /oauth/token failed with status {exc.code}",
            status=exc.code,
            body=raw,
        ) from exc
    except urllib.error.URLError as exc:  # pragma: no cover - network dependent
        raise SkillTreeClientError(
            f"POST /oauth/token transport error: {exc.reason}"
        ) from exc
    # Fail closed: an HTTP 200 with an empty/typeless/token-less body is NOT a successful
    # exchange. Previously an empty body became {} and passed the isinstance check, so the
    # caller (which only watches for exceptions) set token_verified=True with no token.
    if not raw.strip():
        raise LocalSkillTreeAuthError(
            "SkillTree token endpoint returned an empty response"
        )
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise LocalSkillTreeAuthError(
            "SkillTree token endpoint returned non-object JSON"
        )
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise LocalSkillTreeAuthError(
            "SkillTree token endpoint returned no access_token (auth not verified)"
        )
    return payload


def _parse_secret_response(raw: str) -> str:
    text = raw.strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # SkillTree's clientSecret endpoint returns the secret as bare text/plain — this
        # is the documented success shape, not a malformed response.
        return text.strip('"')
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and str(data.get("clientSecret", "")).strip():
            return str(data["clientSecret"])
        if str(payload.get("clientSecret", "")).strip():
            return str(payload["clientSecret"])
    # Parsed as structured JSON but carried no clientSecret: returning the raw JSON blob
    # as if it were a secret would launder a malformed response into a "credential". A
    # structured-but-secretless response has no secret — say so with "".
    return ""
