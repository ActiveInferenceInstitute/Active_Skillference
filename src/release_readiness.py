"""Release-readiness inventory generation and validation."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PUBLIC_REPOSITORY_URL = (
    "https://github.com/ActiveInferenceInstitute/Active_Skillference.git"
)
INVENTORY_PATH = "docs/release_readiness_inventory.md"
# Surfaces that must stay out of version control. Generated deliverables under
# output/ are now committed on purpose so a reader can inspect them without
# running the pipeline, so what remains here is the two families that must never
# be tracked: renderer detritus that churns on every build, and local runtime
# state that holds credentials.
IGNORED_OUTPUT_EXAMPLES = (
    "output/pdf/_combined_manuscript.aux",
    "output/pdf/_combined_manuscript.log",
    "output/slides/00_abstract_slides.aux",
    "output/slides/00_abstract_slides.log",
    ".active_skillference_local/dashboard.log",
    ".active_skillference_local/skilltree_auth.json",
)
REQUIRED_EVIDENCE_COMMANDS = (
    "git status --short (excluding docs/release_readiness_inventory.md)",
    "git ls-files -o --exclude-standard",
    "git diff --check",
    "git diff --stat -- . ':(exclude)docs/release_readiness_inventory.md'",
    "uv run python scripts/validate_release_readiness_inventory.py",
)
ARTIFACT_HASH_TARGETS = (
    "output/data/claims.json",
    "output/data/manuscript_variables.json",
    "output/data/skilltree_project.json",
    "output/figures/figure_registry.json",
)


@dataclass(frozen=True)
class ReleaseReadinessIssue:
    """One inventory drift finding."""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


class ReleaseReadinessError(ValueError):
    """Raised when the release-readiness inventory is stale."""


@dataclass(frozen=True)
class ReleaseReadinessSnapshot:
    """Git-derived release inventory state."""

    status_lines: tuple[str, ...]
    modified_tracked_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    diff_summary: str
    ignored_examples: tuple[str, ...]
    artifact_hashes: tuple[ArtifactHash, ...]


@dataclass(frozen=True)
class ArtifactHash:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class BlockerProbeSummary:
    """Current external blocker probe text for inventory rendering."""

    public_repository: str
    docker_daemon: str


def build_release_readiness_snapshot(root: Path) -> ReleaseReadinessSnapshot:
    """Collect the local, non-mutating git facts encoded in the release inventory."""
    root = Path(root)
    status_lines = tuple(
        line
        for line in _run_git(root, "status", "--short").splitlines()
        if _status_path(line) != INVENTORY_PATH
    )
    untracked_files = tuple(
        line
        for line in _run_git(root, "ls-files", "-o", "--exclude-standard").splitlines()
        if line.strip() and line.strip() != INVENTORY_PATH
    )
    diff_stat = _run_git(
        root, "diff", "--stat", "--", ".", f":(exclude){INVENTORY_PATH}"
    )
    diff_summary = _diff_summary(diff_stat)
    ignored_examples = _check_ignored_examples(root)
    modified_tracked_files = tuple(
        _status_path(line) for line in status_lines if not line.startswith("?? ")
    )
    return ReleaseReadinessSnapshot(
        status_lines=status_lines,
        modified_tracked_files=modified_tracked_files,
        untracked_files=untracked_files,
        diff_summary=diff_summary,
        ignored_examples=ignored_examples,
        artifact_hashes=_collect_artifact_hashes(root),
    )


def collect_blocker_probes(root: Path) -> BlockerProbeSummary:
    """Probe volatile external blockers for inventory rendering."""
    public = _run_command(
        ["git", "ls-remote", "--heads", PUBLIC_REPOSITORY_URL, "HEAD"],
        cwd=root,
        timeout=20,
    )
    docker = _run_command(["docker", "info"], cwd=root, timeout=20)
    return BlockerProbeSummary(
        public_repository=_summarize_public_repository_probe(public),
        docker_daemon=_summarize_probe(docker),
    )


def _summarize_public_repository_probe(
    result: subprocess.CompletedProcess[str],
) -> str:
    """Report reachability *and* whether the public target has any content.

    ``git ls-remote`` exits 0 for a repository that exists but holds no refs, so
    a bare exit-code check reads an empty placeholder repository as ready. That
    is the difference between "the target exists" and "the release is published",
    and DOI/archive metadata must stay blank across that gap.
    """
    if result.returncode != 0:
        return _summarize_probe(result)
    if result.stdout.strip():
        return "reachable (refs present)"
    return "reachable but empty (no refs; not a published release)"


def render_release_readiness_inventory(
    snapshot: ReleaseReadinessSnapshot,
    *,
    blocker_probes: BlockerProbeSummary | None = None,
    date: _dt.date | None = None,
) -> str:
    """Render the canonical release-readiness inventory Markdown."""
    today = date or _dt.datetime.now(_dt.UTC).date()
    probes = blocker_probes or BlockerProbeSummary(
        public_repository="not refreshed by this validation run",
        docker_daemon="not refreshed by this validation run",
    )
    status_count = len(snapshot.status_lines)
    tracked_count = len(snapshot.modified_tracked_files)
    untracked_count = len(snapshot.untracked_files)
    has_dirty_worktree = bool(snapshot.status_lines)
    live_stack_line = (
        "- Live full-stack rehearsal is unblocked because `docker info` reaches "
        "the Docker/Colima daemon. Current proof status is tracked in tasks.yaml; "
        "rerun the app-ready and full-parity commands below before a public release "
        "handoff."
        if probes.docker_daemon == "reachable"
        else (
            "- Live full-stack rehearsal remains blocked until `docker info` reaches "
            "the Docker/Colima daemon. Current probe: "
            f"{probes.docker_daemon}."
        )
    )
    branch_hygiene_line = (
        "- Branch hygiene is clean for this checkout: `git status --short` reports "
        "no tracked or untracked project paths."
        if not has_dirty_worktree
        else (
            "- Branch hygiene remains open until the visible tracked and untracked "
            "project paths are intentionally staged, committed, excluded, or deferred."
        )
    )
    lines = [
        "# Release Readiness Inventory",
        "",
        f"Date: {today.isoformat()}",
        "",
        (
            "Scope: local `Active_Skillference` checkout only. This inventory records "
            "the current git-visible release state and remaining external release "
            "blockers; generation and validation do not create a public release, DOI, "
            "pull request, or destructive cleanup."
        ),
        "",
        "## Dirty Worktree Snapshot",
        "",
        (
            "`git status --short` currently reports "
            f"{status_count} rows outside this inventory file. The detailed file "
            f"lists below contain {tracked_count} modified tracked paths and "
            f"{untracked_count} untracked paths requiring intentional add or exclusion "
            "before a release commit."
        ),
        "",
        (
            "Tracked diff summary outside this inventory file from "
            "`git diff --stat -- . ':(exclude)docs/release_readiness_inventory.md'`: "
            f"`{snapshot.diff_summary}`."
        ),
        "",
        "## Modified Tracked Files",
        "",
    ]
    lines.extend(_path_list(snapshot.modified_tracked_files))
    lines.extend(
        [
            "",
            "## Untracked Files Requiring Intentional Add Later",
            "",
            (
                "These files are visible to `git ls-files -o --exclude-standard` "
                "and must be intentionally reviewed before any release commit:"
            ),
            "",
        ]
    )
    lines.extend(_path_list(snapshot.untracked_files))
    lines.extend(
        [
            "",
            "## Generated Or Ignored Surfaces",
            "",
            (
                "The validator confirms these examples are ignored by git, so generated "
                "publication and local runtime outputs can be refreshed without becoming "
                "tracked release sources by accident:"
            ),
            "",
        ]
    )
    lines.extend(_path_list(snapshot.ignored_examples))
    lines.extend(
        [
            "",
            "## Key Artifact Hashes",
            "",
            (
                "These SHA-256 rows are local reproducibility evidence for generated "
                "bundle artifacts present at validation time. They do not imply a public "
                "archive, DOI, clean release tag, or cross-machine bitwise guarantee."
            ),
            "",
        ]
    )
    lines.extend(_artifact_hash_list(snapshot.artifact_hashes))
    lines.extend(
        [
            "",
            "## Evidence Commands",
            "",
        ]
    )
    lines.extend(f"- `{command}`" for command in REQUIRED_EVIDENCE_COMMANDS)
    lines.extend(
        [
            "",
            "## Remaining Release Blockers",
            "",
            (
                "- Public DOI/repository remains blocked until "
                f"`git ls-remote {PUBLIC_REPOSITORY_URL}` succeeds. Current probe: "
                f"{probes.public_repository}."
            ),
            live_stack_line,
            (
                "- Cross-vendor security audit evidence is closed as a point-in-time "
                "static Forge/GPT-5.4 review in tasks.yaml. That does not create "
                "operational security assurance, dependency/supply-chain coverage, "
                "secrets-in-git-history coverage, or dynamic runtime penetration "
                "testing."
            ),
            branch_hygiene_line,
            "",
            "Once Docker is reachable, run the app-ready proof first, then full dependency parity:",
            "",
            "- `uv run python scripts/validate_full_app_stack.py --app-ready --skip-regenerate`",
            "- `uv run python scripts/validate_full_app_stack.py --skip-regenerate`",
            "",
        ]
    )
    return "\n".join(lines)


def audit_release_readiness_inventory(root: Path) -> list[ReleaseReadinessIssue]:
    """Return release-readiness inventory drift issues without raising."""
    root = Path(root)
    inventory_path = root / "docs" / "release_readiness_inventory.md"
    snapshot = build_release_readiness_snapshot(root)
    issues: list[ReleaseReadinessIssue] = []
    try:
        text = inventory_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [
            ReleaseReadinessIssue(
                "docs/release_readiness_inventory.md", "inventory file is missing"
            )
        ]

    if snapshot.diff_summary not in text:
        issues.append(
            ReleaseReadinessIssue(
                "Dirty Worktree Snapshot",
                f"tracked diff summary is stale; expected {snapshot.diff_summary!r}",
            )
        )
    _audit_exact_section(
        text,
        "Modified Tracked Files",
        snapshot.modified_tracked_files,
        issues,
    )
    _audit_exact_section(
        text,
        "Untracked Files Requiring Intentional Add Later",
        snapshot.untracked_files,
        issues,
    )
    _audit_exact_section(
        text,
        "Generated Or Ignored Surfaces",
        snapshot.ignored_examples,
        issues,
    )
    _audit_artifact_hashes(text, snapshot.artifact_hashes, issues)
    for example in IGNORED_OUTPUT_EXAMPLES:
        if example not in snapshot.ignored_examples:
            issues.append(
                ReleaseReadinessIssue(
                    "Generated Or Ignored Surfaces",
                    f"{example!r} is no longer ignored by git",
                )
            )
    for command in REQUIRED_EVIDENCE_COMMANDS:
        if f"`{command}`" not in text:
            issues.append(
                ReleaseReadinessIssue(
                    "Evidence Commands", f"missing evidence command {command!r}"
                )
            )
    return issues


def validate_release_readiness_inventory(root: Path) -> None:
    """Raise if the release-readiness inventory is stale."""
    issues = audit_release_readiness_inventory(root)
    if issues:
        details = "\n  ".join(str(issue) for issue in issues)
        raise ReleaseReadinessError(
            "release readiness inventory validation failed:\n  "
            f"{details}\n  "
            "To refresh this point-in-time snapshot from the current git state, run: "
            "uv run python scripts/validate_release_readiness_inventory.py --write"
        )


def write_release_readiness_inventory(
    root: Path,
    *,
    blocker_probes: BlockerProbeSummary | None = None,
) -> Path:
    """Refresh the inventory Markdown from current git state and blocker probes."""
    root = Path(root)
    path = root / "docs" / "release_readiness_inventory.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    probes = blocker_probes or collect_blocker_probes(root)
    for _ in range(10):
        snapshot = build_release_readiness_snapshot(root)
        rendered = render_release_readiness_inventory(snapshot, blocker_probes=probes)
        if path.read_text(encoding="utf-8") == rendered:
            return path
        path.write_text(rendered, encoding="utf-8")
    issues = audit_release_readiness_inventory(root)
    if issues:
        raise ReleaseReadinessError(
            "release readiness inventory did not converge after write:\n  "
            + "\n  ".join(str(issue) for issue in issues)
        )
    return path


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ReleaseReadinessError(
            f"git {' '.join(args)} failed with code {result.returncode}: {detail}"
        )
    return result.stdout.rstrip("\n")


def _run_command(
    argv: list[str],
    *,
    cwd: Path,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(argv, 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return subprocess.CompletedProcess(argv, 124, stdout, stderr or "timed out")


def _summarize_probe(result: subprocess.CompletedProcess[str]) -> str:
    if result.returncode == 0:
        return "reachable"
    output = "\n".join(part for part in (result.stderr, result.stdout) if part).strip()
    for line in output.splitlines():
        clean = line.strip()
        if clean:
            return f"blocked ({clean})"
    return f"blocked (exit {result.returncode})"


def _diff_summary(diff_stat: str) -> str:
    lines = [line.strip() for line in diff_stat.splitlines() if line.strip()]
    if not lines:
        return "0 files changed"
    return lines[-1]


def _status_path(line: str) -> str:
    return line[3:].strip() if len(line) > 3 else line.strip()


def _check_ignored_examples(root: Path) -> tuple[str, ...]:
    input_text = "\n".join(IGNORED_OUTPUT_EXAMPLES) + "\n"
    result = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=root,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )
    ignored = tuple(line for line in result.stdout.splitlines() if line.strip())
    return tuple(example for example in IGNORED_OUTPUT_EXAMPLES if example in ignored)


def _collect_artifact_hashes(root: Path) -> tuple[ArtifactHash, ...]:
    paths: list[str] = list(ARTIFACT_HASH_TARGETS)
    registry_path = root / "output" / "figures" / "figure_registry.json"
    if registry_path.is_file():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            registry = []
        if isinstance(registry, list):
            for entry in registry:
                if isinstance(entry, dict):
                    filename = entry.get("filename")
                    if isinstance(filename, str) and filename:
                        paths.append(f"output/figures/{filename}")

    hashes: list[ArtifactHash] = []
    seen: set[str] = set()
    for relative in paths:
        if relative in seen:
            continue
        seen.add(relative)
        path = root / relative
        if path.is_file():
            hashes.append(_hash_artifact(path, relative))
    return tuple(hashes)


def _hash_artifact(path: Path, relative_path: str) -> ArtifactHash:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return ArtifactHash(relative_path, digest.hexdigest(), size)


def _path_list(paths: tuple[str, ...]) -> list[str]:
    if not paths:
        return ["- None."]
    return [f"- `{path}`" for path in paths]


def _artifact_hash_list(items: tuple[ArtifactHash, ...]) -> list[str]:
    if not items:
        return ["- None."]
    return [
        f"- `{item.path}` | sha256: `{item.sha256}` | bytes: {item.size_bytes}"
        for item in items
    ]


def _audit_artifact_hashes(
    text: str,
    expected_hashes: tuple[ArtifactHash, ...],
    issues: list[ReleaseReadinessIssue],
) -> None:
    observed = set(_extract_artifact_hash_rows(text))
    expected = {
        f"{item.path}|{item.sha256}|{item.size_bytes}" for item in expected_hashes
    }
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing:
        issues.append(
            ReleaseReadinessIssue(
                "Key Artifact Hashes",
                "missing or stale artifact hash rows: " + ", ".join(missing),
            )
        )
    if extra:
        issues.append(
            ReleaseReadinessIssue(
                "Key Artifact Hashes",
                "extra artifact hash rows: " + ", ".join(extra),
            )
        )


def _audit_exact_section(
    text: str,
    heading: str,
    expected_paths: tuple[str, ...],
    issues: list[ReleaseReadinessIssue],
) -> None:
    observed = set(_extract_section_paths(text, heading))
    expected = set(expected_paths)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing:
        issues.append(
            ReleaseReadinessIssue(
                heading, "missing paths: " + ", ".join(repr(path) for path in missing)
            )
        )
    if extra:
        issues.append(
            ReleaseReadinessIssue(
                heading, "extra paths: " + ", ".join(repr(path) for path in extra)
            )
        )


def _extract_section_paths(text: str, heading: str) -> tuple[str, ...]:
    match = re.search(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ()
    return tuple(re.findall(r"^-\s+`([^`]+)`\s*$", match.group("body"), re.MULTILINE))


def _extract_artifact_hash_rows(text: str) -> tuple[str, ...]:
    match = re.search(
        r"^## Key Artifact Hashes\n(?P<body>.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ()
    rows = re.findall(
        r"^-\s+`([^`]+)`\s+\|\s+sha256:\s+`([0-9a-f]{64})`\s+\|\s+bytes:\s+(\d+)\s*$",
        match.group("body"),
        re.MULTILINE,
    )
    return tuple(f"{path}|{sha256}|{size}" for path, sha256, size in rows)
