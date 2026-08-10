"""Per-question-type assessment normalization strategies for catalog hardening."""

from __future__ import annotations

import zlib
from itertools import combinations

from src.curriculum.authoring import _q
from src.curriculum.model import AssessmentQuestion, Skill

_RUBRIC_LENSES = (
    "beyond the worked example",
    "in an unfamiliar problem",
    "under a new set of assumptions",
    "across a strand boundary",
)

_LENGTH_FILLERS: tuple[str, ...] = (
    " — weigh this against the prerequisites the skill states.",
    ", relative to where this skill sits in the learning path.",
    ", in light of the skill's own worked example.",
    ", as the strand's boundary conditions are applied.",
    ", considering how this skill is reused downstream.",
)


def _rubric_lens(skill: Skill) -> str:
    index = zlib.crc32(skill.skill_id.encode()) % len(_RUBRIC_LENSES)
    return _RUBRIC_LENSES[index]


def diagnostic_question(skill: Skill) -> AssessmentQuestion:
    objective = skill.objective.strip().rstrip(".")
    name = skill.name
    strand = skill.stratum.value.replace("_", " ")
    return _q(
        f"Which statement best captures why {name} belongs in the {strand} path?",
        [
            f"{objective}.",
            (
                f"{name} is an optional {strand} aside a learner can skip without affecting "
                "any later concept the prerequisite graph depends on."
            ),
            (
                f"{name} only restates an earlier {strand} skill and adds no new reasoning "
                "a learner needs before the strata that follow it."
            ),
        ],
        0,
        origin="rubric",
    )


def transfer_question(skill: Skill) -> AssessmentQuestion:
    name = skill.name
    strand = skill.stratum.value.replace("_", " ")
    scope = _rubric_lens(skill)
    return AssessmentQuestion(
        prompt=f"Which uses of {name} show sound transfer {scope}?",
        answers=(
            (
                f"Applying {name} {scope} while preserving the {strand} prerequisite "
                "meaning the concept actually depends on."
            ),
            (
                f"Restating {name} as a {strand} slogan and applying it {scope} without "
                "checking whether its assumptions still hold."
            ),
            (
                f"Naming the {strand} boundary condition a learner should inspect before "
                f"reusing {name} {scope}."
            ),
            (
                f"Treating {name} as isolated from the {strand} path {scope} and ignoring "
                "the prerequisite concepts that license it."
            ),
        ),
        correct=(0, 2),
        question_type="MultipleChoice",
        origin="rubric",
    )


def misuse_question(skill: Skill) -> AssessmentQuestion:
    name = skill.name
    strand = skill.stratum.value.replace("_", " ")
    scope = _rubric_lens(skill)
    return _q(
        f"Which use of {name} {scope} would overstate what this skill establishes?",
        [
            (
                f"Treating {name} as proof of learner competence or {strand} domain truth "
                f"{scope} without supplying the evidence those claims require."
            ),
            (
                f"Using the documented {strand} prerequisites of {name} to decide which "
                f"later {strand} concept a learner is ready to study {scope}."
            ),
            (
                f"Checking the linked {strand} quiz and exported SkillTree route for {name} "
                f"before it is described as ready for delivery {scope}."
            ),
            (
                f"Naming an explicit {strand} limitation for {name} when its worked example "
                f"is reused {scope}."
            ),
        ],
        0,
        origin="rubric",
    )


def move_correct_answer(
    question: AssessmentQuestion, target_index: int
) -> AssessmentQuestion:
    if question.question_type != "SingleChoice" or len(question.correct) != 1:
        return question
    correct_index = question.correct[0]
    if not question.answers:
        return question
    target_index %= len(question.answers)
    correct_answer = question.answers[correct_index]
    distractors = [
        answer for idx, answer in enumerate(question.answers) if idx != correct_index
    ]
    new_answers = list(distractors)
    new_answers.insert(target_index, correct_answer)
    return AssessmentQuestion(
        prompt=question.prompt,
        answers=tuple(new_answers),
        correct=(target_index,),
        question_type=question.question_type,
        origin=question.origin,
    )


