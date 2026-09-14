"""Strict adapter for the documented FreeGSNKE linearised circuit API.

FreeGSNKE v3.0.1 constructs the retained coupled circuit/plasma system as

    M x_dot + x = F_voltage u - F_profile theta_dot.

Consequently

    A = -M^{-1},
    B = M^{-1} F_voltage,
    E = -M^{-1} F_profile.

The adapter is intentionally duck typed. Unit tests can verify signs and
shapes without importing FreeGSNKE, while a connected CI run applies the same
code to an exact tag/commit and records provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import json

import numpy as np

PINNED_FREEGSNKE_VERSION = "3.0.1"
PINNED_FREEGSNKE_COMMIT = "f776e908c8c333411f9824cbcfed674fafff8dfd"


class FreeGSNKEAdapterError(ValueError):
    """Raised when a solver object violates the frozen export contract."""


@dataclass(frozen=True)
class FreeGSNKELinearization:
    """Continuous-time state-space model plus native matrices and provenance."""

    A: np.ndarray
    B_voltage: np.ndarray
    E_profile_rate: np.ndarray | None
    C_RZ_current: np.ndarray | None
    M_native: np.ndarray
    F_voltage_native: np.ndarray
    F_profile_native: np.ndarray | None
    state_labels: tuple[str, ...]
    input_labels: tuple[str, ...]
    dominant_growth_rate_per_s: float
    unstable_eigenvalues_per_s: np.ndarray
    metadata: dict[str, Any]


def _array(obj: Any, name: str, *, ndim: int | None = None) -> np.ndarray:
    if not hasattr(obj, name):
        raise FreeGSNKEAdapterError(f"missing documented attribute: {name}")
    out = np.asarray(getattr(obj, name), dtype=float)
    if ndim is not None and out.ndim != ndim:
        raise FreeGSNKEAdapterError(f"{name} must have ndim={ndim}, found {out.ndim}")
    if not np.all(np.isfinite(out)):
        raise FreeGSNKEAdapterError(f"{name} contains non-finite values")
    return out


def _labels(
    nonlinear_solver: Any,
    n: int,
    n_active: int,
    state_labels: Sequence[str] | None,
    input_labels: Sequence[str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if state_labels is None:
        active_names = tuple(
            str(name) for name in getattr(nonlinear_solver, "coils_order", ())[:n_active]
        )
        if len(active_names) != n_active:
            active_names = tuple(f"active_coil_{i}" for i in range(n_active))
        n_passive = n - n_active - 1
        state_labels = (
            *(f"active_current:{name}:A" for name in active_names),
            *(f"passive_normal_mode:{i}:A" for i in range(n_passive)),
            "plasma_current:scaled",
        )
    if input_labels is None:
        active_from_states = [label.split(":", 2)[1] for label in state_labels[:n_active]]
        input_labels = tuple(f"active_voltage:{name}:V" for name in active_from_states)
    if len(state_labels) != n:
        raise FreeGSNKEAdapterError("state_labels length does not match state dimension")
    if len(input_labels) != n_active:
        raise FreeGSNKEAdapterError("input_labels length does not match active inputs")
    return tuple(state_labels), tuple(input_labels)


def extract_freegsnke_linearization(
    nonlinear_solver: Any,
    *,
    state_labels: Sequence[str] | None = None,
    input_labels: Sequence[str] | None = None,
    source_version: str = PINNED_FREEGSNKE_VERSION,
    source_commit: str = PINNED_FREEGSNKE_COMMIT,
    extra_metadata: Mapping[str, Any] | None = None,
) -> FreeGSNKELinearization:
    """Extract a continuous-time model from ``freegsnke.nonlinear_solve.nl_solver``.

    The function does not silently repair missing data. A malformed or
    ambiguous object is rejected before any machine-level claim can be made.
    """
    if not hasattr(nonlinear_solver, "linearised_sol"):
        raise FreeGSNKEAdapterError("solver is missing linearised_sol")
    linear = nonlinear_solver.linearised_sol

    M = _array(linear, "Mmatrix", ndim=2)
    if M.shape[0] != M.shape[1] or M.shape[0] < 2:
        raise FreeGSNKEAdapterError(f"Mmatrix must be square with size >=2, found {M.shape}")
    n = M.shape[0]
    if np.linalg.matrix_rank(M) != n:
        raise FreeGSNKEAdapterError("Mmatrix is singular")

    Pm1Rm1 = _array(linear, "Pm1Rm1", ndim=2)
    n_active = int(getattr(linear, "n_active_coils", -1))
    if not (0 < n_active <= Pm1Rm1.shape[1]):
        raise FreeGSNKEAdapterError("invalid n_active_coils/Pm1Rm1 combination")
    if Pm1Rm1.shape[0] != n - 1:
        raise FreeGSNKEAdapterError(
            "Pm1Rm1 rows must equal state dimension minus the plasma-current state"
        )

    F_voltage = np.zeros((n, n_active), dtype=float)
    F_voltage[:-1, :] = Pm1Rm1[:, :n_active]

    A = np.linalg.solve(M, -np.eye(n))
    B_voltage = np.linalg.solve(M, F_voltage)

    forcing_pars_value = getattr(linear, "forcing_pars_matrix", None)
    F_profile: np.ndarray | None
    E_profile_rate: np.ndarray | None
    if forcing_pars_value is None:
        F_profile = None
        E_profile_rate = None
    else:
        F_profile = np.asarray(forcing_pars_value, dtype=float)
        if F_profile.ndim != 2 or F_profile.shape[0] != n:
            raise FreeGSNKEAdapterError("forcing_pars_matrix has incompatible shape")
        if not np.all(np.isfinite(F_profile)):
            raise FreeGSNKEAdapterError("forcing_pars_matrix contains non-finite values")
        E_profile_rate = np.linalg.solve(M, -F_profile)

    C_RZ: np.ndarray | None = None
    dRZdI = getattr(nonlinear_solver, "dRZdI", None)
    if dRZdI is not None:
        C_RZ = np.asarray(dRZdI, dtype=float)
        if C_RZ.shape != (2, n):
            raise FreeGSNKEAdapterError(
                f"dRZdI must be shape (2, {n}) after mode selection; found {C_RZ.shape}"
            )
        if not np.all(np.isfinite(C_RZ)):
            raise FreeGSNKEAdapterError("dRZdI contains non-finite values")

    eig = np.linalg.eigvals(A)
    unstable = eig[np.real(eig) > 0.0]
    dominant = float(np.max(np.real(eig)))

    state_labels_out, input_labels_out = _labels(
        nonlinear_solver, n, n_active, state_labels, input_labels
    )

    documented_growth = np.asarray(getattr(linear, "growth_rates", []), dtype=float).reshape(-1)
    growth_residual: float | None = None
    if documented_growth.size and unstable.size:
        growth_residual = float(
            abs(np.max(np.real(unstable)) - np.max(np.real(documented_growth)))
        )

    metadata: dict[str, Any] = {
        "source": "FreeGSNKE documented linearised circuit API",
        "source_version": source_version,
        "source_commit": source_commit,
        "state_equation": "M x_dot + x = F_voltage u - F_profile theta_dot",
        "state_dimension": n,
        "active_input_dimension": n_active,
        "has_RZ_output_jacobian": C_RZ is not None,
        "documented_growth_rate_residual_per_s": growth_residual,
        "matrix_condition_number_2": float(np.linalg.cond(M)),
        "validation_level": 0,
        "machine_claim_allowed": False,
        "experimental_claim_allowed": False,
    }
    if extra_metadata:
        metadata.update(dict(extra_metadata))

    return FreeGSNKELinearization(
        A=A,
        B_voltage=B_voltage,
        E_profile_rate=E_profile_rate,
        C_RZ_current=C_RZ,
        M_native=M.copy(),
        F_voltage_native=F_voltage,
        F_profile_native=None if F_profile is None else F_profile.copy(),
        state_labels=state_labels_out,
        input_labels=input_labels_out,
        dominant_growth_rate_per_s=dominant,
        unstable_eigenvalues_per_s=unstable,
        metadata=metadata,
    )


def export_freegsnke_linearization(
    nonlinear_solver: Any,
    output_dir: str | Path,
    *,
    extra_metadata: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    """Write a compressed numeric bundle and human-readable metadata JSON."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model = extract_freegsnke_linearization(
        nonlinear_solver,
        extra_metadata=extra_metadata,
    )

    npz_path = output / "freegsnke_mastu_growth_linearization.npz"
    json_path = output / "freegsnke_mastu_growth_linearization.json"
    np.savez_compressed(
        npz_path,
        A_continuous_per_s=model.A,
        B_active_voltage=model.B_voltage,
        E_profile_rate=(
            np.empty((model.A.shape[0], 0))
            if model.E_profile_rate is None
            else model.E_profile_rate
        ),
        C_RZ_current=(
            np.empty((0, model.A.shape[0]))
            if model.C_RZ_current is None
            else model.C_RZ_current
        ),
        Mmatrix_native=model.M_native,
        F_voltage_native=model.F_voltage_native,
        F_profile_native=(
            np.empty((model.A.shape[0], 0))
            if model.F_profile_native is None
            else model.F_profile_native
        ),
        unstable_eigenvalues_per_s=model.unstable_eigenvalues_per_s,
    )

    numeric_sha = hashlib.sha256(npz_path.read_bytes()).hexdigest()
    serializable = dict(model.metadata)
    serializable.update(
        {
            "state_labels": list(model.state_labels),
            "input_labels": list(model.input_labels),
            "dominant_growth_rate_per_s": model.dominant_growth_rate_per_s,
            "unstable_eigenvalues_per_s": [
                {"real": float(np.real(value)), "imag": float(np.imag(value))}
                for value in model.unstable_eigenvalues_per_s
            ],
            "numeric_bundle_sha256": numeric_sha,
        }
    )
    json_path.write_text(json.dumps(serializable, indent=2, sort_keys=True) + "\n")
    return npz_path, json_path
