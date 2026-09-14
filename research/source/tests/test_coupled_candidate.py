from pathlib import Path
import hashlib
import json
import math
import os
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_coupled_candidate as a

@pytest.fixture(scope='module')
def baseline():
    path=os.environ.get('FUSION_POWER_ARCHIVE')
    if not path:pytest.skip('Set FUSION_POWER_ARCHIVE to the original ZIP')
    return a.load_baseline(Path(path))[0]

@pytest.fixture(scope='module')
def result():
    path=os.environ.get('FUSION_POWER_ARCHIVE')
    if not path:pytest.skip('Set FUSION_POWER_ARCHIVE to the original ZIP')
    return a.audit(Path(path))


def test_wrong_hash_rejected(tmp_path):
    p=tmp_path/'input.zip';p.write_bytes(b'wrong archive')
    with pytest.raises(ValueError,match='hash'):a.load_baseline(p)


def test_original_gross_heat_balance(baseline):
    v=baseline
    assert v['p_plant_electric_gross_mw']==pytest.approx(v['eta_turbine']*v['p_plant_primary_heat_mw'],abs=1e-9)


def test_original_energy_identity(baseline):
    x=a.power_case(baseline,.5,baseline['p_fw_blkt_coolant_pump_mw'],1800.)
    assert x['pulse_energy_kwh']==pytest.approx(baseline['e_plant_net_electric_pulse_kwh'],abs=1e-6)


def test_previous_candidate_reproduced(result):
    assert result['power']['prior_candidate_reproduced']['availability_adjusted_net_mw']==pytest.approx(406.5346839749318,abs=1e-9)


def test_recovered_pump_heat_removed(baseline):
    old=a.power_case(baseline,pump_heat_feedback=False);new=a.power_case(baseline)
    delta=baseline['p_fw_blkt_coolant_pump_mw']-new['pump_mechanical_mw_assumed']
    assert old['gross_flat_top_mw']-new['gross_flat_top_mw']==pytest.approx(.4*delta,abs=1e-10)
    assert old['availability_adjusted_net_mw']-new['availability_adjusted_net_mw']==pytest.approx(.4*delta*new['availability_weighted_on_fraction'],abs=1e-10)

@pytest.mark.parametrize('p',[0.,40.,80.,160.,240.])
def test_pump_savings_conservation_formula(baseline,p):
    v=baseline;x=a.power_case(v,.5,p);y=a.power_case(v,.5,v['p_fw_blkt_coolant_pump_mw'])
    delta=(v['p_fw_blkt_coolant_pump_mw']-p)*(1/x['pump_efficiency']-x['turbine_efficiency_assumed'])
    assert x['flat_top_net_mw']-y['flat_top_net_mw']==pytest.approx(delta,abs=1e-9)


def test_corrected_candidate_below_target(result):
    assert result['power']['corrected_same_pump_assumption']['availability_adjusted_net_mw']==pytest.approx(369.6473883939998,abs=1e-9)


def test_ec_requirement_is_a_root(baseline,result):
    ec=result['power']['required_EC_efficiency_at_400MW']
    assert .70<ec<.71
    assert a.power_case(baseline,ec)['availability_adjusted_net_mw']==pytest.approx(400.,abs=1e-8)


def test_turbine_requirement_is_a_root(baseline,result):
    eta=result['power']['required_turbine_efficiency_at_EC60']
    assert a.power_case(baseline,turbine_eff=eta)['availability_adjusted_net_mw']==pytest.approx(400.,abs=1e-8)


def test_pump_requirement_is_a_root(baseline,result):
    pump=result['power']['maximum_pump_mechanical_MW_at_EC60']
    assert a.power_case(baseline,pump_mech_mw=pump)['availability_adjusted_net_mw']==pytest.approx(400.,abs=1e-8)


def test_heat_scaling_fixed_point(baseline,result):
    x=result['power']['self_consistent_pump_heat_scaling_alternative'];p=x['pump_mechanical_mw_assumed']
    q=baseline['p_fw_blkt_heat_deposited_mw']-baseline['p_fw_blkt_coolant_pump_mw']+p
    assert p==pytest.approx(.0375*q,abs=1e-10)


def test_exact_running_load_penalty(baseline):
    x=a.power_case(baseline);y=a.power_case(baseline,extra_running_load_mw=20.)
    assert x['availability_adjusted_net_mw']-y['availability_adjusted_net_mw']==pytest.approx(20*x['availability_weighted_on_fraction'],abs=1e-10)

@pytest.mark.parametrize('kw',[{'ec_eff':0},{'ec_eff':1.1},{'pump_mech_mw':-1},{'dwell_s':-1},{'availability':0}, {'availability':1.01},{'turbine_eff':float('nan')},{'primary_nonpump_heat_fraction':-1}])
def test_invalid_power_input_rejected(baseline,kw):
    with pytest.raises(ValueError):a.power_case(baseline,**kw)


def test_native_fatigue_matches_authentic_mfile(result,baseline):
    assert result['fatigue']['cases']['baseline']['native']['cycles']==pytest.approx(baseline['n_cycle'],abs=1e-8)

