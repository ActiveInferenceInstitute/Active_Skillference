"""Roadmap schema, validation, and TODO rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from src.live_counts import build_live_counts
from src.scholarship.coverage import load_source_matrix

VALID_STATUSES = frozenset({"done", "in_progress", "todo", "blocked"})
VALID_SURFACES = frozenset(
    {
        "curriculum",
        "dashboard",
        "documentation",
        "figures",
        "manuscript",
        "metadata",
        "roadmap",
        "scholarship",
        "skilltree",
        "validation",
    }
)
VALID_SCALES = frozenset({"minor", "medium", "major", "external"})
VALID_SCHOLARSHIP_PLAN_STATUSES = frozenset({"existing", "planned", "audit", "blocked"})
VALID_SCHOLARSHIP_LANES = frozenset(
    {
        "perception_as_inference",
        "active_inference_core",
        "mathematical_foundations",
        "pedagogy_and_learning_paths",
        "delivery_and_reporting",
        "applications_and_scope",
    }
)
VALID_CLAIM_SUPPORT_TYPES = frozenset(
    {
        "computed",
        "descriptive_count",
        "simulation",
        "literature",
        "scope_limit",
        "delivery",
        "visual",
    }
)
SCALE_HEADINGS = (
    ("external", "External Blockers"),
    ("minor", "Minor Improvements"),
    ("medium", "Medium Improvements"),
    ("major", "Major Improvements"),
)
STATUS_MARKERS = {
    "todo": "[ ]",
    "in_progress": "[~]",
    "blocked": "[!]",
}
METRIC_KEYS = {
    "skills": "skill_count",
    "subjects": "subject_count",
    "prerequisite_edges": "edge_count",
    "dependencies": "edge_count",
    "quizzes": "quiz_count",
    "assessments": "assessment_count",
    "claims": "claim_count",
    "figures": "figure_count",
    "cited_sources": "citation_count",
    "max_depth": "max_depth",
}
TODO_DETAIL_DIR = Path("docs") / "todo"


@dataclass(frozen=True)
class RoadmapIssue:
    """One roadmap schema or evidence issue."""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


class RoadmapError(ValueError):
    """Raised when roadmap state or generated TODO output is stale."""


def load_roadmap(path: Path) -> dict[str, Any]:
    """Load the roadmap YAML mapping."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RoadmapError(f"{path} must contain a YAML mapping")
    return payload


