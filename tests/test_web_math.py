"""Tests for rendered-web MathJax normalization."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from src.manuscript.web_math import (
    MATHJAX_SCRIPT_TAG,
    TEMPLATE_MATHJAX_INTEGRITY,
    TEMPLATE_MATHJAX_SRC,
    ensure_mathjax_in_html,
    ensure_mathjax_in_web_dir,
    html_has_math,
    html_has_mathjax,
    html_has_secure_mathjax,
)

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import validate_web_math as validate_web_math_script


def test_ensure_mathjax_in_html_inserts_loader_for_math(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    page.write_text(
        "<html><head></head><body>\\(F = E_q[\\ln q - \\ln p]\\)</body></html>",
        encoding="utf-8",
    )

    assert ensure_mathjax_in_html(page) is True
    text = page.read_text(encoding="utf-8")
    assert "MathJax" in text
    assert "tex-chtml-full.js" in text


def test_ensure_mathjax_in_html_leaves_plain_page_unchanged(tmp_path: Path) -> None:
    page = tmp_path / "plain.html"
    page.write_text(
        "<html><head></head><body>No formulas here.</body></html>", encoding="utf-8"
    )

    assert ensure_mathjax_in_html(page) is False
    assert "MathJax" not in page.read_text(encoding="utf-8")


def test_ensure_mathjax_in_web_dir_returns_changed_paths(tmp_path: Path) -> None:
    web = tmp_path / "web"
    web.mkdir()
    math_page = web / "math.html"
    plain_page = web / "plain.html"
    math_page.write_text(
        "<html><head></head><body>$F(q)$</body></html>", encoding="utf-8"
    )
    plain_page.write_text(
        "<html><head></head><body>Plain text</body></html>", encoding="utf-8"
    )

    changed = ensure_mathjax_in_web_dir(web)

    assert changed == [math_page]
    assert "MathJax" in math_page.read_text(encoding="utf-8")
    assert "MathJax" not in plain_page.read_text(encoding="utf-8")


def test_ensure_mathjax_inserts_before_body_when_no_head(tmp_path: Path) -> None:
    """Math page lacking </head> gets the loader inserted before <body>."""
    page = tmp_path / "headless.html"
    page.write_text("<body>\\[x = y\\]</body>", encoding="utf-8")

    assert ensure_mathjax_in_html(page) is True
    text = page.read_text(encoding="utf-8")
    # Loader must precede the <body> tag, with no </head> seam present.
    assert "</head>" not in text
    assert text.index("MathJax") < text.index("<body")
    assert "tex-chtml-full.js" in text


def test_ensure_mathjax_prepends_when_no_head_or_body(tmp_path: Path) -> None:
    """A bare math fragment with neither </head> nor <body> gets a prepended loader."""
    page = tmp_path / "fragment.html"
    page.write_text("\\(a + b\\)", encoding="utf-8")

    assert ensure_mathjax_in_html(page) is True
    text = page.read_text(encoding="utf-8")
    assert text.startswith("<script>")
    assert "MathJax" in text
    assert text.rstrip().endswith("\\(a + b\\)")


def test_ensure_mathjax_in_html_replaces_insecure_existing_mathjax(
    tmp_path: Path,
) -> None:
    page = tmp_path / "already.html"
    original = (
        "<html><head>"
        "<script>window.MathJax = {};</script>"
        '<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/'
        'tex-chtml-full.js"></script>'
        "</head><body>$E=mc^2$</body></html>"
    )
    page.write_text(original, encoding="utf-8")
    # Sentinel: this page satisfies both MathJax-detection tokens.
    assert html_has_mathjax(original) is True
    assert html_has_secure_mathjax(original) is False

    assert ensure_mathjax_in_html(page) is True
    text = page.read_text(encoding="utf-8")
    assert text != original
    assert html_has_secure_mathjax(text) is True
    assert text.count("tex-chtml-full.js") == 1
    assert "window.MathJax = {}" in text


def test_ensure_mathjax_in_html_skips_secure_existing_mathjax(
    tmp_path: Path,
) -> None:
    page = tmp_path / "secure.html"
    original = (
        "<html><head>"
        "<script>window.MathJax = {};</script>"
        f"{MATHJAX_SCRIPT_TAG}"
        "</head><body>$E=mc^2$</body></html>"
    )
    page.write_text(original, encoding="utf-8")
    assert html_has_secure_mathjax(original) is True

    assert ensure_mathjax_in_html(page) is False
    assert page.read_text(encoding="utf-8") == original


def test_ensure_mathjax_in_web_dir_raises_for_missing_dir(tmp_path: Path) -> None:
    """A non-existent web directory raises FileNotFoundError naming the path."""
    missing = tmp_path / "nope"

    with pytest.raises(FileNotFoundError) as exc:
        ensure_mathjax_in_web_dir(missing)

    assert str(missing) in str(exc.value)


def test_ensure_mathjax_in_web_dir_raises_when_path_is_file(tmp_path: Path) -> None:
    """A file (not a directory) is rejected by the is_dir guard."""
    not_a_dir = tmp_path / "file.html"
    not_a_dir.write_text("<body>$x$</body>", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        ensure_mathjax_in_web_dir(not_a_dir)


def test_ensure_mathjax_in_web_dir_empty_dir_returns_no_changes(tmp_path: Path) -> None:
    """An existing directory with no HTML files yields an empty change list."""
    web = tmp_path / "web"
    web.mkdir()
    (web / "notes.txt").write_text("$ignored$", encoding="utf-8")

    assert ensure_mathjax_in_web_dir(web) == []


def test_validate_web_math_requires_combined_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lone smoke page must not certify that the combined web manuscript exists."""
    web = tmp_path / "web"
    web.mkdir()
    (web / "math_smoke.html").write_text(
        "<html>Plain smoke page.</html>", encoding="utf-8"
    )
    dashboard = tmp_path / "dashboard"
    dashboard.mkdir()
    dashboard_index = dashboard / "index.html"
    dashboard_app = dashboard / "app.js"
    dashboard_index.write_text("MathJax tex-chtml-full.js", encoding="utf-8")
    dashboard_app.write_text(
        "renderRichText typesetMath MathJax.typesetPromise", encoding="utf-8"
    )
    monkeypatch.setattr(validate_web_math_script, "WEB", web)
    monkeypatch.setattr(validate_web_math_script, "DASHBOARD_INDEX", dashboard_index)
    monkeypatch.setattr(validate_web_math_script, "DASHBOARD_APP", dashboard_app)

    issues = validate_web_math_script._issues()

    assert any("output/web/index.html is missing" in issue for issue in issues)


def test_html_has_math_detects_each_delimiter_form() -> None:
    """Each recognized math marker independently triggers detection."""
    assert html_has_math('<span class="math inline">x</span>') is True
    assert html_has_math("inline \\( y \\) here") is True
    assert html_has_math("display \\[ z \\] here") is True
    assert html_has_math("dollar $w$ math") is True
    assert html_has_math("just plain prose") is False


def test_html_has_mathjax_requires_both_tokens() -> None:
    """Detection demands both the MathJax marker and the CHTML bundle name."""
    assert html_has_mathjax("MathJax tex-chtml-full.js") is True
    assert html_has_mathjax("MathJax only, wrong bundle") is False
    assert html_has_mathjax("tex-chtml but no marker") is False
    assert html_has_mathjax("neither token present") is False


def test_html_has_secure_mathjax_accepts_template_mathjax_four() -> None:
    html = (
        "<script>window.MathJax = {};</script>"
        f'<script src="{TEMPLATE_MATHJAX_SRC}" '
        f'integrity="{TEMPLATE_MATHJAX_INTEGRITY}" '
        'crossorigin="anonymous"></script>'
    )
    assert html_has_mathjax(html) is True
    assert html_has_secure_mathjax(html) is True
