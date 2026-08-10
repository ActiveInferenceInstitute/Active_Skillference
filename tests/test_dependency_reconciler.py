"""Tests for live SkillTree dependency reconciliation helpers."""

from __future__ import annotations

import json
from pathlib import Path

from src.skilltree.client import SkillTreeClientError
from src.skilltree.dependency_reconciler import (
    DependencyReconciliationError,
    dependency_pairs_from_payload,
    load_exported_dependencies,
    load_reconciliation_progress,
    reconcile_live_dependencies,
    refresh_reconciliation_progress,
    summarize_dependency_parity,
)
from src.skilltree.model import SkillDependency


class InMemoryDependencyClient:
    def __init__(self, live: set[tuple[str, str]]) -> None:
        self.live = set(live)
        self.assigned: list[tuple[str, str]] = []

    def live_dependency_pairs(self) -> set[tuple[str, str]]:
        return set(self.live)

    def assign_dependency(self, dep: SkillDependency) -> dict[str, object]:
        pair = (dep.skill_id, dep.depends_on_skill_id)
        self.assigned.append(pair)
        self.live.add(pair)
        return {"success": True}


def test_reconciler_assigns_only_missing_edges_and_writes_progress(
    tmp_path: Path,
) -> None:
    client = InMemoryDependencyClient({("mid", "root")})
    progress_path = tmp_path / "dependency_seed_progress.json"

    summary = reconcile_live_dependencies(
        client=client,
        project_id="activeInference",
        dependencies=[
            SkillDependency(skill_id="mid", depends_on_skill_id="root"),
            SkillDependency(skill_id="leaf", depends_on_skill_id="mid"),
        ],
        progress_path=progress_path,
    )

    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert client.assigned == [("leaf", "mid")]
    assert summary.complete is True
    assert summary.missing_before == 1
    assert summary.matched_dependencies_after == 2
    assert progress["projectId"] == "activeInference"
    assert progress["complete"] is True


def test_reconciler_confirms_timeout_edge_after_live_poll() -> None:
    class TimeoutThenLiveClient(InMemoryDependencyClient):
        def __init__(self) -> None:
            super().__init__(set())
            self.reads = 0

        def live_dependency_pairs(self) -> set[tuple[str, str]]:
            self.reads += 1
            if self.reads >= 2:
                return {("leaf", "root")}
            return set()

        def assign_dependency(self, dep: SkillDependency) -> dict[str, object]:
            self.assigned.append((dep.skill_id, dep.depends_on_skill_id))
            raise SkillTreeClientError("POST dependency timed out after 30s")

    summary = reconcile_live_dependencies(
        client=TimeoutThenLiveClient(),
        project_id="activeInference",
        dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
        poll_after_timeout=0.1,
        poll_interval=0.01,
    )

    assert summary.confirmed_after_timeout == 1
    assert summary.complete is True


def test_reconciler_refreshes_stale_progress_from_live_graph(
    tmp_path: Path,
) -> None:
    client = InMemoryDependencyClient({("leaf", "root")})
    progress_path = tmp_path / "dependency_seed_progress.json"
    progress_path.write_text(
        json.dumps(
            {
                "projectId": "activeInference",
                "expectedDependencies": 1,
                "liveDependenciesAfter": 0,
                "matchedDependenciesAfter": 0,
                "missingAfter": 1,
                "complete": False,
            }
        ),
        encoding="utf-8",
    )

    summary = refresh_reconciliation_progress(
        client=client,
        project_id="activeInference",
        dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
        progress_path=progress_path,
    )

    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert client.assigned == []
    assert summary.complete is True
    assert progress["liveDependenciesAfter"] == 1
    assert progress["matchedDependenciesAfter"] == 1
    assert progress["missingAfter"] == 0


def test_reconciler_respects_max_edges_as_partial_chunk(
    tmp_path: Path,
) -> None:
    client = InMemoryDependencyClient(set())
    progress_path = tmp_path / "dependency_seed_progress.json"

    summary = reconcile_live_dependencies(
        client=client,
        project_id="activeInference",
        dependencies=[
            SkillDependency(skill_id="mid", depends_on_skill_id="root"),
            SkillDependency(skill_id="leaf", depends_on_skill_id="mid"),
        ],
        progress_path=progress_path,
        max_edges=1,
    )

    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert client.assigned == [("mid", "root")]
    assert summary.complete is False
    assert summary.stopped_reason == "maxEdges"
    assert summary.missing_after == 1
    assert progress["stoppedReason"] == "maxEdges"


