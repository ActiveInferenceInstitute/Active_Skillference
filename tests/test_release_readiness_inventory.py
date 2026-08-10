"""Release-readiness inventory validation tests."""

from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path

import pytest

from src.release_readiness import (
    IGNORED_OUTPUT_EXAMPLES,
    BlockerProbeSummary,
    ReleaseReadinessError,
    ReleaseReadinessSnapshot,
    audit_release_readiness_inventory,
    build_release_readiness_snapshot,
    render_release_readiness_inventory,
    validate_release_readiness_inventory,
    write_release_readiness_inventory,
)


def test_rendered_inventory_validates_real_git_state(tmp_path: Path) -> None:
    root = _repo_with_dirty_release_state(tmp_path)
    _write_inventory(root)

    assert audit_release_readiness_inventory(root) == []


def test_inventory_rejects_missing_untracked_path(tmp_path: Path) -> None:
    root = _repo_with_dirty_release_state(tmp_path)
    _write_inventory(root)
    (root / "new_validator.py").write_text("print('new')\n", encoding="utf-8")

    issues = audit_release_readiness_inventory(root)

    assert any("new_validator.py" in issue.message for issue in issues)


def test_inventory_rejects_stale_tracked_diff_summary(tmp_path: Path) -> None:
    root = _repo_with_dirty_release_state(tmp_path)
    _write_inventory(root)
    text = (root / "docs" / "release_readiness_inventory.md").read_text(
        encoding="utf-8"
    )
    stale = text.replace("1 file changed", "999 files changed")
    (root / "docs" / "release_readiness_inventory.md").write_text(
        stale, encoding="utf-8"
    )

    with pytest.raises(ReleaseReadinessError, match="tracked diff summary is stale"):
        validate_release_readiness_inventory(root)


def test_stale_inventory_error_mentions_refresh_command(tmp_path: Path) -> None:
    root = _repo_with_dirty_release_state(tmp_path)
    _write_inventory(root)
    text = (root / "docs" / "release_readiness_inventory.md").read_text(
        encoding="utf-8"
    )
    (root / "docs" / "release_readiness_inventory.md").write_text(
        text.replace("1 file changed", "999 files changed"), encoding="utf-8"
    )

    with pytest.raises(ReleaseReadinessError) as excinfo:
        validate_release_readiness_inventory(root)

    assert "validate_release_readiness_inventory.py --write" in str(excinfo.value)


def test_inventory_rejects_ignored_output_drift(tmp_path: Path) -> None:
    root = _repo_with_dirty_release_state(tmp_path, ignore_outputs=False)
    _write_inventory(root)

    issues = audit_release_readiness_inventory(root)

    assert any("is no longer ignored by git" in issue.message for issue in issues)


def test_ignored_output_examples_match_current_renderer_names() -> None:
    examples = set(IGNORED_OUTPUT_EXAMPLES)

    assert "output/docx/Active_Skillference_combined.docx" in examples
    assert "output/epub/Active_Skillference_combined.epub" in examples
    assert "output/slides/00_abstract_slides.pdf" in examples
    assert "output/docx/Active_Skillference.docx" not in examples
    assert "output/epub/Active_Skillference.epub" not in examples
    assert "output/slides/Active_Skillference.pptx" not in examples


def test_clean_inventory_text_does_not_claim_pre_commit_dirty_state() -> None:
    text = render_release_readiness_inventory(
        ReleaseReadinessSnapshot(
            status_lines=(),
            modified_tracked_files=(),
            untracked_files=(),
            diff_summary="0 files changed",
            ignored_examples=("output/web/index.html",),
            artifact_hashes=(),
        ),
        blocker_probes=BlockerProbeSummary(
            public_repository="blocked (Repository not found)",
            docker_daemon="reachable",
        ),
        date=dt.date(2026, 6, 19),
    )

    assert "No staging, commit, push" not in text
    assert (
        "`git status --short` currently reports 0 rows outside this inventory file"
        in text
    )
    assert "- None." in text
    assert "Live full-stack rehearsal is unblocked" in text
    assert "Branch hygiene is clean for this checkout" in text
    assert "Cross-vendor security audit evidence is closed" in text
    assert "Cross-vendor security audit remains blocked" not in text


