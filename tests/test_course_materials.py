"""Tests for generated local course-material records."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Self

import pytest

from src.curriculum.alignment import validate_course_material_alignment
from src.curriculum.catalog import build_curriculum
from src.curriculum.materials import (
    COGNITIVE_KB_SOURCE_ID,
    audit_course_material_index,
    build_course_material_index,
    load_material_sources,
    normalize_course_material_index,
    summarize_course_material_coverage,
    validate_active_skillference_material_contract,
    validate_material_sources,
    write_course_material_artifacts,
)
from src.kernels.examples import build_claim_registry
from src.project_identity import SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME
from src.provenance.binding import render_graph
from src.skilltree.exporter import export_project

REPO = Path(__file__).resolve().parents[1]
SOURCE_PATH = REPO / "data" / "course_material_sources.yaml"


def _exported_project_and_materials() -> tuple[
    dict[str, object], dict[str, object], dict[str, object]
]:
    graph = build_curriculum()
    registry = build_claim_registry()
    rendered = render_graph(graph, registry)
    project = export_project(
        rendered,
        SKILLTREE_PROJECT_ID,
        SKILLTREE_PROJECT_NAME,
    ).to_export_dict()
    source_payload = load_material_sources(SOURCE_PATH)
    material_index = build_course_material_index(
        rendered,
        source_payload,
        registry=registry,
    )
    material_audit = audit_course_material_index(material_index, rendered).to_dict()
    return project, material_index, material_audit


def test_course_material_sources_validate_offline() -> None:
    payload = load_material_sources(SOURCE_PATH)

    issues = validate_material_sources(payload)

    assert issues == []


def test_source_validation_rejects_unpinned_or_unknown_source() -> None:
    payload = load_material_sources(SOURCE_PATH)
    broken = deepcopy(payload)
    broken["sources"][0]["commit"] = "main"
    broken["stratum_mappings"]["math_foundations"][0]["source_id"] = "missing"

    issues = validate_material_sources(broken)

    assert any(issue.code == "commit" for issue in issues)
    assert any(issue.code == "pointer-source" for issue in issues)


def test_active_skillference_source_contract_requires_cognitive_knowledge_base() -> (
    None
):
    payload = load_material_sources(SOURCE_PATH)

    issues = validate_active_skillference_material_contract(payload)

    assert issues == []
    source_ids = {source["source_id"] for source in payload["sources"]}
    assert COGNITIVE_KB_SOURCE_ID in source_ids


def test_active_skillference_source_contract_rejects_missing_kb_topic_pointer() -> None:
    payload = load_material_sources(SOURCE_PATH)
    broken = deepcopy(payload)
    for topic in broken["topic_mappings"]:
        topic["pointers"] = [
            pointer
            for pointer in topic["pointers"]
            if pointer["source_id"] != COGNITIVE_KB_SOURCE_ID
        ]

    issues = validate_active_skillference_material_contract(broken)

    assert any(issue.code == "required-kb-topic-pointer" for issue in issues)


def test_every_skill_has_modular_material_and_external_pointer() -> None:
    graph = build_curriculum()
    registry = build_claim_registry()
    payload = load_material_sources(SOURCE_PATH)

    index = build_course_material_index(graph, payload, registry=registry)

    skills = index["skills"]
    assert isinstance(skills, dict)
    assert len(skills) == len(graph.skills)
    assert "{{claim:" not in str(index)
    for skill in graph.skills:
        record = skills[skill.skill_id]
        assert record["sections"]
        assert len(record["sections"]) >= 7
        assert record["externalPointers"]
        assert record["officialSkillTree"]["subjectRoute"].startswith("/subjects/")
        assert "/skills/" not in record["officialSkillTree"]["subjectRoute"]
        assert record["officialSkillTree"]["unsafeDirectSkillRoute"] == ""
        if record["officialSkillTree"]["quizRoute"]:
            assert "/quizzes/" in record["officialSkillTree"]["quizRoute"]


def test_course_material_coverage_exposes_kb_topic_and_source_counts() -> None:
    graph = build_curriculum()
    registry = build_claim_registry()
    payload = load_material_sources(SOURCE_PATH)

    index = build_course_material_index(graph, payload, registry=registry)
    coverage = summarize_course_material_coverage(index)

    assert coverage == index["coverage"]
    source_counts = coverage["sourcePointerCounts"]
    assert source_counts[COGNITIVE_KB_SOURCE_ID] >= len(graph.skills)
    assert coverage["sourceSkillCounts"][COGNITIVE_KB_SOURCE_ID] == len(graph.skills)
    assert coverage["topicMatchedSkills"] > 0
    assert coverage["cognitiveKnowledgeBaseTopicSkills"] > 0
    assert coverage["unresolvedPointerSkills"] == 0
    assert (
        index["summary"]["cognitiveKnowledgeBasePointers"]
        == source_counts[COGNITIVE_KB_SOURCE_ID]
    )
    example_pointer = next(
        pointer
        for record in index["skills"].values()
        for pointer in record["externalPointers"]
        if pointer["sourceId"] == COGNITIVE_KB_SOURCE_ID
    )
    assert example_pointer["matchScopes"]


def test_course_material_alignment_matches_exported_skills_paths_and_quizzes() -> None:
    project, material_index, material_audit = _exported_project_and_materials()

    report = validate_course_material_alignment(
        project=project,
        material_index=material_index,
        material_audit=material_audit,
    )

    assert report.ok
    expected_skills = sum(len(subject["skills"]) for subject in project["subjects"])
    expected_quizzes = len(project["quizzes"])
    assert expected_skills == 630
    assert expected_quizzes == 630
    assert report.summary["skills"] == expected_skills
    assert report.summary["materialRecords"] == expected_skills
    assert report.summary["quizzes"] == expected_quizzes
    assert report.summary["externalPointers"] >= expected_skills


def test_course_material_alignment_flags_route_and_quiz_drift() -> None:
    project, material_index, material_audit = _exported_project_and_materials()
    skill_id = next(iter(material_index["skills"]))  # type: ignore[index]
    record = material_index["skills"][skill_id]  # type: ignore[index]
    record["officialSkillTree"]["subjectRoute"] = (
        f"/subjects/sub_linalg/skills/{skill_id}"
    )
    record["assessmentSummary"]["questionCount"] = 0

    report = validate_course_material_alignment(
        project=project,
        material_index=material_index,
        material_audit=material_audit,
    )

    assert not report.ok
    assert any(issue.code == "material-subject-route" for issue in report.issues)
    assert any(issue.code == "material-assessment-count" for issue in report.issues)


def test_course_material_alignment_rejects_non_http_pointer_url() -> None:
    project, material_index, material_audit = _exported_project_and_materials()
    skill_id = next(iter(material_index["skills"]))  # type: ignore[index]
    record = material_index["skills"][skill_id]  # type: ignore[index]
    record["externalPointers"][0]["url"] = "javascript:alert(1)"

    report = validate_course_material_alignment(
        project=project,
        material_index=material_index,
        material_audit=material_audit,
    )

    assert any(issue.code == "material-pointer-url-scheme" for issue in report.issues)


def test_course_material_alignment_rejects_stale_summary_count() -> None:
    project, material_index, material_audit = _exported_project_and_materials()
    material_audit["summary"]["externalPointers"] += 1

    report = validate_course_material_alignment(
        project=project,
        material_index=material_index,
        material_audit=material_audit,
    )

    assert any(issue.code == "material-summary-count" for issue in report.issues)


def test_course_material_artifacts_are_written_deterministically(
    tmp_path: Path,
) -> None:
    graph = build_curriculum()
    registry = build_claim_registry()

    index_path, audit_path, audit = write_course_material_artifacts(
        graph,
        source_path=SOURCE_PATH,
        output_dir=tmp_path,
        registry=registry,
    )

    assert audit.ok
    assert index_path.exists()
    assert audit_path.exists()
    assert f'"materialRecords": {len(graph.skills)}' in audit_path.read_text(
        encoding="utf-8"
    )
    assert '"externalPointers"' in index_path.read_text(encoding="utf-8")


def _online_payload() -> dict[str, object]:
    """A minimal source payload with one pinned source and one configured pointer."""
    return {
        "version": 1,
        "sources": [
            {
                "source_id": "testsrc",
                "title": "Test Source",
                "repo_url": "https://github.com/testorg/testrepo",
                "commit": "0123456789abcdef0123456789abcdef01234567",
                "license_status": "External; pinned link only.",
                "status_note": "Test pointer.",
                "path_globs": ["docs/*.md"],
            }
        ],
        "stratum_mappings": {
            "math_foundations": [
                {
                    "source_id": "testsrc",
                    "title": "Doc one",
                    "path": "docs/one.md",
                    "role": "course-module",
                }
            ]
        },
    }


def _serve_tree(httpserver, paths: list[str]) -> None:
    tree = {"tree": [{"path": p, "type": "blob"} for p in paths]}
    httpserver.expect_request(
        "/repos/testorg/testrepo/git/trees/0123456789abcdef0123456789abcdef01234567"
    ).respond_with_json(tree)


def test_course_material_online_validation_passes_when_pointer_exists(
    httpserver, monkeypatch
) -> None:
    """ISC-134: online validation resolves pinned pointers against the live tree."""
    _serve_tree(httpserver, ["docs/one.md", "docs/two.md"])
    monkeypatch.setenv("ASF_GITHUB_API_BASE", httpserver.url_for(""))
    issues = validate_material_sources(_online_payload(), online=True, timeout=5.0)
    online_codes = {"github-tree", "path-glob", "pointer-path"}
    assert not [i for i in issues if i.code in online_codes]


def test_course_material_online_validation_fires_on_missing_pointer(
    httpserver, monkeypatch
) -> None:
    """Negative control (ISC-134): a pointer absent at the pinned commit must fail —
    offline validation cannot catch this, which was the vacuity the audit flagged."""
    _serve_tree(httpserver, ["docs/two.md"])  # docs/one.md is gone
    monkeypatch.setenv("ASF_GITHUB_API_BASE", httpserver.url_for(""))
    issues = validate_material_sources(_online_payload(), online=True, timeout=5.0)
    codes = {issue.code for issue in issues}
    assert "pointer-path" in codes


def test_course_material_online_validation_rejects_non_http_github_api_base(
    monkeypatch,
) -> None:
    """A misconfigured ASF_GITHUB_API_BASE must fail closed, not reach urlopen."""
    monkeypatch.setenv("ASF_GITHUB_API_BASE", "file:///etc/passwd")
    issues = validate_material_sources(_online_payload(), online=True, timeout=5.0)
    tree_issues = [i for i in issues if i.code == "github-tree"]
    assert tree_issues
    assert "only http/https URLs" in tree_issues[0].message


def test_material_source_validation_rejects_malformed_topic_mappings() -> None:
    payload = _online_payload()
    payload["topic_mappings"] = {"match": ["efe"], "pointers": []}

    issues = validate_material_sources(payload)

    assert any(issue.code == "topic-mappings" for issue in issues)


def test_course_material_audit_fires_on_corrupted_record_contracts() -> None:
    graph = build_curriculum()
    registry = build_claim_registry()
    payload = load_material_sources(SOURCE_PATH)
    index = build_course_material_index(graph, payload, registry=registry)
    skills = index["skills"]
    assert isinstance(skills, dict)
    skill_id = next(iter(skills))
    record = skills[skill_id]
    assert isinstance(record, dict)
    official = record["officialSkillTree"]
    assert isinstance(official, dict)

    record["sections"] = [{"heading": "Bad", "body": "still has {{claim:missing}}"}]
    record["externalPointers"] = []
    official["subjectRoute"] = f"/subjects/sub_linalg/skills/{skill_id}"
    official["unsafeDirectSkillRoute"] = f"/subjects/sub_linalg/skills/{skill_id}"

    audit = audit_course_material_index(index, graph)
    codes = {issue.code for issue in audit.issues}

    assert "unresolved-claim-token" in codes
    assert "missing-pointer" in codes
    assert "subject-route" in codes
    assert "unsafe-route" in codes


def test_course_material_normalizer_surfaces_malformed_record_shape() -> None:
    graph = build_curriculum()
    registry = build_claim_registry()
    payload = load_material_sources(SOURCE_PATH)
    index = build_course_material_index(graph, payload, registry=registry)
    skills = index["skills"]
    assert isinstance(skills, dict)
    skill_id = next(iter(skills))
    skills[skill_id] = ["not", "a", "record"]

    normalized = normalize_course_material_index(index)
    coverage = summarize_course_material_coverage(index)
    audit = audit_course_material_index(index, graph)

    assert normalized.records[skill_id].payload is None
    assert skill_id in coverage["unresolvedPointerSkillIds"]
    assert any(issue.code == "record-type" for issue in audit.issues)


def test_github_tree_fetch_retries_transient_5xx(monkeypatch) -> None:
    """A transient 5xx is retried with backoff and the fetch then succeeds."""
    import io
    import json
    import urllib.error

    from src.curriculum.materials import github_sources as gs

    body = json.dumps({"tree": [{"path": "a.md", "type": "blob"}]}).encode()
    state = {"calls": 0}

    class FakeResponse:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        def read(self) -> bytes:
            return self._data

    def fake_urlopen(request, timeout):
        state["calls"] += 1
        if state["calls"] == 1:
            raise urllib.error.HTTPError(
                request.full_url,
                503,
                "Service Unavailable",
                {},
                io.BytesIO(b"boom"),
            )
        return FakeResponse(body)

    monkeypatch.setattr(gs.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(gs.time, "sleep", lambda _seconds: None)

    paths = gs._fetch_github_tree_paths("o", "r", "c" * 40, timeout=2.0)
    assert paths == {"a.md"}
    assert state["calls"] == 2


def test_github_tree_fetch_raises_immediately_on_permanent_4xx(monkeypatch) -> None:
    """A permanent 4xx is not retried (it can never succeed)."""
    import io
    import urllib.error
    import urllib.request

    from src.curriculum.materials import github_sources as gs

    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url, 404, "Not Found", {}, io.BytesIO(b"missing")
        )

    monkeypatch.setattr(gs.time, "sleep", lambda _seconds: None)

    with pytest.raises(urllib.request.HTTPError):
        gs._github_tree_payload(
            urllib.request.Request("https://api.github.com/x"), timeout=2.0
        )


def test_github_tree_fetch_retries_transient_network_error(monkeypatch) -> None:
    """A transient network/timeout error is retried and the fetch then succeeds."""
    import json

    from src.curriculum.materials import github_sources as gs

    body = json.dumps({"tree": [{"path": "a.md", "type": "blob"}]}).encode()
    state = {"calls": 0}

    class FakeResponse:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        def read(self) -> bytes:
            return body

    def fake_urlopen(request, timeout):
        state["calls"] += 1
        if state["calls"] == 1:
            raise TimeoutError("timed out")
        return FakeResponse()

    monkeypatch.setattr(gs.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(gs.time, "sleep", lambda _seconds: None)

    paths = gs._fetch_github_tree_paths("o", "r", "c" * 40, timeout=2.0)
    assert paths == {"a.md"}
    assert state["calls"] == 2


def test_github_tree_fetch_raises_final_error_after_exhausting_attempts(
    monkeypatch,
) -> None:
    """If every retry fails with 5xx, the final HTTPError is re-raised."""
    import io
    import urllib.error
    import urllib.request

    from src.curriculum.materials import github_sources as gs

    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url, 503, "Service Unavailable", {}, io.BytesIO(b"boom")
        )

    monkeypatch.setattr(gs.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(gs.time, "sleep", lambda _seconds: None)

    with pytest.raises(urllib.request.HTTPError) as exc_info:
        gs._github_tree_payload(
            urllib.request.Request("https://api.github.com/x"), timeout=2.0
        )
    assert exc_info.value.code == 503
