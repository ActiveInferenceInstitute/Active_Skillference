#!/usr/bin/env python3
"""Template-render hook for provenance-resolved manuscript output.

The source manuscript intentionally carries ``{{claim:NAME}}`` tokens so review
can see which numbers are kernel-backed. The template renderer consumes
``output/manuscript/`` when present, so this hook writes resolved copies there
after running the project-native kernel/provenance gate.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
OUTPUT_MANUSCRIPT = ROOT / "output" / "manuscript"
RENDER_SKIP = {"AGENTS.md", "README.md", "SYNTAX.md", "preamble.md"}

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.curriculum.model import CLAIM_TOKEN_RE

CODE_SPAN_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
VARIABLE_TOKEN_RE = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_]*)\}\}")
ANY_TOKEN_RE = re.compile(r"\{\{[^}]+}}")


def _render_prose(text: str, variables: dict[str, str]) -> str:
    def replace_claim(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise KeyError(f"unresolved claim token: {key}")
        return variables[key]

    def replace_variable(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return VARIABLE_TOKEN_RE.sub(
        replace_variable, CLAIM_TOKEN_RE.sub(replace_claim, text)
    )


def _render_markdown(text: str, variables: dict[str, str]) -> str:
    parts: list[str] = []
    cursor = 0
    for match in CODE_SPAN_RE.finditer(text):
        parts.append(_render_prose(text[cursor : match.start()], variables))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(_render_prose(text[cursor:], variables))

    rendered = "".join(parts)
    # Code-span examples explain token syntax. Keep them readable without
    # leaving literal double-brace placeholders in rendered public surfaces.
    rendered = CLAIM_TOKEN_RE.sub(lambda m: f"claim:{m.group(1)}", rendered)
    rendered = VARIABLE_TOKEN_RE.sub(lambda m: m.group(1), rendered)
    leftovers = sorted(set(ANY_TOKEN_RE.findall(rendered)))
    if leftovers:
        raise ValueError(f"unresolved manuscript tokens: {', '.join(leftovers)}")
    return rendered


def _variables() -> dict[str, str]:
    path = ROOT / "output" / "data" / "manuscript_variables.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def _copy_render_auxiliaries() -> None:
    for name in ("config.yaml", "preamble.md"):
        source = MANUSCRIPT / name
        if source.is_file():
            shutil.copy2(source, OUTPUT_MANUSCRIPT / name)
    for source in sorted(MANUSCRIPT.glob("*.bib")):
        shutil.copy2(source, OUTPUT_MANUSCRIPT / source.name)


def main(argv: list[str] | None = None) -> int:
    # `--skip-kernels` renders the current `output/data/manuscript_variables.json`
    # without re-running the kernel/provenance gate first. It exists for iterating
    # on prose and for a render that already follows the artifact arm; the default
    # path still regenerates and re-validates every claim.
    arguments = sys.argv[1:] if argv is None else argv
    if "--skip-kernels" in arguments:
        if not (ROOT / "output" / "data" / "manuscript_variables.json").is_file():
            sys.stderr.write(
                "no output/data/manuscript_variables.json; run "
                "`uv run python scripts/run_kernels.py` first\n"
            )
            return 2
    else:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_kernels.py")],
            cwd=ROOT,
            check=True,
        )

    if OUTPUT_MANUSCRIPT.exists():
        shutil.rmtree(OUTPUT_MANUSCRIPT)
    OUTPUT_MANUSCRIPT.mkdir(parents=True)

    variables = _variables()
    for source in sorted(MANUSCRIPT.glob("*.md")):
        if source.name in RENDER_SKIP:
            continue
        rendered = _render_markdown(source.read_text(encoding="utf-8"), variables)
        (OUTPUT_MANUSCRIPT / source.name).write_text(rendered, encoding="utf-8")
    _copy_render_auxiliaries()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
