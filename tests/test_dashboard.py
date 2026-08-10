"""Tests for the local learner dashboard surfaces."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from src.dashboard.artifacts import (
    DashboardArtifactError,
    artifact_inventory,
    get_artifact,
    load_claims_summary,
    load_course_material_index,
    load_course_materials_summary,
    load_curriculum_diagnostics,
    load_curriculum_stats,
    load_figure_table_companions,
    load_redacted_skilltree_export,
    load_scholarship_health_network,
    load_skilltree_project,
    read_json_file,
)
from src.dashboard.config import (
    SKILLS_CLIENT_MODULE_URL,
    DashboardConfig,
    make_dashboard_config,
)
from src.dashboard.graph_analysis import _row_int, analyze_project_graph
from src.dashboard.payload import live_skilltree_summary
from src.dashboard.server import ASSETS_ROOT, dashboard_payload, make_dashboard_handler
from src.dashboard.status import check_skilltree_status
from src.skilltree.local_auth import (
    DEFAULT_LOCAL_ADMIN_USERNAME,
    LocalSkillTreeState,
    save_local_state,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_local_auth_state(
    path: Path,
    client_secret: str = "trusted-secret",
    skilltree_url: str = "http://localhost:8080",
) -> None:
    save_local_state(
        path,
        LocalSkillTreeState(
            admin_username="active_skillference_admin",
            admin_password="admin-password",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url=skilltree_url,
            client_secret=client_secret,
        ),
    )


class _DashboardServer:
    def __init__(self, config: DashboardConfig) -> None:
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_dashboard_handler(config)
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        self.thread.start()
        port = self.server.server_address[1]
        return f"http://127.0.0.1:{port}"

    def __exit__(self, *args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def _fetch(url: str) -> tuple[int, str, bytes]:
    with urllib.request.urlopen(url, timeout=2) as response:
        return response.status, response.headers["Content-Type"], response.read()


def test_dashboard_config_defaults_to_local_skilltree() -> None:
    config = make_dashboard_config(project_root=Path.cwd())
    public = config.to_public_dict()
    assert public["project"]["id"] == "activeInference"  # type: ignore[index]
    assert public["project"]["name"] == "Active Skillference"  # type: ignore[index]
    assert public["skilltree"]["url"] == "http://localhost:8080"  # type: ignore[index]
    assert public["skilltree"]["authenticator"] == ""  # type: ignore[index]
    assert public["skilltree"]["authenticatorConfigured"] is False  # type: ignore[index]
    assert (  # type: ignore[index]
        public["skilltree"]["links"]["learnerDashboard"] == "http://127.0.0.1:8765"
    )
    assert (  # type: ignore[index]
        public["skilltree"]["links"]["skilltreeLogin"]
        == "http://localhost:8080/skills-login?redirect=/progress-and-rankings"
    )
    assert public["skilltree"]["clientModuleUrl"] == SKILLS_CLIENT_MODULE_URL  # type: ignore[index]
    assert SKILLS_CLIENT_MODULE_URL == "/assets/vendor/skills-client-js.esm.min.js"
    local_development = public["skilltree"]["localDevelopment"]  # type: ignore[index]
    assert local_development["defaultUsername"] == DEFAULT_LOCAL_ADMIN_USERNAME
    assert local_development["defaultPassword"] == ""
    assert local_development["defaultPasswordAvailable"] is False
    assert "reset_local_skilltree.py" in local_development["resetCommand"]
    assert public["dashboard"]["port"] == 8765  # type: ignore[index]


def test_dashboard_config_accepts_explicit_authenticator(tmp_path: Path) -> None:
    config = make_dashboard_config(project_root=tmp_path, authenticator="pki")
    public = config.to_public_dict()
    assert public["skilltree"]["authenticator"] == "pki"  # type: ignore[index]
    assert public["skilltree"]["authenticatorConfigured"] is True  # type: ignore[index]


def test_dashboard_config_uses_local_token_endpoint_when_ready(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    _write_local_auth_state(state_dir)
    config = make_dashboard_config(
        project_root=tmp_path,
        local_auth_enabled=True,
        local_state_dir=state_dir,
    )
    public = config.to_public_dict()
    skilltree = public["skilltree"]  # type: ignore[index]
    assert skilltree["authenticator"] == "http://127.0.0.1:8765/api/skilltree/token"
    assert skilltree["authenticatorConfigured"] is True
    assert skilltree["localAuth"]["ready"] is True
    assert skilltree["localAuth"]["browserLoginCompatible"] is False


def test_local_auth_rejects_remote_skilltree_client_module(tmp_path: Path) -> None:
    try:
        make_dashboard_config(
            project_root=tmp_path,
            local_auth_enabled=True,
            skills_client_module_url=(
                "https://unpkg.com/@skilltree/skills-client-js@3.6.3/"
                "dist/skills-client-js.esm.min.js"
            ),
        )
    except ValueError as exc:
        assert "same-origin dashboard asset" in str(exc)
    else:
        raise AssertionError("local auth accepted a remote SkillTree client module")


def test_dashboard_config_exposes_defaults_without_local_state_secrets(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "state"
    _write_local_auth_state(state_dir, client_secret="trusted-secret")
    config = make_dashboard_config(
        project_root=tmp_path,
        local_auth_enabled=True,
        local_state_dir=state_dir,
    )
    public_text = json.dumps(config.to_public_dict())

    assert DEFAULT_LOCAL_ADMIN_USERNAME in public_text
    assert "active-skillference-local" not in public_text
    assert "trusted-secret" not in public_text
    assert "admin-password" not in public_text


def test_dashboard_config_keeps_fallback_when_local_auth_incomplete(
    tmp_path: Path,
) -> None:
    config = make_dashboard_config(
        project_root=tmp_path,
        local_auth_enabled=True,
        local_state_dir=tmp_path / "missing-state",
    )
    public = config.to_public_dict()
    skilltree = public["skilltree"]  # type: ignore[index]
    assert skilltree["authenticator"] == ""
    assert skilltree["authenticatorConfigured"] is False
    assert skilltree["localAuth"]["ready"] is False


def test_dashboard_config_rejects_invalid_values(tmp_path: Path) -> None:
    invalid_values = [
        {"skilltree_url": ""},
        {"project_id": ""},
        {"project_name": ""},
        {"host": ""},
        {"port": 0},
        {"learner_id": ""},
    ]
    for kwargs in invalid_values:
        try:
            DashboardConfig(project_root=tmp_path, **kwargs)
        except ValueError:
            continue
        raise AssertionError(f"DashboardConfig accepted invalid values {kwargs}")


def test_local_auth_requires_loopback_bind(tmp_path: Path) -> None:
    """With the credential-issuing token bridge on, a non-loopback bind fails closed."""
    for non_loopback in ("0.0.0.0", "192.168.1.10", "example.com"):
        try:
            DashboardConfig(
                project_root=tmp_path,
                host=non_loopback,
                local_auth_enabled=True,
            )
        except ValueError:
            continue
        raise AssertionError(f"non-loopback host {non_loopback!r} was accepted")
    # Loopback binds are accepted; and a non-loopback bind is fine without local auth.
    for host in ("127.0.0.1", "localhost", "::1"):
        DashboardConfig(project_root=tmp_path, host=host, local_auth_enabled=True)
    DashboardConfig(project_root=tmp_path, host="0.0.0.0", local_auth_enabled=False)


def test_skilltree_status_reports_success(httpserver) -> None:  # type: ignore[no-untyped-def]
    httpserver.expect_request("/public/status").respond_with_json({"status": "UP"})
    status = check_skilltree_status(httpserver.url_for("/"))
    assert status["available"] is True
    assert status["statusCode"] == 200
    assert status["body"] == {"status": "UP"}


def test_skilltree_status_reports_http_error(httpserver) -> None:  # type: ignore[no-untyped-def]
    httpserver.expect_request("/public/status").respond_with_data(
        "maintenance",
        status=503,
    )
    status = check_skilltree_status(httpserver.url_for("/"))
    assert status["available"] is False
    assert status["statusCode"] == 503
    assert "HTTP 503" in status["message"]


def test_skilltree_status_reports_unavailable_cleanly() -> None:
    status = check_skilltree_status("http://127.0.0.1:9", timeout=0.1)
    assert status["available"] is False
    assert "SkillTree" in status["message"]
    assert status["url"] == "http://127.0.0.1:9/public/status"


def test_skilltree_status_rejects_non_http_scheme() -> None:
    status = check_skilltree_status("file:///etc/passwd", timeout=0.1)
    assert status["available"] is False
    assert status["statusCode"] is None
    assert "only http/https URLs" in status["message"]


def test_dashboard_reads_exported_project_without_mutating_it(tmp_path: Path) -> None:
    project_path = tmp_path / "output" / "data" / "skilltree_project.json"
    payload = {
        "projectId": "activeInference",
        "name": "Active Skillference",
        "subjects": [
            {
                "subjectId": "sub_a",
                "name": "Subject A",
                "description": "A subject",
                "skills": [
                    {
                        "skillId": "skillA",
                        "name": "Skill A",
                        "description": "A skill",
                    },
                    {
                        "skillId": "skillB",
                        "name": "Skill B",
                        "description": "Another skill",
                    },
                ],
            }
        ],
        "dependencies": [{"skillId": "skillA", "dependsOnSkillId": "skillB"}],
        "quizzes": [{"quizId": "skillA_quiz", "name": "Skill A Quiz"}],
    }
    _write_json(project_path, payload)
    before = project_path.read_text(encoding="utf-8")

    summary = load_skilltree_project(tmp_path)

    assert summary["available"] is True
    assert summary["counts"] == {
        "subjects": 1,
        "skills": 2,
        "dependencies": 1,
        "quizzes": 1,
    }
    assert project_path.read_text(encoding="utf-8") == before


def test_dashboard_project_payload_redacts_quiz_answer_keys(tmp_path: Path) -> None:
    project_path = tmp_path / "output" / "data" / "skilltree_project.json"
    payload = {
        "projectId": "activeInference",
        "name": "Active Skillference",
        "subjects": [],
        "dependencies": [],
        "quizzes": [
            {
                "quizId": "skillA_quiz",
                "questions": [
                    {
                        "question": "q?",
                        "answers": [
                            {"answer": "a", "isCorrect": True},
                            {"answer": "b", "isCorrect": False},
                        ],
                    }
                ],
            }
        ],
    }
    _write_json(project_path, payload)

    summary = load_skilltree_project(tmp_path)
    artifact_payload, error = load_redacted_skilltree_export(tmp_path)

    assert error is None
    assert "isCorrect" not in json.dumps(summary)
    assert "isCorrect" not in json.dumps(artifact_payload)
    assert "isCorrect" in project_path.read_text(encoding="utf-8")


def test_graph_analysis_reports_bottlenecks_and_neighborhoods(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "output" / "data" / "skilltree_project.json",
        {
            "projectId": "activeInference",
            "name": "Active Skillference",
            "subjects": [
                {
                    "subjectId": "sub_math",
                    "name": "Math",
                    "description": "Math subject",
                    "skills": [
                        {"skillId": "root", "name": "Root"},
                        {"skillId": "mid", "name": "Middle"},
                    ],
                },
                {
                    "subjectId": "sub_app",
                    "name": "Applications",
                    "description": "Application subject",
                    "skills": [{"skillId": "leaf", "name": "Leaf"}],
                },
            ],
            "dependencies": [
                {"skillId": "mid", "dependsOnSkillId": "root"},
                {"skillId": "leaf", "dependsOnSkillId": "mid"},
            ],
            "quizzes": [],
        },
    )
    project = load_skilltree_project(tmp_path)
    analysis = analyze_project_graph(project)

    assert analysis["available"] is True
    assert analysis["summary"]["maxDepth"] == 2
    assert analysis["bottlenecks"][0]["skillId"] in {"mid", "root"}
    assert analysis["neighborhoods"]["mid"]["prerequisites"][0]["skillId"] == "root"
    assert analysis["neighborhoods"]["mid"]["dependents"][0]["skillId"] == "leaf"
    assert analysis["subjectFlows"][0]["sourceSubjectId"] == "sub_math"
    assert analysis["subjectFlows"][0]["targetSubjectId"] == "sub_app"
    assert analysis["subjectLayout"][0]["subjectId"] == "sub_math"
    assert analysis["subjectLayout"][0]["skillCount"] == 2
    assert analysis["subjectLayout"][0]["outgoingFlowCount"] == 1
    assert analysis["subjectLayout"][0]["outgoingSubjectCount"] == 1
    assert analysis["subjectLayout"][0]["topOutgoingFlow"]["subjectId"] == "sub_app"


def test_json_readers_reject_missing_invalid_and_non_object(tmp_path: Path) -> None:
    missing, missing_error = read_json_file(tmp_path / "missing.json")
    assert missing is None
    assert "does not exist" in str(missing_error)

    invalid = tmp_path / "bad.json"
    invalid.write_text("{", encoding="utf-8")
    payload, error = read_json_file(invalid)
    assert payload is None
    assert error

    list_json = tmp_path / "list.json"
    _write_json(list_json, [1, 2, 3])
    payload, error = read_json_file(list_json)
    assert payload is None
    assert "JSON object" in str(error)


def test_project_summary_handles_malformed_collections(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "output" / "data" / "skilltree_project.json",
        {
            "projectId": "activeInference",
            "name": "Active Inference",
            "subjects": "bad",
            "dependencies": "bad",
            "quizzes": "bad",
        },
    )
    summary = load_skilltree_project(tmp_path)
    assert summary["available"] is False
    assert summary["counts"] == {
        "subjects": 0,
        "skills": 0,
        "dependencies": 0,
        "quizzes": 0,
    }


def test_dashboard_payload_summarizes_missing_artifacts(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:9",
    )
    payload = dashboard_payload(config)
    assert payload["project"]["available"] is False  # type: ignore[index]
    assert payload["claims"]["available"] is False  # type: ignore[index]
    assert payload["skilltree"]["available"] is False  # type: ignore[index]
    assert payload["curriculumDiagnostics"]["available"] is False  # type: ignore[index]
    assert payload["scholarshipHealthNetwork"]["available"] is False  # type: ignore[index]
    assert payload["figureCompanions"]["available"] is False  # type: ignore[index]
    deployment = payload["skilltreeDeployment"]  # type: ignore[index]
    assert deployment["summary"]["browserSafe"] is True
    assert "trusted-secret" not in json.dumps(deployment)
    artifacts = payload["artifacts"]
    assert isinstance(artifacts, list)
    assert any(item["id"] == "skilltree_project" for item in artifacts)
    assert any(item["id"] == "curriculum_diagnostic_gap_map" for item in artifacts)
    assert any(item["id"] == "scholarship_coverage" for item in artifacts)
    assert any(item["id"] == "scholarship_source_health_network" for item in artifacts)
    assert any(item["id"] == "manuscript_artifacts" for item in artifacts)
    assert any(item["id"] == "manuscript_claim_support" for item in artifacts)
    assert any(item["id"] == "course_material_index" for item in artifacts)
    assert any(item["id"] == "course_material_audit" for item in artifacts)
    assert any(item["id"] == "figure_registry" for item in artifacts)
    assert any(item["id"] == "figure_table_companions" for item in artifacts)
    assert any(item["id"] == "active_skillference_cover" for item in artifacts)
    assert any(item["id"] == "active_skillference_skill_atlas" for item in artifacts)
    assert any(item["id"] == "scientific_evidence_matrix" for item in artifacts)
    assert any(item["id"] == "kernel_sensitivity_profiles" for item in artifacts)
    assert any(item["id"] == "vfe_efe_skilltree_bridge" for item in artifacts)
    assert any(item["id"] == "visual_evidence_contract_ladder" for item in artifacts)


def test_live_skilltree_summary_rejects_non_list_dependencies(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:9",
    )
    project = {
        "available": True,
        "dependencies": "not-a-list",
        "counts": {"dependencies": 5},
    }
    result = live_skilltree_summary(config, project)
    assert result["checked"] is False
    assert "not a list" in result["reason"]
    assert result["expectedDependencies"] == 5


def test_artifact_inventory_and_claim_summary_read_real_files(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "output" / "data" / "claims.json",
        {"entropy_fair_coin": {"value": 0.693147, "units": "nats"}},
    )
    _write_json(
        tmp_path / "output" / "figures" / "figure_registry.json",
        [
            {
                "accessibility_note": "Direct labels and high contrast.",
                "alt_text": "Bridge figure preview alt text.",
                "caption": "Bridge figure caption.",
                "chart_family": "table-card bridge",
                "claim_tokens": ["agent_g_sample"],
                "data_grain": "One bridge row per SkillTree subject route fixture.",
                "data_source": "Validated graph data.",
                "data_sources": ["Validated graph data.", "Generated route metadata."],
                "encoding": "Rows encode route fragments.",
                "false_certification_risk": "Prevents route drift.",
                "failure_mode": "Prevents route drift.",
                "filename": "vfe_efe_skilltree_bridge.png",
                "generated_by": "src.figures.plots.plot_vfe_efe_skilltree_bridge",
                "interpretation_boundary": "Wiring evidence only.",
                "label": "fig:vfe_efe_skilltree_bridge",
                "mobile_note": "Open the full-size image for route fragments.",
                "mobile_read": "Open the full-size image for route fragments.",
                "non_color_encoding": "Route text and subject rows carry the bridge reading without hue.",
                "palette_policy": "single-root preferred with neutral route text",
                "palette_roots": ["blue", "gray"],
                "question": "Which route metadata proves the bridge is wired?",
                "qa_role": "Confirms bridge route metadata reaches the dashboard.",
                "static_read": "The static bridge keeps route fragments visible.",
                "subtitle": "Source: validated SkillTree route fixture.",
                "table_companion_id": "companion:vfe_efe_skilltree_bridge",
                "takeaway": "Supplement routes are wired.",
                "visual_grammar": "Blue primary evidence, green success states.",
            }
        ],
    )
    inventory = artifact_inventory(tmp_path)
    claims = load_claims_summary(tmp_path)
    claim_artifact = next(item for item in inventory if item["id"] == "claims")
    cover_artifact = next(
        item for item in inventory if item["id"] == "active_skillference_cover"
    )
    atlas_artifact = next(
        item for item in inventory if item["id"] == "active_skillference_skill_atlas"
    )
    bridge_artifact = next(
        item for item in inventory if item["id"] == "vfe_efe_skilltree_bridge"
    )

    assert claims["available"] is True
    assert claims["count"] == 1
    assert claim_artifact["exists"] is True
    assert claim_artifact["url"] == "/artifacts/claims"
    assert cover_artifact["category"] == "cover"
    assert atlas_artifact["category"] == "cover"
    assert atlas_artifact["url"] == "/artifacts/active_skillference_skill_atlas"
    assert bridge_artifact["category"] == "figures"
    assert bridge_artifact["figure"]["label"] == "fig:vfe_efe_skilltree_bridge"  # type: ignore[index]
    assert bridge_artifact["figure"]["chart_family"] == "table-card bridge"  # type: ignore[index]
    assert (
        bridge_artifact["figure"]["subtitle"]
        == "Source: validated SkillTree route fixture."
    )  # type: ignore[index]
    assert bridge_artifact["figure"]["takeaway"] == "Supplement routes are wired."  # type: ignore[index]
    assert (
        bridge_artifact["figure"]["question"]
        == "Which route metadata proves the bridge is wired?"
    )  # type: ignore[index]
    assert (
        bridge_artifact["figure"]["data_grain"]
        == "One bridge row per SkillTree subject route fixture."
    )  # type: ignore[index]
    assert bridge_artifact["figure"]["palette_roots"] == ["blue", "gray"]  # type: ignore[index]
    assert bridge_artifact["figure"]["failure_mode"] == "Prevents route drift."  # type: ignore[index]
    assert (
        bridge_artifact["figure"]["table_companion_id"]
        == "companion:vfe_efe_skilltree_bridge"
    )  # type: ignore[index]


def test_curriculum_stats_and_unknown_artifact_paths(tmp_path: Path) -> None:
    _write_json(tmp_path / "output" / "data" / "curriculum_stats.json", {"skills": 124})
    stats = load_curriculum_stats(tmp_path)
    assert stats["available"] is True
    assert stats["stats"] == {"skills": 124}
    assert get_artifact("claims").artifact_id == "claims"
    try:
        get_artifact("nope")
    except DashboardArtifactError as exc:
        assert "unknown dashboard artifact" in str(exc)
    else:
        raise AssertionError("unknown artifact was accepted")


def test_dashboard_loaders_read_new_analysis_artifacts(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "output" / "data" / "curriculum_diagnostic_gap_map.json",
        {"summary": {"skills": 1}, "bottlenecks": [], "longChains": []},
    )
    _write_json(
        tmp_path / "output" / "data" / "scholarship_source_health_network.json",
        {"summary": {"sources": 1}, "deadLinks": [], "botBlocks": []},
    )
    _write_json(
        tmp_path / "output" / "data" / "figure_table_companions.json",
        {
            "figures": {
                "fig:fixture": {
                    "columns": ["skillId"],
                    "companionId": "companion:fixture",
                    "figureLabel": "fig:fixture",
                    "rows": [{"skillId": "fixture"}],
                    "title": "Fixture",
                }
            },
            "summary": {"rows": 1},
        },
    )

    diagnostics = load_curriculum_diagnostics(tmp_path)
    network = load_scholarship_health_network(tmp_path)
    companions = load_figure_table_companions(tmp_path)

    assert diagnostics["available"] is True
    assert network["available"] is True
    assert companions["available"] is True
    assert companions["figures"]["fig:fixture"]["rows"][0]["skillId"] == "fixture"  # type: ignore[index]


def test_course_material_dashboard_readers(tmp_path: Path) -> None:
    summary_path = tmp_path / "output" / "data" / "course_material_audit.json"
    index_path = tmp_path / "output" / "data" / "course_material_index.json"
    _write_json(
        summary_path,
        {
            "summary": {
                "skills": 1,
                "materialRecords": 1,
                "externalPointers": 2,
                "sections": 7,
                "ok": True,
            },
            "issues": [],
        },
    )
    _write_json(
        index_path,
        {
            "version": 1,
            "summary": {"skills": 1, "externalPointers": 2, "sources": 1},
            "sources": [],
            "skills": {"skillA": {"skillId": "skillA"}},
        },
    )

    summary = load_course_materials_summary(tmp_path)
    index = load_course_material_index(tmp_path)
    missing = load_course_material_index(tmp_path / "missing")

    assert summary["available"] is True
    assert summary["summary"]["materialRecords"] == 1  # type: ignore[index]
    assert index["available"] is True
    assert index["skills"]["skillA"]["skillId"] == "skillA"  # type: ignore[index]
    assert missing["available"] is False
    assert missing["skills"] == {}


def test_course_material_loaders_fail_closed_on_malformed_json(tmp_path: Path) -> None:
    """Negative control (triple-check #7/#8): a present-but-shapeless artifact must read as
    UNAVAILABLE, not available-but-silently-empty. Previously both loaders returned
    available=True for valid JSON missing the required keys."""
    summary_path = tmp_path / "output" / "data" / "course_material_audit.json"
    index_path = tmp_path / "output" / "data" / "course_material_index.json"
    _write_json(summary_path, {"version": 1})  # no 'summary'
    _write_json(index_path, {"version": 1})  # no skills/sources/summary

    summary = load_course_materials_summary(tmp_path)
    index = load_course_material_index(tmp_path)
    assert summary["available"] is False and summary["error"]
    assert index["available"] is False and "required key" in str(index["error"])


def test_dashboard_assets_include_official_skilltree_client() -> None:
    index = (ASSETS_ROOT / "index.html").read_text(encoding="utf-8")
    app = (ASSETS_ROOT / "app.js").read_text(encoding="utf-8")
    skilltree_client = ASSETS_ROOT / "vendor" / "skills-client-js.esm.min.js"
    assert "Active Skillference Learner Dashboard" in index
    assert "skills-client-container" in index
    assert "local-login-username" in index
    assert "local-login-password" in index
    assert "tex-chtml-full.js" in index
    assert 'integrity="sha384-' in index
    assert 'crossorigin="anonymous"' in index
    assert skilltree_client.exists()
    assert "SkillsConfiguration" in skilltree_client.read_text(encoding="utf-8")
    assert SKILLS_CLIENT_MODULE_URL == "/assets/vendor/skills-client-js.esm.min.js"
    assert "SkillsConfiguration.configure" in app
    assert "fetchSkillTreeAuthToken" in app
    assert "skilltreeConfig.authToken = authToken" in app
    assert "isDashboardAssetModule" in app
    assert "authenticator" in app
    assert "renderRichText" in app
    assert "typesetMath" in app
    assert "MathJax.typesetPromise" in app
    assert "renderLocalLogin" in app
    assert "browserLoginCompatible" in app


def test_dashboard_assets_split_local_learn_from_official_skilltree_routes() -> None:
    app = (ASSETS_ROOT / "app.js").read_text(encoding="utf-8")
    styles = (ASSETS_ROOT / "styles.css").read_text(encoding="utf-8")
    index = (ASSETS_ROOT / "index.html").read_text(encoding="utf-8")
    assert 'getJson("/api/course-materials")' in app
    assert 'data-material-skill-id="${escapeHtml(skill.skillId)}"' in app
    assert "renderMaterialDetail" in app
    assert "Local Learn Material" in app
    assert 'skilltreeUrl("subjects", subject.subjectId)' in app
    assert (
        'skilltreeUrl("subjects", subject.subjectId, "skills", '
        'skill.skillId, "quizzes", skill.quizId)'
    ) in app
    assert (
        'skilltreeUrl("subjects", subject.subjectId, "skills", skill.skillId)'
        not in app
    )
    assert "skillsClientDisplayPath" in app
    assert "serviceUrl: config.skilltree.url" in app
    assert "projectId: config.project.id" in app
    assert "Learn" in app
    assert "Open Subject" in app
    assert "Quiz" in app
    assert "artifact-thumb" in app
    assert "renderDependencyGraph" in app
    assert "renderGraphDiagnostics" in app
    assert "renderCurriculumDiagnostics" in app
    assert "renderFigureCompanions" in app
    assert "renderDeploymentMatrix" in app
    assert "Companion table" in app
    assert "SkillTree Deployment Matrix" in app
    assert "graph-skill-search" in index
    assert "dependency-graph" in index
    assert "curriculum-diagnostics" in index
    assert "artifact-companions" in index
    assert "deployment-matrix" in index
    assert "material-detail" in index
    assert 'loading="lazy"' not in app
    assert ".skill-actions" in styles
    assert ".local-login-card" in styles
    assert ".local-login-credentials" in styles
    assert ".material-detail" in styles
    assert ".artifact-thumb" in styles
    assert ".dependency-graph" in styles
    assert ".graph-diagnostics" in styles
    assert ".curriculum-diagnostics" in styles
    assert ".artifact-companions" in styles
    assert ".deployment-matrix" in styles


def test_dashboard_http_server_serves_core_routes(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "output" / "data" / "claims.json",
        {"entropy_fair_coin": {"value": 0.693147, "units": "nats"}},
    )
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:9",
    )
    with _DashboardServer(config) as base_url:
        index_status, index_type, index_body = _fetch(f"{base_url}/")
        css_status, css_type, _ = _fetch(f"{base_url}/assets/styles.css")
        vendor_status, vendor_type, vendor_body = _fetch(
            f"{base_url}{SKILLS_CLIENT_MODULE_URL}"
        )
        health_status, _, health_body = _fetch(f"{base_url}/healthz")
        config_status, _, config_body = _fetch(f"{base_url}/api/config")
        status_status, _, status_body = _fetch(f"{base_url}/api/status")
        project_status, _, project_body = _fetch(f"{base_url}/api/project")
        claims_status, _, claims_body = _fetch(f"{base_url}/api/claims")
        artifacts_status, _, artifacts_body = _fetch(f"{base_url}/api/artifacts")
        materials_status, _, materials_body = _fetch(f"{base_url}/api/course-materials")
        artifact_status, artifact_type, artifact_body = _fetch(
            f"{base_url}/artifacts/claims"
        )

    payload = json.loads(config_body.decode("utf-8"))

    assert index_status == 200
    assert "text/html" in index_type
    assert b"Active Skillference Learner Dashboard" in index_body
    assert css_status == 200
    assert "text/css" in css_type
    assert vendor_status == 200
    assert "application/javascript" in vendor_type
    assert b"SkillsConfiguration" in vendor_body
    assert health_status == 200
    assert json.loads(health_body.decode("utf-8"))["ok"] is True
    assert config_status == 200
    assert status_status == 200
    assert project_status == 200
    assert claims_status == 200
    assert artifacts_status == 200
    assert materials_status == 200
    assert artifact_status == 200
    assert "application/json" in artifact_type
    assert payload["project"]["id"] == "activeInference"
    assert payload["skilltree"]["authenticator"] == ""
    assert payload["skilltree"]["authenticatorConfigured"] is False
    status_payload = json.loads(status_body.decode("utf-8"))
    assert status_payload["skilltree"]["available"] is False
    assert status_payload["courseMaterials"]["available"] is False
    assert "graphAnalysis" in status_payload
    assert "curriculumDiagnostics" in status_payload
    assert "scholarshipHealthNetwork" in status_payload
    assert "figureCompanions" in status_payload
    assert status_payload["skilltreeDeployment"]["summary"]["browserSafe"] is True
    assert json.loads(project_body.decode("utf-8"))["available"] is False
    assert json.loads(claims_body.decode("utf-8"))["available"] is True
    assert isinstance(json.loads(artifacts_body.decode("utf-8")), list)
    assert json.loads(materials_body.decode("utf-8"))["available"] is False
    assert b"entropy_fair_coin" in artifact_body


def test_dashboard_artifact_route_redacts_skilltree_answer_keys(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "output" / "data" / "skilltree_project.json",
        {
            "projectId": "activeInference",
            "name": "Active Skillference",
            "subjects": [],
            "dependencies": [],
            "quizzes": [
                {
                    "quizId": "skillA_quiz",
                    "questions": [
                        {
                            "question": "q?",
                            "answers": [{"answer": "a", "isCorrect": True}],
                        }
                    ],
                }
            ],
        },
    )
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:9",
    )
    with _DashboardServer(config) as base_url:
        status, content_type, body = _fetch(f"{base_url}/artifacts/skilltree_project")

    assert status == 200
    assert "application/json" in content_type
    text = body.decode("utf-8")
    assert "skillA_quiz" in text
    assert "isCorrect" not in text


def test_dashboard_token_endpoint_returns_skilltree_token_without_leaking_secret(
    tmp_path: Path,
    httpserver,
) -> None:  # type: ignore[no-untyped-def]
    state_dir = tmp_path / "state"
    skilltree_url = httpserver.url_for("").rstrip("/")
    _write_local_auth_state(
        state_dir,
        client_secret="super-secret",
        skilltree_url=skilltree_url,
    )
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": "learner-token", "token_type": "Bearer"}
    )
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url=skilltree_url,
        local_auth_enabled=True,
        local_state_dir=state_dir,
    )
    with _DashboardServer(config) as base_url:
        token_status, _, token_body = _fetch(f"{base_url}/api/skilltree/token")
        status_status, _, status_body = _fetch(f"{base_url}/api/status")

    token = json.loads(token_body.decode("utf-8"))
    status_text = status_body.decode("utf-8")
    assert token_status == 200
    assert status_status == 200
    assert token["access_token"] == "learner-token"
    assert "active-skillference-local" not in status_text
    assert "super-secret" not in status_text
    assert "admin-password" not in status_text
    assert "learner-token" not in status_text


def test_dashboard_token_endpoint_allows_skilltree_origin_for_iframe(
    tmp_path: Path,
    httpserver,
) -> None:  # type: ignore[no-untyped-def]
    state_dir = tmp_path / "state"
    skilltree_url = httpserver.url_for("").rstrip("/")
    _write_local_auth_state(state_dir, skilltree_url=skilltree_url)
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": "learner-token", "token_type": "Bearer"}
    )
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url=skilltree_url,
        local_auth_enabled=True,
        local_state_dir=state_dir,
    )
    with _DashboardServer(config) as base_url:
        request = urllib.request.Request(
            f"{base_url}/api/skilltree/token",
            headers={"Origin": skilltree_url},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            body = json.loads(response.read().decode("utf-8"))
            allow_origin = response.headers["Access-Control-Allow-Origin"]

    assert body["access_token"] == "learner-token"
    assert allow_origin == skilltree_url


def test_dashboard_token_endpoint_options_preflight(
    tmp_path: Path,
    httpserver,
) -> None:  # type: ignore[no-untyped-def]
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url=httpserver.url_for("").rstrip("/"),
    )
    with _DashboardServer(config) as base_url:
        request = urllib.request.Request(
            f"{base_url}/api/skilltree/token",
            method="OPTIONS",
            headers={"Origin": config.skilltree_url},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            assert response.status == 204
            assert (
                response.headers["Access-Control-Allow-Origin"] == config.skilltree_url
            )


def test_dashboard_token_endpoint_fails_cleanly_when_local_auth_not_ready(
    tmp_path: Path,
) -> None:
    config = make_dashboard_config(
        project_root=tmp_path,
        local_auth_enabled=True,
        local_state_dir=tmp_path / "missing-state",
    )
    with _DashboardServer(config) as base_url:
        try:
            _fetch(f"{base_url}/api/skilltree/token")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            assert exc.code == 503
            assert "not ready" in body
        else:
            raise AssertionError("token endpoint unexpectedly succeeded")


def test_dashboard_http_server_rejects_bad_routes(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:9",
    )
    with _DashboardServer(config) as base_url:
        for path, expected_status in [
            ("/assets/", 400),
            ("/assets/../app.js", 400),
            ("/assets/vendor/../app.js", 400),
            ("/assets/missing.css", 404),
            ("/artifacts/unknown", 404),
            ("/missing", 404),
        ]:
            try:
                _fetch(f"{base_url}{path}")
            except urllib.error.HTTPError as exc:
                assert exc.code == expected_status
            else:
                raise AssertionError(f"{path} unexpectedly succeeded")


def test_dashboard_javascript_escapes_local_artifact_content() -> None:
    app = (ASSETS_ROOT / "app.js").read_text(encoding="utf-8")
    assert "function escapeHtml" in app
    assert "function safeHttpUrl" in app
    assert "renderOfficialFallback" in app
    assert 'href="${config.skilltree.links.dashboard}"' not in app
    assert "link.href = safeHttpUrl(config.skilltree.links.dashboard" in app
    assert 'const pointerUrl = safeHttpUrl(pointer.url, "")' in app
    assert "container.replaceChildren(wrapper)" in app
    assert "if (!payload.skilltree.available)" in app
    assert "if (!config.skilltree.authenticatorConfigured)" in app
    assert "Local SkillTree auth is not ready" in app
    assert "mountOfficialDisplay(payload)" in app
    assert "dependencyParityText" in app
    assert "Live SkillTree dependency graph is partial" in app
    assert "exported" in app


def test_dashboard_assets_include_skip_link_with_resolvable_target() -> None:
    """WCAG 2.4.1: a skip link must be the first body element and resolve to <main>."""
    index = (ASSETS_ROOT / "index.html").read_text(encoding="utf-8")
    body_start = index.index("<body>")
    after_body = index[body_start + len("<body>") :].lstrip()
    assert after_body.startswith('<a class="skip-link" href="#main">')
    assert "Skip to main content" in index
    # The skip-link target must exist as an id with a focusable tabindex.
    assert '<main id="main" tabindex="-1">' in index


def test_dashboard_assets_expose_bounded_path_recommendation_surface() -> None:
    index = (ASSETS_ROOT / "index.html").read_text(encoding="utf-8")
    app = (ASSETS_ROOT / "app.js").read_text(encoding="utf-8")
    assert 'id="path-recommendations"' in index
    assert "/api/recommendations" in app
    assert "not personalized advice" in app
    assert "Open Quiz" in app


def test_dashboard_styles_define_focus_visible_and_skip_link() -> None:
    """WCAG 2.4.7: focus-visible outlines and an off-screen skip link must exist."""
    styles = (ASSETS_ROOT / "styles.css").read_text(encoding="utf-8")
    assert ":focus-visible" in styles
    assert ".button:focus-visible" in styles
    assert ".tab:focus-visible" in styles
    assert ".skip-link" in styles
    assert ".skip-link:focus" in styles
    assert ".dependency-flows" in styles


def test_dashboard_javascript_supports_keyboard_tab_navigation() -> None:
    """WAI-ARIA Tabs pattern: arrow/Home/End keys cycle tabs with roving tabindex."""
    app = (ASSETS_ROOT / "app.js").read_text(encoding="utf-8")
    assert "keydown" in app
    assert "ArrowRight" in app
    assert "ArrowLeft" in app
    assert '"Home"' in app
    assert '"End"' in app
    assert "activateTab" in app
    assert 'setAttribute("tabindex", "-1")' in app
    assert 'setAttribute("tabindex", "0")' in app
    assert "tab.focus()" in app


def test_dashboard_renders_accessible_dependency_flow_table() -> None:
    """The flow table consumes the already-sent subjectFlows with proper table semantics."""
    app = (ASSETS_ROOT / "app.js").read_text(encoding="utf-8")
    assert "renderDependencyFlows" in app
    assert "analysis?.subjectFlows" in app
    assert "<caption>" in app
    assert 'scope="col"' in app
    assert "flow.sourceSubjectName" in app
    assert "flow.targetSubjectName" in app
    assert "flow.count" in app
    index = (ASSETS_ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="dependency-flows"' in index


def test_dashboard_artifact_cards_render_figure_metadata_and_large_previews() -> None:
    """The artifact gallery exposes figure-registry semantics, not just thumbnails."""
    app = (ASSETS_ROOT / "app.js").read_text(encoding="utf-8")
    styles = (ASSETS_ROOT / "styles.css").read_text(encoding="utf-8")

    assert "renderFigureMetadata" in app
    assert "figure.chart_family" in app
    assert "figure.question" in app
    assert "figure.subtitle" in app
    assert "figure.takeaway" in app
    assert "figure.data_grain" in app
    assert "figure.encoding" in app
    assert "figure.non_color_encoding" in app
    assert "figure.palette_policy" in app
    assert "figure.palette_roots" in app
    assert "figure.data_source" in app
    assert "figure.data_sources" in app
    assert "figure.interpretation_boundary" in app
    assert "figure.static_read" in app
    assert "figure.mobile_note" in app
    assert "figure.mobile_read" in app
    assert "figure.failure_mode" in app
    assert "figure.qa_role" in app
    assert "figure.visual_grammar" in app
    assert "figure.table_companion_id" in app
    assert "figureCompanionFor" in app
    assert "renderFigureCompanions" in app
    assert "Visual grammar" in app
    assert "Companion" in app
    assert "artifact-figure-contract" in app
    assert "artifact-figure-meta-primary" in app
    assert "Encoding and QA details" in app
    assert "artifact-preview" in app
    assert "Open full-size image" in app
    assert "artifact-preview-label" in app
    assert ".artifact-figure-contract" in styles
    assert ".artifact-figure-meta" in styles
    assert ".artifact-figure-meta-primary" in styles
    assert ".artifact-figure-details" in styles
    assert ".artifact-preview" in styles
    assert ".companion-card" in styles
    assert "620px" in styles
    assert "260px" in styles
    assert "132px" in styles
    assert 'figure.visual_grammar || "shared visual grammar"' not in app

    details = app[
        app.index("function renderFigureMetadata") : app.index(
            "function renderArtifacts"
        )
    ]
    assert details.index("Encoding and QA details") < details.index(
        "figure.visual_grammar"
    )

    artifacts = app[app.index("function renderArtifacts") :]
    assert artifacts.index("artifact-preview") < artifacts.index("<strong><a")
    assert artifacts.index("<strong><a") < artifacts.index("artifact.path")
    assert artifacts.index("artifact.path") < artifacts.index("figure.chart_family")
    assert artifacts.index("figure.chart_family") < artifacts.index(
        "renderFigureMetadata(figure, companion)"
    )
    assert "figure.visual_grammar" not in artifacts


def test_dashboard_orders_artifact_evidence_before_local_login() -> None:
    index = (ASSETS_ROOT / "index.html").read_text(encoding="utf-8")
    styles = (ASSETS_ROOT / "styles.css").read_text(encoding="utf-8")
    compact = styles[styles.index("@media (max-width: 780px)") :]
    login = '<section class="local-login-card"'

    assert index.index('<nav class="tabs"') < index.index(login)
    assert index.index('id="official-panel"') < index.index(login)
    assert index.index('id="artifacts-panel"') < index.index(login)
    assert index.index('id="runtime-panel"') < index.index(login)

    assert "main {" in compact
    assert "flex-direction: column;" in compact
    assert ".tabs {" in compact
    assert ".panel {" in compact
    assert ".local-login-card {" in compact
    assert compact.index(".tabs {") < compact.index(".panel {")
    assert compact.index(".panel {") < compact.index(".local-login-card {")
    assert "order: 3;" in compact
    assert "order: 4;" in compact
    assert "order: 5;" in compact


def test_dashboard_dependency_graph_uses_ordered_lanes() -> None:
    """The SVG graph consumes additive subjectLayout metadata and keeps flow data."""
    app = (ASSETS_ROOT / "app.js").read_text(encoding="utf-8")
    styles = (ASSETS_ROOT / "styles.css").read_text(encoding="utf-8")

    assert "analysis?.subjectLayout" in app
    assert "ordered lanes" in app
    assert "Ordered subject-lane dependency graph" in app
    assert "incomingFlowCount" in app
    assert "incomingSubjectCount" in app
    assert "outgoingFlowCount" in app
    assert "outgoingSubjectCount" in app
    assert "topIncomingFlow" in app
    assert "topOutgoingFlow" in app
    assert ".graph-lane" in styles


def test_dashboard_status_payload_carries_subject_flows(tmp_path: Path) -> None:
    """The flow table's data source (graphAnalysis.subjectFlows) is sent by the server."""
    _write_json(
        tmp_path / "output" / "data" / "skilltree_project.json",
        {
            "projectId": "activeInference",
            "name": "Active Skillference",
            "subjects": [
                {
                    "subjectId": "sub_math",
                    "name": "Math",
                    "description": "Math subject",
                    "skills": [{"skillId": "root", "name": "Root"}],
                },
                {
                    "subjectId": "sub_app",
                    "name": "Applications",
                    "description": "Application subject",
                    "skills": [{"skillId": "leaf", "name": "Leaf"}],
                },
            ],
            "dependencies": [{"skillId": "leaf", "dependsOnSkillId": "root"}],
            "quizzes": [],
        },
    )
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:9",
    )
    with _DashboardServer(config) as base_url:
        _, _, status_body = _fetch(f"{base_url}/api/status")
    status_payload = json.loads(status_body.decode("utf-8"))
    flows = status_payload["graphAnalysis"]["subjectFlows"]
    layout = status_payload["graphAnalysis"]["subjectLayout"]
    live_skilltree = status_payload["liveSkilltree"]
    assert live_skilltree["checked"] is False
    assert live_skilltree["expectedDependencies"] == 1
    assert flows
    assert flows[0]["sourceSubjectId"] == "sub_math"
    assert flows[0]["targetSubjectId"] == "sub_app"
    assert flows[0]["count"] == 1
    assert len(layout) == 2
    assert layout[0]["subjectId"] == "sub_math"
    assert layout[0]["skillCount"] == 1
    assert layout[0]["outgoingFlowCount"] == 1
    assert layout[0]["outgoingSubjectCount"] == 1
    assert layout[0]["topOutgoingFlow"]["subjectId"] == "sub_app"
    assert layout[1]["incomingFlowCount"] == 1
    assert layout[1]["incomingSubjectCount"] == 1
    assert layout[1]["topIncomingFlow"]["subjectId"] == "sub_math"


