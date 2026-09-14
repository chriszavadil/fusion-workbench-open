"""New source-to-module data/UI tests; old four-case regressions remain separate."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'research/source/experiments/plasma_source_coupling_2026_09_11'
D=json.loads((ROOT/'app/data/transport_lab.json').read_text(encoding='utf-8'));R=json.loads((EXP/'KEY_RESULTS.json').read_text());S=json.loads((EXP/'SOURCE_RESULT.json').read_text())
@pytest.mark.parametrize('case',D['cases'][4:],ids=lambda x:x['id'])
def test_two_bank_mean_and_uncertainty_are_actual(case):
 layout=case['layout'];rows=[json.loads((EXP/'runs'/f'{layout}_bank{b}'/'RESULT.json').read_text()) for b in [0,1]]
 field=np.mean([r['tallies']['volume_heating']['mean'] for r in rows],axis=0)/rows[0]['voxel_cm3']
 se=np.sqrt(np.sum(np.array([r['tallies']['volume_heating']['std_dev'] for r in rows])**2,axis=0))/2/rows[0]['voxel_cm3']
 assert np.array_equal(field,case['heating_density']);assert np.array_equal(se,case['heating_standard_error_density'])
 assert case['source_histories']==400000 and case['tallies_averaged_over_banks']==2
 assert case['incident_neutrons_s']==S['normalized_patch_neutrons_s']
 assert not case['physical_validation']
@pytest.mark.parametrize('case',D['cases'][4:],ids=lambda x:x['id'])
def test_recorded_tracks_not_geometric_source_rays(case):
 raw=json.loads((EXP/'runs'/f"{case['layout']}_bank0"/'TRACKS.json').read_text());assert case['paths']==raw['paths']
 assert raw['source_histories_recorded']==16 and case['paths_bank']==0
 for p in case['paths']:
  q=np.asarray(p['states']);assert q.shape[1]==5 and np.isfinite(q).all() and np.all(np.diff(q[:,3])>=0)

def test_source_context_and_geometry_mismatch_are_visible():
 c=D['source_context'];assert c['authoritative_source_result']==S and c['source_particle_count']==131072
 assert c['geometry']==S['geometry'];assert c['parameterized_volume_difference_percent']>2
 assert c['source_result_sha256']==hashlib.sha256((EXP/'SOURCE_RESULT.json').read_bytes()).hexdigest()
 assert len(D['cases'])==6 and not D['physical_validation']

def test_identical_native_browser_transport_packet():
 assert (ROOT/'app/data/transport_lab.json').read_bytes()==(ROOT/'native/Content/WorkbenchData/transport_lab.json').read_bytes()
def test_conditional_heat_not_added_electricity():
 for case in D['cases'][4:]:
  mean=np.asarray(case['heating_density']);rate=case['incident_neutrons_s'];mw_m3=mean*rate*1.602176634e-19
  assert np.isfinite(mw_m3).all() and (mw_m3>=0).all()
 assert not R['extra_electricity'] and not R['whole_reactor_TBR']
def test_new_report_searchable_and_scoped():
 lib=json.loads((ROOT/'app/data/research_library.json').read_text(encoding='utf-8'))
 row=next(x for x in lib['records'] if x['title'].startswith('Plasma source coupling:'))
 assert row['configuration_scope']=='r838' and row['status']=='current update'
 assert '2.407%' in row['body'] and 'not a fusion breakthrough' in row['body']
 assert lib['updated_date']=='2026-09-13'
def test_native_readers_support_new_source_and_preserve_configuration():
 lab=(ROOT/'native/Source/FusionWorkbench/FusionTransportLab.cpp').read_text(encoding='utf-8')
 ui=(ROOT/'native/Source/FusionWorkbench/FusionTransportUI.cpp').read_text(encoding='utf-8')
 assert 'Cases.Num()>0' in lab and 'source_context' in lab
 assert 'Source context / module' in ui and 'SelectConfiguration(' not in ui
 assert 'geometric-ray animation' in ui
