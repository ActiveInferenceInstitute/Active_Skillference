"""Documentation inventory drift checks."""

from __future__ import annotations

import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from src.figures.plots import planned_figure_registry_entries
from src.kernels.examples import build_claim_registry

REPO = Path(__file__).resolve().parents[1]
VISUAL_QA_FIELDS = {
    "data_grain",
    "failure_mode",
    "mobile_read",
    "question",
    "palette_policy",
    "palette_roots",
    "non_color_encoding",
    "static_read",
    "takeaway",
}


def _script_names() -> set[str]:
    return {
        path.name
        for path in (REPO / "scripts").iterdir()
        if path.is_file()
        and path.suffix in {".py", ".sh"}
        and path.name != "__init__.py"
    }


def test_docs_agents_inventory_lists_every_docs_markdown_file() -> None:
    docs_dir = REPO / "docs"
    actual = {path.name for path in docs_dir.glob("*.md")}
    text = (docs_dir / "AGENTS.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s+`([^`]+\.md)`\s+\|\s+([^|]+?)\s+\|$", text, re.MULTILINE)
    documented = {name for name, _purpose in rows}
    terse = [
        name for name, purpose in rows if len(re.findall(r"[A-Za-z0-9]+", purpose)) < 4
    ]

    assert actual - documented == set()
    assert documented - actual == set()
    assert terse == []


def test_docs_todo_pages_match_active_roadmap_and_are_signposted() -> None:
    payload = yaml.safe_load((REPO / "tasks.yaml").read_text(encoding="utf-8"))
    active_ids = {
        str(task["id"])
        for task in payload["tasks"]
        if task["status"] in {"todo", "in_progress", "blocked"}
    }
    detail_dir = REPO / "docs" / "todo"
    actual_ids = {path.stem for path in detail_dir.glob("*.md")}
    todo_text = (REPO / "TODO.md").read_text(encoding="utf-8")
    docs_text = "\n".join(
        (
            (REPO / "docs" / "README.md").read_text(encoding="utf-8"),
            (REPO / "docs" / "AGENTS.md").read_text(encoding="utf-8"),
        )
    )

    assert actual_ids == active_ids
    assert "docs/todo/" in docs_text
    for task_id in active_ids:
        path = f"docs/todo/{task_id}.md"
        page = (detail_dir / f"{task_id}.md").read_text(encoding="utf-8")
        assert f"]({path})" in todo_text
        assert f"- Task id: `{task_id}`" in page
        for heading in (
            "## Deliverables",
            "## Out of Scope",
            "## Evidence Commands",
            "## Acceptance Criteria",
        ):
            assert heading in page


def test_script_inventories_mention_every_top_level_orchestrator() -> None:
    scripts = _script_names()
    script_ref = re.compile(r"`([A-Za-z0-9_]+(?:\.py|\.sh))`")
    for docs_path in (REPO / "docs" / "AGENTS.md", REPO / "scripts" / "README.md"):
        docs_text = docs_path.read_text(encoding="utf-8")
        mentioned = set(script_ref.findall(docs_text))
        missing = sorted(scripts - mentioned)

        assert missing == [], docs_path

    scripts_readme = (REPO / "scripts" / "README.md").read_text(encoding="utf-8")
    table_scripts = set(
        re.findall(
            r"^\|\s+`([A-Za-z0-9_]+(?:\.py|\.sh))`\s+\|", scripts_readme, re.MULTILINE
        )
    )
    assert scripts - table_scripts == set()
    assert table_scripts - scripts == set()


def test_output_inventory_lists_exact_planned_figure_outputs() -> None:
    entries = planned_figure_registry_entries(
        include_scholarship=True,
        include_claim_support=True,
        include_roadmap=True,
    )
    expected = {str(entry["filename"]) for entry in entries}
    expected.update(
        {
            "active_skillference_cover.png",
            "active_skillference_skill_atlas.png",
            "figure_registry.json",
        }
    )
    text = (REPO / "docs" / "output_inventory.md").read_text(encoding="utf-8")
    documented = set(
        re.findall(r"^\|\s+`output/figures/([^`]+)`\s+\|", text, re.MULTILINE)
    )

    assert expected - documented == set()
    assert documented - expected == set()


def test_figure_documentation_mentions_planned_registry_outputs_and_qa_fields() -> None:
    entries = planned_figure_registry_entries(
        include_scholarship=True,
        include_claim_support=True,
        include_roadmap=True,
    )
    filenames = {str(entry["filename"]) for entry in entries}
    docs = {
        "docs/AGENTS.md": (REPO / "docs" / "AGENTS.md").read_text(encoding="utf-8"),
        "docs/rendering_pipeline.md": (
            REPO / "docs" / "rendering_pipeline.md"
        ).read_text(encoding="utf-8"),
        "docs/syntax_guide.md": (REPO / "docs" / "syntax_guide.md").read_text(
            encoding="utf-8"
        ),
        "manuscript/AGENTS.md": (REPO / "manuscript" / "AGENTS.md").read_text(
            encoding="utf-8"
        ),
    }
    for docs_path, text in docs.items():
        missing = sorted(filename for filename in filenames if filename not in text)
        assert missing == [], docs_path

    contract_docs = (
        "\n".join(docs.values())
        + "\n"
        + (REPO / "docs" / "output_inventory.md").read_text(encoding="utf-8")
    )
    missing_fields = sorted(
        field for field in VISUAL_QA_FIELDS if field not in contract_docs
    )
    assert missing_fields == []


def test_syntax_guide_claim_table_matches_live_registry() -> None:
    text = (REPO / "docs" / "syntax_guide.md").read_text(encoding="utf-8")
    documented = {
        (name, source, units.strip())
        for name, source, units in re.findall(
            r"^\|\s+`\{\{claim:([^}]+)\}\}`\s+\|\s+`([^`]+)`\s+\|\s+([^|]+?)\s+\|$",
            text,
            re.MULTILINE,
        )
    }
    registry = build_claim_registry()
    expected = set()
    for name in registry.names():
        claim = registry.get(name)
        expected.add((name, claim.source.rsplit(".", 1)[-1] + "()", claim.units or "-"))

    assert documented == expected


def test_docs_describe_current_visual_contract_without_stale_route_language() -> None:
    docs = {
        "docs/output_conventions.md": (
            REPO / "docs" / "output_conventions.md"
        ).read_text(encoding="utf-8"),
        "docs/forking_guide.md": (REPO / "docs" / "forking_guide.md").read_text(
            encoding="utf-8"
        ),
        "docs/syntax_guide.md": (REPO / "docs" / "syntax_guide.md").read_text(
            encoding="utf-8"
        ),
    }
    for docs_path, text in docs.items():
        missing = sorted(field for field in VISUAL_QA_FIELDS if field not in text)
        assert missing == [], docs_path

    syntax = docs["docs/syntax_guide.md"]
    assert "quiz IDs and route fragments" not in syntax
    assert "learn-route fragments and quiz-route fragments" in syntax