def test_artifact_roster_has_derived_count_and_unique_keys() -> None:
    """The dashboard roster count is derived, while ids and paths stay unique."""
    from src.dashboard.artifacts import ARTIFACTS, EXPECTED_ARTIFACT_COUNT

    assert len(ARTIFACTS) == EXPECTED_ARTIFACT_COUNT
    assert len({artifact.artifact_id for artifact in ARTIFACTS}) == len(ARTIFACTS)
    assert len({artifact.relative_path for artifact in ARTIFACTS}) == len(ARTIFACTS)
    assert any(
        artifact.relative_path
        == Path("output/figures/validation_intent_mismatch_matrix.png")
        for artifact in ARTIFACTS
    )


def test_graph_analysis_unavailable_project_returns_empty_shape() -> None:
    """A project the artifact reader marks unavailable yields a stable empty payload."""
    analysis = analyze_project_graph({"available": False})

    assert analysis["available"] is False
    assert analysis["bottlenecks"] == []
    assert analysis["isolatedRisks"] == []
    assert analysis["longestPaths"] == []
    assert analysis["neighborhoods"] == {}
    assert analysis["subjectLayout"] == []
    assert analysis["subjectFlows"] == []
    assert analysis["summary"] == {
        "skills": 0,
        "dependencies": 0,
        "subjectLanes": 0,
        "subjectFlows": 0,
    }


