"""Minimal SkillTree REST client (stdlib ``urllib`` only — no extra deps).

Endpoint paths follow SkillTree's documented admin + report API
(https://skilltreeplatform.dev). Every method returns parsed JSON and raises
:class:`SkillTreeClientError` on any non-2xx response.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from src.net_guard import NonHttpUrlError, require_http_url
from src.skilltree.admin_ops import (
    dependency_assign_path,
    dependency_payload,
    project_create_body,
    project_create_path,
    quiz_definition_path,
    quiz_question_create_path,
    quiz_question_payload,
    quiz_questions_path,
    report_skill_path,
    skill_create_path,
    skill_payload,
    subject_create_path,
    subject_payload,
)
from src.skilltree.model import (
    Quiz,
    QuizQuestion,
    SkillDependency,
    SkillTreeSkill,
    SkillTreeSubject,
)
from src.skilltree.transport import (
    NoCrossOriginBearerRedirect,
    SkillTreeClientError,
    parse_json_body,
    quiz_question_count,
)

__all__ = ["SkillTreeClient", "SkillTreeClientError", "quiz_question_count"]


class SkillTreeClient:
    """Thin admin/report client for a single SkillTree project."""

    def __init__(
        self, base_url: str, project_id: str, token: str | None = None
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url must be non-empty")
        if not project_id.strip():
            raise ValueError("project_id must be non-empty")
        try:
            self.base_url = require_http_url(
                base_url.rstrip("/"), context="SkillTree client"
            )
        except NonHttpUrlError as exc:
            raise ValueError(str(exc)) from exc
        self.project_id = project_id
        self.token = token
        self._opener = urllib.request.build_opener(NoCrossOriginBearerRedirect)

    def _get(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with self._opener.open(request) as response:
                status = response.status
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise SkillTreeClientError(
                f"GET {path} failed with status {exc.code}",
                status=exc.code,
                body=raw,
            ) from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network-dependent
            raise SkillTreeClientError(
                f"GET {path} transport error: {exc.reason}"
            ) from exc

        if not 200 <= status < 300:  # pragma: no cover - urlopen raises before here
            raise SkillTreeClientError(
                f"GET {path} failed with status {status}", status=status, body=raw
            )
        return parse_json_body(raw)

    def _post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        data = json.dumps(body if body is not None else {}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with self._opener.open(request) as response:
                status = response.status
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise SkillTreeClientError(
                f"POST {path} failed with status {exc.code}",
                status=exc.code,
                body=raw,
            ) from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network-dependent
            raise SkillTreeClientError(
                f"POST {path} transport error: {exc.reason}"
            ) from exc

        if not 200 <= status < 300:  # pragma: no cover - urlopen raises before here
            raise SkillTreeClientError(
                f"POST {path} failed with status {status}", status=status, body=raw
            )
        return parse_json_body(raw)

    def create_project(self, name: str) -> Any:
        return self._post(
            project_create_path(self.project_id),
            project_create_body(self.project_id, name),
        )

    def create_subject(self, subject: SkillTreeSubject) -> Any:
        return self._post(
            subject_create_path(self.project_id, subject.subject_id),
            subject_payload(subject),
        )

    def create_skill(self, subject_id: str, skill: SkillTreeSkill) -> Any:
        return self._post(
            skill_create_path(self.project_id, subject_id, skill.skill_id),
            skill_payload(skill),
        )

    def assign_dependency(self, dep: SkillDependency) -> Any:
        return self._post(
            dependency_assign_path(self.project_id, dep),
            dependency_payload(dep),
        )

    def create_quiz(self, quiz: Quiz) -> Any:
        result = self._post(quiz_definition_path(quiz.quiz_id), quiz.to_dict())
        self._ensure_quiz_questions(quiz)
        return result

    def _ensure_quiz_questions(self, quiz: Quiz) -> None:
        if not quiz.questions:
            return
        existing = self._get(quiz_questions_path(quiz.quiz_id))
        existing_count = min(quiz_question_count(existing), len(quiz.questions))
        if existing_count >= len(quiz.questions):
            return
        for question in quiz.questions[existing_count:]:
            self.create_quiz_question(quiz.quiz_id, question)

    def create_quiz_question(self, quiz_id: str, question: QuizQuestion) -> Any:
        return self._post(
            quiz_question_create_path(quiz_id),
            quiz_question_payload(question),
        )

    def report_skill(self, skill_id: str, user_id: str) -> Any:
        return self._post(
            report_skill_path(self.project_id, skill_id),
            {"userId": user_id},
        )
