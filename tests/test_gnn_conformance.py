"""Conformance tests for the discrete active-inference agent GNN specification.

The pinned-parser half skips cleanly when the GNN checkout or its interpreter is
unavailable; the specification-vs-kernel checks run against the kernel's own
canonical model, so CI still guards the specification.
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from src.gnn_conformance import (
    SPEC_PATH,
    ConformanceError,
    GnnUnavailable,
    Pin,
    canonical_model,
    check_conformance,
    extract_spec,
    load_pin,
    pinned_source,
    receipt,
    resolve_gnn_root,
    resolve_interpreter,
    spec_sha256,
    verify_pin,
)

REQUIRED_SECTIONS = (
    "GNNSection",
    "GNNVersionAndFlags",
    "ModelName",
    "StateSpaceBlock",
    "Connections",
    "InitialParameterization",
    "Equations",
    "Time",
    "ActInfOntologyAnnotation",
    "ModelParameters",
    "Footer",
    "Signature",
)

CANONICAL_PIN = {
    "repository": "ActiveInferenceInstitute/Generalized_Notation_Notation",
    "tag": "v5.0.3",
    "commit": "8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1",
}


@pytest.fixture(scope="module")
def extracted_model() -> dict:
    try:
        return extract_spec()
    except GnnUnavailable as exc:
        pytest.skip(f"pinned GNN checkout unavailable: {exc}")


def test_pin_record_is_canonical() -> None:
    pin = load_pin()
    assert pin.repository == CANONICAL_PIN["repository"]
    assert pin.tag == CANONICAL_PIN["tag"]
    assert pin.commit == CANONICAL_PIN["commit"]


def test_spec_declares_every_section() -> None:
    text = SPEC_PATH.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" in text, f"missing section {section}"


def declared_dimensions() -> dict[str, tuple[int, ...]]:
    text = SPEC_PATH.read_text(encoding="utf-8")
    dimensions: dict[str, tuple[int, ...]] = {}
    for line in text.splitlines():
        match = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)\[([0-9]+(?:\s*,\s*[0-9]+)*)\s*,type=",
            line.strip(),
        )
        if match:
            dimensions[match.group(1)] = tuple(
                int(part) for part in match.group(2).split(",")
            )
    return dimensions


def test_declared_dimensions_match_the_kernel() -> None:
    dimensions = declared_dimensions()
    agent = canonical_model()
    assert dimensions["A"] == (agent["num_observations"], agent["num_states"])
    assert dimensions["B"] == (
        agent["num_states"],
        agent["num_states"],
        agent["num_actions"],
    )
    assert dimensions["C"] == (agent["num_observations"],)
    assert dimensions["D"] == (agent["num_states"],)
    assert dimensions["E"] == (agent["num_actions"],)
    assert dimensions["s"] == (agent["num_states"], 1)
    assert dimensions["o"] == (agent["num_observations"], 1)


def test_kernel_canonical_model_conforms() -> None:
    checks = check_conformance(canonical_model())
    assert len(checks) == 6


def test_mutated_model_is_rejected() -> None:
    model = copy.deepcopy(canonical_model())
    model["B_matrix"][0][0][1] = 0.0  # break the commit transition
    with pytest.raises(ConformanceError, match="transition"):
        check_conformance(model)


def test_invalid_pin_commit_is_rejected(tmp_path) -> None:
    pin = tmp_path / "upstream.json"
    pin.write_text(
        '{"repository": "x", "tag": "v1", "commit": "not-a-sha"}', encoding="utf-8"
    )
    with pytest.raises(ConformanceError, match="40-character"):
        load_pin(pin)


def test_missing_pin_file_is_rejected(tmp_path) -> None:
    with pytest.raises(ConformanceError, match="is missing"):
        load_pin(tmp_path / "upstream.json")


def test_incomplete_pin_record_is_rejected(tmp_path) -> None:
    pin = tmp_path / "upstream.json"
    pin.write_text('{"repository": "x", "tag": "v1"}', encoding="utf-8")
    with pytest.raises(ConformanceError, match="missing the 'commit' field"):
        load_pin(pin)


def test_malformed_pin_file_is_rejected(tmp_path) -> None:
    pin = tmp_path / "upstream.json"
    pin.write_text("not json", encoding="utf-8")
    with pytest.raises(ConformanceError, match="is unreadable"):
        load_pin(pin)


def test_resolve_gnn_root_accepts_an_explicit_checkout(tmp_path) -> None:
    root = tmp_path / "gnn"
    (root / "src" / "gnn").mkdir(parents=True)
    (root / "src" / "gnn" / "__init__.py").write_text("", encoding="utf-8")
    assert resolve_gnn_root(root) == root.resolve()


def test_resolve_gnn_root_rejects_a_missing_checkout(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GNN_ROOT", raising=False)
    # The sibling checkout exists on a development machine, so pin the default
    # root to an absent path: the check must fail closed wherever it runs.
    monkeypatch.setattr(
        "src.gnn_conformance.DEFAULT_GNN_ROOT", tmp_path / "absent-sibling"
    )
    with pytest.raises(GnnUnavailable, match="no GNN checkout"):
        resolve_gnn_root(tmp_path / "absent")


def test_resolve_interpreter_honours_gnn_python(tmp_path, monkeypatch) -> None:
    interpreter = tmp_path / "python"
    interpreter.write_text("", encoding="utf-8")
    monkeypatch.setenv("GNN_PYTHON", str(interpreter))
    assert resolve_interpreter(tmp_path) == interpreter


def test_resolve_interpreter_rejects_missing_gnn_python(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GNN_PYTHON", str(tmp_path / "absent"))
    with pytest.raises(GnnUnavailable, match="GNN_PYTHON"):
        resolve_interpreter(tmp_path)


def test_receipt_records_pin_and_spec_hash() -> None:
    model = canonical_model()
    result = receipt(model, check_conformance(model))
    assert result["spec"] == "gnn/discrete_active_inference_agent.gnn.md"
    assert result["spec_sha256"] == spec_sha256()
    assert result["pin"]["commit"] == CANONICAL_PIN["commit"]
    assert result["dimensions"] == {
        "num_states": 2,
        "num_observations": 2,
        "num_actions": 2,
    }


def test_extraction_uses_schema_major_one(extracted_model: dict) -> None:
    assert extracted_model["extraction_schema_version"].startswith("1.")


def test_extracted_spec_conforms_to_the_kernel(extracted_model: dict) -> None:
    assert len(check_conformance(extracted_model)) == 6


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )


def _scratch_checkout(
    tmp_path: Path,
    *,
    payload: str | None = None,
    exit_code: int = 0,
    package: bool = True,
) -> tuple[Path, Pin]:
    """Create a real git checkout whose ``src/gnn`` tree carries a stub extractor.

    Test-only scratch repositories let the extraction plumbing run for real — git
    archive, tar, and a real interpreter running ``python -m gnn.extract`` — even
    where the GNN clone is absent, which is the CI case.
    """

    root = tmp_path / "scratch-gnn"
    extractor = root / "src" / "gnn" / "extract"
    extractor.mkdir(parents=True)
    if package:
        (root / "src" / "gnn" / "__init__.py").write_text("", encoding="utf-8")
    (extractor / "__init__.py").write_text("", encoding="utf-8")
    body = payload if payload is not None else json.dumps(canonical_model())
    (extractor / "__main__.py").write_text(
        f"import sys\nprint({body!r})\nsys.exit({exit_code})\n",
        encoding="utf-8",
    )
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "GNN Conformance Test")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "stub GNN checkout")
    commit = _git(root, "rev-parse", "HEAD").stdout.strip()
    _git(root, "tag", "v5.0.3")
    return root, Pin(
        repository="ActiveInferenceInstitute/Generalized_Notation_Notation",
        tag="v5.0.3",
        commit=commit,
    )


def test_extract_spec_reads_a_scratch_pinned_checkout(tmp_path) -> None:
    root, pin = _scratch_checkout(tmp_path)
    model = extract_spec(SPEC_PATH, gnn_root=root, interpreter=sys.executable, pin=pin)
    assert model == canonical_model()
    assert len(check_conformance(model)) == 6


def test_extract_spec_rejects_an_error_payload(tmp_path) -> None:
    root, pin = _scratch_checkout(
        tmp_path, payload=json.dumps({"status": "error", "error": "stub rejected"})
    )
    with pytest.raises(ConformanceError, match="rejected"):
        extract_spec(SPEC_PATH, gnn_root=root, interpreter=sys.executable, pin=pin)


def test_extract_spec_rejects_an_unexpected_schema(tmp_path) -> None:
    root, pin = _scratch_checkout(
        tmp_path, payload=json.dumps({"extraction_schema_version": "2.0.0"})
    )
    with pytest.raises(ConformanceError, match="unexpected extraction schema"):
        extract_spec(SPEC_PATH, gnn_root=root, interpreter=sys.executable, pin=pin)


def test_extract_spec_reports_extractor_failure(tmp_path) -> None:
    root, pin = _scratch_checkout(tmp_path, exit_code=3)
    with pytest.raises(ConformanceError, match="extractor failed"):
        extract_spec(SPEC_PATH, gnn_root=root, interpreter=sys.executable, pin=pin)


def test_verify_pin_rejects_an_unknown_tag(tmp_path) -> None:
    root, pin = _scratch_checkout(tmp_path)
    with pytest.raises(ConformanceError, match="git rev-parse"):
        verify_pin(
            root, Pin(repository=pin.repository, tag="v0.0.0", commit=pin.commit)
        )


def test_verify_pin_rejects_an_abbreviated_commit(tmp_path) -> None:
    root, pin = _scratch_checkout(tmp_path)
    abbreviated = Pin(repository=pin.repository, tag=pin.tag, commit=pin.commit[:12])
    with pytest.raises(ConformanceError, match="pinned commit resolves to"):
        verify_pin(root, abbreviated)


def test_verify_pin_rejects_a_tag_at_another_commit(tmp_path) -> None:
    root, pin = _scratch_checkout(tmp_path)
    (root / "src" / "gnn" / "extract" / "extra.py").write_text("", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "second commit")
    _git(root, "tag", "v5.0.4")
    with pytest.raises(ConformanceError, match="pinned tag v5.0.4 resolves to"):
        verify_pin(
            root, Pin(repository=pin.repository, tag="v5.0.4", commit=pin.commit)
        )


def test_pinned_source_rejects_an_incomplete_tree(tmp_path) -> None:
    root, pin = _scratch_checkout(tmp_path, package=False)
    with pytest.raises(ConformanceError, match="incomplete"):
        pinned_source(root, pin, tmp_path / "extracted")


def test_load_pin_rejects_a_non_object(tmp_path) -> None:
    pin_file = tmp_path / "upstream.json"
    pin_file.write_text("[]", encoding="utf-8")
    with pytest.raises(ConformanceError, match="must contain a JSON object"):
        load_pin(pin_file)


def test_resolve_interpreter_falls_back_to_the_running_python(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.delenv("GNN_PYTHON", raising=False)
    assert resolve_interpreter(tmp_path) == Path(sys.executable)


def test_resolve_interpreter_prefers_a_checkout_venv(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GNN_PYTHON", raising=False)
    venv_python = tmp_path / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")
    assert resolve_interpreter(tmp_path) == venv_python


def test_pinned_source_reports_an_archive_failure(tmp_path) -> None:
    root, _pin = _scratch_checkout(tmp_path)
    absent = Pin(repository="stub", tag="v5.0.3", commit="0" * 40)
    with pytest.raises(ConformanceError, match="could not extract pinned GNN source"):
        pinned_source(root, absent, tmp_path / "extracted")
