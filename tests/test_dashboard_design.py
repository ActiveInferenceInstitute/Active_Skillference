from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_CSS = PROJECT_ROOT / "src" / "dashboard" / "assets" / "styles.css"
DESIGN_DOC = PROJECT_ROOT / "DESIGN.md"


def test_dashboard_design_system_document_exists() -> None:
    text = DESIGN_DOC.read_text(encoding="utf-8")

    assert "# Active_Skillference Design System" in text
    assert "--surface-primary" in text
    assert "--accent-primary" in text
    assert "Artifact card" in text


def test_dashboard_css_uses_declared_design_tokens() -> None:
    css = DASHBOARD_CSS.read_text(encoding="utf-8")
    design = DESIGN_DOC.read_text(encoding="utf-8")
    root_block, _, rest = css.partition("}\n")
    root_tokens = set(re.findall(r"--[a-z0-9-]+(?=:\s)", root_block))

    assert "--surface-primary" in root_block
    assert "Inter" not in css
    assert not re.search(r"#[0-9A-Fa-f]{3,8}|rgba\(", rest)
    assert root_tokens
    assert not sorted(token for token in root_tokens if token not in design)
