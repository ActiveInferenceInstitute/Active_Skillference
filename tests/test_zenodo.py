"""Publication API contracts over loopback, with synthetic credentials only."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import pytest
from werkzeug.wrappers import Response

from src.publication import zenodo

TOKEN = "loopback-test-token"
DOI = "10.5072/fixture.7"


@pytest.fixture
def api(httpserver, monkeypatch):
    monkeypatch.setattr(zenodo, "ZENODO_API", httpserver.url_for("/").rstrip("/"))
    return httpserver


def _draft(identifier: int, title: str = "Wanted") -> dict:
    return {
        "id": identifier, "title": title, "state": "unsubmitted", "submitted": False,
        "metadata": {"prereserve_doi": {"doi": DOI}},
        "links": {"html": "http://localhost/draft"},
    }


@pytest.fixture
def observed_upload(monkeypatch):
    streams = []

    class ObserveRequest(urllib.request.BaseHandler):
        def http_request(self, request):
            if request.get_method() == "PUT":
                stream = request.data
                assert hasattr(stream, "read") and not stream.closed
                assert not isinstance(stream, (bytes, bytearray))
                assert stream.tell() == 0
                assert request.get_header("Content-length") == str(os.fstat(stream.fileno()).st_size)
                streams.append(stream)
            return request

        https_request = http_request

    # A request processor observes the real urllib transfer; no response is faked.
    monkeypatch.setattr(urllib.request, "_opener", urllib.request.build_opener(ObserveRequest()))
    return streams


def _upload_bucket(api) -> None:
    api.expect_request("/deposit/depositions/7", method="GET").respond_with_json(
        {"links": {"bucket": api.url_for("/bucket/fixture")}}
    )


def test_upload_streams_open_file_with_exact_length_and_closes_it(api, tmp_path: Path, observed_upload) -> None:
    content = b"actual streamed archive bytes\n" * 32768
    path = tmp_path / "artifact.zip"
    path.write_bytes(content)
    _upload_bucket(api)

    def receive(request):
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        assert request.headers["Content-Length"] == str(len(content))
        assert request.get_data() == content
        return Response(json.dumps({"key": path.name}), content_type="application/json")

    api.expect_request("/bucket/fixture/artifact.zip", method="PUT").respond_with_handler(receive)
    assert zenodo.upload_deposit_file(token=TOKEN, deposition_id=7, path=path) == path.name
    api.check_assertions()
    assert len(observed_upload) == 1 and observed_upload[0].closed


@pytest.mark.parametrize("status,body", [(500, "failed"), (200, "not JSON"), (200, "{}")])
def test_upload_failure_closes_stream_and_never_invents_a_confirmed_filename(
    api, tmp_path: Path, observed_upload, status: int, body: str,
) -> None:
    path = tmp_path / "artifact.zip"
    path.write_bytes(b"archive")
    _upload_bucket(api)
    api.expect_request("/bucket/fixture/artifact.zip", method="PUT").respond_with_data(body, status=status)
    with pytest.raises(zenodo.ZenodoError):
        zenodo.upload_deposit_file(token=TOKEN, deposition_id=7, path=path)
    assert len(observed_upload) == 1 and observed_upload[0].closed


def test_missing_upload_bucket_refuses_before_opening_or_sending_a_file(api, tmp_path: Path) -> None:
    api.expect_request("/deposit/depositions/7", method="GET").respond_with_json({"links": {}})
    with pytest.raises(zenodo.ZenodoError, match="no upload bucket"):
        zenodo.upload_deposit_file(token=TOKEN, deposition_id=7, path=tmp_path / "absent.zip")
    assert [request.method for request, _response in api.log] == ["GET"]


def test_metadata_preserves_declared_identity_but_excludes_non_api_creator_fields(tmp_path: Path) -> None:
    path = tmp_path / ".zenodo.json"
    path.write_text(json.dumps({
        "title": "Fixture", "description": "Declared description", "license": "MIT",
        "version": "", "creators": [{"name": "Fixture Author", "affiliation": "Lab", "email": "private@example.org"}],
    }))
    metadata = zenodo.zenodo_metadata(path)
    assert metadata["title"] == "Fixture" and metadata["license"] == "mit"
    assert metadata["creators"] == [{"name": "Fixture Author", "affiliation": "Lab"}]
    assert "version" not in metadata and "private@example.org" not in json.dumps(metadata)


@pytest.mark.parametrize("payload", [{}, {"id": 7}, {**_draft(7), "submitted": True}])
def test_reservation_rejects_missing_identity_or_doi_and_already_published_result(api, payload) -> None:
    api.expect_request("/deposit/depositions", method="POST").respond_with_json(payload)
    with pytest.raises(zenodo.ZenodoError):
        zenodo.reserve_doi(token=TOKEN, metadata={"title": "Fixture"})


def test_doi_mismatch_sends_no_publication_post(api) -> None:
    api.expect_request("/deposit/depositions/7", method="GET").respond_with_json(_draft(7))
    with pytest.raises(zenodo.ZenodoError, match="refusing to publish"):
        zenodo.publish_deposit(token=TOKEN, deposition_id=7, expected_doi="10.5072/other")
    assert [request.method for request, _response in api.log] == ["GET"]


def test_explicit_matching_doi_allows_only_the_requested_loopback_publication(api) -> None:
    api.expect_request("/deposit/depositions/7", method="GET").respond_with_json(_draft(7))
    api.expect_request("/deposit/depositions/7/actions/publish", method="POST").respond_with_json(
        {"doi": DOI, "state": "done", "submitted": True, "links": {"record_html": api.url_for("/record/7")}}
    )
    result = zenodo.publish_deposit(token=TOKEN, deposition_id=7, expected_doi=DOI)
    assert result["doi"] == DOI and result["submitted"] and result["state"] == "done"
    assert [request.method for request, _response in api.log] == ["GET", "POST"]