def test_reconciler_respects_max_runtime_before_next_edge(
    tmp_path: Path,
) -> None:
    client = InMemoryDependencyClient(set())
    progress_path = tmp_path / "dependency_seed_progress.json"

    summary = reconcile_live_dependencies(
        client=client,
        project_id="activeInference",
        dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
        progress_path=progress_path,
        max_runtime_seconds=0,
    )

    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert client.assigned == []
    assert summary.complete is False
    assert summary.stopped_reason == "maxRuntimeSeconds"
    assert progress["stoppedReason"] == "maxRuntimeSeconds"


def test_reconciler_emits_heartbeat_for_pending_edge() -> None:
    client = InMemoryDependencyClient(set())
    events: list[dict[str, object]] = []

    reconcile_live_dependencies(
        client=client,
        project_id="activeInference",
        dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
        heartbeat_callback=events.append,
    )

    assert events
    assert events[0]["phase"] == "post"
    assert events[0]["skillId"] == "leaf"
    assert events[0]["dependsOnSkillId"] == "root"


def test_reconciler_writes_progress_on_keyboard_interrupt(
    tmp_path: Path,
) -> None:
    class InterruptingClient(InMemoryDependencyClient):
        def assign_dependency(self, dep: SkillDependency) -> dict[str, object]:
            self.assigned.append((dep.skill_id, dep.depends_on_skill_id))
            raise KeyboardInterrupt

    client = InterruptingClient(set())
    progress_path = tmp_path / "dependency_seed_progress.json"

    summary = reconcile_live_dependencies(
        client=client,
        project_id="activeInference",
        dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
        progress_path=progress_path,
    )

    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert client.assigned == [("leaf", "root")]
    assert summary.complete is False
    assert summary.stopped_reason == "interrupted"
    assert progress["stoppedReason"] == "interrupted"


def test_reconciler_rejects_unconfirmed_timeout() -> None:
    class TimeoutClient(InMemoryDependencyClient):
        def assign_dependency(self, dep: SkillDependency) -> dict[str, object]:
            self.assigned.append((dep.skill_id, dep.depends_on_skill_id))
            raise SkillTreeClientError("POST dependency timed out after 30s")

    try:
        reconcile_live_dependencies(
            client=TimeoutClient(set()),
            project_id="activeInference",
            dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
            poll_after_timeout=0,
        )
    except DependencyReconciliationError as exc:
        assert "failed to assign live SkillTree dependency" in str(exc)
    else:
        raise AssertionError("unconfirmed timeout unexpectedly passed")


def test_reconciler_accepts_an_edge_that_lands_after_the_poll_window() -> None:
    """A write that lands after the bounded poll must not fail the run.

    On slow hosts the confirmation poll can expire while the SkillTree write is
    still in flight. The live graph is the declared authority, so the final
    authoritative read decides — observed against the local stack, where an edge
    went live and the run still aborted.
    """

    class SlowWriteClient(InMemoryDependencyClient):
        def __init__(self) -> None:
            super().__init__(set())
            self.reads = 0

        def live_dependency_pairs(self) -> set[tuple[str, str]]:
            self.reads += 1
            # With a zero-length confirmation window the poll reads nothing, so
            # read 1 is the pre-loop snapshot and read 2 is the authoritative
            # read taken after the client gave up.
            if self.reads >= 2:
                return {("leaf", "root")}
            return set()

        def assign_dependency(self, dep: SkillDependency) -> dict[str, object]:
            self.assigned.append((dep.skill_id, dep.depends_on_skill_id))
            raise SkillTreeClientError("POST dependency timed out after 600s")

    client = SlowWriteClient()
    summary = reconcile_live_dependencies(
        client=client,
        project_id="activeInference",
        dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
        poll_after_timeout=0,
    )

    assert summary.confirmed_after_timeout == 1
    assert summary.missing_after == 0
    assert summary.complete is True
    # Pins the path under test: pre-loop snapshot, the post-error authoritative
    # read that confirmed the edge, and the closing refresh — the zero-length
    # poll window never read, so only the post-error read can have confirmed it.
    assert client.reads == 3


def test_reconciler_retries_a_slow_edge_before_failing_the_run() -> None:
    """One stubborn write must not discard the rest of a 1199-edge run."""

    class FlakyWriteClient(InMemoryDependencyClient):
        def __init__(self) -> None:
            super().__init__(set())
            self.attempts = 0

        def assign_dependency(self, dep: SkillDependency) -> dict[str, object]:
            self.attempts += 1
            if self.attempts == 1:
                raise SkillTreeClientError("POST dependency timed out after 600s")
            return super().assign_dependency(dep)

    client = FlakyWriteClient()
    summary = reconcile_live_dependencies(
        client=client,
        project_id="activeInference",
        dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
        poll_after_timeout=0,
    )

    assert client.attempts == 2
    assert summary.retried == 1
    assert summary.created == 1
    assert summary.complete is True


