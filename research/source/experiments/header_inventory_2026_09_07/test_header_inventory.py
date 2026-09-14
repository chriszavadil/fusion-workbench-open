"""Focused numerical/accounting tests, not physical qualification."""
import json,math,hashlib
from pathlib import Path
import numpy as np
import pytest
from scipy.optimize import root
from header_inventory import HeaderStudy
from flow_recheck import solve
HERE=Path(__file__).resolve().parent
@pytest.fixture(scope='module')
def state():return json.loads((HERE/'INPUT_STATE.json').read_text())
@pytest.fixture(scope='module')
def study(state):return HeaderStudy(state)
@pytest.fixture(scope='module')
def output():return json.loads((HERE/'RESULT.json').read_text())
@pytest.fixture(scope='module')
def flows():return json.loads((HERE/'FLOW_RECHECK_RESULT.json').read_text())
def test_state_provenance():
    meta=json.loads((HERE/'PROVENANCE.json').read_text())
    assert hashlib.sha256((HERE/'INPUT_STATE.json').read_bytes()).hexdigest()==meta['input_subset_sha256']
    assert meta['upstream_worktree_clean']
@pytest.mark.parametrize('side',['inboard','outboard'])
def test_inventory_debits_and_caps(study,side):
    g=study.geometry(side,.04)
    assert g['header_coolant_m3']+g['remaining_channel_coolant_m3']==pytest.approx(g['native_coolant_m3'],abs=1e-12)
    assert g['shell_steel_m3']+g['cap_volume_allowance_m3']+g['remaining_nonheader_steel_m3']==pytest.approx(g['native_steel_m3'],abs=1e-12)
    assert g['cap_volume_allowance_m3']>0 and not g['caps_nozzles_and_remaining_structure_qualified']
@pytest.mark.parametrize('radius',[0.,-.1,float('nan'),10.])
def test_bad_geometry_rejected(study,radius):
    with pytest.raises(ValueError):study.geometry('inboard',radius)
@pytest.mark.parametrize('idx',range(4))
def test_saved_point_replays_and_local_radius_minimum(study,output,idx):
    record=output['results'][idx];split=record['configuration']=='outboard_split'
    for side,saved in record['branches'].items():
        r=saved['geometry']['inner_radius_m'];fresh=study.evaluate(side,r,split,record['choice'])
        assert fresh['known_branch_pressure_Pa']==pytest.approx(saved['known_branch_pressure_Pa'],abs=.001)
        assert fresh['maximum_header_Mach']<.1
        assert min(saved['optimization']['neighbor_pressure_differences_Pa'])>0
        g=fresh['geometry'];a=g['inner_radius_m'];b=g['outer_radius_m'];p=study.net.pin
        assert g['ideal_closed_barrel_von_Mises_Pa']==pytest.approx(math.sqrt(3)*p*b*b/(b*b-a*a),rel=1e-12)
        assert fresh['not_a_validated_hardware_result']
@pytest.mark.parametrize('idx',range(4))
def test_common_pressure_and_mass_independent_two_variable_solver(study,output,flows,idx):
    ref=output['results'][idx];saved=flows['results'][idx]['unbalanced'];split=ref['configuration']=='outboard_split'
    radii={k:v['geometry']['inner_radius_m'] for k,v in ref['branches'].items()}
    def residual(x):
        ib=study.evaluate('inboard',radii['inboard'],split,ref['choice'],x[0])
        ob=study.evaluate('outboard',radii['outboard'],split,ref['choice'],x[1])
        return [(ib['known_branch_pressure_Pa']-ob['known_branch_pressure_Pa'])/1e5,(x.sum()-study.net.total)/1000]
    sol=root(residual,[study.net.nominal['inboard'],study.net.nominal['outboard']],tol=1e-10)
    assert sol.success and np.max(abs(np.array(residual(sol.x))))<1e-8
    assert sol.x[0]==pytest.approx(saved['IB']['branch']['flow_kg_s'],abs=1e-5)
    assert abs(saved['pressure_residual_Pa'])<.01
def test_stronger_unsplit_reference_is_not_hidden(output,flows):
    nominal=[r for r in output['results'] if r['configuration']=='unsplit']
    solved=[r['unbalanced'] for r in flows['results'] if r['configuration']=='unsplit']
    assert all(not r['envelope_known_loss_within_allowance'] for r in nominal)
    assert all(r['remaining_common_allowance_Pa']>0 and r['local_FW_temperature_screen_passed'] for r in solved)
def test_split_unbalanced_is_only_narrow_thermal_margin(flows):
    rows=[r['unbalanced'] for r in flows['results'] if r['configuration']=='outboard_split']
    assert all(0<r['IB']['native_temperature_margin_K']<3 for r in rows)
def test_balancing_restore_nominal_without_double_charging(study,output,flows):
    for ref,new in zip(output['results'],flows['results']):
        b=new['restored_nominal']
        if b is None:continue
        assert b['IB']['branch']['flow_kg_s']==pytest.approx(study.net.nominal['inboard'],abs=1e-5)
        assert b['common_pressure_Pa']==pytest.approx(ref['known_common_pressure_Pa_after_nominal_balancing'],abs=.01)
        assert b['remaining_common_allowance_Pa']==pytest.approx(ref['remaining_common_external_pressure_Pa'],abs=.01)
def test_unknown_fitting_and_external_budgets_compete(output):
    r=next(x for x in output['results'] if x['configuration']=='outboard_split' and x['choice']=='outlet')
    ib=r['branches']['inboard'];head=ib['dynamic_head_sum_Pa'];limit=ib['equal_per_header_unknown_K_allowance_if_no_external_loss']
    assert ib['known_branch_pressure_Pa']+limit*head==pytest.approx(550000.,abs=1e-8)
    assert ib['known_branch_pressure_Pa']+limit*head+1000>550000.
    assert not r['physical_manifold_or_plant_validated']
