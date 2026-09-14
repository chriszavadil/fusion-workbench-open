"""Exact canonical export round-trip. Display budgets must never delete evidence."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'research/source/experiments/plasma_source_coupling_2026_09_11'
P=json.loads((ROOT/'app/data/transport_lab.json').read_text());C=P['source_context'];RAW=(ROOT/'app/data/source_context.bin').read_bytes()
DTYPE=np.dtype([('id','<u8'),('bank','<u4'),('index','<u4'),('weight','<f8'),('probability','<f8'),('birth','<f8',(3,)),('target','<f8',(3,)),('local','<f8',(3,)),('direction','<f8',(3,))])
MAGIC,VERSION,COUNT=struct.unpack_from('<IIQ',RAW);ROWS=np.frombuffer(RAW,dtype=DTYPE,offset=16)
def test_all_source_particles_and_stable_identifiers_survive():
 assert MAGIC==0x53574331 and VERSION==1 and DTYPE.itemsize==128
 assert len(ROWS)==COUNT==C['source_particle_count']==131072
 assert len(RAW)==16+COUNT*DTYPE.itemsize and len(np.unique(ROWS['id']))==COUNT
 assert np.array_equal(ROWS['id'],(ROWS['bank'].astype(np.uint64)<<32)|ROWS['index'])
 assert C['source_bank_sha256']==hashlib.sha256(RAW).hexdigest()
@pytest.mark.parametrize('bank',[0,1])
def test_positions_directions_weights_probabilities_and_moments(bank):
 src=np.load(EXP/'source_banks'/f'bank{bank}.npz');rows=ROWS[ROWS['bank']==bank];obs=C['authoritative_source_result']['banks'][bank]
 assert len(rows)==obs['count']==65536
 for target,key in [('birth','birth'),('target','target'),('local','r'),('direction','u')]:assert np.array_equal(rows[target],src[key])
 assert np.array_equal(rows['index'],np.arange(len(rows))) and np.all(rows['weight']==1)
 assert np.all(rows['probability']==1/len(ROWS)) and rows['probability'].sum()==.5
 counts,_=np.histogram(rows['direction'][:,0],bins=obs['mu_bin_edges']);assert np.array_equal(counts,obs['mu_counts'])
 assert rows['direction'][:,0].mean()==obs['mean_mu']
def test_canonical_source_metadata_profiles_and_all_observations_preserved():
 assert C['authoritative_source_result']==json.loads((EXP/'SOURCE_RESULT.json').read_text())
 assert C['authoritative_plasma_profiles']==json.loads((EXP/'PLASMA_SOURCE.json').read_text())
 assert C['authoritative_coupled_result']==json.loads((EXP/'KEY_RESULTS.json').read_text())
 assert C['authoritative_local_input']==json.loads((EXP/'LOCAL_INPUT.json').read_text())

@pytest.mark.parametrize('case',P['cases'][4:],ids=lambda c:c['id'])
def test_both_track_banks_survive_not_only_displayed_bank(case):
 assert len(case['authoritative_track_banks'])==2
 for saved in case['authoritative_track_banks']:
  p=ROOT/saved['source_path'];assert saved['data']==json.loads(p.read_text())
  assert hashlib.sha256(p.read_bytes()).hexdigest()==saved['sha256']
  assert saved['data']['source_histories_recorded']==16

def test_renderer_budget_does_not_change_canonical_data():
 assert C['visualization']['default_source_site_budget']<COUNT
 assert ROWS['probability'].sum()==1
 assert (ROOT/'native/Content/WorkbenchData/source_context.bin').read_bytes()==RAW
 code=(ROOT/'native/Source/FusionWorkbench/FusionTransportLab.cpp').read_text()
 assert 'SourceDrawIndices' in code and 'SourceSites.Add(Site)' in code
 assert 'default_source_site_budget' in code and 'SourceRenderBudget=' in code
