"""Conformance checks for the discrete active-inference agent GNN specification.

The model is specified in ``gnn/discrete_active_inference_agent.gnn.md`` and
validated with the Generalized Notation Notation (GNN) revision pinned in
``gnn/upstream.json``. The pinned revision is read from the pinned commit (via
``git archive``), never from the GNN checkout's working tree, so in-progress
edits in that repository cannot contaminate a check.

Two entry points share this module:

- ``tests/test_gnn_conformance.py`` — pytest checks (the pinned-parser half
  skips cleanly when the GNN checkout or its interpreter is unavailable; the
  specification-vs-kernel checks run against the kernel's own model);
- ``scripts/validate_gnn_spec.py`` — the strict local gate (fails, never
  skips).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.kernels.active_inference import (
    DiscreteActiveInferenceAgent,
    expected_free_energy,
)
from src.kernels.examples import two_action_regime_agent

REPO_ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = REPO_ROOT / "gnn" / "upstream.json"
SPEC_PATH = REPO_ROOT / "gnn" / "discrete_active_inference_agent.gnn.md"
DEFAULT_GNN_ROOT = REPO_ROOT.parent / "Generalized_Notation_Notation"

# The headless extractor contract consumed here: gnn.extract returns the
# POMDPStateSpace mapping described by this schema version. Major version 1 is
# required; minor versions may append keys.
REQUIRED_EXTRACT_SCHEMA_MAJOR = "1"

# The kernel's canonical worked example (examples.py::agent_example): the
# informative sensor is the 0.9-precision regime agent.
CANONICAL_SENSOR_PRECISION = 0.9


class ConformanceError(RuntimeError):
    """The specification does not conform to the pinned GNN revision or the kernel."""


class GnnUnavailable(ConformanceError):
    """The pinned GNN checkout or a suitable interpreter is not available."""


@dataclass(frozen=True)
class Pin:
    """The GNN revision this repository's specification is validated against."""

    repository: str
    tag: str
    commit: str