def audit_roadmap(root: Path) -> list[RoadmapIssue]:
    """Return roadmap issues without raising."""
    root = Path(root)
    payload = load_roadmap(root / "tasks.yaml")
    live_counts = build_live_counts(root)
    scholarship_source_keys = frozenset(
        load_source_matrix(root / "data" / "scholarship_sources.yaml")
    )
    issues: list[RoadmapIssue] = []

    project = payload.get("project")
    if not isinstance(project, dict):
        return [RoadmapIssue("project", "project metadata must be a mapping")]
    if (
        project.get("title")
        != "Active Skillference - Active Inference micro-learning platform"
    ):
        issues.append(
            RoadmapIssue(
                "project.title", "use the human-facing Active Skillference title"
            )
        )
    if not isinstance(project.get("updated"), str) or not project["updated"].strip():
        issues.append(RoadmapIssue("project.updated", "updated date is required"))
    _audit_metric_block(
        project.get("live_metrics"),
        "project.live_metrics",
        live_counts,
        issues,
        require_all=True,
    )

    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        issues.append(RoadmapIssue("tasks", "tasks must be a non-empty list"))
        return issues

    seen_ids: set[str] = set()
    for index, task in enumerate(tasks):
        location = f"tasks[{index}]"
        if not isinstance(task, dict):
            issues.append(RoadmapIssue(location, "task must be a mapping"))
            continue
        task_id = str(task.get("id", "")).strip()
        if not task_id:
            issues.append(RoadmapIssue(location, "id is required"))
        elif task_id in seen_ids:
            issues.append(RoadmapIssue(f"{location}.id", f"duplicate id {task_id!r}"))
        seen_ids.add(task_id)
        if not str(task.get("title", "")).strip():
            issues.append(RoadmapIssue(f"{location}.title", "title is required"))
        status = str(task.get("status", "")).strip()
        if status not in VALID_STATUSES:
            issues.append(
                RoadmapIssue(
                    f"{location}.status",
                    f"status must be one of {sorted(VALID_STATUSES)!r}",
                )
            )
        scale = str(task.get("scale", "")).strip()
        if status in {"todo", "in_progress", "blocked"} and scale not in VALID_SCALES:
            issues.append(
                RoadmapIssue(
                    f"{location}.scale",
                    f"open tasks require a scale in {sorted(VALID_SCALES)!r}",
                )
            )
        surface = str(task.get("surface", "")).strip()
        if surface not in VALID_SURFACES:
            issues.append(
                RoadmapIssue(
                    f"{location}.surface",
                    f"surface must be one of {sorted(VALID_SURFACES)!r}",
                )
            )
        owner = str(task.get("owner", "")).strip()
        if not owner:
            issues.append(
                RoadmapIssue(f"{location}.owner", "owner/source path is required")
            )
        evidence = task.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            issues.append(
                RoadmapIssue(
                    f"{location}.evidence",
                    "evidence must be a non-empty list of commands or artifact checks",
                )
            )
        if status == "done" and len(evidence or []) < 1:
            issues.append(
                RoadmapIssue(f"{location}.evidence", "done tasks require evidence")
            )
        if not str(task.get("notes", "")).strip():
            issues.append(RoadmapIssue(f"{location}.notes", "notes are required"))
        if status in {"todo", "in_progress", "blocked"}:
            _audit_scholarship_plan(
                task.get("scholarship_plan"),
                f"{location}.scholarship_plan",
                issues,
                source_keys=scholarship_source_keys,
            )
        _audit_metric_block(
            task.get("metrics"), f"{location}.metrics", live_counts, issues
        )

    # render_todo indexes required fields directly, so a structurally malformed roadmap
    # would raise here and discard the issues collected above. Guard it so the audit
    # always returns its findings: if the payload is too malformed to render, that is
    # itself a reported issue rather than an uncaught crash.
    try:
        expected_todo = render_todo(payload)
        expected_details = render_todo_detail_pages(payload)
    except (TypeError, KeyError, AttributeError) as exc:
        issues.append(
            RoadmapIssue(
                "TODO.md", f"roadmap too malformed to render TODO surfaces: {exc}"
            )
        )
        return issues
    todo_path = root / "TODO.md"
    if not todo_path.exists():
        issues.append(RoadmapIssue("TODO.md", "generated TODO.md is missing"))
    elif todo_path.read_text(encoding="utf-8") != expected_todo:
        issues.append(
            RoadmapIssue(
                "TODO.md",
                "TODO.md is stale; regenerate it from tasks.yaml",
            )
        )
    detail_dir = root / TODO_DETAIL_DIR
    expected_paths = {TODO_DETAIL_DIR / filename for filename in expected_details}
    actual_paths = (
        {path.relative_to(root) for path in detail_dir.glob("*.md")}
        if detail_dir.exists()
        else set()
    )
    missing_details = sorted(expected_paths - actual_paths)
    extra_details = sorted(actual_paths - expected_paths)
    if missing_details:
        issues.append(
            RoadmapIssue(
                "docs/todo",
                "missing active task detail pages: "
                + ", ".join(path.as_posix() for path in missing_details),
            )
        )
    if extra_details:
        issues.append(
            RoadmapIssue(
                "docs/todo",
                "obsolete task detail pages: "
                + ", ".join(path.as_posix() for path in extra_details),
            )
        )
    for filename, expected in expected_details.items():
        detail_path = detail_dir / filename
        if detail_path.exists() and detail_path.read_text(encoding="utf-8") != expected:
            issues.append(
                RoadmapIssue(
                    f"docs/todo/{filename}",
                    "task detail page is stale; regenerate it from tasks.yaml",
                )
            )
    return issues


def validate_roadmap(root: Path) -> None:
    """Raise if the roadmap or generated TODO surface is stale."""
    issues = audit_roadmap(root)
    if issues:
        raise RoadmapError(
            "roadmap validation failed:\n  "
            + "\n  ".join(str(issue) for issue in issues)
        )


