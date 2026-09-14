"""Data-backed field, trajectory, source-contrast and presentation checks. MIT."""
from pathlib import Path
import hashlib,importlib.util,json,math
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'research/source/experiments/source_direction_spatial_2026_09_10'
DATA=json.loads((ROOT/'app/data/transport_lab.json').read_text(encoding='utf-8'));RESULT=json.loads((EXP/'KEY_RESULTS.json').read_text());ADM=json.loads((EXP/'ADMISSION.json').read_text())
@pytest.mark.parametrize('case',DATA['cases'][:4],ids=lambda x:x['id'])
def test_mesh_fields_are_actual_scores(case):
 raw=json.loads((EXP/'runs'/case['id']/'RESULT.json').read_text());meta=json.loads((EXP/'runs'/case['id']/'GEOMETRY.json').read_text())
 v=raw['mesh']['voxel_cm3'];a=np.asarray(case['heating_density']);s=np.asarray(case['heating_standard_error_density'])
 assert len(a)==24*16*16 and len(s)==len(a)
 assert np.array_equal(a,np.asarray(raw['tallies']['volume_heating']['mean'])/v)
 assert np.array_equal(s,np.asarray(raw['tallies']['volume_heating']['std_dev'])/v)
 assert np.isfinite(a).all() and (a>=0).all()
 assert a.sum()*v==pytest.approx(sum(raw['tallies']['heat_by_cell']['mean'][2:]),rel=1e-10)
 assert raw['mesh']['indices_1based']==[[x+1,y+1,z+1] for z in range(16) for y in range(16) for x in range(24)]
 assert case['result_sha256']==hashlib.sha256((EXP/'runs'/case['id']/'RESULT.json').read_bytes()).hexdigest()
 assert DATA['dimensions_cm']==[meta['dimensions_cm'][k] for k in ['x','y','z']]
@pytest.mark.parametrize('case',DATA['cases'][:4],ids=lambda x:x['id'])
def test_trajectories_are_unmodified_recorded_states(case):
 raw=json.loads((EXP/'runs'/case['id']/'TRACKS.json').read_text());assert raw['source_histories_recorded']==16
 assert len(raw['paths'])==len(case['paths'])
 for original,shown in zip(raw['paths'],case['paths']):
  assert original['states']==shown['states'] and original['particle']==shown['particle']
  assert shown['primary']==original['history'][2] and 1<=shown['primary']<=16
  p=np.asarray(shown['states']);assert p.shape[1]==5 and np.isfinite(p).all()
  assert (np.diff(p[:,3])>=0).all() and (p[:,3:]>=0).all()

def test_two_independent_angular_comparisons():
 assert len({x['seed'] for x in ADM['cases']})==4
 for law in ['cosine','normal']:
  a=RESULT['cases'][law+'_front'];b=RESULT['cases'][law+'_rear'];d=RESULT['front_minus_rear'][law]
  assert d['difference']==pytest.approx(a['tritons_per_source']-b['tritons_per_source'])
  assert d['standard_error']==pytest.approx(math.hypot(a['tritons_standard_error'],b['tritons_standard_error']))
  assert d['interval99'][1]<0 and d['Monte_Carlo_error_only']
 assert RESULT['conclusions']['source_direction_interaction']['interval99'][0]<0<RESULT['conclusions']['source_direction_interaction']['interval99'][1]
 assert not RESULT['conclusions']['full_reactor_TBR']

def test_preserved_tally_and_companion_track_boundary():
 r=json.loads((EXP/'TRACK_API_RECOVERY.json').read_text())
 assert not r['physics_changed']
 assert r['existing_statepoint_preserved_sha256']==RESULT['cases']['cosine_rear']['statepoint_sha256']
 assert sum(c['source_histories'] for c in DATA['cases'][:4])==1600000
 assert all(c['source_histories']==400000 for c in DATA['cases'][:4])

def test_renderer_identical_packets_and_no_physics_promotion():
 assert (ROOT/'app/data/transport_lab.json').read_bytes()==(ROOT/'native/Content/WorkbenchData/transport_lab.json').read_bytes()
 assert not DATA['physical_validation']
 assert sum(len(c['paths']) for c in DATA['cases'][:4])==463
 assert sum(len(p['states']) for c in DATA['cases'][:4] for p in c['paths'])==4693
 assert DATA['admission_sha256']==hashlib.sha256((EXP/'ADMISSION.json').read_bytes()).hexdigest()

def test_common_heating_scale_not_per_case_exaggeration():
 assert DATA['common_heating_scale']==max(max(c['heating_density']) for c in DATA['cases'])
 assert DATA['field_units']=='eV/cm^3 per incident neutron'

@pytest.mark.parametrize('case',DATA['cases'][:4],ids=lambda x:x['id'])
def test_recorded_positions_and_display_time_are_bounded(case):
 size=np.asarray(DATA['dimensions_cm'])
 for path in case['paths']:
  p=np.asarray(path['states']);assert (p[:,:3]>=np.array([-2.3001,-.0001,-.0001])).all()
  assert (p[:,:3]<=size+.0001).all()
  w=p[:,:3]-size/2;w[:,1]*=-1;inverse=w.copy();inverse[:,1]*=-1;inverse+=size/2
  assert np.allclose(inverse,p[:,:3],atol=1e-12)
 maximum=case['max_track_time_s']
 assert math.expm1(math.log1p(maximum/1e-9))*1e-9==pytest.approx(maximum,rel=1e-12)
 assert maximum==max(p['states'][-1][3] for p in case['paths'])

def test_native_voxel_pick_uses_physical_impact_position():
 code=(ROOT/'native/Source/FusionWorkbench/FusionRuntime.cpp').read_text()
 assert 'Lab->InspectWorld(Hit.ImpactPoint)' in code
 assert 'Lab->InspectField(Hit.FaceIndex)' not in code
 ui=(ROOT/'native/Source/FusionWorkbench/FusionTransportUI.cpp').read_text()
 assert 'Voxel (2,2,' in ui and 'TestTransportLab' in ui

def test_browser_does_not_execute_or_inject_research_code():
 js=(ROOT/'app/web/transport-lab.js').read_text()
 assert 'innerHTML' not in js and 'eval(' not in js and 'POST' not in js
 assert 'new THREE.InstancedMesh' in js and 'current.paths' in js
 assert 'Math.log1p(data.common_heating_scale)' in js
