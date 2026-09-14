from pathlib import Path
import importlib.util
import json
import math
import os
import sys
import pytest

PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'audit_plant_closure.py'
spec = importlib.util.spec_from_file_location('plant_audit', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_missing_is_not_zero():
    assert m.parse_mfile('label (unrelated)___ 0') == {'unrelated':0.0}
    with pytest.raises(ValueError):m.required({'unrelated':0.0},'tbr')


def test_real_zero_preserved():
    assert m.required(m.parse_mfile('label (physical_zero)___ 0'),'physical_zero') == 0


def test_fortran_exponent():
    assert m.parse_mfile('x (current)___ -1.25D+03 OP')['current'] == -1250


def test_consistent_duplicate():
    assert m.parse_mfile('x (a)___ 1\ny (a)___ 1')['a'] == 1


def test_inconsistent_duplicate_fails():
    with pytest.raises(ValueError):m.parse_mfile('x (a)___ 1\ny (a)___ 2')


@pytest.mark.parametrize('v',[float('nan'),float('inf')])
def test_nonfinite_required(v):
    with pytest.raises(ValueError):m.required({'a':v},'a')


def test_unsupported_overrides_numerical_flag():
    assert m.classify({'ifail':1},{'message':'Constraint 52 is only supported when running the IFE model'})=='unsupported_configuration'


def test_other_exception_not_physics():
    assert m.classify({'ifail':1},{'message':'some setup error'})=='execution_error'


@pytest.mark.parametrize('values,expected',[({},'missing_solver_status'),({'ifail':1},'numerically_feasible_under_enabled_constraints'),({'ifail':2},'solver_not_converged'),({'ifail':0},'solver_not_converged')])
def test_classification(values,expected):
    assert m.classify(values,None)==expected


def test_trapezoid_known_answer():
    assert m.integrate([0.,10.,0.],[2.,4.])==30.


@pytest.mark.parametrize('values,durations',[([0.],[1.]),([0.,1.],[-1.]),([0.,1.],[0.]),([float('inf'),1.],[1.])])
def test_invalid_time_profile(values,durations):
    with pytest.raises(ValueError):m.integrate(values,durations)


def test_zero_duration_subinterval_valid():
    assert m.integrate([0.,10.,10.],[1.,0.])==5.


@pytest.mark.parametrize('eta,dwell,a',[(0,10,.8),(1.1,10,.8),(.5,-1,.8),(.5,10,0),(.5,10,1.1)])
def test_bad_fixed_design_parameters(eta,dwell,a):
    with pytest.raises(ValueError):m.fixed_design({},eta,dwell,a)


def test_conditional_family_t_is_more_conservative():
    one,_=m.conditional_lower(1.2,.01,5,1)
    grid,q=m.conditional_lower(1.2,.01,5,42)
    assert grid<one
    assert math.isclose(q,6.84714199554418,rel_tol=1e-12)


@pytest.mark.parametrize('se,batches,family',[(-.1,5,42),(.1,1,42),(.1,5,0)])
def test_invalid_statistics(se,batches,family):
    with pytest.raises(ValueError):m.conditional_lower(1.2,se,batches,family)


def test_gate_does_not_accept_matching_material_alone():
    assert not m.matched_blanket_gate({'material_system':'HCPB'},{'material_system':'HCPB'})['coupling_identity_gate_passed']


def test_gate_records_material_mismatch():
    gate=m.matched_blanket_gate({'material_system':'HCPB'},{'material_system':'Pb17Li'})
    assert gate['mismatches']==['material_system']


def test_full_identity_gate():
    x={k:'same-source-hash' for k in ['geometry_sha256','material_inventory_sha256','neutron_source_sha256','nuclear_heating_feedback_sha256']}
    x['material_system']='HCPB'
    assert m.matched_blanket_gate(x,x)['coupling_identity_gate_passed']


def test_corrupt_archive_rejected(tmp_path):
    p=tmp_path/'fake.zip';p.write_bytes(b'not correct')
    with pytest.raises(ValueError,match='hash mismatch'):m.verify_archive(p,'0'*64)


@pytest.fixture(scope='module')
def real_result():
    value=os.environ.get('FUSION_AUDIT_ARCHIVE_DIR')
    if not value:pytest.skip('Set FUSION_AUDIT_ARCHIVE_DIR to the original ZIP directory')
    return m.audit(Path(value))


def test_real_all_eight_profiles_replay(real_result):
    rows=real_result['independent_power_replay']
    assert len(rows)==8
    assert max(r['energy_error_kwh'] for r in rows)<1e-6
    assert max(r['profile_balance_error_mw'] for r in rows)<1e-8


def test_real_classifier_corrected(real_result):
    counts=real_result['reactor_classification_counts']
    assert counts=={'numerically_feasible_under_enabled_constraints':1,'unsupported_configuration':7}
    assert not any(r['raw_tbr_present'] for r in real_result['reactor_case_audit'])
    assert all(r['tbr_value'] is None for r in real_result['reactor_case_audit'])


def test_real_fixed_design_baseline_identity(real_result):
    c=next(r for r in real_result['fixed_design_counterfactuals'] if r['eta_wallplug']==.5 and r['dwell_s']==1800 and r['availability_assumed']==.8)
    p=next(r for r in real_result['independent_power_replay'] if r['case']=='baseline')
    assert math.isclose(c['availability_adjusted_net_mw'],p['availability_adjusted_net_mw'],abs_tol=1e-10)


def test_real_fixed_design_improvement(real_result):
    c=next(r for r in real_result['fixed_design_counterfactuals'] if r['eta_wallplug']==.7 and r['dwell_s']==300 and r['availability_assumed']==.8)
    assert math.isclose(c['availability_adjusted_net_mw'],344.9495011544749,abs_tol=1e-8)
    assert c['flat_top_net_mw']>500


def test_real_400_average_not_closed_by_dwell_alone(real_result):
    c=next(r for r in real_result['fixed_design_dwell_requirements'] if r['target_average_mw']==400 and r['eta']==.7 and r['availability']==.8)
    assert not c['nonnegative_dwell_solution']
    assert c['maximum_dwell_s'] is None


def test_real_conditional_blanket_margin(real_result):
    r=next(x for x in real_result['neutronics_conditional_diagnostic'] if x['case_id']=='t060_e80')
    assert .03<r['maximum_fractional_reduction_for_target_1_15']<.032


def test_real_incompatible_blankets_fail_closed(real_result):
    assert real_result['coupling_gate']['mismatches']==['material_system']
    assert not real_result['coupling_gate']['coupling_identity_gate_passed']
    assert real_result['matched_plant_contract_seed']['native_material_fields']['f_vol_blkt_li4sio4']==.375


def test_output_finite_json(real_result):
    assert json.loads(json.dumps(real_result,allow_nan=False))['all_archive_and_manifest_hashes_verified'] is True
