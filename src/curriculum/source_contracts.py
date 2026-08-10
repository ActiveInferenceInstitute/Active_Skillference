"""Shared contracts for external source pointers (GitHub commits, etc.)."""

from __future__ import annotations

import re

GITHUB_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
