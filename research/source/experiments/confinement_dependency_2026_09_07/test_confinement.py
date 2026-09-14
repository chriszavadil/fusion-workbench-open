"""Focused tests for implemented decisions; no experimental-validation claim."""
from pathlib import Path
from types import SimpleNamespace
import json,sys,math
import pytest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from run_case import extract_seed,identifiers
from run_warm_fixed_process import parse
from min_h_objective import minimum_hfact
@pytest.fixture(scope='module')
def result():return json.loads((HERE/'VALIDATION.json').read_text())
def case(result,name):return next(r for r in result['results'] if r['case']==name)
@pytest.mark.parametrize('name',['H11_bridge','H_min_inverse','H103_native_validation'])
def test_numerical_constraints_and_crosschecks(result,name):
    r=case(result,name)
    assert r['classification']=='numerically_converged'
    assert len(r['equalities'])==3 and len(r['inequality_residuals'])==24
    assert r['max_abs_equality_residual']<1e-7 and r['most_negative_inequality_residual']>-1e-7
    assert abs(r['fatigue_integrator_difference_cycles'])<.001
    assert r['RK45_fatigue_cycles']>=r['duty_cycles']-.001
    assert abs(r['independent_pulse_energy_error_kWh'])<1e-5
    assert abs(r['independent_profile_balance_error_MW'])<1e-7
    assert abs(r['gross_thermal_identity_error_MW'])<1e-7
    assert r['independent_average_MW']==pytest.approx(r['conditional_average_MW'],abs=1e-7)
    assert r['CS_start_current_critical_ratio']<.7+1e-7 and r['TF_operating_critical_ratio']<.7+1e-7
@pytest.mark.parametrize('name',['H1_direct','H1_continued'])
def test_failed_cases_do_not_claim_power(result,name):
    r=case(result,name);assert r['classification']=='solver_not_converged'
    assert r['conditional_average_MW'] is None and r['max_abs_equality_residual']>.01
def test_all_constraints_and_variables_retained(result):
    assert all(r['same_constraint_identifiers'] and r['same_variable_identifiers'] for r in result['results'])
def test_inverse_objective_applied(result):
    r=case(result,'H_min_inverse')
    assert r['printed_objective']==pytest.approx(r['values']['hfact'],abs=1e-12)
    assert r['values']['rmajor']==pytest.approx(9.,abs=1e-7)
    assert 1.02<r['values']['hfact']<1.04
def test_native_objective_restored(result):
    r=case(result,'H103_native_validation')
    assert r['printed_objective']==pytest.approx(.2*r['values']['rmajor'],abs=1e-12)
    assert r['values']['hfact']<=1.03+1e-7
def test_warm_seed_uses_names_not_positions():
    p=HERE/'H11_bridge/case_MFILE.DAT';s=extract_seed(p);v=parse(p)
    assert len(s)==20
    assert s['j_cs_flat_top_end']==pytest.approx(v['j_cs_flat_top_end'])
    assert s['j_cs_flat_top_end']!=v['itvar020']
    assert 'f_nd_alpha_thermal_electron' in s and 'f_nd_alpha_electron' not in s
def test_multiplier_is_not_relabelled_global_experiment(result):
    assert result['not_a_global_certificate'] and result['not_new_thermal_or_TBR_model']
    assert all(r['values']['i_rad_loss']==1 for r in result['results'])
def test_objective_does_not_depend_on_radius():
    d=SimpleNamespace(physics=SimpleNamespace(hfact=1.03,rmajor=9))
    assert minimum_hfact(1,d)==1.03;d.physics.rmajor=8;assert minimum_hfact(1,d)==1.03
@pytest.mark.parametrize('h',[0,-1,math.nan,math.inf])
def test_invalid_objective_value(h):
    with pytest.raises(ValueError):minimum_hfact(1,SimpleNamespace(physics=SimpleNamespace(hfact=h)))
def test_invalid_objective_slot():
    with pytest.raises(ValueError):minimum_hfact(-1,SimpleNamespace(physics=SimpleNamespace(hfact=1)))
def test_warnings_and_deviation_not_hidden(result):
    assert result['source_clean'] and 'overwrote initial hfact' in result['inverse_initialization_deviation']
    assert abs(case(result,'H103_native_validation')['extra_power_warning_MW'])>.1
