from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_freegsnke_gate2_stepper import (  # noqa: E402
    repeated_native_step,
    repeated_state_space_step,
    relative_l2,
)


def test_native_and_state_space_implicit_euler_are_identical() -> None:
    M = np.array([[2.0, 0.2], [0.2, 1.5]])
    F_voltage = np.array([[1.0], [0.25]])
    F_profile = np.array([[0.1], [0.4]])
    A = np.linalg.solve(M, -np.eye(2))
    B = np.linalg.solve(M, F_voltage)
    E = np.linalg.solve(M, -F_profile)

    x0 = np.array([0.3, -0.2])
    voltage = np.array([4.0])
    profile_rate = np.array([-0.5])
    native_forcing = F_voltage @ voltage - F_profile @ profile_rate
    state_space_forcing = B @ voltage + E @ profile_rate

    native = repeated_native_step(M, native_forcing, x0, 0.03, 0.007)
    state_space = repeated_state_space_step(
        A, state_space_forcing, x0, 0.03, 0.007
    )
    assert relative_l2(native, state_space) < 1.0e-14


def test_multi_substep_partition_uses_exact_full_horizon() -> None:
    M = np.array([[1.7]])
    A = np.linalg.solve(M, -np.eye(1))
    forcing_native = np.array([0.8])
    forcing_state = np.linalg.solve(M, forcing_native)
    x0 = np.array([0.25])

    full = 0.031
    max_internal = 0.007
    native = repeated_native_step(M, forcing_native, x0, full, max_internal)
    state = repeated_state_space_step(A, forcing_state, x0, full, max_internal)
    assert np.allclose(native, state, rtol=0.0, atol=2.0e-16)
