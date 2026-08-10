"""Smoke tests: the thin orchestrator scripts run to completion (exit 0)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[1]


# Subprocess timeout is deliberately generous: run_kernels.py (the heavy pipeline:
# 21 figures + audits) normally finishes in ~6s, but this repo's workflow runs
# parallel gate passes (herdr tabs), and under load the same prep has exceeded
# 120s. 300s keeps the smoke suite robust to that without masking real hangs.
_SUBPROCESS_TIMEOUT = 300


def _run(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / script)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )


def _load_script_module(script: str) -> ModuleType:
    script_path = REPO / "scripts" / script
    spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_docker_digests_script_runs() -> None:
    result = _run("validate_docker_digests.py")
    assert result.returncode == 0, result.stderr
    assert "docker image digest pins valid" in result.stdout


def test_validate_docker_digests_helper_flags_tag_only_lines() -> None:
    module = _load_script_module("validate_docker_digests.py")

    assert module.image_lines_without_digest(
        "services:\n  db:\n    image: postgres:15\n"
    ) == ["postgres:15"]
    assert (
        module.image_lines_without_digest(
            "services:\n  db:\n    image: postgres:15@sha256:"
            "c2ca90969ca293925ab474466e837689cc712321afdd9e4640bd0cf942fdca3a\n"
        )
        == []
    )


def test_local_skilltree_runtime_security_defaults() -> None:
    compose = (REPO / "docker-compose.yml").read_text(encoding="utf-8")
    run_skilltree = (REPO / "scripts" / "run_skilltree.sh").read_text(encoding="utf-8")
    run_dashboard = (REPO / "scripts" / "run_learning_dashboard.sh").read_text(
        encoding="utf-8"
    )

    assert "127.0.0.1:5432:5432" in compose
    assert "127.0.0.1:8080:8080" in compose
    assert "ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD:?" in compose
    assert '--token "$SKILLTREE_TOKEN"' not in run_skilltree
    assert '--token "$SKILLTREE_TOKEN"' not in run_dashboard
    assert "POSTGRES_PASSWORD_FILE" in run_skilltree
    assert "POSTGRES_PASSWORD_FILE" in run_dashboard


def test_form_login_password_handoff_avoids_eval_argv_secret() -> None:
    module = _load_script_module("validate_skilltree_form_login.py")

    with module.one_shot_secret_url("argv-secret-password") as password_url:
        script = module.login_submission_js(
            "active-skillference-admin@localhost.invalid",
            password_url,
        )
        with urllib.request.urlopen(password_url, timeout=2) as response:
            secret_body = response.read().decode("utf-8")
        try:
            urllib.request.urlopen(password_url, timeout=2)
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("one-shot password handoff served the secret twice")

    assert "argv-secret-password" not in script
    assert password_url in script
    assert secret_body == "argv-secret-password"


def test_one_shot_secret_url_restricts_cors_origin() -> None:
    module = _load_script_module("validate_skilltree_form_login.py")
    origin = "http://localhost:8080"

    with module.one_shot_secret_url("pw", allowed_origin=origin) as password_url:
        # A foreign origin is refused before the secret is consumed.
        foreign = urllib.request.Request(
            password_url, headers={"Origin": "http://evil.example"}
        )
        try:
            urllib.request.urlopen(foreign, timeout=2)
        except urllib.error.HTTPError as exc:
            assert exc.code == 403
        else:
            raise AssertionError("foreign-origin client read the one-shot secret")

        # The matching origin reads the secret and gets the echoed CORS header.
        allowed = urllib.request.Request(password_url, headers={"Origin": origin})
        with urllib.request.urlopen(allowed, timeout=2) as response:
            assert response.read().decode("utf-8") == "pw"
            assert response.headers.get("Access-Control-Allow-Origin") == origin

        # Single-use: a second read from the allowed origin is a 404.
        second = urllib.request.Request(password_url, headers={"Origin": origin})
        try:
            urllib.request.urlopen(second, timeout=2)
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("one-shot secret was served twice")


def test_build_curriculum_script_runs() -> None:
    result = _run("build_curriculum.py")
    assert result.returncode == 0, result.stderr
    assert "curriculum valid" in result.stdout
    assert (REPO / "output" / "data" / "curriculum_diagnostic_gap_map.json").exists()


def test_run_kernels_script_runs_and_emits_claims() -> None:
    result = _run("run_kernels.py")
    assert result.returncode == 0, result.stderr
    assert "provenance claims" in result.stdout
    assert "validated scholarship coverage" in result.stdout
    assert "validated scholarship gap report" in result.stdout
    assert "validated manuscript artifacts" in result.stdout
    assert "validated cover asset" in result.stdout
    assert "validated page-two visual" in result.stdout
    assert "validated American English manuscript language" in result.stdout
    assert "validated manuscript claim support" in result.stdout
    assert "validated course materials" in result.stdout
    assert (REPO / "output" / "data" / "claims.json").exists()
    assert (REPO / "output" / "data" / "scholarship_coverage.json").exists()
    assert (REPO / "output" / "data" / "scholarship_source_health.json").exists()
    assert (
        REPO / "output" / "data" / "scholarship_source_health_network.json"
    ).exists()
    assert (REPO / "output" / "data" / "scholarship_gap_report.json").exists()
    assert (REPO / "output" / "data" / "manuscript_claim_support.json").exists()
    assert (REPO / "output" / "data" / "curriculum_diagnostic_gap_map.json").exists()
    assert (REPO / "output" / "data" / "figure_table_companions.json").exists()
    assert (REPO / "output" / "data" / "manuscript_artifacts.json").exists()
    assert (REPO / "output" / "data" / "cover_asset_audit.json").exists()
    assert (REPO / "output" / "data" / "front_matter_visual_audit.json").exists()
    assert (REPO / "output" / "data" / "course_material_index.json").exists()
    assert (REPO / "output" / "data" / "course_material_audit.json").exists()
    assert (REPO / "output" / "figures" / "active_skillference_cover.png").exists()
    assert (
        REPO / "output" / "figures" / "active_skillference_skill_atlas.png"
    ).exists()
    assert (REPO / "output" / "figures" / "scholarship_coverage.png").exists()
    assert (REPO / "output" / "figures" / "open_science_source_map.png").exists()
    assert (REPO / "output" / "figures" / "scholarship_source_health.png").exists()
    assert (REPO / "output" / "figures" / "graph_bottlenecks.png").exists()
    assert (REPO / "output" / "figures" / "skill_neighborhood_paths.png").exists()
    assert (
        REPO / "output" / "figures" / "validation_intent_mismatch_matrix.png"
    ).exists()
    assert (
        REPO / "output" / "figures" / "visual_evidence_contract_ladder.png"
    ).exists()
    assert (REPO / "output" / "figures" / "validation_surface_matrix.png").exists()
    assert (REPO / "output" / "figures" / "scientific_evidence_matrix.png").exists()
    assert (REPO / "output" / "figures" / "kernel_sensitivity_profiles.png").exists()
    assert (REPO / "output" / "figures" / "vfe_efe_skilltree_bridge.png").exists()
    assert (REPO / "output" / "figures" / "roadmap_risk.png").exists()


def test_analyze_scholarship_script_runs_and_emits_audit() -> None:
    result = _run("analyze_scholarship.py")
    assert result.returncode == 0, result.stderr
    assert "scholarship coverage valid" in result.stdout
    assert "scholarship gap report valid" in result.stdout
    assert (REPO / "output" / "data" / "scholarship_coverage.json").exists()
    assert (REPO / "output" / "data" / "scholarship_source_health.json").exists()
    assert (
        REPO / "output" / "data" / "scholarship_source_health_network.json"
    ).exists()
    assert (REPO / "output" / "data" / "scholarship_gap_report.json").exists()
    assert (REPO / "output" / "figures" / "scholarship_coverage.png").exists()
    assert (REPO / "output" / "figures" / "open_science_source_map.png").exists()
    assert (REPO / "output" / "figures" / "scholarship_source_health.png").exists()


def test_audit_scholarship_gaps_script_runs_and_emits_report() -> None:
    result = _run("audit_scholarship_gaps.py")
    assert result.returncode == 0, result.stderr
    assert "scholarship gap report valid" in result.stdout
    assert (REPO / "output" / "data" / "scholarship_gap_report.json").exists()


def test_build_course_materials_script_runs_and_emits_artifacts() -> None:
    result = _run("build_course_materials.py")
    assert result.returncode == 0, result.stderr
    assert "course materials valid" in result.stdout
    assert (REPO / "output" / "data" / "course_material_index.json").exists()
    assert (REPO / "output" / "data" / "course_material_audit.json").exists()


def test_validate_course_material_sources_script_runs_offline() -> None:
    result = _run("validate_course_material_sources.py")
    assert result.returncode == 0, result.stderr
    assert "course material sources valid (offline)" in result.stdout


def test_validate_course_material_alignment_script_runs_after_exports() -> None:
    export = _run("export_skilltree.py")
    assert export.returncode == 0, export.stderr
    materials = _run("build_course_materials.py")
    assert materials.returncode == 0, materials.stderr

    result = _run("validate_course_material_alignment.py")

    assert result.returncode == 0, result.stderr
    assert "course material alignment valid" in result.stdout


def test_validate_manuscript_artifacts_script_runs_and_emits_audit() -> None:
    prep = _run("run_kernels.py")
    assert prep.returncode == 0, prep.stderr
    result = _run("validate_manuscript_artifacts.py")
    assert result.returncode == 0, result.stderr
    assert "manuscript artifacts valid" in result.stdout
    assert "cover asset valid" in result.stdout
    assert "page-two visual valid" in result.stdout
    assert (REPO / "output" / "data" / "manuscript_artifacts.json").exists()
    assert (REPO / "output" / "data" / "cover_asset_audit.json").exists()
    assert (REPO / "output" / "data" / "front_matter_visual_audit.json").exists()


def test_validate_manuscript_variables_script_runs_after_kernels() -> None:
    prep = _run("run_kernels.py")
    assert prep.returncode == 0, prep.stderr
    result = _run("validate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr
    assert "manuscript variable audit clean" in result.stdout


def test_validate_claim_support_script_runs_and_emits_audit() -> None:
    result = _run("validate_claim_support.py")
    assert result.returncode == 0, result.stderr
    assert "validated manuscript claim support" in result.stdout
    assert (REPO / "output" / "data" / "manuscript_claim_support.json").exists()


def test_validate_american_english_script_runs() -> None:
    result = _run("validate_american_english.py")
    assert result.returncode == 0, result.stderr
    assert "American English audit clean" in result.stdout


def test_validate_web_math_script_runs_with_rendered_html() -> None:
    web_dir = REPO / "output" / "web"
    web_dir.mkdir(parents=True, exist_ok=True)
    (web_dir / "math_smoke.html").write_text(
        """
        <!doctype html>
        <html>
          <head>
            <script id="MathJax-script" async
              src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js">
            </script>
          </head>
          <body>\\(F = E_q[\\ln q - \\ln p]\\)</body>
        </html>
        """,
        encoding="utf-8",
    )
    prep = _run("ensure_web_math.py")
    assert prep.returncode == 0, prep.stderr
    result = _run("validate_web_math.py")
    assert result.returncode == 0, result.stderr
    assert "web math validation clean" in result.stdout


def test_export_skilltree_script_runs_and_emits_project() -> None:
    result = _run("export_skilltree.py")
    assert result.returncode == 0, result.stderr
    out = REPO / "output" / "data" / "skilltree_project.json"
    assert out.exists()
    assert "{{claim" not in out.read_text()  # provenance tokens resolved


def test_seed_skilltree_script_skips_without_live_server() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "seed_skilltree.py"),
            "--base-url",
            "http://127.0.0.1:1",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "live SkillTree seed skipped" in result.stdout


def test_seed_skilltree_script_reports_auth_failure(httpserver) -> None:  # type: ignore[no-untyped-def]
    httpserver.expect_request(
        "/admin/projects/activeInference",
        method="POST",
    ).respond_with_data("unauthorized", status=401)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "seed_skilltree.py"),
            "--base-url",
            httpserver.url_for("").rstrip("/"),
            "--require-live",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "requires admin authentication" in result.stderr
    assert "Traceback" not in result.stderr


def test_seed_skilltree_uses_env_token_without_argv_exposure(httpserver) -> None:  # type: ignore[no-untyped-def]
    httpserver.expect_request(
        "/admin/projects/activeInference",
        method="POST",
        headers={"Authorization": "Bearer env-only-token"},
    ).respond_with_data("unauthorized", status=401)
    env = {**os.environ, "SKILLTREE_TOKEN": "env-only-token"}

    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "seed_skilltree.py"),
            "--base-url",
            httpserver.url_for("").rstrip("/"),
            "--require-live",
        ],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "requires admin authentication" in result.stderr
    assert "env-only-token" not in " ".join(str(arg) for arg in result.args)
    assert "env-only-token" not in result.stdout
    assert "env-only-token" not in result.stderr


def test_serve_learner_dashboard_check_runs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "serve_learner_dashboard.py"),
            "--skilltree-url",
            "http://127.0.0.1:9",
            "--authenticator",
            "pki",
            "--check",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"activeInference"' in result.stdout
    assert '"authenticator": "pki"' in result.stdout
    assert '"available": false' in result.stdout


def test_serve_learner_dashboard_reports_port_conflict() -> None:
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen()
        port = sock.getsockname()[1]
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "serve_learner_dashboard.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            check=False,
        )
    assert result.returncode == 1
    assert "port is already in use" in result.stderr


def test_validate_live_skilltree_dashboard_script_accepts_healthy_payload(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    project_path = tmp_path / "output" / "data" / "skilltree_project.json"
    project_path.parent.mkdir(parents=True)
    project_path.write_text(
        """
        {
          "projectId": "activeInference",
          "name": "Active Skillference",
          "subjects": [
            {
              "subjectId": "sub_skilltree_mastery_computation",
              "name": "SkillTree Mastery: Computational Contracts",
              "skills": [
                {"skillId": "mastery_computation_07", "name": "Route Handoff"}
              ]
            }
          ],
          "dependencies": [],
          "quizzes": [
            {"quizId": "mastery_computation_07_quiz", "name": "Route Handoff Quiz"}
          ]
        }
        """,
        encoding="utf-8",
    )
    from src.dashboard.artifacts import EXPECTED_ARTIFACT_COUNT

    base_url = httpserver.url_for("").rstrip("/")
    counts = {"subjects": 1, "skills": 1, "dependencies": 0, "quizzes": 1}
    # The validator now asserts the dashboard serves exactly the pinned artifact count,
    # so the healthy payload must present that many existing artifacts.
    served_artifacts = [
        {"id": f"artifact_{index}", "exists": True}
        for index in range(EXPECTED_ARTIFACT_COUNT)
    ]
    httpserver.expect_request("/public/status").respond_with_json({"status": "OK"})
    httpserver.expect_request("/api/status").respond_with_json(
        {
            "project": {
                "projectId": "activeInference",
                "name": "Active Skillference",
                "counts": counts,
            },
            "config": {
                "skilltree": {
                    "url": base_url,
                    "authenticatorConfigured": True,
                    "localAuth": {"ready": True},
                }
            },
            "skilltree": {"available": True, "statusCode": 200},
            "courseMaterials": {
                "available": True,
                "summary": {
                    "materialRecords": 1,
                    "externalPointers": 1,
                    "sections": 7,
                    "ok": True,
                },
            },
            "artifacts": served_artifacts,
        }
    )
    httpserver.expect_request("/api/course-materials").respond_with_json(
        {
            "available": True,
            "summary": {"skills": 1, "externalPointers": 1, "sources": 1},
            "skills": {
                "mastery_computation_07": {
                    "externalPointers": [
                        {"url": "https://github.com/example/repo/blob/abc/path.md"}
                    ],
                    "sections": [{"heading": "Concept", "body": "Route handoff"}],
                }
            },
        }
    )
    httpserver.expect_request("/api/skilltree/token").respond_with_json(
        {"access_token": "opaque-test-token", "token_type": "bearer"}
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "validate_live_skilltree_dashboard.py"),
            "--dashboard-url",
            base_url,
            "--skilltree-url",
            base_url,
            "--project-root",
            str(tmp_path),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert '"ok": true' in result.stdout
    assert '"skills": 1' in result.stdout


def _write_strict_live_dashboard_project(
    tmp_path: Path,
    *,
    registry_filename: str = "contract.png",
    write_figure_file: bool = True,
    registry_overrides: dict[str, object] | None = None,
) -> tuple[dict[str, int], dict[str, object]]:
    import json

    project_path = tmp_path / "output" / "data" / "skilltree_project.json"
    registry_path = tmp_path / "output" / "figures" / "figure_registry.json"
    project_path.parent.mkdir(parents=True)
    registry_path.parent.mkdir(parents=True)
    # A live dashboard is required to serve a clean manuscript artifact audit, so
    # the strict fixture carries one for its single registered figure.
    (tmp_path / "output" / "data" / "manuscript_artifacts.json").write_text(
        json.dumps(
            {
                "issues": [],
                "summary": {
                    "registeredFigures": 1,
                    "declaredFigureLabels": 1,
                    "referencedFigureLabels": 1,
                },
            }
        ),
        encoding="utf-8",
    )
    project_path.write_text(
        json.dumps(
            {
                "projectId": "activeInference",
                "name": "Active Skillference",
                "subjects": [
                    {
                        "subjectId": "sub_skilltree_mastery_computation",
                        "name": "SkillTree Mastery",
                        "skills": [{"skillId": "mastery_computation_07"}],
                    }
                ],
                "dependencies": [],
                "quizzes": [{"quizId": "mastery_computation_07_quiz"}],
            }
        ),
        encoding="utf-8",
    )
    registry_row: dict[str, object] = {
        "filename": registry_filename,
        "label": "fig:contract",
        "caption": "Runtime proof contract fixture for live dashboard validation.",
        "alt_text": "Runtime proof figure fixture linked through registry and dashboard metadata.",
        "generated_by": "tests.test_scripts_smoke._write_strict_live_dashboard_project",
        "chart_family": "runtime proof fixture",
        "question": "Which runtime proof is being checked?",
        "takeaway": "Strict runtime proof is present.",
        "data_sources": ["Generated SkillTree export.", "Dashboard status payload."],
        "data_source": "Generated SkillTree export and dashboard status payload.",
        "data_grain": "One generated runtime proof figure row for the live dashboard validator.",
        "encoding": "One figure row per runtime proof surface.",
        "palette_policy": "single-root preferred with neutral context and runtime-proof accents",
        "palette_roots": ["blue", "gray"],
        "non_color_encoding": "Direct labels and artifact links preserve the fixture reading without color.",
        "subtitle": "Source: strict live dashboard validator fixture.",
        "interpretation_boundary": "Fixture validates wiring only, not learner outcomes.",
        "static_read": "The static PNG is present and linked.",
        "false_certification_risk": "Reject stale or missing runtime proof.",
        "mobile_read": "The dashboard card remains readable on narrow screens.",
        "mobile_note": "The dashboard card remains readable on narrow screens.",
        "failure_mode": "Reject stale or missing runtime proof.",
        "accessibility_note": "Fixture metadata carries the read through text fields.",
        "qa_role": "Strict validator fixture for registry-dashboard contract parity.",
        "visual_grammar": "Runtime proof fixture uses direct labels, neutral context, and explicit status accents.",
        "claim_tokens": [],
    }
    if registry_overrides:
        registry_row.update(registry_overrides)
    registry_path.write_text(json.dumps([registry_row]), encoding="utf-8")
    if write_figure_file:
        (registry_path.parent / registry_filename).write_bytes(b"not-a-real-png")
    return {"subjects": 1, "skills": 1, "dependencies": 0, "quizzes": 1}, registry_row


def _serve_strict_live_dashboard_payload(
    httpserver,  # type: ignore[no-untyped-def]
    *,
    counts: dict[str, int],
    artifacts: list[dict[str, object]],
) -> str:
    base_url = httpserver.url_for("").rstrip("/")
    httpserver.expect_request("/public/status").respond_with_json({"status": "OK"})
    httpserver.expect_request("/api/status").respond_with_json(
        {
            "project": {
                "projectId": "activeInference",
                "name": "Active Skillference",
                "counts": counts,
            },
            "config": {
                "skilltree": {
                    "url": base_url,
                    "authenticatorConfigured": True,
                    "localAuth": {"ready": True},
                }
            },
            "skilltree": {"available": True, "statusCode": 200},
            "courseMaterials": {
                "available": True,
                "summary": {"materialRecords": 1, "externalPointers": 1},
            },
            "artifacts": artifacts,
        }
    )
    httpserver.expect_request("/api/course-materials").respond_with_json(
        {
            "available": True,
            "skills": {
                "mastery_computation_07": {
                    "externalPointers": [{"url": "https://example.test/material"}],
                }
            },
        }
    )
    return base_url


def _strict_artifacts(figure_row: dict[str, object]) -> list[dict[str, object]]:
    from src.dashboard.artifacts import EXPECTED_ARTIFACT_COUNT

    artifacts = [
        {
            "id": "contract",
            "path": "output/figures/contract.png",
            "mediaType": "image/png",
            "exists": True,
            "figure": figure_row,
        },
        {
            "id": "manuscript_artifacts",
            "path": "output/data/manuscript_artifacts.json",
            "mediaType": "application/json",
            "exists": True,
        },
    ]
    artifacts.extend(
        {"id": f"artifact_{index}", "exists": True}
        for index in range(EXPECTED_ARTIFACT_COUNT - 2)
    )
    return artifacts


def test_validate_live_skilltree_dashboard_strict_figure_contracts_pass(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import validate_live_skilltree_dashboard as validator

    counts, figure_row = _write_strict_live_dashboard_project(tmp_path)
    base_url = _serve_strict_live_dashboard_payload(
        httpserver,
        counts=counts,
        artifacts=_strict_artifacts(figure_row),
    )

    result = validator.validate_live_skilltree_dashboard(
        dashboard_url=base_url,
        skilltree_url=base_url,
        project_root=tmp_path,
        require_token=False,
        require_figure_contracts=True,
    )

    assert result["figureContracts"]["checked"] is True
    assert result["figureContracts"]["registered"] == 1


def test_validate_live_skilltree_dashboard_rejects_missing_registered_figure(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import validate_live_skilltree_dashboard as validator

    counts, figure_row = _write_strict_live_dashboard_project(
        tmp_path,
        write_figure_file=False,
    )
    base_url = _serve_strict_live_dashboard_payload(
        httpserver,
        counts=counts,
        artifacts=_strict_artifacts(figure_row),
    )

    try:
        validator.validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
            require_token=False,
            require_figure_contracts=True,
        )
    except validator.LiveSkillTreeDashboardError as exc:
        assert "registered figure file is missing" in str(exc)
    else:
        raise AssertionError("missing registered figure unexpectedly passed")


def test_validate_live_skilltree_dashboard_rejects_missing_dashboard_figure(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    from src.dashboard.artifacts import EXPECTED_ARTIFACT_COUNT

    sys.path.insert(0, str(REPO / "scripts"))
    import validate_live_skilltree_dashboard as validator

    counts, _figure_row = _write_strict_live_dashboard_project(tmp_path)
    artifacts = [
        {"id": f"artifact_{index}", "exists": True}
        for index in range(EXPECTED_ARTIFACT_COUNT)
    ]
    base_url = _serve_strict_live_dashboard_payload(
        httpserver,
        counts=counts,
        artifacts=artifacts,
    )

    try:
        validator.validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
            require_token=False,
            require_figure_contracts=True,
        )
    except validator.LiveSkillTreeDashboardError as exc:
        assert "registered figures missing from dashboard artifacts" in str(exc)
    else:
        raise AssertionError("missing dashboard figure unexpectedly passed")


def test_validate_live_skilltree_dashboard_rejects_missing_contract_field(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import validate_live_skilltree_dashboard as validator

    counts, figure_row = _write_strict_live_dashboard_project(
        tmp_path,
        registry_overrides={"mobile_read": ""},
    )
    base_url = _serve_strict_live_dashboard_payload(
        httpserver,
        counts=counts,
        artifacts=_strict_artifacts(figure_row),
    )

    try:
        validator.validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
            require_token=False,
            require_figure_contracts=True,
        )
    except validator.LiveSkillTreeDashboardError as exc:
        assert "mobile_read" in str(exc)
    else:
        raise AssertionError("missing chart-contract field unexpectedly passed")


def test_validate_live_skilltree_dashboard_rejects_missing_canonical_field(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import validate_live_skilltree_dashboard as validator

    counts, figure_row = _write_strict_live_dashboard_project(
        tmp_path,
        registry_overrides={"palette_policy": ""},
    )
    base_url = _serve_strict_live_dashboard_payload(
        httpserver,
        counts=counts,
        artifacts=_strict_artifacts(figure_row),
    )

    try:
        validator.validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
            require_token=False,
            require_figure_contracts=True,
        )
    except validator.LiveSkillTreeDashboardError as exc:
        assert "palette_policy" in str(exc)
    else:
        raise AssertionError(
            "missing canonical chart-contract field unexpectedly passed"
        )


def test_validate_live_skilltree_dashboard_rejects_missing_live_dependency(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    from src.dashboard.artifacts import EXPECTED_ARTIFACT_COUNT
    from src.skilltree.local_auth import LocalSkillTreeState, save_local_state

    sys.path.insert(0, str(REPO / "scripts"))
    import validate_live_skilltree_dashboard as validator

    project_path = tmp_path / "output" / "data" / "skilltree_project.json"
    project_path.parent.mkdir(parents=True)
    project_path.write_text(
        json.dumps(
            {
                "projectId": "activeInference",
                "name": "Active Skillference",
                "subjects": [
                    {
                        "subjectId": "sub_math",
                        "name": "Math",
                        "skills": [
                            {"skillId": "root", "name": "Root"},
                            {"skillId": "leaf", "name": "Leaf"},
                        ],
                    }
                ],
                "dependencies": [{"skillId": "leaf", "dependsOnSkillId": "root"}],
                "quizzes": [],
            }
        ),
        encoding="utf-8",
    )
    base_url = httpserver.url_for("").rstrip("/")
    state_dir = tmp_path / "state"
    save_local_state(
        state_dir,
        LocalSkillTreeState(
            admin_username="active-skillference-admin@localhost.invalid",
            admin_password="active-skillference-local",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url=base_url,
            client_secret="do-not-print",
        ),
    )
    httpserver.expect_request("/public/status").respond_with_json({"status": "OK"})
    httpserver.expect_request("/api/status").respond_with_json(
        {
            "project": {
                "projectId": "activeInference",
                "name": "Active Skillference",
                "dependencies": [{"skillId": "leaf", "dependsOnSkillId": "root"}],
                "counts": {
                    "subjects": 1,
                    "skills": 2,
                    "dependencies": 1,
                    "quizzes": 0,
                },
            },
            "config": {
                "skilltree": {
                    "url": base_url,
                    "authenticatorConfigured": True,
                    "localAuth": {"ready": True},
                }
            },
            "skilltree": {"available": True, "statusCode": 200},
            "courseMaterials": {
                "available": True,
                "summary": {"materialRecords": 2, "externalPointers": 2},
            },
            "artifacts": [
                {"id": f"artifact_{index}", "exists": True}
                for index in range(EXPECTED_ARTIFACT_COUNT)
            ],
        }
    )
    httpserver.expect_request("/api/course-materials").respond_with_json(
        {
            "available": True,
            "skills": {
                "root": {"externalPointers": [{"url": "https://example.test/root"}]},
                "leaf": {"externalPointers": [{"url": "https://example.test/leaf"}]},
            },
        }
    )
    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>",
        headers={"Set-Cookie": "XSRF-TOKEN=csrf-token; Path=/"},
        content_type="text/html",
    )
    httpserver.expect_request("/performLogin", method="POST").respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/dependency/graph", method="GET"
    ).respond_with_json(
        {
            "nodes": [
                {"id": 1, "skillId": "root"},
                {"id": 2, "skillId": "leaf"},
            ],
            "edges": [],
        }
    )

    try:
        validator.validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
            local_state_dir=state_dir,
            require_token=False,
            require_live_dependencies=True,
        )
    except validator.LiveSkillTreeDashboardError as exc:
        assert "live SkillTree dependency parity failed" in str(exc)
        assert "1/1" not in str(exc)
    else:
        raise AssertionError("missing live dependency unexpectedly passed")


def test_bootstrap_show_local_credentials_reads_ignored_state(tmp_path: Path) -> None:
    from src.skilltree.local_auth import LocalSkillTreeState, save_local_state

    save_local_state(
        tmp_path,
        LocalSkillTreeState(
            admin_username="active-skillference-admin@localhost.invalid",
            admin_password="active-skillference-local",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url="http://localhost:8080",
            client_secret="do-not-print",
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "bootstrap_local_skilltree.py"),
            "--state-dir",
            str(tmp_path),
            "--show-local-credentials",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "local development credentials only" in result.stderr
    assert "active-skillference-admin@localhost.invalid" in result.stdout
    assert "active-skillference-local" in result.stdout
    assert '"browserLoginUsable": true' in result.stdout
    assert "do-not-print" not in result.stdout


def test_bootstrap_show_local_credentials_warns_on_legacy_browser_login(
    tmp_path: Path,
) -> None:
    from src.skilltree.local_auth import LocalSkillTreeState, save_local_state

    save_local_state(
        tmp_path,
        LocalSkillTreeState(
            admin_username="active_skillference_admin",
            admin_password="legacy-password",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url="http://localhost:8080",
            client_secret="do-not-print",
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "bootstrap_local_skilltree.py"),
            "--state-dir",
            str(tmp_path),
            "--show-local-credentials",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "non-email-shaped" in result.stderr
    assert '"browserLoginUsable": false' in result.stdout
    assert "legacy-password" in result.stdout
    assert "do-not-print" not in result.stdout


def test_bootstrap_show_local_credentials_fails_when_state_is_missing(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "bootstrap_local_skilltree.py"),
            "--state-dir",
            str(tmp_path / "missing"),
            "--show-local-credentials",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "local SkillTree credentials are missing" in result.stderr