def test_inventory_rejects_stale_artifact_hash(tmp_path: Path) -> None:
    root = _repo_with_dirty_release_state(tmp_path)
    data_dir = root / "output" / "data"
    figure_dir = root / "output" / "figures"
    data_dir.mkdir(parents=True)
    figure_dir.mkdir(parents=True)
    (data_dir / "claims.json").write_text('{"ok": true}\n', encoding="utf-8")
    (figure_dir / "figure_registry.json").write_text(
        '[{"filename": "curriculum_dag.png"}]\n',
        encoding="utf-8",
    )
    (figure_dir / "curriculum_dag.png").write_bytes(b"png-before")
    _write_inventory(root)

    (figure_dir / "curriculum_dag.png").write_bytes(b"png-after")
    issues = audit_release_readiness_inventory(root)

    assert any("Key Artifact Hashes" == issue.location for issue in issues)
    assert any("output/figures/curriculum_dag.png" in issue.message for issue in issues)


def test_write_inventory_reaches_git_diff_fixed_point(tmp_path: Path) -> None:
    root = _repo_with_dirty_release_state(tmp_path)

    write_release_readiness_inventory(
        root,
        blocker_probes=BlockerProbeSummary(
            public_repository="blocked (Repository not found)",
            docker_daemon="reachable",
        ),
    )

    validate_release_readiness_inventory(root)


def test_inventory_ignores_only_its_own_generated_diff(tmp_path: Path) -> None:
    root = _repo_with_dirty_release_state(tmp_path)
    _git(root, "add", ".")
    _git(root, "commit", "-m", "dirty state committed")

    write_release_readiness_inventory(
        root,
        blocker_probes=BlockerProbeSummary(
            public_repository="blocked (Repository not found)",
            docker_daemon="reachable",
        ),
    )

    assert audit_release_readiness_inventory(root) == []
    (root / "tracked.txt").write_text("old\nnew\nagain\n", encoding="utf-8")
    issues = audit_release_readiness_inventory(root)
    assert any("tracked.txt" in issue.message for issue in issues)


def _write_inventory(root: Path) -> None:
    snapshot = build_release_readiness_snapshot(root)
    text = render_release_readiness_inventory(
        snapshot,
        blocker_probes=BlockerProbeSummary(
            public_repository="blocked (Repository not found)",
            docker_daemon="blocked (Cannot connect to the Docker daemon)",
        ),
        date=dt.date(2026, 6, 19),
    )
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "release_readiness_inventory.md").write_text(
        text, encoding="utf-8"
    )


def _repo_with_dirty_release_state(
    tmp_path: Path, *, ignore_outputs: bool = True
) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Release Inventory Test")
    ignore_text = (
        "output/\n.active_skillference_local/\n" if ignore_outputs else "# none\n"
    )
    (root / ".gitignore").write_text(ignore_text, encoding="utf-8")
    (root / "tracked.txt").write_text("old\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "release_readiness_inventory.md").write_text(
        "placeholder\n", encoding="utf-8"
    )
    _git(root, "add", ".gitignore", "tracked.txt")
    _git(root, "commit", "-m", "initial")
    (root / "tracked.txt").write_text("old\nnew\n", encoding="utf-8")
    (root / "untracked_helper.py").write_text("print('helper')\n", encoding="utf-8")
    return root


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


# --- blocker-probe subsystem (real subprocess) -----------------------------


def test_run_command_success_captures_real_output(tmp_path: Path) -> None:
    from src.release_readiness import _run_command

    result = _run_command(["git", "--version"], cwd=tmp_path, timeout=20)
    assert result.returncode == 0
    assert "git version" in result.stdout


def test_run_command_missing_binary_returns_127(tmp_path: Path) -> None:
    from src.release_readiness import _run_command

    result = _run_command(["asf-nonexistent-binary-xyz"], cwd=tmp_path, timeout=20)
    assert result.returncode == 127
    assert result.stderr


def test_run_command_timeout_returns_124(tmp_path: Path) -> None:
    import sys

    from src.release_readiness import _run_command

    result = _run_command(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        cwd=tmp_path,
        timeout=1,
    )
    assert result.returncode == 124


def test_summarize_probe_distinguishes_reachable_and_blocked() -> None:
    from src.release_readiness import _summarize_probe

    reachable = subprocess.CompletedProcess(["x"], 0, "ok\n", "")
    assert _summarize_probe(reachable) == "reachable"

    blocked = subprocess.CompletedProcess(["x"], 2, "", "Repository not found.\n")
    assert _summarize_probe(blocked) == "blocked (Repository not found.)"

    silent = subprocess.CompletedProcess(["x"], 3, "", "")
    assert _summarize_probe(silent) == "blocked (exit 3)"


def test_collect_blocker_probes_returns_string_summary(tmp_path: Path) -> None:
    from src.release_readiness import BlockerProbeSummary, collect_blocker_probes

    summary = collect_blocker_probes(tmp_path)
    assert isinstance(summary, BlockerProbeSummary)
    assert isinstance(summary.public_repository, str) and summary.public_repository
    assert isinstance(summary.docker_daemon, str) and summary.docker_daemon
