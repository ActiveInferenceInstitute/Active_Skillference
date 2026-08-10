from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import ALL_STRATA, Skill, Subject
from src.curriculum.quality import MIN_ASSESSMENTS_PER_SKILL

_MAX_ROWS = 12
_MAX_REMEDIATION_ROWS = 16


def curriculum_diagnostic_gap_map(graph: CurriculumGraph) -> dict[str, Any]:
    levels = graph.levels()
    subject_by_skill = _subject_by_skill(graph)
    downstream = _downstream_dependents(graph)
    direct_dependents = Counter(prereq for prereq, _ in graph.prerequisite_edges())
    bottlenecks = _bottleneck_rows(
        graph,
        levels=levels,
        subject_by_skill=subject_by_skill,
        downstream=downstream,
        direct_dependents=direct_dependents,
    )
    long_chains = _long_chain_rows(
        graph,
        levels=levels,
        subject_by_skill=subject_by_skill,
        downstream=downstream,
    )
    assessment_balance = _assessment_balance_rows(graph)
    remediation_queue = _remediation_queue(
        bottlenecks=bottlenecks,
        long_chains=long_chains,
        assessment_balance=assessment_balance,
    )
    max_depth = max(levels.values()) if levels else 0
    assessment_warnings = sum(
        1 for row in assessment_balance if row["status"] == "review"
    )
    return {
        "assessmentBalance": assessment_balance,
        "bottlenecks": bottlenecks,
        "claimBoundary": (
            "Diagnostic maintenance map only; it ranks generated curriculum surfaces "
            "and does not report learner performance or empirical efficacy."
        ),
        "longChains": long_chains,
        "remediationQueue": remediation_queue,
        "summary": {
            "assessmentWarningCount": assessment_warnings,
            "bottleneckCount": len(bottlenecks),
            "dependencies": len(graph.prerequisite_edges()),
            "longPathCount": len(long_chains),
            "maxDepth": max_depth,
            "remediationCandidates": len(remediation_queue),
            "skills": len(graph.skills),
            "subjects": len(graph.subjects),
        },
    }


def write_curriculum_diagnostic_gap_map(
    graph: CurriculumGraph,
    path: Path,
) -> Path:
    return write_json_artifact(Path(path), curriculum_diagnostic_gap_map(graph))


def _subject_by_skill(graph: CurriculumGraph) -> dict[str, Subject]:
    return {
        skill.skill_id: subject
        for subject in graph.subjects
        for skill in subject.skills
    }


def _downstream_dependents(graph: CurriculumGraph) -> dict[str, int]:
    forward: dict[str, set[str]] = {skill.skill_id: set() for skill in graph.skills}
    for prereq, dependent in graph.prerequisite_edges():
        forward.setdefault(prereq, set()).add(dependent)
    downstream: dict[str, int] = {}
    for skill in graph.skills:
        seen: set[str] = set()
        stack = list(forward.get(skill.skill_id, set()))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(forward.get(node, set()))
        downstream[skill.skill_id] = len(seen)
    return downstream


def _skill_context(
    skill: Skill,
    *,
    levels: dict[str, int],
    subject_by_skill: dict[str, Subject],
    downstream: dict[str, int],
) -> dict[str, object]:
    subject = subject_by_skill[skill.skill_id]
    return {
        "depth": levels.get(skill.skill_id, 0),
        "downstreamDependentCount": downstream.get(skill.skill_id, 0),
        "name": skill.name,
        "prerequisiteCount": len(skill.prerequisites),
        "skillId": skill.skill_id,
        "stratum": skill.stratum.value,
        "subjectId": subject.subject_id,
        "subjectName": subject.name,
    }