def test_reconciler_single_attempt_mode_fails_on_the_first_error() -> None:
    class AlwaysTimeoutClient(InMemoryDependencyClient):
        def assign_dependency(self, dep: SkillDependency) -> dict[str, object]:
            self.assigned.append((dep.skill_id, dep.depends_on_skill_id))
            raise SkillTreeClientError("POST dependency timed out after 600s")

    try:
        reconcile_live_dependencies(
            client=AlwaysTimeoutClient(set()),
            project_id="activeInference",
            dependencies=[SkillDependency(skill_id="leaf", depends_on_skill_id="root")],
            poll_after_timeout=0,
            attempts_per_edge=1,
        )
    except DependencyReconciliationError as exc:
        assert "after 1 attempt(s)" in str(exc)
    else:
        raise AssertionError("single-attempt mode unexpectedly passed")


def test_reconciler_rejects_zero_attempts_per_edge() -> None:
    try:
        reconcile_live_dependencies(
            client=InMemoryDependencyClient(set()),
            project_id="activeInference",
            dependencies=[],
            attempts_per_edge=0,
        )
    except DependencyReconciliationError as exc:
        assert "attempts_per_edge must be at least 1" in str(exc)
    else:
        raise AssertionError("attempts_per_edge=0 unexpectedly passed")


def test_load_exported_dependencies_deduplicates_in_export_order(
    tmp_path: Path,
) -> None:
    path = tmp_path / "skilltree_project.json"
    path.write_text(
        json.dumps(
            {
                "projectId": "activeInference",
                "dependencies": [
                    {"skillId": "b", "dependsOnSkillId": "a"},
                    {"skillId": "b", "dependsOnSkillId": "a"},
                    {"skillId": "c", "dependsOnSkillId": "b"},
                ],
            }
        ),
        encoding="utf-8",
    )

    exported = load_exported_dependencies(path)

    assert exported.project_id == "activeInference"
    assert [
        (dep.skill_id, dep.depends_on_skill_id) for dep in exported.dependencies
    ] == [("b", "a"), ("c", "b")]


def test_dependency_pairs_from_payload_rejects_malformed_rows() -> None:
    try:
        dependency_pairs_from_payload([{"skillId": "leaf"}])
    except DependencyReconciliationError as exc:
        assert "requires skillId and dependsOnSkillId" in str(exc)
    else:
        raise AssertionError("malformed dependency row unexpectedly passed")


def test_reconciler_rejects_negative_runtime_limits() -> None:
    client = InMemoryDependencyClient(set())
    dependencies = [SkillDependency(skill_id="leaf", depends_on_skill_id="root")]

    try:
        reconcile_live_dependencies(
            client=client,
            project_id="activeInference",
            dependencies=dependencies,
            max_edges=-1,
        )
    except DependencyReconciliationError as exc:
        assert "max_edges must be non-negative" in str(exc)
    else:
        raise AssertionError("negative max_edges unexpectedly passed")

    try:
        reconcile_live_dependencies(
            client=client,
            project_id="activeInference",
            dependencies=dependencies,
            max_runtime_seconds=-0.1,
        )
    except DependencyReconciliationError as exc:
        assert "max_runtime_seconds must be non-negative" in str(exc)
    else:
        raise AssertionError("negative max_runtime_seconds unexpectedly passed")


def test_load_reconciliation_progress_rejects_invalid_files(tmp_path: Path) -> None:
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{not-json", encoding="utf-8")

    try:
        load_reconciliation_progress(invalid_json)
    except DependencyReconciliationError as exc:
        assert "not valid JSON" in str(exc)
    else:
        raise AssertionError("invalid progress JSON unexpectedly passed")

    list_json = tmp_path / "list.json"
    list_json.write_text("[]", encoding="utf-8")

    try:
        load_reconciliation_progress(list_json)
    except DependencyReconciliationError as exc:
        assert "must be a JSON object" in str(exc)
    else:
        raise AssertionError("non-object progress JSON unexpectedly passed")


def test_summarize_dependency_parity_reports_extra_live_edges() -> None:
    summary = summarize_dependency_parity(
        expected_pairs={("leaf", "root")},
        live_pairs={("leaf", "root"), ("extra", "root")},
    )

    assert summary["complete"] is False
    assert summary["missingDependencies"] == 0
    assert summary["extraDependencies"] == 1
    assert summary["extraDependencyExamples"] == [
        {"skillId": "extra", "dependsOnSkillId": "root"}
    ]
