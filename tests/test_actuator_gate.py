"""Fixed-current requirements are not new transport or output-power predictions."""
from pathlib import Path
import hashlib,importlib.util,json,math
import pytest
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'research/source/experiments/plant_current_drive_2026_09_14'
spec=importlib.util.spec_from_file_location('actuator_gate_test',E/'actuator_gate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
D=json.loads((E/'ACTUATOR_GATE.json').read_text(encoding='utf-8'));S=json.loads((E/'ACTUATOR_SCALARS.json').read_text(encoding='utf-8'))
@pytest.mark.parametrize('c',D['cases'],ids=lambda c:c['case'])
def test_same_current_by_independent_identities(c):
 v=S[c['case']]['values'];r=json.loads((E/'runs'/c['case']/'RESULT.json').read_text(encoding='utf-8'))
 assert c['source_sha256']==r['mfile_sha256']==S[c['case']]['mfile_sha256']
 assert c['required_current_MA']==pytest.approx(v['plasma_current']*v['f_c_plasma_auxiliary']/1e6,abs=1e-12)
 assert c['required_current_MA']==pytest.approx(v['eta_cd_hcd_primary']*v['p_hcd_primary_injected_mw'],abs=1e-8)
 assert c['booked_efficiency_kA_per_MW']==v['eta_cd_hcd_primary']*1000
 assert c['model_normalized_gamma']!=c['model_dimensionless_efficiency']
 assert c['minimum_efficiency_at_retained_reserve_kA_per_MW']==pytest.approx(c['required_current_MA']*1000/(200-c['retained_heat_only_allocation_MW']),rel=1e-14)

def test_exact_boundary_and_rejection_on_each_side():
 current=7597.809764607095;threshold=current/170
 assert m.evaluate(current,threshold,200,30)['fixed_point_total_current_condition_met']
 assert m.evaluate(current,threshold*1.01,200,30)['fixed_point_total_current_condition_met']
 assert not m.evaluate(current,threshold*.99,200,30)['fixed_point_total_current_condition_met']
 assert m.evaluate(current,40,200,30)['new_net_power_prediction'] is None

@pytest.mark.parametrize('bad',[0,-1,float('nan'),float('inf'),True])
def test_invalid_efficiency_does_not_become_a_result(bad):
 with pytest.raises(ValueError):m.evaluate(7000,bad,200,30)

def test_complete_export_hashes_attribution_and_no_new_plant_claim():
 assert D['source_scalars_sha256']==hashlib.sha256((E/'ACTUATOR_SCALARS.json').read_bytes()).hexdigest()
 assert D['admission_sha256']==hashlib.sha256((E/'ACTUATOR_GATE_ADMISSION.json').read_bytes()).hexdigest()
 assert (E/'ACTUATOR_GATE.json').read_bytes()==(ROOT/'docs/plant-decision/actuator.json').read_bytes()
 assert not D['physical_validation'] and D['new_solver_runs']==0 and not D['accepted_reference_replaced']
 for c in D['cases']:
  for ex in c['examples']:
   assert ex['new_net_power_prediction'] is None
   expected=c['required_current_MA']*1000/ex['efficiency_kA_per_MW']
   assert expected==pytest.approx(ex['required_drive_MW'],rel=1e-14)
 assert all(s['authors'] and s['url'] and s['reading_scope'] for s in D['sources'])

def test_panel_cannot_silently_modify_the_recorded_power_view():
 js=(ROOT/'docs/plant-decision/actuator.js').read_text(encoding='utf-8');html=(ROOT/'docs/plant-decision/index.html').read_text(encoding='utf-8')
 assert '<script src="actuator.js" type="module">' in html
 assert "fetch('actuator.json')" in js and "$('timeline')" not in js and "$('case-select')" not in js
 assert 'innerHTML' not in js and 'eval(' not in js and 'method:' not in js
 assert 'does not rerun the plant model' in html