def _bottleneck_rows(
    graph: CurriculumGraph,
    *,
    levels: dict[str, int],
    subject_by_skill: dict[str, Subject],
    downstream: dict[str, int],
    direct_dependents: Counter[str],
) -> list[dict[str, object]]:
    ranked = sorted(
        graph.skills,
        key=lambda skill: (
            downstream.get(skill.skill_id, 0),
            direct_dependents.get(skill.skill_id, 0),
            levels.get(skill.skill_id, 0),
            skill.skill_id,
        ),
        reverse=True,
    )
    rows: list[dict[str, object]] = []
    for rank, skill in enumerate(ranked[:_MAX_ROWS], start=1):
        row = _skill_context(
            skill,
            levels=levels,
            subject_by_skill=subject_by_skill,
            downstream=downstream,
        )
        row.update(
            {
                "directDependentCount": direct_dependents.get(skill.skill_id, 0),
                "rank": rank,
                "reviewReason": (
                    "High downstream fan-out; explanation, quiz and prerequisite text "
                    "have broad blast radius."
                ),
            }
        )
        rows.append(row)
    return rows


def _long_chain_rows(
    graph: CurriculumGraph,
    *,
    levels: dict[str, int],
    subject_by_skill: dict[str, Subject],
    downstream: dict[str, int],
) -> list[dict[str, object]]:
    ranked = sorted(
        graph.skills,
        key=lambda skill: (
            levels.get(skill.skill_id, 0),
            downstream.get(skill.skill_id, 0),
            skill.skill_id,
        ),
        reverse=True,
    )
    rows: list[dict[str, object]] = []
    for rank, skill in enumerate(ranked[:_MAX_ROWS], start=1):
        row = _skill_context(
            skill,
            levels=levels,
            subject_by_skill=subject_by_skill,
            downstream=downstream,
        )
        row.update(
            {
                "rank": rank,
                "reviewReason": (
                    "Deep dependency position; add bridge examples when learners cross "
                    "strata or dense prerequisite clusters."
                ),
            }
        )
        rows.append(row)
    return rows


def _assessment_balance_rows(graph: CurriculumGraph) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for stratum in ALL_STRATA:
        skills = [skill for skill in graph.skills if skill.stratum is stratum]
        question_counts = [len(skill.assessments) for skill in skills]
        question_total = sum(question_counts)
        below_floor = sum(
            1 for count in question_counts if count < MIN_ASSESSMENTS_PER_SKILL
        )
        min_questions = min(question_counts) if question_counts else 0
        questions_per_skill = question_total / len(skills) if skills else 0.0
        rows.append(
            {
                "belowFloorSkills": below_floor,
                "minQuestions": min_questions,
                "questions": question_total,
                "questionsPerSkill": round(questions_per_skill, 2),
                "review": (
                    "pass"
                    if below_floor == 0
                    else "add failable assessment depth before release"
                ),
                "skills": len(skills),
                "status": "pass" if below_floor == 0 else "review",
                "stratum": stratum.value,
            }
        )
    return rows


def _remediation_queue(
    *,
    bottlenecks: list[dict[str, object]],
    long_chains: list[dict[str, object]],
    assessment_balance: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in bottlenecks[:8]:
        skill_id = str(row["skillId"])
        seen.add(skill_id)
        rows.append(
            {
                "action": "review high-fan-out explanation and quiz handoff",
                "priority": len(rows) + 1,
                "reason": row["reviewReason"],
                "skillId": skill_id,
                "stratum": row["stratum"],
                "surface": "curriculum",
            }
        )
    for row in long_chains:
        skill_id = str(row["skillId"])
        if skill_id in seen:
            continue
        seen.add(skill_id)
        rows.append(
            {
                "action": "add bridge wording or local example for deep chain position",
                "priority": len(rows) + 1,
                "reason": row["reviewReason"],
                "skillId": skill_id,
                "stratum": row["stratum"],
                "surface": "curriculum",
            }
        )
        if len(rows) >= _MAX_REMEDIATION_ROWS:
            break
    for row in assessment_balance:
        if row["status"] != "review":
            continue
        rows.append(
            {
                "action": "raise assessment floor for stratum",
                "priority": len(rows) + 1,
                "reason": row["review"],
                "skillId": "",
                "stratum": row["stratum"],
                "surface": "assessment",
            }
        )
        if len(rows) >= _MAX_REMEDIATION_ROWS:
            break
    return rows[:_MAX_REMEDIATION_ROWS]
