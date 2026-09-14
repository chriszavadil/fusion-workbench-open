"""Frozen joint surface source through existing equal-inventory headers. MIT."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
import numpy as np,openmc
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'baseline'));from local_model import make
A=json.loads((HERE/'ADMISSION.json').read_text());F=json.loads((HERE/'LOCAL_INPUT.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(o):
 if isinstance(o,dict):return {str(k):plain(v) for k,v in o.items()}
 if isinstance(o,(list,tuple)):return [plain(v) for v in o]
 if isinstance(o,np.generic):return o.item()
 return o
def save(p,o):p.write_text(json.dumps(plain(o),indent=2,sort_keys=True,allow_nan=False)+'\n')
def run():
 xs=Path((HERE/'local_cross_sections_path.txt').read_text().strip());openmc.config['cross_sections']=xs
 for b in [0,1]:
  p=HERE/'source_banks'/f'bank{b}.h5'
  if p.exists():raise RuntimeError('Refuse source-bank overwrite')
  ar=np.load(HERE/'source_banks'/f'bank{b}.npz');particles=[openmc.SourceParticle(r=tuple(r),u=tuple(u),E=A['energy_eV']) for r,u in zip(ar['r'],ar['u'])];openmc.write_source_file(particles,p)
 out=HERE/'runs';out.mkdir(exist_ok=False)
 save(HERE/'RUN_ADMISSION.json',{'admission_sha256':sha(HERE/'ADMISSION.json'),'source_result_sha256':sha(HERE/'SOURCE_RESULT.json'),'banks':{str(b):sha(HERE/'source_banks'/f'bank{b}.h5') for b in [0,1]},'driver_sha256':sha(Path(__file__)),'model_sha256':sha(HERE/'baseline/local_model.py'),'same_materials':True,'before_execution':True})
 env=os.environ.copy();env['OPENMC_CROSS_SECTIONS']=str(xs);env['OMP_NUM_THREADS']=str(A['threads']);done=[]
 for row in A['runs']:
  name=row['layout']+'_bank'+str(row['bank']);folder=out/name;folder.mkdir();model,meta=make(row['layout'],row['seed']);settings=model.settings;settings.source=openmc.FileSource(HERE/'source_banks'/f"bank{row['bank']}.h5");settings.batches=A['batches'];settings.particles=A['particles_per_batch'];settings.track=[(1,1,i) for i in range(1,17)]
  mesh=openmc.RegularMesh();mesh.lower_left=[0,0,0];mesh.upper_right=[meta['dimensions_cm'][k] for k in ['x','y','z']];mesh.dimension=[24,16,16]
  for n,score in [('volume_heating','heating'),('volume_tritons','H3-production')]:
   t=openmc.Tally(name=n);t.filters=[openmc.MeshFilter(mesh)];t.scores=[score]
   if score=='H3-production':t.filters.append(openmc.ParticleFilter(['neutron']))
   model.tallies.append(t)
  save(folder/'GEOMETRY.json',meta);model.export_to_xml(directory=folder);start=time.monotonic()
  with (folder/'private-execution.log').open('w') as log:
   p=subprocess.run([str(Path(sys.executable).with_name('openmc')),'-s',str(A['threads'])],cwd=folder,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=A['timeout_seconds_each'])
  if p.returncode:raise RuntimeError('OpenMC failed; evidence preserved')
  state=folder/f"statepoint.{A['batches']}.h5";tallies={}
  with openmc.StatePoint(state) as sp:
   for n in ['total_tritons','total_heating','heat_by_cell','tritons_by_cell','depth','volume_heating','volume_tritons']:
    t=sp.get_tally(name=n);tallies[n]={'mean':t.mean.ravel().tolist(),'std_dev':t.std_dev.ravel().tolist()}
  paths=[];histories=0
  for track in openmc.Tracks(folder/'tracks.h5'):
   histories+=1
   for j,(ptype,states) in enumerate(track.particle_tracks):
    if str(ptype).lower() not in ('neutron','photon'):continue
    points=[[float(s['r']['x']),float(s['r']['y']),float(s['r']['z']),float(s['time']),float(s['E'])] for s in states]
    if len(points)>1:paths.append({'primary':int(track.identifier[2]),'particle':str(ptype).lower(),'secondary_index':j,'states':points})
  save(folder/'TRACKS.json',{'source_histories_recorded':histories,'paths':paths,'all_states_recorded':True})
  result={'case':row,'histories':A['batches']*A['particles_per_batch'],'tallies':tallies,'elapsed_seconds':time.monotonic()-start,'completed':True,'statepoint_sha256':sha(state),'tracks_sha256':sha(folder/'tracks.h5'),'json_tracks_sha256':sha(folder/'TRACKS.json'),'geometry_sha256':sha(folder/'GEOMETRY.json'),'voxel_cm3':float(np.prod(mesh.width)),'physical_validation':False};save(folder/'RESULT.json',result);done.append(name);print(json.dumps({'completed':name,'seconds':result['elapsed_seconds'],'tritons':tallies['total_tritons']['mean'][0]}),flush=True)
 save(HERE/'STATUS.json',{'all_completed':len(done)==4,'runs':done,'physical_validation':False})
if __name__=='__main__':run()
