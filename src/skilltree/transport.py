"""Shared SkillTree HTTP transport helpers and errors."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class SkillTreeClientError(RuntimeError):
    """Raised on any non-2xx response or transport failure from SkillTree."""

    def __init__(
        self, message: str, status: int | None = None, body: str | None = None
    ) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


def origin(url: str) -> tuple[str, str, int | None]:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port


class NoCrossOriginBearerRedirect(urllib.request.HTTPRedirectHandler):
    """Block redirects that would carry bearer credentials to a different origin."""

    def redirect_request(  # type: ignore[override]
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        if req.has_header("Authorization") and origin(req.full_url) != origin(newurl):
            raise urllib.error.HTTPError(
                req.full_url,
                code,
                "cross-origin redirect blocked for authorized request",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def parse_json_body(raw: str) -> Any:
    return json.loads(raw) if raw.strip() else {}


def quiz_question_count(payload: Any) -> int:
    """Return a question count from SkillTree's admin question-list response."""
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        questions = payload.get("questions")
        if isinstance(questions, list):
            return len(questions)
        data = payload.get("data")
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            nested = data.get("questions")
            if isinstance(nested, list):
                return len(nested)
        count = payload.get("numQuestions")
        if isinstance(count, int) and count >= 0:
            return count
    return 0
