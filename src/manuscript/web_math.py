"""MathJax normalization for rendered manuscript HTML surfaces."""

from __future__ import annotations

import re
from pathlib import Path

MATHJAX_SRC = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js"
MATHJAX_INTEGRITY = (
    "sha384-NR8saakDju74wZ6sprPPhEoWbaP3iVtXVJH12mRSiaIgxMdi33mOQj8bnF2WxzY3"
)
# The publication template currently emits MathJax 4. Keep the project-owned
# MathJax 3 loader for dashboard/local normalization, while recognizing the
# template's exact pinned loader in generated manuscript HTML.
TEMPLATE_MATHJAX_SRC = "https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js"
TEMPLATE_MATHJAX_INTEGRITY = (
    "sha384-2BWc4dVaHADUocwKrUrK9u3iDwHxVMKXWEcoRmUkXYSFKhAsgVAYClu9ydNuo5Oz"
)
MATHJAX_SCRIPT_TAG = (
    f'<script defer src="{MATHJAX_SRC}" integrity="{MATHJAX_INTEGRITY}" '
    'crossorigin="anonymous" onerror="window.renderedMathJaxFailed = true"></script>'
)
MATHJAX_CONFIG_SNIPPET = """\
<script>
  window.MathJax = {
    tex: {
      inlineMath: [["\\\\(", "\\\\)"], ["$", "$"]],
      displayMath: [["\\\\[", "\\\\]"], ["$$", "$$"]],
      processEscapes: true
    }
  };
</script>
"""
MATHJAX_SNIPPET = f"{MATHJAX_CONFIG_SNIPPET}{MATHJAX_SCRIPT_TAG}\n"
_MATHJAX_CDN_SCRIPT_RE = re.compile(
    r"<script\b[^>]*\bsrc=[\"']https://cdn\.jsdelivr\.net/npm/mathjax@[^\"']+[\"'][^>]*>\s*</script>",
    re.IGNORECASE | re.DOTALL,
)


def html_has_math(text: str) -> bool:
    """Return True when rendered HTML contains math-bearing markup or delimiters."""
    return 'class="math' in text or "\\(" in text or "\\[" in text or "$" in text


def html_has_mathjax(text: str) -> bool:
    """Return True when HTML loads a supported MathJax CHTML bundle."""
    return "MathJax" in text and "tex-chtml" in text


def html_has_secure_mathjax(text: str) -> bool:
    return any(
        source in text
        and f'integrity="{integrity}"' in text
        and 'crossorigin="anonymous"' in text
        for source, integrity in (
            (MATHJAX_SRC, MATHJAX_INTEGRITY),
            (TEMPLATE_MATHJAX_SRC, TEMPLATE_MATHJAX_INTEGRITY),
        )
    )


def _insert_mathjax(text: str, snippet: str) -> str:
    if "</head>" in text:
        return text.replace("</head>", snippet + "</head>", 1)
    if "<body" in text:
        return text.replace("<body", snippet + "<body", 1)
    return snippet + text


def ensure_mathjax_in_html(path: Path) -> bool:
    """Insert MathJax into one HTML file when it contains math and lacks MathJax."""
    text = path.read_text(encoding="utf-8")
    if not html_has_math(text):
        return False
    if html_has_secure_mathjax(text):
        return False
    without_cdn_scripts = _MATHJAX_CDN_SCRIPT_RE.sub("", text)
    snippet = (
        MATHJAX_SCRIPT_TAG + "\n"
        if "window.MathJax" in without_cdn_scripts
        else MATHJAX_SNIPPET
    )
    updated = _insert_mathjax(without_cdn_scripts, snippet)
    path.write_text(updated, encoding="utf-8")
    return True


def ensure_mathjax_in_web_dir(web_dir: Path) -> list[Path]:
    """Normalize every HTML file in ``web_dir`` and return modified paths."""
    if not web_dir.is_dir():
        raise FileNotFoundError(f"web output directory does not exist: {web_dir}")
    changed: list[Path] = []
    for path in sorted(web_dir.glob("*.html")):
        if ensure_mathjax_in_html(path):
            changed.append(path)
    return changed
