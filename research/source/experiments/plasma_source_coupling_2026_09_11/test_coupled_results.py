"""Acceptance checks of completed source coupling; not physical validation."""
from pathlib import Path
import hashlib,importlib.util,json,math
import numpy as np
import pytest
HERE=Path(__file__).resolve().parent
A=json.loads((HERE/'ADMISSION.json').read_text());R=json.loads((HERE/'KEY_RESULTS.json').read_text());S=json.loads((HERE/'SOURCE_RESULT.json').read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@pytest.mark.parametrize('layout',['headers_rear','headers_front'])
def test_completed_hash_linked_banks(layout):
 for bank in (0,1):
  p=HERE/'runs'/f'{layout}_bank{bank}';r=json.loads((p/'RESULT.json').read_text())
  assert r['completed'] and r['histories']==200000
  assert r['statepoint_sha256']==digest(p/'statepoint.20.h5')
  assert r['json_tracks_sha256']==digest(p/'TRACKS.json')
  assert r['geometry_sha256']==digest(p/'GEOMETRY.json')
  assert all(np.isfinite(t['mean']).all() and np.isfinite(t['std_dev']).all() for t in r['tallies'].values())
def test_frozen_source_admission():
 assert digest(HERE/'ADMISSION.json')==R['admission_sha256']
 assert digest(HERE/'SOURCE_RESULT.json')==R['source_result_sha256']
 assert len(A['runs'])==4 and len({r['seed'] for r in A['runs']})==4
@pytest.mark.parametrize('layout',['headers_rear','headers_front'])
def test_local_total_heating_matches_cells(layout):
 r=R['cases'][layout]
 assert sum(c['heat_MW'] for c in r['cells'])==pytest.approx(r['conditional_module_nuclear_heat_MW'],rel=1e-10)
 assert r['conditional_module_nuclear_heat_MW']==pytest.approx(r['deposited_MeV_per_incident_neutron']*1.602176634e-19*S['normalized_patch_neutrons_s'],rel=1e-12)
 assert r['between_bank_difference_z']<3

def test_independent_conditional_contrast():
 a=R['cases']['headers_front'];b=R['cases']['headers_rear'];c=R['comparison']
 d=a['tritons_per_incident_neutron']-b['tritons_per_incident_neutron'];s=math.hypot(a['tritons_standard_error'],b['tritons_standard_error'])
 assert c['front_minus_rear_tritons']==pytest.approx(d)
 assert c['standard_error']==pytest.approx(s)
 assert c['interval99']==pytest.approx([d-2.5758293035489*s,d+2.5758293035489*s])
 assert c['source_geometry_and_nuclear_data_uncertainty_excluded']
def test_normalization_records_shape_discrepancy():
 assert S['parameterized_volume_difference_percent']>2
 assert S['source_shape_total_rate_ratio_to_PROCESS']>1
 assert S['normalized_patch_neutrons_s']==pytest.approx(S['patch_fraction']*S['normalization_DT_rate_s'])
 assert R['source_power_geometry_not_reoptimized']
 assert not R['whole_reactor_TBR'] and not R['experimental_validation'] and not R['extra_electricity']
def test_prior_controls_not_replaced_by_assumed_average_source():
 mus=[b['mean_mu'] for b in S['banks']]
 assert all(.7<x<.9 for x in mus)
 assert len(S['source_rays'])==64
 assert S['patch_fraction_scramble_se']>0
