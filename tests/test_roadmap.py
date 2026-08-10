"""Tests for roadmap and repo-wide live-count drift validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from src.live_counts import (
    LiveCountError,
    LiveCountIssue,
    _as_int,
    audit_live_count_literals,
    build_live_counts,
    validate_live_count_literals,
)
from src.roadmap import (
    RoadmapError,
    RoadmapIssue,
    _audit_metric_block,
    audit_roadmap,
    load_roadmap,
    render_todo,
    render_todo_detail_pages,
    validate_roadmap,
    write_todo_surfaces,
)

REPO = Path(__file__).resolve().parents[1]


def test_real_roadmap_and_todo_are_current() -> None:
    validate_roadmap(REPO)


def test_real_authored_surfaces_do_not_carry_stale_live_counts() -> None:
    assert audit_live_count_literals(REPO) == []


def test_roadmap_rejects_stale_project_metrics(tmp_path: Path) -> None:
    roadmap = yaml.safe_load((REPO / "tasks.yaml").read_text(encoding="utf-8"))
    roadmap["project"]["live_metrics"]["skills"] = 1
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(roadmap), encoding="utf-8")
    (tmp_path / "TODO.md").write_text(render_todo(roadmap), encoding="utf-8")
    _copy_minimal_source_surfaces(tmp_path)

    with pytest.raises(RoadmapError, match="stale metric"):
        validate_roadmap(tmp_path)


def test_roadmap_rejects_stale_todo(tmp_path: Path) -> None:
    roadmap = yaml.safe_load((REPO / "tasks.yaml").read_text(encoding="utf-8"))
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(roadmap), encoding="utf-8")
    (tmp_path / "TODO.md").write_text("# stale\n", encoding="utf-8")
    _copy_minimal_source_surfaces(tmp_path)

    with pytest.raises(RoadmapError, match="TODO.md is stale"):
        validate_roadmap(tmp_path)


def test_live_count_audit_rejects_stale_authored_count(tmp_path: Path) -> None:
    _copy_minimal_source_surfaces(tmp_path)
    (tmp_path / "README.md").write_text(
        "Old export had 248 skills.\n", encoding="utf-8"
    )

    issues = audit_live_count_literals(tmp_path)

    assert any(issue.key == "skill_count" and issue.found == 248 for issue in issues)


def test_live_count_audit_reports_historical_count_mentions(
    tmp_path: Path,
) -> None:
    _copy_minimal_source_surfaces(tmp_path)
    (tmp_path / "README.md").write_text(
        "An earlier curriculum had 599 skills total.\n"
        "This release retains a prior export count of 248 skills.\n"
        "Historical documentation lists 248 skills.\n",
        encoding="utf-8",
    )

    issues = audit_live_count_literals(tmp_path)

    assert any(issue.key == "skill_count" and issue.found == 599 for issue in issues)
    assert (
        sum(issue.key == "skill_count" and issue.found == 248 for issue in issues) == 2
    )


def test_live_count_audit_rejects_stale_yaml_count_literal(tmp_path: Path) -> None:
    _copy_minimal_source_surfaces(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "counts.yaml").write_text("skills: 599\n", encoding="utf-8")

    issues = audit_live_count_literals(tmp_path)

    assert any(issue.key == "skill_count" and issue.found == 599 for issue in issues)


def _valid_roadmap_payload() -> dict:
    """Build a minimal, fully valid roadmap payload using real live counts."""
    counts = build_live_counts(REPO)
    metrics = {
        "skills": counts["skill_count"].value,
        "subjects": counts["subject_count"].value,
        "prerequisite_edges": counts["edge_count"].value,
        "dependencies": counts["edge_count"].value,
        "quizzes": counts["quiz_count"].value,
        "assessments": counts["assessment_count"].value,
        "claims": counts["claim_count"].value,
        "figures": counts["figure_count"].value,
        "cited_sources": counts["citation_count"].value,
        "max_depth": counts["max_depth"].value,
    }
    return {
        "project": {
            "title": "Active Skillference - Active Inference micro-learning platform",
            "status": "active",
            "updated": "2026-06-15",
            "live_metrics": dict(metrics),
        },
        "tasks": [
            {
                "id": "asf-example-done",
                "title": "An example completed task",
                "status": "done",
                "surface": "roadmap",
                "owner": "src.roadmap",
                "metrics": {"skills": metrics["skills"]},
                "evidence": ["uv run python scripts/validate_roadmap.py"],
                "notes": "A completed milestone with evidence.",
            },
            {
                "id": "asf-example-open",
                "title": "An example open task",
                "status": "todo",
                "scale": "medium",
                "surface": "dashboard",
                "owner": "src.dashboard",
                "metrics": {"subjects": metrics["subjects"]},
                "evidence": ["uv run pytest tests/test_dashboard.py -q"],
                "notes": "An open task to keep the roadmap honest.",
                "scholarship_plan": {
                    "lanes": ["delivery_and_reporting"],
                    "existing_source_keys": ["skilltree2026docs"],
                    "planned_source_targets": [
                        {
                            "key": "example_source",
                            "status": "planned",
                            "locator": "url:https://example.org/source",
                            "role": "Example delivery and reporting source.",
                        }
                    ],
                    "claim_support_types": ["delivery", "scope_limit"],
                    "boundaries": ["This plan does not establish learner outcomes."],
                    "phase_exit": ["The source role and boundary are audited."],
                },
            },
        ],
    }


def _write_roadmap(tmp_path: Path, payload: dict) -> None:
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    (tmp_path / "TODO.md").write_text(render_todo(payload), encoding="utf-8")
    detail_dir = tmp_path / "docs" / "todo"
    detail_dir.mkdir(parents=True, exist_ok=True)
    for filename, text in render_todo_detail_pages(payload).items():
        (detail_dir / filename).write_text(text, encoding="utf-8")
    _copy_minimal_source_surfaces(tmp_path)


def test_valid_roadmap_payload_passes(tmp_path: Path) -> None:
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    assert audit_roadmap(tmp_path) == []


def test_load_roadmap_rejects_non_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "tasks.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(RoadmapError, match="must contain a YAML mapping"):
        load_roadmap(bad)


def test_roadmap_rejects_non_mapping_project(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["project"] = ["not", "a", "mapping"]
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert issues == [RoadmapIssue("project", "project metadata must be a mapping")]


def test_roadmap_rejects_wrong_title(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["project"]["title"] = "Some Other Title"
    _write_roadmap(tmp_path, payload)
    issues = audit_roadmap(tmp_path)
    assert any(issue.location == "project.title" for issue in issues)


def test_roadmap_rejects_missing_updated(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["project"]["updated"] = "   "
    _write_roadmap(tmp_path, payload)
    issues = audit_roadmap(tmp_path)
    assert any(issue.location == "project.updated" for issue in issues)


def test_audit_metric_block_requires_present_block_when_require_all() -> None:
    # When require_all is set (the project.live_metrics path), a None block is an
    # error; an absent task-level block (require_all default) is silently allowed.
    live = build_live_counts(REPO)

    required: list[RoadmapIssue] = []
    _audit_metric_block(None, "project.live_metrics", live, required, require_all=True)
    assert required == [
        RoadmapIssue("project.live_metrics", "metric block is required")
    ]

    optional: list[RoadmapIssue] = []
    _audit_metric_block(None, "tasks[0].metrics", live, optional)
    assert optional == []


def test_audit_metric_block_rejects_non_mapping_block() -> None:
    live = build_live_counts(REPO)
    issues: list[RoadmapIssue] = []
    _audit_metric_block([1, 2, 3], "project.live_metrics", live, issues)
    assert issues == [RoadmapIssue("project.live_metrics", "metrics must be a mapping")]


def test_audit_metric_block_reports_missing_required_metrics() -> None:
    live = build_live_counts(REPO)
    block = {"skills": live["skill_count"].value}
    issues: list[RoadmapIssue] = []
    _audit_metric_block(block, "project.live_metrics", live, issues, require_all=True)
    assert any(
        issue.location == "project.live_metrics"
        and "missing metrics:" in issue.message
        and "max_depth" in issue.message
        for issue in issues
    )


def test_roadmap_rejects_unknown_metric_key(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["tasks"][0]["metrics"] = {"bogus_metric": 5}
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "tasks[0].metrics.bogus_metric"
        and issue.message == "unknown metric key"
        for issue in issues
    )


def test_roadmap_rejects_non_integer_metric_value(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["tasks"][0]["metrics"] = {"skills": "lots"}
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "tasks[0].metrics.skills"
        and "must be an integer" in issue.message
        for issue in issues
    )


def test_roadmap_rejects_empty_tasks_list(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["tasks"] = []
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert issues[-1] == RoadmapIssue("tasks", "tasks must be a non-empty list")


def test_roadmap_rejects_non_mapping_task(tmp_path: Path) -> None:
    # A non-mapping task is recorded as an issue (location tasks[N]). render_todo is
    # called after collecting issues but is now guarded, so a structurally malformed
    # roadmap returns its findings (including a "too malformed to render" note) instead
    # of raising a raw TypeError, and validate_roadmap surfaces them as a RoadmapError.
    payload = _valid_roadmap_payload()
    payload["tasks"].append("not a mapping")
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert issues, "a malformed task must yield issues, not an empty list"
    assert any("malformed to render" in str(issue) for issue in issues)
    with pytest.raises(RoadmapError):
        validate_roadmap(tmp_path)


def test_roadmap_rejects_task_field_violations(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    # A task that violates id, title, status, surface, owner, evidence, notes at once.
    # evidence is a non-list so the format branch (not just done-evidence) fires.
    payload["tasks"][1] = {
        "id": "",
        "title": "   ",
        "status": "not-a-status",
        "surface": "not-a-surface",
        "owner": "",
        "evidence": "not-a-list",
        "notes": "",
    }
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    locations = {issue.location for issue in audit_roadmap(tmp_path)}
    for suffix in (
        "tasks[1]",
        "tasks[1].title",
        "tasks[1].status",
        "tasks[1].surface",
        "tasks[1].owner",
        "tasks[1].evidence",
        "tasks[1].notes",
    ):
        assert suffix in locations


def test_roadmap_rejects_duplicate_task_id(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["tasks"][1]["id"] = payload["tasks"][0]["id"]
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "tasks[1].id" and "duplicate id" in issue.message
        for issue in issues
    )


def test_roadmap_rejects_open_task_without_scale(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["tasks"][1].pop("scale")
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "tasks[1].scale" and "open tasks require" in issue.message
        for issue in issues
    )


def test_roadmap_rejects_done_task_without_evidence(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    # Keep evidence a list (so the list/string check passes) but make it empty,
    # so the done-requires-evidence branch fires distinctly.
    payload["tasks"][0]["evidence"] = []
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "tasks[0].evidence"
        and issue.message == "done tasks require evidence"
        for issue in issues
    )


def test_roadmap_reports_missing_todo_file(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    _copy_minimal_source_surfaces(tmp_path)
    # Intentionally do not write TODO.md.
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "TODO.md" and "missing" in issue.message for issue in issues
    )


def test_validate_roadmap_raises_on_issues(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["project"]["updated"] = ""
    _write_roadmap(tmp_path, payload)
    with pytest.raises(RoadmapError, match="roadmap validation failed"):
        validate_roadmap(tmp_path)


def test_render_todo_with_no_open_tasks() -> None:
    payload = _valid_roadmap_payload()
    payload["tasks"] = [payload["tasks"][0]]  # only the done task remains
    rendered = render_todo(payload)
    assert "- No open roadmap tasks." in rendered
    assert "Completed Milestones" not in rendered
    assert "[x]" not in rendered
    assert payload["tasks"][0]["id"] not in rendered


def test_render_todo_marks_all_open_statuses() -> None:
    payload = _valid_roadmap_payload()
    base = payload["tasks"][1]
    payload["tasks"] = [
        {**base, "id": "open-todo", "status": "todo"},
        {**base, "id": "open-progress", "status": "in_progress"},
        {**base, "id": "open-blocked", "status": "blocked"},
    ]
    rendered = render_todo(payload)
    assert "[ ] **[open-todo](docs/todo/open-todo.md)**" in rendered
    assert "[~] **[open-progress](docs/todo/open-progress.md)**" in rendered
    assert "[!] **[open-blocked](docs/todo/open-blocked.md)**" in rendered


def test_render_todo_groups_open_tasks_by_scale_with_scope_and_evidence() -> None:
    payload = _valid_roadmap_payload()
    base = payload["tasks"][1]
    payload["tasks"] = [
        {
            **base,
            "id": "open-minor",
            "scale": "minor",
            "notes": "Tighten a local reader-facing edge.",
        },
        {
            **base,
            "id": "open-major",
            "scale": "major",
            "deps": ["open-minor"],
        },
    ]
    rendered = render_todo(payload)

    assert "### Minor Improvements" in rendered
    assert "### Major Improvements" in rendered
    assert "**[open-minor](docs/todo/open-minor.md)**" in rendered
    assert "Scope: Tighten a local reader-facing edge." in rendered
    assert "Evidence: `uv run pytest tests/test_dashboard.py -q`" in rendered
    assert "Depends on: `open-minor`" in rendered


def test_render_todo_detail_pages_scope_active_tasks_only() -> None:
    payload = _valid_roadmap_payload()
    base = payload["tasks"][1]
    payload["tasks"] = [
        payload["tasks"][0],
        {
            **base,
            "id": "open-blocked",
            "status": "blocked",
            "scale": "medium",
            "deps": ["asf-example-done"],
            "notes": "Blocked until docker info reported: daemon unavailable.",
        },
    ]

    pages = render_todo_detail_pages(payload)
    rendered = pages["open-blocked.md"]

    assert set(pages) == {"open-blocked.md"}
    assert "# An example open task" in rendered
    assert "- Task id: `open-blocked`" in rendered
    assert "- Status: `blocked`" in rendered
    assert "- Depends on: `asf-example-done`" in rendered
    assert "- Current blocker: daemon unavailable." in rendered
    assert "## Deliverables" in rendered
    assert "## Out of Scope" in rendered
    assert "## Acceptance Criteria" in rendered
    assert "uv run pytest tests/test_dashboard.py -q" in rendered


def test_render_todo_includes_scholarship_lane() -> None:
    payload = _valid_roadmap_payload()
    rendered = render_todo(payload)
    assert "Scholarship lanes: delivery_and_reporting" in rendered


def test_render_todo_detail_includes_scholarship_plan() -> None:
    payload = _valid_roadmap_payload()
    rendered = render_todo_detail_pages(payload)["asf-example-open.md"]
    assert "## Scholarship and Evidence Plan" in rendered
    assert "`example_source` (planned)" in rendered
    assert "This plan does not establish learner outcomes." in rendered


def test_roadmap_rejects_malformed_scholarship_plan(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["tasks"][1]["scholarship_plan"] = {
        "lanes": ["unknown_lane"],
        "existing_source_keys": [],
        "planned_source_targets": [
            {"key": "", "status": "wrong", "locator": "", "role": ""}
        ],
        "claim_support_types": ["wrong"],
        "boundaries": [],
        "phase_exit": [],
    }
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    locations = {issue.location for issue in audit_roadmap(tmp_path)}
    assert "tasks[1].scholarship_plan.lanes" in locations
    assert "tasks[1].scholarship_plan.planned_source_targets[0].key" in locations
    assert "tasks[1].scholarship_plan.claim_support_types" in locations
    assert "tasks[1].scholarship_plan.boundaries" in locations
    assert "tasks[1].scholarship_plan.phase_exit" in locations


def test_roadmap_rejects_unknown_existing_scholarship_source(tmp_path: Path) -> None:
    payload = _valid_roadmap_payload()
    payload["tasks"][1]["scholarship_plan"]["existing_source_keys"] = ["missing_source"]
    _write_roadmap(tmp_path, _valid_roadmap_payload())
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "tasks[1].scholarship_plan.existing_source_keys[0]"
        and "absent" in issue.message
        for issue in issues
    )


def test_roadmap_rejects_missing_stale_and_obsolete_todo_detail_pages(
    tmp_path: Path,
) -> None:
    payload = _valid_roadmap_payload()
    _write_roadmap(tmp_path, payload)
    detail_dir = tmp_path / "docs" / "todo"

    (detail_dir / "asf-example-open.md").unlink()
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "docs/todo"
        and "missing active task detail pages" in issue.message
        for issue in issues
    )

    write_todo_surfaces(tmp_path)
    (detail_dir / "asf-example-open.md").write_text("# stale\n", encoding="utf-8")
    (detail_dir / "obsolete.md").write_text("# obsolete\n", encoding="utf-8")
    issues = audit_roadmap(tmp_path)
    assert any(
        issue.location == "docs/todo/asf-example-open.md"
        and "task detail page is stale" in issue.message
        for issue in issues
    )
    assert any(
        issue.location == "docs/todo" and "obsolete task detail pages" in issue.message
        for issue in issues
    )

    write_todo_surfaces(tmp_path)
    assert audit_roadmap(tmp_path) == []
    assert not (detail_dir / "obsolete.md").exists()


def test_render_todo_omits_completed_history_when_open_tasks_exist() -> None:
    payload = _valid_roadmap_payload()
    rendered = render_todo(payload)
    done_task = payload["tasks"][0]

    assert "Completed Milestones" not in rendered
    assert "[x]" not in rendered
    assert done_task["id"] not in rendered
    assert done_task["title"] not in rendered


def test_roadmap_issue_str() -> None:
    assert str(RoadmapIssue("a.b", "boom")) == "a.b: boom"


def test_live_count_issue_str() -> None:
    issue = LiveCountIssue(
        path=Path("README.md"),
        line=7,
        key="skill_count",
        found=248,
        expected=600,
        excerpt="had 248 skills",
    )
    rendered = str(issue)
    assert "README.md:7" in rendered
    assert "skill_count literal 248 should be 600" in rendered
    assert "had 248 skills" in rendered


def test_validate_live_count_literals_raises_on_stale(tmp_path: Path) -> None:
    _copy_minimal_source_surfaces(tmp_path)
    (tmp_path / "README.md").write_text(
        "Old export had 248 skills.\n", encoding="utf-8"
    )
    with pytest.raises(LiveCountError, match="stale live-count literals found"):
        validate_live_count_literals(tmp_path)


def test_validate_live_count_literals_passes_when_clean(tmp_path: Path) -> None:
    _copy_minimal_source_surfaces(tmp_path)
    (tmp_path / "README.md").write_text("No counts here at all.\n", encoding="utf-8")
    # Should not raise.
    validate_live_count_literals(tmp_path)


def test_build_live_counts_rejects_missing_figure_registry(tmp_path: Path) -> None:
    for rel in ("data/scholarship_sources.yaml", "manuscript/references.bib"):
        src = REPO / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    manuscript_dir = tmp_path / "manuscript"
    for pattern in ("[0-9][0-9]_*.md", "[0-9][0-9][a-z]_*.md"):
        for src in (REPO / "manuscript").glob(pattern):
            (manuscript_dir / src.name).write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8"
            )
    with pytest.raises(LiveCountError, match="figure registry is missing"):
        build_live_counts(tmp_path)


def test_build_live_counts_rejects_non_list_figure_registry(tmp_path: Path) -> None:
    _copy_minimal_source_surfaces(tmp_path)
    registry = tmp_path / "output" / "figures" / "figure_registry.json"
    registry.write_text('{"not": "a list"}', encoding="utf-8")
    with pytest.raises(LiveCountError, match="JSON list"):
        build_live_counts(tmp_path)


def test_build_live_counts_rejects_registry_missing_png(tmp_path: Path) -> None:
    _copy_minimal_source_surfaces(tmp_path)
    registry = tmp_path / "output" / "figures" / "figure_registry.json"
    registry.write_text(
        '[{"filename": "missing.png", "label": "fig:missing"}]\n',
        encoding="utf-8",
    )
    with pytest.raises(LiveCountError, match="references missing files"):
        build_live_counts(tmp_path)


def test_as_int_coerces_supported_types() -> None:
    assert _as_int(True) == 1
    assert _as_int(False) == 0
    assert _as_int(7) == 7
    assert _as_int(3.9) == 3
    assert _as_int("42") == 42


def test_as_int_rejects_unsupported_type() -> None:
    with pytest.raises(TypeError, match="expected numeric count value"):
        _as_int(["not", "numeric"])


def _copy_minimal_source_surfaces(tmp_path: Path) -> None:
    """Provide files needed by live-count builders while testing temp roadmaps."""
    for rel in (
        "data/scholarship_sources.yaml",
        "manuscript/references.bib",
        "output/figures/figure_registry.json",
    ):
        src = REPO / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    registry = json.loads(
        (tmp_path / "output" / "figures" / "figure_registry.json").read_text(
            encoding="utf-8"
        )
    )
    for row in registry:
        filename = row["filename"]
        # Captured browser evidence declares a tracked asset root of its own
        # instead of sitting beside the generated figures.
        asset_root = str(row.get("asset_root") or "output/figures")
        src = REPO / asset_root / filename
        dst = tmp_path / asset_root / filename
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    manuscript_dir = tmp_path / "manuscript"
    for src in (REPO / "manuscript").glob("[0-9][0-9]*_*.md"):
        (manuscript_dir / src.name).write_text(
            src.read_text(encoding="utf-8"), encoding="utf-8"
        )