def render_todo(payload: dict[str, Any]) -> str:
    """Render the human TODO surface from the roadmap YAML payload."""
    project = payload["project"]
    metrics = project["live_metrics"]
    tasks = payload["tasks"]
    open_tasks = [
        task for task in tasks if task["status"] in {"todo", "in_progress", "blocked"}
    ]

    lines = [
        "# Active Skillference TODO",
        "",
        "<!-- GENERATED FROM tasks.yaml. Do not edit by hand. -->",
        "",
        "## Current Proof",
        "",
        (
            f"- {metrics['skills']} skills, {metrics['subjects']} subjects, "
            f"{metrics['prerequisite_edges']} prerequisite edges, "
            f"{metrics['assessments']} assessment questions."
        ),
        (
            f"- {metrics['claims']} claims, {metrics['figures']} figures, "
            f"{metrics['cited_sources']} cited sources, max depth {metrics['max_depth']}."
        ),
        "",
        "## Active Roadmap",
        "",
    ]
    if open_tasks:
        grouped: dict[str, list[dict[str, Any]]] = {
            scale: [] for scale, _heading in SCALE_HEADINGS
        }
        for task in open_tasks:
            grouped.setdefault(str(task.get("scale", "medium")), []).append(task)
        for scale, heading in SCALE_HEADINGS:
            tasks_for_scale = grouped.get(scale, [])
            if not tasks_for_scale:
                continue
            lines.extend([f"### {heading}", ""])
            for task in tasks_for_scale:
                _render_open_task(lines, task)
            lines.append("")
        if lines[-1] == "":
            lines.pop()
    else:
        lines.append("- No open roadmap tasks.")
    lines.append("")
    return "\n".join(lines)


def _render_open_task(lines: list[str], task: dict[str, Any]) -> None:
    marker = STATUS_MARKERS[task["status"]]
    task_id = str(task["id"])
    detail_path = TODO_DETAIL_DIR / f"{task_id}.md"
    lines.append(
        f"- {marker} **[{task_id}]({detail_path.as_posix()})** "
        f"({task['surface']}): {task['title']}"
    )
    notes = _normalize_markdown_text(str(task.get("notes", "")))
    if notes:
        lines.append(f"  - Scope: {notes}")
    deps = task.get("deps")
    if isinstance(deps, list) and deps:
        lines.append("  - Depends on: " + ", ".join(f"`{dep}`" for dep in deps))
    evidence = task.get("evidence")
    if isinstance(evidence, list) and evidence:
        rendered = "; ".join(f"`{item}`" for item in evidence if str(item).strip())
        if rendered:
            lines.append(f"  - Evidence: {rendered}")
    scholarship_plan = task.get("scholarship_plan")
    if isinstance(scholarship_plan, dict):
        lanes = scholarship_plan.get("lanes", [])
        if isinstance(lanes, list) and lanes:
            lines.append(
                "  - Scholarship lanes: " + ", ".join(str(lane) for lane in lanes)
            )


def _normalize_markdown_text(value: str) -> str:
    return " ".join(value.split())


def render_todo_detail_pages(payload: dict[str, Any]) -> dict[str, str]:
    tasks = payload["tasks"]
    open_tasks = [
        task for task in tasks if task["status"] in {"todo", "in_progress", "blocked"}
    ]
    pages: dict[str, str] = {}
    for task in open_tasks:
        task_id = str(task["id"])
        pages[f"{task_id}.md"] = render_todo_detail_page(task)
    return pages


def render_todo_detail_page(task: dict[str, Any]) -> str:
    task_id = str(task["id"])
    title = str(task["title"])
    status = str(task["status"])
    scale = str(task.get("scale", ""))
    surface = str(task["surface"])
    owner = str(task["owner"])
    notes = _normalize_markdown_text(str(task.get("notes", "")))
    evidence = [str(item) for item in task.get("evidence", []) if str(item).strip()]
    deps = [str(dep) for dep in task.get("deps", []) if str(dep).strip()]
    blocker = _task_blocker(task)
    lines = [
        f"# {title}",
        "",
        "<!-- GENERATED FROM tasks.yaml. Do not edit by hand. -->",
        "",
        "## Roadmap Link",
        "",
        f"- Task id: `{task_id}`",
        f"- Status: `{status}`",
        f"- Scale: `{scale}`",
        f"- Surface: `{surface}`",
        f"- Owner: `{owner}`",
        "- Top-level TODO: [`TODO.md`](../../TODO.md)",
        "",
        "## Scope",
        "",
        notes or "No task scope notes are present in tasks.yaml.",
        "",
        "## Deliverables",
        "",
    ]
    lines.extend(_markdown_bullets(_task_deliverables(task)))
    lines.extend(["", "## Out of Scope", ""])
    lines.extend(_markdown_bullets(_task_out_of_scope(task)))
    lines.extend(["", "## Dependencies and Blockers", ""])
    if deps:
        lines.append("- Depends on: " + ", ".join(f"`{dep}`" for dep in deps))
    else:
        lines.append("- Depends on: none declared in `tasks.yaml`.")
    lines.append(f"- Current blocker: {blocker}")
    lines.extend(["", "## Evidence Commands", ""])
    lines.extend(_markdown_bullets([f"`{item}`" for item in evidence]))
    lines.extend(["", "## Acceptance Criteria", ""])
    lines.extend(_markdown_bullets(_task_acceptance_criteria(task)))
    lines.extend(["", "## Scholarship and Evidence Plan", ""])
    lines.extend(_markdown_bullets(_scholarship_plan_lines(task)))
    lines.append("")
    return "\n".join(lines)


