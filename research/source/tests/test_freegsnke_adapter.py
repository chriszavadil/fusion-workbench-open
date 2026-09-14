from types import SimpleNamespace
import json

import numpy as np
import pytest

from fusion_vertical_safety.freegsnke_adapter import (
    FreeGSNKEAdapterError,
    export_freegsnke_linearization,
    extract_freegsnke_linearization,
)


def _fake_solver():
    # M xdot + x = F u. One negative M eigenvalue creates one unstable A eigenvalue.
    M = np.diag([0.02, -0.01, 0.05])
    pm1rm1 = np.array([[2.0, 0.0], [0.0, 3.0]])
    forcing_pars = np.array([[0.5], [0.0], [0.25]])
    linear = SimpleNamespace(
        Mmatrix=M,
        Pm1Rm1=pm1rm1,
        n_active_coils=1,
        forcing_pars_matrix=forcing_pars,
        growth_rates=np.array([100.0]),
    )
    return SimpleNamespace(
        linearised_sol=linear,
        coils_order=["PF1", "passive-raw"],
        dRZdI=np.array([[0.1, 0.0, 0.0], [0.0, 2e-5, 1e-7]]),
    )


def test_documented_system_maps_to_continuous_state_space():
    model = extract_freegsnke_linearization(_fake_solver())
    np.testing.assert_allclose(model.A, np.diag([-50.0, 100.0, -20.0]))
    np.testing.assert_allclose(model.B_voltage[:, 0], [100.0, 0.0, 0.0])
    np.testing.assert_allclose(model.E_profile_rate[:, 0], [-25.0, 0.0, -5.0])
    np.testing.assert_allclose(model.M_native, np.diag([0.02, -0.01, 0.05]))
    assert model.dominant_growth_rate_per_s == pytest.approx(100.0)
    assert model.metadata["documented_growth_rate_residual_per_s"] == pytest.approx(0.0)


def test_state_and_input_labels_use_active_coil_names():
    model = extract_freegsnke_linearization(_fake_solver())
    assert model.state_labels == (
        "active_current:PF1:A",
        "passive_normal_mode:0:A",
        "plasma_current:scaled",
    )
    assert model.input_labels == ("active_voltage:PF1:V",)


def test_forcing_sign_matches_upstream_stepper_subtraction():
    solver = _fake_solver()
    model = extract_freegsnke_linearization(solver)
    x = np.array([0.1, -0.2, 0.3])
    u = np.array([4.0])
    theta_dot = np.array([2.0])
    lhs_form = np.linalg.solve(
        solver.linearised_sol.Mmatrix,
        np.r_[solver.linearised_sol.Pm1Rm1[:, :1] @ u, 0.0]
        - x
        - solver.linearised_sol.forcing_pars_matrix @ theta_dot,
    )
    ss_form = model.A @ x + model.B_voltage @ u + model.E_profile_rate @ theta_dot
    np.testing.assert_allclose(lhs_form, ss_form)


def test_export_is_hash_linked_and_machine_claims_remain_disabled(tmp_path):
    npz_path, json_path = export_freegsnke_linearization(
        _fake_solver(),
        tmp_path,
        extra_metadata={"notebook_sha256": "abc"},
    )
    assert npz_path.exists()
    metadata = json.loads(json_path.read_text())
    assert metadata["notebook_sha256"] == "abc"
    assert metadata["machine_claim_allowed"] is False
    assert len(metadata["numeric_bundle_sha256"]) == 64


def test_rejects_incompatible_RZ_jacobian():
    solver = _fake_solver()
    solver.dRZdI = np.zeros((2, 2))
    with pytest.raises(FreeGSNKEAdapterError, match="dRZdI"):
        extract_freegsnke_linearization(solver)


def test_rejects_singular_Mmatrix():
    solver = _fake_solver()
    solver.linearised_sol.Mmatrix[0, 0] = 0.0
    with pytest.raises(FreeGSNKEAdapterError, match="singular"):
        extract_freegsnke_linearization(solver)
