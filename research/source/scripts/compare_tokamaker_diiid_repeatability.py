#!/usr/bin/env python3
"""Compare two frozen TokaMaker DIII-D reproduction artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

TOLERANCES = {
    "dominant_growth_absolute_per_s": 1.0e-6,
    "timestep_cross_run_absolute_s": 1.0e-15,
    "timestep_identity_relative_each_run": 1.0e-12,
    "times_max_absolute_s": 1.0e-15,
    "relative_axis_Z_max_absolute_m": 1.0e-9,
    "relative_axis_Z_relative_l2": 1.0e-8,
    "unstable_mode_projection_relative_l2": 1.0e-8,
    "unstable_mode_projection_max_absolute": 1.0e-8,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    arrays_path = execution / "audit_numeric_arrays.npz"
    with np.load(arrays_path) as archive:
        arrays = {name: np.asarray(archive[name]) for name in archive.files}
    return summary, arrays, execution


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    left_summary, left, left_dir = load(args.left)
    right_summary, right, right_dir = load(args.right)
    checks: dict[str, Any] = {}

    exact_summary_fields = (
        "original_cell_count",
        "executed_cell_count",
        "original_cell_source_sha256",
        "executed_original_cell_source_sha256",
        "time_history_length",
        "z_history_shape",
        "eigenmode_history_shape",
    )
    for field in exact_summary_fields:
        checks[f"exact_summary_{field}"] = left_summary.get(field) == right_summary.get(field)

    required_arrays = ("growth_rates", "times", "z_hist", "eig_hist")
    for name in required_arrays:
        checks[f"array_present_{name}"] = name in left and name in right
        checks[f"array_shape_{name}"] = (
            name in left and name in right and left[name].shape == right[name].shape
        )

    growth_difference = abs(
        float(left_summary["dominant_growth_rate_full_precision_per_s"])
        - float(right_summary["dominant_growth_rate_full_precision_per_s"])
    )
    dt_difference = abs(
        float(left_summary["official_timestep_s"])
        - float(right_summary["official_timestep_s"])
    )
    times_max_abs = float(np.max(np.abs(left["times"] - right["times"])))
    z_max_abs = float(np.max(np.abs(left["z_hist"][:, 1] - right["z_hist"][:, 1])))
    z_rel_l2 = relative_l2(left["z_hist"][:, 1], right["z_hist"][:, 1])
    eig_max_abs = float(np.max(np.abs(left["eig_hist"][:, 1] - right["eig_hist"][:, 1])))
    eig_rel_l2 = relative_l2(left["eig_hist"][:, 1], right["eig_hist"][:, 1])

    metrics = {
        "dominant_growth_absolute_per_s": growth_difference,
        "timestep_cross_run_absolute_s": dt_difference,
        "times_max_absolute_s": times_max_abs,
        "relative_axis_Z_max_absolute_m": z_max_abs,
        "relative_axis_Z_relative_l2": z_rel_l2,
        "unstable_mode_projection_max_absolute": eig_max_abs,
        "unstable_mode_projection_relative_l2": eig_rel_l2,
        "left_timestep_identity_relative": float(left_summary["timestep_relative_error"]),
        "right_timestep_identity_relative": float(right_summary["timestep_relative_error"]),
    }

    checks.update(
        {
            "growth_within_tolerance": growth_difference <= TOLERANCES["dominant_growth_absolute_per_s"],
            "timestep_cross_run_within_tolerance": dt_difference <= TOLERANCES["timestep_cross_run_absolute_s"],
            "left_timestep_identity_within_tolerance": metrics["left_timestep_identity_relative"] <= TOLERANCES["timestep_identity_relative_each_run"],
            "right_timestep_identity_within_tolerance": metrics["right_timestep_identity_relative"] <= TOLERANCES["timestep_identity_relative_each_run"],
            "times_within_tolerance": times_max_abs <= TOLERANCES["times_max_absolute_s"],
            "axis_Z_max_within_tolerance": z_max_abs <= TOLERANCES["relative_axis_Z_max_absolute_m"],
            "axis_Z_relative_l2_within_tolerance": z_rel_l2 <= TOLERANCES["relative_axis_Z_relative_l2"],
            "mode_max_within_tolerance": eig_max_abs <= TOLERANCES["unstable_mode_projection_max_absolute"],
            "mode_relative_l2_within_tolerance": eig_rel_l2 <= TOLERANCES["unstable_mode_projection_relative_l2"],
        }
    )

    generated_hashes = []
    for root in (args.left, args.right):
        candidates = list(root.rglob("official-generated/g192185_tokamaker"))
        generated_hashes.append(sha256_file(candidates[0]) if len(candidates) == 1 else None)

    passed = all(bool(value) for value in checks.values())
    result = {
        "schema": "fusion-solution-set.tokamaker-diiid-repeatability.v1",
        "pass": passed,
        "tolerances": TOLERANCES,
        "metrics": metrics,
        "checks": checks,
        "non_gating": {
            "generated_gEQDSK_hashes": generated_hashes,
            "generated_gEQDSK_hash_equal": generated_hashes[0] == generated_hashes[1],
            "left_executed_notebook_sha256": left_summary.get("executed_notebook_sha256"),
            "right_executed_notebook_sha256": right_summary.get("executed_notebook_sha256"),
            "left_directory": str(left_dir),
            "right_directory": str(right_dir),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