@pytest.mark.parametrize('name',['baseline','prior_candidate'])
def test_fatigue_two_integrators_agree(result,name):
    case=result['fatigue']['cases'][name]
    assert abs(case['DOP853']['cycles']-case['RK45']['cycles'])<1e-4

@pytest.mark.parametrize('name',['baseline','prior_candidate'])
def test_euler_refinement_towards_event_solution(result,name):
    case=result['fatigue']['cases'][name];n=case['DOP853']['cycles']
    errors=[abs(x['cycles']-n) for x in case['Euler_refinement']]
    assert all(x>y for x,y in zip(errors,errors[1:]))
    assert errors[-1]/errors[0]<.02


def test_prior_candidate_does_not_clear_20000(result):
    assert result['fatigue']['cases']['prior_candidate']['DOP853']['cycles']<20000


def test_radial_limit_is_event_not_overshot(result):
    case=result['fatigue']['cases']['baseline'];x=case['DOP853']
    assert x['termination']=='radial_crack'
    assert x['final_c_m']==pytest.approx(case['input']['conduit_m']/2,abs=1e-12)
    assert x['final_max_K']<200/1.5


def test_tolerance_refinement():
    x=a.fatigue(293.95,.009813,rtol=1e-8);y=a.fatigue(293.95,.009813,rtol=1e-11)
    assert x['cycles']==pytest.approx(y['cycles'],abs=1e-3)


def test_fatigue_stress_threshold(result):
    stress=result['fatigue']['fixed_conduit_max_stress_for_20000_cycles_mpa']
    assert a.fatigue(stress,.009813)['cycles']==pytest.approx(20000,abs=.001)


def test_mission_cycle_arithmetic(result,baseline):
    f=result['fatigue'];cycle=result['power']['corrected_same_pump_assumption']['cycle_s']
    assert f['cycles_for_30y_no_replacement']==pytest.approx(.8*a.YEAR_S*baseline['life_plant']/cycle,abs=1e-8)
    assert f['cycles_for_30y_no_replacement']>85000


def test_replacement_zero_penalty(result):
    rows=result['fatigue']['replacement_downtime_sensitivities']
    assert rows[0]['long_run_average_net_mw']==result['power']['corrected_same_pump_assumption']['availability_adjusted_net_mw']
    assert all(x['long_run_average_net_mw']>y['long_run_average_net_mw'] for x,y in zip(rows,rows[1:]))


def test_fatigue_specialization_rejects_other_branch():
    with pytest.raises(ValueError,match='a<=c'):a.stress_intensity_endpoints(200,.01,.003,.002)


def test_stress_intensity_linear_in_stress():
    x=np.array(a.stress_intensity_endpoints(200,.01,.00089,.00267));y=np.array(a.stress_intensity_endpoints(400,.01,.00089,.00267))
    assert np.allclose(2*x,y,rtol=1e-13,atol=0)


def test_fuel_perfect_return_and_delivery():
    x=a.fuel_loss_budget(.02,10,1,1,0)
    assert x['minimum_TBR_ignoring_decay']==1
    assert x['passes_necessary_mass_balance']


def test_puffing_amplifies_loss_budget():
    core=a.fuel_loss_budget(.02,0,1.15,.99,.0005);puff=a.fuel_loss_budget(.02,10,1.15,.99,.0005)
    assert core['passes_necessary_mass_balance'] and not puff['passes_necessary_mass_balance']
    assert puff['exhaust_flow_per_burned_flow']==549
    assert puff['minimum_TBR_ignoring_decay']==pytest.approx(1.2873737373737373)


def test_required_recycling_boundary():
    x=a.fuel_loss_budget(.02,10,1.15,.99,.0005);loss=x['maximum_recycle_loss_ignoring_decay']
    y=a.fuel_loss_budget(.02,10,1.15,.99,loss)
    assert y['minimum_TBR_ignoring_decay']==pytest.approx(1.15,abs=1e-12)


def test_no_exhaust_has_no_recycle_requirement():
    x=a.fuel_loss_budget(1,0,1.15,.99,.9)
    assert x['exhaust_flow_per_burned_flow']==0
    assert x['maximum_recycle_loss_ignoring_decay'] is None

@pytest.mark.parametrize('b,g,t,e,l',[(0,1,1.15,.99,0),(.02,-1,1.15,.99,0),(.02,0,-1,.99,0),(.02,0,1.15,0,0),(.02,0,1.15,.99,1.1)])
def test_bad_fuel_parameters(b,g,t,e,l):
    with pytest.raises(ValueError):a.fuel_loss_budget(b,g,t,e,l)


def test_full_output_finite_json(result):
    assert json.loads(json.dumps(result,allow_nan=False))['schema'].endswith('.v1')
    assert len(result['power']['parameter_grid'])==72
    assert len(result['fuel_necessary_budgets'])==81


def test_joint_requirements_close_the_declared_accounting(baseline,result):
    for row in result['power']['joint_maintenance_heat_requirements']:
        x=a.power_case(baseline,turbine_eff=row['required_turbine_efficiency_at_EC60'],availability=row['availability_after_replacement'],primary_nonpump_heat_fraction=row['nonpump_primary_heat_fraction'])
        assert x['availability_adjusted_net_mw']==pytest.approx(400,abs=1e-8)