def test_graph_analysis_skips_malformed_subjects_and_skills() -> None:
    """Non-dict subjects, non-dict skills, and skills with no id are filtered out."""
    project = {
        "available": True,
        "subjects": [
            "not-a-dict",  # skipped: subject not a mapping
            {
                "subjectId": "sub_math",
                "name": "Math",
                "skills": [
                    "not-a-dict-skill",  # skipped: skill not a mapping
                    {"skillId": "", "name": "Empty"},  # skipped: blank skill id
                    {"skillId": "root", "name": "Root", "quizId": "root_quiz"},
                ],
            },
        ],
        "dependencies": [],
    }

    analysis = analyze_project_graph(project)

    assert analysis["available"] is True
    # Only the single well-formed skill survives the filters.
    assert analysis["summary"]["skills"] == 1
    assert list(analysis["neighborhoods"]) == ["root"]
    assert analysis["neighborhoods"]["root"]["quizId"] == "root_quiz"


def test_graph_analysis_skips_malformed_and_dangling_dependencies() -> None:
    """Non-dict deps are skipped; deps referencing unknown skills become missing refs."""
    project = {
        "available": True,
        "subjects": [
            {
                "subjectId": "sub_math",
                "name": "Math",
                "skills": [
                    {"skillId": "root", "name": "Root"},
                    {"skillId": "mid", "name": "Middle"},
                ],
            }
        ],
        "dependencies": [
            "not-a-dict",  # skipped: dependency not a mapping
            {"skillId": "mid", "dependsOnSkillId": "ghost"},  # missing prereq target
            {"skillId": "phantom", "dependsOnSkillId": "root"},  # missing dependent
            {"skillId": "mid", "dependsOnSkillId": "root"},  # valid edge
        ],
    }

    analysis = analyze_project_graph(project)

    missing = analysis["isolatedRisks"]["missingDependencyReferences"]
    assert {"skillId": "mid", "dependsOnSkillId": "ghost"} in missing
    assert {"skillId": "phantom", "dependsOnSkillId": "root"} in missing
    assert len(missing) == 2
    assert analysis["summary"]["missingDependencyReferences"] == 2
    # The one valid edge still resolves the dependency depth.
    assert analysis["summary"]["dependencies"] == 1
    assert analysis["neighborhoods"]["mid"]["depth"] == 1


