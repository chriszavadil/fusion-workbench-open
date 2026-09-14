#!/usr/bin/env python3
"""Compare independent FreeGSNKE exports using physical, basis-invariant outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

FREQUENCIES_RAD_PER_S = (0.0, 10.0, 100.0, 300.0, 1000.0, 3000.0)
GROWTH_ABS_TOL = 1.0e-6
TRANSFER_REL_TOL = 1.0e-7
RESIDUE_REL_TOL = 1.0e-6
GEOMETRY_KEYS = (
    "active_coils_sha256",
    "passive_coils_sha256",
    "limiter_sha256",
    "wall_sha256",
    "source_notebook_sha256",
    "freegsnke_commit",
)


def locate(root: Path, filename: str) -> Path:
    matches = list(root.rglob(filename))
    if len(matches) != 1:
        raise SystemExit(f"expected one {filename} below {root}, found {len(matches)}")
    return matches[0]


def load(root: Path) -> tuple[dict[str, np.ndarray], dict]:
    npz_path = locate(root, "freegsnke_mastu_growth_linearization.npz")
    json_path = locate(root, "freegsnke_mastu_growth_linearization.json")
    with np.load(npz_path) as source:
        arrays = {name: np.asarray(source[name]) for name in source.files}
    return arrays, json.loads(json_path.read_text())


def relative(actual: np.ndarray, expected: np.ndarray) -> float:
    return float(np.linalg.norm(actual - expected) / max(np.linalg.norm(expected), 1.0e-30))


def transfer(A: np.ndarray, C: np.ndarray, G: np.ndarray, omega: float) -> np.ndarray:
    operator = (1j * omega) * np.eye(A.shape[0]) - A
    return C @ np.linalg.solve(operator, G)


def unstable_residue(A: np.ndarray, B: np.ndarray, C: np.ndarray) -> tuple[complex, np.ndarray]:
    eigvals, right_vectors = np.linalg.eig(A)
    index = int(np.argmax(np.real(eigvals)))
    lam = complex(eigvals[index])
    right = right_vectors[:, index]

    left_eigvals, left_vectors = np.linalg.eig(A.T.conj())
    left_index = int(np.argmin(np.abs(left_eigvals - np.conj(lam))))
    left = left_vectors[:, left_index]
    overlap = np.vdot(left, right)
    if abs(overlap) < 1.0e-12:
        raise SystemExit("dominant left/right eigenvectors are numerically orthogonal")
    left = left / np.conj(overlap)
    residue = np.outer(C @ right, left.conj().T @ B)
    return lam, residue


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("replicate_a", type=Path)
    parser.add_argument("replicate_b", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    arrays_a, meta_a = load(args.replicate_a)
    arrays_b, meta_b = load(args.replicate_b)

    exact = {
        key: meta_a.get(key) == meta_b.get(key)
        for key in GEOMETRY_KEYS
    }
    exact["state_labels"] = meta_a.get("state_labels") == meta_b.get("state_labels")
    exact["input_labels"] = meta_a.get("input_labels") == meta_b.get("input_labels")

    A_a = arrays_a["A_continuous_per_s"]
    A_b = arrays_b["A_continuous_per_s"]
    B_a = arrays_a["B_active_voltage"]
    B_b = arrays_b["B_active_voltage"]
    E_a = arrays_a["E_profile_rate"]
    E_b = arrays_b["E_profile_rate"]
    C_a = arrays_a["C_RZ_current"]
    C_b = arrays_b["C_RZ_current"]

    growth_a = float(meta_a["dominant_growth_rate_per_s"])
    growth_b = float(meta_b["dominant_growth_rate_per_s"])
    growth_abs = abs(growth_a - growth_b)

    transfer_records = []
    worst_transfer = 0.0
    for omega in FREQUENCIES_RAD_PER_S:
        voltage_error = relative(
            transfer(A_a, C_a, B_a, omega),
            transfer(A_b, C_b, B_b, omega),
        )
        profile_error = relative(
            transfer(A_a, C_a, E_a, omega),
            transfer(A_b, C_b, E_b, omega),
        )
        worst_transfer = max(worst_transfer, voltage_error, profile_error)
        transfer_records.append(
            {
                "frequency_rad_per_s": omega,
                "voltage_RZ_relative_l2": voltage_error,
                "profile_rate_RZ_relative_l2": profile_error,
            }
        )

    lambda_a, residue_a = unstable_residue(A_a, B_a, C_a)
    lambda_b, residue_b = unstable_residue(A_b, B_b, C_b)
    residue_error = relative(residue_a, residue_b)

    passed = (
        all(exact.values())
        and growth_abs <= GROWTH_ABS_TOL
        and worst_transfer <= TRANSFER_REL_TOL
        and residue_error <= RESIDUE_REL_TOL
    )
    result = {
        "schema": "fusion-solution-set.freegsnke-gate2-repeatability.v1",
        "exact_identity_checks": exact,
        "growth_rate_a_per_s": growth_a,
        "growth_rate_b_per_s": growth_b,
        "growth_rate_absolute_difference_per_s": growth_abs,
        "dominant_eigenvalue_a": {"real": lambda_a.real, "imag": lambda_a.imag},
        "dominant_eigenvalue_b": {"real": lambda_b.real, "imag": lambda_b.imag},
        "unstable_RZ_voltage_residue_relative_l2": residue_error,
        "worst_RZ_transfer_relative_l2": worst_transfer,
        "transfer_records": transfer_records,
        "acceptance": {
            "growth_rate_absolute_per_s": GROWTH_ABS_TOL,
            "RZ_transfer_relative_l2": TRANSFER_REL_TOL,
            "unstable_residue_relative_l2": RESIDUE_REL_TOL,
        },
        "passed": passed,
        "claim_boundary": (
            "independent-run linear-model repeatability only; not nonlinear "
            "recovery, experimental MAST-U validation, or reactor safety"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit("Gate 2 independent-run repeatability failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
