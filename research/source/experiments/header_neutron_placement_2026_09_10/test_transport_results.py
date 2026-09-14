"""Checks of the declared transport experiment, not physical blanket qualification."""
from pathlib import Path
import hashlib,importlib.util,json,math
import numpy as np
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('transport_audit',HERE/'analyze_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
F=json.loads((HERE/'FROZEN_INPUT.json').read_text());A=json.loads((HERE/'RUN_ADMISSION.json').read_text());R=json.loads((HERE/'KEY_RESULTS.json').read_text())
@pytest.mark.parametrize('name',F['layouts'])
def test_two_distinct_completed_runs(name):
 rows=[r for r in A['runs'] if r['layout']==name];assert len(rows)==2 and rows[0]['seed']!=rows[1]['seed']
 for row in rows:
  p=HERE/'candidate_runs'/(name+'_'+str(row['seed']));r=json.loads((p/'RESULT.json').read_text());assert r['completed'] and r['histories']==1000000
  log=(p/'execution.log').read_text();assert 'ERROR:' not in log and 'Could not find cell' not in log
  assert r['statepoint_sha256']==hashlib.sha256((p/'statepoint.40.h5').read_bytes()).hexdigest()

def test_preregistered_input_and_source_hashes_preserved():
 assert A['frozen_input_sha256']==hashlib.sha256((HERE/'FROZEN_INPUT.json').read_bytes()).hexdigest()
 assert A['model_sha256']==hashlib.sha256((HERE/'local_model.py').read_bytes()).hexdigest()
 assert A['materials_sha256']==hashlib.sha256((HERE/'materials_and_reference.py').read_bytes()).hexdigest()
 assert len({r['seed'] for r in A['runs']})==6

def test_inventory_is_matched_not_free_extra_coolant():
 g=json.loads((HERE/'GEOMETRY_CHECKS.json').read_text());assert g['equal_inventory_verified']
 assert all(c['nuclide_inventory_max_relative_difference']<1e-10 for c in g['cases'])
 assert all(c['passed'] and c['points_checked']>=10000 for c in g['cases'])
 assert sum(F['fractions'].values())==pytest.approx(1.,abs=1e-12)
@pytest.mark.parametrize('name',F['layouts'])
def test_tally_additivity_and_real_profiles(name):
 r=R['cases'][name];assert len(r['depth_centres_cm'])==40 and len(r['depth_tritons_per_incident_neutron'])==40
 assert all(x>=0 and math.isfinite(x) for x in r['depth_tritons_per_incident_neutron'])
 assert sum(c['heating_eV_per_incident_neutron'] for c in r['cells'])/1e6==pytest.approx(r['heating_MeV_per_incident_neutron'],rel=1e-7)
 assert sum(c['tritons_per_incident_neutron'] for c in r['cells'])==pytest.approx(r['tritons_per_incident_neutron'],rel=1e-7)
 assert r['source_histories']==2000000 and r['tritons_standard_error']>0

def test_comparison_uses_statistical_not_physical_interval():
 for row in R['comparisons']:
  b=R['cases']['homogeneous'];r=R['cases'][row['layout']]
  assert row['difference']==pytest.approx(r['tritons_per_incident_neutron']-b['tritons_per_incident_neutron'])
  assert row['standard_error']==pytest.approx(math.hypot(r['tritons_standard_error'],b['tritons_standard_error']))
  expected=abs(row['relative_percent'])>2 and (row['interval99'][0]>0 or row['interval99'][1]<0)
  assert row['admitted_geometry_sensitivity_flag']==expected

def test_averaging_independent_estimators():
 rows=[{'tallies':{'x':{'mean':[2.],'std_dev':[.3]}}},{'tallies':{'x':{'mean':[4.],'std_dev':[.4]}}}]
 avg,se=m.combine(rows,'x');assert avg[0]==3 and se[0]==pytest.approx(.25)

def test_computational_benchmark_not_experimental_blanket_claim():
 b=R['reference_computational_replay'];assert b['computational_replay_passed'] and b['physical_validation'] is False
 assert abs(b['cases']['nspectrum']['integrated_ratio_to_archived']-1)<.03
 assert not R['global_TBR_computed'] and not R['physical_validation'] and not R['new_plant_electrical_output_computed']

def test_frozen_front_header_case_stays_stress_case():
 assert any('stress case' in x for x in R['limits'])
 assert F['configuration_id']=='r838'
