"""Prerequisite-graph engine over the curriculum model.

A :class:`CurriculumGraph` wraps the list of :class:`~src.curriculum.model.Subject`
objects and enforces the structural invariants the platform depends on: unique skill
ids, no dangling prerequisites, **no cycles** (it is a DAG), and connectivity from the
foundational roots to the applications canopy. It also provides the topological order
used to seed SkillTree (prerequisites before dependents) and per-skill depth levels.

The public surface (``subjects``, ``skills``, ``prerequisite_edges()``) is exactly the
``CurriculumGraphLike`` protocol the SkillTree exporter binds to.
"""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heapify, heappop, heappush

from .model import ALL_STRATA, CurriculumError, Skill, Stratum, Subject

# Skill-id prefixes of the review / mastery / meta extension families that chain skills
# in sequence (per-stratum ladders) rather than by genuine conceptual prerequisite. The
# substantive conceptual core is everything NOT in this set — including the dynamical,
# geometric, hierarchical, implementation and cognitive-security concept families, which
# an earlier allowlist wrongly excluded and so understated the conceptual depth.
_SCAFFOLD_SKILL_PREFIXES = frozenset(
    {
        "mastery",
        "os",
        "next",
        "sci",
        "viz",
        "pub",
        "audit",
        "practice",
        "front",
        "natsec",
    }
)


