"""Tests for the project path helpers retained from the template scaffold."""

from __future__ import annotations

from pathlib import Path

from src.project_paths import project_output_dirs, resolve_project_root


def test_project_output_dirs_has_expected_keys() -> None:
    dirs = project_output_dirs(Path("/tmp/example"))
    assert set(dirs) == {"output", "figures", "data", "reports", "web"}
    assert dirs["figures"] == Path("/tmp/example/output/figures")


def test_project_output_dirs_defaults_to_repo_root() -> None:
    dirs = project_output_dirs()
    assert dirs["output"].name == "output"


def test_resolve_project_root_returns_path() -> None:
    root = resolve_project_root("src")
    assert isinstance(root, Path)
    assert (root / "src").exists()


def test_resolve_project_root_honors_module_attribute() -> None:
    """A package exposing a ``project_root`` attribute overrides the default root."""
    import sys
    import types

    mod = types.ModuleType("fixture_pkg_with_root")
    mod.project_root = "/tmp/custom_root"  # type: ignore[attr-defined]
    sys.modules["fixture_pkg_with_root"] = mod
    try:
        assert resolve_project_root("fixture_pkg_with_root") == Path("/tmp/custom_root")
    finally:
        del sys.modules["fixture_pkg_with_root"]
