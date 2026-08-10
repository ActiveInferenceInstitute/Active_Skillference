"""Learner-quality checks for the assembled curriculum graph.

These checks deliberately sit above structural DAG validity. A graph can be acyclic,
connected, and exportable while still giving learners shallow quizzes, biased answer
positions, terse descriptions, or learning-path prerequisites that violate the
documented roots-to-canopy stratum order.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import _STRATUM_ORDER, CurriculumError
from src.validation.finding import Finding

MIN_ASSESSMENTS_PER_SKILL = 4
MIN_SKILL_DESCRIPTION_WORDS = 18
MIN_SUBJECT_DESCRIPTION_WORDS = 10
MAX_BALANCED_CORRECT_ANSWER_INDEX_SHARE = 0.45
MIN_PRESENT_ANSWER_INDEX_SHARE = 0.10
MIN_BALANCED_CORRECT_ANSWER_INDEX_SHARE = 0.10
# The correct answer must not be identifiable by length in EITHER direction, per
# answer-count bucket. A one-sided "not the longest" rule pushes the correct answer to
# never-shortest, itself a pick-shortest cue. Within each bucket the strictly-longest and
# strictly-shortest correct shares must both sit near chance (1/n): between the floor and
# the cap. (4-answer chance 0.25, 3-answer 0.33; the band brackets both with margin.)
MAX_LENGTH_RANK_SHARE = 0.42
MIN_LENGTH_RANK_SHARE = 0.12
# No single option index may be a member of the correct set in more than this share of
# multiple-choice questions (chance for a 2-of-4 item is 0.5).
MAX_MC_INDEX_CORRECT_SHARE = 0.60
# No single correct *subset* (e.g. exactly {0, 2}) may cover more than this share of
# multiple-choice questions. Per-index balance alone is gameable: a constant two-index
# rule still passes if the joint distribution is dominated by one or two subsets. With
# C(4, 2)=6 subsets cycled evenly each is ~17%, so 0.30 leaves margin while catching a
# degenerate distribution.
MAX_MC_CORRECT_SET_SHARE = 0.30
# An objective string may be shared by at most this many skills before it reads as
# templated filler rather than a per-skill learning purpose.
MAX_OBJECTIVE_REUSE = 4
# No single name-normalized answer body may appear in the assessments of more than this
# share of skills (measured with the per-skill name stripped, so a template spliced with
# the skill name cannot masquerade as unique). Bounds the original verbatim boilerplate
# (~89% of skills) and any regression; the residual is the per-family review rubrics
# (open-science and mastery), each exactly one (stratum x role) family of 64 skills =
# 10.7%, so the cap sits just above that declared, disclosed instrument scale.
MAX_ANSWER_REUSE_SHARE = 0.12


@dataclass(frozen=True)
class CurriculumQualityIssue(Finding):
    """A concrete quality issue found in a curriculum graph."""


@dataclass(frozen=True)
class SemanticPrerequisiteCoverage:
    """Reachability and assessment-use counts for one semantic prerequisite concept."""

    concept: str
    definers: tuple[str, ...]
    reachable_skills: int
    assessed_skills: int


def _word_count(text: str) -> int:
    return len(text.split())


def audit_curriculum_quality(graph: CurriculumGraph) -> list[CurriculumQualityIssue]:
    """Return learner-quality issues that structural validation does not cover."""
    issues: list[CurriculumQualityIssue] = []
    by_id = {skill.skill_id: skill for skill in graph.skills}

    for subject in graph.subjects:
        if _word_count(subject.description) < MIN_SUBJECT_DESCRIPTION_WORDS:
            issues.append(
                CurriculumQualityIssue(
                    "terse_subject_description",
                    subject.subject_id,
                    "subject descriptions should orient the learner, not only label a bucket",
                )
            )

    for skill in graph.skills:
        if len(skill.assessments) < MIN_ASSESSMENTS_PER_SKILL:
            issues.append(
                CurriculumQualityIssue(
                    "assessment_depth",
                    skill.skill_id,
                    f"expected at least {MIN_ASSESSMENTS_PER_SKILL} failable assessments",
                )
            )
        if not any(q.question_type == "MultipleChoice" for q in skill.assessments):
            issues.append(
                CurriculumQualityIssue(
                    "assessment_variety",
                    skill.skill_id,
                    "skills should include a transfer-style multiple-choice assessment",
                )
            )
        if _word_count(skill.description) < MIN_SKILL_DESCRIPTION_WORDS:
            issues.append(
                CurriculumQualityIssue(
                    "terse_skill_description",
                    skill.skill_id,
                    "skill descriptions should explain the concept and its downstream role",
                )
            )
        if len(skill.tags) < 2 or skill.stratum.value not in skill.tags:
            issues.append(
                CurriculumQualityIssue(
                    "missing_tags",
                    skill.skill_id,
                    "skills should carry at least stratum and topic tags",
                )
            )
        for prereq_id in skill.prerequisites:
            prereq = by_id.get(prereq_id)
            if prereq is None:
                continue
            if prereq.stratum.order > skill.stratum.order:
                issues.append(
                    CurriculumQualityIssue(
                        "backward_prerequisite",
                        skill.skill_id,
                        f"{prereq_id} is in later stratum {prereq.stratum.value}",
                    )
                )
        for related_id in skill.related:
            if related_id == skill.skill_id:
                issues.append(
                    CurriculumQualityIssue(
                        "self_related",
                        skill.skill_id,
                        "a skill cannot list itself as a related concept",
                    )
                )
            elif related_id not in by_id:
                issues.append(
                    CurriculumQualityIssue(
                        "dangling_related",
                        skill.skill_id,
                        f"related skill {related_id!r} does not exist",
                    )
                )
        duplicated_related = set(skill.related) & set(skill.prerequisites)
        if duplicated_related:
            issues.append(
                CurriculumQualityIssue(
                    "related_duplicates_prerequisite",
                    skill.skill_id,
                    f"related links duplicate prerequisites: {sorted(duplicated_related)!r}",
                )
            )

    issues.extend(_audit_objective_reuse(graph))
    issues.extend(_audit_answer_reuse(graph))
    issues.extend(_audit_answer_balance(graph))
    issues.extend(_audit_banned_phrases(graph))
    issues.extend(_audit_implausible_distractors(graph))
    issues.extend(audit_semantic_prerequisites(graph))
    return issues


# Off-domain placeholder strings that were once used as throwaway quiz DISTRACTORS —
# software/UI/platform-plumbing nouns dropped into mathematics or inference questions
# (e.g. "Pixels", "Docker volumes", "CPU vendor", "the subject id"). A learner can
# eliminate them without understanding anything, so they defeat the quiz's diagnostic
# purpose. Two mechanisms, both scoped to INCORRECT answers only (so a term that is
# legitimately the correct answer — or used inside a substantive distractor sentence —
# is never flagged):
#
#   1. BANNED_PLACEHOLDER_DISTRACTORS — full-phrase guard for dual-use words (docker,
#      pixels, cpu, wall-clock, json…) and platform-meta phrases (subject id, repository
#      name…) that ARE legitimate elsewhere, so they can only be matched as a whole
#      distractor, not as a substring. This is a verbatim regression guard for the known
#      filler pool.
#   2. _OFF_DOMAIN_DISTRACTOR_SUBSTRINGS — a display/UI vocabulary (font, screen,
#      brightness, screenshot, typography…) that is never a legitimate answer to a science
#      question in ANY stratum, so it is matched as a substring and catches the whole
#      CLASS, including new variants. test_real_catalog_passes_curriculum_quality_gate is
#      the empirical guard that this set never collides with a legitimate distractor.
#
# This is still not a general semantic-plausibility judge of arbitrary new distractors;
# it targets the specific off-domain filler classes above.
BANNED_PLACEHOLDER_DISTRACTORS: frozenset[str] = frozenset(
    {
        "a docker network",
        "a generated json file",
        "a public repository url",
        "a rendered json file",
        "an arbitrary file name",
        "bone fractures",
        "cpu vendor",
        "docker image tags",
        "docker volumes",
        "identifier normalisation",
        "matplotlib style choices",
        "network latency",
        "only a dashboard and a database",
        "only docker ports",
        "only duplicate subject names",
        "only local readme edits",
        "only repository privacy",
        "only the author's preferred terminology",
        "only the repository name",
        "only the subject title",
        "pixels",
        "python syntax",
        "subject display order",
        "subject identity uniqueness",
        "the alphabetic order of skills",
        "the dashboard uses the same tab",
        "the docker compose file",
        "the docker daemon version",
        "the final deployment command",
        "the order of quiz answers",
        "the server's cpu load",
        "the skill name remains short",
        "the subject id",
        "the subject id changed",
        "the wall-clock alone",
        "wall-clock time",
    }
)
# Display/UI/presentation vocabulary that is never a legitimate science-quiz answer.
# Matched as a substring of an incorrect answer, so the whole class is caught.
_OFF_DOMAIN_DISTRACTOR_SUBSTRINGS: frozenset[str] = frozenset(
    {
        "brightness",
        "button rendering",
        "api route",
        "branch name",
        "color map",
        "color palette",
        "colour map",
        "colour palette",
        "css ",
        "database driver",
        "export order",
        "favicon",
        "font",
        "icon set",
        "markdown file",
        "menu bar",
        "module import",
        "plotting colour",
        "plotting resolution",
        "quiz title",
        "rendered title",
        "screen brightness",
        "screen dimension",
        "screen resolution",
        "screenshot",
        "static title",
        "the exact font",
        "toolbar",
        "typograph",
        "web server",
        "widget",
        # Extended off-domain classes (compute-infra / web / finance) that have no
        # legitimate meaning as a science-quiz answer. Dual-use stems that DO occur in
        # Active Inference prose (memory, process, cache, buffer, thread, state, policy,
        # gradient) are deliberately EXCLUDED here and kept to full-phrase guards only —
        # see the gotcha on substring dual-use false positives. This list is not
        # exhaustive; the real-corpus test is the empirical false-positive guard.
        "blockchain",
        "browser cache",
        "cryptocurrency",
        "docker registry",
        "dropdown menu",
        "file extension",
        "gpu core",
        "html element",
        "html tag",
        "javascript",
        "keyboard shortcut",
        "kubernetes",
        "login button",
        "merge conflict",
        "mouse cursor",
        "smart contract",
        "stack trace",
        "url slug",
    }
)
# A length-balancing clause is appended as ", ..." or " — ...", so a full-phrase banned
# distractor survives as exactly the phrase or the phrase immediately followed by a clause.
_BALANCE_CLAUSE_OPENERS = (", ", " — ")


def _matched_placeholder_distractor(answer: str) -> str | None:
    """Return the off-domain placeholder an answer matches, ignoring appended clauses.

    A full-phrase banned distractor matches when the answer is exactly that phrase or that
    phrase immediately followed by an appended length-balancing clause; this is precise, so
    "Pixels in a raster image" does NOT match "pixels". A display-vocabulary substring
    matches anywhere in the answer, catching the whole off-domain class.
    """
    text = answer.strip().rstrip(".").lower()
    for banned in BANNED_PLACEHOLDER_DISTRACTORS:
        if text == banned or any(
            text.startswith(banned + opener) for opener in _BALANCE_CLAUSE_OPENERS
        ):
            return banned
    for substring in _OFF_DOMAIN_DISTRACTOR_SUBSTRINGS:
        if substring in text:
            return substring
    return None


# Load-bearing concepts a skill cannot legitimately *use* unless the concept's defining
# skill is reachable through its (transitive) prerequisites. Each entry maps a concept to
# (regex patterns that signal genuine use, defining skill ids). Patterns are matched
# case-insensitively against learner-facing text. Kept deliberately to unambiguous,
# single-definer concepts so the gate fires on real pedagogical inversions without
# false-positiving on incidental mentions — the real graph is the empirical guard.
# Only concepts that are ACTUALLY assessed somewhere belong here: a concept with zero
# assessment matches makes the gate vacuous for it (an empty scan can never fire — the
# "non-empty-scan" guard in test_curriculum_quality enforces that every entry has teeth).
# Taylor expansion was removed for exactly this reason: no skill is assessed on it, so the
# entry guarded nothing. Re-add a concept here only once live content is assessed on it.
_CONCEPT_PREREQUISITES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    # Patterns tolerate plural/possessive forms (KLs, ELBOs) so a quiz phrased in the
    # plural cannot escape the gate while the singular triggers it (triple-check #2).
    ("KL divergence", (r"\bKLs?\b", r"kullback", r"\\mathrm\{KL\}"), ("it_kl",)),
    ("Markov chain", (r"markov",), ("p_markov_chain",)),
    ("Laplace approximation", (r"laplace",), ("vm_laplace",)),
    ("ELBO", (r"\bELBOs?\b", r"evidence lower bound"), ("vm_elbo",)),
)


def transitive_prerequisites(graph: CurriculumGraph) -> dict[str, set[str]]:
    """Return each skill id -> the set of all skills reachable through prerequisites."""
    direct = {s.skill_id: set(s.prerequisites) for s in graph.skills}
    closure: dict[str, set[str]] = {}

    def resolve(sid: str, seen: frozenset[str]) -> set[str]:
        if sid in closure:
            return closure[sid]
        acc: set[str] = set()
        for prereq in direct.get(sid, set()):
            if prereq in seen:  # guard (graph is a validated DAG, but be defensive)
                continue
            acc.add(prereq)
            acc |= resolve(prereq, seen | {prereq})
        closure[sid] = acc
        return acc

    for skill in graph.skills:
        resolve(skill.skill_id, frozenset({skill.skill_id}))
    return closure


def semantic_prerequisite_coverage(
    graph: CurriculumGraph,
) -> tuple[SemanticPrerequisiteCoverage, ...]:
    """Return concept-level reachability counts used by the semantic coverage figure."""
    closure = transitive_prerequisites(graph)
    by_id = {s.skill_id: s for s in graph.skills}
    rows: list[SemanticPrerequisiteCoverage] = []
    for concept, patterns, definers in _CONCEPT_PREREQUISITES:
        compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        reach = sum(
            1
            for prereqs in closure.values()
            if any(definer in prereqs for definer in definers)
        )
        assessed = 0
        for skill in graph.skills:
            if skill.skill_id in definers:
                continue
            text = " ".join(
                tuple(question.prompt for question in skill.assessments)
                + tuple(
                    answer
                    for question in skill.assessments
                    for answer in question.answers
                )
            )
            if any(regex.search(text) for regex in compiled):
                assessed += 1
        rows.append(
            SemanticPrerequisiteCoverage(
                concept=concept,
                definers=tuple(definer for definer in definers if definer in by_id),
                reachable_skills=reach,
                assessed_skills=assessed,
            )
        )
    return tuple(rows)


def audit_semantic_prerequisites(
    graph: CurriculumGraph,
) -> list[CurriculumQualityIssue]:
    """Flag a skill *assessed on* a load-bearing concept without the concept's defining
    skill in its transitive prerequisite closure — a learner would be tested on the
    concept before they could have learned it.

    Two deliberate scoping rules keep the gate sharp (fires on real inversions, not on
    motivation):
    1. Scan only **assessment** text (prompts + answers). A description may legitimately
       motivate a downstream concept forward; what a learner is *tested on* is what they
       must already hold as a prerequisite.
    2. Only flag when the definer's stratum is at-or-before the using skill's stratum, so
       a genuine prerequisite edge could exist. A definer in a later stratum is a forward
       reference (e.g. Taylor's quiz naming Laplace as a downstream application), not a
       missing prerequisite — flagging it would demand an illegal backward edge.
    """
    issues: list[CurriculumQualityIssue] = []
    patterns = [
        (concept, [re.compile(p, re.IGNORECASE) for p in pats], definers)
        for concept, pats, definers in _CONCEPT_PREREQUISITES
    ]
    closure = transitive_prerequisites(graph)
    by_id = {s.skill_id: s for s in graph.skills}
    for skill in graph.skills:
        text = " ".join(
            tuple(q.prompt for q in skill.assessments)
            + tuple(a for q in skill.assessments for a in q.answers)
        )
        reachable = closure.get(skill.skill_id, set())
        user_rank = _STRATUM_ORDER[skill.stratum]
        for concept, compiled, definers in patterns:
            if skill.skill_id in definers:
                continue
            reachable_definers = [
                d
                for d in definers
                if d in by_id and _STRATUM_ORDER[by_id[d].stratum] <= user_rank
            ]
            if not reachable_definers:
                continue  # definer only exists in a later stratum → forward reference
            if not any(rx.search(text) for rx in compiled):
                continue
            if not any(d in reachable for d in reachable_definers):
                issues.append(
                    CurriculumQualityIssue(
                        "semantic_prerequisite_missing",
                        skill.skill_id,
                        f"is assessed on {concept!r} but no defining skill "
                        f"{tuple(reachable_definers)} is in its transitive prerequisites",
                    )
                )
    return issues


def _transitive_prerequisites(graph: CurriculumGraph) -> dict[str, set[str]]:
    """Compatibility wrapper for older internal tests; prefer the public helper."""
    return transitive_prerequisites(graph)


def _audit_semantic_prerequisites(
    graph: CurriculumGraph,
) -> list[CurriculumQualityIssue]:
    """Compatibility wrapper for older internal tests; prefer the public helper."""
    return audit_semantic_prerequisites(graph)


def _audit_implausible_distractors(
    graph: CurriculumGraph,
) -> list[CurriculumQualityIssue]:
    """Flag known off-domain placeholder strings used as quiz distractors."""
    issues: list[CurriculumQualityIssue] = []
    for skill in graph.skills:
        for question in skill.assessments:
            for index, answer in enumerate(question.answers):
                if index in question.correct:
                    continue
                banned = _matched_placeholder_distractor(answer)
                if banned is not None:
                    issues.append(
                        CurriculumQualityIssue(
                            "implausible_distractor",
                            skill.skill_id,
                            f"off-domain placeholder used as a distractor: {banned!r}",
                        )
                    )
    return issues


def _audit_answer_reuse(graph: CurriculumGraph) -> list[CurriculumQualityIssue]:
    """Flag a non-rubric answer body reused across too large a share of skills.

    Items marked ``origin == "rubric"`` are shared metacognitive instruments applied
    across skills by design (transfer/misuse/diagnostic) and are exempt — the manuscript
    discloses them as such, and a separate check bounds their per-skill footprint. For
    every BESPOKE (authored) item, reuse is measured on the name-normalized body so a
    template spliced with the per-skill name (or stratum strand) cannot masquerade as
    unique; an authored answer reused across the curriculum is real boilerplate and fails.
    """
    issues: list[CurriculumQualityIssue] = []
    total = len(graph.skills)
    if not total:
        return issues
    skills_per_answer: Counter[str] = Counter()
    for skill in graph.skills:
        answers = {
            answer.replace(skill.name, "{SKILL}")
            for question in skill.assessments
            if question.origin != "rubric"
            for answer in question.answers
        }
        skills_per_answer.update(answers)
        # The shared rubric must not be a skill's ENTIRE assessment: every skill needs at
        # least one bespoke (authored) item so the rubric is scaffolding, not the whole quiz.
        if skill.assessments and all(q.origin == "rubric" for q in skill.assessments):
            issues.append(
                CurriculumQualityIssue(
                    "all_rubric_assessments",
                    skill.skill_id,
                    "skill has only shared rubric items and no bespoke domain assessment",
                )
            )
    for answer, count in skills_per_answer.most_common():
        share = count / total
        if share > MAX_ANSWER_REUSE_SHARE:
            issues.append(
                CurriculumQualityIssue(
                    "answer_reuse",
                    "assessments",
                    f"answer body is reused across {count} skills ({share:.1%}): "
                    f"{answer[:50]!r}",
                )
            )
    return issues


# Endorsement-overreach phrases forbidden in learner-facing curriculum/quiz text. This
# mirrors src.manuscript.claim_support.STRONG_PHRASES (kept in sync by
# test_banned_phrase_list_matches_manuscript) but is defined here so the curriculum
# package never imports the manuscript package (which would reverse the dependency
# direction and create a cycle).
BANNED_ENDORSEMENT_PHRASES: tuple[str, ...] = (
    "national-security grade",
    "national security grade",
    "government validated",
    "government-validated",
    "nsa approved",
    "nsa-approved",
)
_BANNED_PHRASE_RE = re.compile(
    "|".join(re.escape(phrase) for phrase in BANNED_ENDORSEMENT_PHRASES),
    re.IGNORECASE,
)


def _audit_banned_phrases(graph: CurriculumGraph) -> list[CurriculumQualityIssue]:
    """Flag endorsement-overreach phrases (e.g. "NSA approved") in learner-facing text.

    The manuscript already blocks these phrases; this extends the same blocklist to the
    600-skill curriculum and quiz content, which is the published SkillTree surface.
    """
    issues: list[CurriculumQualityIssue] = []
    for skill in graph.skills:
        texts = [skill.name, skill.objective, skill.description]
        for question in skill.assessments:
            texts.append(question.prompt)
            texts.extend(question.answers)
        for text in texts:
            for match in _BANNED_PHRASE_RE.finditer(text):
                issues.append(
                    CurriculumQualityIssue(
                        "banned_endorsement_phrase",
                        skill.skill_id,
                        f"learner-facing text contains banned phrase {match.group(0)!r}",
                    )
                )
    return issues


# Buckets smaller than this are too small for a stable position distribution. The real
# catalog only has large 3-answer and 4-answer buckets, so this guards against noise on
# a rare odd-count bucket without disabling the audit on either real bucket.
_MIN_BUCKET_FOR_POSITION_AUDIT = 12


def _audit_objective_reuse(graph: CurriculumGraph) -> list[CurriculumQualityIssue]:
    """Flag objective strings reused across many skills (templated-filler signal)."""
    issues: list[CurriculumQualityIssue] = []
    counts = Counter(skill.objective.strip() for skill in graph.skills)
    for objective, count in sorted(counts.items()):
        if count > MAX_OBJECTIVE_REUSE:
            issues.append(
                CurriculumQualityIssue(
                    "duplicate_objective",
                    "assessments",
                    f"objective is shared by {count} skills (max {MAX_OBJECTIVE_REUSE}): "
                    f"{objective[:60]!r}",
                )
            )
    return issues


def _audit_answer_balance(graph: CurriculumGraph) -> list[CurriculumQualityIssue]:
    """Audit answer-position, answer-length and multiple-choice correctness balance.

    Position is checked per answer-count bucket so a dead index inside one bucket (e.g.
    index 2 never correct in 3-answer questions) cannot be masked by pooling buckets.
    """
    issues: list[CurriculumQualityIssue] = []
    # Per-bucket single-choice position counters.
    correct_by_bucket: dict[int, Counter[int]] = {}
    # Per-bucket strictly-longest / strictly-shortest correct counts (two-sided length).
    length_longest_by_bucket: Counter[int] = Counter()
    length_shortest_by_bucket: Counter[int] = Counter()
    # Multiple-choice per-index membership and per-correct-set frequency.
    mc_index_correct: Counter[int] = Counter()
    mc_set_counts: Counter[tuple[int, ...]] = Counter()
    mc_total = 0

    for skill in graph.skills:
        for question in skill.assessments:
            answers = question.answers
            count = len(answers)
            if not count:
                continue
            if question.question_type == "SingleChoice" and len(question.correct) == 1:
                correct_index = question.correct[0]
                correct_by_bucket.setdefault(count, Counter())[correct_index] += 1
                lengths = [len(answer) for answer in answers]
                longest, shortest = max(lengths), min(lengths)
                if lengths[correct_index] == longest and lengths.count(longest) == 1:
                    length_longest_by_bucket[count] += 1
                if lengths[correct_index] == shortest and lengths.count(shortest) == 1:
                    length_shortest_by_bucket[count] += 1
            elif question.question_type == "MultipleChoice":
                mc_total += 1
                for index in question.correct:
                    mc_index_correct[index] += 1
                mc_set_counts[tuple(sorted(question.correct))] += 1

    for bucket, correct_positions in sorted(correct_by_bucket.items()):
        bucket_total = sum(correct_positions.values())
        if bucket_total < _MIN_BUCKET_FOR_POSITION_AUDIT:
            continue
        for index in range(bucket):
            share = correct_positions.get(index, 0) / bucket_total
            if share > MAX_BALANCED_CORRECT_ANSWER_INDEX_SHARE:
                issues.append(
                    CurriculumQualityIssue(
                        "answer_position_bias",
                        f"assessments[{bucket}-answer]",
                        f"answer index {index} is correct {share:.1%} of the time",
                    )
                )
            if share < MIN_BALANCED_CORRECT_ANSWER_INDEX_SHARE:
                issues.append(
                    CurriculumQualityIssue(
                        "answer_position_underuse",
                        f"assessments[{bucket}-answer]",
                        f"answer index {index} is correct only {share:.1%} of the time",
                    )
                )

    for bucket, correct_positions in sorted(correct_by_bucket.items()):
        bucket_total = sum(correct_positions.values())
        if bucket_total < _MIN_BUCKET_FOR_POSITION_AUDIT:
            continue
        for label, counts in (
            ("longest", length_longest_by_bucket),
            ("shortest", length_shortest_by_bucket),
        ):
            share = counts.get(bucket, 0) / bucket_total
            if share > MAX_LENGTH_RANK_SHARE or share < MIN_LENGTH_RANK_SHARE:
                issues.append(
                    CurriculumQualityIssue(
                        "answer_length_bias",
                        f"assessments[{bucket}-answer]",
                        f"correct answer is the strictly {label} option {share:.1%} "
                        f"of the time (chance {1 / bucket:.0%}; test-wiseness cue)",
                    )
                )

    if mc_total:
        for index, count in sorted(mc_index_correct.items()):
            share = count / mc_total
            if share > MAX_MC_INDEX_CORRECT_SHARE:
                issues.append(
                    CurriculumQualityIssue(
                        "mc_answer_position_bias",
                        "assessments",
                        f"multiple-choice index {index} is in the correct set "
                        f"{share:.1%} of the time",
                    )
                )
        for correct_set, count in sorted(mc_set_counts.items()):
            share = count / mc_total
            if share > MAX_MC_CORRECT_SET_SHARE:
                issues.append(
                    CurriculumQualityIssue(
                        "mc_answer_set_bias",
                        "assessments",
                        f"multiple-choice correct set {correct_set} covers {share:.1%} "
                        "of questions (a constant answer rule would exploit it)",
                    )
                )

    return issues


def validate_curriculum_quality(graph: CurriculumGraph) -> None:
    """Raise if the curriculum can pass structurally while failing learner quality."""
    issues = audit_curriculum_quality(graph)
    if issues:
        raise CurriculumError(
            "curriculum quality validation failed:\n  "
            + "\n  ".join(str(issue) for issue in issues)
        )