def test_graph_analysis_depth_with_multiple_prerequisites() -> None:
    """A skill with two prerequisites only resolves after both are processed (162->159).

    The topological depth walk must take its true max depth across both incoming
    edges rather than firing as soon as the first prerequisite is drained.
    """
    project = {
        "available": True,
        "subjects": [
            {
                "subjectId": "sub_a",
                "name": "A",
                "skills": [
                    {"skillId": "base", "name": "Base"},
                    {"skillId": "mid", "name": "Mid"},
                    {"skillId": "join", "name": "Join"},
                ],
            }
        ],
        "dependencies": [
            {"skillId": "mid", "dependsOnSkillId": "base"},
            {"skillId": "join", "dependsOnSkillId": "base"},
            {"skillId": "join", "dependsOnSkillId": "mid"},
        ],
    }

    analysis = analyze_project_graph(project)

    depths = {row["skillId"]: row["depth"] for row in analysis["longestPaths"]}
    # base->mid->join is the longest chain; the direct base->join edge must not
    # short-circuit join to depth 1.
    assert depths["base"] == 0
    assert depths["mid"] == 1
    assert depths["join"] == 2
    assert analysis["summary"]["maxDepth"] == 2
    assert analysis["neighborhoods"]["join"]["depth"] == 2


def test_row_int_coerces_supported_types_and_falls_back() -> None:
    """_row_int normalizes bool/int/float/str values and falls back to 0 otherwise."""
    assert _row_int({"k": True}, "k") == 1  # bool branch precedes int branch
    assert _row_int({"k": False}, "k") == 0
    assert _row_int({"k": 7}, "k") == 7
    assert _row_int({"k": 3.9}, "k") == 3  # float truncates toward zero
    assert _row_int({"k": "12"}, "k") == 12  # numeric string parses
    assert _row_int({"k": None}, "k") == 0  # unsupported type -> 0
    assert _row_int({"k": [1, 2]}, "k") == 0  # unsupported type -> 0
    assert _row_int({}, "missing") == 0  # absent key uses default 0