def load_pin(path: Path = PIN_PATH) -> Pin:
    """Read and validate the repository-local GNN pin record."""

    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConformanceError(
            f"{source} is missing; the pinned GNN revision is required to validate "
            "the specification"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ConformanceError(f"{source} is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise ConformanceError(f"{source} must contain a JSON object")
    if data.get("schema") != "gnn-importer-pin/v1":
        raise ConformanceError(
            f"{source}: schema must be 'gnn-importer-pin/v1' "
            f"(got {data.get('schema')!r})"
        )
    try:
        pin = Pin(
            repository=str(data["repository"]),
            tag=str(data["tag"]),
            commit=str(data["commit"]),
        )
    except KeyError as exc:
        raise ConformanceError(f"{source} is missing the {exc} field") from exc
    if len(pin.commit) != 40 or any(c not in "0123456789abcdef" for c in pin.commit):
        raise ConformanceError(
            f"{source}: commit must be a 40-character lowercase hex SHA"
        )
    return pin


def resolve_gnn_root(explicit: Path | str | None = None) -> Path:
    """Return the GNN checkout path (``--gnn-root``, ``GNN_ROOT``, then sibling)."""

    candidates = [explicit, os.environ.get("GNN_ROOT"), DEFAULT_GNN_ROOT]
    for candidate in candidates:
        if not candidate:
            continue
        root = Path(candidate).expanduser().resolve()
        if (root / "src" / "gnn" / "__init__.py").is_file():
            return root
    raise GnnUnavailable(
        "no GNN checkout found; set GNN_ROOT or clone "
        "ActiveInferenceInstitute/Generalized_Notation_Notation next to this "
        f"repository ({DEFAULT_GNN_ROOT})"
    )


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ConformanceError(
            f"git {' '.join(args)} failed in {root}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def verify_pin(root: Path, pin: Pin) -> None:
    """Verify the pinned tag and commit resolve to the same object."""

    commit = _git(root, "rev-parse", "--verify", f"{pin.commit}^{{commit}}")
    if commit != pin.commit:
        raise ConformanceError(f"pinned commit resolves to {commit}, not {pin.commit}")
    tag_commit = _git(root, "rev-parse", "--verify", f"{pin.tag}^{{commit}}")
    if tag_commit != pin.commit:
        raise ConformanceError(
            f"pinned tag {pin.tag} resolves to {tag_commit}, not {pin.commit}"
        )


def pinned_source(root: Path, pin: Pin, destination: Path) -> Path:
    """Extract the pinned ``src/gnn`` tree into ``destination`` and return it."""

    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.Popen(
        ["git", "-C", str(root), "archive", pin.commit, "src/gnn"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    extract = subprocess.run(
        ["tar", "-x", "-C", str(destination)],
        stdin=archive.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    assert archive.stdout is not None
    archive.stdout.close()
    archive_stderr = archive.stderr.read().decode() if archive.stderr else ""
    archive.wait()
    if archive.returncode != 0 or extract.returncode != 0:
        raise ConformanceError(
            f"could not extract pinned GNN source: {archive_stderr.strip()} "
            f"{extract.stderr.strip()}"
        )
    source = destination / "src"
    if not (source / "gnn" / "__init__.py").is_file():
        raise ConformanceError(f"pinned GNN extraction is incomplete at {source}")
    return source


def resolve_interpreter(root: Path) -> Path:
    """Return the Python used to run the pinned extractor.

    ``GNN_PYTHON`` wins; otherwise the GNN checkout's own virtualenv; otherwise
    the interpreter running this module. The headless ``gnn.extract`` path is
    standard-library only for discrete POMDP models, so the fallback is valid
    for this repository's model.
    """

    explicit = os.environ.get("GNN_PYTHON")
    if explicit:
        interpreter = Path(explicit).expanduser()
        if not interpreter.is_file():
            raise GnnUnavailable(f"GNN_PYTHON does not exist: {interpreter}")
        return interpreter
    venv_python = root / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return venv_python
    return Path(sys.executable)


def extract_spec(
    spec: Path = SPEC_PATH,
    gnn_root: Path | str | None = None,
    interpreter: Path | str | None = None,
    pin: Pin | None = None,
) -> dict:
    """Parse ``spec`` with the pinned GNN extractor and return the mapping.

    ``pin`` defaults to this repository's pin record; a caller may pass a pin for
    a scratch checkout (the conformance tests do this to exercise the extraction
    path without the real GNN clone).
    """

    root = resolve_gnn_root(gnn_root)
    active_pin = pin if pin is not None else load_pin()
    verify_pin(root, active_pin)
    python = Path(interpreter) if interpreter else resolve_interpreter(root)
    spec = Path(spec).resolve()
    with tempfile.TemporaryDirectory(prefix="gnn-pinned-") as temporary:
        source = pinned_source(root, active_pin, Path(temporary))
        environment = dict(os.environ)
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            f"{source}{os.pathsep}{existing}" if existing else str(source)
        )
        result = subprocess.run(
            [str(python), "-m", "gnn.extract", str(spec)],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
    if result.returncode != 0:
        raise ConformanceError(
            f"pinned GNN extractor failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    model = json.loads(result.stdout)
    if isinstance(model, dict) and model.get("status") == "error":
        raise ConformanceError(
            f"pinned GNN extractor rejected {spec}: {model['error']}"
        )
    schema = str(model.get("extraction_schema_version", ""))
    if schema.split(".")[0] != REQUIRED_EXTRACT_SCHEMA_MAJOR:
        raise ConformanceError(
            f"unexpected extraction schema version {schema!r}; "
            f"this repository consumes major version {REQUIRED_EXTRACT_SCHEMA_MAJOR}"
        )
    return model


def spec_sha256(spec: Path = SPEC_PATH) -> str:
    """Return the SHA-256 of the specification bytes."""

    return hashlib.sha256(Path(spec).read_bytes()).hexdigest()


def canonical_agent() -> DiscreteActiveInferenceAgent:
    """Return the kernel's canonical sample/commit agent."""

    return two_action_regime_agent(CANONICAL_SENSOR_PRECISION)


def canonical_model(agent: DiscreteActiveInferenceAgent | None = None) -> dict:
    """Build the extractor-shaped mapping for the kernel's canonical model.

    Used by the always-run checks and by tests; the extracted specification must
    match this mapping key by key.
    """

    agent = agent or canonical_agent()
    return {
        "extraction_schema_version": "1.0.0",
        "model_kind": "discrete",
        "num_states": int(agent.A.shape[1]),
        "num_observations": int(agent.A.shape[0]),
        "num_actions": int(agent.B.shape[2]),
        "A_matrix": agent.A.tolist(),
        "B_matrix": agent.B.tolist(),
        "C_vector": agent.C.tolist(),
        "D_vector": agent.D.tolist(),
        "model_parameters": {
            "num_hidden_states": int(agent.A.shape[1]),
            "num_obs": int(agent.A.shape[0]),
            "num_actions": int(agent.B.shape[2]),
            "num_timesteps": 1,
        },
    }


def check_conformance(model: dict) -> list[str]:
    """Check the extracted specification against the kernel.

    Returns the list of passed check names; raises :class:`ConformanceError` on
    the first mismatch.
    """

    agent = canonical_agent()
    passed: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ConformanceError(message)

    require(model.get("model_kind") == "discrete", "model kind must be discrete")
    require(
        (
            int(model["num_states"]),
            int(model["num_observations"]),
            int(model["num_actions"]),
        )
        == (2, 2, 2),
        "the kernel's canonical model is two states, two observations, two actions",
    )
    passed.append("dimensions match the kernel's canonical model (2/2/2)")

    require(
        np.allclose(np.asarray(model["A_matrix"], dtype=float), agent.A),
        "A does not match the kernel's informative sensor",
    )
    passed.append("A matches the kernel's informative sensor (0.9 diagonal)")

    require(
        np.allclose(np.asarray(model["B_matrix"], dtype=float), agent.B),
        "B does not match the kernel's sample/commit transition tensor",
    )
    passed.append("B matches the kernel's sample/commit transitions")

    require(
        np.allclose(np.asarray(model["C_vector"], dtype=float), agent.C),
        "C does not match the kernel's neutral preference vector",
    )
    require(
        np.allclose(np.asarray(model["D_vector"], dtype=float), agent.D),
        "D does not match the kernel's uniform state prior",
    )
    passed.append("C and D match the kernel's neutral preference and uniform prior")

    habit = model.get("E_vector")
    require(
        habit is None or np.allclose(np.asarray(habit, dtype=float), np.full(2, 0.5)),
        "E must be uniform; the kernel has no habit prior",
    )
    passed.append("E is uniform (the kernel has no habit prior)")

    # The declared model, read through the kernel, must reproduce the kernel's
    # own expected-free-energy decomposition for non-trivial beliefs.
    likelihood = np.asarray(model["A_matrix"], dtype=float)
    transitions = np.asarray(model["B_matrix"], dtype=float)
    preferences = np.asarray(model["C_vector"], dtype=float)
    for belief in (agent.infer_states(obs=0), np.array([0.7, 0.3])):
        declared = np.array(
            [
                expected_free_energy(
                    transitions[:, :, action] @ belief, likelihood, preferences
                )[0]
                for action in range(transitions.shape[2])
            ]
        )
        require(
            np.allclose(declared, agent.evaluate_policies(belief)),
            "the declared matrices do not reproduce the kernel's expected free energy",
        )
    passed.append(
        "declared matrices reproduce the kernel's expected-free-energy values"
    )

    return passed


def receipt(model: dict, checks: list[str], spec: Path = SPEC_PATH) -> dict:
    """Build a JSON-serializable receipt for the validation run."""

    pin = load_pin()
    return {
        "spec": str(Path(spec).resolve().relative_to(REPO_ROOT)),
        "spec_sha256": spec_sha256(spec),
        "pin": {"repository": pin.repository, "tag": pin.tag, "commit": pin.commit},
        "extraction_schema_version": model.get("extraction_schema_version"),
        "model_kind": model.get("model_kind"),
        "dimensions": {
            "num_states": model.get("num_states"),
            "num_observations": model.get("num_observations"),
            "num_actions": model.get("num_actions"),
        },
        "checks": checks,
    }
