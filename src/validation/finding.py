"""Shared validation finding type for gate issue dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Finding:
    """A single validation finding with stable code, location, and message."""

    code: str
    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.location}: {self.message}"


class IssueLike(Protocol):
    """Structural type for issue-like objects exposing code/location/message."""

    code: str
    location: str
    message: str


def finding_from_issue(issue: IssueLike) -> Finding:
    """Adapt issue-like dataclasses that expose code/location/message."""
    return Finding(
        code=str(issue.code),
        location=str(issue.location),
        message=str(issue.message),
    )
