#!/usr/bin/env python3
"""Render the manuscript to PDF with the repository's own toolchain.

This is the project's authoritative render path. It hydrates the authored sections
through ``scripts/z_generate_manuscript_variables.py`` (so every ``{{claim:NAME}}``
and count token comes from ``manuscript_variables.json``, never from prose),
assembles the hydrated sections in lexicographic order with page breaks and a
generated title page, and then runs the standard LaTeX citation cycle:

    pandoc --natbib → xelatex → bibtex → xelatex → xelatex

``manuscript/config.yaml`` supplies metadata (title, subtitle, authors, DOI,
keywords), ``manuscript/preamble.md`` supplies the LaTeX packages, and
``manuscript/references.bib`` supplies the bibliography. ``pandoc-crossref``
resolves the manuscript's ``[@fig:label]`` / ``[@sec:label]`` references, which
the preamble's ``cleveref`` prints.

Output: ``output/pdf/Active_Skillference_combined.pdf``.

Everything intermediate (the combined Markdown, the ``.tex``, ``.aux``, ``.log``,
``.bbl``, the bibliography copy, and the first two PDF passes) stays in a scratch
directory under the repository root. It has to live one level below the root, not
under ``output/pdf/``, because the manuscript writes figure paths as
``../output/figures/x.png`` — valid from a file one level below the root.

Requires ``pandoc``, ``pandoc-crossref`` built for the same Pandoc major version,
``xelatex``, and ``bibtex`` on ``PATH``. A missing tool is named and the run stops;
no partial PDF is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
OUTPUT_MANUSCRIPT = ROOT / "output" / "manuscript"
OUTPUT_PDF = ROOT / "output" / "pdf"
PDF_NAME = "Active_Skillference_combined.pdf"
# Files the hydrator writes beside the sections that are not manuscript sections.
SECTION_EXCLUDE = {"config.yaml", "preamble.md", "README.md", "AGENTS.md", "SYNTAX.md"}
# Log lines that mean the PDF would ship with broken references or citations. A LaTeX
# "Font Warning: ... undefined" line must not be read as a broken reference, so a match
# needs both the subject ("Citation"/"Reference") and the word "undefined".
BROKEN_LOG_SUBJECTS = ("Citation", "Reference")


def _require(tool: str) -> str:
    found = shutil.which(tool)
    if found is None:
        raise SystemExit(
            f"{tool} is required to render the manuscript and is not on PATH; "
            "install it (pandoc 3.x, pandoc-crossref for that Pandoc version, and a "
            "TeX Live with xelatex and bibtex) and re-run"
        )
    return found


def _hydrate(skip_kernels: bool) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "z_generate_manuscript_variables.py"),
    ]
    if skip_kernels:
        command.append("--skip-kernels")
    subprocess.run(command, cwd=ROOT, check=True)


def _latex_preamble() -> str:
    """Return the ```latex fenced block from manuscript/preamble.md."""
    text = (MANUSCRIPT / "preamble.md").read_text(encoding="utf-8")
    marker = "```latex"
    start = text.find(marker)
    if start == -1:
        raise SystemExit("manuscript/preamble.md has no ```latex block")
    start = text.find("\n", start) + 1
    end = text.find("```", start)
    if end == -1:
        raise SystemExit("manuscript/preamble.md has an unterminated ```latex block")
    return text[start:end]