def write_todo_surfaces(root: Path) -> None:
    payload = load_roadmap(root / "tasks.yaml")
    (root / "TODO.md").write_text(render_todo(payload), encoding="utf-8")
    detail_dir = root / TODO_DETAIL_DIR
    detail_dir.mkdir(parents=True, exist_ok=True)
    expected = render_todo_detail_pages(payload)
    for filename, text in expected.items():
        (detail_dir / filename).write_text(text, encoding="utf-8")
    for path in detail_dir.glob("*.md"):
        if path.name not in expected:
            path.unlink()


def _markdown_bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None."]
    return [f"- {item}" for item in items]


def _audit_scholarship_plan(
    value: object,
    location: str,
    issues: list[RoadmapIssue],
    *,
    source_keys: frozenset[str],
) -> None:
    """Validate the scholarship package attached to an open roadmap task."""
    if not isinstance(value, dict):
        issues.append(
            RoadmapIssue(location, "open tasks require a scholarship_plan mapping")
        )
        return

    lanes = value.get("lanes")
    if (
        not isinstance(lanes, list)
        or not lanes
        or not all(
            isinstance(lane, str) and lane in VALID_SCHOLARSHIP_LANES for lane in lanes
        )
    ):
        issues.append(
            RoadmapIssue(
                f"{location}.lanes",
                "lanes must be a non-empty list of expected scholarship lanes",
            )
        )

    existing_keys = value.get("existing_source_keys")
    if not isinstance(existing_keys, list) or not all(
        isinstance(key, str) and key.strip() for key in existing_keys
    ):
        issues.append(
            RoadmapIssue(
                f"{location}.existing_source_keys",
                "existing_source_keys must be a list of non-empty source keys",
            )
        )
    else:
        for index, key in enumerate(existing_keys):
            if key not in source_keys:
                issues.append(
                    RoadmapIssue(
                        f"{location}.existing_source_keys[{index}]",
                        f"source key {key!r} is absent from data/scholarship_sources.yaml",
                    )
                )

    planned_sources = value.get("planned_source_targets")
    if not isinstance(planned_sources, list):
        issues.append(
            RoadmapIssue(
                f"{location}.planned_source_targets",
                "planned_source_targets must be a list",
            )
        )
    else:
        seen: set[str] = set()
        for index, source in enumerate(planned_sources):
            source_location = f"{location}.planned_source_targets[{index}]"
            if not isinstance(source, dict):
                issues.append(
                    RoadmapIssue(source_location, "source target must be a mapping")
                )
                continue
            key = str(source.get("key", "")).strip()
            status = str(source.get("status", "")).strip()
            locator = str(source.get("locator", "")).strip()
            role = str(source.get("role", "")).strip()
            if not key:
                issues.append(
                    RoadmapIssue(
                        f"{source_location}.key", "source target key is required"
                    )
                )
            elif key in seen:
                issues.append(
                    RoadmapIssue(
                        f"{source_location}.key", f"duplicate source target {key!r}"
                    )
                )
            seen.add(key)
            if status not in VALID_SCHOLARSHIP_PLAN_STATUSES:
                issues.append(
                    RoadmapIssue(
                        f"{source_location}.status",
                        f"status must be one of {sorted(VALID_SCHOLARSHIP_PLAN_STATUSES)!r}",
                    )
                )
            if not locator:
                issues.append(
                    RoadmapIssue(
                        f"{source_location}.locator", "source locator is required"
                    )
                )
            if not role:
                issues.append(
                    RoadmapIssue(f"{source_location}.role", "source role is required")
                )

    claim_types = value.get("claim_support_types")
    if (
        not isinstance(claim_types, list)
        or not claim_types
        or not all(
            isinstance(item, str) and item in VALID_CLAIM_SUPPORT_TYPES
            for item in claim_types
        )
    ):
        issues.append(
            RoadmapIssue(
                f"{location}.claim_support_types",
                "claim_support_types must be a non-empty list of supported claim types",
            )
        )

    for field in ("boundaries", "phase_exit"):
        items = value.get(field)
        if (
            not isinstance(items, list)
            or not items
            or not all(isinstance(item, str) and item.strip() for item in items)
        ):
            issues.append(
                RoadmapIssue(
                    f"{location}.{field}",
                    f"{field} must be a non-empty list of statements",
                )
            )


