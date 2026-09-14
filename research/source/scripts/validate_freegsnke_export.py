#!/usr/bin/env python3
"""Fail closed when a connected FreeGSNKE export violates its contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

PINNED_COMMIT = "f776e908c8c333411f9824cbcfed674fafff8dfd"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output
    npz_path = output / "freegsnke_mastu_growth_linearization.npz"
    metadata_path = output / "freegsnke_mastu_growth_linearization.json"
    run_path = output / "run_record.json"

    data = np.load(npz_path)
    metadata = json.loads(metadata_path.read_text())
    run = json.loads(run_path.read_text())

    A = data["A_continuous_per_s"]
    B = data["B_active_voltage"]
    M = data["Mmatrix_native"]
    F = data["F_voltage_native"]
    C = data["C_RZ_current"]

    n = A.shape[0]
    assert A.shape == (n, n)
    assert M.shape == (n, n)
    assert B.shape[0] == n and B.shape[1] > 0
    assert F.shape == B.shape
    assert C.shape == (2, n)
    np.testing.assert_allclose(M @ A, -np.eye(n), rtol=1e-10, atol=1e-10)
    np.testing.assert_allclose(M @ B, F, rtol=1e-10, atol=1e-10)

    eig = np.linalg.eigvals(A)
    dominant = float(np.max(np.real(eig)))
    assert dominant > 0.0, "frozen example is expected to contain an unstable mode"
    assert abs(dominant - metadata["dominant_growth_rate_per_s"]) <= max(
        1e-8, 1e-10 * abs(dominant)
    )
    residual = metadata.get("documented_growth_rate_residual_per_s")
    assert residual is not None
    assert residual <= max(1e-8, 1e-10 * abs(dominant))

    actual_sha = hashlib.sha256(npz_path.read_bytes()).hexdigest()
    assert actual_sha == metadata["numeric_bundle_sha256"]
    assert metadata["source_commit"] == PINNED_COMMIT
    assert run["freegsnke_commit"] == PINNED_COMMIT
    assert metadata["machine_claim_allowed"] is False
    assert metadata["experimental_claim_allowed"] is False
    assert metadata["experimental_shot_provenance"] is None

    report = {
        "status": "PASS",
        "state_dimension": n,
        "active_input_dimension": B.shape[1],
        "dominant_growth_rate_per_s": dominant,
        "matrix_condition_number_2": metadata["matrix_condition_number_2"],
        "numeric_bundle_sha256": actual_sha,
        "claim_scope": "machine-derived public MAST-U-like configuration; not experimental",
    }
    (output / "VALIDATION_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
