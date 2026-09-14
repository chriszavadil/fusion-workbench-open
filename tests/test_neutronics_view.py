"""Completed transport evidence projection, not physical reactor validation."""
from pathlib import Path
import hashlib,json,math
import pytest
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'research/source/experiments/header_neutron_placement_2026_09_10'
RAW=json.loads((EXP/'KEY_RESULTS.json').read_text())
PACKET=json.loads((ROOT/'app/data/neutronics.json').read_text())

def test_native_browser_use_identical_completed_data():
 assert (ROOT/'app/data/neutronics.json').read_bytes()==(ROOT/'native/Content/WorkbenchData/neutronics.json').read_bytes()
 assert PACKET['source_result_sha256']==hashlib.sha256((EXP/'KEY_RESULTS.json').read_bytes()).hexdigest()
 assert len(PACKET['cases'])==3
@pytest.mark.parametrize('i,layout',list(enumerate(['homogeneous','headers_rear','headers_front'])))
def test_actual_tallies_not_illustrative_profiles(i,layout):
 row=PACKET['cases'][i];original=RAW['cases'][layout]
 assert row['layout']==layout and row['source_histories']==2000000
 for key in ['tritons_per_incident_neutron','tritons_standard_error','heating_MeV_per_incident_neutron','depth_tritons_per_incident_neutron','depth_tritons_standard_error']:
  assert row[key]==original[key]
 assert len(row['depth_tritons_per_incident_neutron'])==40
 assert all(math.isfinite(x) and x>=0 for x in row['depth_tritons_per_incident_neutron'])
def test_local_denominator_and_physical_scope_not_upgraded():
 assert 'local' in PACKET['configuration_scope']
 assert not PACKET['physical_validation'] and not PACKET['global_TBR_computed']
 assert not PACKET['exploratory_follow_on']['loss_greater_than_2percent_resolved_at_99percent_MC']
 assert 'spans the 2%' in PACKET['decision']

def test_all_six_completed_records_are_available_for_replay():
 admission=json.loads((EXP/'RUN_ADMISSION.json').read_text());assert len(admission['runs'])==6
 assert len({r['seed'] for r in admission['runs']})==6
 for row in admission['runs']:
  folder=EXP/'candidate_runs'/(row['layout']+'_'+str(row['seed']))
  r=json.loads((folder/'RESULT.json').read_text());assert r['completed'] and r['histories']==1000000
  assert (folder/'model_metadata.json').is_file() and (folder/'tallies.xml').is_file()
def test_report_in_reader_and_dashboard_scoped():
 lib=json.loads((ROOT/'app/data/research_library.json').read_text())
 report=next(r for r in lib['records'] if r['title']=='Header neutron study: candidate-linked transport decision')
 assert report['configuration_scope']=='r838' and report['track']=='neutronics'
 assert 'NOT the plant breeding ratio' in next(r['body'] for r in lib['records'] if r['title'].startswith('Research update - 10 September'))
 cat=json.loads((ROOT/'app/data/catalog.json').read_text());track=next(t for t in cat['tracks'] if t['id']=='neutronics')
 assert 'local transport' in track['model_status'] and 'Whole-device' in track['validation_status']
def test_no_public_remote_code_execution_added():
 js=(ROOT/'app/web/neutronics.js').read_text()
 assert 'innerHTML' not in js and 'eval(' not in js and 'POST' not in js
 cpp=(ROOT/'native/Source/FusionWorkbench/FusionNeutronics.cpp').read_text()
 assert 'StartSolver(' not in cpp and 'SelectConfiguration(' not in cpp