def _config() -> dict[str, object]:
    import yaml  # type: ignore[import-untyped]

    payload = yaml.safe_load((MANUSCRIPT / "config.yaml").read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("manuscript/config.yaml did not parse as a mapping")
    return payload


def _latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _titlepage(config: dict[str, object]) -> str:
    """Return the raw-LaTeX title page built from manuscript/config.yaml."""
    paper = config.get("paper") or {}
    book = config.get("book") or {}
    publication = config.get("publication") or {}
    authors = config.get("authors") or []
    paper = paper if isinstance(paper, dict) else {}
    book = book if isinstance(book, dict) else {}
    publication = publication if isinstance(publication, dict) else {}
    cover = (book.get("cover") or {}) if isinstance(book.get("cover"), dict) else {}
    lines = ["```{=latex}", r"\begin{titlepage}", r"\centering"]
    image_name = cover.get("image")
    if isinstance(image_name, str) and image_name:
        image = (OUTPUT_MANUSCRIPT / image_name).resolve()
        if not image.is_file():
            raise SystemExit(
                "book.cover.image does not resolve to a file: "
                f"{image_name} (resolved from {OUTPUT_MANUSCRIPT})"
            )
        lines += [
            r"\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{"
            + image.as_posix()
            + "}",
            r"\vfill",
        ]
    title = str(paper.get("title") or book.get("title") or "")
    subtitle = str(paper.get("subtitle") or book.get("subtitle") or "")
    version = str(paper.get("version") or book.get("edition") or "")
    lines.append(r"{\Huge\bfseries " + _latex_escape(title) + r"\par}")
    if subtitle:
        lines.append(
            r"\vspace{0.6em}{\Large\itshape " + _latex_escape(subtitle) + r"\par}"
        )
    for author in authors if isinstance(authors, list) else []:
        if not isinstance(author, dict):
            continue
        name = _latex_escape(str(author.get("name", "")))
        affiliation = _latex_escape(str(author.get("affiliation", "")))
        orcid = _latex_escape(str(author.get("orcid", "")))
        lines.append(r"\vspace{1.2em}{\large " + name + r"\par}")
        if affiliation:
            lines.append(r"{\normalsize " + affiliation + r"\par}")
        if orcid:
            lines.append(r"{\footnotesize ORCID " + orcid + r"\par}")
    doi = str(publication.get("doi", ""))
    if doi:
        lines.append(
            r"\vspace{1em}{\normalsize \texttt{" + _latex_escape(doi) + r"}\par}"
        )
    if version:
        lines.append(r"{\normalsize version " + _latex_escape(version) + r"\par}")
    lines += [r"\end{titlepage}", "```", ""]
    return "\n".join(lines)


def _section_files() -> list[Path]:
    return [
        path
        for path in sorted(OUTPUT_MANUSCRIPT.glob("*.md"))
        if path.name not in SECTION_EXCLUDE
    ]


def _assemble(config: dict[str, object], destination: Path) -> list[Path]:
    sections = _section_files()
    if not sections:
        raise SystemExit(
            f"no hydrated sections in {OUTPUT_MANUSCRIPT}; run "
            "`uv run python scripts/z_generate_manuscript_variables.py`"
        )
    parts = [_titlepage(config)]
    for index, path in enumerate(sections):
        if index:
            parts.append("```{=latex}\n\\newpage\n```\n")
        parts.append(path.read_text(encoding="utf-8").rstrip() + "\n")
    destination.write_text("\n".join(parts), encoding="utf-8")
    return sections


def _metadata(config: dict[str, object]) -> list[str]:
    paper = config.get("paper") or {}
    book = config.get("book") or {}
    metadata = config.get("metadata") or {}
    paper = paper if isinstance(paper, dict) else {}
    book = book if isinstance(book, dict) else {}
    metadata = metadata if isinstance(metadata, dict) else {}
    title = str(paper.get("title") or book.get("title") or "")
    subtitle = str(paper.get("subtitle") or book.get("subtitle") or "")
    language = str(metadata.get("language") or "en")
    keywords = config.get("keywords") or []
    args = ["--metadata", f"title={title}", "--metadata", f"lang={language}"]
    if subtitle:
        args += ["--metadata", f"subtitle={subtitle}"]
    if keywords:
        args += ["--metadata", "keywords=" + ", ".join(str(word) for word in keywords)]
    return args


def _run(command: list[str], *, cwd: Path, what: str) -> None:
    result = subprocess.run(
        command,
        check=False,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        tail = "\n".join((result.stdout or "").splitlines()[-25:])
        raise SystemExit(f"{what} failed (exit {result.returncode}):\n{tail}")


def _check_log(log: Path) -> None:
    if not log.is_file():
        raise SystemExit(f"no LaTeX log at {log}; the render did not run")
    text = log.read_text(encoding="utf-8", errors="replace")
    broken = [
        line
        for line in text.splitlines()
        if "undefined" in line
        and any(subject in line for subject in BROKEN_LOG_SUBJECTS)
    ]
    if broken:
        raise SystemExit(
            "the rendered PDF would carry unresolved references or citations:\n"
            + "\n".join(broken[:10])
        )


def _write_pdf_receipt(target: Path, *, root: Path = ROOT) -> Path:
    """Record the finalized PDF bytes and the checkout's source revision."""
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    content = target.read_bytes()
    receipt = target.with_suffix(".receipt.json")
    receipt.write_text(
        json.dumps(
            {
                "schema": "active-skillference-pdf/v1",
                "output_path": target.relative_to(root).as_posix(),
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "source_revision": revision,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return receipt


def _render_pdf(scratch: Path, config: dict[str, object]) -> Path:
    pandoc = _require("pandoc")
    crossref = _require("pandoc-crossref")
    xelatex = _require("xelatex")
    bibtex = _require("bibtex")

    preamble = scratch / "preamble.tex"
    preamble.write_text(_latex_preamble(), encoding="utf-8")
    source = scratch / "combined.md"
    sections = _assemble(config, source)
    # bibtex resolves the emitted \bibliography{references} against the build cwd.
    shutil.copy2(MANUSCRIPT / "references.bib", scratch / "references.bib")
    tex = scratch / "combined.tex"

    _run(
        [
            pandoc,
            str(source),
            "--to=latex",
            "--standalone",
            "--toc",
            "--toc-depth=2",
            "--number-sections",
            "--filter",
            crossref,
            "--include-in-header",
            str(preamble),
            "--natbib",
            "--bibliography",
            "references.bib",
            "--metadata",
            "documentclass=article",
            *_metadata(config),
            "-o",
            str(tex),
        ],
        cwd=scratch,
        what="pandoc",
    )

    latex = [xelatex, "-interaction=nonstopmode", "-halt-on-error", tex.name]
    _run(latex, cwd=scratch, what="the first xelatex pass")
    _run([bibtex, "combined"], cwd=scratch, what="bibtex")
    _run(latex, cwd=scratch, what="the second xelatex pass")
    _run(latex, cwd=scratch, what="the final xelatex pass")
    _check_log(scratch / "combined.log")

    produced = scratch / "combined.pdf"
    if not produced.is_file() or produced.stat().st_size == 0:
        raise SystemExit(f"xelatex reported success but wrote no PDF ({produced})")
    OUTPUT_PDF.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_PDF / PDF_NAME
    shutil.copy2(produced, target)
    _write_pdf_receipt(target)
    print(f"rendered {len(sections)} sections -> {target.relative_to(ROOT)}")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-kernels",
        action="store_true",
        help="render the already-generated variables instead of re-running the kernels",
    )
    args = parser.parse_args(argv)

    _require("pandoc")
    _require("pandoc-crossref")
    _require("xelatex")
    _require("bibtex")
    _hydrate(args.skip_kernels)
    config = _config()

    with tempfile.TemporaryDirectory(dir=ROOT, prefix=".render-") as scratch:
        _render_pdf(Path(scratch), config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