def _scholarship_plan_lines(task: dict[str, Any]) -> list[str]:
    """Render a validated scholarship plan as readable TODO bullets."""
    plan = task.get("scholarship_plan")
    if not isinstance(plan, dict):
        return ["No scholarship plan is present in tasks.yaml."]
    lines: list[str] = []
    lanes = plan.get("lanes", [])
    lines.append("Lanes: " + ", ".join(str(item) for item in lanes))
    existing = plan.get("existing_source_keys", [])
    lines.append(
        "Existing source keys: "
        + (", ".join(f"`{item}`" for item in existing) if existing else "none")
    )
    lines.append("Planned source targets:")
    planned = plan.get("planned_source_targets", [])
    if isinstance(planned, list) and planned:
        lines.extend(
            f"  `{source.get('key', '')}` ({source.get('status', '')}): "
            f"{source.get('role', '')} [{source.get('locator', '')}]"
            for source in planned
            if isinstance(source, dict)
        )
    else:
        lines.append("  none")
    lines.append(
        "Claim-support types: "
        + ", ".join(str(item) for item in plan.get("claim_support_types", []))
    )
    lines.append("Boundaries:")
    lines.extend(f"  {item}" for item in plan.get("boundaries", []))
    lines.append("Phase exit:")
    lines.extend(f"  {item}" for item in plan.get("phase_exit", []))
    return lines


def _task_blocker(task: dict[str, Any]) -> str:
    status = str(task.get("status", ""))
    task_id = str(task.get("id", ""))
    notes = _normalize_markdown_text(str(task.get("notes", "")))
    deps = [str(dep) for dep in task.get("deps", []) if str(dep).strip()]
    if status != "blocked":
        if deps:
            return "upstream dependency must clear first: " + ", ".join(
                f"`{dep}`" for dep in deps
            )
        if task_id == "asf-live-stack-ci-rehearsal":
            return "Docker/Colima daemon must be reachable before live full-stack proof can pass."
        return "none; this item is open for implementation."
    if "docker info reported:" in notes:
        return notes.split("docker info reported:", 1)[1].strip()
    if "public GitHub repository is reachable" in notes:
        return "public GitHub repository is not reachable; DOI and public-release metadata must remain blank."
    if task_id == "asf-skilltree-auth-deployment-matrix":
        return (
            "Docker/live SkillTree proof is unavailable until `docker info` succeeds."
        )
    return "blocked by the external condition described in the Scope section."


