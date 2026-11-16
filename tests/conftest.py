"""Pytest configuration for Active Skillference tests."""

import os
import sys

import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Keep the project root and src/ importable when pytest is invoked directly: the
# pyproject `pythonpath` already provides both, but a bare `pytest` started from a
# subdirectory would otherwise miss them. The project is self-contained — there is no
# outer repository whose root has to be added.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
for _path in (ROOT, SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)



@pytest.fixture
def skilltree_admin_content():
    """Serve actual model content over loopback, including private answer keys."""
    def serve(httpserver, project, *, initially_missing=False, quiz_settings=None):
        payload = project.to_export_dict() if hasattr(project, "to_export_dict") else project
        root = f"/admin/projects/{payload['projectId']}"
        import json
        from werkzeug.wrappers import Response

        root_requests = 0

        def project_response(request):
            nonlocal root_requests
            root_requests += 1
            missing = initially_missing and root_requests == 1
            body = {"error": "not found"} if missing else {
                "projectId": payload["projectId"], "name": payload["name"],
                "numSubjects": len(payload["subjects"]),
                "numSkills": sum(len(subject["skills"]) for subject in payload["subjects"]),
            }
            return Response(json.dumps(body), status=404 if missing else 200, content_type="application/json")

        httpserver.expect_request(root, method="GET").respond_with_handler(project_response)
        httpserver.expect_request(f"{root}/subjects", method="GET").respond_with_json(
            payload["subjects"]
        )
        for subject in payload["subjects"]:
            subject_path = f"{root}/subjects/{subject['subjectId']}"
            httpserver.expect_request(subject_path, method="GET").respond_with_json(subject)
            httpserver.expect_request(f"{subject_path}/skills", method="GET").respond_with_json(
                subject["skills"]
            )
            for skill in subject["skills"]:
                httpserver.expect_request(
                    f"{subject_path}/skills/{skill['skillId']}", method="GET",
                ).respond_with_json(skill)
        for quiz in payload["quizzes"]:
            quiz_path = f"/admin/quiz-definitions/{quiz['quizId']}"
            httpserver.expect_request(quiz_path, method="GET").respond_with_json({
                key: quiz[key] for key in ("quizId", "name", "type")
            })
            httpserver.expect_request(f"{quiz_path}/settings", method="GET").respond_with_json(
                (quiz_settings or {}).get(quiz["quizId"], [])
            )
            questions = [] if initially_missing else list(quiz["questions"])

            def read_questions(_request, rows=questions):
                return Response(
                    json.dumps({"questions": rows}), content_type="application/json",
                )

            def create_question(request, rows=questions):
                rows.append(request.get_json())
                return Response("{}", content_type="application/json")

            httpserver.expect_request(f"{quiz_path}/questions", method="GET").respond_with_handler(
                read_questions
            )
            if initially_missing:
                httpserver.expect_request(
                    f"{quiz_path}/create-question", method="POST",
                ).respond_with_handler(create_question)
    return serve


@pytest.fixture
def content_project():
    from src.skilltree.model import Quiz, QuizQuestion, SkillTreeProject, SkillTreeSkill, SkillTreeSubject

    quiz = Quiz(
        quiz_id="q", name="Quiz",
        questions=[
            QuizQuestion(question="First?", answers=[{"answer": "one", "isCorrect": True}]),
            QuizQuestion(question="Second?", answers=[{"answer": "two", "isCorrect": True}]),
        ],
    )
    return SkillTreeProject(
        project_id="p", name="Project",
        subjects=[SkillTreeSubject(
            subject_id="s", name="Subject", description="Subject content",
            skills=[SkillTreeSkill(
                skill_id="k", name="Skill", description="Lesson content",
                self_reporting_type="Quiz", quiz_id="q",
            )],
        )],
        quizzes=[quiz],
    )


@pytest.fixture
def pdf_bytes():
    """Build a structurally valid one-page PDF, not a copied historical output."""
    def make(text="Fixture image"):
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 18 Tf 20 120 Td ({escaped}) Tj ET\n".encode("ascii")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
        ]
        content = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for index, body in enumerate(objects, 1):
            offsets.append(len(content))
            content.extend(f"{index} 0 obj\n".encode("ascii") + body + b"\nendobj\n")
        xref = len(content)
        content.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
        for offset in offsets:
            content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        content.extend(
            f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
        )
        return bytes(content)
    return make


@pytest.fixture
def pdf_project(tmp_path, pdf_bytes):
    """Create disposable source inputs and observe their real local Git revision."""
    import os
    import subprocess

    from src.manuscript.pdf_receipt import PDF_NAME, add_pdf_assets, capture_pdf_inputs

    root = tmp_path / "publication"
    manuscript = root / "manuscript"
    hydrated = root / "output" / "manuscript"
    manuscript.mkdir(parents=True)
    hydrated.mkdir(parents=True)
    assets_dir = hydrated / "assets"
    assets_dir.mkdir()
    assets = [assets_dir / name for name in ("cover.pdf", "atlas.pdf", "body.pdf")]
    for path, label in zip(assets, ("CoverGraphic", "AtlasGraphic", "BodyGraphic"), strict=True):
        path.write_bytes(pdf_bytes(label))
    (manuscript / "config.yaml").write_text(
        "paper:\n  title: FixtureTitlePage\n"
        "authors:\n  - name: Fixture Author\n"
        "book:\n  cover:\n    image: assets/cover.pdf\n"
        "front_matter:\n  page_two_visual:\n    image: assets/atlas.pdf\n"
        "    title: FixtureAtlasPage\n    caption: FixtureAtlasCaption\n",
        encoding="utf-8",
    )
    (manuscript / "preamble.md").write_text("```latex\n\\usepackage{graphicx}\n```\n", encoding="utf-8")
    (manuscript / "references.bib").write_text(
        "@book{fixture,\n title={Fixture Publication},\n author={Example, Test},\n"
        " year={2020},\n publisher={Fixture Press}\n}\n",
        encoding="utf-8",
    )
    section = hydrated / "01_fixture.md"
    section.write_text(
        f"# FixtureBodySection\n\nA cited statement [@fixture].\n\n![Body image]({assets[2].as_posix()})\n",
        encoding="utf-8",
    )
    target = root / "output" / "pdf" / PDF_NAME
    target.parent.mkdir()
    target.write_bytes(pdf_bytes("Finalized fixture PDF"))
    git_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    git_env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    subprocess.run(["git", "init", "--quiet", str(root)], env=git_env, check=True)
    subprocess.run(["git", "add", "."], cwd=root, env=git_env, check=True)
    subprocess.run(
        [
            "git", "-c", "user.name=Receipt Test", "-c", "user.email=receipt@example.org",
            "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
            "commit", "--quiet", "-m", "Disposable publication source",
        ],
        cwd=root, env=git_env, check=True,
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, env=git_env,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    inputs = add_pdf_assets(root, capture_pdf_inputs(root, [section]), assets)
    return {
        "root": root, "section": section, "assets": assets, "target": target,
        "revision": revision, "inputs": inputs, "git_env": git_env,
    }
