"""Live SkillTree dependency parity helpers."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from src.artifacts.json_io import (
    JsonArtifactError,
    read_json_object,
    write_json_artifact,
)
from src.skilltree.client import SkillTreeClientError
from src.skilltree.model import SkillDependency

DependencyPair = tuple[str, str]


class DependencyReconciliationError(RuntimeError):
    """Raised when live SkillTree dependency reconciliation cannot complete."""


class DependencyReconciliationClient(Protocol):
    """Minimal live client contract used by the dependency reconciler."""

    def live_dependency_pairs(self) -> set[DependencyPair]: ...

    def assign_dependency(self, dep: SkillDependency) -> Any: ...


@dataclass(frozen=True)
class ExportedDependencies:
    """Dependency edge list loaded from a SkillTree project export."""

    project_id: str
    dependencies: list[SkillDependency]


@dataclass
class DependencyReconciliationSummary:
    """Machine-readable dependency reconciliation proof."""

    expected_dependencies: int
    live_dependencies_before: int
    missing_before: int
    attempted: int = 0
    already_live: int = 0
    created: int = 0
    confirmed_after_timeout: int = 0
    retried: int = 0
    live_dependencies_after: int = 0
    matched_dependencies_after: int = 0
    missing_after: int = 0
    extra_after: int = 0
    elapsed_seconds: float = 0.0
    stopped_reason: str | None = None
    completed_pairs: list[dict[str, str]] = field(default_factory=list)
    missing_dependency_examples: list[dict[str, str]] = field(default_factory=list)
    extra_dependency_examples: list[dict[str, str]] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        """Return whether the live graph exactly covers the exported dependency set."""
        return self.missing_after == 0 and self.extra_after == 0

    def to_dict(self) -> dict[str, Any]:
        """Return the stable public summary shape."""
        return {
            "expectedDependencies": self.expected_dependencies,
            "liveDependenciesBefore": self.live_dependencies_before,
            "missingBefore": self.missing_before,
            "attempted": self.attempted,
            "alreadyLive": self.already_live,
            "created": self.created,
            "confirmedAfterTimeout": self.confirmed_after_timeout,
            "retried": self.retried,
            "liveDependenciesAfter": self.live_dependencies_after,
            "matchedDependenciesAfter": self.matched_dependencies_after,
            "missingAfter": self.missing_after,
            "extraAfter": self.extra_after,
            "elapsedSeconds": self.elapsed_seconds,
            "stoppedReason": self.stopped_reason,
            "complete": self.complete,
            "completedPairs": self.completed_pairs,
            "missingDependencyExamples": self.missing_dependency_examples,
            "extraDependencyExamples": self.extra_dependency_examples,
            "updatedAt": _utc_now(),
        }


ProgressCallback = Callable[[DependencyReconciliationSummary], None]
HeartbeatCallback = Callable[[dict[str, Any]], None]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def dependency_pair_from_mapping(
    row: Any, *, strict: bool = True
) -> DependencyPair | None:
    """Return a dependency pair from an exported JSON row."""
    if not isinstance(row, dict):
        if strict:
            raise DependencyReconciliationError("dependency row is not an object")
        return None
    skill_id = str(row.get("skillId", "")).strip()
    depends_on = str(row.get("dependsOnSkillId", "")).strip()
    if not skill_id or not depends_on:
        if strict:
            raise DependencyReconciliationError(
                "dependency row requires skillId and dependsOnSkillId"
            )
        return None
    return (skill_id, depends_on)


def dependency_pairs_from_payload(
    rows: Iterable[Any], *, strict: bool = True
) -> set[DependencyPair]:
    """Return unique ``(skillId, dependsOnSkillId)`` pairs from export rows."""
    pairs: set[DependencyPair] = set()
    for row in rows:
        pair = dependency_pair_from_mapping(row, strict=strict)
        if pair is not None:
            pairs.add(pair)
    return pairs


def dependency_pairs_in_order(rows: Iterable[Any]) -> list[DependencyPair]:
    """Return unique dependency pairs preserving export order."""
    seen: set[DependencyPair] = set()
    ordered: list[DependencyPair] = []
    for row in rows:
        pair = dependency_pair_from_mapping(row, strict=True)
        if pair is None:  # pragma: no cover - strict=True raises before this branch
            continue
        if pair in seen:
            continue
        seen.add(pair)
        ordered.append(pair)
    return ordered


def dependency_dict(pair: DependencyPair) -> dict[str, str]:
    """Return the stable JSON representation for one dependency pair."""
    return {"skillId": pair[0], "dependsOnSkillId": pair[1]}


def load_exported_dependencies(path: Path) -> ExportedDependencies:
    """Load dependency edges from a SkillTree project JSON export."""
    try:
        payload = read_json_object(path)
    except FileNotFoundError as exc:
        raise DependencyReconciliationError(
            f"project export is missing: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise DependencyReconciliationError(
            f"project export is not valid JSON: {path}"
        ) from exc
    except JsonArtifactError as exc:
        raise DependencyReconciliationError(
            "project export must be a JSON object"
        ) from exc
    project_id = str(payload.get("projectId", "")).strip()
    if not project_id:
        raise DependencyReconciliationError("project export is missing projectId")
    rows = payload.get("dependencies", [])
    if not isinstance(rows, list):
        raise DependencyReconciliationError(
            "project export dependencies must be a list"
        )
    dependencies = [
        SkillDependency(skill_id=pair[0], depends_on_skill_id=pair[1])
        for pair in dependency_pairs_in_order(rows)
    ]
    return ExportedDependencies(project_id=project_id, dependencies=dependencies)


def load_reconciliation_progress(path: Path) -> dict[str, Any]:
    """Load a previous progress file, returning an empty object if absent."""
    if not path.exists():
        return {}
    try:
        return read_json_object(path)
    except json.JSONDecodeError as exc:
        raise DependencyReconciliationError(
            f"dependency progress file is not valid JSON: {path}"
        ) from exc
    except JsonArtifactError as exc:
        raise DependencyReconciliationError(
            f"dependency progress file must be a JSON object: {path}"
        ) from exc


def write_reconciliation_progress(
    path: Path,
    *,
    project_id: str,
    summary: DependencyReconciliationSummary,
) -> None:
    """Write deterministic progress for an interrupted dependency reconciliation."""
    payload = {"projectId": project_id, **summary.to_dict()}
    write_json_artifact(path, payload)


def summarize_dependency_parity(
    *,
    expected_pairs: set[DependencyPair],
    live_pairs: set[DependencyPair],
    limit: int = 8,
) -> dict[str, Any]:
    """Return a compact parity summary for validators and dashboards."""
    missing = sorted(expected_pairs - live_pairs)
    extra = sorted(live_pairs - expected_pairs)
    matched = expected_pairs & live_pairs
    return {
        "checked": True,
        "expectedDependencies": len(expected_pairs),
        "liveDependencies": len(live_pairs),
        "matchedDependencies": len(matched),
        "missingDependencies": len(missing),
        "extraDependencies": len(extra),
        "complete": not missing and not extra,
        "missingDependencyExamples": [
            dependency_dict(pair) for pair in missing[:limit]
        ],
        "extraDependencyExamples": [dependency_dict(pair) for pair in extra[:limit]],
    }


def _expected_dependency_order(
    dependencies: list[SkillDependency],
) -> list[DependencyPair]:
    return list(
        dict.fromkeys((dep.skill_id, dep.depends_on_skill_id) for dep in dependencies)
    )


def _fresh_live_pairs(client: DependencyReconciliationClient) -> set[DependencyPair]:
    if hasattr(client, "_dependency_pairs"):
        client._dependency_pairs = None
    return client.live_dependency_pairs()


def _confirmation_candidate(exc: SkillTreeClientError) -> bool:
    text = str(exc).lower()
    return exc.status is None and (
        "timed out" in text or "transport error" in text or "connection reset" in text
    )


def _wait_for_pair(
    client: DependencyReconciliationClient,
    pair: DependencyPair,
    *,
    timeout: float,
    interval: float,
    heartbeat_callback: Callable[[float], None] | None = None,
) -> bool:
    started_at = time.monotonic()
    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        if heartbeat_callback is not None:
            heartbeat_callback(time.monotonic() - started_at)
        if pair in _fresh_live_pairs(client):
            return True
        if timeout <= 0:
            break
        time.sleep(max(interval, 0.01))
    return False


def refresh_reconciliation_progress(
    *,
    client: DependencyReconciliationClient,
    project_id: str,
    dependencies: list[SkillDependency],
    progress_path: Path | None = None,
    progress_callback: ProgressCallback | None = None,
) -> DependencyReconciliationSummary:
    """Refresh the progress file from the authoritative live SkillTree graph."""
    expected_order = _expected_dependency_order(dependencies)
    expected_pairs = set(expected_order)
    live_pairs = _fresh_live_pairs(client)
    parity = summarize_dependency_parity(
        expected_pairs=expected_pairs,
        live_pairs=live_pairs,
    )
    summary = DependencyReconciliationSummary(
        expected_dependencies=len(expected_pairs),
        live_dependencies_before=len(live_pairs),
        missing_before=len(expected_pairs - live_pairs),
        already_live=len(expected_pairs & live_pairs),
        live_dependencies_after=parity["liveDependencies"],
        matched_dependencies_after=parity["matchedDependencies"],
        missing_after=parity["missingDependencies"],
        extra_after=parity["extraDependencies"],
        missing_dependency_examples=parity["missingDependencyExamples"],
        extra_dependency_examples=parity["extraDependencyExamples"],
    )
    if progress_path is not None:
        write_reconciliation_progress(
            progress_path,
            project_id=project_id,
            summary=summary,
        )
    if progress_callback is not None:
        progress_callback(summary)
    return summary


def reconcile_live_dependencies(
    *,
    client: DependencyReconciliationClient,
    project_id: str,
    dependencies: list[SkillDependency],
    progress_path: Path | None = None,
    max_edges: int | None = None,
    max_runtime_seconds: float | None = None,
    poll_after_timeout: float = 120.0,
    poll_interval: float = 5.0,
    attempts_per_edge: int = 2,
    progress_callback: ProgressCallback | None = None,
    heartbeat_callback: HeartbeatCallback | None = None,
) -> DependencyReconciliationSummary:
    """Create only missing live dependency edges and return a parity proof.

    ``attempts_per_edge`` bounds how many times one edge may be posted before the
    run fails. At 600-skill scale on emulated Docker a single prerequisite write
    can exceed the client timeout without landing, while the immediately
    following attempt succeeds; aborting a 1199-edge reconciliation on the first
    such write throws away all remaining progress. Set it to 1 to restore
    fail-on-first-error behavior.
    """
    if progress_path is not None:
        load_reconciliation_progress(progress_path)
    if max_edges is not None and max_edges < 0:
        raise DependencyReconciliationError("max_edges must be non-negative")
    if max_runtime_seconds is not None and max_runtime_seconds < 0:
        raise DependencyReconciliationError("max_runtime_seconds must be non-negative")
    if attempts_per_edge < 1:
        raise DependencyReconciliationError("attempts_per_edge must be at least 1")

    started_at = time.monotonic()
    expected_order = _expected_dependency_order(dependencies)
    expected_pairs = set(expected_order)
    live_before = _fresh_live_pairs(client)
    all_missing_order = [pair for pair in expected_order if pair not in live_before]
    missing_order = all_missing_order
    if max_edges is not None:
        missing_order = missing_order[:max_edges]

    summary = DependencyReconciliationSummary(
        expected_dependencies=len(expected_pairs),
        live_dependencies_before=len(live_before),
        missing_before=len(expected_pairs - live_before),
        already_live=len(expected_pairs & live_before),
    )

    def update_elapsed() -> None:
        summary.elapsed_seconds = round(time.monotonic() - started_at, 3)

    def emit_heartbeat(phase: str, pair: DependencyPair) -> None:
        update_elapsed()
        if heartbeat_callback is not None:
            heartbeat_callback(
                {
                    "phase": phase,
                    "skillId": pair[0],
                    "dependsOnSkillId": pair[1],
                    "elapsedSeconds": summary.elapsed_seconds,
                    "matchedDependencies": summary.matched_dependencies_after,
                    "missingDependencies": summary.missing_after,
                    "attempted": summary.attempted,
                }
            )

    def _poll_heartbeat(poll_pair: DependencyPair) -> Callable[[float], None]:
        """Return a heartbeat callback for a poll-after-timeout wait on ``poll_pair``."""

        def _heartbeat(_elapsed: float) -> None:
            emit_heartbeat("pollAfterTimeout", poll_pair)

        return _heartbeat

    def update_progress(live_pairs: set[DependencyPair]) -> None:
        update_elapsed()
        parity = summarize_dependency_parity(
            expected_pairs=expected_pairs,
            live_pairs=live_pairs,
        )
        summary.live_dependencies_after = parity["liveDependencies"]
        summary.matched_dependencies_after = parity["matchedDependencies"]
        summary.missing_after = parity["missingDependencies"]
        summary.extra_after = parity["extraDependencies"]
        summary.missing_dependency_examples = parity["missingDependencyExamples"]
        summary.extra_dependency_examples = parity["extraDependencyExamples"]
        if progress_path is not None:
            write_reconciliation_progress(
                progress_path,
                project_id=project_id,
                summary=summary,
            )
        if progress_callback is not None:
            progress_callback(summary)

    live_current = live_before
    update_progress(live_current)
    for pair in missing_order:
        if (
            max_runtime_seconds is not None
            and time.monotonic() - started_at >= max_runtime_seconds
        ):
            summary.stopped_reason = "maxRuntimeSeconds"
            update_progress(_fresh_live_pairs(client))
            return summary
        dep = SkillDependency(skill_id=pair[0], depends_on_skill_id=pair[1])
        if pair in live_current:
            continue
        for attempt in range(1, attempts_per_edge + 1):
            summary.attempted += 1
            emit_heartbeat("post", pair)
            try:
                result = client.assign_dependency(dep)
            except SkillTreeClientError as exc:
                if _confirmation_candidate(exc) and _wait_for_pair(
                    client,
                    pair,
                    timeout=poll_after_timeout,
                    interval=poll_interval,
                    heartbeat_callback=_poll_heartbeat(pair),
                ):
                    summary.confirmed_after_timeout += 1
                    summary.completed_pairs.append(dependency_dict(pair))
                    live_current = _fresh_live_pairs(client)
                    update_progress(live_current)
                    break
                live_after_error = _fresh_live_pairs(client)
                update_progress(live_after_error)
                if pair in live_after_error:
                    # The live SkillTree graph is the authority, not the HTTP
                    # result. A slow write can land after the client gave up and
                    # after the bounded confirmation poll expired; observing the
                    # edge live means it exists, so treat it as confirmed rather
                    # than failing the run.
                    summary.confirmed_after_timeout += 1
                    summary.completed_pairs.append(dependency_dict(pair))
                    live_current = live_after_error
                    break
                if attempt < attempts_per_edge:
                    summary.retried += 1
                    emit_heartbeat("retry", pair)
                    # Carry the read we just took into the next attempt; a stale
                    # snapshot would re-post an edge that landed meanwhile.
                    live_current = live_after_error
                    continue
                raise DependencyReconciliationError(
                    "failed to assign live SkillTree dependency "
                    f"{pair[0]!r} -> {pair[1]!r} after {attempt} attempt(s): {exc}"
                ) from exc
            except KeyboardInterrupt:
                summary.stopped_reason = "interrupted"
                update_progress(_fresh_live_pairs(client))
                return summary
            if isinstance(result, dict) and result.get("confirmedAfterError"):
                summary.confirmed_after_timeout += 1
            elif not (isinstance(result, dict) and result.get("alreadyExisted")):
                summary.created += 1
            summary.completed_pairs.append(dependency_dict(pair))
            live_current = _fresh_live_pairs(client)
            update_progress(live_current)
            break

    if max_edges is not None and len(all_missing_order) > len(missing_order):
        summary.stopped_reason = "maxEdges"
    update_progress(_fresh_live_pairs(client))
    return summary
