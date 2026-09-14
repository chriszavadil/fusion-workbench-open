#!/usr/bin/env python3
"""Gate 2: compare the exported model with FreeGSNKE's implicit-Euler stepper.

This validates a numerical identity, not plasma recovery. The test uses held-out
random states and forcing vectors frozen before execution and includes both
single-step and multi-substep cases.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

SEED = 20260828
TRIALS_PER_CASE = 6
STATE_SIGMA = 1.0e-3
VOLTAGE_SIGMA = 25.0
PROFILE_RATE_SIGMA = 1.0e-2
TIMESTEP_CASES = (
    (1.0e-5, 1.0e-5),
    (1.0e-4, 1.0e-4),
    (5.0e-4, 1.0e-4),
    (1.0e-3, 2.0e-4),
    (3.0e-3, 2.5e-4),
)
UPSTREAM_NATIVE_TOL = 1.0e-11
UPSTREAM_STATE_SPACE_TOL = 1.0e-10


def relative_l2(actual: np.ndarray, expected: np.ndarray) -> float:
    return float(np.linalg.norm(actual - expected) / max(np.linalg.norm(expected), 1.0))


def repeated_native_step(
    M: np.ndarray,
    forcing: np.ndarray,
    x0: np.ndarray,
    full_timestep: float,
    max_internal_timestep: float,
) -> np.ndarray:
    n_steps = math.ceil(full_timestep / max_internal_timestep)
    dt = full_timestep / n_steps
    operator = M + dt * np.eye(M.shape[0])
    x = x0.copy()
    for _ in range(n_steps):
        x = np.linalg.solve(operator, M @ x + dt * forcing)
    return x


def repeated_state_space_step(
    A: np.ndarray,
    forcing: np.ndarray,
    x0: np.ndarray,
    full_timestep: float,
    max_internal_timestep: float,
) -> np.ndarray:
    n_steps = math.ceil(full_timestep / max_internal_timestep)
    dt = full_timestep / n_steps
    operator = np.eye(A.shape[0]) - dt * A
    x = x0.copy()
    for _ in range(n_steps):
        x = np.linalg.solve(operator, x + dt * forcing)
    return x


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from freegsnke.implicit_euler import implicit_euler_solver

    model_dir = args.model_dir.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    arrays = np.load(model_dir / "freegsnke_mastu_growth_linearization.npz")
    metadata = json.loads(
        (model_dir / "freegsnke_mastu_growth_linearization.json").read_text()
    )

    A = np.asarray(arrays["A_continuous_per_s"], dtype=float)
    B = np.asarray(arrays["B_active_voltage"], dtype=float)
    E = np.asarray(arrays["E_profile_rate"], dtype=float)
    M = np.asarray(arrays["Mmatrix_native"], dtype=float)
    F_voltage = np.asarray(arrays["F_voltage_native"], dtype=float)
    F_profile = np.asarray(arrays["F_profile_native"], dtype=float)

    n = A.shape[0]
    if A.shape != (n, n) or M.shape != (n, n):
        raise SystemExit("invalid state matrix dimensions")
    if B.shape[0] != n or F_voltage.shape != B.shape:
        raise SystemExit("invalid active-voltage dimensions")
    if E.shape[0] != n or F_profile.shape != E.shape:
        raise SystemExit("invalid profile-rate dimensions")

    rng = np.random.default_rng(SEED)
    records: list[dict[str, float | int]] = []
    worst_upstream_native = 0.0
    worst_upstream_state_space = 0.0

    for case_index, (full_dt, max_internal_dt) in enumerate(TIMESTEP_CASES):
        upstream = implicit_euler_solver(
            Mmatrix=M,
            Rmatrix=np.eye(n),
            full_timestep=full_dt,
            max_internal_timestep=max_internal_dt,
        )
        n_steps = int(upstream.n_steps)
        for trial in range(TRIALS_PER_CASE):
            x0 = rng.normal(0.0, STATE_SIGMA, size=n)
            voltage = rng.normal(0.0, VOLTAGE_SIGMA, size=B.shape[1])
            profile_rate = rng.normal(0.0, PROFILE_RATE_SIGMA, size=E.shape[1])

            native_forcing = F_voltage @ voltage - F_profile @ profile_rate
            state_space_forcing = B @ voltage + E @ profile_rate

            upstream_result = upstream.full_stepper(x0.copy(), native_forcing)
            native_result = repeated_native_step(
                M, native_forcing, x0, full_dt, max_internal_dt
            )
            state_space_result = repeated_state_space_step(
                A, state_space_forcing, x0, full_dt, max_internal_dt
            )

            err_native = relative_l2(upstream_result, native_result)
            err_state_space = relative_l2(upstream_result, state_space_result)
            worst_upstream_native = max(worst_upstream_native, err_native)
            worst_upstream_state_space = max(worst_upstream_state_space, err_state_space)
            records.append(
                {
                    "case_index": case_index,
                    "trial": trial,
                    "full_timestep_s": full_dt,
                    "max_internal_timestep_s": max_internal_dt,
                    "internal_steps": n_steps,
                    "upstream_vs_native_relative_l2": err_native,
                    "upstream_vs_state_space_relative_l2": err_state_space,
                }
            )

    summary = {
        "schema": "fusion-solution-set.freegsnke-gate2-stepper.v1",
        "seed": SEED,
        "state_dimension": n,
        "active_input_dimension": B.shape[1],
        "profile_rate_dimension": E.shape[1],
        "trials": len(records),
        "source_commit": metadata.get("freegsnke_commit"),
        "freegs4e_version": metadata.get("freegs4e_version"),
        "dominant_growth_rate_per_s": metadata.get("dominant_growth_rate_per_s"),
        "worst_upstream_vs_native_relative_l2": worst_upstream_native,
        "worst_upstream_vs_state_space_relative_l2": worst_upstream_state_space,
        "acceptance": {
            "upstream_vs_native_relative_l2": UPSTREAM_NATIVE_TOL,
            "upstream_vs_state_space_relative_l2": UPSTREAM_STATE_SPACE_TOL,
        },
        "passed": (
            worst_upstream_native <= UPSTREAM_NATIVE_TOL
            and worst_upstream_state_space <= UPSTREAM_STATE_SPACE_TOL
        ),
        "records": records,
        "claim_boundary": (
            "time-discretisation consistency only; not nonlinear recovery, "
            "experimental MAST-U validation, or reactor safety"
        ),
    }
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))
    if not summary["passed"]:
        raise SystemExit("Gate 2 time-step equivalence failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