def _task_deliverables(task: dict[str, Any]) -> list[str]:
    task_id = str(task.get("id", ""))
    surface = str(task.get("surface", ""))
    owner = str(task.get("owner", ""))
    common = [
        f"Update the `{surface}` surface owned by `{owner}` only as needed for this task.",
        "Refresh generated artifacts or documentation surfaces named by the evidence commands.",
        "Keep `tasks.yaml` canonical and regenerate `TODO.md` rather than hand-editing it.",
    ]
    specific = {
        "asf-public-release-metadata": [
            "Confirm the public repository target is reachable before adding public DOI or repository metadata.",
            "Keep blocked DOI, CFF, CodeMeta, and manuscript URL fields blank until release proof exists.",
        ],
        "asf-skilltree-auth-deployment-matrix": [
            "Keep the browser dashboard payload secret-free while exposing only supported SkillTree mode status.",
            "Run live app-ready proof only after Docker and SkillTree are actually available.",
        ],
        "asf-live-stack-ci-rehearsal": [
            "Produce a repeatable full-stack rehearsal with Docker readiness, seeded SkillTree state, FORM-login proof, dashboard console proof, and dependency parity.",
            "Record raw proof artifacts without weakening offline validators.",
        ],
        "asf-empirical-learner-pilot-package": [
            "Create an ethics-aware learner pilot protocol, export schema, analysis contract, and conditional manuscript language.",
            "Keep learner-effectiveness claims out of the manuscript until real pilot data exist.",
        ],
        "asf-adaptive-path-recommendation-prototype": [
            "Prototype graph-based remediation recommendations from prerequisites, assessment concepts, and SkillTree-owned progress signals.",
            "Display recommendations only as read-only dashboard routing back to official SkillTree surfaces.",
        ],
        "asf-public-archive-provenance-release": [
            "After the public repository blocker clears, complete release tag, Zenodo DOI, CFF, CodeMeta, artifact hashes, notices, and inventory refresh.",
            "Preserve the no-fabricated-metadata boundary until upstream release proof exists.",
        ],
    }
    return specific.get(task_id, []) + common


def _task_out_of_scope(task: dict[str, Any]) -> list[str]:
    task_id = str(task.get("id", ""))
    common = [
        "Do not stage, commit, push, publish, or mint a DOI as part of this task unless a later request explicitly asks for it.",
        "Do not weaken validators, coverage thresholds, provenance checks, or source-role requirements to make evidence pass.",
    ]
    specific = {
        "asf-public-release-metadata": [
            "Do not invent a public repository, DOI, release URL, or publication timestamp.",
        ],
        "asf-skilltree-auth-deployment-matrix": [
            "Do not expose admin secrets, bearer tokens, client secrets, or local private state to browser JavaScript.",
            "Do not claim app-ready live proof while `docker info` fails.",
        ],
        "asf-live-stack-ci-rehearsal": [
            "Do not replace live-stack proof with artifact-only checks.",
        ],
        "asf-empirical-learner-pilot-package": [
            "Do not claim learner efficacy from curriculum structure, quizzes, or synthetic diagnostics.",
        ],
        "asf-adaptive-path-recommendation-prototype": [
            "Do not create an app-owned learner-state store, ranking system, or quiz engine in the dashboard.",
        ],
        "asf-public-archive-provenance-release": [
            "Do not backfill public metadata before `asf-public-release-metadata` is unblocked.",
        ],
    }
    return specific.get(task_id, []) + common


def _task_acceptance_criteria(task: dict[str, Any]) -> list[str]:
    status = str(task.get("status", ""))
    criteria = [
        "All evidence commands listed above pass, or the task remains blocked with exact blocker evidence.",
        "Generated roadmap surfaces validate with `uv run python scripts/validate_roadmap.py`.",
        "Live counts remain current with `uv run python scripts/validate_live_counts.py`.",
    ]
    if status == "blocked":
        criteria.insert(
            0,
            "The blocker is cleared and rerun evidence replaces the current blocked status.",
        )
    return criteria


def _audit_metric_block(
    block: object,
    location: str,
    live_counts: dict[str, Any],
    issues: list[RoadmapIssue],
    *,
    require_all: bool = False,
) -> None:
    if block is None:
        if require_all:
            issues.append(RoadmapIssue(location, "metric block is required"))
        return
    if not isinstance(block, dict):
        issues.append(RoadmapIssue(location, "metrics must be a mapping"))
        return
    if require_all:
        missing = sorted(set(METRIC_KEYS) - set(block))
        if missing:
            issues.append(
                RoadmapIssue(location, "missing metrics: " + ", ".join(missing))
            )
    for key, value in block.items():
        if key not in METRIC_KEYS:
            issues.append(RoadmapIssue(f"{location}.{key}", "unknown metric key"))
            continue
        if not isinstance(value, int):
            issues.append(
                RoadmapIssue(f"{location}.{key}", "metric value must be an integer")
            )
            continue
        expected = live_counts[METRIC_KEYS[key]].value
        if value != expected:
            issues.append(
                RoadmapIssue(
                    f"{location}.{key}",
                    f"stale metric {value}; expected {expected}",
                )
            )