@dataclass
class CurriculumGraph:
    """A validated prerequisite DAG of skills grouped into subjects."""

    subjects: list[Subject]

    @property
    def skills(self) -> list[Skill]:
        """All skills across all subjects, subject order preserved."""
        return [skill for subject in self.subjects for skill in subject.skills]

    def skill_ids(self) -> set[str]:
        return {s.skill_id for s in self.skills}

    def get_skill(self, skill_id: str) -> Skill:
        for skill in self.skills:
            if skill.skill_id == skill_id:
                return skill
        raise CurriculumError(f"no skill with id {skill_id!r}")

    def prerequisite_edges(self) -> list[tuple[str, str]]:
        """Return ``(prerequisite_id, dependent_id)`` for every prerequisite link."""
        edges: list[tuple[str, str]] = []
        for skill in self.skills:
            for prereq in skill.prerequisites:
                edges.append((prereq, skill.skill_id))
        return edges

    def strata_present(self) -> set[Stratum]:
        return {subject.stratum for subject in self.subjects}

    # -- validation ---------------------------------------------------------

    def validate(self) -> None:
        """Raise :class:`CurriculumError` on any structural violation."""
        self._check_unique_ids()
        self._check_unique_names()
        self._check_subject_identity()
        self._check_no_duplicate_prerequisites()
        self._check_prerequisites_exist()
        self._check_no_self_loops()
        self._check_foundational_roots()
        self._check_acyclic()
        self._check_all_skills_reachable_from_foundations()

    def _check_no_duplicate_prerequisites(self) -> None:
        for skill in self.skills:
            if len(set(skill.prerequisites)) != len(skill.prerequisites):
                raise CurriculumError(
                    f"skill {skill.skill_id!r} lists a duplicate prerequisite"
                )

    def _check_unique_ids(self) -> None:
        seen: set[str] = set()
        for skill in self.skills:
            if skill.skill_id in seen:
                raise CurriculumError(f"duplicate skill_id {skill.skill_id!r}")
            seen.add(skill.skill_id)

    def _check_unique_names(self) -> None:
        """Skill display names must be unique project-wide.

        SkillTree enforces unique skill names within a project: creating a second
        skill with an existing name returns a 400 the idempotent local re-seed
        swallows as a phantom "already exists", so the skill is silently never
        created and any prerequisite edge referencing its id later fails with
        "skillId not found". Enforcing uniqueness here turns that latent live-seed
        corruption into a loud build-time failure.
        """
        seen: dict[str, str] = {}
        for skill in self.skills:
            if skill.name in seen:
                raise CurriculumError(
                    f"duplicate skill name {skill.name!r} on skills "
                    f"{seen[skill.name]!r} and {skill.skill_id!r} — SkillTree "
                    "requires project-wide unique skill names"
                )
            seen[skill.name] = skill.skill_id

    def _check_subject_identity(self) -> None:
        """Subjects must have unique ids and unique names, disjoint from skill ids.

        Closes the rest of the silent-swallow class that the skill-name collision
        exposed (a duplicate-named *subject* would be swallowed by the idempotent
        re-seed exactly as the duplicate-named skill was). SkillTree also resolves
        skills and subjects (SkillsGroups) in one project-wide id namespace — the
        live "types [[Skill, SkillsGroup, Badge]]" lookup — so a skill id colliding
        with a subject id is a latent corruption too.
        """
        seen_ids: dict[str, str] = {}
        seen_names: dict[str, str] = {}
        for subject in self.subjects:
            if subject.subject_id in seen_ids:
                raise CurriculumError(f"duplicate subject_id {subject.subject_id!r}")
            seen_ids[subject.subject_id] = subject.subject_id
            if subject.name in seen_names:
                raise CurriculumError(
                    f"duplicate subject name {subject.name!r} on subjects "
                    f"{seen_names[subject.name]!r} and {subject.subject_id!r} — "
                    "SkillTree requires project-wide unique subject names"
                )
            seen_names[subject.name] = subject.subject_id
        skill_ids = self.skill_ids()
        clashing = skill_ids & set(seen_ids)
        if clashing:
            raise CurriculumError(
                f"skill/subject id namespace collision: {sorted(clashing)!r} — "
                "SkillTree resolves skills and subjects in one id namespace"
            )

    def _check_prerequisites_exist(self, skills: list[Skill] | None = None) -> None:
        skills = self.skills if skills is None else skills
        ids = {skill.skill_id for skill in skills}
        for skill in skills:
            for prereq in skill.prerequisites:
                if prereq not in ids:
                    raise CurriculumError(
                        f"skill {skill.skill_id!r} has dangling prerequisite {prereq!r}"
                    )

    def _check_no_self_loops(self) -> None:
        for skill in self.skills:
            if skill.skill_id in skill.prerequisites:
                raise CurriculumError(
                    f"skill {skill.skill_id!r} lists itself as a prerequisite"
                )

    def _check_foundational_roots(self) -> None:
        """Only foundational strata may contain root (zero-prerequisite) skills."""
        for skill in self.skills:
            if skill.is_root and not skill.stratum.is_foundational:
                raise CurriculumError(
                    f"non-foundational skill {skill.skill_id!r} ({skill.stratum.value}) "
                    "has no prerequisites — only foundational strata may have roots"
                )

    def _check_acyclic(self) -> None:
        """Iterative three-colour DFS cycle detection (stack-safe on deep chains).

        Raises :class:`CurriculumError` with the offending path. Iterative rather than
        recursive so a pathologically deep prerequisite chain cannot blow the Python
        stack with a raw ``RecursionError``.
        """
        adjacency: dict[str, tuple[str, ...]] = {
            s.skill_id: s.prerequisites for s in self.skills
        }
        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(adjacency, WHITE)

        for root, root_prereqs in adjacency.items():
            if colour[root] != WHITE:
                continue
            # Each stack frame: (node, iterator over its prerequisites).
            stack: list[tuple[str, object]] = [(root, iter(root_prereqs))]
            path: list[str] = [root]
            colour[root] = GREY
            while stack:
                node, it = stack[-1]
                nxt = next(it, None)  # type: ignore[call-overload]
                if nxt is None:
                    colour[node] = BLACK
                    stack.pop()
                    path.pop()
                    continue
                if colour[nxt] == GREY:
                    cycle = path[path.index(nxt) :] + [nxt]
                    raise CurriculumError("cycle detected: " + " -> ".join(cycle))
                if colour[nxt] == WHITE:
                    colour[nxt] = GREY
                    path.append(nxt)
                    stack.append((nxt, iter(adjacency[nxt])))

    # -- ordering / depth ---------------------------------------------------

    def topological_order(self) -> list[Skill]:
        """Kahn's algorithm, choosing the smallest currently ready skill id."""
        skills = self.skills
        self._check_prerequisites_exist(skills)
        by_id = {skill.skill_id: skill for skill in skills}
        indegree = {sid: 0 for sid in by_id}
        dependents: dict[str, list[str]] = {sid: [] for sid in by_id}
        for skill in skills:
            for prereq in skill.prerequisites:
                indegree[skill.skill_id] += 1
                dependents[prereq].append(skill.skill_id)
        ready = [sid for sid, degree in indegree.items() if degree == 0]
        heapify(ready)
        order: list[Skill] = []
        while ready:
            sid = heappop(ready)
            order.append(by_id[sid])
            for dep in dependents[sid]:
                indegree[dep] -= 1
                if indegree[dep] == 0:
                    heappush(ready, dep)
        if len(order) != len(by_id):
            raise CurriculumError("topological_order failed — graph is cyclic")
        return order

    def levels(self) -> dict[str, int]:
        """Depth of each skill = longest prerequisite chain ending at it (roots = 0)."""
        level: dict[str, int] = {}
        for skill in self.topological_order():
            if skill.is_root:
                level[skill.skill_id] = 0
            else:
                level[skill.skill_id] = 1 + max(level[p] for p in skill.prerequisites)
        return level

    def core_max_depth(self) -> int:
        """Longest prerequisite chain over the substantive conceptual core only.

        The headline ``max_depth`` is dominated by the per-stratum mastery and
        open-science *review* ladders, which chain skills in sequence rather than by true
        conceptual prerequisite. This excludes only those review/meta scaffold families
        (see ``_SCAFFOLD_SKILL_PREFIXES``) and keeps every genuine concept family —
        mathematics, probability, information theory, variational methods, the FEP, active
        inference, computation, applications, plus the dynamical, geometric, hierarchical,
        implementation and cognitive-security families — giving the depth of the actual
        concept chain a learner must climb, separate from review sequencing.
        """
        ordered = self.topological_order()
        core = {
            skill.skill_id
            for skill in ordered
            if skill.skill_id.split("_")[0] not in _SCAFFOLD_SKILL_PREFIXES
        }
        if not core:
            return 0
        level: dict[str, int] = {}
        for skill in ordered:
            if skill.skill_id not in core:
                continue
            core_prereqs = [p for p in skill.prerequisites if p in core]
            level[skill.skill_id] = (
                0 if not core_prereqs else 1 + max(level[p] for p in core_prereqs)
            )
        return max(level.values()) if level else 0

    def reachable_from_foundations(self) -> set[str]:
        """Skill ids reachable by following prerequisite edges up from foundational roots.

        The BFS seeds *only* from roots in a foundational stratum (math/probability),
        not from every zero-prerequisite skill. A valid curriculum has all roots in
        foundational strata (``validate`` enforces this), so the two coincide there; but
        seeding from foundational roots specifically means a curriculum where an
        applications skill traces back only to a *non-foundational* orphan root is
        correctly reported as disconnected, rather than being trivially reachable from
        that illegal root.
        """
        skills = self.skills
        by_id = {skill.skill_id: skill for skill in skills}
        forward: dict[str, list[str]] = {sid: [] for sid in by_id}
        for skill in skills:
            for prereq in skill.prerequisites:
                forward[prereq].append(skill.skill_id)
        roots = [
            skill.skill_id for skill in skills
            if skill.is_root and skill.stratum.is_foundational
        ]
        seen: set[str] = set()
        stack = list(roots)
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(forward[node])
        return seen

    def is_connected_foundations_to_applications(self) -> bool:
        """Every applications skill is reachable from a foundational root."""
        reachable = self.reachable_from_foundations()
        app_ids = {s.skill_id for s in self.skills if s.stratum is Stratum.APPLICATIONS}
        return app_ids.issubset(reachable)

    def skills_without_foundation_path(self) -> tuple[str, ...]:
        """Return skills not reachable from any foundational root."""
        reachable = self.reachable_from_foundations()
        return tuple(
            sorted(
                skill.skill_id
                for skill in self.skills
                if skill.skill_id not in reachable
            )
        )

    def _check_all_skills_reachable_from_foundations(self) -> None:
        missing = self.skills_without_foundation_path()
        if missing:
            raise CurriculumError(
                "skills not reachable from foundational roots: "
                + ", ".join(missing[:12])
                + (" ..." if len(missing) > 12 else "")
            )

    # -- reporting ----------------------------------------------------------

    def stats(self) -> dict[str, object]:
        ordered = self.topological_order()
        levels: dict[str, int] = {}
        core_levels: dict[str, int] = {}
        core_ids = {
            skill.skill_id for skill in ordered
            if skill.skill_id.split("_")[0] not in _SCAFFOLD_SKILL_PREFIXES
        }
        skills_per_stratum = {stratum.value: 0 for stratum in ALL_STRATA}
        for skill in ordered:
            levels[skill.skill_id] = (
                1 + max(levels[prereq] for prereq in skill.prerequisites)
                if skill.prerequisites else 0
            )
            skills_per_stratum[skill.stratum.value] += 1
            if skill.skill_id in core_ids:
                core_prereqs = [prereq for prereq in skill.prerequisites if prereq in core_ids]
                core_levels[skill.skill_id] = (
                    1 + max(core_levels[prereq] for prereq in core_prereqs)
                    if core_prereqs else 0
                )
        strata = {subject.stratum for subject in self.subjects}
        return {
            "subjects": len(self.subjects),
            "skills": len(ordered),
            "prerequisite_edges": sum(len(skill.prerequisites) for skill in ordered),
            "strata_present": sorted(stratum.value for stratum in strata),
            "strata_count": len(strata),
            "all_strata_present": strata == set(ALL_STRATA),
            "max_depth": max(levels.values(), default=0),
            "core_max_depth": max(core_levels.values(), default=0),
            "roots": sum(skill.is_root for skill in ordered),
            "skills_per_stratum": skills_per_stratum,
        }
