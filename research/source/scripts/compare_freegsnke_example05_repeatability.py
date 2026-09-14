#!/usr/bin/env python3
"""Compare two exact FreeGSNKE example05 reproduction artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

TOLERANCES = {
    "time_arrays_max_absolute_s": 1.0e-15,
    "O_point_RZpsi_max_absolute": 1.0e-10,
    "O_point_RZpsi_relative_l2": 1.0e-9,
    "evolving_currents_max_absolute_native_units": 1.0e-7,
    "evolving_currents_relative_l2": 1.0e-9,
    "shape_scalar_max_absolute": 1.0e-10,
    "shape_scalar_relative_l2": 1.0e-9,
    "timestep_absolute_s": 1.0e-15,
}

TIME_ARRAYS = ("history_times", "history_times_nl")
O_POINT_ARRAYS = ("history_o_points", "history_o_points_nl")
CURRENT_ARRAYS = ("history_currents", "history_currents_nl")
SHAPE_ARRAYS = (
    "history_elongation",
    "history_elongation_nl",
    "history_triangularity",
    "history_triangularity_nl",
    "history_squareness",
    "history_squareness_nl",
    "history_area",
    "history_area_nl",
    "history_length",
    "history_length_nl",
)
ALL_ARRAYS = TIME_ARRAYS + O_POINT_ARRAYS + CURRENT_ARRAYS + SHAPE_ARRAYS


def relative_l2(a: np.ndarray, b: np.ndarray) -> float:
    denominator = max(float(np.linalg.norm(a)), float(np.linalg.norm(b)), 1.0e-300)
    return float(np.linalg.norm(a - b) / denominator)


def locate(root: Path) -> Path:
    candidates = list(root.rglob("execution_summary.json"))
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one execution_summary.json in {root}, got {candidates}")
    return candidates[0].parent


def load(root: Path) -> tuple[dict[str, Any], dict[str, np.ndarray], Path]:
    execution = locate(root)
    summary = json.loads((execution / "execution_summary.json").read_text())
    with np.load(execution / "audit_histories.npz") as archive:
        arrays = {name: np.asarray(archive[name]) for name in archive.files}
    return summary, arrays, execution


def max_abs(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.max(np.abs(left - right))) if left.size else 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    ls, left, ld = load(args.left)
    rs, right, rd = load(args.right)
    checks: dict[str, bool] = {}
    metrics: dict[str, float] = {}

    exact_fields = (
        "freegsnke_commit",
        "original_cell_count",
        "executed_cell_count",
        "original_cell_source_sha256",
        "executed_original_cell_source_sha256",
        "state_dimension",
        "linear_history_length",
        "nonlinear_history_length",
    )
    for field in exact_fields:
        checks[f"exact_summary_{field}"] = ls.get(field) == rs.get(field)

    for name in ALL_ARRAYS:
        checks[f"array_present_{name}"] = name in left and name in right
        checks[f"array_shape_{name}"] = (
            name in left and name in right and left[name].shape == right[name].shape
        )

    timestep_difference = abs(float(ls["dt_step_s"]) - float(rs["dt_step_s"]))
    metrics["timestep_absolute_s"] = timestep_difference
    checks["timestep_within_tolerance"] = (
        timestep_difference <= TOLERANCES["timestep_absolute_s"]
    )

    for name in TIME_ARRAYS:
        value = max_abs(left[name], right[name])
        metrics[f"{name}_max_absolute_s"] = value
        checks[f"{name}_within_tolerance"] = (
            value <= TOLERANCES["time_arrays_max_absolute_s"]
        )

    for name in O_POINT_ARRAYS:
        absolute = max_abs(left[name], right[name])
        relative = relative_l2(left[name], right[name])
        metrics[f"{name}_max_absolute"] = absolute
        metrics[f"{name}_relative_l2"] = relative
        checks[f"{name}_max_within_tolerance"] = (
            absolute <= TOLERANCES["O_point_RZpsi_max_absolute"]
        )
        checks[f"{name}_relative_within_tolerance"] = (
            relative <= TOLERANCES["O_point_RZpsi_relative_l2"]
        )

    for name in CURRENT_ARRAYS:
        absolute = max_abs(left[name], right[name])
        relative = relative_l2(left[name], right[name])
        metrics[f"{name}_max_absolute"] = absolute
        metrics[f"{name}_relative_l2"] = relative
        checks[f"{name}_max_within_tolerance"] = (
            absolute <= TOLERANCES["evolving_currents_max_absolute_native_units"]
        )
        checks[f"{name}_relative_within_tolerance"] = (
            relative <= TOLERANCES["evolving_currents_relative_l2"]
        )

    for name in SHAPE_ARRAYS:
        absolute = max_abs(left[name], right[name])
        relative = relative_l2(left[name], right[name])
        metrics[f"{name}_max_absolute"] = absolute
        metrics[f"{name}_relative_l2"] = relative
        checks[f"{name}_max_within_tolerance"] = (
            absolute <= TOLERANCES["shape_scalar_max_absolute"]
        )
        checks[f"{name}_relative_within_tolerance"] = (
            relative <= TOLERANCES["shape_scalar_relative_l2"]
        )

    passed = all(checks.values())
    result = {
        "schema": "fusion-solution-set.freegsnke-example05-repeatability.v1",
        "pass": passed,
        "tolerances": TOLERANCES,
        "metrics": metrics,
        "checks": checks,
        "left_execution_directory": str(ld),
        "right_execution_directory": str(rd),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
