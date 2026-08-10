"""Alignment checks for exported SkillTree data and local lesson material."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.artifacts.json_io import JsonArtifactError, read_json_object
from src.curriculum.source_contracts import GITHUB_COMMIT_RE
from src.validation.finding import Finding


@dataclass(frozen=True)
class CourseAlignmentIssue(Finding):
    """A validation finding for SkillTree/material/quiz alignment."""

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


@dataclass(frozen=True)
class CourseAlignmentReport:
    """Summary and issues for course-material alignment."""

    summary: dict[str, int | bool]
    issues: tuple[CourseAlignmentIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class CourseAlignmentError(RuntimeError):
    """Raised when alignment inputs cannot be loaded."""


def load_json_object(path: Path) -> dict[str, Any]:
    """Load a JSON file and require an object payload."""
    try:
        return read_json_object(path)
    except FileNotFoundError as exc:
        raise CourseAlignmentError(f"{path} does not exist") from exc
    except json.JSONDecodeError as exc:
        raise CourseAlignmentError(f"{path} is not valid JSON") from exc
    except JsonArtifactError as exc:
        raise CourseAlignmentError(f"{path} must contain a JSON object") from exc


def validate_course_material_alignment_files(
    *,
    project_path: Path,
    material_index_path: Path,
    material_audit_path: Path,
) -> CourseAlignmentReport:
    """Validate generated files for course-material, quiz, and route alignment."""
    return validate_course_material_alignment(
        project=load_json_object(project_path),
        material_index=load_json_object(material_index_path),
        material_audit=load_json_object(material_audit_path),
    )


def validate_course_material_alignment(
    *,
    project: dict[str, Any],
    material_index: dict[str, Any],
    material_audit: dict[str, Any],
) -> CourseAlignmentReport:
    """Validate that exported skills, local materials, paths, and quizzes agree."""
    issues: list[CourseAlignmentIssue] = []
    skill_index, subject_by_skill = _project_skill_index(project, issues)
    dependency_prereqs, dependency_dependents = _dependency_index(
        project, skill_index, issues
    )
    quiz_index = _quiz_index(project, issues)
    skill_quiz_ids = {
        str(skill.get("quizId", "")).strip()
        for skill in skill_index.values()
        if str(skill.get("quizId", "")).strip()
    }
    for quiz_id in sorted(set(quiz_index) - skill_quiz_ids):
        issues.append(
            CourseAlignmentIssue(
                "extra-quiz",
                f"quizzes.{quiz_id}",
                "quiz is not referenced by an exported skill",
            )
        )

    material_skills = material_index.get("skills")
    if not isinstance(material_skills, dict):
        issues.append(
            CourseAlignmentIssue(
                "material-skills",
                "course_material_index.skills",
                "course material skills must be a mapping",
            )
        )
        material_skills = {}
    material_skill_ids = {str(skill_id) for skill_id in material_skills}
    exported_skill_ids = set(skill_index)
    for skill_id in sorted(exported_skill_ids - material_skill_ids):
        issues.append(
            CourseAlignmentIssue(
                "missing-material",
                f"course_material_index.skills.{skill_id}",
                "exported skill has no local material record",
            )
        )
    for skill_id in sorted(material_skill_ids - exported_skill_ids):
        issues.append(
            CourseAlignmentIssue(
                "extra-material",
                f"course_material_index.skills.{skill_id}",
                "local material record has no exported skill",
            )
        )

    _audit_summary_counts(
        material_index=material_index,
        material_audit=material_audit,
        exported_skills=len(exported_skill_ids),
        issues=issues,
    )

    section_count = 0
    pointer_count = 0
    for skill_id in sorted(exported_skill_ids & material_skill_ids):
        record = material_skills.get(skill_id)
        if not isinstance(record, dict):
            issues.append(
                CourseAlignmentIssue(
                    "material-record",
                    f"course_material_index.skills.{skill_id}",
                    "material record must be an object",
                )
            )
            continue
        skill = skill_index[skill_id]
        subject = subject_by_skill[skill_id]
        quiz_id = str(skill.get("quizId", "")).strip()
        quiz = quiz_index.get(quiz_id)
        section_count += _validate_material_record(
            skill_id=skill_id,
            skill=skill,
            subject=subject,
            quiz=quiz,
            dependency_prereqs=dependency_prereqs.get(skill_id, set()),
            dependency_dependents=dependency_dependents.get(skill_id, set()),
            record=record,
            issues=issues,
        )
        pointer_count += _pointer_count(record)

    _audit_derived_summary_counts(
        material_index=material_index,
        material_audit=material_audit,
        sections=section_count,
        external_pointers=pointer_count,
        issues=issues,
    )

    summary = {
        "skills": len(exported_skill_ids),
        "materialRecords": len(material_skill_ids),
        "quizzes": len(quiz_index),
        "dependencies": sum(len(values) for values in dependency_prereqs.values()),
        "sections": section_count,
        "externalPointers": pointer_count,
        "ok": not issues,
    }
    return CourseAlignmentReport(summary=summary, issues=tuple(issues))


def _project_skill_index(
    project: dict[str, Any],
    issues: list[CourseAlignmentIssue],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    subjects = project.get("subjects")
    skill_index: dict[str, dict[str, Any]] = {}
    subject_by_skill: dict[str, dict[str, Any]] = {}
    if not isinstance(subjects, list):
        issues.append(
            CourseAlignmentIssue(
                "project-subjects",
                "skilltree_project.subjects",
                "project subjects must be a list",
            )
        )
        return skill_index, subject_by_skill
    for subject_idx, subject in enumerate(subjects):
        if not isinstance(subject, dict):
            issues.append(
                CourseAlignmentIssue(
                    "subject",
                    f"skilltree_project.subjects[{subject_idx}]",
                    "subject must be an object",
                )
            )
            continue
        subject_id = str(subject.get("subjectId", "")).strip()
        skills = subject.get("skills")
        if not subject_id:
            issues.append(
                CourseAlignmentIssue(
                    "subject-id",
                    f"skilltree_project.subjects[{subject_idx}].subjectId",
                    "subjectId is required",
                )
            )
        if not isinstance(skills, list):
            issues.append(
                CourseAlignmentIssue(
                    "subject-skills",
                    f"skilltree_project.subjects[{subject_idx}].skills",
                    "subject skills must be a list",
                )
            )
            continue
        for skill_idx, skill in enumerate(skills):
            if not isinstance(skill, dict):
                issues.append(
                    CourseAlignmentIssue(
                        "skill",
                        f"skilltree_project.subjects[{subject_idx}].skills[{skill_idx}]",
                        "skill must be an object",
                    )
                )
                continue
            skill_id = str(skill.get("skillId", "")).strip()
            if not skill_id:
                issues.append(
                    CourseAlignmentIssue(
                        "skill-id",
                        f"skilltree_project.subjects[{subject_idx}].skills[{skill_idx}].skillId",
                        "skillId is required",
                    )
                )
                continue
            if skill_id in skill_index:
                issues.append(
                    CourseAlignmentIssue(
                        "duplicate-skill",
                        f"skilltree_project.subjects[{subject_idx}].skills[{skill_idx}]",
                        f"duplicate skillId {skill_id!r}",
                    )
                )
                continue
            skill_index[skill_id] = skill
            subject_by_skill[skill_id] = subject
    return skill_index, subject_by_skill


def _dependency_index(
    project: dict[str, Any],
    skill_index: dict[str, dict[str, Any]],
    issues: list[CourseAlignmentIssue],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    prereqs: dict[str, set[str]] = {skill_id: set() for skill_id in skill_index}
    dependents: dict[str, set[str]] = {skill_id: set() for skill_id in skill_index}
    dependencies = project.get("dependencies", [])
    if not isinstance(dependencies, list):
        issues.append(
            CourseAlignmentIssue(
                "dependencies",
                "skilltree_project.dependencies",
                "dependencies must be a list",
            )
        )
        return prereqs, dependents
    for idx, dependency in enumerate(dependencies):
        if not isinstance(dependency, dict):
            issues.append(
                CourseAlignmentIssue(
                    "dependency",
                    f"skilltree_project.dependencies[{idx}]",
                    "dependency must be an object",
                )
            )
            continue
        skill_id = str(dependency.get("skillId", "")).strip()
        prereq_id = str(dependency.get("dependsOnSkillId", "")).strip()
        if skill_id not in skill_index:
            issues.append(
                CourseAlignmentIssue(
                    "dependency-skill",
                    f"skilltree_project.dependencies[{idx}].skillId",
                    f"unknown dependent skill {skill_id!r}",
                )
            )
            continue
        if prereq_id not in skill_index:
            issues.append(
                CourseAlignmentIssue(
                    "dependency-prerequisite",
                    f"skilltree_project.dependencies[{idx}].dependsOnSkillId",
                    f"unknown prerequisite skill {prereq_id!r}",
                )
            )
            continue
        if skill_id == prereq_id:
            issues.append(
                CourseAlignmentIssue(
                    "dependency-self-loop",
                    f"skilltree_project.dependencies[{idx}]",
                    "skill cannot depend on itself",
                )
            )
            continue
        prereqs[skill_id].add(prereq_id)
        dependents[prereq_id].add(skill_id)
    return prereqs, dependents


def _quiz_index(
    project: dict[str, Any],
    issues: list[CourseAlignmentIssue],
) -> dict[str, dict[str, Any]]:
    quizzes = project.get("quizzes")
    quiz_index: dict[str, dict[str, Any]] = {}
    if not isinstance(quizzes, list):
        issues.append(
            CourseAlignmentIssue(
                "quizzes",
                "skilltree_project.quizzes",
                "quizzes must be a list",
            )
        )
        return quiz_index
    for idx, quiz in enumerate(quizzes):
        if not isinstance(quiz, dict):
            issues.append(
                CourseAlignmentIssue(
                    "quiz",
                    f"skilltree_project.quizzes[{idx}]",
                    "quiz must be an object",
                )
            )
            continue
        quiz_id = str(quiz.get("quizId", "")).strip()
        if not quiz_id:
            issues.append(
                CourseAlignmentIssue(
                    "quiz-id",
                    f"skilltree_project.quizzes[{idx}].quizId",
                    "quizId is required",
                )
            )
            continue
        if quiz_id in quiz_index:
            issues.append(
                CourseAlignmentIssue(
                    "duplicate-quiz",
                    f"skilltree_project.quizzes[{idx}]",
                    f"duplicate quizId {quiz_id!r}",
                )
            )
            continue
        quiz_index[quiz_id] = quiz
        _validate_quiz(quiz_id, quiz, issues)
    return quiz_index


def _validate_quiz(
    quiz_id: str,
    quiz: dict[str, Any],
    issues: list[CourseAlignmentIssue],
) -> None:
    questions = quiz.get("questions")
    num_questions = quiz.get("numQuestions")
    if not isinstance(questions, list) or not questions:
        issues.append(
            CourseAlignmentIssue(
                "quiz-questions",
                f"skilltree_project.quizzes.{quiz_id}.questions",
                "quiz must include non-empty questions",
            )
        )
        return
    if num_questions != len(questions):
        issues.append(
            CourseAlignmentIssue(
                "quiz-question-count",
                f"skilltree_project.quizzes.{quiz_id}.numQuestions",
                "numQuestions must match the number of question rows",
            )
        )
    passing_percent = quiz.get("passingPercent")
    if not isinstance(passing_percent, int) or not 1 <= passing_percent <= 100:
        issues.append(
            CourseAlignmentIssue(
                "quiz-passing-percent",
                f"skilltree_project.quizzes.{quiz_id}.passingPercent",
                "passingPercent must be an integer in 1..100",
            )
        )
    for question_idx, question in enumerate(questions):
        location = f"skilltree_project.quizzes.{quiz_id}.questions[{question_idx}]"
        if not isinstance(question, dict):
            issues.append(
                CourseAlignmentIssue(
                    "quiz-question", location, "question must be an object"
                )
            )
            continue
        if not str(question.get("question", "")).strip():
            issues.append(
                CourseAlignmentIssue(
                    "quiz-question-text",
                    f"{location}.question",
                    "question text is required",
                )
            )
        answers = question.get("answers")
        if not isinstance(answers, list) or not answers:
            issues.append(
                CourseAlignmentIssue(
                    "quiz-answers",
                    f"{location}.answers",
                    "question must include answer rows",
                )
            )
            continue
        if not any(
            isinstance(answer, dict) and bool(answer.get("isCorrect"))
            for answer in answers
        ):
            issues.append(
                CourseAlignmentIssue(
                    "quiz-correct-answer",
                    f"{location}.answers",
                    "question must mark at least one answer correct",
                )
            )
        for answer_idx, answer in enumerate(answers):
            answer_location = f"{location}.answers[{answer_idx}]"
            if not isinstance(answer, dict):
                issues.append(
                    CourseAlignmentIssue(
                        "quiz-answer",
                        answer_location,
                        "answer must be an object",
                    )
                )
                continue
            if "answer" not in answer or "isCorrect" not in answer:
                issues.append(
                    CourseAlignmentIssue(
                        "quiz-answer-fields",
                        answer_location,
                        "answer rows need answer and isCorrect fields",
                    )
                )


def _audit_summary_counts(
    *,
    material_index: dict[str, Any],
    material_audit: dict[str, Any],
    exported_skills: int,
    issues: list[CourseAlignmentIssue],
) -> None:
    audit_issues = material_audit.get("issues")
    if audit_issues != []:
        issues.append(
            CourseAlignmentIssue(
                "material-audit-issues",
                "course_material_audit.issues",
                "course material audit must be clean",
            )
        )
    audit_summary = material_audit.get("summary")
    index_summary = material_index.get("summary")
    if not isinstance(audit_summary, dict):
        issues.append(
            CourseAlignmentIssue(
                "material-audit-summary",
                "course_material_audit.summary",
                "course material audit summary must be an object",
            )
        )
        audit_summary = {}
    if not isinstance(index_summary, dict):
        issues.append(
            CourseAlignmentIssue(
                "material-index-summary",
                "course_material_index.summary",
                "course material index summary must be an object",
            )
        )
        index_summary = {}
    if audit_summary.get("ok") is not True:
        issues.append(
            CourseAlignmentIssue(
                "material-audit-ok",
                "course_material_audit.summary.ok",
                "course material audit summary must be ok",
            )
        )
    for key in ("skills", "materialRecords", "externalPointers", "sections"):
        if key not in audit_summary:
            issues.append(
                CourseAlignmentIssue(
                    "material-audit-summary-field",
                    f"course_material_audit.summary.{key}",
                    f"course material audit summary must include {key}",
                )
            )
    for key in ("skills", "externalPointers", "sources"):
        if key not in index_summary:
            issues.append(
                CourseAlignmentIssue(
                    "material-index-summary-field",
                    f"course_material_index.summary.{key}",
                    f"course material index summary must include {key}",
                )
            )
    for location, summary in (
        ("course_material_audit.summary", audit_summary),
        ("course_material_index.summary", index_summary),
    ):
        for key in ("skills", "materialRecords"):
            if key in summary and summary.get(key) != exported_skills:
                issues.append(
                    CourseAlignmentIssue(
                        "material-count",
                        f"{location}.{key}",
                        f"{key} must equal exported skill count {exported_skills}",
                    )
                )
        external_pointers = summary.get("externalPointers")
        if isinstance(external_pointers, int) and external_pointers < exported_skills:
            issues.append(
                CourseAlignmentIssue(
                    "material-pointer-count",
                    f"{location}.externalPointers",
                    "external pointer count must be at least one per skill",
                )
            )


def _audit_derived_summary_counts(
    *,
    material_index: dict[str, Any],
    material_audit: dict[str, Any],
    sections: int,
    external_pointers: int,
    issues: list[CourseAlignmentIssue],
) -> None:
    """Ensure summary counters cannot certify stale material records."""
    checks = (
        (material_audit, "course_material_audit.summary", "sections", sections),
        (
            material_audit,
            "course_material_audit.summary",
            "externalPointers",
            external_pointers,
        ),
        (
            material_index,
            "course_material_index.summary",
            "externalPointers",
            external_pointers,
        ),
    )
    for payload, location, key, expected in checks:
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            continue
        if summary.get(key) != expected:
            issues.append(
                CourseAlignmentIssue(
                    "material-summary-count",
                    f"{location}.{key}",
                    f"{key} must equal the validated record count {expected}",
                )
            )


def _validate_material_record(
    *,
    skill_id: str,
    skill: dict[str, Any],
    subject: dict[str, Any],
    quiz: dict[str, Any] | None,
    dependency_prereqs: set[str],
    dependency_dependents: set[str],
    record: dict[str, Any],
    issues: list[CourseAlignmentIssue],
) -> int:
    location = f"course_material_index.skills.{skill_id}"
    subject_id = str(subject.get("subjectId", "")).strip()
    quiz_id = str(skill.get("quizId", "")).strip()
    if str(record.get("skillId", "")).strip() != skill_id:
        issues.append(
            CourseAlignmentIssue(
                "material-skill-id",
                f"{location}.skillId",
                "material record skillId must match its map key",
            )
        )
    if str(record.get("subjectId", "")).strip() != subject_id:
        issues.append(
            CourseAlignmentIssue(
                "material-subject-id",
                f"{location}.subjectId",
                "material record subjectId must match the exported subject",
            )
        )
    if str(skill.get("selfReportingType", "")).strip() != "Quiz":
        issues.append(
            CourseAlignmentIssue(
                "skill-reporting-type",
                f"skilltree_project.skills.{skill_id}.selfReportingType",
                "exported skill must be quiz-gated",
            )
        )
    if not quiz_id:
        issues.append(
            CourseAlignmentIssue(
                "missing-skill-quiz",
                f"skilltree_project.skills.{skill_id}.quizId",
                "exported skill must reference a quiz",
            )
        )
    elif quiz is None:
        issues.append(
            CourseAlignmentIssue(
                "missing-quiz",
                f"skilltree_project.quizzes.{quiz_id}",
                "exported skill references a missing quiz",
            )
        )

    section_count = _validate_sections(location, record, issues)
    _validate_pointers(location, record, issues)
    _validate_handoff(
        location=location,
        skill_id=skill_id,
        subject_id=subject_id,
        quiz_id=quiz_id,
        record=record,
        issues=issues,
    )
    if quiz is not None:
        _validate_assessment_summary(
            location=location,
            record=record,
            quiz=quiz,
            issues=issues,
        )
    _validate_material_learning_path(
        location=location,
        record=record,
        dependency_prereqs=dependency_prereqs,
        dependency_dependents=dependency_dependents,
        issues=issues,
    )
    return section_count


def _validate_sections(
    location: str,
    record: dict[str, Any],
    issues: list[CourseAlignmentIssue],
) -> int:
    sections = record.get("sections")
    if not isinstance(sections, list) or not sections:
        issues.append(
            CourseAlignmentIssue(
                "material-sections",
                f"{location}.sections",
                "material record must include non-empty sections",
            )
        )
        return 0
    for section_idx, section in enumerate(sections):
        section_location = f"{location}.sections[{section_idx}]"
        if not isinstance(section, dict):
            issues.append(
                CourseAlignmentIssue(
                    "material-section",
                    section_location,
                    "section must be an object",
                )
            )
            continue
        if not str(section.get("heading", "")).strip():
            issues.append(
                CourseAlignmentIssue(
                    "material-section-heading",
                    f"{section_location}.heading",
                    "section heading is required",
                )
            )
        if not str(section.get("body", "")).strip():
            issues.append(
                CourseAlignmentIssue(
                    "material-section-body",
                    f"{section_location}.body",
                    "section body is required",
                )
            )
    return len(sections)


def _validate_pointers(
    location: str,
    record: dict[str, Any],
    issues: list[CourseAlignmentIssue],
) -> None:
    pointers = record.get("externalPointers")
    if not isinstance(pointers, list) or not pointers:
        issues.append(
            CourseAlignmentIssue(
                "material-pointers",
                f"{location}.externalPointers",
                "material record must include at least one external pointer",
            )
        )
        return
    for pointer_idx, pointer in enumerate(pointers):
        pointer_location = f"{location}.externalPointers[{pointer_idx}]"
        if not isinstance(pointer, dict):
            issues.append(
                CourseAlignmentIssue(
                    "material-pointer",
                    pointer_location,
                    "external pointer must be an object",
                )
            )
            continue
        commit = str(pointer.get("commit", "")).strip()
        url = str(pointer.get("url", "")).strip()
        path = str(pointer.get("path", "")).strip()
        for key in (
            "sourceId",
            "sourceTitle",
            "title",
            "role",
            "url",
            "path",
            "commit",
        ):
            if not str(pointer.get(key, "")).strip():
                issues.append(
                    CourseAlignmentIssue(
                        "material-pointer-field",
                        f"{pointer_location}.{key}",
                        f"{key} is required",
                    )
                )
        if commit and not GITHUB_COMMIT_RE.match(commit):
            issues.append(
                CourseAlignmentIssue(
                    "material-pointer-commit",
                    f"{pointer_location}.commit",
                    "pointer commit must be a pinned 40-character SHA",
                )
            )
        if commit and path and f"/blob/{commit}/{path}" not in url:
            issues.append(
                CourseAlignmentIssue(
                    "material-pointer-url",
                    f"{pointer_location}.url",
                    "pointer URL must include the pinned commit and path",
                )
            )
        parsed_url = urlparse(url)
        if (
            parsed_url.scheme not in {"http", "https"}
            or not parsed_url.netloc
            or parsed_url.username is not None
            or parsed_url.password is not None
        ):
            issues.append(
                CourseAlignmentIssue(
                    "material-pointer-url-scheme",
                    f"{pointer_location}.url",
                    "pointer URL must be an absolute http/https URL without embedded credentials",
                )
            )


def _validate_handoff(
    *,
    location: str,
    skill_id: str,
    subject_id: str,
    quiz_id: str,
    record: dict[str, Any],
    issues: list[CourseAlignmentIssue],
) -> None:
    official = record.get("officialSkillTree")
    if not isinstance(official, dict):
        issues.append(
            CourseAlignmentIssue(
                "material-handoff",
                f"{location}.officialSkillTree",
                "officialSkillTree handoff metadata is required",
            )
        )
        return
    expected_subject_route = f"/subjects/{subject_id}"
    expected_quiz_route = f"/subjects/{subject_id}/skills/{skill_id}/quizzes/{quiz_id}"
    subject_route = str(official.get("subjectRoute", "")).strip()
    quiz_route = str(official.get("quizRoute", "")).strip()
    unsafe_route = str(official.get("unsafeDirectSkillRoute", "")).strip()
    if subject_route != expected_subject_route:
        issues.append(
            CourseAlignmentIssue(
                "material-subject-route",
                f"{location}.officialSkillTree.subjectRoute",
                f"subject route must be {expected_subject_route!r}",
            )
        )
    if unsafe_route:
        issues.append(
            CourseAlignmentIssue(
                "material-unsafe-route",
                f"{location}.officialSkillTree.unsafeDirectSkillRoute",
                "unsafe direct skill-detail route must stay empty",
            )
        )
    if quiz_id and quiz_route != expected_quiz_route:
        issues.append(
            CourseAlignmentIssue(
                "material-quiz-route",
                f"{location}.officialSkillTree.quizRoute",
                f"quiz route must be {expected_quiz_route!r}",
            )
        )


def _validate_assessment_summary(
    *,
    location: str,
    record: dict[str, Any],
    quiz: dict[str, Any],
    issues: list[CourseAlignmentIssue],
) -> None:
    summary = record.get("assessmentSummary")
    if not isinstance(summary, dict):
        issues.append(
            CourseAlignmentIssue(
                "material-assessment-summary",
                f"{location}.assessmentSummary",
                "assessment summary is required",
            )
        )
        return
    questions = quiz.get("questions")
    question_rows = questions if isinstance(questions, list) else []
    question_count = len(question_rows)
    if summary.get("questionCount") != question_count:
        issues.append(
            CourseAlignmentIssue(
                "material-assessment-count",
                f"{location}.assessmentSummary.questionCount",
                "material assessment count must match exported quiz question count",
            )
        )
    expected_types = sorted(
        {
            str(question.get("questionType", "")).strip()
            for question in question_rows
            if isinstance(question, dict)
        }
    )
    if summary.get("questionTypes") != expected_types:
        issues.append(
            CourseAlignmentIssue(
                "material-assessment-types",
                f"{location}.assessmentSummary.questionTypes",
                "material assessment types must match exported quiz question types",
            )
        )


def _validate_material_learning_path(
    *,
    location: str,
    record: dict[str, Any],
    dependency_prereqs: set[str],
    dependency_dependents: set[str],
    issues: list[CourseAlignmentIssue],
) -> None:
    prereq_ids = _skill_ref_ids(record.get("prerequisites"))
    downstream_ids = _skill_ref_ids(record.get("downstreamSkills"))
    if prereq_ids != dependency_prereqs:
        issues.append(
            CourseAlignmentIssue(
                "material-prerequisites",
                f"{location}.prerequisites",
                "material prerequisites must match exported dependencies",
            )
        )
    if downstream_ids != dependency_dependents:
        issues.append(
            CourseAlignmentIssue(
                "material-downstream",
                f"{location}.downstreamSkills",
                "material downstream skills must match exported dependents",
            )
        )


def _skill_ref_ids(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {
        str(item.get("skillId", "")).strip()
        for item in value
        if isinstance(item, dict) and str(item.get("skillId", "")).strip()
    }


def _pointer_count(record: dict[str, Any]) -> int:
    pointers = record.get("externalPointers")
    return len(pointers) if isinstance(pointers, list) else 0
