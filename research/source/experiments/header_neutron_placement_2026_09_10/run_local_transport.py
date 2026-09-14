"""Finite, candidate-linked header-layout neutron/photon test; no global TBR claim."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
import numpy as np,openmc
from local_model import make
from materials_and_reference import HERE,F

def plain(o):
 if isinstance(o,dict):return {str(k):plain(v) for k,v in o.items()}
 if isinstance(o,(list,tuple)):return [plain(v) for v in o]
 if isinstance(o,np.generic):return o.item()
 return o

def save(p,o):p.write_text(json.dumps(plain(o),indent=2,sort_keys=True,allow_nan=False)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def execute():
 reference=json.loads((HERE/'REFERENCE_RESULT.json').read_text());geometry=json.loads((HERE/'GEOMETRY_CHECKS.json').read_text())
 if not reference['computational_replay_passed'] or not geometry['equal_inventory_verified']:raise RuntimeError('Prerequisite gate has not passed')
 xs=Path((HERE/'local_cross_sections_path.txt').read_text().strip());openmc.config['cross_sections']=xs
 admission={'schema':'fusion.local-transport-run-admission.v1','frozen_input_sha256':digest(HERE/'FROZEN_INPUT.json'),'model_sha256':digest(HERE/'local_model.py'),'materials_sha256':digest(HERE/'materials_and_reference.py'),'driver_sha256':digest(Path(__file__)),'data_manifest_sha256':digest(HERE/'DATA_MANIFEST.json'),'seed_rule':'base_seed + 100000*layout_index; distinct streams, not common random numbers','runs':[{'layout':layout,'seed':seed+100000*i,'histories':F['batches']*F['particles_per_batch']} for i,layout in enumerate(F['layouts']) for seed in F['seeds']],'physics_scope':'Local repeated slab and header-placement comparison, not toroidal transport, global breeding ratio or measured validation.','reference_scope':'Published aluminum neutron/photon transport computational replay, not HCPB breeding validation.'}
 dest=HERE/'candidate_runs'
 if dest.exists():raise RuntimeError('Refuse to overwrite existing candidate runs')
 dest.mkdir();save(HERE/'RUN_ADMISSION.json',admission)
 env=os.environ.copy();env['OPENMC_CROSS_SECTIONS']=str(xs);env['OMP_NUM_THREADS']=str(F['threads'])
 states=[]
 for row in admission['runs']:
  folder=dest/(row['layout']+'_'+str(row['seed']));folder.mkdir();start=time.monotonic()
  model,meta=make(row['layout'],row['seed']);save(folder/'model_metadata.json',meta);model.export_to_xml(directory=folder)
  status={**row,'completed':False,'physical_validation':False}
  try:
   with (folder/'execution.log').open('w') as log:
    done=subprocess.run([str(Path(sys.executable).with_name('openmc')),'-s',str(F['threads'])],cwd=folder,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=F['timeout_s_each'])
   status['return_code']=done.returncode
   if done.returncode:raise RuntimeError('OpenMC failed; preserve execution.log')
   state=folder/f"statepoint.{F['batches']}.h5"
   with openmc.StatePoint(state) as sp:
    summaries={}
    for name in ['total_tritons','total_heating','lithium_tritons','heat_by_cell','tritons_by_cell','front_leakage','back_leakage','depth']:
     t=sp.get_tally(name=name);summaries[name]={'mean':t.mean.ravel().tolist(),'std_dev':t.std_dev.ravel().tolist(),'scores':t.scores,'nuclides':t.nuclides,'realizations':int(t.num_realizations),'filters':[type(f).__name__ for f in t.filters]}
    if not all(np.all(np.isfinite(s['mean'])) and np.all(np.isfinite(s['std_dev'])) for s in summaries.values()):raise ValueError('Nonfinite tally')
    status.update(completed=True,tallies=summaries,statepoint_sha256=digest(state),openmc_version=openmc.__version__)
  except subprocess.TimeoutExpired:status['error']='bounded_timeout'
  except Exception as exc:status['error']=type(exc).__name__+': '+str(exc)
  status['elapsed_s']=time.monotonic()-start;save(folder/'RESULT.json',status);states.append(status)
  print(json.dumps({k:status[k] for k in ['layout','seed','completed','elapsed_s']}),flush=True)
  if not status['completed']:break
 save(HERE/'RUN_STATUS.json',{'all_admitted_completed':len(states)==len(admission['runs']) and all(x['completed'] for x in states),'completed_runs':sum(x['completed'] for x in states),'attempted_runs':len(states),'physical_validation':False})
if __name__=='__main__':execute()