def balance_answer_lengths(
    question: AssessmentQuestion, target_rank: int, variation: int
) -> AssessmentQuestion:
    if question.question_type != "SingleChoice" or len(question.correct) != 1:
        return question
    answers = list(question.answers)
    count = len(answers)
    if count < 2:
        return question
    correct_index = question.correct[0]
    target_rank %= count
    seed = variation
    for i in range(count):
        answers[i] = (
            answers[i].rstrip(".") + _LENGTH_FILLERS[seed % len(_LENGTH_FILLERS)]
        )
        seed += 1
    distractors = sorted(
        (i for i in range(count) if i != correct_index), key=lambda i: len(answers[i])
    )
    below = distractors[: count - 1 - target_rank]
    above = distractors[count - 1 - target_rank :]
    for i in below:
        guard = 0
        while len(answers[correct_index]) <= len(answers[i]) and guard < 8:
            clause = _LENGTH_FILLERS[seed % len(_LENGTH_FILLERS)]
            answers[correct_index] = answers[correct_index].rstrip(".") + clause
            seed += 1
            guard += 1
    for i in above:
        guard = 0
        while len(answers[i]) <= len(answers[correct_index]) and guard < 8:
            clause = _LENGTH_FILLERS[seed % len(_LENGTH_FILLERS)]
            answers[i] = answers[i].rstrip(".") + clause
            seed += 1
            guard += 1
    return AssessmentQuestion(
        prompt=question.prompt,
        answers=tuple(answers),
        correct=question.correct,
        question_type=question.question_type,
        origin=question.origin,
    )


def assign_mc_correct_set(
    question: AssessmentQuestion, target: tuple[int, ...]
) -> AssessmentQuestion:
    count = len(question.answers)
    if len(target) != len(question.correct):
        return question
    correct_items = [
        answer
        for index, answer in enumerate(question.answers)
        if index in question.correct
    ]
    distractor_items = [
        answer
        for index, answer in enumerate(question.answers)
        if index not in question.correct
    ]
    new_answers: list[str | None] = [None] * count
    correct_iter = iter(correct_items)
    for position in target:
        new_answers[position] = next(correct_iter)
    distractor_iter = iter(distractor_items)
    for index in range(count):
        if new_answers[index] is None:
            new_answers[index] = next(distractor_iter)
    return AssessmentQuestion(
        prompt=question.prompt,
        answers=tuple(answer for answer in new_answers if answer is not None),
        correct=tuple(sorted(target)),
        question_type=question.question_type,
        origin=question.origin,
    )


def rebalance_assessments(
    assessments: list[AssessmentQuestion],
    *,
    single_choice_index: dict[int, int],
    multi_choice_index: dict[tuple[int, int], int],
    length_rank_index: dict[int, int],
) -> list[AssessmentQuestion]:
    """Apply single- and multiple-choice balancing passes to one skill's assessments."""
    rebalanced: list[AssessmentQuestion] = []
    for question in assessments:
        count = len(question.answers)
        if (
            question.question_type == "SingleChoice"
            and len(question.correct) == 1
            and count
        ):
            rank = length_rank_index.get(count, 0)
            length_rank_index[count] = rank + 1
            question = balance_answer_lengths(question, rank, rank)
            target = single_choice_index.get(count, 0)
            single_choice_index[count] = target + 1
            rebalanced.append(move_correct_answer(question, target))
        elif question.question_type == "MultipleChoice" and count:
            key = (count, len(question.correct))
            seq = multi_choice_index.get(key, 0)
            multi_choice_index[key] = seq + 1
            subsets = list(combinations(range(count), len(question.correct)))
            target_set = subsets[seq % len(subsets)]
            rebalanced.append(assign_mc_correct_set(question, target_set))
        else:
            rebalanced.append(question)
    return rebalanced
