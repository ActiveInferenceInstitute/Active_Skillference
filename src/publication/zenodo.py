"""Reserve a Zenodo concept DOI without publishing anything.

Zenodo allocates a DOI to an unpublished draft deposition. That allocation is
real — the identifier is issued to this account and nobody else can receive it —
but it does not resolve until the draft is published, and a draft can still be
discarded. Reserving is therefore the one DOI action that is not irreversible,
which is why this module can perform it and deliberately cannot publish.

There is no publish call here on purpose. Minting a live DOI is a permanent,
outward-facing act and belongs to a human running the release tooling, not to a
build step.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ZENODO_API = "https://zenodo.org/api"
TOKEN_ENV_VAR = "ZENODO_PROD_TOKEN"
_TIMEOUT_SECONDS = 60.0


class ZenodoError(RuntimeError):
    """Raised when a Zenodo interaction fails or returns an unusable payload."""


@dataclass(frozen=True)
class ReservedDoi:
    """A DOI allocated to an unpublished Zenodo draft."""

    doi: str
    deposition_id: int
    #: ``unsubmitted`` while the draft is still unpublished.
    state: str
    submitted: bool
    html_url: str

    @property
    def is_published(self) -> bool:
        return self.submitted or self.state == "done"

    def to_dict(self) -> dict[str, Any]:
        return {
            "doi": self.doi,
            "depositionId": self.deposition_id,
            "state": self.state,
            "submitted": self.submitted,
            "htmlUrl": self.html_url,
            "resolves": self.is_published,
            "note": (
                "Reserved on an unpublished Zenodo draft. The identifier is "
                "allocated but does not resolve until the deposition is "
                "published, which this project does not do automatically."
            ),
        }


def read_token(env_path: Path, *, env_var: str = TOKEN_ENV_VAR) -> str:
    """Read the Zenodo token from a dotenv file without logging its value."""
    if not env_path.is_file():
        raise ZenodoError(f"environment file not found: {env_path}")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith(f"{env_var}="):
            continue
        value = stripped.split("=", 1)[1].strip().strip("'\"")
        if not value:
            raise ZenodoError(f"{env_var} is present but empty in {env_path}")
        return value
    raise ZenodoError(f"{env_var} not found in {env_path}")


def _request(
    path: str,
    *,
    token: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{ZENODO_API}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")[:500]
        raise ZenodoError(
            f"Zenodo {method} {path} failed ({exc.code}): {detail}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ZenodoError(f"Zenodo {method} {path} failed: {exc}") from exc


def zenodo_metadata(zenodo_json: Path) -> dict[str, Any]:
    """Build deposition metadata from the repository's own ``.zenodo.json``.

    Reusing that file keeps one source of truth for title, creators, keywords,
    and license, so a reservation cannot drift from the citation metadata.
    """
    payload = json.loads(zenodo_json.read_text(encoding="utf-8"))
    creators = [
        {
            key: value
            for key, value in creator.items()
            if key in {"name", "affiliation", "orcid"}
        }
        for creator in payload.get("creators", [])
    ]
    metadata: dict[str, Any] = {
        "title": payload["title"],
        "upload_type": payload.get("upload_type", "software"),
        "description": payload["description"],
        "creators": creators,
        "keywords": list(payload.get("keywords", [])),
        "license": str(payload.get("license", "MIT")).lower(),
        "version": payload.get("version", ""),
        "access_right": "open",
    }
    return {key: value for key, value in metadata.items() if value not in ("", [], {})}


def find_draft(*, token: str, title: str) -> ReservedDoi | None:
    """Return an existing unpublished draft with this title, if one exists.

    Prevents a rerun from littering the account with duplicate drafts, each
    burning another reserved identifier.
    """
    rows = _request("/deposit/depositions?size=100", token=token)
    if not isinstance(rows, list):
        raise ZenodoError("Zenodo deposition listing was not a JSON list")
    for row in rows:
        if str(row.get("title", "")).strip() != title.strip():
            continue
        if row.get("submitted") or row.get("state") == "done":
            continue
        doi = str(
            row.get("doi")
            or row.get("metadata", {}).get("prereserve_doi", {}).get("doi", "")
        )
        return ReservedDoi(
            doi=doi,
            deposition_id=int(row["id"]),
            state=str(row.get("state", "")),
            submitted=bool(row.get("submitted")),
            html_url=str(row.get("links", {}).get("html", "")),
        )
    return None


def upload_deposit_file(*, token: str, deposition_id: int, path: Path) -> str:
    """Attach one file to a draft deposition and return its Zenodo filename.

    Zenodo will not publish a deposition with no files, so this runs first. It
    uses the modern bucket API, which streams the body rather than building a
    multipart form in memory.
    """
    deposition = _request(f"/deposit/depositions/{deposition_id}", token=token)
    bucket = str(deposition.get("links", {}).get("bucket", ""))
    if not bucket:
        raise ZenodoError(
            f"deposition {deposition_id} exposes no upload bucket; it may already "
            "be published"
        )
    request = urllib.request.Request(
        f"{bucket}/{urllib.parse.quote(path.name)}",
        data=path.read_bytes(),
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")[:500]
        raise ZenodoError(f"Zenodo file upload failed ({exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ZenodoError(f"Zenodo file upload failed: {exc}") from exc
    return str(payload.get("key", path.name))


def publish_deposit(
    *,
    token: str,
    deposition_id: int,
    expected_doi: str,
) -> dict[str, Any]:
    """Publish a draft deposition after confirming its DOI is the expected one.

    The DOI check is the safety interlock: publishing is permanent, so the one
    thing worth refusing on is minting a record under an identifier the
    repository does not already claim.
    """
    deposition = _request(f"/deposit/depositions/{deposition_id}", token=token)
    reserved = str(
        deposition.get("metadata", {}).get("prereserve_doi", {}).get("doi", "")
        or deposition.get("doi", "")
    )
    if reserved != expected_doi:
        raise ZenodoError(
            f"deposition {deposition_id} carries DOI {reserved!r} but the "
            f"repository records {expected_doi!r}; refusing to publish a record "
            "under an identifier the project does not claim"
        )
    published = _request(
        f"/deposit/depositions/{deposition_id}/actions/publish",
        token=token,
        method="POST",
    )
    return {
        "doi": str(published.get("doi", reserved)),
        "depositionId": deposition_id,
        "state": str(published.get("state", "")),
        "submitted": bool(published.get("submitted", False)),
        "htmlUrl": str(published.get("links", {}).get("record_html", "")),
    }


def reserve_doi(*, token: str, metadata: dict[str, Any]) -> ReservedDoi:
    """Create an unpublished draft deposition and return its reserved DOI."""
    created = _request(
        "/deposit/depositions",
        token=token,
        method="POST",
        payload={"metadata": metadata},
    )
    if not isinstance(created, dict) or "id" not in created:
        raise ZenodoError("Zenodo did not return a deposition id")
    deposition_id = int(created["id"])
    reserved = str(
        created.get("metadata", {}).get("prereserve_doi", {}).get("doi", "")
        or created.get("doi", "")
    )
    if not reserved:
        raise ZenodoError(
            f"Zenodo created draft {deposition_id} but reserved no DOI; "
            "discard the draft and retry rather than inventing an identifier"
        )
    result = ReservedDoi(
        doi=reserved,
        deposition_id=deposition_id,
        state=str(created.get("state", "unsubmitted")),
        submitted=bool(created.get("submitted", False)),
        html_url=str(created.get("links", {}).get("html", "")),
    )
    if result.is_published:
        raise ZenodoError(
            f"deposition {deposition_id} reports as published; this module only "
            "reserves and must never mint a resolving DOI"
        )
    return result
